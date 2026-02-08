"""
Script para corrigir o sexo dos 34 alunos importados do GEDUC
Inferência baseada em nomes comuns
"""

from db.connection import conectar_bd

def inferir_sexo_por_nome(nome):
    """
    Infere o sexo baseado em nomes comuns
    Retorna 'F' para feminino, 'M' para masculino
    """
    if not nome:
        return 'M'
    
    nome_lower = nome.lower()
    primeiro_nome = nome.split()[0].lower()
    
    # Nomes claramente femininos
    nomes_femininos = [
        'ana', 'maria', 'sarah', 'sara', 'rebeca', 'pietra', 'lara', 
        'isadora', 'gabrielly', 'glenda', 'esther', 'marcelly', 'rita',
        'natalia', 'bruna', 'candida', 'yasmin', 'aryella'
    ]
    
    # Nomes claramente masculinos
    nomes_masculinos = [
        'benjamin', 'enzo', 'fernando', 'guilherme', 'henzo', 'igor',
        'joao', 'joão', 'kauan', 'mikael', 'noah', 'deyvison'
    ]
    
    # Verificar primeiro nome
    if primeiro_nome in nomes_femininos:
        return 'F'
    if primeiro_nome in nomes_masculinos:
        return 'M'
    
    # Verificar terminações comuns femininas
    terminacoes_femininas = ['a', 'ella', 'elly', 'bela', 'bella', 'issa', 'isa']
    for term in terminacoes_femininas:
        if primeiro_nome.endswith(term):
            return 'F'
    
    # Verificar terminações comuns masculinas
    terminacoes_masculinas = ['o', 'el', 'son', 'nho']
    for term in terminacoes_masculinas:
        if primeiro_nome.endswith(term):
            return 'M'
    
    # Padrão: masculino (mais conservador)
    return 'M'


def corrigir_sexos():
    """Corrige o sexo dos alunos importados (IDs 2836-2869)"""
    
    print("="*80)
    print("CORREÇÃO DO SEXO DOS ALUNOS IMPORTADOS")
    print("="*80)
    
    conn = conectar_bd()
    if not conn:
        print("❌ Erro ao conectar ao banco de dados")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    # Buscar os 34 alunos importados (IDs 2836-2869)
    cursor.execute("""
        SELECT id, nome, sexo
        FROM Alunos
        WHERE id BETWEEN 2836 AND 2869
        ORDER BY id
    """)
    
    alunos = cursor.fetchall()
    
    if not alunos:
        print("❌ Nenhum aluno encontrado no range 2836-2869")
        cursor.close()
        conn.close()
        return
    
    print(f"\n✓ {len(alunos)} alunos encontrados\n")
    print("="*80)
    print("CORREÇÕES")
    print("="*80)
    
    corrigidos = 0
    mantidos = 0
    
    for aluno in alunos:
        aluno_id = aluno['id']
        nome = aluno['nome']
        sexo_atual = aluno['sexo']
        
        # Inferir sexo correto
        sexo_correto = inferir_sexo_por_nome(nome)
        
        if sexo_atual != sexo_correto:
            # Atualizar
            cursor.execute("""
                UPDATE Alunos
                SET sexo = %s
                WHERE id = %s
            """, (sexo_correto, aluno_id))
            
            print(f"[{aluno_id:04d}] 🔄 {nome}")
            print(f"        {sexo_atual} → {sexo_correto}")
            corrigidos += 1
        else:
            print(f"[{aluno_id:04d}] ✓ {nome} ({sexo_atual})")
            mantidos += 1
    
    # Commit das alterações
    conn.commit()
    
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"✓ Total de alunos: {len(alunos)}")
    print(f"✓ Corrigidos: {corrigidos}")
    print(f"✓ Mantidos: {mantidos}")
    print("\n✅ Sexos corrigidos com sucesso!")
    
    cursor.close()
    conn.close()


if __name__ == '__main__':
    corrigir_sexos()
