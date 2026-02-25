"""
Script para detectar mudanças entre a comparação antiga e a nova no GEDUC
Identifica quem entrou e quem saiu
"""
import json
import unicodedata
from db.connection import conectar_bd

def normalizar_nome_comparacao(nome):
    """Remove acentos, espaços extras e converte para maiúsculo"""
    if not nome:
        return ""
    nome = ' '.join(nome.split())
    nfkd = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return nome_sem_acento.upper()

# Lista dos 36 alunos que estavam no GEDUC na última verificação
alunos_geduc_anterior = [
    "ANA BEATRIZ MARQUES SOARES",
    "ANA CLARA SANTOS SILVA",
    "ANA CLARA SILVA DE ALBUQUERQUE",
    "ANA JULIA LOBATO CHEVES",
    "ANA JULIA RIBEIRO SIMPLICIO",
    "ARYELLA LOURENCO SILVA",
    "BENJAMIN BORGES MARTINS",
    "BRUNA RAYANE FRAZAO ARAUJO",
    "CANDIDA ROBERTA DA SILVA BORALHO",
    "DEYVISON MARCELO CARNEIRO FERREIRA",
    "ENZO DE SOUZA FURTADO",
    "ESTHER DE JESUS MENDES",
    "FERNANDO GABRIEL SOUSA DA SILVA",
    "GABRIELLY SILVA DO NASCIMENTO",
    "GLENDA ELIZA DE OLIVEIRA RIBEIRO",
    "GUILHERME MARTINS DE OLIVEIRA",
    "HENZO HENRIQUE DOS SANTOS SERRA",
    "IGOR BENJAMIN RIBEIRO DE OLIVEIRA",
    "ISADORA PEREIRA MOTA",
    "JOAO HELIO GONCALVES BARROS",
    "JOAO MIGUEL DA CONCEICAO",
    "JOAO MIGUEL DOS SANTOS VIEIRA",
    "KAUAN ARTHUR DOS SANTOS PORTO",
    "LARA CECILIA MENDES DE ALMEIDA",
    "MARCELLY VITORIA SANTOS DA SILVA",
    "MARIA HELENA VERACY BISPO OLIVEIRA",
    "MARIA ISABELLY FERREIRA SENA",
    "MARIA JULIA BATISTA DO NASCIMENTO",
    "MIKAEL CABRAL LOPES",
    "NATALIA DA SILVA ALVES",
    "NOAH BENJAMIN FERNANDES DOS SANTOS",
    "PIETRA BRANDAO NASCIMENTO",
    "REBECA SOUSA MARTINS",
    "RITA LARISSA MARTINS DA SILVA",
    "SARAH LOPES BARBOSA",
    "YASMIN YSABELLY LOPES MONTEIRO"
]

# Normalizar lista anterior
anterior_norm = {normalizar_nome_comparacao(nome): nome for nome in alunos_geduc_anterior}

# Buscar alunos do sistema local (matriculados em 2026)
conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# Primeiro, obter o ID do ano letivo 2026
cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2026")
ano_letivo_row = cursor.fetchone()
ano_letivo_id = ano_letivo_row['id'] if ano_letivo_row else None

if not ano_letivo_id:
    print("❌ Erro: Ano letivo 2026 não encontrado!")
    cursor.close()
    conn.close()
    exit(1)

cursor.execute("""
    SELECT DISTINCT a.id, a.nome
    FROM Alunos a
    INNER JOIN Matriculas m ON a.id = m.aluno_id
    WHERE m.ano_letivo_id = %s
    ORDER BY a.nome
""", (ano_letivo_id,))

alunos_local = {normalizar_nome_comparacao(row['nome']): row['nome'] for row in cursor.fetchall()}

# Carregar alunos ATUAIS do GEDUC
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alunos_geduc_atual = []
for turma in data.get('turmas', []):
    alunos_geduc_atual.extend(turma.get('alunos', []))

# Filtrar apenas os que não estão no sistema local (os "novos")
novos_geduc_atual = []
for aluno in alunos_geduc_atual:
    nome_norm = normalizar_nome_comparacao(aluno['nome'])
    if nome_norm not in alunos_local:
        novos_geduc_atual.append({
            'nome': aluno['nome'].strip(),
            'nome_norm': nome_norm,
            'cpf': aluno.get('cpf', 'SEM CPF')
        })

atual_norm = {a['nome_norm']: a for a in novos_geduc_atual}

print("="*80)
print("DETECTOR DE MUDANÇAS NO GEDUC")
print("="*80)
print(f"\nAlunos novos na verificação ANTERIOR: {len(anterior_norm)}")
print(f"Alunos novos na verificação ATUAL: {len(atual_norm)}")

# Identificar quem SAIU (estava na lista anterior mas não está na atual)
saiu = []
for nome_norm, nome_orig in anterior_norm.items():
    if nome_norm not in atual_norm:
        saiu.append(nome_orig)

# Identificar quem ENTROU (está na lista atual mas não estava na anterior)
entrou = []
for nome_norm, dados in atual_norm.items():
    if nome_norm not in anterior_norm:
        entrou.append(dados)

print("\n" + "="*80)
print("MUDANÇAS DETECTADAS")
print("="*80)

if saiu:
    print(f"\n❌ SAÍRAM ({len(saiu)} alunos):")
    for nome in sorted(saiu):
        print(f"   - {nome}")
else:
    print("\n✓ Nenhum aluno saiu")

if entrou:
    print(f"\n🆕 ENTRARAM ({len(entrou)} alunos):")
    for dados in sorted(entrou, key=lambda x: x['nome']):
        print(f"   - {dados['nome']} (CPF: {dados['cpf']})")
else:
    print("\n✓ Nenhum aluno novo entrou")

print("\n" + "="*80)
print("RESUMO")
print("="*80)
print(f"Diferença líquida: {len(entrou) - len(saiu):+d} alunos")

if len(saiu) == 0 and len(entrou) == 0:
    print("\n✅ Nenhuma mudança detectada no GEDUC")
elif len(saiu) == len(entrou) == 1:
    print(f"\n⚠️  1 aluno saiu e 1 aluno entrou (substituição)")
else:
    print(f"\n⚠️  {len(saiu)} saíram, {len(entrou)} entraram")

cursor.close()
conn.close()
