from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import json

from bs4 import BeautifulSoup


def _normalize_key(s: str) -> str:
    if s is None:
        return ''
    s = s.upper()
    # remover acentos básicos
    s = (s
         .replace('Á', 'A').replace('À', 'A').replace('Ã', 'A').replace('Â', 'A')
         .replace('É', 'E').replace('È', 'E').replace('Ê', 'E')
         .replace('Í', 'I')
         .replace('Ó', 'O').replace('Ô', 'O').replace('Õ', 'O')
         .replace('Ú', 'U')
         .replace('Ç', 'C'))
    # manter apenas alfanuméricos
    s = re.sub(r'[^A-Z0-9]', '', s)
    return s


def parse_local_turmas(html_path: Path) -> List[Dict[str, Any]]:
    """Parseia uma página de listagem de turmas do sistema local.

    Retorna lista de dicts: { 'nome': str, 'href': str|None, 'raw': str }
    """
    html = html_path.read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')

    turmas: List[Dict[str, Any]] = []

    # Tentar encontrar selects de opção (muito comum)
    sel = soup.find('select')
    if sel:
        for opt in sel.find_all('option'):
            nome = opt.get_text(strip=True)
            if not nome:
                continue
            turmas.append({'nome': nome, 'href': None, 'raw': nome})
        if turmas:
            return turmas

    # Caso não exista select, procurar por tabelas com links
    for table in soup.find_all('table'):
        for a in table.find_all('a', href=True):
            nome = a.get_text(strip=True)
            if not nome:
                continue
            href = a['href']
            turmas.append({'nome': nome, 'href': href, 'raw': nome})
        if turmas:
            return turmas

    # Fallback: procurar por linhas com textos que pareçam turmas
    for li in soup.find_all(['li', 'div', 'p']):
        txt = li.get_text(strip=True)
        if not txt:
            continue
        # heurística simples: contém dígito e letra (ex: '1º Ano A MATUTINO')
        if re.search(r'\d', txt) and len(txt) > 3:
            turmas.append({'nome': txt, 'href': None, 'raw': txt})
    return turmas


def parse_local_horario_por_turma(html_path: Path) -> Dict[str, Any]:
    """Parseia uma página de horário por turma do sistema local.

    Retorna dict com: turma_nome, turno (quando possível), horarios: list de linhas
    Cada linha é dict com 'horario' e colunas por dia (Segunda..Sexta).
    """
    html = html_path.read_text(encoding='utf-8', errors='ignore')
    soup = BeautifulSoup(html, 'html.parser')

    # tentar obter título/identificação
    titulo = None
    for tag in ['h1', 'h2', 'h3', 'title']:
        t = soup.find(tag)
        if t and t.get_text(strip=True):
            titulo = t.get_text(strip=True)
            break

    # procurar por tabela contendo dias da semana
    table = None
    for t in soup.find_all('table'):
        txt = t.get_text().upper()
        if any(d in txt for d in ['SEGUNDA', 'TERÇA', 'QUARTA', 'QUINTA', 'SEXTA']):
            table = t
            break

    rows = []
    if table:
        # identificar cabeçalho com horários/dias
        thead = table.find('thead')
        body = table.find('tbody') or table
        for tr in body.find_all('tr'):
            tds = tr.find_all(['td', 'th'])
            if not tds:
                continue
            contents = [td.get_text(strip=True) for td in tds]
            rows.append(contents)

    # Tentar extrair turno a partir do título
    turno = None
    if titulo:
        up = titulo.upper()
        if 'MATUT' in up:
            turno = 'Matutino'
        elif 'VESP' in up or 'VESPERT' in up:
            turno = 'Vespertino'
        elif 'NOTUR' in up:
            turno = 'Noturno'

    return {'turma_nome': titulo, 'turno': turno, 'rows': rows, 'source_file': str(html_path)}


def build_local_map_from_folder(folder: Path) -> Dict[str, Dict[str, Any]]:
    """Varre uma pasta com páginas salvas e retorna mapa de chaves normalizadas -> horario dict."""
    folder = Path(folder)
    mapa = {}

    # tentar localizar arquivos conhecidos
    # 'turmas semana.html' para lista; 'horario por turma.html' para exemplo de turma
    turmas_files = list(folder.glob('*.html'))
    # primeiro, tentar parsear arquivos de turma individual e indexar por nome
    for f in turmas_files:
        name = f.name.lower()
        if 'horario' in name and 'turma' in name:
            try:
                h = parse_local_horario_por_turma(f)
                key = _normalize_key(h.get('turma_nome') or f.stem)
                mapa[key] = h
            except Exception:
                continue

    # depois, tentar varrer arquivo de lista para achar links e abrir os vinculados
    for f in turmas_files:
        name = f.name.lower()
        if 'turmas' in name:
            try:
                turmas = parse_local_turmas(f)
                for t in turmas:
                    nome = t.get('nome')
                    key = _normalize_key(nome)
                    # se houver href relativo, tentar abrir arquivo correspondente
                    href = t.get('href')
                    horario = None
                    if href:
                        # transformar href em path local se for relativo
                        p = (folder / href).resolve()
                        if p.exists():
                            horario = parse_local_horario_por_turma(p)
                    if not horario:
                        # tentar achar arquivo que contenha parte do nome
                        for cand in turmas_files:
                            if nome and nome.lower() in cand.name.lower():
                                try:
                                    horario = parse_local_horario_por_turma(cand)
                                    break
                                except Exception:
                                    continue
                    if horario:
                        mapa[key] = horario
            except Exception:
                continue

    return mapa


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('folder', help='Pasta contendo as páginas HTML salvas')
    p.add_argument('--out', help='Arquivo JSON de saída', default='output/local_horarios.json')
    args = p.parse_args()
    m = build_local_map_from_folder(Path(args.folder))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Mapeado', len(m), 'turmas. Saída em', args.out)
