import os
import io
import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from config import get_image_path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle
import platform
from conexao import conectar_bd
from types import ModuleType
from typing import Optional
from gerarPDF import salvar_e_abrir_pdf
from utilitarios.gerenciador_documentos import salvar_documento_sistema
from utilitarios.tipos_documentos import TIPO_DECLARACAO
from config_logs import get_logger

logger = get_logger(__name__)
messagebox: Optional[ModuleType] = None
try:
    import tkinter.messagebox as messagebox  # type: ignore
except Exception:
    # Em ambientes sem tkinter (ex: análise estática), mantém variável definida
    messagebox = None

def obter_dados_escola(cursor, escola_id):
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
    cursor.execute(query_escola, (escola_id,))
    return cursor.fetchone()

def obter_dados_aluno(cursor, aluno_id):
    # Primeiro tenta obter o ano letivo atual
    cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = YEAR(CURDATE())")
    ano_atual = cursor.fetchone()
    
    if not ano_atual:
        cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
        ano_atual = cursor.fetchone()
        
    ano_letivo_id = ano_atual[0] if ano_atual else 1  # Acessa o primeiro elemento da tupla
    
    query_aluno = """
        SELECT 
            a.nome AS nome_aluno, 
            a.data_nascimento AS nascimento, 
            a.sexo AS sexo,
            s.nome AS nome_serie, 
            t.nome AS nome_turma, 
            t.turno AS turno,
            n.nome AS nivel_ensino
        FROM 
            Alunos a
        JOIN 
            Matriculas m ON a.id = m.aluno_id
        JOIN 
            Turmas t ON m.turma_id = t.id
        JOIN 
            series s ON t.serie_id = s.id
        LEFT JOIN 
            NiveisEnsino n ON s.nivel_id = n.id
        WHERE
            m.ano_letivo_id = %s
            AND
            a.id = %s;
    """
    cursor.execute(query_aluno, (ano_letivo_id, aluno_id))
    resultado = cursor.fetchone()
    
    if not resultado:
        # Tenta buscar apenas os dados básicos do aluno, sem matrícula
        query_simples = """
            SELECT 
                a.nome AS nome_aluno, 
                a.data_nascimento AS nascimento, 
                a.sexo AS sexo,
                NULL AS nome_serie, 
                NULL AS nome_turma, 
                NULL AS turno,
                NULL AS nivel_ensino
            FROM 
                Alunos a
            WHERE
                a.id = %s;
        """
        cursor.execute(query_simples, (aluno_id,))
        resultado = cursor.fetchone()
        
    return resultado

def obter_responsaveis(cursor, aluno_id):
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
    cursor.execute(query_responsaveis, (aluno_id,))
    return cursor.fetchall()

from utils.dates import formatar_data_extenso as formatar_data

def criar_cabecalho(dados_escola):
    nome_escola, inep_escola, cnpj_escola, endereco_escola, municipio_escola = dados_escola[1], dados_escola[3], dados_escola[4], dados_escola[2], dados_escola[5]
    return [
        "ESTADO DO MARANHÃO",
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        f"<b>{nome_escola}</b>",
        f"<b>INEP: {inep_escola}</b>",
        f"<b>CNPJ: {cnpj_escola}</b>"
    ]

def criar_rodape(dados_escola):
    endereco_escola, municipio_escola = dados_escola[2], dados_escola[5]
    return f"{endereco_escola} - {municipio_escola}."

def criar_pdf(buffer, cabecalho, rodape_texto, dados_aluno, responsaveis, marcacoes, nome_escola, motivo_outros=""):
    nome_aluno, nascimento, sexo, nome_serie, nome_turma, turno, nivel_ensino = dados_aluno
    turma = f"{nome_serie} {nome_turma}"
    responsavel1 = responsaveis[0][0] if len(responsaveis) > 0 else None
    responsavel2 = responsaveis[1][0] if len(responsaveis) > 1 else None

    data_nascimento = pd.to_datetime(nascimento).strftime("%d/%m/%Y") if pd.notnull(nascimento) else ""
    data_documento = formatar_data(datetime.datetime.now())

    genero_aluno = 'feminino' if sexo == 'F' else 'masculino'

    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        leftMargin=85, 
        rightMargin=56, 
        topMargin=85, 
        bottomMargin=56
    )
    elements = []

    figura_superior = str(get_image_path('pacologo.png'))
    figura_inferior = str(get_image_path('logopacobranco.png'))

    data = [
        [Image(figura_superior, width=1 * inch, height=1 * inch),
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
         Image(figura_inferior, width=1.5 * inch, height=1 * inch)]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4.5 * inch, 1.32 * inch])
    table_style = TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')])
    table.setStyle(table_style)
    elements.append(table)

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("<b>Declaração Escolar</b>", ParagraphStyle(name='DeclaracaoTitulo', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.5 * inch))

    style_declaracao = ParagraphStyle(
        name='DeclaracaoTexto',
        fontSize=12,
        alignment=4,
        leading=18
    )

    if pd.isna(responsavel1):
        if pd.isna(responsavel2):
            elements.append(Paragraph(
                f"Declaramos, para os devidos fins, que <b>{nome_aluno}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de, está regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} na <b>{nome_escola}</b> cursando o <b>{turma} </b> do {nivel_ensino} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if turno == 'MAT' else 'no turno <b>vespertino</b>'}.",
                style_declaracao))
        else:
            elements.append(Paragraph(
                f"Declaramos, para os devidos fins, que <b>{nome_aluno}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel2}</b>, está regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} na <b>{nome_escola}</b> cursando o <b>{turma}</b> do {nivel_ensino} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if turno == 'MAT' else 'no turno <b>vespertino</b>'}.",
                style_declaracao))
    elif pd.isna(responsavel2):
        elements.append(Paragraph(
            f"Declaramos, para os devidos fins, que <b>{nome_aluno}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel1}</b>, está regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} na <b>{nome_escola}</b> cursando o <b>{turma} </b> do {nivel_ensino} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if turno == 'MAT' else 'no turno <b>vespertino</b>'}.",
            style_declaracao))
    else:
        elements.append(Paragraph(
            f"Declaramos, para os devidos fins, que <b>{nome_aluno}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel1}</b> e <b>{responsavel2}</b>, está regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} na <b>{nome_escola}</b> cursando o <b>{turma}</b> do {nivel_ensino} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if turno == 'MAT' else 'no turno <b>vespertino</b>'}.",
            style_declaracao))

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Nada consta que desabone sua conduta.",  ParagraphStyle(name='texto direita', fontSize=12, alignment=2)))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Por ser verdade, firmo o presente documento.", ParagraphStyle(name='texto direita', fontSize=12, alignment=2)))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("<b>Declaração para fim de:</b>", style_declaracao))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Calcular a largura disponível (considerando as margens)
    largura_disponivel = letter[0] - 85 - 56  # largura da página - margem esquerda - margem direita
    
    # Usar strings simples em vez de Paragraph para evitar quebras de linha
    transferencia = f"{'(X)' if marcacoes[0][0] else '(   )'} Transferência"
    bolsa_familia = f"{'(X)' if marcacoes[0][1] else '(   )'} Bolsa Família"
    trabalho = f"{'(X)' if marcacoes[0][2] else '(   )'} Trabalho"
    
    # Texto da opção "Outros"
    if marcacoes[0][3]:
        # Para "Outros" usamos Paragraph para ter o negrito, mas em uma célula separada
        outros_check = "(X) Outros:"
        motivo_formatado = Paragraph(f"<b>{motivo_outros}</b>", 
                                    ParagraphStyle(name='EstiloMotivo', fontSize=12))
    else:
        outros_check = "(   ) Outros:"
        motivo_formatado = "_____________________"
        
    # Criar a tabela com todas as opções em texto simples
    data2 = [[transferencia, bolsa_familia, trabalho, outros_check, motivo_formatado]]
    
    # Distribuir largura mais uniformemente
    table2 = Table(data2, colWidths=[largura_disponivel*0.22, largura_disponivel*0.22, 
                                     largura_disponivel*0.17, largura_disponivel*0.14, None])
    
    # Estilo da tabela
    table2.setStyle(TableStyle([
        ('ALIGN', (0, 0), (3, 0), 'LEFT'),   # Alinhar à esquerda as 4 primeiras colunas
        ('ALIGN', (4, 0), (4, 0), 'LEFT'),   # Alinhar à esquerda a coluna do motivo
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('FONTSIZE', (0, 0), (3, 0), 12),    # Tamanho da fonte para as 4 primeiras colunas
    ]))
    
    elements.append(table2)
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Paço do Lumiar – MA, " + data_documento + ".",
                              ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=2)))

    elements.append(Spacer(1, 1 * inch))
    elements.append(Paragraph("______________________________________",
                              ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("GESTOR(A)", ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=1)))

    def rodape(canvas, doc):
        width, height = letter
        canvas.saveState()
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(width / 2, 0.75 * inch, rodape_texto)
        canvas.restoreState()

    doc.build(elements, onFirstPage=rodape, onLaterPages=rodape)

def gerar_declaracao_aluno(aluno_id, marcacoes, motivo_outros=""):
    conn = conectar_bd()
    # Se a conexão falhar, `conectar_bd` pode retornar None — evitar acessar atributos de None
    if conn is None:
        if messagebox:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados para gerar a declaração.")
        else:
            logger.error("Erro: Não foi possível conectar ao banco de dados para gerar a declaração.")
        return
    cursor = conn.cursor()

    escola_id = 60
    dados_escola = obter_dados_escola(cursor, escola_id)
    if not dados_escola:
        cursor.close()
        conn.close()
        if messagebox:
            messagebox.showerror("Erro", "Dados da escola não encontrados.")
        else:
            logger.error("Erro: Dados da escola não encontrados.")
        return
    dados_aluno = obter_dados_aluno(cursor, aluno_id)
    responsaveis = obter_responsaveis(cursor, aluno_id)

    cursor.close()
    conn.close()

    if not dados_aluno:
        return

    cabecalho = criar_cabecalho(dados_escola)
    rodape_texto = criar_rodape(dados_escola)

    # Criar nome do arquivo baseado nos dados do aluno
    nome_aluno = str(dados_aluno[0]) if dados_aluno and dados_aluno[0] is not None else "aluno"
    data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"Declaracao_{nome_aluno.replace(' ', '_')}_{data_atual}.pdf"
    
    # Caminho completo do arquivo
    caminho_arquivo = os.path.join('documentos_gerados', nome_arquivo)
    
    # Garantir que o diretório existe
    os.makedirs('documentos_gerados', exist_ok=True)

    # Primeiro criar o PDF em memória
    buffer = io.BytesIO()
    criar_pdf(buffer, cabecalho, rodape_texto, dados_aluno, responsaveis, marcacoes, dados_escola[1], motivo_outros)
    
    # Salvar o PDF no disco
    with open(caminho_arquivo, 'wb') as f:
        f.write(buffer.getvalue())

    # Determinar a finalidade baseada nas marcações
    finalidade = None
    if marcacoes[0][0]:
        finalidade = "Transferência"
    elif marcacoes[0][1]:
        finalidade = "Bolsa Família"
    elif marcacoes[0][2]:
        finalidade = "Trabalho"
    elif marcacoes[0][3]:
        finalidade = f"Outros: {motivo_outros}"

    # Criar descrição
    descricao = f"Declaração escolar do aluno {nome_aluno}"
    if dados_aluno[3] and dados_aluno[4]:  # Se tem série e turma
        descricao += f" - {dados_aluno[3]} {dados_aluno[4]}"
    if dados_aluno[5]:  # Se tem turno
        descricao += f" - Turno: {'Matutino' if dados_aluno[5] == 'MAT' else 'Vespertino'}"

    # Salvar no Google Drive e banco de dados
    sucesso, mensagem, link = salvar_documento_sistema(
        caminho_arquivo=caminho_arquivo,
        tipo_documento=TIPO_DECLARACAO,
        aluno_id=aluno_id,
        finalidade=finalidade,
        descricao=descricao
    )

    # Abrir o arquivo local
    if not sucesso:
        # Se houver erro no upload, ainda abre o arquivo local mas mostra mensagem de erro
        if messagebox:
            messagebox.showwarning("Aviso", "O documento foi gerado mas houve um erro ao salvá-lo no sistema:\n" + mensagem)
        else:
            logger.warning("Aviso: O documento foi gerado mas houve um erro ao salvá-lo no sistema:\n%s", mensagem)
    
    # Abrir o arquivo para visualização
    buffer.seek(0)
    salvar_e_abrir_pdf(buffer)
