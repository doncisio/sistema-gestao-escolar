import tempfile
import os
import pandas as pd
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import black, white, grey
from reportlab.lib.units import inch
from enum import Enum
from conexao import conectar_bd
from diariodeclasse_capa import create_custom_pdf
from GerenciadorDocumentosSistema import GerenciadorDocumentosSistema
from typing import Optional, Any, cast
from config_logs import get_logger

logger = get_logger(__name__)

# Constante para o tipo de documento
TIPO_DIARIO_CLASSE = "Diário de Classe"

# Definição da enumeração para as orientações
class Orientacao(Enum):
    IDENTIFICAÇÃO_TURMA = "Utilize caneta azul ou preta para o registro. Utilizar a mesma cor de caneta até o fim do ano letivo."
    PRINCIPAIS_AÇÕES_LETIVAS = "Registre as datas dos principais acontecimentos pedagógicos do ano letivo (formações, planejamentos, reunião de pais etc)."
    NÍVEIS_APRENDIZAGEM_DA_ESCRITA = "Realize teste diagnóstico de escrita, de acordo com os meses indicados, e identifique a situação de cada aluno conforme a legenda disponível na página."
    NÍVEIS_DE_LEITURA = "Realize teste diagnóstico de leitura, de acordo com os meses indicados, e identifique a situação de cada aluno conforme a legenda disponível na página."
    REGISTRO_DE_FREQUÊNCIA = "Registre as presenças dos alunos com um (.) e faltas com (F)."
    REGISTRO_DOS_OBJETOS_DE_CONHECIMENTO_HABILIDADES_CÓDIGO_ALFANUMÉRICO_E_ATIVIDADES_DESENVOLVIDAS = "Registre os objetos de conhecimento, o código da habilidade explorada e as atividades desenvolvidas de forma clara e objetiva. Ex.: CI. Corpo Humano (EF01CI02). Atividade coletiva, construção e análise da silhueta dos alunos em papel pardo."
    HABILIDADES_AVALIADAS_NO_PERÍODO = "Registre a tarefa realizada (T1, T2 e T3), o instrumento utilizado e as habilidades avaliadas em cada uma. Ex. T3/Atividade escrita. Habilidades: (EF01MA02, EF01MA03, EF01MA04, EF01MA06)"
    REGISTRO_DO_DESEMPENHO_AVALIATIVO = (
        "O registro do resultado dos alunos será por notas. A média de aprovação é 6 e, segundo o calendário escolar teremos 4 períodos letivos. As notas dos períodos letivos serão compostas da seguinte maneira:",
        [ ['ESTUDANTE', 'LÍNGUA PORTUGUESA','LÍNGUA PORTUGUESA','LÍNGUA PORTUGUESA','LÍNGUA PORTUGUESA','LÍNGUA PORTUGUESA','LÍNGUA PORTUGUESA','LÍNGUA PORTUGUESA'],
            [' ESTUDANTE','T1', 'T2', 'T3', 'T4', 'M', 'EDR', 'NP'],
            ['Alana', '7.0', '7.0', '7.0', '7.0', '7.0', '7.0', '7.0'],
            ['Carlos', '5.0', '6.0', '6.0', '6.0', '5.75', '7.0', '6.0']
        ],
        "LEGENDA:<br/>T1 = primeira atividade avaliativa;<br/>" \
        "T2 = segunda atividade avaliativa;<br/>" \
        "T3 = terceira atividade avaliativa;<br/>" \
        "T4 = quarta atividade avaliativa;<br/>" \
        "M = Média do Período;<br/>" \
        "EDR = Estudos Direcionados de Recuperação;<br/>" \
        "NP = Nota do Período."
    )
    SÍNTESE_DE_REGISTRO_DO_DESEMPENHO_FINAL_DO_ESTUDANTE = (
    "A média anual será a média aritmética simples das quatro notas dos períodos. Se o estudante obtiver média anual igual ou superior a 6,0 (seis), será aprovado no componente curricular. Se obtiver média anual inferior a 6,0 (seis), terá direito à Avaliação Final (AF). O estudante precisa obter nota satisfatória igual ou superior a 6,0 na Avaliação Final para aprovação no componente curricular. No campo Situação Final há de se registrar Aprovado (A) ou Reprovado (R).\n" \
    "<b>Obs: O Diário deverá estar sempre na escola, à disposição para qualquer consulta ou análise por meio do período escolar, reunião de pais e etc.</b>\n"
    )
    ANOTAÇÕES_IMPORTANTES = "Aqui o(a) professor(a) poderá relatar algumas situações não contempladas em nenhuma das tabelas anteriores, como a entrada de um aluno no meio do período escolar, reunião de pais e etc."
    RESULTADO_ANUAL= "Registro do parecer final do aluno de acordo com a legenda estabelecida."
    QUADRO_DEMONSTRATIVO_DE_CARGA_HORÁRIA = "Nesse campo será preenchido a carga horária anual que aconteceu no ano de ensino."

# Função para criar o PDF
def criar_pdf(nome_arquivo):
    conn = conectar_bd()
    cursor = cast(Any, conn).cursor(dictionary=True)

    # Consulta SQL para buscar os dados necessários
    query = """
        SELECT 
        a.nome AS 'NOME DO ALUNO', 
        a.sexo AS 'SEXO', 
        a.data_nascimento AS 'NASCIMENTO',
        s.nome AS 'NOME_SERIE', 
        t.nome AS 'NOME_TURMA', 
        t.turno AS 'TURNO', 
        m.status AS 'SITUAÇÃO',
        f.nome AS 'NOME_PROFESSOR',
        GROUP_CONCAT(DISTINCT r.telefone ORDER BY r.id SEPARATOR '/') AS 'TELEFONES'
    FROM 
        Alunos a
    JOIN 
        Matriculas m ON a.id = m.aluno_id
    JOIN 
        Turmas t ON m.turma_id = t.id
    JOIN 
        series s ON t.serie_id = s.id
    LEFT JOIN 
        ResponsaveisAlunos ra ON a.id = ra.aluno_id
    LEFT JOIN 
        Responsaveis r ON ra.responsavel_id = r.id
    LEFT JOIN
        Funcionarios f ON f.turma = t.id AND f.cargo = 'Professor@'
    WHERE 
        m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = 2024)
    AND 
        a.escola_id = 3
        AND s.id <= 7 -- Filtro para séries com ID menor ou igual a 7
    GROUP BY 
        a.id, a.nome, a.sexo, a.data_nascimento, s.nome, t.nome, t.turno, m.status, f.nome
    ORDER BY
        a.nome ASC;
    """

    cursor.execute(query)
    dados_aluno = cursor.fetchall()

    # Convertendo os dados para um DataFrame
    df = pd.DataFrame(dados_aluno)

    # Adicionando a coluna 'OBSERVACAO' com valor padrão vazio
    df['OBSERVACAO'] = ''
    # Define as margens conforme a ABNT
    margem_esquerda = 18  # Margem esquerda (0,5 polegadas)
    margem_direita = 18   # Margem direita (0,5 polegadas)
    margem_superior = 20   # Margem superior (0,5 polegadas)
    margem_inferior = 10   # Margem inferior (0,5 polegadas)

    # Cria um documento PDF com tamanho carta (letter) e margens definidas
    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=letter,
        rightMargin=margem_direita,
        leftMargin=margem_esquerda,
        topMargin=margem_superior,
        bottomMargin=margem_inferior
    )

    # Estilos de parágrafo
    styles = getSampleStyleSheet()
    estilo_normal = styles['Normal']
    
    # Adiciona um estilo de parágrafo justificado
    estilo_justificado = ParagraphStyle(
        'Justificado',
        parent=estilo_normal,
        alignment=4  # 0=left, 1=center, 2=right, 3=justify
    )
    # Função para formatar os números de telefone
    def formatar_telefone(telefone):
        return f"{telefone[:5]}-{telefone[5:]}"
    # Cria uma lista para armazenar os elementos do PDF
    elementos = []

    # Agrupar os dados por nome_serie, nome_turma e turno
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        
        # Adiciona a introdução ao documento
        elementos.append(Paragraph("Professor(a),", estilo_justificado))
        elementos.append(Spacer(0.1 * inch, 0.1 * inch))

        # Texto introdutório sobre o Ensino Fundamental
        texto_intro_fundamental = Paragraph(
            "O Ensino Fundamental é uma fase determinante na formação do discente, portanto, distinguir e garantir as competências e "
            "habilidades essenciais para os alunos é fundamental para o sucesso nessa etapa de ensino. O processo de avaliação é indispensável "
            "para que você conheça cada aluno de acordo com as suas especificidades e busque novas estratégias de ensino que garantam os "
            "direitos de seus alunos.", estilo_justificado)
        
        elementos.append(texto_intro_fundamental)
        elementos.append(Spacer(0.1 * inch, 0.1 * inch))

        # Texto sobre o Diário de Classe
        texto_diario_classe = Paragraph(
            "O Diário de Classe é uma ferramenta que subsidiará sua prática avaliativa, através de instrumentos de registro e "
            "acompanhamento que permitirão o monitoramento do avanço, ou não, dos alunos e, assim, fundamentar decisões que beneficiarão "
            "o desenvolvimento do processo de ensino e aprendizagem.", estilo_justificado)
        
        elementos.append(texto_diario_classe)
        elementos.append(Spacer(0.1 * inch, 0.1 * inch))

        # Adiciona as orientações ao documento usando enumerações
        elementos.append(Paragraph("ORIENTAÇÕES PARA USO DO DIÁRIO ESCOLAR", estilo_justificado))
        elementos.append(Spacer(0.1 * inch, 0.1 * inch))

        # Adicionando os itens da Enum ao PDF
        for index, orientacao in enumerate(Orientacao):
            valor = orientacao.value
            
            if isinstance(valor, tuple):
                descricao = valor[0]
                tabela_dados = valor[1]
                legenda_tabela = valor[2]
                paragrafo_nome = Paragraph(f"<b>{index + 1}. {orientacao.name.replace('_', ' ').title()}:</b> {descricao}", estilo_justificado)
                elementos.append(paragrafo_nome)

                # Criação da tabela se houver dados associados
                if tabela_dados:
                    tabela_estudantes = Table(tabela_dados)
                    # Estilo da tabela
                    tabela_estudantes.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('BACKGROUND', (0, 0), (-1, 1), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (1, 1), (-1,-1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (1, 1), (-1,-1), colors.beige),
                        ('GRID', (0, 0), (-1,-1), 1, colors.black),
                        ('SPAN', (1, 0), (7, 0)),
                        ('SPAN', (0, 0), (0, 1)), 
                    ]))
                    elementos.append(tabela_estudantes)

                    # Adiciona a legenda após a tabela
                    legenda_paragraph = Paragraph(legenda_tabela.replace("<br/>", "<br />"), estilo_justificado)
                    elementos.append(legenda_paragraph)

            else:
                paragrafo_nome = Paragraph(f"<b>{index + 1}. {orientacao.name.replace('_', ' ').title()}:</b> {valor}", estilo_justificado)
                elementos.append(paragrafo_nome)

            # Espaço entre os parágrafos
            elementos.append(Spacer(0.1 * inch, 0.1 * inch))
        
        elementos.append(PageBreak())

        # Extraindo o nome do professor da turma
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
        
        # Adicionar o título da turma
        elementos.append(Paragraph(f"<b>ANO LETIVO: {datetime.datetime.now().year} - PROFESSOR: {nome_professor} </b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=4)))
        elementos.append(Spacer(1, 0.1 * inch))
        elementos.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {'Vespertino' if {turno} == 'VESP' else 'Matutino'} - MAT. INICIAL: ______ MAT. PÓS CENSO: ______</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=4)))
        elementos.append(Spacer(1, 0.2 * inch))
        # Filtrar apenas os alunos com a situação "Ativo"
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']
        data = [['Nº', 'Nome do Aluno', 'Nascimento', 'Sexo', 'Telefones']]

        # Função para formatar os dados, garantindo que 'NASCIMENTO' não seja None
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            sexo = row['SEXO']
            
            # Verifica se a data de nascimento é None, e atribui uma string padrão se for o caso
            if row['NASCIMENTO']:
                nascimento = row['NASCIMENTO'].strftime('%d/%m/%Y')
            else:
                nascimento = "Data não disponível"
            
            # Obter os telefones, remover duplicatas e formatar
            telefones = row['TELEFONES']
            if telefones:
                telefones = list(set(telefones.split('/')))
            else:
                telefones = []
            telefones = [formatar_telefone(telefone) for telefone in telefones if telefone]
            telefones_str = ' / '.join(telefones) if telefones else 'N/A'

            data.append([row_num, nome, nascimento, sexo, telefones_str])

        # Preencher com linhas em branco até completar 35
        total_linhas_desejadas = 36
        linhas_atual = len(data) - 1  # Desconsiderando o cabeçalho

        for i in range(linhas_atual + 1, total_linhas_desejadas + 1):
            data.append([i, '', '', '', ''])  # Adiciona uma linha em branco

        # Criação da tabela
        table = Table(data)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ])
        table.setStyle(table_style)
        elementos.append(table)

        # Adicionar a quebra de página após a última tabela
        
        elementos.append(PageBreak())

    # Constrói o PDF
    doc.build(elementos)

# Função principal para criar o PDF temporário e abrir no programa padrão do sistema operacional
def main(nome_aluno: Optional[str] = None):
    try:
        gerenciador = GerenciadorDocumentosSistema()
        nome_documento = f"Diário de Classe - {datetime.datetime.now().strftime('%Y')}"
        arquivo_temp = None
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            criar_pdf(temp_file.name)
            arquivo_temp = temp_file.name

        if arquivo_temp:
            gerenciador.salvar_documento(
                tipo_documento=TIPO_DIARIO_CLASSE,
                nome_documento=nome_documento,
                arquivo_origem=arquivo_temp,
                referencia_aluno=nome_aluno
            )
            
            # Abre o arquivo PDF gerado
            if os.name == 'nt':  # Windows
                os.startfile(arquivo_temp)
            elif os.name == 'posix':  # Linux and MacOS
                os.system(f'open "{arquivo_temp}"' if sys.platform == 'darwin' else f'xdg-open "{arquivo_temp}"')

    except Exception as e:
        logger.exception("Erro ao gerar o diário de classe: %s", e)
        raise

# Chama a função principal para executar o script.
if __name__ == "__main__":
    main()