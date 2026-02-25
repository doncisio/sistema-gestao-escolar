"""
Script para importar KARLLOS AUGUSTO XIMENES DOS SANTOS com padronização de nomes
"""
import json
from db.connection import conectar_bd
from datetime import datetime

def capitalizar_nome_brasileiro(nome):
    """
    Capitaliza nome seguindo regras brasileiras:
    - Primeira letra de cada palavra maiúscula
    - Preposições (da, de, do, dos, das, e) em minúsculo (exceto início)
    """
    if not nome:
        return nome
    
    # Preposições que ficam em minúsculo
    preposicoes = {'da', 'de', 'do', 'dos', 'das', 'e'}
    
    partes = nome.strip().split()
    resultado = []
    
    for i, palavra in enumerate(partes):
        palavra_cap = palavra.capitalize()
        
        # Primeira palavra sempre maiúscula, demais preposições em minúsculo
        if i != 0 and palavra_cap.lower() in preposicoes:
            resultado.append(palavra_cap.lower())
        else:
            resultado.append(palavra_cap)
    
    return ' '.join(resultado)


def inferir_sexo_por_nome(nome_completo):
    """Infere sexo baseado no primeiro nome"""
    if not nome_completo:
        return 'M'
    
    primeiro_nome = nome_completo.strip().split()[0].upper()
    
    # Nomes masculinos comuns
    nomes_masculinos = {
        'KARLLOS', 'CARLOS', 'AUGUSTO', 'JOAO', 'JOSE', 'PEDRO', 'PAULO', 
        'LUCAS', 'MIGUEL', 'GABRIEL', 'RAFAEL', 'DANIEL', 'DIEGO', 'BRUNO',
        'FELIPE', 'GUSTAVO', 'HENRIQUE', 'RODRIGO', 'FERNANDO', 'MARCELO',
        'EDUARDO', 'LEONARDO', 'MATHEUS', 'GUILHERME', 'VITOR', 'CAIO',
        'THIAGO', 'ENZO', 'BENJAMIN', 'ARTHUR', 'DAVI', 'SAMUEL', 'NICOLAS',
        'EMANUEL', 'ERICK', 'HEITOR', 'BERNARDO', 'THEO', 'LORENZO', 'PIETRO',
        'JUAN', 'KAUAN', 'RYAN', 'ANTHONY', 'KEVIN', 'IAGO', 'JULIO', 'KALEB'
    }
    
    # Nomes femininos comuns
    nomes_femininos = {
        'MARIA', 'ANA', 'JULIA', 'BEATRIZ', 'LETICIA', 'LARISSA', 'FERNANDA',
        'AMANDA', 'JESSICA', 'MARIANA', 'GABRIELA', 'ISABELA', 'RAFAELA',
        'CAMILA', 'CAROLINA', 'SOPHIA', 'ALICE', 'VALENTINA', 'LAURA',
        'HELENA', 'LUIZA', 'VITORIA', 'YASMIN', 'LARA', 'REBECA', 'SARAH'
    }
    
    if primeiro_nome in nomes_masculinos:
        return 'M'
    elif primeiro_nome in nomes_femininos:
        return 'F'
    
    # Terminações típicas
    if primeiro_nome.endswith(('A', 'IA', 'NA', 'RA')):
        return 'F'
    
    return 'M'


def mapear_raca(codigo_cor):
    """Mapeia código de cor do GEDUC para raça no formato do banco"""
    mapa = {
        '0': 'pardo',       # Não declarada -> pardo (padrão)
        '1': 'branco',      # Branca
        '2': 'preto',       # Preta
        '3': 'pardo',       # Parda
        '4': 'amarelo',     # Amarela
        '5': 'indígena'     # Indígena
    }
    return mapa.get(str(codigo_cor), 'pardo')


print("="*80)
print("IMPORTAÇÃO: KARLLOS AUGUSTO XIMENES DOS SANTOS")
print("="*80)

# Buscar dados no JSON
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

aluno_geduc = None
for turma in data['turmas']:
    for aluno in turma['alunos']:
        if 'KARLLOS' in aluno['nome']:
            aluno_geduc = aluno
            break
    if aluno_geduc:
        break

if not aluno_geduc:
    print("❌ KARLLOS não encontrado no JSON!")
    exit(1)

print("\n📄 Dados do GEDUC:")
print(f"   Nome: {aluno_geduc['nome']}")
print(f"   CPF: {aluno_geduc['cpf']}")
print(f"   Data Nascimento: {aluno_geduc['data_nascimento']}")
print(f"   Mãe: {aluno_geduc.get('mae', 'NÃO INFORMADO')}")
print(f"   Pai: {aluno_geduc.get('pai', 'NÃO INFORMADO')}")

# Aplicar padronização
nome_padronizado = capitalizar_nome_brasileiro(aluno_geduc['nome'])
mae_padronizado = capitalizar_nome_brasileiro(aluno_geduc.get('mae', ''))
pai_padronizado = capitalizar_nome_brasileiro(aluno_geduc.get('pai', ''))
sexo_inferido = inferir_sexo_por_nome(nome_padronizado)
raca = mapear_raca(aluno_geduc.get('cor', '0'))

print("\n✨ Dados Padronizados:")
print(f"   Nome: {nome_padronizado}")
print(f"   Sexo: {sexo_inferido}")
print(f"   Raça: {raca}")
print(f"   Mãe: {mae_padronizado}")
print(f"   Pai: {pai_padronizado}")

# Confirmar importação
confirmacao = input("\n❓ Confirma importação? (S/N): ")
if confirmacao.upper() != 'S':
    print("❌ Importação cancelada")
    exit(0)

# Conectar ao banco
conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

try:
    # Verificar se já existe
    cpf_formatado = aluno_geduc['cpf']
    cursor.execute("SELECT id, nome FROM Alunos WHERE cpf = %s", (cpf_formatado,))
    existe = cursor.fetchone()
    
    if existe:
        print(f"\n⚠️  Aluno já existe: ID {existe['id']} - {existe['nome']}")
        print("❌ Importação cancelada")
        exit(1)
    
    # Inserir aluno
    query_aluno = """
        INSERT INTO Alunos (
            nome, data_nascimento, cpf, sexo, raca, escola_id
        ) VALUES (
            %s, %s, %s, %s, %s, %s
        )
    """
    
    valores = (
        nome_padronizado,
        aluno_geduc['data_nascimento'],
        cpf_formatado,
        sexo_inferido,
        raca,  # Já vem no formato correto do mapeamento
        60  # Escola padrão
    )
    
    cursor.execute(query_aluno, valores)
    aluno_id = cursor.lastrowid
    
    print(f"\n✅ Aluno importado com sucesso!")
    print(f"   ID: {aluno_id}")
    print(f"   Nome: {nome_padronizado}")
    
    # Inserir responsáveis se houver dados
    responsaveis_inseridos = 0
    
    if aluno_geduc.get('mae') and aluno_geduc.get('cpf_mae'):
        try:
            # Verificar se responsável já existe
            cursor.execute("SELECT id FROM Responsaveis WHERE cpf = %s", 
                         (aluno_geduc['cpf_mae'],))
            resp = cursor.fetchone()
            
            if resp:
                resp_id = resp['id']
            else:
                # Inserir responsável
                query_resp = """
                    INSERT INTO Responsaveis (nome, cpf, telefone, grau_parentesco)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_resp, (
                    mae_padronizado,
                    aluno_geduc['cpf_mae'],
                    aluno_geduc.get('celular', '') or None,
                    'Mãe'
                ))
                resp_id = cursor.lastrowid
            
            # Vincular
            cursor.execute("""
                INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
                VALUES (%s, %s)
            """, (resp_id, aluno_id))
            
            responsaveis_inseridos += 1
            print(f"   ✓ Mãe vinculada: {mae_padronizado}")
        except Exception as e:
            print(f"   ⚠️  Erro ao vincular mãe: {e}")
    
    if aluno_geduc.get('pai') and aluno_geduc.get('cpf_pai'):
        try:
            # Verificar se responsável já existe
            cursor.execute("SELECT id FROM Responsaveis WHERE cpf = %s", 
                         (aluno_geduc['cpf_pai'],))
            resp = cursor.fetchone()
            
            if resp:
                resp_id = resp['id']
            else:
                # Inserir responsável
                query_resp = """
                    INSERT INTO Responsaveis (nome, cpf, telefone, grau_parentesco)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_resp, (
                    pai_padronizado,
                    aluno_geduc['cpf_pai'],
                    aluno_geduc.get('celular', '') or None,
                    'Pai'
                ))
                resp_id = cursor.lastrowid
            
            # Vincular
            cursor.execute("""
                INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
                VALUES (%s, %s)
            """, (resp_id, aluno_id))
            
            responsaveis_inseridos += 1
            print(f"   ✓ Pai vinculado: {pai_padronizado}")
        except Exception as e:
            print(f"   ⚠️  Erro ao vincular pai: {e}")
    
    conn.commit()
    
    print(f"\n✅ Importação concluída!")
    print(f"   Total responsáveis: {responsaveis_inseridos}")
    print("="*80)

except Exception as e:
    print(f"\n❌ Erro durante importação: {e}")
    conn.rollback()
    import traceback
    traceback.print_exc()

finally:
    cursor.close()
    conn.close()
