import sys
import os
from pathlib import Path
import json

# permitir import de src quando executado diretamente
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.importers.geduc_horarios import parse_horario_por_turma
from src.utils.horarios_mapper import mapear_disc_prof
from src.utils.horarios_persistence import upsert_horarios


BASE = Path(r"c:/gestao/historico_geduc_imports")
if not BASE.exists():
    print("Pasta de importações não encontrada:", BASE)
    raise SystemExit(1)

# Horários e dias padrão (mesmos usados na interface)
HORARIOS_MATUTINO = ["07:10-08:00", "08:00-08:50", "08:50-09:40", "09:40-10:00", "10:00-10:50", "10:50-11:40"]
HORARIOS_VESPERTINO = ["13:10-14:00", "14:00-14:50", "14:50-15:40", "15:40-16:00", "16:00-16:50", "16:50-17:40"]
DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]


def infer_horarios(rows):
    if not rows:
        return HORARIOS_MATUTINO
    n = len(rows)
    if n == len(HORARIOS_MATUTINO):
        return HORARIOS_MATUTINO
    if n == len(HORARIOS_VESPERTINO):
        return HORARIOS_VESPERTINO
    # se n for compatível, tentar dividir em matutino+vespertino
    if n == len(HORARIOS_MATUTINO) + len(HORARIOS_VESPERTINO):
        # retornaremos a concatenação (não usado diretamente)
        return HORARIOS_MATUTINO + HORARIOS_VESPERTINO
    # fallback: gerar horários genéricos
    return [f"R{idx+1}" for idx in range(n)]


def process_file(json_path: Path, disciplinas, professores, mapeamentos):
    data = json.loads(json_path.read_text(encoding='utf-8'))
    turma_id = data.get('turma_id') or data.get('turma', {}).get('id')
    rows = data.get('rows') or []
    horario_list = infer_horarios(rows)

    items = []
    for r_idx, row in enumerate(rows):
        for c_idx, cell in enumerate(row):
            valor = (cell or '').strip()
            if not valor:
                continue
            dia = DIAS[c_idx] if c_idx < len(DIAS) else f'Dia{c_idx+1}'
            horario = horario_list[r_idx] if r_idx < len(horario_list) else f'R{r_idx+1}'

            disc_id, prof_id = mapear_disc_prof(valor, disciplinas, professores, mapeamentos)

            items.append({
                'turma_id': turma_id,
                'dia': dia,
                'horario': horario,
                'valor': valor,
                'disciplina_id': disc_id,
                'professor_id': prof_id,
            })
    return items


def load_mapeamentos():
    path = Path(r"c:/gestao/historico_geduc_imports/mapeamentos_horarios.json")
    if not path.exists():
        return {'disciplinas': {}, 'professores': {}}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {'disciplinas': {}, 'professores': {}}


def main():
    # carregar disciplinas/professores do sistema (fallback simples)
    # Aqui usamos consultas simples ao banco via src.core.conexao.conectar_bd()
    try:
        from src.core.conexao import conectar_bd
        conn = conectar_bd()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, nome FROM disciplinas WHERE escola_id = 60")
        disciplinas = cur.fetchall()
        cur.execute("SELECT id, nome FROM funcionarios WHERE escola_id = 60")
        professores = cur.fetchall()
        cur.close()
        conn.close()
    except Exception:
        disciplinas = []
        professores = []

    mapeamentos = load_mapeamentos()

    all_items = []
    for f in BASE.glob('horario_turma_*.json'):
        print('Processando', f)
        items = process_file(f, disciplinas, professores, mapeamentos)
        print('  itens gerados:', len(items))
        if items:
            inserted = upsert_horarios(items)
            print(f'  persistidos: {inserted}')
            all_items.extend(items)

    print('Total items processados:', len(all_items))


if __name__ == '__main__':
    main()
