-- ============================================================================
-- Migration 002: Criar tabelas de permissões
-- Fase 1 - Infraestrutura de Autenticação
-- Data: 2025-11-28
-- ============================================================================

-- Tabela de permissões disponíveis no sistema
CREATE TABLE IF NOT EXISTS permissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL COMMENT 'Código único da permissão (ex: alunos.criar)',
    descricao VARCHAR(200) NOT NULL COMMENT 'Descrição legível da permissão',
    modulo VARCHAR(50) NOT NULL COMMENT 'Módulo ao qual a permissão pertence',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_permissoes_codigo UNIQUE (codigo),
    INDEX idx_permissoes_modulo (modulo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Catálogo de permissões disponíveis no sistema';


-- ============================================================================
-- Tabela de relacionamento perfil-permissões
-- Define quais permissões cada perfil possui por padrão
-- ============================================================================
CREATE TABLE IF NOT EXISTS perfil_permissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    perfil ENUM('administrador', 'coordenador', 'professor') NOT NULL,
    permissao_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_perfil_permissao UNIQUE (perfil, permissao_id),
    CONSTRAINT fk_perfil_perm_permissao FOREIGN KEY (permissao_id) 
        REFERENCES permissoes(id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_perfil_perm_perfil (perfil)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Relacionamento entre perfis e suas permissões padrão';


-- ============================================================================
-- Tabela de permissões personalizadas por usuário (opcional)
-- Permite adicionar ou remover permissões específicas de um usuário
-- ============================================================================
CREATE TABLE IF NOT EXISTS usuario_permissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    permissao_id INT NOT NULL,
    tipo ENUM('adicionar', 'remover') NOT NULL DEFAULT 'adicionar' 
        COMMENT 'adicionar: dá permissão extra; remover: retira permissão do perfil',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_usuario_permissao UNIQUE (usuario_id, permissao_id),
    CONSTRAINT fk_usuario_perm_permissao FOREIGN KEY (permissao_id) 
        REFERENCES permissoes(id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_usuario_perm_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Permissões personalizadas por usuário (exceções ao perfil padrão)';
