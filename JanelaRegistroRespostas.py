"""
Janela para Registro de Respostas de Avaliações
Permite registrar respostas dos alunos questão por questão
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from banco_questoes.resposta_service import RespostaService
from conexao import conectar_bd


class JanelaRegistroRespostas:
    def __init__(self, parent, avaliacao_id, turma_id, ano_letivo_atual):
        self.parent = parent
        self.avaliacao_id = avaliacao_id
        self.turma_id = turma_id
        self.ano_letivo_atual = ano_letivo_atual
        self.resposta_service = RespostaService()
        
        self.janela = tk.Toplevel(parent)
        self.janela.title("📝 Registro de Respostas")
        self.janela.geometry("1200x700")
        self.janela.transient(parent)
        
        # Dados carregados
        self.avaliacao = None
        self.questoes = []
        self.alunos = []
        self.aluno_atual_idx = 0
        self.questao_atual_idx = 0
        self.respostas_temp = {}  # {aluno_id: {questao_id: valor}}
        
        self.criar_interface()
        self.carregar_dados()
        
    def criar_interface(self):
        """Cria a interface da janela"""
        
        # Frame superior - informações
        frame_info = ttk.Frame(self.janela, padding=10)
        frame_info.pack(fill=tk.X)
        
        self.lbl_avaliacao = ttk.Label(frame_info, text="Avaliação: Carregando...", 
                                       font=('Arial', 12, 'bold'))
        self.lbl_avaliacao.pack(anchor=tk.W)
        
        self.lbl_progresso = ttk.Label(frame_info, text="Aluno 0 de 0 | Questão 0 de 0")
        self.lbl_progresso.pack(anchor=tk.W, pady=5)
        
        # Frame principal com 2 colunas
        frame_principal = ttk.Frame(self.janela, padding=10)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Coluna esquerda - Lista de alunos
        frame_esq = ttk.LabelFrame(frame_principal, text="📋 Alunos", padding=10)
        frame_esq.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        
        # Scrollbar para lista de alunos
        scroll_alunos = ttk.Scrollbar(frame_esq)
        scroll_alunos.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree_alunos = ttk.Treeview(frame_esq, columns=('Status',), 
                                        show='tree headings',
                                        yscrollcommand=scroll_alunos.set,
                                        height=20)
        self.tree_alunos.heading('#0', text='Nome')
        self.tree_alunos.heading('Status', text='Status')
        self.tree_alunos.column('Status', width=100)
        self.tree_alunos.pack(fill=tk.BOTH, expand=True)
        scroll_alunos.config(command=self.tree_alunos.yview)
        
        self.tree_alunos.bind('<<TreeviewSelect>>', self.ao_selecionar_aluno)
        
        # Coluna direita - Questões
        frame_dir = ttk.LabelFrame(frame_principal, text="❓ Questões", padding=10)
        frame_dir.grid(row=0, column=1, sticky='nsew')
        
        frame_principal.columnconfigure(0, weight=1)
        frame_principal.columnconfigure(1, weight=2)
        frame_principal.rowconfigure(0, weight=1)
        
        # Navegação de questões
        frame_nav_questoes = ttk.Frame(frame_dir)
        frame_nav_questoes.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(frame_nav_questoes, text="◀ Anterior", 
                  command=self.questao_anterior).pack(side=tk.LEFT, padx=5)
        
        self.lbl_questao_num = ttk.Label(frame_nav_questoes, text="Questão 1 de 0",
                                         font=('Arial', 10, 'bold'))
        self.lbl_questao_num.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(frame_nav_questoes, text="Próxima ▶", 
                  command=self.questao_proxima).pack(side=tk.LEFT, padx=5)
        
        # Container de questão
        self.frame_questao = ttk.Frame(frame_dir)
        self.frame_questao.pack(fill=tk.BOTH, expand=True)
        
        # Frame inferior - ações
        frame_acoes = ttk.Frame(self.janela, padding=10)
        frame_acoes.pack(fill=tk.X)
        
        ttk.Button(frame_acoes, text="💾 Salvar Todas as Respostas", 
                  command=self.salvar_todas_respostas,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_acoes, text="🔄 Recarregar", 
                  command=self.carregar_dados).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_acoes, text="❌ Fechar", 
                  command=self.janela.destroy).pack(side=tk.RIGHT, padx=5)
        
    def carregar_dados(self):
        """Carrega avaliação, questões e alunos do banco"""
        try:
            conn = conectar_bd()
            if not conn:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados")
                return
                
            cursor = conn.cursor(dictionary=True)
            
            # Carrega avaliação
            cursor.execute("""
                SELECT av.*, d.nome as disciplina_nome
                FROM avaliacoes av
                LEFT JOIN disciplinas d ON av.componente_curricular = d.componente_curricular
                WHERE av.id = %s
            """, (self.avaliacao_id,))
            self.avaliacao = cursor.fetchone()
            
            if not self.avaliacao:
                messagebox.showerror("Erro", "Avaliação não encontrada")
                cursor.close()
                conn.close()
                self.janela.destroy()
                return
            
            # Carrega questões da avaliação
            cursor.execute("""
                SELECT q.*, aq.ordem, aq.pontuacao
                FROM avaliacoes_questoes aq
                INNER JOIN questoes q ON aq.questao_id = q.id
                WHERE aq.avaliacao_id = %s
                ORDER BY aq.ordem
            """, (self.avaliacao_id,))
            self.questoes = cursor.fetchall()
            
            # Carrega alunos da turma
            cursor.execute("""
                SELECT a.id, a.nome_completo,
                       aa.id as avaliacao_aluno_id, aa.status, aa.presente
                FROM alunos a
                INNER JOIN matriculas m ON a.id = m.aluno_id
                LEFT JOIN avaliacoes_alunos aa ON aa.aluno_id = a.id 
                    AND aa.avaliacao_id = %s AND aa.turma_id = %s
                WHERE m.turma_id = %s 
                  AND m.ano_letivo_id = %s
                  AND m.status_matricula = 'Cursando'
                ORDER BY a.nome_completo
            """, (self.avaliacao_id, self.turma_id, self.turma_id, self.ano_letivo_atual))
            self.alunos = cursor.fetchall()
            
            # Carrega respostas já existentes
            for aluno in self.alunos:
                if aluno['avaliacao_aluno_id']:
                    cursor.execute("""
                        SELECT questao_id, alternativa_id, resposta_texto, pontos
                        FROM respostas_questoes
                        WHERE avaliacao_aluno_id = %s
                    """, (aluno['avaliacao_aluno_id'],))
                    
                    respostas = cursor.fetchall()
                    aluno_id = aluno['id']
                    if aluno_id not in self.respostas_temp:
                        self.respostas_temp[aluno_id] = {}
                    
                    for resp in respostas:
                        questao_id = resp['questao_id']
                        if resp['alternativa_id']:
                            # Busca letra da alternativa
                            cursor.execute("""
                                SELECT letra FROM alternativas WHERE id = %s
                            """, (resp['alternativa_id'],))
                            alt = cursor.fetchone()
                            self.respostas_temp[aluno_id][questao_id] = alt['letra'] if alt else None
                        else:
                            self.respostas_temp[aluno_id][questao_id] = resp['resposta_texto']
            
            cursor.close()
            conn.close()
            self.atualizar_interface()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
    
    def atualizar_interface(self):
        """Atualiza todos os elementos da interface"""
        if self.avaliacao:
            titulo = f"Avaliação: {self.avaliacao['titulo']} - {self.avaliacao['disciplina_nome']} - Bimestre {self.avaliacao['bimestre']}"
            self.lbl_avaliacao.config(text=titulo)
        
        # Atualiza lista de alunos
        self.tree_alunos.delete(*self.tree_alunos.get_children())
        for idx, aluno in enumerate(self.alunos):
            status = "✓ Respondeu" if aluno.get('avaliacao_aluno_id') else "⏳ Pendente"
            iid = self.tree_alunos.insert('', tk.END, text=aluno['nome_completo'], 
                                          values=(status,))
            if idx == self.aluno_atual_idx:
                self.tree_alunos.selection_set(iid)
                self.tree_alunos.see(iid)
        
        self.atualizar_questao_atual()
        self.atualizar_progresso()
    
    def atualizar_questao_atual(self):
        """Mostra a questão atual"""
        # Limpa frame
        for widget in self.frame_questao.winfo_children():
            widget.destroy()
        
        if not self.questoes or not self.alunos:
            return
        
        questao = self.questoes[self.questao_atual_idx]
        aluno = self.alunos[self.aluno_atual_idx]
        
        # Número e pontuação
        ttk.Label(self.frame_questao, 
                 text=f"Questão {questao['ordem']} - {questao['pontuacao']} pontos",
                 font=('Arial', 11, 'bold')).pack(anchor=tk.W, pady=5)
        
        # Enunciado
        frame_enunciado = ttk.LabelFrame(self.frame_questao, text="Enunciado", padding=10)
        frame_enunciado.pack(fill=tk.X, pady=5)
        
        text_enunciado = scrolledtext.ScrolledText(frame_enunciado, height=6, wrap=tk.WORD,
                                                    font=('Arial', 10))
        text_enunciado.insert('1.0', questao['enunciado'])
        text_enunciado.config(state='disabled')
        text_enunciado.pack(fill=tk.BOTH, expand=True)
        
        # Frame de resposta
        frame_resposta = ttk.LabelFrame(self.frame_questao, text="Resposta", padding=10)
        frame_resposta.pack(fill=tk.BOTH, expand=True, pady=5)
        
        aluno_id = aluno['id']
        questao_id = questao['id']
        valor_salvo = self.respostas_temp.get(aluno_id, {}).get(questao_id)
        
        if questao['tipo'] == 'multipla_escolha':
            # Radio buttons para alternativas
            self.var_resposta = tk.StringVar(value=valor_salvo or '')
            
            # Busca alternativas
            conn = conectar_bd()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT id, letra, texto, correta
                    FROM alternativas
                    WHERE questao_id = %s
                    ORDER BY letra
                """, (questao_id,))
                alternativas = cursor.fetchall()
                cursor.close()
                conn.close()
            else:
                alternativas = []
            
            for alt in alternativas:
                rb = ttk.Radiobutton(frame_resposta, 
                                    text=f"{alt['letra']}) {alt['texto']}", 
                                    variable=self.var_resposta,
                                    value=alt['letra'])
                rb.pack(anchor=tk.W, pady=2)
                
                # Ao selecionar, salva temporariamente
                rb.config(command=lambda q_id=questao_id, a_id=aluno_id: 
                         self.salvar_resposta_temp(a_id, q_id, self.var_resposta.get()))
        
        else:  # dissertativa
            self.text_resposta = scrolledtext.ScrolledText(frame_resposta, height=10, 
                                                           wrap=tk.WORD, font=('Arial', 10))
            if valor_salvo:
                self.text_resposta.insert('1.0', valor_salvo)
            self.text_resposta.pack(fill=tk.BOTH, expand=True)
            
            # Botão para salvar texto
            ttk.Button(frame_resposta, text="💾 Salvar Resposta", 
                      command=lambda: self.salvar_resposta_temp(
                          aluno_id, questao_id, self.text_resposta.get('1.0', 'end-1c')
                      )).pack(pady=5)
        
        self.lbl_questao_num.config(text=f"Questão {self.questao_atual_idx + 1} de {len(self.questoes)}")
    
    def atualizar_progresso(self):
        """Atualiza label de progresso"""
        total_alunos = len(self.alunos)
        aluno_num = self.aluno_atual_idx + 1 if self.alunos else 0
        total_questoes = len(self.questoes)
        questao_num = self.questao_atual_idx + 1 if self.questoes else 0
        
        self.lbl_progresso.config(
            text=f"Aluno {aluno_num} de {total_alunos} | Questão {questao_num} de {total_questoes}"
        )
    
    def salvar_resposta_temp(self, aluno_id, questao_id, valor):
        """Salva resposta na memória temporária"""
        if aluno_id not in self.respostas_temp:
            self.respostas_temp[aluno_id] = {}
        self.respostas_temp[aluno_id][questao_id] = valor
    
    def questao_anterior(self):
        """Navega para questão anterior"""
        if self.questao_atual_idx > 0:
            self.questao_atual_idx -= 1
            self.atualizar_questao_atual()
            self.atualizar_progresso()
    
    def questao_proxima(self):
        """Navega para próxima questão"""
        if self.questao_atual_idx < len(self.questoes) - 1:
            self.questao_atual_idx += 1
            self.atualizar_questao_atual()
            self.atualizar_progresso()
    
    def ao_selecionar_aluno(self, event):
        """Quando seleciona aluno na lista"""
        selecao = self.tree_alunos.selection()
        if selecao:
            item = selecao[0]
            idx = self.tree_alunos.index(item)
            self.aluno_atual_idx = idx
            self.questao_atual_idx = 0  # Volta para primeira questão
            self.atualizar_questao_atual()
            self.atualizar_progresso()
    
    def salvar_todas_respostas(self):
        """Salva todas as respostas no banco de dados"""
        if not messagebox.askyesno("Confirmar", 
                                   "Salvar todas as respostas no banco de dados?"):
            return
        
        try:
            erros = []
            sucesso_count = 0
            
            for aluno in self.alunos:
                aluno_id = aluno['id']
                respostas_aluno = self.respostas_temp.get(aluno_id, {})
                
                if not respostas_aluno:
                    continue  # Aluno sem respostas
                
                # Cria ou recupera avaliacao_aluno_id
                avaliacao_aluno_id = aluno.get('avaliacao_aluno_id')
                
                if not avaliacao_aluno_id:
                    # Cria novo registro
                    avaliacao_aluno_id = self.resposta_service.criar_avaliacao_aluno(
                        self.avaliacao_id, aluno_id, self.turma_id, presente=True
                    )
                
                # Salva cada resposta
                for questao_id, valor in respostas_aluno.items():
                    if not valor or (isinstance(valor, str) and not valor.strip()):
                        continue  # Resposta vazia
                    
                    # Busca tipo da questão
                    questao = next((q for q in self.questoes if q['id'] == questao_id), None)
                    if not questao:
                        continue
                    
                    try:
                        if questao['tipo'] == 'multipla_escolha':
                            # Busca alternativa_id pela letra
                            conn_alt = conectar_bd()
                            if conn_alt:
                                cursor_alt = conn_alt.cursor(dictionary=True)
                                cursor_alt.execute("""
                                    SELECT id FROM alternativas 
                                    WHERE questao_id = %s AND letra = %s
                                """, (questao_id, valor))
                                alt = cursor_alt.fetchone()
                                cursor_alt.close()
                                conn_alt.close()
                            else:
                                alt = None
                            
                            if alt:
                                self.resposta_service.registrar_resposta_objetiva(
                                    avaliacao_aluno_id, questao_id, alt['id'], auto_corrigir=True
                                )
                                sucesso_count += 1
                        
                        else:  # dissertativa
                            self.resposta_service.registrar_resposta_dissertativa(
                                avaliacao_aluno_id, questao_id, valor
                            )
                            sucesso_count += 1
                    
                    except Exception as e:
                        erros.append(f"Aluno {aluno['nome_completo']}, Questão {questao['ordem']}: {str(e)}")
            
            # Mensagem final
            msg = f"✅ {sucesso_count} respostas salvas com sucesso!"
            if erros:
                msg += f"\n\n❌ {len(erros)} erros:\n" + "\n".join(erros[:10])
                if len(erros) > 10:
                    msg += f"\n... e mais {len(erros) - 10} erros"
            
            messagebox.showinfo("Resultado", msg)
            self.carregar_dados()  # Recarrega para atualizar status
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar respostas: {str(e)}")


if __name__ == "__main__":
    # Teste standalone
    root = tk.Tk()
    root.withdraw()
    
    # Substitua pelos IDs reais para teste
    janela = JanelaRegistroRespostas(root, avaliacao_id=1, turma_id=1, ano_letivo_atual=2025)
    root.mainloop()
