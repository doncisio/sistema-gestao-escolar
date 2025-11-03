from tkinter import messagebox
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

class GerenciadorDocumentos:
    def __init__(self):
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Configurações do Google Drive
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.service = None
        self.setup_google_drive()
    
    def setup_google_drive(self):
        """Configura a autenticação com o Google Drive"""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    # Token expirado ou revogado, remover e refazer autenticação
                    print(f"Erro ao renovar token: {e}")
                    if os.path.exists('token.pickle'):
                        os.remove('token.pickle')
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                    creds = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        
        # Configurar pasta raiz do sistema
        self.pasta_raiz_id = self.get_or_create_pasta_raiz()
    
    def get_or_create_pasta_raiz(self):
        """
        Obtém ou cria a pasta raiz do sistema no Google Drive.
        A pasta raiz é chamada 'Sistema Escolar - Documentos'
        """
        nome_pasta_raiz = 'Sistema Escolar - Documentos'
        
        # Procurar pasta existente
        results = self.service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and name='{nome_pasta_raiz}' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        # Se encontrou a pasta, retorna o ID
        if results['files']:
            pasta_id = results['files'][0]['id']
        else:
            # Se não encontrou, cria uma nova pasta
            folder_metadata = {
                'name': nome_pasta_raiz,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            pasta_id = folder['id']
            
            # Configurar permissão para que qualquer pessoa com o link possa ver
            permission = {
                'type': 'anyone',
                'role': 'reader',
                'allowFileDiscovery': False
            }
            self.service.permissions().create(
                fileId=pasta_id,
                body=permission
            ).execute()
        
        return pasta_id
    
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

    def get_or_create_folder(self, folder_name, parent_id=None):
        """
        Obtém ou cria uma pasta no Google Drive.
        
        Args:
            folder_name (str): Nome da pasta
            parent_id (str, optional): ID da pasta pai
            
        Returns:
            str: ID da pasta
        """
        # Procurar pasta existente
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        # Se encontrou a pasta, retorna o ID
        if results['files']:
            return results['files'][0]['id']
        
        # Se não encontrou, cria uma nova pasta
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            folder_metadata['parents'] = [parent_id]
        
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()
        
        return folder['id']

    def salvar_documento(self, caminho_arquivo, tipo_documento, aluno_id=None, funcionario_id=None, 
                        finalidade=None, descricao=None, pasta_drive=None):
        """
        Salva um documento no Google Drive e registra no banco de dados.
        
        Args:
            caminho_arquivo (str): Caminho completo do arquivo a ser salvo
            tipo_documento (str): Tipo do documento (ex: 'Declaração', 'Boletim', etc.)
            aluno_id (int, optional): ID do aluno relacionado ao documento
            funcionario_id (int, optional): ID do funcionário relacionado ao documento
            finalidade (str, optional): Finalidade do documento
            descricao (str, optional): Descrição adicional do documento
            pasta_drive (str, optional): ID da pasta pai onde criar a estrutura
        
        Returns:
            tuple: (sucesso, mensagem, link_documento)
        """
        from utilitarios.tipos_documentos import get_categoria_documento
        
        # Criar estrutura de pastas usando a pasta raiz como base
        ano_atual = datetime.now().year
        
        # Pasta do ano
        pasta_principal = self.get_or_create_folder(f"Documentos Gerados {ano_atual}", 
                                                  pasta_drive or self.pasta_raiz_id)
        
        # Pasta da categoria
        categoria = get_categoria_documento(tipo_documento)
        pasta_categoria = self.get_or_create_folder(categoria, pasta_principal)
        
        # Pasta do tipo específico de documento
        pasta_tipo = self.get_or_create_folder(tipo_documento, pasta_categoria)
        try:
            nome_arquivo = os.path.basename(caminho_arquivo)
            
            # Upload para o Google Drive
            file_metadata = {
                'name': nome_arquivo,
                'parents': [pasta_tipo]  # Usar a pasta específica do tipo de documento
            }
            
            mimetype = mimetypes.guess_type(caminho_arquivo)[0]
            media = MediaFileUpload(caminho_arquivo, mimetype=mimetype, resumable=True)
            
            try:
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()
                
                # Configurar permissão de visualização
                permission = {
                    'type': 'anyone',
                    'role': 'reader'
                }
                self.service.permissions().create(
                    fileId=file['id'],
                    body=permission
                ).execute()
            except Exception as e:
                if 'invalid_grant' in str(e) or 'Token has been expired' in str(e):
                    # Token expirado, tentar renovar
                    print("Token do Google Drive expirou. Renovando...")
                    self.setup_google_drive()
                    # Tentar novamente após renovar
                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id, webViewLink'
                    ).execute()
                    
                    permission = {
                        'type': 'anyone',
                        'role': 'reader'
                    }
                    self.service.permissions().create(
                        fileId=file['id'],
                        body=permission
                    ).execute()
                else:
                    raise
            
            # Salvar no banco de dados
            conn = self.conectar_bd()
            if not conn:
                return False, "Erro ao conectar ao banco de dados", None
            
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO documentos_emitidos 
                    (tipo_documento, nome_arquivo, data_de_upload, finalidade, descricao, link_no_drive,
                     aluno_id, funcionario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    tipo_documento,
                    nome_arquivo,
                    datetime.now(),
                    finalidade,
                    descricao,
                    file['webViewLink'],
                    aluno_id,
                    funcionario_id
                ))
                
                conn.commit()
                return True, "Documento salvo com sucesso!", file['webViewLink']
                
            except mysql.connector.Error as e:
                conn.rollback()
                return False, f"Erro ao salvar no banco de dados: {str(e)}", None
                
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            return False, f"Erro ao salvar documento: {str(e)}", None

# Instância global do gerenciador
gerenciador = GerenciadorDocumentos()

def salvar_documento_sistema(caminho_arquivo, tipo_documento, aluno_id=None, funcionario_id=None,
                           finalidade=None, descricao=None, pasta_drive=None):
    """
    Função auxiliar para facilitar o uso do gerenciador de documentos.
    Utiliza a instância global do gerenciador.
    
    Args:
        caminho_arquivo (str): Caminho completo do arquivo a ser salvo
        tipo_documento (str): Tipo do documento (ex: 'Declaração', 'Boletim', etc.)
        aluno_id (int, optional): ID do aluno relacionado ao documento
        funcionario_id (int, optional): ID do funcionário relacionado ao documento
        finalidade (str, optional): Finalidade do documento
        descricao (str, optional): Descrição adicional do documento
        pasta_drive (str, optional): ID da pasta no Google Drive onde o arquivo será salvo
        
    Returns:
        tuple: (sucesso, mensagem, link_documento)
    """
    return gerenciador.salvar_documento(
        caminho_arquivo,
        tipo_documento,
        aluno_id,
        funcionario_id,
        finalidade,
        descricao,
        pasta_drive
    )