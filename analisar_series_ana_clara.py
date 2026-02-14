from db.connection import conectar_bd
from datetime import date

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# Info de Ana Clara
cursor.execute("""
    SELECT id, nome, data_nascimento, cpf
    FROM Alunos
    WHERE id = 2922
""")
ana = cursor.fetchone()

print("=" * 90)
print("ANA CLARA - ANÁLISE DE SÉRIES")
print("=" * 90)
print(f"\n📌 Dados atuais:")
print(f"   ID: {ana['id']}")
print(f"   Nome: {ana['nome']}")
print(f"   Data Nascimento: {ana['data_nascimento']}")
print(f"   CPF: {ana['cpf']}")

if ana['data_nascimento']:
    idade_2026 = 2026 - ana['data_nascimento'].year
    idade_2024 = 2024 - ana['data_nascimento'].year
    idade_2025 = 2025 - ana['data_nascimento'].year
    
    print(f"\n📅 Idades esperadas:")
    print(f"   2024: {idade_2024} anos → deveria estar no 7º ou 8º Ano")
    print(f"   2025: {idade_2025} anos → deveria estar no 8º ou 9º Ano")
    print(f"   2026: {idade_2026} anos → 9º Ano (confirmado pela matrícula)")

# Verificar tabela de séries
print(f"\n📚 Tabela de Séries no sistema:")
cursor.execute("SELECT id, nome FROM series ORDER BY id")
series = cursor.fetchall()
for s in series:
    print(f"   ID {s['id']:2d}: {s['nome']}")

# Histórico recuperado
print(f"\n📋 Histórico escolar recuperado (com serie_id incorreto?):")
cursor.execute("""
    SELECT DISTINCT h.ano_letivo_id, h.serie_id, s.nome as serie_nome, COUNT(*) as total
    FROM historico_escolar h
    JOIN series s ON h.serie_id = s.id
    WHERE h.aluno_id = 2922
    GROUP BY h.ano_letivo_id, h.serie_id, s.nome
    ORDER BY h.ano_letivo_id
""")
historico = cursor.fetchall()

for h in historico:
    print(f"   Ano {h['ano_letivo_id']} | Série ID {h['serie_id']:2d} ({h['serie_nome']:8s}) | {h['total']} disciplinas")

# Verificar dados originais do backup
print(f"\n⚠️  ANÁLISE:")
print(f"   Os registros recuperados mostram 1º Ano, mas Ana Clara nasceu em 2011")
print(f"   e deveria ter cursado 7º/8º anos em 2024-2025.")
print(f"\n   Possibilidades:")
print(f"   1. O ID 2058 era de outra pessoa (dados incorretos)")
print(f"   2. Os dados do backup estão corretos mas o serie_id mudou")
print(f"   3. Houve erro na migração/mapeamento de séries")

cursor.close()
conn.close()
