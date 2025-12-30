#!/usr/bin/env python3
"""
Script interativo para buscar páginas de horários no GEDUC.

Fluxo:
- Inicia o navegador via `AutomacaoGEDUC`
- Faz login (reCAPTCHA resolvido manualmente pelo usuário)
- Permite ao usuário navegar no navegador e pressionar ENTER no terminal para salvar a página atual como HTML
- Opcionalmente o HTML é parseado com `parse_horario_por_turma` e salvo como JSON ao lado

Uso:
  - Defina as variáveis de ambiente `GEDUC_USER` e `GEDUC_PASS` ou informe quando solicitado
  - Execute: python scripts/fetch_horarios_geduc.py
  - Após o login e resolução do reCAPTCHA, navegue até uma página de horário e pressione ENTER

"""
from pathlib import Path
import os
import time
import getpass
from datetime import datetime

from src.importadores.geduc import AutomacaoGEDUC
from selenium.webdriver.common.by import By
from src.importers.geduc_horarios import parse_horario_por_turma, save_json


OUT_DIR = Path(r"c:/gestao/historico_geduc_imports")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def timestamp_str():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def salvar_pagina(driver, prefix="horario"):
    ts = timestamp_str()
    filename = f"{prefix}_{ts}.html"
    out_path = OUT_DIR / filename
    html = driver.page_source
    out_path.write_text(html, encoding="utf-8")
    print(f"✓ HTML salvo: {out_path}")

    # Tentar parsear imediatamente (silencioso em caso de falha)
    try:
        json_data = parse_horario_por_turma(out_path)
        json_path = out_path.with_suffix('.json')
        save_json(json_data, json_path)
        print(f"✓ JSON parseado salvo: {json_path}")
        return out_path, json_path
    except Exception as e:
        print(f"⚠ Falha ao parsear HTML salvo: {e}")
        return out_path, None


def main():
    user = os.environ.get('GEDUC_USER')
    pwd = os.environ.get('GEDUC_PASS')

    if not user:
        user = input('Usuário GEDUC: ').strip()
    if not pwd:
        pwd = getpass.getpass('Senha GEDUC (input oculto): ')

    automacao = AutomacaoGEDUC(headless=False)

    print('\n→ Iniciando navegador...')
    if not automacao.iniciar_navegador():
        print('✗ Não foi possível iniciar o navegador. Veja logs.')
        return

    try:
        print('\n→ Fazendo login. Você precisará resolver o reCAPTCHA manualmente no navegador.')
        ok = automacao.fazer_login(user, pwd, timeout_recaptcha=180)
        if not ok:
            print('✗ Login falhou ou timeout. Abortando.')
            return

        print('\n✓ Login efetuado. Instruções:')
        print('- Navegue no navegador até a página de HORÁRIO da turma desejada')
        print('- Quando estiver na página, volte ao terminal e pressione ENTER para salvar a página atual')
        print("- Digite 'auto' + ENTER para tentar um modo automático (pode falhar dependendo da página)")
        print("- Digite 'done' + ENTER para encerrar e fechar o navegador\n")

        while True:
            cmd = input('Aguardando comando (ENTER salvar / auto / done): ').strip()
            if cmd.lower() == 'done':
                print('Encerrando...')
                break
                if cmd.lower() == 'auto':
                    print('Tentando modo automático: navegar em Secretaria → Horário por Semana e salvar páginas de horário...')
                    try:
                        # Acessar listagem de horários por semana
                        list_url = f"{automacao.url_base}/index.php?class=QuadhorariosemanalList&method=onReload"
                        automacao.driver.get(list_url)
                        time.sleep(1)

                        # Buscar links para formulário de horário semanal
                        links = automacao.driver.find_elements(By.CSS_SELECTOR, "a[href*='QuadhorariosemanalForm']")
                        # Caso não encontre, tentar links que abrem o item (ícone folder)
                        if not links:
                            links = automacao.driver.find_elements(By.CSS_SELECTOR, "a[title*='Abrir Hor'] , a[href*='QuadhorariosemanalList']")

                        hrefs = []
                        for a in links:
                            try:
                                href = a.get_attribute('href')
                                if href and 'Quadhorariosemanal' in href:
                                    hrefs.append(href)
                            except Exception:
                                continue

                        hrefs = list(dict.fromkeys(hrefs))  # dedupe
                        print(f'→ {len(hrefs)} link(s) encontrados')

                        for href in hrefs:
                            try:
                                # Normalizar URL relativo
                                if href.startswith('index.php') or href.startswith('/index.php'):
                                    full = automacao.url_base.rstrip('/') + '/' + href.lstrip('/')
                                else:
                                    full = href

                                print('→ Acessando', full)
                                automacao.driver.get(full)
                                time.sleep(1)
                                salvar_pagina(automacao.driver)
                            except Exception as e:
                                print('⚠ Erro salvando link', href, e)

                    except Exception as e:
                        print('⚠ Erro no modo automático:', e)
                    continue

            # default: salvar a página atual
            try:
                salvar_pagina(automacao.driver)
            except Exception as e:
                print('✗ Erro ao salvar página atual:', e)

    finally:
        print('\n→ Fechando navegador...')
        automacao.fechar()


if __name__ == '__main__':
    main()
