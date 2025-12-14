#!/usr/bin/env python3
"""
Teste rápido para executar o método interno `_buscar_dados_pedagogicos`
do `DashboardCoordenador` e imprimir o resultado ou exceção.

Execute a partir da raiz do repositório:
    powershell.exe -NoProfile -Command "python ./scripts/test_dashboard_coordenador.py"

Observação: o script usará as credenciais/configurações de DB do projeto.
"""

import os
import sys
import json
import traceback

# Garantir que o diretório raiz do projeto esteja no path para permitir imports locais
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def teste_conexao_db():
    try:
        from db.connection import get_cursor
        with get_cursor() as cur:
            cur.execute('SELECT 1 as ok')
            r = cur.fetchone()
            print('DB test:', r)
    except Exception:
        print('DB test exception:')
        traceback.print_exc()


def teste_queries(escola_id=60, ano_letivo=None):
    """Executa as mesmas queries do dashboard coordenador passo a passo e imprime resultados/exceções."""
    import datetime
    from db.connection import get_cursor

    try:
        with get_cursor() as cursor:
            # determinar ano letivo
            if ano_letivo is None:
                cursor.execute(
                    "SELECT ano_letivo FROM AnosLetivos WHERE CURDATE() BETWEEN data_inicio AND data_fim LIMIT 1"
                )
                r = cursor.fetchone()
                ano_letivo_val = r['ano_letivo'] if r else str(datetime.datetime.now().year)
            else:
                ano_letivo_val = ano_letivo

            print('Ano letivo determinado:', ano_letivo_val)

            queries = [
                ("Médias por disciplina", """
                    SELECT d.nome AS disciplina,
                           ROUND(AVG(n.nota), 2) AS media,
                           COUNT(DISTINCT n.aluno_id) AS total_alunos
                    FROM notas n
                    JOIN disciplinas d ON n.disciplina_id = d.id
                    JOIN matriculas m ON n.aluno_id = m.aluno_id 
                        AND n.ano_letivo_id = m.ano_letivo_id
                    JOIN alunos a ON n.aluno_id = a.id
                    WHERE n.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                    GROUP BY d.id, d.nome
                    ORDER BY media DESC
                """, (ano_letivo_val, escola_id)),

                ("Desempenho por série", """
                    SELECT 
                        s.nome AS serie,
                        ROUND(AVG(n.nota), 2) AS media,
                        COUNT(DISTINCT m.aluno_id) AS total_alunos
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    JOIN alunos a ON m.aluno_id = a.id
                    LEFT JOIN notas n ON m.aluno_id = n.aluno_id 
                        AND m.ano_letivo_id = n.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                    GROUP BY s.id, s.nome
                    ORDER BY s.nome
                """, (ano_letivo_val, escola_id)),

                ("Alunos baixo desempenho", """
                    SELECT 
                        a.nome AS aluno,
                        s.nome AS serie,
                        t.nome AS turma,
                        ROUND(AVG(n.nota), 2) AS media_geral
                    FROM alunos a
                    JOIN matriculas m ON a.id = m.aluno_id
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = m.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                    GROUP BY a.id, a.nome, s.nome, t.nome
                    HAVING media_geral < 6.0
                    ORDER BY media_geral ASC
                    LIMIT 20
                """, (ano_letivo_val, escola_id)),

                ("Alunos baixa frequência", """
                    SELECT 
                        a.nome AS aluno,
                        s.nome AS serie,
                        t.nome AS turma,
                        COALESCE(SUM(fb.faltas), 0) AS total_faltas
                    FROM alunos a
                    JOIN matriculas m ON a.id = m.aluno_id
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    LEFT JOIN faltas_bimestrais fb ON a.id = fb.aluno_id 
                        AND fb.ano_letivo_id = m.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                    GROUP BY a.id, a.nome, s.nome, t.nome
                    HAVING total_faltas > 40
                    ORDER BY total_faltas DESC
                    LIMIT 20
                """, (ano_letivo_val, escola_id)),

                ("Turmas pendências", """
                    SELECT 
                        s.nome AS serie,
                        t.nome AS turma,
                        d.nome AS disciplina,
                        COUNT(DISTINCT m.aluno_id) AS alunos_sem_nota
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN series s ON t.serie_id = s.id
                    JOIN alunos a ON m.aluno_id = a.id
                    CROSS JOIN disciplinas d
                    LEFT JOIN notas n ON m.aluno_id = n.aluno_id 
                        AND n.disciplina_id = d.id 
                        AND n.ano_letivo_id = m.ano_letivo_id
                    WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)
                      AND a.escola_id = %s
                      AND m.status = 'Ativo'
                      AND n.id IS NULL
                      AND d.ativo = 1
                    GROUP BY s.id, s.nome, t.id, t.nome, d.id, d.nome
                    HAVING alunos_sem_nota > 0
                    ORDER BY s.nome, t.nome, d.nome
                    LIMIT 30
                """, (ano_letivo_val, escola_id)),
            ]

            for label, sql, params in queries:
                try:
                    print('\nExecutando:', label)
                    cursor.execute(sql, params)
                    rows = cursor.fetchall()
                    print('Rows count:', len(rows))
                    if rows:
                        print('Primeira linha:', rows[0])
                except Exception:
                    print('Erro na query:', label)
                    traceback.print_exc()

    except Exception:
        print('Erro geral ao executar queries:')
        traceback.print_exc()


import config
from src.ui.dashboard_coordenador import DashboardCoordenador


def main():
    # Ajuste `escola_id` ou `ano_letivo` conforme necessário
    escola_id = 60
    ano_letivo = None

    # Instanciar como se fosse o coordenador '03499893379' (séries configuradas em feature_flags)
    username = '03499893379'
    series = config.coordenador_series_para_usuario(username)
    print('Séries permitidas para', username, ':', series)

    dc = DashboardCoordenador(janela=None, db_service=None, frame_getter=lambda: None,
                              escola_id=escola_id, ano_letivo=ano_letivo, series_permitidas=series)

    try:
        # Testar conexão e executar queries individuais primeiro
        teste_conexao_db()
        teste_queries(escola_id=escola_id, ano_letivo=ano_letivo)

        dados = dc._buscar_dados_pedagogicos()
        print("OK: dados retornados")
        print(json.dumps(dados, indent=2, default=str, ensure_ascii=False))
    except Exception:
        print("EXCEPTION:")
        traceback.print_exc()


if __name__ == '__main__':
    main()

