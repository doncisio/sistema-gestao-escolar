import json
from collections import Counter

with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*80)
print("ANÁLISE DAS CLASSIFICAÇÕES DAS TURMAS")
print("="*80)

for turma in data.get('turmas', []):
    turma_id = turma.get('id')
    turma_nome = turma.get('nome')
    alunos = turma.get('alunos', [])
    
    # Calcular idades
    idades = []
    for aluno in alunos:
        if aluno.get('data_nascimento'):
            ano = int(aluno['data_nascimento'].split('-')[0])
            idades.append(2026 - ano)
    
    contador = Counter(idades)
    idade_comum = contador.most_common(1)[0][0] if contador else None
    
    print(f"\nTurma {turma_id}: '{turma_nome}'")
    print(f"  Alunos: {len(alunos)}")
    print(f"  Distribuição de idades: {dict(contador.most_common())}")
    
    # Detectar empates
    if len(contador) > 1:
        valores = contador.values()
        max_freq = max(valores)
        idades_empatadas = [idade for idade, freq in contador.items() if freq == max_freq]
        
        if len(idades_empatadas) > 1:
            print(f"  ⚠️  EMPATE detectado! Idades {idades_empatadas} têm mesma frequência ({max_freq})")
            print(f"  Algoritmo escolheu: {idade_comum} anos → {turma_nome}")
            
            # Sugerir a maior idade em caso de empate
            idade_maior = max(idades_empatadas)
            mapa = {6: '1º Ano', 7: '1º Ano', 8: '2º Ano', 9: '3º Ano', 
                   10: '4º Ano', 11: '5º Ano', 12: '6º Ano', 13: '7º Ano',
                   14: '8º Ano', 15: '9º Ano'}
            serie_sugerida = mapa.get(idade_maior, 'Desconhecido')
            
            if serie_sugerida != turma_nome:
                print(f"  💡 SUGESTÃO: Usar idade {idade_maior} → {serie_sugerida}")

print("\n" + "="*80)
