"""
Script para testar vínculos professor-disciplina por turma específica
"""

from src.core.conexao import conectar_bd

def testar_vinculos_turma(turma_id=38):  # 38 = 1º Ano
    """Testa os vínculos de uma turma específica"""
    
    conn = conectar_bd()
    if not conn:
        print("❌ Erro ao conectar ao banco")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    print("\n" + "="*80)
    print(f"TESTE DE VÍNCULOS - TURMA ID {turma_id}")
    print("="*80)
    
    # Buscar informações da turma
    cursor.execute("""
        SELECT t.id, t.nome, s.nome as serie_nome, t.turno
        FROM turmas t
        JOIN series s ON t.serie_id = s.id
        WHERE t.id = %s
    """, (turma_id,))
    
    turma = cursor.fetchone()
    if not turma:
        print(f"❌ Turma {turma_id} não encontrada")
        return
    
    print(f"\n📚 TURMA: {turma['serie_nome']} {turma['nome']} - Turno: {turma['turno']}")
    print("-" * 80)
    
    # 1. Disciplinas vinculadas à turma
    print("\n1️⃣ DISCIPLINAS VINCULADAS À TURMA:")
    print("-" * 80)
    cursor.execute("""
        SELECT DISTINCT d.id, d.nome
        FROM disciplinas d
        INNER JOIN funcionario_disciplinas fd ON d.id = fd.disciplina_id
        WHERE (fd.turma_id = %s OR fd.turma_id IS NULL)
        AND d.escola_id = 60
        ORDER BY d.nome
    """, (turma_id,))
    
    disciplinas = cursor.fetchall()
    if disciplinas:
        print(f"✓ {len(disciplinas)} disciplinas encontradas:")
        for disc in disciplinas:
            print(f"  • {disc['nome']} (ID: {disc['id']})")
    else:
        print("⚠️ Nenhuma disciplina vinculada a esta turma")
    
    # 2. Para cada disciplina, mostrar professores
    print("\n2️⃣ PROFESSORES POR DISCIPLINA:")
    print("-" * 80)
    for disc in disciplinas:
        cursor.execute("""
            SELECT DISTINCT f.id, f.nome, f.polivalente
            FROM funcionarios f
            INNER JOIN funcionario_disciplinas fd ON f.id = fd.funcionario_id
            WHERE fd.disciplina_id = %s
            AND (fd.turma_id = %s OR fd.turma_id IS NULL)
            AND f.escola_id = 60
            ORDER BY f.nome
        """, (disc['id'], turma_id))
        
        professores = cursor.fetchall()
        if professores:
            print(f"\n📖 {disc['nome']}:")
            for prof in professores:
                poliv = "✓ Polivalente" if prof['polivalente'] == 'sim' else ""
                print(f"  → {prof['nome']} {poliv}")
        else:
            print(f"\n📖 {disc['nome']}: ⚠️ SEM PROFESSOR VINCULADO")
    
    # 3. Professores polivalentes da turma
    print("\n3️⃣ PROFESSORES POLIVALENTES VINCULADOS:")
    print("-" * 80)
    cursor.execute("""
        SELECT DISTINCT f.id, f.nome
        FROM funcionarios f
        INNER JOIN funcionario_disciplinas fd ON f.id = fd.funcionario_id
        WHERE f.polivalente IN ('sim', 'Sim', 'SIM', 1)
        AND (fd.turma_id = %s OR fd.turma_id IS NULL)
        AND f.escola_id = 60
        ORDER BY f.nome
    """, (turma_id,))
    
    polivalentes = cursor.fetchall()
    if polivalentes:
        print(f"✓ {len(polivalentes)} professor(es) polivalente(s):")
        for prof in polivalentes:
            print(f"  • {prof['nome']}")
    else:
        print("⚠️ Nenhum professor polivalente vinculado")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("CONCLUSÃO:")
    print("="*80)
    if disciplinas and all(has_prof(d['id'], turma_id) for d in disciplinas):
        print("✅ Turma está totalmente configurada!")
    else:
        print("⚠️ Há disciplinas sem professores vinculados")
    print()

def has_prof(disc_id, turma_id):
    """Verifica se uma disciplina tem professor vinculado"""
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM funcionario_disciplinas
        WHERE disciplina_id = %s AND (turma_id = %s OR turma_id IS NULL)
    """, (disc_id, turma_id))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0

if __name__ == "__main__":
    print("\n🔍 Testando vínculos para diferentes turmas:\n")
    
    # Testar turmas de diferentes anos
    turmas_teste = [
        (38, "1º Ano"),
        (39, "2º Ano"),
        (43, "6º Ano"),
        (44, "7º Ano A"),
    ]
    
    for turma_id, nome in turmas_teste:
        print(f"\n{'='*80}")
        print(f"TESTANDO: {nome} (ID: {turma_id})")
        print('='*80)
        testar_vinculos_turma(turma_id)
        input("\nPressione ENTER para continuar...")
