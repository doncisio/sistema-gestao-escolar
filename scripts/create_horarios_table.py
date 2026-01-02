import sys
import os
# Garantir que o diretório do projeto esteja no path para importar `src`
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.core.conexao import conectar_bd

sql = """
CREATE TABLE IF NOT EXISTS horarios_importados (
  id INT AUTO_INCREMENT PRIMARY KEY,
  turma_id INT NOT NULL,
  dia VARCHAR(32) NOT NULL,
  horario VARCHAR(32) NOT NULL,
  valor TEXT NOT NULL,
  disciplina_id INT NULL,
  professor_id INT NULL,
  geduc_turma_id INT NULL,
  UNIQUE KEY ux_horario_turma (turma_id, dia, horario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

conn = conectar_bd()
if not conn:
    raise SystemExit("Não foi possível conectar ao banco para criar a tabela")

cur = conn.cursor()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
print("Tabela horarios_importados criada (ou já existia).")
