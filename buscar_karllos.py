import json

with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for turma in data['turmas']:
    for aluno in turma['alunos']:
        if 'KARLLOS' in aluno['nome']:
            print(f"Turma ID: {turma['id']}")
            print(f"Turma Nome: {turma.get('nome', 'SEM NOME')}")
            print(f"\nDados do aluno:")
            for key, value in aluno.items():
                print(f"  {key}: {value}")
