# Melhorias propostas para o banco redeescola

Contexto: dump MySQL 8.0 em backups/backup_redeescola.sql com tabelas de diario escolar (alunos, matriculas, turmas, notas, sessoes, logs, etc.). Sugestoes abaixo priorizam integridade, performance e operacao.

## Itens de prioridade alta
- Padronizar charset/collation para utf8mb4_0900_ai_ci em todas as tabelas (ex.: logs_acesso usa utf8mb4_unicode_ci). Evita comparacoes inconsistentes e problemas de ordenacao/filtro.
- Garantir nome/identificacao obrigatorios em turmas (campo nome hoje NULL/" " em varios registros) e evitar strings vazias. Tornar NOT NULL com constraint de formato.
- Impor unicidade de turma por escola+ano letivo+serie+turno+nome (unique key) para evitar turmas duplicadas com nomes vazios.
- Matriculas: tornar data_matricula NOT NULL, validar que aluno_id, turma_id e ano_letivo_id nao fiquem NULL em matriculas ativas. Rever acao de FK para evitar registros orfaos em exclusao de alunos/turmas.
- Notas: transformar idx_notas_completo em UNIQUE (aluno_id, disciplina_id, bimestre, ano_letivo_id) para impedir notas duplicadas por bimestre/disciplina. Avaliar uso de DECIMAL(5,2) se notas puderem ter casas decimais adicionais.
- Revisar enums que guardam dominio de negocio (status, turno, bimestre, racas) para tabelas de referencia (dimensoes) com FK; facilita manutencao e consistencia entre tabelas.

## Integridade e qualidade de dados
- Remover defaults opinativos (ex.: alunos.local_nascimento = "Paco do Lumiar" e descricao_transtorno = "Nenhum"); trocar por NOT NULL + valor explicito ou tabela de dominios.
- Corrigir comentarios com caracteres truncados ("transfer??ncia" em matriculas) indicando problema de collation/encoding no script; ajustar fonte dos scripts/migrations.
- Harmonizar regras de exclusao: hoje matriculas/notas nao possuem ON DELETE e podem impedir limpeza ou gerar orfaos. Definir estrategia: soft delete (flag ativo) ou ON DELETE CASCADE/SET NULL conforme o dominio permitir.
- Adicionar campos de trilha (created_at, updated_at, deleted_at) nas tabelas criticas que ainda nao possuem (alunos, matriculas, turmas, notas) com triggers ou defaults.

## Performance e indexacao
- Matriculas: criar idx(turma_id, status) e idx(ano_letivo_id, status) para consultas por turma/ano e situacao; manter unique aluno+ano_letivo existente.
- Turmas: idx(escola_id, ano_letivo_id, serie_id) para alocar alunos/consultar oferta por escola/ano.
- Logs_acesso: manter idx(created_at) ja existente, mas considerar particionar/arquivar por data ou mover para schema de auditoria com TTL para evitar crescimento desnecessario.
- Sessoes_usuario: adicionar idx(usuario_id, ativa) para invalidacao rapida de sessoes; ja existe idx em expira_em e token unico.

## Modelagem/limpeza
- Tabelas duplicadas: existe documentos_emitidos e documentosemitidos; consolidar em uma unica tabela e migrar dados, mantendo historico via view ou tabela legado.
- Normalizar telefone/email de setores e responsaveis em tabelas proprias para reutilizar e aplicar validacao.
- Separar responsaveis por aluno em tabela unica com relacao N:N clara (responsaveisalunos) e constraints de unicidade por tipo de responsavel.

## Operacao e governanca
- Adotar ciclo de migrations versionadas (pasta db/migrations) como fonte da verdade, evitando divergencia com dumps manuais.
- Criar checklist de integridade periodica: busca por NULL indevidos, turmas com nome vazio, matriculas com combinacoes repetidas, notas duplicadas.
- Automatizar backup com consistencia (mysqldump com --single-transaction) e restauracao testada; manter scripts de verificacao de checksum dos dumps.

## Proximos passos recomendados
1) Definir collation/charset padrao e aplicar em ambiente de staging, verificando impacto em buscas FULLTEXT (alunos.nome).
2) Criar migrations para constraints propostas (unicidades, NOT NULL, novas FKs) e rodar scripts de saneamento para limpar registros com valores vazios.
3) Consolidar tabelas duplicadas e revisar enums/dominios migrando para tabelas de dimensao.
4) Ajustar monitoracao: rotacionar logs_acesso e criar rotina de limpeza de sessoes expiradas.
