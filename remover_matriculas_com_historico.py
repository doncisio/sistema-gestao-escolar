"""
Script para remover matrículas de 2026 com tratamento de foreign keys
"""
from db.connection import conectar_bd

# IDs das matrículas que ainda precisam ser removidas
matriculas_pendentes = [
    {'matricula_id': 1371, 'aluno': 'Alícia Araújo do Nascimento', 'aluno_id': 2655},
    {'matricula_id': 1511, 'aluno': 'João Helio Goncalves Barros', 'aluno_id': 2860}
]

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

print("="*80)
print("REMOÇÃO DE MATRÍCULAS COM HISTÓRICO")
print("="*80)

for mat in matriculas_pendentes:
    print(f"\n📋 {mat['aluno']} (ID Aluno: {mat['aluno_id']})")
    print(f"   Matrícula ID: {mat['matricula_id']}")
    
    # Verificar histórico
    cursor.execute("""
        SELECT COUNT(*) as total FROM historico_matricula 
        WHERE matricula_id = %s
    """, (mat['matricula_id'],))
    
    hist = cursor.fetchone()
    total_hist = hist['total']
    
    print(f"   📊 Registros em historico_matricula: {total_hist}")
    
    if total_hist > 0:
        print(f"   🔄 Removendo {total_hist} registro(s) do histórico...")
        try:
            cursor.execute("""
                DELETE FROM historico_matricula 
                WHERE matricula_id = %s
            """, (mat['matricula_id'],))
            print(f"   ✅ Histórico removido")
        except Exception as e:
            print(f"   ❌ Erro ao remover histórico: {e}")
            continue
    
    # Remover matrícula
    print(f"   🔄 Removendo matrícula...")
    try:
        cursor.execute("""
            DELETE FROM Matriculas WHERE id = %s
        """, (mat['matricula_id'],))
        print(f"   ✅ Matrícula removida")
    except Exception as e:
        print(f"   ❌ Erro ao remover matrícula: {e}")

# Commit
conn.commit()

# Verificação final
print("\n" + "="*80)
print("VERIFICAÇÃO FINAL")
print("="*80)

cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2026")
ano_letivo_id = cursor.fetchone()['id']

for mat in matriculas_pendentes:
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM Matriculas m
        WHERE m.aluno_id = %s AND m.ano_letivo_id = %s
    """, (mat['aluno_id'], ano_letivo_id))
    
    result = cursor.fetchone()
    total = result['total']
    
    status = "✅ OK - Removida" if total == 0 else f"⚠️  Ainda tem {total} matrícula(s)"
    print(f"{mat['aluno']}: {status}")

print("="*80)

cursor.close()
conn.close()
