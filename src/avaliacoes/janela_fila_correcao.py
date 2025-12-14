"""
Janela para Correção Manual de Questões Dissertativas
Permite atribuir pontuação e comentários às respostas
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from banco_questoes.resposta_service import RespostaService
from src.core.conexao import conectar_bd


class JanelaFilaCorrecao:
    def __init__(self, parent, professor_id=None, turma_id=None, avaliacao_id=None):
        self.parent = parent
        self.professor_id = professor_id
        self.turma_id = turma_id
        self.avaliacao_id = avaliacao_id
        self.resposta_service = RespostaService()
        
        self.janela = tk.Toplevel(parent)
        self.janela.title("✏️ Fila de Correção")
        self.janela.geometry("1000x750")
        self.janela.transient(parent)
        
        self.fila = []
        self.indice_atual = 0
        
        self.criar_interface()
        self.carregar_fila()
        
    def criar_interface(self):
        """Cria a interface da janela"""
        
        # Frame superior - filtros
        frame_filtros = ttk.LabelFrame(self.janela, text="🔍 Filtros", padding=10)
        frame_filtros.pack(fill=tk.X, padx=10, pady=5)
        
        # Filtros em linha
        ttk.Label(frame_filtros, text="Turma:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.cb_turma = ttk.Combobox(frame_filtros, width=20, state='readonly')
        self.cb_turma.grid(row=0, column=1, padx=5)
        
        ttk.Label(frame_filtros, text="Avaliação:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.cb_avaliacao = ttk.Combobox(frame_filtros, width=30, state='readonly')
        self.cb_avaliacao.grid(row=0, column=3, padx=5)
        
        ttk.Button(frame_filtros, text="🔄 Filtrar", 
                  command=self.aplicar_filtros).grid(row=0, column=4, padx=10)
        
        # Frame info
        frame_info = ttk.Frame(self.janela, padding=10)
        frame_info.pack(fill=tk.X)
        
        self.lbl_info = ttk.Label(frame_info, text="Carregando fila de correção...",
                                  font=('Arial', 11, 'bold'))
        self.lbl_info.pack(anchor=tk.W)
        
        self.lbl_progresso = ttk.Label(frame_info, text="Resposta 0 de 0")
        self.lbl_progresso.pack(anchor=tk.W, pady=2)
        
        # Progress bar
        self.progress = ttk.Progressbar(frame_info, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Frame principal - questão e resposta
        frame_principal = ttk.Frame(self.janela, padding=10)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Questão
        frame_questao = ttk.LabelFrame(frame_principal, text="❓ Questão", padding=10)
        frame_questao.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.lbl_questao_info = ttk.Label(frame_questao, text="", font=('Arial', 10, 'bold'))
        self.lbl_questao_info.pack(anchor=tk.W, pady=5)
        
        self.text_enunciado = scrolledtext.ScrolledText(frame_questao, height=6, 
                                                        wrap=tk.WORD, font=('Arial', 10))
        self.text_enunciado.pack(fill=tk.BOTH, expand=True)
        self.text_enunciado.config(state='disabled')
        
        # Resposta do aluno
        frame_resposta = ttk.LabelFrame(frame_principal, text="📝 Resposta do Aluno", padding=10)
        frame_resposta.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.lbl_aluno = ttk.Label(frame_resposta, text="", font=('Arial', 10, 'bold'))
        self.lbl_aluno.pack(anchor=tk.W, pady=5)
        
        self.text_resposta = scrolledtext.ScrolledText(frame_resposta, height=8, 
                                                       wrap=tk.WORD, font=('Arial', 10),
                                                       bg='#fffacd')
        self.text_resposta.pack(fill=tk.BOTH, expand=True)
        self.text_resposta.config(state='disabled')
        
        # Frame de correção
        frame_correcao = ttk.LabelFrame(self.janela, text="✏️ Correção", padding=10)
        frame_correcao.pack(fill=tk.X, padx=10, pady=5)
        
        # Pontuação
        frame_pontos = ttk.Frame(frame_correcao)
        frame_pontos.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_pontos, text="Pontos:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.spin_pontos = ttk.Spinbox(frame_pontos, from_=0, to=100, width=10,
                                       font=('Arial', 11))
        self.spin_pontos.pack(side=tk.LEFT, padx=5)
        
        self.lbl_pontos_max = ttk.Label(frame_pontos, text="/ 0.0", font=('Arial', 10))
        self.lbl_pontos_max.pack(side=tk.LEFT)
        
        # Atalhos de pontuação
        frame_atalhos = ttk.Frame(frame_pontos)
        frame_atalhos.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(frame_atalhos, text="Atalhos:").pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_atalhos, text="0%", width=5,
                  command=lambda: self.definir_porcentagem(0)).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_atalhos, text="50%", width=5,
                  command=lambda: self.definir_porcentagem(50)).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_atalhos, text="75%", width=5,
                  command=lambda: self.definir_porcentagem(75)).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_atalhos, text="100%", width=5,
                  command=lambda: self.definir_porcentagem(100)).pack(side=tk.LEFT, padx=2)
        
        # Comentário
        ttk.Label(frame_correcao, text="Comentário (opcional):", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        self.text_comentario = scrolledtext.ScrolledText(frame_correcao, height=3, 
                                                         wrap=tk.WORD, font=('Arial', 9))
        self.text_comentario.pack(fill=tk.X)
        
        # Frame de navegação e ações
        frame_acoes = ttk.Frame(self.janela, padding=10)
        frame_acoes.pack(fill=tk.X)
        
        # Navegação
        frame_nav = ttk.Frame(frame_acoes)
        frame_nav.pack(side=tk.LEFT)
        
        ttk.Button(frame_nav, text="◀◀ Primeira", 
                  command=self.ir_primeira).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_nav, text="◀ Anterior", 
                  command=self.ir_anterior).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_nav, text="Próxima ▶", 
                  command=self.ir_proxima).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_nav, text="Última ▶▶", 
                  command=self.ir_ultima).pack(side=tk.LEFT, padx=2)
        
        # Ações
        frame_btns = ttk.Frame(frame_acoes)
        frame_btns.pack(side=tk.RIGHT)
        
        ttk.Button(frame_btns, text="💾 Salvar e Próxima", 
                  command=self.salvar_e_proxima,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_btns, text="❌ Fechar", 
                  command=self.fechar).pack(side=tk.LEFT, padx=5)
        
        # Atalhos de teclado
        self.janela.bind('<Control-s>', lambda e: self.salvar_e_proxima())
        self.janela.bind('<Left>', lambda e: self.ir_anterior())
        self.janela.bind('<Right>', lambda e: self.ir_proxima())
        
    def carregar_fila(self):
        """Carrega fila de correção do banco"""
        try:
            self.fila = self.resposta_service.buscar_fila_correcao(
                professor_id=self.professor_id,
                turma_id=self.turma_id,
                avaliacao_id=self.avaliacao_id
            )
            
            if not self.fila:
                messagebox.showinfo("Informação", "Não há respostas pendentes de correção!")
                self.lbl_info.config(text="✅ Nenhuma resposta pendente")
                return
            
            self.indice_atual = 0
            self.atualizar_interface()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar fila: {str(e)}")
    
    def aplicar_filtros(self):
        """Aplica filtros selecionados"""
        # TODO: implementar lógica de filtros quando necessário
        self.carregar_fila()
    
    def atualizar_interface(self):
        """Atualiza interface com resposta atual"""
        if not self.fila:
            return
        
        resposta = self.fila[self.indice_atual]
        
        # Atualiza informações
        total = len(self.fila)
        atual = self.indice_atual + 1
        self.lbl_info.config(text=f"📋 Fila de Correção - {total} resposta(s) pendente(s)")
        self.lbl_progresso.config(text=f"Resposta {atual} de {total}")
        self.progress['maximum'] = total
        self.progress['value'] = atual
        
        # Questão
        info_questao = f"Questão {resposta['ordem']} - Pontuação máxima: {resposta['pontuacao']} pontos"
        self.lbl_questao_info.config(text=info_questao)
        
        self.text_enunciado.config(state='normal')
        self.text_enunciado.delete('1.0', tk.END)
        self.text_enunciado.insert('1.0', resposta['enunciado'])
        self.text_enunciado.config(state='disabled')
        
        # Resposta do aluno
        turma_nome = resposta.get('turma_nome', 'Turma não informada')
        self.lbl_aluno.config(text=f"Aluno: {resposta['aluno_nome']} ({turma_nome})")
        
        self.text_resposta.config(state='normal')
        self.text_resposta.delete('1.0', tk.END)
        self.text_resposta.insert('1.0', resposta['resposta_texto'] or '')
        self.text_resposta.config(state='disabled')
        
        # Pontuação
        self.spin_pontos.config(to=resposta['pontuacao'])
        self.spin_pontos.set(resposta.get('pontos', 0))
        self.lbl_pontos_max.config(text=f"/ {resposta['pontuacao']}")
        
        # Comentário
        self.text_comentario.delete('1.0', tk.END)
        if resposta.get('comentario_corretor'):
            self.text_comentario.insert('1.0', resposta['comentario_corretor'])
    
    def definir_porcentagem(self, porcentagem):
        """Define pontuação como porcentagem do máximo"""
        if not self.fila:
            return
        
        resposta = self.fila[self.indice_atual]
        pontos_max = float(resposta['pontuacao'])
        pontos = (pontos_max * porcentagem) / 100
        self.spin_pontos.set(f"{pontos:.2f}")
    
    def salvar_correcao(self):
        """Salva correção atual"""
        if not self.fila:
            return False
        
        resposta = self.fila[self.indice_atual]
        
        try:
            pontos = float(self.spin_pontos.get())
            comentario = self.text_comentario.get('1.0', 'end-1c').strip()
            
            # Validação
            if pontos < 0 or pontos > resposta['pontuacao']:
                messagebox.showerror("Erro", 
                    f"Pontuação deve estar entre 0 e {resposta['pontuacao']}")
                return False
            
            # Salva via service
            self.resposta_service.corrigir_resposta(
                resposta_id=resposta['id'],
                pontos=pontos,
                comentario=comentario if comentario else None
            )
            
            return True
            
        except ValueError:
            messagebox.showerror("Erro", "Pontuação inválida")
            return False
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar correção: {str(e)}")
            return False
    
    def salvar_e_proxima(self):
        """Salva correção e vai para próxima"""
        if self.salvar_correcao():
            # Remove da fila
            self.fila.pop(self.indice_atual)
            
            if not self.fila:
                messagebox.showinfo("Concluído", "✅ Todas as correções foram finalizadas!")
                self.janela.destroy()
                return
            
            # Ajusta índice se necessário
            if self.indice_atual >= len(self.fila):
                self.indice_atual = len(self.fila) - 1
            
            self.atualizar_interface()
    
    def ir_primeira(self):
        """Vai para primeira resposta"""
        if self.fila:
            self.indice_atual = 0
            self.atualizar_interface()
    
    def ir_ultima(self):
        """Vai para última resposta"""
        if self.fila:
            self.indice_atual = len(self.fila) - 1
            self.atualizar_interface()
    
    def ir_anterior(self):
        """Vai para resposta anterior"""
        if self.fila and self.indice_atual > 0:
            self.indice_atual -= 1
            self.atualizar_interface()
    
    def ir_proxima(self):
        """Vai para próxima resposta"""
        if self.fila and self.indice_atual < len(self.fila) - 1:
            self.indice_atual += 1
            self.atualizar_interface()
    
    def fechar(self):
        """Fecha janela com confirmação se houver alterações"""
        if self.fila:
            if messagebox.askyesno("Confirmar", 
                f"Ainda há {len(self.fila)} resposta(s) pendente(s).\nDeseja realmente fechar?"):
                self.janela.destroy()
        else:
            self.janela.destroy()


if __name__ == "__main__":
    # Teste standalone
    root = tk.Tk()
    root.withdraw()
    
    janela = JanelaFilaCorrecao(root)
    root.mainloop()
