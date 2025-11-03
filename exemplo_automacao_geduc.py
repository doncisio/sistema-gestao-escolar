"""
Exemplo simples de uso da automação do GEDUC
Execute este arquivo para testar a extração de notas
"""

from automatizar_extracao_geduc import AutomacaoGEDUC
import sys
import os
import glob

def exemplo_uso_basico():
    """
    Exemplo básico: extrai notas do 1º bimestre
    """
    print("="*70)
    print("EXEMPLO DE USO - AUTOMAÇÃO GEDUC")
    print("="*70)
    print()
    
    # Solicitar credenciais
    usuario = input("Digite seu usuário do GEDUC: ").strip()
    senha = input("Digite sua senha: ").strip()
    
    if not usuario or not senha:
        print("✗ Erro: Usuário e senha são obrigatórios!")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("INICIANDO EXTRAÇÃO")
    print("="*70 + "\n")
    
    # Criar instância da automação
    automacao = AutomacaoGEDUC(headless=False)  # headless=True para não mostrar navegador
    
    try:
        # 1. Iniciar navegador
        print("→ Iniciando navegador Chrome...")
        if not automacao.iniciar_navegador():
            print("✗ Não foi possível iniciar o navegador")
            sys.exit(1)
        
        # 2. Fazer login
        print("\n→ Fazendo login no GEDUC...")
        if not automacao.fazer_login(usuario, senha):
            print("✗ Login falhou - verifique suas credenciais")
            automacao.fechar()
            sys.exit(1)
        
        print("✓ Login realizado com sucesso!")
        
        # 3. Extrair notas
        print("\n→ Extraindo notas...")
        print("  (Extraindo apenas do 1º bimestre para este exemplo)")
        print("  (Para extrair todos os bimestres, use: bimestres=[1, 2, 3, 4])")
        print()
        
        def callback_progresso(processadas, total):
            """Mostra progresso da extração"""
            percentual = (processadas / total * 100) if total > 0 else 0
            print(f"  Progresso: {processadas}/{total} ({percentual:.1f}%)")
        
        # Extrair apenas 1º bimestre (para teste rápido)
        if not automacao.extrair_todas_notas(
            bimestres=[1],  # Apenas 1º bimestre
            diretorio_saida="notas_extraidas",
            callback_progresso=callback_progresso
        ):
            print("✗ Erro durante extração")
            automacao.fechar()
            sys.exit(1)
        
        # Arquivos já foram salvos automaticamente
        print(f"\n✓ Sucesso! Arquivos criados em: notas_extraidas/")
        print(f"  Formato: 1 arquivo por turma/bimestre")
        print(f"  Cada arquivo contém múltiplas planilhas (uma por disciplina)")
        
        # Listar alguns arquivos criados
        import glob
        arquivos = glob.glob("notas_extraidas/*.xlsx")
        if arquivos:
            print(f"\nArquivos criados ({len(arquivos)} total):")
            for arquivo in arquivos[:10]:  # Mostrar apenas os 10 primeiros
                print(f"  - {os.path.basename(arquivo)}")
            if len(arquivos) > 10:
                print(f"  ... e mais {len(arquivos) - 10} arquivos")
        else:
            print("⚠ Nenhum arquivo encontrado (talvez não haja notas lançadas)")
        
        print("\n" + "="*70)
        print("EXTRAÇÃO CONCLUÍDA!")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Extração cancelada pelo usuário")
    
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Sempre fechar o navegador
        print("\n→ Fechando navegador...")
        automacao.fechar()
        print("✓ Concluído")


def exemplo_uso_avancado():
    """
    Exemplo avançado: extrai todos os bimestres com mais controle
    """
    print("="*70)
    print("EXEMPLO AVANÇADO - EXTRAÇÃO COMPLETA")
    print("="*70)
    print()
    
    # Credenciais
    usuario = input("Usuário: ").strip()
    senha = input("Senha: ").strip()
    
    if not usuario or not senha:
        print("✗ Credenciais obrigatórias!")
        return
    
    # Configurações
    print("\nConfiguração:")
    print("1 - Apenas 1º bimestre (rápido)")
    print("2 - 1º e 2º bimestres")
    print("3 - Todos os 4 bimestres (completo)")
    
    opcao = input("\nEscolha uma opção [1-3]: ").strip()
    
    if opcao == '1':
        bimestres = [1]
    elif opcao == '2':
        bimestres = [1, 2]
    elif opcao == '3':
        bimestres = [1, 2, 3, 4]
    else:
        print("Opção inválida! Usando padrão: 1º bimestre")
        bimestres = [1]
    
    # Modo silencioso?
    modo_silencioso = input("\nExecutar em modo silencioso (sem mostrar navegador)? [s/N]: ").strip().lower()
    headless = modo_silencioso == 's'
    
    print("\n" + "="*70)
    print("INICIANDO EXTRAÇÃO")
    print(f"Bimestres: {', '.join([f'{b}º' for b in bimestres])}")
    print(f"Modo: {'Silencioso' if headless else 'Visual'}")
    print("="*70 + "\n")
    
    # Criar automação
    automacao = AutomacaoGEDUC(headless=headless)
    
    try:
        # Processo completo
        if not automacao.iniciar_navegador():
            return
        
        if not automacao.fazer_login(usuario, senha):
            print("✗ Login falhou")
            automacao.fechar()
            return
        
        print("✓ Login OK\n")
        
        # Extrair com estatísticas detalhadas
        inicio = __import__('time').time()
        
        def callback_detalhado(processadas, total):
            tempo_decorrido = __import__('time').time() - inicio
            if total > 0:
                tempo_estimado = (tempo_decorrido / processadas) * (total - processadas) if processadas > 0 else 0
                print(f"  [{processadas}/{total}] {processadas/total*100:.1f}% - "
                      f"Tempo: {tempo_decorrido:.1f}s - Estimado: {tempo_estimado:.1f}s")
        
        if not automacao.extrair_todas_notas(
            bimestres=bimestres, 
            diretorio_saida="notas_extraidas",
            callback_progresso=callback_detalhado
        ):
            print("✗ Erro na extração")
            automacao.fechar()
            return
        
        # Estatísticas finais (arquivos já foram salvos automaticamente)
        tempo_total = __import__('time').time() - inicio
        print(f"\n{'='*70}")
        print("ESTATÍSTICAS")
        print(f"{'='*70}")
        print(f"Tempo total: {tempo_total:.1f}s ({tempo_total/60:.1f} minutos)")
        print(f"Arquivos salvos em: notas_extraidas/")
        print(f"Formato: 1 arquivo por turma/bimestre com múltiplas planilhas")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
    
    finally:
        automacao.fechar()


if __name__ == "__main__":
    print("\nEscolha o modo de execução:")
    print("1 - Uso básico (apenas 1º bimestre)")
    print("2 - Uso avançado (escolher bimestres)")
    print("3 - Interface gráfica (abrir janela)")
    
    escolha = input("\nOpção [1-3]: ").strip()
    
    if escolha == '1':
        exemplo_uso_basico()
    elif escolha == '2':
        exemplo_uso_avancado()
    elif escolha == '3':
        from automatizar_extracao_geduc import interface_automacao
        interface_automacao()
    else:
        print("Opção inválida!")
