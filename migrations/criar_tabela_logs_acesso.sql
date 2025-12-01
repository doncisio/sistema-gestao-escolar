-- =====================================================
-- Script para criar tabela de logs de acesso
-- Sistema de Gestão Escolar - Fase 5: Gestão de Usuários
-- =====================================================

-- Tabela de logs de acesso do sistema
CREATE TABLE IF NOT EXISTS logs_acesso (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT UNSIGNED NOT NULL,
    acao VARCHAR(100) NOT NULL,
    detalhes TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices para consultas frequentes
    INDEX idx_usuario_id (usuario_id),
    INDEX idx_acao (acao),
    INDEX idx_created_at (created_at),
    
    -- Foreign key para tabela de usuários
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Exemplos de ações que serão registradas:
-- - login: Login bem-sucedido
-- - login_falha: Tentativa de login com falha
-- - logout: Logout do sistema
-- - criar_usuario: Criação de novo usuário
-- - atualizar_usuario: Atualização de dados de usuário
-- - desativar_usuario: Desativação de usuário
-- - ativar_usuario: Ativação de usuário
-- - resetar_senha: Reset de senha de usuário
-- - acesso_negado: Tentativa de acesso a recurso não permitido
