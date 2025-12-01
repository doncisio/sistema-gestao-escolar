-- Script para adicionar colunas de escola origem e destino nas matrículas
-- Para registrar de qual escola o aluno veio (transferência recebida) 
-- e para qual escola o aluno foi (transferência expedida)

-- Adicionar coluna escola_origem_id (escola de onde o aluno veio)
ALTER TABLE `matriculas` 
ADD COLUMN `escola_origem_id` INT NULL COMMENT 'ID da escola de origem em caso de transferência recebida' AFTER `status`,
ADD CONSTRAINT `fk_matriculas_escola_origem` 
    FOREIGN KEY (`escola_origem_id`) 
    REFERENCES `escolas` (`id`) 
    ON DELETE SET NULL 
    ON UPDATE CASCADE;

-- Adicionar coluna escola_destino_id (escola para onde o aluno foi)
ALTER TABLE `matriculas` 
ADD COLUMN `escola_destino_id` INT NULL COMMENT 'ID da escola de destino em caso de transferência expedida' AFTER `escola_origem_id`,
ADD CONSTRAINT `fk_matriculas_escola_destino` 
    FOREIGN KEY (`escola_destino_id`) 
    REFERENCES `escolas` (`id`) 
    ON DELETE SET NULL 
    ON UPDATE CASCADE;

-- Criar índices para melhorar performance das consultas
CREATE INDEX `idx_escola_origem` ON `matriculas` (`escola_origem_id`);
CREATE INDEX `idx_escola_destino` ON `matriculas` (`escola_destino_id`);

-- Comentário sobre o uso das colunas:
-- escola_origem_id: Usado quando o aluno é RECEBIDO de outra escola (transferência recebida)
-- escola_destino_id: Usado quando o aluno é TRANSFERIDO para outra escola (transferência expedida)
