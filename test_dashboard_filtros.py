"""
Script de teste para verificar os novos filtros do dashboard.
Testa a função obter_estatisticas_alunos com os filtros do Lista_atualizada.py.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.estatistica_service import obter_estatisticas_alunos

def main():
    print("=" * 80)
    print("TESTE: Dashboard com filtros do Lista_atualizada.py")
    print("=" * 80)
    
    # Testar com ano letivo None (deve buscar ano atual)
    print("\n[1] Testando com ano_letivo=None (detecta ano atual automaticamente):")
    print("-" * 80)
    
    dados = obter_estatisticas_alunos(escola_id=60, ano_letivo=None)
    
    if dados:
        print(f"✓ Dados obtidos com sucesso!")
        print(f"\nEstatísticas do Dashboard:")
        print(f"  • Total de alunos (Ativos + Transferidos): {dados.get('total_alunos', 0)}")
        print(f"  • Alunos ativos: {dados.get('alunos_ativos', 0)}")
        print(f"  • Alunos transferidos: {dados.get('alunos_transferidos', 0)}")
        print(f"  • Alunos sem matrícula: {dados.get('alunos_sem_matricula', 0)}")
        
        alunos_por_serie = dados.get('alunos_por_serie', [])
        print(f"\n  • Alunos por série: {len(alunos_por_serie)} séries encontradas")
        if alunos_por_serie:
            print("    Detalhamento:")
            for item in alunos_por_serie:
                print(f"      - {item['serie']}: {item['quantidade']} alunos")
        
        alunos_por_turno = dados.get('alunos_por_turno', [])
        print(f"\n  • Alunos por turno:")
        if alunos_por_turno:
            for item in alunos_por_turno:
                print(f"      - {item['turno']}: {item['quantidade']} alunos")
        
        print("\n✓ Teste concluído com sucesso!")
    else:
        print("✗ Falha ao obter dados")
        return 1
    
    # Testar com ano letivo específico
    print("\n[2] Testando com ano_letivo='2024' (ano específico):")
    print("-" * 80)
    
    dados2 = obter_estatisticas_alunos(escola_id=60, ano_letivo='2024')
    
    if dados2:
        print(f"✓ Dados obtidos para 2024!")
        print(f"  • Total: {dados2.get('total_alunos', 0)}")
        print(f"  • Ativos: {dados2.get('alunos_ativos', 0)}")
        print(f"  • Transferidos: {dados2.get('alunos_transferidos', 0)}")
    else:
        print("⚠ Nenhum dado para ano 2024 (pode não existir no banco)")
    
    print("\n" + "=" * 80)
    print("COMPARAÇÃO: Antes vs Depois")
    print("=" * 80)
    print("\nANTES (filtro simples):")
    print("  • WHERE m.status = 'Ativo'")
    print("  • Total mostrava apenas alunos ativos")
    print("  • Não considerava ano letivo")
    
    print("\nDEPOIS (filtro do Lista_atualizada.py):")
    print("  • WHERE (m.status = 'Ativo' OR m.status = 'Transferido' OR m.status = 'Transferida')")
    print("  • WHERE m.ano_letivo_id = (SELECT id FROM AnosLetivos WHERE ano_letivo = %s)")
    print("  • Total mostra ativos + transferidos do ano letivo correto")
    print("  • Dashboard mais preciso e contextualizado")
    
    print("\n" + "=" * 80)
    return 0

if __name__ == '__main__':
    sys.exit(main())
