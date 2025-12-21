#!/usr/bin/env python3
"""Curadoria do mapeamento GEDUC

Gera:
- config/mapeamento_curado_80.json  (apenas sugestões >= 80%)
- sql/mapeamento_geduc_curado_80.sql (inserts para 'escola' apenas)
- config/mapeamento_restante_80.json (sugestões < 80% para revisão)

Uso: python scripts/curar_mapeamento_geduc.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUG_PATH = ROOT / 'config' / 'mapeamento_sugerido.json'
DET_PATH = ROOT / 'config' / 'detalhes_escolas_geduc.json'
OUT_CURADO = ROOT / 'config' / 'mapeamento_curado_80.json'
OUT_RESTANTE = ROOT / 'config' / 'mapeamento_restante_80.json'
OUT_SQL = ROOT / 'sql' / 'mapeamento_geduc_curado_80.sql'


def parse_similarity(s):
    if s is None:
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return float(str(s).strip().rstrip('%'))
    except Exception:
        return 0.0


def main():
    sugerido = json.loads(SUG_PATH.read_text(encoding='utf-8'))
    detalhes = json.loads(DET_PATH.read_text(encoding='utf-8'))
    detalhes_map = {e.get('id_geduc'): e for e in detalhes.get('escolas', [])}

    escolas = sugerido.get('escolas', [])
    curado = []
    restante = []

    for item in escolas:
        sim = parse_similarity(item.get('similaridade'))
        target = {
            'id_local': item.get('id_local'),
            'nome_local': item.get('nome_local'),
            'id_geduc': item.get('id_geduc'),
            'nome_geduc': item.get('nome_geduc'),
            'similaridade': f"{sim:.1f}%",
        }
        # anexar detalhes da escola GEDUC quando disponível
        det = detalhes_map.get(item.get('id_geduc'))
        if det:
            target['detalhes_geduc'] = {
                'NOME': det.get('NOME'),
                'ENDERECO': det.get('ENDERECO'),
                'CODIGOINEP': det.get('CODIGOINEP'),
                'TELEFONE': det.get('TELEFONE'),
                'CEP': det.get('CEP'),
                'BAIRRO': det.get('BAIRRO'),
                'REGIAO': det.get('REGIAO'),
                'IDREGIAO': det.get('IDREGIAO'),
            }

        if sim >= 80.0:
            curado.append(target)
        else:
            restante.append(target)

    # salvar JSONs
    OUT_CURADO.parent.mkdir(parents=True, exist_ok=True)
    OUT_RESTANTE.parent.mkdir(parents=True, exist_ok=True)
    OUT_SQL.parent.mkdir(parents=True, exist_ok=True)

    OUT_CURADO.write_text(json.dumps({'extraido_em': sugerido.get('extraido_em'), 'escolas': curado}, ensure_ascii=False, indent=2), encoding='utf-8')
    OUT_RESTANTE.write_text(json.dumps({'extraido_em': sugerido.get('extraido_em'), 'escolas': restante}, ensure_ascii=False, indent=2), encoding='utf-8')

    # gerar SQL contendo apenas INSERTs para 'escola' do curado
    header = """
-- Curadoria automática: mapeamentos com similaridade >= 80%
-- Gerado por scripts/curar_mapeamento_geduc.py

CREATE TABLE IF NOT EXISTS mapeamento_geduc (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tipo ENUM('escola', 'disciplina', 'curso', 'curriculo', 'serie', 'turno') NOT NULL,
    id_local INT NOT NULL,
    nome_local VARCHAR(255),
    id_geduc INT NOT NULL,
    nome_geduc VARCHAR(255),
    similaridade VARCHAR(10),
    verificado BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserts automáticos (escola)
"""

    inserts = []
    for e in curado:
        id_local = e.get('id_local') or 'NULL'
        nome_local = (e.get('nome_local') or '').replace("'", "''")
        id_geduc = e.get('id_geduc') or 'NULL'
        nome_geduc = (e.get('nome_geduc') or '').replace("'", "''")
        sim = e.get('similaridade') or ''
        inserts.append("INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', %s, '%s', %s, '%s', '%s');" % (id_local, nome_local, id_geduc, nome_geduc, sim))

    OUT_SQL.write_text(header + '\n'.join(inserts) + '\n', encoding='utf-8')

    # resumo
    print(f"Total sugerido: {len(escolas)}")
    print(f"Curados (>=80%): {len(curado)} -> {OUT_CURADO}")
    print(f"Restantes (<80%): {len(restante)} -> {OUT_RESTANTE}")
    print(f"SQL gerado: {OUT_SQL}")


if __name__ == '__main__':
    main()
