"""
Serviço de Logs de Acesso

Este módulo gerencia o registro de logs de ações dos usuários no sistema.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from db.connection import get_connection, get_cursor
from config_logs import get_logger
from auth.usuario_logado import UsuarioLogado

logger = get_logger(__name__)


class LogsAcessoService:
    """Serviço para gerenciar logs de acesso do sistema."""
    
    # Ações padrão do sistema
    ACAO_LOGIN = 'login'
    ACAO_LOGIN_FALHA = 'login_falha'
    ACAO_LOGOUT = 'logout'
    ACAO_CRIAR_USUARIO = 'criar_usuario'
    ACAO_ATUALIZAR_USUARIO = 'atualizar_usuario'
    ACAO_DESATIVAR_USUARIO = 'desativar_usuario'
    ACAO_ATIVAR_USUARIO = 'ativar_usuario'
    ACAO_RESETAR_SENHA = 'resetar_senha'
    ACAO_ACESSO_NEGADO = 'acesso_negado'
    
    @staticmethod
    def registrar(acao: str, detalhes: str = None, 
                  usuario_id: int = None, ip_address: str = None) -> bool:
        """
        Registra uma ação no log de acesso.
        
        Args:
            acao: Código da ação (ex: 'login', 'logout', 'criar_usuario')
            detalhes: Descrição detalhada da ação (opcional)
            usuario_id: ID do usuário (se não informado, usa o logado)
            ip_address: Endereço IP (opcional)
            
        Returns:
            True se registrou com sucesso, False caso contrário
        """
        try:
            # Se não informou usuario_id, usar o logado
            if usuario_id is None:
                usuario_id = UsuarioLogado.get_usuario_id()
            
            # Se ainda não tem usuario_id (login_falha, por exemplo), usar 0
            if usuario_id is None:
                usuario_id = 0
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO logs_acesso (usuario_id, acao, detalhes, ip_address)
                    VALUES (%s, %s, %s, %s)
                """, (usuario_id, acao, detalhes, ip_address))
                conn.commit()
            
            logger.debug(f"Log registrado: {acao} - {detalhes}")
            return True
            
        except Exception as e:
            # Não propagar erro de log para não quebrar o fluxo principal
            logger.warning(f"Erro ao registrar log de acesso: {e}")
            return False
    
    @staticmethod
    def registrar_login(usuario_id: int, username: str, sucesso: bool = True):
        """
        Registra uma tentativa de login.
        
        Args:
            usuario_id: ID do usuário
            username: Nome de usuário
            sucesso: Se o login foi bem-sucedido
        """
        if sucesso:
            LogsAcessoService.registrar(
                LogsAcessoService.ACAO_LOGIN,
                f"Login bem-sucedido: {username}",
                usuario_id
            )
        else:
            LogsAcessoService.registrar(
                LogsAcessoService.ACAO_LOGIN_FALHA,
                f"Tentativa de login falha: {username}",
                usuario_id or 0
            )
    
    @staticmethod
    def registrar_logout():
        """Registra o logout do usuário atual."""
        username = UsuarioLogado.get_username()
        LogsAcessoService.registrar(
            LogsAcessoService.ACAO_LOGOUT,
            f"Logout: {username}"
        )
    
    @staticmethod
    def registrar_acesso_negado(recurso: str):
        """
        Registra uma tentativa de acesso negado.
        
        Args:
            recurso: Nome do recurso que foi negado
        """
        username = UsuarioLogado.get_username() or 'desconhecido'
        LogsAcessoService.registrar(
            LogsAcessoService.ACAO_ACESSO_NEGADO,
            f"Acesso negado a '{recurso}' para usuário: {username}"
        )
    
    @staticmethod
    def listar_logs(
        usuario_id: int = None,
        acao: str = None,
        data_inicio: datetime = None,
        data_fim: datetime = None,
        limite: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista logs de acesso com filtros opcionais.
        
        Args:
            usuario_id: Filtrar por usuário específico
            acao: Filtrar por tipo de ação
            data_inicio: Data inicial do período
            data_fim: Data final do período
            limite: Número máximo de registros
            
        Returns:
            Lista de dicionários com os logs
        """
        try:
            query = """
                SELECT 
                    l.id, l.usuario_id, l.acao, l.detalhes, 
                    l.ip_address, l.created_at,
                    u.username
                FROM logs_acesso l
                LEFT JOIN usuarios u ON l.usuario_id = u.id
                WHERE 1=1
            """
            params = []
            
            if usuario_id is not None:
                query += " AND l.usuario_id = %s"
                params.append(usuario_id)
            
            if acao:
                query += " AND l.acao = %s"
                params.append(acao)
            
            if data_inicio:
                query += " AND l.created_at >= %s"
                params.append(data_inicio)
            
            if data_fim:
                query += " AND l.created_at <= %s"
                params.append(data_fim)
            
            query += " ORDER BY l.created_at DESC LIMIT %s"
            params.append(limite)
            
            with get_cursor() as cursor:
                cursor.execute(query, tuple(params))
                resultados = cursor.fetchall()
            
            logs = []
            for row in resultados:
                if isinstance(row, dict):
                    logs.append(row)
                else:
                    logs.append({
                        'id': row[0],
                        'usuario_id': row[1],
                        'acao': row[2],
                        'detalhes': row[3],
                        'ip_address': row[4],
                        'created_at': row[5],
                        'username': row[6]
                    })
            
            return logs
            
        except Exception as e:
            logger.exception(f"Erro ao listar logs de acesso: {e}")
            return []
    
    @staticmethod
    def listar_ultimos_logins(limite: int = 10) -> List[Dict[str, Any]]:
        """
        Lista os últimos logins bem-sucedidos.
        
        Args:
            limite: Número máximo de registros
            
        Returns:
            Lista de logins recentes
        """
        return LogsAcessoService.listar_logs(
            acao=LogsAcessoService.ACAO_LOGIN,
            limite=limite
        )
    
    @staticmethod
    def listar_tentativas_falhas(dias: int = 7, limite: int = 50) -> List[Dict[str, Any]]:
        """
        Lista tentativas de login que falharam nos últimos dias.
        
        Args:
            dias: Período em dias para buscar
            limite: Número máximo de registros
            
        Returns:
            Lista de tentativas de login falhas
        """
        data_inicio = datetime.now() - timedelta(days=dias)
        return LogsAcessoService.listar_logs(
            acao=LogsAcessoService.ACAO_LOGIN_FALHA,
            data_inicio=data_inicio,
            limite=limite
        )
    
    @staticmethod
    def contar_por_acao(dias: int = 30) -> Dict[str, int]:
        """
        Conta logs por tipo de ação nos últimos dias.
        
        Args:
            dias: Período em dias para contagem
            
        Returns:
            Dicionário com contagem por ação
        """
        try:
            data_inicio = datetime.now() - timedelta(days=dias)
            
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT acao, COUNT(*) as total
                    FROM logs_acesso
                    WHERE created_at >= %s
                    GROUP BY acao
                    ORDER BY total DESC
                """, (data_inicio,))
                resultados = cursor.fetchall()
            
            contagem = {}
            for row in resultados:
                if isinstance(row, dict):
                    contagem[row['acao']] = row['total']
                else:
                    contagem[row[0]] = row[1]
            
            return contagem
            
        except Exception as e:
            logger.exception(f"Erro ao contar logs por ação: {e}")
            return {}
    
    @staticmethod
    def limpar_logs_antigos(dias: int = 90) -> int:
        """
        Remove logs mais antigos que o período especificado.
        
        Args:
            dias: Período em dias (logs mais antigos serão removidos)
            
        Returns:
            Número de registros removidos
        """
        try:
            data_limite = datetime.now() - timedelta(days=dias)
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM logs_acesso WHERE created_at < %s",
                    (data_limite,)
                )
                removidos = cursor.rowcount
                conn.commit()
            
            logger.info(f"Removidos {removidos} logs de acesso antigos (> {dias} dias)")
            return removidos
            
        except Exception as e:
            logger.exception(f"Erro ao limpar logs antigos: {e}")
            return 0


# Funções de conveniência
def registrar_log(acao: str, detalhes: str = None, usuario_id: int = None) -> bool:
    """Atalho para LogsAcessoService.registrar()"""
    return LogsAcessoService.registrar(acao, detalhes, usuario_id)


def registrar_login(usuario_id: int, username: str, sucesso: bool = True):
    """Atalho para LogsAcessoService.registrar_login()"""
    return LogsAcessoService.registrar_login(usuario_id, username, sucesso)


def registrar_logout():
    """Atalho para LogsAcessoService.registrar_logout()"""
    return LogsAcessoService.registrar_logout()


def registrar_acesso_negado(recurso: str):
    """Atalho para LogsAcessoService.registrar_acesso_negado()"""
    return LogsAcessoService.registrar_acesso_negado(recurso)
