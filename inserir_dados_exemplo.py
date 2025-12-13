"""
Script completo para inserir dados de exemplo no banco de questões
"""
import sys
sys.path.insert(0, r'C:\gestao')

from banco_questoes.services import QuestaoService
from banco_questoes.models import Questao, TipoQuestao, StatusQuestao, ComponenteCurricular, AnoEscolar, QuestaoAlternativa
from banco_questoes.texto_base_service import TextoBaseService, TipoTextoBase, TextoBase
from conexao import conectar_bd
import config

# IDs para o sistema
escola_id = config.ESCOLA_ID
autor_id = 1

print("=" * 60)
print("INSERINDO DADOS DE EXEMPLO - BANCO DE QUESTOES")
print("=" * 60)

# 1. TEXTOS BASE
print("\n1. TEXTOS BASE")
print("-" * 60)

texto1 = TextoBase(
    titulo="Texto A - Sustentabilidade Ambiental",
    tipo=TipoTextoBase.TEXTO,
    conteudo=(
        "A sustentabilidade ambiental tornou-se um tema central nas discussoes globais. "
        "Preservar os recursos naturais e adotar praticas sustentaveis sao fundamentais "
        "para garantir um futuro melhor as proximas geracoes. O equilibrio entre desenvolvimento "
        "economico e conservacao ambiental e o grande desafio do seculo XXI."
    ),
    escola_id=escola_id,
    autor_id=autor_id
)
texto1_id = TextoBaseService.criar(texto1)
print(f"OK - Texto A criado (ID: {texto1_id})")

texto2 = TextoBase(
    titulo="Texto B - Tecnologia Digital",
    tipo=TipoTextoBase.TEXTO,
    conteudo=(
        "A tecnologia digital transformou profundamente a forma como nos comunicamos. "
        "As redes sociais conectam pessoas ao redor do mundo instantaneamente, mas tambem "
        "trazem desafios relacionados a privacidade e ao uso consciente da informacao. "
        "O desafio e encontrar o equilibrio entre beneficios e riscos."
    ),
    escola_id=escola_id,
    autor_id=autor_id
)
texto2_id = TextoBaseService.criar(texto2)
print(f"OK - Texto B criado (ID: {texto2_id})")

# 2. QUESTÕES DISSERTATIVAS
print("\n2. QUESTOES DISSERTATIVAS")
print("-" * 60)

q1 = Questao(
    enunciado="Com base nos textos A e B, identifique o tema central de cada um e compare-os quanto a relevancia para a sociedade atual.",
    tipo=TipoQuestao.DISSERTATIVA,
    componente_curricular=ComponenteCurricular.LINGUA_PORTUGUESA,
    ano_escolar=AnoEscolar.ANO_7,
    habilidade_bncc_codigo="EF69LP03",
    dificuldade="media",
    status=StatusQuestao.APROVADA,
    escola_id=escola_id,
    autor_id=autor_id
)
q1_id = QuestaoService.criar(q1)
print(f"OK - Questao dissertativa 1 (ID: {q1_id})")

q2 = Questao(
    enunciado="Escolha um dos textos e elabore tres perguntas sobre seu conteudo.",
    tipo=TipoQuestao.DISSERTATIVA,
    componente_curricular=ComponenteCurricular.LINGUA_PORTUGUESA,
    ano_escolar=AnoEscolar.ANO_7,
    habilidade_bncc_codigo="EF69LP03",
    dificuldade="media",
    status=StatusQuestao.APROVADA,
    escola_id=escola_id,
    autor_id=autor_id
)
q2_id = QuestaoService.criar(q2)
print(f"OK - Questao dissertativa 2 (ID: {q2_id})")

# 3. QUESTÕES MÚLTIPLA ESCOLHA
print("\n3. QUESTOES MULTIPLA ESCOLHA")
print("-" * 60)

q3 = Questao(
    enunciado="Segundo o Texto A, qual e o grande desafio do seculo XXI?",
    tipo=TipoQuestao.MULTIPLA_ESCOLHA,
    componente_curricular=ComponenteCurricular.LINGUA_PORTUGUESA,
    ano_escolar=AnoEscolar.ANO_7,
    habilidade_bncc_codigo="EF67LP08",
    dificuldade="facil",
    status=StatusQuestao.APROVADA,
    escola_id=escola_id,
    autor_id=autor_id
)
q3_id = QuestaoService.criar(q3)

conn = conectar_bd()
cursor = conn.cursor()

# Alternativas Q3
QuestaoService._inserir_alternativa(cursor, q3_id, QuestaoAlternativa(letra="A", texto="Aumentar a producao industrial", correta=False))
QuestaoService._inserir_alternativa(cursor, q3_id, QuestaoAlternativa(letra="B", texto="Equilibrar desenvolvimento economico e conservacao ambiental", correta=True))
QuestaoService._inserir_alternativa(cursor, q3_id, QuestaoAlternativa(letra="C", texto="Reduzir o uso de tecnologias", correta=False))
QuestaoService._inserir_alternativa(cursor, q3_id, QuestaoAlternativa(letra="D", texto="Ignorar problemas ambientais", correta=False))

conn.commit()
print(f"OK - Questao multipla escolha 1 (ID: {q3_id}) com 4 alternativas")

q4 = Questao(
    enunciado="De acordo com o Texto B, qual e o principal desafio da tecnologia digital?",
    tipo=TipoQuestao.MULTIPLA_ESCOLHA,
    componente_curricular=ComponenteCurricular.LINGUA_PORTUGUESA,
    ano_escolar=AnoEscolar.ANO_7,
    habilidade_bncc_codigo="EF67LP08",
    dificuldade="facil",
    status=StatusQuestao.APROVADA,
    escola_id=escola_id,
    autor_id=autor_id
)
q4_id = QuestaoService.criar(q4)

# Alternativas Q4
QuestaoService._inserir_alternativa(cursor, q4_id, QuestaoAlternativa(letra="A", texto="Eliminar as redes sociais", correta=False))
QuestaoService._inserir_alternativa(cursor, q4_id, QuestaoAlternativa(letra="B", texto="Encontrar equilibrio entre beneficios e riscos", correta=True))
QuestaoService._inserir_alternativa(cursor, q4_id, QuestaoAlternativa(letra="C", texto="Aumentar exposicao as telas", correta=False))
QuestaoService._inserir_alternativa(cursor, q4_id, QuestaoAlternativa(letra="D", texto="Proibir acesso de criancas", correta=False))

conn.commit()
print(f"OK - Questao multipla escolha 2 (ID: {q4_id}) com 4 alternativas")

q5 = Questao(
    enunciado='No Texto A, a palavra "sustentaveis" pode ser substituida por:',
    tipo=TipoQuestao.MULTIPLA_ESCOLHA,
    componente_curricular=ComponenteCurricular.LINGUA_PORTUGUESA,
    ano_escolar=AnoEscolar.ANO_7,
    habilidade_bncc_codigo="EF67LP32",
    dificuldade="facil",
    status=StatusQuestao.APROVADA,
    escola_id=escola_id,
    autor_id=autor_id
)
q5_id = QuestaoService.criar(q5)

# Alternativas Q5
QuestaoService._inserir_alternativa(cursor, q5_id, QuestaoAlternativa(letra="A", texto="Descartaveis", correta=False))
QuestaoService._inserir_alternativa(cursor, q5_id, QuestaoAlternativa(letra="B", texto="Renovaveis e duradouras", correta=True))
QuestaoService._inserir_alternativa(cursor, q5_id, QuestaoAlternativa(letra="C", texto="Caras e inacessiveis", correta=False))
QuestaoService._inserir_alternativa(cursor, q5_id, QuestaoAlternativa(letra="D", texto="Antigas e ultrapassadas", correta=False))

conn.commit()
cursor.close()
conn.close()

print(f"OK - Questao multipla escolha 3 (ID: {q5_id}) com 4 alternativas")

# RESUMO
print("\n" + "=" * 60)
print("RESUMO - DADOS INSERIDOS COM SUCESSO!")
print("=" * 60)
print("\nTEXTOS BASE:")
print(f"  ID {texto1_id}: Texto A - Sustentabilidade Ambiental")
print(f"  ID {texto2_id}: Texto B - Tecnologia Digital")
print("\nQUESTOES:")
print(f"  ID {q1_id}: Dissertativa - Comparacao de textos")
print(f"  ID {q2_id}: Dissertativa - Elaboracao de perguntas")
print(f"  ID {q3_id}: Multipla escolha - Desafio seculo XXI")
print(f"  ID {q4_id}: Multipla escolha - Tecnologia digital")
print(f"  ID {q5_id}: Multipla escolha - Vocabulario")
print("=" * 60)
print("\nPROXIMOS PASSOS:")
print("1. Execute: python main.py")
print("2. Clique em 'Banco de Questoes BNCC'")
print("3. Aba 'Montar Avaliacao':")
print("   - Titulo: Avaliacao de Lingua Portuguesa")
print("   - Componente: Lingua Portuguesa")
print("   - Ano: 7º ano")
print("   - Bimestre: 2º bimestre")
print("\n4. Secao 'Textos Base':")
print(f"   - Adicionar Texto A (ID {texto1_id}), questoes: {q1_id},{q2_id},{q3_id}")
print(f"   - Adicionar Texto B (ID {texto2_id}), questoes: {q1_id},{q2_id},{q4_id}")
print("\n5. Adicionar todas as 5 questoes na ordem")
print("6. Clicar em 'Gerar PDF'")
print("=" * 60)
