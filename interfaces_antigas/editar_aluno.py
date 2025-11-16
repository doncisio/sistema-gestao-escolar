from config_logs import get_logger
logger = get_logger(__name__)
from datetime import datetime
from tkinter import messagebox, ttk
from tkinter import *
import mysql.connector
from mysql.connector import Error
from conexao import conectar_bd
from tkcalendar import DateEntry
from Seguranca import atualizar_treeview

# Cores
co0 = "#2e2d2b"  # preta
co1 = "#feffff"  # Branca
co2 = "#e5e5e5"  # Cinza
co3 = "#00a095"  # Verde 
co4 = "#403d3d"  # Letra
co5 = "#003452"  # Azul
co6 = "#ef5350"  # Vermelho
co7 = "#038cfc"  # azul
co8 = "#263238"  # +verde
co9 = "#e9edf5"  # +verde

# Variável global para armazenar o ID da turma selecionada
selected_turma_id = None

def editar_aluno(frame_detalhes, frame_dados, frame_tabela, treeview, query, aluno_id):
    # Lista global para armazenar os frames dos responsáveis
    global lista_frames_responsaveis, contador_responsaveis, opcoes_parentesco
    lista_frames_responsaveis = []
    contador_responsaveis = 0
    opcoes_parentesco = ["Mãe", "Pai", "Tio", "Tia", "Avô", "Avó", "Outro"]
    
    # Configurar frames para expandir com a janela
    frame_detalhes.pack_propagate(False)
    frame_tabela.pack_propagate(False)
    
    # Função para carregar os dados do aluno no formulário
    def carregar_dados_aluno():
        try:
            conn = conectar_bd()
            cursor = conn.cursor(buffered=True)  # Usando buffered=True para evitar "Unread result found"

            # 1. Pesquisar turma_id na tabela Matriculas usando aluno_id
            cursor.execute("SELECT turma_id FROM matriculas WHERE aluno_id = %s", (aluno_id,))
            turma_id_result = cursor.fetchone()  # Lê o resultado da consulta
            turma_id = turma_id_result[0] if turma_id_result else None

            if turma_id:
                # 2. Pesquisar turno e serie_id na tabela Turmas usando turma_id
                cursor.execute("SELECT turno, serie_id FROM turmas WHERE id = %s", (turma_id,))
                turma_info = cursor.fetchone()  # Lê o resultado da consulta
                if turma_info:
                    turno, serie_id = turma_info

                    # 3. Pesquisar nome na tabela Series usando serie_id
                    cursor.execute("SELECT nome FROM serie WHERE id = %s", (serie_id,))
                    serie = cursor.fetchone()  # Lê o resultado da consulta
                    if serie:
                        serie_nome = serie[0]
                    else:
                        serie_nome = "Desconhecida"
                else:
                    turno = "Desconhecido" 
                    serie_nome = "Desconhecida"

            # Carregar dados do aluno
            cursor.execute("SELECT nome, endereco, cpf, sus, sexo, data_nascimento, raca FROM alunos WHERE id = %s", (aluno_id,))
            aluno = cursor.fetchone()  # Lê o resultado da consulta
            if aluno:
                e_nome.delete(0, END)
                e_nome.insert(0, str(aluno[0]))  # Nome
                e_endereco.delete(0, END)
                e_endereco.insert(0, str(aluno[1]))  # Endereço
                e_cpf.delete(0, END)
                e_cpf.insert(0, str(aluno[2]))  # CPF
                e_sus.delete(0, END)
                e_sus.insert(0, str(aluno[3]))  # SUS
                c_sexo.set(str(aluno[4]))  # Sexo
                c_data_nascimento.delete(0, END)
                c_data_nascimento.set_date(datetime.strptime(str(aluno[5]), "%Y-%m-%d").date())  # Data de Nascimento
                c_raca.set(str(aluno[6]))  # Raça
                c_turno.set(turno)  # Turno
                c_serie.set(serie_nome)  # Série

            # Carregar dados dos responsáveis
            cursor.execute(
                "SELECT r.id, r.nome, r.grau_parentesco, r.telefone, r.rg, r.cpf "
                "FROM responsaveis r "
                "JOIN responsaveisalunos ra ON r.id = ra.responsavel_id "
                "JOIN alunos a ON ra.aluno_id = a.id "
                "WHERE a.id = %s", 
                (aluno_id,)
            )
            responsaveis = cursor.fetchall()  # Lê todos os resultados da consulta

            # Criar a interface para os responsáveis
            criar_interface_responsaveis()
            
            # Preencher os dados dos responsáveis existentes
            for responsavel in responsaveis:
                resp_id, resp_nome, resp_parentesco, resp_telefone, resp_rg, resp_cpf = responsavel
                
                # Criar um novo frame para o responsável
                frame_resp = add_responsavel()
                
                # Preencher os campos
                frame_resp.campos['nome'].insert(0, resp_nome if resp_nome else "")
                frame_resp.campos['telefone'].insert(0, resp_telefone if resp_telefone else "")
                frame_resp.campos['rg'].insert(0, resp_rg if resp_rg else "")
                frame_resp.campos['cpf'].insert(0, resp_cpf if resp_cpf else "")
                frame_resp.campos['parentesco'].set(resp_parentesco if resp_parentesco else "")
                
                # Armazenar o ID do responsável no frame para uso posterior
                frame_resp.responsavel_id = resp_id

            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            logger.error("Erro ao carregar dados do aluno: %s", err)
    
    # Função para criar a interface de responsáveis
    def criar_interface_responsaveis():
        # Criando um frame para abrigar a lista de responsáveis
        global frame_lista_responsaveis
        frame_lista_responsaveis = Frame(frame_tabela, bg=co1)
        frame_lista_responsaveis.pack(fill=BOTH, expand=True)
        
        # Criando um canvas com scrollbar para os responsáveis
        canvas = Canvas(frame_lista_responsaveis, bg=co1)
        scrollbar = ttk.Scrollbar(frame_lista_responsaveis, orient="vertical", command=canvas.yview)
        
        # Frame interno para os responsáveis
        global frame_responsaveis
        frame_responsaveis = Frame(canvas, bg=co1)
        
        # Configurando o canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Criando uma janela no canvas para o frame
        canvas_frame = canvas.create_window((0, 0), window=frame_responsaveis, anchor="nw")
        
        # Configurando o evento de redimensionamento
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        frame_responsaveis.bind("<Configure>", on_frame_configure)
        
        # Função para ajustar o tamanho da janela do canvas quando o frame mudar
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Botão para adicionar novos responsáveis no frame_dados
        b_add_responsavel = Button(frame_dados, text="Adicionar Responsável", bg=co3, fg=co1, 
                                  font=('Ivy 10 bold'), relief=RAISED, overrelief=RIDGE, 
                                  command=add_responsavel)
        b_add_responsavel.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

    # Função para adicionar um novo responsável
    def add_responsavel():
        global contador_responsaveis
        contador_responsaveis += 1
        
        # Criando um frame para cada responsável
        frame_resp = Frame(frame_responsaveis, bg=co2, bd=1, relief="solid")
        frame_resp.pack(fill=X, expand=True, padx=5, pady=5)
        
        # Configurar o layout do frame responsável para ser responsivo
        for i in range(4):  # 4 colunas
            frame_resp.grid_columnconfigure(i, weight=1)
        
        # Adicionando o frame à lista para controle
        lista_frames_responsaveis.append(frame_resp)
        
        # Título do responsável
        l_titulo = Label(frame_resp, text=f"Responsável {contador_responsaveis}", height=1, 
                        anchor=NW, font=('Ivy 12 bold'), bg=co2, fg=co4)
        l_titulo.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Botão para remover o responsável
        b_remover = Button(frame_resp, text="Remover", bg=co6, fg=co1, 
                           font=('Ivy 8'), relief=RAISED, overrelief=RIDGE, 
                           command=lambda f=frame_resp: remover_responsavel(f))
        b_remover.grid(row=0, column=3, padx=5, pady=5, sticky="e")
        
        # Campos do responsável
        # Nome
        l_nome_resp = Label(frame_resp, text="Nome do Responsável *", height=1, anchor=NW, 
                          font=('Ivy 10'), bg=co2, fg=co4)
        l_nome_resp.grid(row=1, column=0, sticky="w", padx=10, pady=2)
        e_nome_resp = Entry(frame_resp, justify='left', relief='solid')
        e_nome_resp.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        
        # Telefone
        l_telefone = Label(frame_resp, text="Telefone", height=1, anchor=NW, 
                          font=('Ivy 10'), bg=co2, fg=co4)
        l_telefone.grid(row=1, column=1, sticky="w", padx=10, pady=2)
        e_telefone = Entry(frame_resp, justify='left', relief='solid')
        e_telefone.grid(row=2, column=1, sticky="ew", padx=10, pady=2)
        
        # RG
        l_rg = Label(frame_resp, text="RG", height=1, anchor=NW, 
                    font=('Ivy 10'), bg=co2, fg=co4)
        l_rg.grid(row=1, column=2, sticky="w", padx=10, pady=2)
        e_rg = Entry(frame_resp, justify='left', relief='solid')
        e_rg.grid(row=2, column=2, sticky="ew", padx=10, pady=2)
        
        # CPF
        l_cpf = Label(frame_resp, text="CPF *", height=1, anchor=NW, 
                     font=('Ivy 10'), bg=co2, fg=co4)
        l_cpf.grid(row=1, column=3, sticky="w", padx=10, pady=2)
        e_cpf = Entry(frame_resp, justify='left', relief='solid')
        e_cpf.grid(row=2, column=3, sticky="ew", padx=10, pady=2)
        
        # Parentesco
        l_parentesco = Label(frame_resp, text="Parentesco", height=1, anchor=NW, 
                            font=('Ivy 10'), bg=co2, fg=co4)
        l_parentesco.grid(row=3, column=0, sticky="w", padx=10, pady=2)
        c_parentesco = ttk.Combobox(frame_resp, values=opcoes_parentesco)
        c_parentesco.grid(row=4, column=0, sticky="ew", padx=10, pady=2)
        
        # Armazenando as entradas no frame para recuperação posterior
        frame_resp.campos = {
            'nome': e_nome_resp,
            'telefone': e_telefone,
            'rg': e_rg,
            'cpf': e_cpf,
            'parentesco': c_parentesco
        }
        
        # Inicializando o ID do responsável (se é um novo responsável)
        frame_resp.responsavel_id = None
        
        # Atualiza a região de rolagem do canvas
        frame_responsaveis.update_idletasks()
        
        return frame_resp

    # Função para remover um responsável
    def remover_responsavel(frame):
        if len(lista_frames_responsaveis) > 1:  # Garantir que haja pelo menos um responsável
            lista_frames_responsaveis.remove(frame)
            frame.destroy()
            reordenar_responsaveis()
        else:
            messagebox.showwarning("Aviso", "É necessário manter pelo menos um responsável!")

    # Função para reordenar os títulos dos responsáveis após remoção
    def reordenar_responsaveis():
        for i, frame in enumerate(lista_frames_responsaveis, 1):
            for widget in frame.winfo_children():
                if isinstance(widget, Label) and "Responsável" in widget.cget("text"):
                    widget.config(text=f"Responsável {i}")
                    break

    # Função para salvar as alterações do aluno
    def salvar_aluno():
        try:
            conn = conectar_bd()
            if not conn:
                raise Exception("Falha ao conectar ao banco de dados.")

            cursor = conn.cursor(buffered=True)

            # Coletar os dados do formulário
            nome = e_nome.get()
            endereco = e_endereco.get()
            cpf = e_cpf.get()
            sus = e_sus.get()
            sexo = c_sexo.get()
            data_nascimento = c_data_nascimento.get_date().strftime("%Y-%m-%d")  # Formato MySQL
            raca = c_raca.get()

            # Validar campos obrigatórios
            if not nome or not cpf:
                messagebox.showerror("Erro", "Os campos 'Nome' e 'CPF' são obrigatórios.")
                return

            # Validar e formatar a data
            try:
                data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Erro", "Formato de data inválido. Use o formato AAAA-MM-DD.")
                return

            # Atualizar os dados do aluno no banco de dados
            cursor.execute(
                """
                UPDATE alunos 
                SET nome = %s, endereco = %s, cpf = %s, sus = %s, sexo = %s, data_nascimento = %s, raca = %s 
                WHERE id = %s
                """,
                (nome, endereco, cpf, sus, sexo, data_nascimento, raca, aluno_id)
            )
            conn.commit()

            # Atualizar o Treeview (se necessário)
            if treeview and treeview.winfo_exists():
                atualizar_treeview(treeview, cursor, query)

            cursor.close()
            conn.close()

            messagebox.showinfo("Sucesso", "Dados do aluno salvos com sucesso.")
        except mysql.connector.Error as err:
            logger.error("Erro ao salvar dados do aluno: %s", err)
            messagebox.showerror("Erro", f"Não foi possível salvar os dados do aluno: {err}")
        except Exception as err:
            logger.error("Erro geral ao salvar dados do aluno: %s", err)
            messagebox.showerror("Erro", f"Erro inesperado: {err}")

    # Função para salvar as alterações dos responsáveis
    def salvar_responsaveis():
        try:
            conn = conectar_bd()
            cursor = conn.cursor(buffered=True)

            # Função auxiliar para salvar ou atualizar um único responsável
            def salvar_ou_atualizar_responsavel(frame):
                campos = frame.campos
                nome = campos['nome'].get()
                telefone = campos['telefone'].get()
                rg = campos['rg'].get()
                cpf = campos['cpf'].get()
                parentesco = campos['parentesco'].get()
                responsavel_id = getattr(frame, 'responsavel_id', None)
                
                if not nome:  # Se o nome estiver vazio, não processa
                    return None

                if responsavel_id:  # Responsável existente, atualizar
                    cursor.execute(
                        """
                        UPDATE responsaveis 
                        SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s, cpf = %s
                        WHERE id = %s
                        """,
                        (nome, parentesco, telefone, rg, cpf, responsavel_id)
                    )
                    return responsavel_id
                else:  # Novo responsável, inserir
                    # Verificar se já existe um responsável com esse CPF
                    if cpf:
                        cursor.execute("SELECT id FROM responsaveis WHERE cpf = %s", (cpf,))
                        resp_existente = cursor.fetchone()
                        if resp_existente:
                            responsavel_id = resp_existente[0]
                            # Atualizar os dados
                            cursor.execute(
                                """
                                UPDATE responsaveis 
                                SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s
                                WHERE id = %s
                                """,
                                (nome, parentesco, telefone, rg, responsavel_id)
                            )
                            return responsavel_id
                    
                    # Inserir novo responsável
                    cursor.execute(
                        """
                        INSERT INTO responsaveis (nome, grau_parentesco, telefone, rg, cpf)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (nome, parentesco, telefone, rg, cpf)
                    )
                    return cursor.lastrowid

            # Para cada responsável na lista, salvar ou atualizar
            for frame in lista_frames_responsaveis:
                responsavel_id = salvar_ou_atualizar_responsavel(frame)
                
                if responsavel_id:
                    # Verificar se a associação já existe
                    cursor.execute(
                        "SELECT id FROM responsaveisalunos WHERE responsavel_id = %s AND aluno_id = %s",
                        (responsavel_id, aluno_id)
                    )
                    if not cursor.fetchone():
                        # Associar o responsável ao aluno
                        cursor.execute(
                            "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                            (responsavel_id, aluno_id)
                        )

            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Sucesso", "Dados dos responsáveis salvos com sucesso!")
        except mysql.connector.Error as err:
            logger.error("Erro ao salvar dados dos responsáveis: %s", err)
            messagebox.showerror("Erro", f"Não foi possível salvar os dados dos responsáveis: {err}")
            
    # Função para salvar tudo (aluno e responsáveis)
    def salvar_tudo():
        try:
            # Chamar a função para salvar os dados do aluno
            salvar_aluno()

            # Chamar a função para salvar os dados dos responsáveis
            salvar_responsaveis()

            messagebox.showinfo("Sucesso", "Dados do aluno e dos responsáveis salvos com sucesso!")
        except Exception as err:
            logger.error("Erro ao salvar dados: %s", err)
            messagebox.showerror("Erro", "Não foi possível salvar os dados.")

    # Configura o gerenciador de layout do frame_dados
    frame_dados.grid_columnconfigure(0, weight=1)
    frame_dados.grid_columnconfigure(1, weight=1)
    frame_dados.grid_columnconfigure(2, weight=1)

    # Configura o gerenciador de layout do frame_detalhes
    for i in range(4):  # 4 colunas
        frame_detalhes.grid_columnconfigure(i, weight=1)
    for i in range(8):  # 8 linhas
        frame_detalhes.grid_rowconfigure(i, weight=1)

    # Interface de edição do aluno usando grid
    l_nome = Label(frame_detalhes, text="Nome *", bg=co1, fg=co4)
    l_nome.grid(row=0, column=0, sticky=W, padx=10, pady=5)
    e_nome = Entry(frame_detalhes, width=35, justify='left', relief='solid')
    e_nome.grid(row=0, column=0, sticky=W, padx=10, pady=25)

    l_endereco = Label(frame_detalhes, text="Endereço", bg=co1, fg=co4)
    l_endereco.grid(row=1, column=0, sticky=W, padx=10, pady=5)
    e_endereco = Entry(frame_detalhes, width=35, justify='left', relief='solid')
    e_endereco.grid(row=1, column=0, sticky=W, padx=10, pady=25)

    l_sus = Label(frame_detalhes, text="Cartão SUS", bg=co1, fg=co4)
    l_sus.grid(row=2, column=0, sticky=W, padx=10, pady=5)
    e_sus = Entry(frame_detalhes, width=20, justify='left', relief='solid')
    e_sus.grid(row=2, column=0, sticky=W, padx=10, pady=25)

    l_sexo = Label(frame_detalhes, text="Sexo", bg=co1, fg=co4)
    l_sexo.grid(row=2, column=1, sticky=W, padx=10, pady=5)
    c_sexo = ttk.Combobox(frame_detalhes, width=12, values=('M', 'F'))
    c_sexo.grid(row=2, column=1, sticky=W, padx=10, pady=25)

    l_data_nascimento = Label(frame_detalhes, text="Data de Nascimento", bg=co1, fg=co4)
    l_data_nascimento.grid(row=0, column=2, sticky=W, padx=10, pady=5)
    c_data_nascimento = DateEntry(
        frame_detalhes,
        width=14,
        background='darkblue',
        foreground='white',
        borderwidth=2,
        date_pattern='yyyy-mm-dd'  # Define o formato da data
    )
    c_data_nascimento.grid(row=0, column=2, sticky=W, padx=10, pady=25)

    l_cpf = Label(frame_detalhes, text="CPF *", bg=co1, fg=co4)
    l_cpf.grid(row=1, column=2, sticky=W, padx=10, pady=5)
    e_cpf = Entry(frame_detalhes, width=16, justify='left', relief='solid')
    e_cpf.grid(row=1, column=2, sticky=W, padx=10, pady=25)
    
    # Função para fechar o calendário após selecionar a data
    def fechar_calendario(event):
        c_data_nascimento._top_cal.withdraw()  # Fecha o calendário

    # Vincula o evento de seleção de data à função
    c_data_nascimento.bind("<<DateEntrySelected>>", fechar_calendario)

    def obter_series():
        try:
            conn = conectar_bd()
            if not conn:
                return []
            cursor = conn.cursor()

            # Consulta para obter séries vinculadas ao ano letivo 2025
            cursor.execute("""
                SELECT s.id, s.nome 
                FROM serie s
                JOIN turmas t ON s.id = t.serie_id
                JOIN anosletivos a ON t.ano_letivo_id = a.id
                WHERE a.ano_letivo = %s
                GROUP BY s.id, s.nome
            """, (2025,))
            series = cursor.fetchall()
            cursor.close()
            conn.close()
            logger.info("Séries obtidas: %s", series)
            return series
        except mysql.connector.Error as err:
            logger.error("Erro ao obter séries: %s", err)
            return []

    def obter_turmas(serie_id):
        try:
            conn = conectar_bd()
            if not conn:
                return []
            cursor = conn.cursor()

            # Consulta para obter turmas vinculadas à série e ao ano letivo 2025
            cursor.execute("""
                SELECT t.nome, t.turno 
                FROM turmas t
                JOIN anosletivos a ON t.ano_letivo_id = a.id
                WHERE t.serie_id = %s AND a.ano_letivo = %s
            """, (serie_id, 2025))
            turmas = cursor.fetchall()
            cursor.close()
            conn.close()
            logger.info(f"Turmas obtidas para a série {serie_id}:", turmas)
            return turmas
        except mysql.connector.Error as err:
            logger.error("Erro ao obter turmas:", err)
            return []

    def obter_turno(turma_nome, serie_id):
        try:
            conn = conectar_bd()
            if not conn:
                return []
            cursor = conn.cursor()

            # Consulta para obter turnos vinculados à turma, série e ano letivo 2025
            if turma_nome:
                cursor.execute("""
                    SELECT t.turno 
                    FROM turmas t
                    JOIN anosletivos a ON t.ano_letivo_id = a.id
                    WHERE t.nome = %s AND t.serie_id = %s AND a.ano_letivo = %s
                """, (turma_nome, serie_id, 2025))
            else:
                cursor.execute("""
                    SELECT DISTINCT t.turno 
                    FROM turmas t
                    JOIN anosletivos a ON t.ano_letivo_id = a.id
                    WHERE t.serie_id = %s AND a.ano_letivo = %s
                """, (serie_id, 2025))
            turnos = cursor.fetchall()
            cursor.close()
            conn.close()
            logger.info(f"Turnos obtidos para a turma {turma_nome if turma_nome else 'vazia'}:", [turno[0] for turno in turnos])
            return [turno[0] for turno in turnos]
        except mysql.connector.Error as err:
            logger.error("Erro ao obter turno:", err)
            return []

    def atualizar_turmas(event):
        serie_selecionada = c_serie.get()
        logger.info("Série selecionada:", serie_selecionada)

        # Obter o ID da série selecionada
        serie_id = next((serie[0] for serie in series if serie[1] == serie_selecionada), None)
        if serie_id is None:
            logger.info("Série não encontrada.")
            return

        # Obter turmas para a série selecionada
        turmas = obter_turmas(serie_id)
        nomes_turmas = [turma[0] for turma in turmas if turma[0]]

        # Atualizar os valores da combobox de turmas
        c_turma['values'] = nomes_turmas
        c_turma.set('')
        c_turno.set('')
        logger.info("Turmas atualizadas.")

        if not nomes_turmas:
            atualizar_turno(None)

    def atualizar_turno(event):
        global selected_turma_id

        serie_selecionada = c_serie.get()
        turma_selecionada = c_turma.get()
        logger.info("Turma selecionada:", turma_selecionada)

        # Obter o ID da série selecionada
        serie_id = next((serie[0] for serie in series if serie[1] == serie_selecionada), None)
        if serie_id is None:
            logger.info("Série não encontrada.")
            return

        try:
            conn = conectar_bd()
            if not conn:
                return
            cursor = conn.cursor()

            # Consulta para obter o ID da turma selecionada
            cursor.execute("""
                SELECT t.id 
                FROM turmas t
                JOIN anosletivos a ON t.ano_letivo_id = a.id
                WHERE t.nome = %s AND t.serie_id = %s AND a.ano_letivo = %s
            """, (turma_selecionada, serie_id, 2025))
            result = cursor.fetchone()
            selected_turma_id = result[0] if result else None
            logger.info("Turma ID:", selected_turma_id)

            cursor.close()
            conn.close()

            # Obter turnos para a turma selecionada
            turnos = obter_turno(turma_selecionada, serie_id)
            if turnos:
                c_turno['values'] = turnos 
                c_turno.set(turnos[0] if len(turnos) == 1 else '')
            else:
                c_turno['values'] = []
                c_turno.set('')
            logger.info("Turno atualizado.")
        except mysql.connector.Error as err:
            logger.error("Erro ao atualizar turno:", err)

    def obter_racas():
        try:
            conn = conectar_bd()
            if not conn:
                return []
            cursor = conn.cursor()
            cursor.execute("SHOW COLUMNS FROM alunos LIKE 'raca'")
            result = cursor.fetchone()[1]
            if isinstance(result, bytes):
                result = result.decode()
            racas = result.strip("enum()").replace("'", "").split(",")
            cursor.close()
            conn.close()
            logger.info("Raças obtidas do banco de dados:", racas)
            return racas
        except mysql.connector.Error as err:
            logger.error("Erro ao obter raças:", err)
            return []

    # Pegando as séries
    series = obter_series()
    series_nomes = [serie[1] for serie in series]

    l_serie = Label(frame_detalhes, text="Série", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_serie.grid(row=2, column=2, sticky=W, padx=10, pady=5)
    c_serie = ttk.Combobox(frame_detalhes, width=16, font=('Ivy 8 bold'))
    c_serie['values'] = series_nomes
    c_serie.grid(row=2, column=2, sticky=W, padx=10, pady=25)
    c_serie.bind("<<ComboboxSelected>>", atualizar_turmas)

    # Pegando as turmas
    l_turma = Label(frame_detalhes, text="Turma", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_turma.grid(row=2, column=3, sticky=W, padx=10, pady=5)
    c_turma = ttk.Combobox(frame_detalhes, width=10, font=('Ivy 8 bold'))
    c_turma.grid(row=2, column=3, sticky=W, padx=10, pady=25)
    c_turma.bind("<<ComboboxSelected>>", atualizar_turno)

    # Pegando os turnos
    l_turno = Label(frame_detalhes, text="Turno", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_turno.grid(row=3, column=3, sticky=W, padx=10, pady=5)
    c_turno = ttk.Combobox(frame_detalhes, width=10, font=('Ivy 8 bold'))
    c_turno.grid(row=3, column=3, sticky=W, padx=10, pady=25)

    # Adicionando Raças
    racas = obter_racas()
    logger.info("Raças obtidas para o combobox:", racas)

    l_raca = Label(frame_detalhes, text="Cor/Raça".upper(), height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_raca.grid(row=3, column=0, sticky=W, padx=10, pady=5)
    c_raca = ttk.Combobox(frame_detalhes, width=16, font=('Ivy 8 bold'))
    c_raca['values'] = racas
    c_raca.grid(row=3, column=0, sticky=W, padx=10, pady=25)

    botao_salvar = Button(frame_dados, text="Salvar Aluno", command=salvar_tudo)
    botao_salvar.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

    # Carregar dados do aluno
    carregar_dados_aluno()

# Função para atualizar a matrícula no banco de dados
def atualizar_matricula(aluno_id, nova_turma_id):
    try:
        conn = conectar_bd()
        cursor = conn.cursor()

        # Atualiza a turma_id na tabela Matriculas para o aluno especificado
        cursor.execute("UPDATE matriculas SET turma_id = %s WHERE aluno_id = %s AND status = 'Ativo'", (nova_turma_id, aluno_id))
        conn.commit()

        cursor.close()
        conn.close()

        messagebox.showinfo("Sucesso", "Turma atualizada com sucesso na matrícula do aluno!")
    except mysql.connector.Error as err:
        logger.error("Erro ao atualizar a matrícula do aluno:", err)
        messagebox.showerror("Erro", "Não foi possível atualizar a matrícula do aluno.")