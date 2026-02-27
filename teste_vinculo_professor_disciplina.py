"""
Script de teste para verificar vínculos professor-disciplina-turma
Este script ajuda a diagnosticar problemas de vinculação
"""

from src.core.conexao import conectar_bd

def verificar_vinculos():
    """Verifica os vínculos entre professores, disciplinas e turmas"""
    
    conn = conectar_bd()
    if not conn:
        print("❌ Erro ao conectar ao banco de dados")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    print("\n" + "="*80)
    print("VERIFICAÇÃO DE VÍNCULOS PROFESSOR-DISCIPLINA-TURMA")
    print("="*80)
    
    # 1. Verificar professores cadastrados
    print("\n1️⃣ PROFESSORES CADASTRADOS:")
    print("-" * 80)
    cursor.execute("""
        SELECT id, nome, cargo, polivalente 
        FROM funcionarios 
        WHERE cargo IN ('Professor@', 'Especialista (Coordenadora)')
        AND escola_id = 60
        ORDER BY nome
    """)
    professores = cursor.fetchall()
    
    if professores:
        for prof in professores:
            poliv = prof.get('polivalente', 'não definido')
            print(f"  ID: {prof['id']:3d} | {prof['nome']:40s} | Polivalente: {poliv}")
    else:
        print("  ⚠️  Nenhum professor encontrado!")
    
    # 2. Verificar disciplinas
    print("\n2️⃣ DISCIPLINAS CADASTRADAS:")
    print("-" * 80)
    cursor.execute("""
        SELECT id, nome 
        FROM disciplinas 
        WHERE escola_id = 60
        ORDER BY nome
    """)
    disciplinas = cursor.fetchall()
    
    if disciplinas:
        for disc in disciplinas:
            print(f"  ID: {disc['id']:3d} | {disc['nome']}")
    else:
        print("  ⚠️  Nenhuma disciplina encontrada!")
    
    # 3. Verificar vínculos na tabela funcionario_disciplinas
    print("\n3️⃣ VÍNCULOS PROFESSOR-DISCIPLINA-TURMA:")
    print("-" * 80)
    cursor.execute("""
        SELECT 
            fd.id,
            f.nome AS professor,
            d.nome AS disciplina,
            CONCAT(s.nome, ' ', t.nome) AS turma,
            t.turno,
            fd.turma_id
        FROM funcionario_disciplinas fd
        INNER JOIN funcionarios f ON fd.funcionario_id = f.id
        INNER JOIN disciplinas d ON fd.disciplina_id = d.id
        LEFT JOIN turmas t ON fd.turma_id = t.id
        LEFT JOIN series s ON t.serie_id = s.id
        WHERE f.escola_id = 60
        ORDER BY f.nome, d.nome, s.nome, t.nome
    """)
    vinculos = cursor.fetchall()
    
    if vinculos:
        for v in vinculos:
            turma_info = v['turma'] if v['turma'] else "TODAS AS TURMAS"
            turno_info = f"({v['turno']})" if v.get('turno') else ""
            print(f"  {v['professor']:35s} → {v['disciplina']:25s} → {turma_info} {turno_info}")
    else:
        print("  ⚠️  Nenhum vínculo encontrado!")
        print("  💡 Dica: Vincule professores às disciplinas no cadastro/edição de funcionários")
    
    # 4. Verificar professores SEM vínculos
    print("\n4️⃣ PROFESSORES SEM VÍNCULOS:")
    print("-" * 80)
    cursor.execute("""
        SELECT f.id, f.nome
        FROM funcionarios f
        WHERE f.cargo IN ('Professor@', 'Especialista (Coordenadora)')
        AND f.escola_id = 60
        AND NOT EXISTS (
            SELECT 1 FROM funcionario_disciplinas fd 
            WHERE fd.funcionario_id = f.id
        )
        ORDER BY f.nome
    """)
    sem_vinculo = cursor.fetchall()
    
    if sem_vinculo:
        print("  ⚠️  Os seguintes professores NÃO têm disciplinas vinculadas:")
        for prof in sem_vinculo:
            print(f"    - {prof['nome']} (ID: {prof['id']})")
        print("\n  💡 Esses professores não aparecerão na lista de horários para disciplinas específicas")
    else:
        print("  ✅ Todos os professores têm pelo menos uma disciplina vinculada!")
    
    # 5. Verificar turmas disponíveis
    print("\n5️⃣ TURMAS CADASTRADAS (Ano Letivo 2026):")
    print("-" * 80)
    cursor.execute("""
        SELECT t.id, s.nome AS serie, t.nome AS turma, t.turno
        FROM turmas t
        INNER JOIN series s ON t.serie_id = s.id
        INNER JOIN anosletivos al ON t.ano_letivo_id = al.id
        WHERE t.escola_id = 60 
        AND al.ano_letivo = 2026
        ORDER BY s.nome, t.nome
    """)
    turmas = cursor.fetchall()
    
    if turmas:
        for t in turmas:
            print(f"  ID: {t['id']:3d} | {t['serie']:15s} {t['turma']:10s} | Turno: {t['turno']}")
    else:
        print("  ⚠️  Nenhuma turma encontrada para 2026!")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("RESUMO DAS MELHORIAS IMPLEMENTADAS:")
    print("="*80)
    print("""
    ✅ Os comboboxes agora permitem digitação livre
    ✅ Filtro inteligente ao selecionar disciplina
    ✅ Mostra apenas professores vinculados à disciplina selecionada
    ✅ Se não houver vínculos, mostra todos os professores
    ✅ Autocomplete ao digitar nos campos
    ✅ Logs detalhados para diagnóstico
    
    📋 COMO USAR:
    1. Abra o gerenciamento de horários
    2. Selecione uma turma
    3. Clique em um horário para editar
    4. Selecione uma disciplina
    5. A lista de professores será filtrada automaticamente!
    """)

if __name__ == "__main__":
    verificar_vinculos()
