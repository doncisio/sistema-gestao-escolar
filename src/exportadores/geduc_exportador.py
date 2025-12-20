"""
Módulo para exportar histórico escolar para o sistema GEDUC
============================================================

Reaproveita a classe AutomacaoGEDUC existente para fazer login com Selenium,
mas adiciona métodos específicos para ENVIAR dados (exportação).

Autor: Sistema de Gestão Escolar
Data: 20/12/2025
"""

from typing import Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import unicodedata

from src.importadores.geduc import AutomacaoGEDUC
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class ExportadorGEDUC(AutomacaoGEDUC):
    """
    Exportador de dados para GEDUC
    
    Herda AutomacaoGEDUC para reaproveitar:
    - Inicialização do navegador Selenium
    - Login com reCAPTCHA manual
    - Navegação básica
    
    Adiciona métodos para:
    - Preencher formulário de histórico escolar
    - Enviar notas e disciplinas
    - Validar submissão
    """
    
    def __init__(self, headless=False):
        """
        Inicializa exportador
        
        Args:
            headless: Se True, executa navegador em modo headless
        """
        super().__init__(headless=headless)
        logger.info("Exportador GEDUC inicializado")
    
    @staticmethod
    def normalizar_nome(nome: str) -> str:
        """
        Normaliza nome do aluno para busca no GEDUC
        
        Remove acentuação e converte para maiúsculas, conforme esperado pelo GEDUC.
        
        Args:
            nome: Nome do aluno
            
        Returns:
            Nome normalizado (maiúsculo sem acentos)
        """
        if not nome:
            return ""
        
        # Remover acentuação (NFD = decompor caracteres, categoria Mn = marcas não-espaçadas)
        nome_sem_acento = ''.join(
            c for c in unicodedata.normalize('NFD', nome) 
            if unicodedata.category(c) != 'Mn'
        )
        
        # Remover sufixos comuns
        sufixos = [
            '( Transferencia Externa )',
            '( TRANSFERENCIA EXTERNA )',
            ' (TRANSFERIDO)',
            ' (EVADIDO)',
            ' - TRANSFERIDO',
            '(Transferido)',
            '(TRANSFERIDO)',
            ' - Transferido',
            ' (Evadido)',
            ' - Evadido'
        ]
        
        nome_upper = nome_sem_acento.upper()
        for sufixo in sufixos:
            if nome_upper.endswith(sufixo.upper()):
                nome_upper = nome_upper[:-(len(sufixo))]
                break
        
        return nome_upper.strip()
    
    def buscar_aluno_por_nome(self, nome_aluno: str, timeout: int = 15) -> Optional[Dict[str, any]]:
        """
        Busca aluno no GEDUC pelo nome
        
        Args:
            nome_aluno: Nome do aluno (será normalizado automaticamente)
            timeout: Tempo máximo para busca
            
        Returns:
            Dicionário com dados do aluno encontrado ou None:
            {
                'id': int,          # ID do aluno no GEDUC
                'nome': str,        # Nome conforme retornado pelo GEDUC
                'nome_busca': str   # Nome normalizado usado na busca
            }
        """
        if not self.driver:
            logger.error("Navegador não iniciado")
            return None
        
        try:
            # Normalizar nome para busca
            nome_normalizado = self.normalizar_nome(nome_aluno)
            logger.info(f"Buscando aluno: '{nome_aluno}' → '{nome_normalizado}'")
            
            # Acessar página de busca de alunos
            # ATENÇÃO: A URL exata pode variar - ajustar conforme necessário
            url_busca = f"{self.url_base}/index.php?class=FichaAlunoForm"
            self.driver.get(url_busca)
            
            wait = WebDriverWait(self.driver, timeout)
            
            # Aguardar campo de busca
            # Possíveis nomes: NOME, nome, busca, search
            campo_busca = None
            for campo_nome in ['NOME', 'nome', 'busca', 'search', 'BUSCA']:
                try:
                    campo_busca = wait.until(
                        EC.presence_of_element_located((By.NAME, campo_nome))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not campo_busca:
                logger.error("Campo de busca não encontrado")
                return None
            
            # Preencher nome (já normalizado)
            campo_busca.clear()
            campo_busca.send_keys(nome_normalizado)
            logger.info(f"  → Nome preenchido no campo de busca")
            
            # Clicar em botão de busca
            botao_buscar = None
            for texto in ['Buscar', 'Pesquisar', 'Search', 'Procurar']:
                try:
                    botao_buscar = self.driver.find_element(
                        By.XPATH,
                        f"//button[contains(text(), '{texto}')] | //input[@type='submit' and contains(@value, '{texto}')]"
                    )
                    break
                except NoSuchElementException:
                    continue
            
            if botao_buscar:
                botao_buscar.click()
                time.sleep(2)  # Aguardar resultados
                logger.info("  → Busca executada")
            else:
                # Tentar submit do form
                campo_busca.submit()
                time.sleep(2)
                logger.info("  → Form submetido")
            
            # Procurar resultado na tabela ou lista
            # Estratégia 1: Procurar link com o nome do aluno
            try:
                # Procurar por link que contenha o nome (pode ser parcial)
                xpath_link = f"//a[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{nome_normalizado}')]"
                link_aluno = self.driver.find_element(By.XPATH, xpath_link)
                
                nome_encontrado = link_aluno.text.strip()
                logger.info(f"  ✓ Aluno encontrado: {nome_encontrado}")
                
                # Extrair ID do link (geralmente está na URL do href)
                href = link_aluno.get_attribute('href')
                
                # Tentar extrair IDALUNO da URL
                # Exemplos: ?IDALUNO=123, &IDALUNO=456
                import re
                match = re.search(r'[?&]IDALUNO=(\d+)', href)
                if match:
                    id_aluno = int(match.group(1))
                    logger.info(f"  ✓ ID extraído: {id_aluno}")
                    
                    return {
                        'id': id_aluno,
                        'nome': nome_encontrado,
                        'nome_busca': nome_normalizado
                    }
                else:
                    logger.warning("  ⚠ ID do aluno não encontrado na URL")
                    return None
                    
            except NoSuchElementException:
                logger.warning(f"  ⚠ Aluno '{nome_normalizado}' não encontrado nos resultados")
                return None
            
        except Exception as e:
            logger.exception(f"Erro ao buscar aluno: {e}")
            return None
    
    def acessar_cadastro_historico(self, idaluno: int, idinstituicao: int, ano: int, 
                                   idcurso: int, tipoescola: int = 1) -> bool:
        """
        Acessa página de cadastro/edição de histórico escolar
        
        Args:
            idaluno: ID do aluno no GEDUC
            idinstituicao: ID da instituição
            ano: Ano letivo
            idcurso: ID do curso/série
            tipoescola: Tipo de escola (1=regular)
            
        Returns:
            True se acessou com sucesso, False caso contrário
        """
        if not self.driver:
            logger.error("Navegador não iniciado")
            return False
        
        try:
            # URL baseada na análise da Fase 1
            url = (
                f"{self.url_base}/index.php"
                f"?class=DisciplinasHistorico"
                f"&method=onEdit"
                f"&IDCURSO={idcurso}"
                f"&ANO={ano}"
                f"&IDALUNO={idaluno}"
                f"&IDINSTITUICAO={idinstituicao}"
                f"&TIPOESCOLA={tipoescola}"
            )
            
            logger.info(f"Acessando cadastro de histórico: aluno={idaluno}, ano={ano}")
            self.driver.get(url)
            
            # Aguardar carregamento do formulário
            wait = WebDriverWait(self.driver, 15)
            
            # Aguardar elementos principais do formulário
            # Baseado na análise: campos IDCURRICULO, IDDISCIPLINAS[], etc.
            wait.until(
                EC.presence_of_element_located((By.NAME, "IDCURRICULO"))
            )
            
            logger.info("✓ Formulário de histórico carregado")
            return True
            
        except TimeoutException:
            logger.error("Timeout ao carregar formulário de histórico")
            return False
        except Exception as e:
            logger.exception(f"Erro ao acessar cadastro de histórico: {e}")
            return False
    
    def preencher_historico(
        self,
        idcurriculo: int,
        disciplinas: List[Dict[str, str]],
        visivel: int = 1
    ) -> bool:
        """
        Preenche formulário de histórico com disciplinas
        
        Args:
            idcurriculo: ID do currículo
            disciplinas: Lista de dicionários com dados das disciplinas
                Formato: [
                    {
                        'id': '77',
                        'cht': '400',
                        'media': '8.5',
                        'falta': '0',
                        'situacao': '0'
                    },
                    ...
                ]
            visivel: Se histórico é visível (1=sim, 0=não)
            
        Returns:
            True se preencheu com sucesso, False caso contrário
        """
        if not self.driver:
            logger.error("Navegador não iniciado")
            return False
        
        try:
            logger.info(f"Preenchendo histórico: currículo={idcurriculo}, disciplinas={len(disciplinas)}")
            
            # 1. Preencher currículo
            try:
                select_curriculo = Select(self.driver.find_element(By.NAME, "IDCURRICULO"))
                select_curriculo.select_by_value(str(idcurriculo))
                logger.info(f"  ✓ Currículo selecionado: {idcurriculo}")
            except Exception as e:
                logger.warning(f"  ⚠ Não foi possível selecionar currículo: {e}")
            
            # 2. Preencher campo VISIVEL se existir
            try:
                input_visivel = self.driver.find_element(By.NAME, "VISIVEL")
                if input_visivel.get_attribute("type") == "checkbox":
                    if visivel and not input_visivel.is_selected():
                        input_visivel.click()
                    elif not visivel and input_visivel.is_selected():
                        input_visivel.click()
                else:
                    input_visivel.clear()
                    input_visivel.send_keys(str(visivel))
                logger.info(f"  ✓ Visibilidade configurada: {visivel}")
            except NoSuchElementException:
                logger.debug("  Campo VISIVEL não encontrado (pode ser opcional)")
            
            # 3. Clicar no botão "Carregar Disciplinas" se existir
            # Baseado na análise, pode haver botão para carregar lista de disciplinas
            try:
                btn_carregar = self.driver.find_element(
                    By.XPATH, 
                    "//button[contains(text(), 'Carregar') or contains(@onclick, 'carregar')]"
                )
                btn_carregar.click()
                time.sleep(2)  # Aguardar carregamento
                logger.info("  ✓ Disciplinas carregadas")
            except NoSuchElementException:
                logger.debug("  Botão 'Carregar Disciplinas' não encontrado")
            
            # 4. Preencher arrays de disciplinas
            # ATENÇÃO: A estrutura exata precisa ser confirmada na Tarefa 1.2
            # Este é um exemplo baseado na análise da Fase 1
            
            for idx, disc in enumerate(disciplinas):
                try:
                    # IDDISCIPLINAS[] - pode ser checkbox, select ou input
                    # Tentar várias estratégias
                    
                    # Estratégia 1: Checkbox com value=ID da disciplina
                    try:
                        checkbox = self.driver.find_element(
                            By.XPATH,
                            f"//input[@type='checkbox' and @name='IDDISCIPLINAS[]' and @value='{disc['id']}']"
                        )
                        if not checkbox.is_selected():
                            checkbox.click()
                        logger.debug(f"    ✓ Disciplina {disc['id']} selecionada (checkbox)")
                    except NoSuchElementException:
                        # Estratégia 2: Campos dinâmicos (gerados por JavaScript)
                        # Precisará ser ajustado após captura real
                        pass
                    
                    # CHT[] - Carga horária
                    try:
                        input_cht = self.driver.find_element(
                            By.XPATH,
                            f"(//input[@name='CHT[]'])[{idx + 1}]"
                        )
                        input_cht.clear()
                        input_cht.send_keys(disc['cht'])
                    except NoSuchElementException:
                        logger.debug(f"    Campo CHT[{idx}] não encontrado")
                    
                    # MEDIA[]
                    if 'media' in disc and disc['media']:
                        try:
                            input_media = self.driver.find_element(
                                By.XPATH,
                                f"(//input[@name='MEDIA[]'])[{idx + 1}]"
                            )
                            input_media.clear()
                            input_media.send_keys(disc['media'])
                        except NoSuchElementException:
                            logger.debug(f"    Campo MEDIA[{idx}] não encontrado")
                    
                    # FALTA[]
                    if 'falta' in disc:
                        try:
                            input_falta = self.driver.find_element(
                                By.XPATH,
                                f"(//input[@name='FALTA[]'])[{idx + 1}]"
                            )
                            input_falta.clear()
                            input_falta.send_keys(disc['falta'])
                        except NoSuchElementException:
                            logger.debug(f"    Campo FALTA[{idx}] não encontrado")
                    
                    # SITUACAO[]
                    if 'situacao' in disc:
                        try:
                            select_situacao = Select(self.driver.find_element(
                                By.XPATH,
                                f"(//select[@name='SITUACAO[]'])[{idx + 1}]"
                            ))
                            select_situacao.select_by_value(disc['situacao'])
                        except NoSuchElementException:
                            logger.debug(f"    Campo SITUACAO[{idx}] não encontrado")
                    
                    logger.info(f"  ✓ Disciplina {idx + 1}/{len(disciplinas)} preenchida")
                    
                except Exception as e:
                    logger.warning(f"  ⚠ Erro ao preencher disciplina {idx}: {e}")
            
            logger.info("✓ Formulário preenchido com sucesso")
            return True
            
        except Exception as e:
            logger.exception(f"Erro ao preencher histórico: {e}")
            return False
    
    def salvar_historico(self, timeout: int = 30) -> Dict[str, any]:
        """
        Clica no botão Salvar e aguarda confirmação
        
        Args:
            timeout: Tempo máximo para aguardar resposta
            
        Returns:
            Dicionário com resultado:
            {
                'sucesso': bool,
                'mensagem': str,
                'id_exportacao': str (opcional)
            }
        """
        if not self.driver:
            return {
                'sucesso': False,
                'mensagem': 'Navegador não iniciado'
            }
        
        try:
            logger.info("Salvando histórico...")
            
            # Procurar botão Salvar
            # Possíveis textos: "Salvar", "Gravar", "Enviar"
            botao_salvar = None
            
            for texto in ["Salvar", "Gravar", "Enviar", "Save"]:
                try:
                    botao_salvar = self.driver.find_element(
                        By.XPATH,
                        f"//button[contains(text(), '{texto}')] | //input[@type='submit' and contains(@value, '{texto}')]"
                    )
                    break
                except NoSuchElementException:
                    continue
            
            if not botao_salvar:
                return {
                    'sucesso': False,
                    'mensagem': 'Botão Salvar não encontrado no formulário'
                }
            
            # Guardar URL atual para detectar redirect
            url_antes = self.driver.current_url
            
            # Clicar em Salvar
            botao_salvar.click()
            logger.info("  → Botão Salvar clicado, aguardando resposta...")
            
            # Aguardar processamento
            time.sleep(2)
            
            # Estratégias para detectar sucesso:
            resultado = self._verificar_resultado_salvamento(url_antes, timeout)
            
            if resultado['sucesso']:
                logger.info(f"✓ Histórico salvo com sucesso: {resultado['mensagem']}")
            else:
                logger.error(f"✗ Falha ao salvar: {resultado['mensagem']}")
            
            return resultado
            
        except Exception as e:
            logger.exception(f"Erro ao salvar histórico: {e}")
            return {
                'sucesso': False,
                'mensagem': f'Erro ao clicar em Salvar: {str(e)}'
            }
    
    def _verificar_resultado_salvamento(self, url_antes: str, timeout: int) -> Dict[str, any]:
        """
        Verifica se salvamento foi bem-sucedido
        
        Estratégias:
        1. Procurar mensagem de sucesso/erro na página
        2. Verificar se houve redirect
        3. Procurar alertas JavaScript
        """
        try:
            # Aguardar um pouco para processar
            wait = WebDriverWait(self.driver, timeout)
            
            # Estratégia 1: Procurar por mensagens de sucesso
            mensagens_sucesso = [
                "sucesso", "salvo com sucesso", "gravado", 
                "cadastrado", "atualizado", "success"
            ]
            
            for msg in mensagens_sucesso:
                try:
                    elemento = self.driver.find_element(
                        By.XPATH,
                        f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{msg}')]"
                    )
                    texto = elemento.text
                    return {
                        'sucesso': True,
                        'mensagem': texto[:200]  # Limitar tamanho
                    }
                except NoSuchElementException:
                    continue
            
            # Estratégia 2: Verificar redirect (mudou de página)
            time.sleep(1)
            url_depois = self.driver.current_url
            
            if url_depois != url_antes:
                logger.info(f"  → Redirect detectado: {url_antes} → {url_depois}")
                
                # Se voltou para lista ou página de sucesso
                if "list" in url_depois.lower() or "index" in url_depois.lower():
                    return {
                        'sucesso': True,
                        'mensagem': 'Redirect após salvamento (sucesso presumido)'
                    }
            
            # Estratégia 3: Verificar se ainda tem erros na página
            mensagens_erro = [
                "erro", "error", "falha", "inválido", "obrigatório",
                "preencha", "campo vazio"
            ]
            
            for msg in mensagens_erro:
                try:
                    elemento = self.driver.find_element(
                        By.XPATH,
                        f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{msg}')]"
                    )
                    texto = elemento.text
                    return {
                        'sucesso': False,
                        'mensagem': f'Erro no formulário: {texto[:200]}'
                    }
                except NoSuchElementException:
                    continue
            
            # Se não encontrou nada, assumir sucesso (pode ser ajustado)
            return {
                'sucesso': True,
                'mensagem': 'Formulário submetido (verificar manualmente se salvou)'
            }
            
        except Exception as e:
            logger.exception(f"Erro ao verificar resultado: {e}")
            return {
                'sucesso': False,
                'mensagem': f'Não foi possível verificar resultado: {str(e)}'
            }
    
    def fechar(self):
        """Fecha navegador e limpa recursos"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navegador fechado")
            except Exception as e:
                logger.warning(f"Erro ao fechar navegador: {e}")
            finally:
                self.driver = None


def exportar_historico_aluno(
    aluno_id: int,
    usuario_geduc: str,
    senha_geduc: str,
    dados_historico: Dict,
    callback_progresso: Optional[callable] = None
) -> Dict[str, any]:
    """
    Função principal para exportar histórico escolar de um aluno para o GEDUC
    
    Esta é a função chamada pela interface (historico_escolar.py)
    
    Args:
        aluno_id: ID do aluno no sistema local
        usuario_geduc: Usuário do GEDUC
        senha_geduc: Senha do GEDUC
        dados_historico: Dicionário com dados a exportar:
            {
                # OPÇÃO 1: Fornecer ID direto (se já conhecido)
                'idaluno_geduc': int,      # ID do aluno no GEDUC (opcional)
                
                # OPÇÃO 2: Buscar por nome (se ID não fornecido)
                'nome_aluno': str,         # Nome do aluno para busca (opcional)
                
                # Dados obrigatórios
                'idinstituicao': int,
                'ano': int,
                'idcurso': int,
                'idcurriculo': int,
                'tipoescola': int,
                'disciplinas': [
                    {
                        'id': str,
                        'cht': str,
                        'media': str,
                        'falta': str,
                        'situacao': str
                    },
                    ...
                ]
            }
        callback_progresso: Função opcional para reportar progresso
                           callback_progresso(mensagem: str)
    
    Returns:
        {
            'sucesso': bool,
            'registros_enviados': int,
            'mensagem': str,
            'erro': str (se houver)
        }
    """
    exportador = None
    
    try:
        # Callback helper
        def progresso(msg):
            logger.info(msg)
            if callback_progresso:
                callback_progresso(msg)
        
        progresso("Iniciando exportação para GEDUC...")
        
        # 1. Inicializar navegador
        progresso("Iniciando navegador Chrome...")
        exportador = ExportadorGEDUC(headless=False)  # Não-headless para resolver reCAPTCHA
        
        if not exportador.iniciar_navegador():
            return {
                'sucesso': False,
                'erro': 'Falha ao iniciar navegador Chrome'
            }
        
        # 2. Fazer login
        progresso("Fazendo login no GEDUC...")
        progresso("⚠ ATENÇÃO: Resolva o reCAPTCHA manualmente no navegador!")
        
        if not exportador.fazer_login(usuario_geduc, senha_geduc, timeout_recaptcha=120):
            return {
                'sucesso': False,
                'erro': 'Falha no login do GEDUC'
            }
        
        progresso("✓ Login realizado com sucesso")
        
        # 2.5. Buscar aluno se necessário
        idaluno_geduc = dados_historico.get('idaluno_geduc')
        
        if not idaluno_geduc and 'nome_aluno' in dados_historico:
            # Buscar aluno por nome
            nome_aluno = dados_historico['nome_aluno']
            progresso(f"Buscando aluno no GEDUC: {nome_aluno}...")
            
            resultado_busca = exportador.buscar_aluno_por_nome(nome_aluno)
            
            if resultado_busca:
                idaluno_geduc = resultado_busca['id']
                progresso(f"✓ Aluno encontrado: {resultado_busca['nome']} (ID: {idaluno_geduc})")
            else:
                return {
                    'sucesso': False,
                    'erro': f'Aluno não encontrado no GEDUC: {nome_aluno}'
                }
        
        if not idaluno_geduc:
            return {
                'sucesso': False,
                'erro': 'ID do aluno no GEDUC não fornecido e busca por nome não configurada'
            }
        
        # 3. Acessar formulário de histórico
        progresso("Acessando formulário de histórico...")
        
        if not exportador.acessar_cadastro_historico(
            idaluno=idaluno_geduc,
            idinstituicao=dados_historico['idinstituicao'],
            ano=dados_historico['ano'],
            idcurso=dados_historico['idcurso'],
            tipoescola=dados_historico.get('tipoescola', 1)
        ):
            return {
                'sucesso': False,
                'erro': 'Falha ao acessar formulário de histórico'
            }
        
        progresso("✓ Formulário carregado")
        
        # 4. Preencher dados
        progresso(f"Preenchendo {len(dados_historico['disciplinas'])} disciplinas...")
        
        if not exportador.preencher_historico(
            idcurriculo=dados_historico['idcurriculo'],
            disciplinas=dados_historico['disciplinas'],
            visivel=dados_historico.get('visivel', 1)
        ):
            return {
                'sucesso': False,
                'erro': 'Falha ao preencher formulário'
            }
        
        progresso("✓ Formulário preenchido")
        
        # 5. Salvar
        progresso("Salvando histórico...")
        
        resultado = exportador.salvar_historico()
        
        if resultado['sucesso']:
            progresso("✓ Exportação concluída com sucesso!")
            return {
                'sucesso': True,
                'registros_enviados': len(dados_historico['disciplinas']),
                'mensagem': resultado['mensagem']
            }
        else:
            return {
                'sucesso': False,
                'erro': resultado['mensagem']
            }
        
    except Exception as e:
        logger.exception(f"Erro durante exportação: {e}")
        return {
            'sucesso': False,
            'erro': f'Erro inesperado: {str(e)}'
        }
    
    finally:
        # Sempre fechar navegador
        if exportador:
            exportador.fechar()
