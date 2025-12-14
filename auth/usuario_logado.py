"""
Singleton para gerenciar o usuário logado na sessão atual.

Mantém o estado do usuário durante toda a execução da aplicação.
"""

from typing import List, Optional
from src.core.config import perfis_habilitados
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class UsuarioLogado:
    """
    Singleton que mantém o estado do usuário logado.
    
    Esta classe armazena as informações do usuário durante a sessão
    e fornece métodos para verificação de permissões.
    
    Uso:
        # Após login bem-sucedido
        UsuarioLogado.set_usuario(usuario)
        
        # Verificar permissão
        if UsuarioLogado.tem_permissao('alunos.criar'):
            criar_aluno()
        
        # Obter usuário atual
        usuario = UsuarioLogado.get_usuario()
        
        # Logout
        UsuarioLogado.limpar()
    """
    
    _instance = None
    _usuario = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'UsuarioLogado':
        """Retorna a instância singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_usuario(cls, usuario) -> None:
        """
        Define o usuário logado na sessão.
        
        Args:
            usuario: Objeto Usuario retornado pelo AuthService.login()
        """
        cls._usuario = usuario
        if usuario:
            logger.info(f"👤 Usuário definido: {usuario.username} ({usuario.perfil_display})")
    
    @classmethod
    def get_usuario(cls):
        """
        Retorna o usuário logado atual.
        
        Returns:
            Usuario ou None se não houver usuário logado
        """
        return cls._usuario
    
    @classmethod
    def limpar(cls) -> None:
        """
        Remove o usuário da sessão (logout).
        """
        if cls._usuario:
            logger.info(f"👋 Sessão encerrada: {cls._usuario.username}")
        cls._usuario = None
    
    @classmethod
    def esta_logado(cls) -> bool:
        """
        Verifica se há um usuário logado.
        
        Returns:
            True se há usuário logado, False caso contrário
        """
        # Se perfis não estão habilitados, considera sempre logado
        if not perfis_habilitados():
            return True
        return cls._usuario is not None
    
    @classmethod
    def tem_permissao(cls, codigo_permissao: str) -> bool:
        """
        Verifica se o usuário logado possui uma permissão específica.
        
        Se o sistema de perfis não estiver habilitado, sempre retorna True
        (comportamento legado - acesso total).
        
        Args:
            codigo_permissao: Código da permissão (ex: 'alunos.criar')
            
        Returns:
            True se tem permissão, False caso contrário
        """
        # Se perfis não estão habilitados, libera tudo
        if not perfis_habilitados():
            return True
        
        if cls._usuario is None:
            return False
        
        return cls._usuario.tem_permissao(codigo_permissao)
    
    @classmethod
    def tem_alguma_permissao(cls, permissoes: List[str]) -> bool:
        """
        Verifica se o usuário possui pelo menos uma das permissões.
        
        Args:
            permissoes: Lista de códigos de permissões
            
        Returns:
            True se tem pelo menos uma permissão
        """
        if not perfis_habilitados():
            return True
        
        if cls._usuario is None:
            return False
        
        return cls._usuario.tem_alguma_permissao(permissoes)
    
    @classmethod
    def tem_todas_permissoes(cls, permissoes: List[str]) -> bool:
        """
        Verifica se o usuário possui todas as permissões.
        
        Args:
            permissoes: Lista de códigos de permissões
            
        Returns:
            True se tem todas as permissões
        """
        if not perfis_habilitados():
            return True
        
        if cls._usuario is None:
            return False
        
        return cls._usuario.tem_todas_permissoes(permissoes)
    
    @classmethod
    def get_perfil(cls) -> Optional[str]:
        """
        Retorna o perfil do usuário logado.
        
        Returns:
            String do perfil ('administrador', 'coordenador', 'professor') ou None
        """
        if not perfis_habilitados():
            return 'administrador'  # Acesso total quando desabilitado
        
        if cls._usuario is None:
            return None
        
        return cls._usuario.perfil.value
    
    @classmethod
    def get_nome_display(cls) -> str:
        """
        Retorna o nome do usuário para exibição.
        
        Returns:
            Nome do funcionário ou username, ou string padrão se não logado
        """
        if not perfis_habilitados():
            return "Administrador"
        
        if cls._usuario is None:
            return "Não logado"
        
        return cls._usuario.nome_display
    
    @classmethod
    def get_funcionario_id(cls) -> Optional[int]:
        """
        Retorna o ID do funcionário vinculado ao usuário.
        
        Returns:
            ID do funcionário ou None
        """
        if cls._usuario is None:
            return None
        
        return cls._usuario.funcionario_id
    
    @classmethod
    def is_admin(cls) -> bool:
        """
        Verifica se o usuário logado é administrador.
        
        Returns:
            True se é administrador
        """
        if not perfis_habilitados():
            return True
        
        if cls._usuario is None:
            return False
        
        return cls._usuario.is_admin()
    
    @classmethod
    def is_coordenador(cls) -> bool:
        """
        Verifica se o usuário logado é coordenador.
        
        Returns:
            True se é coordenador
        """
        if not perfis_habilitados():
            return False
        
        if cls._usuario is None:
            return False
        
        return cls._usuario.is_coordenador()
    
    @classmethod
    def is_professor(cls) -> bool:
        """
        Verifica se o usuário logado é professor.
        
        Returns:
            True se é professor
        """
        if not perfis_habilitados():
            return False
        
        if cls._usuario is None:
            return False
        
        return cls._usuario.is_professor()
    
    @classmethod
    def precisa_trocar_senha(cls) -> bool:
        """
        Verifica se o usuário precisa trocar a senha (primeiro acesso).
        
        Returns:
            True se é primeiro acesso e precisa trocar senha
        """
        if not perfis_habilitados():
            return False
        
        if cls._usuario is None:
            return False
        
        return cls._usuario.primeiro_acesso
    
    @classmethod
    def get_turmas_permitidas(cls) -> Optional[List[int]]:
        """
        Retorna IDs das turmas que o usuário pode acessar.
        
        Para administradores e coordenadores, retorna None (todas as turmas).
        Para professores, retorna lista de IDs das turmas vinculadas.
        
        Returns:
            Lista de IDs ou None para acesso total
        """
        if not perfis_habilitados():
            return None  # Acesso total
        
        if cls._usuario is None:
            return []  # Nenhuma turma
        
        if cls._usuario.is_admin() or cls._usuario.is_coordenador():
            return None  # Acesso total
        
        # Para professor, buscar turmas vinculadas
        # Esta consulta será implementada quando o relacionamento
        # professor-turma estiver definido no banco
        # Por enquanto retorna None (acesso total) para não bloquear
        return None
    
    @classmethod
    def to_dict(cls) -> Optional[dict]:
        """
        Retorna dados do usuário como dicionário.
        
        Returns:
            Dicionário com dados do usuário ou None
        """
        if cls._usuario is None:
            return None
        
        return cls._usuario.to_dict()
