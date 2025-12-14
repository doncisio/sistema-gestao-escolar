"""
RespostaService - Serviço para gerenciamento de respostas e correção de avaliações
Autor: Sistema de Gestão Escolar
Data: 14/12/2025
"""

from src.core.config_logs import get_logger
logger = get_logger(__name__)

from typing import Optional, List, Dict, Tuple
from datetime import datetime
from decimal import Decimal
from src.core.conexao import conectar_bd
import config

class RespostaService:
    """Serviço para gerenciamento de respostas de alunos em avaliações."""
    
    @staticmethod
    def criar_avaliacao_aluno(
        avaliacao_id: int,
        aluno_id: int,
        turma_id: int,
        lancado_por: int,
        data_aplicacao: Optional[datetime] = None,
        avaliacao_aplicada_id: Optional[int] = None,
        presente: bool = True
    ) -> Optional[int]:
        """
        Cria um registro de avaliação para um aluno específico.
        
        Args:
            avaliacao_id: ID da avaliação
            aluno_id: ID do aluno
            turma_id: ID da turma
            lancado_por: ID do professor que lançou
            data_aplicacao: Data de aplicação (default: agora)
            avaliacao_aplicada_id: ID da aplicação por turma (opcional)
            presente: Se o aluno estava presente
            
        Returns:
            ID do registro criado ou None em caso de erro
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if not conn:
                logger.error("Erro ao conectar ao banco de dados")
                return None
                
            cursor = conn.cursor()
            
            # Buscar pontuação máxima da avaliação
            cursor.execute("""
                SELECT pontuacao_total
                FROM avaliacoes
                WHERE id = %s
            """, (avaliacao_id,))
            
            resultado = cursor.fetchone()
            if not resultado:
                logger.error(f"Avaliação {avaliacao_id} não encontrada")
                return None
                
            pontuacao_maxima = resultado[0]
            
            # Inserir registro
            query = """
                INSERT INTO avaliacoes_alunos (
                    avaliacao_id, aluno_id, turma_id, 
                    avaliacao_aplicada_id, data_aplicacao,
                    pontuacao_maxima, presente, lancado_por, lancado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            cursor.execute(query, (
                avaliacao_id,
                aluno_id,
                turma_id,
                avaliacao_aplicada_id,
                data_aplicacao or datetime.now(),
                pontuacao_maxima,
                presente,
                lancado_por
            ))
            
            conn.commit()
            avaliacao_aluno_id = cursor.lastrowid
            
            logger.info(f"Avaliação de aluno criada: ID {avaliacao_aluno_id}")
            return avaliacao_aluno_id
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao criar avaliação de aluno: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def registrar_resposta_objetiva(
        avaliacao_aluno_id: int,
        questao_id: int,
        alternativa_letra: str,
        pontuacao_maxima: Decimal,
        auto_corrigir: bool = True
    ) -> bool:
        """
        Registra resposta de questão objetiva (múltipla escolha).
        
        Args:
            avaliacao_aluno_id: ID da avaliação do aluno
            questao_id: ID da questão
            alternativa_letra: Letra da alternativa (A, B, C, D, E)
            pontuacao_maxima: Pontuação máxima da questão
            auto_corrigir: Se deve corrigir automaticamente (default: True)
            
        Returns:
            True se sucesso, False caso contrário
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Buscar alternativa e gabarito
            cursor.execute("""
                SELECT qa.id, qa.correta, q.gabarito_letra
                FROM questoes_alternativas qa
                INNER JOIN questoes q ON qa.questao_id = q.id
                WHERE qa.questao_id = %s AND qa.letra = %s
            """, (questao_id, alternativa_letra))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                logger.error(f"Alternativa {alternativa_letra} não encontrada para questão {questao_id}")
                return False
                
            alternativa_id, e_correta, gabarito = resultado
            
            # Calcular pontuação se auto-corrigir
            pontuacao_obtida = Decimal('0.00')
            correta = None
            status = 'respondida'
            
            if auto_corrigir:
                correta = e_correta
                pontuacao_obtida = pontuacao_maxima if e_correta else Decimal('0.00')
                status = 'corrigida'
            
            # Inserir ou atualizar resposta
            query = """
                INSERT INTO respostas_questoes (
                    avaliacao_aluno_id, questao_id, alternativa_id, 
                    alternativa_letra, pontuacao_maxima, pontuacao_obtida,
                    correta, status, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    alternativa_id = VALUES(alternativa_id),
                    alternativa_letra = VALUES(alternativa_letra),
                    pontuacao_obtida = VALUES(pontuacao_obtida),
                    correta = VALUES(correta),
                    status = VALUES(status),
                    updated_at = NOW()
            """
            
            cursor.execute(query, (
                avaliacao_aluno_id,
                questao_id,
                alternativa_id,
                alternativa_letra,
                pontuacao_maxima,
                pontuacao_obtida,
                correta,
                status
            ))
            
            conn.commit()
            
            # Se auto-corrigiu, atualizar nota total
            if auto_corrigir:
                RespostaService.calcular_nota_total(avaliacao_aluno_id)
            
            logger.info(f"Resposta objetiva registrada: questão {questao_id}, alternativa {alternativa_letra}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao registrar resposta objetiva: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def registrar_resposta_dissertativa(
        avaliacao_aluno_id: int,
        questao_id: int,
        resposta_texto: str,
        pontuacao_maxima: Decimal,
        resposta_imagem: Optional[str] = None
    ) -> bool:
        """
        Registra resposta de questão dissertativa.
        
        Args:
            avaliacao_aluno_id: ID da avaliação do aluno
            questao_id: ID da questão
            resposta_texto: Texto da resposta
            pontuacao_maxima: Pontuação máxima da questão
            resposta_imagem: Caminho/URL da imagem (opcional)
            
        Returns:
            True se sucesso, False caso contrário
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Inserir ou atualizar resposta
            query = """
                INSERT INTO respostas_questoes (
                    avaliacao_aluno_id, questao_id, resposta_texto,
                    resposta_imagem, pontuacao_maxima, status, updated_at
                ) VALUES (%s, %s, %s, %s, %s, 'nao_corrigida', NOW())
                ON DUPLICATE KEY UPDATE
                    resposta_texto = VALUES(resposta_texto),
                    resposta_imagem = VALUES(resposta_imagem),
                    status = 'nao_corrigida',
                    updated_at = NOW()
            """
            
            cursor.execute(query, (
                avaliacao_aluno_id,
                questao_id,
                resposta_texto,
                resposta_imagem,
                pontuacao_maxima
            ))
            
            conn.commit()
            logger.info(f"Resposta dissertativa registrada: questão {questao_id}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao registrar resposta dissertativa: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def corrigir_resposta(
        resposta_id: int,
        pontuacao_obtida: Decimal,
        corrigido_por: int,
        comentario: Optional[str] = None
    ) -> bool:
        """
        Corrige uma resposta dissertativa manualmente.
        
        Args:
            resposta_id: ID da resposta
            pontuacao_obtida: Pontuação atribuída
            corrigido_por: ID do professor corretor
            comentario: Comentário/feedback (opcional)
            
        Returns:
            True se sucesso, False caso contrário
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Buscar resposta e validar pontuação
            cursor.execute("""
                SELECT avaliacao_aluno_id, pontuacao_maxima
                FROM respostas_questoes
                WHERE id = %s
            """, (resposta_id,))
            
            resultado = cursor.fetchone()
            if not resultado:
                logger.error(f"Resposta {resposta_id} não encontrada")
                return False
                
            avaliacao_aluno_id, pontuacao_maxima = resultado
            
            if pontuacao_obtida > pontuacao_maxima:
                logger.warning(f"Pontuação obtida ({pontuacao_obtida}) maior que máxima ({pontuacao_maxima})")
                pontuacao_obtida = pontuacao_maxima
            
            # Calcular percentual e marcar como correta/incorreta
            percentual = (pontuacao_obtida / pontuacao_maxima) * 100 if pontuacao_maxima > 0 else 0
            correta = pontuacao_obtida >= (pontuacao_maxima * Decimal('0.6'))  # 60% ou mais = correta
            
            # Atualizar resposta
            query = """
                UPDATE respostas_questoes
                SET pontuacao_obtida = %s,
                    percentual_acerto = %s,
                    correta = %s,
                    status = 'corrigida',
                    corrigido_por = %s,
                    corrigido_em = NOW(),
                    comentario_correcao = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            
            cursor.execute(query, (
                pontuacao_obtida,
                percentual,
                correta,
                corrigido_por,
                comentario,
                resposta_id
            ))
            
            conn.commit()
            
            # Atualizar nota total
            RespostaService.calcular_nota_total(avaliacao_aluno_id)
            
            logger.info(f"Resposta {resposta_id} corrigida: {pontuacao_obtida}/{pontuacao_maxima}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao corrigir resposta: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def calcular_nota_total(avaliacao_aluno_id: int) -> bool:
        """
        Recalcula a nota total de uma avaliação de aluno.
        
        Args:
            avaliacao_aluno_id: ID da avaliação do aluno
            
        Returns:
            True se sucesso, False caso contrário
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Chamar procedure de cálculo
            cursor.callproc('calcular_nota_avaliacao_aluno', (avaliacao_aluno_id,))
            conn.commit()
            
            logger.info(f"Nota total recalculada para avaliacao_aluno_id {avaliacao_aluno_id}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao calcular nota total: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def buscar_fila_correcao(
        professor_id: Optional[int] = None,
        turma_id: Optional[int] = None,
        avaliacao_id: Optional[int] = None,
        limite: int = 100
    ) -> List[Dict]:
        """
        Busca respostas dissertativas pendentes de correção.
        
        Args:
            professor_id: Filtrar por professor (opcional)
            turma_id: Filtrar por turma (opcional)
            avaliacao_id: Filtrar por avaliação (opcional)
            limite: Número máximo de registros
            
        Returns:
            Lista de dicionários com dados das respostas pendentes
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if not conn:
                return []
                
            cursor = conn.cursor(dictionary=True)
            
            # Montar query com filtros dinâmicos
            where_clauses = []
            params = []
            
            if professor_id:
                where_clauses.append("professor_id = %s")
                params.append(professor_id)
            
            if turma_id:
                where_clauses.append("turma_id = %s")
                params.append(turma_id)
            
            if avaliacao_id:
                where_clauses.append("avaliacao_id = %s")
                params.append(avaliacao_id)
            
            where_sql = " AND " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
                SELECT *
                FROM vw_fila_correcao
                WHERE 1=1 {where_sql}
                ORDER BY data_aplicacao ASC, aluno_nome ASC
                LIMIT %s
            """
            
            params.append(limite)
            cursor.execute(query, tuple(params))
            
            respostas = cursor.fetchall()
            logger.info(f"{len(respostas)} respostas pendentes encontradas")
            return respostas
            
        except Exception as e:
            logger.error(f"Erro ao buscar fila de correção: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def buscar_respostas_aluno(
        avaliacao_aluno_id: int
    ) -> List[Dict]:
        """
        Busca todas as respostas de um aluno em uma avaliação.
        
        Args:
            avaliacao_aluno_id: ID da avaliação do aluno
            
        Returns:
            Lista de dicionários com dados das respostas
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if not conn:
                return []
                
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    rq.*,
                    q.enunciado,
                    q.tipo AS questao_tipo,
                    q.dificuldade,
                    qa.letra AS alternativa_selecionada_letra,
                    qa.texto AS alternativa_selecionada_texto
                FROM respostas_questoes rq
                INNER JOIN questoes q ON rq.questao_id = q.id
                LEFT JOIN questoes_alternativas qa ON rq.alternativa_id = qa.id
                WHERE rq.avaliacao_aluno_id = %s
                ORDER BY q.id
            """
            
            cursor.execute(query, (avaliacao_aluno_id,))
            respostas = cursor.fetchall()
            
            return respostas
            
        except Exception as e:
            logger.error(f"Erro ao buscar respostas do aluno: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def finalizar_avaliacao_aluno(
        avaliacao_aluno_id: int,
        corrigido_por: int
    ) -> bool:
        """
        Finaliza a correção de uma avaliação de aluno.
        
        Args:
            avaliacao_aluno_id: ID da avaliação do aluno
            corrigido_por: ID do professor que finalizou
            
        Returns:
            True se sucesso, False caso contrário
        """
        conn = None
        cursor = None
        try:
            conn = conectar_bd()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Verificar se todas as respostas foram corrigidas
            cursor.execute("""
                SELECT COUNT(*) 
                FROM respostas_questoes
                WHERE avaliacao_aluno_id = %s 
                  AND status != 'corrigida'
            """, (avaliacao_aluno_id,))
            
            pendentes = cursor.fetchone()[0]
            
            if pendentes > 0:
                logger.warning(f"Ainda existem {pendentes} respostas não corrigidas")
                return False
            
            # Atualizar status
            cursor.execute("""
                UPDATE avaliacoes_alunos
                SET status = 'finalizada',
                    corrigido_por = %s,
                    finalizado_em = NOW()
                WHERE id = %s
            """, (corrigido_por, avaliacao_aluno_id))
            
            conn.commit()
            logger.info(f"Avaliação de aluno {avaliacao_aluno_id} finalizada")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro ao finalizar avaliação: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
