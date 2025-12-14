import os
import json
import sys
from pathlib import Path

from src.core.config_logs import get_logger
logger = get_logger(__name__)

LOCAL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'local_config.json')


def _extract_drive_id(s: str):
    if not s:
        return None
    s = s.strip()
    if '/folders/' in s:
        parts = s.split('/folders/')
        if len(parts) > 1:
            return parts[1].split('?')[0].split('/')[0]
    if '/d/' in s:
        parts = s.split('/d/')
        if len(parts) > 1:
            return parts[1].split('/')[0]
    if 'id=' in s:
        parts = s.split('id=')
        if len(parts) > 1:
            return parts[1].split('&')[0]
    if len(s) >= 20 and all(c.isalnum() or c in ['-', '_'] for c in s):
        return s
    return None


def get_drive_folder_id():
    v = os.environ.get('DOCUMENTS_DRIVE_FOLDER_ID')
    if v:
        return _extract_drive_id(v) or v
    try:
        if os.path.exists(LOCAL_CONFIG_PATH):
            with open(LOCAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            val = cfg.get('drive_folder_id')
            if val:
                return _extract_drive_id(str(val)) or str(val)
    except Exception as e:
        logger.exception('Erro lendo local_config: %s', e)
    try:
        import config as _cfg
        default = getattr(_cfg, 'DEFAULT_DRIVE_FOLDER_ID', None)
        if default:
            return _extract_drive_id(default) or default
    except Exception:
        pass
    return None


def make_test_file(path: str):
    # cria um arquivo simples (pode ser .pdf ou .txt)
    data = b"Teste de upload do sistema de gestao.\n"
    with open(path, 'wb') as f:
        f.write(data)


def main():
    try:
        from drive_uploader import upload_file
    except Exception as e:
        logger.exception('drive_test: nao foi possivel importar drive_uploader: %s', e)
        print('Erro: drive_uploader não está disponível. Veja logs.')
        sys.exit(2)

    parent = get_drive_folder_id()
    logger.info('drive_test: usando parent_id=%s', parent)

    tmpname = os.path.join(os.path.dirname(__file__), 'drive_test_upload.pdf')
    make_test_file(tmpname)
    print('Arquivo de teste criado em:', tmpname)

    fid, link = upload_file(tmpname, parent_id=parent)
    if fid:
        print('Upload concluído: id=', fid)
        if link:
            print('Link de visualização:', link)
    else:
        print('Upload falhou. Veja logs em logs/app.log')


if __name__ == '__main__':
    main()
