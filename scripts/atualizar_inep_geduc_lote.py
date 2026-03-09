"""
Atualização em lote do CODIGOINEP dos alunos no GEDUC
======================================================
Lê um CSV/Excel com colunas IDALUNO e CODIGOINEP (ou CPF e CODIGOINEP)
e para cada linha abre o formulário do aluno no GEDUC, preenche o campo
"Identificação única MEC" (CODIGOINEP) e salva.

Uso:
    python scripts/atualizar_inep_geduc_lote.py --arquivo planilha.csv
    python scripts/atualizar_inep_geduc_lote.py --arquivo planilha.xlsx --coluna-id CPF

Formato do arquivo de entrada (CSV ou Excel):
    Coluna de ID do aluno:   IDALUNO  (GEDUC)  — padrão
                         ou  CPF              — com --coluna-id CPF
    Coluna INEP:             CODIGOINEP        — padrão
                         ou  outro nome com --coluna-inep NOME_COLUNA

Pré-requisitos:
    pip install selenium webdriver-manager pandas openpyxl
"""

import sys
import time
import argparse
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    import pandas as pd
except ImportError:
    print("✗ pandas não instalado. Execute: pip install pandas openpyxl")
    sys.exit(1)

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("✗ selenium não instalado. Execute: pip install selenium webdriver-manager")
    sys.exit(1)

from src.importadores.geduc import AutomacaoGEDUC

# ─── configuração de log ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("inep_lote")

URL_BASE = "https://semed.geduc.com.br"


# ─── helpers ──────────────────────────────────────────────────────────────────

def _ler_planilha(caminho: str, coluna_id: str, coluna_inep: str) -> list[dict]:
    """
    Lê CSV ou Excel e retorna lista de dicts com chaves 'id_aluno' e 'codigoinep'.
    Linhas com CODIGOINEP vazio/nulo são ignoradas.
    """
    caminho = Path(caminho)
    if not caminho.exists():
        logger.error("✗ Arquivo não encontrado: %s", caminho)
        sys.exit(1)

    ext = caminho.suffix.lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(caminho, dtype=str)
    elif ext == ".csv":
        df = pd.read_csv(caminho, dtype=str, sep=None, engine="python")
    else:
        logger.error("✗ Formato não suportado: %s  (use .csv, .xlsx ou .xls)", ext)
        sys.exit(1)

    # normalizar nomes de colunas (maiúsculas, sem espaços extras)
    df.columns = [c.strip().upper() for c in df.columns]
    coluna_id   = coluna_id.strip().upper()
    coluna_inep = coluna_inep.strip().upper()

    faltantes = [c for c in (coluna_id, coluna_inep) if c not in df.columns]
    if faltantes:
        logger.error("✗ Coluna(s) não encontrada(s): %s", faltantes)
        logger.error("  Colunas disponíveis: %s", list(df.columns))
        sys.exit(1)

    registros = []
    for _, row in df.iterrows():
        id_val   = str(row[coluna_id]).strip()
        inep_val = str(row[coluna_inep]).strip()
        if id_val in ("", "nan", "None") or inep_val in ("", "nan", "None"):
            continue
        registros.append({"id_aluno": id_val, "codigoinep": inep_val})

    logger.info("✓ %d registros com CODIGOINEP carregados.", len(registros))
    return registros


def _obter_idaluno_por_cpf(driver, cpf: str) -> str | None:
    """
    Busca o IDALUNO de um aluno pelo CPF na lista de alunos do GEDUC.
    Retorna a string do ID ou None se não encontrado.
    """
    url = f"{URL_BASE}/index.php?class=ListarAluno&tabela=AlunoFormNew"
    driver.get(url)
    wait = WebDriverWait(driver, 15)

    try:
        # Tentar campo de busca por CPF
        campo_busca = wait.until(EC.presence_of_element_located((By.NAME, "CPF")))
        campo_busca.clear()
        campo_busca.send_keys(cpf)
        # submeter pesquisa
        btn = driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")
        btn.click()
        time.sleep(2)
    except (TimeoutException, NoSuchElementException):
        pass

    # Procurar link de edição na tabela de resultados
    try:
        link = driver.find_element(
            By.XPATH,
            f"//a[contains(@href,'AlunoFormNew') and contains(@href,'onEdit')]"
            f"[ancestor::tr[contains(.,'{cpf}')]]"
        )
        href = link.get_attribute("href")
        import re
        m = re.search(r"IDALUNO=(\d+)", href)
        if m:
            return m.group(1)
    except NoSuchElementException:
        pass

    return None


def _atualizar_codigoinep(driver, idaluno: str, codigoinep: str) -> bool:
    """
    Abre o formulário do aluno, preenche CODIGOINEP e salva.
    Retorna True se bem-sucedido.
    """
    url_editar = (
        f"{URL_BASE}/index.php"
        f"?class=AlunoFormNew&method=onEdit&key={idaluno}&IDALUNO={idaluno}"
    )
    driver.get(url_editar)
    wait = WebDriverWait(driver, 20)

    try:
        # Aguardar o campo CODIGOINEP estar disponível
        campo = wait.until(
            EC.presence_of_element_located((By.NAME, "CODIGOINEP"))
        )
    except TimeoutException:
        logger.warning("  ✗ Campo CODIGOINEP não encontrado para IDALUNO=%s", idaluno)
        return False

    # Limpar e preencher o campo
    driver.execute_script("arguments[0].value = '';", campo)
    campo.clear()
    campo.send_keys(codigoinep)

    # Clicar em "Salvar Registro"
    try:
        btn_salvar = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH,
                 "//button[contains(@onclick,'onSave')] | "
                 "//button[contains(@aria-label,'Salvar')] | "
                 "//button[.//span[contains(text(),'Salvar')]]")
            )
        )
        driver.execute_script("arguments[0].click();", btn_salvar)
    except TimeoutException:
        logger.warning("  ✗ Botão Salvar não encontrado para IDALUNO=%s", idaluno)
        return False

    # Aguardar confirmação (URL muda ou mensagem de sucesso)
    time.sleep(2)

    # Verificar se houve erro óbvio na página
    page_source = driver.page_source.lower()
    if "erro" in page_source and "codigoinep" in page_source:
        logger.warning("  ✗ Possível erro ao salvar IDALUNO=%s", idaluno)
        return False

    return True


# ─── fluxo principal ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Atualiza CODIGOINEP (número INEP) dos alunos no GEDUC em lote."
    )
    parser.add_argument(
        "--arquivo", "-a", required=True,
        help="Caminho para o CSV ou Excel com os dados (ex: inep.csv)"
    )
    parser.add_argument(
        "--coluna-id", default="IDALUNO",
        help="Nome da coluna com o ID do aluno no GEDUC (padrão: IDALUNO) ou CPF"
    )
    parser.add_argument(
        "--coluna-inep", default="CODIGOINEP",
        help="Nome da coluna com o número INEP (padrão: CODIGOINEP)"
    )
    parser.add_argument(
        "--usuario", "-u", default="",
        help="Usuário do GEDUC (pode ser digitado interativamente)"
    )
    parser.add_argument(
        "--pausa", type=float, default=1.5,
        help="Pausa em segundos entre cada aluno (padrão: 1.5)"
    )
    parser.add_argument(
        "--inicio", type=int, default=0,
        help="Índice inicial para retomar processamento interrompido (padrão: 0)"
    )
    args = parser.parse_args()

    # ── Credenciais ────────────────────────────────────────────────────────────
    usuario = args.usuario or input("Usuário GEDUC: ").strip()
    senha   = input("Senha GEDUC (não é exibida): ")

    # ── Leitura da planilha ────────────────────────────────────────────────────
    registros = _ler_planilha(args.arquivo, args.coluna_id, args.coluna_inep)
    if not registros:
        logger.error("✗ Nenhum registro válido encontrado.")
        sys.exit(1)

    total = len(registros)
    logger.info("→ Total a processar: %d alunos (iniciando no índice %d)", total, args.inicio)

    # ── Iniciar navegador e login ──────────────────────────────────────────────
    geduc = AutomacaoGEDUC(headless=False)
    geduc.iniciar_navegador()

    ok = geduc.fazer_login(usuario, senha, timeout_recaptcha=120)
    if not ok:
        logger.error("✗ Falha no login. Encerrando.")
        geduc.driver.quit()
        sys.exit(1)

    driver = geduc.driver
    usa_cpf = args.coluna_id.strip().upper() == "CPF"

    # ── Processar cada aluno ───────────────────────────────────────────────────
    sucessos  = 0
    falhas    = 0
    log_erros: list[str] = []

    for idx, reg in enumerate(registros[args.inicio:], start=args.inicio):
        id_value   = reg["id_aluno"]
        codigoinep = reg["codigoinep"]

        logger.info("[%d/%d] %s=%s  →  INEP=%s",
                    idx + 1, total, args.coluna_id, id_value, codigoinep)

        idaluno = id_value

        # Se a coluna de ID é CPF, precisamos descobrir o IDALUNO
        if usa_cpf:
            idaluno = _obter_idaluno_por_cpf(driver, id_value)
            if not idaluno:
                logger.warning("  ✗ IDALUNO não encontrado para CPF=%s — pulado.", id_value)
                falhas += 1
                log_erros.append(f"CPF {id_value}: IDALUNO não encontrado")
                continue

        resultado = _atualizar_codigoinep(driver, idaluno, codigoinep)

        if resultado:
            logger.info("  ✓ CODIGOINEP salvo com sucesso.")
            sucessos += 1
        else:
            logger.warning("  ✗ Falha ao salvar IDALUNO=%s.", idaluno)
            falhas += 1
            log_erros.append(f"IDALUNO {idaluno} (orig={id_value}): falha ao salvar")

        time.sleep(args.pausa)

    # ── Relatório final ────────────────────────────────────────────────────────
    logger.info("\n%s", "=" * 55)
    logger.info("RESULTADO FINAL")
    logger.info("  ✓ Sucesso : %d", sucessos)
    logger.info("  ✗ Falhas  : %d", falhas)
    if log_erros:
        logger.info("\nRegistros com falha:")
        for e in log_erros:
            logger.info("  • %s", e)
    logger.info("=" * 55)

    driver.quit()


if __name__ == "__main__":
    main()
