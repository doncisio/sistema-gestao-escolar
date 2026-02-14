"""
Excluir duplicados de Isaac Gabriel e Jose Bento
IDs a excluir: 2891, 2892
"""
from db.connection import conectar_bd

# IDs dos duplicados (sem matrícula)
duplicados = [
    {'id': 2891, 'nome': 'Isaac Gabriel Diniz Amorim', 'cpf': '09928419337'},
    {'id': 2892, 'nome': 'Jose Bento Lobato Lago', 'cpf': '63560331340'}
]

print("="*80)
print("EXCLUSÃO DE DUPLICADOS")
print("="*80)

conexao = conectar_bd()
cursor = conexao.cursor(dictionary=True, buffered=True)

try:
    for dup in duplicados:
        aluno_id = dup['id']
        nome = dup['nome']
        cpf = dup['cpf']
        
        print(f"\n📌 Excluindo: {nome} (ID: {aluno_id}, CPF: {cpf})")
        
        # Verificar se tem matrículas
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Matriculas
            WHERE aluno_id = %s
        """, (aluno_id,))
        
        result = cursor.fetchone()
        if result['total'] > 0:
            print(f"   ⚠️ ATENÇÃO: Este aluno tem {result['total']} matrícula(s)!")
            print(f"   ❌ NÃO SERÁ EXCLUÍDO por segurança")
            continue
        
        # Excluir vínculos com responsáveis
        cursor.execute("""
            DELETE FROM ResponsaveisAlunos
            WHERE aluno_id = %s
        """, (aluno_id,))
        responsaveis = cursor.rowcount
        
        # Excluir aluno
        cursor.execute("""
            DELETE FROM Alunos
            WHERE id = %s
        """, (aluno_id,))
        
        print(f"   ✅ Excluído com sucesso!")
        print(f"      - Vínculos com responsáveis: {responsaveis}")
    
    conexao.commit()
    print("\n" + "="*80)
    print("✅ EXCLUSÃO CONCLUÍDA COM SUCESSO!")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    conexao.rollback()
    
finally:
    cursor.close()
    conexao.close()

print("\n📊 Verificando resultado...")
conexao = conectar_bd()
cursor = conexao.cursor(dictionary=True, buffered=True)

for dup in duplicados:
    cursor.execute("SELECT COUNT(*) as total FROM Alunos WHERE id = %s", (dup['id'],))
    result = cursor.fetchone()
    if result['total'] == 0:
        print(f"   ✓ ID {dup['id']} ({dup['nome']}): EXCLUÍDO")
    else:
        print(f"   ⚠️ ID {dup['id']} ({dup['nome']}): AINDA EXISTE")

cursor.close()
conexao.close()
