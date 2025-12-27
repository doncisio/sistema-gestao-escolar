from pathlib import Path
import json
from typing import List, Dict, Any

from bs4 import BeautifulSoup


def parse_turmas(html_path: Path) -> List[Dict[str, Any]]:
    """Parseia o arquivo de lista de turmas e extrai id, nome e link (quando presente)."""
    html = html_path.read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')

    turmas = []

    # Procurar pela tabela que contém 'Lista de Turmas' ou pelas linhas de dados
    # Vamos iterar por todas as <tr> dentro de tabelas e tentar extrair colunas coerentes
    for table in soup.find_all('table'):
        # detectar cabeçalho com 'Turma' ou 'Série/Curso'
        thead = table.find('thead')
        if thead and ('Turma' in thead.get_text() or 'Série' in thead.get_text() or 'Lista de Turmas' in table.get_text()):
            tbody = table.find('tbody') or table
            for tr in tbody.find_all('tr'):
                tds = tr.find_all('td')
                if not tds:
                    continue

                # tentar localizar link com IDTURMA
                link = tr.find('a', href=True)
                href = link['href'] if link else None

                # procurar coluna que pareça conter código/ID (número)
                codigo = None
                nome = None
                for td in tds:
                    txt = td.get_text(strip=True)
                    if txt.isdigit():
                        codigo = int(txt)
                        continue
                    # heurística: coluna com '-MATU' ou 'ANo' ou 'ANO' etc
                    if any(x in txt for x in ['AN', 'ANO', 'ANo', 'MATU', 'VESP', 'Turma']):
                        nome = txt

                # fallback: tentar pegar segunda ou quarta coluna como nome
                if not nome and len(tds) >= 5:
                    nome = tds[4].get_text(strip=True)

                if codigo or nome:
                    turmas.append({'id': codigo, 'nome': nome, 'href': href})

            # assumimos que apenas uma tabela é necessária
            break

    return turmas


def parse_horario_por_turma(html_path: Path) -> Dict[str, Any]:
    """Parseia o formulário/grade de horário por turma e retorna uma estrutura matricial.

    Retorna dict com chaves: turma_id, turma_nome (quando disponível), rows (lista de listas de células)
    Cada célula é uma string (texto da <a> ou opção selecionada do <select>)."""
    html = html_path.read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')

    # IDTURMA hidden
    id_input = soup.find('input', {'name': 'IDTURMA'})
    turma_id = id_input['value'] if id_input and id_input.has_attr('value') else None

    # Tentar obter nome da turma no título da página
    titulo = None
    h1 = soup.find(['h1', 'h2', 'h3'])
    if h1:
        titulo = h1.get_text(strip=True)

    # Encontrar a tabela principal que contém selects 'disc_' ou anchors com disciplinas
    table = None
    for t in soup.find_all('table'):
        if t.find('select', attrs={'name': lambda v: v and v.startswith('disc_')} ) or t.find('a', href=True):
            table = t
            break

    rows = []
    if table:
        tbody = table.find('tbody') or table
        for tr in tbody.find_all('tr'):
            # coletar todas as células que possuam selects/links/input relevantes
            cells = []
            tds = tr.find_all(['td', 'th'])
            if not tds:
                continue

            for td in tds:
                # ignorar hidden inputs
                if td.find('input', {'type': 'hidden'}):
                    continue

                a = td.find('a')
                sel = td.find('select')
                if a and a.get_text(strip=True):
                    cells.append(a.get_text(strip=True))
                elif sel:
                    # pegar option selecionado; se nenhum, pegar ''
                    opt = sel.find('option', selected=True)
                    if not opt:
                        # às vezes não há atributo selected; pegar ''
                        opts = sel.find_all('option')
                        opt = next((o for o in opts if o.has_attr('selected')), None) or None
                    val = opt.get_text(strip=True) if opt else ''
                    cells.append(val)
                else:
                    # célula possivelmente vazia ou contém label
                    txt = td.get_text(strip=True)
                    # ignorar linhas de intervalo curtas
                    cells.append(txt)

            # apenas considerar linhas com conteúdo relevante
            if any(c != '' for c in cells):
                rows.append(cells)

    result = {
        'turma_id': int(turma_id) if turma_id and str(turma_id).isdigit() else turma_id,
        'turma_nome': titulo,
        'rows': rows,
        'source_file': str(html_path)
    }

    return result


def save_json(obj: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    # pequena rotina de teste manual quando executado diretamente
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('html', help='Arquivo HTML de horário por turma')
    p.add_argument('--out', help='Arquivo JSON de saída', default='output/horario.json')
    args = p.parse_args()

    res = parse_horario_por_turma(Path(args.html))
    save_json(res, Path(args.out))
    print('Salvo em', args.out)
