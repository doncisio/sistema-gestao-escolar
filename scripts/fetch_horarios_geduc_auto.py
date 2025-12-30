#!/usr/bin/env python3
"""
Execução automática: inicia navegador, faz login no GEDUC (aguarda reCAPTCHA),
navega para QuadhorariosemanalList e salva as páginas de horário encontradas.

Use as variáveis de ambiente `GEDUC_USER` e `GEDUC_PASS`.
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# garantir que o root do projeto esteja no sys.path para permitir imports relativos
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.importadores.geduc import AutomacaoGEDUC
from src.importers.geduc_horarios import parse_horario_por_turma, save_json
from selenium.webdriver.common.by import By


OUT_DIR = Path(r"c:/gestao/historico_geduc_imports")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def salvar_pagina(driver, prefix="horario"):
    path = OUT_DIR / f"{prefix}_{ts()}.html"
    html = driver.page_source
    path.write_text(html, encoding='utf-8')
    print("✓ HTML salvo:", path)
    try:
        data = parse_horario_por_turma(path)
        jpath = path.with_suffix('.json')
        save_json(data, jpath)
        print("✓ JSON salvo:", jpath)
    except Exception as e:
        print("⚠ Erro ao parsear salvo:", e)


def main():
    user = os.environ.get('GEDUC_USER')
    pwd = os.environ.get('GEDUC_PASS')
    if not user:
        user = input('GEDUC usuário: ')
    if not pwd:
        # não ecoar a senha no console
        try:
            import getpass
            pwd = getpass.getpass('GEDUC senha: ')
        except Exception:
            pwd = input('GEDUC senha: ')

    automacao = AutomacaoGEDUC(headless=False)
    if not automacao.iniciar_navegador():
        raise SystemExit('Falha ao iniciar navegador')

    try:
        print('→ Fazendo login (resolva reCAPTCHA no navegador)')
        ok = automacao.fazer_login(user, pwd, timeout_recaptcha=300)
        if not ok:
            raise SystemExit('Login falhou ou timeout')

        print('✓ Login ok; navegando para listagem de horários...')
        list_url = f"{automacao.url_base}/index.php?class=QuadhorariosemanalList&method=onReload"
        automacao.driver.get(list_url)
        time.sleep(1.5)

        # coletar links para o formulário de horário semanal
        anchors = automacao.driver.find_elements(By.CSS_SELECTOR, "a[href*='QuadhorariosemanalForm'], a[href*='QuadhorariosemanalList']")
        hrefs = []
        for a in anchors:
            try:
                href = a.get_attribute('href')
                if href and 'Quadhorariosemanal' in href:
                    hrefs.append(href)
            except Exception:
                continue

        hrefs = list(dict.fromkeys(hrefs))
        print(f'→ {len(hrefs)} link(s) encontrados')

        for href in hrefs:
            print('→ Acessando', href)
            if href.startswith('index.php') or href.startswith('/index.php'):
                full = automacao.url_base.rstrip('/') + '/' + href.lstrip('/')
            else:
                full = href
            automacao.driver.get(full)
            time.sleep(1.0)
            salvar_pagina(automacao.driver, prefix='horario')

        print('Concluído')

    finally:
        automacao.fechar()


if __name__ == '__main__':
    main()
