"""
Migração: normalizar campo 'descricao_transtorno' na tabela alunos.

Converte os valores brutos com códigos CID (ex: 'TEA - CID: CID 10 F84.0',
'CID: F91.3', 'CID: CID 11 F6A05') para rótulos padronizados e legíveis,
sem o código CID explícito (ex: 'TEA', 'TDO', 'TDAH').

Uso:
    python scripts/normalizar_transtornos_banco.py            # dry-run (apenas mostra o que seria alterado)
    python scripts/normalizar_transtornos_banco.py --aplicar  # aplica as alterações no banco

Exemplo de mapeamento:
  'CID: F91.3'                 → 'TDO'
  'CID: F90.0'                 → 'TDAH'
  'TEA - CID: F84.0'           → 'TEA'
  'CID: CID 11 F6A05'          → 'TDAH'
  'TEA - CID: CID10 F84.0'     → 'TEA'
  'TEA - CID: CID 10 F 84.0'   → 'TEA'
  'TEA, ALTAS HABILIDADES'     → 'TEA / Altas Habilidades'
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from db.connection import conectar_bd
from src.utils.transtornos import normalizar_descricao_transtorno


def main(aplicar: bool = False) -> None:
    conn = conectar_bd()
    cursor = conn.cursor(buffered=True)

    # Buscar todos os alunos com descricao_transtorno diferente de 'Nenhum' e não nulo
    cursor.execute("""
        SELECT id, nome, descricao_transtorno
        FROM alunos
        WHERE descricao_transtorno IS NOT NULL
          AND descricao_transtorno NOT IN ('Nenhum', '', '0')
        ORDER BY id
    """)
    rows = cursor.fetchall()

    alteracoes: list[tuple[int, str, str, str]] = []  # (id, nome, antigo, novo)

    for aluno_id, nome, valor_atual in rows:
        normalizado = normalizar_descricao_transtorno(valor_atual)
        if normalizado != (valor_atual or '').strip():
            alteracoes.append((aluno_id, nome, valor_atual, normalizado))

    if not alteracoes:
        print("✅ Nenhuma alteração necessária — todos os valores já estão normalizados.")
        return

    print(f"{'=' * 70}")
    print(f"{'MODO SIMULAÇÃO (dry-run)' if not aplicar else 'APLICANDO ALTERAÇÕES'}")
    print(f"{'=' * 70}")
    print(f"{'ID':<6}  {'NOME':<45}  {'ANTES':<35}  →  DEPOIS")
    print(f"{'-' * 130}")

    for aluno_id, nome, antigo, novo in alteracoes:
        nome_fmt = nome[:43] + '..' if len(nome) > 45 else nome
        antigo_fmt = (antigo or '')[:33] + '..' if len(antigo or '') > 35 else antigo
        print(f"{aluno_id:<6}  {nome_fmt:<45}  {antigo_fmt:<35}  →  {novo}")

    print(f"{'-' * 130}")
    print(f"\nTotal de registros a atualizar: {len(alteracoes)}")

    if not aplicar:
        print("\n⚠️  Execução em modo DRY-RUN. Nenhuma alteração foi feita no banco.")
        print("    Para aplicar, execute com o argumento '--aplicar':\n")
        print("    python scripts/normalizar_transtornos_banco.py --aplicar\n")
        return

    # Aplicar atualizações
    print("\nAplicando atualizações...")
    for aluno_id, nome, antigo, novo in alteracoes:
        cursor.execute(
            "UPDATE alunos SET descricao_transtorno = %s WHERE id = %s",
            (novo, aluno_id)
        )

    conn.commit()
    print(f"\n✅ {len(alteracoes)} registros atualizados com sucesso.")
    cursor.close()
    conn.close()


if __name__ == '__main__':
    aplicar = '--aplicar' in sys.argv
    main(aplicar=aplicar)
