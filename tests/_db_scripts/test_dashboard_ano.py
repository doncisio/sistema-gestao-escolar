"""
Script para testar o dashboard com ano letivo específico
"""
from src.core.conexao import inicializar_pool
from src.services.estatistica_service import obter_estatisticas_alunos
from db.connection import get_cursor

inicializar_pool()

print("=" * 80)
print("TESTE: Dashboard - Detecção de Ano Letivo")
print("=" * 80)

# Simular lógica do dashboard para ano letivo
with get_cursor() as cursor:
    # 1. Tentar ano atual
    cursor.execute("SELECT ano_letivo FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
    resultado_ano = cursor.fetchone()
    
    if not resultado_ano:
        print("\n❌ Ano atual não encontrado, buscando mais recente...")
        cursor.execute("SELECT ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
        resultado_ano = cursor.fetchone()
    
    if resultado_ano:
        ano_detectado = resultado_ano['ano_letivo']
        print(f"\n✓ Ano detectado: {ano_detectado}")
    else:
        ano_detectado = None
        print("\n❌ Nenhum ano letivo encontrado!")

# Testar com ano None (usa lógica interna do service)
print("\n" + "=" * 80)
print("1. Teste com ano_letivo=None (lógica automática)")
print("=" * 80)
dados1 = obter_estatisticas_alunos(escola_id=60, ano_letivo=None)
if dados1:
    print(f"Total alunos: {dados1.get('total_alunos')}")
    print(f"Ativos: {dados1.get('alunos_ativos')}")
    print(f"Transferidos: {dados1.get('alunos_transferidos')}")

# Testar com ano '2025' explícito
print("\n" + "=" * 80)
print("2. Teste com ano_letivo='2025' (explícito)")
print("=" * 80)
dados2 = obter_estatisticas_alunos(escola_id=60, ano_letivo='2025')
if dados2:
    print(f"Total alunos: {dados2.get('total_alunos')}")
    print(f"Ativos: {dados2.get('alunos_ativos')}")
    print(f"Transferidos: {dados2.get('alunos_transferidos')}")

# Verificar se o dashboard está passando ano corretamente
print("\n" + "=" * 80)
print("VERIFICAÇÃO: Diferença entre None e '2025'")
print("=" * 80)

if dados1 and dados2:
    if dados1['total_alunos'] != dados2['total_alunos']:
        print(f"⚠️  PROBLEMA ENCONTRADO!")
        print(f"   Com None: {dados1['total_alunos']} alunos")
        print(f"   Com '2025': {dados2['total_alunos']} alunos")
        print(f"\n💡 Solução: Dashboard deve passar ano_letivo='2025' explicitamente!")
    else:
        print(f"✓ Ambos retornam {dados1['total_alunos']} alunos")
