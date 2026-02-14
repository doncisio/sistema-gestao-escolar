import mysql.connector
from datetime import datetime

# Conectar ao banco de dados
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='987412365',
    database='redeescola'
)

cursor = conn.cursor()

# IDs para excluir (registros do GEDUC sem histórico escolar)
ids_para_excluir = [
    (2916, "Andre Martins Marques Junior"),
    (2914, "Assis Reis Gomes Junior"),
    (2915, "Eike Emanoel Mendes Soeiro"),
    (2917, "Esther Talita dos Santos Braga"),
    (2918, "Luana Larissa Medeiros Martins"),
    (2919, "Marya Vitoria Silva Nogueira"),
    (2920, "Pedro Henrique Silva Costa")
]

# IDs para manter (registros originais com histórico escolar)
ids_para_manter = [
    (577, "Andre Martins Marques Junior"),
    (2698, "Assis Reis Gomes Junior"),
    (2693, "Eike Emanoel Mendes Soeiro"),
    (584, "Esther Talita dos Santos Braga"),
    (594, "Luana Larissa Medeiros Martins"),
    (599, "Marya Vitoria Silva Nogueira"),
    (608, "Pedro Henrique Silva Costa")
]

print("=" * 80)
print("EXCLUSÃO DE DUPLICATAS - 7º ANO")
print("=" * 80)
print(f"\nRegistros a MANTER (originais com histórico):")
for id_aluno, nome in ids_para_manter:
    print(f"  ✅ ID {id_aluno}: {nome}")

print(f"\nRegistros a EXCLUIR (GEDUC sem histórico):")
for id_aluno, nome in ids_para_excluir:
    print(f"  ❌ ID {id_aluno}: {nome}")

print("\n" + "=" * 80)

for id_aluno, nome in ids_para_excluir:
    print(f"\nProcessando ID {id_aluno}: {nome}")
    print("-" * 80)
    
    try:
        # Verificar dados associados antes de excluir
        cursor.execute("SELECT COUNT(*) FROM Matriculas WHERE aluno_id = %s", (id_aluno,))
        qtd_matriculas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM historico_escolar WHERE aluno_id = %s", (id_aluno,))
        qtd_historico = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM documentos_emitidos WHERE aluno_id = %s", (id_aluno,))
        qtd_documentos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ResponsaveisAlunos WHERE aluno_id = %s", (id_aluno,))
        qtd_responsaveis = cursor.fetchone()[0]
        
        print(f"  Matrículas: {qtd_matriculas}")
        print(f"  Histórico escolar: {qtd_historico}")
        print(f"  Documentos emitidos: {qtd_documentos}")
        print(f"  Responsáveis: {qtd_responsaveis}")
        
        # Excluir em ordem (respeitando foreign keys)
        
        # 1. Excluir matrículas
        if qtd_matriculas > 0:
            cursor.execute("DELETE FROM Matriculas WHERE aluno_id = %s", (id_aluno,))
            print(f"  ✓ {qtd_matriculas} matrícula(s) excluída(s)")
        
        # 2. Excluir histórico escolar
        if qtd_historico > 0:
            cursor.execute("DELETE FROM historico_escolar WHERE aluno_id = %s", (id_aluno,))
            print(f"  ✓ {qtd_historico} registro(s) de histórico excluído(s)")
        
        # 3. Excluir documentos emitidos
        if qtd_documentos > 0:
            cursor.execute("DELETE FROM documentos_emitidos WHERE aluno_id = %s", (id_aluno,))
            print(f"  ✓ {qtd_documentos} documento(s) excluído(s)")
        
        # 4. Excluir responsáveis
        if qtd_responsaveis > 0:
            cursor.execute("DELETE FROM ResponsaveisAlunos WHERE aluno_id = %s", (id_aluno,))
            print(f"  ✓ {qtd_responsaveis} responsável(is) excluído(s)")
        
        # 5. Excluir aluno
        cursor.execute("DELETE FROM Alunos WHERE id = %s", (id_aluno,))
        print(f"  ✓ Aluno excluído")
        
        conn.commit()
        print(f"  ✅ ID {id_aluno} excluído com sucesso!")
        
    except Exception as e:
        print(f"  ❌ Erro ao excluir ID {id_aluno}: {e}")
        conn.rollback()

print("\n" + "=" * 80)
print("VERIFICAÇÃO FINAL")
print("=" * 80)

for id_aluno, nome in ids_para_manter:
    cursor.execute("SELECT COUNT(*) FROM Alunos WHERE id = %s", (id_aluno,))
    existe = cursor.fetchone()[0]
    if existe:
        print(f"✅ ID {id_aluno} ({nome}) - MANTIDO")
    else:
        print(f"❌ ID {id_aluno} ({nome}) - ERRO: FOI EXCLUÍDO!")

for id_aluno, nome in ids_para_excluir:
    cursor.execute("SELECT COUNT(*) FROM Alunos WHERE id = %s", (id_aluno,))
    existe = cursor.fetchone()[0]
    if not existe:
        print(f"✅ ID {id_aluno} ({nome}) - EXCLUÍDO")
    else:
        print(f"❌ ID {id_aluno} ({nome}) - ERRO: NÃO FOI EXCLUÍDO!")

print("\n" + "=" * 80)
print("PROCESSO CONCLUÍDO")
print("=" * 80)

cursor.close()
conn.close()
