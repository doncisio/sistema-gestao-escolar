"""
Módulo de Autenticação e Controle de Acesso
===========================================

Este módulo implementa o sistema de perfis de usuário, autenticação e
controle de permissões do Sistema de Gestão Escolar.

Componentes:
- models: Classes de dados (Usuario, Permissao, Sessao)
- auth_service: Serviço de autenticação (login, logout, verificação)
- usuario_logado: Singleton para gerenciar usuário da sessão atual
- decorators: Decorators para controle de acesso em funções/métodos
- password_utils: Utilitários para hash e verificação de senhas

Uso básico:
    from auth import AuthService, UsuarioLogado, requer_permissao
    
    # Login
    usuario = AuthService.login('username', 'senha')
    
    # Verificar permissão
    if UsuarioLogado.tem_permissao('alunos.criar'):
        criar_aluno()
    
    # Decorator em função
    @requer_permissao('alunos.criar')
    def criar_aluno():
        ...
"""

from .models import Usuario, Permissao, Perfil
from .usuario_logado import UsuarioLogado
from .auth_service import AuthService
from .decorators import requer_permissao, requer_login, requer_perfil

__all__ = [
    'Usuario',
    'Permissao',
    'Perfil',
    'UsuarioLogado',
    'AuthService',
    'requer_permissao',
    'requer_login',
    'requer_perfil',
]
