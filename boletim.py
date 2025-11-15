import io
import os
from datetime import datetime
from utilitarios.gerenciador_documentos import salvar_documento_sistema
from utilitarios.tipos_documentos import TIPO_BOLETIM
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from gerarPDF import salvar_e_abrir_pdf
from conexao import conectar_bd
from db.connection import get_connection
from biblio_editor import arredondar_personalizado, quebra_linha
from config_logs import get_logger
from typing import Any, cast

logger = get_logger(__name__)


def _to_int_param(val):
    try:
        return int(val)
    except Exception:
        try:
            return int(float(val))
        except Exception:
            return val


def _to_str_param(val):
    return "" if val is None else str(val)


def _tuple_of_str(seq):
    return tuple(str(x) for x in seq)


def _safe_float(val, default=0.0):
    try:
        return float(val)
    except Exception:
        try:
            return float(str(val))
        except Exception:
            return default


def _safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        try:
            return int(float(val))
        except Exception:
            try:
                return int(str(val))
            except Exception:
                return default

def obter_disciplinas_por_serie(serie_id):
    """Obter as disciplinas adequadas para a série especificada."""
    try:
        with get_connection() as conn:
            if conn is None:
                return {}
            cursor = cast(Any, conn).cursor()
            try:
                # Primeiro determinar o nível de ensino da série
                cursor.execute("""
                    SELECT nivel_id FROM serie WHERE id = %s
                """, (_safe_int(serie_id, 0),))

                nivel_result = cursor.fetchone()
                if not nivel_result:
                    return {}

                nivel_id = _to_int_param(nivel_result[0])

                # Obter as disciplinas para este nível de ensino
                cursor.execute("""
                    SELECT id, nome FROM disciplinas 
                    WHERE nivel_id = %s
                    ORDER BY nome
                """, (_safe_int(nivel_id, 0),))

                disciplinas = cursor.fetchall()

                # Mapear as disciplinas para um dicionário nome -> id
                disciplina_id_map = {disc[1]: disc[0] for disc in disciplinas}

                return disciplina_id_map
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
    except Exception:
        # Em caso de erro de conexão ou execução, retornar vazio
        logger.exception("Erro ao obter disciplinas por serie")
        return {}

def consultar_dados_aluno(aluno_id, ano_letivo_id):
    query_aluno = """
        SELECT
            escolas.nome AS nome_escola,
            alunos.nome AS nome_aluno,
            serie.nome AS serie,
            turmas.nome AS turma,
            turmas.turno AS turno,
            anosletivos.ano_letivo,
            disciplinas.nome AS disciplina,
            notas.nota AS nota,
            notas.bimestre AS bimestre,
            faltas.faltas AS faltas_bimestrais,
            anosletivos.numero_dias_aula,
            serie.id AS serie_id
        FROM
            matriculas
        JOIN
            alunos ON matriculas.aluno_id = alunos.id
        JOIN
            turmas ON matriculas.turma_id = turmas.id
        JOIN
            serie ON turmas.serie_id = serie.id
        JOIN
            anosletivos ON matriculas.ano_letivo_id = anosletivos.id
        JOIN
            escolas ON turmas.escola_id = escolas.id
        LEFT JOIN notas ON notas.aluno_id = alunos.id AND notas.ano_letivo_id = anosletivos.id
        LEFT JOIN disciplinas ON notas.disciplina_id = disciplinas.id
        LEFT JOIN faltas_bimestrais AS faltas ON faltas.aluno_id = alunos.id 
            AND faltas.bimestre = notas.bimestre
            AND faltas.ano_letivo_id = anosletivos.id
        WHERE alunos.id = %s AND notas.ano_letivo_id = %s
        ORDER BY disciplinas.nome, notas.bimestre;
    """
    try:
        with get_connection() as conn:
            if conn is None:
                return []
            cursor = cast(Any, conn).cursor()
            try:
                params = (_to_int_param(aluno_id), _to_int_param(ano_letivo_id))
                cursor.execute(query_aluno, params)
                dados_aluno = cursor.fetchall()
                return dados_aluno
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
    except Exception:
        logger.exception("Erro ao consultar dados do aluno")
        return []


def boletiminiciais(aluno_id, ano_letivo_id):
    from utilitarios.gerenciador_documentos import salvar_documento_sistema
    from utilitarios.tipos_documentos import TIPO_BOLETIM
    
    # Consultar os dados do aluno
    dados_aluno = consultar_dados_aluno(aluno_id, ano_letivo_id)

    if not dados_aluno:
        logger.info("Aluno não encontrado ou sem notas registradas.")
        return
    
    # Extrair as informações do cabeçalho da primeira linha
    primeira_linha = dados_aluno[0]
    nome_escola = str(primeira_linha[0] or "")
    nome_aluno = str(primeira_linha[1] or "")
    serie = str(primeira_linha[2] or "")
    turma = str(primeira_linha[3] or "")
    turno = str(primeira_linha[4] or "")
    ano_letivo = primeira_linha[5]
    serie_id = primeira_linha[11]  # Acessa o campo serie_id da consulta
    
    # Obter apenas as disciplinas que o aluno realmente cursou
    disciplinas_cursadas = set()
    for linha in dados_aluno:
        if linha[6]:  # se o nome da disciplina não for None
            disciplinas_cursadas.add(linha[6])
    
    # Ordenar as disciplinas alfabeticamente
    ordem_disciplinas = sorted(list(disciplinas_cursadas))
    
    if not ordem_disciplinas:
        logger.info("Não foi possível encontrar disciplinas cursadas pelo aluno")
        return

    # Criar o PDF em memória
    buffer = io.BytesIO()
    # Definindo as margens em pontos (1,27 cm = 36 pontos)
    margem = 10

    # Criar o documento com margens
    doc = SimpleDocTemplate(buffer,
                            pagesize=landscape(A4),
                            topMargin=margem,
                            bottomMargin=margem,
                            leftMargin=margem,
                            rightMargin=margem)

    # Informações do cabeçalho
    cabecalho = [
        "<b>PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR</b>",
        "<b>SECRETARIA MUNICIPAL DE EDUCAÇÃO</b>"
    ]
    cabecalho2 = [
        "<b>BOLETIM ESCOLAR</b>",
        "<b>ANOS INICIAIS</b>",
        "<b>1º AO 5º ANO</b>"
    ]
    responsavel =[
        "1º BIMESTRE:______________________________",
        "2º BIMESTRE:______________________________",
        "3º BIMESTRE:______________________________",
        "4º BIMESTRE:______________________________"
    ]


    # Adicionando a imagem
    figura_superior = os.path.join(os.path.dirname(__file__), 'pacologo.png')  # Ajuste o nome do arquivo conforme necessário
    # Definir estilos
    estilo_centro = ParagraphStyle(name='centro', fontSize=12, alignment=1, leading=18)
    estilo_formatado = ParagraphStyle(name='centro', fontSize=12, alignment=4, leading=18)

    # Estilo para células de tabela e helper para garantir Paragraphs
    estilo_valor = ParagraphStyle(name='valor', fontSize=10, alignment=1)
    def _cell(val, style=estilo_valor):
        if isinstance(val, Paragraph):
            return val
        return Paragraph(str(val), style)

    paragrafo1 = Paragraph("O aluno(a) deve ser avaliado quanto às capacidades cognitivas e suas competências socioemocionais;", estilo_formatado)
    paragrafo2 = Paragraph("O rendimento do aluno(a) será expresso em conceitos, já definidos no diário escolar;", estilo_formatado)
    paragrafo3 = Paragraph("A frequência mínima para promoção é de 75% da carga horária anual.", estilo_formatado)

    data_costa = [[paragrafo1], [paragrafo2], [paragrafo3]]

    # Criando a tabela e definindo o estilo da nova tabela
    table_costa = Table(data_costa, colWidths=[3.5 * inch])
    table_costa.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
    ]))

    # Criar parágrafos com linhas para assinatura em cima e os nomes embaixo
    paragrafo_escola = Paragraph(f"<i><b>{nome_escola.upper()}</b></i><br/>________________________________________________<br/>UNIDADE DE ENSINO", estilo_centro)
    paragrafo_aluno = Paragraph(f"<i><b>{nome_aluno.upper()}</b></i><br/>________________________________________________<br/>ALUNO(A)", estilo_centro)
    paragrafo_gestor = Paragraph("________________________________________________<br/>GESTOR(A)", estilo_centro)
    paragrafo_ano = Paragraph(f"<b>{serie.upper()}</b><br/>__________<br/>ANO", estilo_centro)
    paragrafo_turma = Paragraph(f"<b>{turma.upper()}</b><br/>__________<br/>TURMA", estilo_centro)
    paragrafo_turno = Paragraph(f"<b>{turno.upper()}</b><br/>__________<br/>TURNO", estilo_centro)
    paragrafo_anoletivo = Paragraph(f"<b>{ano_letivo}</b><br/>__________<br/>ANO LETIVO", estilo_centro)

    data_turma =[
        [paragrafo_ano,paragrafo_turma,paragrafo_turno,paragrafo_anoletivo]
    ]
    # Criando a tabela e definindo o estilo da tabela de preenchimento
    table_turma = Table(data_turma, colWidths=[1.17 * inch] * 4)  # Definindo largura das colunas
    table_turma.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    data = [
        [table_costa, Image(figura_superior, width=1 * inch, height=1 * inch)],
        ['', Paragraph('<br/>'.join(cabecalho), estilo_centro)],
        ['', ''],
        ['', paragrafo_escola],
        ['', paragrafo_aluno],
        ['',table_turma],
        ['',paragrafo_gestor],
    ]

    # Criando a tabela e definindo o estilo da tabela principal
    table = Table(data, colWidths=[5.2 * inch, 5.2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Adicionando a tabela aos elementos do PDF
    elements = []
    elements.append(table)

    # Criando uma nova tabela para o conteúdo abaixo do cabeçalho
    data_conteudo = [
        [Paragraph('<br/>'.join(cabecalho2), estilo_centro)]
    ]

    # Criando a tabela e definindo o estilo da nova tabela
    table_conteudo = Table(data_conteudo, colWidths=[3 * inch])
    table_conteudo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
    ]))

    # Atualizando a tabela principal para incluir a nova tabela na segunda coluna
    data[2][1] = table_conteudo
    altura = 65
    row_heights = [None, altura, None, altura, altura, altura, altura]
    # Atualizando a tabela principal com os novos dados
    table = Table(data, colWidths=[5.3 * inch, 5.3 * inch], rowHeights=row_heights)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alinhamento horizontal centralizado
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical centralizado
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        # ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
        ('SPAN', (0, 0), (0, 6)),
    ]))

    # Adicionando a tabela atualizada aos elementos do PDF
    elements = []
    elements.append(table)
    # Iniciar a segunda página com a tabela
    elements.append(PageBreak())
    elements.append(Paragraph("<b>RENDIMENTO ANUAL DO ALUNO</b>",ParagraphStyle(name='centro', fontSize=14, alignment=1, leading=18)))
    elements.append(Spacer(1, 0.125 * inch))
    # Inicialização da tabela de notas
    data_nota = [
        [quebra_linha("COMPONENTES CURRICULARES"), quebra_linha("1º BIMESTRE"), quebra_linha("2º BIMESTRE"),
        quebra_linha("3º BIMESTRE"), quebra_linha("4º BIMESTRE"), quebra_linha("MÉDIA ANUAL"),
        quebra_linha("RECUPERAÇÃO FINAL"), quebra_linha("MÉDIA FINAL")],
    ]

    # Inicialização do dicionário para armazenar notas e faltas por disciplina
    notas_disciplinas = {disciplina: ["--", "--", "--", "--"] for disciplina in ordem_disciplinas}
    faltas_bimestrais = {disciplina: [0, 0, 0, 0] for disciplina in ordem_disciplinas}

    # Iterar sobre os dados do aluno
    for linha in dados_aluno:
        disciplina = linha[6]  # 'disciplina' é a 7ª coluna (índice 6)
        bimestre = linha[8]    # 'bimestre' é a 9ª coluna (índice 8)
        nota = _safe_float(linha[7], 0.0)
        faltas = _safe_int(linha[9], 0)

        # Verificar se a disciplina está na lista
        if disciplina not in ordem_disciplinas:
            continue

        # Dividir a nota por 10 para formatação
        nota_formatada = nota / 10

        # Preencher a nota correspondente ao bimestre
        if bimestre == '1º bimestre':
            notas_disciplinas[disciplina][0] = f"{nota_formatada:.1f}"
            faltas_bimestrais[disciplina][0] += faltas
        elif bimestre == '2º bimestre':
            notas_disciplinas[disciplina][1] = f"{nota_formatada:.1f}"
            faltas_bimestrais[disciplina][1] += faltas
        elif bimestre == '3º bimestre':
            notas_disciplinas[disciplina][2] = f"{nota_formatada:.1f}"
            faltas_bimestrais[disciplina][2] += faltas
        elif bimestre == '4º bimestre':
            notas_disciplinas[disciplina][3] = f"{nota_formatada:.1f}"
            faltas_bimestrais[disciplina][3] += faltas

    # Conectar ao banco de dados para buscar recuperação
    conn = conectar_bd()
    if conn is None:
        recuperacoes = {}
        disciplina_ids = {}
    else:
        cursor = cast(Any, conn).cursor()
        try:
            # Dicionário para armazenar as recuperações e IDs das disciplinas
            recuperacoes = {}
            disciplina_ids = {}

            # Buscar IDs de todas as disciplinas necessárias de uma vez
            placeholders = ', '.join(['%s'] * len(ordem_disciplinas))
            cursor.execute(f"""
                SELECT id, nome FROM disciplinas 
                WHERE nome IN ({placeholders})
            """, _tuple_of_str(ordem_disciplinas))

            for disc_id, disc_nome in cursor.fetchall():
                disciplina_ids[disc_nome] = disc_id

            # Buscar todas as recuperações de uma vez para este aluno
            cursor.execute("""
                SELECT disciplina_id, nota 
                FROM recuperacao 
                WHERE aluno_id = %s AND ano_letivo_id = %s
            """, (_to_int_param(aluno_id), _to_int_param(ano_letivo_id)))

            for disc_id, nota_rec in cursor.fetchall():
                recuperacoes[disc_id] = nota_rec

            # Buscar todas as avaliações finais de uma vez para este aluno
            cursor.execute("""
                SELECT disciplina_id, nota 
                FROM avaliacao_final 
                WHERE aluno_id = %s AND ano_letivo_id = %s
            """, (_to_int_param(aluno_id), _to_int_param(ano_letivo_id)))
            resultados_av = cursor.fetchall()
            avaliacoes = {r[0]: r[1] for r in resultados_av}

            # Preencher a tabela data_nota com as disciplinas e suas respectivas notas
            for disciplina in ordem_disciplinas:
                # Calcular média aritmética das notas
                notas = [_safe_float(nota) for nota in notas_disciplinas[disciplina] if nota != "--"]

                if not notas:
                    continue  # Pular disciplinas sem notas registradas

                # Calcular média anual com as notas disponíveis
                media_anual_sem_arredondamento = sum(notas) / len(notas)
                media_anual_arredondada = arredondar_personalizado(media_anual_sem_arredondamento)

                # Verificar se temos o ID desta disciplina
                disciplina_id = disciplina_ids.get(disciplina)

                if disciplina_id:
                    # Verificar se há recuperação para esta disciplina
                    nota_recuperacao = "--"
                    media_final_arredondada = media_anual_arredondada

                    if disciplina_id in recuperacoes:
                        rec_val = _safe_float(recuperacoes[disciplina_id], 0.0)
                        nota_recuperacao = f"{rec_val/10:.1f}"
                        media_final_sem_arredondamento = (media_anual_sem_arredondamento + rec_val) / 2
                        media_final_arredondada = arredondar_personalizado(media_final_sem_arredondamento)

                    # Só mostrar a média final se tiver 4 notas
                    if len(notas) == 4:
                        data_nota.append([
                            _cell(quebra_linha(disciplina)),
                            _cell(notas_disciplinas[disciplina][0]),
                            _cell(notas_disciplinas[disciplina][1]),
                            _cell(notas_disciplinas[disciplina][2]),
                            _cell(notas_disciplinas[disciplina][3]),
                            _cell(f"{media_anual_arredondada:.1f}"),
                            _cell(nota_recuperacao),
                            _cell(f"{media_final_arredondada:.1f}")
                        ])
                    else:
                        data_nota.append([
                            _cell(quebra_linha(disciplina)),
                            _cell(notas_disciplinas[disciplina][0]),
                            _cell(notas_disciplinas[disciplina][1]),
                            _cell(notas_disciplinas[disciplina][2]),
                            _cell(notas_disciplinas[disciplina][3]),
                            _cell(f"{media_anual_arredondada:.1f}"),
                            _cell(nota_recuperacao),
                            _cell("--")
                        ])
                else:
                    # Só mostrar a média final se tiver 4 notas
                    if len(notas) == 4:
                        data_nota.append([
                            _cell(quebra_linha(disciplina)),
                            _cell(notas_disciplinas[disciplina][0]),
                            _cell(notas_disciplinas[disciplina][1]),
                            _cell(notas_disciplinas[disciplina][2]),
                            _cell(notas_disciplinas[disciplina][3]),
                            _cell(f"{media_anual_arredondada:.1f}"),
                            _cell("--"),
                            _cell(f"{media_anual_arredondada:.1f}")
                        ])
                    else:
                        data_nota.append([
                            _cell(quebra_linha(disciplina)),
                            _cell(notas_disciplinas[disciplina][0]),
                            _cell(notas_disciplinas[disciplina][1]),
                            _cell(notas_disciplinas[disciplina][2]),
                            _cell(notas_disciplinas[disciplina][3]),
                            _cell(f"{media_anual_arredondada:.1f}"),
                            _cell("--"),
                            _cell("--")
                        ])

            # Calcular total de faltas por disciplina
            total_faltas_por_disciplina = {}
            for disciplina in ordem_disciplinas:
                total_faltas_por_disciplina[disciplina] = sum(faltas_bimestrais[disciplina])

            # Calcular total geral de faltas
            total_faltas = sum(sum(faltas) for faltas in faltas_bimestrais.values())

            # Adicionar a linha de Faltas ao final da tabela (garantir Paragraphs nas células)
            faltas_row = [
                _cell("FALTAS"),
            ]
            for i in range(4):
                faltas_row.append(_cell(sum(faltas_bimestrais[disciplina][i] for disciplina in ordem_disciplinas)))
            faltas_row.extend([_cell(""), _cell(""), _cell(f"{total_faltas}")])

            data_nota.append(faltas_row)
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    # Criando a tabela de notas com ReportLab
    tabela_notas = Table(data_nota, colWidths=[1.6 * inch] + [1.2 * inch] * 4 + [1 * inch] + [1.5 * inch]+ [1.2 * inch])
    tabela_notas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (-3, -1), (-1, -1)),
    ]))

    # Adiciona a tabela ao PDF
    elements.append(tabela_notas)

    elements.append(Spacer(1, 0.125 * inch))
    data_assinatura_responsavel =[
        [Paragraph("ASSINATURA DO RESPONSÁVEL:", estilo_centro)],
        [Paragraph('<br/>'.join(responsavel), estilo_formatado)]
    ]
    tabela_assinatura = Table(data_assinatura_responsavel, colWidths=[4.5 * inch])
    tabela_assinatura.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    numero_dias_aula = _safe_int(primeira_linha[10], 0) # Ajuste conforme necessário para acessar o valor correto

    # Inicializar a variável para armazenar o resultado final
    resultado_final = ["( ) AP - Aprovado", "( ) PNAD - Progressão com Necessidade de Apoio Didático", "( ) RP-Reprovado"]

    # Verificar se todas as disciplinas têm 4 notas
    todas_notas_completas = True
    media_final_arredondada = 0
    for disciplina in ordem_disciplinas:
        notas = [_safe_float(nota) for nota in notas_disciplinas[disciplina] if nota != "--"]
        if len(notas) != 4:
            todas_notas_completas = False
            break

    # Só verificar aprovação se todas as notas estiverem completas
    if todas_notas_completas:
        if media_final_arredondada < 6 or total_faltas > (0.25 * numero_dias_aula):
            resultado_final[0] = "( ) AP - Aprovado"
            resultado_final[1] = "( ) PNAD - Progressão com Necessidade de Apoio Didático"
            if total_faltas > (0.25 * numero_dias_aula):
                resultado_final[2] = "(X) RP-Reprovado por faltas"
            else:
                resultado_final[2] = "(X) RP-Reprovado"
        elif media_final_arredondada >= 6 and total_faltas <= (0.25 * numero_dias_aula):
            resultado_final[0] = "(X) AP - Aprovado"
        else:
            resultado_final[0] = "( ) AP - Aprovado"
            resultado_final[1] = "(X) PNAD - Progressão com Necessidade de Apoio Didático"
            resultado_final[2] = "( ) RP-Reprovado"
    else:
        # Se não tiver todas as notas, marcar como pendente
        resultado_final[0] = "( ) AP - Aprovado"
        resultado_final[1] = "( ) PNAD - Progressão com Necessidade de Apoio Didático"
        resultado_final[2] = "( ) RP-Reprovado"

    # Atualizar data_resultadofinal
    data_resultadofinal = [
        [Paragraph("RESULTADO FINAL:", estilo_formatado)],
        [Paragraph(resultado_final[0], estilo_formatado)],
        [Paragraph(resultado_final[1], estilo_formatado)],
        [Paragraph(resultado_final[2], estilo_formatado)]
    ]
    altura1 = 20
    row_heights1 = [None, altura1, None, altura1]
    tabela_resultadofinal = Table(data_resultadofinal, colWidths=[4.5 * inch], rowHeights=row_heights1)
    tabela_resultadofinal.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    data_professor = [
        [Paragraph("PROFESSOR:<br/>_________________________", estilo_formatado)]
    ]
    tabela_professor = Table(data_professor, colWidths=[4.5 * inch])
    tabela_professor.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    data_resultados= [
        [tabela_resultadofinal, tabela_assinatura],
        [tabela_professor, '']
    ]
    
    tabela_resultados = Table(data_resultados,colWidths=[5.125 * inch, 5.125 * inch])

    tabela_resultados.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Alinha a primeira coluna à esquerda
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Alinha a segunda coluna à direita
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(tabela_resultados)
    elements.append(Spacer(1, 0.125 * inch))
    
    # Só mostrar a mensagem se todas as notas estiverem completas
    if todas_notas_completas:
        # Usar o ano letivo seguinte ao valor obtido do banco de dados
        ano_futuro = _safe_int(ano_letivo, 0) + 1
        # Supondo que 'serie' seja uma string que contém o ano, como "1º Ano"
        ano_atual = _safe_int(serie.split()[0].replace('º', ''), 0)  # Remove o símbolo "º"
        
        # Mensagem sobre o próximo ano letivo
        if resultado_final[2].startswith("(X) RP-Reprovado"):
            # Caso o aluno tenha sido reprovado
            mensagem = f"O aluno frequentará o {ano_atual}º Ano do Ensino Fundamental em {ano_futuro}."
        else:
            if serie == "9º Ano":
                mensagem = f"O aluno frequentará o 1º Ano do Ensino Médio em {ano_futuro}."
            else:
                mensagem = f"O aluno frequentará o {ano_atual + 1}º Ano do Ensino Fundamental em {ano_futuro}."

        # Adicionando a mensagem ao PDF
        elements.append(Paragraph(f"<b>{mensagem}</b>", estilo_centro))

    # Construindo o PDF 
    doc.build(elements)

    # Resetar o buffer para o início
    buffer.seek(0)
    
    # Criar nome do arquivo
    data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"Boletim_{nome_aluno.replace(' ', '_')}_{data_atual}.pdf"
    caminho_arquivo = os.path.join('documentos_gerados', nome_arquivo)
    
    # Garantir que o diretório existe
    os.makedirs('documentos_gerados', exist_ok=True)
    
    # Salvar o arquivo localmente
    with open(caminho_arquivo, 'wb') as f:
        f.write(buffer.getvalue())
    
    # Criar descrição detalhada
    descricao = f"Boletim do aluno {nome_aluno}"
    if turma:
        descricao += f" - {serie} {turma}"
    if turno:
        descricao += f" - Turno: {'Matutino' if turno == 'MAT' else 'Vespertino'}"
    
    # Salvar no sistema de gerenciamento de documentos
    sucesso, mensagem, link = salvar_documento_sistema(
        caminho_arquivo=caminho_arquivo,
        tipo_documento=TIPO_BOLETIM,
        aluno_id=aluno_id,
        finalidade=f"Boletim {ano_letivo}",
        descricao=descricao
    )
    
    if not sucesso:
        from tkinter import messagebox
        messagebox.showwarning("Aviso", 
                           "O boletim foi gerado mas houve um erro ao salvá-lo no sistema:\n" + mensagem)
    
    salvar_e_abrir_pdf(buffer)

def boletimfinais(aluno_id, ano_letivo_id):
    conn = conectar_bd()
    if conn is None:
        logger.error("Erro ao conectar ao banco de dados.")
        return
    cursor = cast(Any, conn).cursor()

    # Consulta para obter informações do aluno específico
    query_aluno = """
        SELECT
            escolas.nome AS nome_escola,
            alunos.nome AS nome_aluno,
            serie.nome AS serie,
            turmas.nome AS turma,
            turmas.turno AS turno,
            anosletivos.ano_letivo,
            disciplinas.nome AS disciplina,
            notas.nota AS nota,
            notas.bimestre AS bimestre,
            faltas.faltas AS faltas_bimestrais,
            anosletivos.numero_dias_aula,
            serie.id AS serie_id
        FROM
            matriculas
        JOIN
            alunos ON matriculas.aluno_id = alunos.id
        JOIN
            turmas ON matriculas.turma_id = turmas.id
        JOIN
            serie ON turmas.serie_id = serie.id
        JOIN
            anosletivos ON matriculas.ano_letivo_id = anosletivos.id
        JOIN
            escolas ON turmas.escola_id = escolas.id
        LEFT JOIN notas ON notas.aluno_id = alunos.id AND notas.ano_letivo_id = anosletivos.id
        LEFT JOIN disciplinas ON notas.disciplina_id = disciplinas.id
        LEFT JOIN faltas_bimestrais AS faltas ON faltas.aluno_id = alunos.id 
            AND faltas.bimestre = notas.bimestre
            AND faltas.ano_letivo_id = anosletivos.id
        WHERE alunos.id = %s AND notas.ano_letivo_id = %s
        ORDER BY disciplinas.nome, notas.bimestre;
    """

    params = (_to_int_param(aluno_id), _to_int_param(ano_letivo_id))
    cursor.execute(query_aluno, params)
    dados_aluno = cursor.fetchall()
    cursor.close()
    conn.close()

    if not dados_aluno:
        logger.info("Aluno não encontrado ou sem notas registradas.")
        return

    # Extrair as informações do cabeçalho da primeira linha
    primeira_linha = dados_aluno[0]
    nome_escola = str(primeira_linha[0] or "")
    nome_aluno = str(primeira_linha[1] or "")
    serie = str(primeira_linha[2] or "")
    turma = str(primeira_linha[3] or "")
    turno = str(primeira_linha[4] or "")
    ano_letivo = primeira_linha[5]
    serie_id = primeira_linha[11]  # Nova coluna adicionada na consulta
    
    # Obter apenas as disciplinas que o aluno realmente cursou
    disciplinas_cursadas = set()
    for linha in dados_aluno:
        if linha[6]:  # se o nome da disciplina não for None
            disciplinas_cursadas.add(linha[6])
    
    # Ordenar as disciplinas alfabeticamente
    ordem_disciplinas = sorted(list(disciplinas_cursadas))
    
    # Obter os IDs das disciplinas para posterior consulta de recuperação e avaliação final
    conn = conectar_bd()
    disciplina_id_map = {}
    if conn is None:
        disciplina_id_map = {}
    else:
        cursor = cast(Any, conn).cursor()
        try:
            # Buscar IDs das disciplinas que o aluno cursou
            placeholders = ', '.join(['%s'] * len(ordem_disciplinas))
            cursor.execute(f"""
                SELECT id, nome FROM disciplinas 
                WHERE nome IN ({placeholders})
            """, _tuple_of_str(ordem_disciplinas))

            for disc_id, disc_nome in cursor.fetchall():
                disciplina_id_map[disc_nome] = disc_id
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
    
    if not ordem_disciplinas:
        logger.info("Não foi possível encontrar disciplinas cursadas pelo aluno")
        return

    def quebra_linha(texto):
        # Divide o texto em linhas e aplica a formatação desejada
        linhas = str(texto or "").upper().split('\n')
        return Paragraph('<br/>'.join(linhas), ParagraphStyle(
            'header', 
            fontName='Helvetica-Bold', 
            fontSize=12,
            alignment=1))  # Centralizado
            
    def quebra_linha_menor(texto):
        # Divide o texto em linhas e aplica a formatação desejada
        linhas = str(texto or "").upper().split('\n')
        return Paragraph('<br/>'.join(linhas), ParagraphStyle(
            'header', 
            fontName='Helvetica-Bold', 
            fontSize=9,
            alignment=1))  # Centralizado

    # Criar o PDF em memória
    buffer = io.BytesIO()
    # Definindo as margens em pontos (1,27 cm = 36 pontos)
    margem = 10

    # Criar o documento com margens
    doc = SimpleDocTemplate(buffer,
                            pagesize=landscape(A4),
                            topMargin=margem,
                            bottomMargin=margem,
                            leftMargin=margem,
                            rightMargin=margem)

    # Informações do cabeçalho
    cabecalho = [
        "<b>PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR</b>",
        "<b>SECRETARIA MUNICIPAL DE EDUCAÇÃO</b>"
    ]
    cabecalho2 = [
        "<b>BOLETIM ESCOLAR</b>",
        "<b>6º AO 9º ANO</b>"
    ]
    responsavel =[
        "1º PERÍODO:______________________________________________",
        "2º PERÍODO:______________________________________________",
        "3º PERÍODO:______________________________________________",
        "4º PERÍODO:______________________________________________"
    ]


    # Adicionando a imagem
    figura_superior = os.path.join(os.path.dirname(__file__), 'pacologo.png')  # Ajuste o nome do arquivo conforme necessário
    # Definir estilos
    estilo_centro = ParagraphStyle(name='centro', fontSize=12, alignment=1, leading=18)
    estilo_formatado = ParagraphStyle(name='centro', fontSize=12, alignment=4, leading=16)

    # Estilo para células de tabela e helper para garantir Paragraphs
    estilo_valor = ParagraphStyle(name='valor', fontSize=10, alignment=1)
    def _cell(val, style=estilo_valor):
        if isinstance(val, Paragraph):
            return val
        return Paragraph(str(val), style)

    paragrafo1 = Paragraph("1. O(a) estudante é avaliado(a) em situações diversas no processo de ensino - aprendizagem;", estilo_formatado)
    paragrafo2 = Paragraph("2. O rendimento dos estudantes é gerado a partir de 4 notas de cada período letivo, médias aritméticas simples, notas, resultado de diferentes estratégias einstrumentos usados para a avaliação.;", estilo_formatado)
    paragrafo3 = Paragraph("3. A média anual é uma média aritmética simples das quatro notas do período. O estudante poderá ser submetido a uma avaliação final, caso seu desempenho não seja minimamente satisfatório para aprovação.", estilo_formatado)
    paragrafo4 = Paragraph("4. A frequência mínima para promoção é de 75% da carga horária anual.", estilo_formatado)
    data_costa = [[paragrafo1], [paragrafo2], [paragrafo3], [paragrafo4]]

    # Criando a tabela e definindo o estilo da nova tabela
    table_costa = Table(data_costa, colWidths=[3.5 * inch])
    table_costa.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
    ]))

    # Criar parágrafos com linhas para assinatura em cima e os nomes embaixo
    paragrafo_escola = Paragraph(f"<i><b>{nome_escola.upper()}</b></i><br/>________________________________________________<br/>UNIDADE DE ENSINO", estilo_centro)
    paragrafo_aluno = Paragraph(f"<i><b>{nome_aluno.upper()}</b></i><br/>________________________________________________<br/>ALUNO(A)", estilo_centro)
    paragrafo_gestor = Paragraph("________________________________________________<br/>GESTOR(A)", estilo_centro)
    paragrafo_ano = Paragraph(f"<b>{serie.upper()}</b><br/>__________<br/>ANO", estilo_centro)
    paragrafo_turma = Paragraph(f"<b>{turma.upper()}</b><br/>__________<br/>TURMA", estilo_centro)
    paragrafo_turno = Paragraph(f"<b>{turno.upper()}</b><br/>__________<br/>TURNO", estilo_centro)
    paragrafo_anoletivo = Paragraph(f"<b>{ano_letivo}</b><br/>__________<br/>ANO LETIVO", estilo_centro)

    data_turma =[
        [paragrafo_ano,paragrafo_turma,paragrafo_turno,paragrafo_anoletivo]
    ]
    # Criando a tabela e definindo o estilo da tabela de preenchimento
    table_turma = Table(data_turma, colWidths=[1.17 * inch] * 4)  # Definindo largura das colunas
    table_turma.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    data = [
        [table_costa, Image(figura_superior, width=1 * inch, height=1 * inch)],
        ['', Paragraph('<br/>'.join(cabecalho), estilo_centro)],
        ['', ''],
        ['', paragrafo_escola],
        ['', paragrafo_aluno],
        ['',table_turma],
        ['',paragrafo_gestor],
    ]

    # Criando a tabela e definindo o estilo da tabela principal
    table = Table(data, colWidths=[5.2 * inch, 5.2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Adicionando a tabela aos elementos do PDF
    elements = []
    elements.append(table)

    # Criando uma nova tabela para o conteúdo abaixo do cabeçalho
    data_conteudo = [
        [Paragraph('<br/>'.join(cabecalho2), estilo_centro)]
    ]

    # Criando a tabela e definindo o estilo da nova tabela
    table_conteudo = Table(data_conteudo, colWidths=[3 * inch])
    table_conteudo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
    ]))

    # Atualizando a tabela principal para incluir a nova tabela na segunda coluna
    data[2][1] = table_conteudo
    altura = 65
    row_heights = [None, altura, None, altura, altura, altura, altura]
    # Atualizando a tabela principal com os novos dados
    table = Table(data, colWidths=[5.3 * inch, 5.3 * inch], rowHeights=row_heights)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Alinhamento horizontal centralizado
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alinhamento vertical centralizado
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        # ('GRID', (0, 0), (-1, -1), 1.5, colors.black),
        ('SPAN', (0, 0), (0, 6)),
    ]))

    # Adicionando a tabela atualizada aos elementos do PDF
    elements = []
    elements.append(table)
    # Iniciar a segunda página com a tabela
    elements.append(PageBreak())
    elements.append(Paragraph("<b>RENDIMENTO ANUAL DO ALUNO</b>",ParagraphStyle(name='centro', fontSize=14, alignment=1, leading=18)))
    elements.append(Spacer(1, 0.125 * inch))
    # Inicialização da tabela de notas
    estilo_cabecalho_menor = ParagraphStyle(name='cabecalho_menor', fontSize=10, alignment=1)
    data_nota = [
        [quebra_linha("COMPONENTES CURRICULARES"), quebra_linha("1º PERÍODO"), _cell(''), quebra_linha("2º PERÍODO"), _cell(''),
        quebra_linha("3º PERÍODO"), _cell(''), quebra_linha("4º PERÍODO"), _cell(''), quebra_linha("RESULTADOS FINAIS"), _cell(''), _cell(''), _cell(''), quebra_linha_menor("SITUAÇÃO FINAL")],
        [quebra_linha("COMPONENTES CURRICULARES"), quebra_linha_menor("NOTA"), quebra_linha_menor("FALTAS"), quebra_linha_menor("NOTA"), quebra_linha_menor("FALTAS"), quebra_linha_menor("NOTA"), quebra_linha_menor("FALTAS"), quebra_linha_menor("NOTA"), quebra_linha_menor("FALTAS"), quebra_linha_menor("MÉDIA ANUAL"),quebra_linha_menor("AVAL. FINAL"),quebra_linha_menor("NOTA FINAL"),quebra_linha_menor("TOTAL FALTAS"), quebra_linha_menor("SITUAÇÃO FINAL")]
    ]

    # Inicialização do dicionário para armazenar notas e faltas por disciplina
    notas_disciplinas = {disciplina: ["--", "--", "--", "--"] for disciplina in ordem_disciplinas}
    faltas_bimestrais = {disciplina: [0, 0, 0, 0] for disciplina in ordem_disciplinas}

    # Iterar sobre os dados do aluno
    for linha in dados_aluno:
        disciplina = linha[6]  # 'disciplina' é a 7ª coluna (índice 6)
        bimestre = linha[8]    # 'bimestre' é a 9ª coluna (índice 8)
        nota = _safe_float(linha[7], 0.0)  # 'nota' é a 8ª coluna (índice 7)
        faltas = _safe_int(linha[9], 0)  # Ensure faltas defaults to zero if None

        # Verificar se a disciplina está no mapeamento
        if disciplina not in ordem_disciplinas:
            continue

        # Dividir a nota por 10 para formatação
        nota_formatada = nota / 10

        # Preencher a nota correspondente ao bimestre
        if bimestre == '1º bimestre':
            notas_disciplinas[disciplina][0] = f"{nota_formatada:.1f}"
            faltas_bimestrais[disciplina][0] = faltas
        elif bimestre == '2º bimestre':
            notas_disciplinas[disciplina][1] = f"{nota_formatada:.1f}"
            faltas_bimestrais[disciplina][1] = faltas
        elif bimestre == '3º bimestre':
            notas_disciplinas[disciplina][2] = f"{nota_formatada:.1f}"
            faltas_bimestrais[disciplina][2] = faltas
        elif bimestre == '4º bimestre':
            notas_disciplinas[disciplina][3] = f"{nota_formatada:.1f}"
            faltas_bimestrais[disciplina][3] = faltas

    # Calcular total de faltas
    total_faltas = sum(sum(faltas) for faltas in faltas_bimestrais.values())
    numero_dias_aula = _safe_int(primeira_linha[10], 0)
    finalizado = False
    
    # Obter todas as recuperações e avaliações finais de uma vez
    conn = conectar_bd()
    if conn is None:
        recuperacoes = {}
        avaliacoes = {}
    else:
        cursor = cast(Any, conn).cursor()
        try:
            # Buscar todas as recuperações
            cursor.execute("""
                SELECT disciplina_id, nota 
                FROM recuperacao 
                WHERE aluno_id = %s AND ano_letivo_id = %s
            """, (_to_int_param(aluno_id), _to_int_param(ano_letivo_id)))
            resultados_rec = cursor.fetchall()
            recuperacoes = {r[0]: r[1] for r in resultados_rec}

            # Buscar todas as avaliações finais
            cursor.execute("""
                SELECT disciplina_id, nota 
                FROM avaliacao_final 
                WHERE aluno_id = %s AND ano_letivo_id = %s
            """, (_to_int_param(aluno_id), _to_int_param(ano_letivo_id)))
            resultados_av = cursor.fetchall()
            avaliacoes = {r[0]: r[1] for r in resultados_av}

            # Preencher a tabela data_nota com as disciplinas e suas respectivas notas
            for disciplina in ordem_disciplinas:
                # Calcular média aritmética das notas
                notas = []
                for nota in notas_disciplinas[disciplina]:
                    if nota != "--":
                        notas.append(_safe_float(nota))

                if not notas:
                    continue  # Pular disciplinas sem notas registradas

                # Calcular média anual com as notas disponíveis
                media_anual_sem_arredondamento = sum(notas) / len(notas)
                media_anual_arredondada = arredondar_personalizado(media_anual_sem_arredondamento)

                # Verificar se temos o ID desta disciplina
                disciplina_id = disciplina_id_map.get(disciplina)

                if disciplina_id:
                    # Verificar se há recuperação para esta disciplina
                    nota_recuperacao = "--"
                    media_final_arredondada = media_anual_arredondada

                    if disciplina_id in recuperacoes:
                        rec_val = _safe_float(recuperacoes[disciplina_id], 0.0)
                        nota_recuperacao = f"{rec_val/10:.1f}"
                        media_final_sem_arredondamento = (media_anual_sem_arredondamento + rec_val) / 2
                        media_final_arredondada = arredondar_personalizado(media_final_sem_arredondamento)

                    # Adicionar a linha à tabela data_nota com as notas reais
                    data_nota.append([
                        _cell(quebra_linha(disciplina)),
                        _cell(notas_disciplinas[disciplina][0]),
                        _cell(str(faltas_bimestrais[disciplina][0]) if faltas_bimestrais[disciplina][0] > 0 else "--"),
                        _cell(notas_disciplinas[disciplina][1]),
                        _cell(str(faltas_bimestrais[disciplina][1]) if faltas_bimestrais[disciplina][1] > 0 else "--"),
                        _cell(notas_disciplinas[disciplina][2]),
                        _cell(str(faltas_bimestrais[disciplina][2]) if faltas_bimestrais[disciplina][2] > 0 else "--"),
                        _cell(notas_disciplinas[disciplina][3]),
                        _cell(str(faltas_bimestrais[disciplina][3]) if faltas_bimestrais[disciplina][3] > 0 else "--"),
                        _cell(f"{media_anual_arredondada:.1f}"),
                        _cell(nota_recuperacao),
                        _cell(f"{media_final_arredondada:.1f}" if len(notas) == 4 else "--"),
                        _cell(str(sum(faltas_bimestrais[disciplina]))),
                        _cell("AP" if len(notas) == 4 and media_final_arredondada >= 6 else ("RP" if len(notas) == 4 else "--"))
                    ])
                else:
                    data_nota.append([
                        _cell(quebra_linha(disciplina)),
                        _cell(notas_disciplinas[disciplina][0]),
                        _cell(str(faltas_bimestrais[disciplina][0]) if faltas_bimestrais[disciplina][0] > 0 else "--"),
                        _cell(notas_disciplinas[disciplina][1]),
                        _cell(str(faltas_bimestrais[disciplina][1]) if faltas_bimestrais[disciplina][1] > 0 else "--"),
                        _cell(notas_disciplinas[disciplina][2]),
                        _cell(str(faltas_bimestrais[disciplina][2]) if faltas_bimestrais[disciplina][2] > 0 else "--"),
                        _cell(notas_disciplinas[disciplina][3]),
                        _cell(str(faltas_bimestrais[disciplina][3]) if faltas_bimestrais[disciplina][3] > 0 else "--"),
                        _cell(f"{media_anual_arredondada:.1f}"),
                        _cell("--"),
                        _cell(f"{media_anual_arredondada:.1f}" if len(notas) == 4 else "--"),
                        _cell(str(sum(faltas_bimestrais[disciplina]))),
                        _cell("AP" if len(notas) == 4 and media_anual_arredondada >= 6 else ("RP" if len(notas) == 4 else "--"))
                    ])
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

    # Criando a tabela de notas com ReportLab
    tabela_notas = Table(data_nota, colWidths=[1.6 * inch] + [0.70 * inch] * 12 + [1.1 * inch])
    tabela_notas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BACKGROUND', (0, 0), (13, 1), colors.lightgrey),  
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (1, 0), (2, 0)),
        ('SPAN', (3, 0), (4, 0)),
        ('SPAN', (5, 0), (6, 0)),
        ('SPAN', (7, 0), (8, 0)),
        ('SPAN', (9, 0), (12, 0)),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (13, 0), (13, 1)),
    ]))

    # Adiciona a tabela ao PDF
    elements.append(tabela_notas)

    elements.append(Spacer(1, 0.125 * inch))
    data_assinatura_responsavel =[
        [Paragraph("ASSINATURA DO RESPONSÁVEL:", estilo_centro)],
        [Paragraph('<br/><br/>'.join(responsavel), estilo_formatado)]
    ]
    tabela_assinatura = Table(data_assinatura_responsavel, colWidths=[5.5 * inch])
    tabela_assinatura.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Inicializar a variável para armazenar o resultado final
    resultado_final = ["( ) AP - Aprovado", "( ) RP - Reprovado"]

    # Verificar se todas as disciplinas têm 4 notas
    todas_notas_completas = True
    media_final_arredondada = 0
    for disciplina in ordem_disciplinas:
        notas = [float(nota) for nota in notas_disciplinas[disciplina] if nota != "--"]
        if len(notas) != 4:
            todas_notas_completas = False
            break

    # Só verificar aprovação se todas as notas estiverem completas
    if todas_notas_completas:
        if media_final_arredondada < 6 or total_faltas > (0.25 * numero_dias_aula):
            resultado_final[0] = "( ) AP - Aprovado"
            resultado_final[1] = "( ) RP - Reprovado"
        elif media_final_arredondada >= 6 and total_faltas <= (0.25 * numero_dias_aula):
            resultado_final[0] = "(X) AP - Aprovado"
        else:
            resultado_final[0] = "( ) AP - Aprovado"
            resultado_final[1] = "(X) RP - Reprovado"
    else: 
        # Se não tiver todas as notas, marcar como pendente
        resultado_final[0] = "( ) AP - Aprovado"
        resultado_final[1] = "( ) RP - Reprovado"

    # Atualizar data_resultadofinal
    data_resultadofinal = [
        [Paragraph("RESULTADO FINAL:", estilo_formatado)],
        [Paragraph(resultado_final[0], estilo_formatado)],
        [Paragraph(resultado_final[1], estilo_formatado)]
    ]
    altura1 = 18
    row_heights1 = [None, altura1, None]
    tabela_resultadofinal = Table(data_resultadofinal, colWidths=[5.5 * inch], rowHeights=row_heights1)
    tabela_resultadofinal.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    data_professor = [
        [Paragraph("SECRETÁRIO(A)/RESPONSÁVEL PELO REGISTRO:<br/>.<br/>.", estilo_formatado)]
    ]
    tabela_professor = Table(data_professor, colWidths=[5.5 * inch])
    tabela_professor.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    data_resultados= [
        [tabela_assinatura, tabela_professor],
        ['', tabela_resultadofinal]
    ]
    
    tabela_resultados = Table(data_resultados,colWidths=[5.55 * inch, 5.55 * inch])
    tabela_resultados.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('SPAN', (0, 0), (0, 1)),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        # ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(tabela_resultados)
    elements.append(Spacer(1, 0.125 * inch))
    
    # Só mostrar a mensagem se todas as notas estiverem completas
    if todas_notas_completas:
        # Usar o ano letivo seguinte ao valor obtido do banco de dados
        ano_futuro = _safe_int(ano_letivo, 0) + 1
        # Supondo que 'serie' seja uma string que contém o ano, como "1º Ano"
        ano_atual = _safe_int(serie.split()[0].replace('º', ''), 0)  # Remove o símbolo "º"
        
        # Mensagem sobre o próximo ano letivo
        if resultado_final[1].startswith("(X) RP-Reprovado"):
            # Caso o aluno tenha sido reprovado
            mensagem = f"O aluno frequentará o {ano_atual}º Ano do Ensino Fundamental em {ano_futuro}."
        else:
            if serie == "9º Ano":
                mensagem = f"O aluno frequentará o 1º Ano do Ensino Médio em {ano_futuro}."
            else:
                mensagem = f"O aluno frequentará o {ano_atual + 1}º Ano do Ensino Fundamental em {ano_futuro}."

        # Adicionando a mensagem ao PDF
        elements.append(Paragraph(f"<b>{mensagem}</b>", estilo_centro))

    # Construindo o PDF 
    doc.build(elements)

    # Resetar o buffer para o início
    buffer.seek(0)
    
    # Criar nome do arquivo
    data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"Boletim_{nome_aluno.replace(' ', '_')}_{data_atual}.pdf"
    caminho_arquivo = os.path.join('documentos_gerados', nome_arquivo)
    
    # Garantir que o diretório existe
    os.makedirs('documentos_gerados', exist_ok=True)
    
    # Salvar o arquivo localmente
    with open(caminho_arquivo, 'wb') as f:
        f.write(buffer.getvalue())
    
    # Criar descrição detalhada
    descricao = f"Boletim do aluno {nome_aluno}"
    if turma:
        descricao += f" - {serie} {turma}"
    if turno:
        descricao += f" - Turno: {'Matutino' if turno == 'MAT' else 'Vespertino'}"
    
    # Salvar no sistema de gerenciamento de documentos
    sucesso, mensagem, link = salvar_documento_sistema(
        caminho_arquivo=caminho_arquivo,
        tipo_documento=TIPO_BOLETIM,
        aluno_id=aluno_id,
        finalidade=f"Boletim {ano_letivo}",
        descricao=descricao
    )
    
    if not sucesso:
        from tkinter import messagebox
        messagebox.showwarning("Aviso", 
                           "O boletim foi gerado mas houve um erro ao salvá-lo no sistema:\n" + mensagem)
    
    salvar_e_abrir_pdf(buffer)

def boletim(aluno_id, ano_letivo_id):
    """Busca o serie_id e ano_letivo_id para um aluno específico e gera o boletim apropriado."""
    conn = conectar_bd()
    if conn is None:
        logger.error("Erro ao conectar ao banco de dados.")
        return
    cursor = cast(Any, conn).cursor()

    try:
        # Verificar se o aluno possui matrícula ativa no ano letivo especificado
        query = """
        SELECT t.serie_id, a.ano_letivo, s.nome, m.id as matricula_id
        FROM matriculas m
        JOIN turmas t ON m.turma_id = t.id
        JOIN anosletivos a ON m.ano_letivo_id = a.id
        JOIN serie s ON t.serie_id = s.id
        WHERE m.aluno_id = %s AND m.ano_letivo_id = %s AND m.status = 'Ativo'
        """
        params = (_to_int_param(aluno_id), _to_int_param(ano_letivo_id))
        cursor.execute(query, params)
        resultado = cursor.fetchone()
        
        if resultado:
            serie_id = _safe_int(resultado[0], 0)
            nome_serie = resultado[2]
            matricula_id = resultado[3]
            
            # Verificar se existem notas registradas para o aluno no ano letivo
            query_notas = """
            SELECT COUNT(*) 
            FROM notas 
            WHERE aluno_id = %s AND ano_letivo_id = %s
            """
            cursor.execute(query_notas, (_to_int_param(aluno_id), _to_int_param(ano_letivo_id)))
            _row = cursor.fetchone()
            count_notas = _row[0] if _row else 0
            
            # Verificar se existem faltas registradas para o aluno no ano letivo
            query_faltas = """
            SELECT COUNT(*) 
            FROM faltas_bimestrais 
            WHERE aluno_id = %s AND ano_letivo_id = %s
            """
            cursor.execute(query_faltas, (_to_int_param(aluno_id), _to_int_param(ano_letivo_id)))
            _row = cursor.fetchone()
            count_faltas = _row[0] if _row else 0
            
            if count_notas == 0:
                logger.warning(f"Não há notas registradas para o aluno ID {aluno_id} no ano letivo selecionado.")
                return
            
            logger.info(f"Gerando boletim para o aluno ID {aluno_id} da série {nome_serie}")
            logger.info(f"Total de notas: {count_notas}, Total de registros de faltas: {count_faltas}")
            
            # Verificar se é anos iniciais ou finais
            if serie_id > 7:  # Anos finais (6º ao 9º)
                boletimfinais(aluno_id, ano_letivo_id)
            else:  # Anos iniciais (1º ao 5º)
                boletiminiciais(aluno_id, ano_letivo_id)
        else:
            logger.info(f"Nenhuma matrícula ativa encontrada para aluno_id: {aluno_id} no ano letivo: {ano_letivo_id}")

    finally:
        cursor.close()
        conn.close()
 
# Comentário explicativo e exemplo de uso:
"""
Para gerar um boletim, use a função boletim(aluno_id, ano_letivo_id) com os IDs corretos.
Exemplo:
    boletim(457, 1)  # Gera boletim para o aluno ID 457 no ano letivo ID 1
"""
# Descomente a linha abaixo para testar com um aluno específico:
# boletim(572, 1)