import xlsxwriter
from src.core.conexao import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Tenta conectar ao banco de dados
conn = conectar_bd()

if conn is None:
    logger.error("Não foi possível conectar ao banco de dados.  Encerrando.")
    exit()  # Encerra o script se a conexão falhar

try:
    cursor = conn.cursor(dictionary=True)  # Obtém o cursor, usando dictionary=True

    # Define o ano letivo desejado
    ano_letivo_id = 26

    # Consulta para obter as séries e turmas
    query_series_turmas = """
    SELECT DISTINCT s.nome AS serie_nome, t.nome AS turma_nome, t.id AS turma_id
    FROM turmas t
    JOIN series s ON t.serie_id = s.id
    WHERE t.ano_letivo_id = %s
    """
    cursor.execute(query_series_turmas, (ano_letivo_id,))
    series_turmas = cursor.fetchall()

    # Cria um novo arquivo Excel
    workbook = xlsxwriter.Workbook('relatorio_alunos.xlsx')

    # Para cada série/turma, cria uma planilha
    for serie_turma in series_turmas:  # Itera diretamente sobre os dicionários
        serie_nome = serie_turma['serie_nome']
        turma_nome = serie_turma['turma_nome']
        turma_id = serie_turma['turma_id']

        # Cria o nome da planilha
        planilha_nome = f"{serie_nome} - {turma_nome}"
        worksheet = workbook.add_worksheet(planilha_nome)

        # Escreve os cabeçalhos na planilha
        worksheet.write(0, 0, 'Nome do Responsável')
        worksheet.write(0, 1, 'Nome do Aluno')
        worksheet.write(0, 2, 'Telefone do Responsável')

        # Consulta para obter os dados dos alunos e responsáveis
        query_alunos = """
        SELECT r.nome AS responsavel_nome, 
               a.nome AS aluno_nome, 
               r.telefone AS responsavel_telefone
        FROM responsaveis r
        JOIN responsaveisalunos ra ON r.id = ra.responsavel_id
        JOIN alunos a ON ra.aluno_id = a.id
        JOIN matriculas m ON a.id = m.aluno_id
        WHERE m.turma_id = %s AND m.ano_letivo_id = %s AND escola_id = 60
        """
        cursor.execute(query_alunos, (turma_id, ano_letivo_id))
        alunos = cursor.fetchall()

        # Escreve os dados dos alunos na planilha
        row = 1
        for aluno in alunos: # Itera diretamente sobre os dicionários
            worksheet.write(row, 0, aluno['responsavel_nome'])
            worksheet.write(row, 1, aluno['aluno_nome'])
            worksheet.write(row, 2, aluno['responsavel_telefone'] or '')  # Insere vazio se não houver telefone
            row += 1

    # Fecha o arquivo Excel
    workbook.close()

    logger.info("Relatório gerado com sucesso!")

except Exception as e:
    logger.exception(f"Um erro inesperado ocorreu: {e}")

finally:
    # Fecha a conexão com o banco de dados
    if conn and conn.is_connected(): # Verifica se conn não é None antes de usar
        cursor.close()
        conn.close()
        logger.info("Conexão MySQL foi fechada")

