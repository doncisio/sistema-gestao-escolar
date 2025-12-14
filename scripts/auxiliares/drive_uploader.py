import os
import pickle
from typing import Optional, Tuple, Any, Dict

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Escopo para criar/editar arquivos na conta do usuário
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def _get_service(credentials_path: str = 'credentials.json', token_path: str = 'token_drive.pickle'):
    creds = None
    logger.debug("_get_service: credentials_path=%s token_path=%s", credentials_path, token_path)
    if os.path.exists(token_path):
        logger.debug("_get_service: token file exists: %s", token_path)
        try:
            with open(token_path, 'rb') as f:
                creds = pickle.load(f)
            logger.debug("_get_service: loaded token; valid=%s expired=%s", getattr(creds, 'valid', None), getattr(creds, 'expired', None))
        except Exception as e:
            logger.exception("_get_service: falha ao carregar token: %s", e)
            creds = None

    if not creds or not creds.valid:
        try:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            logger.exception("Falha ao obter credenciais do Google Drive: %s", e)
            raise

    try:
        service = build('drive', 'v3', credentials=creds)
        logger.debug("_get_service: Drive service criado com sucesso")
        return service
    except Exception as e:
        logger.exception("_get_service: falha ao criar service Drive: %s", e)
        raise


def upload_file(filepath: str, parent_id: Optional[str] = None, name: Optional[str] = None, replace_existing: bool = True) -> Tuple[Optional[str], Optional[str]]:
    """Faz upload de `filepath` para o Google Drive.

    Retorna (fileId, webViewLink) ou (None, None) em caso de erro.
    """
    try:
        service = _get_service()
    except Exception as e:
        logger.exception("upload_file: não foi possível obter service: %s", e)
        return None, None

    if not name:
        name = os.path.basename(filepath)

    mime_type = 'application/pdf'
    media = MediaFileUpload(filepath, mimetype=mime_type)

    # Tipar explicitamente como dicionário para evitar avisos de tipo do Pylance
    body: Dict[str, Any] = {'name': name}
    if parent_id:
        body['parents'] = [parent_id]

    # Log da tentativa
    logger.info("upload_file: iniciando upload file=%s parent_id=%s name=%s replace=%s", filepath, parent_id, name, replace_existing)

    # Se foi passada uma parent_id, testar se a pasta existe e se temos permissão
    if parent_id:
        try:
            logger.debug("upload_file: verificando existência da pasta parent_id=%s", parent_id)
            info = service.files().get(fileId=parent_id, fields='id,name').execute()
            logger.debug("upload_file: pasta verificada: %s", info)
        except Exception as e:
            logger.exception("upload_file: falha ao verificar pasta parent_id=%s: %s", parent_id, e)

    # Se solicitado, procurar arquivo existente com mesmo nome na pasta e substituir
    try:
        if replace_existing:
            # Montar query para procurar pelo nome e pasta (ou raiz)
            q_parts = []
            # name equality - escape single quotes by replacing with "'" is tricky; assume typical filenames
            q_parts.append(f"name = '{name}'")
            if parent_id:
                q_parts.append(f"'{parent_id}' in parents")
            else:
                q_parts.append("'root' in parents")

            q = ' and '.join(q_parts) + " and trashed = false"
            logger.debug("upload_file: procurando arquivos existentes com q=%s", q)
            res = service.files().list(q=q, fields='files(id,name)', spaces='drive').execute()
            files = res.get('files', []) if res else []
            if files:
                # Substituir o primeiro arquivo encontrado
                existing = files[0]
                existing_id = existing.get('id')
                logger.info("upload_file: arquivo existente encontrado id=%s name=%s - substituindo", existing_id, existing.get('name'))
                try:
                    updated = service.files().update(fileId=existing_id, media_body=media, fields='id, webViewLink').execute()
                    fid = updated.get('id')
                    web = updated.get('webViewLink')
                    logger.info("upload_file: arquivo substituído no Drive: %s (id=%s)", filepath, fid)
                    return fid, web
                except Exception as e:
                    logger.exception("upload_file: falha ao atualizar arquivo existente id=%s: %s", existing_id, e)
                    # continuar para tentar criar novo arquivo

        # Se não encontrou ou não substituiu, criar novo
        created = service.files().create(body=body, media_body=media, fields='id, webViewLink').execute()
        file_id = created.get('id')
        web_view = created.get('webViewLink')
        logger.info("Arquivo enviado para Drive: %s (id=%s)", filepath, file_id)
        logger.debug("upload_file: response=%s", created)
        return file_id, web_view

    except Exception as e:
        logger.exception("Falha ao enviar/atualizar arquivo para Drive: %s", e)
        return None, None
