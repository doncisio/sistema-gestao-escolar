"""
Investiga o caso do Yan Davi Sampaio Correia
"""
import json
from db.connection import conectar_bd

# Buscar no GEDUC
print("="*80)
print("INVESTIGAÇÃO: YAN DAVI SAMPAIO CORREIA")
print("="*80)

with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Procurar Yan Davi no GEDUC
print("\n📂 DADOS NO GEDUC:")
print("-"*80)

encontrado = False
for turma in data.get('turmas', []):
    for aluno in turma.get('alunos', []):
        if 'YAN DAVI' in aluno['nome'].upper():
            encontrado = True
            print(f"\n✓ Aluno encontrado no GEDUC!")
            print(f"  Nome: {aluno['nome']}")
            print(f"  CPF: {aluno.get('cpf', 'SEM CPF')}")
            print(f"  Data Nascimento: {aluno.get('data_nascimento', 'SEM DATA')}")
            print(f"\n  TURMA GEDUC:")
            print(f"    ID: {turma.get('id')}")
            print(f"    Nome (inferido): {turma.get('nome', 'SEM NOME')}")
            
            # Calcular idade
            if aluno.get('data_nascimento'):
                ano_nasc = int(aluno['data_nascimento'].split('-')[0])
                idade_2026 = 2026 - ano_nasc
                print(f"    Idade em 2026: {idade_2026} anos")
            
            # Contar idades dos colegas de turma
            idades_turma = []
            for colega in turma.get('alunos', []):
                if colega.get('data_nascimento'):
                    ano = int(colega['data_nascimento'].split('-')[0])
                    idades_turma.append(2026 - ano)
            
            if idades_turma:
                from collections import Counter
                contador = Counter(idades_turma)
                print(f"\n  ANÁLISE DA TURMA:")
                print(f"    Total de alunos: {len(turma['alunos'])}")
                print(f"    Distribuição de idades: {dict(contador.most_common())}")
                print(f"    Idade mais comum: {contador.most_common(1)[0][0]} anos")

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
    WHERE a.nome LIKE '%YAN DAVI%'
    AND al.ano_letivo = 2026
""")

resultado = cursor.fetchone()

if resultado:
    print(f"\n✓ Aluno encontrado no Sistema Local!")
    print(f"  ID: {resultado['id']}")
    print(f"  Nome: {resultado['nome']}")
    print(f"  Data Nascimento: {resultado['data_nascimento']}")
    print(f"  Série: {resultado['serie']}")
    print(f"  Turma: {resultado['turma']}")
    print(f"  Turno: {resultado['turno']}")
    print(f"  Status: {resultado['status']}")
else:
    print("\n❌ Não encontrado no Sistema Local com matrícula em 2026")

cursor.close()
conn.close()

print("\n" + "="*80)

if not encontrado:
    print("⚠️  Aluno não encontrado no GEDUC - verifique o nome")
