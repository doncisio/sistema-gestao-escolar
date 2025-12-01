-- ============================================
-- Script para Resolver Erro 1419
-- Sistema de Gestão Escolar
-- ============================================

-- EXECUTE ESTE SCRIPT COMO ROOT OU USUÁRIO COM PRIVILÉGIO SUPER

-- Verificar configuração atual
SELECT 'Verificando configuracao atual...' AS Status;
SHOW VARIABLES LIKE 'log_bin_trust_function_creators';
SHOW VARIABLES LIKE 'log_bin';

-- Habilitar criação de functions/procedures sem privilégio SUPER
SELECT 'Habilitando log_bin_trust_function_creators...' AS Status;
SET GLOBAL log_bin_trust_function_creators=1;

-- Verificar se foi aplicado
SELECT 'Verificando se foi aplicado...' AS Status;
SHOW VARIABLES LIKE 'log_bin_trust_function_creators';

-- Informar resultado
SELECT 
    CASE 
        WHEN @@GLOBAL.log_bin_trust_function_creators = 1 
        THEN 'SUCESSO: Configuracao aplicada. Agora voce pode restaurar backups normalmente.'
        ELSE 'ERRO: Configuracao nao foi aplicada. Verifique seus privilegios.'
    END AS Resultado;

-- NOTA: Esta configuração será perdida após reiniciar o MySQL
-- Para tornar permanente, adicione ao arquivo my.ini:
-- [mysqld]
-- log_bin_trust_function_creators=1
