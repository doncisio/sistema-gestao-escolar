"""Teste direto da função listar_turmas."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testando listar_turmas()...")

# Primeiro sem usuario logado/perfil
os.environ['SKIP_OPTIONAL_IMPORTS'] = '1'

try:
    from src.services.turma_service import listar_turmas
    
    # Desabilitar perfis temporariamente
    import json
    with open('feature_flags.json', 'r') as f:
        flags = json.load(f)
    
    original = flags['flags']['perfis_habilitados']['enabled']
    flags['flags']['perfis_habilitados']['enabled'] = False
    
    with open('feature_flags.json', 'w') as f:
        json.dump(flags, f, indent=2)
    
    print("Perfis desabilitados para teste")
    
    resultado = listar_turmas(aplicar_filtro_perfil=False)
    print(f"Tipo: {type(resultado)}")
    print(f"Tamanho: {len(resultado) if resultado else 'None'}")
    
    # Restaurar
    flags['flags']['perfis_habilitados']['enabled'] = original
    with open('feature_flags.json', 'w') as f:
        json.dump(flags, f, indent=2)
    print("Perfis restaurados")
    
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
