"""
Importador de Alunos do GEDUC para Sistema Local
ETAPA 1: Extrai dados do GEDUC e salva em arquivo JSON
ETAPA 2: Importa do arquivo JSON para o banco de dados local
Importa apenas alunos que não existem no sistema (verifica por nome normalizado)
"""

import os
import sys
import re
import time
import json
import traceback
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.connection import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Configurações do GEDUC
GEDUC_URL = "https://semed.geduc.com.br"
GEDUC_LOGIN_URL = f"{GEDUC_URL}/index.php?class=LoginForm"
GEDUC_TURMAS_URL = f"{GEDUC_URL}/index.php?class=TurmaList"

# Mapeamentos de códigos
MAPA_DEFICIENCIAS = {
    '1': 'CEGUEIRA', '2': 'BAIXA VISÃO', '3': 'SURDEZ',
    '4': 'DEF. AUDITIVA', '5': 'DEF. INTELECTUAL', '6': 'DEF. FÍSICA',
    '7': 'DEF. MÚLTIPLA', '8': 'SURDOCEGUEIRA', '9': 'OUTROS', '10': 'VISÃO MONOCULAR'
}

MAPA_TRANSTORNOS = {
    '1': 'TDAH', '2': 'DISLEXIA', '3': 'DISGRAFIA',
    '4': 'DISLALIA', '5': 'DISCALCULIA', '6': 'TPAC', '7': None
}

MAPA_TGD = {
    '1': 'TEA', '2': 'SÍNDROME DE RETT',
    '3': 'SÍNDROME DE ASPERGER', '4': 'TDI'
}

MAPA_RACA = {
    '0': 'Não declarada', '1': 'Branca', '2': 'Preta',
    '3': 'Parda', '4': 'Amarela', '5': 'Indígena'
}

# Mapa de código IBGE do estado (2 dígitos) → sigla UF
MAPA_CODIGO_UF = {
    '11': 'RO', '12': 'AC', '13': 'AM', '14': 'RR', '15': 'PA',
    '16': 'AP', '17': 'TO', '21': 'MA', '22': 'PI', '23': 'CE',
    '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL', '28': 'SE',
    '29': 'BA', '31': 'MG', '32': 'ES', '33': 'RJ', '35': 'SP',
    '41': 'PR', '42': 'SC', '43': 'RS', '50': 'MS', '51': 'MT',
    '52': 'GO', '53': 'DF',
}

# Mapa de raça GEDUC → ENUM do banco local
MAPA_RACA_ENUM = {
    'Branca': 'branco',
    'Preta': 'preto',
    'Parda': 'pardo',
    'Amarela': 'amarelo',
    'Indígena': 'indígena',
    'Não declarada': 'pardo',
}

# Preposições que não são capitalizadas em nomes próprios
_PREPOSICOES = {'de', 'da', 'das', 'do', 'dos', 'e', 'em', 'a', 'o', 'ao'}


def normalizar_nome(nome: str) -> str:
    """Normaliza nome: remove acentos, maiúsculo, sem caracteres especiais (usado para comparação)"""
    if not nome:
        return ""
    nome_sem_acento = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nome_sem_acento if not unicodedata.combining(c)])
    nome_upper = nome_sem_acento.upper()
    nome_limpo = re.sub(r'[^A-Z\s]', '', nome_upper)
    return ' '.join(nome_limpo.split())


def capitalizar_nome(nome: str) -> str:
    """Converte nome para Title Case respeitando preposições (padrão do banco)"""
    if not nome:
        return ""
    partes = nome.strip().split()
    resultado = []
    for i, p in enumerate(partes):
        if i == 0 or p.lower() not in _PREPOSICOES:
            resultado.append(p.capitalize())
        else:
            resultado.append(p.lower())
    return ' '.join(resultado)


def formatar_cpf(cpf_raw: str) -> Optional[str]:
    """Formata CPF de 11 dígitos para xxx.xxx.xxx-xx"""
    if not cpf_raw:
        return None
    digits = re.sub(r'\D', '', cpf_raw)
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"
    return cpf_raw or None


# Palavras com cedilha/acento que o GEDUC grava em CAIXA ALTA sem acento
_PALAVRAS_MUNICIPIO: dict = {
    # preposições (ficam minúsculas, exceto início da string)
    'DE': 'de', 'DO': 'do', 'DA': 'da', 'DOS': 'dos', 'DAS': 'das', 'E': 'e',
    # palavras que precisam de acento ou cedilha
    'SAO': 'São', 'JOSE': 'José', 'JOAO': 'João',
    'LUIS': 'Luís', 'LUIZ': 'Luiz',
    'PACO': 'Paço', 'ACAILANDIA': 'Açailândia',
    'GONCALO': 'Gonçalo', 'MARANHAO': 'Maranhão',
    'BELEM': 'Belém', 'MACAPA': 'Macapá', 'AMAPA': 'Amapá',
    'PARNAIBA': 'Parnaíba', 'TERESINA': 'Teresina',
    'CODO': 'Codó', 'TURIACU': 'Turiaçu', 'ICATU': 'Icatu',
    'ACAILANDIA': 'Açailândia', 'ACARA': 'Açará',
    'BRASILIA': 'Brasília', 'GOIANIA': 'Goiânia',
    'RIBEIRAO': 'Ribeirão', 'SERTAOZINHO': 'Sertãozinho',
    'SANTAREM': 'Santarém', 'BRAGANCA': 'Bragança',
    'INES': 'Inês', 'ALCANTARA': 'Alcântara',
    'VARZEA': 'Várzea', 'CAUCAIA': 'Caucaia',
    'PARAUAPEBAS': 'Parauapebas', 'TUCURUI': 'Tucuruí',
    'FLORIANOPOLIS': 'Florianópolis', 'FORTALEZA': 'Fortaleza',
    'SAO': 'São',  # variante sem til
}


def _sem_acento(texto: str) -> str:
    """Remove acentos/cedilha para normalização de lookup."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def _normalizar_municipio(texto: str) -> Optional[str]:
    """Normaliza nome de município vindo do GEDUC:
    - Descarta sufixo '- UF' (ex: 'PACO DO LUMIAR - MA' → 'Paço do Lumiar')
    - Descarta valores inválidos ('00', '0', 'None')
    - Aplica capitalização correta com acentos/cedilha
    """
    if not texto or str(texto).strip() in ('', 'None', '00', '0'):
        return None
    texto = str(texto).strip()
    # Remover sufixo " - UF" (ex: "PACO DO LUMIAR - MA")
    if ' - ' in texto:
        texto = texto.split(' - ')[0].strip()
    palavras = texto.split()
    resultado = []
    for i, palavra in enumerate(palavras):
        chave = _sem_acento(palavra).upper()
        if chave in _PALAVRAS_MUNICIPIO:
            forma = _PALAVRAS_MUNICIPIO[chave]
            # Primeira palavra nunca fica minúscula
            if i == 0 and forma[0].islower():
                forma = forma[0].upper() + forma[1:]
            resultado.append(forma)
        else:
            resultado.append(palavra.capitalize())
    return ' '.join(resultado)


def extrair_valor_campo(html_content: str, campo: str) -> Optional[str]:
    """Extrai valor de um campo do HTML"""
    pattern = rf"tform_send_data\('form_Aluno',\s*'{campo}',\s*'([^']*)',"
    match = re.search(pattern, html_content)
    if match:
        return match.group(1)
    pattern = rf"tform_send_data_by_id\('form_Aluno',\s*'{campo}',\s*'([^']*)',"
    match = re.search(pattern, html_content)
    return match.group(1) if match else None


def extrair_nome_select(html_content: str, soup, campo: str) -> Optional[str]:
    """Retorna o texto visível da opção selecionada num <select>.
    Combina o código do tform_send_data com as <option> do select para obter o nome real.
    """
    codigo = extrair_valor_campo(html_content, campo)
    if not codigo:
        return None
    sel = soup.find('select', {'name': campo})
    if sel:
        opt = sel.find('option', value=codigo)
        if opt:
            return opt.text.strip() or None
    return codigo or None  # fallback: retorna o próprio código


def extrair_checkboxes(html_content: str, campo_prefix: str) -> List[str]:
    """Extrai valores de campos checkbox marcados"""
    valores = []
    soup = BeautifulSoup(html_content, 'html.parser')
    checkboxes = soup.find_all('input', {'type': 'checkbox', 'checked': True})
    for cb in checkboxes:
        name = cb.get('name', '')
        if name.startswith(campo_prefix):
            valor = cb.get('value', '')
            if valor:
                valores.append(valor)
    return valores


def construir_descricao_transtorno(deficiencias: List[str], transtornos: List[str],
                                   tgd: Optional[str], cid: Optional[str],
                                   althab: Optional[str]) -> str:
    """Constrói descrição do transtorno com abreviações"""
    partes = []
    if tgd and tgd in MAPA_TGD:
        partes.append(MAPA_TGD[tgd])
    for t in transtornos:
        if t in MAPA_TRANSTORNOS and MAPA_TRANSTORNOS[t]:
            partes.append(MAPA_TRANSTORNOS[t])
    for d in deficiencias:
        if d in MAPA_DEFICIENCIAS:
            partes.append(MAPA_DEFICIENCIAS[d])
    if althab == '1':
        partes.append('ALTAS HABILIDADES')
    descricao = ', '.join(partes) if partes else ''
    if cid:
        descricao = f'{descricao} - CID: {cid}' if descricao else f'CID: {cid}'
    return descricao or 'Nenhum'


def converter_data_geduc(data_str: str) -> Optional[str]:
    """Converte data DD/MM/AAAA para AAAA-MM-DD"""
    if not data_str or not data_str.strip():
        return None
    try:
        dt = datetime.strptime(data_str.strip(), '%d/%m/%Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        logger.warning(f"Data inválida: {data_str}")
        return None


def extrair_dados_aluno_html(html_content: str) -> Optional[Dict]:
    """Extrai todos os dados de um aluno do HTML"""
    try:
        nome = extrair_valor_campo(html_content, 'NOME')
        if not nome:
            logger.error("Nome não encontrado")
            return None
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        dados = {
            'nome': nome,
            'nome_normalizado': normalizar_nome(nome),
            'data_nascimento': converter_data_geduc(extrair_valor_campo(html_content, 'DT_NASCIMENTO')),
            'cpf': extrair_valor_campo(html_content, 'CPF'),
            'sexo': None,
            'mae': extrair_valor_campo(html_content, 'FILIACAO_MAE'),
            'pai': extrair_valor_campo(html_content, 'FILIACAO_PAI'),
            'responsavel_tipo': None,  # preenchido abaixo com fallback
            'cpf_mae': extrair_valor_campo(html_content, 'CPFMAE'),
            'cpf_pai': extrair_valor_campo(html_content, 'CPFPAI'),
            'profissao_mae': extrair_valor_campo(html_content, 'PROFISSAO_MAE'),
            'profissao_pai': extrair_valor_campo(html_content, 'PROFISSAO_PAI'),
            'nascimento_mae': converter_data_geduc(extrair_valor_campo(html_content, 'NASCIMENTOMAE')),
            'nascimento_pai': converter_data_geduc(extrair_valor_campo(html_content, 'NASCIMENTOPAI')),
            'outros_nome': extrair_valor_campo(html_content, 'OUTROS_NOME'),
            'outros_cpf': extrair_valor_campo(html_content, 'OUTROS_CPF'),
            'outros_profissao': extrair_valor_campo(html_content, 'OUTROS_PROFISSAO'),
            'outros_nascimento': converter_data_geduc(extrair_valor_campo(html_content, 'OUTROS_NASCIMENTO')),
            'celular': extrair_valor_campo(html_content, 'CELULAR'),
            'email': extrair_valor_campo(html_content, 'EMAIL_RESP'),
            'fone_comercial': extrair_valor_campo(html_content, 'FONE_COM'),
            'cor': extrair_valor_campo(html_content, 'COR'),
            'nacionalidade': extrair_valor_campo(html_content, 'NACIONALIDADE'),
            # Naturalidade — nome real via <select>, código IBGE como fallback
            'codigo_naturalidade': extrair_valor_campo(html_content, 'NATURALIDADE'),
            'local_nascimento':    _normalizar_municipio(extrair_nome_select(html_content, soup, 'NATURALIDADE')),
            'codigo_estado':       MAPA_CODIGO_UF.get(str(extrair_valor_campo(html_content, 'ESTADO') or ''), None),
            'cid': extrair_valor_campo(html_content, 'CID'),
            'tgd': extrair_valor_campo(html_content, 'TGD'),
            'althab': extrair_valor_campo(html_content, 'ALTHAB'),
            'codigo_inep': extrair_valor_campo(html_content, 'CODIGOINEP'),
            'inep_escola': extrair_valor_campo(html_content, 'INEPESCOLA'),
            # Endereço de residência (campos reais do GEDUC)
            'cep':           extrair_valor_campo(html_content, 'CEP'),
            'logradouro':    extrair_valor_campo(html_content, 'RUA'),
            'numero_end':    extrair_valor_campo(html_content, 'N'),
            'complemento':   extrair_valor_campo(html_content, 'COMPLEMENTO'),
            'bairro':        extrair_valor_campo(html_content, 'BAIRRO'),
            # nome real do município e estado de residência via <select>
            'municipio_res': _normalizar_municipio(extrair_nome_select(html_content, soup, 'CIDADE')),
            'uf_res':        extrair_nome_select(html_content, soup, 'ESTADOEND'),
        }
        
        sexo_codigo = extrair_valor_campo(html_content, 'SEXO')
        if sexo_codigo == '1':
            dados['sexo'] = 'M'
        elif sexo_codigo == '2':
            dados['sexo'] = 'F'
        # Se não encontrar, mantém None (campo não detectado no HTML)

        # RESPONSAVEL: tenta tform_send_data primeiro, depois radio button com checked
        resp = extrair_valor_campo(html_content, 'RESPONSAVEL')
        if not resp:
            radio = soup.find('input', {'type': 'radio', 'name': 'RESPONSAVEL', 'checked': True})
            if radio:
                resp = radio.get('value', '') or None
        dados['responsavel_tipo'] = resp
        
        deficiencias = extrair_checkboxes(html_content, 'TIPODEF')
        transtornos = extrair_checkboxes(html_content, 'TGDEDU')
        dados['descricao_transtorno'] = construir_descricao_transtorno(
            deficiencias, transtornos, dados['tgd'], dados['cid'], dados['althab'])
        
        dados['raca'] = MAPA_RACA.get(dados['cor'], 'Não declarada')
        return dados
    except Exception as e:
        logger.error(f"Erro ao extrair dados: {e}")
        return None


def criar_driver_chrome():
    """Cria Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    prefs = {"profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


def fazer_login_geduc(driver, usuario: str, senha: str) -> bool:
    """Faz login no GEDUC"""
    try:
        logger.info("Fazendo login...")
        driver.get(GEDUC_LOGIN_URL)
        wait = WebDriverWait(driver, 10)
        
        # Preenche usuário
        campo_usuario = wait.until(EC.presence_of_element_located((By.NAME, "login")))
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)
        
        # Preenche senha
        campo_senha = driver.find_element(By.NAME, "password")
        campo_senha.clear()
        campo_senha.send_keys(senha)
        
        # Tenta encontrar o botão de várias formas
        botao_entrar = None
        try:
            # Tenta por tipo submit
            botao_entrar = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        except:
            try:
                # Tenta por classe btn-primary ou similar
                botao_entrar = driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
            except:
                try:
                    # Tenta qualquer botão dentro do form
                    botao_entrar = driver.find_element(By.CSS_SELECTOR, "form button")
                except:
                    try:
                        # Tenta por input submit
                        botao_entrar = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                    except:
                        # Última tentativa: pressiona Enter no campo senha
                        campo_senha.send_keys(Keys.RETURN)
                        time.sleep(3)
                        if "LoginForm" not in driver.current_url:
                            logger.info("✅ Login OK (via Enter)")
                            return True
                        logger.error("Login falhou")
                        return False
        
        if botao_entrar:
            botao_entrar.click()
            time.sleep(3)
            if "LoginForm" in driver.current_url:
                logger.error("Login falhou - credenciais inválidas")
                return False
            logger.info("✅ Login OK")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return False


def obter_lista_turmas(driver) -> List[Dict]:
    """Obtém lista de turmas"""
    try:
        logger.info("Buscando turmas...")
        driver.get(GEDUC_TURMAS_URL)
        time.sleep(3)
        
        # Salva HTML para debug
        html_debug = driver.page_source
        logger.info(f"Tamanho do HTML: {len(html_debug)} caracteres")
        
        soup = BeautifulSoup(html_debug, 'html.parser')
        turmas = []
        
        # Tenta diferentes padrões de links
        # Padrão 1: class=AlunoList
        links = soup.find_all('a', href=re.compile(r'class=AlunoList', re.IGNORECASE))
        logger.info(f"Padrão 1 (AlunoList): {len(links)} links encontrados")
        
        if not links:
            # Padrão 2: qualquer link com 'key=' na URL
            links = soup.find_all('a', href=re.compile(r'key=\d+'))
            logger.info(f"Padrão 2 (key=): {len(links)} links encontrados")
        
        if not links:
            # Padrão 3: procura na tabela
            tabela = soup.find('table')
            if tabela:
                links = tabela.find_all('a', href=True)
                logger.info(f"Padrão 3 (tabela): {len(links)} links encontrados")
        
        # Debug: mostra alguns links
        if links:
            logger.info(f"Exemplo de link: {links[0].get('href', 'N/A')[:100]}")
        
        for link in links:
            href = link.get('href', '')
            
            # Filtra apenas links de turma/alunos
            if 'AlunoList' in href or 'TurmaForm' in href or 'MatriculaList' in href:
                match = re.search(r'key=(\d+)', href)
                if match:
                    turma_id = match.group(1)
                    
                    # Pega nome da turma
                    nome = link.get_text(strip=True)
                    if not nome or len(nome) > 100:  # Se texto muito longo ou vazio
                        tr = link.find_parent('tr')
                        if tr:
                            tds = tr.find_all('td')
                            nome = tds[0].get_text(strip=True) if tds else f"Turma {turma_id}"
                        else:
                            nome = f"Turma {turma_id}"
                    
                    # Monta URL completa
                    if href.startswith('http'):
                        url = href
                    elif href.startswith('index.php'):
                        url = f"{GEDUC_URL}/{href}"
                    else:
                        url = f"{GEDUC_URL}/index.php?{href.split('?')[1]}" if '?' in href else f"{GEDUC_URL}/{href}"
                    
                    # Evita duplicatas
                    if not any(t['id'] == turma_id for t in turmas):
                        turmas.append({'id': turma_id, 'nome': nome, 'url': url})
                        logger.info(f"  Turma encontrada: {nome} (ID: {turma_id})")
        
        logger.info(f"✅ {len(turmas)} turmas encontradas")
        
        # Se não encontrou nada, salva HTML para análise
        if not turmas:
            with open('debug_turmas.html', 'w', encoding='utf-8') as f:
                f.write(html_debug)
            logger.warning("HTML salvo em debug_turmas.html para análise")
        
        return turmas
        
    except Exception as e:
        logger.error(f"Erro ao buscar turmas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def obter_lista_alunos_turma(driver, turma_url: str) -> List[Dict]:
    """Obtém lista de alunos de uma turma (com suporte a paginação)"""
    def _extrair_links_pagina(soup) -> List[Dict]:
        """Extrai links de alunos de uma página — aceita qualquer ordem de parâmetros na URL"""
        alunos = []
        ids_vistos = set()
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'AlunoForm' not in href:
                continue
            match = re.search(r'key=(\d+)', href)
            if match and match.group(1) not in ids_vistos:
                url = f"{GEDUC_URL}/{href}" if not href.startswith('http') else href
                alunos.append({'id': match.group(1), 'url': url})
                ids_vistos.add(match.group(1))
        return alunos

    try:
        alunos = []
        ids_coletados = set()
        url_atual = turma_url
        pagina = 1

        while url_atual:
            logger.info(f"  Página {pagina}: {url_atual}")
            driver.get(url_atual)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            novos = _extrair_links_pagina(soup)
            adicionados = 0
            for a in novos:
                if a['id'] not in ids_coletados:
                    alunos.append(a)
                    ids_coletados.add(a['id'])
                    adicionados += 1
            logger.info(f"    {adicionados} alunos encontrados nesta página")

            # Verifica se há próxima página (link "Próximo", ">" ou similar)
            prox = None
            for link in soup.find_all('a', href=True):
                texto = link.get_text(strip=True)
                if texto in ('>', 'Próximo', 'Próxima', 'Next', '»'):
                    href = link.get('href', '')
                    prox = f"{GEDUC_URL}/{href}" if not href.startswith('http') else href
                    break

            # Se não achou link de próxima ou não trouxe alunos novos, encerra
            if not prox or adicionados == 0:
                break
            url_atual = prox
            pagina += 1

        return alunos
    except Exception as e:
        logger.error(f"Erro ao buscar alunos: {e}")
        return []


def acessar_e_extrair_aluno(driver, aluno_url: str) -> Optional[Dict]:
    """Acessa página do aluno e extrai dados"""
    try:
        driver.get(aluno_url)
        time.sleep(2)
        return extrair_dados_aluno_html(driver.page_source)
    except Exception as e:
        logger.error(f"Erro ao acessar aluno: {e}")
        return None


def extrair_alunos_geduc(usuario: str, senha: str, arquivo_saida: str = 'alunos_geduc.json',
                        turmas_especificas: List[str] = None):
    """ETAPA 1: Extrai dados do GEDUC e salva em JSON"""
    driver = None
    dados_completos = {'data_extracao': datetime.now().isoformat(), 'turmas': [], 'total_alunos': 0}
    
    try:
        total_extraidos = 0
        total_erros = 0
        
        driver = criar_driver_chrome()
        if not fazer_login_geduc(driver, usuario, senha):
            return
        
        turmas = obter_lista_turmas(driver)
        if not turmas:
            logger.error("Nenhuma turma encontrada")
            return
        
        if turmas_especificas:
            turmas = [t for t in turmas if t['id'] in turmas_especificas]
        
        for idx, turma in enumerate(turmas, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"TURMA [{idx}/{len(turmas)}]: {turma['nome']}")
            logger.info(f"{'='*60}")
            
            alunos = obter_lista_alunos_turma(driver, turma['url'])
            logger.info(f"{len(alunos)} alunos")
            
            turma_dados = {'id': turma['id'], 'nome': turma['nome'], 'alunos': []}
            
            for i, aluno in enumerate(alunos, 1):
                logger.info(f"  [{i}/{len(alunos)}] ID: {aluno['id']}")
                dados = acessar_e_extrair_aluno(driver, aluno['url'])
                if not dados:
                    total_erros += 1
                    continue
                logger.info(f"    {dados['nome']}")
                if dados.get('descricao_transtorno') != 'Nenhum':
                    logger.info(f"    🏥 {dados['descricao_transtorno']}")
                turma_dados['alunos'].append(dados)
                total_extraidos += 1
                time.sleep(1)
            
            dados_completos['turmas'].append(turma_dados)
        
        dados_completos['total_alunos'] = total_extraidos
        
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(dados_completos, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n✅ {total_extraidos} alunos extraídos")
        logger.info(f"📄 Salvo em: {arquivo_saida}")
        
    except Exception as e:
        logger.error(f"Erro: {e}")
    finally:
        if driver:
            driver.quit()


def aluno_existe(cursor, nome_normalizado: str) -> bool:
    """Verifica se aluno já existe"""
    cursor.execute("SELECT id, nome FROM alunos")
    for aluno_id, nome_banco in cursor.fetchall():
        if normalizar_nome(nome_banco) == nome_normalizado:
            logger.info(f"Já existe: {nome_banco} (ID: {aluno_id})")
            return True
    return False


def buscar_escola_por_inep(cursor, codigo_inep: str) -> Optional[int]:
    """Busca escola por INEP"""
    if not codigo_inep:
        return None
    cursor.execute("SELECT id FROM escolas WHERE inep = %s", (codigo_inep,))
    result = cursor.fetchone()
    return result[0] if result else None


def obter_escola_padrao(cursor) -> int:
    """Retorna primeira escola"""
    cursor.execute("SELECT id FROM escolas ORDER BY id LIMIT 1")
    result = cursor.fetchone()
    if not result:
        raise Exception("Nenhuma escola cadastrada!")
    return result[0]


def inserir_aluno(cursor, dados: Dict, escola_id: int) -> int:
    """Insere aluno no banco"""
    query = """
        INSERT INTO alunos (nome, data_nascimento, sexo, cpf, raca,
                           descricao_transtorno, escola_id,
                           local_nascimento, UF_nascimento,
                           endereco, bairro, cidade, estado, cep)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    raca_enum = MAPA_RACA_ENUM.get(dados.get('raca', 'Não declarada'), 'pardo')
    logradouro = dados.get('logradouro') or ''
    numero = dados.get('numero_end') or ''
    endereco = f"{logradouro}, {numero}" if logradouro and numero else (logradouro or None)
    valores = (
        capitalizar_nome(dados['nome']),
        dados['data_nascimento'],
        dados.get('sexo', 'M'),
        formatar_cpf(dados.get('cpf')),
        raca_enum,
        dados.get('descricao_transtorno', 'Nenhum'),
        escola_id,
        dados.get('local_nascimento') or None,   # nome do município (via <select>)
        dados.get('codigo_estado') or None,       # nome do estado (via <select>)
        endereco,
        dados.get('bairro') or None,
        dados.get('municipio_res') or None,
        dados.get('uf_res') or None,
        dados.get('cep') or None,
    )
    cursor.execute(query, valores)
    return cursor.lastrowid


def _carregar_cache_responsaveis(cursor) -> Dict:
    """Carrega cache de responsáveis existentes: {nome_normalizado: id} e {cpf: id}"""
    cursor.execute("SELECT id, nome, cpf FROM responsaveis")
    cache_nome = {}
    cache_cpf = {}
    for row in cursor.fetchall():
        rid = row[0] if not isinstance(row, dict) else row['id']
        rnome = row[1] if not isinstance(row, dict) else row['nome']
        rcpf = row[2] if not isinstance(row, dict) else row['cpf']
        if rnome:
            cache_nome[normalizar_nome(rnome)] = rid
        if rcpf:
            cache_cpf[rcpf] = rid
    return {'nome': cache_nome, 'cpf': cache_cpf}


def inserir_responsavel(cursor, nome: str, cpf: str, telefone: str,
                        parentesco: str, profissao: str = None,
                        cache: Dict = None) -> int:
    """Insere ou retorna responsável existente.
    Verifica duplicatas por CPF (prioritário) e depois por nome normalizado.
    Passa `cache` (retornado por _carregar_cache_responsaveis) para evitar
    SELECT repetido a cada chamada.
    """
    cpf_fmt = formatar_cpf(cpf) if cpf else None
    nome_fmt = capitalizar_nome(nome) if nome else nome
    nome_norm = normalizar_nome(nome_fmt) if nome_fmt else None

    # 1. Verifica por CPF
    if cpf_fmt:
        if cache and cpf_fmt in cache['cpf']:
            return cache['cpf'][cpf_fmt]
        cursor.execute("SELECT id FROM responsaveis WHERE cpf = %s", (cpf_fmt,))
        result = cursor.fetchone()
        if result:
            rid = result[0] if not isinstance(result, dict) else result['id']
            if cache is not None:
                cache['cpf'][cpf_fmt] = rid
            return rid

    # 2. Verifica por nome normalizado
    if nome_norm:
        if cache and nome_norm in cache['nome']:
            return cache['nome'][nome_norm]
        cursor.execute("SELECT id, nome FROM responsaveis")
        for row in cursor.fetchall():
            rid = row[0] if not isinstance(row, dict) else row['id']
            rnome = row[1] if not isinstance(row, dict) else row['nome']
            if normalizar_nome(rnome) == nome_norm:
                if cache is not None:
                    cache['nome'][nome_norm] = rid
                return rid

    # 3. Insere novo
    query = "INSERT INTO responsaveis (nome, cpf, telefone, grau_parentesco) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (nome_fmt, cpf_fmt, telefone, parentesco))
    novo_id = cursor.lastrowid
    if cache is not None:
        if nome_norm:
            cache['nome'][nome_norm] = novo_id
        if cpf_fmt:
            cache['cpf'][cpf_fmt] = novo_id
    return novo_id


def vincular_responsavel(cursor, aluno_id: int, responsavel_id: int):
    """Vincula responsável ao aluno"""
    cursor.execute("INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                  (responsavel_id, aluno_id))


def processar_responsaveis(cursor, dados: Dict, aluno_id: int, celular: str,
                           cache: Dict = None):
    """Processa responsáveis — usa cache para evitar duplicatas por nome ou CPF"""
    resp_tipo = dados.get('responsavel_tipo', '0')
    if dados.get('mae'):
        resp_id = inserir_responsavel(cursor, dados['mae'], dados.get('cpf_mae'),
                                      celular if resp_tipo == '0' else '', 'Mãe',
                                      dados.get('profissao_mae'), cache)
        vincular_responsavel(cursor, aluno_id, resp_id)
    if dados.get('pai'):
        resp_id = inserir_responsavel(cursor, dados['pai'], dados.get('cpf_pai'),
                                      celular if resp_tipo == '1' else '', 'Pai',
                                      dados.get('profissao_pai'), cache)
        vincular_responsavel(cursor, aluno_id, resp_id)
    if dados.get('outros_nome'):
        resp_id = inserir_responsavel(cursor, dados['outros_nome'], dados.get('outros_cpf'),
                                      celular if resp_tipo == '2' else '', 'Outro Responsável',
                                      dados.get('outros_profissao'), cache)
        vincular_responsavel(cursor, aluno_id, resp_id)


def importar_do_arquivo(arquivo_json: str, escola_padrao_id: int = None):
    """ETAPA 2: Importa do JSON para banco de dados"""
    conn = conectar_bd()
    if not conn:
        logger.error("Erro ao conectar BD")
        return
    
    cursor = conn.cursor()
    
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados_completos = json.load(f)
        
        total_importados = 0
        total_duplicados = 0
        total_erros = 0

        if not escola_padrao_id:
            escola_padrao_id = obter_escola_padrao(cursor)

        # Cache de responsáveis para evitar duplicatas por nome ou CPF
        cache_resp = _carregar_cache_responsaveis(cursor)
        
        logger.info(f"Escola padrão: {escola_padrao_id}")
        logger.info(f"Total no arquivo: {dados_completos.get('total_alunos', 0)}")
        
        for turma in dados_completos.get('turmas', []):
            logger.info(f"\n{'='*60}")
            logger.info(f"TURMA: {turma['nome']}")
            logger.info(f"{'='*60}")
            
            for idx, dados in enumerate(turma['alunos'], 1):
                logger.info(f"[{idx}] {dados['nome']}")
                
                if aluno_existe(cursor, dados['nome_normalizado']):
                    total_duplicados += 1
                    continue
                
                if not dados.get('data_nascimento'):
                    logger.error("  Sem data nascimento")
                    total_erros += 1
                    continue
                
                escola_id = escola_padrao_id
                if dados.get('inep_escola'):
                    escola = buscar_escola_por_inep(cursor, dados['inep_escola'])
                    if escola:
                        escola_id = escola
                
                try:
                    aluno_id = inserir_aluno(cursor, dados, escola_id)
                    logger.info(f"  ✅ Importado ID: {aluno_id}")
                    
                    if dados.get('celular') or dados.get('mae') or dados.get('pai'):
                        processar_responsaveis(cursor, dados, aluno_id, dados.get('celular', ''), cache_resp)
                    
                    conn.commit()
                    total_importados += 1
                    
                    if dados.get('descricao_transtorno') != 'Nenhum':
                        logger.info(f"  🏥 {dados['descricao_transtorno']}")
                except Exception as e:
                    logger.error(f"  ❌ Erro: {e}")
                    conn.rollback()
                    total_erros += 1
        
        logger.info(f"\n✅ Importados: {total_importados}")
        logger.info(f"⚠️  Duplicados: {total_duplicados}")
        logger.info(f"❌ Erros: {total_erros}")
        
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {arquivo_json}")
    except Exception as e:
        logger.error(f"Erro: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    print("="*60)
    print("IMPORTADOR GEDUC")
    print("="*60)
    print("1 - Extrair do GEDUC (salvar JSON)")
    print("2 - Importar JSON para BD")
    print("3 - Fazer tudo")
    print("-"*60)
    
    opcao = input("Opção: ").strip()
    
    if opcao not in ['1', '2', '3']:
        print("❌ Inválido")
        exit()
    
    if opcao in ['1', '3']:
        print("\n=== EXTRAÇÃO ===")
        usuario = input("Usuário GEDUC: ").strip()
        if not usuario:
            exit()
        from getpass import getpass
        senha = getpass("Senha: ").strip()
        if not senha:
            exit()
        arquivo = input("Arquivo JSON (Enter=alunos_geduc.json): ").strip() or 'alunos_geduc.json'
        turmas = input("IDs turmas (vírgula, Enter=todas): ").strip()
        turmas_lista = [t.strip() for t in turmas.split(',')] if turmas else None
        
        if input("\nContinuar extração? (S/N): ").upper() == 'S':
            extrair_alunos_geduc(usuario, senha, arquivo, turmas_lista)
        else:
            exit()
    
    if opcao in ['2', '3']:
        print("\n=== IMPORTAÇÃO ===")
        if opcao == '2':
            arquivo = input("Arquivo JSON (Enter=alunos_geduc.json): ").strip() or 'alunos_geduc.json'
        
        if not os.path.exists(arquivo):
            print(f"❌ Não encontrado: {arquivo}")
            exit()
        
        escola = input("ID escola (Enter=primeira): ").strip()
        escola_id = int(escola) if escola else None
        
        print(f"\nArquivo: {arquivo}")
        print(f"Verificação: Nome normalizado")
        print(f"Abreviações: TEA, TDAH, etc.")
        
        if input("\nContinuar importação? (S/N): ").upper() == 'S':
            importar_do_arquivo(arquivo, escola_id)
