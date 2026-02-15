"""
Script para padronizar todos os CPFs no banco de dados para o formato 000.000.000-00
"""
from src.core.conexao import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def formatar_cpf(cpf):
    """
    Formata CPF para o padrão 000.000.000-00.
    
    Args:
        cpf: String com CPF (pode estar formatado ou não)
        
    Returns:
        CPF formatado ou None se inválido
    """
    if not cpf:
        return None
    
    # Remove caracteres não numéricos
    cpf_numeros = ''.join(filter(str.isdigit, str(cpf)))
    
    # Verifica se tem 11 dígitos
    if len(cpf_numeros) == 11:
        return f"{cpf_numeros[:3]}.{cpf_numeros[3:6]}.{cpf_numeros[6:9]}-{cpf_numeros[9:]}"
    
    # Se não tiver 11 dígitos, retorna None
    return None


def padronizar_cpfs_tabela(cursor, tabela, id_campo='id'):
    """
    Padroniza CPFs de uma tabela específica.
    
    Args:
        cursor: Cursor do banco de dados
        tabela: Nome da tabela
        id_campo: Nome do campo ID da tabela
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processando tabela: {tabela}")
    logger.info(f"{'='*60}")
    
    # Buscar todos os registros com CPF
    query_select = f"SELECT {id_campo}, cpf FROM {tabela} WHERE cpf IS NOT NULL AND cpf != ''"
    cursor.execute(query_select)
    registros = cursor.fetchall()
    
    if not registros:
        logger.info(f"  Nenhum CPF found na tabela {tabela}")
        return 0
    
    logger.info(f"  Encontrados {len(registros)} registros com CPF")
    
    atualizados = 0
    ja_formatados = 0
    invalidos = 0
    
    for registro in registros:
        id_valor = registro[0]
        cpf_atual = registro[1]
        
        # Formatar CPF
        cpf_formatado = formatar_cpf(cpf_atual)
        
        if not cpf_formatado:
            logger.warning(f"  CPF inválido (ID {id_valor}): {cpf_atual}")
            invalidos += 1
            continue
        
        # Verificar se já está formatado
        if cpf_atual == cpf_formatado:
            ja_formatados += 1
            continue
        
        # Atualizar no banco
        query_update = f"UPDATE {tabela} SET cpf = %s WHERE {id_campo} = %s"
        cursor.execute(query_update, (cpf_formatado, id_valor))
        logger.info(f"  ✓ ID {id_valor}: {cpf_atual} → {cpf_formatado}")
        atualizados += 1
    
    logger.info(f"\n  Resultado da tabela {tabela}:")
    logger.info(f"    • Atualizados: {atualizados}")
    logger.info(f"    • Já formatados: {ja_formatados}")
    logger.info(f"    • Inválidos: {invalidos}")
    
    return atualizados


def padronizar_todos_cpfs():
    """
    Padroniza todos os CPFs no banco de dados.
    """
    conn = conectar_bd()
    cursor = conn.cursor()
    
    try:
        logger.info("\n" + "="*60)
        logger.info("INICIANDO PADRONIZAÇÃO DE CPFs")
        logger.info("="*60)
        
        total_atualizados = 0
        
        # Tabela Alunos
        total_atualizados += padronizar_cpfs_tabela(cursor, 'Alunos', 'id')
        
        # Tabela funcionarios
        total_atualizados += padronizar_cpfs_tabela(cursor, 'funcionarios', 'id')
        
        # Tabela Responsaveis
        total_atualizados += padronizar_cpfs_tabela(cursor, 'Responsaveis', 'id')
        
        # Commit das alterações
        conn.commit()
        
        logger.info("\n" + "="*60)
        logger.info(f"✅ PADRONIZAÇÃO CONCLUÍDA!")
        logger.info(f"   Total de CPFs atualizados: {total_atualizados}")
        logger.info("="*60 + "\n")
        
        return True
        
    except Exception as e:
        conn.rollback()
        logger.exception(f"Erro ao padronizar CPFs: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    padronizar_todos_cpfs()
