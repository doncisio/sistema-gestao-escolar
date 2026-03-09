import os
import pickle
import time
from typing import Optional, Tuple, Any, Dict

import httplib2
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Escopo para criar/editar arquivos na conta do usuário
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Timeout em segundos para chamadas HTTP ao Google Drive
_HTTP_TIMEOUT = 15
# Número de tentativas para upload em caso de falha de rede
_MAX_RETRIES = 2
# Pausa entre tentativas (segundos)
_RETRY_DELAY = 3


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
        authed_http = AuthorizedHttp(creds, http=httplib2.Http(timeout=_HTTP_TIMEOUT))
        service = build('drive', 'v3', http=authed_http)
        logger.debug("_get_service: Drive service criado com sucesso (timeout=%ss)", _HTTP_TIMEOUT)
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

    last_error: Optional[Exception] = None
    for attempt in range(1, _MAX_RETRIES + 2):  # tentativas: 1, 2, 3
        try:
            # Recriar MediaFileUpload a cada tentativa (não é reutilizável)
            media = MediaFileUpload(filepath, mimetype=mime_type)

            if replace_existing:
                # Montar query para procurar pelo nome e pasta (ou raiz)
                q_parts = [f"name = '{name}'"]
                if parent_id:
                    q_parts.append(f"'{parent_id}' in parents")
                else:
                    q_parts.append("'root' in parents")
                q = ' and '.join(q_parts) + " and trashed = false"
                logger.debug("upload_file: procurando arquivos existentes (tentativa %d) q=%s", attempt, q)
                res = service.files().list(q=q, fields='files(id,name)', spaces='drive').execute()
                files = res.get('files', []) if res else []
                if files:
                    existing = files[0]
                    existing_id = existing.get('id')
                    logger.info("upload_file: arquivo existente id=%s - substituindo", existing_id)
                    updated = service.files().update(fileId=existing_id, media_body=media, fields='id, webViewLink').execute()
                    fid = updated.get('id')
                    web = updated.get('webViewLink')
                    logger.info("upload_file: arquivo substituído no Drive: %s (id=%s)", filepath, fid)
                    return fid, web

            # Criar novo arquivo
            created = service.files().create(body=body, media_body=media, fields='id, webViewLink').execute()
            file_id = created.get('id')
            web_view = created.get('webViewLink')
            logger.info("Arquivo enviado para Drive: %s (id=%s)", filepath, file_id)
            return file_id, web_view

        except (TimeoutError, OSError) as e:
            last_error = e
            if attempt <= _MAX_RETRIES:
                logger.warning(
                    "upload_file: falha de rede (tentativa %d/%d): %s — aguardando %ds para nova tentativa",
                    attempt, _MAX_RETRIES + 1, e, _RETRY_DELAY
                )
                time.sleep(_RETRY_DELAY)
            else:
                logger.error("upload_file: todas as %d tentativas falharam por timeout/rede: %s", _MAX_RETRIES + 1, e)
                return None, None
        except Exception as e:
            logger.exception("Falha ao enviar/atualizar arquivo para Drive: %s", e)
            return None, None

    # Nunca deveria chegar aqui, mas satisfaz o type checker
    logger.error("upload_file: esgotadas as tentativas. Último erro: %s", last_error)
    return None, None
