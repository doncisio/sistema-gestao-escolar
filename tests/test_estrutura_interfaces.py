"""
Testes para validar a estrutura das interfaces.

Este teste garante que não há código de inicialização
(criar_frames, criar_header, etc.) em lugares incorretos,
especialmente após statements `return` em métodos que não são __init__.
"""

import subprocess
import sys
from pathlib import Path


def test_validacao_estrutura_interfaces():
    """
    Testa se não há código de inicialização após returns nas interfaces.
    
    Este teste executa o script validar_estrutura_interfaces.py e verifica
    se todos os arquivos estão estruturados corretamente.
    
    O teste falha se:
    - Código de inicialização está após um return
    - Métodos como criar_frames() estão fora do __init__
    """
    # Caminho do script de validação
    script_path = Path(__file__).parent.parent / 'validar_estrutura_interfaces.py'
    
    # Executar o script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(script_path.parent)
    )
    
    # Verificar se encontrou "Nenhum problema encontrado"
    assert "[OK] Nenhum problema encontrado!" in result.stdout, \
        f"Problemas de estrutura encontrados nas interfaces:\n\n{result.stdout}\n\nErros:\n{result.stderr}"


def test_script_validacao_existe():
    """Verifica se o script de validação existe"""
    script_path = Path(__file__).parent.parent / 'validar_estrutura_interfaces.py'
    assert script_path.exists(), \
        f"Script de validação não encontrado: {script_path}"


def test_diretorio_interfaces_existe():
    """Verifica se o diretório de interfaces existe"""
    interfaces_dir = Path(__file__).parent.parent / 'src' / 'interfaces'
    assert interfaces_dir.exists(), \
        f"Diretório de interfaces não encontrado: {interfaces_dir}"
    
    # Verificar se há arquivos Python no diretório
    arquivos_python = list(interfaces_dir.glob('*.py'))
    assert len(arquivos_python) > 0, \
        "Nenhum arquivo Python encontrado em src/interfaces/"


if __name__ == '__main__':
    # Permite executar o teste diretamente
    import pytest
    pytest.main([__file__, '-v'])
