-- ============================================================================
-- Migration 003: Inserir permissões base do sistema
-- Fase 1 - Infraestrutura de Autenticação
-- Data: 2025-11-28
-- ============================================================================

-- Limpar permissões existentes (para reexecução segura)
-- SET FOREIGN_KEY_CHECKS = 0;
-- TRUNCATE TABLE perfil_permissoes;
-- TRUNCATE TABLE permissoes;
-- SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- INSERIR TODAS AS PERMISSÕES DO SISTEMA
-- ============================================================================

INSERT INTO permissoes (codigo, descricao, modulo) VALUES

-- Módulo Alunos
('alunos.visualizar', 'Visualizar lista de alunos', 'alunos'),
('alunos.visualizar_proprios', 'Visualizar apenas alunos das próprias turmas', 'alunos'),
('alunos.criar', 'Cadastrar novos alunos', 'alunos'),
('alunos.editar', 'Editar dados de alunos', 'alunos'),
('alunos.excluir', 'Excluir alunos do sistema', 'alunos'),
('alunos.documentos', 'Gerar documentos de alunos (declarações, etc)', 'alunos'),
('alunos.historico', 'Visualizar e gerar histórico escolar', 'alunos'),
('alunos.transferencia', 'Realizar transferência de alunos', 'alunos'),

-- Módulo Funcionários
('funcionarios.visualizar', 'Visualizar lista de funcionários', 'funcionarios'),
('funcionarios.criar', 'Cadastrar novos funcionários', 'funcionarios'),
('funcionarios.editar', 'Editar dados de funcionários', 'funcionarios'),
('funcionarios.excluir', 'Excluir funcionários do sistema', 'funcionarios'),
('funcionarios.documentos', 'Gerar documentos de funcionários', 'funcionarios'),
('funcionarios.licencas', 'Gerenciar licenças de funcionários', 'funcionarios'),

-- Módulo Turmas
('turmas.visualizar', 'Visualizar todas as turmas', 'turmas'),
('turmas.visualizar_proprias', 'Visualizar apenas turmas próprias (professor)', 'turmas'),
('turmas.criar', 'Criar novas turmas', 'turmas'),
('turmas.editar', 'Editar dados de turmas', 'turmas'),
('turmas.excluir', 'Excluir turmas', 'turmas'),
('turmas.gerenciar_alunos', 'Adicionar/remover alunos de turmas', 'turmas'),

-- Módulo Matrículas
('matriculas.visualizar', 'Visualizar matrículas', 'matriculas'),
('matriculas.criar', 'Realizar novas matrículas', 'matriculas'),
('matriculas.editar', 'Editar matrículas existentes', 'matriculas'),
('matriculas.cancelar', 'Cancelar matrículas', 'matriculas'),

-- Módulo Notas
('notas.visualizar', 'Visualizar notas de todos os alunos', 'notas'),
('notas.visualizar_proprias', 'Visualizar notas apenas das próprias turmas', 'notas'),
('notas.lancar', 'Lançar notas em qualquer turma', 'notas'),
('notas.lancar_proprias', 'Lançar notas apenas nas próprias turmas', 'notas'),
('notas.editar', 'Editar notas já lançadas (qualquer turma)', 'notas'),
('notas.editar_proprias', 'Editar notas apenas das próprias turmas', 'notas'),

-- Módulo Frequência
('frequencia.visualizar', 'Visualizar frequência de todos os alunos', 'frequencia'),
('frequencia.visualizar_proprias', 'Visualizar frequência apenas das próprias turmas', 'frequencia'),
('frequencia.lancar', 'Lançar frequência em qualquer turma', 'frequencia'),
('frequencia.lancar_proprias', 'Lançar frequência apenas nas próprias turmas', 'frequencia'),
('frequencia.editar', 'Editar frequência já lançada', 'frequencia'),

-- Módulo Relatórios
('relatorios.visualizar', 'Acessar módulo de relatórios', 'relatorios'),
('relatorios.gerar_todos', 'Gerar relatórios de toda a escola', 'relatorios'),
('relatorios.gerar_proprios', 'Gerar relatórios apenas das próprias turmas', 'relatorios'),
('relatorios.atas', 'Gerar atas de resultados', 'relatorios'),
('relatorios.listas', 'Gerar listas de alunos', 'relatorios'),
('relatorios.boletins', 'Gerar boletins de alunos', 'relatorios'),

-- Módulo Dashboard
('dashboard.visualizar', 'Visualizar dashboard', 'dashboard'),
('dashboard.completo', 'Visualizar dashboard completo da escola', 'dashboard'),
('dashboard.pedagogico', 'Visualizar dashboard pedagógico', 'dashboard'),
('dashboard.proprio', 'Visualizar dashboard das próprias turmas', 'dashboard'),

-- Módulo Sistema/Administração
('sistema.configuracoes', 'Acessar configurações do sistema', 'sistema'),
('sistema.backup', 'Realizar backup do banco de dados', 'sistema'),
('sistema.transicao_ano', 'Executar transição de ano letivo', 'sistema'),
('sistema.usuarios', 'Gerenciar usuários do sistema', 'sistema'),
('sistema.logs', 'Visualizar logs de acesso', 'sistema'),

-- Módulo BNCC/Pedagógico (para futuras implementações)
('bncc.visualizar', 'Visualizar habilidades BNCC', 'bncc'),
('bncc.relatorios', 'Gerar relatórios por habilidades BNCC', 'bncc'),
('questoes.criar', 'Criar questões no banco de questões', 'questoes'),
('questoes.editar_proprias', 'Editar apenas questões próprias', 'questoes'),
('questoes.editar_todas', 'Editar qualquer questão', 'questoes'),
('questoes.aprovar', 'Aprovar questões para uso', 'questoes'),
('avaliacoes.criar', 'Criar avaliações', 'avaliacoes'),
('avaliacoes.aplicar', 'Aplicar avaliações nas turmas', 'avaliacoes')

ON DUPLICATE KEY UPDATE descricao = VALUES(descricao), modulo = VALUES(modulo);


-- ============================================================================
-- CONFIGURAR PERMISSÕES POR PERFIL
-- ============================================================================

-- Limpar configurações anteriores
DELETE FROM perfil_permissoes;

-- ============================================================================
-- PERFIL: ADMINISTRADOR (acesso total)
-- ============================================================================
INSERT INTO perfil_permissoes (perfil, permissao_id)
SELECT 'administrador', id FROM permissoes;


-- ============================================================================
-- PERFIL: COORDENADOR (acesso pedagógico, sem funções administrativas críticas)
-- ============================================================================
INSERT INTO perfil_permissoes (perfil, permissao_id)
SELECT 'coordenador', id FROM permissoes WHERE codigo IN (
    -- Alunos: visualizar e documentos, sem criar/editar/excluir
    'alunos.visualizar',
    'alunos.documentos',
    'alunos.historico',
    
    -- Funcionários: apenas visualizar
    'funcionarios.visualizar',
    
    -- Turmas: visualizar todas
    'turmas.visualizar',
    
    -- Matrículas: visualizar
    'matriculas.visualizar',
    
    -- Notas: visualizar todas (acompanhamento pedagógico)
    'notas.visualizar',
    
    -- Frequência: visualizar todas
    'frequencia.visualizar',
    
    -- Relatórios: acesso completo
    'relatorios.visualizar',
    'relatorios.gerar_todos',
    'relatorios.atas',
    'relatorios.listas',
    'relatorios.boletins',
    
    -- Dashboard: completo e pedagógico
    'dashboard.visualizar',
    'dashboard.completo',
    'dashboard.pedagogico',
    
    -- BNCC: acesso completo
    'bncc.visualizar',
    'bncc.relatorios',
    
    -- Questões: aprovar e visualizar
    'questoes.aprovar',
    'questoes.editar_todas',
    
    -- Avaliações: criar e aplicar
    'avaliacoes.criar',
    'avaliacoes.aplicar'
);


-- ============================================================================
-- PERFIL: PROFESSOR (acesso restrito às próprias turmas)
-- ============================================================================
INSERT INTO perfil_permissoes (perfil, permissao_id)
SELECT 'professor', id FROM permissoes WHERE codigo IN (
    -- Alunos: visualizar apenas das próprias turmas
    'alunos.visualizar_proprios',
    
    -- Turmas: visualizar apenas próprias
    'turmas.visualizar_proprias',
    
    -- Notas: lançar e editar apenas nas próprias turmas
    'notas.visualizar_proprias',
    'notas.lancar_proprias',
    'notas.editar_proprias',
    
    -- Frequência: lançar apenas nas próprias turmas
    'frequencia.visualizar_proprias',
    'frequencia.lancar_proprias',
    
    -- Relatórios: apenas das próprias turmas
    'relatorios.visualizar',
    'relatorios.gerar_proprios',
    'relatorios.boletins',
    
    -- Dashboard: apenas próprio
    'dashboard.visualizar',
    'dashboard.proprio',
    
    -- BNCC: visualizar
    'bncc.visualizar',
    
    -- Questões: criar e editar próprias
    'questoes.criar',
    'questoes.editar_proprias',
    
    -- Avaliações: criar e aplicar
    'avaliacoes.criar',
    'avaliacoes.aplicar'
);


-- ============================================================================
-- VERIFICAÇÃO
-- ============================================================================
-- SELECT perfil, COUNT(*) as total_permissoes 
-- FROM perfil_permissoes 
-- GROUP BY perfil;
