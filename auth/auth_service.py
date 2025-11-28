"""
Serviço de Autenticação.

Gerencia login, logout, verificação de credenciais e permissões.
"""

import socket
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, cast

from config_logs import get_logger
from conexao import conectar_bd

from .models import Usuario, Perfil, Permissao
from .password_utils import gerar_hash_senha, verificar_senha, gerar_senha_temporaria

logger = get_logger(__name__)

# Configurações de segurança
MAX_TENTATIVAS_LOGIN = 5
TEMPO_BLOQUEIO_MINUTOS = 15


class AuthService:
    """
    Serviço de autenticação do sistema.
    
    Responsável por:
    - Validar credenciais de login
    - Carregar permissões do usuário
    - Registrar logs de acesso
    - Gerenciar bloqueio por tentativas falhas
    """
    
    @staticmethod
    def login(username: str, senha: str) -> Tuple[Optional[Usuario], str]:
        """
        Realiza o login do usuário.
        
        Args:
            username: Nome de usuário
            senha: Senha em texto plano
            
        Returns:
            Tupla (Usuario ou None, mensagem de erro/sucesso)
        """
        if not username or not senha:
            return None, "Usuário e senha são obrigatórios"
        
        username = username.strip().lower()
        
        try:
            conn = conectar_bd()
            if not conn:
                return None, "Erro de conexão com o banco de dados"
            
            cursor = conn.cursor(dictionary=True)
            
            # Buscar usuário
            cursor.execute("""
                SELECT 
                    u.id,
                    u.funcionario_id,
                    u.username,
                    u.senha_hash,
                    u.perfil,
                    u.ativo,
                    u.primeiro_acesso,
                    u.ultimo_acesso,
                    u.tentativas_login,
                    u.bloqueado_ate,
                    f.nome as nome_funcionario,
                    f.cargo as cargo_funcionario
                FROM usuarios u
                JOIN funcionarios f ON f.id = u.funcionario_id
                WHERE u.username = %s
            """, (username,))
            
            row = cast(Optional[Dict[str, Any]], cursor.fetchone())
            
            if not row:
                # Registrar tentativa com usuário inexistente
                AuthService._registrar_log(
                    cursor, None, username, 'login_falha_usuario_inexistente',
                    f"Tentativa de login com usuário inexistente: {username}"
                )
                conn.commit()
                cursor.close()
                conn.close()
                return None, "Usuário ou senha inválidos"
            
            # Verificar se está bloqueado
            if row['bloqueado_ate']:
                bloqueado_ate = row['bloqueado_ate']
                if isinstance(bloqueado_ate, str):
                    bloqueado_ate = datetime.fromisoformat(bloqueado_ate)
                
                if datetime.now() < bloqueado_ate:
                    minutos_restantes = int((bloqueado_ate - datetime.now()).total_seconds() / 60) + 1
                    cursor.close()
                    conn.close()
                    return None, f"Usuário bloqueado. Tente novamente em {minutos_restantes} minutos"
                else:
                    # Desbloquear usuário (tempo expirou)
                    cursor.execute("""
                        UPDATE usuarios 
                        SET bloqueado_ate = NULL, tentativas_login = 0
                        WHERE id = %s
                    """, (row['id'],))
            
            # Verificar se está ativo
            if not row['ativo']:
                AuthService._registrar_log(
                    cursor, row['id'], username, 'login_falha_usuario_inativo',
                    "Tentativa de login com usuário inativo"
                )
                conn.commit()
                cursor.close()
                conn.close()
                return None, "Usuário desativado. Contate o administrador"
            
            # Verificar senha
            if not verificar_senha(senha, row['senha_hash']):
                # Incrementar tentativas falhas
                tentativas = (row['tentativas_login'] or 0) + 1
                
                if tentativas >= MAX_TENTATIVAS_LOGIN:
                    # Bloquear usuário
                    bloqueado_ate = datetime.now() + timedelta(minutes=TEMPO_BLOQUEIO_MINUTOS)
                    cursor.execute("""
                        UPDATE usuarios 
                        SET tentativas_login = %s, bloqueado_ate = %s
                        WHERE id = %s
                    """, (tentativas, bloqueado_ate, row['id']))
                    
                    AuthService._registrar_log(
                        cursor, row['id'], username, 'login_usuario_bloqueado',
                        f"Usuário bloqueado após {tentativas} tentativas falhas"
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return None, f"Usuário bloqueado por {TEMPO_BLOQUEIO_MINUTOS} minutos após múltiplas tentativas"
                else:
                    cursor.execute("""
                        UPDATE usuarios SET tentativas_login = %s WHERE id = %s
                    """, (tentativas, row['id']))
                    
                    AuthService._registrar_log(
                        cursor, row['id'], username, 'login_falha_senha',
                        f"Senha incorreta (tentativa {tentativas}/{MAX_TENTATIVAS_LOGIN})"
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    restantes = MAX_TENTATIVAS_LOGIN - tentativas
                    return None, f"Usuário ou senha inválidos ({restantes} tentativas restantes)"
            
            # Login bem-sucedido!
            # Resetar tentativas e atualizar último acesso
            cursor.execute("""
                UPDATE usuarios 
                SET tentativas_login = 0, 
                    bloqueado_ate = NULL,
                    ultimo_acesso = NOW()
                WHERE id = %s
            """, (row['id'],))
            
            # Carregar permissões
            permissoes = AuthService._carregar_permissoes(cursor, row['id'], row['perfil'])
            
            # Registrar log de sucesso
            AuthService._registrar_log(
                cursor, row['id'], username, 'login_sucesso',
                f"Login bem-sucedido - Perfil: {row['perfil']}"
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Criar objeto Usuario
            usuario = Usuario(
                id=row['id'],
                funcionario_id=row['funcionario_id'],
                username=row['username'],
                perfil=row['perfil'],
                ativo=row['ativo'],
                primeiro_acesso=row['primeiro_acesso'],
                ultimo_acesso=datetime.now(),
                permissoes=permissoes,
                nome_funcionario=row['nome_funcionario'],
                cargo_funcionario=row['cargo_funcionario']
            )
            
            logger.info(f"✅ Login bem-sucedido: {username} ({usuario.perfil_display})")
            
            return usuario, "Login realizado com sucesso"
            
        except Exception as e:
            logger.exception(f"Erro no login: {e}")
            return None, f"Erro ao realizar login: {str(e)}"
    
    @staticmethod
    def _carregar_permissoes(cursor, usuario_id: int, perfil: str) -> List[str]:
        """
        Carrega todas as permissões do usuário.
        
        Combina permissões do perfil com personalizações do usuário.
        """
        permissoes = set()
        
        # Permissões do perfil
        cursor.execute("""
            SELECT p.codigo
            FROM perfil_permissoes pp
            JOIN permissoes p ON p.id = pp.permissao_id
            WHERE pp.perfil = %s
        """, (perfil,))
        
        for row in cursor.fetchall():
            permissoes.add(row['codigo'])
        
        # Permissões personalizadas do usuário
        cursor.execute("""
            SELECT p.codigo, up.tipo
            FROM usuario_permissoes up
            JOIN permissoes p ON p.id = up.permissao_id
            WHERE up.usuario_id = %s
        """, (usuario_id,))
        
        for row in cursor.fetchall():
            if row['tipo'] == 'adicionar':
                permissoes.add(row['codigo'])
            elif row['tipo'] == 'remover':
                permissoes.discard(row['codigo'])
        
        return list(permissoes)
    
    @staticmethod
    def _registrar_log(cursor: Any, usuario_id: Optional[int], username: str, 
                       acao: str, detalhes: Optional[str] = None) -> None:
        """Registra log de acesso no banco."""
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except:
            ip = None
        
        cursor.execute("""
            INSERT INTO logs_acesso (usuario_id, username_tentativa, acao, detalhes, ip_address)
            VALUES (%s, %s, %s, %s, %s)
        """, (usuario_id, username, acao, detalhes, ip))
    
    @staticmethod
    def logout(usuario: Usuario) -> bool:
        """
        Registra o logout do usuário.
        
        Args:
            usuario: Usuário que está fazendo logout
            
        Returns:
            True se logout registrado com sucesso
        """
        try:
            conn = conectar_bd()
            if not conn:
                return False
            
            cursor = conn.cursor()
            AuthService._registrar_log(
                cursor, usuario.id, usuario.username, 'logout',
                f"Logout do usuário - Perfil: {usuario.perfil.value}"
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"👋 Logout: {usuario.username}")
            return True
            
        except Exception as e:
            logger.exception(f"Erro ao registrar logout: {e}")
            return False
    
    @staticmethod
    def alterar_senha(usuario_id: int, senha_atual: str, nova_senha: str) -> Tuple[bool, str]:
        """
        Altera a senha do usuário.
        
        Args:
            usuario_id: ID do usuário
            senha_atual: Senha atual para verificação
            nova_senha: Nova senha desejada
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            conn = conectar_bd()
            if not conn:
                return False, "Erro de conexão com o banco de dados"
            
            cursor = conn.cursor(dictionary=True)
            
            # Buscar senha atual
            cursor.execute(
                "SELECT senha_hash, username FROM usuarios WHERE id = %s",
                (usuario_id,)
            )
            row = cast(Optional[Dict[str, Any]], cursor.fetchone())
            
            if not row:
                cursor.close()
                conn.close()
                return False, "Usuário não encontrado"
            
            # Verificar senha atual
            if not verificar_senha(senha_atual, row['senha_hash']):
                AuthService._registrar_log(
                    cursor, usuario_id, row['username'], 'alteracao_senha_falha',
                    "Senha atual incorreta"
                )
                conn.commit()
                cursor.close()
                conn.close()
                return False, "Senha atual incorreta"
            
            # Gerar hash da nova senha
            novo_hash = gerar_hash_senha(nova_senha)
            
            # Atualizar senha
            cursor.execute("""
                UPDATE usuarios 
                SET senha_hash = %s, primeiro_acesso = FALSE
                WHERE id = %s
            """, (novo_hash, usuario_id))
            
            AuthService._registrar_log(
                cursor, usuario_id, row['username'], 'alteracao_senha_sucesso',
                "Senha alterada com sucesso"
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"🔐 Senha alterada: usuário ID {usuario_id}")
            return True, "Senha alterada com sucesso"
            
        except Exception as e:
            logger.exception(f"Erro ao alterar senha: {e}")
            return False, f"Erro ao alterar senha: {str(e)}"
    
    @staticmethod
    def resetar_senha(usuario_id: int, admin_id: int) -> Tuple[bool, str, Optional[str]]:
        """
        Reseta a senha do usuário (ação de administrador).
        
        Gera uma senha temporária que o usuário deve trocar no próximo login.
        
        Args:
            usuario_id: ID do usuário a ter senha resetada
            admin_id: ID do administrador realizando a ação
            
        Returns:
            Tupla (sucesso, mensagem, senha_temporaria ou None)
        """
        try:
            conn = conectar_bd()
            if not conn:
                return False, "Erro de conexão com o banco de dados", None
            
            cursor = conn.cursor(dictionary=True)
            
            # Verificar se usuário existe
            cursor.execute(
                "SELECT username FROM usuarios WHERE id = %s",
                (usuario_id,)
            )
            row = cast(Optional[Dict[str, Any]], cursor.fetchone())
            
            if not row:
                cursor.close()
                conn.close()
                return False, "Usuário não encontrado", None
            
            # Gerar senha temporária
            senha_temp = gerar_senha_temporaria(10)
            hash_senha = gerar_hash_senha(senha_temp)
            
            # Atualizar senha e marcar como primeiro acesso
            cursor.execute("""
                UPDATE usuarios 
                SET senha_hash = %s, 
                    primeiro_acesso = TRUE,
                    tentativas_login = 0,
                    bloqueado_ate = NULL
                WHERE id = %s
            """, (hash_senha, usuario_id))
            
            # Registrar log
            AuthService._registrar_log(
                cursor, admin_id, row['username'], 'reset_senha',
                f"Senha resetada pelo admin ID {admin_id}"
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"🔄 Senha resetada: usuário {row['username']} (por admin ID {admin_id})")
            return True, "Senha resetada com sucesso", senha_temp
            
        except Exception as e:
            logger.exception(f"Erro ao resetar senha: {e}")
            return False, f"Erro ao resetar senha: {str(e)}", None
    
    @staticmethod
    def criar_usuario(funcionario_id: int, username: str, perfil: str, 
                      senha: Optional[str] = None, admin_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Cria um novo usuário no sistema.
        
        Args:
            funcionario_id: ID do funcionário a ser vinculado
            username: Nome de usuário desejado
            perfil: Perfil do usuário ('administrador', 'coordenador', 'professor')
            senha: Senha inicial (se None, gera senha temporária)
            admin_id: ID do admin criando o usuário (para log)
            
        Returns:
            Tupla (sucesso, mensagem, senha_gerada ou None)
        """
        try:
            conn = conectar_bd()
            if not conn:
                return False, "Erro de conexão com o banco de dados", None
            
            cursor = conn.cursor(dictionary=True)
            
            # Verificar se funcionário existe
            cursor.execute(
                "SELECT id, nome FROM funcionarios WHERE id = %s",
                (funcionario_id,)
            )
            func = cast(Optional[Dict[str, Any]], cursor.fetchone())
            if not func:
                cursor.close()
                conn.close()
                return False, "Funcionário não encontrado", None
            
            # Verificar se funcionário já tem usuário
            cursor.execute(
                "SELECT id FROM usuarios WHERE funcionario_id = %s",
                (funcionario_id,)
            )
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return False, "Este funcionário já possui um usuário cadastrado", None
            
            # Verificar se username já existe
            cursor.execute(
                "SELECT id FROM usuarios WHERE username = %s",
                (username.lower().strip(),)
            )
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return False, "Este nome de usuário já está em uso", None
            
            # Validar perfil
            try:
                Perfil.from_string(perfil)
            except ValueError:
                cursor.close()
                conn.close()
                return False, f"Perfil inválido: {perfil}", None
            
            # Gerar senha se não fornecida
            senha_gerada = None
            if not senha:
                senha = gerar_senha_temporaria(10)
                senha_gerada = senha
            
            hash_senha = gerar_hash_senha(senha)
            
            # Inserir usuário
            cursor.execute("""
                INSERT INTO usuarios (funcionario_id, username, senha_hash, perfil, primeiro_acesso)
                VALUES (%s, %s, %s, %s, TRUE)
            """, (funcionario_id, username.lower().strip(), hash_senha, perfil.lower()))
            
            novo_id = cursor.lastrowid
            
            # Registrar log
            if admin_id:
                AuthService._registrar_log(
                    cursor, admin_id, username, 'criar_usuario',
                    f"Novo usuário criado: {username} (perfil: {perfil})"
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✨ Novo usuário criado: {username} (perfil: {perfil})")
            return True, f"Usuário {username} criado com sucesso", senha_gerada
            
        except Exception as e:
            logger.exception(f"Erro ao criar usuário: {e}")
            return False, f"Erro ao criar usuário: {str(e)}", None
    
    @staticmethod
    def verificar_permissao(usuario_id: int, codigo_permissao: str) -> bool:
        """
        Verifica se um usuário possui determinada permissão.
        
        Método estático para verificação rápida sem precisar do objeto Usuario.
        
        Args:
            usuario_id: ID do usuário
            codigo_permissao: Código da permissão a verificar
            
        Returns:
            True se tem permissão, False caso contrário
        """
        try:
            conn = conectar_bd()
            if not conn:
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Buscar perfil do usuário
            cursor.execute(
                "SELECT perfil FROM usuarios WHERE id = %s AND ativo = TRUE",
                (usuario_id,)
            )
            row = cast(Optional[Dict[str, Any]], cursor.fetchone())
            
            if not row:
                cursor.close()
                conn.close()
                return False
            
            # Administrador tem todas as permissões
            if row['perfil'] == 'administrador':
                cursor.close()
                conn.close()
                return True
            
            # Verificar permissão do perfil
            cursor.execute("""
                SELECT 1 FROM perfil_permissoes pp
                JOIN permissoes p ON p.id = pp.permissao_id
                WHERE pp.perfil = %s AND p.codigo = %s
            """, (row['perfil'], codigo_permissao))
            
            tem_no_perfil = cursor.fetchone() is not None
            
            # Verificar permissões personalizadas
            cursor.execute("""
                SELECT up.tipo FROM usuario_permissoes up
                JOIN permissoes p ON p.id = up.permissao_id
                WHERE up.usuario_id = %s AND p.codigo = %s
            """, (usuario_id, codigo_permissao))
            
            personalizada = cast(Optional[Dict[str, Any]], cursor.fetchone())
            
            cursor.close()
            conn.close()
            
            if personalizada:
                return personalizada['tipo'] == 'adicionar'
            
            return tem_no_perfil
            
        except Exception as e:
            logger.exception(f"Erro ao verificar permissão: {e}")
            return False
    
    @staticmethod
    def listar_usuarios() -> List[Dict[str, Any]]:
        """
        Lista todos os usuários do sistema.
        
        Returns:
            Lista de dicionários com dados dos usuários
        """
        try:
            conn = conectar_bd()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    u.id,
                    u.funcionario_id,
                    u.username,
                    u.perfil,
                    u.ativo,
                    u.primeiro_acesso,
                    u.ultimo_acesso,
                    f.nome as nome_funcionario,
                    f.cargo as cargo_funcionario
                FROM usuarios u
                JOIN funcionarios f ON f.id = u.funcionario_id
                ORDER BY f.nome
            """)
            
            usuarios = cast(List[Dict[str, Any]], cursor.fetchall())
            
            cursor.close()
            conn.close()
            
            return usuarios
            
        except Exception as e:
            logger.exception(f"Erro ao listar usuários: {e}")
            return []
    
    @staticmethod
    def desativar_usuario(usuario_id: int, admin_id: int) -> Tuple[bool, str]:
        """
        Desativa um usuário do sistema.
        
        Args:
            usuario_id: ID do usuário a desativar
            admin_id: ID do admin realizando a ação
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            conn = conectar_bd()
            if not conn:
                return False, "Erro de conexão com o banco de dados"
            
            cursor = conn.cursor(dictionary=True)
            
            # Verificar se não é o próprio admin
            if usuario_id == admin_id:
                cursor.close()
                conn.close()
                return False, "Você não pode desativar sua própria conta"
            
            # Buscar usuário
            cursor.execute(
                "SELECT username FROM usuarios WHERE id = %s",
                (usuario_id,)
            )
            row = cast(Optional[Dict[str, Any]], cursor.fetchone())
            
            if not row:
                cursor.close()
                conn.close()
                return False, "Usuário não encontrado"
            
            # Desativar
            cursor.execute(
                "UPDATE usuarios SET ativo = FALSE WHERE id = %s",
                (usuario_id,)
            )
            
            AuthService._registrar_log(
                cursor, admin_id, row['username'], 'desativar_usuario',
                f"Usuário {row['username']} desativado"
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"🚫 Usuário desativado: {row['username']}")
            return True, f"Usuário {row['username']} desativado com sucesso"
            
        except Exception as e:
            logger.exception(f"Erro ao desativar usuário: {e}")
            return False, f"Erro ao desativar usuário: {str(e)}"
    
    @staticmethod
    def ativar_usuario(usuario_id: int, admin_id: int) -> Tuple[bool, str]:
        """
        Reativa um usuário desativado.
        
        Args:
            usuario_id: ID do usuário a ativar
            admin_id: ID do admin realizando a ação
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        try:
            conn = conectar_bd()
            if not conn:
                return False, "Erro de conexão com o banco de dados"
            
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT username FROM usuarios WHERE id = %s",
                (usuario_id,)
            )
            row = cast(Optional[Dict[str, Any]], cursor.fetchone())
            
            if not row:
                cursor.close()
                conn.close()
                return False, "Usuário não encontrado"
            
            cursor.execute(
                "UPDATE usuarios SET ativo = TRUE WHERE id = %s",
                (usuario_id,)
            )
            
            AuthService._registrar_log(
                cursor, admin_id, row['username'], 'ativar_usuario',
                f"Usuário {row['username']} reativado"
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Usuário reativado: {row['username']}")
            return True, f"Usuário {row['username']} reativado com sucesso"
            
        except Exception as e:
            logger.exception(f"Erro ao ativar usuário: {e}")
            return False, f"Erro ao ativar usuário: {str(e)}"
