"""
Models do módulo de autenticação.

Define as classes de dados para usuários, permissões e perfis.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Perfil(str, Enum):
    """Perfis de usuário disponíveis no sistema."""
    ADMINISTRADOR = 'administrador'
    COORDENADOR = 'coordenador'
    PROFESSOR = 'professor'
    
    @classmethod
    def from_string(cls, valor: str) -> 'Perfil':
        """Converte string para enum Perfil."""
        valor_lower = valor.lower().strip()
        for perfil in cls:
            if perfil.value == valor_lower:
                return perfil
        raise ValueError(f"Perfil inválido: {valor}")
    
    @property
    def nome_display(self) -> str:
        """Retorna nome formatado para exibição."""
        nomes = {
            'administrador': 'Administrador',
            'coordenador': 'Coordenador Pedagógico',
            'professor': 'Professor'
        }
        return nomes.get(self.value, self.value.title())


@dataclass
class Permissao:
    """Representa uma permissão do sistema."""
    id: int
    codigo: str
    descricao: str
    modulo: str
    
    def __str__(self) -> str:
        return self.codigo
    
    def __hash__(self) -> int:
        return hash(self.codigo)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Permissao):
            return self.codigo == other.codigo
        if isinstance(other, str):
            return self.codigo == other
        return False


@dataclass
class Usuario:
    """
    Representa um usuário do sistema.
    
    Attributes:
        id: ID único do usuário
        funcionario_id: ID do funcionário vinculado
        username: Nome de usuário para login
        perfil: Perfil de acesso (administrador, coordenador, professor)
        ativo: Se o usuário está ativo
        primeiro_acesso: Se é o primeiro acesso (precisa trocar senha)
        ultimo_acesso: Data/hora do último acesso
        permissoes: Lista de permissões do usuário
        nome_funcionario: Nome do funcionário (para exibição)
        cargo_funcionario: Cargo do funcionário
    """
    id: int
    funcionario_id: int
    username: str
    perfil: Perfil
    ativo: bool = True
    primeiro_acesso: bool = True
    ultimo_acesso: Optional[datetime] = None
    permissoes: List[str] = field(default_factory=list)
    nome_funcionario: Optional[str] = None
    cargo_funcionario: Optional[str] = None
    
    def __post_init__(self):
        """Converte perfil string para enum se necessário."""
        if isinstance(self.perfil, str):
            self.perfil = Perfil.from_string(self.perfil)
    
    @property
    def nome_display(self) -> str:
        """Retorna nome para exibição na interface."""
        return self.nome_funcionario or self.username
    
    @property
    def perfil_display(self) -> str:
        """Retorna nome do perfil formatado."""
        return self.perfil.nome_display
    
    def tem_permissao(self, codigo_permissao: str) -> bool:
        """
        Verifica se o usuário possui uma permissão específica.
        
        Args:
            codigo_permissao: Código da permissão (ex: 'alunos.criar')
            
        Returns:
            True se tem a permissão, False caso contrário
        """
        # Administrador tem todas as permissões
        if self.perfil == Perfil.ADMINISTRADOR:
            return True
        
        return codigo_permissao in self.permissoes
    
    def tem_alguma_permissao(self, permissoes: List[str]) -> bool:
        """
        Verifica se o usuário possui pelo menos uma das permissões.
        
        Args:
            permissoes: Lista de códigos de permissões
            
        Returns:
            True se tem pelo menos uma permissão
        """
        if self.perfil == Perfil.ADMINISTRADOR:
            return True
        
        return any(p in self.permissoes for p in permissoes)
    
    def tem_todas_permissoes(self, permissoes: List[str]) -> bool:
        """
        Verifica se o usuário possui todas as permissões.
        
        Args:
            permissoes: Lista de códigos de permissões
            
        Returns:
            True se tem todas as permissões
        """
        if self.perfil == Perfil.ADMINISTRADOR:
            return True
        
        return all(p in self.permissoes for p in permissoes)
    
    def is_admin(self) -> bool:
        """Verifica se é administrador."""
        return self.perfil == Perfil.ADMINISTRADOR
    
    def is_coordenador(self) -> bool:
        """Verifica se é coordenador."""
        return self.perfil == Perfil.COORDENADOR
    
    def is_professor(self) -> bool:
        """Verifica se é professor."""
        return self.perfil == Perfil.PROFESSOR
    
    def to_dict(self) -> dict:
        """Converte para dicionário (útil para serialização)."""
        return {
            'id': self.id,
            'funcionario_id': self.funcionario_id,
            'username': self.username,
            'perfil': self.perfil.value,
            'ativo': self.ativo,
            'primeiro_acesso': self.primeiro_acesso,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
            'permissoes': self.permissoes,
            'nome_funcionario': self.nome_funcionario,
            'cargo_funcionario': self.cargo_funcionario
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Usuario':
        """Cria instância a partir de dicionário."""
        ultimo_acesso = None
        if data.get('ultimo_acesso'):
            if isinstance(data['ultimo_acesso'], str):
                ultimo_acesso = datetime.fromisoformat(data['ultimo_acesso'])
            else:
                ultimo_acesso = data['ultimo_acesso']
        
        return cls(
            id=data['id'],
            funcionario_id=data['funcionario_id'],
            username=data['username'],
            perfil=data['perfil'],
            ativo=data.get('ativo', True),
            primeiro_acesso=data.get('primeiro_acesso', True),
            ultimo_acesso=ultimo_acesso,
            permissoes=data.get('permissoes', []),
            nome_funcionario=data.get('nome_funcionario'),
            cargo_funcionario=data.get('cargo_funcionario')
        )


@dataclass
class Sessao:
    """
    Representa uma sessão de usuário.
    
    Usada para controle de sessões ativas (opcional).
    """
    id: int
    usuario_id: int
    token: str
    ip_address: Optional[str]
    iniciada_em: datetime
    expira_em: datetime
    ativa: bool = True
