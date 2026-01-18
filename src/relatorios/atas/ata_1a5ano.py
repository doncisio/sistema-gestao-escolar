import io
import os
import pandas as pd
from reportlab.platypus import Image, Paragraph, Table, TableStyle, Spacer, PageBreak
from src.core.config import get_image_path, ANO_LETIVO_ATUAL
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
from src.utils.utilitarios.tipos_documentos import TIPO_ATA
from reportlab.lib.colors import black, white
from reportlab.lib.enums import TA_JUSTIFY
from src.core.conexao import conectar_bd
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf, criar_pdf
from scripts.migracao.inserir_no_historico_escolar import inserir_no_historico_escolar
from scripts.auxiliares.biblio_editor import adicionar_quebra_linha, quebra_linha, arredondar_personalizado, criar_cabecalho_pdf
from src.utils.dates import formatar_data_extenso
import datetime
from typing import Any, Dict, Optional, cast, List
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# `formatar_data_extenso` importado de `utils.dates`

def obter_dados_alunos(cursor):
    query = """
        SELECT
        a.id AS aluno_id,
        a.nome AS 'NOME DO ALUNO',
        a.sexo AS 'SEXO',
        a.data_nascimento AS 'NASCIMENTO',
        s.nome AS 'NOME_SERIE',
        s.id AS 'SERIE_ID',
        t.nome AS 'NOME_TURMA',
        t.turno AS 'TURNO',
        m.status AS 'STATUS',
        m.data_matricula AS 'DATA_MATRICULA',
        f.nome AS 'NOME_PROFESSOR',
        COALESCE(SUM(CASE WHEN d.nome = 'LÍNGUA PORTUGUESA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) / NULLIF(COUNT(CASE WHEN d.nome = 'LÍNGUA PORTUGUESA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) AS 'NOTA_PORTUGUES',
        COALESCE(SUM(CASE WHEN d.nome = 'MATEMÁTICA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) / NULLIF(COUNT(CASE WHEN d.nome = 'MATEMÁTICA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) AS 'NOTA_MATEMATICA',
        COALESCE(SUM(CASE WHEN d.nome = 'HISTÓRIA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) / NULLIF(COUNT(CASE WHEN d.nome = 'HISTÓRIA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) AS 'NOTA_HISTORIA',
        COALESCE(SUM(CASE WHEN d.nome = 'GEOGRAFIA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) / NULLIF(COUNT(CASE WHEN d.nome = 'GEOGRAFIA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) AS 'NOTA_GEOGRAFIA',
        COALESCE(SUM(CASE WHEN d.nome = 'CIÊNCIAS' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) / NULLIF(COUNT(CASE WHEN d.nome = 'CIÊNCIAS' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) AS 'NOTA_CIENCIAS',
        COALESCE(SUM(CASE WHEN d.nome = 'ARTE' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) / NULLIF(COUNT(CASE WHEN d.nome = 'ARTE' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) AS 'NOTA_ARTES',
        COALESCE(SUM(CASE WHEN d.nome = 'ENSINO RELIGIOSO' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) / NULLIF(COUNT(CASE WHEN d.nome = 'ENSINO RELIGIOSO' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) AS 'NOTA_ENS_RELIGIOSO',
        COALESCE(SUM(CASE WHEN d.nome = 'EDUCAÇÃO FÍSICA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) / NULLIF(COUNT(CASE WHEN d.nome = 'EDUCAÇÃO FÍSICA' AND d.nivel_id = 2 AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025) THEN COALESCE(n.nota, 0) END), 0) AS 'NOTA_ED_FISICA'
    FROM
        Alunos a
    JOIN
        Matriculas m ON a.id = m.aluno_id
    JOIN
        Turmas t ON m.turma_id = t.id
    JOIN
        series s ON t.serie_id = s.id
    LEFT JOIN
        Notas n ON a.id = n.aluno_id AND n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025)
    LEFT JOIN
        Disciplinas d ON n.disciplina_id = d.id
    LEFT JOIN
        Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
    WHERE
        m.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025)
        AND a.escola_id = 60
        AND m.status IN ('Ativo', 'Transferido', 'Evadido')
        AND s.id <= 7 -- Filtro para séries com ID menor ou igual a 7
    GROUP BY
        a.id, a.nome, s.nome, t.nome, t.turno, m.status, m.data_matricula, f.nome, s.id
    ORDER BY
        a.nome ASC;
    """
    cursor.execute(query)
    return cursor.fetchall()

def processar_dados(dados_aluno):
    df = pd.DataFrame(dados_aluno)
    for coluna in ['NOTA_PORTUGUES', 'NOTA_MATEMATICA', 'NOTA_HISTORIA', 'NOTA_GEOGRAFIA', 'NOTA_CIENCIAS', 'NOTA_ARTES', 'NOTA_ENS_RELIGIOSO', 'NOTA_ED_FISICA']:
        df[coluna] = pd.to_numeric(df[coluna], errors='coerce').fillna(0).astype(int)
    return df

def determinar_situacao_final(row, faltas_dict, limite_faltas, notas_finais=None, disciplinas_map=None):
    """Determina a situação final do aluno considerando notas e faltas"""
    aluno_id = row['aluno_id']
    
    # Verificar faltas primeiro
    if faltas_dict.get(aluno_id, 0) > limite_faltas:
        return 'Reprovada*' if row['SEXO'] == 'F' else 'Reprovado*'
    
    # Se não houver notas_finais ou disciplinas_map, usar lógica antiga
    if not notas_finais or not disciplinas_map:
        colunas = ['NOTA_PORTUGUES', 'NOTA_MATEMATICA', 'NOTA_CIENCIAS', 'NOTA_HISTORIA', 'NOTA_GEOGRAFIA', 'NOTA_ARTES', 'NOTA_ENS_RELIGIOSO', 'NOTA_ED_FISICA']
        if all(arredondar_personalizado(row[col]) >= 60 for col in colunas):
            return 'Aprovada' if row['SEXO'] == 'F' else 'Aprovado'
        return 'Reprovada' if row['SEXO'] == 'F' else 'Reprovado'
    
    # Usar notas_finais quando disponível
    notas_para_verificar = []
    for col, disciplina_id in disciplinas_map.items():
        if aluno_id in notas_finais and disciplina_id in notas_finais[aluno_id]:
            nota = float(notas_finais[aluno_id][disciplina_id])
            if nota > 0:
                notas_para_verificar.append(nota)
        else:
            nota = arredondar_personalizado(row[col])
            if nota > 0:
                notas_para_verificar.append(nota)
    
    # Se não houver notas válidas, aprovar (caso raro)
    if not notas_para_verificar:
        return 'Aprovada' if row['SEXO'] == 'F' else 'Aprovado'
    
    # Verificar se todas as notas são >= 60
    if all(nota >= 60 for nota in notas_para_verificar):
        return 'Aprovada' if row['SEXO'] == 'F' else 'Aprovado'
    return 'Reprovada' if row['SEXO'] == 'F' else 'Reprovado'

def verificar_ano_letivo_terminado(cursor, ano_letivo=2025):
    """Verifica se o ano letivo especificado já terminou."""
    try:
        # Verificar se a data atual é posterior à data_fim do ano letivo
        cursor.execute("""
            SELECT ano_letivo, data_fim FROM anosletivos WHERE ano_letivo = %s
        """, (ano_letivo,))
        resultado = cursor.fetchone()
        
        if resultado and resultado['data_fim']:
            data_fim = resultado['data_fim']
            data_atual = datetime.datetime.now().date()
            return data_atual >= data_fim
        
        # Se não houver data_fim definida, não considerar o ano letivo como terminado
        return False
    except Exception as e:
        logger.exception("Erro ao verificar término do ano letivo: %s", e)
        # Como houve erro, é mais seguro não exportar as notas
        return False

def obter_notas_finais(cursor):
    """
    Obtém as notas finais dos alunos após recuperação anual.
    
    Consulta a tabela notas_finais que contém:
    - media_final: nota final após recuperação (se houver)
    
    Retorna dict: {aluno_id: {disciplina_id: nota}}
    """
    try:
        cursor.execute("""
            SELECT aluno_id, disciplina_id, media_final as nota
            FROM notas_finais 
            WHERE ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025)
        """)
        notas_finais = {}
        for n in cursor.fetchall():
            aluno_id = n['aluno_id']
            disciplina_id = n['disciplina_id']
            nota = n['nota']
            if aluno_id not in notas_finais:
                notas_finais[aluno_id] = {}
            notas_finais[aluno_id][disciplina_id] = nota
        return notas_finais
    except Exception as e:
        logger.warning("Tabela notas_finais não disponível ou vazia: %s", e)
        return {}

# Mapeamento de nomes de colunas para disciplina_id
disciplinas_map = {
    'NOTA_PORTUGUES': 1,  # ID para Português
    'NOTA_MATEMATICA': 2,  # ID para Matemática
    'NOTA_HISTORIA': 3,     # ID para História
    'NOTA_GEOGRAFIA': 4,    # ID para Geografia
    'NOTA_CIENCIAS': 5,    # ID para Ciências
    'NOTA_ARTES': 6,        # ID para Artes
    'NOTA_ENS_RELIGIOSO': 7, # ID para Ensino Religioso
    'NOTA_ED_FISICA': 8    # ID para Educação Física
}

def gerar_pdf(df, faltas_dict, limite_faltas, cabecalho, figura_superior, figura_inferior, notas_finais=None, ano_letivo_terminado=False):
    buffer = io.BytesIO()
    elements = []

    data_atual = datetime.datetime.now().date()
    elements.append(criar_cabecalho_pdf(figura_superior, figura_inferior, cabecalho))
    elements.append(Spacer(1, 3.3 * inch))
    elements.append(Paragraph(f"<b>ATA GERAL<br/>DE<br/>RESULTADOS FINAIS {ANO_LETIVO_ATUAL}</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1, leading=30)))
    elements.append(Spacer(1, 4 * inch))
    elements.append(Paragraph(f"<b>{ANO_LETIVO_ATUAL}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
    elements.append(PageBreak())

    # Iniciar a segunda página com a tabela
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
       
        elements.append(criar_cabecalho_pdf(figura_superior, figura_inferior, cabecalho))
        elements.append(Spacer(1, 0.25 * inch))
        elements.append(Paragraph(f"<b>ATA DE RESULTADOS FINAIS – {ANO_LETIVO_ATUAL}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.125 * inch))
        elements.append(Paragraph(f"INSTITUIÇÃO DE ENSINO: U.E.B. PROFª NADIR NASCIMENTO MORAES aos {formatar_data_extenso()}, concluiu-se o processo de avaliação somativa dos alunos do {nome_serie}{'' if nome_turma == ' ' else nome_turma}, {'Turno <b>Matutino</b>' if turno == 'MAT' else 'Turno <b>Vespertino</b>'}, do Ensino Fundamental I, desta Instituição de Ensino, com os seguintes resultados:", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=TA_JUSTIFY, leading=18)))
        elements.append(Spacer(1, 0.125 * inch))

        # Definir os dados da tabela com as notas
        data = [
            ['Nº', 'NOME DO ALUNO', 
             adicionar_quebra_linha("L. PORTUGUESA"), 
             adicionar_quebra_linha("MATEMÁTICA"),
             adicionar_quebra_linha("CIÊNCIAS"), 
             adicionar_quebra_linha("HISTÓRIA"), 
             adicionar_quebra_linha("GEOGRAFIA"), 
             adicionar_quebra_linha("ARTE"), 
             adicionar_quebra_linha("ENS. RELIGIOSO"), 
             adicionar_quebra_linha("ED. FÍSICA"),
             quebra_linha("SITUAÇÃO\nFINAL")]
        ]

        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            if row['STATUS'] == 'Transferido':
                status = 'TRANSFERIDA' if row['SEXO'] == 'F' else 'TRANSFERIDO'
                data.append([row_num, nome, status, status, status, status, status, status, status, status, status])
            elif row['STATUS'] == 'Evadido':
                status = 'EVADIDA' if row['SEXO'] == 'F' else 'EVADIDO'
                data.append([row_num, nome, status, status, status, status, status, status, status, status, status])
            else:
                notas_atualizadas = []
                aluno_id = row['aluno_id']
                for col in ['NOTA_PORTUGUES', 'NOTA_MATEMATICA', 'NOTA_CIENCIAS', 
                            'NOTA_HISTORIA', 'NOTA_GEOGRAFIA', 'NOTA_ARTES', 
                            'NOTA_ENS_RELIGIOSO', 'NOTA_ED_FISICA']:
                    disciplina_id = disciplinas_map[col]
                    
                    # Usar nota de notas_finais se disponível, senão calcular da média bimestral
                    if notas_finais and aluno_id in notas_finais and disciplina_id in notas_finais[aluno_id]:
                        nota_atual = int(notas_finais[aluno_id][disciplina_id])
                    else:
                        nota_atual = int(arredondar_personalizado(row[col]))
                    
                    notas_atualizadas.append(nota_atual)
                    
                    # Inserir no histórico escolar se o ano letivo estiver fechado
                    ano_letivo_id = 1  # ID para 2025
                    escola_id = 60
                    serie_id = row['SERIE_ID']
                    if ano_letivo_terminado:
                        inserir_no_historico_escolar(aluno_id, disciplina_id, float(nota_atual), ano_letivo_id, escola_id, serie_id)
                situacao_final = row['Situação Final']
                data.append([row_num, nome] + notas_atualizadas + [situacao_final])

        table = Table(data, colWidths=[0.35 * inch, 3.4 * inch, 0.35 * inch, 0.35 * inch, 0.35 * inch, 0.35 * inch, 0.35 * inch, 0.35 * inch, 0.35 * inch, 0.35 * inch, 1 * inch])
        # Mesclando as células para alunos transferidos
        for i in range(len(data)):
            if data[i][2] == 'TRANSFERIDO':  # Verifica se a linha contém 'TRANSFERIDO'
                table.setStyle(TableStyle([
                    ('SPAN', (2, i), (10, i))  # Mescla da coluna 2 até a coluna 10 na linha i
                ]))
            elif data[i][2] == 'TRANSFERIDA':  # Verifica se a linha contém 'TRANSFERIDA'
                table.setStyle(TableStyle([
                    ('SPAN', (2, i), (10, i))  # Mescla da coluna 2 até a coluna 10 na linha i
                ]))
            elif data[i][2] == 'EVADIDO':  # Verifica se a linha contém 'EVADIDO'
                table.setStyle(TableStyle([
                    ('SPAN', (2, i), (10, i))  # Mescla da coluna 2 até a coluna 10 na linha i
                ]))
            elif data[i][2] == 'EVADIDA':  # Verifica se a linha contém 'EVADIDA'
                table.setStyle(TableStyle([
                    ('SPAN', (2, i), (10, i))  # Mescla da coluna 2 até a coluna 10 na linha i
                ]))
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black),
        ]))

        elements.append(table)
        if any(faltas_dict.get(row['aluno_id'], 0) > limite_faltas for _, row in turma_df.iterrows()):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Observação: (*) <b>Aluno(a) reprovado(a) por excesso de faltas.</b>", 
                                    ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=4, leading=18)))
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("E para constar. Eu, Tarcisio Sousa de Almeida, Técnico em Administração Escolar, lavrei a presente Ata que vai assinada por mim e pelo(a) Gestor(a) da Instituição de Ensino.", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=TA_JUSTIFY, leading=18)))
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(f"Paço do Lumiar – MA, {formatar_data_extenso()}.",
                              ParagraphStyle(name='DeclaracaoTexto', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.5 * inch))
        estilo_centro = ParagraphStyle(name='centro', fontSize=12, alignment=1)
        paragrafo_secretario = Paragraph("_________________________________<br/><br/>Técnico em Administração Escolar", estilo_centro)
        paragrafo_gestor = Paragraph("_________________________________<br/><br/>Gestor(a)", estilo_centro)
        dados_tabela = [[paragrafo_secretario, paragrafo_gestor]]
        tabela = Table(dados_tabela, colWidths=[250, 250])
        tabela.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'BOTTOM')]))
        elements.append(tabela)
        elements.append(PageBreak())

    criar_pdf(buffer, elements)
    
    # Abrir o arquivo para visualização
    buffer.seek(0)
    salvar_e_abrir_pdf(buffer)
    
    # Retornar o buffer para uso posterior
    return buffer

def ata_geral():
    conn = conectar_bd()
    if conn is None:
        return
    cursor = cast(Any, conn).cursor(dictionary=True)
    
    # Verificar se o ano letivo terminou
    ano_letivo_terminado = verificar_ano_letivo_terminado(cursor)
    
    dados_aluno = obter_dados_alunos(cursor)
    df = processar_dados(dados_aluno)

    try:
        cursor.execute("SELECT numero_dias_aula FROM anosletivos WHERE ano_letivo = 2025")
        resultado_ano_letivo = cast(Optional[Dict[str, Any]], cursor.fetchone())
        if resultado_ano_letivo is None:
            logger.error("Nenhum ano letivo encontrado para 2025.")
            return
        total_aulas = resultado_ano_letivo['numero_dias_aula']
    except Exception as e:
        logger.exception("Erro ao executar a consulta: %s", e)
        return

    limite_faltas = round(total_aulas * 0.25)

    try:
        cursor.execute("""
            SELECT aluno_id, SUM(faltas) AS total_faltas 
            FROM faltas_bimestrais 
            WHERE ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025)
            GROUP BY aluno_id
        """)
        faltas_bimestrais_resultado = cast(List[Dict[str, Any]], cursor.fetchall())
        faltas_dict = {f['aluno_id']: f['total_faltas'] for f in faltas_bimestrais_resultado}
    except Exception as e:
        logger.exception("Erro ao executar a consulta de faltas: %s", e)
        faltas_dict = {}

    cabecalho = [
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>UEB PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]

    # Caminhos das figuras
    figura_superior = str(get_image_path('pacologo.png'))
    figura_inferior = str(get_image_path('logopaco.jpg'))

    # Obter notas finais (pós-recuperação anual) se disponível
    notas_finais = obter_notas_finais(cursor)
    
    # Mapeamento de disciplinas para 1º ao 5º ano
    disciplinas_map = {
        'NOTA_PORTUGUES': 1,  # ID para Português
        'NOTA_MATEMATICA': 2,  # ID para Matemática
        'NOTA_HISTORIA': 3,     # ID para História
        'NOTA_GEOGRAFIA': 4,    # ID para Geografia
        'NOTA_CIENCIAS': 5,    # ID para Ciências
        'NOTA_ARTES': 6,        # ID para Artes
        'NOTA_ENS_RELIGIOSO': 7, # ID para Ensino Religioso
        'NOTA_ED_FISICA': 8    # ID para Educação Física
    }
    
    df['Situação Final'] = df.apply(lambda row: determinar_situacao_final(row, faltas_dict, limite_faltas, notas_finais, disciplinas_map), axis=1)
    
    # Criar nome do arquivo
    data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"Ata_Geral_{data_atual}.pdf"
    caminho_arquivo = os.path.join('documentos_gerados', nome_arquivo)
    
    # Garantir que o diretório existe
    os.makedirs('documentos_gerados', exist_ok=True)
    
    # Gerar o PDF
    buffer = io.BytesIO()
    gerar_pdf(df, faltas_dict, limite_faltas, cabecalho, figura_superior, figura_inferior, notas_finais, ano_letivo_terminado)
    
    # Salvar o arquivo localmente
    buffer.seek(0)
    with open(caminho_arquivo, 'wb') as f:
        f.write(buffer.getvalue())
    
    # Criar descrição detalhada
    descricao = f"Ata Geral de Resultados Finais {ANO_LETIVO_ATUAL} - Anos Iniciais"
    
    # Salvar no sistema de gerenciamento de documentos
    sucesso, mensagem, link = salvar_documento_sistema(
        caminho_arquivo=caminho_arquivo,
        tipo_documento=TIPO_ATA,
        finalidade=f"Resultados Finais {ANO_LETIVO_ATUAL}",
        descricao=descricao
    )
    
    if not sucesso:
        from tkinter import messagebox
        messagebox.showwarning("Aviso", 
                           "A ata foi gerada mas houve um erro ao salvá-la no sistema:\n" + mensagem)

if __name__ == "__main__":
    ata_geral()
