from src.core.conexao import conectar_bd
from datetime import date

def calcular_idade_data_corte(data_nascimento, ano_referencia):
    """Calcula idade na data de corte 31/03"""
    data_corte = date(ano_referencia, 3, 31)
    idade = data_corte.year - data_nascimento.year
    if (data_corte.month, data_corte.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# Buscar todos os alunos do 8º ano
cursor.execute('''
    SELECT a.id, a.nome, a.data_nascimento, m.status, t.nome as turma
    FROM Alunos a
    JOIN Matriculas m ON a.id = m.aluno_id
    JOIN Turmas t ON m.turma_id = t.id
    JOIN series s ON t.serie_id = s.id
    JOIN AnosLetivos al ON m.ano_letivo_id = al.id
    WHERE a.escola_id = 60
    AND al.ano_letivo = 2026
    AND m.status = 'Ativo'
    AND s.id = 10
    ORDER BY a.data_nascimento
''')

alunos = cursor.fetchall()
print(f'Total de alunos do 8º ano: {len(alunos)}\n')

print('Alunos em distorção (2+ anos):')
count = 0
for aluno in alunos:
    idade = calcular_idade_data_corte(aluno['data_nascimento'], 2026)
    distorcao = idade - 13  # idade ideal do 8º ano
    if distorcao >= 2:
        count += 1
        print(f"{aluno['nome']}")
        print(f"  Nascimento: {aluno['data_nascimento']} | Idade: {idade} | Distorção: {distorcao} anos")
        print(f"  Turma: {aluno['turma']}")
        print()

print(f'Total em distorção 2+: {count}')

cursor.close()
conn.close()
