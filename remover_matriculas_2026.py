"""
Script para remover matrículas de 2026 dos alunos que saíram
"""
from db.connection import conectar_bd

# IDs dos alunos que não foram matriculados em 2026
alunos_para_remover = [
    {'id': 2655, 'nome': 'Alícia Araújo do Nascimento', 'cpf': '638.096.473-81'},
    {'id': 2860, 'nome': 'João Helio Goncalves Barros', 'cpf': '628.922.383-66'},
    {'id': 927, 'nome': 'Luis Carlos da Conceição Souza', 'cpf': 'SEM CPF'}
]

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

print("="*80)
print("REMOÇÃO DE MATRÍCULAS 2026 - ALUNOS NÃO MATRICULADOS NO GEDUC")
print("="*80)

# Buscar ID do ano letivo 2026
cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2026")
ano_letivo_row = cursor.fetchone()

if not ano_letivo_row:
    print("❌ Erro: Ano letivo 2026 não encontrado!")
    cursor.close()
    conn.close()
    exit(1)

ano_letivo_id = ano_letivo_row['id']
print(f"📅 Ano Letivo 2026 - ID: {ano_letivo_id}")

# Verificar matrículas existentes
print(f"\n🔍 Verificando matrículas existentes...")
print("-"*80)

matriculas_para_deletar = []

for aluno in alunos_para_remover:
    cursor.execute("""
        SELECT m.id, m.aluno_id, a.nome, m.turma_id, t.nome as nome_turma,
               m.data_matricula, m.status
        FROM Matriculas m
        JOIN Alunos a ON m.aluno_id = a.id
        LEFT JOIN Turmas t ON m.turma_id = t.id
        WHERE m.aluno_id = %s AND m.ano_letivo_id = %s
    """, (aluno['id'], ano_letivo_id))
    
    matriculas = cursor.fetchall()
    
    if matriculas:
        print(f"\n👤 {aluno['nome']} (ID: {aluno['id']})")
        print(f"   CPF: {aluno['cpf']}")
        print(f"   ⚠️  {len(matriculas)} matrícula(s) encontrada(s) em 2026:")
        
        for mat in matriculas:
            turma_display = mat['nome_turma'] if mat['nome_turma'] else f"Turma ID {mat['turma_id']}"
            print(f"      - Matrícula ID: {mat['id']}")
            print(f"        Turma: {turma_display}")
            print(f"        Data: {mat['data_matricula']}")
            print(f"        Status: {mat['status']}")
            matriculas_para_deletar.append({
                'matricula_id': mat['id'],
                'aluno_nome': mat['nome'],
                'aluno_id': mat['aluno_id'],
                'turma': turma_display
            })
    else:
        print(f"\n👤 {aluno['nome']} (ID: {aluno['id']})")
        print(f"   ✓ Nenhuma matrícula em 2026")

if not matriculas_para_deletar:
    print("\n✅ Nenhuma matrícula para remover!")
    print("="*80)
    cursor.close()
    conn.close()
    exit(0)

# Resumo
print("\n" + "="*80)
print("RESUMO DAS MATRÍCULAS A SEREM REMOVIDAS")
print("="*80)
print(f"\n📊 Total: {len(matriculas_para_deletar)} matrícula(s)")
print()

for i, mat in enumerate(matriculas_para_deletar, 1):
    print(f"{i}. {mat['aluno_nome']} (ID Aluno: {mat['aluno_id']})")
    print(f"   Matrícula ID: {mat['matricula_id']}")
    print(f"   Turma: {mat['turma']}")
    print()

print("⚠️  ATENÇÃO: Esta operação irá DELETAR as matrículas acima!")
print("⚠️  Os registros da tabela Alunos NÃO serão afetados.")
print()

confirmacao = input("❓ Confirma a remoção? (S/N): ")

if confirmacao.upper() != 'S':
    print("\n❌ Operação cancelada!")
    print("="*80)
    cursor.close()
    conn.close()
    exit(0)

# Executar remoção
print("\n🔄 Removendo matrículas...")

removidas = 0
erros = 0

for mat in matriculas_para_deletar:
    try:
        cursor.execute("""
            DELETE FROM Matriculas WHERE id = %s
        """, (mat['matricula_id'],))
        
        print(f"✅ Matrícula {mat['matricula_id']} removida - {mat['aluno_nome']}")
        removidas += 1
        
    except Exception as e:
        print(f"❌ Erro ao remover matrícula {mat['matricula_id']}: {e}")
        erros += 1

# Commit
if removidas > 0:
    conn.commit()
    print(f"\n✅ {removidas} matrícula(s) removida(s) com sucesso!")
else:
    print(f"\n⚠️  Nenhuma matrícula foi removida")

if erros > 0:
    print(f"❌ {erros} erro(s) durante a operação")

# Verificação final
print("\n" + "="*80)
print("VERIFICAÇÃO FINAL")
print("="*80)

for aluno in alunos_para_remover:
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM Matriculas m
        WHERE m.aluno_id = %s AND m.ano_letivo_id = %s
    """, (aluno['id'], ano_letivo_id))
    
    result = cursor.fetchone()
    total = result['total']
    
    status = "✅ OK" if total == 0 else f"⚠️  Ainda tem {total} matrícula(s)"
    print(f"{aluno['nome']}: {status}")

print("="*80)

cursor.close()
conn.close()
