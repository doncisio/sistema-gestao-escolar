from src.core.conexao import conectar_bd

import logging

logging.basicConfig(level=logging.INFO)

def inserir_no_historico_escolar(aluno_id, disciplina_id, media, ano_letivo_id, escola_id, serie_id):
    """
    Insere ou atualiza o histórico escolar de um aluno.

    Parâmetros:
    aluno_id (int): ID do aluno.
    disciplina_id (int): ID da disciplina.
    media (float): Média do aluno na disciplina.
    ano_letivo_id (int): ID do ano letivo.
    escola_id (int): ID da escola.
    serie_id (int): ID da série.
    """
    
    try:
        with conectar_bd() as conexao:
            with conexao.cursor() as cursor:
                if verificar_registro_existente(cursor, aluno_id, disciplina_id, ano_letivo_id):
                    logging.info("Registro já existe")
                    atualizar_historico(cursor, aluno_id, disciplina_id, media, ano_letivo_id)
                else:
                    logging.info("Inserindo registro")
                    inserir_historico(cursor, aluno_id, disciplina_id, media, ano_letivo_id, escola_id, serie_id)

                conexao.commit()
                
    except Exception as e:
        logging.error(f"Erro ao inserir no histórico escolar: {e}", exc_info=True)

def inserir_historico(cursor, aluno_id, disciplina_id, media, ano_letivo_id, escola_id, serie_id):
    """
    Insere um novo registro no histórico escolar.

    Parâmetros:
    aluno_id (int): ID do aluno.
    disciplina_id (int): ID da disciplina.
    media (float): Média do aluno na disciplina.
    ano_letivo_id (int): ID do ano letivo.
    escola_id (int): ID da escola.
    serie_id (int): ID da série.
    """
    try:
        cursor.execute("""
            INSERT INTO historico_escolar (aluno_id, disciplina_id, media, ano_letivo_id, escola_id, serie_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (aluno_id, disciplina_id, media, ano_letivo_id, escola_id, serie_id))
        logging.info("Registro inserido com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao inserir registro: {e}", exc_info=True)

def verificar_registro_existente(cursor, aluno_id, disciplina_id, ano_letivo_id):
    """
    Verifica se um registro já existe no histórico escolar.

    Parâmetros:
    aluno_id (int): ID do aluno.
    disciplina_id (int): ID da disciplina.
    ano_letivo_id (int): ID do ano letivo.

    Retorna:
    bool: True se o registro existir, False caso contrário.
    """
    cursor.execute("""
        SELECT COUNT(*) FROM historico_escolar 
        WHERE aluno_id = %s AND disciplina_id = %s AND ano_letivo_id = %s
    """, (aluno_id, disciplina_id, ano_letivo_id))
    
    return cursor.fetchone()[0] > 0

def atualizar_historico(cursor, aluno_id, disciplina_id, media, ano_letivo_id):
    """
    Atualiza a média de um aluno em uma disciplina específica no histórico escolar.

    Parâmetros:
    aluno_id (int): ID do aluno.
    disciplina_id (int): ID da disciplina.
    media (float): Nova média do aluno na disciplina.
    ano_letivo_id (int): ID do ano letivo.
    """
    try:
        cursor.execute("""
            UPDATE historico_escolar
            SET media = %s
            WHERE aluno_id = %s AND disciplina_id = %s AND ano_letivo_id = %s
        """, (media, aluno_id, disciplina_id, ano_letivo_id))
        logging.info("Registro atualizado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao atualizar registro: {e}", exc_info=True)