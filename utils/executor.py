"""Helper simples para executar tarefas em background com ThreadPoolExecutor
e integrar callbacks seguros com Tkinter usando `janela.after()`.

Uso:
    from utils.executor import submit_background

    def trabalho():
        return 123

    def on_done(result):
        print(result)

    submit_background(trabalho, on_done=on_done, janela=janela)

Tem fallback para logging/exception e função `shutdown_executor()` para encerramento.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import traceback
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

# Singleton executor
_EXECUTOR: Optional[ThreadPoolExecutor] = None


def _get_executor(max_workers: int = 4) -> ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = ThreadPoolExecutor(max_workers=max_workers)
    return _EXECUTOR


def submit_background(fn: Callable[..., Any], *args, on_done: Optional[Callable[[Any], None]] = None,
                      on_error: Optional[Callable[[BaseException], None]] = None, janela=None, **kwargs) -> None:
    """Submete `fn(*args, **kwargs)` ao executor.

    - `on_done(result)` é chamado na thread principal via `janela.after(0, ...)` se `janela` fornecido.
    - `on_error(exc)` é chamado na thread principal via `janela.after(0, ...)` em caso de exceção.
    - Se `janela` não for fornecido, callbacks são chamados diretamente na thread do worker.
    """
    excallback = on_error
    donecb = on_done

    def _run():
        try:
            result = fn(*args, **kwargs)
            if donecb:
                # Capturar em variável local para evitar que o analisador a veja como Optional
                _done = donecb
                if janela is not None:
                    try:
                        janela.after(0, lambda _d=_done, _r=result: _d(_r))
                    except Exception:
                        # Se a UI estiver indisponível, chamar diretamente
                        try:
                            _done(result)
                        except Exception:
                            logger.exception('Erro em on_done callback')
                else:
                    try:
                        _done(result)
                    except Exception:
                        logger.exception('Erro em on_done callback')
            return result
        except BaseException as e:
            logger.exception('Erro na tarefa de background: %s', e)
            if excallback:
                # Capturar em variável local para satisfazer verificações de tipo
                _err = excallback
                if janela is not None:
                    try:
                        janela.after(0, lambda _e=e, _cb=_err: _cb(_e))
                    except Exception:
                        try:
                            _err(e)
                        except Exception:
                            logger.exception('Erro em on_error callback')
                else:
                    try:
                        _err(e)
                    except Exception:
                        logger.exception('Erro em on_error callback')
            return None

    try:
        executor = _get_executor()
        executor.submit(_run)
    except Exception:
        # Se falhar ao acessar executor, rodar em thread simples
        import threading

        t = threading.Thread(target=_run, daemon=True)
        t.start()


def shutdown_executor(wait: bool = False) -> None:
    """Encerra o executor se foi criado."""
    global _EXECUTOR
    if _EXECUTOR is not None:
        try:
            _EXECUTOR.shutdown(wait=wait)
        except Exception:
            logger.exception('Erro ao encerrar executor')
        _EXECUTOR = None
