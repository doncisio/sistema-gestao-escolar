from config_logs import get_logger
logger = get_logger(__name__)
"""
Script para modificar o trigger verificar_disciplina_funcionario
Permite que TODOS os professores (polivalentes ou não) possam ter disciplinas
"""
import mysql.connector
from conexao import conectar_bd
from typing import Any, cast

def main():
    conn: Any = conectar_bd()
    if not conn:
        logger.info("Não foi possível conectar ao banco de dados.")
        return False
    cursor: Any = cast(Any, conn).cursor()

    try:
        logger.info("="*80)
        logger.info("MODIFICANDO TRIGGER DO BANCO DE DADOS")
        logger.info("="*80)
        
        # Passo 1: Remover trigger antigo
        logger.info("\n1. Removendo trigger antigo...")
        try:
            cursor.execute("DROP TRIGGER IF EXISTS verificar_disciplina_funcionario")
            logger.info("   ✓ Trigger antigo removido")
        except Exception as e:
            logger.error(f"   ⚠ Erro ao remover: {e}")
        
        # Passo 2: Criar novo trigger
        logger.info("\n2. Criando novo trigger...")
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
            logger.info("   ✓ Novo trigger criado com sucesso!")
        except Exception as e:
            logger.error(f"   ✗ Erro ao criar trigger: {e}")
            return False

        conn.commit()

        logger.info("\n" + "="*80)
        logger.info("ALTERAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("="*80)
        logger.info("\nResumo das mudanças:")
        logger.info("  ANTES: Apenas professores NÃO polivalentes podiam ter disciplinas")
        logger.info("  AGORA: TODOS os professores (polivalentes ou não) podem ter disciplinas")
        logger.info("\nValidação mantida:")
        logger.info("  - Apenas funcionários com cargo 'Professor@' podem ter disciplinas")
        logger.info("  - Turmas volantes (sem disciplina específica) podem ser de qualquer professor")
        logger.info("="*80)

        # Passo 3: Testar o novo trigger
        logger.info("\n3. Testando o novo trigger...")
        logger.info("   Inserindo disciplina para funcionário 117 (polivalente)...")

        funcionario_id = 117
        disciplina_id = 1  # PORTUGUÊS
        turma_id = 28  # 1º Ano

        try:
            cursor.execute("""
                INSERT INTO funcionario_disciplinas (funcionario_id, disciplina_id, turma_id)
                VALUES (%s, %s, %s)
            """, (funcionario_id, disciplina_id, turma_id))

            conn.commit()
            logger.info("   ✓ SUCESSO! Disciplina inserida sem erros!")

            # Verificar
            cursor.execute("""
                SELECT fd.id, d.nome as disciplina, t.nome as turma, s.nome as serie
                FROM funcionario_disciplinas fd
                JOIN disciplinas d ON fd.disciplina_id = d.id
                JOIN turmas t ON fd.turma_id = t.id
                JOIN series s ON t.serie_id = s.id
                WHERE fd.funcionario_id = %s
            """, (funcionario_id,))

            registros = cursor.fetchall()
            logger.info(f"\n   Disciplinas do funcionário {funcionario_id}: {len(registros)}")
            for reg in registros:
                logger.info(f"     - {reg[1]} em {reg[3]} Turma {reg[2]}")

        except Exception as e:
            logger.error(f"   ✗ Erro ao testar: {e}")
            conn.rollback()

        logger.info("\n✓ Processo concluído!")
        return True
    finally:
        try:
            cast(Any, cursor).close()
        except Exception:
            pass
        try:
            cast(Any, conn).close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
