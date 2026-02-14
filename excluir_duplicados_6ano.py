"""
Excluir duplicados do 6º ano
IDs a excluir: 2907, 2909, 2910, 2911, 2912, 2913
"""
from db.connection import conectar_bd

# IDs dos duplicados (sem matrícula) - apenas os relacionados ao 6º ano
duplicados = [
    {'id': 2907, 'nome': 'Alicya Beatriz dos Santos Ferreira'},
    {'id': 2909, 'nome': 'Caio Brito Marques'},
    {'id': 2910, 'nome': 'Joao Guilherme das Neves Corvelo'},
    {'id': 2911, 'nome': 'Kallebe Kaua Pereira Correia'},
    {'id': 2912, 'nome': 'Kaua Kaiky Pereira Correia'},
    {'id': 2913, 'nome': 'Lucas Davi Melo Marques'}
]

print("="*80)
print("EXCLUSÃO DE DUPLICADOS DO 6º ANO")
print("="*80)
print(f"Total de registros a excluir: {len(duplicados)}")
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
        
        # Excluir histórico escolar se existir
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM historico_escolar
            WHERE aluno_id = %s
        """, (aluno_id,))
        
        result_hist = cursor.fetchone()
        
        if result_hist['total'] > 0:
            cursor.execute("""
                DELETE FROM historico_escolar
                WHERE aluno_id = %s
            """, (aluno_id,))
            historico = cursor.rowcount
            print(f"      - Histórico escolar: {historico} registros removidos")
        
        # Excluir documentos emitidos se existir
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM documentos_emitidos
            WHERE aluno_id = %s
        """, (aluno_id,))
        
        result_docs = cursor.fetchone()
        
        if result_docs['total'] > 0:
            cursor.execute("""
                DELETE FROM documentos_emitidos
                WHERE aluno_id = %s
            """, (aluno_id,))
            docs = cursor.rowcount
            print(f"      - Documentos emitidos: {docs} registros removidos")
        
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

excluidos = 0
nao_excluidos = 0

for dup in duplicados:
    cursor.execute("SELECT COUNT(*) as total FROM Alunos WHERE id = %s", (dup['id'],))
    result = cursor.fetchone()
    if result['total'] == 0:
        print(f"   ✓ ID {dup['id']}: EXCLUÍDO")
        excluidos += 1
    else:
        print(f"   ⚠️ ID {dup['id']}: AINDA EXISTE")
        nao_excluidos += 1

print(f"\n📊 Resumo:")
print(f"   ✅ Excluídos: {excluidos}")
print(f"   ⚠️ Não excluídos: {nao_excluidos}")

cursor.close()
conexao.close()
