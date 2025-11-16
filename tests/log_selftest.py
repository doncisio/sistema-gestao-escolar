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
print('log exists:', p.exists())
if p.exists():
    text = p.read_text(encoding='utf-8')
    lines = text.splitlines()
    tail = '\n'.join(lines[-20:]) if len(lines) > 0 else ''
    print('---- log tail (últimas linhas) ----')
    print(tail)
    print('---- end log ----')
else:
    print('Arquivo de log não encontrado')
