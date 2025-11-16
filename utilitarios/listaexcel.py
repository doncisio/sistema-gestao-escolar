import pandas as pd
from conexao import conectar_bd
from config_logs import get_logger

logger = get_logger(__name__)

def fetch_student_data_with_responsibles(ano_letivo):
    """
    Busca os dados dos alunos com seus respectivos responsáveis e telefones.
    """
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    
    # Consulta SQL para buscar os dados dos alunos e responsáveis
    query = """
        SELECT 
            s.nome AS 'NOME_SERIE',
            t.nome AS 'NOME_TURMA',
            t.turno AS 'TURNO',
            a.nome AS 'NOME DO ALUNO', 
            r.nome AS 'RESPONSAVEL',
            r.telefone AS 'TELEFONE'
        FROM 
            Alunos a
        JOIN 
            Matriculas m ON a.id = m.aluno_id
        JOIN 
            Turmas t ON m.turma_id = t.id
        JOIN 
            Serie s ON t.serie_id = s.id
        LEFT JOIN 
            ResponsaveisAlunos ra ON a.id = ra.aluno_id
        LEFT JOIN 
            Responsaveis r ON ra.responsavel_id = r.id
        WHERE 
            m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
        AND 
            a.escola_id = 60
        AND
            m.status = 'Ativo'
        ORDER BY 
            s.nome, t.nome, t.turno, a.nome;
    """
    try:
        cursor.execute(query, (ano_letivo,))
        dados_aluno = cursor.fetchall()
        return dados_aluno
    except Exception as e:
        logger.exception("Erro ao executar a consulta: %s", str(e))
        return None

def create_excel_with_sheets(ano_letivo):
    """
    Cria um arquivo Excel com uma planilha para cada série e turma,
    onde cada aluno tem uma linha para cada responsável.
    """
    # Busca os dados dos alunos e responsáveis
    dados_aluno = fetch_student_data_with_responsibles(ano_letivo)
    if not dados_aluno:
        logger.warning("Nenhum dado encontrado.")
        return
    
    # Converte os dados em um DataFrame
    df = pd.DataFrame(dados_aluno)
    
    # Verifica se há dados no DataFrame
    if df.empty:
        logger.warning("O DataFrame está vazio.")
        return
    
    # Agrupa os dados por série e turma
    grouped = df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO'])
    
    # Cria um arquivo Excel
    with pd.ExcelWriter('alunos_por_turma.xlsx', engine='xlsxwriter') as writer:
        for (nome_serie, nome_turma, turno), group in grouped:
            # Filtra apenas as colunas necessárias
            sheet_df = group[['NOME DO ALUNO', 'RESPONSAVEL', 'TELEFONE']]
            
            # Define o nome da planilha (limite de 31 caracteres)
            sheet_name = f"{nome_serie[:10]}_{nome_turma[:10]}_{turno}"
            sheet_name = sheet_name[:31]
            
            # Salva a planilha no Excel
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    logger.info("Arquivo Excel criado com sucesso!")

# Executa a função principal
create_excel_with_sheets(2025)