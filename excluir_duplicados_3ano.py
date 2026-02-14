"""
Excluir duplicados do 3º ano
IDs a excluir: 2893, 2894, 2895
"""
from db.connection import conectar_bd

# IDs dos duplicados (sem matrícula)
duplicados = [
    {'id': 2893, 'nome': 'Kaique Leonardo Moreno de Sa'},
    {'id': 2894, 'nome': 'Luis Gustavo Teixeira Pinheiro'},
    {'id': 2895, 'nome': 'Miguel Arthur Santos da Silva Azevedo'}
]

print("="*80)
print("EXCLUSÃO DE DUPLICADOS DO 3º ANO")
print("="*80)

conexao = conectar_bd()
cursor = conexao.cursor(dictionary=True, buffered=True)

try:
    for dup in duplicados:
        aluno_id = dup['id']
        nome = dup['nome']
        
        print(f"\n📌 Excluindo: {nome} (ID: {aluno_id})")
        
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
