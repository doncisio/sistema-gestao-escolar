"""
Excluir duplicados do 5º ano (com histórico escolar)
"""
from db.connection import conectar_bd

# IDs dos duplicados (sem matrícula)
duplicados = [
    {'id': 2900, 'nome': 'Angelica do Espirito Santo Bezerra'},
    {'id': 2901, 'nome': 'Esther Blesson Mendes Mouzinho'},
    {'id': 1696, 'nome': 'Lucas Guilherme Gonçalves Trovão'},
    {'id': 2902, 'nome': 'Guilherme Emanuell Silva Goncalves'},
    {'id': 2904, 'nome': 'Maria Luisa Medeiros Dantas'},
    {'id': 2905, 'nome': 'Miguel Braga Pacheco'},
    {'id': 2906, 'nome': 'Myrabe Adhassa Oscar Alves'},
    {'id': 1584, 'nome': 'Maria Rita Silva Araujo'},
    {'id': 2857, 'nome': 'Marcelly Vitoria Santos da Silva (duplicado 1)'},
    {'id': 2903, 'nome': 'Marcelly Vitoria Santos da Silva (duplicado 2)'}
]

print("="*80)
print("EXCLUSÃO DE DUPLICADOS DO 5º ANO")
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
        
        # Verificar histórico escolar
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM historico_escolar
            WHERE aluno_id = %s
        """, (aluno_id,))
        
        result_hist = cursor.fetchone()
        
        # Excluir histórico escolar se existir
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
