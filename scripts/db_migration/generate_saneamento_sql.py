#!/usr/bin/env python3
"""Gera scripts SQL de saneamento em db/migrations:
- backup_turmas.sql (copia turmas afetadas)
- saneamento_turmas.sql (atualiza nomes vazios)
- backup_notas_duplicadas.sql (copia notas duplicadas)
- saneamento_notas_duplicadas.sql (deleta duplicadas mantendo menor id)
- saneamento_matriculas_data.sql (backup + update para data_matricula NULL)
"""
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'db', 'migrations')
OUT_DIR = os.path.normpath(OUT_DIR)
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR, exist_ok=True)

# 1) Turmas: backup e update nomes vazios
bk_turmas = os.path.join(OUT_DIR, 'saneamento_backup_turmas.sql')
upd_turmas = os.path.join(OUT_DIR, 'saneamento_turmas.sql')
with open(bk_turmas,'w',encoding='utf-8') as f:
    f.write("-- Backup das turmas com nome NULL ou vazio\n")
    f.write("CREATE TABLE IF NOT EXISTS backup_turmas_semdados AS SELECT * FROM turmas WHERE nome IS NULL OR TRIM(nome) = '';\n")
with open(upd_turmas,'w',encoding='utf-8') as f:
    f.write("-- Preencher nomes vazios em turmas com 'Turma_<id>'\n")
    f.write("UPDATE turmas SET nome = CONCAT('Turma_', id) WHERE nome IS NULL OR TRIM(nome) = '';\n")

# 2) Notas duplicadas: backup e delete mantendo menor id (keeps first)
bk_notas = os.path.join(OUT_DIR, 'saneamento_backup_notas_duplicadas.sql')
del_notas = os.path.join(OUT_DIR, 'saneamento_notas_duplicadas.sql')
with open(bk_notas,'w',encoding='utf-8') as f:
    f.write("-- Backup das notas duplicadas por aluno,disciplina,bimestre,ano_letivo\n")
    f.write("CREATE TABLE IF NOT EXISTS backup_notas_duplicadas AS SELECT n.* FROM notas n WHERE (n.aluno_id, n.disciplina_id, n.bimestre, n.ano_letivo_id) IN (SELECT aluno_id, disciplina_id, bimestre, ano_letivo_id FROM notas GROUP BY aluno_id, disciplina_id, bimestre, ano_letivo_id HAVING COUNT(*)>1);\n")
with open(del_notas,'w',encoding='utf-8') as f:
    f.write("-- Deleta notas duplicadas mantendo a menor id (ajuste se preferir outra regra)\n")
    f.write("DELETE n FROM notas n\n")
    f.write("INNER JOIN (\n")
    f.write("  SELECT MIN(id) as keep_id, aluno_id, disciplina_id, bimestre, ano_letivo_id\n")
    f.write("  FROM notas\n")
    f.write("  GROUP BY aluno_id, disciplina_id, bimestre, ano_letivo_id\n")
    f.write("  HAVING COUNT(*) > 1\n")
    f.write(") dup ON n.aluno_id = dup.aluno_id AND n.disciplina_id = dup.disciplina_id AND n.bimestre = dup.bimestre AND n.ano_letivo_id = dup.ano_letivo_id\n")
    f.write("WHERE n.id <> dup.keep_id;\n")

# 3) Matriculas: backup e preencher data_matricula NULL com uma data placeholder
bk_mat = os.path.join(OUT_DIR, 'saneamento_backup_matriculas.sql')
upd_mat = os.path.join(OUT_DIR, 'saneamento_matriculas_data.sql')
with open(bk_mat,'w',encoding='utf-8') as f:
    f.write("-- Backup das matriculas com data_matricula NULL\n")
    f.write("CREATE TABLE IF NOT EXISTS backup_matriculas_null_data AS SELECT * FROM matriculas WHERE data_matricula IS NULL;\n")
with open(upd_mat,'w',encoding='utf-8') as f:
    f.write("-- Atualiza matriculas com data_matricula NULL para '2024-01-01' (ajuste conforme politica)\n")
    f.write("UPDATE matriculas SET data_matricula = '2024-01-01' WHERE data_matricula IS NULL;\n")

print('Arquivos gerados em:', OUT_DIR)
print('- ' + os.path.basename(bk_turmas))
print('- ' + os.path.basename(upd_turmas))
print('- ' + os.path.basename(bk_notas))
print('- ' + os.path.basename(del_notas))
print('- ' + os.path.basename(bk_mat))
print('- ' + os.path.basename(upd_mat))
print('\nRevise os arquivos antes de aplicar. Ajuste a regra de manutenção de duplicatas se preferir (por ex. manter a nota maior ou a mais recente).')
