import os
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import NameObject
from datetime import datetime
from conexao import conectar_bd
from config_logs import get_logger

logger = get_logger(__name__)

# Dicionário para mapear números dos meses para nomes em português
meses = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

def preencher_pdf_template(pdf_entrada, pdf_saida, dados):
    """Preenche os campos de formulário de um PDF com os dados fornecidos."""
    # Abrir o PDF de entrada
    reader = PdfReader(pdf_entrada)
    writer = PdfWriter()

    for page in reader.pages:
        # Verificar se a página possui campos de formulário
        if "/Annots" in page:
            for annot in page["/Annots"]:
                annot_obj = annot.get_object()
                if "/T" in annot_obj:  # Verifica se o campo tem um nome
                    field_name = annot_obj["/T"]
                    if field_name in dados:
                        # Atualizar o valor do campo
                        annot_obj.update({NameObject("/V"): NameObject(dados[field_name])})
                        logger.debug(f"Preenchendo campo '{field_name}' com valor '{dados[field_name]}'")
                    else:
                        logger.debug(f"Campo '{field_name}' não está nos dados fornecidos.")

        writer.add_page(page)

    # Salvar o PDF preenchido
    with open(pdf_saida, "wb") as output_pdf:
        writer.write(output_pdf)

def obter_dados_banco():
    """Busca os dados dos alunos e seus responsáveis no banco de dados."""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    # Consulta SQL para buscar dados dos alunos
    query = """
        SELECT 
            a.id AS id,
            a.nome AS nome_aluno,
            a.data_nascimento AS nascimento_aluno,
            a.local_nascimento AS local_aluno,
            a.UF_nascimento AS uf_aluno
        FROM 
            alunos a
        JOIN 
            matriculas m ON a.id = m.aluno_id  
        JOIN 
            turmas t ON t.id = m.turma_id
        JOIN 
            serie s ON s.id = t.serie_id
        WHERE 
            m.ano_letivo_id = %s AND s.id = %s
        ORDER BY
            a.nome ASC;
    """
    cursor.execute(query, (1, 11))  # Substitua os valores pelos reais
    dados_alunos = cursor.fetchall()

    alunos = []

    for aluno in dados_alunos:
        # Consulta para buscar responsáveis
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
        cursor.execute(query_responsaveis, (aluno['id'],))
        responsaveis = cursor.fetchall()

        responsavel1 = responsaveis[0]['responsavel'] if len(responsaveis) > 0 else ""
        responsavel2 = responsaveis[1]['responsavel'] if len(responsaveis) > 1 else ""

        # Formatar dados
        data_nascimento = aluno['nascimento_aluno']
        dia, mes, ano = ("", "", "")
        if data_nascimento:
            dia = data_nascimento.day
            mes = meses[data_nascimento.month]
            ano = data_nascimento.year

        hoje = datetime.now()
        dia_atual = hoje.day
        mes_atual = meses[hoje.month]
        ano_atual = hoje.year

        alunos.append({
            "Nome do aluno": aluno['nome_aluno'],
            "Responsável 1": responsavel1,
            "Responsável 2": responsavel2,
            "Dia nascimento": str(dia),
            "Mês nascimento": mes,
            "Ano nascimento": str(ano),
            "Cidade nascimento": aluno['local_aluno'],
            "UF nascimento": aluno['uf_aluno'],
            "Dia atual": str(dia_atual),
            "Mês atual": mes_atual,
            "Ano atual": str(ano_atual),
        })

    return alunos

# Preencher os PDFs com dados dos alunos filtrados
dados_alunos = obter_dados_banco()
pdf_template = "CERTIFICADO form 2024.pdf"

# Criar a pasta 'Diplomas' se não existir
pasta_diplomas = os.path.join(os.getcwd(), 'Diplomas')
os.makedirs(pasta_diplomas, exist_ok=True)

for aluno in dados_alunos:
    nome_pdf_saida = os.path.join(pasta_diplomas, f"{aluno['Nome do aluno']}_certificado.pdf")
    preencher_pdf_template(pdf_template, nome_pdf_saida, aluno)
    logger.info(f"PDF gerado: {nome_pdf_saida}")
