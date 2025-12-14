"""
Decorators para controle de acesso.

Fornece decorators que podem ser aplicados em funções/métodos para
verificar permissões antes da execução.
"""

from functools import wraps
from typing import Callable, List, Optional, Union
import tkinter as tk
from tkinter import messagebox

from src.core.config import perfis_habilitados
from src.core.config_logs import get_logger
from .usuario_logado import UsuarioLogado
from .models import Perfil

logger = get_logger(__name__)


def requer_login(func: Callable) -> Callable:
    """
    Decorator que exige que o usuário esteja logado.
    
    Se o sistema de perfis não estiver habilitado, permite a execução.
    Se não houver usuário logado, exibe mensagem de erro.
    
    Uso:
        @requer_login
        def minha_funcao():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Se perfis não estão habilitados, executa normalmente
        if not perfis_habilitados():
            return func(*args, **kwargs)
        
        # Verificar se está logado
        if not UsuarioLogado.esta_logado():
            logger.warning(f"Acesso negado (não logado): {func.__name__}")
            messagebox.showerror(
                "Acesso Negado",
                "Você precisa estar logado para realizar esta ação."
            )
            return None
        
        return func(*args, **kwargs)
    
    return wrapper


def requer_permissao(permissao: Union[str, List[str]], todas: bool = False) -> Callable:
    """
    Decorator que verifica se o usuário tem determinada permissão.
    
    Se o sistema de perfis não estiver habilitado, permite a execução.
    Se não tiver permissão, exibe mensagem de erro.
    
    Args:
        permissao: Código da permissão ou lista de permissões
        todas: Se True, exige todas as permissões; se False, exige apenas uma
        
    Uso:
        @requer_permissao('alunos.criar')
        def criar_aluno():
            ...
        
        @requer_permissao(['alunos.editar', 'alunos.excluir'], todas=True)
        def editar_e_excluir():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Se perfis não estão habilitados, executa normalmente
            if not perfis_habilitados():
                return func(*args, **kwargs)
            
            # Verificar se está logado
            if not UsuarioLogado.esta_logado():
                logger.warning(f"Acesso negado (não logado): {func.__name__}")
                messagebox.showerror(
                    "Acesso Negado",
                    "Você precisa estar logado para realizar esta ação."
                )
                return None
            
            # Normalizar para lista
            permissoes = [permissao] if isinstance(permissao, str) else permissao
            
            # Verificar permissões
            if todas:
                tem_acesso = UsuarioLogado.tem_todas_permissoes(permissoes)
            else:
                tem_acesso = UsuarioLogado.tem_alguma_permissao(permissoes)
            
            if not tem_acesso:
                usuario = UsuarioLogado.get_usuario()
                nome_usuario = usuario.username if usuario else "desconhecido"
                
                logger.warning(
                    f"Acesso negado: {nome_usuario} tentou acessar {func.__name__} "
                    f"(requer: {permissoes})"
                )
                
                # Formatar mensagem
                if len(permissoes) == 1:
                    msg_permissao = f"Permissão necessária: {permissoes[0]}"
                else:
                    conector = "todas" if todas else "uma das"
                    msg_permissao = f"Necessário {conector}: {', '.join(permissoes)}"
                
                messagebox.showerror(
                    "Acesso Negado",
                    f"Você não tem permissão para realizar esta ação.\n\n{msg_permissao}"
                )
                return None
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def requer_perfil(perfis: Union[str, Perfil, List[Union[str, Perfil]]]) -> Callable:
    """
    Decorator que verifica se o usuário tem determinado perfil.
    
    Se o sistema de perfis não estiver habilitado, permite a execução.
    
    Args:
        perfis: Perfil ou lista de perfis permitidos
        
    Uso:
        @requer_perfil('administrador')
        def funcao_admin():
            ...
        
        @requer_perfil(['administrador', 'coordenador'])
        def funcao_admin_ou_coord():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Se perfis não estão habilitados, executa normalmente
            if not perfis_habilitados():
                return func(*args, **kwargs)
            
            # Verificar se está logado
            if not UsuarioLogado.esta_logado():
                logger.warning(f"Acesso negado (não logado): {func.__name__}")
                messagebox.showerror(
                    "Acesso Negado",
                    "Você precisa estar logado para realizar esta ação."
                )
                return None
            
            # Normalizar perfis para lista de valores
            lista_perfis = [perfis] if not isinstance(perfis, list) else perfis
            valores_perfis = []
            for p in lista_perfis:
                if isinstance(p, Perfil):
                    valores_perfis.append(p.value)
                else:
                    valores_perfis.append(p.lower())
            
            # Verificar perfil do usuário
            perfil_atual = UsuarioLogado.get_perfil()
            
            if perfil_atual not in valores_perfis:
                usuario = UsuarioLogado.get_usuario()
                nome_usuario = usuario.username if usuario else "desconhecido"
                
                logger.warning(
                    f"Acesso negado: {nome_usuario} (perfil: {perfil_atual}) "
                    f"tentou acessar {func.__name__} (requer: {valores_perfis})"
                )
                
                # Formatar nomes dos perfis
                nomes_perfis = []
                for v in valores_perfis:
                    try:
                        nomes_perfis.append(Perfil.from_string(v).nome_display)
                    except:
                        nomes_perfis.append(v.title())
                
                messagebox.showerror(
                    "Acesso Negado",
                    f"Esta função é restrita aos perfis:\n• " + 
                    "\n• ".join(nomes_perfis)
                )
                return None
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def verificar_permissao_silencioso(permissao: str) -> bool:
    """
    Verifica permissão sem exibir mensagem de erro.
    
    Útil para verificações condicionais na interface (mostrar/ocultar botões).
    
    Args:
        permissao: Código da permissão
        
    Returns:
        True se tem permissão, False caso contrário
    """
    if not perfis_habilitados():
        return True
    
    return UsuarioLogado.tem_permissao(permissao)


def verificar_perfil_silencioso(perfis: Union[str, List[str]]) -> bool:
    """
    Verifica perfil sem exibir mensagem de erro.
    
    Útil para verificações condicionais na interface.
    
    Args:
        perfis: Perfil ou lista de perfis permitidos
        
    Returns:
        True se tem um dos perfis, False caso contrário
    """
    if not perfis_habilitados():
        return True
    
    perfil_atual = UsuarioLogado.get_perfil()
    
    if perfil_atual is None:
        return False
    
    lista_perfis = [perfis] if isinstance(perfis, str) else perfis
    return perfil_atual in [p.lower() for p in lista_perfis]


class ControleAcesso:
    """
    Classe utilitária para verificações de acesso em lote.
    
    Útil para configurar múltiplos elementos de interface.
    
    Uso:
        controle = ControleAcesso()
        
        if controle.pode('alunos.criar'):
            criar_botao_novo_aluno()
        
        if controle.is_admin():
            criar_menu_admin()
    """
    
    @staticmethod
    def pode(permissao: str) -> bool:
        """Verifica se pode realizar ação."""
        return verificar_permissao_silencioso(permissao)
    
    @staticmethod
    def pode_alguma(permissoes: List[str]) -> bool:
        """Verifica se pode realizar pelo menos uma das ações."""
        if not perfis_habilitados():
            return True
        return UsuarioLogado.tem_alguma_permissao(permissoes)
    
    @staticmethod
    def pode_todas(permissoes: List[str]) -> bool:
        """Verifica se pode realizar todas as ações."""
        if not perfis_habilitados():
            return True
        return UsuarioLogado.tem_todas_permissoes(permissoes)
    
    @staticmethod
    def is_perfil(perfis: Union[str, List[str]]) -> bool:
        """Verifica se é um dos perfis."""
        return verificar_perfil_silencioso(perfis)
    
    @staticmethod
    def is_admin() -> bool:
        """Verifica se é administrador."""
        return verificar_perfil_silencioso('administrador')
    
    @staticmethod
    def is_coordenador() -> bool:
        """Verifica se é coordenador."""
        return verificar_perfil_silencioso('coordenador')
    
    @staticmethod
    def is_professor() -> bool:
        """Verifica se é professor."""
        return verificar_perfil_silencioso('professor')
    
    @staticmethod
    def is_admin_ou_coordenador() -> bool:
        """Verifica se é administrador ou coordenador."""
        return verificar_perfil_silencioso(['administrador', 'coordenador'])
    
    @staticmethod
    def get_perfil_atual() -> Optional[str]:
        """Retorna o perfil atual."""
        if not perfis_habilitados():
            return 'administrador'
        return UsuarioLogado.get_perfil()
    
    @staticmethod
    def get_nome_usuario() -> str:
        """Retorna nome do usuário para exibição."""
        return UsuarioLogado.get_nome_display()
