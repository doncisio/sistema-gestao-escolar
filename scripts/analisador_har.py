#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisador de Arquivos HAR - GEDUC
===================================

Script para analisar capturas de requisições HTTP do GEDUC exportadas em formato HAR.
Extrai informações críticas como headers, cookies, CSRF tokens e estrutura de payload.

Uso:
    python scripts/analisador_har.py <arquivo.har>
    python scripts/analisador_har.py "historico geduc/capturas/geduc_20251220.har"
"""

import json
import sys
from typing import Dict, List, Any
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import re


class AnalisadorHAR:
    """Analisador de arquivos HAR para descobrir estrutura de requisições"""
    
    def __init__(self, arquivo_har: str):
        self.arquivo = Path(arquivo_har)
        self.dados = None
        self.requisicoes_post = []
        self.cookies = set()
        self.csrf_tokens = []
        
    def carregar(self) -> bool:
        """Carrega arquivo HAR"""
        try:
            with open(self.arquivo, 'r', encoding='utf-8') as f:
                self.dados = json.load(f)
            print(f"✓ Arquivo HAR carregado: {self.arquivo}")
            return True
        except Exception as e:
            print(f"✗ Erro ao carregar HAR: {e}")
            return False
    
    def filtrar_requisicoes(self):
        """Filtra requisições relevantes do GEDUC"""
        if not self.dados:
            return
        
        entries = self.dados.get('log', {}).get('entries', [])
        
        for entry in entries:
            request = entry.get('request', {})
            method = request.get('method', '')
            url = request.get('url', '')
            
            # Filtrar apenas requisições do GEDUC
            if 'geduc.com.br' in url:
                if method == 'POST':
                    self.requisicoes_post.append(entry)
                
                # Coletar cookies
                cookies = request.get('cookies', [])
                for cookie in cookies:
                    self.cookies.add(cookie.get('name', ''))
        
        print(f"✓ Encontradas {len(self.requisicoes_post)} requisições POST")
        print(f"✓ Encontrados {len(self.cookies)} tipos de cookies diferentes")
    
    def analisar_login(self):
        """Analisa requisições de login"""
        print("\n" + "=" * 80)
        print("ANÁLISE: Requisições de Login")
        print("=" * 80)
        
        login_reqs = [
            req for req in self.requisicoes_post
            if 'login' in req['request']['url'].lower()
        ]
        
        if not login_reqs:
            print("⚠ Nenhuma requisição de login encontrada")
            print("Dica: Certifique-se de ter feito login enquanto o DevTools estava gravando")
            return
        
        for idx, req in enumerate(login_reqs, 1):
            print(f"\n--- Requisição de Login #{idx} ---")
            request = req['request']
            
            print(f"\nURL: {request['url']}")
            print(f"Método: {request['method']}")
            
            # Headers
            print("\nHeaders importantes:")
            for header in request.get('headers', []):
                name = header['name']
                value = header['value']
                if name.lower() in ['content-type', 'referer', 'origin', 'cookie', 'x-csrf-token']:
                    print(f"  {name}: {value[:100]}...")
            
            # POST Data
            post_data = request.get('postData', {})
            if post_data:
                print("\nDados do POST:")
                
                params = post_data.get('params', [])
                if params:
                    for param in params:
                        print(f"  {param['name']} = {param.get('value', '')}")
                
                text = post_data.get('text', '')
                if text:
                    print(f"\nPayload raw:")
                    print(f"  {text[:200]}...")
                    
                    # Tentar parsear
                    if 'application/x-www-form-urlencoded' in post_data.get('mimeType', ''):
                        parsed = parse_qs(text)
                        print("\nPayload parseado:")
                        for key, values in parsed.items():
                            print(f"  {key} = {values[0]}")
            
            # Response
            response = req.get('response', {})
            print(f"\nResposta:")
            print(f"  Status: {response.get('status')}")
            print(f"  Redirect: {response.get('redirectURL', 'N/A')}")
            
            # Cookies set
            set_cookies = response.get('cookies', [])
            if set_cookies:
                print("\nCookies criados:")
                for cookie in set_cookies:
                    print(f"  {cookie['name']} = {cookie.get('value', '')[:50]}...")
    
    def analisar_historico(self):
        """Analisa requisições de cadastro de histórico/notas"""
        print("\n" + "=" * 80)
        print("ANÁLISE: Requisições de Cadastro de Notas/Histórico")
        print("=" * 80)
        
        historico_reqs = [
            req for req in self.requisicoes_post
            if 'disciplinashistorico' in req['request']['url'].lower()
            or 'onsave' in req['request']['url'].lower()
            or 'onedit' in req['request']['url'].lower()
        ]
        
        if not historico_reqs:
            print("⚠ Nenhuma requisição de histórico encontrada")
            print("Dica: Navegue até cadastro de notas e salve um registro")
            return
        
        for idx, req in enumerate(historico_reqs, 1):
            print(f"\n--- Requisição de Histórico #{idx} ---")
            request = req['request']
            
            # URL completa com query params
            url = request['url']
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            print(f"\nURL: {parsed_url.path}")
            print("\nQuery Parameters:")
            for key, values in query_params.items():
                print(f"  {key} = {values[0]}")
            
            # Headers críticos
            print("\nHeaders:")
            for header in request.get('headers', []):
                name = header['name']
                value = header['value']
                if name.lower() in ['content-type', 'referer', 'cookie', 'x-csrf-token', 'x-requested-with']:
                    display_value = value[:80] + "..." if len(value) > 80 else value
                    print(f"  {name}: {display_value}")
            
            # POST Data (arrays de disciplinas)
            post_data = request.get('postData', {})
            if post_data:
                print("\nPayload:")
                
                params = post_data.get('params', [])
                text = post_data.get('text', '')
                
                if params:
                    # Agrupar arrays
                    arrays = {}
                    simples = {}
                    
                    for param in params:
                        name = param['name']
                        value = param.get('value', '')
                        
                        if '[]' in name:
                            base_name = name.replace('[]', '')
                            if base_name not in arrays:
                                arrays[base_name] = []
                            arrays[base_name].append(value)
                        else:
                            simples[name] = value
                    
                    print("\n  Campos simples:")
                    for key, value in simples.items():
                        print(f"    {key} = {value}")
                    
                    print("\n  Arrays:")
                    for key, values in arrays.items():
                        print(f"    {key}[] = {values}")
                        
                elif text:
                    print(f"  Raw: {text[:300]}...")
                    
                    # Tentar identificar estrutura
                    if 'IDDISCIPLINAS' in text:
                        print("\n  ✓ Detectado padrão de arrays de disciplinas")
                        
                        # Contar quantas disciplinas
                        matches = re.findall(r'IDDISCIPLINAS%5B%5D=(\d+)', text)
                        if matches:
                            print(f"  ✓ {len(matches)} disciplinas no payload")
            
            # Response
            response = req.get('response', {})
            status = response.get('status')
            print(f"\nResposta:")
            print(f"  Status: {status}")
            
            # Tentar ver corpo da resposta
            content = response.get('content', {})
            text = content.get('text', '')
            if text:
                print(f"  Tipo: {content.get('mimeType', 'unknown')}")
                if len(text) < 500:
                    print(f"  Corpo: {text}")
                else:
                    print(f"  Tamanho: {len(text)} bytes")
                    
                    # Procurar por mensagens
                    if 'sucesso' in text.lower():
                        print("  ✓ Contém 'sucesso'")
                    if 'erro' in text.lower():
                        print("  ✗ Contém 'erro'")
    
    def detectar_csrf(self):
        """Detecta tokens CSRF nas requisições"""
        print("\n" + "=" * 80)
        print("ANÁLISE: Tokens CSRF")
        print("=" * 80)
        
        csrf_patterns = [
            r'csrf[_-]?token',
            r'_token',
            r'authenticity[_-]?token',
            r'request[_-]?token'
        ]
        
        encontrados = []
        
        for req in self.requisicoes_post:
            request = req['request']
            
            # Procurar em headers
            for header in request.get('headers', []):
                name = header['name'].lower()
                for pattern in csrf_patterns:
                    if re.search(pattern, name):
                        encontrados.append({
                            'tipo': 'header',
                            'nome': header['name'],
                            'valor': header['value'][:50] + '...',
                            'url': request['url']
                        })
            
            # Procurar em POST data
            post_data = request.get('postData', {})
            params = post_data.get('params', [])
            for param in params:
                name = param['name'].lower()
                for pattern in csrf_patterns:
                    if re.search(pattern, name):
                        encontrados.append({
                            'tipo': 'payload',
                            'nome': param['name'],
                            'valor': param.get('value', '')[:50] + '...',
                            'url': request['url']
                        })
        
        if encontrados:
            print(f"\n✓ Encontrados {len(encontrados)} tokens CSRF potenciais:")
            for token in encontrados:
                print(f"\n  Tipo: {token['tipo']}")
                print(f"  Nome: {token['nome']}")
                print(f"  Valor: {token['valor']}")
                print(f"  URL: {token['url']}")
        else:
            print("\n⚠ Nenhum token CSRF óbvio detectado")
            print("Isso pode significar:")
            print("  - O sistema não usa CSRF tokens")
            print("  - Os tokens têm nomes não convencionais")
            print("  - É necessário análise manual")
    
    def listar_cookies(self):
        """Lista todos os cookies únicos encontrados"""
        print("\n" + "=" * 80)
        print("ANÁLISE: Cookies")
        print("=" * 80)
        
        print("\nCookies encontrados:")
        for cookie in sorted(self.cookies):
            print(f"  - {cookie}")
        
        # Identificar cookie de sessão mais provável
        sessao_provavel = [
            c for c in self.cookies
            if any(word in c.lower() for word in ['session', 'sess', 'phpsessid', 'jsessionid'])
        ]
        
        if sessao_provavel:
            print("\nCookies de sessão prováveis:")
            for cookie in sessao_provavel:
                print(f"  → {cookie}")
    
    def gerar_exemplo_curl(self):
        """Gera exemplo de comando cURL para requisição de histórico"""
        print("\n" + "=" * 80)
        print("EXEMPLO: Comando cURL")
        print("=" * 80)
        
        # Pegar primeira requisição de histórico
        historico_reqs = [
            req for req in self.requisicoes_post
            if 'disciplinashistorico' in req['request']['url'].lower()
        ]
        
        if not historico_reqs:
            print("⚠ Nenhuma requisição de histórico para gerar exemplo")
            return
        
        req = historico_reqs[0]
        request = req['request']
        
        print("\n```bash")
        print(f"curl '{request['url']}' \\")
        
        # Headers
        for header in request.get('headers', []):
            name = header['name']
            value = header['value']
            
            # Pular alguns headers
            if name.lower() in ['host', 'content-length', 'connection']:
                continue
            
            # Mascarar cookies
            if name.lower() == 'cookie':
                value = 'PHPSESSID=XXXXXXXXXX'
            
            print(f"  -H '{name}: {value}' \\")
        
        # POST data
        post_data = request.get('postData', {})
        if post_data:
            text = post_data.get('text', '')
            if text:
                # Limitar tamanho
                if len(text) > 200:
                    text = text[:200] + '...'
                print(f"  --data-raw '{text}'")
        
        print("```")
    
    def gerar_relatorio_completo(self):
        """Gera relatório completo da análise"""
        print("\n" + "╔" + "═" * 78 + "╗")
        print("║" + " RELATÓRIO DE ANÁLISE HAR - GEDUC ".center(78) + "║")
        print("╚" + "═" * 78 + "╝")
        
        self.listar_cookies()
        self.detectar_csrf()
        self.analisar_login()
        self.analisar_historico()
        self.gerar_exemplo_curl()
        
        print("\n" + "=" * 80)
        print("PRÓXIMOS PASSOS")
        print("=" * 80)
        print("""
1. Revisar as informações acima e documentar em:
   docs/RESULTADO_CAPTURA_GEDUC.md

2. Atualizar o script POC com as descobertas:
   scripts/poc_exportacao_geduc.py
   
3. Configurar credenciais de teste:
   set GEDUC_USER=seu_usuario
   set GEDUC_PASS=sua_senha

4. Executar POC atualizado:
   python scripts/poc_exportacao_geduc.py

5. Validar sucesso da integração
""")


def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python analisador_har.py <arquivo.har>")
        print("\nExemplo:")
        print('  python scripts/analisador_har.py "historico geduc/capturas/geduc.har"')
        sys.exit(1)
    
    arquivo = sys.argv[1]
    
    analisador = AnalisadorHAR(arquivo)
    
    if not analisador.carregar():
        sys.exit(1)
    
    analisador.filtrar_requisicoes()
    analisador.gerar_relatorio_completo()
    
    print("\n✓ Análise concluída!")


if __name__ == "__main__":
    main()
