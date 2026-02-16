"""
Script para diagnosticar o problema do movimento mensal mostrando 341
"""
from src.core.conexao import inicializar_pool
from src.services.estatistica_service import obter_movimento_mensal_resumo, obter_estatisticas_alunos

inicializar_pool()

print("=" * 80)
print("DIAGNÓSTICO: Movimento Mensal vs Dashboard")
print("=" * 80)

# 1. Estatísticas gerais (dashboard)
print("\n1. DASHBOARD (total_alunos)")
print("-" * 80)
dados_dashboard = obter_estatisticas_alunos(escola_id=60, ano_letivo='2025')
if dados_dashboard:
    print(f"Total alunos: {dados_dashboard['total_alunos']}")
    print(f"Ativos: {dados_dashboard['alunos_ativos']}")
    print(f"Transferidos: {dados_dashboard['alunos_transferidos']}")

# 2. Movimento mensal
print("\n2. MOVIMENTO MENSAL (mês atual)")
print("-" * 80)
movimento = obter_movimento_mensal_resumo(escola_id=60, ano_letivo='2025')
if movimento and movimento.get('meses'):
    ultimo_mes = movimento['meses'][-1]  # Último mês calculado
    print(f"Mês: {ultimo_mes['mes']}")
    print(f"Ativos: {ultimo_mes['ativos']}")
    print(f"Transferidos: {ultimo_mes['transferidos']}")
    print(f"Evadidos: {ultimo_mes['evadidos']}")
    total_movimento = ultimo_mes['ativos'] + ultimo_mes['transferidos'] + ultimo_mes['evadidos']
    print(f"TOTAL (Ativos + Transferidos + Evadidos): {total_movimento}")

# 3. Comparação
print("\n3. COMPARAÇÃO")
print("-" * 80)
if dados_dashboard and movimento:
    ultimo_mes = movimento['meses'][-1]
    total_movimento = ultimo_mes['ativos'] + ultimo_mes['transferidos'] + ultimo_mes['evadidos']
    
    if dados_dashboard['total_alunos'] != ultimo_mes['ativos']:
        print(f"⚠️  PROBLEMA ENCONTRADO!")
        print(f"   Dashboard (Ativos + Transferidos): {dados_dashboard['total_alunos']}")
        print(f"   Movimento (Apenas Ativos): {ultimo_mes['ativos']}")
        print(f"   Diferença: {dados_dashboard['total_alunos'] - ultimo_mes['ativos']}")
        print(f"\n💡 SOLUÇÃO: Movimento mensal deve somar Ativos + Transferidos para o gráfico")
        print(f"   Total correto seria: {ultimo_mes['ativos']} + {ultimo_mes['transferidos']} = {ultimo_mes['ativos'] + ultimo_mes['transferidos']}")
    else:
        print("✓ Dashboard e Movimento Mensal estão alinhados")

# 4. Detalhamento dos meses
print("\n4. MOVIMENTO MENSAL - TODOS OS MESES")
print("-" * 80)
if movimento and movimento.get('meses'):
    print(f"{'Mês':<10} {'Ativos':<10} {'Transf.':<10} {'Evad.':<10} {'Total':<10}")
    print("-" * 50)
    for m in movimento['meses']:
        total = m['ativos'] + m['transferidos'] + m['evadidos']
        print(f"{m['mes']:<10} {m['ativos']:<10} {m['transferidos']:<10} {m['evadidos']:<10} {total:<10}")
