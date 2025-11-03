"""
Script para modificar o trigger verificar_disciplina_funcionario
Permite que TODOS os professores (polivalentes ou não) possam ter disciplinas
"""
import mysql.connector
from conexao import conectar_bd

def main():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    print("="*80)
    print("MODIFICANDO TRIGGER DO BANCO DE DADOS")
    print("="*80)
    
    # Passo 1: Remover trigger antigo
    print("\n1. Removendo trigger antigo...")
    try:
        cursor.execute("DROP TRIGGER IF EXISTS verificar_disciplina_funcionario")
        print("   ✓ Trigger antigo removido")
    except Exception as e:
        print(f"   ⚠ Erro ao remover: {e}")
    
    # Passo 2: Criar novo trigger
    print("\n2. Criando novo trigger...")
    trigger_sql = """
CREATE TRIGGER verificar_disciplina_funcionario 
BEFORE INSERT ON funcionario_disciplinas 
FOR EACH ROW 
BEGIN
    DECLARE cargo_professor VARCHAR(100);

    -- Buscar o cargo do funcionário
    SELECT cargo INTO cargo_professor 
    FROM funcionarios 
    WHERE id = NEW.funcionario_id;

    -- Permitir disciplinas específicas apenas para professores
    -- Permite turmas volantes (disciplina_id IS NULL) para qualquer professor
    IF cargo_professor != 'Professor@' AND NEW.disciplina_id IS NOT NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Somente Professores podem ter disciplinas associadas';
    END IF;
END
"""
    
    try:
        cursor.execute(trigger_sql)
        print("   ✓ Novo trigger criado com sucesso!")
    except Exception as e:
        print(f"   ✗ Erro ao criar trigger: {e}")
        cursor.close()
        conn.close()
        return False
    
    conn.commit()
    
    print("\n" + "="*80)
    print("ALTERAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print("\nResumo das mudanças:")
    print("  ANTES: Apenas professores NÃO polivalentes podiam ter disciplinas")
    print("  AGORA: TODOS os professores (polivalentes ou não) podem ter disciplinas")
    print("\nValidação mantida:")
    print("  - Apenas funcionários com cargo 'Professor@' podem ter disciplinas")
    print("  - Turmas volantes (sem disciplina específica) podem ser de qualquer professor")
    print("="*80)
    
    # Passo 3: Testar o novo trigger
    print("\n3. Testando o novo trigger...")
    print("   Inserindo disciplina para funcionário 117 (polivalente)...")
    
    funcionario_id = 117
    disciplina_id = 1  # PORTUGUÊS
    turma_id = 28  # 1º Ano
    
    try:
        cursor.execute("""
            INSERT INTO funcionario_disciplinas (funcionario_id, disciplina_id, turma_id)
            VALUES (%s, %s, %s)
        """, (funcionario_id, disciplina_id, turma_id))
        
        conn.commit()
        print("   ✓ SUCESSO! Disciplina inserida sem erros!")
        
        # Verificar
        cursor.execute("""
            SELECT fd.id, d.nome as disciplina, t.nome as turma, s.nome as serie
            FROM funcionario_disciplinas fd
            JOIN disciplinas d ON fd.disciplina_id = d.id
            JOIN turmas t ON fd.turma_id = t.id
            JOIN serie s ON t.serie_id = s.id
            WHERE fd.funcionario_id = %s
        """, (funcionario_id,))
        
        registros = cursor.fetchall()
        print(f"\n   Disciplinas do funcionário {funcionario_id}: {len(registros)}")
        for reg in registros:
            print(f"     - {reg[1]} em {reg[3]} Turma {reg[2]}")
            
    except Exception as e:
        print(f"   ✗ Erro ao testar: {e}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("\n✓ Processo concluído!")
    return True

if __name__ == "__main__":
    main()
