"""
Investiga Alessandro Pereira Alves
"""
import json
from db.connection import conectar_bd
import unicodedata

def normalizar_nome(nome):
    """Remove acentos e normaliza"""
    if not nome:
        return ""
    nfkd = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return nome_sem_acento.upper().strip()

print("="*80)
print("INVESTIGAÇÃO: ALESSANDRO PEREIRA ALVES")
print("="*80)

# Buscar no GEDUC
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("\n📂 DADOS NO GEDUC:")
print("-"*80)

nome_procurado = normalizar_nome("Alessandro Pereira Alves")

for turma in data.get('turmas', []):
    for aluno in turma.get('alunos', []):
        nome_aluno = normalizar_nome(aluno['nome'])
        if nome_aluno == nome_procurado:
            print(f"\n✓ Aluno encontrado no GEDUC!")
            print(f"  Nome original: {aluno['nome']}")
            print(f"  Nome normalizado: {nome_aluno}")
            print(f"  CPF: {aluno.get('cpf', 'SEM CPF')}")
            print(f"  Data Nascimento: {aluno.get('data_nascimento', 'SEM DATA')}")
            print(f"\n  TURMA GEDUC:")
            print(f"    ID: {turma.get('id')}")
            print(f"    Nome: '{turma.get('nome', 'SEM NOME')}'")
            
            # Calcular idade
            if aluno.get('data_nascimento'):
                ano_nasc = int(aluno['data_nascimento'].split('-')[0])
                idade_2026 = 2026 - ano_nasc
                print(f"    Idade em 2026: {idade_2026} anos")

# Buscar no Sistema Local
print("\n📂 DADOS NO SISTEMA LOCAL:")
print("-"*80)

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT 
        a.id, a.nome, a.data_nascimento,
        m.status,
        s.nome AS serie,
        t.nome AS turma,
        t.turno
    FROM Alunos a
    LEFT JOIN Matriculas m ON a.id = m.aluno_id
    LEFT JOIN AnosLetivos al ON m.ano_letivo_id = al.id
    LEFT JOIN Turmas t ON m.turma_id = t.id
    LEFT JOIN series s ON t.serie_id = s.id
    WHERE a.nome LIKE '%ALESSANDRO%PEREIRA%'
    AND al.ano_letivo = 2026
""")

resultado = cursor.fetchone()

if resultado:
    print(f"\n✓ Aluno encontrado no Sistema Local!")
    print(f"  ID: {resultado['id']}")
    print(f"  Nome: {resultado['nome']}")
    print(f"  Série: {resultado['serie']}")
    print(f"  Turma: {resultado['turma']}")
    print(f"  Status: {resultado['status']}")

cursor.close()
conn.close()

print("\n" + "="*80)
print("ANÁLISE")
print("="*80)

# Verificar quais turmas são 2º Ano no GEDUC
print("\nTurmas 2º Ano no GEDUC:")
for turma in data.get('turmas', []):
    if turma.get('nome') == '2º Ano':
        print(f"  Turma ID {turma['id']}: {turma['nome']} - {len(turma['alunos'])} alunos")
