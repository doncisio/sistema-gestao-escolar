"""
Verifica quantos alunos do GEDUC já estão cadastrados no sistema
(com ou sem matrícula)
"""
import json
import unicodedata
from db.connection import conectar_bd

def normalizar_nome(nome):
    """Remove acentos e normaliza"""
    if not nome:
        return ""
    nfkd = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return nome_sem_acento.upper().strip()

# Carregar alunos do GEDUC
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alunos_geduc = []
for turma in data.get('turmas', []):
    for aluno in turma.get('alunos', []):
        aluno['nome_normalizado'] = normalizar_nome(aluno['nome'])
        alunos_geduc.append(aluno)

# Buscar todos os alunos do sistema local (com ou sem matrícula)
conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT id, nome, cpf, data_nascimento
    FROM Alunos
    WHERE escola_id = 60
""")

alunos_local = cursor.fetchall()

# Criar dicionário por nome e CPF
alunos_local_por_nome = {}
alunos_local_por_cpf = {}

for aluno in alunos_local:
    nome_norm = normalizar_nome(aluno['nome'])
    alunos_local_por_nome[nome_norm] = aluno
    
    if aluno['cpf']:
        alunos_local_por_cpf[aluno['cpf']] = aluno

# Comparar
cadastrados = []
nao_cadastrados = []

for aluno_geduc in alunos_geduc:
    nome_norm = aluno_geduc['nome_normalizado']
    cpf = aluno_geduc.get('cpf', '').strip()
    
    encontrado = False
    
    # Verificar por CPF primeiro
    if cpf and cpf in alunos_local_por_cpf:
        encontrado = True
        aluno_local = alunos_local_por_cpf[cpf]
    # Verificar por nome
    elif nome_norm in alunos_local_por_nome:
        encontrado = True
        aluno_local = alunos_local_por_nome[nome_norm]
    
    if encontrado:
        # Verificar se tem matrícula em 2026
        cursor.execute("""
            SELECT m.id, m.status, t.nome as turma
            FROM Matriculas m
            LEFT JOIN Turmas t ON m.turma_id = t.id
            LEFT JOIN AnosLetivos a ON m.ano_letivo_id = a.id
            WHERE m.aluno_id = %s AND a.ano_letivo = 2026
        """, (aluno_local['id'],))
        
        matricula = cursor.fetchone()
        
        cadastrados.append({
            'nome_geduc': aluno_geduc['nome'],
            'nome_local': aluno_local['nome'],
            'id': aluno_local['id'],
            'cpf': cpf or 'SEM CPF',
            'tem_matricula': bool(matricula),
            'status_matricula': matricula['status'] if matricula else None
        })
    else:
        nao_cadastrados.append({
            'nome': aluno_geduc['nome'],
            'cpf': cpf or 'SEM CPF'
        })

cursor.close()
conn.close()

# Relatório
print("="*80)
print("ANÁLISE: ALUNOS DO GEDUC NO SISTEMA LOCAL")
print("="*80)
print(f"\nTotal de alunos no GEDUC: {len(alunos_geduc)}")
print(f"Total de alunos no sistema local: {len(alunos_local)}")
print()
print("="*80)
print("SITUAÇÃO DOS ALUNOS DO GEDUC")
print("="*80)
print(f"✅ Cadastrados no sistema: {len(cadastrados)}")

com_matricula = sum(1 for a in cadastrados if a['tem_matricula'])
sem_matricula = sum(1 for a in cadastrados if not a['tem_matricula'])

print(f"   └─ Com matrícula em 2026: {com_matricula}")
print(f"   └─ SEM matrícula em 2026: {sem_matricula} ⚠️")
print()
print(f"❌ NÃO cadastrados: {len(nao_cadastrados)}")
print()

if sem_matricula > 0:
    print("="*80)
    print(f"ALUNOS CADASTRADOS SEM MATRÍCULA EM 2026 ({sem_matricula})")
    print("="*80)
    for idx, aluno in enumerate([a for a in cadastrados if not a['tem_matricula']], 1):
        print(f"{idx:02d}. {aluno['nome_local']} (ID: {aluno['id']})")
        if aluno['nome_local'] != aluno['nome_geduc']:
            print(f"    Nome no GEDUC: {aluno['nome_geduc']}")
    print()

if nao_cadastrados:
    print("="*80)
    print(f"ALUNOS NÃO CADASTRADOS ({len(nao_cadastrados)})")
    print("="*80)
    for idx, aluno in enumerate(nao_cadastrados, 1):
        print(f"{idx:02d}. {aluno['nome']}")
        print(f"    CPF: {aluno['cpf']}")
    print()

print("="*80)
print("PRÓXIMOS PASSOS")
print("="*80)
if sem_matricula > 0:
    print(f"📝 Criar matrículas para {sem_matricula} alunos já cadastrados")
if nao_cadastrados:
    print(f"👤 Cadastrar {len(nao_cadastrados)} alunos que faltam")
print("="*80)
