import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config_logs import get_logger
logger = get_logger('selftest')
logger.debug('Teste de log DEBUG')
logger.info('Teste de log INFO')
logger.warning('Teste de log WARNING')
logger.error('Teste de log ERROR')

import pathlib
p = pathlib.Path('logs/app.log')
logger.info('log exists: %s', p.exists())
if p.exists():
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines()
    tail = '\n'.join(lines[-20:]) if len(lines) > 0 else ''
    logger.info('---- log tail (últimas linhas) ----')
    logger.info(tail)
    logger.info('---- end log ----')
else:
    logger.warning('Arquivo de log não encontrado')
