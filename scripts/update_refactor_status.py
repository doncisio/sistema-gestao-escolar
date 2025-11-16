"""Atualiza a seção de status em ANALISE_main_py.md com base em REFACTOR_STATUS.json.

Uso:
  python scripts/update_refactor_status.py --show
  python scripts/update_refactor_status.py --set db/connection.py
  python scripts/update_refactor_status.py --unset db/connection.py
  python scripts/update_refactor_status.py --render-only

Ele substitui o bloco entre <!-- REFSTATUS:START --> e <!-- REFSTATUS:END -->.
"""
import argparse
import json
import os
from datetime import datetime
from config_logs import get_logger

logger = get_logger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STATUS_FILE = os.path.join(ROOT, 'REFACTOR_STATUS.json')
ANALISE_FILE = os.path.join(ROOT, 'ANALISE_main_py.md')
MARKER_START = '<!-- REFSTATUS:START -->'
MARKER_END = '<!-- REFSTATUS:END -->'


def load_status():
    with open(STATUS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_status(status):
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)


def render_block(status):
    lines = []
    for key, item in status.items():
        title = item.get('title', key)
        done = item.get('done', False)
        when = item.get('when')
        checkbox = '[x]' if done else '[ ]'
        if when and done:
            lines.append(f"- {checkbox} {title}  ")
        else:
            lines.append(f"- {checkbox} {title}")
    lines.append('\nObservações:')
    lines.append('- Marquei apenas as ações que já foram realizadas no repositório e validadas localmente.')
    lines.append('- Posso manter esse bloco atualizado conforme formos concluindo outras propostas.')
    return '\n'.join(lines)


def update_analise_file(rendered_block):
    with open(ANALISE_FILE, 'r', encoding='utf-8') as f:
        text = f.read()
    if MARKER_START not in text or MARKER_END not in text:
        raise RuntimeError('Marcadores não encontrados em ANALISE_main_py.md')
    pre, rest = text.split(MARKER_START, 1)
    _, post = rest.split(MARKER_END, 1)
    new_text = pre + MARKER_START + '\n' + rendered_block + '\n' + MARKER_END + post
    with open(ANALISE_FILE, 'w', encoding='utf-8') as f:
        f.write(new_text)
    return new_text


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--set', dest='set_key', help='Marcar chave como done')
    p.add_argument('--unset', dest='unset_key', help='Desmarcar chave')
    p.add_argument('--show', action='store_true', help='Mostrar status atual')
    p.add_argument('--render-only', action='store_true', help='Renderizar e mostrar, sem gravar arquivo')
    args = p.parse_args()

    status = load_status()

    changed = False
    if args.set_key:
        key = args.set_key
        if key not in status:
            logger.error(f'Chave {key} não encontrada em {STATUS_FILE}')
            return
        status[key]['done'] = True
        status[key]['when'] = datetime.utcnow().isoformat() + 'Z'
        changed = True
    if args.unset_key:
        key = args.unset_key
        if key not in status:
            logger.error(f'Chave {key} não encontrada em {STATUS_FILE}')
            return
        status[key]['done'] = False
        status[key].pop('when', None)
        changed = True

    if changed:
        save_status(status)

    rendered = render_block(status)

    if args.render_only:
        print(rendered)
        return

    if args.show:
        print(rendered)
        return

    # atualizar o arquivo ANALISE_main_py.md
    new_text = update_analise_file(rendered)
    print('ANALISE_main_py.md atualizado com o bloco de status.')


if __name__ == '__main__':
    main()
