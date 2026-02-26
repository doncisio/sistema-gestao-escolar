"""
Gerador de PDF para Termo de Autorização - Programa "Cuidar dos Olhos"
Gera termos preenchidos com dados dos alunos e responsáveis
"""
from src.core.config_logs import get_logger
from src.core.config import get_image_path, ANO_LETIVO_ATUAL, PROJECT_ROOT
from src.core.conexao import conectar_bd
logger = get_logger(__name__)

import io
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from PyPDF2 import PdfWriter
from pathlib import Path
import datetime

# Dicionário de meses em português
MESES_PT = {
    1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
    5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
    9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
}


def obter_dados_escola(escola_id=60):
    """Obtém dados da escola do banco de dados."""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT nome FROM escolas WHERE id = %s"
        cursor.execute(query, (escola_id,))
        resultado = cursor.fetchone()
        return resultado['nome'] if resultado else "Escola não encontrada"
    finally:
        cursor.close()
        conn.close()


def obter_alunos_ativos(turma_id=None):
    """
    Obtém todos os alunos ativos do ano letivo atual com dados da turma.
    
    Args:
        turma_id: ID da turma para filtrar (opcional). Se None, retorna todos.
    """
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                a.id,
                a.nome AS nome_aluno,
                a.data_nascimento,
                a.cpf,
                s.nome AS nome_serie,
                t.nome AS nome_turma,
                t.turno,
                s.id AS serie_id,
                t.id AS turma_id
            FROM 
                Alunos a
            JOIN 
                Matriculas m ON a.id = m.aluno_id
            JOIN 
                Turmas t ON m.turma_id = t.id
            JOIN 
                series s ON t.serie_id = s.id
            WHERE 
                m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
            AND 
                a.escola_id = 60
            AND
                m.status = 'Ativo'
        """
        
        params = [ANO_LETIVO_ATUAL]
        
        # Filtrar por turma se especificado
        if turma_id is not None:
            query += " AND t.id = %s"
            params.append(turma_id)
        
        query += """
            ORDER BY
                s.id, t.nome, a.nome
        """
        
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obter_turmas_ativas():
    """Obtém lista de turmas com alunos ativos no ano letivo atual."""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT DISTINCT
                t.id AS turma_id,
                s.id AS serie_id,
                s.nome AS nome_serie,
                t.nome AS nome_turma,
                t.turno,
                COUNT(DISTINCT a.id) AS total_alunos
            FROM 
                Turmas t
            JOIN 
                series s ON t.serie_id = s.id
            JOIN
                Matriculas m ON m.turma_id = t.id
            JOIN
                Alunos a ON a.id = m.aluno_id
            WHERE 
                m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
            AND 
                a.escola_id = 60
            AND
                m.status = 'Ativo'
            GROUP BY
                t.id, s.id, s.nome, t.nome, t.turno
            ORDER BY
                s.id, t.nome
        """
        cursor.execute(query, (ANO_LETIVO_ATUAL,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obter_responsaveis_do_aluno(aluno_id):
    """Obtém todos os responsáveis de um aluno específico."""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                r.id,
                r.nome,
                r.telefone
            FROM 
                Responsaveis r
            JOIN 
                ResponsaveisAlunos ra ON r.id = ra.responsavel_id  
            WHERE 
                ra.aluno_id = %s
            ORDER BY
                r.nome
        """
        cursor.execute(query, (aluno_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obter_professores_ativos(escola_id=60):
    """Obtém todos os professores ativos da escola."""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                id,
                nome,
                cpf,
                data_nascimento,
                cargo,
                matricula,
                telefone,
                whatsapp
            FROM 
                funcionarios
            WHERE 
                escola_id = %s
                AND cargo = 'Professor@'
            ORDER BY
                nome
        """
        cursor.execute(query, (escola_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obter_servidores_ativos(escola_id=60):
    """Obtém todos os servidores ativos da escola (exceto professores)."""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                id,
                nome,
                cpf,
                data_nascimento,
                cargo,
                matricula,
                telefone,
                whatsapp
            FROM 
                funcionarios
            WHERE 
                escola_id = %s
                AND cargo != 'Professor@'
            ORDER BY
                nome
        """
        cursor.execute(query, (escola_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def adicionar_cabecalho(elements):
    """Adiciona o cabeçalho com logo no topo."""
    # Caminho da imagem do logo
    logo_path = str(PROJECT_ROOT / 'imagens' / 'pacologo.png')
    
    # Adicionar logo centralizado
    img = Image(logo_path, width=1.2 * inch, height=1.2 * inch)
    img.hAlign = 'CENTER'
    elements.append(img)
    elements.append(Spacer(1, 0.2*inch))


def adicionar_rodape_pagina(canvas_obj, doc):
    """Callback para adicionar rodapé fixo em cada página."""
    # Caminho da imagem do rodapé
    rodape_path = str(PROJECT_ROOT / 'imagens' / 'rodapepaco.png')
    
    # Usar largura total da página A4 (não apenas área de texto)
    largura_pagina = A4[0]  # Largura total da página
    altura_rodape = 0.8 * inch
    
    # Posição: x = 0 (borda esquerda da página), y = bem no fundo
    x_pos = 0
    y_pos = 0 * inch  # 0 inch acima da borda inferior da página
    
    # Desenhar imagem no canvas ocupando toda a largura da página
    canvas_obj.drawImage(
        rodape_path,
        x_pos,
        y_pos,
        width=largura_pagina,
        height=altura_rodape,
        preserveAspectRatio=False,  # Esticar para ocupar toda largura
        mask='auto'
    )


def gerar_termo_individual(aluno, responsavel, nome_escola, tipo_participante='estudante'):
    """
    Gera um termo individual preenchido para um aluno e responsável.
    
    Args:
        aluno: Dicionário com dados do aluno/funcionário
        responsavel: Dicionário com dados do responsável (para estudantes) ou None (para professores/servidores)
        nome_escola: Nome da escola
        tipo_participante: 'estudante', 'professor' ou 'servidor'
        
    Returns:
        BytesIO: Buffer com o PDF gerado
    """
    buffer = io.BytesIO()
    
    # Criar documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=1.0*cm,
        bottomMargin=3*cm  # Aumentar margem inferior para acomodar rodapé
    )
    
    elements = []
    
    # Adicionar cabeçalho com logo
    adicionar_cabecalho(elements)
    
    # Título do documento
    cabecalho_texto = ParagraphStyle(
        'CabecalhoTexto',
        fontSize=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=12
    )
    elements.append(Paragraph(
        "ESTADO DO MARANHÃO<br/>MUNICÍPIO DE PAÇO DO LUMIAR<br/>SECRETARIA MUNICIPAL DE EDUCAÇÃO - SEMED",
        cabecalho_texto
    ))
    elements.append(Spacer(1, 0.3*inch))
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para o título
    titulo_style = ParagraphStyle(
        'TituloTermo',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=0.1*inch
    )
    
    # Estilo para subtítulo
    subtitulo_style = ParagraphStyle(
        'SubtituloTermo',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=0.3*inch
    )
    
    # Estilo para texto justificado
    texto_style = ParagraphStyle(
        'TextoJustificado',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        leading=14,
        spaceAfter=0.15*inch
    )
    
    # Estilo para campos
    campo_style = ParagraphStyle(
        'Campo',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        leading=16,
        leftIndent=0
    )
    
    # Estilo para data alinhada à direita
    data_style = ParagraphStyle(
        'DataDireita',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        leading=16
    )
    
    # Título
    elements.append(Paragraph("<b>TERMO DE AUTORIZAÇÃO E INTERESSE</b>", titulo_style))
    elements.append(Paragraph('<b>Programa "Cuidar dos Olhos"</b>', subtitulo_style))
    
    # Nome conforme tipo de participante
    if tipo_participante == 'estudante':
        # Para estudantes: nome do responsável
        nome_responsavel = responsavel['nome'] if responsavel else "_" * 100
        elements.append(Paragraph(
            f"Eu, <b>{nome_responsavel}</b>,",
            campo_style
        ))
    else:
        # Para professores e servidores: próprio nome
        nome_pessoa = aluno.get('nome_aluno') or aluno.get('nome') or "_" * 100
        elements.append(Paragraph(
            f"Eu, <b>{nome_pessoa}</b>,",
            campo_style
        ))
    elements.append(Spacer(1, 0.1*inch))
    
    # Checkbox responsável/interessado
    if tipo_participante == 'estudante':
        elements.append(Paragraph(
            "[<b>X</b>] Responsável legal pelo(a) estudante",
            campo_style
        ))
        elements.append(Paragraph(
            "[  ] Próprio(a) interessado(a) (maior de idade)",
            campo_style
        ))
    else:
        elements.append(Paragraph(
            "[  ] Responsável legal pelo(a) estudante",
            campo_style
        ))
        elements.append(Paragraph(
            "[<b>X</b>] Próprio(a) interessado(a) (maior de idade)",
            campo_style
        ))
    elements.append(Spacer(1, 0.15*inch))
    
    # Nome do estudante/servidor
    nome_pessoa = aluno.get('nome_aluno') or aluno.get('nome') or "_" * 100
    elements.append(Paragraph(
        f"Nome do estudante/servidor: <b>{nome_pessoa}</b>",
        campo_style
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    # Data de nascimento (preenchida se disponível)
    data_nasc = aluno.get('data_nascimento')
    if data_nasc:
        data_nasc_formatada = data_nasc.strftime('%d/%m/%Y') if hasattr(data_nasc, 'strftime') else str(data_nasc)
    else:
        data_nasc_formatada = "____/____/________"
    
    elements.append(Paragraph(
        f"Data de nascimento: <b>{data_nasc_formatada}</b>",
        campo_style
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    # CPF (preenchido se disponível) - CPF já está formatado no banco
    cpf = aluno.get('cpf') if aluno.get('cpf') else "_" * 40
    elements.append(Paragraph(
        f"CPF (se houver): <b>{cpf}</b>",
        campo_style
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    # Unidade Escolar (preenchida)
    elements.append(Paragraph(
        f"Unidade Escolar: <b>{nome_escola}</b>",
        campo_style
    ))
    elements.append(Spacer(1, 0.1*inch))
    
    # Checkbox Etapa/Função - conforme tipo de participante
    if tipo_participante == 'estudante':
        checkbox_text = "Etapa/Função: [<b>X</b>] Estudante   [  ] Professor(a)   [  ] Servidor(a)"
    elif tipo_participante == 'professor':
        checkbox_text = "Etapa/Função: [  ] Estudante   [<b>X</b>] Professor(a)   [  ] Servidor(a)"
    else:  # servidor
        checkbox_text = "Etapa/Função: [  ] Estudante   [  ] Professor(a)   [<b>X</b>] Servidor(a)"
    
    elements.append(Paragraph(
        checkbox_text,
        campo_style
    ))
    elements.append(Spacer(1, 0.25*inch))
    
    # Declaração
    texto_declaracao = """Declaro, para os devidos fins, que manifesto interesse em participar da ação do 
Programa "Cuidar dos Olhos", destinada à realização de triagem oftalmológica, consultas 
especializadas e, quando indicado, recebimento de óculos."""
    
    elements.append(Paragraph(texto_declaracao, texto_style))
    
    # Autorização
    texto_autorizacao = """Autorizo a participação na referida ação, bem como o uso das informações acima 
exclusivamente para fins de organização e execução do programa, nos termos da legislação 
vigente."""
    
    elements.append(Paragraph(texto_autorizacao, texto_style))
    
    # Ciência
    texto_ciencia = """Estou ciente de que a participação dependerá do cronograma e da organização definidos 
pelos organizadores da ação."""
    
    elements.append(Paragraph(texto_ciencia, texto_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Local e data (preenchida com data atual) - alinhada à direita
    data_atual = datetime.datetime.now()
    mes_portugues = MESES_PT[data_atual.month]
    data_formatada = f"{data_atual.day:02d} de {mes_portugues} de {data_atual.year}"
    
    # Criar parágrafo com alinhamento à direita
    data_direita_style = ParagraphStyle(
        'DataAlinhada',
        parent=data_style,
        alignment=TA_LEFT,
        fontSize=11
    )
    elements.append(Paragraph(
        f'<para align="right">Paço do Lumiar - MA, <b>{data_formatada}</b></para>',
        campo_style
    ))
    elements.append(Spacer(1, 0.5*inch))
    
    # Assinatura
    elements.append(Paragraph(
        "Assinatura do responsável ou do(a) interessado(a):",
        campo_style
    ))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(
        "_" * 76,
        campo_style
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Telefone (deixar em branco para preenchimento manual)
    elements.append(Paragraph(
        "Telefone para contato: (____) _____________________________",
        campo_style
    ))
    
    # Gerar PDF com rodapé fixo em cada página
    try:
        doc.build(elements, onFirstPage=adicionar_rodape_pagina, onLaterPages=adicionar_rodape_pagina)
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.exception(f"Erro ao gerar termo individual: {e}")
        return None


def gerar_termo_cuidar_olhos():
    """
    Gera termos preenchidos para todos os alunos ativos e seus responsáveis.
    Cria arquivos PDF separados por turma na pasta 'Programa Cuidar dos Olhos'.
    """
    try:
        logger.info("Iniciando geração dos Termos de Autorização - Programa Cuidar dos Olhos")
        
        # Obter dados da escola
        nome_escola = obter_dados_escola(60)
        
        # Obter alunos ativos
        alunos = obter_alunos_ativos()
        if not alunos:
            logger.warning("Nenhum aluno ativo encontrado")
            return False
        
        logger.info(f"Encontrados {len(alunos)} alunos ativos")
        
        # Criar pasta de saída
        pasta_saida = PROJECT_ROOT / 'Programa Cuidar dos Olhos'
        pasta_saida.mkdir(parents=True, exist_ok=True)
        logger.info(f"Pasta criada/verificada: {pasta_saida}")
        
        # Agrupar alunos por turma
        from collections import defaultdict
        turmas = defaultdict(list)
        
        for aluno in alunos:
            chave_turma = (aluno['nome_serie'], aluno['nome_turma'], aluno['turno'])
            turmas[chave_turma].append(aluno)
        
        logger.info(f"Alunos agrupados em {len(turmas)} turmas")
        
        # Gerar PDF para cada turma
        total_termos = 0
        total_turmas = 0
        arquivos_gerados = []
        
        for (serie, turma, turno), alunos_turma in sorted(turmas.items()):
            writer = PdfWriter()
            termos_turma = 0
            
            logger.info(f"Processando {serie} - Turma {turma} ({turno}) - {len(alunos_turma)} alunos")
            
            for aluno in alunos_turma:
                # Obter todos os responsáveis do aluno
                responsaveis = obter_responsaveis_do_aluno(aluno['id'])
                
                if not responsaveis:
                    logger.warning(f"  Aluno {aluno['nome_aluno']} sem responsável - pulando")
                    continue
                
                # Gerar um termo para cada responsável
                for responsavel in responsaveis:
                    # Gerar termo individual
                    buffer_termo = gerar_termo_individual(aluno, responsavel, nome_escola)
                    
                    if buffer_termo:
                        # Adicionar ao PDF da turma
                        from PyPDF2 import PdfReader
                        reader = PdfReader(buffer_termo)
                        for page in reader.pages:
                            writer.add_page(page)
                        termos_turma += 1
                        logger.debug(f"  ✓ {aluno['nome_aluno']} - {responsavel['nome']}")
            
            # Salvar PDF da turma se houver termos
            if termos_turma > 0:
                # Sanitizar nome do arquivo
                nome_arquivo_limpo = f"{serie}_{turma}_{turno}".replace("/", "-").replace("\\", "-").replace(" ", "_")
                nome_arquivo = pasta_saida / f"Termos_{nome_arquivo_limpo}.pdf"
                
                with open(nome_arquivo, "wb") as output_pdf:
                    writer.write(output_pdf)
                
                arquivos_gerados.append(nome_arquivo)
                total_termos += termos_turma
                total_turmas += 1
                logger.info(f"  ✅ {termos_turma} termos salvos em: {nome_arquivo.name}")
            else:
                logger.warning(f"  ⚠ Nenhum termo gerado para {serie} - Turma {turma}")
        
        if total_turmas == 0:
            logger.warning("Nenhum termo foi gerado")
            return False
        
        # Mensagem de sucesso
        logger.info("=" * 70)
        logger.info(f"✅ CONCLUÍDO!")
        logger.info(f"   {total_termos} termos gerados em {total_turmas} arquivos")
        logger.info(f"   Pasta: {pasta_saida}")
        logger.info("=" * 70)
        
        # Abrir a pasta no explorador
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(str(pasta_saida))
            elif platform.system() == "Darwin":
                os.system(f"open '{pasta_saida}'")
            else:
                os.system(f"xdg-open '{pasta_saida}'")
        except Exception as e:
            logger.warning(f"Não foi possível abrir a pasta automaticamente: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao gerar termos: {e}")
        return False


def gerar_termo_turma_especifica(turma_id, nome_turma_display=None):
    """
    Gera termos para uma turma específica.
    
    Args:
        turma_id: ID da turma
        nome_turma_display: Nome da turma para exibição (opcional)
        
    Returns:
        bool: True se gerado com sucesso, False caso contrário
    """
    try:
        logger.info(f"Iniciando geração dos Termos - Turma específica (ID: {turma_id})")
        
        # Obter dados da escola
        nome_escola = obter_dados_escola(60)
        
        # Obter alunos da turma específica
        alunos = obter_alunos_ativos(turma_id=turma_id)
        
        if not alunos:
            logger.warning(f"Nenhum aluno ativo encontrado para a turma ID {turma_id}")
            return False
        
        # Pegar informações da turma do primeiro aluno
        serie = alunos[0]['nome_serie']
        turma = alunos[0]['nome_turma']
        turno = alunos[0]['turno']
        
        logger.info(f"Processando {serie} - Turma {turma} ({turno}) - {len(alunos)} alunos")
        
        # Criar pasta de saída
        pasta_saida = PROJECT_ROOT / 'Programa Cuidar dos Olhos'
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        # Criar PDF
        writer = PdfWriter()
        termos_gerados = 0
        
        for aluno in alunos:
            # Obter todos os responsáveis do aluno
            responsaveis = obter_responsaveis_do_aluno(aluno['id'])
            
            if not responsaveis:
                logger.warning(f"  Aluno {aluno['nome_aluno']} sem responsável - pulando")
                continue
            
            # Gerar um termo para cada responsável
            for responsavel in responsaveis:
                # Gerar termo individual
                buffer_termo = gerar_termo_individual(aluno, responsavel, nome_escola)
                
                if buffer_termo:
                    # Adicionar ao PDF
                    from PyPDF2 import PdfReader
                    reader = PdfReader(buffer_termo)
                    for page in reader.pages:
                        writer.add_page(page)
                    termos_gerados += 1
                    logger.debug(f"  ✓ {aluno['nome_aluno']} - {responsavel['nome']}")
        
        if termos_gerados == 0:
            logger.warning(f"Nenhum termo foi gerado para a turma")
            return False
        
        # Sanitizar nome do arquivo
        nome_arquivo_limpo = f"{serie}_{turma}_{turno}".replace("/", "-").replace("\\", "-").replace(" ", "_")
        nome_arquivo = pasta_saida / f"Termos_{nome_arquivo_limpo}.pdf"
        
        # Salvar PDF
        with open(nome_arquivo, "wb") as output_pdf:
            writer.write(output_pdf)
        
        logger.info(f"✅ {termos_gerados} termos gerados: {nome_arquivo.name}")
        
        # Abrir o PDF
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(str(nome_arquivo))
            elif platform.system() == "Darwin":
                os.system(f"open '{nome_arquivo}'")
            else:
                os.system(f"xdg-open '{nome_arquivo}'")
        except Exception as e:
            logger.warning(f"Não foi possível abrir o PDF automaticamente: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao gerar termos da turma: {e}")
        return False


def gerar_termo_professores():
    """
    Gera termos para todos os professores da escola.
    """
    try:
        logger.info("Iniciando geração dos Termos - Professores")
        
        # Obter dados da escola
        nome_escola = obter_dados_escola(60)
        
        # Obter professores
        professores = obter_professores_ativos(60)
        
        if not professores:
            logger.warning("Nenhum professor encontrado")
            return False
        
        logger.info(f"Encontrados {len(professores)} professores")
        
        # Criar pasta de saída
        pasta_saida = PROJECT_ROOT / 'Programa Cuidar dos Olhos'
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        # Criar PDF
        writer = PdfWriter()
        termos_gerados = 0
        
        for professor in professores:
            # Para professores, o nome aparece duas vezes (como responsável e como interessado)
            # Adaptar estrutura para compatibilidade com gerar_termo_individual
            pessoa_data = {
                'nome': professor['nome'],
                'nome_aluno': professor['nome'],  # Mesmo nome aparece aqui
                'data_nascimento': professor.get('data_nascimento'),
                'cpf': professor.get('cpf')
            }
            
            # Gerar termo individual (sem responsável, pois é o próprio interessado)
            buffer_termo = gerar_termo_individual(pessoa_data, None, nome_escola, tipo_participante='professor')
            
            if buffer_termo:
                from PyPDF2 import PdfReader
                reader = PdfReader(buffer_termo)
                for page in reader.pages:
                    writer.add_page(page)
                termos_gerados += 1
                logger.debug(f"  ✓ {professor['nome']}")
        
        if termos_gerados == 0:
            logger.warning("Nenhum termo foi gerado para professores")
            return False
        
        # Salvar PDF
        nome_arquivo = pasta_saida / "Termos_Professores.pdf"
        with open(nome_arquivo, "wb") as output_pdf:
            writer.write(output_pdf)
        
        logger.info(f"✅ {termos_gerados} termos gerados: {nome_arquivo.name}")
        
        # Abrir o PDF
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(str(nome_arquivo))
            elif platform.system() == "Darwin":
                os.system(f"open '{nome_arquivo}'")
            else:
                os.system(f"xdg-open '{nome_arquivo}'")
        except Exception as e:
            logger.warning(f"Não foi possível abrir o PDF automaticamente: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao gerar termos de professores: {e}")
        return False


def gerar_termo_servidores():
    """
    Gera termos para todos os servidores da escola (exceto professores).
    """
    try:
        logger.info("Iniciando geração dos Termos - Servidores")
        
        # Obter dados da escola
        nome_escola = obter_dados_escola(60)
        
        # Obter servidores
        servidores = obter_servidores_ativos(60)
        
        if not servidores:
            logger.warning("Nenhum servidor encontrado")
            return False
        
        logger.info(f"Encontrados {len(servidores)} servidores")
        
        # Criar pasta de saída
        pasta_saida = PROJECT_ROOT / 'Programa Cuidar dos Olhos'
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        # Criar PDF
        writer = PdfWriter()
        termos_gerados = 0
        
        for servidor in servidores:
            # Para servidores, o nome aparece duas vezes (como responsável e como interessado)
            # Adaptar estrutura para compatibilidade com gerar_termo_individual
            pessoa_data = {
                'nome': servidor['nome'],
                'nome_aluno': servidor['nome'],  # Mesmo nome aparece aqui
                'data_nascimento': servidor.get('data_nascimento'),
                'cpf': servidor.get('cpf')
            }
            
            # Gerar termo individual (sem responsável, pois é o próprio interessado)
            buffer_termo = gerar_termo_individual(pessoa_data, None, nome_escola, tipo_participante='servidor')
            
            if buffer_termo:
                from PyPDF2 import PdfReader
                reader = PdfReader(buffer_termo)
                for page in reader.pages:
                    writer.add_page(page)
                termos_gerados += 1
                logger.debug(f"  ✓ {servidor['nome']}")
        
        if termos_gerados == 0:
            logger.warning("Nenhum termo foi gerado para servidores")
            return False
        
        # Salvar PDF
        nome_arquivo = pasta_saida / "Termos_Servidores.pdf"
        with open(nome_arquivo, "wb") as output_pdf:
            writer.write(output_pdf)
        
        logger.info(f"✅ {termos_gerados} termos gerados: {nome_arquivo.name}")
        
        # Abrir o PDF
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(str(nome_arquivo))
            elif platform.system() == "Darwin":
                os.system(f"open '{nome_arquivo}'")
            else:
                os.system(f"xdg-open '{nome_arquivo}'")
        except Exception as e:
            logger.warning(f"Não foi possível abrir o PDF automaticamente: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao gerar termos de servidores: {e}")
        return False


def gerar_planilha_estudantes(alunos_responsaveis):
    """
    Gera planilha PDF com os estudantes que assinaram os termos.
    
    Args:
        alunos_responsaveis: Lista de tuplas (aluno, responsavel)
        
    Returns:
        bool: True se gerado com sucesso, False caso contrário
    """
    try:
        logger.info(f"Iniciando geração da Planilha de Estudantes - {len(alunos_responsaveis)} registros")
        
        # Obter dados da escola
        nome_escola = obter_dados_escola(60)
        
        # Criar pasta de saída
        pasta_saida = PROJECT_ROOT / 'Programa Cuidar dos Olhos'
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        # Criar documento PDF
        nome_arquivo = pasta_saida / "Planilha_Levantamento_Estudantes.pdf"
        
        doc = SimpleDocTemplate(
            str(nome_arquivo),
            pagesize=landscape(A4),
            leftMargin=1.5*cm,
            rightMargin=1.5*cm,
            topMargin=1.0*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=0.2*inch
        )
        
        elements.append(Paragraph(
            "<b>PLANILHA DE LEVANTAMENTO DE INTERESSADOS - ESTUDANTES<br/>PROGRAMA 'CUIDAR DOS OLHOS'</b>",
            titulo_style
        ))
        
        # Nome da escola
        escola_style = ParagraphStyle(
            'Escola',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=0.3*inch
        )
        
        elements.append(Paragraph(f"<b>Escola Municipal:</b> {nome_escola}", escola_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Preparar dados da tabela
        data_tabela = [
            ['Nº', 'Nome Completo', 'CPF', 'Data de\nNascimento', 'Responsável Legal\n(se menor)', 'Telefone']
        ]
        
        for i, (aluno, responsavel) in enumerate(alunos_responsaveis, 1):
            # Nome do aluno
            nome_aluno = aluno.get('nome_aluno', '')
            
            # CPF do aluno
            cpf_aluno = aluno.get('cpf', '-') if aluno.get('cpf') else '-'
            
            # Data de nascimento
            data_nasc = aluno.get('data_nascimento')
            if data_nasc:
                data_nasc_formatada = data_nasc.strftime('%d/%m/%Y') if hasattr(data_nasc, 'strftime') else str(data_nasc)
            else:
                data_nasc_formatada = '-'
            
            # Nome do responsável
            nome_responsavel = responsavel.get('nome', '-')
            
            # Telefone
            telefone = responsavel.get('telefone', '-') if responsavel.get('telefone') else '-'
            
            data_tabela.append([
                str(i),
                nome_aluno,
                cpf_aluno,
                data_nasc_formatada,
                nome_responsavel,
                telefone
            ])
        
        # Criar tabela (A4 paisagem tem ~26.7cm de largura útil)
        tabela = Table(data_tabela, colWidths=[1*cm, 7*cm, 3*cm, 2.5*cm, 7*cm, 3.5*cm])
        
        # Estilo da tabela
        tabela.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), '#4472C4'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Corpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Coluna Nº centralizada
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),   # Outras colunas à esquerda
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            
            # Linhas
            ('GRID', (0, 0), (-1, -1), 0.5, 'black'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), ['white', '#E7E6E6']),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(tabela)
        elements.append(Spacer(1, 0.3*inch))
        
        # Observação
        obs_style = ParagraphStyle(
            'Obs',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_JUSTIFY,
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph(
            "<b>Observação:</b> A planilha deverá ser encaminhada à SEMED juntamente com os Termos de Autorização devidamente assinados, conforme orientações do Ofício Circular.",
            obs_style
        ))
        
        # Gerar PDF
        doc.build(elements)
        
        logger.info(f"✅ Planilha gerada com sucesso: {nome_arquivo.name}")
        
        # Abrir o PDF
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(str(nome_arquivo))
            elif platform.system() == "Darwin":
                os.system(f"open '{nome_arquivo}'")
            else:
                os.system(f"xdg-open '{nome_arquivo}'")
        except Exception as e:
            logger.warning(f"Não foi possível abrir o PDF automaticamente: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao gerar planilha de estudantes: {e}")
        return False


def gerar_planilha_profissionais(profissionais):
    """
    Gera planilha PDF com os professores e servidores que assinaram os termos.
    
    Args:
        profissionais: Lista de tuplas (funcionario, tipo)
        
    Returns:
        bool: True se gerado com sucesso, False caso contrário
    """
    try:
        logger.info(f"Iniciando geração da Planilha de Profissionais - {len(profissionais)} registros")
        
        # Obter dados da escola
        nome_escola = obter_dados_escola(60)
        
        # Criar pasta de saída
        pasta_saida = PROJECT_ROOT / 'Programa Cuidar dos Olhos'
        pasta_saida.mkdir(parents=True, exist_ok=True)
        
        # Criar documento PDF
        nome_arquivo = pasta_saida / "Planilha_Levantamento_Professores_Servidores.pdf"
        
        doc = SimpleDocTemplate(
            str(nome_arquivo),
            pagesize=landscape(A4),
            leftMargin=1.5*cm,
            rightMargin=1.5*cm,
            topMargin=1.0*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        titulo_style = ParagraphStyle(
            'Titulo',
            parent=styles['Heading1'],
            fontSize=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=0.2*inch
        )
        
        elements.append(Paragraph(
            "<b>PLANILHA DE LEVANTAMENTO DE INTERESSADOS - PROFESSORES E SERVIDORES<br/>PROGRAMA 'CUIDAR DOS OLHOS'</b>",
            titulo_style
        ))
        
        # Nome da escola
        escola_style = ParagraphStyle(
            'Escola',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=0.3*inch
        )
        
        elements.append(Paragraph(f"<b>Escola Municipal:</b> {nome_escola}", escola_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Preparar dados da tabela
        data_tabela = [
            ['Nº', 'Nome Completo', 'CPF', 'Data de\nNascimento', 'Cargo/Função\n(Professor/Servidor)', 'Matrícula\nFuncional', 'Telefone']
        ]
        
        for i, (funcionario, tipo) in enumerate(profissionais, 1):
            # Nome
            nome = funcionario.get('nome', '')
            
            # CPF
            cpf = funcionario.get('cpf', '-') if funcionario.get('cpf') else '-'
            
            # Data de nascimento
            data_nasc = funcionario.get('data_nascimento')
            if data_nasc:
                data_nasc_formatada = data_nasc.strftime('%d/%m/%Y') if hasattr(data_nasc, 'strftime') else str(data_nasc)
            else:
                data_nasc_formatada = '-'
            
            # Cargo/Função - definir se é Professor ou Servidor
            cargo_db = funcionario.get('cargo', '')
            cargo = 'Professor' if cargo_db == 'Professor@' else 'Servidor'
            
            # Matrícula funcional
            matricula = funcionario.get('matricula', '-') if funcionario.get('matricula') else '-'
            
            # Telefone - priorizar whatsapp sobre telefone normal
            whatsapp = funcionario.get('whatsapp', '')
            telefone_normal = funcionario.get('telefone', '')
            telefone = whatsapp if whatsapp else (telefone_normal if telefone_normal else '-')
            
            data_tabela.append([
                str(i),
                nome,
                cpf,
                data_nasc_formatada,
                cargo,
                matricula,
                telefone
            ])
        
        # Criar tabela (A4 paisagem tem ~26.7cm de largura útil)
        tabela = Table(data_tabela, colWidths=[1*cm, 6.5*cm, 3*cm, 2.5*cm, 3.5*cm, 2.5*cm, 3.5*cm])
        
        # Estilo da tabela
        tabela.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), '#4472C4'),
            ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Corpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Coluna Nº centralizada
            ('ALIGN', (1, 1), (-1, -1), 'LEFT'),   # Outras colunas à esquerda
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            
            # Linhas
            ('GRID', (0, 0), (-1, -1), 0.5, 'black'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), ['white', '#E7E6E6']),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(tabela)
        elements.append(Spacer(1, 0.3*inch))
        
        # Observação
        obs_style = ParagraphStyle(
            'Obs',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_JUSTIFY,
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph(
            "<b>Observação:</b> A planilha deverá ser encaminhada à SEMED juntamente com os Termos de Autorização devidamente assinados, conforme orientações do Ofício Circular.",
            obs_style
        ))
        
        # Gerar PDF
        doc.build(elements)
        
        logger.info(f"✅ Planilha gerada com sucesso: {nome_arquivo.name}")
        
        # Abrir o PDF
        try:
            import platform
            if platform.system() == "Windows":
                os.startfile(str(nome_arquivo))
            elif platform.system() == "Darwin":
                os.system(f"open '{nome_arquivo}'")
            else:
                os.system(f"xdg-open '{nome_arquivo}'")
        except Exception as e:
            logger.warning(f"Não foi possível abrir o PDF automaticamente: {e}")
        
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao gerar planilha de profissionais: {e}")
        return False


if __name__ == "__main__":
    gerar_termo_cuidar_olhos()
