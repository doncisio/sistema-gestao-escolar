"""
Script para excluir matrículas do ano letivo 2026 de alunos que não renovaram
Esses alunos estão apenas no sistema local, mas não no GEDUC
"""

from db.connection import conectar_bd, get_cursor

# Lista dos 26 alunos que estão apenas no sistema local (não renovaram matrícula)
ALUNOS_NAO_RENOVADOS = [
    "Alice Ferreira Alves",
    "Ana Beatriz Monteiro da Silva",
    "Ana Luiza Ferreira Castro",
    "Barbara Ellen Barbosa Ferreira",
    "Carlos Daniel Almeida Teixeira",
    "Carlos Eduardo Garcias dos Santos",
    "Edson Kauã Nascimento Castro",
    "Enos Natanael Matos da Silva",
    "Gabriela Coelho da Silva",
    "Iana Sophie Sousa Lima",
    "Iasmim Vitória Abreu da Silva",
    "João Miguel Frasão Montes",
    "João Pedro Silva Perreira",
    "Jonilson Freitas de Sousa Neto",
    "Laerth Miguel Sousa Brito",
    "Lara Sophia Perna dos Santos",
    "Laura Marie Matos Gonçalves",
    "Lorena Vitoria Cunha Moraes",
    "Luiz Miguel dos Santos Sales",
    "Marcelly Vitória Santos da Silva Azevedo",
    "Marcia Hianla Silva Ataide",
    "Matheus Leite Lima",
    "Maxwel Ferreira Rocha",
    "Pedro Victor Almeida Carvalho",
    "Rayssa dos Santos da Silva",
    "Rhyan Carlos Araujo Gomes"
]

def normalizar_nome(nome):
    """Remove acentos e converte para maiúsculo"""
    import unicodedata
    nfkd = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return nome_sem_acento.upper()

def excluir_matriculas_2026():
    """Exclui matrículas do ano letivo 2026 dos alunos que não renovaram"""
    
    print("="*80)
    print("EXCLUSÃO DE MATRÍCULAS NÃO RENOVADAS - ANO LETIVO 2026")
    print("="*80)
    print(f"\nTotal de alunos a processar: {len(ALUNOS_NAO_RENOVADOS)}")
    print("\nEstes alunos não estão no GEDUC, portanto não renovaram matrícula.")
    print("Vamos excluir apenas o registro de matrícula em 2026.\n")
    
    conn = conectar_bd()
    if not conn:
        print("❌ ERRO: Não foi possível conectar ao banco de dados!")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    # Buscar ID do ano letivo 2026
    cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2026")
    ano_letivo = cursor.fetchone()
    
    if not ano_letivo:
        print("❌ ERRO: Ano letivo 2026 não encontrado!")
        cursor.close()
        conn.close()
        return
    
    ano_letivo_id = ano_letivo['id']
    print(f"✓ Ano letivo 2026 encontrado (ID: {ano_letivo_id})\n")
    
    excluidos = 0
    nao_encontrados = []
    sem_matricula = []
    
    print("Processando alunos:\n")
    
    for idx, nome_aluno in enumerate(ALUNOS_NAO_RENOVADOS, 1):
        nome_normalizado = normalizar_nome(nome_aluno)
        
        # Buscar aluno pelo nome
        cursor.execute("""
            SELECT id, nome 
            FROM Alunos 
            WHERE UPPER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                REPLACE(nome, 'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U'), 'Ç', 'C')
            ) = %s
        """, (nome_normalizado,))
        
        aluno = cursor.fetchone()
        
        if not aluno:
            print(f"[{idx:02d}] ⚠️  {nome_aluno}")
            print(f"     ALUNO NÃO ENCONTRADO NO BANCO\n")
            nao_encontrados.append(nome_aluno)
            continue
        
        aluno_id = aluno['id']
        aluno_nome = aluno['nome']
        
        # Verificar se tem matrícula em 2026
        cursor.execute("""
            SELECT id 
            FROM Matriculas 
            WHERE aluno_id = %s AND ano_letivo_id = %s
        """, (aluno_id, ano_letivo_id))
        
        matricula = cursor.fetchone()
        
        if not matricula:
            print(f"[{idx:02d}] ℹ️  {aluno_nome} (ID: {aluno_id})")
            print(f"     Já sem matrícula em 2026\n")
            sem_matricula.append(nome_aluno)
            continue
        
        matricula_id = matricula['id']
        
        # Primeiro, excluir registros relacionados em historico_matricula
        cursor.execute("""
            DELETE FROM historico_matricula 
            WHERE matricula_id = %s
        """, (matricula_id,))
        
        # Depois excluir a matrícula
        cursor.execute("""
            DELETE FROM Matriculas 
            WHERE id = %s
        """, (matricula_id,))
        
        print(f"[{idx:02d}] ✅ {aluno_nome} (ID: {aluno_id})")
        print(f"     Matrícula ID {matricula_id} EXCLUÍDA\n")
        excluidos += 1
    
    # Confirmar exclusões
    conn.commit()
    
    print("="*80)
    print("RESUMO")
    print("="*80)
    print(f"Total processado: {len(ALUNOS_NAO_RENOVADOS)}")
    print(f"✅ Matrículas excluídas: {excluidos}")
    print(f"ℹ️  Já sem matrícula: {len(sem_matricula)}")
    print(f"⚠️  Alunos não encontrados: {len(nao_encontrados)}")
    
    if nao_encontrados:
        print("\nAlunos não encontrados:")
        for nome in nao_encontrados:
            print(f"  - {nome}")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Processo concluído!")
    print("="*80)

if __name__ == "__main__":
    print("\nEste script vai excluir matrículas de 2026 de alunos que não renovaram.")
    print("São alunos que estão no sistema local mas não no GEDUC.\n")
    
    resposta = input("Deseja continuar? (sim/nao): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        excluir_matriculas_2026()
    else:
        print("\nOperação cancelada pelo usuário.")
