"""
Script de benchmark para medir tempo de startup antes e depois das otimizações.
"""

import time
import sys
import subprocess
from pathlib import Path


def measure_import_time(module_name: str) -> float:
    """
    Mede o tempo de import de um módulo.
    
    Args:
        module_name: Nome do módulo a importar
    
    Returns:
        Tempo em segundos
    """
    start = time.time()
    try:
        __import__(module_name)
        return time.time() - start
    except ImportError as e:
        print(f"❌ Erro ao importar {module_name}: {e}")
        return -1.0


def measure_startup_time() -> dict:
    """
    Mede tempos de startup de componentes principais.
    
    Returns:
        Dicionário com tempos medidos
    """
    results = {}
    
    print("📊 Medindo tempo de imports...")
    print("-" * 50)
    
    # Módulos pesados
    heavy_modules = [
        'matplotlib',
        'matplotlib.pyplot',
        'pandas',
        'numpy',
        'reportlab.platypus'
    ]
    
    for module in heavy_modules:
        print(f"Medindo {module}...", end=" ")
        elapsed = measure_import_time(module)
        if elapsed >= 0:
            results[module] = elapsed
            print(f"{elapsed:.3f}s")
        else:
            print("SKIP")
    
    print("-" * 50)
    
    # Módulos do sistema
    print("\n📦 Medindo módulos do sistema...")
    print("-" * 50)
    
    system_modules = [
        'config',
        'config_logs',
        'conexao',
        'db.connection',
        'services.report_service',
        'utils.lazy_imports',
    ]
    
    for module in system_modules:
        print(f"Medindo {module}...", end=" ")
        elapsed = measure_import_time(module)
        if elapsed >= 0:
            results[module] = elapsed
            print(f"{elapsed:.3f}s")
        else:
            print("SKIP")
    
    print("-" * 50)
    
    return results


def measure_application_startup() -> float:
    """
    Mede tempo total de startup da aplicação.
    
    Returns:
        Tempo em segundos
    """
    print("\n🚀 Medindo startup completo da aplicação...")
    print("-" * 50)
    
    # Script de teste que importa e inicializa a aplicação
    test_script = """
import time
start = time.time()

from application import Application
app = Application()
# Não inicializar UI completa, apenas estrutura

elapsed = time.time() - start
print(f"STARTUP_TIME={elapsed:.3f}")
"""
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Extrair tempo do output
        for line in result.stdout.split('\n'):
            if line.startswith('STARTUP_TIME='):
                time_str = line.split('=')[1]
                return float(time_str)
        
        print("❌ Não foi possível medir startup da aplicação")
        return -1.0
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout ao medir startup")
        return -1.0
    except Exception as e:
        print(f"❌ Erro ao medir startup: {e}")
        return -1.0


def compare_lazy_vs_eager() -> dict:
    """
    Compara tempo de import com e sem lazy loading.
    
    Returns:
        Dicionário com comparação
    """
    print("\n⚡ Comparando lazy vs eager loading...")
    print("-" * 50)
    
    comparison = {}
    
    # Teste 1: Import direto (eager)
    print("Teste 1: Import direto de pandas...")
    start = time.time()
    import pandas as pd
    eager_time = time.time() - start
    print(f"  Import direto: {eager_time:.3f}s")
    comparison['pandas_eager'] = eager_time
    
    # Teste 2: Lazy import
    print("\nTeste 2: Lazy import de pandas...")
    start = time.time()
    from utils.lazy_imports import get_pandas
    lazy_import_time = time.time() - start
    print(f"  Lazy import (sem carregar): {lazy_import_time:.3f}s")
    comparison['pandas_lazy_import'] = lazy_import_time
    
    # Teste 3: Primeiro uso do lazy import
    print("\nTeste 3: Primeiro uso do lazy pandas...")
    start = time.time()
    pd_lazy = get_pandas()
    lazy_first_use = time.time() - start
    print(f"  Primeiro uso: {lazy_first_use:.3f}s")
    comparison['pandas_lazy_first_use'] = lazy_first_use
    
    # Teste 4: Segundo uso (deve ser instantâneo)
    print("\nTeste 4: Segundo uso do lazy pandas...")
    start = time.time()
    pd_lazy2 = get_pandas()
    lazy_second_use = time.time() - start
    print(f"  Segundo uso: {lazy_second_use:.4f}s")
    comparison['pandas_lazy_second_use'] = lazy_second_use
    
    print("-" * 50)
    if eager_time > 0:
        print(f"\n💡 Economia no startup: {eager_time - lazy_import_time:.3f}s")
        print(f"   ({((eager_time - lazy_import_time) / eager_time * 100):.1f}% mais rápido)")
    else:
        print("\n💡 Módulo já estava carregado, impossível comparar")
    
    return comparison


def generate_report(results: dict):
    """
    Gera relatório de performance.
    
    Args:
        results: Dicionário com tempos medidos
    """
    print("\n" + "=" * 50)
    print("📋 RELATÓRIO DE PERFORMANCE")
    print("=" * 50)
    
    # Total de imports
    total_time = sum(t for t in results.values() if t > 0)
    print(f"\n⏱️  Tempo total de imports: {total_time:.3f}s")
    
    # Top 5 mais lentos
    print("\n🐌 Top 5 imports mais lentos:")
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    for i, (module, time_taken) in enumerate(sorted_results[:5], 1):
        if time_taken > 0:
            percentage = (time_taken / total_time) * 100
            print(f"  {i}. {module:30s} {time_taken:.3f}s ({percentage:.1f}%)")
    
    # Recomendações
    print("\n💡 Recomendações:")
    slow_modules = [m for m, t in results.items() if t > 0.5]
    if slow_modules:
        print(f"  • Considere lazy loading para: {', '.join(slow_modules)}")
    else:
        print("  • ✅ Todos os imports estão otimizados!")
    
    print("\n" + "=" * 50)


def main():
    """Executa benchmark completo."""
    print("🔍 Sistema de Benchmark de Performance")
    print("=" * 50)
    print()
    
    # Benchmark de imports
    import_results = measure_startup_time()
    
    # Comparação lazy vs eager
    lazy_comparison = compare_lazy_vs_eager()
    
    # Relatório final
    generate_report(import_results)
    
    # Salvar resultados
    output_file = Path("benchmark_results.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("BENCHMARK DE PERFORMANCE - Sistema de Gestão Escolar\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("TEMPOS DE IMPORT:\n")
        f.write("-" * 60 + "\n")
        for module, time_taken in sorted(import_results.items()):
            f.write(f"{module:40s} {time_taken:.3f}s\n")
        
        f.write("\n\nCOMPARAÇÃO LAZY VS EAGER:\n")
        f.write("-" * 60 + "\n")
        for key, value in lazy_comparison.items():
            f.write(f"{key:40s} {value:.4f}s\n")
        
        total = sum(t for t in import_results.values() if t > 0)
        f.write(f"\n\nTEMPO TOTAL: {total:.3f}s\n")
    
    print(f"\n💾 Resultados salvos em: {output_file}")


if __name__ == "__main__":
    main()
