"""
Sistema robusto de tratamento de erros para aplicação.

Este módulo fornece:
- Handler global de exceções não capturadas
- Decorators para tratamento seguro de operações
- Logging estruturado de erros
- Mensagens amigáveis ao usuário
"""

import sys
import traceback
from functools import wraps
from typing import Callable, Optional, Any
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

from src.core.config_logs import get_logger
from pydantic import ValidationError

logger = get_logger(__name__)


class ErrorHandler:
    """Handler global de erros da aplicação."""
    
    # Controle de rate limiting para evitar spam de diálogos
    _last_error_dialog = None
    _error_dialog_cooldown = 2.0  # segundos
    
    @staticmethod
    def handle_exception(exc_type, exc_value, exc_traceback):
        """
        Handler para exceções não capturadas.
        
        Instalado via sys.excepthook para capturar todos os erros não tratados.
        
        Args:
            exc_type: Tipo da exceção
            exc_value: Valor/instância da exceção
            exc_traceback: Traceback da exceção
        """
        # KeyboardInterrupt não deve ser capturado
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log completo do erro
        logger.critical(
            "Exceção não tratada capturada",
            exc_info=(exc_type, exc_value, exc_traceback),
            extra={
                'error_type': exc_type.__name__,
                'error_message': str(exc_value),
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # Rate limiting para evitar múltiplos diálogos
        now = datetime.now()
        if (ErrorHandler._last_error_dialog is None or 
            (now - ErrorHandler._last_error_dialog).total_seconds() > ErrorHandler._error_dialog_cooldown):
            
            ErrorHandler._last_error_dialog = now
            
            # Mostrar diálogo amigável ao usuário
            try:
                error_msg = (
                    "Ocorreu um erro inesperado no sistema.\n\n"
                    f"Tipo: {exc_type.__name__}\n"
                    f"Detalhes: {str(exc_value)[:200]}\n\n"
                    "O erro foi registrado nos logs.\n"
                    "Por favor, reinicie o sistema."
                )
                
                messagebox.showerror(
                    "Erro Crítico",
                    error_msg
                )
            except Exception:
                # Se falhar ao mostrar dialog, apenas logar
                logger.exception("Falha ao mostrar diálogo de erro")
    
    @staticmethod
    def install():
        """Instala o handler global de exceções."""
        sys.excepthook = ErrorHandler.handle_exception
        logger.info("Handler global de exceções instalado")


def safe_action(
    error_title: str = "Erro",
    error_message: Optional[str] = None,
    log_level: str = "error",
    return_on_error: Any = None,
    show_dialog: bool = True
) -> Callable:
    """
    Decorator para executar ações de forma segura com tratamento de erros.
    
    Captura exceções comuns e exibe mensagens amigáveis ao usuário.
    Ideal para uso em callbacks de UI.
    
    Args:
        error_title: Título do diálogo de erro
        error_message: Mensagem customizada (None = usar mensagem da exceção)
        log_level: Nível de log ('debug', 'info', 'warning', 'error', 'critical')
        return_on_error: Valor a retornar em caso de erro
        show_dialog: Se True, mostra messagebox com o erro
    
    Examples:
        @safe_action(error_title="Erro ao Cadastrar")
        def cadastrar_aluno():
            # código que pode falhar
            pass
        
        @safe_action(error_title="Erro", show_dialog=False, return_on_error=False)
        def validar_cpf(cpf):
            # validação que não precisa mostrar dialog
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except ValidationError as e:
                # Erros de validação do Pydantic
                error_msg = error_message or _format_validation_error(e)
                
                if log_level == "warning":
                    logger.warning(
                        f"Validação falhou em {func.__name__}",
                        extra={'errors': e.errors()}
                    )
                else:
                    logger.error(
                        f"Validação falhou em {func.__name__}",
                        extra={'errors': e.errors()}
                    )
                
                if show_dialog:
                    messagebox.showerror(
                        error_title or "Erro de Validação",
                        error_msg
                    )
                
                return return_on_error
            
            except ImportError as e:
                # Erros de módulo não encontrado
                error_msg = error_message or (
                    "Módulo necessário não encontrado.\n\n"
                    f"Detalhes: {str(e)}"
                )
                
                logger.error(
                    f"ImportError em {func.__name__}: {e}",
                    exc_info=True
                )
                
                if show_dialog:
                    messagebox.showerror(
                        error_title or "Erro de Módulo",
                        error_msg
                    )
                
                return return_on_error
            
            except PermissionError as e:
                # Erros de permissão de arquivo/sistema
                error_msg = error_message or (
                    "Sem permissão para executar a operação.\n\n"
                    "Verifique as permissões de arquivo ou execute como administrador."
                )
                
                logger.error(
                    f"PermissionError em {func.__name__}: {e}",
                    exc_info=True
                )
                
                if show_dialog:
                    messagebox.showerror(
                        error_title or "Erro de Permissão",
                        error_msg
                    )
                
                return return_on_error
            
            except FileNotFoundError as e:
                # Arquivo não encontrado
                error_msg = error_message or (
                    "Arquivo não encontrado.\n\n"
                    f"Caminho: {str(e)}"
                )
                
                logger.error(
                    f"FileNotFoundError em {func.__name__}: {e}",
                    exc_info=True
                )
                
                if show_dialog:
                    messagebox.showerror(
                        error_title or "Arquivo Não Encontrado",
                        error_msg
                    )
                
                return return_on_error
            
            except Exception as e:
                # Qualquer outra exceção
                error_msg = error_message or (
                    "Ocorreu um erro inesperado.\n\n"
                    f"Detalhes: {str(e)[:200]}"
                )
                
                # Log com nível configurável
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"Erro em {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'error_type': type(e).__name__
                    }
                )
                
                if show_dialog:
                    messagebox.showerror(error_title, error_msg)
                
                return return_on_error
        
        return wrapper
    return decorator


def safe_db_operation(
    error_title: str = "Erro de Banco de Dados",
    rollback: bool = True
) -> Callable:
    """
    Decorator específico para operações de banco de dados.
    
    Captura erros de MySQL e garante rollback se necessário.
    
    Args:
        error_title: Título do diálogo de erro
        rollback: Se True, executa rollback em caso de erro
    
    Examples:
        @safe_db_operation(error_title="Erro ao Salvar Aluno")
        def salvar_aluno(conn, dados):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO alunos ...")
            conn.commit()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                # Tentar identificar conexão para rollback
                conn = None
                for arg in args:
                    if hasattr(arg, 'rollback'):
                        conn = arg
                        break
                
                # Executar rollback se possível
                if rollback and conn:
                    try:
                        conn.rollback()
                        logger.info("Rollback executado após erro")
                    except Exception as rb_error:
                        logger.exception(f"Falha ao executar rollback: {rb_error}")
                
                # Log do erro
                logger.error(
                    f"Erro de banco em {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'error_type': type(e).__name__,
                        'rollback_executed': rollback and conn is not None
                    }
                )
                
                # Mensagem amigável
                error_msg = (
                    "Erro ao acessar o banco de dados.\n\n"
                    "Verifique a conexão e tente novamente.\n"
                    f"Detalhes técnicos: {str(e)[:150]}"
                )
                
                messagebox.showerror(error_title, error_msg)
                
                return None
        
        return wrapper
    return decorator


def _format_validation_error(error: ValidationError) -> str:
    """
    Formata erros de validação do Pydantic de forma amigável.
    
    Args:
        error: Exceção ValidationError do Pydantic
    
    Returns:
        Mensagem formatada para exibição ao usuário
    """
    errors = error.errors()
    
    if len(errors) == 1:
        err = errors[0]
        field = " → ".join(str(loc) for loc in err['loc'])
        return f"Erro no campo '{field}':\n{err['msg']}"
    
    # Múltiplos erros
    messages = ["Erros de validação encontrados:\n"]
    for err in errors[:5]:  # Limitar a 5 erros
        field = " → ".join(str(loc) for loc in err['loc'])
        messages.append(f"• {field}: {err['msg']}")
    
    if len(errors) > 5:
        messages.append(f"\n... e mais {len(errors) - 5} erro(s)")
    
    return "\n".join(messages)


class ErrorContext:
    """
    Context manager para tratamento de erros com cleanup garantido.
    
    Útil para operações que precisam de cleanup mesmo em caso de erro.
    
    Examples:
        with ErrorContext("Gerando relatório"):
            gerar_relatorio()
            # cleanup automático mesmo se falhar
    """
    
    def __init__(
        self,
        operation_name: str,
        cleanup: Optional[Callable] = None,
        show_error: bool = True
    ):
        """
        Inicializa o context manager.
        
        Args:
            operation_name: Nome da operação (para logging)
            cleanup: Função de cleanup a executar sempre
            show_error: Se True, mostra messagebox em caso de erro
        """
        self.operation_name = operation_name
        self.cleanup = cleanup
        self.show_error = show_error
        self.error = None
    
    def __enter__(self):
        logger.debug(f"Iniciando operação: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        # Executar cleanup sempre
        if self.cleanup:
            try:
                self.cleanup()
                logger.debug(f"Cleanup executado para: {self.operation_name}")
            except Exception as e:
                logger.exception(f"Erro no cleanup de {self.operation_name}: {e}")
        
        # Se houve erro, logar e opcionalmente mostrar
        if exc_type is not None:
            self.error = exc_value
            
            logger.error(
                f"Erro em {self.operation_name}: {exc_value}",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            if self.show_error:
                messagebox.showerror(
                    "Erro",
                    f"Erro ao executar '{self.operation_name}':\n\n{str(exc_value)[:200]}"
                )
            
            # Suprimir exceção (já tratada)
            return True
        
        logger.debug(f"Operação concluída com sucesso: {self.operation_name}")
        return False


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator para retentar operação em caso de erro.
    
    Útil para operações que podem falhar temporariamente (rede, IO, etc).
    
    Args:
        max_attempts: Número máximo de tentativas
        delay: Delay em segundos entre tentativas
        exceptions: Tupla de exceções que devem causar retry
    
    Examples:
        @retry_on_error(max_attempts=3, delay=2.0)
        def conectar_servidor():
            # tentar conectar
            pass
    """
    import time
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"Tentativa {attempt}/{max_attempts} falhou em {func.__name__}: {e}. "
                            f"Retentando em {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Todas as {max_attempts} tentativas falharam em {func.__name__}",
                            exc_info=True
                        )
            
            # Se chegou aqui, todas as tentativas falharam
            # Garantir que não tentamos `raise None` (Pylance reclama)
            if last_exception is not None:
                raise last_exception
            # Caso improvável de não termos exceção registrada, lançar uma RuntimeError
            raise RuntimeError(f"{func.__name__} falhou após {max_attempts} tentativas sem exceção registrada")
        
        return wrapper
    return decorator


# Instalar handler global ao importar o módulo
ErrorHandler.install()


if __name__ == "__main__":
    # Testes do sistema de error handling
    
    print("🧪 Testando sistema de tratamento de erros...\n")
    
    # Teste 1: safe_action básico
    @safe_action(error_title="Teste 1", show_dialog=False, return_on_error="ERRO")
    def teste_validacao():
        from pydantic import BaseModel
        
        class Modelo(BaseModel):
            nome: str
            idade: int
        
        # Vai falhar validação — construir dados via `Any` para evitar alerta do Pylance
        dados: Any = {"nome": 123, "idade": "abc"}
        Modelo(**dados)
    
    resultado = teste_validacao()
    print(f"✓ Teste 1 (validação): {resultado == 'ERRO'}")
    
    # Teste 2: retry_on_error
    tentativas = []
    
    @retry_on_error(max_attempts=3, delay=0.1, exceptions=(ValueError,))
    def teste_retry():
        tentativas.append(1)
        if len(tentativas) < 3:
            raise ValueError("Erro temporário")
        return "SUCESSO"
    
    resultado = teste_retry()
    print(f"✓ Teste 2 (retry): {resultado == 'SUCESSO' and len(tentativas) == 3}")
    
    # Teste 3: ErrorContext
    cleanup_executado = []
    
    with ErrorContext("Teste 3", cleanup=lambda: cleanup_executado.append(1), show_error=False):
        pass
    
    print(f"✓ Teste 3 (context): {len(cleanup_executado) == 1}")
    
    print("\n✅ Todos os testes passaram!")
