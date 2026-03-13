"""
Script para normalizar as matrículas dos funcionários no banco de dados.

Garante que todas as matrículas sigam o formato XXXXX-X,
ou seja, o último dígito separado por hífen.

Exemplos de normalização:
    '1167982'    → '116798-2'
    '6019382'    → '601938-2'
    '116547-2'   → '116547-2'  (já correto, sem alteração)
    '67003879-4' → '67003879-4' (já correto, sem alteração)

Uso:
    python normalizar_matriculas_funcionarios.py
    python normalizar_matriculas_funcionarios.py --dry-run   (apenas exibe, sem alterar)
"""
import sys
import argparse

sys.path.insert(0, r'c:\gestao')

from src.utils.formatador_cpf import normalizar_matricula
from db.connection import conectar_bd


def main(dry_run: bool = False):
    conn = conectar_bd()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, nome, matricula FROM funcionarios "
        "WHERE matricula IS NOT NULL AND matricula != ''"
    )
    rows = cur.fetchall()

    atualizados = 0
    sem_alteracao = 0

    for func_id, nome, matricula_atual in rows:
        normalizada = normalizar_matricula(matricula_atual)
        if normalizada == matricula_atual:
            sem_alteracao += 1
            continue

        print(f"ID {func_id:>5}  {nome[:40]:<40}  '{matricula_atual}'  →  '{normalizada}'")
        if not dry_run:
            cur.execute(
                "UPDATE funcionarios SET matricula = %s WHERE id = %s",
                (normalizada, func_id)
            )
        atualizados += 1

    if not dry_run and atualizados > 0:
        conn.commit()

    cur.close()
    conn.close()

    modo = "[DRY-RUN] " if dry_run else ""
    print(f"\n{modo}Matrículas alteradas : {atualizados}")
    print(f"{modo}Já no formato correto: {sem_alteracao}")
    print(f"{modo}Total verificadas    : {len(rows)}")

    if dry_run and atualizados > 0:
        print("\nExecute sem --dry-run para aplicar as alterações.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normaliza matrículas de funcionários no banco.")
    parser.add_argument("--dry-run", action="store_true", help="Apenas exibe o que seria alterado, sem gravar.")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
