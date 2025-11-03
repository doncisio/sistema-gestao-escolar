from controllers.aluno_controller import AlunoController
from controllers.frequencia_controller import FrequenciaController

def test_get_alunos_por_turma():
    # Testando o método diretamente da classe AlunoController
    aluno_controller = AlunoController()
    
    # Testando para uma turma específica (ID 28)
    turma_id = 28
    print(f"\nTestando AlunoController.get_by_turma(turma_id={turma_id}):")
    alunos = aluno_controller.get_by_turma(turma_id)
    print(f"Total de alunos obtidos: {len(alunos)}")
    for i, aluno in enumerate(alunos[:5], 1):  # Mostrar apenas os primeiros 5 para não sobrecarregar o console
        print(f"{i}. ID: {aluno['id']}, Nome: {aluno['nome']}")
    
    if len(alunos) > 5:
        print(f"...e mais {len(alunos) - 5} alunos")
    
    # Testando como o método é chamado pelo FrequenciaController
    freq_controller = FrequenciaController()
    
    print(f"\nTestando FrequenciaController.get_alunos_por_turma(turma_id={turma_id}):")
    alunos_via_freq = freq_controller.get_alunos_por_turma(turma_id)
    print(f"Total de alunos obtidos via FrequenciaController: {len(alunos_via_freq)}")
    for i, aluno in enumerate(alunos_via_freq[:5], 1):  # Mostrar apenas os primeiros 5
        print(f"{i}. ID: {aluno['id']}, Nome: {aluno['nome']}")
    
    if len(alunos_via_freq) > 5:
        print(f"...e mais {len(alunos_via_freq) - 5} alunos")
    
    # Comparar os resultados
    if len(alunos) != len(alunos_via_freq):
        print(f"\nAlerta: Os métodos retornam quantidades diferentes de alunos! ({len(alunos)} vs {len(alunos_via_freq)})")
    else:
        print(f"\nOs dois métodos retornam a mesma quantidade de alunos: {len(alunos)}")

if __name__ == "__main__":
    test_get_alunos_por_turma() 