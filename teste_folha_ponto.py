"""
Script de teste para geração de folha de ponto
Demonstra como usar o gerador de folha de ponto
"""

from gerar_folha_ponto import gerar_folha_ponto_funcionario
from datetime import datetime

def teste_gerar_folha_ponto():
    """
    Testa a geração de folha de ponto
    """
    print("=" * 60)
    print("TESTE DE GERAÇÃO DE FOLHA DE PONTO")
    print("=" * 60)
    
    # Solicitar ID do funcionário
    try:
        funcionario_id = int(input("\nDigite o ID do funcionário: "))
    except ValueError:
        print("Erro: ID inválido!")
        return
    
    # Solicitar mês e ano (opcional)
    usar_atual = input("\nUsar mês/ano atual? (S/N): ").strip().upper()
    
    if usar_atual == 'S':
        mes = None
        ano = None
        hoje = datetime.now()
        mes_exibir = hoje.month
        ano_exibir = hoje.year
    else:
        try:
            mes = int(input("Digite o mês (1-12): "))
            ano = int(input("Digite o ano (ex: 2025): "))
            
            if not (1 <= mes <= 12):
                print("Erro: Mês deve estar entre 1 e 12!")
                return
            
            mes_exibir = mes
            ano_exibir = ano
        except ValueError:
            print("Erro: Valores inválidos!")
            return
    
    print(f"\nGerando folha de ponto para:")
    print(f"  - Funcionário ID: {funcionario_id}")
    print(f"  - Mês/Ano: {mes_exibir:02d}/{ano_exibir}")
    print("\nProcessando...")
    
    # Gerar folha de ponto
    resultado = gerar_folha_ponto_funcionario(funcionario_id, mes, ano)
    
    if resultado:
        print(f"\n✓ Folha de ponto gerada com sucesso!")
        print(f"  Arquivo: {resultado}")
        print("\nDeseja abrir o arquivo? (S/N): ", end="")
        abrir = input().strip().upper()
        
        if abrir == 'S':
            import os
            import subprocess
            if os.path.exists(resultado):
                try:
                    # Abrir arquivo com o visualizador padrão
                    os.startfile(resultado)
                    print("Arquivo aberto!")
                except Exception as e:
                    print(f"Erro ao abrir arquivo: {e}")
    else:
        print("\n✗ Erro ao gerar folha de ponto!")
        print("  Verifique se o ID do funcionário existe no banco de dados.")
    
    print("\n" + "=" * 60)

def listar_funcionarios_disponiveis():
    """
    Lista alguns funcionários disponíveis no banco de dados
    """
    from conexao import conectar_bd
    
    print("\n" + "=" * 60)
    print("FUNCIONÁRIOS CADASTRADOS")
    print("=" * 60)
    
    conn = conectar_bd()
    if not conn:
        print("Erro ao conectar ao banco de dados!")
        return
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 
                id, 
                nome, 
                cargo, 
                matricula
            FROM Funcionarios 
            ORDER BY nome 
            LIMIT 20
        """
        cursor.execute(query)
        funcionarios = cursor.fetchall()
        
        if not funcionarios:
            print("\nNenhum funcionário cadastrado.")
        else:
            print(f"\n{'ID':<6} {'Nome':<30} {'Cargo':<25} {'Matrícula':<15}")
            print("-" * 76)
            for func in funcionarios:
                print(f"{func['id']:<6} {func['nome']:<30} {func['cargo']:<25} {func.get('matricula') or 'N/A':<15}")
            
            if len(funcionarios) == 20:
                print("\n(Mostrando apenas os primeiros 20 funcionários)")
        
    except Exception as e:
        print(f"Erro ao listar funcionários: {e}")
    finally:
        conn.close()
    
    print("=" * 60)

def menu_principal():
    """
    Menu principal do teste
    """
    while True:
        print("\n" + "=" * 60)
        print("GERADOR DE FOLHA DE PONTO")
        print("=" * 60)
        print("\n1. Listar funcionários")
        print("2. Gerar folha de ponto")
        print("3. Sair")
        print("\nEscolha uma opção: ", end="")
        
        opcao = input().strip()
        
        if opcao == '1':
            listar_funcionarios_disponiveis()
        elif opcao == '2':
            teste_gerar_folha_ponto()
        elif opcao == '3':
            print("\nEncerrando...")
            break
        else:
            print("\nOpção inválida!")

if __name__ == "__main__":
    menu_principal()
