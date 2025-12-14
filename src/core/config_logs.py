import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

# Importar settings centralizado
try:
    from src.core.config.settings import settings
except ImportError:
    settings = None


class JSONFormatter(logging.Formatter):
    """
    Formatter que gera logs em formato JSON estruturado.
    Útil para integração com sistemas de análise de logs.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o log record como JSON.
        
        Args:
            record: Log record do Python
            
        Returns:
            String JSON com os dados estruturados
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adicionar exception info se presente
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Adicionar campos extras se presentes
        if hasattr(record, 'extra_fields'):
            extra_fields = getattr(record, 'extra_fields', {})
            log_data.update(extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """
    Formatter key=value melhorado com mais contexto.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata como key=value com informações adicionais."""
        parts = [
            f'timestamp={datetime.fromtimestamp(record.created).isoformat()}',
            f'level={record.levelname}',
            f'logger={record.name}',
            f'module={record.module}',
            f'function={record.funcName}',
            f'line={record.lineno}',
            f'message={record.getMessage()}'
        ]
        
        if record.exc_info:
            parts.append(f'exception={self.formatException(record.exc_info)}')
        
        return ' '.join(parts)


def setup_logging(
    log_file: str = 'logs/app.log',
    level: Optional[int] = None,
    use_json: Optional[bool] = None,
    rotation_type: str = 'size',  # 'size', 'time', 'both'
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    when: str = 'midnight'  # Para TimedRotatingFileHandler
) -> None:
    """
    Configura logging estruturado com opções avançadas.
    
    Se settings estiver disponível, usa configurações de lá.
    Caso contrário, usa valores passados ou padrão.

    Args:
        log_file: Caminho do arquivo de log
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL) - None usa settings
        use_json: Se True, usa JSON formatter; se False, usa key=value - None usa settings
        rotation_type: Tipo de rotação ('size', 'time', 'both')
        max_bytes: Tamanho máximo do arquivo para rotação por tamanho
        backup_count: Número de arquivos de backup a manter
        when: Quando fazer rotação por tempo ('midnight', 'H', 'D', 'W0'-'W6')
    """
    logger = logging.getLogger()
    
    # Evitar reconfiguração duplicada
    if getattr(logger, '_configured_for_app', False):
        return
    
    # Determinar configurações a partir de settings se disponível
    if settings:
        if level is None:
            level = getattr(logging, settings.log.level, logging.INFO)
        if use_json is None:
            use_json = settings.log.format == 'json'
    else:
        if level is None:
            level = logging.INFO
        if use_json is None:
            use_json = False

    logger.setLevel(level)

    # Criar diretório de logs
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Escolher formatter
    formatter: logging.Formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        # Formatter simples key=value para console
        fmt = '%(asctime)s level=%(levelname)s name=%(name)s message=%(message)s'
        formatter = logging.Formatter(fmt)

    # Console handler (sempre key=value simples)
    console_fmt = '%(asctime)s level=%(levelname)s name=%(name)s message=%(message)s'
    console_formatter: logging.Formatter = logging.Formatter(console_fmt)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(console_formatter)
    logger.addHandler(ch)

    # File handlers com rotação
    if rotation_type in ('size', 'both'):
        # Rotação por tamanho
        fh_size = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        fh_size.setLevel(level)
        fh_size.setFormatter(formatter)
        logger.addHandler(fh_size)
    
    if rotation_type in ('time', 'both'):
        # Rotação por tempo
        log_file_timed = log_file.replace('.log', '_timed.log')
        fh_timed = TimedRotatingFileHandler(
            log_file_timed,
            when=when,
            interval=1,
            backupCount=backup_count,
            encoding='utf-8'
        )
        fh_timed.setLevel(level)
        fh_timed.setFormatter(formatter)
        logger.addHandler(fh_timed)

    # Marcar como configurado
    setattr(logger, '_configured_for_app', True)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retorna um logger já configurado.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        
    Returns:
        Logger configurado
    """
    setup_logging()
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: int, message: str, **context) -> None:
    """
    Log com contexto adicional (útil para JSON formatter).
    
    Args:
        logger: Logger a usar
        level: Nível do log
        message: Mensagem
        **context: Campos extras para adicionar ao log
        
    Example:
        log_with_context(logger, logging.INFO, "Usuário logado", user_id=123, ip="192.168.1.1")
    """
    extra = {'extra_fields': context}
    logger.log(level, message, extra=extra)

