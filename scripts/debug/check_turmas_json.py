import json

with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

turmas = data.get('turmas', [])
total = len(turmas)
vazios = sum(1 for t in turmas if not t.get('nome') or t.get('nome').strip() == '')

print(f"Total de turmas: {total}")
print(f"Turmas com nome vazio: {vazios}")
print(f"Turmas com nome preenchido: {total - vazios}")

if vazios == total:
    print("\n⚠️  TODOS os nomes de turmas estão vazios!")
    print("\nSolução: Executar novamente o importar_geduc.py (opção 1) para extrair os nomes das turmas")
    print("OU: Preencher manualmente baseado nos IDs das turmas")
