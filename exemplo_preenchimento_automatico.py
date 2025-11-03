"""
Exemplo de uso do preenchimento automático de notas
quando o período está fechado no GEDUC
"""

import tkinter as tk
from automatizar_extracao_geduc import AutomacaoGEDUC
from InterfaceCadastroEdicaoNotas import InterfaceCadastroEdicaoNotas
from preencher_notas_automatico import criar_preenchimento_automatico
import time


def exemplo_preenchimento_com_periodo_fechado():
    """
    Exemplo completo de como usar o preenchimento automático
    quando o sistema detecta que o período está fechado
    """
    
    print("="*70)
    print("EXEMPLO: PREENCHIMENTO AUTOMÁTICO COM PERÍODO FECHADO")
    print("="*70)
    print()
    print("Este exemplo demonstra:")
    print("1. Login no GEDUC")
    print("2. Navegação para página de registro de notas")
    print("3. Detecção de período fechado")
    print("4. Extração automática das notas")
    print("5. Preenchimento da interface local")
    print()
    print("="*70)
    
    # Solicitar credenciais
    usuario = input("\nUsuário GEDUC: ").strip()
    senha = input("Senha GEDUC: ").strip()
    
    if not usuario or not senha:
        print("✗ Usuário e senha são obrigatórios!")
        return
    
    # Criar instância do automação
    automacao = AutomacaoGEDUC(headless=False)
    
    try:
        # Iniciar navegador
        print("\n→ Iniciando navegador...")
        if not automacao.iniciar_navegador():
            print("✗ Falha ao iniciar navegador")
            return
        
        # Fazer login
        print("→ Fazendo login...")
        if not automacao.fazer_login(usuario, senha, timeout_recaptcha=120):
            print("✗ Falha no login")
            return
        
        # Acessar registro de notas
        print("→ Acessando registro de notas...")
        if not automacao.acessar_registro_notas():
            print("✗ Falha ao acessar registro de notas")
            return
        
        # Neste ponto, você precisa navegar até a turma/disciplina/bimestre desejado
        print("\n" + "="*70)
        print("NAVEGAÇÃO MANUAL NECESSÁRIA")
        print("="*70)
        print()
        print("Agora você precisa:")
        print("1. Selecionar a TURMA no dropdown")
        print("2. Selecionar a DISCIPLINA no dropdown")
        print("3. Selecionar o BIMESTRE/PERÍODO")
        print("4. Clicar em 'Exibir Alunos' ou botão equivalente")
        print()
        print("Quando o sistema mostrar o alerta de período fechado,")
        print("pressione ENTER aqui para iniciar o preenchimento automático...")
        print("="*70)
        
        input("\nPressione ENTER quando estiver pronto...")
        
        # Criar janela principal do Tkinter (necessária para a interface)
        root = tk.Tk()
        root.withdraw()  # Esconder janela principal
        
        # Criar interface de notas
        print("\n→ Criando interface de cadastro de notas...")
        interface_notas = InterfaceCadastroEdicaoNotas()
        
        # Aguardar interface carregar
        print("→ Aguardando interface carregar...")
        print("   ⚠️  Configure a turma, disciplina e bimestre na interface!")
        print("   Pressione ENTER quando a interface estiver carregada...")
        input()
        
        # Criar instância do preenchimento automático
        print("\n→ Iniciando preenchimento automático...")
        preenchedor = criar_preenchimento_automatico(
            driver=automacao.driver,
            interface_notas=interface_notas
        )
        
        # Processar página e preencher automaticamente
        sucesso = preenchedor.processar_pagina_notas()
        
        if sucesso:
            print("\n✓ Processo concluído com sucesso!")
            print("→ Verifique a interface de notas")
            print("→ Se estiver correto, clique em 'Salvar Notas'")
        else:
            print("\n✗ Processo não foi concluído")
        
        # Manter janela aberta
        print("\nFechando o navegador em 10 segundos...")
        print("(Pressione Ctrl+C para cancelar)")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n\n→ Processo cancelado pelo usuário")
    
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Fechar navegador
        print("\n→ Fechando navegador...")
        automacao.fechar()
        print("✓ Concluído")


def exemplo_simplificado():
    """
    Exemplo simplificado assumindo que você já está na página
    de notas do GEDUC com período fechado
    """
    
    print("="*70)
    print("EXEMPLO SIMPLIFICADO: PREENCHIMENTO AUTOMÁTICO")
    print("="*70)
    print()
    print("PRÉ-REQUISITOS:")
    print("1. Você já está logado no GEDUC")
    print("2. Já navegou até a página de registro de notas")
    print("3. Já selecionou turma, disciplina e bimestre")
    print("4. O alerta de período fechado apareceu")
    print()
    print("="*70)
    
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    
    # Conectar ao navegador já aberto (se você configurar o remote debugging)
    # Ou iniciar novo navegador
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✓ Conectado ao navegador existente")
    except:
        print("✗ Não foi possível conectar ao navegador")
        print("   Inicie o Chrome com: chrome.exe --remote-debugging-port=9222")
        return
    
    # Criar interface de notas
    root = tk.Tk()
    root.withdraw()
    
    print("\n→ Criando interface de cadastro de notas...")
    interface_notas = InterfaceCadastroEdicaoNotas()
    
    print("→ Configure a turma, disciplina e bimestre na interface")
    print("   Pressione ENTER quando estiver pronto...")
    input()
    
    # Criar preenchedor
    preenchedor = criar_preenchimento_automatico(driver, interface_notas)
    
    # Processar
    print("\n→ Processando página de notas...")
    preenchedor.processar_pagina_notas()
    
    print("\n✓ Processo concluído!")


if __name__ == "__main__":
    print("\nEscolha o exemplo:")
    print("1 - Exemplo completo (faz login e tudo)")
    print("2 - Exemplo simplificado (já está logado)")
    print()
    
    opcao = input("Opção (1 ou 2): ").strip()
    
    if opcao == "1":
        exemplo_preenchimento_com_periodo_fechado()
    elif opcao == "2":
        exemplo_simplificado()
    else:
        print("Opção inválida!")
