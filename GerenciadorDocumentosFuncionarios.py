import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Frame, Label, Entry, Button, LabelFrame, RAISED, RIDGE, END
import mysql.connector
from mysql.connector import Error
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle
import webbrowser
from datetime import datetime
from typing import Any, cast
from dotenv import load_dotenv
from config_logs import get_logger

logger = get_logger(__name__)

class GerenciadorDocumentosFuncionarios:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Documentos de Funcionários")
        self.root.geometry("900x700")
        
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
        
        # Configurações
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.service = None
        self.setup_google_drive()
        self.setup_database()
        
        self.create_widgets()
        self.load_funcionarios()
    
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
                if not os.path.exists('credentials.json'):
                    messagebox.showerror(
                        "Erro de Configuração", 
                        "Arquivo 'credentials.json' não encontrado!\n\n"
                        "Para usar o Google Drive, você precisa:\n"
                        "1. Acessar https://console.cloud.google.com/\n"
                        "2. Criar um projeto\n"
                        "3. Habilitar Google Drive API\n"
                        "4. Criar credenciais OAuth 2.0\n"
                        "5. Baixar o arquivo credentials.json\n"
                        "6. Colocar na mesma pasta deste script"
                    )
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive configurado com sucesso!")
    
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
                logger.info("Conexão com o banco estabelecida com sucesso!")
                return conn
        except Error as e:
            messagebox.showerror(
                "Erro de Conexão", 
                f"Erro ao conectar com o banco de dados: {e}\n\n"
                "Verifique se:\n"
                "1. O MySQL está rodando\n"
                "2. As credenciais no arquivo .env estão corretas\n"
                "3. O banco 'redeescola' existe"
            )
            return None
    
    def setup_database(self):
        """Configura a conexão com o banco de dados"""
        self.conn = self.conectar_bd()
        if self.conn:
            self.cursor = self.conn.cursor()
        else:
            # Se não conseguiu conectar, fecha a aplicação
            self.root.destroy()
    
    def create_widgets(self):
        """Cria os elementos da interface"""
        # Frame principal
        main_frame = Frame(self.root, bg=self.co1, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky='nsew')
        
        # Título
        title_label = Label(main_frame, text="Gerenciador de Documentos de Funcionários", 
                          font=('Ivy', 16, 'bold'), bg=self.co1, fg=self.co0)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Frame de upload
        upload_frame = LabelFrame(main_frame, text="Upload de Documento", padx=10, pady=10,
                                bg=self.co1, fg=self.co0, font=('Ivy', 10, 'bold'))
        upload_frame.grid(row=1, column=0, columnspan=3, sticky='we', pady=(0, 10))
        
        # Seleção de funcionário
        Label(upload_frame, text="Funcionário:", bg=self.co1, fg=self.co0,
              font=('Ivy', 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.funcionario_var = tk.StringVar()
        self.funcionario_combo = ttk.Combobox(upload_frame, textvariable=self.funcionario_var, 
                                            width=40, font=('Ivy', 10))
        self.funcionario_combo.grid(row=0, column=1, sticky='we', pady=5, padx=(5, 0))
        
        # Descrição do documento
        Label(upload_frame, text="Descrição:", bg=self.co1, fg=self.co0,
              font=('Ivy', 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.descricao_entry = Entry(upload_frame, width=40, font=('Ivy', 10), bg=self.co0)
        self.descricao_entry.grid(row=1, column=1, sticky='we', pady=5, padx=(5, 0))
        
        # Tipo de documento
        Label(upload_frame, text="Tipo:", bg=self.co1, fg=self.co0,
              font=('Ivy', 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.tipo_var = tk.StringVar()
        self.tipo_combo = ttk.Combobox(upload_frame, textvariable=self.tipo_var, 
                                      width=40, font=('Ivy', 10))
        self.tipo_combo['values'] = ('Contrato', 'RG', 'CPF', 'Comprovante de Endereço', 
                                   'Diploma', 'Certificado', 'Outros')
        self.tipo_combo.grid(row=2, column=1, sticky='we', pady=5, padx=(5, 0))
        
        # Botão para selecionar arquivo
        Button(upload_frame, text="Selecionar Arquivo", command=self.selecionar_arquivo,
               font=('Ivy', 10), bg=self.co4, fg=self.co0,
               relief=RAISED, overrelief=RIDGE).grid(row=3, column=0, pady=10)
        
        self.arquivo_label = Label(upload_frame, text="Nenhum arquivo selecionado",
                                 bg=self.co1, fg="gray", font=('Ivy', 10))
        self.arquivo_label.grid(row=3, column=1, sticky=tk.W, pady=10, padx=(5, 0))
        
        # Botão para upload
        Button(upload_frame, text="Fazer Upload", command=self.fazer_upload,
               font=('Ivy', 10), bg=self.co2, fg=self.co0,
               relief=RAISED, overrelief=RIDGE).grid(row=4, column=0, columnspan=2, pady=10)
        
        # Frame de documentos
        docs_frame = LabelFrame(main_frame, text="Documentos do Funcionário", padx=10, pady=10,
                              bg=self.co1, fg=self.co0, font=('Ivy', 10, 'bold'))
        docs_frame.grid(row=2, column=0, columnspan=3, sticky='nsew', pady=(10, 0))
        
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
        
        # Treeview para mostrar documentos
        columns = ('ID', 'Nome', 'Tipo', 'Data Upload', 'Descrição')
        self.tree = ttk.Treeview(docs_frame, columns=columns, show='headings',
                                height=12, style="Custom.Treeview")
        
        # Definindo cabeçalhos e larguras
        self.tree.heading('ID', text='ID')
        self.tree.column('ID', width=50)
        self.tree.heading('Nome', text='Nome do Arquivo')
        self.tree.column('Nome', width=200)
        self.tree.heading('Tipo', text='Tipo')
        self.tree.column('Tipo', width=120)
        self.tree.heading('Data Upload', text='Data Upload')
        self.tree.column('Data Upload', width=120)
        self.tree.heading('Descrição', text='Descrição')
        self.tree.column('Descrição', width=250)
        
        self.tree.grid(row=0, column=0, columnspan=3, sticky='nsew')
        
        # Scrollbar para a treeview
        scrollbar = ttk.Scrollbar(docs_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=3, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Frame de botões (sempre visível na parte inferior)
        buttons_frame = Frame(docs_frame, bg=self.co1)
        buttons_frame.grid(row=1, column=0, columnspan=4, pady=10, sticky='we')
        
        # Botão para carregar documentos
        Button(buttons_frame, text="Carregar Documentos", command=self.carregar_documentos,
               font=('Ivy', 10, 'bold'), bg=self.co4, fg=self.co0, width=20,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").grid(row=0, column=0, padx=5, pady=5)
        
        # Botão para abrir documento
        Button(buttons_frame, text="Abrir no Drive", command=self.abrir_documento,
               font=('Ivy', 10, 'bold'), bg=self.co2, fg=self.co0, width=20,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").grid(row=0, column=1, padx=5, pady=5)
        
        # Botão para excluir documento
        Button(buttons_frame, text="Excluir Documento", command=self.excluir_documento,
               font=('Ivy', 10, 'bold'), bg=self.co8, fg=self.co0, width=20,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").grid(row=0, column=2, padx=5, pady=5)
        
        # Botão para atualizar lista de funcionários
        Button(buttons_frame, text="Atualizar Funcionários", command=self.load_funcionarios,
               font=('Ivy', 10, 'bold'), bg=self.co5, fg=self.co0, width=20,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").grid(row=0, column=3, padx=5, pady=5)
        
        # Configurar weights para responsividade
        upload_frame.columnconfigure(1, weight=1)
        docs_frame.columnconfigure(0, weight=1)
        docs_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Variáveis de controle
        self.arquivo_selecionado = None
        self.funcionario_id = None
    
    def load_funcionarios(self):
        """Carrega a lista de funcionários do banco de dados"""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Erro", "Sem conexão com o banco de dados.")
            return
        
        try:
            # Primeiro, vamos verificar se a tabela funcionarios existe
            self.cursor.execute("""
                SELECT id, nome FROM funcionarios 
                ORDER BY nome
            """)
            funcionarios = self.cursor.fetchall()
            
            # Criar dicionário para mapear nome para ID
            self.funcionarios_map = {}
            nomes = []
            
            for func_id, nome in funcionarios:
                self.funcionarios_map[nome] = func_id
                nomes.append(nome)
            
            self.funcionario_combo['values'] = nomes
            
                if nomes:
                    self.funcionario_combo.set(nomes[0])
                    logger.info("Carregados %d funcionários", len(nomes))
                    self.carregar_documentos()  # Carrega documentos automaticamente
                else:
                    logger.info("Nenhum funcionário encontrado na base de dados")
                    messagebox.showinfo("Info", "Nenhum funcionário cadastrado no sistema.")
                
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar funcionários: {e}")
            logger.exception("Erro ao carregar funcionários: %s", e)
    
    def selecionar_arquivo(self):
        """Seleciona um arquivo para upload"""
        arquivo = filedialog.askopenfilename(
            title="Selecionar Documento",
            filetypes=[
                ("Todos os arquivos", "*.*"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx *.doc"),
                ("Imagens", "*.jpg *.jpeg *.png *.gif"),
                ("Texto", "*.txt")
            ]
        )
        
        if arquivo:
            self.arquivo_selecionado = arquivo
            nome_arquivo = os.path.basename(arquivo)
            self.arquivo_label.config(text=nome_arquivo, foreground="black")
    
    def get_or_create_drive_folder(self, folder_name, parent_id=None):
        """Obtém o ID de uma pasta no Google Drive ou cria se não existir"""
        # Garantir que o serviço do Drive esteja configurado
        if not self.service:
            messagebox.showerror("Erro", "Serviço do Google Drive não configurado.")
            return None

        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            else:
                # Criar nova pasta
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    file_metadata['parents'] = [parent_id]
                
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                logger.info("Pasta criada no Drive: %s (ID: %s)", folder_name, file.get('id'))
                return file.get('id')
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao acessar/criar pasta no Drive: {e}")
            return None

    def upload_para_drive(self, file_path, file_name):
        """Faz upload do arquivo para o Google Drive dentro da pasta do funcionário"""
        # Proteção: garantir serviço do Drive configurado
        if not self.service:
            messagebox.showerror("Erro", "Serviço do Google Drive não configurado.")
            return None, None

        try:
            # 1️⃣ Pasta principal "Documentos Funcionários"
            main_folder_id = self.get_or_create_drive_folder("Documentos Funcionários")

            # 2️⃣ Nome do funcionário (para criar a subpasta)
            funcionario_nome = self.funcionario_var.get()
            if not funcionario_nome:
                messagebox.showwarning("Aviso", "Por favor, selecione um funcionário.")
                return None, None

            # 3️⃣ Criar subpasta do funcionário dentro da principal
            subfolder_id = self.get_or_create_drive_folder(funcionario_nome, main_folder_id)

            # 4️⃣ Metadados do arquivo
            file_metadata = {
                'name': file_name,
                'mimeType': self.get_mime_type(file_path),
                'parents': [subfolder_id]
            }

            # 5️⃣ Fazer upload
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            logger.info("Upload realizado: %s (ID: %s)", file_name, file.get('id'))
            return file.get('id'), file.get('webViewLink')

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao fazer upload para o Drive: {e}")
            return None, None
    
    def excluir_do_drive(self, drive_file_id):
        """Exclui um arquivo do Google Drive pelo ID"""
        try:
            if not drive_file_id:
                logger.warning("Arquivo sem ID do Drive. Ignorando exclusão.")
                return
            if not self.service:
                messagebox.showerror("Erro", "Serviço do Google Drive não configurado.")
                return
            self.service.files().delete(fileId=drive_file_id).execute()
            logger.info("Arquivo do Drive %s excluído com sucesso.", drive_file_id)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir arquivo do Drive: {e}")

    def get_mime_type(self, file_path):
        """Obtém o MIME type do arquivo"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def fazer_upload(self):
        """Processa o upload do documento"""
        if not self.arquivo_selecionado:
            messagebox.showwarning("Aviso", "Por favor, selecione um arquivo.")
            return
        
        if not self.funcionario_var.get():
            messagebox.showwarning("Aviso", "Por favor, selecione um funcionário.")
            return
        
        if not os.path.exists(self.arquivo_selecionado):
            messagebox.showerror("Erro", "Arquivo não encontrado.")
            return
        
        if not self.service:
            messagebox.showerror("Erro", "Serviço do Google Drive não configurado.")
            return
        
        try:
            # Obter ID do funcionário
            funcionario_nome = self.funcionario_var.get()
            self.funcionario_id = self.funcionarios_map[funcionario_nome]
            
            nome_arquivo = os.path.basename(self.arquivo_selecionado)
            descricao = self.descricao_entry.get()
            tipo = self.tipo_var.get() or 'Outros'
            
            # Fazer upload para o Google Drive
            file_id, link_drive = self.upload_para_drive(self.arquivo_selecionado, nome_arquivo)
            
            if file_id and link_drive:
                # Inserir no banco de dados
                sql = """
                INSERT INTO documentos_funcionarios 
                (funcionario_id, nome_arquivo, tipo, link_no_drive, descricao) 
                VALUES (%s, %s, %s, %s, %s)
                """
                
                valores = (self.funcionario_id, nome_arquivo, tipo, link_drive, descricao)
                # Proteção: garantir conexão e cursor antes de gravar
                if not getattr(self, 'conn', None) or not getattr(self, 'cursor', None):
                    messagebox.showerror("Erro", "Sem conexão com o banco de dados.")
                    return
                conn = self.conn
                cursor = self.cursor
                cursor.execute(sql, valores)
                cast(Any, conn).commit()
                
                messagebox.showinfo("Sucesso", "Documento salvo com sucesso!")
                
                # Limpar campos
                self.arquivo_selecionado = None
                self.arquivo_label.config(text="Nenhum arquivo selecionado", foreground="gray")
                self.descricao_entry.delete(0, tk.END)
                self.tipo_var.set('')
                
                # Atualizar lista de documentos
                self.carregar_documentos()
            else:
                messagebox.showerror("Erro", "Falha no upload para o Google Drive.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar documento: {e}")
    
    def carregar_documentos(self):
        """Carrega os documentos do funcionário selecionado"""
        if not self.funcionario_var.get():
            return
        
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Erro", "Sem conexão com o banco de dados.")
            return
        
        try:
            # Limpar treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            funcionario_nome = self.funcionario_var.get()
            self.funcionario_id = self.funcionarios_map[funcionario_nome]
            
            # Buscar documentos no banco
            sql = """
            SELECT id, nome_arquivo, tipo, data_de_upload, descricao 
            FROM documentos_funcionarios 
            WHERE funcionario_id = %s 
            ORDER BY data_de_upload DESC
            """
            
            self.cursor.execute(sql, (self.funcionario_id,))
            documentos = self.cursor.fetchall()
            
            for doc in documentos:
                # Formatar data (proteger contra valores que não sejam datetime)
                val_data = doc[3]
                if val_data is None:
                    data_formatada = ''
                elif isinstance(val_data, datetime):
                    data_formatada = val_data.strftime('%d/%m/%Y %H:%M')
                elif isinstance(val_data, (int, float)):
                    try:
                        data_formatada = datetime.fromtimestamp(float(val_data)).strftime('%d/%m/%Y %H:%M')
                    except Exception:
                        data_formatada = str(val_data)
                else:
                    # Fallback para outros tipos (date, Decimal, str, etc.)
                    try:
                        data_formatada = str(val_data)
                    except Exception:
                        data_formatada = ''
                self.tree.insert('', tk.END, values=(
                    doc[0], doc[1], doc[2] or '', data_formatada, doc[4] or ''
                ))
            
            logger.info("Carregados %d documentos", len(documentos))
                
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar documentos: {e}")
    
    def abrir_documento(self):
        """Abre o documento selecionado no navegador"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Por favor, selecione um documento.")
            return
        
        try:
            item = self.tree.item(selected_item[0])
            doc_id = item['values'][0]
            
            # Buscar link do documento
            sql = "SELECT link_no_drive FROM documentos_funcionarios WHERE id = %s"
            self.cursor.execute(sql, (doc_id,))
            resultado = self.cursor.fetchone()
            
            if resultado and resultado[0]:
                webbrowser.open(str(resultado[0]))
            else:
                messagebox.showerror("Erro", "Link do documento não encontrado.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir documento: {e}")
    
    def excluir_documento(self):
        """Exclui o documento selecionado do banco e do Google Drive"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Por favor, selecione um documento.")
            return

        try:
            item = self.tree.item(selected_item[0])
            doc_id = item['values'][0]
            nome_arquivo = item['values'][1]

            # Confirmar exclusão
            resposta = messagebox.askyesno(
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir o documento '{nome_arquivo}'?\n\nEsta ação não pode ser desfeita."
            )

            if not resposta:
                return

            # Buscar o link no banco de dados
            sql = "SELECT link_no_drive FROM documentos_funcionarios WHERE id = %s"
            self.cursor.execute(sql, (doc_id,))
            resultado = self.cursor.fetchone()

            if resultado and resultado[0]:
                link = resultado[0]

                # Garantir que temos uma string para operar
                try:
                    link_str = str(link)
                except Exception:
                    link_str = ''

                # Extrair file_id do link (funciona para qualquer formato de link do Drive)
                file_id = None
                if '/d/' in link_str:
                    parts = link_str.split('/d/')
                    if len(parts) > 1:
                        file_id = parts[1].split('/')[0]
                elif 'id=' in link_str:
                    parts = link_str.split('id=')
                    if len(parts) > 1:
                        file_id = parts[1].split('&')[0]
                elif link_str:
                    file_id = link_str.split('/')[-1]

                # Excluir do Google Drive (se possível)
                if file_id:
                    try:
                        if not self.service:
                            logger.info(f"⚠️ Serviço do Drive não configurado; não foi possível excluir {file_id}")
                        else:
                            self.service.files().update(fileId=file_id, body={"trashed": True}).execute()
                            logger.info(f"✅ Documento excluído do Drive: {file_id}")
                    except Exception as e:
                        logger.info(f"⚠️ Aviso: não foi possível excluir do Drive: {e}")

            # Excluir do banco de dados
            sql_delete = "DELETE FROM documentos_funcionarios WHERE id = %s"
            if not getattr(self, 'conn', None) or not getattr(self, 'cursor', None):
                messagebox.showerror("Erro", "Sem conexão com o banco de dados.")
                return
            conn = self.conn
            cursor = self.cursor
            cursor.execute(sql_delete, (doc_id,))
            cast(Any, conn).commit()

            # Atualizar a interface
            self.carregar_documentos()
            messagebox.showinfo("Sucesso", f"Documento '{nome_arquivo}' excluído com sucesso!")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir documento: {e}")

    
    def __del__(self):
        """Fecha a conexão com o banco ao destruir o objeto"""
        if hasattr(self, 'conn') and self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()

def main():
    try:
        root = tk.Tk()
        app = GerenciadorDocumentosFuncionarios(root)
        root.mainloop()
    except Exception as e:
        logger.exception("Erro ao iniciar aplicação: %s", e)
        messagebox.showerror("Erro", f"Erro ao iniciar aplicação: {e}")

if __name__ == "__main__":
    main()