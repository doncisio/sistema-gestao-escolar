import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_file='logs/app.log', level=logging.INFO):
    """Configura logging estruturado simples (key=value) com arquivo e console.

    Não importa se for chamado várias vezes; evita reconfigurar handlers duplicados.
    """
    logger = logging.getLogger()
    if getattr(logger, '_configured_for_app', False):
        return

    logger.setLevel(level)

    # Criar diretório de logs
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Formatter simples em estilo key=value para facilitar parsing
    fmt = '%(asctime)s level=%(levelname)s name=%(name)s message=%(message)s'
    formatter = logging.Formatter(fmt)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler com rotação
    fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger._configured_for_app = True


def get_logger(name=None):
    """Retorna um logger já configurado. Chama setup_logging() na primeira vez."""
    setup_logging()
    return logging.getLogger(name)
