import mysql.connector
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Configurações do banco de dados
db_config = {
    'user': 'seu_usuario',
    'password': 'sua_senha',
    'host': '127.0.0.1',
    'database': 'redeescola'
}

# Autenticação com Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'H:\Meu Drive\NADIR_2024\Backup\client_secret_87138225601-u54i0smdhdse7bi30rt5an4ho9h30hjr.apps.googleusercontent.com.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)

def criar_pasta(nome_pasta):
    file_metadata = {
        'name': nome_pasta,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def definir_permissoes(folder_id, email_usuario):
    permission = {
        'type': 'user',
        'role': 'owner',  # Acesso total
        'emailAddress': email_usuario
    }
    service.permissions().create(fileId=folder_id, body=permission).execute()

# Conectar ao banco de dados
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Criar pastas para alunos
cursor.execute("SELECT nome FROM alunos")
alunos = cursor.fetchall()
for (nome,) in alunos:
    pasta_id = criar_pasta(nome)  # Cria uma pasta com o nome do aluno
    definir_permissoes(pasta_id, 'doncisio@example.com')  # Define permissões para doncisio

# Criar pastas para funcionários
cursor.execute("SELECT nome FROM funcionarios")
funcionarios = cursor.fetchall()
for (nome,) in funcionarios:
    pasta_id = criar_pasta(nome)  # Cria uma pasta com o nome do funcionário
    definir_permissoes(pasta_id, 'doncisio@example.com')  # Define permissões para doncisio

# Fechar a conexão
cursor.close()
conn.close()