"""Script para concluir matrículas antigas deixando apenas a matrícula mais recente ativa.

Uso:
  - Dry-run (padrão): mostra o que seria atualizado
      python concluir_matriculas_antigas.py

  - Aplicar alterações no banco:
      python concluir_matriculas_antigas.py --apply

Opções:
  --aluno ALUNO_ID    : aplicar apenas para um aluno específico
  --limit N           : limitar processamento aos N primeiros alunos (para testes)

Observação: faça backup antes de rodar `--apply` em produção.
"""
from __future__ import annotations
import argparse
from typing import List, Tuple
from db.connection import get_connection

CONCLUDED_STATUS = 'Concluído'
FALLBACK_CONCLUDED = ('Concluida', 'Concluído')
ACTIVE_STATUS = 'Ativo'


def coletar_alunos_com_multiplas_matriculas(limit: int | None = None) -> List[int]:
    q = """
    SELECT aluno_id
    FROM matriculas
    GROUP BY aluno_id
    HAVING COUNT(*) > 1
    ORDER BY aluno_id
    """
    if limit:
        q = q + f"\nLIMIT {int(limit)}"

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(q)
        rows = cur.fetchall()
        return [r[0] for r in rows]


def obter_matriculas_aluno(aluno_id: int) -> List[Tuple[int, int, str, str]]:
    """Retorna lista de tuplas (id, ano_letivo_id, data_matricula, status) ordenadas da mais recente para a mais antiga."""
    q = """
    SELECT id, ano_letivo_id, data_matricula, status
    FROM matriculas
    WHERE aluno_id = %s
    ORDER BY ano_letivo_id DESC, data_matricula DESC, id DESC
    """
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(q, (aluno_id,))
        return cur.fetchall()


def processar_aluno(aluno_id: int, apply: bool = False) -> Tuple[int, int]:
    """Conclui matrículas antigas de um aluno.

    Retorna (updated_count, kept_id)
    """
    rows = obter_matriculas_aluno(aluno_id)
    if not rows or len(rows) == 1:
        return 0, rows[0][0] if rows else (0)

    # primeira linha é a mais recente
    latest_id = rows[0][0]
    older_ids = [r[0] for r in rows[1:]]

    updated = 0
    if apply:
        with get_connection() as conn:
            cur = conn.cursor()
            # marcar todos os antigos como concluída (exceto o mais recente)
            if older_ids:
                q = f"UPDATE matriculas SET status = %s WHERE id IN ({', '.join(['%s'] * len(older_ids))})"
                params = [CONCLUDED_STATUS] + older_ids
                cur.execute(q, tuple(params))
                updated += cur.rowcount

            # garantir que o mais recente está marcado como ativo
            cur.execute("UPDATE matriculas SET status = %s WHERE id = %s", (ACTIVE_STATUS, latest_id))
            # cur.rowcount não necessariamente útil aqui
            try:
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    else:
        updated = len(older_ids)

    return updated, latest_id


def restrict_active(ano: int = 2025, escola_id: int = 60, apply: bool = False):
    """Garante que apenas alunos com matrícula em `ano` na `escola_id` vinculada a uma série/turma
    mantenham matrícula(s) com status 'Ativo'. Marca como 'Concluida' as demais matrículas ativas.

    Em dry-run (apply=False) apenas mostra contagens.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # total atuais ativos
        cur.execute("SELECT COUNT(*) FROM matriculas WHERE status = %s", (ACTIVE_STATUS,))
        total_ativos = cur.fetchone()[0]

        # alunos que têm ao menos uma matrícula qualificadora
        cur.execute(
            """
            SELECT DISTINCT m.aluno_id
            FROM matriculas m
            JOIN turmas t ON m.turma_id = t.id
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            WHERE a.ano_letivo = %s AND t.escola_id = %s AND t.serie_id IS NOT NULL AND COALESCE(t.nome, '') <> ''
            """,
            (ano, escola_id),
        )
        alunos_qual = [r[0] for r in cur.fetchall()]

        # contagem de ativos que pertencem a alunos qualificados e são as próprias matrículas qualificadoras
        if alunos_qual:
            # ids list as CSV for queries
            placeholder = ','.join(['%s'] * len(alunos_qual))

            cur.execute(
                f"""
                SELECT COUNT(*) FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN anosletivos a ON m.ano_letivo_id = a.id
                WHERE m.status = %s AND a.ano_letivo = %s AND t.escola_id = %s AND m.aluno_id IN ({placeholder})
                """.format(placeholder=placeholder),
                tuple([ACTIVE_STATUS, ano, escola_id] + alunos_qual),
            )
            ativos_qualificadores = cur.fetchone()[0]

            # ativos dos alunos qualificados que NÃO são qualificadores (serão concluídos)
            cur.execute(
                f"""
                SELECT COUNT(*) FROM matriculas m
                WHERE m.status = %s AND m.aluno_id IN ({placeholder})
                AND NOT EXISTS (
                    SELECT 1 FROM matriculas m2
                    JOIN turmas t2 ON m2.turma_id = t2.id
                    JOIN anosletivos a2 ON m2.ano_letivo_id = a2.id
                    WHERE m2.aluno_id = m.aluno_id AND a2.ano_letivo = %s AND t2.escola_id = %s AND t2.serie_id IS NOT NULL AND COALESCE(t2.nome, '') <> ''
                )
                """.format(placeholder=placeholder),
                tuple([ACTIVE_STATUS] + alunos_qual + [ano, escola_id]),
            )
            ativos_qual_naoqual = cur.fetchone()[0]
        else:
            ativos_qualificadores = 0
            ativos_qual_naoqual = 0

        # ativos de alunos que não têm matrícula qualificadora (serão concluídos)
        if alunos_qual:
            cur.execute(
                f"SELECT COUNT(*) FROM matriculas WHERE status = %s AND aluno_id NOT IN ({','.join(['%s']*len(alunos_qual))})",
                tuple([ACTIVE_STATUS] + alunos_qual),
            )
            ativos_nao_tem_qual = cur.fetchone()[0]
        else:
            cur.execute("SELECT COUNT(*) FROM matriculas WHERE status = %s", (ACTIVE_STATUS,))
            ativos_nao_tem_qual = cur.fetchone()[0]

        total_para_concluir = ativos_qual_naoqual + ativos_nao_tem_qual

        print(f"Total ativos atuais: {total_ativos}")
        print(f"Ativos que atendem aos critérios (ano={ano}, escola={escola_id}): {ativos_qualificadores}")
        print(f"Ativos que serão concluídos (estimado): {total_para_concluir}")

        if not apply:
            print("Dry-run: nenhuma alteração será aplicada. Use --apply para gravar as mudanças.")
            return

        # Aplicar atualizações:
        # 1) Concluir ativos de alunos sem matrícula qualificadora
        # Usar CONCLUDED_STATUS ao atualizar; aceitar também variações existentes
        if alunos_qual:
            cur.execute(
                f"UPDATE matriculas SET status = %s WHERE status = %s AND aluno_id NOT IN ({','.join(['%s']*len(alunos_qual))})",
                tuple([CONCLUDED_STATUS, ACTIVE_STATUS] + alunos_qual),
            )
            concl1 = cur.rowcount
        else:
            cur.execute("UPDATE matriculas SET status = %s WHERE status = %s", (CONCLUDED_STATUS, ACTIVE_STATUS))
            concl1 = cur.rowcount

        # 2) Para alunos qualificados, concluir suas matrículas ativas que não são qualificadoras
        cur.execute(
            """
            UPDATE matriculas m
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            LEFT JOIN turmas t ON m.turma_id = t.id
            SET m.status = %s
            WHERE m.status = %s
            AND EXISTS (
                SELECT 1 FROM matriculas m2
                JOIN turmas t2 ON m2.turma_id = t2.id
                JOIN anosletivos a2 ON m2.ano_letivo_id = a2.id
                WHERE m2.aluno_id = m.aluno_id AND a2.ano_letivo = %s AND t2.escola_id = %s AND t2.serie_id IS NOT NULL AND COALESCE(t2.nome, '') <> ''
            )
            AND NOT (a.ano_letivo = %s AND t.escola_id = %s AND t.serie_id IS NOT NULL AND COALESCE(t.nome, '') <> '')
            """,
            (CONCLUDED_STATUS, ACTIVE_STATUS, ano, escola_id, ano, escola_id),
        )
        concl2 = cur.rowcount

        try:
            conn.commit()
        except Exception:
            conn.rollback()
            raise

        print(f"Aplicado: matrículas concluídas (alunos sem qual): {concl1}, (alunos qual mas não qualificadoras): {concl2}, total: {concl1+concl2}")


def main():
    parser = argparse.ArgumentParser(description="Concluir matrículas antigas deixando apenas a atual ativa")
    parser.add_argument("--apply", action="store_true", help="Aplica as alterações no banco (padrão: dry-run)")
    parser.add_argument("--aluno", type=int, help="ID do aluno para processar apenas esse aluno")
    parser.add_argument("--limit", type=int, help="Limitar N alunos (apenas para testes)")
    parser.add_argument("--restrict-active", action="store_true", help="Limitar matrículas Ativo apenas aos alunos com matrícula em --ano na escola --escola (mantém só as vinculadas a série/turma)")
    parser.add_argument("--escola", type=int, default=60, help="ID da escola a considerar (padrão: 60)")
    parser.add_argument("--ano", type=int, default=2025, help="Ano letivo a considerar (padrão: 2025)")
    args = parser.parse_args()

    if args.apply:
        print("Executando em modo APPLY: alterações serão gravadas no banco.")
    else:
        print("Modo DRY-RUN: nenhuma alteração será aplicada. Use --apply para gravar.")

    if args.aluno:
        lista = [args.aluno]
    else:
        lista = coletar_alunos_com_multiplas_matriculas(limit=args.limit)

    total_updated = 0
    total_alunos = len(lista)

    for i, aluno_id in enumerate(lista, start=1):
        updated, kept_id = processar_aluno(aluno_id, apply=args.apply)
        total_updated += updated
        print(f"[{i}/{total_alunos}] Aluno {aluno_id}: atualizada(s) {updated}, mantida matrícula {kept_id}")

    print(f"\nResumo: alunos processados: {total_alunos}, matrículas atualizadas: {total_updated}")

    # Se solicitada a restrição global de matrículas Ativo, executar verificação/atualização
    if args.restrict_active:
        print('\nExecutando verificação de restrição de matrículas Ativo...')
        restrict_active(args.ano, args.escola, apply=args.apply)


if __name__ == '__main__':
    main()

