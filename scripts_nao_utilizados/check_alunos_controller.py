import os
import sys
from config_logs import get_logger
logger = get_logger(__name__)

# Garantir que a raiz do projeto esteja no `sys.path` para resolver imports locais
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# As importações abaixo podem não ser resolvidas pelo Pylance em scripts fora
# da raiz do projeto. O comentário `# type: ignore` suprime o aviso de
# "reportMissingImports" no editor; ao mesmo tempo, o `sys.path` acima
# permite que a importação funcione em tempo de execução.
from controllers.aluno_controller import AlunoController  # type: ignore
from controllers.frequencia_controller import FrequenciaController  # type: ignore

def test_get_alunos_por_turma():
    # Testando o método diretamente da classe AlunoController
    aluno_controller = AlunoController()
    
    # Testando para uma turma específica (ID 28)
    turma_id = 28
    logger.info(f"\nTestando AlunoController.get_by_turma(turma_id={turma_id}):")
    alunos = aluno_controller.get_by_turma(turma_id)
    logger.info(f"Total de alunos obtidos: {len(alunos)}")
    for i, aluno in enumerate(alunos[:5], 1):  # Mostrar apenas os primeiros 5 para não sobrecarregar o console
        logger.info(f"{i}. ID: {aluno['id']}, Nome: {aluno['nome']}")
    
    if len(alunos) > 5:
        logger.info(f"...e mais {len(alunos) - 5} alunos")
    
    # Testando como o método é chamado pelo FrequenciaController
    freq_controller = FrequenciaController()
    
    logger.info(f"\nTestando FrequenciaController.get_alunos_por_turma(turma_id={turma_id}):")
    alunos_via_freq = freq_controller.get_alunos_por_turma(turma_id)
    logger.info(f"Total de alunos obtidos via FrequenciaController: {len(alunos_via_freq)}")
    for i, aluno in enumerate(alunos_via_freq[:5], 1):  # Mostrar apenas os primeiros 5
        logger.info(f"{i}. ID: {aluno['id']}, Nome: {aluno['nome']}")
    
    if len(alunos_via_freq) > 5:
        logger.info(f"...e mais {len(alunos_via_freq) - 5} alunos")
    
    # Comparar os resultados
    if len(alunos) != len(alunos_via_freq):
        logger.info(f"\nAlerta: Os métodos retornam quantidades diferentes de alunos! ({len(alunos)} vs {len(alunos_via_freq)})")
    else:
        logger.info(f"\nOs dois métodos retornam a mesma quantidade de alunos: {len(alunos)}")

if __name__ == "__main__":
    test_get_alunos_por_turma() 