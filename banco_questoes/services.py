"""
Service do Banco de Questões BNCC

Serviço para CRUD de questões, avaliações e operações relacionadas.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
import json

from config_logs import get_logger
from db.connection import get_cursor
from config import perfis_habilitados
from auth.usuario_logado import UsuarioLogado

from .models import (
    Questao, QuestaoAlternativa, QuestaoArquivo,
    Avaliacao, AvaliacaoQuestao, AvaliacaoAplicada,
    RespostaAluno, QuestaoFavorita, QuestaoComentario,
    DesempenhoAlunoHabilidade,
    FiltroQuestoes, EstatisticasQuestao,
    TipoQuestao, StatusQuestao, VisibilidadeQuestao,
    ComponenteCurricular, AnoEscolar, DificuldadeQuestao,
    TipoAvaliacao, StatusAvaliacao, StatusAplicacao, NivelDominio
)

logger = get_logger(__name__)


class QuestaoService:
    """Serviço para operações com questões."""
    
    # ========================================================================
    # CRUD DE QUESTÕES
    # ========================================================================
    
    @staticmethod
    def criar(questao: Questao) -> Optional[int]:
        """
        Cria uma nova questão no banco de dados.
        
        Args:
            questao: Objeto Questao com os dados
            
        Returns:
            ID da questão criada ou None em caso de erro
        """
        try:
            with get_cursor(commit=True) as cursor:
                # Inserir questão principal
                sql = """
                    INSERT INTO questoes (
                        componente_curricular, ano_escolar, habilidade_bncc_codigo,
                        habilidade_bncc_secundaria, tipo, dificuldade, tempo_estimado,
                        enunciado, comando, texto_apoio, fonte_texto,
                        gabarito_letra, gabarito_dissertativa, rubrica_correcao,
                        pontuacao_maxima, gabarito_vf, contexto, tags,
                        status, visibilidade, escola_id, autor_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """

                params = (
                    questao.componente_curricular.value if questao.componente_curricular else None,
                    questao.ano_escolar.value if questao.ano_escolar else None,
                    questao.habilidade_bncc_codigo,
                    questao.habilidade_bncc_secundaria,
                    questao.tipo.value if isinstance(questao.tipo, TipoQuestao) else questao.tipo,
                    questao.dificuldade.value if isinstance(questao.dificuldade, DificuldadeQuestao) else questao.dificuldade,
                    questao.tempo_estimado,
                    questao.enunciado,
                    questao.comando,
                    questao.texto_apoio,
                    questao.fonte_texto,
                    questao.gabarito_letra,
                    questao.gabarito_dissertativa,
                    questao.rubrica_correcao,
                    float(questao.pontuacao_maxima) if questao.pontuacao_maxima else 10.0,
                    json.dumps(questao.gabarito_vf) if questao.gabarito_vf else None,
                    questao.contexto.value if questao.contexto else 'escolar',
                    json.dumps(questao.tags) if questao.tags else None,
                    questao.status.value if isinstance(questao.status, StatusQuestao) else questao.status,
                    questao.visibilidade.value if isinstance(questao.visibilidade, VisibilidadeQuestao) else questao.visibilidade,
                    questao.escola_id,
                    questao.autor_id
                )

                cursor.execute(sql, params)
                questao_id = cursor.lastrowid

                # Inserir alternativas se houver
                if questao.alternativas:
                    for alt in questao.alternativas:
                        QuestaoService._inserir_alternativa(cursor, questao_id, alt)

                logger.info(f"Questão criada com ID {questao_id}")
                return questao_id
                
        except Exception as e:
            logger.exception(f"Erro ao criar questão: {e}")
            return None
    
    @staticmethod
    def _inserir_alternativa(cursor, questao_id: int, alt: QuestaoAlternativa) -> Optional[int]:
        """Insere uma alternativa no banco."""
        sql = """
            INSERT INTO questoes_alternativas (
                questao_id, letra, texto, correta, feedback, ordem
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            questao_id, alt.letra, alt.texto, alt.correta, alt.feedback, alt.ordem
        ))
        return cursor.lastrowid
    
    @staticmethod
    def atualizar(questao: Questao) -> bool:
        """
        Atualiza uma questão existente.
        
        Args:
            questao: Objeto Questao com os dados atualizados
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        if not questao.id:
            logger.error("Tentativa de atualizar questão sem ID")
            return False
        
        try:
            with get_cursor() as cursor:
                sql = """
                    UPDATE questoes SET
                        componente_curricular = %s,
                        ano_escolar = %s,
                        habilidade_bncc_codigo = %s,
                        habilidade_bncc_secundaria = %s,
                        tipo = %s,
                        dificuldade = %s,
                        tempo_estimado = %s,
                        enunciado = %s,
                        comando = %s,
                        texto_apoio = %s,
                        fonte_texto = %s,
                        gabarito_letra = %s,
                        gabarito_dissertativa = %s,
                        rubrica_correcao = %s,
                        pontuacao_maxima = %s,
                        gabarito_vf = %s,
                        contexto = %s,
                        tags = %s,
                        status = %s,
                        visibilidade = %s
                    WHERE id = %s
                """
                
                params = (
                    questao.componente_curricular.value if questao.componente_curricular else None,
                    questao.ano_escolar.value if questao.ano_escolar else None,
                    questao.habilidade_bncc_codigo,
                    questao.habilidade_bncc_secundaria,
                    questao.tipo.value if isinstance(questao.tipo, TipoQuestao) else questao.tipo,
                    questao.dificuldade.value if isinstance(questao.dificuldade, DificuldadeQuestao) else questao.dificuldade,
                    questao.tempo_estimado,
                    questao.enunciado,
                    questao.comando,
                    questao.texto_apoio,
                    questao.fonte_texto,
                    questao.gabarito_letra,
                    questao.gabarito_dissertativa,
                    questao.rubrica_correcao,
                    float(questao.pontuacao_maxima) if questao.pontuacao_maxima else 10.0,
                    json.dumps(questao.gabarito_vf) if questao.gabarito_vf else None,
                    questao.contexto.value if questao.contexto else 'escolar',
                    json.dumps(questao.tags) if questao.tags else None,
                    questao.status.value if isinstance(questao.status, StatusQuestao) else questao.status,
                    questao.visibilidade.value if isinstance(questao.visibilidade, VisibilidadeQuestao) else questao.visibilidade,
                    questao.id
                )
                
                cursor.execute(sql, params)
                
                # Atualizar alternativas
                if questao.alternativas:
                    # Remover alternativas antigas
                    cursor.execute("DELETE FROM questoes_alternativas WHERE questao_id = %s", (questao.id,))
                    # Inserir novas
                    for alt in questao.alternativas:
                        QuestaoService._inserir_alternativa(cursor, questao.id, alt)
                
                logger.info(f"Questão {questao.id} atualizada")
                return True
                
        except Exception as e:
            logger.exception(f"Erro ao atualizar questão {questao.id}: {e}")
            return False
    
    @staticmethod
    def buscar_por_id(questao_id: int, carregar_alternativas: bool = True) -> Optional[Questao]:
        """
        Busca uma questão pelo ID.
        
        Args:
            questao_id: ID da questão
            carregar_alternativas: Se deve carregar as alternativas
            
        Returns:
            Questao ou None se não encontrada
        """
        try:
            with get_cursor() as cursor:
                sql = """
                    SELECT q.*, f.nome as autor_nome
                    FROM questoes q
                    LEFT JOIN funcionarios f ON f.id = q.autor_id
                    WHERE q.id = %s
                """
                cursor.execute(sql, (questao_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                questao = Questao.from_row(row)
                
                if carregar_alternativas and questao.is_multipla_escolha:
                    questao.alternativas = QuestaoService._carregar_alternativas(cursor, questao_id)
                
                return questao
                
        except Exception as e:
            logger.exception(f"Erro ao buscar questão {questao_id}: {e}")
            return None
    
    @staticmethod
    def _carregar_alternativas(cursor, questao_id: int) -> List[QuestaoAlternativa]:
        """Carrega alternativas de uma questão."""
        cursor.execute("""
            SELECT * FROM questoes_alternativas 
            WHERE questao_id = %s 
            ORDER BY ordem, letra
        """, (questao_id,))
        
        return [QuestaoAlternativa.from_dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def buscar_alternativas(questao_id: int) -> List[QuestaoAlternativa]:
        """
        Busca alternativas de uma questão (método público).
        
        Args:
            questao_id: ID da questão
            
        Returns:
            Lista de alternativas ordenadas
        """
        try:
            with get_cursor() as cursor:
                return QuestaoService._carregar_alternativas(cursor, questao_id)
        except Exception as e:
            logger.exception(f"Erro ao buscar alternativas da questão {questao_id}: {e}")
            return []
    
    @staticmethod
    def excluir(questao_id: int) -> bool:
        """
        Exclui uma questão.
        
        Args:
            questao_id: ID da questão
            
        Returns:
            True se excluída, False caso contrário
        """
        try:
            with get_cursor() as cursor:
                # Verificar se questão está em alguma avaliação
                cursor.execute("""
                    SELECT COUNT(*) FROM avaliacoes_questoes WHERE questao_id = %s
                """, (questao_id,))
                count = cursor.fetchone()[0]
                
                if count > 0:
                    logger.warning(f"Questão {questao_id} não pode ser excluída pois está em {count} avaliações")
                    return False
                
                # Excluir (cascade vai remover alternativas e arquivos)
                cursor.execute("DELETE FROM questoes WHERE id = %s", (questao_id,))
                
                logger.info(f"Questão {questao_id} excluída")
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.exception(f"Erro ao excluir questão {questao_id}: {e}")
            return False
    
    # ========================================================================
    # BUSCA E FILTROS
    # ========================================================================
    
    @staticmethod
    def buscar(
        filtros: Optional[FiltroQuestoes] = None,
        limite: int = 50,
        offset: int = 0,
        ordenar_por: str = "created_at",
        ordem: str = "DESC"
    ) -> Tuple[List[Questao], int]:
        """
        Busca questões com filtros.
        
        Args:
            filtros: Filtros a aplicar
            limite: Máximo de resultados
            offset: Deslocamento para paginação
            ordenar_por: Campo para ordenação
            ordem: ASC ou DESC
            
        Returns:
            Tupla (lista_questoes, total_sem_limite)
        """
        try:
            with get_cursor() as cursor:
                # Base da query
                sql_base = """
                    SELECT q.*, f.nome as autor_nome
                    FROM questoes q
                    LEFT JOIN funcionarios f ON f.id = q.autor_id
                """
                
                # Construir condições
                conditions = []
                params = []
                
                if filtros:
                    conds, prms = filtros.to_sql_conditions()
                    conditions.extend(conds)
                    params.extend(prms)
                
                # Montar WHERE
                where_clause = ""
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
                
                # Query de contagem
                sql_count = f"SELECT COUNT(*) as total FROM questoes q {where_clause}"
                cursor.execute(sql_count, params)
                total = cursor.fetchone()['total']
                
                # Query principal com ordenação e paginação
                campos_ordenacao = ['created_at', 'updated_at', 'vezes_aplicada', 'taxa_acerto_media', 'dificuldade']
                if ordenar_por not in campos_ordenacao:
                    ordenar_por = 'created_at'
                ordem = 'DESC' if ordem.upper() not in ['ASC', 'DESC'] else ordem.upper()
                
                sql_main = f"""
                    {sql_base}
                    {where_clause}
                    ORDER BY q.{ordenar_por} {ordem}
                    LIMIT %s OFFSET %s
                """
                params.extend([limite, offset])
                
                cursor.execute(sql_main, params)
                rows = cursor.fetchall()
                
                questoes = [Questao.from_row(row) for row in rows]
                
                return questoes, total
                
        except Exception as e:
            logger.exception(f"Erro na busca de questões: {e}")
            return [], 0
    
    @staticmethod
    def buscar_por_habilidade(
        habilidade_codigo: str,
        escola_id: Optional[int] = None,
        apenas_aprovadas: bool = True,
        limite: int = 20
    ) -> List[Questao]:
        """
        Busca questões por código de habilidade BNCC.
        
        Args:
            habilidade_codigo: Código da habilidade (ex: EF07MA02)
            escola_id: Filtrar por escola
            apenas_aprovadas: Se True, retorna apenas questões aprovadas
            limite: Máximo de resultados
            
        Returns:
            Lista de questões
        """
        filtros = FiltroQuestoes(
            habilidade_bncc=habilidade_codigo,
            escola_id=escola_id,
            status=StatusQuestao.APROVADA if apenas_aprovadas else None
        )
        questoes, _ = QuestaoService.buscar(filtros, limite=limite)
        return questoes
    
    # ========================================================================
    # FAVORITOS
    # ========================================================================
    
    @staticmethod
    def favoritar(questao_id: int, professor_id: int, pasta: Optional[str] = None) -> bool:
        """Adiciona questão aos favoritos."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO questoes_favoritas (questao_id, professor_id, pasta)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE pasta = %s
                """, (questao_id, professor_id, pasta, pasta))
                return True
        except Exception as e:
            logger.exception(f"Erro ao favoritar questão: {e}")
            return False
    
    @staticmethod
    def desfavoritar(questao_id: int, professor_id: int) -> bool:
        """Remove questão dos favoritos."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM questoes_favoritas
                    WHERE questao_id = %s AND professor_id = %s
                """, (questao_id, professor_id))
                return True
        except Exception as e:
            logger.exception(f"Erro ao desfavoritar questão: {e}")
            return False
    
    @staticmethod
    def listar_favoritas(professor_id: int, pasta: Optional[str] = None) -> List[Questao]:
        """Lista questões favoritas de um professor."""
        try:
            with get_cursor() as cursor:
                sql = """
                    SELECT q.*, f.nome as autor_nome
                    FROM questoes q
                    INNER JOIN questoes_favoritas qf ON qf.questao_id = q.id
                    LEFT JOIN funcionarios f ON f.id = q.autor_id
                    WHERE qf.professor_id = %s
                """
                params: List[Any] = [professor_id]
                
                if pasta:
                    sql += " AND qf.pasta = %s"
                    params.append(pasta)
                
                sql += " ORDER BY qf.created_at DESC"
                
                cursor.execute(sql, params)
                return [Questao.from_row(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.exception(f"Erro ao listar favoritas: {e}")
            return []
    
    # ========================================================================
    # REVISÃO E APROVAÇÃO
    # ========================================================================
    
    @staticmethod
    def submeter_para_revisao(questao_id: int) -> bool:
        """Submete questão para revisão."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    UPDATE questoes SET status = 'revisao' WHERE id = %s AND status = 'rascunho'
                """, (questao_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Erro ao submeter questão para revisão: {e}")
            return False
    
    @staticmethod
    def aprovar(questao_id: int, revisor_id: int, observacoes: Optional[str] = None) -> bool:
        """Aprova uma questão."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    UPDATE questoes 
                    SET status = 'aprovada', revisada_por = %s, revisada_em = NOW(), observacoes_revisao = %s
                    WHERE id = %s AND status = 'revisao'
                """, (revisor_id, observacoes, questao_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Erro ao aprovar questão: {e}")
            return False
    
    @staticmethod
    def rejeitar(questao_id: int, revisor_id: int, observacoes: str) -> bool:
        """Rejeita uma questão (volta para rascunho)."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    UPDATE questoes 
                    SET status = 'rascunho', revisada_por = %s, revisada_em = NOW(), observacoes_revisao = %s
                    WHERE id = %s AND status = 'revisao'
                """, (revisor_id, observacoes, questao_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Erro ao rejeitar questão: {e}")
            return False


class AvaliacaoService:
    """Serviço para operações com avaliações."""
    
    @staticmethod
    def criar(avaliacao: Avaliacao) -> Optional[int]:
        """Cria uma nova avaliação."""
        try:
            with get_cursor() as cursor:
                sql = """
                    INSERT INTO avaliacoes (
                        titulo, descricao, componente_curricular, ano_escolar, bimestre,
                        tipo, pontuacao_total, tempo_limite, instrucoes, cabecalho_personalizado,
                        mostrar_gabarito_professor, embaralhar_questoes, embaralhar_alternativas,
                        num_versoes, status, escola_id, professor_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                params = (
                    avaliacao.titulo,
                    avaliacao.descricao,
                    avaliacao.componente_curricular.value if avaliacao.componente_curricular else None,
                    avaliacao.ano_escolar.value if avaliacao.ano_escolar else None,
                    avaliacao.bimestre,
                    avaliacao.tipo.value if avaliacao.tipo else 'somativa',
                    float(avaliacao.pontuacao_total) if avaliacao.pontuacao_total else 10.0,
                    avaliacao.tempo_limite,
                    avaliacao.instrucoes,
                    avaliacao.cabecalho_personalizado,
                    avaliacao.mostrar_gabarito_professor,
                    avaliacao.embaralhar_questoes,
                    avaliacao.embaralhar_alternativas,
                    avaliacao.num_versoes,
                    avaliacao.status.value if avaliacao.status else 'rascunho',
                    avaliacao.escola_id,
                    avaliacao.professor_id
                )
                
                cursor.execute(sql, params)
                return cursor.lastrowid
                
        except Exception as e:
            logger.exception(f"Erro ao criar avaliação: {e}")
            return None
    
    @staticmethod
    def adicionar_questao(avaliacao_id: int, questao_id: int, ordem: int = 0, pontuacao: Optional[float] = None) -> bool:
        """Adiciona uma questão à avaliação."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO avaliacoes_questoes (avaliacao_id, questao_id, ordem, pontuacao)
                    VALUES (%s, %s, %s, %s)
                """, (avaliacao_id, questao_id, ordem, pontuacao))
                return True
        except Exception as e:
            logger.exception(f"Erro ao adicionar questão à avaliação: {e}")
            return False
    
    @staticmethod
    def remover_questao(avaliacao_id: int, questao_id: int) -> bool:
        """Remove uma questão da avaliação."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM avaliacoes_questoes
                    WHERE avaliacao_id = %s AND questao_id = %s
                """, (avaliacao_id, questao_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Erro ao remover questão da avaliação: {e}")
            return False
    
    @staticmethod
    def buscar_por_id(avaliacao_id: int, carregar_questoes: bool = True) -> Optional[Avaliacao]:
        """Busca avaliação por ID."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT a.*, f.nome as professor_nome
                    FROM avaliacoes a
                    LEFT JOIN funcionarios f ON f.id = a.professor_id
                    WHERE a.id = %s
                """, (avaliacao_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                avaliacao = Avaliacao(
                    id=row['id'],
                    titulo=row['titulo'],
                    descricao=row.get('descricao'),
                    componente_curricular=ComponenteCurricular(row['componente_curricular']) if row.get('componente_curricular') else None,
                    ano_escolar=AnoEscolar(row['ano_escolar']) if row.get('ano_escolar') else None,
                    bimestre=row.get('bimestre'),
                    tipo=TipoAvaliacao(row['tipo']) if row.get('tipo') else TipoAvaliacao.SOMATIVA,
                    pontuacao_total=Decimal(str(row.get('pontuacao_total', 10))),
                    tempo_limite=row.get('tempo_limite'),
                    instrucoes=row.get('instrucoes'),
                    cabecalho_personalizado=row.get('cabecalho_personalizado'),
                    mostrar_gabarito_professor=bool(row.get('mostrar_gabarito_professor', True)),
                    embaralhar_questoes=bool(row.get('embaralhar_questoes', False)),
                    embaralhar_alternativas=bool(row.get('embaralhar_alternativas', False)),
                    num_versoes=row.get('num_versoes', 1),
                    status=StatusAvaliacao(row['status']) if row.get('status') else StatusAvaliacao.RASCUNHO,
                    escola_id=row.get('escola_id'),
                    professor_id=row.get('professor_id'),
                    professor_nome=row.get('professor_nome'),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                )
                
                if carregar_questoes:
                    avaliacao.questoes = AvaliacaoService._carregar_questoes(cursor, avaliacao_id)
                
                return avaliacao
                
        except Exception as e:
            logger.exception(f"Erro ao buscar avaliação {avaliacao_id}: {e}")
            return None
    
    @staticmethod
    def _carregar_questoes(cursor, avaliacao_id: int) -> List[AvaliacaoQuestao]:
        """Carrega questões de uma avaliação."""
        cursor.execute("""
            SELECT aq.*, q.enunciado, q.tipo, q.habilidade_bncc_codigo
            FROM avaliacoes_questoes aq
            INNER JOIN questoes q ON q.id = aq.questao_id
            WHERE aq.avaliacao_id = %s
            ORDER BY aq.ordem
        """, (avaliacao_id,))
        
        questoes = []
        for row in cursor.fetchall():
            aq = AvaliacaoQuestao(
                id=row['id'],
                avaliacao_id=row['avaliacao_id'],
                questao_id=row['questao_id'],
                ordem=row['ordem'],
                pontuacao=Decimal(str(row['pontuacao'])) if row.get('pontuacao') else None,
                obrigatoria=bool(row.get('obrigatoria', True))
            )
            # Carregar questão completa se necessário
            aq.questao = QuestaoService.buscar_por_id(row['questao_id'])
            questoes.append(aq)
        
        return questoes
    
    @staticmethod
    def listar_por_professor(professor_id: int, status: Optional[StatusAvaliacao] = None) -> List[Avaliacao]:
        """Lista avaliações de um professor."""
        try:
            with get_cursor() as cursor:
                sql = """
                    SELECT a.*, f.nome as professor_nome,
                           (SELECT COUNT(*) FROM avaliacoes_questoes WHERE avaliacao_id = a.id) as total_questoes
                    FROM avaliacoes a
                    LEFT JOIN funcionarios f ON f.id = a.professor_id
                    WHERE a.professor_id = %s
                """
                params: List[Any] = [professor_id]
                
                if status:
                    sql += " AND a.status = %s"
                    params.append(status.value)
                
                sql += " ORDER BY a.created_at DESC"
                
                cursor.execute(sql, params)
                
                avaliacoes = []
                for row in cursor.fetchall():
                    av = Avaliacao(
                        id=row['id'],
                        titulo=row['titulo'],
                        descricao=row.get('descricao'),
                        componente_curricular=ComponenteCurricular(row['componente_curricular']) if row.get('componente_curricular') else None,
                        ano_escolar=AnoEscolar(row['ano_escolar']) if row.get('ano_escolar') else None,
                        bimestre=row.get('bimestre'),
                        status=StatusAvaliacao(row['status']) if row.get('status') else StatusAvaliacao.RASCUNHO,
                        professor_id=row.get('professor_id'),
                        professor_nome=row.get('professor_nome'),
                        created_at=row.get('created_at')
                    )
                    avaliacoes.append(av)
                
                return avaliacoes
                
        except Exception as e:
            logger.exception(f"Erro ao listar avaliações do professor: {e}")
            return []
    
    @staticmethod
    def aplicar_para_turma(
        avaliacao_id: int,
        turma_id: int,
        data_aplicacao: date,
        aplicador_id: int,
        data_limite_lancamento: Optional[date] = None
    ) -> Optional[int]:
        """Registra a aplicação de uma avaliação para uma turma."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO avaliacoes_aplicadas (
                        avaliacao_id, turma_id, data_aplicacao, data_limite_lancamento,
                        status, aplicada_por
                    ) VALUES (%s, %s, %s, %s, 'agendada', %s)
                """, (avaliacao_id, turma_id, data_aplicacao, data_limite_lancamento, aplicador_id))
                
                return cursor.lastrowid
                
        except Exception as e:
            logger.exception(f"Erro ao aplicar avaliação para turma: {e}")
            return None


class RespostaService:
    """Serviço para lançamento e correção de respostas."""
    
    @staticmethod
    def lancar_resposta(
        avaliacao_aplicada_id: int,
        aluno_id: int,
        questao_id: int,
        resposta_letra: Optional[str] = None,
        resposta_texto: Optional[str] = None
    ) -> Optional[int]:
        """Lança resposta de um aluno."""
        try:
            with get_cursor() as cursor:
                # Verificar se já existe resposta
                cursor.execute("""
                    SELECT id FROM respostas_alunos
                    WHERE avaliacao_aplicada_id = %s AND aluno_id = %s AND questao_id = %s
                """, (avaliacao_aplicada_id, aluno_id, questao_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Atualizar
                    cursor.execute("""
                        UPDATE respostas_alunos
                        SET resposta_letra = %s, resposta_texto = %s
                        WHERE id = %s
                    """, (resposta_letra, resposta_texto, existing[0]))
                    return existing[0]
                else:
                    # Inserir
                    cursor.execute("""
                        INSERT INTO respostas_alunos (
                            avaliacao_aplicada_id, aluno_id, questao_id,
                            resposta_letra, resposta_texto
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (avaliacao_aplicada_id, aluno_id, questao_id, resposta_letra, resposta_texto))
                    return cursor.lastrowid
                    
        except Exception as e:
            logger.exception(f"Erro ao lançar resposta: {e}")
            return None
    
    @staticmethod
    def corrigir_automaticamente(avaliacao_aplicada_id: int) -> Dict[str, int]:
        """
        Corrige automaticamente questões de múltipla escolha.
        
        Returns:
            Dicionário com estatísticas da correção
        """
        try:
            with get_cursor() as cursor:
                # Buscar respostas não corrigidas de questões de múltipla escolha
                cursor.execute("""
                    SELECT r.id, r.resposta_letra, q.gabarito_letra, aq.pontuacao
                    FROM respostas_alunos r
                    INNER JOIN questoes q ON q.id = r.questao_id
                    INNER JOIN avaliacoes_questoes aq ON aq.questao_id = q.id
                    INNER JOIN avaliacoes_aplicadas aa ON aa.id = r.avaliacao_aplicada_id AND aa.avaliacao_id = aq.avaliacao_id
                    WHERE r.avaliacao_aplicada_id = %s
                    AND q.tipo = 'multipla_escolha'
                    AND r.correta IS NULL
                """, (avaliacao_aplicada_id,))
                
                respostas = cursor.fetchall()
                
                corretas = 0
                erradas = 0
                
                for resp in respostas:
                    resp_id, resp_letra, gabarito, pontuacao = resp
                    is_correta = resp_letra and resp_letra.upper() == gabarito.upper() if gabarito else False
                    pts = pontuacao if is_correta else 0
                    
                    cursor.execute("""
                        UPDATE respostas_alunos
                        SET correta = %s, pontuacao_obtida = %s
                        WHERE id = %s
                    """, (is_correta, pts, resp_id))
                    
                    if is_correta:
                        corretas += 1
                    else:
                        erradas += 1
                
                return {'corretas': corretas, 'erradas': erradas, 'total': corretas + erradas}
                
        except Exception as e:
            logger.exception(f"Erro na correção automática: {e}")
            return {'corretas': 0, 'erradas': 0, 'total': 0}
    
    @staticmethod
    def corrigir_dissertativa(
        resposta_id: int,
        pontuacao: float,
        corretor_id: int,
        feedback: Optional[str] = None
    ) -> bool:
        """Corrige uma questão dissertativa."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    UPDATE respostas_alunos
                    SET pontuacao_obtida = %s, correta = %s, 
                        corrigida_por = %s, corrigida_em = NOW(),
                        feedback_professor = %s
                    WHERE id = %s
                """, (pontuacao, pontuacao > 0, corretor_id, feedback, resposta_id))
                return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Erro ao corrigir dissertativa: {e}")
            return False


class DesempenhoService:
    """Serviço para análise de desempenho."""
    
    @staticmethod
    def atualizar_desempenho_aluno_habilidade(
        aluno_id: int,
        habilidade_codigo: str,
        ano_letivo_id: int
    ) -> bool:
        """Atualiza o desempenho consolidado de um aluno em uma habilidade."""
        try:
            with get_cursor() as cursor:
                # Calcular estatísticas
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_questoes,
                        SUM(CASE WHEN r.correta = TRUE THEN 1 ELSE 0 END) as total_acertos
                    FROM respostas_alunos r
                    INNER JOIN questoes q ON q.id = r.questao_id
                    INNER JOIN avaliacoes_aplicadas aa ON aa.id = r.avaliacao_aplicada_id
                    INNER JOIN avaliacoes a ON a.id = aa.avaliacao_id
                    INNER JOIN turmas t ON t.id = aa.turma_id
                    WHERE r.aluno_id = %s
                    AND q.habilidade_bncc_codigo = %s
                    AND t.ano_letivo_id = %s
                    AND r.correta IS NOT NULL
                """, (aluno_id, habilidade_codigo, ano_letivo_id))
                
                row = cursor.fetchone()
                total = row[0] or 0
                acertos = row[1] or 0
                
                if total == 0:
                    return True
                
                taxa = (acertos / total) * 100
                nivel = DesempenhoAlunoHabilidade.calcular_nivel_dominio(taxa)
                
                # Upsert
                cursor.execute("""
                    INSERT INTO desempenho_aluno_habilidade (
                        aluno_id, habilidade_bncc_codigo, ano_letivo_id,
                        total_questoes_respondidas, total_acertos, taxa_acerto, nivel_dominio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        total_questoes_respondidas = %s,
                        total_acertos = %s,
                        taxa_acerto = %s,
                        nivel_dominio = %s,
                        updated_at = NOW()
                """, (
                    aluno_id, habilidade_codigo, ano_letivo_id,
                    total, acertos, taxa, nivel.value,
                    total, acertos, taxa, nivel.value
                ))
                
                return True
                
        except Exception as e:
            logger.exception(f"Erro ao atualizar desempenho: {e}")
            return False
    
    @staticmethod
    def obter_desempenho_turma_habilidade(
        turma_id: int,
        habilidade_codigo: str,
        ano_letivo_id: int
    ) -> Dict[str, Any]:
        """Obtém desempenho consolidado de uma turma em uma habilidade."""
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT dah.aluno_id) as total_alunos,
                        AVG(dah.taxa_acerto) as media_taxa,
                        SUM(CASE WHEN dah.nivel_dominio = 'inicial' THEN 1 ELSE 0 END) as nivel_inicial,
                        SUM(CASE WHEN dah.nivel_dominio = 'basico' THEN 1 ELSE 0 END) as nivel_basico,
                        SUM(CASE WHEN dah.nivel_dominio = 'intermediario' THEN 1 ELSE 0 END) as nivel_intermediario,
                        SUM(CASE WHEN dah.nivel_dominio = 'avancado' THEN 1 ELSE 0 END) as nivel_avancado
                    FROM desempenho_aluno_habilidade dah
                    INNER JOIN matriculas m ON m.aluno_id = dah.aluno_id AND m.status = 'Ativo'
                    WHERE m.turma_id = %s
                    AND dah.habilidade_bncc_codigo = %s
                    AND dah.ano_letivo_id = %s
                """, (turma_id, habilidade_codigo, ano_letivo_id))
                
                row = cursor.fetchone()
                
                return {
                    'habilidade': habilidade_codigo,
                    'total_alunos': row['total_alunos'] or 0,
                    'media_taxa_acerto': float(row['media_taxa'] or 0),
                    'distribuicao_niveis': {
                        'inicial': row['nivel_inicial'] or 0,
                        'basico': row['nivel_basico'] or 0,
                        'intermediario': row['nivel_intermediario'] or 0,
                        'avancado': row['nivel_avancado'] or 0
                    }
                }
                
        except Exception as e:
            logger.exception(f"Erro ao obter desempenho da turma: {e}")
            return {}
