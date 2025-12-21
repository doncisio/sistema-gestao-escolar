"""
Script para extrair dados de mapeamento do GEDUC
Busca e salva em arquivos JSON:
- Escolas (instituições) com IDs
- Disciplinas com IDs
- Cursos com IDs
- Currículos com IDs
- Séries/Turmas com IDs
- Outros dados necessários para mapeamento

Uso:
    python scripts/extrair_dados_mapeamento_geduc.py
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.importadores.geduc import AutomacaoGEDUC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
from bs4 import BeautifulSoup


class ExtratorDadosGEDUC(AutomacaoGEDUC):
    """
    Extensor de AutomacaoGEDUC para extrair dados de mapeamento
    """
    
    def __init__(self, headless=False):
        super().__init__(headless=headless)
        self.dados_mapeamento = {
            'data_extracao': datetime.now().isoformat(),
            'escolas': [],
            'disciplinas': [],
            'cursos': [],
            'curriculos': [],
            'series': [],
            'turnos': [],
            'tipos_avaliacao': []
        }
    
    def extrair_escolas(self):
        """
        Extrai lista de escolas (instituições) do GEDUC
        Acessa página de cadastro ou lista de escolas
        """
        print("\n📚 Extraindo escolas...")
        
        try:
            # Tentar acessar página de escolas/instituições
            urls_possiveis = [
                "/index.php?class=InstituicaoList",
                "/index.php?class=EscolaList",
                "/index.php?class=UnidadeList",
                "/index.php?class=InstituicaoForm",
            ]
            
            for url in urls_possiveis:
                try:
                    self.driver.get(f"{self.url_base}{url}")
                    time.sleep(2)
                    
                    # Verificar se carregou página válida
                    if "Instituição" in self.driver.page_source or "Escola" in self.driver.page_source:
                        print(f"  ✓ Acessou: {url}")
                        break
                except:
                    continue
            
            # Se houver campo de Tipo de Escola, selecionar explicitamente "Escolas da Rede" (valor 1)
            try:
                tipo_opts = None
                for t in ['TIPOESCOLA', 'TIPO_ESCOLA', 'IDTIPOESCOLA', 'TIPO']:
                    try:
                        tipo_opts = self.obter_opcoes_select(t)
                        if tipo_opts:
                            # procurar opção com texto claro
                            escolha = None
                            for o in tipo_opts:
                                txt = (o.get('text') or '').upper()
                                if 'ESCOLAS DA REDE' in txt or ('ESCOLAS' in txt and 'REDE' in txt) or 'REDE' in txt:
                                    escolha = o['value']
                                    break
                            # se não encontrou por texto, tentar valor '1'
                            if not escolha:
                                for o in tipo_opts:
                                    if str(o.get('value')) == '1':
                                        escolha = o['value']
                                        break
                            if escolha:
                                try:
                                    self.selecionar_opcao(t, escolha)
                                    time.sleep(1)
                                    print(f"  ✓ Selecionado '{t}' = {escolha} (Escolas da Rede)")
                                except Exception:
                                    pass
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # MÉTODO 1: Tentar extrair de select/dropdown (priorizar IDINSTITUICAO)
            selects_possiveis = ['IDINSTITUICAO', 'IDESCOLA', 'IDUNIDADE', 'instituicao_id']
            
            for select_name in selects_possiveis:
                try:
                    opcoes = self.obter_opcoes_select(select_name)
                    if opcoes:
                        # Validar se as opções parecem ser nomes de escolas
                        textos = [opt['text'].upper() for opt in opcoes if opt.get('text')]
                        keywords = ['ESCOLA', 'INSTITUTO', 'CENTRO', 'CRECHE', 'EMEF', 'E.M.', 'CEI', 'C.E.I']
                        matches = sum(1 for t in textos if any(k in t for k in keywords))
                        proporcao = matches / max(1, len(textos))

                        if proporcao < 0.05:
                            # Provavelmente não são escolas (p.ex. nomes de pessoas). Tentar próximo select.
                            print(f"  ⚠ Select '{select_name}' encontrado, mas opções não parecem ser nomes de escolas (match={proporcao:.2f}). Ignorando.")
                            continue

                        print(f"  ✓ Encontrou {len(opcoes)} escolas no select '{select_name}'")
                        self.dados_mapeamento['escolas'] = [
                            {
                                'id_geduc': int(opt['value']),
                                'nome': opt['text']
                            }
                            for opt in opcoes
                        ]
                        return True
                except:
                    continue
            
            # MÉTODO 2: Tentar extrair de tabela
            try:
                tabela = self.driver.find_element(By.TAG_NAME, "table")
                linhas = tabela.find_elements(By.TAG_NAME, "tr")
                
                for linha in linhas[1:]:  # Pular cabeçalho
                    colunas = linha.find_elements(By.TAG_NAME, "td")
                    if len(colunas) >= 2:
                        # Tentar extrair ID do link de edição
                        links = linha.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            href = link.get_attribute('href')
                            if href and ('edit' in href.lower() or 'form' in href.lower()):
                                # Extrair ID da URL
                                import re
                                match = re.search(r'[?&](?:IDINSTITUICAO|IDESCOLA|id)=(\d+)', href)
                                if match:
                                    id_escola = int(match.group(1))
                                    nome_escola = colunas[0].text.strip() or colunas[1].text.strip()
                                    
                                    self.dados_mapeamento['escolas'].append({
                                        'id_geduc': id_escola,
                                        'nome': nome_escola
                                    })
                                    break
                
                if self.dados_mapeamento['escolas']:
                    print(f"  ✓ Extraiu {len(self.dados_mapeamento['escolas'])} escolas da tabela")
                    return True
            except:
                pass

            # MÉTODO 3: Fallback com BeautifulSoup - procurar links com ID na URL
            try:
                import re
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                encontrados = {}
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    match = re.search(r'[?&](?:IDINSTITUICAO|IDESCOLA|id)=(\d+)', href, re.IGNORECASE)
                    if match:
                        id_escola = int(match.group(1))
                        nome = (a.get_text(strip=True) or '').strip()
                        if not nome:
                            tr = a.find_parent('tr')
                            if tr:
                                tds = tr.find_all('td')
                                if tds:
                                    nome = tds[0].get_text(strip=True)
                        if nome and id_escola not in encontrados:
                            encontrados[id_escola] = nome

                if encontrados:
                    for idv, nomev in encontrados.items():
                        self.dados_mapeamento['escolas'].append({'id_geduc': idv, 'nome': nomev})
                    print(f"  ✓ Extraiu {len(self.dados_mapeamento['escolas'])} escolas via fallback de links")
                    return True
            except Exception:
                pass

            # MÉTODO 4: Tentar via fluxo Registrar Notas (menu Secretaria > Gerar Historico > selecionar aluno > Registrar Notas)
            try:
                print("  → Tentando fluxo via 'AlunosHistoricoManualList' -> Selecionar -> Registrar Notas...")
                # 1) Abrir lista de alunos (manual)
                self.driver.get(f"{self.url_base}/index.php?class=AlunosHistoricoManualList")
                time.sleep(2)

                # 2) Encontrar primeiro botão/link 'Selecionar' que leva ao HistoricoAcadList (ou equivalente)
                selecionado = False
                try:
                    links = self.driver.find_elements(By.TAG_NAME, 'a')
                    for a in links:
                        href = (a.get_attribute('href') or '')
                        txt = (a.text or '').strip()
                        if 'HistoricoAcadList' in href or 'onReload' in href or txt.lower().startswith('selecion'):
                            try:
                                a.click()
                                selecionado = True
                                time.sleep(2)
                                break
                            except Exception:
                                # tentar navegar diretamente pelo href
                                try:
                                    if href:
                                        self.driver.get(href)
                                        selecionado = True
                                        time.sleep(2)
                                        break
                                except Exception:
                                    continue
                except Exception:
                    pass

                if not selecionado:
                    # não conseguiu selecionar aluno; fallback para RegNotasForm direto
                    self.driver.get(f"{self.url_base}/index.php?class=RegNotasForm")
                    time.sleep(2)

                # 3) Procurar link/ícone 'Registrar Notas' (escolasHistorico onEdit) e navegar
                try:
                    anchors = self.driver.find_elements(By.TAG_NAME, 'a')
                    for a in anchors:
                        href = (a.get_attribute('href') or '')
                        if 'class=escolasHistorico' in href and ('method=onEdit' in href or 'Registrar' in (a.get_attribute('title') or '')):
                            # navegar diretamente pela URL relativa (mais confiável que click em ícone)
                            try:
                                if href.startswith('http'):
                                    target = href
                                else:
                                    target = f"{self.url_base}/{href.lstrip('./')}"
                                self.driver.get(target)
                                time.sleep(2)
                                break
                            except Exception:
                                try:
                                    a.click()
                                    time.sleep(2)
                                    break
                                except Exception:
                                    continue
                except Exception:
                    pass

                # 4) Selecionar explicitamente 'TIPOESCOLA' = Escolas da Rede (valor '1') se presente
                try:
                    tipo_opts = self.obter_opcoes_select('TIPOESCOLA') or self.obter_opcoes_select('TIPO_ESCOLA')
                    if tipo_opts:
                        escolha = None
                        for o in tipo_opts:
                            txt = (o.get('text') or '').upper()
                            if 'ESCOLAS DA REDE' in txt or ('ESCOLAS' in txt and 'REDE' in txt) or 'REDE' in txt:
                                escolha = o['value']
                                break
                        if not escolha:
                            for o in tipo_opts:
                                if str(o.get('value')) == '1':
                                    escolha = o['value']
                                    break
                        if escolha:
                            try:
                                self.selecionar_opcao('TIPOESCOLA', escolha)
                                time.sleep(1)
                                print(f"  ✓ Selecionado TIPOESCOLA = {escolha}")
                            except Exception:
                                pass
                except Exception:
                    pass

                # 5) Extrair select de escolas (nome 'IDINSTITUICAO' ou 'IDESCOLA')
                for select_name in ['IDINSTITUICAO', 'IDESCOLA', 'IDUNIDADE', 'instituicao_id']:
                    try:
                        opcoes = self.obter_opcoes_select(select_name)
                        if opcoes:
                            print(f"  ✓ Encontrou {len(opcoes)} escolas no select '{select_name}' via fluxo AlunosHistoricoManualList/Registrar Notas")
                            self.dados_mapeamento['escolas'] = [
                                {'id_geduc': int(opt['value']), 'nome': opt['text']}
                                for opt in opcoes
                            ]
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            
            print("  ⚠ Não foi possível extrair escolas automaticamente")
            print("  → Tente acessar manualmente e verificar a estrutura da página")
            # Salvar HTML da página para análise manual
            try:
                caminho_html = Path('config/ultima_pagina_instituicao.html')
                with open(caminho_html, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"  ⇢ HTML da página salvo em: {caminho_html}")
            except Exception:
                pass
            return False
            
        except Exception as e:
            print(f"  ✗ Erro ao extrair escolas: {e}")
            return False
    
    def extrair_disciplinas(self):
        """
        Extrai lista de disciplinas do GEDUC
        """
        print("\n📖 Extraindo disciplinas...")
        
        try:
            # Tentar acessar página de disciplinas
            urls_possiveis = [
                "/index.php?class=DisciplinaList",
                "/index.php?class=DisciplinasForm",
                "/index.php?class=CadastroDisciplinas",
            ]
            
            for url in urls_possiveis:
                try:
                    self.driver.get(f"{self.url_base}{url}")
                    time.sleep(2)
                    
                    if "Disciplina" in self.driver.page_source:
                        print(f"  ✓ Acessou: {url}")
                        break
                except:
                    continue
            
            # MÉTODO 1: Extrair de select
            selects_possiveis = ['IDDISCIPLINA', 'IDTURMASDISP', 'disciplina_id']
            
            for select_name in selects_possiveis:
                try:
                    opcoes = self.obter_opcoes_select(select_name)
                    if opcoes:
                        print(f"  ✓ Encontrou {len(opcoes)} disciplinas no select '{select_name}'")
                        self.dados_mapeamento['disciplinas'] = [
                            {
                                'id_geduc': int(opt['value']),
                                'nome': opt['text']
                            }
                            for opt in opcoes
                        ]
                        return True
                except:
                    continue
            
            # MÉTODO 2: Extrair de tabela
            try:
                tabela = self.driver.find_element(By.TAG_NAME, "table")
                linhas = tabela.find_elements(By.TAG_NAME, "tr")
                
                for linha in linhas[1:]:
                    colunas = linha.find_elements(By.TAG_NAME, "td")
                    if len(colunas) >= 2:
                        links = linha.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            href = link.get_attribute('href')
                            if href and ('edit' in href.lower() or 'form' in href.lower()):
                                import re
                                match = re.search(r'[?&](?:IDDISCIPLINA|id)=(\d+)', href)
                                if match:
                                    id_disciplina = int(match.group(1))
                                    nome_disciplina = colunas[0].text.strip() or colunas[1].text.strip()
                                    
                                    self.dados_mapeamento['disciplinas'].append({
                                        'id_geduc': id_disciplina,
                                        'nome': nome_disciplina
                                    })
                                    break
                
                if self.dados_mapeamento['disciplinas']:
                    print(f"  ✓ Extraiu {len(self.dados_mapeamento['disciplinas'])} disciplinas da tabela")
                    return True
            except:
                pass
            
            # MÉTODO 3: Acessar página de notas e extrair de lá
            try:
                print("  → Tentando extrair de página de notas...")
                self.driver.get(f"{self.url_base}/index.php?class=CadastroNotasForm")
                time.sleep(3)
                
                # Tentar selecionar uma turma primeiro
                try:
                    turmas = self.obter_opcoes_select('IDTURMA')
                    if turmas:
                        self.selecionar_opcao('IDTURMA', turmas[0]['value'])
                        time.sleep(2)
                except:
                    pass
                
                # Agora tentar extrair disciplinas
                opcoes = self.obter_opcoes_select('IDTURMASDISP')
                if opcoes:
                    print(f"  ✓ Encontrou {len(opcoes)} disciplinas na página de notas")
                    self.dados_mapeamento['disciplinas'] = [
                        {
                            'id_geduc': int(opt['value']),
                            'nome': opt['text']
                        }
                        for opt in opcoes
                    ]
                    return True
            except:
                pass
            
            print("  ⚠ Não foi possível extrair disciplinas automaticamente")
            return False
            
        except Exception as e:
            print(f"  ✗ Erro ao extrair disciplinas: {e}")
            return False
    
    def extrair_cursos(self):
        """
        Extrai lista de cursos do GEDUC
        """
        print("\n🎓 Extraindo cursos...")
        
        try:
            urls_possiveis = [
                "/index.php?class=CursoList",
                "/index.php?class=CursosForm",
                "/index.php?class=DisciplinasHistorico",
            ]
            
            for url in urls_possiveis:
                try:
                    self.driver.get(f"{self.url_base}{url}")
                    time.sleep(2)
                    
                    if "Curso" in self.driver.page_source:
                        print(f"  ✓ Acessou: {url}")
                        break
                except:
                    continue
            
            # Extrair de select
            selects_possiveis = ['IDCURSO', 'curso_id', 'CURSO']
            
            for select_name in selects_possiveis:
                try:
                    opcoes = self.obter_opcoes_select(select_name)
                    if opcoes:
                        print(f"  ✓ Encontrou {len(opcoes)} cursos no select '{select_name}'")
                        self.dados_mapeamento['cursos'] = [
                            {
                                'id_geduc': int(opt['value']),
                                'nome': opt['text']
                            }
                            for opt in opcoes
                        ]
                        return True
                except:
                    continue
            
            print("  ⚠ Não foi possível extrair cursos")
            return False
            
        except Exception as e:
            print(f"  ✗ Erro ao extrair cursos: {e}")
            return False
    
    def extrair_curriculos(self):
        """
        Extrai lista de currículos do GEDUC
        """
        print("\n📋 Extraindo currículos...")
        
        try:
            # Acessar página de histórico onde aparece currículo
            self.driver.get(f"{self.url_base}/index.php?class=DisciplinasHistorico")
            time.sleep(2)
            
            # Extrair de select
            selects_possiveis = ['IDCURRICULO', 'curriculo_id', 'CURRICULO']
            
            for select_name in selects_possiveis:
                try:
                    opcoes = self.obter_opcoes_select(select_name)
                    if opcoes:
                        print(f"  ✓ Encontrou {len(opcoes)} currículos no select '{select_name}'")
                        self.dados_mapeamento['curriculos'] = [
                            {
                                'id_geduc': int(opt['value']),
                                'nome': opt['text']
                            }
                            for opt in opcoes
                        ]
                        return True
                except:
                    continue
            
            print("  ⚠ Não foi possível extrair currículos")
            return False
            
        except Exception as e:
            print(f"  ✗ Erro ao extrair currículos: {e}")
            return False
    
    def extrair_series(self):
        """
        Extrai lista de séries/anos do GEDUC
        """
        print("\n📚 Extraindo séries...")
        
        try:
            # Acessar página de turmas
            self.driver.get(f"{self.url_base}/index.php?class=TurmaList")
            time.sleep(2)
            
            # Extrair de select
            selects_possiveis = ['IDSERIE', 'serie_id', 'SERIE']
            
            for select_name in selects_possiveis:
                try:
                    opcoes = self.obter_opcoes_select(select_name)
                    if opcoes:
                        print(f"  ✓ Encontrou {len(opcoes)} séries no select '{select_name}'")
                        self.dados_mapeamento['series'] = [
                            {
                                'id_geduc': int(opt['value']),
                                'nome': opt['text']
                            }
                            for opt in opcoes
                        ]
                        return True
                except:
                    continue
            
            print("  ⚠ Não foi possível extrair séries")
            return False
            
        except Exception as e:
            print(f"  ✗ Erro ao extrair séries: {e}")
            return False
    
    def extrair_turnos(self):
        """
        Extrai lista de turnos do GEDUC
        """
        print("\n🕐 Extraindo turnos...")
        
        try:
            selects_possiveis = ['IDTURNO', 'turno_id', 'TURNO']
            
            for select_name in selects_possiveis:
                try:
                    opcoes = self.obter_opcoes_select(select_name)
                    if opcoes:
                        print(f"  ✓ Encontrou {len(opcoes)} turnos no select '{select_name}'")
                        self.dados_mapeamento['turnos'] = [
                            {
                                'id_geduc': int(opt['value']),
                                'nome': opt['text']
                            }
                            for opt in opcoes
                        ]
                        return True
                except:
                    continue
            
            print("  ⚠ Não foi possível extrair turnos")
            return False
            
        except Exception as e:
            print(f"  ✗ Erro ao extrair turnos: {e}")
            return False
    
    def extrair_todos_dados(self):
        """
        Executa todas as extrações
        """
        print("\n" + "="*60)
        print("🔍 EXTRAÇÃO DE DADOS DE MAPEAMENTO DO GEDUC")
        print("="*60)
        
        # Extrair cada tipo de dado
        self.extrair_escolas()
        self.extrair_disciplinas()
        self.extrair_cursos()
        self.extrair_curriculos()
        self.extrair_series()
        self.extrair_turnos()
        
        print("\n" + "="*60)
        print("📊 RESUMO DA EXTRAÇÃO")
        print("="*60)
        print(f"  Escolas:      {len(self.dados_mapeamento['escolas'])}")
        print(f"  Disciplinas:  {len(self.dados_mapeamento['disciplinas'])}")
        print(f"  Cursos:       {len(self.dados_mapeamento['cursos'])}")
        print(f"  Currículos:   {len(self.dados_mapeamento['curriculos'])}")
        print(f"  Séries:       {len(self.dados_mapeamento['series'])}")
        print(f"  Turnos:       {len(self.dados_mapeamento['turnos'])}")
        print("="*60)
    
    def salvar_dados(self, arquivo_saida=None):
        """
        Salva dados extraídos em arquivo JSON
        """
        if arquivo_saida is None:
            # Criar nome com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo_saida = f"config/mapeamento_geduc_{timestamp}.json"
        
        # Garantir que diretório existe
        os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)
        
        # Salvar JSON
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(self.dados_mapeamento, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Dados salvos em: {arquivo_saida}")
        
        # Também salvar versão "latest"
        arquivo_latest = "config/mapeamento_geduc_latest.json"
        with open(arquivo_latest, 'w', encoding='utf-8') as f:
            json.dump(self.dados_mapeamento, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Cópia salva em: {arquivo_latest}")
        
        return arquivo_saida


def main():
    """
    Função principal
    """
    print("\n" + "="*60)
    print("🌐 EXTRATOR DE DADOS DE MAPEAMENTO DO GEDUC")
    print("="*60)
    print("\nEste script irá:")
    print("  1. Fazer login no GEDUC")
    print("  2. Navegar pelas páginas de cadastro")
    print("  3. Extrair IDs e nomes de:")
    print("     • Escolas (instituições)")
    print("     • Disciplinas")
    print("     • Cursos")
    print("     • Currículos")
    print("     • Séries")
    print("     • Turnos")
    print("  4. Salvar tudo em arquivo JSON")
    print("\n" + "="*60)
    
    # Solicitar credenciais
    usuario = input("\n👤 Usuário GEDUC: ").strip()
    
    if not usuario:
        print("❌ Usuário não fornecido. Encerrando.")
        return
    
    import getpass
    senha = getpass.getpass("🔐 Senha GEDUC: ")
    
    if not senha:
        print("❌ Senha não fornecida. Encerrando.")
        return
    
    # Perguntar se quer modo headless
    headless_input = input("\n🖥️  Executar sem abrir navegador? (s/N): ").strip().lower()
    headless = headless_input == 's'
    
    # Criar extrator
    extrator = ExtratorDadosGEDUC(headless=headless)
    
    try:
        # Iniciar navegador
        print("\n🌐 Iniciando navegador...")
        extrator.iniciar_navegador()
        
        # Fazer login
        print("🔐 Fazendo login...")
        if not extrator.fazer_login(usuario, senha):
            print("❌ Falha no login. Encerrando.")
            return
        
        print("✅ Login realizado com sucesso!")
        
        # Extrair todos os dados
        extrator.extrair_todos_dados()
        
        # Salvar
        arquivo = extrator.salvar_dados()
        
        print("\n" + "="*60)
        print("✅ EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print(f"\n📁 Arquivo gerado: {arquivo}")
        print("\n💡 Próximos passos:")
        print("  1. Abra o arquivo JSON gerado")
        print("  2. Compare IDs do GEDUC com IDs do sistema local")
        print("  3. Crie tabela de mapeamento ou atualize config")
        print("  4. Use esse mapeamento no exportador")
        print("\n" + "="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante extração: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Fechar navegador
        print("\n🔒 Fechando navegador...")
        extrator.fechar()


if __name__ == "__main__":
    main()
