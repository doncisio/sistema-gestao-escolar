"""
Preenche os nomes das turmas no JSON do GEDUC baseado na idade predominante
dos alunos de cada turma (mais confiável que idade individual)
"""
import json
from collections import Counter

def calcular_idade_em_2026(data_nasc):
    """Calcula idade em 2026"""
    if not data_nasc or data_nasc == 'None':
        return None
    try:
        ano = int(data_nasc.split('-')[0])
        return 2026 - ano
    except:
        return None

def inferir_serie_por_idade_predominante(idades):
    """
    Infere série baseada na idade predominante da turma
    Em caso de empate, escolhe a MAIOR idade (mais provável ser a série correta)
    """
    if not idades:
        return "Série Não Identificada"
    
    # Contador de idades
    contador = Counter(idades)
    
    # Pega a frequência máxima
    max_freq = max(contador.values())
    
    # Em caso de empate, pega a MAIOR idade entre as mais comuns
    idades_empatadas = [idade for idade, freq in contador.items() if freq == max_freq]
    idade_comum = max(idades_empatadas)
    
    # Mapear idade para série
    mapa = {
        6: '1º Ano', 7: '1º Ano',
        8: '2º Ano',
        9: '3º Ano',
        10: '4º Ano',
        11: '5º Ano',
        12: '6º Ano',
        13: '7º Ano',
        14: '8º Ano',
        15: '9º Ano',
        16: '9º Ano'  # Repetentes
    }
    
    return mapa.get(idade_comum, f"Série Não Identificada (idade {idade_comum})")

print("="*80)
print("PREENCHENDO NOMES DAS TURMAS NO JSON")
print("="*80)

# Carregar JSON
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\nTotal de turmas: {len(data.get('turmas', []))}\n")

# Processar cada turma
turmas_atualizadas = 0

for turma in data.get('turmas', []):
    turma_id = turma.get('id')
    alunos = turma.get('alunos', [])
    
    if not alunos:
        print(f"⚠️  Turma {turma_id}: SEM ALUNOS")
        continue
    
    # Coletar idades dos alunos
    idades = []
    for aluno in alunos:
        idade = calcular_idade_em_2026(aluno.get('data_nascimento'))
        if idade:
            idades.append(idade)
    
    if not idades:
        print(f"⚠️  Turma {turma_id}: SEM DATAS DE NASCIMENTO")
        continue
    
    # Inferir série
    serie = inferir_serie_por_idade_predominante(idades)
    
    # Atualizar nome da turma
    turma['nome'] = serie
    turmas_atualizadas += 1
    
    # Estatísticas
    idade_min = min(idades)
    idade_max = max(idades)
    idade_media = sum(idades) / len(idades)
    contador = Counter(idades)
    
    print(f"Turma {turma_id}:")
    print(f"  → {serie}")
    print(f"  Alunos: {len(alunos)} | Idades: {idade_min}-{idade_max} (média: {idade_media:.1f})")
    print(f"  Distribuição: {dict(contador.most_common())}")
    print()

# Salvar JSON atualizado
backup_file = 'alunos_geduc_backup_sem_nomes.json'
output_file = 'alunos_geduc.json'

# Fazer backup
print("="*80)
print("SALVANDO ARQUIVO")
print("="*80)

with open(backup_file, 'w', encoding='utf-8') as f:
    # Recarregar original para backup
    with open(output_file, 'r', encoding='utf-8') as fo:
        data_original = json.load(fo)
    json.dump(data_original, f, ensure_ascii=False, indent=2)

print(f"✓ Backup salvo em: {backup_file}")

# Salvar atualizado
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✓ JSON atualizado salvo em: {output_file}")

print(f"\n{'='*80}")
print("RESUMO")
print("="*80)
print(f"Turmas atualizadas: {turmas_atualizadas}/{len(data.get('turmas', []))}")
print("="*80)
