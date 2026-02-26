"""
Módulo para gerar lista de alunos em distorção idade-série
Formulário de Mapeamento de Alunos - Programa Correção de Fluxo Escolar

CÁLCULO DE IDADE:
A idade é calculada com base na DATA DE CORTE: 31/03 do ano letivo.
Este é o padrão oficial usado pelo Censo Escolar e sistema GEDUC.

CONFIGURAÇÃO DE POLOS:
Para adicionar o polo de outras escolas, edite o dicionário POLO_POR_ESCOLA abaixo.
Exemplo:
    POLO_POR_ESCOLA = {
        60: "01",  # EM Profª. Nadir Nascimento Moraes
        70: "02",  # Outra Escola
        80: "03",  # Mais uma Escola
    }
"""

from src.core.config_logs import get_logger
logger = get_logger(__name__)

import io
from datetime import date
from typing import List, Dict, Optional, Any, cast
import pandas as pd

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from src.core.config import get_image_path, ANO_LETIVO_ATUAL, ESCOLA_ID
from src.core.conexao import conectar_bd
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf


# Mapeamento de série_id para idade ideal
IDADE_IDEAL_POR_SERIE = {
    3: 6,   # 1º ano
    4: 7,   # 2º ano
    5: 8,   # 3º ano
    6: 9,   # 4º ano
    7: 10,  # 5º ano
    8: 11,  # 6º ano
    9: 12,  # 7º ano
    10: 13, # 8º ano
    11: 14  # 9º ano
}

# Mapeamento de polos por escola_id
# TODO: Adicionar mais escolas conforme necessário
POLO_POR_ESCOLA = {
    60: "V - MAIOBÃO II",  # EM Profª. Nadir Nascimento Moraes
    # Adicione outras escolas aqui
}


def calcular_idade_data_corte(data_nascimento: date, ano_referencia: int) -> int:
    """
    Calcula a idade do aluno na data de corte (31/03 do ano de referência).
    Esta é a data oficial usada pelo Censo Escolar e sistema GEDUC.
    """
    data_corte = date(ano_referencia, 3, 31)
    idade = data_corte.year - data_nascimento.year
    # Ajustar se ainda não fez aniversário até a data de corte
    if (data_corte.month, data_corte.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade


def obter_dados_escola(escola_id: int) -> Optional[Dict]:
    """Busca informações da escola no banco de dados."""
    conn = conectar_bd()
    if not conn:
        logger.error("Erro ao conectar ao banco de dados")
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id, nome, endereco, inep, cnpj, municipio, telefone
            FROM escolas 
            WHERE id = %s
        """
        cursor.execute(query, (escola_id,))
        escola = cursor.fetchone()
        
        # Adicionar campo polo com valor do mapeamento ou vazio
        if escola:
            escola['polo'] = POLO_POR_ESCOLA.get(escola_id, '_____')
        
        return escola
    except Exception as e:
        logger.error(f"Erro ao buscar dados da escola: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def obter_gestor_geral(escola_id: int) -> Optional[str]:
    """Busca o nome do gestor geral da escola."""
    conn = conectar_bd()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT nome, telefone 
            FROM funcionarios 
            WHERE escola_id = %s 
            AND (funcao = 'Gestor Geral' OR cargo = 'Gestor Geral')
            LIMIT 1
        """
        cursor.execute(query, (escola_id,))
        gestor = cursor.fetchone()
        if gestor:
            return gestor
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar gestor: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def obter_alunos_distorcao(escola_id: int, ano_letivo: int, anos_minimos: int = 2) -> List[Dict]:
    """
    Busca alunos em distorção idade-série da escola.
    
    Args:
        escola_id: ID da escola
        ano_letivo: Ano letivo de referência
        anos_minimos: Anos mínimos de distorção (padrão: 2)
        
    Returns:
        Lista de alunos em distorção com dados completos
    """
    conn = conectar_bd()
    if not conn:
        logger.error("Erro ao conectar ao banco de dados")
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT 
                a.id,
                a.nome,
                a.data_nascimento,
                a.cpf,
                s.id AS serie_id,
                s.nome AS serie_nome,
                t.nome AS turma_nome,
                t.turno,
                m.id AS matricula_id
            FROM 
                Alunos a
            JOIN 
                Matriculas m ON a.id = m.aluno_id
            JOIN 
                Turmas t ON m.turma_id = t.id
            JOIN 
                series s ON t.serie_id = s.id
            JOIN
                AnosLetivos al ON m.ano_letivo_id = al.id
            WHERE 
                a.escola_id = %s
                AND al.ano_letivo = %s
                AND m.status = 'Ativo'
                AND a.data_nascimento IS NOT NULL
            ORDER BY 
                s.nome, t.nome, a.nome
        """
        
        cursor.execute(query, (escola_id, ano_letivo))
        alunos = cursor.fetchall()
        
        # Filtrar apenas alunos em distorção
        alunos_distorcao = []
        for aluno in alunos:
            serie_id = aluno['serie_id']
            data_nascimento = aluno['data_nascimento']
            
            if serie_id not in IDADE_IDEAL_POR_SERIE:
                continue
            
            idade_atual = calcular_idade_data_corte(data_nascimento, ano_letivo)
            idade_ideal = IDADE_IDEAL_POR_SERIE[serie_id]
            anos_distorcao = idade_atual - idade_ideal
            
            if anos_distorcao >= anos_minimos:
                aluno['idade'] = idade_atual
                aluno['idade_ideal'] = idade_ideal
                aluno['anos_distorcao'] = anos_distorcao
                alunos_distorcao.append(aluno)
        
        logger.info(f"Total de alunos em distorção: {len(alunos_distorcao)}")
        return alunos_distorcao
        
    except Exception as e:
        logger.error(f"Erro ao buscar alunos em distorção: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def obter_responsaveis_aluno(aluno_id: int) -> List[Dict]:
    """Busca os responsáveis de um aluno."""
    conn = conectar_bd()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT r.nome, r.grau_parentesco, r.telefone
            FROM responsaveis r
            JOIN responsaveisalunos ra ON r.id = ra.responsavel_id
            WHERE ra.aluno_id = %s
            ORDER BY r.id
            LIMIT 1
        """
        cursor.execute(query, (aluno_id,))
        responsaveis = cursor.fetchall()
        return responsaveis
    except Exception as e:
        logger.error(f"Erro ao buscar responsáveis do aluno {aluno_id}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def criar_cabecalho(escola: Dict, figura_inferior: str) -> Table:
    """Cria o cabeçalho padrão com logo e informações da escola."""
    nome_escola = escola.get('nome', 'ESCOLA MUNICIPAL').upper()
    inep = escola.get('inep', '')
    cnpj = escola.get('cnpj', '')
    
    cabecalho_texto = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        f"<b>{nome_escola}</b>",
        f"<b>INEP: {inep}</b>",
        f"<b>CNPJ: {cnpj}</b>"
    ]
    
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho_texto), ParagraphStyle(name='Header', fontSize=12, alignment=TA_CENTER))]
    ]
    
    table = Table(data, colWidths=[7.5 * inch])
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ]))
    
    return table


def criar_titulo_formulario(escola: Dict, gestor: Optional[Dict], ano_letivo: int) -> list:
    """Cria o título e informações do formulário."""
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Título principal
    titulo_style = ParagraphStyle(
        'TituloFormulario',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=3,
        fontName='Helvetica-Bold'
    )
    
    elements.append(Paragraph(
        "FORMULÁRIO DE MAPEAMENTO DE ALUNOS EM DISTORÇÃO IDADE–ANO/SÉRIE",
        titulo_style
    ))
    
    # Subtítulo
    subtitulo_style = ParagraphStyle(
        'SubtituloFormulario',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=3,
        fontName='Helvetica-Bold'
    )
    
    elements.append(Paragraph(
        f"PROGRAMA CORREÇÃO DE FLUXO ESCOLAR  {ano_letivo}",
        subtitulo_style
    ))
    
    # Data de corte
    data_corte_style = ParagraphStyle(
        'DataCorte',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceAfter=10,
        fontName='Helvetica-Oblique',
        textColor=HexColor('#666666')
    )
    
    elements.append(Paragraph(
        "<i>Data de corte para cálculo de idade: 31/03/2026 (padrão Censo Escolar/GEDUC)</i>",
        data_corte_style
    ))
    
    # Informações da escola
    info_style = ParagraphStyle(
        'InfoEscola',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=4
    )
    
    nome_escola = escola.get('nome', 'ESCOLA MUNICIPAL').upper()
    polo = escola.get('polo', '_____')
    nome_gestor = gestor.get('nome', '_' * 50) if gestor else '_' * 50
    telefone_gestor = gestor.get('telefone', '(98) 99999-9999') if gestor else '(98) 99999-9999'
    
    # Formatação do telefone
    if telefone_gestor and telefone_gestor != '(98) 99999-9999':
        from scripts.auxiliares.biblio_editor import formatar_telefone
        telefone_gestor = formatar_telefone(telefone_gestor)
    
    elements.append(Paragraph(f"<b>{nome_escola}</b> <b>POLO:</b> {polo}", info_style))
    elements.append(Paragraph(f"<b>GESTOR:</b> {nome_gestor}   <b>FONE:</b> {telefone_gestor}", info_style))
    
    # Segmentos atendidos
    segmentos_style = ParagraphStyle(
        'Segmentos',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=12
    )
    
    elements.append(Paragraph(
        "<b>SEGMENTOS ATENDIDOS:</b>   (   ) Séries iniciais     (   ) Séries Finais      (X) Séries iniciais e Finais",
        segmentos_style
    ))
    
    return elements


def criar_tabela_alunos(alunos: List[Dict]) -> Table:
    """Cria a tabela com os dados dos alunos em distorção."""
    
    # Cabeçalho da tabela
    cabecalhos = [
        'N°',
        'NOME DO(A)\nESTUDANTE',
        'DATA DE\nNASC.',
        'IDADE',
        'ANO/SÉRIE\nDE ORIGEM',
        'RECLASSIFICAR',
        'CONDIÇÃO DE\nLEITURA',
        'RESPONSÁVEL\nLEGAL',
        'CONTATO'
    ]
    
    data = [cabecalhos]
    
    # Preencher dados dos alunos
    for idx, aluno in enumerate(alunos, 1):
        # Buscar responsável
        responsaveis = obter_responsaveis_aluno(aluno['id'])
        responsavel_nome = responsaveis[0]['nome'] if responsaveis else ''
        responsavel_tel = responsaveis[0]['telefone'] if responsaveis else ''
        
        # Formatação do telefone
        if responsavel_tel:
            from scripts.auxiliares.biblio_editor import formatar_telefone
            responsavel_tel = formatar_telefone(responsavel_tel)
        
        # Formatação da data
        data_nasc = aluno['data_nascimento'].strftime('%d/%m/%Y') if aluno['data_nascimento'] else ''
        
        # Série formatada
        serie = aluno['serie_nome']
        
        linha = [
            str(idx),
            aluno['nome'],
            data_nasc,
            str(aluno['idade']),
            serie,
            '[  ] Sim     [  ] Não',
            '[  ] Leitor   [  ] Não leitor',
            responsavel_nome,
            responsavel_tel
        ]
        
        data.append(linha)
    
    # Criar tabela
    col_widths = [
        0.3 * inch,  # N°
        2.2 * inch,  # Nome
        0.7 * inch,  # Data Nasc
        0.5 * inch,  # Idade
        0.8 * inch,  # Série
        1.0 * inch,  # Reclassificar
        1.2 * inch,  # Condição Leitura
        1.5 * inch,  # Responsável
        1.0 * inch   # Contato
    ]
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Estilo da tabela - Cabeçalho branco para economizar tinta
    from reportlab.lib.colors import HexColor
    cinza_claro = HexColor('#E8E8E8')
    
    table.setStyle(TableStyle([
        # Cabeçalho - fundo cinza claro em vez de preto (economiza tinta)
        ('BACKGROUND', (0, 0), (-1, 0), cinza_claro),
        ('TEXTCOLOR', (0, 0), (-1, 0), black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Corpo da tabela
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # N°
        ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Idade
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Série
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        
        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, black),  # Linha mais grossa no cabeçalho
        
        # Espaçamento
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    return table


def criar_orientacoes() -> list:
    """Cria a seção de orientações para preenchimento."""
    elements = []
    
    elements.append(Spacer(1, 0.2 * inch))
    
    style = ParagraphStyle(
        'Orientacoes',
        fontSize=9,
        alignment=TA_LEFT,
        spaceAfter=4,
        leading=12
    )
    
    elements.append(Paragraph("<b>ORIENTAÇÕES PARA PREENCHIMENTO:</b>", style))
    elements.append(Paragraph("• Listar apenas estudantes que apresentem distorção idade–ano/série (2 anos ou mais).", style))
    elements.append(Paragraph("• Marcar apenas UMA opção em cada campo de seleção.", style))
    elements.append(Paragraph("• A condição \"Leitor / Não leitor\" deve considerar avaliação pedagógica diagnóstica da escola.", style))
    elements.append(Paragraph("• A condição \"RECLASSIFICAR\" deve considerar avaliação pedagógica diagnóstica da escola.", style))
    elements.append(Paragraph("• O preenchimento correto e completo é indispensável para organização das turmas de Correção de Fluxo.", style))
    
    elements.append(Spacer(1, 0.075 * inch))
    
    elements.append(Paragraph(
        "Declaro que as informações acima são verdadeiras e foram levantadas pela equipe pedagógica da unidade escolar.",
        style
    ))
    
    elements.append(Spacer(1, 0.1 * inch))
    
    # Campos de assinatura
    assina_style = ParagraphStyle(
        'Assinatura',
        fontSize=9,
        alignment=TA_LEFT
    )
    
    elements.append(Paragraph(
        "<b>Resp. pelo preenchimento:</b> Tarcisio Sousa de Almeida  <b>Cargo/Função:</b> Técnico em Administração Escolar",
        assina_style
    ))
    
    elements.append(Spacer(1, 0.2 * inch))
    
    elements.append(Paragraph(
        "_____________________________________________",
        ParagraphStyle('AssinaturaGestao', fontSize=9, alignment=TA_CENTER)
    ))
    elements.append(Paragraph(
        "Gestão Escolar",
        ParagraphStyle('TextoGestao', fontSize=9, alignment=TA_CENTER)
    ))
    
    return elements


def gerar_lista_distorcao_fluxo(escola_id: int = ESCOLA_ID, ano_letivo: int = ANO_LETIVO_ATUAL):
    """
    Gera o PDF com o formulário de mapeamento de alunos em distorção idade-série.
    
    Args:
        escola_id: ID da escola (padrão: configurado no sistema)
        ano_letivo: Ano letivo de referência (padrão: ano atual do sistema)
    """
    logger.info(f"Gerando lista de distorção de fluxo - Escola: {escola_id}, Ano: {ano_letivo}")
    
    # Buscar dados da escola
    escola = obter_dados_escola(escola_id)
    if not escola:
        logger.error("Escola não encontrada")
        return None
    
    # Buscar gestor
    gestor = obter_gestor_geral(escola_id)
    
    # Buscar alunos em distorção
    alunos = obter_alunos_distorcao(escola_id, ano_letivo)
    
    if not alunos:
        logger.info("Nenhum aluno em distorção encontrado")
        from tkinter import messagebox
        messagebox.showinfo(
            "Informação",
            "Nenhum aluno em distorção idade-série encontrado para esta escola."
        )
        return None
    
    # Configurar documento
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.125 * inch,
        bottomMargin=0.125 * inch
    )
    
    elements = []
    
    # Imagem do logo
    figura_inferior = str(get_image_path('logopaco.png'))
    
    # Cabeçalho
    elements.append(criar_cabecalho(escola, figura_inferior))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Título e informações
    elements.extend(criar_titulo_formulario(escola, gestor, ano_letivo))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Tabela de alunos
    elements.append(criar_tabela_alunos(alunos))
    
    # Orientações
    elements.extend(criar_orientacoes())
    
    # Construir PDF
    doc.build(elements)
    
    # Salvar e abrir
    buffer.seek(0)
    nome_arquivo = f"MAPEAMENTO_DISTORCAO_FLUXO_{escola_id}_{ano_letivo}.pdf"
    
    resultado = salvar_e_abrir_pdf(buffer, nome_arquivo)
    
    if resultado:
        logger.info(f"PDF gerado com sucesso: {nome_arquivo}")
    
    return buffer


if __name__ == "__main__":
    # Para testes
    gerar_lista_distorcao_fluxo()
