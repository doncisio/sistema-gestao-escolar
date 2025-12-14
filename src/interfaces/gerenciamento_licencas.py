from src.core.config_logs import get_logger
logger = get_logger(__name__)
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import mysql.connector
from typing import Any, cast
import sys
import os
# Importar a função de conexão correta
from src.core.conexao import conectar_bd

# Cores baseadas em main.py
co0 = "#F5F5F5"  # Branco suave
co1 = "#003A70"  # Azul escuro
co2 = "#77B341"  # Verde
co3 = "#E2418E"  # Rosa/Magenta
co4 = "#4A86E8"  # Azul mais claro
co5 = "#F26A25"  # Laranja
co6 = "#F7B731"  # Amarelo
co7 = "#333333"  # Cinza escuro
co8 = "#BF3036"  # Vermelho
co9 = "#6FA8DC"  # Azul claro

class InterfaceGerenciamentoLicencas:
    def __init__(self, root, funcionario_id=None):
        self.root = root
        self.funcionario_id = funcionario_id
        self.initialized_successfully = False
        
        # Configurar a janela
        self.root.title("Gerenciamento de Licenças")
        self.root.geometry("800x600")
        
        # Criar conexão com o banco
        self.conn: Any = conectar_bd()
        if not self.conn:
            messagebox.showerror("Erro Crítico", "Não foi possível conectar ao banco de dados. A janela de licenças não pode ser aberta.")
            return
        
        self.cursor: Any = cast(Any, self.conn).cursor(dictionary=True)
        
        try:
            # Criar a interface dentro de um bloco try
            self.criar_interface()
            
            # Se um funcionário específico foi passado, carregar seus dados
            if self.funcionario_id:
                self.carregar_dados_funcionario()
            
            # Configurar evento de fechamento
            self.root.protocol("WM_DELETE_WINDOW", self.ao_fechar)
            self.initialized_successfully = True
        except Exception as e:
            messagebox.showerror("Erro de Interface", f"Erro ao criar a interface de licenças: {e}")
            if self.conn:
                try:
                    cast(Any, self.cursor).close()
                    cast(Any, self.conn).close()
                except: pass
            return
    
    def criar_interface(self):
        # Configurar Estilos ttk
        style = ttk.Style(self.root)
        style.theme_use("clam") # Usar um tema base que permite mais customização

        # Estilos Gerais
        style.configure(".", background=co0, foreground=co7, font=('Ivy', 10)) # Estilo base para widgets ttk
        style.configure("TFrame", background=co0)
        style.configure("TLabel", background=co0, foreground=co7, font=('Ivy', 10))
        style.configure("TEntry", fieldbackground=co0, foreground=co7, font=('Ivy', 10))
        style.configure("TCombobox", fieldbackground=co0, foreground=co7, font=('Ivy', 10))
        style.map("TCombobox", fieldbackground=[('readonly', co0)]) # Manter fundo branco ao ser readonly

        # Estilo Botões
        style.configure("TButton", background=co4, foreground=co0, font=('Ivy', 10, 'bold'), padding=5)
        style.map("TButton",
                  background=[('active', co9), ('disabled', '#cccccc')],
                  foreground=[('active', co0), ('disabled', '#666666')])

        # Estilo Botão Salvar/Registrar (Verde)
        style.configure("Success.TButton", background=co2, foreground=co0)
        style.map("Success.TButton", background=[('active', '#5a9e2a')])

        # Estilo Botão Excluir (Vermelho)
        style.configure("Danger.TButton", background=co8, foreground=co0)
        style.map("Danger.TButton", background=[('active', '#a3292e')])

        # Estilo Botão Limpar (Amarelo/Laranja)
        style.configure("Warn.TButton", background=co6, foreground=co7)
        style.map("Warn.TButton", background=[('active', '#d4a02a')])

        # Estilo Treeview
        style.configure("Custom.Treeview",
                        background=co0,
                        foreground=co7,
                        fieldbackground=co0,
                        font=('Calibri', 11))
        style.configure("Custom.Treeview.Heading",
                        background=co1,
                        foreground=co0,
                        font=('Calibri', 13, 'bold'),
                        padding=5)
        style.map('Custom.Treeview',
                  background=[('selected', co4)],
                  foreground=[('selected', co0)])
        # Remover bordas internas se desejar (opcional)
        style.layout("Custom.Treeview", [('Custom.Treeview.treearea', {'sticky': 'nswe'})])

        # Estilo LabelFrame
        style.configure("TLabelFrame", background=co0, bordercolor=co9, relief="groove", padding=10)
        style.configure("TLabelFrame.Label", background=co0, foreground=co1, font=('Ivy', 11, 'bold'))


        # Frame principal com duas colunas
        self.frame_principal = ttk.Frame(self.root, padding="10") # Estilo padrão TFrame aplicado
        self.frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(self.frame_principal, text="Gerenciamento de Licenças", font=("Arial", 16, "bold"),
                  background=co0, foreground=co1).grid( # Cores aplicadas diretamente
            row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        # ===== Frame esquerdo para exibir funcionários =====
        self.frame_esquerdo = ttk.LabelFrame(self.frame_principal, text="Funcionários", padding="10") # Estilo TLabeFrame aplicado
        self.frame_esquerdo.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        # Botões de filtro
        frame_filtros = ttk.Frame(self.frame_esquerdo) # Estilo TFrame aplicado
        frame_filtros.pack(fill=tk.X, pady=5)
        
        ttk.Button(frame_filtros, text="Todos", command=self.carregar_todos_funcionarios).pack(side=tk.LEFT, padx=2) # Estilo TButton padrão
        ttk.Button(frame_filtros, text="Em Licença", command=self.carregar_funcionarios_em_licenca).pack(side=tk.LEFT, padx=2) # Estilo TButton padrão
        ttk.Button(frame_filtros, text="Polivalentes", command=lambda: self.carregar_funcionarios_por_cargo_polivalente("Professor@", "sim")).pack(side=tk.LEFT, padx=2) # Estilo TButton padrão
        ttk.Button(frame_filtros, text="Não Polivalentes", command=lambda: self.carregar_funcionarios_por_cargo_polivalente("Professor@", "não")).pack(side=tk.LEFT, padx=2) # Estilo TButton padrão
        
        # Campo de pesquisa
        frame_pesquisa = ttk.Frame(self.frame_esquerdo) # Estilo TFrame aplicado
        frame_pesquisa.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_pesquisa, text="Pesquisar:").pack(side=tk.LEFT) # Estilo TLabel aplicado
        self.e_pesquisa = ttk.Entry(frame_pesquisa) # Estilo TEntry aplicado
        self.e_pesquisa.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.e_pesquisa.bind("<KeyRelease>", self.pesquisar_funcionario)
        
        # Treeview para lista de funcionários
        self.tree_funcionarios = ttk.Treeview(self.frame_esquerdo, columns=("ID", "Nome", "Cargo", "Polivalente"),
                                              show="headings", style="Custom.Treeview") # Estilo Custom.Treeview aplicado
        self.tree_funcionarios.heading("ID", text="ID")
        self.tree_funcionarios.heading("Nome", text="Nome")
        self.tree_funcionarios.heading("Cargo", text="Cargo")
        self.tree_funcionarios.heading("Polivalente", text="Polivalente")
        
        self.tree_funcionarios.column("ID", width=50, anchor=tk.W)
        self.tree_funcionarios.column("Nome", width=200, anchor=tk.W)
        self.tree_funcionarios.column("Cargo", width=100, anchor=tk.W)
        self.tree_funcionarios.column("Polivalente", width=80, anchor=tk.W)
        
        self.tree_funcionarios.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree_funcionarios.bind("<<TreeviewSelect>>", self.ao_selecionar_funcionario)
        
        # Barra de rolagem para a Treeview
        scrollbar = ttk.Scrollbar(self.frame_esquerdo, orient=tk.VERTICAL, command=self.tree_funcionarios.yview)
        self.tree_funcionarios.configure(yscrollcommand=cast(Any, scrollbar.set))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ===== Frame direito para formulário de licença =====
        self.frame_direito = ttk.LabelFrame(self.frame_principal, text="Licença", padding="10") # Estilo TLabelFrame aplicado
        self.frame_direito.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        
        # Informações do funcionário
        ttk.Label(self.frame_direito, text="Funcionário:").grid(row=0, column=0, sticky=tk.W, pady=2) # Estilo TLabel
        self.lbl_nome_funcionario = ttk.Label(self.frame_direito, text="", foreground=co1, font=('Ivy', 10, 'bold')) # Foreground destacado
        self.lbl_nome_funcionario.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.frame_direito, text="Cargo:").grid(row=1, column=0, sticky=tk.W, pady=2) # Estilo TLabel
        self.lbl_cargo_funcionario = ttk.Label(self.frame_direito, text="", foreground=co1) # Foreground destacado
        self.lbl_cargo_funcionario.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.frame_direito, text="Polivalente:").grid(row=2, column=0, sticky=tk.W, pady=2) # Estilo TLabel
        self.lbl_polivalente_funcionario = ttk.Label(self.frame_direito, text="", foreground=co1) # Foreground destacado
        self.lbl_polivalente_funcionario.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Separador
        ttk.Separator(self.frame_direito, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=2, sticky='we', pady=10)
        
        # Formulário para nova licença
        ttk.Label(self.frame_direito, text="Motivo da Licença:").grid(row=4, column=0, sticky=tk.W, pady=2) # Estilo TLabel
        self.c_motivo = ttk.Combobox(self.frame_direito, width=30) # Estilo TCombobox
        self.c_motivo['values'] = (
            "Licença Maternidade", 
            "Licença Paternidade", 
            "Licença Médica", 
            "Licença Prêmio", 
            "Licença para Capacitação",
            "Licença para Tratamento de Saúde",
            "Licença por Motivo de Doença em Pessoa da Família",
            "Outros"
        )
        self.c_motivo.grid(row=4, column=1, sticky='we', pady=2)
        
        ttk.Label(self.frame_direito, text="Data de Início:").grid(row=5, column=0, sticky=tk.W, pady=2) # Estilo TLabel
        # Aplicando cores ao DateEntry (pode variar a aparência dependendo da versão do tkcalendar)
        self.c_data_inicio = DateEntry(self.frame_direito, width=18, background=co1, foreground=co0,
                                       borderwidth=2, date_pattern='dd/mm/yyyy', style='TEntry', # Tentar usar estilo base
                                       selectbackground=co4, selectforeground=co0)
        self.c_data_inicio.grid(row=5, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.frame_direito, text="Data de Fim:").grid(row=6, column=0, sticky=tk.W, pady=2) # Estilo TLabel
        self.c_data_fim = DateEntry(self.frame_direito, width=18, background=co1, foreground=co0,
                                    borderwidth=2, date_pattern='dd/mm/yyyy', style='TEntry', # Tentar usar estilo base
                                    selectbackground=co4, selectforeground=co0)
        # Definir data de fim para 30 dias após a data de início por padrão
        self.c_data_fim.set_date(datetime.now() + timedelta(days=30))
        self.c_data_fim.grid(row=6, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(self.frame_direito, text="Observação:").grid(row=7, column=0, sticky=tk.W, pady=2) # Estilo TLabel
        # Usando tk.Text, aplicar cores diretamente
        self.t_observacao = tk.Text(self.frame_direito, width=30, height=5, background=co0, foreground=co7,
                                    font=('Ivy', 10), relief="solid", borderwidth=1)
        self.t_observacao.grid(row=7, column=1, sticky='we', pady=2)
        
        # Botões
        frame_botoes = ttk.Frame(self.frame_direito) # Estilo TFrame
        frame_botoes.grid(row=8, column=0, columnspan=2, pady=10)
        
        self.btn_salvar = ttk.Button(frame_botoes, text="Registrar Licença", command=self.salvar_licenca,
                                     state=tk.DISABLED, style="Success.TButton") # Estilo Success.TButton
        self.btn_salvar.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_botoes, text="Limpar", command=self.limpar_formulario, style="Warn.TButton").pack(side=tk.LEFT, padx=5) # Estilo Warn.TButton
        
        # Frame para histórico de licenças
        self.frame_historico = ttk.LabelFrame(self.frame_direito, text="Histórico de Licenças", padding="10") # Estilo TLabelFrame
        self.frame_historico.grid(row=9, column=0, columnspan=2, sticky='we', pady=5)
        
        # Treeview para histórico de licenças
        self.tree_licencas = ttk.Treeview(self.frame_historico, columns=("ID", "Motivo", "Início", "Fim"),
                                          show="headings", height=5, style="Custom.Treeview") # Estilo Custom.Treeview
        self.tree_licencas.heading("ID", text="ID")
        self.tree_licencas.heading("Motivo", text="Motivo")
        self.tree_licencas.heading("Início", text="Data Início")
        self.tree_licencas.heading("Fim", text="Data Fim")
        
        self.tree_licencas.column("ID", width=30, anchor=tk.W)
        self.tree_licencas.column("Motivo", width=150, anchor=tk.W)
        self.tree_licencas.column("Início", width=80, anchor=tk.W)
        self.tree_licencas.column("Fim", width=80, anchor=tk.W)
        
        self.tree_licencas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Barra de rolagem para a Treeview de licenças
        scrollbar_licencas = ttk.Scrollbar(self.frame_historico, orient=tk.VERTICAL, command=self.tree_licencas.yview)
        self.tree_licencas.configure(yscrollcommand=cast(Any, scrollbar_licencas.set))
        scrollbar_licencas.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botão para excluir licença
        ttk.Button(self.frame_historico, text="Excluir Licença Selecionada", command=self.excluir_licenca,
                   style="Danger.TButton").pack(pady=5) # Estilo Danger.TButton
        
        # Configurar pesos das colunas para redimensionamento
        self.frame_principal.columnconfigure(0, weight=1)
        self.frame_principal.columnconfigure(1, weight=1)
        self.frame_principal.rowconfigure(1, weight=1)
        
        # Carregar funcionários
        self.carregar_todos_funcionarios()
    
    def carregar_dados_funcionario(self):
        try:
            # Buscar dados do funcionário no banco
            self.cursor.execute("""
                SELECT id, nome, cargo, polivalente
                FROM funcionarios
                WHERE id = %s
            """, (self.funcionario_id,))
            
            funcionario = self.cursor.fetchone()
            
            if funcionario:
                # Selecionar o funcionário na árvore
                for child in self.tree_funcionarios.get_children():
                    if self.tree_funcionarios.item(child, 'values')[0] == str(cast(Any, funcionario)['id']):
                        self.tree_funcionarios.selection_set(child)
                        self.tree_funcionarios.see(child)
                        self.ao_selecionar_funcionario(None)
                        break
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados do funcionário: {e}")
    
    def carregar_todos_funcionarios(self):
        try:
            # Limpar a lista atual
            for item in self.tree_funcionarios.get_children():
                self.tree_funcionarios.delete(item)
            
            # Buscar todos os funcionários
            self.cursor.execute("""
                SELECT id, nome, cargo, polivalente
                FROM funcionarios
                ORDER BY nome
            """)
            
            funcionarios = self.cursor.fetchall()
            
            # Adicionar funcionários à treeview
            for funcionario in funcionarios:
                self.tree_funcionarios.insert("", tk.END, values=(
                    cast(Any, funcionario)['id'],
                    cast(Any, funcionario)['nome'],
                    cast(Any, funcionario)['cargo'],
                    cast(Any, funcionario)['polivalente']
                ))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar funcionários: {e}")
    
    def carregar_funcionarios_em_licenca(self):
        try:
            # Limpar a lista atual
            for item in self.tree_funcionarios.get_children():
                self.tree_funcionarios.delete(item)
            
            # Buscar funcionários em licença
            self.cursor.execute("""
                SELECT DISTINCT f.id, f.nome, f.cargo, f.polivalente
                FROM funcionarios f
                JOIN licencas l ON f.id = l.funcionario_id
                WHERE CURRENT_DATE() BETWEEN l.data_inicio AND l.data_fim
                ORDER BY f.nome
            """)
            
            funcionarios = self.cursor.fetchall()
            
            # Adicionar funcionários à treeview
            for funcionario in funcionarios:
                self.tree_funcionarios.insert("", tk.END, values=(
                    cast(Any, funcionario)['id'],
                    cast(Any, funcionario)['nome'],
                    cast(Any, funcionario)['cargo'],
                    cast(Any, funcionario)['polivalente']
                ))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar funcionários em licença: {e}")
    
    def carregar_funcionarios_por_cargo_polivalente(self, cargo, polivalente):
        try:
            # Limpar a lista atual
            for item in self.tree_funcionarios.get_children():
                self.tree_funcionarios.delete(item)
            
            # Buscar funcionários pelo cargo e polivalente
            self.cursor.execute("""
                SELECT id, nome, cargo, polivalente
                FROM funcionarios
                WHERE cargo = %s AND polivalente = %s
                ORDER BY nome
            """, (cargo, polivalente))
            
            funcionarios = self.cursor.fetchall()
            
            # Adicionar funcionários à treeview
            for funcionario in funcionarios:
                self.tree_funcionarios.insert("", tk.END, values=(
                    cast(Any, funcionario)['id'],
                    cast(Any, funcionario)['nome'],
                    cast(Any, funcionario)['cargo'],
                    cast(Any, funcionario)['polivalente']
                ))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar funcionários: {e}")
    
    def pesquisar_funcionario(self, event=None):
        termo_pesquisa = self.e_pesquisa.get().strip().lower()
        
        if not termo_pesquisa:
            self.carregar_todos_funcionarios()
            return
        
        try:
            # Limpar a lista atual
            for item in self.tree_funcionarios.get_children():
                self.tree_funcionarios.delete(item)
            
            # Buscar funcionários que correspondam ao termo de pesquisa
            self.cursor.execute("""
                SELECT id, nome, cargo, polivalente
                FROM funcionarios
                WHERE LOWER(nome) LIKE %s OR LOWER(matricula) LIKE %s
                ORDER BY nome
            """, (f"%{termo_pesquisa}%", f"%{termo_pesquisa}%"))
            
            funcionarios = self.cursor.fetchall()
            
            # Adicionar funcionários à treeview
            for funcionario in funcionarios:
                self.tree_funcionarios.insert("", tk.END, values=(
                    cast(Any, funcionario)['id'],
                    cast(Any, funcionario)['nome'],
                    cast(Any, funcionario)['cargo'],
                    cast(Any, funcionario)['polivalente']
                ))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao pesquisar funcionários: {e}")
    
    def ao_selecionar_funcionario(self, event):
        selecionado = self.tree_funcionarios.selection()
        
        if not selecionado:
            return
        
        # Obter valores do funcionário selecionado
        valores = self.tree_funcionarios.item(selecionado[0], 'values')
        funcionario_id = valores[0]
        
        # Atualizar labels
        self.lbl_nome_funcionario.config(text=valores[1])
        self.lbl_cargo_funcionario.config(text=valores[2])
        self.lbl_polivalente_funcionario.config(text=valores[3])
        
        # Armazenar o ID do funcionário
        self.funcionario_id = funcionario_id
        
        # Habilitar botão de salvar
        self.btn_salvar.config(state=tk.NORMAL)
        
        # Carregar licenças do funcionário
        self.carregar_licencas_funcionario()
    
    def carregar_licencas_funcionario(self):
        if not self.funcionario_id:
            return
        
        try:
            # Limpar a lista atual de licenças
            for item in self.tree_licencas.get_children():
                self.tree_licencas.delete(item)
            
            # Buscar licenças do funcionário
            self.cursor.execute("""
                SELECT id, motivo, DATE_FORMAT(data_inicio, '%d/%m/%Y') as data_inicio, 
                       DATE_FORMAT(data_fim, '%d/%m/%Y') as data_fim
                FROM licencas
                WHERE funcionario_id = %s
                ORDER BY data_inicio DESC
            """, (self.funcionario_id,))
            
            licencas = self.cursor.fetchall()
            
            # Adicionar licenças à treeview
            for licenca in licencas:
                self.tree_licencas.insert("", tk.END, values=(
                    cast(Any, licenca)['id'],
                    cast(Any, licenca)['motivo'],
                    cast(Any, licenca)['data_inicio'],
                    cast(Any, licenca)['data_fim']
                ))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar licenças: {e}")
    
    def salvar_licenca(self):
        if not self.funcionario_id:
            messagebox.showwarning("Aviso", "Selecione um funcionário primeiro.")
            return
        
        # Obter dados do formulário
        motivo = self.c_motivo.get()
        data_inicio = self.c_data_inicio.get_date()
        data_fim = self.c_data_fim.get_date()
        observacao = self.t_observacao.get("1.0", tk.END).strip()
        
        # Validar campos
        if not motivo:
            messagebox.showwarning("Aviso", "Informe o motivo da licença.")
            return
        
        if data_fim < data_inicio:
            messagebox.showwarning("Aviso", "A data de fim não pode ser anterior à data de início.")
            return
        
        try:
            # Verificar licenças que se sobrepõem
            self.cursor.execute("""
                SELECT COUNT(*) as count
                FROM licencas
                WHERE funcionario_id = %s
                AND (
                    (data_inicio <= %s AND data_fim >= %s) OR
                    (data_inicio <= %s AND data_fim >= %s) OR
                    (data_inicio >= %s AND data_fim <= %s)
                )
            """, (
                self.funcionario_id, 
                data_inicio, data_inicio,  # Início está dentro de uma licença existente
                data_fim, data_fim,        # Fim está dentro de uma licença existente
                data_inicio, data_fim      # A licença existente está completamente dentro do período
            ))
            
            _row = self.cursor.fetchone()
            sobreposicao = cast(Any, _row)['count'] if _row is not None else 0
            
            if sobreposicao > 0:
                resposta = messagebox.askyesno(
                    "Sobreposição de Licenças", 
                    "Já existe uma licença registrada que se sobrepõe a este período. Deseja continuar?"
                )
                if not resposta:
                    return
            
            # Verificar se é professor polivalente
            self.cursor.execute("""
                SELECT cargo, polivalente, turma 
                FROM funcionarios
                WHERE id = %s
            """, (self.funcionario_id,))
            
            funcionario = self.cursor.fetchone()
            
            # Inserir licença no banco de dados
            self.cursor.execute("""
                INSERT INTO licencas (funcionario_id, motivo, data_inicio, data_fim, observacao)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                self.funcionario_id,
                motivo,
                data_inicio.strftime("%Y-%m-%d"),
                data_fim.strftime("%Y-%m-%d"),
                observacao
            ))
            
            # Se for professor polivalente e tiver uma turma designada, verificar se precisa buscar substituto
            if funcionario and cast(Any, funcionario)['cargo'] == 'Professor@' and cast(Any, funcionario)['polivalente'] == 'sim' and cast(Any, funcionario).get('turma'):
                messagebox.showinfo(
                    "Informação", 
                    "Professor polivalente em licença. Você pode designar um professor não polivalente seletivado como substituto."
                )
            
            cast(Any, self.conn).commit()
            messagebox.showinfo("Sucesso", "Licença registrada com sucesso!")
            
            # Limpar formulário e recarregar licenças
            self.limpar_formulario()
            self.carregar_licencas_funcionario()
            
        except Exception as e:
            cast(Any, self.conn).rollback()
            messagebox.showerror("Erro", f"Erro ao registrar licença: {e}")
    
    def excluir_licenca(self):
        selecionado = self.tree_licencas.selection()
        
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione uma licença para excluir.")
            return
        
        # Obter ID da licença selecionada
        licenca_id = self.tree_licencas.item(selecionado[0], 'values')[0]
        
        # Verificar se esta licença tem substituições ativas
        try:
            self.cursor.execute("""
                SELECT sp.id, f.nome, fs.nome as substituto_nome
                FROM licencas l
                JOIN funcionarios f ON l.funcionario_id = f.id
                JOIN substituicoes_professores sp ON f.id = sp.substituido_id
                JOIN funcionarios fs ON sp.professor_id = fs.id
                WHERE l.id = %s AND sp.data_fim IS NULL
            """, (licenca_id,))
            
            substituicoes = self.cursor.fetchall()
            
            if substituicoes:
                # Perguntar se devem ser encerradas as substituições
                substitutos_nomes = ", ".join([cast(Any, s)['substituto_nome'] for s in substituicoes])

                resposta = messagebox.askyesno(
                    "Encerrar Substituições", 
                    f"Existem {len(substituicoes)} professor(es) substituto(s) para esta licença: {substitutos_nomes}.\n\n"
                    "Deseja encerrar as substituições automaticamente?"
                )

                if resposta:
                    # Encerrar as substituições
                    for subst in substituicoes:
                        self.cursor.execute("""
                            UPDATE substituicoes_professores
                            SET data_fim = CURRENT_DATE()
                            WHERE id = %s
                        """, (cast(Any, subst)['id'],))
        except Exception as e:
            logger.error(f"Erro ao verificar substituições: {e}")
        
        # Confirmar exclusão
        resposta = messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir esta licença?")
        if not resposta:
            return
        
        try:
            # Excluir licença
            self.cursor.execute("DELETE FROM licencas WHERE id = %s", (licenca_id,))
            cast(Any, self.conn).commit()
            
            messagebox.showinfo("Sucesso", "Licença excluída com sucesso!")
            
            # Recarregar licenças
            self.carregar_licencas_funcionario()
            
        except Exception as e:
            cast(Any, self.conn).rollback()
            messagebox.showerror("Erro", f"Erro ao excluir licença: {e}")
    
    def limpar_formulario(self):
        self.c_motivo.set("")
        self.c_data_inicio.set_date(datetime.now())
        self.c_data_fim.set_date(datetime.now() + timedelta(days=30))
        self.t_observacao.delete("1.0", tk.END)
    
    def ao_fechar(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
        self.root.destroy()

# Função para abrir a interface de licenças
def abrir_interface_licencas(funcionario_id=None):
    root = tk.Toplevel()
    app = InterfaceGerenciamentoLicencas(root, funcionario_id)
    
    # Verificar se a inicialização foi bem-sucedida antes de manipular a janela
    if not app.initialized_successfully:
        # Se a inicialização falhou (ex: erro de DB), destruir a janela e retornar
        if root.winfo_exists(): # Verifica se a janela ainda existe
            root.destroy()
        return None # Retorna None para indicar falha
    
    # Se a inicialização foi bem-sucedida, continuar
    try:
        # Tenta obter a janela principal (parent)
        if root.master:
            root.transient(cast(Any, root.master))
    except:
        pass  # Se não for possível, simplesmente ignora
    root.focus_force()
    root.grab_set()
    return app

# Para teste direto do arquivo
if __name__ == "__main__":
    root = tk.Tk()
    app = InterfaceGerenciamentoLicencas(root)
    root.mainloop() 