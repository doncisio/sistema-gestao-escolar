from tkinter import ttk, filedialog, messagebox, Frame, Label
from tkinter import *
import tkinter as tk
import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import mimetypes
from dotenv import load_dotenv
import webbrowser

class GerenciadorDocumentosSistema:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Documentos do Sistema")
        self.root.geometry("1200x700")
        
        # Definição das cores (mesmas da tela principal)
        self.co0 = "#F5F5F5"  # Branco suave para o fundo
        self.co1 = "#003A70"  # Azul escuro
        self.co2 = "#77B341"  # Verde
        self.co3 = "#E2418E"  # Rosa/Magenta
        self.co4 = "#4A86E8"  # Azul mais claro
        self.co5 = "#F26A25"  # Laranja
        self.co6 = "#F7B731"  # Amarelo
        self.co7 = "#333333"  # Cinza escuro
        self.co8 = "#BF3036"  # Vermelho
        self.co9 = "#6FA8DC"  # Azul claro
        
        # Configurar cores da janela
        self.root.configure(bg=self.co1)
        
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Configurações do Google Drive
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.service = None
        self.setup_google_drive()
        self.setup_database()
        
        self.create_widgets()
        self.carregar_documentos()
    
    def setup_google_drive(self):
        """Configura a autenticação com o Google Drive"""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def conectar_bd(self):
        """Conecta ao banco de dados usando variáveis de ambiente"""
        try:
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                auth_plugin='mysql_native_password'
            )
            if conn.is_connected():
                return conn
        except Error as e:
            messagebox.showerror(
                "Erro de Conexão", 
                f"Erro ao conectar com o banco de dados: {e}"
            )
            return None
    
    def setup_database(self):
        """Configura a conexão com o banco de dados"""
        self.conn = self.conectar_bd()
        if self.conn:
            self.cursor = self.conn.cursor()
        else:
            self.root.destroy()
    
    def create_widgets(self):
        """Cria os elementos da interface"""
        # Frame principal
        main_frame = Frame(self.root, bg=self.co1, padx=10, pady=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Título
        title_frame = Frame(main_frame, bg=self.co1)
        title_frame.pack(fill=X, pady=(0, 20))
        
        Label(title_frame, text="Gerenciador de Documentos do Sistema", 
              font=('Ivy', 16, 'bold'), bg=self.co1, fg=self.co0).pack()
        
        # Frame de filtros
        filter_frame = LabelFrame(main_frame, text="Filtros", padx=10, pady=10,
                                bg=self.co1, fg=self.co0, font=('Ivy', 10, 'bold'))
        filter_frame.pack(fill=X, pady=(0, 10))
        
        # Grid de filtros
        Label(filter_frame, text="Tipo:", bg=self.co1, fg=self.co0,
              font=('Ivy', 10)).grid(row=0, column=0, padx=5, pady=5)
        
        self.tipo_var = StringVar()
        self.tipo_combo = ttk.Combobox(filter_frame, textvariable=self.tipo_var, 
                                     width=30, font=('Ivy', 10))
        self.tipo_combo['values'] = (
            'Todos', 'Declaração', 'Boletim', 'Histórico Escolar', 
            'Lista Atualizada', 'Ata', 'Outros'
        )
        self.tipo_combo.grid(row=0, column=1, padx=5, pady=5)
        self.tipo_combo.set('Todos')
        
        Label(filter_frame, text="Data:", bg=self.co1, fg=self.co0,
              font=('Ivy', 10)).grid(row=0, column=2, padx=5, pady=5)
        
        self.data_var = StringVar()
        self.data_combo = ttk.Combobox(filter_frame, textvariable=self.data_var,
                                     width=20, font=('Ivy', 10))
        self.data_combo['values'] = (
            'Todos', 'Hoje', 'Últimos 7 dias', 'Último mês', 'Este ano'
        )
        self.data_combo.grid(row=0, column=3, padx=5, pady=5)
        self.data_combo.set('Todos')
        
        Button(filter_frame, text="Filtrar", command=self.carregar_documentos,
               font=('Ivy', 10), bg=self.co4, fg=self.co0,
               relief=RAISED, overrelief=RIDGE).grid(row=0, column=4, padx=5, pady=5)
        
        # Frame da tabela
        table_frame = Frame(main_frame, bg=self.co1)
        table_frame.pack(fill=BOTH, expand=True)
        
        # Configurar estilo da Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview",
                      background=self.co0,
                      foreground=self.co7,
                      fieldbackground=self.co0,
                      font=('Ivy', 10))
        style.configure("Custom.Treeview.Heading",
                      background=self.co1,
                      foreground=self.co0,
                      font=('Ivy', 10, 'bold'))
        
        # Criar Treeview
        columns = ('ID', 'Tipo', 'Nome Arquivo', 'Data Upload', 'Finalidade', 'Descrição', 'Aluno/Funcionário')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                style="Custom.Treeview", height=15)
        
        # Configurar colunas
        self.tree.heading('ID', text='ID')
        self.tree.heading('Tipo', text='Tipo')
        self.tree.heading('Nome Arquivo', text='Nome do Arquivo')
        self.tree.heading('Data Upload', text='Data de Upload')
        self.tree.heading('Finalidade', text='Finalidade')
        self.tree.heading('Descrição', text='Descrição')
        self.tree.heading('Aluno/Funcionário', text='Aluno/Funcionário')
        
        self.tree.column('ID', width=50)
        self.tree.column('Tipo', width=150)
        self.tree.column('Nome Arquivo', width=250)
        self.tree.column('Data Upload', width=150)
        self.tree.column('Finalidade', width=150)
        self.tree.column('Descrição', width=250)
        self.tree.column('Aluno/Funcionário', width=200)
        
        # Scrollbars
        yscroll = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        # Layout da tabela e scrollbars
        self.tree.grid(row=0, column=0, sticky=NSEW)
        yscroll.grid(row=0, column=1, sticky=NS)
        xscroll.grid(row=1, column=0, sticky=EW)
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Frame de botões (sempre visível na parte inferior)
        button_frame = Frame(main_frame, bg=self.co1)
        button_frame.pack(fill=X, pady=(10, 0), side=BOTTOM)
        
        Button(button_frame, text="Abrir Documento", command=self.abrir_documento,
               font=('Ivy', 10, 'bold'), bg=self.co2, fg=self.co0, width=18,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        
        Button(button_frame, text="Excluir Documento", command=self.excluir_documento,
               font=('Ivy', 10, 'bold'), bg=self.co8, fg=self.co0, width=18,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        
        Button(button_frame, text="Atualizar Lista", command=self.carregar_documentos,
               font=('Ivy', 10, 'bold'), bg=self.co4, fg=self.co0, width=18,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
    
    def carregar_documentos(self):
        """Carrega os documentos com base nos filtros selecionados"""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Erro", "Sem conexão com o banco de dados.")
            return
        
        try:
            # Limpar tabela
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Construir a query base
            query = """
                SELECT 
                    d.id, 
                    d.tipo_documento, 
                    d.nome_arquivo, 
                    d.data_de_upload, 
                    d.finalidade, 
                    d.descricao,
                    COALESCE(a.nome, '') as nome_aluno,
                    COALESCE(f.nome, '') as nome_funcionario
                FROM documentos_emitidos d
                LEFT JOIN alunos a ON d.aluno_id = a.id
                LEFT JOIN funcionarios f ON d.funcionario_id = f.id
                WHERE 1=1
            """
            params = []
            
            # Adicionar filtro de tipo
            if self.tipo_var.get() != 'Todos':
                query += " AND tipo_documento = %s"
                params.append(self.tipo_var.get())
            
            # Adicionar filtro de data
            data_filtro = self.data_var.get()
            if data_filtro != 'Todos':
                if data_filtro == 'Hoje':
                    query += " AND DATE(data_de_upload) = CURDATE()"
                elif data_filtro == 'Últimos 7 dias':
                    query += " AND data_de_upload >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
                elif data_filtro == 'Último mês':
                    query += " AND data_de_upload >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
                elif data_filtro == 'Este ano':
                    query += " AND YEAR(data_de_upload) = YEAR(CURDATE())"
            
            query += " ORDER BY data_de_upload DESC"
            
            # Executar a query
            self.cursor.execute(query, params)
            documentos = self.cursor.fetchall()
            
            # Preencher a tabela
            for doc in documentos:
                id_doc, tipo, nome, data, finalidade, descricao, nome_aluno, nome_funcionario = doc
                # Formatar a data
                if data:
                    data = data.strftime('%d/%m/%Y %H:%M')
                # Definir pessoa relacionada
                pessoa = nome_aluno if nome_aluno else nome_funcionario
                self.tree.insert('', 'end', values=(
                    id_doc, tipo, nome, data, 
                    finalidade if finalidade else '',
                    descricao if descricao else '',
                    pessoa if pessoa else ''
                ))
            
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar documentos: {e}")
    
    def abrir_documento(self):
        """Abre o documento selecionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Por favor, selecione um documento.")
            return
        
        try:
            item = self.tree.item(selected[0])
            doc_id = item['values'][0]
            
            # Buscar link do documento
            self.cursor.execute(
                "SELECT link_no_drive FROM documentos_emitidos WHERE id = %s",
                (doc_id,)
            )
            resultado = self.cursor.fetchone()
            
            if resultado and resultado[0]:
                webbrowser.open(resultado[0])
            else:
                messagebox.showwarning(
                    "Aviso", 
                    "Link do documento não encontrado no Google Drive."
                )
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir documento: {e}")
    
    def excluir_documento(self):
        """Exclui o documento selecionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Por favor, selecione um documento.")
            return
        
        try:
            item = self.tree.item(selected[0])
            doc_id = item['values'][0]
            nome_arquivo = item['values'][2]
            
            # Confirmar exclusão
            if not messagebox.askyesno(
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir o documento '{nome_arquivo}'?"
            ):
                return
            
            # Buscar link do Drive
            self.cursor.execute(
                "SELECT link_no_drive FROM documentos_emitidos WHERE id = %s",
                (doc_id,)
            )
            resultado = self.cursor.fetchone()
            
            if resultado and resultado[0]:
                # Extrair ID do arquivo do Drive do link
                drive_id = resultado[0].split('/')[-2]
                try:
                    # Tentar excluir do Drive
                    self.service.files().delete(fileId=drive_id).execute()
                except Exception as e:
                    print(f"Erro ao excluir do Drive: {e}")
            
            # Excluir do banco de dados
            self.cursor.execute(
                "DELETE FROM documentos_emitidos WHERE id = %s",
                (doc_id,)
            )
            self.conn.commit()
            
            # Atualizar a tabela
            self.carregar_documentos()
            
            messagebox.showinfo(
                "Sucesso",
                f"Documento '{nome_arquivo}' excluído com sucesso!"
            )
            
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Erro", f"Erro ao excluir documento: {e}")
    
    def __del__(self):
        """Fecha a conexão com o banco ao destruir o objeto"""
        if hasattr(self, 'conn') and self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()

def main():
    try:
        root = tk.Tk()
        app = GerenciadorDocumentosSistema(root)
        root.mainloop()
    except Exception as e:
        print(f"Erro ao iniciar aplicação: {e}")
        messagebox.showerror("Erro", f"Erro ao iniciar aplicação: {e}")

if __name__ == "__main__":
    main()