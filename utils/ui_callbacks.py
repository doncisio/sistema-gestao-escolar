"""
Módulo de callbacks e utilidades para UI.

Este módulo fornece callbacks genéricos e funções de utilidade para a interface
de usuário, eliminando dependências circulares entre módulos.
"""

from typing import Callable, Optional, Any
from tkinter import ttk
from config_logs import get_logger

logger = get_logger(__name__)


def atualizar_treeview(treeview: ttk.Treeview, cursor: Any, query: str) -> None:
    """
    Atualiza o Treeview com dados do banco de dados.
    
    Esta função substitui a função de mesmo nome em Seguranca.py,
    eliminando dependências circulares.
    
    Args:
        treeview: Widget Treeview do tkinter
        cursor: Cursor do banco de dados MySQL
        query: Query SQL para executar
        
    Raises:
        Exception: Se houver erro ao atualizar o Treeview
    """
    try:
        # Verificar se o Treeview ainda existe
        if not treeview or not treeview.winfo_exists():
            logger.error("Erro: O Treeview não está mais ativo.")
            return

        # Limpar os itens existentes no Treeview
        for item in treeview.get_children():
            treeview.delete(item)

        # Executar a consulta SQL e preencher o Treeview
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            treeview.insert("", "end", values=row)
            
        logger.debug(f"Treeview atualizado com {len(rows)} registros")
            
    except Exception as e:
        logger.error(f"Erro ao atualizar o Treeview: {e}")
        raise


class CallbackRegistry:
    """
    Registro de callbacks para evitar dependências circulares.
    
    Permite que módulos registrem callbacks que podem ser chamados
    por outros módulos sem criar imports circulares.
    """
    
    _callbacks: dict[str, Callable] = {}
    
    @classmethod
    def register(cls, name: str, callback: Callable) -> None:
        """
        Registra um callback.
        
        Args:
            name: Nome identificador do callback
            callback: Função a ser registrada
        """
        cls._callbacks[name] = callback
        logger.debug(f"Callback registrado: {name}")
    
    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Remove um callback registrado.
        
        Args:
            name: Nome do callback a remover
        """
        if name in cls._callbacks:
            del cls._callbacks[name]
            logger.debug(f"Callback removido: {name}")
    
    @classmethod
    def call(cls, name: str, *args, **kwargs) -> Optional[Any]:
        """
        Chama um callback registrado.
        
        Args:
            name: Nome do callback a chamar
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
            
        Returns:
            Resultado da função callback ou None se não existir
        """
        callback = cls._callbacks.get(name)
        if callback:
            try:
                return callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Erro ao executar callback '{name}': {e}")
                raise
        else:
            logger.warning(f"Callback '{name}' não encontrado")
            return None
    
    @classmethod
    def has(cls, name: str) -> bool:
        """
        Verifica se um callback está registrado.
        
        Args:
            name: Nome do callback
            
        Returns:
            True se o callback existe, False caso contrário
        """
        return name in cls._callbacks
    
    @classmethod
    def clear(cls) -> None:
        """Remove todos os callbacks registrados."""
        cls._callbacks.clear()
        logger.debug("Todos os callbacks foram removidos")


# Instância global do registro (singleton)
callback_registry = CallbackRegistry()
