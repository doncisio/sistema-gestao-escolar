-- ============================================================================
-- Migration 001: Criar tabela de usuários do sistema
-- Fase 1 - Infraestrutura de Autenticação
-- Data: 2025-11-28
-- ============================================================================

-- Tabela de usuários do sistema
-- Cada usuário é vinculado a um funcionário existente
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    funcionario_id INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    perfil ENUM('administrador', 'coordenador', 'professor') NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    primeiro_acesso BOOLEAN DEFAULT TRUE COMMENT 'Indica se usuário precisa trocar senha no primeiro login',
    ultimo_acesso DATETIME NULL,
    tentativas_login INT DEFAULT 0 COMMENT 'Contador de tentativas de login falhas',
    bloqueado_ate DATETIME NULL COMMENT 'Data/hora até quando o usuário está bloqueado',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT uk_usuarios_username UNIQUE (username),
    CONSTRAINT uk_usuarios_funcionario UNIQUE (funcionario_id),
    CONSTRAINT fk_usuarios_funcionario FOREIGN KEY (funcionario_id) 
        REFERENCES funcionarios(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    
    -- Índices
    INDEX idx_usuarios_username (username),
    INDEX idx_usuarios_perfil (perfil),
    INDEX idx_usuarios_ativo (ativo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Usuários do sistema com autenticação e perfis de acesso';


-- ============================================================================
-- Tabela de logs de acesso
-- Registra todas as ações de login/logout e ações importantes
-- ============================================================================
CREATE TABLE IF NOT EXISTS logs_acesso (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL COMMENT 'NULL para tentativas de login com usuário inexistente',
    username_tentativa VARCHAR(50) NULL COMMENT 'Username usado na tentativa (para auditoria)',
    acao VARCHAR(100) NOT NULL COMMENT 'Tipo de ação: login, logout, login_falha, etc',
    detalhes TEXT NULL COMMENT 'Detalhes adicionais da ação',
    ip_address VARCHAR(45) NULL COMMENT 'Endereço IP (suporta IPv6)',
    user_agent VARCHAR(255) NULL COMMENT 'Informações do navegador/sistema',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para consultas de auditoria
    INDEX idx_logs_usuario (usuario_id),
    INDEX idx_logs_acao (acao),
    INDEX idx_logs_data (created_at),
    INDEX idx_logs_username (username_tentativa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Logs de acesso e auditoria do sistema';


-- ============================================================================
-- Tabela de sessões ativas (opcional, para controle de sessões)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessoes_usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    token_sessao VARCHAR(255) NOT NULL COMMENT 'Token único da sessão',
    ip_address VARCHAR(45) NULL,
    iniciada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expira_em TIMESTAMP NOT NULL,
    ativa BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT uk_sessoes_token UNIQUE (token_sessao),
    
    INDEX idx_sessoes_usuario (usuario_id),
    INDEX idx_sessoes_expira (expira_em),
    INDEX idx_sessoes_ativa (ativa)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Controle de sessões ativas dos usuários';
