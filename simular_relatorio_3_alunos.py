"""
Simular lógica do relatório para os 3 alunos
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

print("="*80)
print("SIMULANDO LÓGICA DO RELATÓRIO PARA OS 3 ALUNOS")
print("="*80)

# 1. Carregar GEDUC
print("\n1️⃣ Carregando GEDUC...")
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

alunos_geduc_dict = {}
for turma in data.get('turmas', []):
    turma_id = turma.get('id', '')
    turma_nome = turma.get('nome', '')
    serie_geduc = turma_nome if turma_nome else 'Série Não Identificada'
    
    for aluno in turma.get('alunos', []):
        nome_norm = normalizar_nome(aluno['nome'])
        cpf = aluno.get('cpf', '').strip()
        
        alunos_geduc_dict[nome_norm] = {
            'nome': aluno['nome'],
            'cpf': cpf,
            'turma_id_geduc': turma_id,
            'turma_nome_geduc': turma_nome,
            'serie_geduc': serie_geduc
        }
        
        if cpf:
            alunos_geduc_dict[cpf] = alunos_geduc_dict[nome_norm]

print(f"   ✓ {len(data.get('turmas', []))} turmas carregadas")

# 2. Buscar alunos do sistema local
print("\n2️⃣ Buscando alunos no Sistema Local...")
conn = conectar_bd()
cursor = conn.cursor(dictionary=True, buffered=True)

cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = 2026")
ano_2026 = cursor.fetchone()
ano_letivo_id = ano_2026['id']

print(f"   ✓ Ano Letivo 2026 ID: {ano_letivo_id}")

# Buscar os 3 alunos específicos
alunos_ids = [2830, 2828, 2829]

for aluno_id in alunos_ids:
    cursor.execute("""
        SELECT 
            a.id AS aluno_id,
            a.nome AS nome,
            a.cpf AS cpf,
            m.id AS matricula_id,
            m.status AS status_matricula,
            s.nome AS serie_local,
            t.nome AS turma_local,
            t.turno AS turno
        FROM Alunos a
        LEFT JOIN Matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s
        LEFT JOIN Turmas t ON m.turma_id = t.id
        LEFT JOIN series s ON t.serie_id = s.id
        WHERE a.escola_id = 60 AND a.id = %s
    """, (ano_letivo_id, aluno_id))
    
    aluno_local = cursor.fetchone()
    
    if not aluno_local:
        print(f"\n❌ Aluno ID {aluno_id} não encontrado!")
        continue
    
    print(f"\n{'='*80}")
    print(f"ALUNO: {aluno_local['nome']}")
    print(f"{'='*80}")
    
    nome_norm = normalizar_nome(aluno_local['nome'])
    cpf = aluno_local['cpf']
    
    print(f"📌 Dados Locais:")
    print(f"   ID: {aluno_local['aluno_id']}")
    print(f"   Nome: {aluno_local['nome']}")
    print(f"   CPF: {cpf}")
    print(f"   Matrícula ID: {aluno_local['matricula_id']}")
    print(f"   Status: {aluno_local['status_matricula']}")
    print(f"   Série: {aluno_local['serie_local']}")
    print(f"   Turma: {aluno_local['turma_local']}")
    
    # Buscar aluno no GEDUC (lógica do relatório)
    aluno_geduc = None
    
    # Buscar por CPF primeiro
    if cpf and cpf in alunos_geduc_dict:
        aluno_geduc = alunos_geduc_dict[cpf]
        print(f"\n📌 Match GEDUC: POR CPF")
    # Buscar por nome
    elif nome_norm in alunos_geduc_dict:
        aluno_geduc = alunos_geduc_dict[nome_norm]
        print(f"\n📌 Match GEDUC: POR NOME")
    
    if aluno_geduc:
        print(f"   Nome GEDUC: {aluno_geduc['nome']}")
        print(f"   CPF GEDUC: {aluno_geduc['cpf']}")
        print(f"   Série GEDUC: {aluno_geduc['serie_geduc']}")
        print(f"   Turma GEDUC: {aluno_geduc['turma_nome_geduc']}")
        
        # Lógica do relatório
        tem_matricula = aluno_local['matricula_id'] is not None
        
        print(f"\n🔍 ANÁLISE DO RELATÓRIO:")
        print(f"   tem_matricula = {tem_matricula}")
        
        if tem_matricula:
            serie_local = aluno_local['serie_local']
            serie_geduc = aluno_geduc['serie_geduc']
            
            print(f"   Série Local: '{serie_local}'")
            print(f"   Série GEDUC: '{serie_geduc}'")
            print(f"   Séries iguais? {serie_local == serie_geduc}")
            
            if serie_local != serie_geduc:
                print(f"   ⚠️ SERIA CLASSIFICADO COMO: DIVERGENTE")
            else:
                print(f"   ✅ SERIA CLASSIFICADO COMO: OK (não aparece no relatório)")
        else:
            print(f"   ❌ SERIA CLASSIFICADO COMO: SEM MATRÍCULA")
    else:
        print(f"\n❌ Aluno NÃO encontrado no GEDUC")

cursor.close()
conn.close()

print("\n" + "="*80)
