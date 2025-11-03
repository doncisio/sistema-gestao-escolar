import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector

# Função para conectar ao banco de dados
def conectar_banco():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='seu_usuario',  # Substitua pelo seu usuário do MySQL
            password='sua_senha',  # Substitua pela sua senha do MySQL
            database='redeescola'  # Nome do seu banco de dados
        )
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {err}")
        return None

# Função para salvar nota no banco de dados
def salvar_nota():
    aluno_id = aluno_id_entry.get()
    disciplina_id = disciplina_id_entry.get()
    bimestre = bimestre_combobox.get()
    nota = nota_entry.get()
    
    if aluno_id and disciplina_id and bimestre and nota:
        try:
            nota = float(nota)  # Converte a nota para float
            conn = conectar_banco()  # Conecta ao banco usando a função importada
            cursor = conn.cursor()  # Cria um cursor para executar comandos
            
            cursor.execute("INSERT INTO notas (aluno_id, disciplina_id, bimestre, nota) VALUES (%s, %s, %s, %s)", 
                           (aluno_id, disciplina_id, bimestre, nota))
            conn.commit()  # Confirma as alterações no banco
            cursor.close()  # Fecha o cursor
            conn.close()  # Fecha a conexão
            messagebox.showinfo("Sucesso", "Nota salva com sucesso!")
            limpar_campos_nota()
            
            # Verifica se já existem 4 notas para calcular a média
            if len([n for n in notas if n['aluno_id'] == aluno_id and n['disciplina_id'] == disciplina_id]) == 4:
                calcular_media(aluno_id, disciplina_id)
        except ValueError:
            messagebox.showerror("Erro", "Por favor, insira uma nota válida.")
    else:
        messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")

def calcular_media(aluno_id, disciplina_id):
    # Coletar notas do banco de dados para calcular a média
    conn = conectar_banco()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nota FROM notas WHERE aluno_id = %s AND disciplina_id = %s", (aluno_id, disciplina_id))
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()

        notas_bimestrais = [resultado[0] for resultado in resultados]
        if len(notas_bimestrais) == 4:  # Verifica se há 4 notas
            media = sum(notas_bimestrais) / 4
            salvar_historico(aluno_id, disciplina_id, media)
            messagebox.showinfo("Média Calculada", f"Média para Aluno ID {aluno_id} na Disciplina ID {disciplina_id}: {media:.1f}")

def salvar_historico(aluno_id, disciplina_id, media):
    ano_letivo_id = ano_letivo_entry.get()  # Obter ano letivo de um campo de entrada
    escola_id = escola_id_entry.get()  # Obter escola ID de um campo de entrada
    conceito = conceito_combobox.get()  # Obter conceito de um combobox
    
    if ano_letivo_id and escola_id and conceito:  # Conectar ao banco e inserir no histórico escolar
        conn = conectar_banco()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO historico_escolar (aluno_id, disciplina_id, media, ano_letivo_id, escola_id, conceito) VALUES (%s, %s, %s, %s, %s, %s)", 
                           (aluno_id, disciplina_id, round(media, 1), ano_letivo_id, escola_id, conceito))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Sucesso", "Média salva no histórico escolar!")
    else:
        messagebox.showerror("Erro", "Ano letivo, Escola ID e Conceito devem ser preenchidos.")

def limpar_campos_nota():
    aluno_id_entry.delete(0, tk.END)
    disciplina_id_entry.delete(0, tk.END)
    bimestre_combobox.set('')
    nota_entry.delete(0, tk.END)

def salvar_disciplina():
    nome = disciplina_nome_entry.get()
    nivel_id = nivel_id_entry.get()
    carga_horaria = carga_horaria_entry.get()
    escola_id = escola_id_entry.get()

    if nome and nivel_id and carga_horaria and escola_id:
        try:
            carga_horaria = int(carga_horaria)
            disciplinas.append({
                'nome': nome,
                'nivel_id': nivel_id,
                'carga_horaria': carga_horaria,
                'escola_id': escola_id
            })  # Conectar ao banco e inserir a disciplina
            conn = conectar_banco()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO disciplinas (nome, nivel_id, carga_horaria, escola_id) VALUES (%s, %s, %s, %s)", 
                               (nome, nivel_id, carga_horaria, escola_id))
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo("Sucesso", "Disciplina salva com sucesso!")
                limpar_campos_disciplina()
        except ValueError:
            messagebox.showerror("Erro", "Carga horária deve ser um número inteiro.")
    else:
        messagebox.showerror("Erro", "Todos os campos devem ser preenchidos.")

def limpar_campos_disciplina():
    disciplina_nome_entry.delete(0, tk.END)
    nivel_id_entry.delete(0, tk.END)
    carga_horaria_entry.delete(0, tk.END)
    escola_id_entry.delete(0, tk.END)

def criar_interface():
    global aluno_id_entry, disciplina_id_entry, bimestre_combobox, nota_entry
    global ano_letivo_entry, escola_id_entry, conceito_combobox
    global disciplina_nome_entry, nivel_id_entry, carga_horaria_entry

    janela = tk.Tk()
    janela.title("Gestão Escolar")
    janela.geometry("850x670")
    
    # Seção para Notas
    tk.Label(janela, text="Notas").grid(row=0,columnspan=2)
    
    tk.Label(janela,text="Aluno ID:").grid(row=1,column=0)
    aluno_id_entry=tk.Entry(janela)
    aluno_id_entry.grid(row=1,column=1)

    tk.Label(janela,text="Disciplina ID:").grid(row=2,column=0)
    disciplina_id_entry=tk.Entry(janela)
    disciplina_id_entry.grid(row=2,column=1)

    tk.Label(janela,text="Bimestre:").grid(row=3,column=0)
    bimestre_combobox=tk.ttk.Combobox(janela,value=["1º bimestre","2º bimestre","3º bimestre","4º bimestre"])
    bimestre_combobox.grid(row=3,column=1)

    for i in range(4):
        tk.Label(janela,text=f"Nota {i+1} ({i+1}º Bimestre):").grid(row=4+i*2,column=0)
        nota_entry=tk.Entry(janela)
        nota_entry.grid(row=4+i*2,column=1)

    salvar_nota_button=tk.Button(janela,text="Salvar Notas",command=salvar_nota)
    salvar_nota_button.grid(row=12,columnspan=2)

    # Seção para Disciplinas
    tk.Label(janela,text="Disciplinas").grid(row=13,columnspan=2)
    
    tk.Label(janela,text="Nome:").grid(row=14,column=0)
    disciplina_nome_entry=tk.Entry(janela)
    disciplina_nome_entry.grid(row=14,column=1)

    tk.Label(janela,text="Nível ID:").grid(row=15,column=0)
    nivel_id_entry=tk.Entry(janela)
    nivel_id_entry.grid(row=15,column=1)

    tk.Label(janela,text="Carga Horária:").grid(row=16,column=0)
    carga_horaria_entry=tk.Entry(janela)
    carga_horaria_entry.grid(row=16,column=1)

    tk.Label(janela,text="Escola ID:").grid(row=17,column=0)
    escola_id_entry=tk.Entry(janela)
    escola_id_entry.grid(row=17,column=1)

    salvar_disciplina_button=tk.Button(janela,text="Salvar Disciplina",command=salvar_disciplina)
    salvar_disciplina_button.grid(row=18,columnspan=2)

    # Seção para Histórico Escolar
    tk.Label(janela,text="Histórico Escolar").grid(row=19,columnspan=2)

    tk.Label(janela,text="Ano Letivo:").grid(row=20,column=0)
    ano_letivo_entry=tk.Entry(janela)
    ano_letivo_entry.grid(row=20,column=1)

    tk.Label(janela,text="Conceito:").grid(row=21,column=0)
    conceito_combobox=tk.ttk.Combobox(janela,value=["RUIM","BOM","ÓTIMO"])
    conceito_combobox.grid(row=21,column=1)

    janela.mainloop()  # Executa a interface

# Execução da interface
if __name__ == "__main__":
   criar_interface()
