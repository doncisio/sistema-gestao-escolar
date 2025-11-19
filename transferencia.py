import datetime
import io
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from conexao import conectar_bd
from db.connection import get_cursor
from typing import Any, cast
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white
from utilitarios.extrairdados import obter_dados_aluno, obter_dados_responsaveis
from gerarPDF import salvar_e_abrir_pdf
from utilitarios.gerenciador_documentos import salvar_documento_sistema
from utilitarios.tipos_documentos import TIPO_TRANSFERENCIA
from utils.dates import formatar_data
from config_logs import get_logger

logger = get_logger(__name__)

def gerar_documento_transferencia(aluno_id, ano_letivo_id):
    # Conectar ao banco de dados (usa get_connection para garantir fechamento)
    try:
        # Usar cursor com commit automático no exit (gera commit/rollback conforme sucesso/exceção)
        with get_cursor(commit=True) as cursor:

        # Obter dados do aluno
        query_aluno = """
            SELECT 
                a.nome AS nome_aluno, 
                a.data_nascimento AS nascimento, 
                a.sexo AS sexo,
                s.nome AS nome_serie, 
                t.nome AS nome_turma, 
                t.turno AS turno,
                n.nome AS nivel_ensino, 
                m.status,
                t.id AS turma_id
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
                a.id = %s AND m.ano_letivo_id = %s;
        """
        cursor.execute(query_aluno, (aluno_id, ano_letivo_id))
        resultado = cursor.fetchone()
        
        if not resultado:
            logger.warning("Aluno não encontrado.")
            return

        # Extrair informações do resultado
        dados_aluno = {
            "nome_aluno": resultado[0],
            "nascimento": resultado[1],
            "sexo": resultado[2],
            "nome_serie": resultado[3],
            "nome_turma": resultado[4],
            "turno": resultado[5],
            "nivel_ensino": resultado[6],
            "status": resultado[7],
            "turma_id": resultado[8]
        }

        logger.debug(f"Dados do aluno: {dados_aluno}")  # Debug

        # Obter dados dos responsáveis
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
        resultados_responsaveis = cursor.fetchall()
        responsaveis = [responsavel[0] for responsavel in resultados_responsaveis]
        responsavel1 = responsaveis[0] if len(responsaveis) > 0 else None
        responsavel2 = responsaveis[1] if len(responsaveis) > 1 else None
        
        # Mesclar dados nome serie e turma
        turma = f"{dados_aluno['nome_serie']} {dados_aluno['nome_turma']}"

        # Formatar a data de nascimento
        data_nascimento = pd.to_datetime(dados_aluno['nascimento']).strftime("%d/%m/%Y") if pd.notnull(dados_aluno['nascimento']) else ""

        # Formatar a data atual no formato "DIA de MÊS de ANO"
        data_documento = formatar_data(datetime.datetime.now())

        # Consultar notas do aluno e os nomes das disciplinas
            cursor.execute("""
            SELECT d.nome AS disciplina_nome, n.bimestre, n.nota 
            FROM notas n 
            JOIN disciplinas d ON n.disciplina_id = d.id 
            WHERE n.aluno_id = %s AND n.ano_letivo_id = %s
            ORDER BY FIELD(n.bimestre, '1º bimestre', '2º bimestre', '3º bimestre')
        """, (aluno_id, ano_letivo_id))
        
        notas = cursor.fetchall()
        genero_aluno = 'feminino' if dados_aluno['sexo'] == 'F' else 'masculino'

        # Definindo o estilo do parágrafo com espaçamento entre linhas
        style_declaracao = ParagraphStyle(
            name='DeclaracaoTexto',
            fontSize=12,
            alignment=4,
            leading=18  # Ajusta o espaçamento entre linhas (1.5 vezes o tamanho da fonte padrão de 12pt)
        )

        # Informações do cabeçalho
        cabecalho = [
            "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
            "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
            "<b>EM PROFª. NADIR NASCIMENTO MORAES</b>",
            "<b>INEP: 21008485</b>",
            "<b>CNPJ: 06.003.636/0001-73</b>"
        ]

        # Caminhos das figuras
        figura_superior = os.path.join(os.path.dirname(__file__), 'pacologo.png')
        figura_inferior = os.path.join(os.path.dirname(__file__), 'logopacobranco.png')

        # Criar o PDF em memória
        buffer = io.BytesIO()
        # Define as margens da página (em pontos) para margens estreitas
        left_margin = 85.05    # Margem esquerda (3cm)
        right_margin = 56.7   # Margem direita (2cm)
        top_margin = 56.7     # Margem superior (2cm) - Reduzida de 3cm para 2cm
        bottom_margin = 56.7  # Margem inferior (2cm)

        # Cria o documento PDF com as margens ajustadas
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            leftMargin=left_margin, 
            rightMargin=right_margin, 
            topMargin=top_margin, 
            bottomMargin=bottom_margin
        )
        
        # Estilos para o documento
        styles = getSampleStyleSheet()
        story = []

        # Adicionar o cabeçalho antes de cada tabela
        data = [
            [Image(figura_superior, width=1 * inch, height=1 * inch),
                Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
                Image(figura_inferior, width=1.5 * inch, height=1 * inch)]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table_style = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ])
        table.setStyle(table_style)
        story.append(table)

        story.append(Spacer(1, 0.35 * inch))

        # Adicionar título
        story.append(Paragraph("Declaração de Desempenho Acadêmico", styles['Title']))
        story.append(Spacer(1, 0.25 * inch))
        # Adicionar informações do aluno
        if pd.isna(responsavel1):
            if pd.isna(responsavel2):
                story.append(Paragraph(
                    f"Declaramos, para os devidos fins, que <b>{dados_aluno['nome_aluno']}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de, esteve regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} nesta Instituição de Ensino, no <b>{turma} </b> do {dados_aluno['nivel_ensino']} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if dados_aluno['turno'] == 'MAT' else 'no turno <b>vespertino</b>'}.",
                    style_declaracao))
            else:
                story.append(Paragraph(
                    f"Declaramos, para os devidos fins, que <b>{dados_aluno['nome_aluno']}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel2}</b>, esteve regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} nesta Instituição de Ensino, na <b>{turma}</b> do {dados_aluno['nivel_ensino']} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if dados_aluno['turno'] == 'MAT' else 'no turno <b>vespertino</b>'}.",
                    style_declaracao))
        elif pd.isna(responsavel2):
            story.append(Paragraph(
                f"Declaramos, para os devidos fins, que <b>{dados_aluno['nome_aluno']}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel1}</b>, esteve regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} nesta Instituição de Ensino, na <b>{turma} </b> do {dados_aluno['nivel_ensino']} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if dados_aluno['turno'] == 'MAT' else 'no turno <b>vespertino</b>'}.",
                style_declaracao))
        else:
            story.append(Paragraph(
                f"Declaramos, para os devidos fins, que <b>{dados_aluno['nome_aluno']}</b>, nascid{'o' if genero_aluno == 'masculino' else 'a'} em <b>{data_nascimento}</b>, filh{'o' if genero_aluno == 'masculino' else 'a'} de <b>{responsavel1}</b> e <b>{responsavel2}</b>, esteve regularmente matriculad{'o' if genero_aluno == 'masculino' else 'a'} nesta Instituição de Ensino, no <b>{turma}</b> do {dados_aluno['nivel_ensino']} no ano de <b>{datetime.datetime.now().year}</b>, {'no turno <b>matutino</b>' if dados_aluno['turno'] == 'MAT' else 'no turno <b>vespertino</b>'}.",
                style_declaracao))

        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph("Abaixo segue o desempenho acadêmico parcial do(a) aluno(a) no ano corrente:", style_declaracao))
        story.append(Spacer(1, 0.25 * inch))
        # Adicionar espaço entre seções
        story.append(Paragraph("<br/>", styles['Normal']))

        # Criar tabela para as notas
        table_data = [["COMPONENTE CURRICULAR", "1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"]]
        
        # Agrupar notas por disciplina
        notas_por_disciplina = {}
        
        for disciplina_nome, bimestre, nota in notas:
            if disciplina_nome not in notas_por_disciplina:
                notas_por_disciplina[disciplina_nome] = {'1º bimestre': None, '2º bimestre': None, '3º bimestre': None, '4º bimestre': None}
            
            # Dividir a nota por 10 antes de armazená-la
            if nota is not None:
                nota /= 10
                
            notas_por_disciplina[disciplina_nome][bimestre] = nota

        for disciplina_nome, notas in notas_por_disciplina.items():
            table_data.append([
                disciplina_nome,
                notas['1º bimestre'] if notas['1º bimestre'] is not None else '--',
                notas['2º bimestre'] if notas['2º bimestre'] is not None else '--',
                notas['3º bimestre'] if notas['3º bimestre'] is not None else '--',
                notas['4º bimestre'] if notas['4º bimestre'] is not None else '--'
            ])

        # Criar tabela com estilo
        table = Table(table_data)
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
        ])
        
        table.setStyle(style)
        
        # Adicionar tabela ao documento
        story.append(table)
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph(f"A presente declaração é emitida a pedido do(a) Sr(a). {responsavel2}, responsável legal pel{'o aluno' if genero_aluno == 'masculino' else 'a aluna'}, para fins de apresentação à nova escola.", style_declaracao))

        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("Paço do Lumiar – MA, " + data_documento + ".",
                                  ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=2)))
        # Adicionar espaço para assinatura do Diretor Geral
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("______________________________________",
                                  ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=1)))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("GESTOR(A)", ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=1)))

        # Construir o PDF
        doc.build(story)

        # Resetar o buffer para o início
        buffer.seek(0)

        # Criar nome do arquivo
        data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"Transferencia_{dados_aluno['nome_aluno'].replace(' ', '_')}_{data_atual}.pdf"
        caminho_arquivo = os.path.join('documentos_gerados', nome_arquivo)

        # Garantir que o diretório existe
        os.makedirs('documentos_gerados', exist_ok=True)

        # Salvar o arquivo localmente
        with open(caminho_arquivo, 'wb') as f:
            f.write(buffer.getvalue())

        # Criar descrição detalhada
        descricao = f"Declaração de Transferência do aluno {dados_aluno['nome_aluno']}"
        if turma:
            descricao += f" - {turma}"
        if dados_aluno.get('turno'):
            descricao += f" - Turno: {'Matutino' if dados_aluno.get('turno') == 'MAT' else 'Vespertino'}"

        # Tentar salvar no sistema de gerenciamento de documentos
        try:
            sucesso, mensagem, link = salvar_documento_sistema(
                caminho_arquivo=caminho_arquivo,
                tipo_documento=TIPO_TRANSFERENCIA,
                aluno_id=aluno_id,
                finalidade=f"Transferência {datetime.datetime.now().year}",
                descricao=descricao
            )

            if not sucesso:
                # Mostrar aviso ao usuário (sem interromper)
                try:
                    from tkinter import messagebox
                    messagebox.showwarning("Aviso", "O documento foi gerado, mas houve um erro ao salvá-lo no sistema:\n" + mensagem)
                except Exception:
                    logger.warning("Aviso: O documento foi gerado, mas houve um erro ao salvá-lo no sistema: %s", mensagem)

        except Exception as e:
            # Se não existir o tipo de documento ou falhar, registrar e prosseguir
            logger.exception(f"Erro ao salvar documento no sistema: {e}")

            # Abrir/mostrar o PDF gerado
            salvar_e_abrir_pdf(buffer)

            # Commit é tratado pelo context manager `get_cursor(commit=True)`

    except Exception as e:
        logger.exception(f"Erro ao gerar documento de transferência: {e}")
        return

# gerar_documento_transferencia(575)