import re
import mysql.connector
from datetime import datetime

# Ler o backup e procurar pela linha de historico_escolar
print("📂 Lendo arquivo de backup...")
with open(r'C:\gestao\backup_redeescola.sql', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Procurar pela linha INSERT INTO historico_escolar
print("🔍 Procurando linha de historico_escolar...")
pattern = r"INSERT INTO `historico_escolar` VALUES (.+?);"
match = re.search(pattern, content, re.DOTALL)

if not match:
    print("❌ Não encontrou a linha de historico_escolar no backup")
    exit(1)

valores_str = match.group(1)
print(f"✓ Linha encontrada (tamanho: {len(valores_str)} caracteres)")

# Parsear todos os registros
print("📊 Parseando registros...")
# ESTRUTURA CORRETA DO BACKUP (igual à atual):
# (id, aluno_id, disciplina_id, media, ano_letivo_id, escola_id, conceito, serie_id)
registros_pattern = r'\((\d+),(\d+),(\d+),([\d.]+|NULL),(\d+),(\d+),(?:\'([^\']*?)\'|NULL),(\d+)\)'
registros = re.findall(registros_pattern, valores_str)

print(f"✓ Total de registros parseados: {len(registros)}")

# Filtrar registros com aluno_id = 2058
registros_2058 = [r for r in registros if r[1] == '2058']
print(f"✓ Encontrados {len(registros_2058)} registros para aluno_id 2058")

if len(registros_2058) == 0:
    print("❌ Nenhum registro encontrado para ID 2058")
    exit(1)

# Mostrar os registros encontrados COM O MAPEAMENTO CORRETO
print("\n📋 Registros encontrados (mapeamento CORRETO):")
print("-" * 100)
for r in registros_2058:
    id_hist, aluno_id, disciplina_id, media, ano_letivo, escola_id, conceito, serie_id = r
    print(f"ID: {id_hist}, Ano: {ano_letivo}, Escola: {escola_id}, Série: {serie_id}, Disciplina: {disciplina_id}, Média: {media}, Conceito: {conceito or 'NULL'}")

# Conectar ao banco
print("\n💾 Conectando ao banco de dados...")
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='987412365',
        database='redeescola'
    )
    cursor = conn.cursor()
    
    # DELETAR os registros inseridos incorretamente
    print("\n🗑️  Deletando registros inseridos incorretamente...")
    cursor.execute("DELETE FROM historico_escolar WHERE aluno_id = 2922")
    deletados = cursor.rowcount
    print(f"✓ {deletados} registros deletados")
    
    # Preparar os valores para inserção CORRETA (aluno_id mudado de 2058 para 2922)
    valores_insert = []
    for r in registros_2058:
        id_hist, _, disciplina_id, media, ano_letivo, escola_id, conceito, serie_id = r
        # Converter NULL e conceito vazio
        media_val = None if media == 'NULL' else float(media)
        conceito_val = None if (conceito == '' or conceito == 'NULL') else conceito
        
        valores_insert.append((
            2922,  # Novo aluno_id
            int(disciplina_id),
            media_val,
            int(ano_letivo),
            int(escola_id),  # escola_id CORRETO (era r[5])
            conceito_val,
            int(serie_id)    # serie_id CORRETO (era r[7])
        ))
    
    # Inserir os registros
    sql = """
        INSERT INTO historico_escolar 
        (aluno_id, disciplina_id, media, ano_letivo_id, escola_id, conceito, serie_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.executemany(sql, valores_insert)
    conn.commit()
    
    print(f"✅ {cursor.rowcount} registros inseridos CORRETAMENTE para Ana Clara (ID 2922)!")
    
    # Verificar com detalhes
    cursor.execute("""
        SELECT h.ano_letivo_id, s.nome as serie, COUNT(*) as total
        FROM historico_escolar h
        JOIN series s ON h.serie_id = s.id
        WHERE h.aluno_id = 2922
        GROUP BY h.ano_letivo_id, s.nome
        ORDER BY h.ano_letivo_id
    """)
    print("\n📊 Registros por ano/série:")
    for row in cursor.fetchall():
        print(f"   Ano {row[0]}: {row[1]:10s} - {row[2]} disciplinas")
    
    cursor.close()
    conn.close()
    
except mysql.connector.Error as err:
    print(f"❌ Erro ao conectar/inserir: {err}")
    exit(1)

print("\n🎉 Correção concluída!")
