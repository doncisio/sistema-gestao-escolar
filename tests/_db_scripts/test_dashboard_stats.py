"""
Script de teste para diagnosticar o problema do dashboard
"""
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')

from src.core.conexao import inicializar_pool
from src.services.estatistica_service import obter_estatisticas_alunos

print("="*60)
print("TESTE: obter_estatisticas_alunos")
print("="*60)

inicializar_pool()

try:
    print("\n1. Chamando obter_estatisticas_alunos(escola_id=60)...")
    dados = obter_estatisticas_alunos(escola_id=60)
    
    print(f"\n2. Resultado: {type(dados)}")
    if dados:
        print(f"\n3. Chaves: {dados.keys()}")
        print(f"\n4. Total de alunos: {dados.get('total_alunos')}")
        print(f"\n5. Alunos ativos: {dados.get('alunos_ativos')}")
        print(f"\n6. Alunos por série: {dados.get('alunos_por_serie')}")
        
        if dados.get('alunos_por_serie'):
            print(f"\n7. Primeira série: {dados['alunos_por_serie'][0]}")
    else:
        print("\n3. ERRO: dados retornados são None ou vazios")
        
except Exception as e:
    print(f"\nERRO CAPTURADO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("FIM DO TESTE")
print("="*60)
