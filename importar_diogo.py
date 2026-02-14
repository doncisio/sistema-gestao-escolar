"""
Importa DIOGO SANTOS SILVA com debug detalhado
"""
import json
from datetime import datetime
from db.connection import conectar_bd

def normalizar_nome_sistema_local(nome):
    """Padroniza nome no formato do sistema local"""
    if not nome:
        return ""
    nome = ' '.join(nome.split())
    palavras = nome.split()
    palavras_formatadas = []
    minusculas = ['da', 'de', 'do', 'das', 'dos', 'e']
    
    for palavra in palavras:
        if palavra.lower() in minusculas and len(palavras_formatadas) > 0:
            palavras_formatadas.append(palavra.lower())
        else:
            palavras_formatadas.append(palavra.capitalize())
    
    return ' '.join(palavras_formatadas)

# Carregar dados do GEDUC
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Procurar Diogo
diogo = None
for turma in data.get('turmas', []):
    for aluno in turma.get('alunos', []):
        if aluno['nome'].upper() == 'DIOGO SANTOS SILVA':
            diogo = aluno
            break
    if diogo:
        break

if not diogo:
    print("❌ Diogo Santos Silva não encontrado no GEDUC")
    exit()

print("="*80)
print("DADOS DO GEDUC - DIOGO SANTOS SILVA")
print("="*80)
for key, value in diogo.items():
    print(f"{key}: {value}")

print("\n" + "="*80)
print("TENTANDO IMPORTAR")
print("="*80)

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

try:
    nome = normalizar_nome_sistema_local(diogo['nome'])
    print(f"\nNome normalizado: {nome}")
    
    # Data de nascimento
    data_nascimento = diogo.get('data_nascimento')
    print(f"Data nascimento original: {data_nascimento}")
    
    if data_nascimento:
        try:
            if isinstance(data_nascimento, str):
                if '/' in data_nascimento:
                    data_nascimento = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
                else:
                    # Já está em formato YYYY-MM-DD
                    pass
        except Exception as e:
            print(f"⚠️  Erro ao converter data: {e}")
            data_nascimento = None
    
    print(f"Data nascimento convertida: {data_nascimento}")
    
    # Inferir sexo
    sexo = 'M'  # Diogo é masculino
    print(f"Sexo: {sexo}")
    
    cpf = diogo.get('cpf', '').strip()
    print(f"CPF: {cpf}")
    
    raca = 'pardo'
    descricao_transtorno = diogo.get('descricao_transtorno', 'Nenhum')
    escola_id = 60
    
    print(f"\nExecutando INSERT...")
    cursor.execute("""
        INSERT INTO Alunos (
            nome, data_nascimento, sexo, cpf, raca,
            descricao_transtorno, escola_id, local_nascimento, UF_nascimento
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        nome, data_nascimento, sexo,
        cpf if cpf else None,
        raca, descricao_transtorno, escola_id,
        'Paço do Lumiar', 'MA'
    ))
    
    aluno_id = cursor.lastrowid
    print(f"✅ Aluno inserido! ID: {aluno_id}")
    
    # Inserir responsáveis
    if diogo.get('mae'):
        print(f"\nInserindo mãe: {diogo['mae']}")
        cursor.execute("""
            INSERT INTO Responsaveis (nome, grau_parentesco)
            VALUES (%s, %s)
        """, (normalizar_nome_sistema_local(diogo['mae']), 'Mãe'))
        mae_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
            VALUES (%s, %s)
        """, (mae_id, aluno_id))
        print(f"✅ Mãe vinculada!")
    
    if diogo.get('pai'):
        print(f"\nInserindo pai: {diogo['pai']}")
        cursor.execute("""
            INSERT INTO Responsaveis (nome, grau_parentesco)
            VALUES (%s, %s)
        """, (normalizar_nome_sistema_local(diogo['pai']), 'Pai'))
        pai_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
            VALUES (%s, %s)
        """, (pai_id, aluno_id))
        print(f"✅ Pai vinculado!")
    
    conn.commit()
    print("\n✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ ERRO: {type(e).__name__}")
    print(f"Mensagem: {str(e)}")
    print(f"Detalhes: {repr(e)}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
