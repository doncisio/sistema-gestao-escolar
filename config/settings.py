"""
Configuração centralizada e validada do sistema de gestão escolar.

Este módulo carrega todas as configurações de variáveis de ambiente,
com validação e valores padrão apropriados.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Versão do sistema
VERSION = "2.0.0"


@dataclass
class DatabaseConfig:
    """Configurações do banco de dados MySQL."""
    host: str
    user: str
    password: str
    name: str
    pool_size: int
    
    def validate(self) -> list[str]:
        """Valida as configurações obrigatórias."""
        errors = []
        if not self.host:
            errors.append("DB_HOST não configurado")
        if not self.user:
            errors.append("DB_USER não configurado")
        if not self.password:
            errors.append("DB_PASSWORD não configurado")
        if not self.name:
            errors.append("DB_NAME não configurado")
        if self.pool_size < 1 or self.pool_size > 50:
            errors.append("DB_POOL_SIZE deve estar entre 1 e 50")
        return errors


@dataclass
class AppConfig:
    """Configurações gerais da aplicação."""
    escola_id: int
    test_mode: bool
    documents_root: str
    google_credentials_path: str
    
    def validate(self) -> list[str]:
        """Valida as configurações."""
        errors = []
        if self.escola_id <= 0:
            errors.append("ESCOLA_ID deve ser maior que 0")
        # Documents root e credentials podem não existir inicialmente
        return errors


@dataclass
class LogConfig:
    """Configurações de logging."""
    level: str
    format: str  # 'text' ou 'json'
    
    def validate(self) -> list[str]:
        """Valida as configurações de log."""
        errors = []
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.level not in valid_levels:
            errors.append(f"LOG_LEVEL deve ser um de: {', '.join(valid_levels)}")
        if self.format not in ['text', 'json']:
            errors.append("LOG_FORMAT deve ser 'text' ou 'json'")
        return errors


@dataclass
class BackupConfig:
    """Configurações de backup automático."""
    enabled: bool
    interval_hours: int
    
    def validate(self) -> list[str]:
        """Valida as configurações de backup."""
        errors = []
        if self.interval_hours < 1 or self.interval_hours > 168:  # Max 1 semana
            errors.append("BACKUP_INTERVAL_HOURS deve estar entre 1 e 168")
        return errors


class Settings:
    """Classe principal de configurações do sistema."""
    
    def __init__(self):
        """Inicializa e carrega todas as configurações."""
        self.database = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            name=os.getenv('DB_NAME', 'redeescola'),
            pool_size=int(os.getenv('DB_POOL_SIZE', '5'))
        )
        
        self.app = AppConfig(
            escola_id=int(os.getenv('ESCOLA_ID', '60')),
            test_mode=os.getenv('GESTAO_TEST_MODE', 'False').lower() in ('true', '1', 'yes'),
            documents_root=os.getenv(
                'DOCUMENTS_SECRETARIA_ROOT',
                r"G:\Meu Drive\Sistema Escolar - Documentos"
            ),
            google_credentials_path=os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        )
        
        self.log = LogConfig(
            level=os.getenv('LOG_LEVEL', 'INFO').upper(),
            format=os.getenv('LOG_FORMAT', 'text').lower()
        )
        
        self.backup = BackupConfig(
            enabled=os.getenv('BACKUP_ENABLED', 'True').lower() in ('true', '1', 'yes'),
            interval_hours=int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
        )
        
        self.version = VERSION
        
    def validate_all(self) -> tuple[bool, list[str]]:
        """
        Valida todas as configurações.
        
        Returns:
            tuple[bool, list[str]]: (is_valid, error_messages)
        """
        all_errors = []
        
        all_errors.extend(self.database.validate())
        all_errors.extend(self.app.validate())
        all_errors.extend(self.log.validate())
        all_errors.extend(self.backup.validate())
        
        return len(all_errors) == 0, all_errors
    
    def get_summary(self) -> dict:
        """Retorna um resumo das configurações (sem senhas)."""
        return {
            'version': self.version,
            'database': {
                'host': self.database.host,
                'user': self.database.user,
                'name': self.database.name,
                'pool_size': self.database.pool_size,
            },
            'app': {
                'escola_id': self.app.escola_id,
                'test_mode': self.app.test_mode,
            },
            'log': {
                'level': self.log.level,
                'format': self.log.format,
            },
            'backup': {
                'enabled': self.backup.enabled,
                'interval_hours': self.backup.interval_hours,
            }
        }


# Instância singleton das configurações
settings = Settings()


# Função de conveniência para validar ao importar (opcional)
def validate_settings() -> None:
    """
    Valida as configurações e lança exceção se houver erros.
    Use no início da aplicação para falhar rápido.
    """
    is_valid, errors = settings.validate_all()
    if not is_valid:
        error_msg = "Erro(s) de configuração:\n" + "\n".join(f"  - {err}" for err in errors)
        raise ValueError(error_msg)
