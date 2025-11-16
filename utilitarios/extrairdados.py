def obter_dados_aluno(cursor, aluno_id):
    """
    Consulta informações principais do aluno no banco de dados.

    Args:
        cursor: Cursor do banco de dados.
        aluno_id (int): ID do aluno a ser consultado.

    Returns:
        dict: Um dicionário com os dados do aluno, ou None se o aluno não for encontrado.
    """
    query_aluno = """
        SELECT 
            a.nome AS nome_aluno, 
            a.data_nascimento AS nascimento, 
            a.sexo AS sexo,
            s.nome AS nome_serie, 
            t.nome AS nome_turma, 
            t.turno AS turno,
            n.nome AS nivel_ensino, 
            m.status
        FROM 
            Alunos a
        JOIN 
            Matriculas m ON a.id = m.aluno_id
        JOIN 
            Turmas t ON m.turma_id = t.id
        JOIN 
            Serie s ON t.serie_id = s.id
        LEFT JOIN 
            NiveisEnsino n ON s.nivel_id = n.id
        WHERE 
            a.id = %s;
    """
    try:
        # Criar um novo cursor para esta consulta
        novo_cursor = cursor._connection.cursor()
        novo_cursor.execute(query_aluno, (aluno_id,))
        resultado = novo_cursor.fetchone()
        novo_cursor.close()
        
        if not resultado:
            return None  # Aluno não encontrado.

        # Nomeando os campos retornados para melhor legibilidade.
        dados_aluno = {
            "nome_aluno": resultado[0],
            "nascimento": resultado[1],
            "sexo": resultado[2],
            "nome_serie": resultado[3],
            "nome_turma": resultado[4],
            "turno": resultado[5],
            "nivel_ensino": resultado[6],
            "status": resultado[7]
        }

        return dados_aluno
    except Exception as e:
        from config_logs import get_logger
        logger = get_logger(__name__)
        logger.exception(f"Erro ao obter dados do aluno: {e}")
        return None

def obter_dados_responsaveis(cursor, aluno_id):
    """
    Consulta os nomes dos responsáveis por um aluno no banco de dados.

    Args:
        cursor: Cursor do banco de dados.
        aluno_id (int): ID do aluno a ser consultado.

    Returns:
        list: Lista com os nomes dos responsáveis.
              Retorna uma lista vazia se nenhum responsável for encontrado.
    """
    query_responsaveis = """
        SELECT 
            r.nome AS responsavel
        FROM 
            Responsaveis r
        JOIN 
            ResponsaveisAlunos ra ON r.id = ra.responsavel_id  
        WHERE 
            ra.aluno_id = %s;
    """
    try:
        # Criar um novo cursor para esta consulta
        novo_cursor = cursor._connection.cursor()
        novo_cursor.execute(query_responsaveis, (aluno_id,))
        resultados = novo_cursor.fetchall()
        novo_cursor.close()

        # Extrair apenas os nomes dos responsáveis
        responsaveis = [responsavel[0] for responsavel in resultados]

        return responsaveis
    except Exception as e:
        from config_logs import get_logger
        logger = get_logger(__name__)
        logger.exception(f"Erro ao obter dados dos responsáveis: {e}")
        return []

def obter_dados_escola(cursor, escola_id):
    """
    Consulta as informações de uma escola no banco de dados.

    Args:
        cursor: Cursor do banco de dados.
        escola_id (int): ID da escola que deseja buscar.

    Returns:
        dict: Um dicionário contendo os dados da escola ou None se não encontrar.
    """
    query_escola = """
        SELECT 
            e.id AS escola_id, 
            e.nome AS nome_escola, 
            e.endereco AS endereco_escola, 
            e.inep AS inep_escola,
            e.cnpj AS cnpj_escola,
            e.municipio AS municipio_escola
        FROM 
            Escolas e
        WHERE 
            e.id = %s;
    """
    try:
        cursor.execute(query_escola, (escola_id,))
        resultado = cursor.fetchone()

        if resultado:
            return {
                "id": resultado[0],
                "nome": resultado[1],
                "endereco": resultado[2],
                "inep": resultado[3],
                "cnpj": resultado[4],
                "municipio": resultado[5],
            }
        else:
            return None
    except Exception as e:
        from config_logs import get_logger
        logger = get_logger(__name__)
        logger.exception(f"Erro ao obter dados da escola: {e}")
        return None
