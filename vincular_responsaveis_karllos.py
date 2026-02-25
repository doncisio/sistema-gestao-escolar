"""
Script para vincular responsáveis ao Karllos Augusto
"""
from db.connection import conectar_bd

def capitalizar_nome_brasileiro(nome):
    """Capitaliza nome seguindo regras brasileiras"""
    if not nome:
        return nome
    
    preposicoes = {'da', 'de', 'do', 'dos', 'das', 'e'}
    partes = nome.strip().split()
    resultado = []
    
    for i, palavra in enumerate(partes):
        palavra_cap = palavra.capitalize()
        if i != 0 and palavra_cap.lower() in preposicoes:
            resultado.append(palavra_cap.lower())
        else:
            resultado.append(palavra_cap)
    
    return ' '.join(resultado)

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

aluno_id = 2924
mae_nome = capitalizar_nome_brasileiro("PATRICIA NASCIMENTO XIMENES")
pai_nome = capitalizar_nome_brasileiro("CAROS ANDRE MENDES DOS SANTOS")
celular = ""  # Não tem no GEDUC

print("="*80)
print(f"VINCULANDO RESPONSÁVEIS - Aluno ID: {aluno_id}")
print("="*80)

# Verificar responsáveis atuais
cursor.execute("""
    SELECT r.id, r.nome, r.cpf, r.grau_parentesco 
    FROM ResponsaveisAlunos ra 
    JOIN Responsaveis r ON ra.responsavel_id = r.id 
    WHERE ra.aluno_id = %s
""", (aluno_id,))

responsaveis_atuais = cursor.fetchall()
print(f"\n📋 Responsáveis atuais: {len(responsaveis_atuais)}")
for resp in responsaveis_atuais:
    print(f"   - {resp['nome']} ({resp['grau_parentesco']})")

# Inserir Mãe
print(f"\n👩 Inserindo MÃE: {mae_nome}")
try:
    # Verificar se já existe pelo nome
    cursor.execute("""
        SELECT id FROM Responsaveis 
        WHERE UPPER(TRIM(nome)) = UPPER(TRIM(%s))
    """, (mae_nome,))
    
    resp_existente = cursor.fetchone()
    
    if resp_existente:
        mae_id = resp_existente['id']
        print(f"   ✓ Responsável já existe (ID: {mae_id})")
    else:
        # Inserir novo responsável
        cursor.execute("""
            INSERT INTO Responsaveis (nome, grau_parentesco, telefone)
            VALUES (%s, %s, %s)
        """, (mae_nome, 'Mãe', celular if celular else None))
        mae_id = cursor.lastrowid
        print(f"   ✓ Responsável criado (ID: {mae_id})")
    
    # Verificar se já está vinculado
    cursor.execute("""
        SELECT 1 FROM ResponsaveisAlunos 
        WHERE responsavel_id = %s AND aluno_id = %s
    """, (mae_id, aluno_id))
    
    if cursor.fetchone():
        print(f"   ⚠️  Já vinculado ao aluno")
    else:
        # Vincular
        cursor.execute("""
            INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
            VALUES (%s, %s)
        """, (mae_id, aluno_id))
        print(f"   ✅ Vinculado com sucesso!")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Inserir Pai
print(f"\n👨 Inserindo PAI: {pai_nome}")
try:
    # Verificar se já existe pelo nome
    cursor.execute("""
        SELECT id FROM Responsaveis 
        WHERE UPPER(TRIM(nome)) = UPPER(TRIM(%s))
    """, (pai_nome,))
    
    resp_existente = cursor.fetchone()
    
    if resp_existente:
        pai_id = resp_existente['id']
        print(f"   ✓ Responsável já existe (ID: {pai_id})")
    else:
        # Inserir novo responsável
        cursor.execute("""
            INSERT INTO Responsaveis (nome, grau_parentesco, telefone)
            VALUES (%s, %s, %s)
        """, (pai_nome, 'Pai', celular if celular else None))
        pai_id = cursor.lastrowid
        print(f"   ✓ Responsável criado (ID: {pai_id})")
    
    # Verificar se já está vinculado
    cursor.execute("""
        SELECT 1 FROM ResponsaveisAlunos 
        WHERE responsavel_id = %s AND aluno_id = %s
    """, (pai_id, aluno_id))
    
    if cursor.fetchone():
        print(f"   ⚠️  Já vinculado ao aluno")
    else:
        # Vincular
        cursor.execute("""
            INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
            VALUES (%s, %s)
        """, (pai_id, aluno_id))
        print(f"   ✅ Vinculado com sucesso!")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Commit
conn.commit()

# Verificar resultado final
cursor.execute("""
    SELECT r.id, r.nome, r.cpf, r.grau_parentesco 
    FROM ResponsaveisAlunos ra 
    JOIN Responsaveis r ON ra.responsavel_id = r.id 
    WHERE ra.aluno_id = %s
""", (aluno_id,))

responsaveis_finais = cursor.fetchall()
print(f"\n✅ Responsáveis finais: {len(responsaveis_finais)}")
for resp in responsaveis_finais:
    cpf_display = resp['cpf'] if resp['cpf'] else 'SEM CPF'
    print(f"   - {resp['nome']} ({resp['grau_parentesco']}) - {cpf_display}")

print("="*80)

cursor.close()
conn.close()
