from db.connection import conectar_bd

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# ID a ser excluído
id_excluir = 2921
nome_aluno = "Kaik Rua Pereira de Morais"

print("=" * 90)
print(f"EXCLUSÃO DE DUPLICATA: {nome_aluno}")
print("=" * 90)
print(f"\n🗑️  Preparando para excluir ID {id_excluir}...")

# Verificar dados antes de excluir
cursor.execute("""
    SELECT id, nome, cpf, data_nascimento
    FROM Alunos
    WHERE id = %s
""", (id_excluir,))

aluno = cursor.fetchone()

if not aluno:
    print(f"❌ Aluno ID {id_excluir} não encontrado!")
    cursor.close()
    conn.close()
    exit(1)

print(f"\n📋 Dados do registro a ser excluído:")
print(f"   ID: {aluno['id']}")
print(f"   Nome: {aluno['nome']}")
print(f"   CPF: {aluno['cpf'] or 'NÃO INFORMADO'}")
print(f"   Data Nascimento: {aluno['data_nascimento']}")

# Verificar matrícula
cursor.execute("""
    SELECT COUNT(*) as total
    FROM Matriculas
    WHERE aluno_id = %s
""", (id_excluir,))

mat_count = cursor.fetchone()['total']
print(f"\n📚 Matrículas: {mat_count}")

# Verificar histórico
cursor.execute("""
    SELECT COUNT(*) as total
    FROM historico_escolar
    WHERE aluno_id = %s
""", (id_excluir,))

hist_count = cursor.fetchone()['total']
print(f"📋 Histórico Escolar: {hist_count}")

# Verificar documentos
cursor.execute("""
    SELECT COUNT(*) as total
    FROM documentos_emitidos
    WHERE aluno_id = %s
""", (id_excluir,))

docs_count = cursor.fetchone()['total']
print(f"📄 Documentos Emitidos: {docs_count}")

# Verificar responsáveis
cursor.execute("""
    SELECT COUNT(*) as total
    FROM ResponsaveisAlunos
    WHERE aluno_id = %s
""", (id_excluir,))

resp_count = cursor.fetchone()['total']
print(f"👥 Responsáveis: {resp_count}")

# Excluir em ordem (respeitando foreign keys)
print(f"\n🔄 Executando exclusão...")

try:
    # 1. Histórico escolar
    if hist_count > 0:
        cursor.execute("DELETE FROM historico_escolar WHERE aluno_id = %s", (id_excluir,))
        print(f"   ✓ {cursor.rowcount} registro(s) de histórico escolar excluídos")
    
    # 2. Documentos emitidos
    if docs_count > 0:
        cursor.execute("DELETE FROM documentos_emitidos WHERE aluno_id = %s", (id_excluir,))
        print(f"   ✓ {cursor.rowcount} documento(s) emitido(s) excluído(s)")
    
    # 3. Responsáveis
    if resp_count > 0:
        cursor.execute("DELETE FROM ResponsaveisAlunos WHERE aluno_id = %s", (id_excluir,))
        print(f"   ✓ {cursor.rowcount} responsável(is) excluído(s)")
    
    # 4. Matrículas (se houver)
    if mat_count > 0:
        cursor.execute("DELETE FROM Matriculas WHERE aluno_id = %s", (id_excluir,))
        print(f"   ✓ {cursor.rowcount} matrícula(s) excluída(s)")
    
    # 5. Aluno
    cursor.execute("DELETE FROM Alunos WHERE id = %s", (id_excluir,))
    print(f"   ✓ Aluno ID {id_excluir} excluído")
    
    conn.commit()
    print(f"\n✅ Exclusão concluída com sucesso!")
    
    # Verificar registro mantido
    print(f"\n📌 Verificando registro mantido (ID 2751)...")
    cursor.execute("""
        SELECT a.id, a.nome, a.cpf, a.data_nascimento,
               (SELECT COUNT(*) FROM Matriculas WHERE aluno_id = a.id AND ano_letivo_id = 26) as mat_2026
        FROM Alunos a
        WHERE a.id = 2751
    """)
    
    mantido = cursor.fetchone()
    if mantido:
        print(f"   ✓ ID: {mantido['id']}")
        print(f"   ✓ Nome: {mantido['nome']}")
        print(f"   ✓ CPF: {mantido['cpf'] or 'NÃO INFORMADO'}")
        print(f"   ✓ Data Nascimento: {mantido['data_nascimento']}")
        print(f"   ✓ Matrícula 2026: {'SIM' if mantido['mat_2026'] > 0 else 'NÃO'}")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro durante a exclusão: {e}")
    cursor.close()
    conn.close()
    exit(1)

cursor.close()
conn.close()

print("\n" + "=" * 90)
print("CONCLUSÃO")
print("=" * 90)
print(f"✅ Duplicata de {nome_aluno} removida com sucesso!")
print(f"   - ID excluído: {id_excluir}")
print(f"   - ID mantido: 2751 (com matrícula 2026)")
