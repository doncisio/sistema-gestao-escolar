USE `redeescola`;

-- Migration: adicionar colunas parsed para os códigos BNCC
-- Observação: alguns servidores MySQL não aceitam várias adições em único ALTER ou
-- a cláusula IF NOT EXISTS em CREATE INDEX. Por compatibilidade, usamos ALTERs separados.
-- Cria a tabela base caso não exista (definição mínima)
CREATE TABLE IF NOT EXISTS `bncc_habilidades` (
	`id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
	`codigo` VARCHAR(60) NOT NULL,
	`descricao` TEXT DEFAULT NULL,
	`created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	`updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	PRIMARY KEY (`id`),
	UNIQUE KEY `uk_bncc_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `bncc_habilidades` ADD COLUMN `etapa_sigla` VARCHAR(8) DEFAULT NULL COMMENT 'EI/EF/EM';
ALTER TABLE `bncc_habilidades` ADD COLUMN `grupo_faixa` VARCHAR(10) DEFAULT NULL COMMENT 'Grupo faixa etaria para EI (01,02,03)';
ALTER TABLE `bncc_habilidades` ADD COLUMN `campo_experiencias` VARCHAR(8) DEFAULT NULL COMMENT 'EO/CG/TS/EF/ET (para EI)';
ALTER TABLE `bncc_habilidades` ADD COLUMN `ano_bloco` VARCHAR(8) DEFAULT NULL COMMENT 'Ano ou bloco (p.ex. 01..09 ou 15,69 para EF)';
ALTER TABLE `bncc_habilidades` ADD COLUMN `componente_codigo` VARCHAR(8) DEFAULT NULL COMMENT 'Componente curricular (LP, MA, etc.)';
ALTER TABLE `bncc_habilidades` ADD COLUMN `em_competencia` TINYINT UNSIGNED DEFAULT NULL COMMENT 'Competência (para EM: 1..9)';
ALTER TABLE `bncc_habilidades` ADD COLUMN `em_sequencia` SMALLINT UNSIGNED DEFAULT NULL COMMENT 'Sequência da habilidade dentro da competência (para EM)';
ALTER TABLE `bncc_habilidades` ADD COLUMN `codigo_raw` VARCHAR(60) DEFAULT NULL COMMENT 'Código original (duplicado aqui para conveniência)';

-- Indexes para busca rápida
-- Criar índices apenas se não existirem (algumas versões do MySQL não aceitam IF NOT EXISTS)
-- Tentamos criar e ignoramos erro se já existir (cliente pode optar por manualmente verificar)
CREATE INDEX `idx_bncc_etapa` ON `bncc_habilidades` (`etapa_sigla`);
CREATE INDEX `idx_bncc_componente` ON `bncc_habilidades` (`componente_codigo`);
CREATE INDEX `idx_bncc_ano_bloco` ON `bncc_habilidades` (`ano_bloco`);

-- Atualização opcional: popular `codigo_raw` com `codigo` (execute após aplicar migration se desejar)
-- UPDATE bncc_habilidades SET codigo_raw = codigo;

-- OBS: revisar e ajustar nomes conforme necessidade local.
