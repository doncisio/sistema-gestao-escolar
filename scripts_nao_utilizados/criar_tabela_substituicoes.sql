-- Criar tabela para registrar as substituições de professores em licença
CREATE TABLE IF NOT EXISTS `substituicoes_professores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `professor_id` int NOT NULL COMMENT 'ID do professor substituto',
  `substituido_id` int NOT NULL COMMENT 'ID do professor em licença que está sendo substituído',
  `data_inicio` date NOT NULL COMMENT 'Data de início da substituição',
  `data_fim` date DEFAULT NULL COMMENT 'Data de fim da substituição (NULL se ainda ativa)',
  `observacao` text,
  PRIMARY KEY (`id`),
  KEY `fk_professor_substituto` (`professor_id`),
  KEY `fk_professor_substituido` (`substituido_id`),
  CONSTRAINT `fk_professor_substituto` FOREIGN KEY (`professor_id`) REFERENCES `funcionarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_professor_substituido` FOREIGN KEY (`substituido_id`) REFERENCES `funcionarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Criar ou atualizar uma view para ver professores em licença e seus substitutos
CREATE OR REPLACE VIEW `view_professores_licenca_substitutos` AS
SELECT 
    l.id AS licenca_id,
    f.id AS professor_id,
    f.nome AS professor_nome,
    f.polivalente AS professor_polivalente,
    f.turma AS turma_id,
    t.nome AS turma_nome,
    s.nome AS serie_nome,
    l.motivo AS motivo_licenca,
    l.data_inicio AS licenca_inicio,
    l.data_fim AS licenca_fim,
    sp.id AS substituicao_id,
    fs.id AS substituto_id,
    fs.nome AS substituto_nome,
    fs.vinculo AS substituto_vinculo,
    fs.polivalente AS substituto_polivalente,
    sp.data_inicio AS substituicao_inicio,
    sp.data_fim AS substituicao_fim
FROM 
    licencas l
JOIN 
    funcionarios f ON l.funcionario_id = f.id
LEFT JOIN 
    turmas t ON f.turma = t.id
LEFT JOIN 
    serie s ON t.serie_id = s.id
LEFT JOIN 
    substituicoes_professores sp ON f.id = sp.substituido_id AND (
        (l.data_inicio <= sp.data_inicio AND l.data_fim >= sp.data_inicio) OR
        (sp.data_fim IS NULL AND CURRENT_DATE() BETWEEN l.data_inicio AND l.data_fim)
    )
LEFT JOIN 
    funcionarios fs ON sp.professor_id = fs.id
WHERE 
    f.cargo = 'Professor@'
    AND f.polivalente = 'sim'
ORDER BY
    l.data_inicio DESC, f.nome; 