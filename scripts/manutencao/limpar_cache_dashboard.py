"""
Script para limpar cache do dashboard e verificar
"""
from src.core.conexao import inicializar_pool
from src.utils.cache import dashboard_cache

inicializar_pool()

print("=" * 80)
print("LIMPEZA DE CACHE DO DASHBOARD")
print("=" * 80)

# Limpar cache usando invalidate_pattern com padrão vazio (limpa tudo)
count = dashboard_cache.invalidate_pattern('')
print(f"\n✓ Cache limpo! {count} entradas removidas")

# Verificar estatísticas novamente
from src.services.estatistica_service import obter_estatisticas_alunos

print("\nBuscando estatísticas atualizadas...")
dados = obter_estatisticas_alunos(escola_id=60, ano_letivo='2025')

if dados:
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS ATUALIZADAS")
    print("=" * 80)
    print(f"Total de alunos: {dados.get('total_alunos')}")
    print(f"Alunos ativos: {dados.get('alunos_ativos')}")
    print(f"Alunos transferidos: {dados.get('alunos_transferidos', 'N/A')}")
    print(f"Alunos sem matrícula: {dados.get('alunos_sem_matricula', 'N/A')}")
    
    print("\nAlunos por série:")
    for serie in dados.get('alunos_por_serie', []):
        print(f"  - {serie['serie']}: {serie['quantidade']} alunos")
    
    if dados.get('total_alunos') == 342:
        print("\n✅ CORRETO: Dashboard mostrando 342 alunos!")
    else:
        print(f"\n❌ ERRO: Esperado 342, mas mostra {dados.get('total_alunos')}")
else:
    print("\n❌ Erro ao obter estatísticas!")
