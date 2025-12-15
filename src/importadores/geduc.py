"""
Script para automatizar a extração de notas do GEDUC
Faz login, navega pelas páginas e extrai todas as notas automaticamente
"""

from selenium import webdriver
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Tentar importar webdriver-manager (facilita instalação do ChromeDriver)
try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_DISPONIVEL = True
except ImportError:
    WEBDRIVER_MANAGER_DISPONIVEL = False
    logger.warning("⚠ webdriver-manager não instalado. Instale com: pip install webdriver-manager")
from bs4 import BeautifulSoup
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
import time
import os
import re
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import json


class AutomacaoGEDUC:
    """
    Classe para automatizar extração de notas do GEDUC
    """
    
    def __init__(self, headless=False):
        """
        Inicializa o navegador
        headless: Se True, executa sem abrir janela do navegador
        """
        # Tipo opcional: pode ser None até o navegador ser iniciado
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        self.url_base = "https://semed.geduc.com.br"
        self.dados_extraidos = []
        
    def iniciar_navegador(self):
        """
        Configura e inicia o navegador Chrome
        """
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Tentar diferentes métodos de inicialização
            driver_iniciado = False
            metodo_usado = ""
            
            # MÉTODO 1: Tentar usar ChromeDriver do PATH (mais rápido)
            if not driver_iniciado:
                try:
                    logger.info("→ Tentando usar ChromeDriver do sistema...")
                    self.driver = webdriver.Chrome(options=chrome_options)
                    driver_iniciado = True
                    metodo_usado = "ChromeDriver do sistema (PATH)"
                except Exception as e1:
                    logger.warning("  ✗ ChromeDriver do sistema não encontrado")
            
            # MÉTODO 2: Usar webdriver-manager com cache
            if not driver_iniciado and WEBDRIVER_MANAGER_DISPONIVEL:
                try:
                    logger.info("→ Tentando usar webdriver-manager (cache)...")
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver_iniciado = True
                    metodo_usado = "webdriver-manager (cache)"
                except Exception as e2:
                    logger.exception("  ✗ Erro com webdriver-manager: %s", e2)
                    
                    # Se erro foi de conexão, tentar cache offline
                    if "Could not reach host" in str(e2) or "offline" in str(e2).lower():
                        try:
                            logger.info("→ Tentando usar cache offline do webdriver-manager...")
                            # Forçar uso de cache existente
                            import webdriver_manager.chrome as wm_chrome
                            cache_path = os.path.join(os.path.expanduser("~"), ".wdm", "drivers", "chromedriver")
                            
                            if os.path.exists(cache_path):
                                # Procurar executável no cache
                                for root, dirs, files in os.walk(cache_path):
                                    for file in files:
                                        if file == "chromedriver.exe" or file == "chromedriver":
                                            driver_path = os.path.join(root, file)
                                            logger.info("  → Encontrado no cache: %s", driver_path)
                                            service = Service(driver_path)
                                            self.driver = webdriver.Chrome(service=service, options=chrome_options)
                                            driver_iniciado = True
                                            metodo_usado = "webdriver-manager (cache offline)"
                                            break
                                    if driver_iniciado:
                                        break
                        except Exception as e3:
                            logger.exception("  ✗ Cache offline não disponível: %s", e3)
            
            # MÉTODO 3: Procurar chromedriver.exe na pasta do script
            if not driver_iniciado:
                try:
                    logger.info("→ Procurando chromedriver.exe na pasta do script...")
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    local_chromedriver = os.path.join(script_dir, "chromedriver.exe")
                    
                    if os.path.exists(local_chromedriver):
                        logger.info("  → Encontrado: %s", local_chromedriver)
                        service = Service(local_chromedriver)
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        driver_iniciado = True
                        metodo_usado = "ChromeDriver local (pasta do script)"
                    else:
                        logger.warning("  ✗ Não encontrado em: %s", local_chromedriver)
                except Exception as e4:
                    logger.exception("  ✗ Erro ao usar ChromeDriver local: %s", e4)
            
            # Se nenhum método funcionou
            if not driver_iniciado:
                raise Exception("Nenhum método de inicialização funcionou")
            
            # Sucesso!
            assert self.driver is not None, "navegador não iniciado"
            self.driver.set_page_load_timeout(30)
            logger.info("✓ Navegador iniciado com sucesso usando: %s", metodo_usado)
            return True
            
        except Exception as e:
            logger.exception("✗ Erro ao iniciar navegador: %s", e)
            
            # Mensagem de erro personalizada
            mensagem_erro = "❌ Não foi possível iniciar o navegador Chrome.\n\n"
            mensagem_erro += "📝 SOLUÇÕES DISPONÍVEIS:\n\n"
            
            mensagem_erro += "1️⃣  SOLUÇÃO RÁPIDA (Recomendada):\n"
            mensagem_erro += "   • Baixe chromedriver.exe manualmente\n"
            mensagem_erro += "   • Site: https://googlechromelabs.github.io/chrome-for-testing/\n"
            mensagem_erro += f"   • Copie para: {os.path.dirname(os.path.abspath(__file__))}\n\n"
            
            mensagem_erro += "2️⃣  VERIFICAR CHROME:\n"
            mensagem_erro += "   • Certifique-se de ter Google Chrome instalado\n"
            mensagem_erro += "   • Atualize para a versão mais recente\n\n"
            
            mensagem_erro += "3️⃣  CONEXÃO DE INTERNET:\n"
            mensagem_erro += "   • Verifique sua conexão\n"
            mensagem_erro += "   • Desative proxy/firewall temporariamente\n\n"
            
            mensagem_erro += f"🔍 Erro técnico: {str(e)[:200]}"
            
            messagebox.showerror("Erro ao Iniciar Navegador", mensagem_erro)
            return False
    
    def fazer_login(self, usuario, senha, timeout_recaptcha=60):
        """
        Faz login no sistema GEDUC
        IMPORTANTE: Aguarda resolução manual do reCAPTCHA
        
        timeout_recaptcha: Tempo máximo (segundos) para aguardar resolução do reCAPTCHA
        """
        # Garantir que o navegador foi iniciado antes de usar o driver
        if self.driver is None:
            logger.error("✗ Erro: navegador não iniciado. Chame iniciar_navegador() antes de fazer login.")
            return False

        try:
            logger.info("→ Acessando página de login...")
            self.driver.get(f"{self.url_base}/index.php?class=LoginForm")
            
            # Aguardar carregamento da página
            wait = WebDriverWait(self.driver, 15)
            
            # Aguardar campo de usuário estar presente
            campo_usuario = wait.until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            
            # Preencher usuário
            campo_usuario.clear()
            campo_usuario.send_keys(usuario)
            logger.info("  ✓ Usuário preenchido: %s", usuario)
            
            # Preencher senha
            campo_senha = self.driver.find_element(By.NAME, "password")
            campo_senha.clear()
            campo_senha.send_keys(senha)
            logger.info("  ✓ Senha preenchida")
            
            # Verificar se há reCAPTCHA na página
            logger.info("\n%s", "="*60)
            logger.info("⚠️  ATENÇÃO: reCAPTCHA DETECTADO!")
            logger.info("%s", "="*60)
            logger.info("→ Por favor, resolva o reCAPTCHA manualmente no navegador")
            logger.info("→ Marque a caixa 'Não sou um robô'")
            logger.info("→ Você tem %s segundos para resolver", timeout_recaptcha)
            logger.info("→ Após resolver o reCAPTCHA, clique no botão de LOGIN")
            logger.info("→ Aguardando...")
            logger.info("%s\n", "="*60)
            
            # Aguardar usuário resolver o reCAPTCHA e fazer login manualmente
            # Monitora se a URL mudou (saiu da página de login)
            url_login = self.driver.current_url
            tempo_inicio = time.time()
            
            while True:
                time.sleep(2)  # Verifica a cada 2 segundos
                
                # Verificar se saiu da página de login (login bem-sucedido)
                if "LoginForm" not in self.driver.current_url:
                    logger.info("✓ Login realizado com sucesso!")
                    return True
                
                # Verificar timeout
                tempo_decorrido = time.time() - tempo_inicio
                if tempo_decorrido > timeout_recaptcha:
                    logger.error("✗ Timeout de %s s expirado", timeout_recaptcha)
                    logger.error("  O reCAPTCHA não foi resolvido a tempo")
                    return False
                
                # Mostrar progresso
                tempo_restante = int(timeout_recaptcha - tempo_decorrido)
                if tempo_restante % 10 == 0:  # Mostrar a cada 10 segundos
                    logger.info("  ⏳ Aguardando... (%s s restantes)", tempo_restante)
            
        except TimeoutException:
            logger.error("✗ Timeout ao carregar página de login")
            return False
        except Exception as e:
            logger.exception("✗ Erro durante login: %s", e)
            return False
    
    def acessar_registro_notas(self):
        """
        Navega até a página de registro de notas
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            logger.info("→ Navegando para registro de notas...")
            
            # URL da página de registro de notas
            self.driver.get(f"{self.url_base}/index.php?class=RegNotasForm")
            
            # Aguardar carregamento
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.NAME, "IDTURMA")))
            
            logger.info("✓ Página de registro de notas carregada")
            return True
            
        except Exception as e:
            logger.exception("✗ Erro ao acessar registro de notas: %s", e)
            return False
    
    def acessar_recuperacao_bimestral(self):
        """
        Navega até a página de recuperação bimestral
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            logger.info("→ Navegando para recuperação bimestral...")
            
            # URL da página de recuperação bimestral
            self.driver.get(f"{self.url_base}/index.php?class=RegNotasbimForm")
            
            # Aguardar carregamento
            wait = WebDriverWait(self.driver, 15)
            wait.until(EC.presence_of_element_located((By.NAME, "IDTURMA")))
            
            logger.info("✓ Página de recuperação bimestral carregada")
            return True
            
        except Exception as e:
            logger.exception("✗ Erro ao acessar recuperação bimestral: %s", e)
            return False
    
    def obter_opcoes_select(self, select_name):
        """
        Obtém todas as opções de um elemento select
        Retorna lista de dicionários com {'value': valor, 'text': texto}
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            select_element = Select(self.driver.find_element(By.NAME, select_name))
            opcoes = []
            
            for option in select_element.options:
                valor = option.get_attribute('value')
                texto = option.text.strip()
                
                # Pular opções vazias ou de instrução
                if valor and valor != '' and not texto.startswith('---'):
                    opcoes.append({
                        'value': valor,
                        'text': texto
                    })
            
            return opcoes
            
        except Exception as e:
            logger.exception("✗ Erro ao obter opções do select '%s': %s", select_name, e)
            return []
    
    def selecionar_opcao(self, select_name, valor):
        """
        Seleciona uma opção em um elemento select pelo valor
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            select_element = Select(self.driver.find_element(By.NAME, select_name))
            select_element.select_by_value(str(valor))
            time.sleep(0.5)  # Aguardar processamento
            return True
        except Exception as e:
            logger.exception("✗ Erro ao selecionar opção '%s' em '%s': %s", valor, select_name, e)
            return False
    
    def selecionar_bimestre(self, numero_bimestre):
        """
        Seleciona o bimestre pelos radio buttons
        numero_bimestre: 1, 2, 3 ou 4
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            # Buscar todos os radio buttons de avaliação
            radios = self.driver.find_elements(By.NAME, "IDAVALIACOES")
            
            for radio in radios:
                radio_id = radio.get_attribute('id')
                # Buscar label associada
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{radio_id}']")
                    texto_label = label.text.strip()
                    
                    # Verificar se contém o número do bimestre
                    if f"{numero_bimestre}º" in texto_label or f"{numero_bimestre}°" in texto_label:
                        # Clicar no radio button
                        self.driver.execute_script("arguments[0].click();", radio)
                        time.sleep(0.5)
                        return True
                except:
                    continue
            
            logger.warning("✗ Bimestre %sº não encontrado", numero_bimestre)
            return False
            
        except Exception as e:
            logger.exception("✗ Erro ao selecionar bimestre: %s", e)
            return False
    
    def clicar_exibir_alunos(self):
        """
        Clica no botão para exibir os alunos
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            # Buscar botão de exibir alunos
            botoes = self.driver.find_elements(By.TAG_NAME, "button")
            
            for botao in botoes:
                texto = botao.text.strip().upper()
                if "EXIBIR" in texto or "ALUNOS" in texto or "CARREGAR" in texto:
                    self.driver.execute_script("arguments[0].click();", botao)
                    time.sleep(2)  # Aguardar carregamento da tabela
                    return True
            
            # Tentar também por input type=button
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='button']")
            for input_btn in inputs:
                valor = input_btn.get_attribute('value')
                if valor and ("EXIBIR" in valor.upper() or "ALUNOS" in valor.upper()):
                    self.driver.execute_script("arguments[0].click();", input_btn)
                    time.sleep(2)
                    return True
            
            logger.warning("✗ Botão 'Exibir Alunos' não encontrado")
            return False
            
        except Exception as e:
            logger.exception("✗ Erro ao clicar em exibir alunos: %s", e)
            return False
    
    def extrair_notas_pagina_atual(self, turma_nome=None, disciplina_nome=None, bimestre_numero=None):
        """
        Extrai notas da página atual usando BeautifulSoup
        Retorna dicionário com turma, disciplina, bimestre e lista de alunos
        
        turma_nome: Nome da turma (se None, tenta extrair do HTML)
        disciplina_nome: Nome da disciplina (se None, tenta extrair do HTML)
        bimestre_numero: Número do bimestre (se None, tenta extrair do HTML)
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            # Obter HTML da página
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Usar parâmetros passados ou tentar extrair do HTML
            if turma_nome is None:
                turma = "Desconhecida"
                turma_select = soup.find('select', {'name': 'IDTURMA'})
                if turma_select:
                    turma_option = turma_select.find('option', {'selected': True})
                    if turma_option:
                        turma = turma_option.text.strip()
            else:
                turma = turma_nome
            
            if disciplina_nome is None:
                disciplina = "Desconhecida"
                disciplina_select = soup.find('select', {'name': 'IDTURMASDISP'})
                if disciplina_select:
                    disciplina_option = disciplina_select.find('option', {'selected': True})
                    if disciplina_option:
                        disciplina = disciplina_option.text.strip()
            else:
                disciplina = disciplina_nome
            
            if bimestre_numero is None:
                bimestre = "1º"
                bimestre_radios = soup.find_all('input', {'name': 'IDAVALIACOES'})
                for radio in bimestre_radios:
                    if radio.get('checked'):
                        radio_id = radio.get('id')
                        label = soup.find('label', {'for': radio_id})
                        if label:
                            texto_bimestre = label.text.strip()
                            match = re.search(r'(\d+)º', texto_bimestre)
                            if match:
                                bimestre = f"{match.group(1)}º"
            else:
                bimestre = f"{bimestre_numero}º"
            
            # Extrair alunos e notas da tabela
            alunos_notas = []
            tbody = soup.find('tbody', {'class': 'tdatagrid_body'})
            
            if tbody:
                rows = tbody.find_all('tr', {'class': ['tdatagrid_row_odd', 'tdatagrid_row_even']})
                
                for row in rows:
                    cells = row.find_all('td', {'class': 'tdatagrid_cell'})
                    
                    if len(cells) >= 2:
                        ordem_text = cells[0].text.strip()
                        nome_aluno = cells[1].text.strip()
                        
                        if ordem_text and nome_aluno and ordem_text.isdigit():
                            # Extrair notas
                            if len(cells) >= 3:
                                nota_inputs = cells[2].find_all('input', {'class': 'tfield'})
                                notas = []
                                
                                for input_nota in nota_inputs:
                                    valor_nota = input_nota.get('value', '')
                                    if valor_nota:
                                        try:
                                            nota_float = float(valor_nota)
                                            notas.append(nota_float)
                                        except ValueError:
                                            pass
                                
                                # Calcular média
                                if notas:
                                    media = sum(notas) / len(notas)
                                    nota_final = media * 10
                                else:
                                    nota_final = ''
                                    notas = []  # Lista vazia se não houver notas
                                
                                alunos_notas.append({
                                    'ordem': int(ordem_text),
                                    'nome': nome_aluno,
                                    'notas_individuais': notas,  # Guardar notas individuais
                                    'media': nota_final  # Média final (média × 10)
                                })
            
            # Log para depuração: listar nomes extraídos e checar presença de aluna específica
            try:
                nomes_extraidos = [a.get('nome', '').upper() for a in alunos_notas]
                logger.debug(f"[DEBUG_GEDUC] Alunos extraídos ({len(nomes_extraidos)}): {', '.join(nomes_extraidos[:20])}{'...' if len(nomes_extraidos)>20 else ''}")
                # Verificar presença de 'MARIA CECILYA' aproximada
                encontradas = [n for n in nomes_extraidos if 'MARIA' in n and ('CECIL' in n or 'CEC' in n or 'CECI' in n)]
                if encontradas:
                    logger.debug(f"[DEBUG_GEDUC] Possíveis ocorrências de Maria Cecilya encontradas: {encontradas}")
                else:
                    logger.debug("[DEBUG_GEDUC] Nenhuma ocorrência clara de 'Maria Cecilya' encontrada entre os nomes extraídos.")
            except Exception:
                logger.exception("Erro ao gerar debug dos nomes extraídos do GEDUC")

            return {
                'turma': turma,
                'disciplina': disciplina,
                'bimestre': bimestre,
                'alunos': alunos_notas,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.exception("✗ Erro ao extrair notas: %s", e)
            return None
    
    def extrair_recuperacao_pagina_atual(self):
        """
        Extrai dados de recuperação da página RegNotasbimForm
        
        Estrutura REAL da tabela (descoberta via debug 01/11/2025):
        - Coluna 0: Ordem
        - Coluna 1: Matrícula
        - Coluna 2: Alunos (NOME)
        - Coluna 3: (INPUT) Média Atual campo 1
        - Coluna 4: (INPUT) Média Atual campo 2
        - Coluna 5: (INPUT) Média Atual campo 3
        - Coluna 6: (INPUT) código
        - Coluna 7: (INPUT) valor
        - Coluna 8: Situação (texto "Aprovado"/"Reprovado")
        - Coluna 9: (INPUT) RECUPERAÇÃO ← COLUNA CORRETA!
        - Coluna 10: Média Gravada
        
        Returns:
            Lista de dicts: [{'nome': 'ALUNO', 'recuperacao': 7.0}, ...]
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            # Aguardar tabela carregar
            wait = WebDriverWait(self.driver, 10)
            tabela = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table, table.tdatagrid_table"))
            )
            
            # Buscar todas as linhas da tabela
            linhas = tabela.find_elements(By.TAG_NAME, "tr")
            
            dados = []
            
            # Processar linhas (pular cabeçalho)
            for idx, linha in enumerate(linhas):
                # Pular cabeçalho (primeira linha geralmente)
                if idx == 0:
                    continue
                
                try:
                    colunas = linha.find_elements(By.TAG_NAME, "td")
                    
                    # Verificar se tem colunas suficientes (precisa ter pelo menos 10 colunas)
                    if len(colunas) < 10:
                        continue
                    
                    # Estrutura REAL da tabela (descoberta via debug):
                    # [0] = Ordem
                    # [1] = Matrícula
                    # [2] = Alunos (nome)
                    # [3] = (INPUT) Média Atual campo 1
                    # [4] = (INPUT) Média Atual campo 2
                    # [5] = (INPUT) Média Atual campo 3
                    # [6] = (INPUT) código
                    # [7] = (INPUT) valor
                    # [8] = Situação (texto)
                    # [9] = (INPUT) Recuperação ← COLUNA CORRETA!
                    # [10] = Média Gravada
                    
                    # Extrair nome do aluno (coluna 2)
                    nome = colunas[2].text.strip()
                    
                    if not nome:
                        continue
                    
                    # Extrair recuperação (coluna 9 - CORRIGIDO!)
                    recuperacao = None
                    try:
                        # Tentar pegar de input na coluna 9
                        recup_input = colunas[9].find_element(By.TAG_NAME, "input")
                        recup_str = recup_input.get_attribute("value")
                    except:
                        # Se não for input, pegar texto da coluna 9
                        recup_str = colunas[9].text.strip()
                    
                    # Converter para float
                    if recup_str and recup_str != '':
                        try:
                            # Substituir vírgula por ponto
                            recup_str = recup_str.replace(',', '.')
                            recuperacao = float(recup_str)
                        except ValueError:
                            recuperacao = None
                    
                    # Adicionar aos dados (mesmo se recuperação for None)
                    dados.append({
                        'nome': nome,
                        'recuperacao': recuperacao
                    })
                
                except Exception as e:
                    # Erro em linha específica, continuar para próxima
                    continue
            
            logger.info("✓ Extraídos %d registros de recuperação", len(dados))
            return dados
            
        except Exception as e:
            logger.exception("✗ Erro ao extrair dados de recuperação: %s", e)
            return []
    
    def extrair_todas_notas(self, turmas_selecionadas=None, bimestres=[1, 2, 3, 4], diretorio_saida="notas_extraidas", callback_progresso=None):
        """
        Extrai todas as notas de todas as combinações de turma/disciplina/bimestre
        NOVO: Cria 1 arquivo Excel por TURMA/BIMESTRE com múltiplas planilhas (uma por disciplina)
        Salva IMEDIATAMENTE após processar cada turma/bimestre
        
        turmas_selecionadas: Lista de IDs de turmas (None = todas)
        bimestres: Lista de números de bimestres para extrair
        diretorio_saida: Diretório onde salvar os arquivos
        callback_progresso: Função para atualizar progresso (opcional)
        """
        try:
            assert self.driver is not None, "navegador não iniciado"
            logger.info("\n%s", "="*60)
            logger.info("INICIANDO EXTRAÇÃO AUTOMÁTICA DE NOTAS")
            logger.info("%s\n", "="*60)
            
            # Criar diretório de saída
            if not os.path.exists(diretorio_saida):
                os.makedirs(diretorio_saida)
                logger.info("✓ Diretório criado: %s", diretorio_saida)
            
            # Acessar página de registro de notas
            if not self.acessar_registro_notas():
                return False
            
            # Obter todas as turmas disponíveis
            logger.info("→ Obtendo lista de turmas...")
            turmas = self.obter_opcoes_select('IDTURMA')
            
            if not turmas:
                logger.error("✗ Nenhuma turma encontrada")
                return False
            
            logger.info("  ✓ %d turmas encontradas", len(turmas))
            
            # Filtrar turmas se especificado
            if turmas_selecionadas:
                turmas = [t for t in turmas if t['value'] in turmas_selecionadas]
            
            total_arquivos_criados = 0
            total_planilhas_criadas = 0
            
            # Iterar por cada turma
            for idx_turma, turma in enumerate(turmas, 1):
                logger.info("\n[%d/%d] TURMA: %s", idx_turma, len(turmas), turma['text'])
                logger.info("%s", "-" * 60)
                
                # Selecionar turma
                if not self.selecionar_opcao('IDTURMA', turma['value']):
                    continue
                
                time.sleep(1)  # Aguardar carregamento de disciplinas
                
                # Obter disciplinas da turma
                disciplinas = self.obter_opcoes_select('IDTURMASDISP')
                
                if not disciplinas:
                    logger.warning("  ⚠ Nenhuma disciplina encontrada para esta turma")
                    continue
                
                logger.info("  → %d disciplinas encontradas", len(disciplinas))
                
                # Processar cada bimestre para esta turma
                for bimestre in bimestres:
                    logger.info("\n  → PROCESSANDO BIMESTRE %sº", bimestre)
                    
                    # Dicionário para armazenar dados de todas as disciplinas deste bimestre
                    dados_turma_bimestre = {
                        'turma': turma['text'],
                        'bimestre': bimestre,
                        'disciplinas': []
                    }
                    
                    # Iterar por cada disciplina
                    for idx_disc, disciplina in enumerate(disciplinas, 1):
                        logger.info("    [%d/%d] %s", idx_disc, len(disciplinas), disciplina['text'])
                        
                        # Selecionar disciplina
                        if not self.selecionar_opcao('IDTURMASDISP', disciplina['value']):
                            logger.error("✗ Erro ao selecionar")
                            continue
                        
                        time.sleep(0.5)
                        
                        # Selecionar bimestre
                        if not self.selecionar_bimestre(bimestre):
                            logger.error("✗ Erro ao selecionar bimestre")
                            continue
                        
                        # Clicar em exibir alunos
                        if not self.clicar_exibir_alunos():
                            logger.error("✗ Erro ao carregar alunos")
                            continue
                        
                        # Extrair notas (passando nome da turma, disciplina e bimestre)
                        dados = self.extrair_notas_pagina_atual(
                            turma_nome=turma['text'],
                            disciplina_nome=disciplina['text'],
                            bimestre_numero=bimestre
                        )
                        
                        if dados and dados['alunos']:
                            dados_turma_bimestre['disciplinas'].append(dados)
                            logger.info("✓ %d alunos", len(dados['alunos']))
                        else:
                            logger.warning("⚠ Sem notas")
                        
                        # Atualizar callback de progresso
                        if callback_progresso:
                            callback_progresso(total_planilhas_criadas + 1, len(turmas) * len(bimestres) * len(disciplinas))
                    
                    # SALVAR IMEDIATAMENTE após processar todas as disciplinas deste bimestre
                    if dados_turma_bimestre['disciplinas']:
                        arquivo_criado = self._salvar_turma_bimestre(dados_turma_bimestre, diretorio_saida)
                        if arquivo_criado:
                            total_arquivos_criados += 1
                            total_planilhas_criadas += len(dados_turma_bimestre['disciplinas'])
                            logger.info("\n  ✓ ARQUIVO SALVO: %s", os.path.basename(arquivo_criado))
                            logger.info("    → %d planilhas (disciplinas)", len(dados_turma_bimestre['disciplinas']))
                    else:
                        logger.warning("\n  ⚠ Nenhuma nota encontrada para o %sº bimestre", bimestre)
            
            logger.info("\n%s", "="*60)
            logger.info("EXTRAÇÃO CONCLUÍDA!")
            logger.info("Total de arquivos Excel criados: %d", total_arquivos_criados)
            logger.info("Total de planilhas (disciplinas): %d", total_planilhas_criadas)
            logger.info("Localização: %s", os.path.abspath(diretorio_saida))
            logger.info("%s\n", "="*60)
            
            return True
            
        except Exception as e:
            logger.exception("✗ Erro durante extração: %s", e)
            return False
    
    def _salvar_turma_bimestre(self, dados_turma_bimestre, diretorio_saida):
        """
        Salva um arquivo Excel com múltiplas planilhas (uma por disciplina)
        para uma turma/bimestre específico
        
        dados_turma_bimestre: {
            'turma': 'Nome da turma',
            'bimestre': número do bimestre,
            'disciplinas': [lista de dados de disciplinas]
        }
        """
        try:
            turma = dados_turma_bimestre['turma']
            bimestre = dados_turma_bimestre['bimestre']
            disciplinas = dados_turma_bimestre['disciplinas']
            
            if not disciplinas:
                return None
            
            # Limpar nome da turma para usar no arquivo
            turma_limpa = re.sub(r'[^\w\s-]', '', turma).strip().replace(' ', '_')
            
            # Nome do arquivo: Notas_TURMA_Xbim.xlsx
            nome_arquivo = f"Notas_{turma_limpa}_{bimestre}bim.xlsx"
            caminho_arquivo = os.path.join(diretorio_saida, nome_arquivo)
            
            # Criar workbook
            wb = openpyxl.Workbook()
            
            # Criar uma planilha para cada disciplina
            for idx, dados_disciplina in enumerate(disciplinas):
                # Nome da planilha (limitado a 31 caracteres do Excel)
                nome_disciplina = dados_disciplina['disciplina'][:31]
                
                # Criar planilha
                if idx == 0:
                    # Renomear a planilha ativa padrão
                    ws = wb.active
                    assert ws is not None, "Planilha padrão não encontrada"
                    ws.title = nome_disciplina
                else:
                    # Criar nova planilha
                    ws = wb.create_sheet(title=nome_disciplina)
                    assert ws is not None, "Falha ao criar nova planilha"
                
                # Preencher planilha com dados da disciplina
                self._preencher_planilha(ws, dados_disciplina)
            
            # Salvar arquivo
            wb.save(caminho_arquivo)
            return caminho_arquivo
            
        except Exception as e:
            logger.exception("\n  ✗ Erro ao salvar arquivo: %s", e)
            return None
    
    def _preencher_planilha(self, ws, dados):
        """
        Preenche uma planilha do Excel com os dados de uma disciplina
        Agora inclui colunas para cada nota individual + coluna de média
        """
        try:
            # Estilos
            header_font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
            header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            header_alignment = Alignment(horizontal='center', vertical='center')
            
            cell_font = Font(name='Arial', size=10)
            cell_alignment = Alignment(horizontal='center', vertical='center')
            cell_alignment_left = Alignment(horizontal='left', vertical='center')
            
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # Informações no topo
            ws['A1'] = f"Turma: {dados['turma']}"
            ws['A2'] = f"Disciplina: {dados['disciplina']}"
            ws['A3'] = f"Bimestre: {dados['bimestre']}"
            
            ws['A1'].font = Font(name='Arial', size=12, bold=True)
            ws['A2'].font = Font(name='Arial', size=12, bold=True)
            ws['A3'].font = Font(name='Arial', size=12, bold=True)
            
            # Descobrir quantas notas individuais existem (máximo entre todos os alunos)
            max_notas = 0
            for aluno in dados['alunos']:
                num_notas = len(aluno.get('notas_individuais', []))
                if num_notas > max_notas:
                    max_notas = num_notas
            
            # Cabeçalho da tabela (linha 5)
            ws['A5'] = 'Nº'
            ws['B5'] = 'Nome do Aluno'
            
            # Criar colunas para cada nota individual
            col_letra = 'C'
            for i in range(1, max_notas + 1):
                col = chr(ord('C') + i - 1)
                ws[f'{col}5'] = f'Nota {i}'
                col_letra = col
            
            # Coluna da média (depois das notas individuais)
            col_media = chr(ord(col_letra) + 1)
            ws[f'{col_media}5'] = 'Média'
            
            # Aplicar estilo ao cabeçalho
            for col_idx in range(ord('A'), ord(col_media) + 1):
                col = chr(col_idx)
                cell = ws[f'{col}5']
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = thin_border
            
            # Ajustar largura das colunas
            ws.column_dimensions['A'].width = 6
            ws.column_dimensions['B'].width = 45
            for i in range(max_notas):
                col = chr(ord('C') + i)
                ws.column_dimensions[col].width = 10
            ws.column_dimensions[col_media].width = 12
            
            # Dados dos alunos (começando na linha 6)
            row = 6
            for aluno in dados['alunos']:
                # Número e nome
                ws[f'A{row}'] = aluno['ordem']
                ws[f'B{row}'] = aluno['nome']
                
                # Notas individuais
                notas_individuais = aluno.get('notas_individuais', [])
                for i, nota in enumerate(notas_individuais):
                    col = chr(ord('C') + i)
                    ws[f'{col}{row}'] = round(nota, 2)
                    ws[f'{col}{row}'].alignment = cell_alignment
                    ws[f'{col}{row}'].font = cell_font
                    ws[f'{col}{row}'].border = thin_border
                
                # Preencher colunas vazias se este aluno tiver menos notas que o máximo
                for i in range(len(notas_individuais), max_notas):
                    col = chr(ord('C') + i)
                    ws[f'{col}{row}'].alignment = cell_alignment
                    ws[f'{col}{row}'].font = cell_font
                    ws[f'{col}{row}'].border = thin_border
                
                # Média
                media = aluno.get('media', '')
                if media != '':
                    ws[f'{col_media}{row}'] = round(media, 2)
                
                # Aplicar estilo às células de número, nome e média
                ws[f'A{row}'].alignment = cell_alignment
                ws[f'B{row}'].alignment = cell_alignment_left
                ws[f'{col_media}{row}'].alignment = cell_alignment
                
                for col_idx in range(ord('A'), ord(col_media) + 1):
                    col = chr(col_idx)
                    cell = ws[f'{col}{row}']
                    cell.font = cell_font
                    cell.border = thin_border
                
                row += 1
            
        except Exception as e:
            logger.exception("✗ Erro ao preencher planilha: %s", e)
    
    def salvar_dados_excel(self, diretorio_saida="notas_extraidas"):
        """
        DEPRECATED: Use extrair_todas_notas() que já salva automaticamente
        Mantido para compatibilidade com código antigo
        """
        logger.warning("⚠️ Aviso: Os arquivos já foram salvos automaticamente durante a extração")
        return []
    

    
    def fechar(self):
        """
        Fecha o navegador
        """
        if self.driver:
            self.driver.quit()
            logger.info("✓ Navegador fechado")


def interface_automacao():
    """
    Interface gráfica para automação de extração de notas
    """
    root = tk.Tk()
    root.title("Automação de Extração de Notas - GEDUC")
    root.geometry("700x600")
    root.configure(bg="#F5F5F5")
    
    # Centralizar janela
    root.update_idletasks()
    width = 700
    height = 600
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Cores
    co0 = "#F5F5F5"
    co1 = "#003A70"
    co2 = "#77B341"
    co4 = "#4A86E8"
    
    # Variáveis
    usuario_var = tk.StringVar()
    senha_var = tk.StringVar()
    headless_var = tk.BooleanVar(value=False)
    timeout_var = tk.IntVar(value=120)  # 2 minutos por padrão
    bim1_var = tk.BooleanVar(value=True)
    bim2_var = tk.BooleanVar(value=True)
    bim3_var = tk.BooleanVar(value=True)
    bim4_var = tk.BooleanVar(value=True)
    
    # Frame principal
    frame_principal = tk.Frame(root, bg=co0)
    frame_principal.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
    
    # Título
    titulo = tk.Label(
        frame_principal,
        text="Automação de Extração de Notas GEDUC",
        font=("Arial", 16, "bold"),
        bg=co0,
        fg=co1
    )
    titulo.pack(pady=(0, 10))
    
    # Aviso sobre reCAPTCHA
    aviso_recaptcha = tk.Label(
        frame_principal,
        text="⚠️ IMPORTANTE: Você precisará resolver o reCAPTCHA manualmente no navegador",
        font=("Arial", 9, "italic"),
        bg=co0,
        fg="#E65100"
    )
    aviso_recaptcha.pack(pady=(0, 15))
    
    # Credenciais
    frame_credenciais = tk.LabelFrame(
        frame_principal,
        text="Credenciais de Acesso",
        font=("Arial", 11, "bold"),
        bg=co0,
        fg=co1,
        padx=15,
        pady=10
    )
    frame_credenciais.pack(fill=tk.X, pady=10)
    
    # Usuário
    tk.Label(frame_credenciais, text="Usuário:", font=("Arial", 10), bg=co0).grid(row=0, column=0, sticky="w", pady=5)
    entry_usuario = tk.Entry(frame_credenciais, textvariable=usuario_var, font=("Arial", 10), width=40)
    entry_usuario.grid(row=0, column=1, pady=5, padx=(10, 0))
    
    # Senha
    tk.Label(frame_credenciais, text="Senha:", font=("Arial", 10), bg=co0).grid(row=1, column=0, sticky="w", pady=5)
    entry_senha = tk.Entry(frame_credenciais, textvariable=senha_var, font=("Arial", 10), width=40, show="*")
    entry_senha.grid(row=1, column=1, pady=5, padx=(10, 0))
    
    # Opções
    frame_opcoes = tk.LabelFrame(
        frame_principal,
        text="Opções de Extração",
        font=("Arial", 11, "bold"),
        bg=co0,
        fg=co1,
        padx=15,
        pady=10
    )
    frame_opcoes.pack(fill=tk.X, pady=10)
    
    # Bimestres
    tk.Label(frame_opcoes, text="Bimestres a extrair:", font=("Arial", 10, "bold"), bg=co0).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 5))
    
    tk.Checkbutton(frame_opcoes, text="1º Bimestre", variable=bim1_var, font=("Arial", 9), bg=co0).grid(row=1, column=0, sticky="w", padx=(20, 0))
    tk.Checkbutton(frame_opcoes, text="2º Bimestre", variable=bim2_var, font=("Arial", 9), bg=co0).grid(row=1, column=1, sticky="w")
    tk.Checkbutton(frame_opcoes, text="3º Bimestre", variable=bim3_var, font=("Arial", 9), bg=co0).grid(row=1, column=2, sticky="w")
    tk.Checkbutton(frame_opcoes, text="4º Bimestre", variable=bim4_var, font=("Arial", 9), bg=co0).grid(row=1, column=3, sticky="w")
    
    # Modo headless
    aviso_headless = tk.Label(
        frame_opcoes,
        text="⚠️ Não recomendado: você precisa ver o reCAPTCHA",
        font=("Arial", 8, "italic"),
        bg=co0,
        fg="#666666"
    )
    aviso_headless.grid(row=3, column=0, columnspan=4, sticky="w", pady=(0, 0), padx=(20, 0))
    
    # Timeout do reCAPTCHA
    tk.Label(
        frame_opcoes,
        text="Tempo para resolver reCAPTCHA (segundos):",
        font=("Arial", 9),
        bg=co0
    ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 5))
    
    timeout_spinbox = tk.Spinbox(
        frame_opcoes,
        from_=30,
        to=300,
        textvariable=timeout_var,
        font=("Arial", 9),
        width=10
    )
    timeout_spinbox.grid(row=4, column=2, sticky="w", pady=(10, 5))
    
    tk.Checkbutton(
        frame_opcoes,
        text="Modo silencioso (sem abrir navegador)",
        variable=headless_var,
        font=("Arial", 9),
        bg=co0
    ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))
    
    # Log de progresso
    frame_log = tk.LabelFrame(
        frame_principal,
        text="Progresso",
        font=("Arial", 11, "bold"),
        bg=co0,
        fg=co1,
        padx=10,
        pady=10
    )
    frame_log.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # Barra de progresso
    progress_bar = ttk.Progressbar(frame_log, mode='indeterminate')
    progress_bar.pack(fill=tk.X, pady=(0, 10))
    
    # Texto de log
    text_log = tk.Text(frame_log, height=10, font=("Consolas", 9), bg="white", fg="black")
    text_log.pack(fill=tk.BOTH, expand=True)
    
    scrollbar = tk.Scrollbar(frame_log, command=text_log.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_log.config(yscrollcommand=scrollbar.set)
    
    def adicionar_log(mensagem):
        """Adiciona mensagem ao log"""
        try:
            # Agendar atualização no main thread via after para garantir thread-safety
            try:
                text_log.after(0, lambda m=mensagem: (text_log.insert(tk.END, f"{m}\n"), text_log.see(tk.END)))
            except Exception:
                # Fallback: tentar inserir diretamente (último recurso)
                text_log.insert(tk.END, f"{mensagem}\n")
                text_log.see(tk.END)
        except Exception:
            # Silenciar erros de log para não interromper a automação
            pass
    
    def iniciar_extracao():
        """Inicia o processo de extração"""
        usuario = usuario_var.get().strip()
        senha = senha_var.get().strip()
        
        if not usuario or not senha:
            messagebox.showerror("Erro", "Preencha usuário e senha!", parent=root)
            return
        
        # Obter bimestres selecionados
        bimestres = []
        if bim1_var.get(): bimestres.append(1)
        if bim2_var.get(): bimestres.append(2)
        if bim3_var.get(): bimestres.append(3)
        if bim4_var.get(): bimestres.append(4)
        
        if not bimestres:
            messagebox.showerror("Erro", "Selecione pelo menos um bimestre!", parent=root)
            return
        
        # Desabilitar botão
        btn_iniciar.config(state=tk.DISABLED)
        progress_bar.start()
        text_log.delete(1.0, tk.END)
        
        # Executar em thread separada
        import threading
        
        def executar():
            automacao = None
            try:
                adicionar_log("="*60)
                adicionar_log("INICIANDO AUTOMAÇÃO DE EXTRAÇÃO DE NOTAS")
                adicionar_log("="*60)
                
                # Criar instância
                automacao = AutomacaoGEDUC(headless=headless_var.get())
                
                # Iniciar navegador
                adicionar_log("\n→ Iniciando navegador...")
                if not automacao.iniciar_navegador():
                    adicionar_log("✗ Erro ao iniciar navegador")
                    return
                adicionar_log("✓ Navegador iniciado")
                
                # Fazer login
                adicionar_log("\n→ Fazendo login no GEDUC...")
                adicionar_log("⚠️  ATENÇÃO: Você precisará resolver o reCAPTCHA manualmente!")
                adicionar_log("   Marque a caixa 'Não sou um robô' no navegador")
                adicionar_log("   Depois clique no botão LOGIN")
                adicionar_log("")
                
                timeout_recaptcha = timeout_var.get()
                if not automacao.fazer_login(usuario, senha, timeout_recaptcha=timeout_recaptcha):
                    adicionar_log("✗ Login falhou - verifique usuário e senha")
                    adicionar_log("   Ou o tempo para resolver o reCAPTCHA expirou")
                    return
                adicionar_log("✓ Login realizado com sucesso")
                
                # Extrair notas
                adicionar_log(f"\n→ Extraindo notas dos bimestres: {', '.join([f'{b}º' for b in bimestres])}")
                adicionar_log("   (Os arquivos serão salvos automaticamente após cada turma/bimestre)")
                adicionar_log("   (Este processo pode levar alguns minutos...)\n")
                
                def callback_progresso(processadas, total):
                    adicionar_log(f"   Progresso: {processadas}/{total} planilhas processadas")
                
                if not automacao.extrair_todas_notas(
                    bimestres=bimestres, 
                    diretorio_saida="notas_extraidas",
                    callback_progresso=callback_progresso
                ):
                    adicionar_log("✗ Erro durante extração")
                    return
                
                # Mensagem final
                adicionar_log("\n" + "="*60)
                adicionar_log("EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
                adicionar_log(f"Arquivos salvos em: {os.path.abspath('notas_extraidas')}")
                adicionar_log("="*60)
                
                messagebox.showinfo(
                    "Sucesso",
                    f"Extração concluída!\n\n"
                    f"Os arquivos Excel foram salvos em:\n"
                    f"notas_extraidas/\n\n"
                    f"Formato: 1 arquivo por turma/bimestre\n"
                    f"Cada arquivo contém múltiplas planilhas (uma por disciplina)",
                    parent=root
                )
                
            except Exception as e:
                adicionar_log(f"\n✗ ERRO: {e}")
                import traceback
                adicionar_log(traceback.format_exc())
                messagebox.showerror("Erro", f"Erro durante extração:\n{e}", parent=root)
            
            finally:
                if automacao:
                    adicionar_log("\n→ Fechando navegador...")
                    automacao.fechar()
                
                progress_bar.stop()
                btn_iniciar.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=executar, daemon=True)
        thread.start()
    
    # Botão iniciar
    btn_iniciar = tk.Button(
        frame_principal,
        text="INICIAR EXTRAÇÃO AUTOMÁTICA",
        command=iniciar_extracao,
        bg=co2,
        fg="white",
        font=("Arial", 12, "bold"),
        relief=tk.RAISED,
        cursor="hand2",
        height=2
    )
    btn_iniciar.pack(pady=10, fill=tk.X)
    
    root.mainloop()


if __name__ == "__main__":
    interface_automacao()
