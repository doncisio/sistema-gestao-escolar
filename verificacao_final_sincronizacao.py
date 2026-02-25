from db.connection import conectar_bd

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# Buscar ID do ano letivo 2026
cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2026")
ano_letivo_id = cursor.fetchone()['id']

print("="*80)
print("✅ VERIFICAÇÃO FINAL - SINCRONIZAÇÃO COM GEDUC")
print("="*80)

# 1. Alunos que foram removidos
alunos_removidos = [
    {'id': 2655, 'nome': 'Alícia Araújo do Nascimento'},
    {'id': 2860, 'nome': 'João Helio Goncalves Barros'},
    {'id': 927, 'nome': 'Luis Carlos da Conceição Souza'}
]

print("\n❌ ALUNOS SEM MATRÍCULA EM 2026 (removidos):")
print("-"*80)
for aluno in alunos_removidos:
    cursor.execute("""
        SELECT COUNT(*) as total FROM Matriculas 
        WHERE aluno_id = %s AND ano_letivo_id = %s
    """, (aluno['id'], ano_letivo_id))
    
    total = cursor.fetchone()['total']
    status = "✅ OK" if total == 0 else f"❌ ERRO: {total} matrícula(s)"
    print(f"   {aluno['nome']}: {status}")

# 2. Aluno importado
print("\n✅ ALUNO IMPORTADO DO GEDUC:")
print("-"*80)
cursor.execute("""
    SELECT a.id, a.nome, a.cpf, 
           COUNT(m.id) as total_matriculas_2026
    FROM Alunos a
    LEFT JOIN Matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s
    WHERE a.id = 2924
    GROUP BY a.id
""", (ano_letivo_id,))

karllos = cursor.fetchone()
if karllos:
    print(f"   {karllos['nome']}")
    print(f"   CPF: {karllos['cpf']}")
    print(f"   Matrículas em 2026: {karllos['total_matriculas_2026']}")
    if karllos['total_matriculas_2026'] == 0:
        print(f"   ⚠️  Precisa matricular em uma turma")
    else:
        print(f"   ✅ Já matriculado")

# 3. Total geral de matriculados em 2026
cursor.execute("""
    SELECT COUNT(DISTINCT m.aluno_id) as total
    FROM Matriculas m
    WHERE m.ano_letivo_id = %s
""", (ano_letivo_id,))

total_matriculados = cursor.fetchone()['total']

print("\n📊 RESUMO:")
print("-"*80)
print(f"   Total de alunos matriculados em 2026: {total_matriculados}")
print(f"   Esperado no GEDUC: 295 alunos")
print(f"   Diferença: {total_matriculados - 295:+d} alunos")

if total_matriculados == 295:
    print("\n   ✅ Sistema local sincronizado com GEDUC!")
elif total_matriculados == 294:
    print("\n   ⚠️  Falta 1 aluno (Karllos Augusto precisa ser matriculado)")
else:
    print(f"\n   ⚠️  Verificar diferença de {abs(total_matriculados - 295)} alunos")

print("="*80)

cursor.close()
conn.close()
