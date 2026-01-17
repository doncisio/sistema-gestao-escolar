-- Migration: Criar tabela notas_finais
-- Data: 2026-01-17
-- Descrição: Tabela para armazenar médias finais anuais e notas de recuperação final
-- 
-- Esta tabela permite:
-- - Armazenar média anual (dos 4 bimestres)
-- - Armazenar nota de recuperação final
-- - Armazenar média final (após recuperação)
-- - Rastreamento de alterações via data_atualizacao

CREATE TABLE IF NOT EXISTS `notas_finais` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ano_letivo_id` int NOT NULL,
  `aluno_id` int NOT NULL,
  `disciplina_id` int NOT NULL,
  `media_anual` decimal(4,1) NOT NULL COMMENT 'Média dos 4 bimestres (multiplicada por 10)',
  `nota_recuperacao_final` decimal(4,1) DEFAULT NULL COMMENT 'Nota da recuperação final (multiplicada por 10)',
  `media_final` decimal(4,1) NOT NULL COMMENT 'Média final - após recuperação se houver (multiplicada por 10)',
  `data_atualizacao` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_aluno_disciplina_ano` (`aluno_id`,`disciplina_id`,`ano_letivo_id`),
  KEY `idx_aluno` (`aluno_id`),
  KEY `idx_disciplina` (`disciplina_id`),
  KEY `idx_ano_letivo` (`ano_letivo_id`),
  CONSTRAINT `fk_notas_finais_aluno` FOREIGN KEY (`aluno_id`) REFERENCES `alunos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_notas_finais_disciplina` FOREIGN KEY (`disciplina_id`) REFERENCES `disciplinas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_notas_finais_ano_letivo` FOREIGN KEY (`ano_letivo_id`) REFERENCES `anosletivos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `notas_finais_chk_1` CHECK (((`media_anual` >= 0.0) and (`media_anual` <= 100.0))),
  CONSTRAINT `notas_finais_chk_2` CHECK (((`media_final` >= 0.0) and (`media_final` <= 100.0))),
  CONSTRAINT `notas_finais_chk_3` CHECK (((`nota_recuperacao_final` IS NULL) OR ((`nota_recuperacao_final` >= 0.0) and (`nota_recuperacao_final` <= 100.0))))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
COMMENT='Armazena médias finais anuais e notas de recuperação final';

-- Criar índice composto para otimizar consultas frequentes
CREATE INDEX `idx_notas_finais_lookup` ON `notas_finais` (`ano_letivo_id`, `aluno_id`, `disciplina_id`);
