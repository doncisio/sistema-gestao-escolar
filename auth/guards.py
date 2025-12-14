"""
Guards e helpers para validação de permissões na UI.

Este módulo fornece classes e funções auxiliares para facilitar
a validação de permissões em componentes da interface.
"""

from typing import Callable, Optional, List, Union
from functools import wraps
import tkinter.messagebox as mb

from src.core.config import perfis_habilitados
from src.core.config_logs import get_logger
from auth.usuario_logado import UsuarioLogado
from auth.models import Perfil

logger = get_logger(__name__)


class PermissionGuard:
    """
    Classe helper para validar permissões de forma programática.
    
    Útil para validar permissões em tempo de execução sem usar decorators.
    """
    
    @staticmethod
    def check_permission(
        permissao: Union[str, List[str]], 
        show_error: bool = True,
        todas: bool = False
    ) -> bool:
        """
        Verifica se o usuário atual tem a permissão especificada.
        
        Args:
            permissao: Código da permissão ou lista de permissões
            show_error: Se True, exibe mensagem de erro ao usuário
            todas: Se True, exige todas as permissões; se False, apenas uma
            
        Returns:
            bool: True se tem permissão, False caso contrário
            
        Example:
            if PermissionGuard.check_permission('alunos.criar'):
                # Criar aluno
                pass
        """
        # Se perfis não estão habilitados, sempre retorna True
        if not perfis_habilitados():
            return True
        
        # Verificar se está logado
        if not UsuarioLogado.esta_logado():
            if show_error:
                mb.showerror(
                    "Acesso Negado",
                    "Você precisa estar logado para realizar esta ação."
                )
            return False
        
        # Normalizar para lista
        permissoes = [permissao] if isinstance(permissao, str) else permissao
        
        # Verificar permissões
        if todas:
            tem_acesso = UsuarioLogado.tem_todas_permissoes(permissoes)
        else:
            tem_acesso = UsuarioLogado.tem_alguma_permissao(permissoes)
        
        if not tem_acesso and show_error:
            if len(permissoes) == 1:
                msg = f"Permissão necessária: {permissoes[0]}"
            else:
                conector = "todas" if todas else "uma das"
                msg = f"Necessário {conector}: {', '.join(permissoes)}"
            
            mb.showerror(
                "Acesso Negado",
                f"Você não tem permissão para realizar esta ação.\n\n{msg}"
            )
        
        return tem_acesso
    
    @staticmethod
    def check_profile(
        perfis: Union[str, Perfil, List[Union[str, Perfil]]],
        show_error: bool = True
    ) -> bool:
        """
        Verifica se o usuário atual tem o perfil especificado.
        
        Args:
            perfis: Perfil ou lista de perfis permitidos
            show_error: Se True, exibe mensagem de erro ao usuário
            
        Returns:
            bool: True se tem o perfil, False caso contrário
            
        Example:
            if PermissionGuard.check_profile(['admin', 'secretaria']):
                # Função administrativa
                pass
        """
        # Se perfis não estão habilitados, sempre retorna True
        if not perfis_habilitados():
            return True
        
        # Verificar se está logado
        if not UsuarioLogado.esta_logado():
            if show_error:
                mb.showerror(
                    "Acesso Negado",
                    "Você precisa estar logado para realizar esta ação."
                )
            return False
        
        # Normalizar para lista de strings
        perfis_lista: List[str] = []
        if isinstance(perfis, (str, Perfil)):
            perfis_lista = [str(perfis) if isinstance(perfis, Perfil) else perfis]
        else:
            perfis_lista = [str(p) if isinstance(p, Perfil) else p for p in perfis]
        
        # Obter usuário
        usuario = UsuarioLogado.get_usuario()
        if not usuario:
            return False
        
        # Verificar se o perfil do usuário está na lista
        tem_perfil = usuario.perfil in perfis_lista
        
        if not tem_perfil and show_error:
            perfil_usuario = usuario.perfil_display
            mb.showerror(
                "Acesso Negado",
                f"Seu perfil ({perfil_usuario}) não tem acesso a esta funcionalidade.\n\n"
                f"Perfis permitidos: {', '.join(perfis_lista)}"
            )
        
        return tem_perfil
    
    @staticmethod
    def is_readonly_mode(app) -> bool:
        """
        Verifica se a aplicação está em modo somente leitura.
        
        Args:
            app: Instância de Application
            
        Returns:
            bool: True se está em modo somente leitura
        """
        return getattr(app, 'readonly_mode', False)


def disable_on_readonly(func: Callable) -> Callable:
    """
    Decorator que desabilita a função se estiver em modo somente leitura.
    
    Args:
        func: Função a ser decorada
        
    Returns:
        Função decorada
        
    Example:
        @disable_on_readonly
        def editar_aluno(self):
            # Esta função não será executada em modo somente leitura
            pass
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Verificar se self é uma instância de Application ou tem referência
        app = self if hasattr(self, 'readonly_mode') else getattr(self, 'app', None)
        
        if app and PermissionGuard.is_readonly_mode(app):
            mb.showwarning(
                "Modo Somente Leitura",
                "O sistema está em modo somente leitura.\n"
                "Esta ação não está disponível."
            )
            logger.warning(f"Ação bloqueada em modo somente leitura: {func.__name__}")
            return None
        
        return func(self, *args, **kwargs)
    
    return wrapper


# Exemplos de uso documentados
"""
EXEMPLOS DE USO:

1. Usando decorator de permissão:
    
    from auth.guards import require_permission
    
    @require_permission('alunos.criar')
    def criar_aluno(self):
        # Código aqui
        pass

2. Usando decorator de perfil:
    
    from auth.decorators import requer_perfil
    
    @requer_perfil(['administrador', 'secretaria'])
    def funcao_administrativa(self):
        # Código aqui
        pass

3. Validação programática:
    
    from auth.guards import PermissionGuard
    
    def minha_funcao(self):
        if not PermissionGuard.check_permission('alunos.editar'):
            return  # Sem permissão
        
        # Continuar com a edição
        pass

4. Verificar perfil programaticamente:
    
    if PermissionGuard.check_profile(['admin', 'coordenador']):
        # Mostrar opções avançadas
        pass

5. Modo somente leitura:
    
    from auth.guards import disable_on_readonly
    
    @disable_on_readonly
    def editar_funcionario(self):
        # Esta função não executa em modo somente leitura
        pass

6. Múltiplos decorators:
    
    from auth.decorators import requer_perfil, requer_login
    from auth.guards import disable_on_readonly
    
    @requer_login
    @requer_perfil('administrador')
    @disable_on_readonly
    def restaurar_backup(self):
        # Função muito sensível com múltiplas validações
        pass
"""
