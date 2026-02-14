"""
Investigar histórico escolar de Ana Clara
"""
from db.connection import conectar_bd

conexao = conectar_bd()
cursor = conexao.cursor(dictionary=True, buffered=True)

print("="*80)
print("INVESTIGAÇÃO: ANA CLARA SILVA DE ALBUQUERQUE")
print("="*80)

# Verificar o registro atual (ID 2922)
print("\n📌 Verificando registro atual (ID 2922)...")
cursor.execute("""
    SELECT id, nome, cpf, data_nascimento
    FROM Alunos
    WHERE id = 2922
""")
ana_atual = cursor.fetchone()

if ana_atual:
    print(f"\n   ✓ Registro encontrado:")
    print(f"     ID: {ana_atual['id']}")
    print(f"     Nome: {ana_atual['nome']}")
    print(f"     CPF: {ana_atual['cpf']}")
    print(f"     Data Nasc: {ana_atual['data_nascimento']}")
else:
    print("   ❌ Registro não encontrado!")
    cursor.close()
    conexao.close()
    exit()

# Verificar se o registro excluído ainda existe
print("\n📌 Verificando registro excluído (ID 2058)...")
cursor.execute("""
    SELECT COUNT(*) as total
    FROM Alunos
    WHERE id = 2058
""")
result = cursor.fetchone()

if result['total'] > 0:
    print(f"   ⚠️ ATENÇÃO: Registro 2058 AINDA EXISTE!")
else:
    print(f"   ✓ Registro 2058 foi excluído conforme esperado")

# Verificar histórico escolar atual do ID 2922
print("\n📌 Histórico escolar atual de Ana Clara (ID 2922)...")
cursor.execute("""
    SELECT 
        h.id,
        h.aluno_id,
        al.ano_letivo,
        s.nome as serie,
        d.nome as disciplina,
        h.media,
        h.conceito
    FROM historico_escolar h
    LEFT JOIN AnosLetivos al ON h.ano_letivo_id = al.id
    LEFT JOIN series s ON h.serie_id = s.id
    LEFT JOIN Disciplinas d ON h.disciplina_id = d.id
    WHERE h.aluno_id = 2922
    ORDER BY al.ano_letivo, d.nome
""")

historico_atual = cursor.fetchall()

if historico_atual:
    print(f"\n   ✓ {len(historico_atual)} registro(s) de histórico encontrado(s):")
    anos = set()
    for hist in historico_atual:
        anos.add(hist['ano_letivo'])
    print(f"   Anos letivos: {sorted(anos) if anos else 'N/A'}")
    print(f"\n   Primeiros 5 registros:")
    for i, hist in enumerate(historico_atual[:5]):
        ano = hist['ano_letivo'] if hist['ano_letivo'] else 'N/A'
        serie = hist['serie'] if hist['serie'] else 'N/A'
        disc = hist['disciplina'] if hist['disciplina'] else 'N/A'
        media = hist['media'] if hist['media'] else '-'
        conceito = hist['conceito'] if hist['conceito'] else '-'
        print(f"     {i+1}. Ano: {ano} | Série: {serie} | {disc} | Média: {media} | Conceito: {conceito}")
else:
    print(f"   ❌ Nenhum histórico escolar encontrado para ID 2922")

# Verificar se existe histórico escolar órfão (sem aluno)
print("\n📌 Verificando histórico escolar do ID 2058 (excluído)...")
cursor.execute("""
    SELECT COUNT(*) as total
    FROM historico_escolar
    WHERE aluno_id = 2058
""")
result_hist = cursor.fetchone()

if result_hist['total'] > 0:
    print(f"   ⚠️ ATENÇÃO: Ainda existem {result_hist['total']} registros de histórico com aluno_id = 2058!")
    print(f"   Isso significa que a exclusão não foi completada ou foi revertida.")
else:
    print(f"   ✓ Histórico escolar do ID 2058 foi excluído (18 registros)")

# Verificar matrícula atual
print("\n📌 Matrícula 2026 de Ana Clara (ID 2922)...")
cursor.execute("""
    SELECT 
        m.id as matricula_id,
        m.status,
        s.nome as serie,
        t.nome as turma
    FROM Matriculas m
    LEFT JOIN Turmas t ON m.turma_id = t.id
    LEFT JOIN series s ON t.serie_id = s.id
    LEFT JOIN AnosLetivos al ON m.ano_letivo_id = al.id
    WHERE m.aluno_id = 2922 AND al.ano_letivo = 2026
""")

matricula = cursor.fetchone()

if matricula:
    print(f"\n   ✓ Matrícula encontrada:")
    print(f"     ID: {matricula['matricula_id']}")
    print(f"     Série: {matricula['serie']}")
    print(f"     Turma: {matricula['turma']}")
    print(f"     Status: {matricula['status']}")
else:
    print(f"   ❌ Nenhuma matrícula em 2026 encontrada")

print("\n" + "="*80)
print("CONCLUSÃO")
print("="*80)
print("\n⚠️ O histórico escolar do registro duplicado (ID 2058) foi permanentemente")
print("   excluído quando o registro foi removido.")
print("\nℹ️ IMPORTANTE:")
print("   - Os 18 registros de histórico pertenciam ao ID 2058 (sem CPF, sem matrícula)")
print("   - O registro correto é o ID 2922 (com CPF, com matrícula 2026)")
print("   - Não é possível recuperar os dados excluídos sem um backup do banco")
print("\n💡 PRÓXIMOS PASSOS:")
print("   1. Verificar se existe backup do banco de dados")
print("   2. Se houver backup, restaurar apenas a tabela historico_escolar")
print("   3. Copiar os registros do ID 2058 para o ID 2922")
print("   4. Excluir novamente os registros do ID 2058")

cursor.close()
conexao.close()
