"""
Script para executar testes de integração.

Este script executa todos os testes de integração e gera relatórios
de cobertura e resultados.

Uso:
    python run_integration_tests.py [opções]

Opções:
    --skip-slow: Pula testes marcados como lentos
    --verbose: Modo verbose com mais detalhes
    --coverage: Gera relatório de cobertura
    --html: Gera relatório HTML
"""

import sys
import subprocess
from pathlib import Path
import argparse

# Cores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    """Imprime cabeçalho formatado."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(message):
    """Imprime mensagem de sucesso."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Imprime mensagem de erro."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    """Imprime mensagem de aviso."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def run_command(cmd, description):
    """
    Executa comando e retorna resultado.
    
    Args:
        cmd: Lista com comando e argumentos
        description: Descrição da operação
        
    Returns:
        True se sucesso, False caso contrário
    """
    print(f"{Colors.OKCYAN}→ {description}...{Colors.ENDC}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print_success(f"{description} - OK")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print_error(f"{description} - FALHOU")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print_error(f"{description} - ERRO: {e}")
        return False


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Executa testes de integração do sistema'
    )
    parser.add_argument(
        '--skip-slow',
        action='store_true',
        help='Pula testes marcados como lentos'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Modo verbose'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Gera relatório de cobertura'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Gera relatório HTML'
    )
    parser.add_argument(
        '--markers',
        '-m',
        type=str,
        help='Executar apenas testes com marcadores específicos (ex: integration)'
    )
    
    args = parser.parse_args()
    
    print_header("TESTES DE INTEGRAÇÃO - SISTEMA DE GESTÃO ESCOLAR")
    
    # Diretório de testes
    tests_dir = Path(__file__).parent / 'tests' / 'integration'
    
    if not tests_dir.exists():
        print_error(f"Diretório de testes não encontrado: {tests_dir}")
        return 1
    
    # Construir comando pytest
    cmd = ['pytest', str(tests_dir)]
    
    # Adicionar opções
    if args.verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    if args.skip_slow:
        cmd.append('--skip-slow')
        print_warning("Testes lentos serão pulados")
    
    if args.markers:
        cmd.extend(['-m', args.markers])
        print(f"{Colors.OKCYAN}Executando apenas testes marcados como: {args.markers}{Colors.ENDC}")
    
    if args.coverage:
        cmd.extend(['--cov=.', '--cov-report=term-missing'])
        print(f"{Colors.OKCYAN}Relatório de cobertura será gerado{Colors.ENDC}")
    
    if args.html:
        cmd.extend(['--html=report.html', '--self-contained-html'])
        print(f"{Colors.OKCYAN}Relatório HTML será gerado: report.html{Colors.ENDC}")
    
    # Adicionar opções padrão
    cmd.extend([
        '--tb=short',  # Traceback curto
        '--color=yes',  # Colorir output
        '-ra'  # Mostrar resumo de todos os resultados
    ])
    
    print(f"\n{Colors.OKBLUE}Comando: {' '.join(cmd)}{Colors.ENDC}\n")
    
    # Executar testes
    print_header("EXECUTANDO TESTES")
    
    try:
        result = subprocess.run(cmd, check=False)
        
        print_header("RESULTADO")
        
        if result.returncode == 0:
            print_success("TODOS OS TESTES PASSARAM!")
            return 0
        elif result.returncode == 1:
            print_error("ALGUNS TESTES FALHARAM")
            return 1
        elif result.returncode == 2:
            print_error("ERRO DE EXECUÇÃO")
            return 2
        elif result.returncode == 5:
            print_warning("NENHUM TESTE FOI COLETADO")
            return 0
        else:
            print_error(f"CÓDIGO DE SAÍDA: {result.returncode}")
            return result.returncode
            
    except KeyboardInterrupt:
        print_warning("\nTestes interrompidos pelo usuário")
        return 130
    except Exception as e:
        print_error(f"Erro ao executar testes: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
