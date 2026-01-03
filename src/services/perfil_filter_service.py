"""
Serviço de filtro de dados por perfil de usuário.

Este módulo centraliza a lógica de filtro de dados baseado no perfil
do usuário logado (administrador, coordenador, professor).

Quando o sistema de perfis está habilitado:
- Administrador: Acesso total a todos os dados
- Coordenador: Acesso total a todos os dados (visualização)
- Professor: Acesso apenas às suas turmas e alunos vinculados
"""

from typing import List, Dict, Any, Optional
from src.core.config import perfis_habilitados, ANO_LETIVO_ATUAL
from src.core.config_logs import get_logger
from auth.usuario_logado import UsuarioLogado
from db.connection import get_cursor

logger = get_logger(__name__)


class PerfilFilterService:
    """
    Serviço para filtrar dados baseado no perfil do usuário logado.
    
    Este serviço fornece métodos para obter IDs de turmas e alunos
    que o usuário atual pode acessar.
    """
    
    @staticmethod
    def get_turmas_usuario() -> Optional[List[int]]:
        """
        Retorna IDs das turmas que o usuário atual pode acessar.
        
        Returns:
            - None: Acesso total (admin/coordenador ou perfis desabilitados)
            - List[int]: Lista de IDs de turmas permitidas (professor)
            - []: Lista vazia se não houver turmas (professor sem turmas)
        """
        # Se perfis não estão habilitados, retorna None (acesso total)
        if not perfis_habilitados():
            return None
        
        # Verificar perfil do usuário
        perfil = UsuarioLogado.get_perfil()
        
        if perfil is None:
            logger.warning("Usuário não logado, retornando lista vazia de turmas")
            return []
        
        # Admin e coordenador têm acesso total
        if perfil in ['administrador', 'coordenador']:
            return None
        
        # Professor: buscar turmas vinculadas
        if perfil == 'professor':
            funcionario_id = UsuarioLogado.get_funcionario_id()
            if funcionario_id is None:
                logger.warning("Professor sem funcionário vinculado")
                return []
            
            return PerfilFilterService._buscar_turmas_professor(funcionario_id)
        
        # Perfil desconhecido: retorna lista vazia por segurança
        logger.warning(f"Perfil desconhecido: {perfil}")
        return []
    
    @staticmethod
    def _buscar_turmas_professor(funcionario_id: int) -> List[int]:
        """
        Busca IDs das turmas vinculadas a um professor.
        
        Busca turmas onde o professor leciona disciplinas (funcionario_disciplinas).
        
        Args:
            funcionario_id: ID do funcionário (professor)
            
        Returns:
            Lista de IDs das turmas
        """
        try:
            with get_cursor() as cursor:
                # Buscar turmas onde o professor leciona disciplinas
                query = """
                    SELECT DISTINCT fd.turma_id
                    FROM funcionario_disciplinas fd
                    INNER JOIN turmas t ON t.id = fd.turma_id
                    WHERE fd.funcionario_id = %s
                    AND t.ano_letivo_id = (
                        SELECT id FROM anosletivos 
                        WHERE ano_letivo = %s
                        LIMIT 1
                    )
                """
                cursor.execute(query, (funcionario_id, ANO_LETIVO_ATUAL))
                resultados = cursor.fetchall()
                
                turmas_ids = []
                for row in resultados:
                    if isinstance(row, dict):
                        turmas_ids.append(row['turma_id'])
                    else:
                        turmas_ids.append(row[0])
                
                logger.debug(f"Professor {funcionario_id} tem acesso a {len(turmas_ids)} turmas")
                return turmas_ids
                
        except Exception as e:
            logger.exception(f"Erro ao buscar turmas do professor: {e}")
            return []
    
    @staticmethod
    def get_alunos_ids_permitidos() -> Optional[List[int]]:
        """
        Retorna IDs dos alunos que o usuário atual pode acessar.
        
        Returns:
            - None: Acesso total (admin/coordenador ou perfis desabilitados)
            - List[int]: Lista de IDs de alunos permitidos (professor)
        """
        turmas_ids = PerfilFilterService.get_turmas_usuario()
        
        if turmas_ids is None:
            return None  # Acesso total
        
        if not turmas_ids:
            return []  # Professor sem turmas
        
        # Buscar alunos matriculados nas turmas
        try:
            with get_cursor() as cursor:
                placeholders = ','.join(['%s'] * len(turmas_ids))
                query = f"""
                    SELECT DISTINCT m.aluno_id
                    FROM matriculas m
                    WHERE m.turma_id IN ({placeholders})
                    AND m.status = 'Ativo'
                """
                cursor.execute(query, tuple(turmas_ids))
                resultados = cursor.fetchall()
                
                alunos_ids = []
                for row in resultados:
                    if isinstance(row, dict):
                        alunos_ids.append(row['aluno_id'])
                    else:
                        alunos_ids.append(row[0])
                
                logger.debug(f"Usuário tem acesso a {len(alunos_ids)} alunos")
                return alunos_ids
                
        except Exception as e:
            logger.exception(f"Erro ao buscar alunos permitidos: {e}")
            return []
    
    @staticmethod
    def filtrar_turmas(turmas: List[Dict], turmas_ids: Optional[List[int]] = None) -> List[Dict]:
        """
        Filtra lista de turmas baseado nos IDs permitidos.
        
        Args:
            turmas: Lista de turmas a filtrar
            turmas_ids: Lista de IDs permitidos (None = sem filtro)
            
        Returns:
            Lista filtrada de turmas
        """
        if turmas_ids is None:
            return turmas
        
        return [t for t in turmas if t.get('id') in turmas_ids]
    
    @staticmethod
    def filtrar_alunos(alunos: List[Dict], alunos_ids: Optional[List[int]] = None) -> List[Dict]:
        """
        Filtra lista de alunos baseado nos IDs permitidos.
        
        Args:
            alunos: Lista de alunos a filtrar
            alunos_ids: Lista de IDs permitidos (None = sem filtro)
            
        Returns:
            Lista filtrada de alunos
        """
        if alunos_ids is None:
            return alunos
        
        return [a for a in alunos if a.get('id') in alunos_ids]
    
    @staticmethod
    def pode_acessar_turma(turma_id: int) -> bool:
        """
        Verifica se o usuário atual pode acessar uma turma específica.
        
        Args:
            turma_id: ID da turma
            
        Returns:
            True se pode acessar, False caso contrário
        """
        turmas_ids = PerfilFilterService.get_turmas_usuario()
        
        if turmas_ids is None:
            return True  # Acesso total
        
        return turma_id in turmas_ids
    
    @staticmethod
    def pode_acessar_aluno(aluno_id: int) -> bool:
        """
        Verifica se o usuário atual pode acessar um aluno específico.
        
        Args:
            aluno_id: ID do aluno
            
        Returns:
            True se pode acessar, False caso contrário
        """
        alunos_ids = PerfilFilterService.get_alunos_ids_permitidos()
        
        if alunos_ids is None:
            return True  # Acesso total
        
        return aluno_id in alunos_ids
    
    @staticmethod
    def get_sql_filtro_turmas(alias: str = "t") -> tuple:
        """
        Retorna cláusula SQL e parâmetros para filtrar turmas.
        
        Args:
            alias: Alias da tabela turmas na query
            
        Returns:
            Tupla (clausula_sql, parametros)
            - clausula_sql: String vazia ou "AND t.id IN (...)"
            - parametros: Lista vazia ou lista de IDs
        """
        turmas_ids = PerfilFilterService.get_turmas_usuario()
        
        if turmas_ids is None:
            return "", []
        
        if not turmas_ids:
            # Retorna condição que sempre é falsa
            return f" AND {alias}.id IN (NULL)", []
        
        placeholders = ','.join(['%s'] * len(turmas_ids))
        return f" AND {alias}.id IN ({placeholders})", turmas_ids
    
    @staticmethod
    def get_info_acesso() -> Dict[str, Any]:
        """
        Retorna informações sobre o acesso do usuário atual.
        
        Returns:
            Dicionário com informações de acesso
        """
        if not perfis_habilitados():
            return {
                'perfil': 'administrador',
                'nome_display': 'Administrador',
                'acesso_total': True,
                'turmas_count': None,
                'alunos_count': None
            }
        
        perfil = UsuarioLogado.get_perfil()
        nome = UsuarioLogado.get_nome_display()
        
        turmas_ids = PerfilFilterService.get_turmas_usuario()
        acesso_total = turmas_ids is None
        
        return {
            'perfil': perfil or 'desconhecido',
            'nome_display': nome,
            'acesso_total': acesso_total,
            'turmas_count': len(turmas_ids) if turmas_ids is not None else None,
            'alunos_count': len(PerfilFilterService.get_alunos_ids_permitidos() or []) if not acesso_total else None
        }


# Funções de conveniência para uso direto
def get_turmas_usuario() -> Optional[List[int]]:
    """Atalho para PerfilFilterService.get_turmas_usuario()"""
    return PerfilFilterService.get_turmas_usuario()


def get_alunos_permitidos() -> Optional[List[int]]:
    """Atalho para PerfilFilterService.get_alunos_ids_permitidos()"""
    return PerfilFilterService.get_alunos_ids_permitidos()


def pode_acessar_turma(turma_id: int) -> bool:
    """Atalho para PerfilFilterService.pode_acessar_turma()"""
    return PerfilFilterService.pode_acessar_turma(turma_id)


def pode_acessar_aluno(aluno_id: int) -> bool:
    """Atalho para PerfilFilterService.pode_acessar_aluno()"""
    return PerfilFilterService.pode_acessar_aluno(aluno_id)


def get_sql_filtro_turmas(alias: str = "t") -> tuple:
    """Atalho para PerfilFilterService.get_sql_filtro_turmas()"""
    return PerfilFilterService.get_sql_filtro_turmas(alias)
