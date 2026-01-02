"""
Script para limpar o cache do dashboard após correção do movimento mensal
"""
from src.core.conexao import inicializar_pool
from src.utils.cache import dashboard_cache

inicializar_pool()

print("=" * 80)
print("LIMPEZA DE CACHE DO DASHBOARD")
print("=" * 80)

# Limpar cache do dashboard
dashboard_cache.invalidate()
print("✓ Cache do dashboard limpo com sucesso!")
print("\nO gráfico de movimento mensal na página principal será atualizado")
print("com os dados corretos do ano letivo 2025 na próxima visualização.")
print("=" * 80)
