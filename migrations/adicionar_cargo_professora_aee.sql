-- Migration: adicionar cargo "Professora de Atendimento Educacional Especializado (AEE)"
-- Data: 2026-03-05

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
    'Vigia Noturno',
    'Interprete de Libras'
) NULL DEFAULT NULL;
