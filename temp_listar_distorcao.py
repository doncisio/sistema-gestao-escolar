from src.relatorios.listas.lista_distorcao_fluxo import obter_alunos_distorcao

alunos = obter_alunos_distorcao(60, 2026, 2)

print(f'Total de alunos em distorção (2+ anos): {len(alunos)}\n')

# Agrupar por série
series = {}
for aluno in alunos:
    serie = aluno['serie_nome']
    if serie not in series:
        series[serie] = []
    series[serie].append(aluno)

# Mostrar por série
for serie in sorted(series.keys()):
    print(f'\n{serie}: {len(series[serie])} alunos')
    for aluno in series[serie]:
        print(f'  {aluno["nome"]} - Nasc: {aluno["data_nascimento"]} - Idade: {aluno["idade"]} - Distorção: {aluno["anos_distorcao"]} anos')
