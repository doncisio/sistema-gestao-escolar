# 🔧 Guia Técnico: Exportação de Histórico Escolar para GEDUC

**Complemento ao Plano de Ação**  
**Data:** 20/12/2025

---

## 📐 1. ARQUITETURA PROPOSTA

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA LOCAL                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Interface Gráfica (Tkinter)                          │  │
│  │  - Seleção de dados a exportar                        │  │
│  │  - Configuração de parâmetros                         │  │
│  │  - Monitoramento de progresso                         │  │
│  └───────────────┬───────────────────────────────────────┘  │
│                  │                                           │
│  ┌───────────────▼───────────────────────────────────────┐  │
│  │  Camada de Serviço (GEDUCExportador)                  │  │
│  │  - Orquestração da exportação                         │  │
│  │  - Controle de fluxo e transações                     │  │
│  │  - Gerenciamento de sessão GEDUC                      │  │
│  └───────────────┬───────────────────────────────────────┘  │
│                  │                                           │
│  ┌───────────────▼───────────────────────────────────────┐  │
│  │  Camada de Dados                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │  │
│  │  │ Mapeador     │  │ Validador    │  │ Logger      │  │  │
│  │  │ - Conversão  │  │ - Regras     │  │ - Auditoria │  │  │
│  │  │   de dados   │  │ - Integridade│  │ - Rastreio  │  │  │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │  │
│  └───────────────┬───────────────────────────────────────┘  │
│                  │                                           │
│  ┌───────────────▼───────────────────────────────────────┐  │
│  │  Banco de Dados MySQL                                  │  │
│  │  - historico_escolar                                   │  │
│  │  - alunos, disciplinas, series, etc.                   │  │
│  │  - exportacoes_geduc (auditoria)                       │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS / Selenium WebDriver
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA GEDUC ONLINE                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Interface Web                                          │ │
│  │  - Formulários HTML                                     │ │
│  │  - Validações JavaScript                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Backend GEDUC                                          │ │
│  │  - Lógica de negócio                                    │ │
│  │  - Validações server-side                               │ │
│  │  - Banco de dados GEDUC                                 │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 2. CÓDIGO EXEMPLO - ESTRUTURA BÁSICA

### 2.1 Classe Principal `GEDUCExportador`

```python
# src/exportadores/geduc_exportador.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Optional
import time
from datetime import datetime

from src.core.conexao import conectar_bd
from src.core.config_logs import get_logger
from src.exportadores.geduc_mapeador import GEDUCMapeador
from src.exportadores.geduc_validador import GEDUCValidador

logger = get_logger(__name__)


class GEDUCExportador:
    """
    Classe para exportar histórico escolar do sistema local para o GEDUC.
    
    Utiliza Selenium WebDriver para automatizar o preenchimento de formulários
    na interface web do GEDUC.
    """
    
    def __init__(self, usuario: str, senha: str, headless: bool = False):
        """
        Inicializa o exportador.
        
        Args:
            usuario: Login do GEDUC
            senha: Senha do GEDUC
            headless: Se True, executa sem interface gráfica
        """
        self.usuario = usuario
        self.senha = senha
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.url_base = "https://semed.geduc.com.br"
        
        # Componentes auxiliares
        self.mapeador = GEDUCMapeador()
        self.validador = GEDUCValidador()
        
        # Controle de sessão
        self.sessao_ativa = False
        self.ultimo_acesso = None
        
        # Estatísticas
        self.total_exportado = 0
        self.total_erros = 0
        self.total_sucesso = 0
        
    def iniciar_navegador(self) -> bool:
        """Configura e inicia o navegador Chrome."""
        try:
            options = webdriver.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless')
                
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            # Evitar detecção de automação
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)
            
            logger.info("✓ Navegador iniciado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao iniciar navegador: {e}")
            return False
    
    def fazer_login(self) -> bool:
        """Realiza login no GEDUC."""
        try:
            logger.info("→ Acessando página de login...")
            self.driver.get(f"{self.url_base}/index.php")
            
            # Aguardar carregamento
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            
            # Preencher credenciais
            self.driver.find_element(By.NAME, "login").send_keys(self.usuario)
            self.driver.find_element(By.NAME, "password").send_keys(self.senha)
            
            # Submeter formulário
            self.driver.find_element(By.NAME, "password").submit()
            
            # Verificar sucesso do login
            time.sleep(2)
            if "index.php" in self.driver.current_url:
                logger.info("✓ Login realizado com sucesso")
                self.sessao_ativa = True
                self.ultimo_acesso = datetime.now()
                return True
            else:
                logger.error("✗ Falha no login")
                return False
                
        except Exception as e:
            logger.error(f"✗ Erro ao fazer login: {e}")
            return False
    
    def acessar_historico_escolar(self) -> bool:
        """Navega até a página de cadastro de histórico escolar."""
        try:
            # URL precisa ser identificada durante a Fase 1
            url_historico = f"{self.url_base}/index.php?class=HistoricoEscolarForm"
            
            logger.info("→ Acessando página de histórico escolar...")
            self.driver.get(url_historico)
            
            # Verificar se carregou corretamente
            time.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao acessar histórico: {e}")
            return False
    
    def exportar_historico_aluno(self, aluno_id: int) -> Dict:
        """
        Exporta todo o histórico escolar de um aluno.
        
        Args:
            aluno_id: ID do aluno no banco local
            
        Returns:
            Dict com resultado da exportação
        """
        resultado = {
            'aluno_id': aluno_id,
            'total_registros': 0,
            'sucesso': 0,
            'erros': 0,
            'mensagens': []
        }
        
        try:
            # Buscar dados do aluno
            conn = conectar_bd()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    h.id,
                    a.nome as aluno_nome,
                    d.nome as disciplina_nome,
                    s.nome as serie_nome,
                    al.ano_letivo,
                    e.nome as escola_nome,
                    h.media,
                    h.conceito,
                    d.carga_horaria
                FROM historico_escolar h
                JOIN alunos a ON h.aluno_id = a.id
                JOIN disciplinas d ON h.disciplina_id = d.id
                JOIN series s ON h.serie_id = s.id
                JOIN anosletivos al ON h.ano_letivo_id = al.id
                JOIN escolas e ON h.escola_id = e.id
                WHERE a.id = %s
                ORDER BY al.ano_letivo, s.id, d.nome
            """
            
            cursor.execute(query, (aluno_id,))
            registros = cursor.fetchall()
            
            resultado['total_registros'] = len(registros)
            logger.info(f"→ Encontrados {len(registros)} registros para aluno {aluno_id}")
            
            # Exportar cada registro
            for registro in registros:
                sucesso = self._exportar_registro_individual(registro)
                
                if sucesso:
                    resultado['sucesso'] += 1
                    self.total_sucesso += 1
                else:
                    resultado['erros'] += 1
                    self.total_erros += 1
                    
                self.total_exportado += 1
                
            cursor.close()
            conn.close()
            
            logger.info(f"✓ Exportação concluída: {resultado['sucesso']}/{resultado['total_registros']} registros")
            return resultado
            
        except Exception as e:
            logger.error(f"✗ Erro na exportação do aluno {aluno_id}: {e}")
            resultado['mensagens'].append(str(e))
            return resultado
    
    def _exportar_registro_individual(self, registro: Dict) -> bool:
        """
        Exporta um único registro de histórico escolar.
        
        Args:
            registro: Dicionário com dados do registro
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Validar dados antes de enviar
            if not self.validador.validar_registro(registro):
                logger.warning(f"⚠ Registro inválido: {registro}")
                return False
            
            # Mapear dados do formato local para GEDUC
            dados_geduc = self.mapeador.mapear_registro(registro)
            
            # Preencher formulário (implementação depende da estrutura do GEDUC)
            # Esta é uma estrutura genérica - precisa ser adaptada
            
            # 1. Selecionar aluno
            select_aluno = Select(self.driver.find_element(By.NAME, "IDALUNO"))
            select_aluno.select_by_visible_text(dados_geduc['aluno_nome'])
            
            # 2. Selecionar disciplina
            select_disciplina = Select(self.driver.find_element(By.NAME, "IDDISCIPLINA"))
            select_disciplina.select_by_visible_text(dados_geduc['disciplina_nome'])
            
            # 3. Selecionar série
            select_serie = Select(self.driver.find_element(By.NAME, "IDSERIE"))
            select_serie.select_by_visible_text(dados_geduc['serie_nome'])
            
            # 4. Preencher ano letivo
            input_ano = self.driver.find_element(By.NAME, "ANO_LETIVO")
            input_ano.clear()
            input_ano.send_keys(dados_geduc['ano_letivo'])
            
            # 5. Preencher média/conceito
            if dados_geduc['media']:
                input_media = self.driver.find_element(By.NAME, "MEDIA")
                input_media.clear()
                input_media.send_keys(str(dados_geduc['media']))
            
            if dados_geduc['conceito']:
                select_conceito = Select(self.driver.find_element(By.NAME, "CONCEITO"))
                select_conceito.select_by_value(dados_geduc['conceito'])
            
            # 6. Preencher carga horária
            input_ch = self.driver.find_element(By.NAME, "CARGA_HORARIA")
            input_ch.clear()
            input_ch.send_keys(str(dados_geduc['carga_horaria']))
            
            # 7. Submeter formulário
            botao_salvar = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            botao_salvar.click()
            
            # 8. Verificar mensagem de sucesso
            time.sleep(1)
            # Aqui você deve verificar se apareceu mensagem de sucesso
            
            logger.info(f"✓ Registro exportado: {registro['disciplina_nome']} - {registro['ano_letivo']}")
            
            # Registrar exportação no banco de auditoria
            self._registrar_auditoria(registro, 'sucesso')
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Erro ao exportar registro: {e}")
            self._registrar_auditoria(registro, 'erro', str(e))
            return False
    
    def _registrar_auditoria(self, registro: Dict, status: str, mensagem_erro: str = None):
        """Registra a tentativa de exportação no banco de auditoria."""
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO exportacoes_geduc_detalhes 
                (exportacao_id, aluno_id, disciplina_id, ano_letivo_id, status, mensagem_erro)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # Nota: exportacao_id deve vir de uma sessão de exportação
            cursor.execute(query, (
                None,  # Implementar controle de sessão
                registro.get('aluno_id'),
                registro.get('disciplina_id'),
                registro.get('ano_letivo_id'),
                status,
                mensagem_erro
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {e}")
    
    def exportar_historico_turma(self, turma_id: int, ano_letivo_id: int, 
                                  callback_progresso=None) -> Dict:
        """
        Exporta histórico de todos os alunos de uma turma.
        
        Args:
            turma_id: ID da turma
            ano_letivo_id: ID do ano letivo
            callback_progresso: Função callback para atualizar progresso
            
        Returns:
            Dicionário com estatísticas da exportação
        """
        resultado = {
            'turma_id': turma_id,
            'total_alunos': 0,
            'alunos_sucesso': 0,
            'alunos_erro': 0,
            'detalhes': []
        }
        
        try:
            # Buscar alunos da turma
            conn = conectar_bd()
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT a.id
                FROM alunos a
                JOIN matriculas m ON a.id = m.aluno_id
                WHERE m.turma_id = %s AND m.ano_letivo_id = %s
                AND m.status = 'Ativo'
                ORDER BY a.nome
            """
            
            cursor.execute(query, (turma_id, ano_letivo_id))
            alunos = cursor.fetchall()
            
            resultado['total_alunos'] = len(alunos)
            logger.info(f"→ Exportando {len(alunos)} alunos da turma {turma_id}")
            
            # Exportar cada aluno
            for idx, (aluno_id,) in enumerate(alunos, 1):
                logger.info(f"  [{idx}/{len(alunos)}] Aluno ID {aluno_id}")
                
                resultado_aluno = self.exportar_historico_aluno(aluno_id)
                resultado['detalhes'].append(resultado_aluno)
                
                if resultado_aluno['erros'] == 0:
                    resultado['alunos_sucesso'] += 1
                else:
                    resultado['alunos_erro'] += 1
                
                # Callback de progresso
                if callback_progresso:
                    callback_progresso(idx, len(alunos))
                
                # Pequeno delay para não sobrecarregar o servidor
                time.sleep(0.5)
            
            cursor.close()
            conn.close()
            
            logger.info(f"✓ Exportação da turma concluída")
            return resultado
            
        except Exception as e:
            logger.error(f"✗ Erro na exportação da turma: {e}")
            return resultado
    
    def gerar_relatorio_exportacao(self, resultado: Dict) -> str:
        """
        Gera relatório textual da exportação.
        
        Args:
            resultado: Dicionário com resultados da exportação
            
        Returns:
            String com relatório formatado
        """
        relatorio = []
        relatorio.append("=" * 60)
        relatorio.append("RELATÓRIO DE EXPORTAÇÃO PARA GEDUC")
        relatorio.append("=" * 60)
        relatorio.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        relatorio.append("")
        
        if 'total_alunos' in resultado:
            # Exportação de turma
            relatorio.append(f"Tipo: Exportação de Turma")
            relatorio.append(f"Turma ID: {resultado['turma_id']}")
            relatorio.append(f"Total de Alunos: {resultado['total_alunos']}")
            relatorio.append(f"Alunos com Sucesso: {resultado['alunos_sucesso']}")
            relatorio.append(f"Alunos com Erro: {resultado['alunos_erro']}")
        else:
            # Exportação de aluno
            relatorio.append(f"Tipo: Exportação de Aluno")
            relatorio.append(f"Aluno ID: {resultado['aluno_id']}")
            relatorio.append(f"Total de Registros: {resultado['total_registros']}")
            relatorio.append(f"Registros com Sucesso: {resultado['sucesso']}")
            relatorio.append(f"Registros com Erro: {resultado['erros']}")
        
        relatorio.append("")
        relatorio.append("=" * 60)
        
        return "\n".join(relatorio)
    
    def fechar(self):
        """Fecha o navegador e encerra a sessão."""
        if self.driver:
            self.driver.quit()
            logger.info("✓ Navegador fechado")
            self.sessao_ativa = False
```

### 2.2 Classe `GEDUCMapeador`

```python
# src/exportadores/geduc_mapeador.py

from typing import Dict
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class GEDUCMapeador:
    """
    Classe responsável por mapear dados do sistema local para o formato GEDUC.
    """
    
    def __init__(self):
        # Mapeamentos de nomenclaturas
        self.mapa_disciplinas = self._carregar_mapa_disciplinas()
        self.mapa_series = self._carregar_mapa_series()
        self.mapa_conceitos = {
            (9.0, 10.0): 'A',
            (7.0, 8.9): 'B',
            (5.0, 6.9): 'C',
            (3.0, 4.9): 'D',
            (0.0, 2.9): 'E'
        }
    
    def _carregar_mapa_disciplinas(self) -> Dict:
        """Carrega mapeamento de nomes de disciplinas."""
        # Este mapeamento deve ser construído durante a Fase 1
        return {
            'LÍNGUA PORTUGUESA': 'Português',
            'MATEMATICA': 'Matemática',
            'CIÊNCIAS': 'Ciências',
            'HISTÓRIA': 'História',
            'GEOGRAFIA': 'Geografia',
            'ARTE': 'Artes',
            'EDUCAÇÃO FÍSICA': 'Ed. Física',
            'INGLÊS': 'Língua Inglesa',
            # ... adicionar mais conforme necessário
        }
    
    def _carregar_mapa_series(self) -> Dict:
        """Carrega mapeamento de nomenclatura de séries."""
        return {
            '1º ANO': '1º Ano',
            '2º ANO': '2º Ano',
            '3º ANO': '3º Ano',
            '4º ANO': '4º Ano',
            '5º ANO': '5º Ano',
            '6º ANO': '6º Ano',
            '7º ANO': '7º Ano',
            '8º ANO': '8º Ano',
            '9º ANO': '9º Ano',
            # ... adicionar mais conforme necessário
        }
    
    def mapear_registro(self, registro: Dict) -> Dict:
        """
        Mapeia um registro do formato local para GEDUC.
        
        Args:
            registro: Dados do registro no formato local
            
        Returns:
            Dicionário com dados no formato GEDUC
        """
        dados_geduc = {
            'aluno_nome': registro.get('aluno_nome', ''),
            'disciplina_nome': self._mapear_disciplina(registro.get('disciplina_nome', '')),
            'serie_nome': self._mapear_serie(registro.get('serie_nome', '')),
            'ano_letivo': registro.get('ano_letivo', ''),
            'escola_nome': registro.get('escola_nome', ''),
            'media': self._normalizar_media(registro.get('media')),
            'conceito': self._mapear_conceito(registro.get('media'), registro.get('conceito')),
            'carga_horaria': registro.get('carga_horaria', 0)
        }
        
        return dados_geduc
    
    def _mapear_disciplina(self, disciplina_local: str) -> str:
        """Mapeia nome da disciplina do local para GEDUC."""
        disciplina_upper = disciplina_local.upper().strip()
        return self.mapa_disciplinas.get(disciplina_upper, disciplina_local)
    
    def _mapear_serie(self, serie_local: str) -> str:
        """Mapeia nome da série do local para GEDUC."""
        serie_upper = serie_local.upper().strip()
        return self.mapa_series.get(serie_upper, serie_local)
    
    def _normalizar_media(self, media) -> float:
        """Normaliza a média para o formato aceito pelo GEDUC."""
        if media is None:
            return 0.0
        
        try:
            media_float = float(media)
            return round(media_float, 1)
        except (ValueError, TypeError):
            logger.warning(f"⚠ Média inválida: {media}")
            return 0.0
    
    def _mapear_conceito(self, media, conceito_existente: str = None) -> str:
        """
        Mapeia média numérica para conceito.
        
        Args:
            media: Média numérica
            conceito_existente: Conceito já cadastrado (se houver)
            
        Returns:
            Conceito (A, B, C, D, E)
        """
        # Se já tem conceito, usar
        if conceito_existente:
            return conceito_existente.upper()
        
        # Senão, calcular a partir da média
        media_normalizada = self._normalizar_media(media)
        
        for (min_val, max_val), conceito in self.mapa_conceitos.items():
            if min_val <= media_normalizada <= max_val:
                return conceito
        
        return 'E'  # Padrão para médias muito baixas
```

### 2.3 Classe `GEDUCValidador`

```python
# src/exportadores/geduc_validador.py

from typing import Dict, List
import re
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class GEDUCValidador:
    """
    Classe responsável por validar dados antes da exportação.
    """
    
    def validar_registro(self, registro: Dict) -> bool:
        """
        Valida se um registro está apto para exportação.
        
        Args:
            registro: Dicionário com dados do registro
            
        Returns:
            True se válido, False caso contrário
        """
        erros = []
        
        # Validar campos obrigatórios
        if not registro.get('aluno_nome'):
            erros.append("Nome do aluno não informado")
        
        if not registro.get('disciplina_nome'):
            erros.append("Nome da disciplina não informado")
        
        if not registro.get('serie_nome'):
            erros.append("Nome da série não informado")
        
        if not registro.get('ano_letivo'):
            erros.append("Ano letivo não informado")
        
        # Validar formato dos dados
        if not self._validar_ano_letivo(registro.get('ano_letivo')):
            erros.append(f"Ano letivo inválido: {registro.get('ano_letivo')}")
        
        if not self._validar_media(registro.get('media')):
            erros.append(f"Média inválida: {registro.get('media')}")
        
        if not self._validar_carga_horaria(registro.get('carga_horaria')):
            erros.append(f"Carga horária inválida: {registro.get('carga_horaria')}")
        
        # Logar erros
        if erros:
            logger.warning(f"⚠ Registro inválido: {', '.join(erros)}")
            return False
        
        return True
    
    def _validar_ano_letivo(self, ano_letivo) -> bool:
        """Valida formato do ano letivo."""
        if not ano_letivo:
            return False
        
        try:
            ano = int(ano_letivo)
            return 1900 <= ano <= 2100
        except (ValueError, TypeError):
            return False
    
    def _validar_media(self, media) -> bool:
        """Valida valor da média."""
        if media is None:
            return True  # Média pode ser opcional
        
        try:
            media_float = float(media)
            return 0.0 <= media_float <= 10.0
        except (ValueError, TypeError):
            return False
    
    def _validar_carga_horaria(self, carga_horaria) -> bool:
        """Valida carga horária."""
        if not carga_horaria:
            return False
        
        try:
            ch = int(carga_horaria)
            return 0 < ch <= 2000  # Limite razoável
        except (ValueError, TypeError):
            return False
    
    def validar_lote(self, registros: List[Dict]) -> Dict:
        """
        Valida um lote de registros.
        
        Args:
            registros: Lista de registros
            
        Returns:
            Dicionário com estatísticas de validação
        """
        resultado = {
            'total': len(registros),
            'validos': 0,
            'invalidos': 0,
            'registros_invalidos': []
        }
        
        for registro in registros:
            if self.validar_registro(registro):
                resultado['validos'] += 1
            else:
                resultado['invalidos'] += 1
                resultado['registros_invalidos'].append(registro)
        
        logger.info(f"Validação: {resultado['validos']}/{resultado['total']} válidos")
        
        return resultado
```

---

## 🔍 3. QUERIES SQL NECESSÁRIAS

### 3.1 Criar Tabelas de Auditoria

```sql
-- Tabela principal de exportações
CREATE TABLE IF NOT EXISTS exportacoes_geduc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_exportacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT,
    tipo_exportacao VARCHAR(50) COMMENT 'aluno, turma, escola',
    entidade_id INT COMMENT 'ID do aluno, turma ou escola',
    registros_total INT DEFAULT 0,
    registros_sucesso INT DEFAULT 0,
    registros_erro INT DEFAULT 0,
    tempo_execucao_segundos INT,
    status VARCHAR(20) DEFAULT 'em_andamento' COMMENT 'sucesso, parcial, erro, cancelado',
    log_resumo TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_data_exportacao (data_exportacao),
    INDEX idx_status (status),
    INDEX idx_tipo_entidade (tipo_exportacao, entidade_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de detalhes por registro
CREATE TABLE IF NOT EXISTS exportacoes_geduc_detalhes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exportacao_id INT NOT NULL,
    aluno_id INT,
    disciplina_id INT,
    ano_letivo_id INT,
    serie_id INT,
    status VARCHAR(20) COMMENT 'sucesso, erro, pendente',
    tentativas INT DEFAULT 1,
    mensagem_erro TEXT,
    dados_enviados JSON COMMENT 'Snapshot dos dados enviados',
    data_tentativa DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exportacao_id) REFERENCES exportacoes_geduc(id) ON DELETE CASCADE,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE SET NULL,
    FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id) ON DELETE SET NULL,
    FOREIGN KEY (ano_letivo_id) REFERENCES anosletivos(id) ON DELETE SET NULL,
    INDEX idx_exportacao (exportacao_id),
    INDEX idx_aluno (aluno_id),
    INDEX idx_status_detalhe (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela de configurações e mapeamentos
CREATE TABLE IF NOT EXISTS geduc_mapeamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(50) COMMENT 'disciplina, serie, conceito, etc',
    valor_local VARCHAR(200),
    valor_geduc VARCHAR(200),
    ativo BOOLEAN DEFAULT TRUE,
    observacao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tipo_valor (tipo, valor_local),
    INDEX idx_tipo (tipo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3.2 Query para Buscar Histórico Completo de Aluno

```sql
SELECT 
    h.id as historico_id,
    a.id as aluno_id,
    a.nome as aluno_nome,
    a.data_nascimento,
    a.cpf,
    d.id as disciplina_id,
    d.nome as disciplina_nome,
    d.carga_horaria,
    s.id as serie_id,
    s.nome as serie_nome,
    al.id as ano_letivo_id,
    al.ano_letivo,
    e.id as escola_id,
    e.nome as escola_nome,
    e.inep as escola_inep,
    h.media,
    h.conceito,
    -- Verificar se já foi exportado
    (SELECT COUNT(*) 
     FROM exportacoes_geduc_detalhes egd 
     WHERE egd.aluno_id = a.id 
       AND egd.disciplina_id = d.id 
       AND egd.ano_letivo_id = al.id
       AND egd.status = 'sucesso') as ja_exportado
FROM historico_escolar h
INNER JOIN alunos a ON h.aluno_id = a.id
INNER JOIN disciplinas d ON h.disciplina_id = d.id
INNER JOIN series s ON h.serie_id = s.id
INNER JOIN anosletivos al ON h.ano_letivo_id = al.id
INNER JOIN escolas e ON h.escola_id = e.id
WHERE a.id = %s
ORDER BY al.ano_letivo DESC, s.id, d.nome;
```

### 3.3 Query para Buscar Histórico por Turma

```sql
SELECT 
    a.id as aluno_id,
    a.nome as aluno_nome,
    COUNT(DISTINCT h.id) as total_registros,
    COUNT(DISTINCT CASE WHEN egd.status = 'sucesso' THEN h.id END) as ja_exportados,
    COUNT(DISTINCT CASE WHEN egd.status = 'erro' THEN h.id END) as com_erro
FROM alunos a
INNER JOIN matriculas m ON a.id = m.aluno_id
LEFT JOIN historico_escolar h ON a.id = h.aluno_id AND h.ano_letivo_id = m.ano_letivo_id
LEFT JOIN exportacoes_geduc_detalhes egd ON h.aluno_id = egd.aluno_id 
    AND h.disciplina_id = egd.disciplina_id 
    AND h.ano_letivo_id = egd.ano_letivo_id
WHERE m.turma_id = %s 
  AND m.ano_letivo_id = %s
  AND m.status = 'Ativo'
GROUP BY a.id, a.nome
ORDER BY a.nome;
```

---

## 📊 4. SCRIPT DE TESTE STANDALONE

Este script pode ser usado para testar a exportação isoladamente:

```python
# scripts/teste_exportacao_geduc.py

import sys
import os

# Adicionar caminho do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.exportadores.geduc_exportador import GEDUCExportador
from src.core.config_logs import get_logger
import getpass

logger = get_logger(__name__)


def main():
    """Script de teste para exportação GEDUC."""
    
    print("=" * 60)
    print("TESTE DE EXPORTAÇÃO PARA GEDUC")
    print("=" * 60)
    print()
    
    # Solicitar credenciais
    usuario = input("Usuário GEDUC: ")
    senha = getpass.getpass("Senha GEDUC: ")
    
    # Solicitar ID do aluno
    aluno_id = input("\nID do aluno para teste: ")
    
    try:
        aluno_id = int(aluno_id)
    except ValueError:
        print("❌ ID inválido!")
        return
    
    # Confirmar
    print(f"\n⚠️  Será exportado o histórico completo do aluno ID {aluno_id}")
    confirma = input("Continuar? (s/N): ")
    
    if confirma.lower() != 's':
        print("Cancelado pelo usuário")
        return
    
    print("\n" + "=" * 60)
    print("INICIANDO EXPORTAÇÃO...")
    print("=" * 60 + "\n")
    
    # Criar exportador
    exportador = GEDUCExportador(usuario, senha, headless=False)
    
    try:
        # Iniciar navegador
        if not exportador.iniciar_navegador():
            print("❌ Erro ao iniciar navegador")
            return
        
        # Fazer login
        if not exportador.fazer_login():
            print("❌ Erro ao fazer login")
            return
        
        print("✅ Login realizado com sucesso\n")
        
        # Acessar página de histórico
        if not exportador.acessar_historico_escolar():
            print("❌ Erro ao acessar página de histórico")
            return
        
        print("✅ Página de histórico acessada\n")
        
        # Exportar histórico do aluno
        resultado = exportador.exportar_historico_aluno(aluno_id)
        
        # Exibir relatório
        print("\n" + "=" * 60)
        print("RESULTADO DA EXPORTAÇÃO")
        print("=" * 60)
        print(f"Total de Registros: {resultado['total_registros']}")
        print(f"Sucesso: {resultado['sucesso']}")
        print(f"Erros: {resultado['erros']}")
        
        if resultado['mensagens']:
            print("\nMensagens:")
            for msg in resultado['mensagens']:
                print(f"  - {msg}")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Exportação cancelada pelo usuário")
        
    except Exception as e:
        logger.exception("Erro durante exportação")
        print(f"\n❌ Erro: {e}")
        
    finally:
        # Fechar navegador
        exportador.fechar()
        print("\n✅ Navegador fechado")


if __name__ == "__main__":
    main()
```

---

## 🔐 5. CONSIDERAÇÕES DE SEGURANÇA

### 5.1 Armazenamento de Credenciais
**Nunca armazenar credenciais em texto plano!**

```python
# Usar arquivo de configuração criptografado
import json
from cryptography.fernet import Fernet

class GerenciadorCredenciais:
    def __init__(self, arquivo_chave='credenciais.key'):
        self.arquivo_chave = arquivo_chave
        self.cipher = self._carregar_ou_criar_chave()
    
    def _carregar_ou_criar_chave(self):
        """Carrega ou cria chave de criptografia."""
        if os.path.exists(self.arquivo_chave):
            with open(self.arquivo_chave, 'rb') as f:
                chave = f.read()
        else:
            chave = Fernet.generate_key()
            with open(self.arquivo_chave, 'wb') as f:
                f.write(chave)
        
        return Fernet(chave)
    
    def salvar_credenciais(self, usuario, senha):
        """Salva credenciais criptografadas."""
        dados = {'usuario': usuario, 'senha': senha}
        dados_json = json.dumps(dados).encode()
        dados_criptografados = self.cipher.encrypt(dados_json)
        
        with open('credenciais_geduc.enc', 'wb') as f:
            f.write(dados_criptografados)
    
    def carregar_credenciais(self):
        """Carrega credenciais descriptografadas."""
        with open('credenciais_geduc.enc', 'rb') as f:
            dados_criptografados = f.read()
        
        dados_json = self.cipher.decrypt(dados_criptografados)
        dados = json.loads(dados_json.decode())
        
        return dados['usuario'], dados['senha']
```

---

## 📈 6. MONITORAMENTO E MÉTRICAS

```python
# Classe para coletar métricas
class MetricasExportacao:
    def __init__(self):
        self.metricas = {
            'total_exportacoes': 0,
            'tempo_total_segundos': 0,
            'taxa_sucesso': 0.0,
            'registros_por_segundo': 0.0,
            'erros_por_tipo': {}
        }
    
    def registrar_exportacao(self, resultado, tempo_segundos):
        """Registra métricas de uma exportação."""
        self.metricas['total_exportacoes'] += 1
        self.metricas['tempo_total_segundos'] += tempo_segundos
        
        # Calcular taxa de sucesso
        if resultado['total_registros'] > 0:
            taxa = resultado['sucesso'] / resultado['total_registros']
            self.metricas['taxa_sucesso'] = (
                self.metricas['taxa_sucesso'] * (self.metricas['total_exportacoes'] - 1) + taxa
            ) / self.metricas['total_exportacoes']
        
        # Calcular registros por segundo
        if tempo_segundos > 0:
            self.metricas['registros_por_segundo'] = resultado['total_registros'] / tempo_segundos
    
    def gerar_relatorio_metricas(self):
        """Gera relatório de métricas."""
        return f"""
        === MÉTRICAS DE EXPORTAÇÃO ===
        Total de Exportações: {self.metricas['total_exportacoes']}
        Tempo Total: {self.metricas['tempo_total_segundos']}s
        Taxa de Sucesso: {self.metricas['taxa_sucesso']:.2%}
        Registros/segundo: {self.metricas['registros_por_segundo']:.2f}
        """
```

---

**Última Atualização:** 20/12/2025  
**Versão:** 1.0
