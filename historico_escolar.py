import os
import io
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from utilitarios.gerenciador_documentos import salvar_documento_sistema
from utilitarios.tipos_documentos import TIPO_HISTORICO
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle
from conexao import conectar_bd
from gerarPDF import salvar_e_abrir_pdf, salvar
import logging
import time
from config_logs import get_logger

# Logger do módulo
logger = get_logger(__name__)
from utilitarios.conversoes import to_safe_int, to_safe_float

# Cache global para imagens e estilos
_IMAGE_CACHE = {}
_STYLE_CACHE = {}
_PARAGRAPH_CACHE = {}

def _get_cached_image(path, width, height):
    """Retorna uma imagem em cache para evitar recarregamento."""
    key = (path, width, height)
    if key not in _IMAGE_CACHE:
        _IMAGE_CACHE[key] = Image(path, width=width, height=height)
    return _IMAGE_CACHE[key]

def _get_cached_style(name, **kwargs):
    """Retorna um estilo em cache para evitar recriação."""
    key = (name, tuple(sorted(kwargs.items())))
    if key not in _STYLE_CACHE:
        _STYLE_CACHE[key] = ParagraphStyle(name=name, **kwargs)
    return _STYLE_CACHE[key]

def _get_cached_paragraph(text, style_name, **style_kwargs):
    """Retorna um parágrafo em cache para textos estáticos."""
    key = (text, style_name, tuple(sorted(style_kwargs.items())))
    if key not in _PARAGRAPH_CACHE:
        style = _get_cached_style(style_name, **style_kwargs)
        _PARAGRAPH_CACHE[key] = Paragraph(text, style)
    return _PARAGRAPH_CACHE[key]

# Mapeamento entre nomes antigos e novos das disciplinas
mapeamento_disciplinas = {
    "PORTUGUÊS": "LÍNGUA PORTUGUESA",
    "MATEMÁTICA": "MATEMÁTICA",
    "HISTÓRIA": "HISTÓRIA",
    "GEOGRAFIA": "GEOGRAFIA",
    "CIÊNCIAS": "CIÊNCIAS",
    "ARTES": "ARTE",
    "ENS. RELIGIOSO": "ENSINO RELIGIOSO",
    "ED. FÍSICA": "EDUCAÇÃO FÍSICA",
    "INGLÊS": "LÍNGUA INGLESA",
    "FILOSOFIA": "FILOSOFIA"
}

from utils.dates import formatar_data_extenso as formatar_data

def quebra_linha(texto):
    # Ajusta o tamanho da fonte para textos mais longos
    if len(texto) > 20:
        fontSize = 5
    elif len(texto) > 15:
        fontSize = 5
    else:
        fontSize = 7
    
    # Cache do estilo baseado no fontSize
    style = _get_cached_style(
        f'header_{fontSize}',
        fontName='Helvetica-BoldOblique',
        fontSize=fontSize,
        alignment=1,
        leading=fontSize+2,
        spaceBefore=0,
        spaceAfter=0,
        allowWidows=0,
        allowOrphans=0
    )
    return Paragraph(texto.upper(), style)

def titulo(texto):
    style = _get_cached_style('titulo_header', fontName='Helvetica-Bold', fontSize=7.5, alignment=1)
    return Paragraph(texto, style)

def obter_disciplinas_do_historico(aluno_id):
    conn = conectar_bd()
    if not conn:
        logger.error("Erro: Não foi possível conectar ao banco de dados")
        return []
    
    cursor = conn.cursor()
    try:
        consulta = """
            SELECT DISTINCT d.nome AS disciplina
            FROM historico_escolar h
            JOIN disciplinas d ON h.disciplina_id = d.id
            WHERE h.aluno_id = %s;
        """
        cursor.execute(consulta, (aluno_id,))
        resultados = cursor.fetchall()
        return [linha[0] for linha in resultados]
    finally:
        cursor.close()
        conn.close()

def substituir_disciplinas(aluno_id):
    disciplinas_todas = obter_disciplinas_do_historico(aluno_id)
    
    # Verifica se a disciplina está no mapeamento (tanto como chave quanto como valor)
    disciplinas_desconhecidas = [
        d for d in disciplinas_todas 
        if d not in mapeamento_disciplinas.values() and d not in mapeamento_disciplinas.keys()
    ]
    logger.info(f"Disciplinas desconhecidas: {disciplinas_desconhecidas}")
    
    tabela_estudos_realizados = [
        [quebra_linha("COMPONENTES CURRICULARES")] + [titulo("ANO")] * 18,
        [quebra_linha("COMPONENTES CURRICULARES"), "ALFABET./1º ANO", "ALFABET./1º ANO", "1ª SÉRIE/2º ANO", "1ª SÉRIE/2º ANO", 
         "2ª SÉRIE/3º ANO", "2ª SÉRIE/3º ANO", "3ª SÉRIE/4º ANO", "3ª SÉRIE/4º ANO", "4ª SÉRIE/5º ANO", 
         "4ª SÉRIE/5º ANO", "5ª SÉRIE/6º ANO", "5ª SÉRIE/6º ANO", "6ª SÉRIE/7º ANO", "6ª SÉRIE/7º ANO", 
         "7ª SÉRIE/8º ANO", "7ª SÉRIE/8º ANO", "8ª SÉRIE/9º ANO", "8ª SÉRIE/9º ANO"],
        [quebra_linha("COMPONENTES CURRICULARES"), "CONCEITO", "CH", "CONCEITO", "CH", "CONCEITO", "CH", "CONCEITO", "CH", "CONCEITO", 
         "CH", "CONCEITO", "CH", "CONCEITO", "CH", "CONCEITO", "CH", "CONCEITO", "CH"],
        [quebra_linha("LÍNGUA PORTUGUESA"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("MATEMÁTICA"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("HISTÓRIA"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("GEOGRAFIA"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("CIÊNCIAS"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("ARTE"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("ENSINO RELIGIOSO"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("EDUCAÇÃO FÍSICA"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("LÍNGUA INGLESA"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [quebra_linha("FILOSOFIA"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
    ]
    
    # Adiciona dinamicamente as disciplinas desconhecidas
    for disciplina in disciplinas_desconhecidas:
        tabela_estudos_realizados.append([quebra_linha(disciplina)] + ["--"] * 18)
    
    # Adiciona as linhas finais da tabela
    tabela_estudos_realizados.extend([
        [titulo("SITUAÇÃO FINAL"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"],
        [titulo("TOTAL/CH"), "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--", "--"]
    ])
    
    return tabela_estudos_realizados

def preencher_tabela_estudos_realizados(data_tabela_estudos_realizados, historico):

    def update_cell(row, col, value):
        if data_tabela_estudos_realizados[row][col] == "--":
            data_tabela_estudos_realizados[row][col] = value

    for disciplina, carga_horaria, serie, media, conceito, carga_horaria_total, ano_letivo_id in historico:
        # Verifica se a disciplina está no mapeamento
        disciplina_atual = mapeamento_disciplinas.get(disciplina, disciplina)
        
        for row_index in range(3, len(data_tabela_estudos_realizados) - 2):
            disciplina_texto = data_tabela_estudos_realizados[row_index][0].text if isinstance(data_tabela_estudos_realizados[row_index][0], Paragraph) else data_tabela_estudos_realizados[row_index][0]
            if disciplina_texto == disciplina_atual:
                col_index = (serie - 3) * 2 + 1
                if col_index <= len(data_tabela_estudos_realizados[0]):
                    if media is not None:
                        media_dividida = media / 10
                        if isinstance(media, (int, float)) and media == int(media):
                            update_cell(row_index, col_index, f"{media_dividida:.1f}")
                        else:
                            update_cell(row_index, col_index, f"{media_dividida:.2f}")
                    if conceito is not None:
                        update_cell(row_index, col_index, str(conceito))
                    carga_horaria_col = col_index + 1
                    if carga_horaria_col < len(data_tabela_estudos_realizados[0]):
                        update_cell(row_index, carga_horaria_col, str(carga_horaria) if carga_horaria and carga_horaria != "None" else "--")
                break

def is_valid_media(media):
    """Verifica se a média é um número válido."""
    return media not in ["--", "ND", ""] and isinstance(media, (int, float))

def preencher_situacao_final(data_tabela_estudos_realizados, quantitativo_serie_ids, carga_total_por_serie):
    situacao_final = []
    for row_index in range(3, len(data_tabela_estudos_realizados) - 2):
        medias = [
            float(data_tabela_estudos_realizados[row_index][col]) 
            for col in range(1, len(data_tabela_estudos_realizados[0]), 2) 
            if is_valid_media(data_tabela_estudos_realizados[row_index][col])
        ]
        conceitos_presentes = any(
            is_valid_media(data_tabela_estudos_realizados[row_index][col]) 
            for col in range(0, len(data_tabela_estudos_realizados[0]), 2)
        )
        if all(media >= 60 for media in medias):
            situacao_final.append("Promovido(a)")
        elif conceitos_presentes:
            situacao_final.append("Promovido(a)")
        else:
            situacao_final.append("Retido(a)")

    for serie_id in carga_total_por_serie.keys():
        situacao_col_index = (serie_id - 3) * 2 + 1
        carga_col_index = (serie_id - 3) * 2 + 2
        data_tabela_estudos_realizados[-2][situacao_col_index] = situacao_final[serie_id - 3]
        
        # Verifica se há carga horária total para esta série
        carga_horaria_total = carga_total_por_serie[serie_id]['carga_horaria_total']
        
        if carga_total_por_serie[serie_id]['todas_null']:
            # Se todas as cargas horárias individuais são nulas, usa a carga horária total
            if carga_horaria_total and carga_horaria_total != "None":
                data_tabela_estudos_realizados[-1][situacao_col_index] = f"{carga_horaria_total}H"
            else:
                data_tabela_estudos_realizados[-1][situacao_col_index] = "--"
        else:
            # Se há cargas horárias individuais, soma todas
            total_carga = sum(
                int(value.replace("H", "")) if isinstance(value, str) and value.replace("H", "").strip().isdigit() else 0
                for value in (data_tabela_estudos_realizados[i][carga_col_index] for i in range(3, len(data_tabela_estudos_realizados) - 2))
            )
            # Se a soma for maior que 0, usa a soma, senão usa a carga horária total
            if total_carga > 0:
                data_tabela_estudos_realizados[-1][situacao_col_index] = f"{total_carga}H"
            elif carga_horaria_total and carga_horaria_total != "None":
                data_tabela_estudos_realizados[-1][situacao_col_index] = f"{carga_horaria_total}H"
            else:
                data_tabela_estudos_realizados[-1][situacao_col_index] = "--"

def criar_tabela_estudos_realizados(data_tabela_estudos_realizados):
    # Cria a tabela com os dados fornecidos
    tabela_estudos_realizados = Table(data_tabela_estudos_realizados, colWidths=[1.17 * inch] + [0.477 * inch, 0.282 * inch] * 9, rowHeights=12)
    
    # Define o estilo da tabela usando cache
    if 'estudos_realizados' not in _STYLE_CACHE:
        _STYLE_CACHE['estudos_realizados'] = TableStyle([
        # Estilos gerais
        ('TEXTCOLOR', (0, 0), (-1, -1), 'black'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, 'black'),
        
        # SPAN para o cabeçalho
        ('SPAN', (0, 0), (0, 2)),  # Coluna "COMPONENTES CURRICULARES"
        ('SPAN', (1, 0), (18, 0)),  # Linha "ANO"
        ('SPAN', (1, 1), (2, 1)),  # "ALFABET./1º ANO"
        ('SPAN', (3, 1), (4, 1)),  # "1ª SÉRIE/2º ANO"
        ('SPAN', (5, 1), (6, 1)),  # "2ª SÉRIE/3º ANO"
        ('SPAN', (7, 1), (8, 1)),  # "3ª SÉRIE/4º ANO"
        ('SPAN', (9, 1), (10, 1)),  # "4ª SÉRIE/5º ANO"
        ('SPAN', (11, 1), (12, 1)),  # "5ª SÉRIE/6º ANO"
        ('SPAN', (13, 1), (14, 1)),  # "6ª SÉRIE/7º ANO"
        ('SPAN', (15, 1), (16, 1)),  # "7ª SÉRIE/8º ANO"
        ('SPAN', (17, 1), (18, 1)),  # "8ª SÉRIE/9º ANO"
        
        # SPAN para as linhas finais (SITUAÇÃO FINAL e TOTAL/CH)
        ('SPAN', (1, -2), (2, -2)),  # SITUAÇÃO FINAL
        ('SPAN', (3, -2), (4, -2)),
        ('SPAN', (5, -2), (6, -2)),
        ('SPAN', (7, -2), (8, -2)),
        ('SPAN', (9, -2), (10, -2)),
        ('SPAN', (11, -2), (12, -2)),
        ('SPAN', (13, -2), (14, -2)),
        ('SPAN', (15, -2), (16, -2)),
        ('SPAN', (17, -2), (18, -2)),

        ('SPAN', (1, -1), (2, -1)),  # SITUAÇÃO FINAL
        ('SPAN', (3, -1), (4, -1)),
        ('SPAN', (5, -1), (6, -1)),
        ('SPAN', (7, -1), (8, -1)),
        ('SPAN', (9, -1), (10, -1)),
        ('SPAN', (11, -1), (12, -1)),
        ('SPAN', (13, -1), (14, -1)),
        ('SPAN', (15, -1), (16, -1)),
        ('SPAN', (17, -1), (18, -1)),
        
        # Estilos de fonte para as colunas de conceitos
        ('FONTNAME', (1, 3), (1, -3), 'Helvetica-Bold'),  # Coluna 1
        ('FONTNAME', (3, 3), (3, -3), 'Helvetica-Bold'),  # Coluna 3
        ('FONTNAME', (5, 3), (5, -3), 'Helvetica-Bold'),  # Coluna 5
        ('FONTNAME', (7, 3), (7, -3), 'Helvetica-Bold'),  # Coluna 7
        ('FONTNAME', (9, 3), (9, -3), 'Helvetica-Bold'),  # Coluna 9
        ('FONTNAME', (11, 3), (11, -3), 'Helvetica-Bold'),  # Coluna 11
        ('FONTNAME', (13, 3), (13, -3), 'Helvetica-Bold'),  # Coluna 13
        ('FONTNAME', (15, 3), (15, -3), 'Helvetica-Bold'),  # Coluna 15
        ('FONTNAME', (17, 3), (17, -3), 'Helvetica-Bold'),  # Coluna 17
        
        # Estilo para as últimas duas linhas (SITUAÇÃO FINAL e TOTAL/CH)
        ('FONTNAME', (1, -2), (-1, -1), 'Helvetica-BoldOblique'),
        ])
    
    table_style_tabela3 = _STYLE_CACHE['estudos_realizados']
    # Aplica o estilo à tabela
    tabela_estudos_realizados.setStyle(table_style_tabela3)
    return tabela_estudos_realizados

def criar_tabela_caminho_escolar(resultados):
    data_tabela_caminho_escolar = [
        ["ANO", "ANO LETIVO", "ESTABELECIMENTO DE ENSINO", "LOCAL", "RESULTADO FINAL"],
        ["ALFABETIZAÇÃO/ 1° ANO", "--", "--", "--", "--"],
        ["1° SÉRIE/ 2° ANO", "--", "--", "--", "--"],
        ["2° SÉRIE/ 3° ANO", "--", "--", "--", "--"],
        ["3° SÉRIE/ 4° ANO", "--", "--", "--", "--"],
        ["4° SÉRIE/ 5° ANO", "--", "--", "--", "--"],
        ["5° SÉRIE/ 6° ANO", "--", "--", "--", "--"],
        ["6° SÉRIE/ 7° ANO", "--", "--", "--", "--"],
        ["7° SÉRIE/ 8° ANO", "--", "--", "--", "--"],
        ["8° SÉRIE/ 9° ANO", "--", "--", "--", "--"]
    ]
    serie_id_map = {
        3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9
    }
    for resultado in resultados:
        serie_id = resultado[1]
        ano_letivo = resultado[2]
        escola_nome = resultado[3]
        escola_municipio = resultado[4]
        situacao_final = resultado[5]
        if escola_nome == 'UI Profª Nadir Nascimento Moraes' or escola_nome == 'UEB Profª Nadir Nascimento Moraes':
            escola_nome += '*'
        serie_idx = serie_id_map.get(serie_id)
        if serie_idx:
            data_tabela_caminho_escolar[serie_idx][1] = ano_letivo
            data_tabela_caminho_escolar[serie_idx][2] = escola_nome
            data_tabela_caminho_escolar[serie_idx][3] = escola_municipio
            data_tabela_caminho_escolar[serie_idx][4] = situacao_final
    tabela_caminho_escolar = Table(data_tabela_caminho_escolar, colWidths=[1.17 * inch, 0.76 * inch, 2.28 * inch, 2.28 * inch, 1.52 * inch], rowHeights=14)
    
    if 'caminho_escolar' not in _STYLE_CACHE:
        _STYLE_CACHE['caminho_escolar'] = TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), 'black'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, 'black'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (3, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (4, 1), (4, -1), 'Helvetica-BoldOblique'),
        ])
    
    tabela_caminho_escolar.setStyle(_STYLE_CACHE['caminho_escolar'])
    return tabela_caminho_escolar

def criar_tabela_observacoes(resultados, num_disciplinas_desconhecidas=0):
    # Texto base da observação
    texto_base = "Observação: Documento expedido em época legal, sem emendas ou rasuras."
    
    # Cache do estilo de tabela de observações
    if 'observacoes_table' not in _STYLE_CACHE:
        _STYLE_CACHE['observacoes_table'] = TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), 'black'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), 
            ('FONTSIZE', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, 'black'),
        ])
    
    # Buscar observações do banco de dados
    conn = conectar_bd()
    if not conn:
        logger.error("Erro: Não foi possível conectar ao banco de dados para buscar observações")
        # Retorna tabela apenas com observação base
        obs_style = _get_cached_style('obs_title', fontSize=8, alignment=4, leading=10)
        paragrafo_obs = Paragraph(texto_base, obs_style)
        data_tabela_observacoes = [[paragrafo_obs, ""]]
        tabela_observacoes = Table(data_tabela_observacoes, colWidths=[4.21 * inch, 3.78 * inch])
        tabela_observacoes.setStyle(_STYLE_CACHE['observacoes_table'])
        return tabela_observacoes
    
    cursor = conn.cursor()
    observacoes_adicionais = set()  # Usando set para evitar duplicatas
    
    try:
        logger.info("Início da busca de observações")
        logger.info(f"Número total de resultados para buscar observações: {len(resultados)}")
        
        # Para cada resultado (série/ano), buscar observações correspondentes
        for resultado in resultados:
            serie_id = resultado[0]  # Primeiro elemento é serie_id
            ano_letivo_id = resultado[1]  # Segundo elemento é ano_letivo_id
            escola_id = resultado[2]  # Terceiro elemento é escola_id
            
            logger.info(f"Buscando observações para: série_id={serie_id}, ano_letivo_id={ano_letivo_id}, escola_id={escola_id}")
            
            # Buscar observações específicas
            cursor.execute("""
                SELECT observacao 
                FROM observacoes_historico 
                WHERE serie_id = %s AND ano_letivo_id = %s AND escola_id = %s
            """, (serie_id, ano_letivo_id, escola_id))
            
            obs = cursor.fetchone()
            if obs and obs[0]:
                # Obter o nome da escola para prefixar a observação
                cursor.execute("SELECT nome FROM escolas WHERE id = %s", (escola_id,))
                escola_nome_result = cursor.fetchone()
                if escola_nome_result:
                    escola_nome_obs = escola_nome_result[0]
                    obs_formatada = f"<b>[{escola_nome_obs}]</b> {obs[0]}"
                    logger.info(f"Observação encontrada: {obs_formatada}")
                    observacoes_adicionais.add(obs_formatada)
            else:
                logger.info("Nenhuma observação encontrada para estes parâmetros")
            
            # Verificar se é a escola que precisa da observação especial
            cursor.execute("SELECT nome FROM escolas WHERE id = %s", (escola_id,))
            escola_nome_result = cursor.fetchone()
            if escola_nome_result:
                escola_nome = escola_nome_result[0]
                if escola_nome == 'UI Profª Nadir Nascimento Moraes' or escola_nome == 'UEB Profª Nadir Nascimento Moraes':
                    obs_escola = "*A unidade escolar mencionada neste documento teve sua denominação alterada para <b>Escola Municipal Profª Nadir Nascimento Moraes</b>, conforme estabelecido pelo <b>Decreto nº 4.006, de 29 de janeiro de 2025.</b>"
                    obs_escola_formatada = f"<b>[{escola_nome}]</b> {obs_escola}"
                    logger.info(f"Adicionando observação especial da escola: {obs_escola_formatada}")
                    observacoes_adicionais.add(obs_escola_formatada)
    finally:
        cursor.close()
        conn.close()
    
    logger.info("Resumo das observações")
    logger.info(f"Total de observações encontradas: {len(observacoes_adicionais)}")
    for i, obs in enumerate(observacoes_adicionais, 1):
        logger.info(f"{i}. {obs}")
    
    # Combinar todas as observações; altura agora é automática pela tabela
    texto_completo = texto_base
    if observacoes_adicionais:
        texto_completo += "<br/><b>Observações por escola:</b><br/>" + "<br/>".join(observacoes_adicionais)

    obs_style = _get_cached_style('obs_title', fontSize=8, alignment=4, leading=10)
    paragrafo_obs = Paragraph(texto_completo, obs_style)

    data_tabela_observacoes = [[paragrafo_obs, ""]]
    # Sem rowHeights: o ReportLab calcula a altura exata conforme o conteúdo
    tabela_observacoes = Table(data_tabela_observacoes, colWidths=[4.21 * inch, 3.78 * inch])
    tabela_observacoes.setStyle(_STYLE_CACHE['observacoes_table'])
    return tabela_observacoes

def criar_tabela_informacoes():
    data_tabela_informacoes = [
        ["Ciclo de Alfabetização", "4° Ano ao 9° Ano"],
        ["AD: Aprovação Direta", "AD: Aprovação Direta"],
        ["PNAD: Promovidos com Necessidade de Apoio Didático (1º e 2º ano)", "PNAD: Promovidos com Necessidade de Apoio Didático (3º ano)"],
        ["APNAD:  Aprovação com Necessidade de Apoio Didático", "RT: Retido"],
        ["RT: Retido", ""]
    ]
    tabela_informacoes = Table(data_tabela_informacoes, colWidths=[4.21 * inch, 3.78 * inch], rowHeights=9)
    
    if 'informacoes' not in _STYLE_CACHE:
        _STYLE_CACHE['informacoes'] = TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), 'black'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (0, -1), 0.5, 'black'),
            ('BOX', (1, 0), (1, -1), 0.5, 'black'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
        ])
    
    tabela_informacoes.setStyle(_STYLE_CACHE['informacoes'])
    return tabela_informacoes

def criar_tabela_legenda(data_documento):
    data_tabela_legenda = [
        ["TABELA DE CONVERSÃO","D - Desenvolvido - 10.0 / PD - Parcialmente Desenvolvido - 8.0 a 9.0",f"Paço do Lumiar - MA, {data_documento}."],
        ["TABELA DE CONVERSÃO","ED - Em Desenvolvimento - 6.0 a 7.0 / ND - Não desenvolveu - 5.0",f"Paço do Lumiar - MA, {data_documento}."]
    ]
    tabela_legenda = Table(data_tabela_legenda, colWidths=[1.17 * inch, 3.8 * inch, 3.02 * inch], rowHeights=10)
    
    if 'legenda' not in _STYLE_CACHE:
        _STYLE_CACHE['legenda'] = TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), 'black'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOX', (0, 0), (0, -1), 0.5, 'black'),
            ('BOX', (1, 0), (1, -1), 0.5, 'black'),
            ('BOX', (2, 0), (2, -1), 0.5, 'black'),
            ('SPAN', (0, 0), (0, 1)),
            ('SPAN', (2, 0), (2, 1)),
        ])
    
    tabela_legenda.setStyle(_STYLE_CACHE['legenda'])
    return tabela_legenda

def criar_tabela_assinatura():
    estilo_centro = _get_cached_style('centro_assinatura', fontSize=8, alignment=1)
    paragrafo_secretario = Paragraph("______________________________________________________________<br/>Responsável pelo Preenchimento", estilo_centro)
    paragrafo_gestor = Paragraph("______________________________________________________________<br/>Gestor(a)", estilo_centro)
    dados_tabela_assinatura = [[paragrafo_secretario, paragrafo_gestor]]
    tabela_assinatura = Table(dados_tabela_assinatura, colWidths=[4 * inch, 4 * inch], rowHeights=13)
    
    if 'assinatura' not in _STYLE_CACHE:
        _STYLE_CACHE['assinatura'] = TableStyle([('VALIGN', (0, 0), (-1, -1), 'BOTTOM')])
    
    tabela_assinatura.setStyle(_STYLE_CACHE['assinatura'])
    return tabela_assinatura

def historico_escolar(aluno_id,
                      aluno=None,
                      escola=None,
                      responsaveis=None,
                      historico=None,
                      resultados=None,
                      dados_observacoes=None,
                      carga_total_por_serie=None,
                      disciplinas=None):
    logger = get_logger(__name__)
    logger.info(f"historico_escolar: chamado para aluno_id={aluno_id} com parametros fornecidos: aluno={bool(aluno)}, escola={bool(escola)}, responsaveis={bool(responsaveis)}, historico={bool(historico)}, resultados={bool(resultados)}, dados_observacoes={bool(dados_observacoes)}, carga_total_por_serie={bool(carga_total_por_serie)}, disciplinas={bool(disciplinas)}")

    conn = conectar_bd()
    if not conn:
        logger.error("Erro: Não foi possível conectar ao banco de dados")
        return
        
    cursor = conn.cursor()
    escola_id = 60

    # Se um objeto `escola` foi fornecido pela interface, usá-lo em vez de consultar o BD
    if escola is not None:
        # aceitar dicts ou tuplas no formato esperado
        if isinstance(escola, dict):
            dados_escola = (
                escola.get('id'),
                escola.get('nome'),
                escola.get('endereco'),
                escola.get('inep'),
                escola.get('cnpj'),
                escola.get('municipio')
            )
        else:
            dados_escola = escola
        logger.info("Usando dados da escola fornecidos pela interface/cache")
    else:
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
        start_q = time.time()
        cursor.execute(query_escola, (escola_id,))
        dados_escola = cursor.fetchone()
        elapsed_ms = int((time.time() - start_q) * 1000)
        logger.info(f"event=db_query name=select_escola escola_id={escola_id} duration_ms={elapsed_ms}")

    # Se `aluno` foi passado pela interface, usar os dados fornecidos
    if aluno is not None:
        if isinstance(aluno, dict):
            dados_aluno = (
                aluno.get('nome'),
                aluno.get('data_nascimento'),
                aluno.get('sexo'),
                aluno.get('local_nascimento'),
                aluno.get('UF_nascimento')
            )
        else:
            dados_aluno = aluno
        logger.info("Usando dados do aluno fornecidos pela interface/cache")
    else:
        query_aluno = """
        SELECT 
            a.nome AS nome_aluno, 
            a.data_nascimento AS nascimento, 
            a.sexo AS sexo,
            a.local_nascimento AS localn,
            a.UF_nascimento AS uf
        FROM 
            Alunos a
        WHERE 
            a.id = %s;
    """
        start_q = time.time()
        cursor.execute(query_aluno, (aluno_id,))
        dados_aluno = cursor.fetchone()
        elapsed_ms = int((time.time() - start_q) * 1000)
        logger.info(f"event=db_query name=select_aluno aluno_id={aluno_id} duration_ms={elapsed_ms}")

    # Responsáveis: aceitar lista de strings ou estrutura similar retornada pelo BD
    if responsaveis is not None:
        # converter lista de nomes em formato semelhante ao fetchall() [(nome,), ...]
        if responsaveis and isinstance(responsaveis[0], str):
            responsaveis = [(r,) for r in responsaveis]
        logger.info("Usando lista de responsáveis fornecida pela interface/cache")
    else:
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
        start_q = time.time()
        cursor.execute(query_responsaveis, (aluno_id,))
        responsaveis = cursor.fetchall()
        elapsed_ms = int((time.time() - start_q) * 1000)
        logger.info(f"event=db_query name=select_responsaveis aluno_id={aluno_id} duration_ms={elapsed_ms} rows={len(responsaveis) if responsaveis is not None else 0}")

    # Histórico por disciplina: usar parâmetro se fornecido para evitar reconsulta
    if historico is not None:
        logger.info("Usando histórico fornecido pela interface/cache")
    else:
        query_historico = """
        SELECT 
            d.nome AS disciplina,
            d.carga_horaria,
            h.serie_id,
            h.media,
            h.conceito,
            cht.carga_horaria_total,
            h.ano_letivo_id
        FROM 
            historico_escolar AS h
        JOIN 
            disciplinas AS d ON h.disciplina_id = d.id
        LEFT JOIN 
            carga_horaria_total AS cht ON h.serie_id = cht.serie_id
            AND h.ano_letivo_id = cht.ano_letivo_id 
            AND h.escola_id = cht.escola_id
        WHERE 
            h.aluno_id = %s
        ORDER BY 
            h.serie_id;
        """
        start_q = time.time()
        cursor.execute(query_historico, (aluno_id,))
        historico = cursor.fetchall()
        elapsed_ms = int((time.time() - start_q) * 1000)
        logger.info(f"event=db_query name=select_historico aluno_id={aluno_id} duration_ms={elapsed_ms} rows={len(historico) if historico is not None else 0}")

    if not historico:
        logger.info("Nenhum histórico encontrado para o aluno.")
        return

    # Se o chamador já forneceu `carga_total_por_serie`, respeitar esse dicionário
    # (ex.: quando o wrapper montou o mapa a partir do cache). Caso contrário,
    # calcular com base no `historico` retornado do BD.
    if carga_total_por_serie is None:
        carga_total_por_serie = {}
        serie_ids_unicos = set()
        for registro in historico:
            disciplina, carga_horaria, serie_id, media, conceito, carga_horaria_total, ano_letivo_id = registro
            serie_ids_unicos.add(serie_id)
            if serie_id not in carga_total_por_serie:
                carga_total_por_serie[serie_id] = {
                    'carga_total': 0,
                    'todas_null': True,
                    'carga_horaria_total': carga_horaria_total
                }
            if carga_horaria is not None:
                carga_total_por_serie[serie_id]['todas_null'] = False
                n = to_safe_int(carga_horaria)
                if n is not None:
                    carga_total_por_serie[serie_id]['carga_total'] += n
    else:
        # Garantir que as chaves/estruturas esperadas existam e coletar os ids
        serie_ids_unicos = set()
        try:
            for sid, info in carga_total_por_serie.items():
                serie_ids_unicos.add(sid)
                # normalizar estrutura mínima
                if not isinstance(info, dict):
                    carga_total_por_serie[sid] = {'carga_total': None, 'todas_null': True, 'carga_horaria_total': None}
                else:
                    info.setdefault('carga_total', None)
                    info.setdefault('todas_null', True)
                    info.setdefault('carga_horaria_total', None)
        except Exception:
            # Em caso de formato inesperado, recuperar comportamento seguro
            carga_total_por_serie = {}
            serie_ids_unicos = set()

    for serie_id in serie_ids_unicos:
        try:
            if carga_total_por_serie[serie_id].get('todas_null'):
                carga_total_por_serie[serie_id]['carga_total'] = carga_total_por_serie[serie_id].get('carga_horaria_total')
            logger.info(f"serie_id={serie_id} carga_total={carga_total_por_serie[serie_id].get('carga_total')}")
        except Exception:
            logger.exception(f"Erro ao obter carga_total para serie_id={serie_id}")
    quantitativo_serie_ids = len(serie_ids_unicos)

    if resultados is not None:
        logger.info("Usando resultados (resumo por série) fornecidos pela interface/cache")
    else:
        query_historia_escolar = """
        SELECT 
            h.aluno_id,
            h.serie_id,
            a.ano_letivo,
            e.nome AS escola_nome,
            e.municipio AS escola_municipio,
            CASE
                WHEN COUNT(h.media) = 0 AND COUNT(h.conceito) > 0 THEN 'Promovido(a)'
                WHEN MIN(h.media) >= 60 THEN 'Promovido(a)'
                WHEN MIN(h.media) < 60 THEN 'Retido(a)'
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
        start_q = time.time()
        cursor.execute(query_historia_escolar, (aluno_id,))
        resultados = cursor.fetchall()
        elapsed_ms = int((time.time() - start_q) * 1000)
        logger.info(f"event=db_query name=select_resultados_por_serie aluno_id={aluno_id} duration_ms={elapsed_ms} rows={len(resultados) if resultados is not None else 0}")
    
    # Buscar os IDs dos anos letivos para as observações
    if dados_observacoes is not None:
        logger.info("Usando dados_observacoes fornecidos pela interface/cache")
    else:
        query_anos_letivos = """
        SELECT DISTINCT h.serie_id, h.ano_letivo_id, h.escola_id
        FROM historico_escolar h
        WHERE h.aluno_id = %s
        ORDER BY h.serie_id;
        """
        start_q = time.time()
        cursor.execute(query_anos_letivos, (aluno_id,))
        dados_observacoes = cursor.fetchall()
        elapsed_ms = int((time.time() - start_q) * 1000)
        logger.info(f"event=db_query name=select_anos_letivos_para_observacoes aluno_id={aluno_id} duration_ms={elapsed_ms} rows={len(dados_observacoes) if dados_observacoes is not None else 0}")
    
    cursor.close()
    conn.close()

    if not dados_aluno:
        logger.error("Aluno não encontrado.")
        return

    # Ordem correta conforme SELECT: nome, data_nascimento, sexo, local_nascimento, UF_nascimento
    nome_aluno, nascimento, sexo, localn, uf = dados_aluno
    responsavel1 = responsaveis[0][0] if len(responsaveis) > 0 else None
    responsavel2 = responsaveis[1][0] if len(responsaveis) > 1 else None
    if responsavel1 and responsavel2:
        filho_de_texto = f'<b>FILHO DE:</b> {responsavel1} e {responsavel2}'
    elif responsavel1:
        filho_de_texto = f'<b>FILHO DE:</b> {responsavel1}'
    elif responsavel2:
        filho_de_texto = f'<b>FILHO DE:</b> {responsavel2}'
    else:
        filho_de_texto = f'<b>FILHO DE:</b>'

    # Formatação segura da data de nascimento
    from datetime import date
    data_nascimento = ""
    if nascimento is not None:
        try:
            # Se nascimento é uma string, tenta diferentes formatos
            if isinstance(nascimento, str):
                # Tenta formato YYYY-MM-DD
                try:
                    data_obj = datetime.strptime(nascimento, "%Y-%m-%d")
                    data_nascimento = data_obj.strftime("%d/%m/%Y")
                except ValueError:
                    # Tenta formato DD/MM/YYYY
                    try:
                        data_obj = datetime.strptime(nascimento, "%d/%m/%Y")
                        data_nascimento = data_obj.strftime("%d/%m/%Y")
                    except ValueError:
                        # Se não conseguir parsear, deixa como está
                        data_nascimento = nascimento
                    
            # Se nascimento já é um objeto datetime ou date
            elif isinstance(nascimento, (datetime, date)):
                data_nascimento = nascimento.strftime("%d/%m/%Y")
            else:
                # Para outros tipos, tenta converter para string
                data_nascimento = str(nascimento)
                
        except (ValueError, TypeError, AttributeError) as e:
            logger.exception(f"Erro ao formatar data de nascimento: {e}")
            data_nascimento = str(nascimento) if nascimento else ""
    data_documento = formatar_data(datetime.now())

    if dados_escola:
        nome_escola, inep_escola, cnpj_escola, endereco_escola, municipio_escola = dados_escola[1], dados_escola[3], dados_escola[4], dados_escola[2], dados_escola[5]
        cabecalho = [
            "<b>PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR</b>",
            "<b>SECRETARIA MUNICIPAL DE EDUCAÇÃO</b>",
            f"<b>CNPJ: {cnpj_escola}</b>",
            "<b>Resolução nº 202/95 de 08/11/1995</b>",
            f"<b>INEP: {inep_escola}</b>"
        ]
    else:
        logger.error("Dados da escola não encontrados.")
        return

    figura_superior = os.path.join(os.path.dirname(__file__), 'imagens', 'pacologo.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), 'imagens', 'logopacobranco.png')

    buffer = io.BytesIO()
    left_margin = 18
    right_margin = 18
    top_margin = 20
    bottom_margin = 10

    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        leftMargin=left_margin, 
        rightMargin=right_margin, 
        topMargin=top_margin, 
        bottomMargin=bottom_margin
    )
    elements = []

    # Criar uma tabela para o cabeçalho usando cache de imagens
    img_sup = _get_cached_image(figura_superior, 0.75 * inch, 0.75 * inch)
    img_inf = _get_cached_image(figura_inferior, 1.5 * inch, 1 * inch)
    header_style = _get_cached_style('hist_header', fontSize=8, alignment=1)
    
    data = [
        [img_sup,
         Paragraph('<br/>'.join(cabecalho), header_style),
         img_inf]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch], rowHeights=9)
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))

    # Cache de estilos para tabela de identificação
    title_style = _get_cached_style('id_title', fontSize=8, alignment=1)
    address_style = _get_cached_style('id_address', fontSize=8, alignment=1)
    data_title_style = _get_cached_style('id_data_title', fontSize=8, alignment=1)
    label_left_style = _get_cached_style('id_label_left', fontSize=8, alignment=0)
    label_center_style = _get_cached_style('id_label_center', fontSize=8, alignment=1)
    
    data_tabela1 = [
        [Paragraph(f'<b>"{nome_escola}"</b>', title_style)],
        [Paragraph(f'<i>{endereco_escola}, {municipio_escola}</i>', address_style)],
        [Paragraph('<b>DADOS ALUNO</b>', data_title_style)],
        [Paragraph(f'<b>NOME:</b> {nome_aluno}', label_left_style)],
        [
            Paragraph(f'<b>NATURAL DE:</b> {localn or ""}', label_left_style),
            Paragraph(f'<b>UF:</b>', label_center_style),
            Paragraph(f'{uf or ""}', label_center_style),
            Paragraph(f'<b>DATA DE NASCIMENTO:</b> {data_nascimento}', label_left_style)
        ],
        [Paragraph(filho_de_texto, label_left_style)]
    ]
    table_style_tabela1 = TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('SPAN', (0, 1), (-1, 1)),
        ('SPAN', (0, 2), (-1, 2)),
        ('SPAN', (0, 3), (-1, 3)),
        ('SPAN', (0, 5), (-1, 5)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1),0.5, 'black'),
    ])
    tabela_identificacao = Table(data_tabela1, colWidths=[3.12 * inch, 0.49 * inch, 0.49 * inch, 3.9 * inch], rowHeights=14)
    tabela_identificacao.setStyle(table_style_tabela1)
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(tabela_identificacao)

    estudos_title_style = _get_cached_style('estudos_title', fontSize=7, alignment=1)
    data_tabela1 = [
        [Paragraph('<b>ESTUDOS REALIZADOS</b>', estudos_title_style)]
    ]
    
    if 'estudos_inicio' not in _STYLE_CACHE:
        _STYLE_CACHE['estudos_inicio'] = TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1),0.5, 'black'),
        ])
    
    tabela_inicio = Table(data_tabela1, colWidths=[8 * inch], rowHeights=9)
    tabela_inicio.setStyle(_STYLE_CACHE['estudos_inicio'])
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(tabela_inicio)
    elements.append(Spacer(1, 0.1 * inch))

    data_tabela_estudos_realizados = substituir_disciplinas(aluno_id)
    preencher_tabela_estudos_realizados(data_tabela_estudos_realizados, historico)
    preencher_situacao_final(data_tabela_estudos_realizados, quantitativo_serie_ids, carga_total_por_serie)
    tabela_estudos_realizados = criar_tabela_estudos_realizados(data_tabela_estudos_realizados)
    elements.append(tabela_estudos_realizados)
    elements.append(Spacer(1, 0.1 * inch))

    tabela_caminho_escolar = criar_tabela_caminho_escolar(resultados)
    elements.append(tabela_caminho_escolar)
    elements.append(Spacer(1, 0.1 * inch))

    disciplinas_desconhecidas = obter_disciplinas_do_historico(aluno_id)
    num_disciplinas_desconhecidas = len([d for d in disciplinas_desconhecidas if d not in [
        "PORTUGUÊS", "MATEMÁTICA", "HISTÓRIA", "GEOGRAFIA", 
        "CIÊNCIAS", "ARTES", "ENS. RELIGIOSO", "ED. FÍSICA", 
        "INGLÊS", "FILOSOFIA", "TEATRO", "ÉTICA E CIDADANIA"
    ]])
    
    # Log para acompanhamento dos ajustes de layout
    logger.info(f"Número de disciplinas desconhecidas: {num_disciplinas_desconhecidas}")
    
    # Ajusta o espaçamento baseado no número de disciplinas extras
    # Isso ajudará a manter o documento em uma única página
    espacamento = max(0.05, 0.1 - (max(0, num_disciplinas_desconhecidas - 2) * 0.01)) * inch
    logger.info(f"Espaçamento ajustado: {espacamento/inch:.2f} inch")
    
    # Usar dados_observacoes em vez de resultados para a tabela de observações
    tabela_observacoes = criar_tabela_observacoes(dados_observacoes, num_disciplinas_desconhecidas)
    elements.append(tabela_observacoes)
    elements.append(Spacer(1, espacamento))

    tabela_informacoes = criar_tabela_informacoes()
    elements.append(tabela_informacoes)
    elements.append(Spacer(1, espacamento))

    tabela_legenda = criar_tabela_legenda(data_documento)
    elements.append(tabela_legenda)
    elements.append(Spacer(1, max(0.3, 0.65 - (max(0, num_disciplinas_desconhecidas - 2) * 0.05)) * inch))

    tabela_assinatura = criar_tabela_assinatura()
    elements.append(tabela_assinatura)
    # Medir tempo de renderização/geração do PDF
    start_render = time.time()
    doc.build(elements)
    elapsed_render_ms = int((time.time() - start_render) * 1000)
    logger.info(f"event=pdf_render name=historico_escolar duration_ms={elapsed_render_ms}")

    # Resetar o buffer para o início
    buffer.seek(0)
    
    # Criar nome do arquivo
    data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Garantir que nome_aluno é uma string antes de usar replace
    nome_aluno_str = str(nome_aluno) if nome_aluno is not None else "Aluno"
    nome_arquivo = f"Historico_{nome_aluno_str.replace(' ', '_')}_{data_atual}.pdf"
    caminho_arquivo = os.path.join('documentos_gerados', nome_arquivo)
    
    # Garantir que o diretório existe
    os.makedirs('documentos_gerados', exist_ok=True)
    
    # Salvar o arquivo localmente
    with open(caminho_arquivo, 'wb') as f:
        f.write(buffer.getvalue())
    
    # Criar descrição detalhada
    series = sorted(list(serie_ids_unicos))
    descricao = f"Histórico Escolar do aluno {nome_aluno_str}"
    if series:
        descricao += f" - {min(series)}ª a {max(series)}ª série"
    
    # Salvar no sistema de gerenciamento de documentos
    sucesso, mensagem, link = salvar_documento_sistema(
        caminho_arquivo=caminho_arquivo,
        tipo_documento=TIPO_HISTORICO,
        aluno_id=aluno_id,
        finalidade="Histórico Escolar",
        descricao=descricao
    )
    
    if not sucesso:
        from tkinter import messagebox
        messagebox.showwarning("Aviso", 
                           "O histórico escolar foi gerado mas houve um erro ao salvá-lo no sistema:\n" + mensagem)
    
    salvar_e_abrir_pdf(buffer)

# historico_escolar(942)