from typing import List, Dict, Optional
from src.core.conexao import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def upsert_horarios(dados: List[Dict]) -> int:
    """
    Insere ou atualiza (upsert) uma lista de horários em `horarios_importados`.
    
    Usa transação para garantir atomicidade: ou todos os registros são salvos,
    ou nenhum é salvo (rollback em caso de erro).
    
    Args:
        dados: Lista de dicionários com campos:
            - turma_id (obrigatório): ID da turma
            - dia (obrigatório): Dia da semana
            - horario (obrigatório): Horário (formato "HH:MM-HH:MM")
            - valor (obrigatório): Texto do horário
            - disciplina_id (opcional): ID da disciplina
            - professor_id (opcional): ID do professor
    
    Returns:
        Número de linhas processadas
        
    Raises:
        ValueError: Se dados estiverem vazios ou campos obrigatórios faltando
        RuntimeError: Se não conseguir conectar ao banco
        Exception: Qualquer erro durante a execução (com rollback automático)
    """
    if not dados:
        raise ValueError("Lista de dados não pode ser vazia")
    
    # Validar campos obrigatórios
    campos_obrigatorios = ['turma_id', 'dia', 'horario', 'valor']
    for idx, item in enumerate(dados):
        if not isinstance(item, dict):
            raise ValueError(f"Item {idx} não é um dicionário válido")
        
        for campo in campos_obrigatorios:
            if campo not in item or item[campo] is None:
                raise ValueError(
                    f"Item {idx} está faltando campo obrigatório '{campo}'. "
                    f"Dados do item: {item}"
                )
    
    # Conectar ao banco
    conn = conectar_bd()
    if not conn:
        raise RuntimeError("Não foi possível conectar ao banco de dados")
    
    cursor = None
    count = 0
    
    try:
        cursor = conn.cursor()
        
        # Iniciar transação explícita
        conn.start_transaction()
        
        sql = (
            "INSERT INTO horarios_importados "
            "(turma_id, dia, horario, valor, disciplina_id, professor_id) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "valor=VALUES(valor), "
            "disciplina_id=VALUES(disciplina_id), "
            "professor_id=VALUES(professor_id)"
        )
        
        for idx, item in enumerate(dados):
            params = (
                item.get('turma_id'),
                item.get('dia'),
                item.get('horario'),
                item.get('valor'),
                item.get('disciplina_id'),
                item.get('professor_id'),
            )
            
            try:
                cursor.execute(sql, params)
                count += 1
            except Exception as e:
                logger.error(
                    f"Erro ao executar SQL para item {idx}: {e}. "
                    f"Params: {params}"
                )
                raise
        
        # Commit da transação
        conn.commit()
        logger.info(f"Upsert concluído com sucesso: {count} linha(s) processada(s)")
        
    except Exception as e:
        # Rollback em caso de erro
        logger.error(f"Erro durante upsert, executando rollback: {e}", exc_info=True)
        if conn:
            try:
                conn.rollback()
                logger.info("Rollback executado com sucesso")
            except Exception as rollback_err:
                logger.error(f"Erro durante rollback: {rollback_err}")
        raise
        
    finally:
        # Limpar recursos
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                logger.warning(f"Erro ao fechar cursor: {e}")
        
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.warning(f"Erro ao fechar conexão: {e}")
    
    return count
