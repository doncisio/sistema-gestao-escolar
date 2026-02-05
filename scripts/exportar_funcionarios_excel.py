from pathlib import Path
from typing import List, Dict, Any
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from db.connection import get_cursor

OUTPUT_PATH = Path("documentos_gerados/funcionarios_redeescola.xlsx")


def _normalize_text(value: Any) -> str:
    """Transforma valores em texto caixa alta, mantendo vazio quando None."""
    if value is None:
        return ""
    return str(value).strip().upper()


def _build_address(row: Dict[str, Any]) -> str:
    parts: List[str] = []

    logradouro = row.get("endereco_logradouro")
    if logradouro:
        parts.append(str(logradouro))

    numero = row.get("endereco_numero")
    if numero:
        parts.append(f"N {numero}")

    complemento = row.get("endereco_complemento")
    if complemento:
        parts.append(str(complemento))

    bairro = row.get("endereco_bairro")
    if bairro:
        parts.append(str(bairro))

    cidade = row.get("endereco_cidade")
    estado = row.get("endereco_estado")
    if cidade and estado:
        parts.append(f"{cidade}/{estado}")
    elif cidade:
        parts.append(str(cidade))
    elif estado:
        parts.append(str(estado))

    return " - ".join(parts)


def _fetch_funcionarios() -> List[Dict[str, Any]]:
    query = """
        SELECT
            nome,
            cpf,
            data_nascimento,
            email,
            telefone,
            whatsapp,
            endereco_cep,
            endereco_logradouro,
            endereco_numero,
            endereco_complemento,
            endereco_bairro,
            endereco_cidade,
            endereco_estado,
            funcao,
            cargo,
            vinculo
        FROM funcionarios
        ORDER BY nome
    """

    with get_cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall() or []

        if rows and not isinstance(rows[0], dict):
            columns = [desc[0] for desc in cursor.description]
            rows = [dict(zip(columns, r)) for r in rows]

    return rows


def _format_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    formatted: List[Dict[str, str]] = []

    for row in rows:
        data_nasc = row.get("data_nascimento")
        if data_nasc is None:
            data_nasc_str = ""
        else:
            data_nasc_str = getattr(data_nasc, "strftime", lambda fmt: str(data_nasc))("%d/%m/%Y")

        endereco = _build_address(row)
        telefone = row.get("telefone") or row.get("whatsapp") or ""
        naturalidade = row.get("endereco_cidade") or ""
        funcao = row.get("funcao") or row.get("cargo") or ""

        formatted.append(
            {
                "NOME": _normalize_text(row.get("nome")),
                "CPF": _normalize_text(row.get("cpf")),
                "DATA DE NASCIMENTO": _normalize_text(data_nasc_str),
                "EMAIL": _normalize_text(row.get("email")),
                "TELEFONE": _normalize_text(telefone),
                "NATURALIDADE": _normalize_text(naturalidade),
                "CEP": _normalize_text(row.get("endereco_cep")),
                "ENDERECO": _normalize_text(endereco),
                "FUNCAO": _normalize_text(funcao),
                "REGIME": _normalize_text(row.get("vinculo")),
            }
        )

    return formatted


def exportar_funcionarios_para_excel(saida: Path = OUTPUT_PATH) -> Path:
    rows = _fetch_funcionarios()
    dataset = _format_rows(rows)

    saida.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        dataset,
        columns=[
            "NOME",
            "CPF",
            "DATA DE NASCIMENTO",
            "EMAIL",
            "TELEFONE",
            "NATURALIDADE",
            "CEP",
            "ENDERECO",
            "FUNCAO",
            "REGIME",
        ],
    )
    df.to_excel(saida, index=False)
    return saida


def main():
    path = exportar_funcionarios_para_excel()
    print(f"Arquivo gerado em: {path.resolve()}")


if __name__ == "__main__":
    main()
