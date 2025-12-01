-- Script para remover a limitação de professores polivalentes terem disciplinas
-- Data: 22/10/2025
-- Autor: Sistema de Gestão Escolar

-- =============================================================================
-- IMPORTANTE: Execute este script no banco de dados para remover a limitação
-- =============================================================================

USE redeescola;

-- Passo 1: Remover a trigger antiga que impedia professores polivalentes de ter disciplinas
DROP TRIGGER IF EXISTS `verificar_disciplina_funcionario`;

-- Passo 2: Criar nova trigger que permite todos os professores terem disciplinas
-- A nova trigger apenas verifica se é um professor, sem restrição sobre polivalente
DELIMITER ;;

CREATE TRIGGER `verificar_disciplina_funcionario` 
BEFORE INSERT ON `funcionario_disciplinas` 
FOR EACH ROW 
BEGIN
    DECLARE cargo_professor VARCHAR(100);

    -- Buscar o cargo do funcionário
    SELECT cargo INTO cargo_professor 
    FROM funcionarios 
    WHERE id = NEW.funcionario_id;

    -- Verificar se é um professor (permitindo tanto polivalentes quanto não polivalentes)
    IF cargo_professor != 'Professor@' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Somente Professores podem ter disciplinas associadas';
    END IF;
END;;

DELIMITER ;

-- =============================================================================
-- Resultado Esperado:
-- - Professores NÃO polivalentes: podem ter disciplinas (como antes)
-- - Professores polivalentes: AGORA podem ter disciplinas (nova funcionalidade)
-- - Outros funcionários: NÃO podem ter disciplinas (mantém a segurança)
-- =============================================================================

-- Verificar se a trigger foi criada corretamente
SHOW TRIGGERS FROM redeescola WHERE `Table` = 'funcionario_disciplinas';

-- Teste opcional: Verificar se há professores polivalentes no sistema
SELECT 
    id,
    nome,
    cargo,
    polivalente,
    volante
FROM funcionarios 
WHERE cargo = 'Professor@' AND polivalente = 'sim';

-- Mensagem de sucesso
SELECT 'Limitação removida com sucesso! Professores polivalentes agora podem ter disciplinas associadas.' AS Status;
