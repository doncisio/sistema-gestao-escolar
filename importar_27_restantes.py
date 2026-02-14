"""
Importa os 27 alunos restantes do GEDUC
Verifica CPF antes de importar para evitar duplicatas
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

def mapear_raca(raca_geduc):
    """Mapeia raça do GEDUC para o sistema local"""
    if not raca_geduc:
        return 'pardo'
    
    raca_lower = raca_geduc.lower().strip()
    mapa = {
        'parda': 'pardo', 'pardo': 'pardo',
        'branca': 'branco', 'branco': 'branco',
        'preta': 'preto', 'preto': 'preto',
        'negra': 'preto', 'negro': 'preto',
        'indígena': 'indígena', 'indigena': 'indígena',
        'amarela': 'amarelo', 'amarelo': 'amarelo',
        'não declarada': 'pardo', 'nao declarada': 'pardo'
    }
    return mapa.get(raca_lower, 'pardo')

def inferir_sexo_por_nome(nome):
    """Infere sexo pelo nome"""
    if not nome:
        return 'M'
    
    primeiro_nome = nome.split()[0].lower()
    
    nomes_femininos = [
        'ana', 'maria', 'sarah', 'sara', 'rebeca', 'pietra', 'lara', 
        'isadora', 'gabrielly', 'glenda', 'esther', 'marcelly', 'rita',
        'natalia', 'bruna', 'candida', 'yasmin', 'valentina', 'iara'
    ]
    
    nomes_masculinos = [
        'benjamin', 'enzo', 'fernando', 'guilherme', 'henzo', 'igor',
        'joao', 'joão', 'kauan', 'mikael', 'noah', 'deyvison', 'pedro',
        'john', 'juan', 'kaua'
    ]
    
    if primeiro_nome in nomes_femininos:
        return 'F'
    if primeiro_nome in nomes_masculinos:
        return 'M'
    
    # Verificar terminações
    if primeiro_nome.endswith(('a', 'ella', 'elly', 'bela', 'bella', 'issa', 'isa')):
        return 'F'
    if primeiro_nome.endswith(('o', 'el', 'son', 'nho')):
        return 'M'
    
    return 'M'

def cpf_ja_existe(cursor, cpf):
    """Verifica se CPF já existe no banco"""
    if not cpf or cpf.strip() == '':
        return False
    
    cursor.execute("SELECT id FROM Alunos WHERE cpf = %s", (cpf.strip(),))
    return cursor.fetchone() is not None

def importar_aluno(cursor, aluno_geduc, conn):
    """Importa um aluno do GEDUC"""
    nome = normalizar_nome_sistema_local(aluno_geduc['nome'])
    
    # Verificar CPF
    cpf = aluno_geduc.get('cpf', '').strip()
    if cpf_ja_existe(cursor, cpf):
        return None, f"CPF {cpf} já existe"
    
    # Data de nascimento
    data_nascimento = aluno_geduc.get('data_nascimento')
    if data_nascimento and isinstance(data_nascimento, str):
        try:
            if '/' in data_nascimento:
                data_nascimento = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
        except:
            data_nascimento = None
    
    sexo = inferir_sexo_por_nome(nome)
    raca = mapear_raca(aluno_geduc.get('raca', 'pardo'))
    descricao_transtorno = aluno_geduc.get('descricao_transtorno', 'Nenhum')
    escola_id = 60
    
    # Inserir aluno
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
    
    # Inserir responsáveis
    responsaveis_inseridos = 0
    
    # Mãe
    if aluno_geduc.get('mae'):
        try:
            cursor.execute("""
                INSERT INTO Responsaveis (nome, cpf, grau_parentesco)
                VALUES (%s, %s, %s)
            """, (
                normalizar_nome_sistema_local(aluno_geduc['mae']),
                aluno_geduc.get('cpf_mae', '').strip() or None,
                'Mãe'
            ))
            mae_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
                VALUES (%s, %s)
            """, (mae_id, aluno_id))
            responsaveis_inseridos += 1
        except:
            pass
    
    # Pai
    if aluno_geduc.get('pai'):
        try:
            cursor.execute("""
                INSERT INTO Responsaveis (nome, cpf, grau_parentesco)
                VALUES (%s, %s, %s)
            """, (
                normalizar_nome_sistema_local(aluno_geduc['pai']),
                aluno_geduc.get('cpf_pai', '').strip() or None,
                'Pai'
            ))
            pai_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
                VALUES (%s, %s)
            """, (pai_id, aluno_id))
            responsaveis_inseridos += 1
        except:
            pass
    
    return aluno_id, responsaveis_inseridos

# Carregar dados do GEDUC
print("="*80)
print("IMPORTAÇÃO DOS 27 ALUNOS RESTANTES DO GEDUC")
print("="*80)
print("\nCarregando dados do GEDUC...")

with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extrair todos os alunos
alunos_geduc = []
for turma in data.get('turmas', []):
    alunos_geduc.extend(turma.get('alunos', []))

print(f"✓ {len(alunos_geduc)} alunos carregados do GEDUC\n")

# Conectar ao banco
conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

print("Processando alunos...\n")

importados = 0
ja_existem = 0
erros = []

for idx, aluno_geduc in enumerate(alunos_geduc, 1):
    nome_original = aluno_geduc['nome']
    cpf = aluno_geduc.get('cpf', '').strip()
    
    try:
        # Verificar se CPF já existe
        if cpf and cpf_ja_existe(cursor, cpf):
            ja_existem += 1
            continue
        
        # Importar aluno
        aluno_id, resp_count = importar_aluno(cursor, aluno_geduc, conn)
        
        if aluno_id:
            conn.commit()
            importados += 1
            nome_formatado = normalizar_nome_sistema_local(nome_original)
            print(f"[{importados:02d}] ✅ {nome_formatado}")
            print(f"     ID: {aluno_id} | CPF: {cpf or 'SEM CPF'} | Responsáveis: {resp_count}\n")
        else:
            ja_existem += 1
            
    except Exception as e:
        erros.append({
            'nome': nome_original,
            'cpf': cpf,
            'erro': str(e)
        })
        conn.rollback()
        print(f"❌ {nome_original}")
        print(f"   ERRO: {str(e)}\n")

cursor.close()
conn.close()

print("="*80)
print("RESUMO DA IMPORTAÇÃO")
print("="*80)
print(f"Total de alunos no GEDUC: {len(alunos_geduc)}")
print(f"✅ Importados agora: {importados}")
print(f"ℹ️  Já existiam (pulados): {ja_existem}")
print(f"❌ Erros: {len(erros)}")

if erros:
    print("\nAlunos com erro:")
    for erro in erros:
        nome_errado = erro['nome']
        print(f"  - {nome_errado}")
        print(f"    CPF: {erro['cpf']}")
        print(f"    Erro: {erro['erro']}")

print("\n✓ Importação concluída!")
print("="*80)
print("\n⚠️  ATENÇÃO: As matrículas devem ser criadas manualmente.")
print("   Os alunos foram cadastrados, mas ainda não estão matriculados em 2026.\n")
