from pathlib import Path
from src.importers.geduc_horarios import parse_turmas, parse_horario_por_turma, save_json
import json


def main():
    base = Path(r"c:/gestao/historico geduc")

    out_dir = Path(r"c:/gestao/historico_geduc_imports")
    out_dir.mkdir(parents=True, exist_ok=True)

    turmas_file = base / 'turmas semana.html'
    horario_file = base / 'horario por turma.html'

    if turmas_file.exists():
        turmas = parse_turmas(turmas_file)
        save_json({'turmas': turmas}, out_dir / 'turmas_lista.json')
        print(f'Lista de turmas salva em {out_dir / "turmas_lista.json"}')
    else:
        print('Arquivo de turmas não encontrado:', turmas_file)

    if horario_file.exists():
        horario = parse_horario_por_turma(horario_file)
        tid = horario.get('turma_id') or 'sem_id'
        save_json(horario, out_dir / f'horario_turma_{tid}.json')
        print(f'Horário da turma salvo em {out_dir / f"horario_turma_{tid}.json"}')
    else:
        print('Arquivo de horário por turma não encontrado:', horario_file)


if __name__ == '__main__':
    main()
