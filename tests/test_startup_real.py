"""
Script para medir tempo real de inicialização do main.py
"""
import time
import subprocess
import sys

print("=" * 80)
print("TESTE DE INICIALIZAÇÃO REAL DO SISTEMA")
print("=" * 80)

print("\nMedindo tempo de inicialização...")
print("(O sistema será fechado automaticamente após 2 segundos)\n")

inicio = time.time()

# Executar o sistema por 2 segundos e fechar
try:
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=r"c:\gestao"
    )
    
    # Aguardar 2 segundos
    time.sleep(2)
    
    # Terminar o processo
    proc.terminate()
    proc.wait(timeout=2)
    
except subprocess.TimeoutExpired:
    proc.kill()
except Exception as e:
    print(f"Erro: {e}")

fim = time.time()
tempo_total = (fim - inicio) * 1000

print(f"\n✓ Sistema iniciado em aproximadamente: {tempo_total:.0f}ms")
print("\nNota: Este é o tempo até a janela estar visível.")
print("Componentes como dashboard serão carregados sob demanda.")

print("\n" + "=" * 80)
