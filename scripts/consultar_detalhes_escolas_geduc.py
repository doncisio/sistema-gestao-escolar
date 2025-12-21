"""
Consultar detalhes das instituições extraídas do GEDUC

Gera `config/detalhes_escolas_geduc.json` com campos adicionais para cada escola

Uso:
    python scripts/consultar_detalhes_escolas_geduc.py

Observação: executa login interativo e pede para resolver reCAPTCHA no navegador.
"""

import json
import time
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# garantir que o diretório raiz esteja no path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.importadores.geduc import AutomacaoGEDUC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


def extrair_campos_pagina(driver, nomes_campos):
    dados = {}
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    for campo in nomes_campos:
        valor = None
        # 1) tentar campo por name via Selenium
        try:
            try:
                elem = driver.find_element(By.NAME, campo)
            except Exception:
                elem = driver.find_element(By.ID, campo)

            tag = elem.tag_name.lower()
            if tag in ('input', 'textarea'):
                valor = elem.get_attribute('value')
            elif tag == 'select':
                try:
                    sel = Select(elem)
                    opt = sel.first_selected_option
                    valor = opt.text.strip()
                except Exception:
                    valor = elem.text.strip()
        except Exception:
            # fallback: procurar no HTML com BeautifulSoup por name/id
            try:
                s = soup.find(attrs={"name": campo}) or soup.find(id=campo)
                if s:
                    if s.name == 'select':
                        opt = s.find('option', selected=True)
                        if not opt:
                            # pegar primeira não vazia
                            opts = [o for o in s.find_all('option') if (o.get('value') or '').strip()]
                            opt = opts[0] if opts else None
                        if opt:
                            valor = opt.text.strip()
                    else:
                        valor = (s.get('value') or s.text or '').strip()
            except Exception:
                valor = None

        dados[campo] = valor

    return dados


def main():
    caminho_map = Path('config/mapeamento_geduc_latest.json')
    if not caminho_map.exists():
        print('Arquivo config/mapeamento_geduc_latest.json não encontrado. Rode o extrator primeiro.')
        return

    mapping = json.loads(caminho_map.read_text(encoding='utf-8'))
    escolas = mapping.get('escolas', [])
    if not escolas:
        print('Nenhuma escola encontrada no mapeamento. Rode o extrator primeiro.')
        return

    # Solicitar credenciais
    usuario = input('\n👤 Usuário GEDUC: ').strip()
    if not usuario:
        print('Usuário não fornecido. Encerrando.')
        return
    import getpass
    senha = getpass.getpass('🔐 Senha GEDUC: ')
    if not senha:
        print('Senha não fornecida. Encerrando.')
        return

    ag = AutomacaoGEDUC(headless=False)
    print('\n🌐 Iniciando navegador...')
    if not ag.iniciar_navegador():
        print('Falha ao iniciar navegador')
        return

    print('🔐 Fazendo login...')
    if not ag.fazer_login(usuario, senha):
        print('Falha no login. Encerrando.')
        ag.fechar()
        return

    # Adicionar campos de região/polo (variações possíveis de atributo)
    nomes_campos = ['NOME', 'ENDERECO', 'CODIGOINEP', 'IDCIDADE', 'IDESTADO', 'TELEFONE', 'CEP', 'BAIRRO', 'REGIAO', 'IDREGIAO', 'REGIÃO']

    resultados = []

    for idx, item in enumerate(escolas, start=1):
        idv = item.get('id_geduc')
        nome_base = item.get('nome')
        print(f"[{idx}/{len(escolas)}] Consultando id={idv} - {nome_base}")
        try:
            url = f"{ag.url_base}/index.php?class=InstituicaoForm&method=onEdit&key={idv}"
            ag.driver.get(url)
            time.sleep(1.2)

            dados = extrair_campos_pagina(ag.driver, nomes_campos)
            dados.update({'id_geduc': idv, 'nome_geduc': nome_base})
            resultados.append(dados)
        except Exception as e:
            print(f"  ✗ Erro ao consultar {idv}: {e}")
            resultados.append({'id_geduc': idv, 'nome_geduc': nome_base, 'error': str(e)})

    # Salvar resultados
    out_path = Path('config/detalhes_escolas_geduc.json')
    out_latest = Path('config/detalhes_escolas_geduc_latest.json')
    payload = {'extraido_em': time.strftime('%Y-%m-%dT%H:%M:%S'), 'escolas': resultados}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    out_latest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"\n💾 Dados salvos em: {out_path}")
    ag.fechar()


if __name__ == '__main__':
    main()
