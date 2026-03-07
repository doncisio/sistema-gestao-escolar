-- Migration: Renomear cargo 'Tutor/Cuidador' para 'Tutor'
-- Data: 2026-03-06

-- Passo 1: Adiciona 'Tutor' ao ENUM mantendo 'Tutor/Cuidador' temporariamente
ALTER TABLE funcionarios
  MODIFY COLUMN cargo ENUM(
    'Administrador do Sistemas',
    'Gestor Escolar',
    'Professor@',
    'Professora de Atendimento Educacional Especializado (AEE)',
    'Auxiliar administrativo',
    'Agente de Portaria',
    'Merendeiro',
    'Auxiliar de serviços gerais',
    'Técnico em Administração Escolar',
    'Especialista (Coordenadora)',
    'Tutor/Cuidador',
    'Tutor',
    'Vigia Noturno',
    'Interprete de Libras'
  );

-- Passo 2: Atualiza os registros existentes
UPDATE funcionarios SET cargo = 'Tutor' WHERE cargo = 'Tutor/Cuidador';

-- Passo 3: Remove 'Tutor/Cuidador' do ENUM
ALTER TABLE funcionarios
  MODIFY COLUMN cargo ENUM(
    'Administrador do Sistemas',
    'Gestor Escolar',
    'Professor@',
    'Professora de Atendimento Educacional Especializado (AEE)',
    'Auxiliar administrativo',
    'Agente de Portaria',
    'Merendeiro',
    'Auxiliar de serviços gerais',
    'Técnico em Administração Escolar',
    'Especialista (Coordenadora)',
    'Tutor',
    'Vigia Noturno',
    'Interprete de Libras'
  );

