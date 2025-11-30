from datetime import datetime
from tkinter import Toplevel, Frame, Label, Entry, Button, StringVar
from tkinter import LEFT, RIGHT, BOTH, X, Y, VERTICAL, W
from tkinter import messagebox, ttk
from PIL import ImageTk, Image
import mysql.connector
from mysql.connector import Error
from conexao import conectar_bd
from tkcalendar import DateEntry
from utils.ui_callbacks import atualizar_treeview
from typing import Any, Optional, cast

def abrir_edicao_aluno(janela_pai, aluno_id, treeview=None, query=None):
    """
    Abre um formulário modal para edição de aluno.
    
    Args:
        janela_pai: A janela pai onde o modal será aberto
        aluno_id: ID do aluno a ser editado
        treeview: Treeview para atualizar após a edição (opcional)
        query: Query para atualizar o treeview (opcional)
    """
    # Definir cores
    co0 = "#F5F5F5"  # Branco suave para o fundo
    co1 = "#FFFFFF"  # Branco
    co2 = "#e5e5e5"  # Cinza claro
    co3 = "#00a095"  # Verde
    co4 = "#4A86E8"  # Azul mais claro
    co5 = "#003A70"  # Azul escuro
    co6 = "#ef5350"  # Vermelho
    co7 = "#333333"  # Cinza escuro
    co8 = "#BF3036"  # Vermelho escuro
    co9 = "#6FA8DC"  # Azul claro
    
    # Variáveis para conexão e cursor
    conn: Any = None
    cursor: Any = None
    
    try:
        # Obter informações do aluno
        conn = conectar_bd()
        # Se a conexão falhar, `conectar_bd` pode retornar None.
        # Evita acessar atributos de None (Pylance: reportOptionalMemberAccess).
        if conn is None:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
            return
        # Cast para Any para suprimir checagens estritas de tipo no Pylance
        cursor = cast(Any, conn).cursor()
        
        # Buscar dados do aluno
        cursor.execute("""
            SELECT a.nome, a.data_nascimento, a.local_nascimento, a.UF_nascimento,
                   a.endereco, a.sus, a.sexo, a.cpf, a.nis, a.raca, a.escola_id,
                   a.descricao_transtorno
            FROM alunos a
            WHERE a.id = %s
        """, (aluno_id,))
        dados_aluno = cursor.fetchone()
        
        if dados_aluno:
            nome, data_nascimento, local_nascimento, uf_nascimento, endereco, sus, sexo, cpf, nis, raca, escola_id, descricao_transtorno = dados_aluno
            
            # Obter o nome da escola
            cursor.execute("SELECT nome FROM escolas WHERE id = %s", (escola_id,))
            escola_nome_result = cursor.fetchone()
            escola_nome = escola_nome_result[0] if escola_nome_result else "Escola não encontrada"
            
            # Verificar matrícula ativa
            # Obtém o ID do ano letivo atual
            cursor.execute("SELECT id, ano_letivo FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
            resultado_ano = cursor.fetchone()
            
            if not resultado_ano:
                # Se não encontrar o ano letivo atual, tenta obter o ano letivo mais recente
                cursor.execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado_ano = cursor.fetchone()
            
            if not resultado_ano:
                messagebox.showwarning("Aviso", "Não foi possível determinar o ano letivo atual.")
                return

            ano_letivo_id, ano_letivo = resultado_ano
            
            # Procurar informações da matrícula ativa
            cursor.execute("""
                SELECT m.id, t.id, t.nome, t.turno, s.id, s.nome
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN serie s ON t.serie_id = s.id
                WHERE m.aluno_id = %s 
                AND m.ano_letivo_id = %s 
                AND m.status = 'Ativo'
            """, (aluno_id, ano_letivo_id))
            
            matricula_info = cursor.fetchone()
            tem_matricula = matricula_info is not None
            
            # Criar a janela de edição
            janela_edicao = Toplevel(janela_pai)
            janela_edicao.title(f"Editar Aluno - {nome}")
            janela_edicao.geometry("750x600")
            janela_edicao.configure(background=co1)
            janela_edicao.transient(janela_pai)
            janela_edicao.focus_force()
            janela_edicao.grab_set()
            
            # Frame principal
            frame_principal = Frame(janela_edicao, bg=co1, padx=20, pady=20)
            frame_principal.pack(fill=BOTH, expand=True)
            
            # Título
            titulo_frame = Frame(frame_principal, bg=co1)
            titulo_frame.pack(fill=X, pady=(0, 20))
            
            Label(titulo_frame, text=f"Edição de Dados do Aluno", 
                  font=("Arial", 16, "bold"), bg=co1, fg=co7).pack(side=LEFT)
            
            # Container para as abas
            container = ttk.Notebook(frame_principal)
            container.pack(fill=BOTH, expand=True)
            
            # Abas
            aba_dados = Frame(container, bg=co1)
            aba_matricula = Frame(container, bg=co1)
            aba_responsaveis = Frame(container, bg=co1)  # Nova aba para responsáveis
            
            container.add(aba_dados, text="Dados Pessoais")
            container.add(aba_matricula, text="Matrícula")
            container.add(aba_responsaveis, text="Responsáveis")
            
            # ---- ABA DE DADOS PESSOAIS ----
            # Frame para os campos
            form_frame = Frame(aba_dados, bg=co1, padx=10, pady=10)
            form_frame.pack(fill=BOTH, expand=True)
            
            # Configuração de grid para organizar os campos
            form_frame.columnconfigure(0, weight=1)
            form_frame.columnconfigure(1, weight=1)
            
            # Estilo para os campos
            label_estilo = {'bg': co1, 'fg': co7, 'font': ('Arial', 10)}
            entry_estilo = {'width': 30, 'relief': 'solid', 'font': ('Arial', 10)}
            combo_estilo = {'width': 28, 'font': ('Arial', 10)}
            
            # Primeira coluna - Dados Básicos
            frame_col1 = Frame(form_frame, bg=co1)
            frame_col1.grid(row=0, column=0, sticky='nsew', padx=10, pady=5)
            
            Label(frame_col1, text="Informações Básicas", font=("Arial", 12, "bold"), bg=co1, fg=co5).pack(anchor=W, pady=(0, 10))
            
            # Nome
            Label(frame_col1, text="Nome Completo *", **label_estilo).pack(anchor=W, pady=(5, 0))
            e_nome = Entry(frame_col1, **entry_estilo)
            e_nome.pack(fill=X, pady=(0, 10))
            e_nome.insert(0, str(nome) if nome is not None else "")
            
            # Data de Nascimento
            Label(frame_col1, text="Data de Nascimento", **label_estilo).pack(anchor=W, pady=(5, 0))
            c_data_nascimento = DateEntry(frame_col1, width=28, background=co5, foreground='white', 
                                         borderwidth=2, date_pattern='yyyy-mm-dd')
            c_data_nascimento.pack(anchor=W, pady=(0, 10))
            if data_nascimento:
                c_data_nascimento.set_date(datetime.strptime(str(data_nascimento), "%Y-%m-%d").date())
            
            # Local de Nascimento
            Label(frame_col1, text="Local de Nascimento", **label_estilo).pack(anchor=W, pady=(5, 0))
            e_local_nascimento = Entry(frame_col1, **entry_estilo)
            e_local_nascimento.pack(fill=X, pady=(0, 10))
            e_local_nascimento.insert(0, str(local_nascimento) if local_nascimento else "Paço do Lumiar")
            
            # UF de Nascimento
            Label(frame_col1, text="UF de Nascimento", **label_estilo).pack(anchor=W, pady=(5, 0))
            estados_brasileiros = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", 
                                 "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", 
                                 "SP", "SE", "TO"]
            c_uf_nascimento = ttk.Combobox(frame_col1, values=estados_brasileiros, **combo_estilo)
            c_uf_nascimento.pack(anchor=W, pady=(0, 10))
            c_uf_nascimento.set(uf_nascimento if uf_nascimento else "MA")
            
            # Segunda coluna - Dados Complementares
            frame_col2 = Frame(form_frame, bg=co1)
            frame_col2.grid(row=0, column=1, sticky='nsew', padx=10, pady=5)
            
            Label(frame_col2, text="Informações Complementares", font=("Arial", 12, "bold"), bg=co1, fg=co5).pack(anchor=W, pady=(0, 10))
            
            # CPF (col 1)
            frame_cpf = Frame(frame_col2, bg=co1)
            frame_cpf.grid(row=0, column=0, sticky='nsew', padx=5)
            
            Label(frame_cpf, text="CPF", **label_estilo).pack(anchor=W, pady=(5, 0))
            e_cpf = Entry(frame_cpf, width=20, relief='solid')
            e_cpf.pack(fill=X, pady=(0, 10))
            e_cpf.insert(0, str(cpf) if cpf else "")
            
            # NIS (col 2)
            frame_nis = Frame(frame_col2, bg=co1)
            frame_nis.grid(row=0, column=1, sticky='nsew', padx=5)
            
            Label(frame_nis, text="NIS", **label_estilo).pack(anchor=W, pady=(5, 0))
            e_nis = Entry(frame_nis, width=20, relief='solid')
            e_nis.pack(fill=X, pady=(0, 10))
            e_nis.insert(0, str(nis) if nis else "")
            
            # Cartão SUS
            Label(frame_col2, text="Cartão SUS", **label_estilo).pack(anchor=W, pady=(5, 0))
            e_sus = Entry(frame_col2, **entry_estilo)
            e_sus.pack(fill=X, pady=(0, 10))
            e_sus.insert(0, str(sus) if sus else "")
            
            # Endereço
            Label(frame_col2, text="Endereço", **label_estilo).pack(anchor=W, pady=(5, 0))
            e_endereco = Entry(frame_col2, **entry_estilo)
            e_endereco.pack(fill=X, pady=(0, 10))
            e_endereco.insert(0, str(endereco) if endereco else "")
            
            # Sexo
            Label(frame_col2, text="Sexo", **label_estilo).pack(anchor=W, pady=(5, 0))
            c_sexo = ttk.Combobox(frame_col2, values=('M', 'F'), **combo_estilo)
            c_sexo.pack(anchor=W, pady=(0, 10))
            c_sexo.set(sexo if sexo else "")
            
            # Terceira linha - Informações Escolares
            frame_linha2 = Frame(form_frame, bg=co1)
            frame_linha2.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10, pady=15)
            
            Label(frame_linha2, text="Informações Escolares e Complementares", font=("Arial", 12, "bold"), bg=co1, fg=co5).pack(anchor=W, pady=(0, 10))
            
            # Criar um frame para os campos da segunda linha
            frame_campos2 = Frame(frame_linha2, bg=co1)
            frame_campos2.pack(fill=X)
            frame_campos2.columnconfigure(0, weight=1)
            frame_campos2.columnconfigure(1, weight=1)
            frame_campos2.columnconfigure(2, weight=1)
            
            # Escola (col 1)
            frame_escola = Frame(frame_campos2, bg=co1)
            frame_escola.grid(row=0, column=0, sticky='nsew', padx=5)
            
            Label(frame_escola, text="Escola *", **label_estilo).pack(anchor=W, pady=(5, 0))
            escolas_map = {}
            cursor.execute("SELECT id, nome FROM escolas ORDER BY nome, id")
            escolas = cursor.fetchall()
            
            # Criar mapeamento e valores para combobox
            escolas_valores = []
            for id, nome in escolas:
                # Se já existe uma escola com este nome, adicionar o ID ao nome para diferenciar
                if nome in escolas_map:
                    nome_com_id = f"{nome} (ID: {id})"
                    escolas_valores.append(nome_com_id)
                    escolas_map[nome_com_id] = id
                else:
                    escolas_valores.append(nome)
                    escolas_map[nome] = id
            
            c_escola = ttk.Combobox(frame_escola, values=escolas_valores, **combo_estilo)
            c_escola.pack(fill=X, pady=(0, 10))
            
            # Definir a escola atual do aluno
            for nome, id in escolas_map.items():
                if id == escola_id:
                    c_escola.set(nome)
                    break
                
            # Raça (col 2)
            frame_raca = Frame(frame_campos2, bg=co1)
            frame_raca.grid(row=0, column=1, sticky='nsew', padx=5)
            
            Label(frame_raca, text="Raça *", **label_estilo).pack(anchor=W, pady=(5, 0))
            c_raca = ttk.Combobox(frame_raca, values=('preto', 'pardo', 'branco', 'indígena', 'amarelo'), **combo_estilo)
            c_raca.pack(fill=X, pady=(0, 10))
            c_raca.set(raca if raca else "pardo")
            
            # Descrição do Transtorno (linha completa)
            Label(frame_linha2, text="Descrição do Transtorno", **label_estilo).pack(anchor=W, pady=(5, 0))
            e_descricao_transtorno = Entry(frame_linha2, width=60, relief='solid')
            e_descricao_transtorno.pack(fill=X, pady=(0, 10))
            e_descricao_transtorno.insert(0, str(descricao_transtorno) if descricao_transtorno else "Nenhum")
            
            # ---- ABA DE MATRÍCULA ----
            # Frame para os campos de matrícula
            matricula_frame = Frame(aba_matricula, bg=co1, padx=20, pady=20)
            matricula_frame.pack(fill=BOTH, expand=True)
            
            # Status da matrícula
            status_frame = Frame(matricula_frame, bg=co1, relief='solid', bd=1)
            status_frame.pack(fill=X, pady=10)
            
            if tem_matricula:
                matricula_id, turma_id, turma_nome, turma_turno, serie_id, serie_nome = matricula_info
                status_label = Label(status_frame, text="Status da Matrícula: ATIVO", 
                                  font=("Arial", 14, "bold"), bg=co2, fg=co3, padx=10, pady=10)
                status_label.pack(fill=X)
                
                # Detalhes da matrícula
                detalhes_frame = Frame(matricula_frame, bg=co1, pady=10)
                detalhes_frame.pack(fill=X)
                
                Label(detalhes_frame, text="Detalhes da Matrícula Atual", 
                     font=("Arial", 12, "bold"), bg=co1, fg=co7).pack(anchor=W, pady=10)
                    
                Label(detalhes_frame, text=f"Série: {serie_nome}", 
                     font=("Arial", 11), bg=co1, fg=co7).pack(anchor=W, pady=2)
                    
                Label(detalhes_frame, text=f"Turma: {turma_nome}", 
                     font=("Arial", 11), bg=co1, fg=co7).pack(anchor=W, pady=2)
                    
                Label(detalhes_frame, text=f"Turno: {turma_turno}", 
                     font=("Arial", 11), bg=co1, fg=co7).pack(anchor=W, pady=2)
                
                # Frame para alterar matrícula
                alterar_frame = Frame(matricula_frame, bg=co1, pady=20)
                alterar_frame.pack(fill=X)
                
                Label(alterar_frame, text="Alterar Matrícula", 
                     font=("Arial", 12, "bold"), bg=co1, fg=co7).pack(anchor=W, pady=10)
                
                # Botão para editar matrícula
                Button(alterar_frame, text="Editar Matrícula", 
                      command=lambda: editar_matricula(aluno_id, matricula_id, turma_id, serie_id),
                      font=('Ivy 10'), bg=co4, fg=co0, width=20).pack(side=LEFT, padx=5, pady=10)
                
                # Botão para cancelar matrícula
                Button(alterar_frame, text="Cancelar Matrícula", 
                      command=lambda: cancelar_matricula(matricula_id),
                      font=('Ivy 10'), bg=co6, fg=co0, width=20).pack(side=LEFT, padx=5, pady=10)
                
                # Botão para atualizar status
                statuses = ["Ativo", "Evadido", "Cancelado", "Transferido", "Concluído"]
                c_status = ttk.Combobox(alterar_frame, values=statuses, width=15)
                c_status.pack(side=LEFT, padx=5, pady=10)
                c_status.set("Ativo")  # Status padrão
                
                Button(alterar_frame, text="Atualizar Status", 
                      command=lambda: atualizar_status_matricula(matricula_id, c_status.get()),
                      font=('Ivy 10'), bg=co4, fg=co0, width=15).pack(side=LEFT, padx=5, pady=10)
                
            else:
                status_label = Label(status_frame, text="Status da Matrícula: NÃO MATRICULADO", 
                                  font=("Arial", 14, "bold"), bg=co2, fg=co6, padx=10, pady=10)
                status_label.pack(fill=X)
                
                # Mensagem e botão para criar matrícula
                Label(matricula_frame, text="O aluno não possui matrícula ativa para o ano letivo atual.", 
                     font=("Arial", 12), bg=co1, fg=co7).pack(anchor=W, pady=10)
                
                # Criar uma referência a função matricular_aluno
                from main import matricular_aluno as matricular_aluno_func
                    
                Button(matricula_frame, text="Matricular Aluno", 
                      command=lambda: matricular_aluno_do_modulo(aluno_id),
                      font=('Ivy 12 bold'), bg=co3, fg=co0, width=20, height=2).pack(pady=20)
                
                # Função de ajuste para chamar o matricular_aluno do módulo principal
                def matricular_aluno_do_modulo(aluno_id):
                    # Fecha a janela de edição
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                    
                    janela_edicao.destroy()
                    
                    # Chama a função matricular_aluno do módulo main
                    matricular_aluno_func(aluno_id)
            
            # Funções para lidar com alterações de matrícula
            def editar_matricula(aluno_id, matricula_id, turma_atual_id, serie_atual_id):
                nonlocal conn, cursor
                try:
                    # Criar janela de edição
                    janela_edicao_matricula = Toplevel(janela_edicao)
                    janela_edicao_matricula.title("Editar Matrícula")
                    janela_edicao_matricula.geometry("500x650")
                    janela_edicao_matricula.configure(background=co1)
                    janela_edicao_matricula.transient(janela_edicao)
                    janela_edicao_matricula.focus_force()
                    janela_edicao_matricula.grab_set()
                    
                    # Frame principal
                    frame_edicao = Frame(janela_edicao_matricula, bg=co1, padx=20, pady=20)
                    frame_edicao.pack(fill=BOTH, expand=True)
                    
                    # Título
                    Label(frame_edicao, text="Editar Matrícula", 
                          font=("Arial", 14, "bold"), bg=co1, fg=co7).pack(pady=(0, 20))
                    
                    # Obter informações da série atual
                    cursor.execute("""
                        SELECT s.id, s.nome, t.id, t.nome, t.turno
                        FROM serie s
                        JOIN turmas t ON s.id = t.serie_id
                        WHERE t.id = %s
                    """, (turma_atual_id,))
                    serie_atual = cursor.fetchone()
                    
                    # Selecionar Série
                    serie_frame = Frame(frame_edicao, bg=co1)
                    serie_frame.pack(fill=X, pady=10)
                    
                    Label(serie_frame, text="Série:", bg=co1, fg=co7).pack(anchor=W)
                    serie_var = StringVar(value=str(serie_atual[1]) if serie_atual and serie_atual[1] is not None else "")
                    cb_serie = ttk.Combobox(serie_frame, textvariable=serie_var, width=40)
                    cb_serie.pack(fill=X, pady=(5, 0))
                    
                    # Selecionar Turma
                    turma_frame = Frame(frame_edicao, bg=co1)
                    turma_frame.pack(fill=X, pady=10)
                    
                    Label(turma_frame, text="Turma:", bg=co1, fg=co7).pack(anchor=W)
                    turma_var = StringVar(value=str(serie_atual[3]) if serie_atual and serie_atual[3] is not None else "")
                    cb_turma = ttk.Combobox(turma_frame, textvariable=turma_var, width=40)
                    cb_turma.pack(fill=X, pady=(5, 0))
                    
                    # Escola de Origem (para alunos transferidos recebidos)
                    escola_origem_frame = Frame(frame_edicao, bg=co1)
                    escola_origem_frame.pack(fill=X, pady=10)
                    
                    Label(escola_origem_frame, text="Escola de Origem (se transferido):", bg=co1, fg=co7).pack(anchor=W)
                    escola_origem_var = StringVar()
                    cb_escola_origem = ttk.Combobox(escola_origem_frame, textvariable=escola_origem_var, width=40)
                    cb_escola_origem.pack(fill=X, pady=(5, 0))
                    
                    # Escola de Destino (para alunos transferidos expedidos)
                    escola_destino_frame = Frame(frame_edicao, bg=co1)
                    escola_destino_frame.pack(fill=X, pady=10)
                    
                    Label(escola_destino_frame, text="Escola de Destino (se transferindo):", bg=co1, fg=co7).pack(anchor=W)
                    escola_destino_var = StringVar()
                    cb_escola_destino = ttk.Combobox(escola_destino_frame, textvariable=escola_destino_var, width=40)
                    cb_escola_destino.pack(fill=X, pady=(5, 0))
                    
                    # Dicionários para mapear nomes para IDs
                    series_map = {}
                    turmas_map = {}
                    escolas_map = {}
                    
                    # Carregar séries
                    cursor.execute("""
                        SELECT DISTINCT s.id, s.nome 
                        FROM serie s
                        JOIN turmas t ON s.id = t.serie_id
                        WHERE t.escola_id = 60
                        AND t.ano_letivo_id = %s
                        ORDER BY s.nome
                    """, (ano_letivo_id,))
                    series = cursor.fetchall()
                    
                    if not series:
                        messagebox.showwarning("Aviso", "Não foram encontradas séries para a escola selecionada.")
                        return
                    
                    series_map.clear()
                    for serie in series:
                        series_map[serie[1]] = serie[0]
                    
                    cb_serie['values'] = list(series_map.keys())
                    
                    # Carregar escolas
                    cursor.execute("""
                        SELECT id, nome 
                        FROM escolas
                        ORDER BY nome
                    """)
                    escolas = cursor.fetchall()
                    
                    escolas_map.clear()
                    escolas_map[''] = None  # Opção vazia
                    for escola in escolas:
                        escolas_map[escola[1]] = escola[0]
                    
                    cb_escola_origem['values'] = [''] + list([e[1] for e in escolas])
                    cb_escola_destino['values'] = [''] + list([e[1] for e in escolas])
                    
                    # Carregar valores atuais de escola origem/destino
                    cursor.execute("""
                        SELECT escola_origem_id, escola_destino_id
                        FROM matriculas
                        WHERE id = %s
                    """, (matricula_id,))
                    escola_data = cursor.fetchone()
                    
                    if escola_data:
                        if escola_data[0]:  # escola_origem_id
                            cursor.execute("SELECT nome FROM escolas WHERE id = %s", (escola_data[0],))
                            origem = cursor.fetchone()
                            if origem:
                                escola_origem_var.set(origem[0])
                        
                        if escola_data[1]:  # escola_destino_id
                            cursor.execute("SELECT nome FROM escolas WHERE id = %s", (escola_data[1],))
                            destino = cursor.fetchone()
                            if destino:
                                escola_destino_var.set(destino[0])
                    
                    # Carregar turmas da série atual
                    if serie_atual:
                        cursor.execute("""
                            SELECT id, nome
                            FROM turmas 
                            WHERE serie_id = %s AND escola_id = 60 AND ano_letivo_id = %s
                            ORDER BY nome
                        """, (serie_atual[0], ano_letivo_id))
                        
                        turmas = cursor.fetchall()
                        
                        if turmas:
                            turmas_map.clear()
                            for turma in turmas:
                                turmas_map[turma[1]] = turma[0]
                            
                            cb_turma['values'] = list(turmas_map.keys())
                    
                    # Função para carregar turmas quando a série é alterada
                    def carregar_turmas(event=None):
                        nonlocal cursor
                        serie_nome = serie_var.get()
                        if not serie_nome or serie_nome not in series_map:
                            return
                        
                        serie_id = series_map[serie_nome]
                        
                        cursor.execute("""
                            SELECT id, nome
                            FROM turmas 
                            WHERE serie_id = %s AND escola_id = 60 AND ano_letivo_id = %s
                            ORDER BY nome
                        """, (serie_id, ano_letivo_id))
                        
                        turmas = cursor.fetchall()
                        
                        if turmas:
                            turmas_map.clear()
                            for turma in turmas:
                                turmas_map[turma[1]] = turma[0]
                            
                            cb_turma['values'] = list(turmas_map.keys())
                            # Se houver apenas uma turma, seleciona automaticamente
                            if len(turmas) == 1:
                                cb_turma.set(turmas[0][1])
                    
                    # Vincular evento ao combobox de série
                    cb_serie.bind("<<ComboboxSelected>>", carregar_turmas)
                    
                    # Função para adicionar nova escola
                    def adicionar_nova_escola():
                        nonlocal cursor, conn
                        try:
                            # Criar janela de diálogo para adicionar escola
                            dialog_escola = Toplevel(janela_edicao_matricula)
                            dialog_escola.title("Adicionar Nova Escola")
                            dialog_escola.geometry("400x450")
                            dialog_escola.configure(background=co1)
                            dialog_escola.transient(janela_edicao_matricula)
                            dialog_escola.focus_force()
                            dialog_escola.grab_set()

                            # Frame principal
                            form_frame = Frame(dialog_escola, padx=20, pady=10, bg=co1)
                            form_frame.pack(fill=BOTH, expand=True)

                            # Título
                            Label(form_frame, text="Adicionar Nova Escola", 
                                  font=("Arial", 12, "bold"), bg=co1, fg=co7).pack(pady=(5, 15))

                            # Campos do formulário
                            Label(form_frame, text="Nome:", bg=co1, fg=co7).pack(anchor=W, pady=(5, 2))
                            nome_entry = Entry(form_frame, width=40, bg=co0)
                            nome_entry.pack(fill=X, pady=(0, 10))

                            Label(form_frame, text="Endereço:", bg=co1, fg=co7).pack(anchor=W, pady=(5, 2))
                            endereco_entry = Entry(form_frame, width=40, bg=co0)
                            endereco_entry.pack(fill=X, pady=(0, 10))

                            Label(form_frame, text="INEP:", bg=co1, fg=co7).pack(anchor=W, pady=(5, 2))
                            inep_entry = Entry(form_frame, width=40, bg=co0)
                            inep_entry.pack(fill=X, pady=(0, 10))

                            Label(form_frame, text="CNPJ:", bg=co1, fg=co7).pack(anchor=W, pady=(5, 2))
                            cnpj_entry = Entry(form_frame, width=40, bg=co0)
                            cnpj_entry.pack(fill=X, pady=(0, 10))

                            Label(form_frame, text="Município:", bg=co1, fg=co7).pack(anchor=W, pady=(5, 2))
                            municipio_entry = Entry(form_frame, width=40, bg=co0)
                            municipio_entry.pack(fill=X, pady=(0, 10))

                            def salvar_nova_escola():
                                try:
                                    nome = nome_entry.get().strip()
                                    if not nome:
                                        messagebox.showwarning("Aviso", "O nome da escola é obrigatório.")
                                        return
                                    
                                    # Inserir nova escola no banco de dados
                                    cursor.execute("""
                                        INSERT INTO escolas (nome, endereco, inep, cnpj, municipio)
                                        VALUES (%s, %s, %s, %s, %s)
                                    """, (
                                        nome,
                                        endereco_entry.get().strip(),
                                        inep_entry.get().strip(),
                                        cnpj_entry.get().strip(),
                                        municipio_entry.get().strip()
                                    ))
                                    conn.commit()
                                    
                                    # Obter o ID da escola recém-criada
                                    novo_id = cursor.lastrowid
                                    
                                    # Atualizar os comboboxes
                                    escolas_map[nome] = novo_id
                                    cb_escola_origem['values'] = [''] + list([e for e in escolas_map.keys() if e != ''])
                                    cb_escola_destino['values'] = [''] + list([e for e in escolas_map.keys() if e != ''])
                                    
                                    messagebox.showinfo("Sucesso", "Escola adicionada com sucesso!")
                                    dialog_escola.destroy()
                                except Exception as e:
                                    conn.rollback()
                                    messagebox.showerror("Erro", f"Erro ao adicionar escola: {str(e)}")

                            # Frame para botões
                            botoes_frame = Frame(form_frame, bg=co1)
                            botoes_frame.pack(fill=X, pady=10)

                            Button(botoes_frame, text="Salvar",
                                   command=salvar_nova_escola,
                                   bg=co3, fg=co1, width=15,
                                   font=('Ivy', 9, 'bold')).pack(side=LEFT, padx=5)
                            
                            Button(botoes_frame, text="Cancelar",
                                   command=dialog_escola.destroy,
                                   bg=co6, fg=co1, width=15,
                                   font=('Ivy', 9, 'bold')).pack(side=RIGHT, padx=5)

                        except Exception as e:
                            messagebox.showerror("Erro", f"Erro ao abrir formulário: {str(e)}")
                    
                    # Função para salvar alterações
                    def salvar_alteracoes_matricula():
                        nonlocal conn, cursor
                        try:
                            serie_nome = serie_var.get()
                            turma_nome = turma_var.get()
                            
                            if not serie_nome or serie_nome not in series_map:
                                messagebox.showwarning("Aviso", "Por favor, selecione uma série válida.")
                                return
                                
                            if not turma_nome or turma_nome not in turmas_map:
                                messagebox.showwarning("Aviso", "Por favor, selecione uma turma válida.")
                                return
                            
                            nova_turma_id = turmas_map[turma_nome]
                            
                            # Obter IDs das escolas selecionadas
                            escola_origem_nome = escola_origem_var.get()
                            escola_destino_nome = escola_destino_var.get()
                            
                            escola_origem_id = escolas_map.get(escola_origem_nome) if escola_origem_nome else None
                            escola_destino_id = escolas_map.get(escola_destino_nome) if escola_destino_nome else None
                            
                            # Registrar no histórico
                            cursor.execute("""
                                INSERT INTO historico_matricula 
                                (matricula_id, status_anterior, status_novo, data_mudanca)
                                VALUES (%s, 'Ativo', 'Ativo', CURDATE())
                            """, (matricula_id,))
                            
                            # Atualizar a matrícula
                            cursor.execute("""
                                UPDATE matriculas 
                                SET turma_id = %s,
                                    escola_origem_id = %s,
                                    escola_destino_id = %s
                                WHERE id = %s
                            """, (nova_turma_id, escola_origem_id, escola_destino_id, matricula_id))
                            
                            conn.commit()
                            messagebox.showinfo("Sucesso", "Matrícula atualizada com sucesso!")
                            
                            # Fechar janela de edição
                            janela_edicao_matricula.destroy()
                            
                            # Recarregar a interface de edição do aluno
                            janela_edicao.destroy()
                            abrir_edicao_aluno(janela_pai, aluno_id, treeview, query)
                            
                        except Exception as e:
                            conn.rollback()
                            messagebox.showerror("Erro", f"Erro ao atualizar matrícula: {str(e)}")
                    
                    # Botões
                    botoes_frame = Frame(frame_edicao, bg=co1)
                    botoes_frame.pack(fill=X, pady=20)
                    
                    # Botão para adicionar nova escola
                    Button(botoes_frame, text="➕ Nova Escola", 
                          command=adicionar_nova_escola,
                          font=('Ivy 9'), bg=co4, fg=co1, width=15).pack(side=LEFT, padx=5)
                    
                    Button(botoes_frame, text="Salvar", 
                          command=salvar_alteracoes_matricula,
                          font=('Ivy 10 bold'), bg=co3, fg=co0, width=15).pack(side=LEFT, padx=5)
                    
                    Button(botoes_frame, text="Cancelar", 
                          command=janela_edicao_matricula.destroy,
                          font=('Ivy 10'), bg=co6, fg=co0, width=15).pack(side=RIGHT, padx=5)
                
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao abrir interface de edição de matrícula: {str(e)}")
            
            def cancelar_matricula(matricula_id):
                nonlocal conn, cursor
                try:
                    # Registrar no histórico
                    cursor.execute("""
                        INSERT INTO historico_matricula 
                        (matricula_id, status_anterior, status_novo, data_mudanca)
                        VALUES (%s, 'Ativo', 'Cancelado', CURDATE())
                    """, (matricula_id,))
                    
                    # Atualizar status da matrícula
                    cursor.execute("""
                        UPDATE matriculas 
                        SET status = 'Cancelado' 
                        WHERE id = %s
                    """, (matricula_id,))
                    
                    conn.commit()
                    messagebox.showinfo("Sucesso", "Matrícula cancelada com sucesso!")
                    
                    # Recarregar a interface de edição do aluno
                    janela_edicao.destroy()
                    abrir_edicao_aluno(janela_pai, aluno_id, treeview, query)
                    
                except Exception as e:
                    conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao cancelar matrícula: {str(e)}")
            
            def atualizar_status_matricula(matricula_id, novo_status):
                nonlocal conn, cursor
                try:
                    # Registrar no histórico
                    cursor.execute("""
                        INSERT INTO historico_matricula 
                        (matricula_id, status_anterior, status_novo, data_mudanca)
                        VALUES (%s, 'Ativo', %s, CURDATE())
                    """, (matricula_id, novo_status))
                    
                    # Atualizar o status da matrícula
                    cursor.execute("""
                        UPDATE matriculas 
                        SET status = %s 
                        WHERE id = %s
                    """, (novo_status, matricula_id))
                    
                    conn.commit()
                    messagebox.showinfo("Sucesso", f"Status da matrícula atualizado para: {novo_status}")
                    
                    # Atualizar o status visual
                    status_label.config(text=f"Status da Matrícula: {novo_status.upper()}")
                    if novo_status == "Ativo":
                        status_label.config(fg=co3)
                    else:
                        status_label.config(fg=co6)
                        
                except Exception as e:
                    conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao atualizar status: {str(e)}")
            
            # Função para salvar as alterações dos dados do aluno
            def salvar_alteracoes():
                nonlocal conn, cursor
                try:
                    # Obter o ID da escola selecionada
                    escola_nome = c_escola.get()
                    escola_id = None
                    
                    for nome, id in escolas_map.items():
                        if nome == escola_nome:
                            escola_id = id
                            break
                    
                    if not escola_id:
                        messagebox.showerror("Erro", "Escola inválida ou não selecionada.")
                        return
                    
                    # Validar campos obrigatórios
                    nome = e_nome.get()
                    raca = c_raca.get()
                    
                    if not nome or not raca:
                        messagebox.showerror("Erro", "Os campos Nome e Raça são obrigatórios.")
                        return
                    
                    # Preparar os dados para atualização
                    data_nascimento = c_data_nascimento.get_date().strftime("%Y-%m-%d") if c_data_nascimento.get() else None
                    local_nascimento = e_local_nascimento.get()
                    uf_nascimento = c_uf_nascimento.get()
                    endereco = e_endereco.get()
                    sus = e_sus.get()
                    sexo = c_sexo.get()
                    cpf = e_cpf.get()
                    nis = e_nis.get()
                    descricao_transtorno = e_descricao_transtorno.get()
                    
                    # Atualizar o aluno no banco de dados
                    cursor.execute(
                        """
                        UPDATE alunos SET
                            nome = %s, data_nascimento = %s, local_nascimento = %s, UF_nascimento = %s,
                            endereco = %s, sus = %s, sexo = %s, cpf = %s, nis = %s, raca = %s, escola_id = %s, 
                            descricao_transtorno = %s
                        WHERE id = %s
                        """,
                        (
                            nome, data_nascimento, local_nascimento, uf_nascimento,
                            endereco, sus, sexo, cpf, nis, raca, escola_id, 
                            descricao_transtorno, aluno_id
                        )
                    )
                    
                    conn.commit()
                    messagebox.showinfo("Sucesso", "Dados do aluno atualizados com sucesso!")
                    
                    # Fechar a janela e atualizar a visualização
                    if cursor:
                        cursor.close()
                        cursor = None
                    
                    if conn:
                        conn.close()
                        conn = None
                    
                    janela_edicao.destroy()
                    
                    # Atualizar a tabela principal se treeview estiver disponível
                    if treeview is not None and query is not None:
                        atualizar_treeview(treeview, cursor, query)
                    
                except Exception as e:
                    conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao salvar alterações: {str(e)}")
            
            # Função para fechar a janela e liberar recursos
            def fechar_janela():
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
                janela_edicao.destroy()
            
            # Configurar ação de fechamento
            janela_edicao.protocol("WM_DELETE_WINDOW", fechar_janela)
            
            # Botões de ação
            botoes_frame = Frame(frame_principal, bg=co1, pady=10)
            botoes_frame.pack(fill=X)
            
            Button(botoes_frame, text="Salvar Alterações", 
                  command=salvar_alteracoes,
                  font=('Ivy 10 bold'), bg=co3, fg=co0, width=20).pack(side=LEFT, padx=5)
            
            Button(botoes_frame, text="Cancelar", 
                  command=fechar_janela,
                  font=('Ivy 10'), bg=co6, fg=co0, width=15).pack(side=RIGHT, padx=5)
            
            # ---- ABA DE RESPONSÁVEIS ----
            responsaveis_frame = Frame(aba_responsaveis, bg=co1, padx=20, pady=20)
            responsaveis_frame.pack(fill=BOTH, expand=True)
            
            # Frame para a lista de responsáveis
            lista_frame = Frame(responsaveis_frame, bg=co1)
            lista_frame.pack(fill=BOTH, expand=True)
            
            # Criar Treeview para listar responsáveis
            colunas = ('ID', 'Nome', 'Parentesco', 'Telefone', 'RG', 'CPF')
            tree_responsaveis = ttk.Treeview(lista_frame, columns=colunas, show='headings')
            
            # Configurar colunas
            for col in colunas:
                tree_responsaveis.heading(col, text=col)
                tree_responsaveis.column(col, width=100)
            
            # Adicionar scrollbar
            scrollbar = ttk.Scrollbar(lista_frame, orient=VERTICAL, command=tree_responsaveis.yview)
            tree_responsaveis.configure(yscrollcommand=scrollbar.set)
            
            # Posicionar elementos
            tree_responsaveis.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)
            
            # Frame para botões
            botoes_frame = Frame(responsaveis_frame, bg=co1)
            botoes_frame.pack(fill=X, pady=10)
            
            # Botões de ação
            Button(botoes_frame, text="Adicionar Responsável", 
                  command=lambda: adicionar_responsavel(aluno_id, tree_responsaveis),
                  font=('Ivy 10'), bg=co3, fg=co0).pack(side=LEFT, padx=5)
            
            Button(botoes_frame, text="Editar Responsável", 
                  command=lambda: editar_responsavel(aluno_id, tree_responsaveis),
                  font=('Ivy 10'), bg=co4, fg=co0).pack(side=LEFT, padx=5)
            
            Button(botoes_frame, text="Remover Responsável", 
                  command=lambda: remover_responsavel(aluno_id, tree_responsaveis),
                  font=('Ivy 10'), bg=co6, fg=co0).pack(side=LEFT, padx=5)
            
            # Função para carregar responsáveis
            def carregar_responsaveis():
                # Limpar a treeview
                for item in tree_responsaveis.get_children():
                    tree_responsaveis.delete(item)
                
                # Carregar responsáveis do aluno
                cursor.execute("""
                    SELECT r.id, r.nome, r.grau_parentesco, r.telefone, r.rg, r.cpf
                    FROM responsaveis r
                    JOIN responsaveisalunos ra ON r.id = ra.responsavel_id
                    WHERE ra.aluno_id = %s
                """, (aluno_id,))
                
                for responsavel in cursor.fetchall():
                    tree_responsaveis.insert('', 'end', values=responsavel)
            
            # Carregar responsáveis inicialmente
            carregar_responsaveis()
            
            # Função para adicionar responsável
            def adicionar_responsavel(aluno_id, tree):
                janela_responsavel = Toplevel(janela_edicao)
                janela_responsavel.title("Adicionar Responsável")
                janela_responsavel.geometry("400x500")
                janela_responsavel.configure(background=co1)
                janela_responsavel.transient(janela_edicao)
                janela_responsavel.focus_force()
                janela_responsavel.grab_set()
                
                # Frame principal
                frame = Frame(janela_responsavel, bg=co1, padx=20, pady=20)
                frame.pack(fill=BOTH, expand=True)
                
                # Campos do formulário
                Label(frame, text="Nome *", bg=co1, fg=co7).pack(anchor=W)
                e_nome = Entry(frame, width=40)
                e_nome.pack(fill=X, pady=(0, 10))
                
                Label(frame, text="Grau de Parentesco *", bg=co1, fg=co7).pack(anchor=W)
                e_parentesco = Entry(frame, width=40)
                e_parentesco.pack(fill=X, pady=(0, 10))
                
                Label(frame, text="Telefone", bg=co1, fg=co7).pack(anchor=W)
                e_telefone = Entry(frame, width=40)
                e_telefone.pack(fill=X, pady=(0, 10))
                
                Label(frame, text="RG", bg=co1, fg=co7).pack(anchor=W)
                e_rg = Entry(frame, width=40)
                e_rg.pack(fill=X, pady=(0, 10))
                
                Label(frame, text="CPF", bg=co1, fg=co7).pack(anchor=W)
                e_cpf = Entry(frame, width=40)
                e_cpf.pack(fill=X, pady=(0, 10))
                
                def salvar():
                    try:
                        # Validar campos obrigatórios
                        if not e_nome.get() or not e_parentesco.get():
                            messagebox.showerror("Erro", "Nome e grau de parentesco são obrigatórios.")
                            return
                        
                        # Inserir responsável
                        cursor.execute("""
                            INSERT INTO responsaveis (nome, grau_parentesco, telefone, rg, cpf)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (e_nome.get(), e_parentesco.get(), e_telefone.get(), e_rg.get(), e_cpf.get()))
                        
                        responsavel_id = cursor.lastrowid
                        
                        # Vincular responsável ao aluno
                        cursor.execute("""
                            INSERT INTO responsaveisalunos (responsavel_id, aluno_id)
                            VALUES (%s, %s)
                        """, (responsavel_id, aluno_id))
                        
                        conn.commit()
                        messagebox.showinfo("Sucesso", "Responsável adicionado com sucesso!")
                        
                        # Recarregar lista de responsáveis
                        carregar_responsaveis()
                        
                        # Fechar janela
                        janela_responsavel.destroy()
                        
                    except Exception as e:
                        conn.rollback()
                        messagebox.showerror("Erro", f"Erro ao adicionar responsável: {str(e)}")
                
                # Botões
                botoes_frame = Frame(frame, bg=co1)
                botoes_frame.pack(fill=X, pady=20)
                
                Button(botoes_frame, text="Salvar", 
                      command=salvar,
                      font=('Ivy 10 bold'), bg=co3, fg=co0).pack(side=LEFT, padx=5)
                
                Button(botoes_frame, text="Cancelar", 
                      command=janela_responsavel.destroy,
                      font=('Ivy 10'), bg=co6, fg=co0).pack(side=RIGHT, padx=5)
            
            # Função para editar responsável
            def editar_responsavel(aluno_id, tree):
                # Verificar se há item selecionado
                item = tree.selection()
                if not item:
                    messagebox.showwarning("Aviso", "Selecione um responsável para editar.")
                    return
                
                # Obter dados do responsável selecionado
                responsavel_id = tree.item(item[0])['values'][0]
                
                # Criar janela de edição
                janela_edicao_resp = Toplevel(janela_edicao)
                janela_edicao_resp.title("Editar Responsável")
                janela_edicao_resp.geometry("400x500")
                janela_edicao_resp.configure(background=co1)
                janela_edicao_resp.transient(janela_edicao)
                janela_edicao_resp.focus_force()
                janela_edicao_resp.grab_set()
                
                # Frame principal
                frame = Frame(janela_edicao_resp, bg=co1, padx=20, pady=20)
                frame.pack(fill=BOTH, expand=True)
                
                # Carregar dados do responsável
                cursor.execute("""
                    SELECT nome, grau_parentesco, telefone, rg, cpf
                    FROM responsaveis
                    WHERE id = %s
                """, (responsavel_id,))
                
                dados = cursor.fetchone()
                if not dados:
                    messagebox.showerror("Erro", "Responsável não encontrado.")
                    return
                
                # Campos do formulário
                Label(frame, text="Nome *", bg=co1, fg=co7).pack(anchor=W)
                e_nome = Entry(frame, width=40)
                e_nome.insert(0, str(dados[0]) if dados[0] else "")
                e_nome.pack(fill=X, pady=(0, 10))
                
                Label(frame, text="Grau de Parentesco *", bg=co1, fg=co7).pack(anchor=W)
                e_parentesco = Entry(frame, width=40)
                e_parentesco.insert(0, str(dados[1]) if dados[1] else "")
                e_parentesco.pack(fill=X, pady=(0, 10))
                
                Label(frame, text="Telefone", bg=co1, fg=co7).pack(anchor=W)
                e_telefone = Entry(frame, width=40)
                e_telefone.insert(0, str(dados[2]) if dados[2] else "")
                e_telefone.pack(fill=X, pady=(0, 10))
                
                Label(frame, text="RG", bg=co1, fg=co7).pack(anchor=W)
                e_rg = Entry(frame, width=40)
                e_rg.insert(0, str(dados[3]) if dados[3] else "")
                e_rg.pack(fill=X, pady=(0, 10))
                
                Label(frame, text="CPF", bg=co1, fg=co7).pack(anchor=W)
                e_cpf = Entry(frame, width=40)
                e_cpf.insert(0, str(dados[4]) if dados[4] else "")
                e_cpf.pack(fill=X, pady=(0, 10))
                
                def salvar():
                    try:
                        # Validar campos obrigatórios
                        if not e_nome.get() or not e_parentesco.get():
                            messagebox.showerror("Erro", "Nome e grau de parentesco são obrigatórios.")
                            return
                        
                        # Atualizar responsável
                        cursor.execute("""
                            UPDATE responsaveis 
                            SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s, cpf = %s
                            WHERE id = %s
                        """, (e_nome.get(), e_parentesco.get(), e_telefone.get(), e_rg.get(), e_cpf.get(), responsavel_id))
                        
                        conn.commit()
                        messagebox.showinfo("Sucesso", "Responsável atualizado com sucesso!")
                        
                        # Recarregar lista de responsáveis
                        carregar_responsaveis()
                        
                        # Fechar janela
                        janela_edicao_resp.destroy()
                        
                    except Exception as e:
                        conn.rollback()
                        messagebox.showerror("Erro", f"Erro ao atualizar responsável: {str(e)}")
                
                # Botões
                botoes_frame = Frame(frame, bg=co1)
                botoes_frame.pack(fill=X, pady=20)
                
                Button(botoes_frame, text="Salvar", 
                      command=salvar,
                      font=('Ivy 10 bold'), bg=co3, fg=co0).pack(side=LEFT, padx=5)
                
                Button(botoes_frame, text="Cancelar", 
                      command=janela_edicao_resp.destroy,
                      font=('Ivy 10'), bg=co6, fg=co0).pack(side=RIGHT, padx=5)
            
            # Função para remover responsável
            def remover_responsavel(aluno_id, tree):
                # Verificar se há item selecionado
                item = tree.selection()
                if not item:
                    messagebox.showwarning("Aviso", "Selecione um responsável para remover.")
                    return
                
                # Confirmar remoção
                if not messagebox.askyesno("Confirmação", "Tem certeza que deseja remover este responsável?"):
                    return
                
                try:
                    # Obter ID do responsável
                    responsavel_id = tree.item(item[0])['values'][0]
                    
                    # Remover vínculo com o aluno
                    cursor.execute("""
                        DELETE FROM responsaveisalunos
                        WHERE responsavel_id = %s AND aluno_id = %s
                    """, (responsavel_id, aluno_id))
                    
                    # Remover responsável
                    cursor.execute("""
                        DELETE FROM responsaveis
                        WHERE id = %s
                    """, (responsavel_id,))
                    
                    conn.commit()
                    messagebox.showinfo("Sucesso", "Responsável removido com sucesso!")
                    
                    # Recarregar lista de responsáveis
                    carregar_responsaveis()
                    
                except Exception as e:
                    conn.rollback()
                    messagebox.showerror("Erro", f"Erro ao remover responsável: {str(e)}")
    
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir interface de edição: {str(e)}")
        if cursor:
            cursor.close()
        if conn:
            conn.close() 