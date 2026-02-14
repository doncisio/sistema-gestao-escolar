"""
Investigar relação entre matrículas e ano letivo
"""
from db.connection import conectar_bd

conexao = conectar_bd()
cursor = conexao.cursor(dictionary=True, buffered=True)

print("="*80)
print("INVESTIGANDO ANO LETIVO E MATRÍCULAS")
print("="*80)

# 1. Verificar ID do ano letivo 2026
print("\n1️⃣ Buscando ID do ano letivo 2026...")
cursor.execute("SELECT id, ano_letivo FROM AnosLetivos WHERE ano_letivo = 2026")
ano_2026 = cursor.fetchone()

if ano_2026:
    print(f"   ✓ Ano Letivo 2026 encontrado:")
    print(f"     ID: {ano_2026['id']}")
    print(f"     Ano: {ano_2026['ano_letivo']}")
    ano_letivo_id = ano_2026['id']
else:
    print("   ❌ Ano letivo 2026 NÃO encontrado!")
    cursor.close()
    conexao.close()
    exit()

# 2. Verificar matrículas dos 3 alunos
print(f"\n2️⃣ Verificando matrículas dos 3 alunos com ano_letivo_id = {ano_letivo_id}...")

alunos = [
    ('John Miguel Moreira Monteiro', 2830, 1476),
    ('Mauricio Silva Miranda', 2828, 1472),
    ('Murilo Silva Miranda', 2829, 1471)
]

for nome, aluno_id, matricula_id in alunos:
    print(f"\n   📌 {nome} (Aluno ID: {aluno_id}, Matrícula ID: {matricula_id})")
    
    # Verificar matrícula
    cursor.execute("""
        SELECT *
        FROM Matriculas
        WHERE id = %s
    """, (matricula_id,))
    
    mat = cursor.fetchone()
    
    if mat:
        print(f"      ✓ Matrícula encontrada:")
        print(f"        Dados: {mat}")
    else:
        print(f"      ❌ Matrícula {matricula_id} não encontrada!")

# 3. Testar a query exata usada pelo relatório
print(f"\n3️⃣ Testando query do relatório para os 3 alunos...")

for nome, aluno_id, _ in alunos:
    print(f"\n   📌 {nome}")
    
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
    
    resultado = cursor.fetchone()
    
    if resultado:
        print(f"      Resultado da query:")
        print(f"        - Aluno ID: {resultado['aluno_id']}")
        print(f"        - Nome: {resultado['nome']}")
        print(f"        - Matrícula ID: {resultado['matricula_id']}")
        print(f"        - Status: {resultado['status_matricula']}")
        print(f"        - Série: {resultado['serie_local']}")
        print(f"        - Turma: {resultado['turma_local']}")
        
        if resultado['matricula_id'] is None:
            print(f"        ❌ PROBLEMA: matricula_id é NULL!")
            print(f"           Isso faz o relatório considerar 'SEM MATRÍCULA'")

cursor.close()
conexao.close()

print("\n" + "="*80)
