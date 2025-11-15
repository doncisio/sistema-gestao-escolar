from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from conexao import conectar_bd
from typing import Any, Dict, List, cast
import datetime
import os
import logging
import stat
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def criar_diretorio_com_permissao(diretorio):
    """Cria um diretório com as permissões adequadas se ele não existir."""
    if not os.path.exists(diretorio):
        try:
            # Criar o diretório com permissões totais
            os.makedirs(diretorio)
            # Dar permissões de leitura/escrita para todos
            os.chmod(diretorio, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            logger.info(f"Diretório '{diretorio}' criado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao criar diretório: {e}")
            raise

def gerar_relatorio_series_faltantes():
    logger.info("Iniciando geração do relatório...")
    
    # Conectar ao banco de dados
    conn = conectar_bd()
    if not conn:
        logger.error("Erro ao conectar ao banco de dados")
        return

    try:
        # Criar diretório se não existir
        criar_diretorio_com_permissao('documentos_gerados')

        cursor = conn.cursor(dictionary=True)
        
        logger.info("Executando consulta SQL para alunos ativos...")
        # Consulta SQL para obter os dados de alunos ativos
        query_alunos_ativos = """
        SELECT DISTINCT 
            m.aluno_id,
            al.nome as nome_aluno,
            t.serie_id as serie_atual
        FROM matriculas m
        JOIN turmas t ON m.turma_id = t.id
        JOIN alunos al ON al.id = m.aluno_id
        WHERE m.ano_letivo_id = 26 
        AND m.status = 'Ativo'
        ORDER BY t.serie_id, al.nome;
        """
        
        cursor.execute(query_alunos_ativos)
        # Cursor foi criado com dictionary=True; cast para ajudar o analisador de tipos
        alunos_ativos = cast(List[Dict[str, Any]], cursor.fetchall())
        logger.info(f"Encontrados {len(alunos_ativos)} alunos ativos")

        # Consulta para obter o histórico escolar de cada aluno
        query_historico = """
        SELECT 
            h.aluno_id,
            h.serie_id,
            a.ano_letivo,
            e.nome AS escola_nome,
            e.municipio AS escola_municipio,
            CASE
                WHEN COUNT(h.media) = 0 AND COUNT(h.conceito) > 0 THEN 'Promovido(a)'
                WHEN MIN(h.media) >= 48 THEN 'Promovido(a)'
                WHEN MIN(h.media) < 48 THEN 'Retido(a)'
            END AS situacao_final
        FROM 
            historico_escolar h
        JOIN 
            anosletivos a ON h.ano_letivo_id = a.id
        JOIN 
            escolas e ON h.escola_id = e.id
        WHERE 
            h.aluno_id = %s
        GROUP BY 
            h.aluno_id, h.serie_id, a.ano_letivo, e.nome, e.municipio;
        """

        # Preparar dados para o relatório
        alunos_incompletos = []
        alunos_completos = []

        for aluno in alunos_ativos:
            # `cursor` foi criado com dictionary=True, portanto `aluno` é um dict.
            # Extrair explicitamente o aluno_id em variável local para ajudar o analisador de tipos.
            aluno_id = aluno.get('aluno_id') if isinstance(aluno, dict) else None
            cursor.execute(query_historico, (aluno_id,))
            historico = cast(List[Dict[str, Any]], cursor.fetchall())
            
            # Criar dicionário com as séries existentes
            series_existentes = {registro['serie_id']: registro for registro in historico}
            
            # Verificar séries faltantes
            series_faltantes = []
            for serie_id in range(3, aluno['serie_atual'] + 1):
                if serie_id not in series_existentes:
                    series_faltantes.append(serie_id)
            
            if series_faltantes:
                # Aluno tem histórico incompleto
                for serie_faltante in series_faltantes:
                    alunos_incompletos.append({
                        'aluno_id': aluno_id,
                        'nome_aluno': aluno['nome_aluno'],
                        'serie_atual': aluno['serie_atual'],
                        'serie_faltante': serie_faltante
                    })
            else:
                # Aluno tem histórico completo
                situacao_final = historico[-1]['situacao_final'] if historico else 'Sem histórico'
                alunos_completos.append({
                    'aluno_id': aluno_id,
                    'nome_aluno': aluno['nome_aluno'],
                    'serie_atual': aluno['serie_atual'],
                    'situacao_final': situacao_final
                })

        logger.info(f"Encontrados {len(alunos_incompletos)} registros de alunos com histórico incompleto")
        logger.info(f"Encontrados {len(alunos_completos)} registros de alunos com histórico completo")

        # Criar o documento PDF com nome único
        timestamp = int(time.time())
        nome_arquivo = os.path.join('documentos_gerados', f"relatorio_series_faltantes_{timestamp}.pdf")
        logger.info(f"Gerando PDF: {nome_arquivo}")
        
        doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.HexColor('#444444')
        )
        
        # Título principal
        elements.append(Paragraph("Relatório de Histórico Escolar", title_style))
        elements.append(Paragraph(f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        elements.append(Spacer(1, 30))

        # Seção 1: Alunos com histórico incompleto
        elements.append(Paragraph("Alunos com Histórico Incompleto", subtitle_style))
        elements.append(Spacer(1, 10))
        
        if alunos_incompletos:
            dados_incompleto = [['ID Aluno', 'Nome do Aluno', 'Série Atual', 'Série Faltante']]
            for aluno in alunos_incompletos:
                dados_incompleto.append([
                    str(aluno['aluno_id']),
                    aluno['nome_aluno'],
                    str(aluno['serie_atual']),
                    str(aluno['serie_faltante'])
                ])
            
            table_incompleto = Table(dados_incompleto)
            table_incompleto.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9999')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table_incompleto)
        else:
            elements.append(Paragraph("Nenhum aluno com histórico incompleto encontrado.", styles['Normal']))

        elements.append(Spacer(1, 30))

        # Seção 2: Alunos com histórico completo
        elements.append(Paragraph("Alunos com Histórico Completo", subtitle_style))
        elements.append(Spacer(1, 10))

        if alunos_completos:
            dados_completo = [['ID Aluno', 'Nome do Aluno', 'Série Atual', 'Situação Final']]
            for aluno in alunos_completos:
                dados_completo.append([
                    str(aluno['aluno_id']),
                    aluno['nome_aluno'],
                    str(aluno['serie_atual']),
                    aluno['situacao_final']
                ])
            
            table_completo = Table(dados_completo)
            table_completo.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#99FF99')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table_completo)
        else:
            elements.append(Paragraph("Nenhum aluno com histórico completo encontrado.", styles['Normal']))
        
        # Gerar PDF
        logger.info("Gerando PDF...")
        doc.build(elements)
        logger.info(f"Relatório gerado com sucesso: {nome_arquivo}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {str(e)}", exc_info=True)
    finally:
        if conn:
            conn.close()
            logger.info("Conexão com o banco de dados fechada")

if __name__ == "__main__":
    gerar_relatorio_series_faltantes() 