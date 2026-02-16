"""
Análise completa: por que 34 ao invés de 36?
"""
import json
from db.connection import conectar_bd
import unicodedata

def normalizar_nome_comparacao(nome):
    """Remove acentos, espaços extras e converte para maiúsculo"""
    if not nome:
        return ""
    # Remover espaços extras
    nome = ' '.join(nome.split())
    nfkd = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return nome_sem_acento.upper()

# Carregar alunos do GEDUC
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alunos_geduc = []
for turma in data.get('turmas', []):
    alunos_geduc.extend(turma.get('alunos', []))

# Conectar ao banco e buscar alunos do sistema local
conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT nome FROM Alunos")
alunos_local = {normalizar_nome_comparacao(row['nome']): row['nome'] for row in cursor.fetchall()}

print("="*80)
print("ANÁLISE COMPLETA")
print("="*80)
print(f"\nTotal no GEDUC: {len(alunos_geduc)}")
print(f"Total no sistema local: {len(alunos_local)}")

# Filtrar alunos que estão apenas no GEDUC
apenas_geduc = []
for aluno in alunos_geduc:
    nome_norm = normalizar_nome_comparacao(aluno['nome'])
    if nome_norm not in alunos_local:
        apenas_geduc.append(aluno)

print(f"\n✅ Apenas no GEDUC (novos): {len(apenas_geduc)}")

print("\n" + "="*80)
print("LISTA DE ALUNOS NOVOS NO GEDUC")
print("="*80)
for i, aluno in enumerate(sorted(apenas_geduc, key=lambda x: x['nome']), 1):
    nome = aluno['nome']
    cpf = aluno.get('cpf', 'SEM CPF')
    print(f"{i:02d}. {nome.strip()} - CPF: {cpf}")

cursor.close()
conn.close()
