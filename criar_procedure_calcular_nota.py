"""
Script para criar a procedure calcular_nota_avaliacao_aluno
Autor: Sistema de Gestão Escolar
Data: 14/12/2025
"""

from config_logs import get_logger
logger = get_logger(__name__)

from conexao import conectar_bd

def criar_procedure():
    """Cria a procedure para cálculo de nota."""
    print("\n" + "="*80)
    print(" CRIANDO PROCEDURE: calcular_nota_avaliacao_aluno")
    print("="*80 + "\n")
    
    conn = conectar_bd()
    if not conn:
        print("❌ Falha ao conectar ao banco")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Dropar se existir
        print("Removendo procedure anterior (se existir)...")
        cursor.execute("DROP PROCEDURE IF EXISTS calcular_nota_avaliacao_aluno")
        
        # Criar procedure
        sql = """
CREATE PROCEDURE calcular_nota_avaliacao_aluno(
    IN p_avaliacao_aluno_id BIGINT UNSIGNED
)
BEGIN
    DECLARE v_pontuacao_obtida DECIMAL(5,2);
    DECLARE v_pontuacao_maxima DECIMAL(5,2);
    DECLARE v_nota_total DECIMAL(5,2);
    DECLARE v_percentual DECIMAL(5,2);
    DECLARE v_todas_corrigidas BOOLEAN;
    
    -- Somar pontuação obtida e máxima
    SELECT 
        COALESCE(SUM(pontuacao_obtida), 0),
        COALESCE(SUM(pontuacao_maxima), 0),
        MIN(CASE WHEN status != 'corrigida' THEN 0 ELSE 1 END) = 1
    INTO 
        v_pontuacao_obtida,
        v_pontuacao_maxima,
        v_todas_corrigidas
    FROM respostas_questoes
    WHERE avaliacao_aluno_id = p_avaliacao_aluno_id;
    
    -- Calcular percentual e nota (escala 0-10)
    IF v_pontuacao_maxima > 0 THEN
        SET v_percentual = (v_pontuacao_obtida / v_pontuacao_maxima) * 100;
        SET v_nota_total = (v_pontuacao_obtida / v_pontuacao_maxima) * 10;
    ELSE
        SET v_percentual = 0;
        SET v_nota_total = 0;
    END IF;
    
    -- Atualizar registro
    UPDATE avaliacoes_alunos
    SET 
        pontuacao_obtida = v_pontuacao_obtida,
        pontuacao_maxima = v_pontuacao_maxima,
        nota_total = v_nota_total,
        percentual_acerto = v_percentual,
        status = CASE 
            WHEN v_todas_corrigidas THEN 'corrigida'
            ELSE status
        END,
        corrigido_em = CASE 
            WHEN v_todas_corrigidas AND corrigido_em IS NULL THEN NOW()
            ELSE corrigido_em
        END
    WHERE id = p_avaliacao_aluno_id;
END
        """
        
        print("Criando procedure...")
        cursor.execute(sql)
        conn.commit()
        
        print("\n✅ Procedure criada com sucesso!\n")
        
        # Testar se foi criada
        cursor.execute("SHOW PROCEDURE STATUS WHERE Name = 'calcular_nota_avaliacao_aluno'")
        resultado = cursor.fetchone()
        
        if resultado:
            print(f"✅ Validação: Procedure encontrada no banco")
            print(f"   Database: {resultado[0]}")
            print(f"   Name: {resultado[1]}")
            print(f"   Type: {resultado[2]}")
            return True
        else:
            print("❌ Erro: Procedure não encontrada após criação")
            return False
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro ao criar procedure: {e}")
        logger.error(f"Erro: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import sys
    sucesso = criar_procedure()
    sys.exit(0 if sucesso else 1)
