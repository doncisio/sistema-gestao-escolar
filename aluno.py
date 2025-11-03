from tkinter.ttk import *
from tkinter import *
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from PIL import Image, ImageTk
from datetime import datetime
from conexao import conectar_bd
import mysql.connector
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

def alunos(frame_detalhes, frame_dados, frame_tabela, treeview, query):
    # Configurar frames para expandir com a janela
    frame_detalhes.pack_propagate(False)
    frame_tabela.pack_propagate(False)
    
    # Lista global para armazenar os frames dos responsáveis
    global lista_frames_responsaveis, contador_responsaveis, responsaveis_removidos
    lista_frames_responsaveis = []
    contador_responsaveis = 0
    responsaveis_removidos = []
    
    # Lista de opções para campos de seleção
    opcoes_parentesco = ["Mãe", "Pai", "Tio", "Tia", "Avô", "Avó", "Outro"]
    opcoes_sexo = ["M", "F"]
    opcoes_status = ["Ativo", "Evadido", "Cancelado", "Transferido", "Concluído"]
    
    # Função para limpar os campos e voltar à tela principal
    def voltar_pagina_principal():
        # Importar a função voltar do main para evitar dependência circular
        import main
        main.voltar()
    
    # Criação do formulário no frame_detalhes
    # Configurar layout do frame_detalhes
    for i in range(5):  # 5 colunas
        frame_detalhes.grid_columnconfigure(i, weight=1)
    
    # Primeira linha - Nome e Data de Nascimento
    l_nome = Label(frame_detalhes, text="Nome *", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_nome.grid(row=0, column=0, columnspan=2, sticky=W, padx=10, pady=5)
    global e_nome
    e_nome = Entry(frame_detalhes, width=40, justify='left', relief='solid')
    e_nome.grid(row=0, column=0, columnspan=2, sticky=W, padx=10, pady=25)
    
    l_data_nascimento = Label(frame_detalhes, text="Data de Nascimento *", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_data_nascimento.grid(row=0, column=2, sticky=W, padx=10, pady=5)
    global c_data_nascimento
    c_data_nascimento = DateEntry(frame_detalhes, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    c_data_nascimento.grid(row=0, column=2, sticky=W, padx=10, pady=25)
    
    # Segunda linha - Endereço e Cartão SUS
    l_endereco = Label(frame_detalhes, text="Endereço", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_endereco.grid(row=1, column=0, columnspan=2, sticky=W, padx=10, pady=5)
    global e_endereco
    e_endereco = Entry(frame_detalhes, width=40, justify='left', relief='solid')
    e_endereco.grid(row=1, column=0, columnspan=2, sticky=W, padx=10, pady=25)
    
    l_sus = Label(frame_detalhes, text="Cartão SUS", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_sus.grid(row=1, column=2, sticky=W, padx=10, pady=5)
    global e_sus
    e_sus = Entry(frame_detalhes, width=20, justify='left', relief='solid')
    e_sus.grid(row=1, column=2, sticky=W, padx=10, pady=25)
    
    # Terceira linha - CPF, NIS e Sexo
    l_cpf = Label(frame_detalhes, text="CPF", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_cpf.grid(row=2, column=0, sticky=W, padx=10, pady=5)
    global e_cpf
    e_cpf = Entry(frame_detalhes, width=20, justify='left', relief='solid')
    e_cpf.grid(row=2, column=0, sticky=W, padx=10, pady=25)
    
    l_nis = Label(frame_detalhes, text="NIS", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_nis.grid(row=2, column=1, sticky=W, padx=10, pady=5)
    global e_nis
    e_nis = Entry(frame_detalhes, width=20, justify='left', relief='solid')
    e_nis.grid(row=2, column=1, sticky=W, padx=10, pady=25)
    
    l_sexo = Label(frame_detalhes, text="Sexo", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_sexo.grid(row=2, column=2, sticky=W, padx=10, pady=5)
    global c_sexo
    c_sexo = ttk.Combobox(frame_detalhes, width=10, values=opcoes_sexo)
    c_sexo.grid(row=2, column=2, sticky=W, padx=10, pady=25)
    
    l_local_nascimento = Label(frame_detalhes, text="Local de Nascimento", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_local_nascimento.grid(row=2, column=3, sticky=W, padx=10, pady=5)
    global e_local_nascimento
    e_local_nascimento = Entry(frame_detalhes, width=25, justify='left', relief='solid')
    e_local_nascimento.grid(row=2, column=3, sticky=W, padx=10, pady=25)
    
    # Quarta linha - UF Nascimento, Raça
    l_uf_nascimento = Label(frame_detalhes, text="UF Nascimento", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_uf_nascimento.grid(row=3, column=0, sticky=W, padx=10, pady=5)
    global e_uf_nascimento
    e_uf_nascimento = Entry(frame_detalhes, width=5, justify='left', relief='solid')
    e_uf_nascimento.grid(row=3, column=0, sticky=W, padx=10, pady=25)
    e_uf_nascimento.insert(0, "MA")  # Valor padrão
    
    l_raca = Label(frame_detalhes, text="Cor/Raça *", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_raca.grid(row=3, column=1, sticky=W, padx=10, pady=5)
    global c_raca
    c_raca = ttk.Combobox(frame_detalhes, width=15, values=["preto", "pardo", "branco", "indígena", "amarelo"])
    c_raca.grid(row=3, column=1, sticky=W, padx=10, pady=25)
    c_raca.set("pardo")  # Valor padrão
    
    # Quinta linha - Descrição do Transtorno
    l_descricao_transtorno = Label(frame_detalhes, text="Descrição do Transtorno", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_descricao_transtorno.grid(row=4, column=0, columnspan=3, sticky=W, padx=10, pady=5)
    global e_descricao_transtorno
    e_descricao_transtorno = Entry(frame_detalhes, width=50, justify='left', relief='solid')
    e_descricao_transtorno.grid(row=4, column=0, columnspan=3, sticky=W, padx=10, pady=25)
    e_descricao_transtorno.insert(0, "Nenhum")  # Valor padrão
    
    # Obter séries do banco de dados
    def obter_series():
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            
            # Consulta para obter séries vinculadas ao ano letivo atual
            cursor.execute("""
                SELECT s.id, s.nome 
                FROM serie s
                JOIN turmas t ON s.id = t.serie_id
                JOIN anosletivos a ON t.ano_letivo_id = a.id
                WHERE a.ano_letivo = YEAR(GETDATE())
                GROUP BY s.id, s.nome
            """)
            
            series = cursor.fetchall()
            if not series:  # Se não encontrar para o ano atual, tenta 2025
                cursor.execute("""
                    SELECT s.id, s.nome 
                    FROM serie s
                    JOIN turmas t ON s.id = t.serie_id
                    JOIN anosletivos a ON t.ano_letivo_id = a.id
                    WHERE a.ano_letivo = 2025
                    GROUP BY s.id, s.nome
                """)
                series = cursor.fetchall()
            
            cursor.close()
            conn.close()
            return series
        except mysql.connector.Error as err:
            print("Erro ao obter séries:", err)
            return []
    
    # Obter turmas com base na série selecionada
    def obter_turmas(serie_id):
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            
            # Consulta para obter turmas vinculadas à série e ao ano letivo
            cursor.execute("""
                SELECT t.id, t.nome, t.turno
                FROM turmas t
                JOIN anosletivos a ON t.ano_letivo_id = a.id
                WHERE t.serie_id = %s AND a.ano_letivo = 2025
                ORDER BY t.nome, t.turno
            """, (serie_id,))
            
            turmas = cursor.fetchall()
            cursor.close()
            conn.close()
            return turmas
        except mysql.connector.Error as err:
            print("Erro ao obter turmas:", err)
            return []
    
    # Evento de atualização das turmas quando a série é alterada
    def atualizar_turmas(event):
        serie_selecionada = c_serie.get()
        
        # Obter o ID da série selecionada
        serie_id = next((serie[0] for serie in series if serie[1] == serie_selecionada), None)
        if serie_id is None:
            return
        
        # Obter turmas para a série selecionada
        turmas = obter_turmas(serie_id)
        nomes_turmas = [f"{turma[1]} - {turma[2]}" for turma in turmas]
        
        # Armazenar o ID das turmas para uso posterior
        global turmas_ids
        turmas_ids = {f"{turma[1]} - {turma[2]}": turma[0] for turma in turmas}
        
        # Atualizar os valores da combobox de turmas
        c_turma['values'] = nomes_turmas
        c_turma.set('')
    
    # Evento de atualização do turno quando a turma é alterada
    def atualizar_turno(event):
        turma_selecionada = c_turma.get()
        if turma_selecionada and " - " in turma_selecionada:
            turno = turma_selecionada.split(" - ")[1]
            c_turno.set(turno)
    
    # Sexta linha - Série, Turma e Turno
    l_serie = Label(frame_detalhes, text="Série *", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_serie.grid(row=5, column=0, sticky=W, padx=10, pady=5)
    
    # Obter séries
    series = obter_series()
    series_nomes = [serie[1] for serie in series]
    
    global c_serie, c_turma, c_turno, turmas_ids
    c_serie = ttk.Combobox(frame_detalhes, width=25, values=series_nomes)
    c_serie.grid(row=5, column=0, sticky=W, padx=10, pady=25)
    c_serie.bind("<<ComboboxSelected>>", atualizar_turmas)
    
    l_turma = Label(frame_detalhes, text="Turma *", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_turma.grid(row=5, column=1, sticky=W, padx=10, pady=5)
    c_turma = ttk.Combobox(frame_detalhes, width=15)
    c_turma.grid(row=5, column=1, sticky=W, padx=10, pady=25)
    c_turma.bind("<<ComboboxSelected>>", atualizar_turno)
    
    l_turno = Label(frame_detalhes, text="Turno", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_turno.grid(row=5, column=2, sticky=W, padx=10, pady=5)
    c_turno = ttk.Combobox(frame_detalhes, width=10, values=["MAT", "VESP"], state="disabled")
    c_turno.grid(row=5, column=2, sticky=W, padx=10, pady=25)
    
    # Botão para avançar para o cadastro de responsáveis
    botao_responsavel = Button(frame_detalhes, text="Continuar para Responsáveis >>", height=2, 
                             bg=co3, fg=co1, font=('Ivy 10 bold'), relief=RAISED, overrelief=RIDGE,
                             command=responsavel)
    botao_responsavel.grid(row=6, column=0, columnspan=3, pady=10, padx=10, sticky=EW)
    
    # Função para criar interface de responsáveis
    def responsavel():
        # Remove o botão original de continuar cadastro
        for widget in frame_detalhes.winfo_children():
            if isinstance(widget, Button) and "Continuar para Responsáveis" in widget["text"]:
                widget.destroy()
        
        # Limpar o frame da tabela para adicionar os responsáveis
        for widget in frame_tabela.winfo_children():
            widget.destroy()
        
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
        
        # Adicionar botões no frame_dados
        for widget in frame_dados.winfo_children():
            widget.destroy()
        
        # Botão para voltar
        b_voltar = Button(frame_dados, text="<< Voltar", bg=co5, fg=co1, 
                        font=('Ivy 10'), relief=RAISED, overrelief=RIDGE,
                        command=voltar_pagina_principal)
        b_voltar.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Botão para adicionar novos responsáveis
        b_add_responsavel = Button(frame_dados, text="+ Adicionar Responsável", bg=co3, fg=co1, 
                                 font=('Ivy 10 bold'), relief=RAISED, overrelief=RIDGE, 
                                 command=add_responsavel)
        b_add_responsavel.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Botão para salvar
        b_salvar = Button(frame_dados, text="Salvar Aluno", bg=co7, fg=co1, 
                        font=('Ivy 10 bold'), relief=RAISED, overrelief=RIDGE,
                        command=lambda: salvar_aluno(treeview, query))
        b_salvar.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        
        # Adiciona o primeiro responsável automaticamente
        add_responsavel()
    
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
    
    # Função para salvar o aluno e seus responsáveis
    def salvar_aluno(treeview, query):
        # Validar campos obrigatórios
        nome = e_nome.get()
        data_nascimento = c_data_nascimento.get_date()
        cpf = e_cpf.get()
        sexo = c_sexo.get()
        raca = c_raca.get()
        serie = c_serie.get()
        turma = c_turma.get()
        
        if not nome or not cpf or not sexo or not raca or not serie or not turma:
            messagebox.showerror("Erro", "Preencha todos os campos obrigatórios (marcados com *).")
            return
        
        # Validar que há pelo menos um responsável
        if len(lista_frames_responsaveis) == 0:
            messagebox.showerror("Erro", "Adicione pelo menos um responsável.")
            return
        
        # Validar dados dos responsáveis
        for i, frame in enumerate(lista_frames_responsaveis, 1):
            nome_resp = frame.campos['nome'].get()
            cpf_resp = frame.campos['cpf'].get()
            
            if not nome_resp or not cpf_resp:
                messagebox.showerror("Erro", f"Preencha nome e CPF do Responsável {i}.")
                return
        
        try:
            # Conectar ao banco de dados
            conn = conectar_bd()
            cursor = conn.cursor()
            
            # Obter o ID da escola atual
            escola_id = 3  # Valor padrão, ajuste conforme necessário
            
            # Inserir o aluno
            data_nascimento_str = data_nascimento.strftime('%Y-%m-%d')
            local_nascimento = e_local_nascimento.get() or "Paço do Lumiar"
            uf_nascimento = e_uf_nascimento.get() or "MA"
            endereco = e_endereco.get() or ""
            sus = e_sus.get() or ""
            descricao_transtorno = e_descricao_transtorno.get() or "Nenhum"
            
            # Inserir o aluno
            cursor.execute("""
                INSERT INTO alunos 
                (nome, data_nascimento, local_nascimento, UF_nascimento, endereco, sus, sexo, cpf, nis, raca, 
                escola_id, descricao_transtorno)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nome, data_nascimento_str, local_nascimento, uf_nascimento, endereco, sus, sexo, cpf, e_nis.get(), raca, 
                escola_id, descricao_transtorno
            ))
            
            # Obter o ID do aluno inserido
            aluno_id = cursor.lastrowid
            
            # Obter o ID da turma selecionada
            turma_id = None
            if turmas_ids and turma in turmas_ids:
                turma_id = turmas_ids[turma]
            else:
                # Obter o ID do ano letivo atual (2025)
                cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2025")
                ano_letivo_id = cursor.fetchone()[0]
                
                # Obter o ID da série selecionada
                serie_id = next((s[0] for s in series if s[1] == serie), None)
                
                turno = c_turno.get()
                turma_nome = turma.split(" - ")[0] if " - " in turma else turma
                
                # Buscar a turma no banco de dados
                cursor.execute("""
                    SELECT id FROM turmas 
                    WHERE nome = %s AND serie_id = %s AND turno = %s AND ano_letivo_id = %s
                """, (turma_nome, serie_id, turno, ano_letivo_id))
                
                result = cursor.fetchone()
                if result:
                    turma_id = result[0]
            
            # Verificar se conseguiu obter o ID da turma
            if not turma_id:
                raise Exception("Não foi possível obter o ID da turma selecionada.")
            
            # Obter o ID do ano letivo (2025)
            cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2025")
            ano_letivo_id = cursor.fetchone()[0]
            
            # Inserir a matrícula
            data_atual = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO matriculas (aluno_id, turma_id, data_matricula, ano_letivo_id, status) 
                VALUES (%s, %s, %s, %s, %s)
            """, (aluno_id, turma_id, data_atual, ano_letivo_id, "Ativo"))
            
            # Inserir/atualizar responsáveis
            for frame in lista_frames_responsaveis:
                nome_resp = frame.campos['nome'].get()
                telefone = frame.campos['telefone'].get() or ""
                rg = frame.campos['rg'].get() or ""
                cpf_resp = frame.campos['cpf'].get()
                parentesco = frame.campos['parentesco'].get() or ""
                
                # Verificar se já existe um responsável com esse CPF
                cursor.execute("SELECT id FROM responsaveis WHERE cpf = %s", (cpf_resp,))
                responsavel_existente = cursor.fetchone()
                
                if responsavel_existente:
                    # Atualizar responsável existente
                    responsavel_id = responsavel_existente[0]
                    cursor.execute("""
                        UPDATE responsaveis 
                        SET nome = %s, telefone = %s, rg = %s, grau_parentesco = %s 
                        WHERE id = %s
                    """, (nome_resp, telefone, rg, parentesco, responsavel_id))
                else:
                    # Inserir novo responsável
                    cursor.execute("""
                        INSERT INTO responsaveis (nome, telefone, rg, cpf, grau_parentesco) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, (nome_resp, telefone, rg, cpf_resp, parentesco))
                    responsavel_id = cursor.lastrowid
                
                # Associar responsável ao aluno
                cursor.execute("""
                    INSERT INTO responsaveisalunos (responsavel_id, aluno_id) 
                    VALUES (%s, %s)
                """, (responsavel_id, aluno_id))
            
            # Commit das alterações
            conn.commit()
            
            # Atualizar a tabela na interface
            if treeview and treeview.winfo_exists():
                atualizar_treeview(treeview, cursor, query)
            
            messagebox.showinfo("Sucesso", "Aluno cadastrado com sucesso!")
            
            # Voltar para a tela principal
            voltar_pagina_principal()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao salvar no banco de dados: {err}")
            print(f"Erro MySQL: {err}")
            if conn:
                conn.rollback()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
            print(f"Erro geral: {e}")
            if conn:
                conn.rollback()
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

# Funções auxiliares para serem chamadas de outros módulos

def excluir_aluno(aluno_id, treeview, query):
    """Exclui um aluno do banco de dados e atualiza a treeview."""
    try:
        # Confirmar exclusão
        resposta = messagebox.askyesno("Confirmar Exclusão", 
                                     "Tem certeza que deseja excluir este aluno?\nEsta ação não pode ser desfeita.")
        if not resposta:
            return False
        
        # Conectar ao banco de dados
        conn = conectar_bd()
        cursor = conn.cursor()
        
        # Verificar se o aluno existe
        cursor.execute("SELECT nome FROM alunos WHERE id = %s", (aluno_id,))
        result = cursor.fetchone()
        if not result:
            messagebox.showerror("Erro", "Aluno não encontrado.")
            return False
        
        # Excluir associações com responsáveis
        cursor.execute("DELETE FROM responsaveisalunos WHERE aluno_id = %s", (aluno_id,))
        
        # Excluir matrículas
        cursor.execute("DELETE FROM matriculas WHERE aluno_id = %s", (aluno_id,))
        
        # Excluir o aluno
        cursor.execute("DELETE FROM alunos WHERE id = %s", (aluno_id,))
        
        # Commit das alterações
        conn.commit()
        
        # Não é mais necessário atualizar a treeview aqui, pois a função em main.py fará isso
        # Isso evita atualizações duplicadas e possíveis erros
        
        messagebox.showinfo("Sucesso", "Aluno excluído com sucesso!")
        
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao excluir aluno: {err}")
        print(f"Erro MySQL ao excluir aluno: {err}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao excluir aluno: {e}")
        print(f"Erro geral ao excluir aluno: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()
