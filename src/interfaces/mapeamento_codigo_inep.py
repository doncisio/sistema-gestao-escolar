"""
Interface para confirmação de mapeamento de códigos INEP
Autor: Sistema de Gestão Escolar
Data: 21/02/2026
"""

from tkinter import (
    Toplevel, Frame, Label, Button, Entry, Scrollbar, Canvas,
    messagebox, ttk, StringVar, BooleanVar, Checkbutton,
    LEFT, RIGHT, TOP, BOTTOM, BOTH, X, Y, W, E, N, S, END
)
from tkinter import filedialog
from typing import List, Dict, Optional
from src.services.mapeador_codigo_inep import MapeadorCodigoINEP
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class InterfaceConfirmacaoMapeamentoINEP:
    """Interface para confirmar mapeamentos de códigos INEP"""
    
    def __init__(self, master=None):
        """
        Inicializa a interface
        
        Args:
            master: Janela pai (opcional)
        """
        # Criar janela
        if master:
            self.janela = Toplevel(master)
        else:
            from tkinter import Tk
            self.janela = Tk()
        
        self.janela.title("Mapeamento de Códigos INEP")
        self.janela.geometry("1200x700")
        self.janela.configure(background='#feffff')
        
        # Cores
        self.co0 = "#2e2d2b"  # Preta
        self.co1 = "#feffff"  # Branca
        self.co2 = "#e5e5e5"  # Cinza
        self.co3 = "#00a095"  # Verde 
        self.co4 = "#403d3d"  # Letra
        self.co5 = "#003452"  # Azul
        self.co6 = "#ef5350"  # Vermelho
        self.co7 = "#038cfc"  # Azul
        
        # Dados
        self.mapeador = None
        self.mapeamentos = []
        self.linhas_tabela = []
        self.arquivo_excel = None
        
        # Variáveis de filtro
        self.filtro_status = StringVar(value="todos")
        self.filtro_busca = StringVar()
        self.filtro_busca.trace('w', lambda *args: self.filtrar_tabela())
        
        # Criar interface
        self.criar_interface()
    
    def criar_interface(self):
        """Cria a interface gráfica"""
        # Header
        frame_header = Frame(self.janela, bg=self.co5, height=60)
        frame_header.pack(fill=X)
        
        Label(
            frame_header,
            text="Importação de Códigos INEP",
            font=('Arial 16 bold'),
            bg=self.co5,
            fg=self.co1
        ).pack(pady=15)
        
        # Frame de ações
        frame_acoes = Frame(self.janela, bg=self.co1, height=80)
        frame_acoes.pack(fill=X, padx=10, pady=10)
        
        # Botão para selecionar arquivo
        Button(
            frame_acoes,
            text="📂 Selecionar Arquivo Excel",
            command=self.selecionar_arquivo,
            font=('Arial 10 bold'),
            bg=self.co7,
            fg=self.co1,
            width=25,
            height=2
        ).pack(side=LEFT, padx=5)
        
        # Label mostrando arquivo selecionado
        self.label_arquivo = Label(
            frame_acoes,
            text="Nenhum arquivo selecionado",
            font=('Arial 9'),
            bg=self.co1,
            fg=self.co4,
            anchor=W
        )
        self.label_arquivo.pack(side=LEFT, padx=10, fill=X, expand=True)
        
        # Botão para processar
        self.btn_processar = Button(
            frame_acoes,
            text="🔄 Processar Mapeamento",
            command=self.processar_mapeamento,
            font=('Arial 10 bold'),
            bg=self.co3,
            fg=self.co1,
            width=25,
            height=2,
            state='disabled'
        )
        self.btn_processar.pack(side=RIGHT, padx=5)
        
        # Frame de estatísticas
        self.frame_stats = Frame(self.janela, bg=self.co2, height=60)
        self.frame_stats.pack(fill=X, padx=10, pady=5)
        
        # Frame de filtros
        frame_filtros = Frame(self.janela, bg=self.co1, height=50)
        frame_filtros.pack(fill=X, padx=10, pady=5)
        
        Label(
            frame_filtros,
            text="Buscar:",
            font=('Arial 10'),
            bg=self.co1,
            fg=self.co4
        ).pack(side=LEFT, padx=5)
        
        Entry(
            frame_filtros,
            textvariable=self.filtro_busca,
            font=('Arial 10'),
            width=40
        ).pack(side=LEFT, padx=5)
        
        Label(
            frame_filtros,
            text="Filtrar por:",
            font=('Arial 10'),
            bg=self.co1,
            fg=self.co4
        ).pack(side=LEFT, padx=(20, 5))
        
        ttk.Radiobutton(
            frame_filtros,
            text="Todos",
            variable=self.filtro_status,
            value="todos",
            command=self.filtrar_tabela
        ).pack(side=LEFT, padx=5)
        
        ttk.Radiobutton(
            frame_filtros,
            text="Confirmados",
            variable=self.filtro_status,
            value="confirmado",
            command=self.filtrar_tabela
        ).pack(side=LEFT, padx=5)
        
        ttk.Radiobutton(
            frame_filtros,
            text="Para Revisar",
            variable=self.filtro_status,
            value="revisar",
            command=self.filtrar_tabela
        ).pack(side=LEFT, padx=5)
        
        # Frame da tabela
        frame_tabela = Frame(self.janela, bg=self.co1)
        frame_tabela.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Criar Treeview
        colunas = ('Aplicar', 'Nome Excel', 'Nome Banco', 'Código INEP', 'Turma', 'Similaridade', 'Status')
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show='headings', height=15)
        
        # Configurar colunas
        self.tree.heading('Aplicar', text='✓')
        self.tree.heading('Nome Excel', text='Nome no Excel')
        self.tree.heading('Nome Banco', text='Nome no Banco')
        self.tree.heading('Código INEP', text='Código INEP')
        self.tree.heading('Turma', text='Turma')
        self.tree.heading('Similaridade', text='Similaridade')
        self.tree.heading('Status', text='Status')
        
        self.tree.column('Aplicar', width=50, anchor='center')
        self.tree.column('Nome Excel', width=200)
        self.tree.column('Nome Banco', width=200)
        self.tree.column('Código INEP', width=120, anchor='center')
        self.tree.column('Turma', width=100)
        self.tree.column('Similaridade', width=100, anchor='center')
        self.tree.column('Status', width=100, anchor='center')
        
        # Scrollbars
        scrollbar_v = Scrollbar(frame_tabela, orient='vertical', command=self.tree.yview)
        scrollbar_h = Scrollbar(frame_tabela, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Posicionar componentes
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_v.grid(row=0, column=1, sticky='ns')
        scrollbar_h.grid(row=1, column=0, sticky='ew')
        
        frame_tabela.grid_rowconfigure(0, weight=1)
        frame_tabela.grid_columnconfigure(0, weight=1)
        
        # Tags para cores
        self.tree.tag_configure('confirmado', background='#c8e6c9')
        self.tree.tag_configure('revisar', background='#fff9c4')
        self.tree.tag_configure('nao_aplicar', background='#ffccbc')
        
        # Evento de clique duplo
        self.tree.bind('<Double-1>', self.alternar_aplicar)
        
        # Frame de ações finais
        frame_acoes_finais = Frame(self.janela, bg=self.co1, height=60)
        frame_acoes_finais.pack(fill=X, padx=10, pady=10)
        
        self.btn_aplicar = Button(
            frame_acoes_finais,
            text="✓ Aplicar Mapeamentos Selecionados",
            command=self.aplicar_mapeamentos,
            font=('Arial 12 bold'),
            bg=self.co3,
            fg=self.co1,
            width=30,
            height=2,
            state='disabled'
        )
        self.btn_aplicar.pack(side=RIGHT, padx=5)
        
        Button(
            frame_acoes_finais,
            text="✗ Cancelar",
            command=self.janela.destroy,
            font=('Arial 12'),
            bg=self.co6,
            fg=self.co1,
            width=15,
            height=2
        ).pack(side=RIGHT, padx=5)
        
        Button(
            frame_acoes_finais,
            text="☑ Marcar Todos",
            command=lambda: self.marcar_todos(True),
            font=('Arial 10'),
            bg=self.co7,
            fg=self.co1,
            width=15
        ).pack(side=LEFT, padx=5)
        
        Button(
            frame_acoes_finais,
            text="☐ Desmarcar Todos",
            command=lambda: self.marcar_todos(False),
            font=('Arial 10'),
            bg=self.co4,
            fg=self.co1,
            width=15
        ).pack(side=LEFT, padx=5)
    
    def selecionar_arquivo(self):
        """Abre diálogo para selecionar arquivo Excel"""
        arquivo = filedialog.askopenfilename(
            title="Selecionar arquivo Excel",
            filetypes=[("Arquivos Excel", "*.xlsx *.xls"), ("Todos os arquivos", "*.*")],
            initialdir="C:/gestao"
        )
        
        if arquivo:
            self.arquivo_excel = arquivo
            self.label_arquivo.config(text=f"Arquivo: {arquivo}")
            self.btn_processar.config(state='normal')
            logger.info(f"Arquivo selecionado: {arquivo}")
    
    def processar_mapeamento(self):
        """Processa o mapeamento do arquivo Excel"""
        if not self.arquivo_excel:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado!")
            return
        
        try:
            # Criar mapeador
            self.mapeador = MapeadorCodigoINEP(self.arquivo_excel)
            
            # Carregar dados
            if not self.mapeador.carregar_excel():
                messagebox.showerror("Erro", "Erro ao carregar arquivo Excel!")
                return
            
            if not self.mapeador.carregar_alunos_banco():
                messagebox.showerror("Erro", "Erro ao carregar alunos do banco de dados!")
                return
            
            # Mapear alunos
            self.mapeamentos = self.mapeador.mapear_alunos()
            
            # Adicionar flag de aplicar (por padrão, aplica confirmados automaticamente)
            for m in self.mapeamentos:
                m['aplicar'] = m['status'] == 'confirmado'
            
            # Atualizar interface
            self.atualizar_tabela()
            self.atualizar_estatisticas()
            self.btn_aplicar.config(state='normal')
            
            messagebox.showinfo(
                "Sucesso",
                f"Mapeamento processado com sucesso!\n\n"
                f"Total de registros: {len(self.mapeamentos)}\n"
                f"Confirmados: {sum(1 for m in self.mapeamentos if m['status'] == 'confirmado')}\n"
                f"Para revisar: {sum(1 for m in self.mapeamentos if m['status'] == 'revisar')}"
            )
            
        except Exception as e:
            logger.exception(f"Erro ao processar mapeamento: {e}")
            messagebox.showerror("Erro", f"Erro ao processar mapeamento:\n{str(e)}")
    
    def atualizar_tabela(self):
        """Atualiza a tabela com os mapeamentos"""
        # Limpar tabela
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adicionar mapeamentos
        for m in self.mapeamentos:
            aplicar = "✓" if m['aplicar'] else "✗"
            nome_excel = m['nome_excel']
            nome_banco = m['nome_banco'] or "NÃO ENCONTRADO"
            codigo_inep = m['codigo_inep']
            turma = m['turma']
            similaridade = f"{m['similaridade']:.1%}"
            status = m['status'].upper()
            
            # Determinar tag
            if not m['aplicar']:
                tag = 'nao_aplicar'
            elif m['status'] == 'confirmado':
                tag = 'confirmado'
            else:
                tag = 'revisar'
            
            self.tree.insert(
                '',
                END,
                values=(aplicar, nome_excel, nome_banco, codigo_inep, turma, similaridade, status),
                tags=(tag,)
            )
    
    def filtrar_tabela(self):
        """Filtra a tabela baseado nos critérios selecionados"""
        if not self.mapeamentos:
            return
        
        # Limpar tabela
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        busca = self.filtro_busca.get().upper()
        status_filtro = self.filtro_status.get()
        
        # Adicionar apenas mapeamentos que atendem aos filtros
        for m in self.mapeamentos:
            # Filtro de status
            if status_filtro != "todos" and m['status'] != status_filtro:
                continue
            
            # Filtro de busca
            if busca:
                if busca not in m['nome_excel'].upper() and busca not in (m['nome_banco'] or "").upper():
                    continue
            
            aplicar = "✓" if m['aplicar'] else "✗"
            nome_excel = m['nome_excel']
            nome_banco = m['nome_banco'] or "NÃO ENCONTRADO"
            codigo_inep = m['codigo_inep']
            turma = m['turma']
            similaridade = f"{m['similaridade']:.1%}"
            status = m['status'].upper()
            
            # Determinar tag
            if not m['aplicar']:
                tag = 'nao_aplicar'
            elif m['status'] == 'confirmado':
                tag = 'confirmado'
            else:
                tag = 'revisar'
            
            self.tree.insert(
                '',
                END,
                values=(aplicar, nome_excel, nome_banco, codigo_inep, turma, similaridade, status),
                tags=(tag,)
            )
    
    def atualizar_estatisticas(self):
        """Atualiza as estatísticas"""
        # Limpar frame
        for widget in self.frame_stats.winfo_children():
            widget.destroy()
        
        if not self.mapeamentos:
            return
        
        stats = self.mapeador.obter_estatisticas()
        aplicar = sum(1 for m in self.mapeamentos if m['aplicar'])
        
        labels = [
            f"Total: {stats['total']}",
            f"Confirmados: {stats['confirmados']}",
            f"Para Revisar: {stats['revisar']}",
            f"Já possuem código: {stats['ja_tem_codigo']}",
            f"Selecionados para aplicar: {aplicar}"
        ]
        
        for i, texto in enumerate(labels):
            Label(
                self.frame_stats,
                text=texto,
                font=('Arial 10 bold'),
                bg=self.co2,
                fg=self.co4
            ).pack(side=LEFT, padx=20, pady=10)
    
    def alternar_aplicar(self, event):
        """Alterna o status de aplicar de um mapeamento"""
        item = self.tree.selection()[0]
        valores = self.tree.item(item, 'values')
        
        if not valores:
            return
        
        nome_excel = valores[1]
        
        # Encontrar mapeamento
        for m in self.mapeamentos:
            if m['nome_excel'] == nome_excel:
                m['aplicar'] = not m['aplicar']
                break
        
        # Atualizar tabela
        self.filtrar_tabela()
        self.atualizar_estatisticas()
    
    def marcar_todos(self, marcar: bool):
        """Marca ou desmarca todos os mapeamentos"""
        for m in self.mapeamentos:
            m['aplicar'] = marcar
        
        self.filtrar_tabela()
        self.atualizar_estatisticas()
    
    def aplicar_mapeamentos(self):
        """Aplica os mapeamentos selecionados no banco de dados"""
        if not self.mapeamentos:
            messagebox.showerror("Erro", "Nenhum mapeamento disponível!")
            return
        
        mapeamentos_aplicar = [m for m in self.mapeamentos if m['aplicar'] and m['aluno_id']]
        
        if not mapeamentos_aplicar:
            messagebox.showwarning("Aviso", "Nenhum mapeamento selecionado para aplicar!")
            return
        
        # Confirmar com usuário
        resposta = messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja aplicar {len(mapeamentos_aplicar)} mapeamentos?\n\n"
            f"Esta ação irá atualizar os códigos INEP no banco de dados."
        )
        
        if not resposta:
            return
        
        try:
            sucessos, erros = self.mapeador.aplicar_mapeamentos(mapeamentos_aplicar)
            
            if erros == 0:
                messagebox.showinfo(
                    "Sucesso",
                    f"Mapeamentos aplicados com sucesso!\n\n"
                    f"Registros atualizados: {sucessos}"
                )
                self.janela.destroy()
            else:
                messagebox.showwarning(
                    "Concluído com Erros",
                    f"Processo concluído com alguns erros:\n\n"
                    f"Sucessos: {sucessos}\n"
                    f"Erros: {erros}"
                )
            
        except Exception as e:
            logger.exception(f"Erro ao aplicar mapeamentos: {e}")
            messagebox.showerror("Erro", f"Erro ao aplicar mapeamentos:\n{str(e)}")


def abrir_interface_mapeamento_inep(master=None):
    """
    Função auxiliar para abrir a interface de mapeamento
    
    Args:
        master: Janela pai (opcional)
    """
    interface = InterfaceConfirmacaoMapeamentoINEP(master)
    interface.janela.mainloop()


if __name__ == "__main__":
    abrir_interface_mapeamento_inep()
