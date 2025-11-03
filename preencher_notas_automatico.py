"""
Módulo para preencher automaticamente as notas na interface
quando o período estiver fechado no GEDUC
"""

import time
import re
import unicodedata
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from bs4 import BeautifulSoup
from tkinter import messagebox
import tkinter as tk


class PreenchimentoAutomaticoNotas:
    """
    Classe para detectar períodos fechados e preencher automaticamente
    as notas na interface de cadastro/edição
    """
    
    def __init__(self, driver, interface_notas):
        """
        Inicializa o preenchimento automático
        
        Args:
            driver: Instância do Selenium WebDriver
            interface_notas: Instância da InterfaceCadastroEdicaoNotas
        """
        self.driver = driver
        self.interface = interface_notas
        
    @staticmethod
    def normalizar_nome(nome):
        """
        Normaliza nome removendo acentuação e convertendo para maiúsculas
        para comparação com os nomes do GEDUC
        
        Args:
            nome: Nome com acentuação e formatação normal
            
        Returns:
            Nome normalizado (maiúsculas, sem acentuação)
        """
        if not nome:
            return ""
        
        # Remover sufixos de transferência (com ou sem espaços extras)
        # Padrões: "( Transferencia Externa )", "(Transferencia Externa)", etc.
        nome = re.sub(r'\s*\(\s*Transferencia\s+Externa\s*\)\s*$', '', nome, flags=re.IGNORECASE)
        nome = nome.strip()
        
        # Remover acentuação usando NFD (Normalization Form Canonical Decomposition)
        nfd = unicodedata.normalize('NFD', nome)
        nome_sem_acento = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
        
        # Converter para maiúsculas
        nome_normalizado = nome_sem_acento.upper()
        
        return nome_normalizado
    
    def detectar_alerta_periodo_fechado(self, timeout=3):
        """
        Detecta se apareceu o alerta de período fechado
        
        Returns:
            dict com 'fechado': bool e 'periodo': str (ex: "2º PERÍODO")
            ou None se não houver alerta
        """
        try:
            # Aguardar um pouco para o alert aparecer
            time.sleep(1)
            
            # Tentar detectar alert JavaScript
            try:
                alert = self.driver.switch_to.alert
                texto_alert = alert.text
                
                # Verificar se é o alerta de período fechado
                if "fechada" in texto_alert.lower() or "fechado" in texto_alert.lower():
                    # Extrair o período (1º, 2º, 3º ou 4º PERÍODO)
                    match = re.search(r'(\d+)º\s*PERÍODO', texto_alert, re.IGNORECASE)
                    if match:
                        numero_periodo = match.group(1)
                        
                        # Aceitar o alerta para continuar
                        alert.accept()
                        
                        print(f"✓ Detectado período fechado: {numero_periodo}º PERÍODO")
                        
                        return {
                            'fechado': True,
                            'periodo': numero_periodo,
                            'texto_completo': texto_alert
                        }
                else:
                    # Não é o alerta esperado, aceitar e retornar None
                    alert.accept()
                    return None
                    
            except NoAlertPresentException:
                # Não há alert, verificar se há modal/div de aviso
                html_content = self.driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Procurar por divs/modals com texto de período fechado
                textos_possiveis = soup.find_all(string=re.compile(r'fechad[oa]', re.IGNORECASE))
                
                for texto in textos_possiveis:
                    if "período" in texto.lower() or "periodo" in texto.lower():
                        match = re.search(r'(\d+)º\s*PERÍODO', texto, re.IGNORECASE)
                        if match:
                            numero_periodo = match.group(1)
                            
                            print(f"✓ Detectado período fechado (via HTML): {numero_periodo}º PERÍODO")
                            
                            # Tentar fechar modal se existir
                            try:
                                botao_ok = self.driver.find_element(By.XPATH, "//button[contains(text(), 'OK') or contains(text(), 'Fechar')]")
                                botao_ok.click()
                                time.sleep(0.5)
                            except:
                                pass
                            
                            return {
                                'fechado': True,
                                'periodo': numero_periodo,
                                'texto_completo': texto
                            }
                
                return None
                
        except Exception as e:
            print(f"✗ Erro ao detectar alerta: {e}")
            return None
    
    def extrair_notas_periodo_fechado(self):
        """
        Extrai as notas da página atual mesmo com período fechado
        
        Returns:
            dict com dados das notas ou None em caso de erro
        """
        try:
            # Aguardar carregamento da página
            time.sleep(2)
            
            # Obter HTML da página
            html_content = self.driver.page_source
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extrair turma selecionada
            turma_select = soup.find('select', {'name': 'IDTURMA'})
            turma_nome = "Desconhecida"
            if turma_select:
                turma_option = turma_select.find('option', {'selected': True})
                if turma_option:
                    turma_nome = turma_option.text.strip()
            
            # Extrair disciplina selecionada
            disciplina_select = soup.find('select', {'name': 'IDTURMASDISP'})
            disciplina_nome = "Desconhecida"
            if disciplina_select:
                disciplina_option = disciplina_select.find('option', {'selected': True})
                if disciplina_option:
                    disciplina_nome = disciplina_option.text.strip()
            
            # Extrair bimestre/período selecionado
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
                            bimestre = match.group(1)
            
            # Extrair alunos e notas da tabela
            alunos_notas = []
            tbody = soup.find('tbody', {'class': 'tdatagrid_body'})
            
            if tbody:
                rows = tbody.find_all('tr', {'class': ['tdatagrid_row_odd', 'tdatagrid_row_even']})
                
                for row in rows:
                    cells = row.find_all('td', {'class': 'tdatagrid_cell'})
                    
                    if len(cells) >= 2:
                        ordem_text = cells[0].text.strip()
                        nome_aluno_geduc_original = cells[1].text.strip()  # Nome original do GEDUC
                        nome_aluno_geduc = self.normalizar_nome(nome_aluno_geduc_original)  # Nome normalizado (remove sufixos)
                        
                        if ordem_text and nome_aluno_geduc and ordem_text.isdigit():
                            # Extrair notas individuais - mesmo método do automatizar_extracao_geduc.py
                            notas_individuais = []
                            
                            if len(cells) >= 3:
                                # IMPORTANTE: As notas estão DENTRO da célula cells[2] como múltiplos inputs
                                nota_inputs = cells[2].find_all('input', {'class': 'tfield'})
                                
                                for input_nota in nota_inputs:
                                    valor_nota = input_nota.get('value', '').strip()
                                    if valor_nota:
                                        try:
                                            nota_float = float(valor_nota.replace(',', '.'))
                                            notas_individuais.append(nota_float)
                                        except ValueError:
                                            pass
                            
                            # Calcular média (igual ao automatizar_extracao_geduc.py)
                            nota_final = None
                            if notas_individuais:
                                nota_final = sum(notas_individuais) / len(notas_individuais)
                            
                            alunos_notas.append({
                                'ordem': int(ordem_text),
                                'nome_geduc': nome_aluno_geduc,  # Nome normalizado do GEDUC
                                'nota': nota_final,
                                'notas_individuais': notas_individuais  # Para debug
                            })
            
            print(f"✓ Extraídos {len(alunos_notas)} alunos com notas")
            
            return {
                'turma': turma_nome,
                'disciplina': disciplina_nome,
                'bimestre': bimestre,
                'alunos': alunos_notas
            }
            
        except Exception as e:
            print(f"✗ Erro ao extrair notas: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def preencher_interface_automaticamente(self, dados_geduc):
        """
        Preenche automaticamente a interface com os dados extraídos do GEDUC
        
        Args:
            dados_geduc: Dicionário com turma, disciplina, bimestre e alunos
            
        Returns:
            dict com estatísticas do preenchimento
        """
        try:
            if not dados_geduc or not dados_geduc.get('alunos'):
                print("✗ Nenhum dado para preencher")
                return None
            
            # Verificar se a interface tem as entradas de notas carregadas
            if not hasattr(self.interface, 'entradas_notas') or not self.interface.entradas_notas:
                print("✗ Interface não tem entradas de notas carregadas")
                return None
            
            # Mapear alunos da interface (ID -> nome normalizado)
            alunos_interface = {}
            for aluno_id, entrada in self.interface.entradas_notas.items():
                # Obter nome do aluno na interface
                # O nome está armazenado na tabela
                for aluno_info in self.interface.alunos:
                    if aluno_info[0] == aluno_id:
                        nome_original = aluno_info[1]
                        nome_normalizado = self.normalizar_nome(nome_original)
                        alunos_interface[aluno_id] = {
                            'nome_original': nome_original,
                            'nome_normalizado': nome_normalizado,
                            'entrada': entrada
                        }
                        break
            
            # Preencher notas fazendo correspondência por nome normalizado
            preenchidos = 0
            nao_encontrados = []
            
            for aluno_geduc in dados_geduc['alunos']:
                nome_geduc = aluno_geduc['nome_geduc']
                nota = aluno_geduc['nota']
                notas_individuais = aluno_geduc.get('notas_individuais', [])
                
                if nota is None:
                    continue
                
                # Arredondar média primeiro (igual ao automatizar_extracao_geduc.py)
                # depois converter GEDUC (0-10) para interface (0-100)
                nota_arredondada = round(float(nota), 1)
                nota_interface = nota_arredondada * 10
                
                # Procurar aluno na interface com nome correspondente
                encontrado = False
                for aluno_id, info in alunos_interface.items():
                    if info['nome_normalizado'] == nome_geduc:
                        # Encontrou correspondência - preencher nota
                        entrada = info['entrada']
                        
                        # Limpar e preencher com nota convertida
                        entrada.delete(0, tk.END)
                        entrada.insert(0, str(nota_interface))
                        
                        preenchidos += 1
                        encontrado = True
                        
                        # Mostrar notas individuais para debug
                        if notas_individuais:
                            notas_str = ", ".join([str(n) for n in notas_individuais])
                            print(f"  ✓ {info['nome_original']}: [{notas_str}] → média {nota:.2f} (GEDUC) → {nota_interface:.1f} (Interface)")
                        else:
                            print(f"  ✓ {info['nome_original']}: {nota} (GEDUC) → {nota_interface} (Interface)")
                        break
                
                if not encontrado:
                    nao_encontrados.append(nome_geduc)
            
            # Atualizar estatísticas da interface
            if hasattr(self.interface, 'atualizar_estatisticas'):
                self.interface.atualizar_estatisticas()
            
            # Retornar estatísticas
            resultado = {
                'total_geduc': len(dados_geduc['alunos']),
                'total_interface': len(alunos_interface),
                'preenchidos': preenchidos,
                'nao_encontrados': nao_encontrados
            }
            
            print(f"\n✓ Preenchimento concluído:")
            print(f"  - Total no GEDUC: {resultado['total_geduc']}")
            print(f"  - Total na interface: {resultado['total_interface']}")
            print(f"  - Preenchidos: {resultado['preenchidos']}")
            if nao_encontrados:
                print(f"  - Não encontrados: {len(nao_encontrados)}")
                for nome in nao_encontrados:
                    print(f"    • {nome}")
            
            return resultado
            
        except Exception as e:
            print(f"✗ Erro ao preencher interface: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def processar_pagina_notas(self):
        """
        Método principal que:
        1. Detecta se o período está fechado
        2. Extrai as notas
        3. Preenche a interface automaticamente
        
        Returns:
            True se processou com sucesso, False caso contrário
        """
        try:
            print("\n" + "="*60)
            print("VERIFICANDO PERÍODO E EXTRAINDO NOTAS")
            print("="*60)
            
            # Detectar alerta de período fechado
            alerta = self.detectar_alerta_periodo_fechado()
            
            if alerta and alerta['fechado']:
                print(f"\n⚠️  PERÍODO FECHADO DETECTADO: {alerta['periodo']}º PERÍODO")
            else:
                print("→ Período não está fechado - extraindo notas normalmente")
            
            print("→ Extraindo notas da página...")
            
            # Extrair notas da página (independente de alerta)
            dados_geduc = self.extrair_notas_periodo_fechado()
            
            if dados_geduc:
                print(f"\n→ Dados extraídos:")
                print(f"  - Turma: {dados_geduc['turma']}")
                print(f"  - Disciplina: {dados_geduc['disciplina']}")
                print(f"  - Bimestre: {dados_geduc['bimestre']}º")
                print(f"  - Alunos: {len(dados_geduc['alunos'])}")
                
                # Perguntar ao usuário se deseja preencher automaticamente
                mensagem_titulo = "Período Fechado - Preenchimento Automático" if (alerta and alerta['fechado']) else "Preenchimento Automático"
                mensagem_texto = ""
                
                if alerta and alerta['fechado']:
                    mensagem_texto = f"⚠️  Período fechado detectado: {alerta['periodo']}º PERÍODO\n\n"
                
                mensagem_texto += f"Foram encontrados {len(dados_geduc['alunos'])} alunos com notas.\n\n"
                mensagem_texto += "Deseja preencher automaticamente a interface de notas?"
                
                resposta = messagebox.askyesno(
                    mensagem_titulo,
                    mensagem_texto,
                    icon='question'
                )
                
                if resposta:
                    print("\n→ Preenchendo interface automaticamente...")
                    resultado = self.preencher_interface_automaticamente(dados_geduc)
                    
                    if resultado:
                        # Exibir resultado apenas no console (sem messagebox)
                        print(f"\n✓ Preenchimento concluído!")
                        print(f"  Total de notas preenchidas: {resultado['preenchidos']}")
                        print(f"  Total de alunos na interface: {resultado['total_interface']}")
                        
                        if resultado['nao_encontrados']:
                            print(f"\n  ⚠️ Alunos não encontrados ({len(resultado['nao_encontrados'])}):")
                            for nome in resultado['nao_encontrados'][:5]:  # Mostrar no máximo 5
                                print(f"    • {nome}")
                            if len(resultado['nao_encontrados']) > 5:
                                print(f"    ... e mais {len(resultado['nao_encontrados']) - 5}")
                        
                        return True
                    else:
                        messagebox.showerror("Erro", "Não foi possível preencher a interface.")
                        return False
                else:
                    print("→ Preenchimento automático cancelado pelo usuário")
                    return False
            else:
                messagebox.showerror("Erro", "Não foi possível extrair os dados do GEDUC.")
                return False
                
        except Exception as e:
            print(f"✗ Erro ao processar página: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro ao processar página de notas:\n{str(e)}")
            return False


def criar_preenchimento_automatico(driver, interface_notas):
    """
    Função auxiliar para criar instância de PreenchimentoAutomaticoNotas
    
    Args:
        driver: Instância do Selenium WebDriver
        interface_notas: Instância da InterfaceCadastroEdicaoNotas
        
    Returns:
        Instância de PreenchimentoAutomaticoNotas
    """
    return PreenchimentoAutomaticoNotas(driver, interface_notas)
