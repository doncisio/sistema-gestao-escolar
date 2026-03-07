"""
Script para limpar o cache do dashboard e verificar as estatísticas atualizadas.
Uso: python scripts/manutencao/limpar_cache_dashboard.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.cache import dashboard_cache, global_cache
from db.connection import conectar_bd

print("=" * 60)
print("  LIMPEZA DE CACHE DO DASHBOARD")
print("=" * 60)

# Estatísticas antes
stats_antes = dashboard_cache.get_stats()
print(f"\nEntradas no cache antes: {stats_antes['size']}")

# Limpa todo o dashboard_cache
dashboard_cache.invalidate()
global_cache.invalidate()
print("Cache limpo com sucesso!")

# Verifica o ano letivo ativo
try:
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, ano_letivo FROM anosletivos
        WHERE CURDATE() BETWEEN data_inicio AND data_fim
        ORDER BY data_inicio DESC LIMIT 1
    """)
    row = cursor.fetchone()
    if not row:
        cursor.execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
        row = cursor.fetchone()
    ano_letivo_id = row[0] if row else None
    ano_letivo_val = str(row[1]) if row else None
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Aviso: nao foi possivel determinar o ano letivo: {e}")
    ano_letivo_id = None
    ano_letivo_val = None

print(f"\nAno letivo ativo: {ano_letivo_val or 'nao determinado'}")

# Busca estatísticas atualizadas (sem cache)
from src.services.estatistica_service import obter_estatisticas_alunos
print("\nBuscando estatisticas atualizadas...")
try:
    dados = obter_estatisticas_alunos(escola_id=60, ano_letivo=ano_letivo_val)
except Exception as e:
    print(f"Erro ao buscar estatisticas: {e}")
    dados = None

if dados:
    print("\n" + "=" * 60)
    print("  ESTATISTICAS ATUALIZADAS")
    print("=" * 60)
    print(f"  Total (ativos + transferidos): {dados.get('total_alunos', 'N/A')}")
    print(f"  Alunos ativos               : {dados.get('alunos_ativos', 'N/A')}")
    print(f"  Alunos transferidos         : {dados.get('alunos_transferidos', 'N/A')}")
    print("\n  Alunos por serie:")
    for serie in dados.get('alunos_por_serie', []):
        print(f"    {serie['serie']}: {serie['quantidade']}")
else:
    print("\nNenhum dado retornado para o ano letivo atual.")
