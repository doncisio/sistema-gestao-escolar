"""
Exemplo de uso do módulo NotaAta para gerar relatórios de notas.

Este script demonstra como utilizar as funções do módulo NotaAta 
para gerar diferentes tipos de relatórios de notas bimestrais.
"""

import sys
import traceback
from NotaAta import (
    nota_bimestre,
    nota_bimestre2,
    gerar_relatorio_notas
)

def mostrar_menu():
    """Exibe o menu de opções para o usuário."""
    print("\n=== SISTEMA DE GERAÇÃO DE RELATÓRIOS DE NOTAS ===")
    print("1. Gerar relatório 1º Bimestre (Séries Iniciais)")
    print("2. Gerar relatório 2º Bimestre (Séries Iniciais)")
    print("3. Gerar relatório 3º Bimestre (Séries Iniciais)")
    print("4. Gerar relatório 4º Bimestre (Séries Iniciais)")
    print("5. Gerar relatório 1º Bimestre (Séries Finais)")
    print("6. Gerar relatório 2º Bimestre (Séries Finais)")
    print("7. Gerar relatório 3º Bimestre (Séries Finais)")
    print("8. Gerar relatório 4º Bimestre (Séries Finais)")
    print("9. Gerar relatório personalizado")
    print("0. Sair")
    return input("\nEscolha uma opção: ")

def gerar_relatorio_personalizado():
    """Permite ao usuário definir parâmetros para um relatório personalizado."""
    try:
        # Obter o bimestre
        print("\n=== RELATÓRIO PERSONALIZADO ===")
        print("Escolha o bimestre:")
        print("1. 1º Bimestre")
        print("2. 2º Bimestre")
        print("3. 3º Bimestre")
        print("4. 4º Bimestre")
        opcao_bimestre = input("Opção: ")
        
        bimestres = {
            "1": "1º bimestre",
            "2": "2º bimestre",
            "3": "3º bimestre",
            "4": "4º bimestre"
        }
        
        if opcao_bimestre not in bimestres:
            print("Opção inválida!")
            return
            
        bimestre = bimestres[opcao_bimestre]
        
        # Obter o nível de ensino
        print("\nEscolha o nível de ensino:")
        print("1. Séries Iniciais (1º ao 5º ano)")
        print("2. Séries Finais (6º ao 9º ano)")
        opcao_nivel = input("Opção: ")
        
        nivel_ensino = "iniciais" if opcao_nivel == "1" else "finais"
        
        # Obter o ano letivo
        ano_letivo = input("\nDigite o ano letivo (ou deixe em branco para usar 2025): ")
        if ano_letivo.strip():
            try:
                ano_letivo = int(ano_letivo)
            except ValueError:
                print("Ano letivo inválido! Usando 2025.")
                ano_letivo = 2025
        else:
            ano_letivo = 2025
        
        # Obter o ID da escola
        escola_id = input("\nDigite o ID da escola (ou deixe em branco para usar o padrão 60): ")
        if escola_id.strip():
            try:
                escola_id = int(escola_id)
            except ValueError:
                print("ID de escola inválido! Usando o padrão 60.")
                escola_id = 60
        else:
            escola_id = 60
        
        # Definir o status de matrícula
        print("\nEscolha os status de matrícula a incluir:")
        print("1. Apenas alunos ativos")
        print("2. Alunos ativos e transferidos")
        opcao_status = input("Opção: ")
        
        if opcao_status == "2":
            status_matricula = ["Ativo", "Transferido"]
        else:
            status_matricula = None  # Usa o padrão (Ativo)
        
        # Gerar o relatório com os parâmetros especificados
        print(f"\nGerando relatório para {bimestre}, nível {nivel_ensino}, ano {ano_letivo}, escola ID {escola_id}...")
        
        resultado = gerar_relatorio_notas(
            bimestre=bimestre,
            nivel_ensino=nivel_ensino,
            ano_letivo=ano_letivo,
            escola_id=escola_id,
            status_matricula=status_matricula
        )
        
        if resultado:
            print("Relatório gerado com sucesso!")
        else:
            print("Não foi possível gerar o relatório.")
    
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"Erro ao gerar relatório personalizado: {e}")
        traceback.print_exc()

def executar_opcao(opcao):
    """Executa a ação correspondente à opção escolhida."""
    try:
        # Mapeamento das opções para funções e parâmetros
        mapeamento = {
            "1": (nota_bimestre, ["1º bimestre"]),
            "2": (nota_bimestre, ["2º bimestre"]),
            "3": (nota_bimestre, ["3º bimestre"]),
            "4": (nota_bimestre, ["4º bimestre"]),
            "5": (nota_bimestre2, ["1º bimestre"]),
            "6": (nota_bimestre2, ["2º bimestre"]),
            "7": (nota_bimestre2, ["3º bimestre"]),
            "8": (nota_bimestre2, ["4º bimestre"]),
            "9": (gerar_relatorio_personalizado, [])
        }
        
        if opcao in mapeamento:
            funcao, args = mapeamento[opcao]
            funcao(*args)
        elif opcao == "0":
            print("Encerrando o programa...")
            sys.exit(0)
        else:
            print("Opção inválida!")
    
    except Exception as e:
        print(f"Erro ao executar a opção: {e}")
        traceback.print_exc()

def main():
    """Função principal do programa."""
    try:
        while True:
            opcao = mostrar_menu()
            executar_opcao(opcao)
            input("\nPressione Enter para continuar...")
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro inesperado: {e}")
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 