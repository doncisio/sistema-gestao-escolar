from bs4 import BeautifulSoup
from pathlib import Path

p = Path(r"c:/gestao/historico_geduc_imports/horario_20251227_162253.html")
html = p.read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

print('Buscando textos contendo "turma" (case-insensitive):')
for tag in soup.find_all(text=lambda t: t and 'turma' in t.lower()):
    txt = tag.strip()
    if txt:
        print('-', txt)

print('\nProcurando selects/labels relacionados a turma:')
for sel in soup.find_all(['select', 'label', 'h1', 'h2', 'h3', 'strong']):
    txt = (sel.get_text() or '').strip()
    if 'turma' in txt.lower() or 'ano' in txt.lower() or 'turmas' in txt.lower():
        print('TAG', sel.name, '=>', txt[:200])

print('\nProcurando option com id ou name contendo TURMA:')
for opt in soup.find_all('option'):
    if opt.get('value') and ('TURMA' in opt.get('value').upper() or 'turma' in opt.get_text().lower()):
        print('OPTION', opt.get('value'), '=>', opt.get_text())
