#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POC - Prova de Conceito: Exportação para GEDUC
===============================================

Tarefa 1.3 da Fase 1
Script de teste para validar autenticação e submissão de dados ao GEDUC.

Autor: Sistema de Gestão Escolar
Data: 20/12/2025
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/poc_geduc_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class GEDUCClientPOC:
    """
    Cliente POC para testar conexão e submissão ao GEDUC.
    
    Este é um protótipo para validação. A versão final será mais robusta.
    """
    
    BASE_URL = "https://semed.geduc.com.br"
    
    def __init__(self, timeout: int = 30):
        """
        Inicializa o cliente GEDUC.
        
        Args:
            timeout: Tempo limite para requisições em segundos
        """
        self.session = self._criar_sessao()
        self.timeout = timeout
        self.logged_in = False
        self.csrf_token = None
        
    def _criar_sessao(self) -> requests.Session:
        """Cria sessão com retry automático"""
        session = requests.Session()
        
        # Configurar retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers padrão (simular navegador)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def fazer_login(self, usuario: str, senha: str) -> bool:
        """
        Realiza login no GEDUC.
        
        Args:
            usuario: Nome de usuário
            senha: Senha
            
        Returns:
            True se login bem-sucedido, False caso contrário
        """
        logger.info("Iniciando processo de login no GEDUC...")
        
        try:
            # 1. Acessar página de login para obter formulário e possível CSRF token
            logger.info("Acessando página de login...")
            url_login = f"{self.BASE_URL}/index.php"
            
            response = self.session.get(url_login, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML para encontrar campos do formulário
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Procurar por token CSRF (pode ter nomes diferentes)
            csrf_input = soup.find('input', {'name': lambda x: x and 'csrf' in x.lower()})
            if csrf_input:
                self.csrf_token = csrf_input.get('value')
                logger.info(f"Token CSRF encontrado: {self.csrf_token[:20]}...")
            
            # 2. Preparar dados de login
            # ATENÇÃO: Estrutura real do formulário precisa ser descoberta na Tarefa 1.2
            login_data = {
                'login': usuario,
                'password': senha,
                # Adicionar outros campos conforme descoberto na captura
            }
            
            if self.csrf_token:
                login_data['csrf_token'] = self.csrf_token
            
            # 3. Enviar POST de login
            logger.info("Enviando credenciais de login...")
            response = self.session.post(
                url_login,
                data=login_data,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # 4. Verificar se login foi bem-sucedido
            # Métodos possíveis:
            # - Verificar cookie de sessão
            # - Verificar redirect para dashboard
            # - Procurar por texto específico na página
            
            if 'PHPSESSID' in self.session.cookies or 'session' in self.session.cookies:
                logger.info("Cookie de sessão detectado")
                self.logged_in = True
            
            # Verificar se há mensagem de erro
            if 'erro' in response.text.lower() or 'senha incorreta' in response.text.lower():
                logger.error("Login falhou - credenciais inválidas")
                return False
            
            # Verificar se redirecionou para dashboard
            if 'dashboard' in response.url.lower():
                logger.info("Redirecionado para dashboard - login bem-sucedido")
                self.logged_in = True
                return True
            
            logger.warning("Status de login incerto - verificar manualmente")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro durante login: {str(e)}")
            return False
    
    def buscar_aluno(self, nome: str = None, id_geduc: int = None) -> Optional[Dict]:
        """
        Busca aluno no GEDUC.
        
        Args:
            nome: Nome do aluno para buscar
            id_geduc: ID do aluno no GEDUC
            
        Returns:
            Dicionário com dados do aluno ou None
        """
        if not self.logged_in:
            logger.error("Não está logado no GEDUC")
            return None
        
        logger.info(f"Buscando aluno: nome={nome}, id={id_geduc}")
        
        # TODO: Implementar após Tarefa 1.2 descobrir endpoint de busca
        # Exemplo:
        # url_busca = f"{self.BASE_URL}/index.php?class=FichaAlunoForm&method=onSearch"
        
        return {
            'id': id_geduc or 235718,
            'nome': nome or "TESTE POC",
            'encontrado': True
        }
    
    def enviar_historico(
        self,
        idaluno: int,
        idinstituicao: int,
        ano: int,
        idcurso: int,
        idcurriculo: int,
        disciplinas: List[Dict[str, str]]
    ) -> Dict:
        """
        Envia histórico escolar para GEDUC.
        
        Args:
            idaluno: ID do aluno no GEDUC
            idinstituicao: ID da instituição
            ano: Ano letivo
            idcurso: ID do curso/série
            idcurriculo: ID do currículo
            disciplinas: Lista de dicionários com dados das disciplinas
            
        Returns:
            Dicionário com resultado da operação
        """
        if not self.logged_in:
            return {
                'sucesso': False,
                'erro': 'Não está logado no GEDUC'
            }
        
        logger.info(f"Enviando histórico: aluno={idaluno}, ano={ano}, disciplinas={len(disciplinas)}")
        
        try:
            # URL conforme documentado na Fase 1
            url = f"{self.BASE_URL}/index.php"
            params = {
                'class': 'DisciplinasHistorico',
                'method': 'onEdit',
                'IDCURSO': idcurso,
                'ANO': ano,
                'IDALUNO': idaluno,
                'IDINSTITUICAO': idinstituicao,
                'TIPOESCOLA': 1
            }
            
            # Preparar payload
            data = {
                'IDALUNO': str(idaluno),
                'IDINSTITUICAO': str(idinstituicao),
                'ANO': str(ano),
                'IDESCOLA': '',
                'TIPOESCOLA': '1',
                'VISIVEL': '1',
                'IDCURSO': str(idcurso),
                'IDCURRICULO': str(idcurriculo)
            }
            
            # Adicionar arrays de disciplinas
            for disc in disciplinas:
                # Usar setdefault para criar listas
                for key in ['IDDISCIPLINAS[]', 'CHT[]', 'MEDIA[]', 'FALTA[]', 'SITUACAO[]']:
                    if key not in data:
                        data[key] = []
            
            # Popular arrays
            for disc in disciplinas:
                data['IDDISCIPLINAS[]'].append(str(disc['id']))
                data['CHT[]'].append(str(disc['cht']))
                data['MEDIA[]'].append(str(disc.get('media', '')))
                data['FALTA[]'].append(str(disc.get('falta', '')))
                data['SITUACAO[]'].append(str(disc.get('situacao', '')))
            
            # Adicionar CSRF token se existir
            if self.csrf_token:
                data['csrf_token'] = self.csrf_token
            
            # Headers específicos para form POST
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': self.BASE_URL,
                'Referer': f"{self.BASE_URL}/index.php?class=DisciplinasHistorico"
            }
            
            # Enviar POST
            logger.info(f"Enviando POST para {url}")
            logger.debug(f"Params: {params}")
            logger.debug(f"Data: {data}")
            
            response = self.session.post(
                url,
                params=params,
                data=data,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Analisar resposta
            logger.info(f"Status code: {response.status_code}")
            logger.debug(f"Response: {response.text[:500]}...")
            
            # Verificar sucesso (depende do formato da resposta - descobrir na Tarefa 1.2)
            if response.status_code == 200:
                # Procurar por indicadores de sucesso
                if 'sucesso' in response.text.lower() or 'salvo' in response.text.lower():
                    return {
                        'sucesso': True,
                        'mensagem': 'Histórico enviado com sucesso',
                        'registros_enviados': len(disciplinas)
                    }
            
            return {
                'sucesso': False,
                'erro': 'Resposta inesperada do servidor',
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar histórico: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def logout(self):
        """Realiza logout do GEDUC"""
        logger.info("Realizando logout...")
        
        try:
            # URL de logout (descobrir na Tarefa 1.2)
            url_logout = f"{self.BASE_URL}/index.php?class=LoginForm&method=onLogout"
            self.session.get(url_logout, timeout=self.timeout)
            self.logged_in = False
            logger.info("Logout realizado")
        except Exception as e:
            logger.warning(f"Erro ao fazer logout: {str(e)}")


def teste_conexao_basica():
    """Teste 1: Verificar se consegue conectar ao GEDUC"""
    logger.info("=" * 80)
    logger.info("TESTE 1: Conexão Básica")
    logger.info("=" * 80)
    
    try:
        client = GEDUCClientPOC()
        response = client.session.get(f"{client.BASE_URL}/index.php", timeout=10)
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Cookies: {dict(response.cookies)}")
        logger.info(f"URL final: {response.url}")
        
        if response.status_code == 200:
            logger.info("✓ Conexão básica OK")
            return True
        else:
            logger.error("✗ Falha na conexão básica")
            return False
    except Exception as e:
        logger.error(f"✗ Erro: {str(e)}")
        return False


def teste_login():
    """Teste 2: Tentar login (requer credenciais reais)"""
    logger.info("=" * 80)
    logger.info("TESTE 2: Login")
    logger.info("=" * 80)
    
    # ATENÇÃO: Não commitar credenciais reais!
    # Usar variáveis de ambiente ou arquivo de configuração
    usuario = os.getenv('GEDUC_USER', 'usuario_teste')
    senha = os.getenv('GEDUC_PASS', 'senha_teste')
    
    if usuario == 'usuario_teste':
        logger.warning("⚠ Usando credenciais de teste - não irá funcionar")
        logger.info("Configure as variáveis de ambiente GEDUC_USER e GEDUC_PASS")
        return False
    
    try:
        client = GEDUCClientPOC()
        sucesso = client.fazer_login(usuario, senha)
        
        if sucesso:
            logger.info("✓ Login bem-sucedido")
            client.logout()
            return True
        else:
            logger.error("✗ Falha no login")
            return False
    except Exception as e:
        logger.error(f"✗ Erro: {str(e)}")
        return False


def teste_envio_historico():
    """Teste 3: Enviar histórico de teste"""
    logger.info("=" * 80)
    logger.info("TESTE 3: Envio de Histórico")
    logger.info("=" * 80)
    
    usuario = os.getenv('GEDUC_USER')
    senha = os.getenv('GEDUC_PASS')
    
    if not usuario or not senha:
        logger.warning("⚠ Credenciais não configuradas - pulando teste")
        return False
    
    try:
        client = GEDUCClientPOC()
        
        # Login
        if not client.fazer_login(usuario, senha):
            logger.error("✗ Falha no login")
            return False
        
        # Dados de teste (baseado na análise da Fase 1)
        disciplinas_teste = [
            {'id': '77', 'cht': '400', 'media': '8.5', 'falta': '0', 'situacao': '0'},
            {'id': '78', 'cht': '40', 'media': '9.0', 'falta': '2', 'situacao': '0'},
            {'id': '79', 'cht': '40', 'media': '8.0', 'falta': '0', 'situacao': '0'}
        ]
        
        resultado = client.enviar_historico(
            idaluno=235718,  # ID de teste
            idinstituicao=1318,
            ano=2025,
            idcurso=4,
            idcurriculo=69,
            disciplinas=disciplinas_teste
        )
        
        client.logout()
        
        if resultado['sucesso']:
            logger.info("✓ Histórico enviado com sucesso")
            logger.info(f"Detalhes: {resultado}")
            return True
        else:
            logger.error(f"✗ Falha ao enviar: {resultado.get('erro')}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Erro: {str(e)}")
        return False


def main():
    """Função principal - executa todos os testes"""
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " POC - Exportação GEDUC ".center(78) + "║")
    logger.info("║" + " Tarefa 1.3 - Fase 1 ".center(78) + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("")
    
    resultados = {
        'Conexão Básica': teste_conexao_basica(),
        'Login': teste_login(),
        'Envio Histórico': teste_envio_historico()
    }
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESUMO DOS TESTES")
    logger.info("=" * 80)
    
    for teste, resultado in resultados.items():
        status = "✓ PASSOU" if resultado else "✗ FALHOU"
        logger.info(f"{teste:.<50} {status}")
    
    logger.info("=" * 80)
    
    total = len(resultados)
    passou = sum(1 for r in resultados.values() if r)
    
    logger.info(f"Total: {passou}/{total} testes passaram")
    
    if passou == total:
        logger.info("🎉 Todos os testes passaram!")
        return 0
    else:
        logger.warning("⚠ Alguns testes falharam - revisar implementação")
        return 1


if __name__ == "__main__":
    sys.exit(main())
