from datetime import datetime
from tkinter import messagebox, Label, Entry, Button, END, NW
import tkinter.ttk as ttk
import mysql.connector
from mysql.connector import Error
from Seguranca import atualizar_treeview
from conexao import conectar_bd
from PIL import ImageTk, Image
from tkcalendar import DateEntry
from tkinter import filedialog as fd
from typing import Any, cast
from config_logs import get_logger

logger = get_logger(__name__)

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
c09 = "#e9edf5"  # +verde

def novo_funcionario(frame_detalhes, treeview, query):
    global e_nomef, c_cargof, c_polivalente, data_nascimentof, e_cpff, c_telefonef

    # criando campos de entrada
    l_nomef = Label(frame_detalhes, text="Nome *", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_nomef.place(x=4, y=10)
    e_nomef = Entry(frame_detalhes, width=35, justify='left', relief='solid')
    e_nomef.place(x=7, y=40)

    l_cargof = Label(frame_detalhes, text="Cargo", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_cargof.place(x=4, y=70)

    # Criando a combobox para o campo Cargo
    cargos = ['Administrador do Sistemas','Gestor Escolar','Professor@','Auxiliar administrativo','Agente de Portaria','Merendeiro','Auxiliar de serviços gerais','Técnico em Administração Escolar','Especialista (Coordenadora)','Tutor/Cuidador']
    c_cargof = ttk.Combobox(frame_detalhes, values=cargos, width=35, state='readonly')
    c_cargof.place(x=7, y=100)

    l_polivalente = Label(frame_detalhes, text="Polivalente", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_polivalente.place(x=4, y=130)

    # Criando a combobox para o campo Polivalente
    polivalente_opcoes = ['sim', 'não']
    c_polivalente = ttk.Combobox(frame_detalhes, values=polivalente_opcoes, width=20, state='readonly')
    c_polivalente.place(x=7, y=160)
    c_polivalente.set('não')  # Valor padrão

    l_data_nascimentof = Label(frame_detalhes, text="Data de Nascimento", height=1, anchor=NW, font=('Ivy 10'), bg=co1,
                               fg=co4)
    l_data_nascimentof.place(x=446, y=10)
    data_nascimentof = DateEntry(frame_detalhes, width=14, background='darkblue', foreground='white', borderwidth=2,
                                 year=2024)
    data_nascimentof.place(x=450, y=40)

    l_cpff = Label(frame_detalhes, text="CPF *", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_cpff.place(x=446, y=70)
    e_cpff = Entry(frame_detalhes, width=16, justify='left', relief='solid')
    e_cpff.place(x=450, y=100)

    l_telefonef = Label(frame_detalhes, text="Telefone", height=1, anchor=NW, font=('Ivy 10'), bg=co1, fg=co4)
    l_telefonef.place(x=446, y=130)
    c_telefonef = Entry(frame_detalhes, width=20, justify='left', relief='solid')
    c_telefonef.place(x=450, y=160)

    # Função para habilitar/desabilitar o campo Polivalente baseado na seleção de Cargo
    def atualizar_polivalente(event):
        if c_cargof.get() == 'Professor@':
            c_polivalente.config(state='readonly')
        else:
            c_polivalente.config(state='disabled')

    # Vinculando a função ao evento de seleção da combobox Cargo
    c_cargof.bind('<<ComboboxSelected>>', atualizar_polivalente)

    # Desabilitando a combobox Polivalente inicialmente
    c_polivalente.config(state='disabled')

    # Botão para salvar o funcionário
    b_salvar = Button(frame_detalhes, text="Salvar", command=lambda: salvar_funcionario(treeview, query), width=20)
    b_salvar.place(x=450, y=200)

def salvar_funcionario(treeview, query):
    nome = e_nomef.get()
    cargo = c_cargof.get()
    polivalente = c_polivalente.get()
    data_nascimento_str = data_nascimentof.get()
    cpf = e_cpff.get()
    telefone = c_telefonef.get()

    # Tente converter a string de data para o formato correto
    try:
        data_nascimento = datetime.strptime(data_nascimento_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        messagebox.showerror("Erro", "Formato de data inválido. Use DD/MM/YYYY.")
        return

    # Conectando ao banco de dados
    conn = conectar_bd()
    if not conn:
        messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
        logger.error("Não foi possível conectar ao banco de dados.")
        return

    try:
        cursor = cast(Any, conn).cursor()

        # Inserir o funcionário
        cursor.execute("""
            INSERT INTO Funcionarios (nome, cargo, polivalente, data_nascimento, cpf, telefone)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nome, cargo, polivalente, data_nascimento, cpf, telefone))

        # Confirmar as alterações
        conn.commit()
        # Atualizar a Treeview
        atualizar_treeview(treeview, cursor, query)
        messagebox.showinfo("Sucesso", "Funcionário inserido com sucesso.")
        logger.info("Funcionário inserido com sucesso.")

    except mysql.connector.Error as e:
        logger.exception("Erro ao salvar funcionário: %s", e)
        messagebox.showerror("Erro", f"Erro ao salvar funcionário: {e}")
        conn.rollback()

def gerar_declaracao_funcionario(id_funcionario):
    # Implementação da função para gerar a declaração do funcionário
    pass

def carregar_funcionario_para_edicao(id_funcionario):
    global e_nomef, c_cargof, c_polivalente, data_nascimentof, e_cpff, c_telefonef

    # Conectando ao banco de dados
    conn = conectar_bd()
    if not conn:
        messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
        return

    try:
        cursor = cast(Any, conn).cursor()
        
        # Buscar os dados do funcionário no banco de dados pelo id
        cursor.execute("SELECT nome, cargo, polivalente, data_nascimento, cpf, telefone FROM Funcionarios WHERE id = %s", (id_funcionario,))
        funcionario = cursor.fetchone()

        if funcionario:
            # Preencher os campos com os dados do funcionário
            e_nomef.delete(0, END)
            e_nomef.insert(END, str(funcionario[0]) if funcionario[0] is not None else "")

            c_cargof.set(funcionario[1])

            c_polivalente.set(funcionario[2])
            
            data_nascimentof.set_date(funcionario[3])  # Preenchendo campo DateEntry com a data
            
            e_cpff.delete(0, END)
            e_cpff.insert(END, str(funcionario[4]) if funcionario[4] is not None else "")

            c_telefonef.delete(0, END)
            c_telefonef.insert(END, str(funcionario[5]) if funcionario[5] is not None else "")

        else:
            messagebox.showerror("Erro", "Funcionário não encontrado.")
        
    except mysql.connector.Error as e:
        messagebox.showerror("Erro", f"Erro ao carregar dados do funcionário: {e}")
    
    finally:
        cursor.close()
        conn.close()

def atualizar_funcionario(id_funcionario, treeview, query):
    nome = e_nomef.get()
    cargo = c_cargof.get()
    polivalente = c_polivalente.get()
    data_nascimento_str = data_nascimentof.get()
    cpf = e_cpff.get()
    telefone = c_telefonef.get()

    # Verificar se os campos obrigatórios estão preenchidos
    if not nome or not cpf:
        messagebox.showerror("Erro", "Os campos Nome e CPF são obrigatórios.")
        return

    try:
        data_nascimento = datetime.strptime(data_nascimento_str, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        messagebox.showerror("Erro", "Formato de data inválido. Use DD/MM/YYYY.")
        return

    # Conectar ao banco de dados
    conn = conectar_bd()
    if not conn:
        messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
        return

    try:
        cursor = cast(Any, conn).cursor()

        # Comando SQL para atualizar os dados do funcionário
        cursor.execute("""
            UPDATE Funcionarios
            SET nome = %s, cargo = %s, polivalente = %s, data_nascimento = %s, cpf = %s, telefone = %s
            WHERE id = %s
        """, (nome, cargo, polivalente, data_nascimento, cpf, telefone, id_funcionario))

        # Confirmar a alteração
        conn.commit()

        # Atualizar a Treeview com os novos dados
        atualizar_treeview(treeview, cursor, query)

        messagebox.showinfo("Sucesso", "Funcionário atualizado com sucesso.")

    except mysql.connector.Error as e:
        messagebox.showerror("Erro", f"Erro ao atualizar o funcionário: {e}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

def exibir_funcionario_para_edicao(id_funcionario, frame_detalhes, treeview, query):
    # Carregar os dados do funcionário selecionado nos campos de entrada
    carregar_funcionario_para_edicao(id_funcionario)

    # Alterar o texto do botão de salvar para "Atualizar"
    b_atualizar = Button(frame_detalhes, text="Atualizar", command=lambda: atualizar_funcionario(id_funcionario, treeview, query), width=20)
    b_atualizar.place(x=450, y=200)