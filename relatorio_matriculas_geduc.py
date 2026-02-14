"""
Gera relatório Excel comparando matrículas do Sistema Local vs GEDUC
- Aba 1: Alunos com série divergente (matriculados em série diferente)
- Aba 2: Alunos sem matrícula em 2026 (com série do GEDUC)
"""
import json
import unicodedata
from datetime import datetime
from db.connection import conectar_bd
import pandas as pd

def normalizar_nome(nome):
    """Remove acentos e normaliza"""
    if not nome:
        return ""
    nfkd = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return nome_sem_acento.upper().strip()

def inferir_serie_por_idade(data_nascimento):
    """
    Infere a série esperada em 2026 baseado na data de nascimento
    Lógica: idade ideal para cada série
    """
    if not data_nascimento:
        return "SEM DATA DE NASCIMENTO"
    
    try:
        # Converter data para calcular idade
        if isinstance(data_nascimento, str):
            if '-' in data_nascimento:
                ano_nasc = int(data_nascimento.split('-')[0])
            else:
                return "DATA INVÁLIDA"
        else:
            return "DATA INVÁLIDA"
        
        # Calcular idade em 2026
        idade_em_2026 = 2026 - ano_nasc
        
        # Mapear idade para série (considerando ingresso aos 6 anos no 1º ano)
        # Idade 7 → 1º Ano, Idade 8 → 2º Ano, etc.
        if idade_em_2026 == 7:
            return '1º Ano'
        elif idade_em_2026 == 8:
            return '2º Ano'
        elif idade_em_2026 == 9:
            return '3º Ano'
        elif idade_em_2026 == 10:
            return '4º Ano'
        elif idade_em_2026 == 11:
            return '5º Ano'
        elif idade_em_2026 == 12:
            return '6º Ano'
        elif idade_em_2026 == 13:
            return '7º Ano'
        elif idade_em_2026 == 14:
            return '8º Ano'
        elif idade_em_2026 == 15:
            return '9º Ano'
        elif idade_em_2026 == 6:
            return '1º Ano'  # Pode estar iniciando
        elif idade_em_2026 > 15:
            return f'9º Ano (idade {idade_em_2026})'
        elif idade_em_2026 < 6:
            return f'Pré-escola (idade {idade_em_2026})'
        else:
            return f"Idade {idade_em_2026}"
            
    except:
        return "ERRO AO CALCULAR"

print("="*80)
print("RELATÓRIO DE MATRÍCULAS: SISTEMA LOCAL vs GEDUC")
print("="*80)

# Carregar alunos do GEDUC
print("\n📂 Carregando dados do GEDUC...")
with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Criar dicionário de alunos GEDUC com suas séries
alunos_geduc_dict = {}
for turma in data.get('turmas', []):
    turma_id = turma.get('id', '')
    turma_nome = turma.get('nome', '')  # Nome da turma já preenchido (ex: "8º Ano")
    
    # Usar o nome da turma como série (mais confiável que idade individual)
    serie_geduc = turma_nome if turma_nome else 'Série Não Identificada'
    
    for aluno in turma.get('alunos', []):
        nome_norm = normalizar_nome(aluno['nome'])
        cpf = aluno.get('cpf', '').strip()
        data_nasc = aluno.get('data_nascimento', '')
        
        alunos_geduc_dict[nome_norm] = {
            'nome': aluno['nome'],
            'cpf': cpf,
            'turma_id_geduc': turma_id,
            'turma_nome_geduc': turma_nome,
            'data_nascimento': data_nasc,
            'serie_geduc': serie_geduc
        }
        
        # Adicionar também por CPF se disponível
        if cpf:
            alunos_geduc_dict[cpf] = alunos_geduc_dict[nome_norm]

print(f"✓ {len(data.get('turmas', []))} turmas carregadas do GEDUC")

# Buscar alunos do sistema local
print("\n📂 Carregando dados do Sistema Local...")
conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# Buscar ID do ano letivo 2026
cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = 2026")
ano_2026 = cursor.fetchone()
ano_letivo_id = ano_2026['id'] if ano_2026 else None

if not ano_letivo_id:
    print("❌ ERRO: Ano letivo 2026 não encontrado!")
    cursor.close()
    conn.close()
    exit()

# Buscar todos os alunos da escola 60
cursor.execute("""
    SELECT 
        a.id AS aluno_id,
        a.nome AS nome,
        a.cpf AS cpf,
        m.id AS matricula_id,
        m.status AS status_matricula,
        s.nome AS serie_local,
        t.nome AS turma_local,
        t.turno AS turno
    FROM Alunos a
    LEFT JOIN Matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s
    LEFT JOIN Turmas t ON m.turma_id = t.id
    LEFT JOIN series s ON t.serie_id = s.id
    WHERE a.escola_id = 60
    ORDER BY a.nome
""", (ano_letivo_id,))

alunos_local = cursor.fetchall()

print(f"✓ {len(alunos_local)} alunos encontrados no Sistema Local")

cursor.close()
conn.close()

# Processar comparações
print("\n⚙️  Processando comparações...")

alunos_divergentes = []  # Matriculados mas em série diferente
alunos_sem_matricula = []  # Sem matrícula em 2026

for aluno_local in alunos_local:
    nome_norm = normalizar_nome(aluno_local['nome'])
    cpf = aluno_local['cpf']
    
    # Buscar aluno no GEDUC
    aluno_geduc = None
    
    # Buscar por CPF primeiro
    if cpf and cpf in alunos_geduc_dict:
        aluno_geduc = alunos_geduc_dict[cpf]
    # Buscar por nome
    elif nome_norm in alunos_geduc_dict:
        aluno_geduc = alunos_geduc_dict[nome_norm]
    
    # Se aluno está no GEDUC
    if aluno_geduc:
        tem_matricula = aluno_local['matricula_id'] is not None
        
        if tem_matricula:
            # Verificar se série é diferente
            serie_local = aluno_local['serie_local']
            serie_geduc = aluno_geduc['serie_geduc']
            
            if serie_local != serie_geduc:
                alunos_divergentes.append({
                    'ID': aluno_local['aluno_id'],
                    'Nome': aluno_local['nome'],
                    'CPF': cpf or '',
                    'Série Atual (Sistema)': serie_local or 'SEM SÉRIE',
                    'Turma Atual (Sistema)': aluno_local['turma_local'] or '',
                    'Turno Atual': aluno_local['turno'] or '',
                    'Status': aluno_local['status_matricula'],
                    'Série GEDUC (Correto)': serie_geduc,
                    'Turma GEDUC': aluno_geduc.get('turma_nome_geduc', ''),
                    'Turma GEDUC ID': aluno_geduc['turma_id_geduc'],
                    'Data Nascimento': aluno_geduc['data_nascimento'],
                    'Situação': '⚠️ SÉRIE DIVERGENTE'
                })
        else:
            # Sem matrícula em 2026
            alunos_sem_matricula.append({
                'ID': aluno_local['aluno_id'],
                'Nome': aluno_local['nome'],
                'CPF': cpf or '',
                'Série GEDUC (Matricular em)': aluno_geduc['serie_geduc'],
                'Turma GEDUC': aluno_geduc.get('turma_nome_geduc', ''),
                'Turma GEDUC ID': aluno_geduc['turma_id_geduc'],
                'Data Nascimento': aluno_geduc['data_nascimento'],
                'Situação': '📝 SEM MATRÍCULA 2026'
            })

print(f"\n✓ Processamento concluído!")
print(f"   - Alunos com série divergente: {len(alunos_divergentes)}")
print(f"   - Alunos sem matrícula: {len(alunos_sem_matricula)}")

# Gerar Excel
print("\n📊 Gerando arquivo Excel...")

nome_arquivo = f"RELATORIO_MATRICULAS_GEDUC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
    # Aba 1: Alunos com série divergente
    if alunos_divergentes:
        df_divergentes = pd.DataFrame(alunos_divergentes)
        df_divergentes.to_excel(writer, sheet_name='Séries Divergentes', index=False)
        print(f"   ✓ Aba 'Séries Divergentes': {len(alunos_divergentes)} registros")
    else:
        # Criar aba vazia
        df_vazio = pd.DataFrame({'Mensagem': ['✅ Nenhuma divergência encontrada!']})
        df_vazio.to_excel(writer, sheet_name='Séries Divergentes', index=False)
        print(f"   ✓ Aba 'Séries Divergentes': Sem divergências")
    
    # Aba 2: Alunos sem matrícula
    if alunos_sem_matricula:
        df_sem_matricula = pd.DataFrame(alunos_sem_matricula)
        df_sem_matricula.to_excel(writer, sheet_name='Sem Matrícula 2026', index=False)
        print(f"   ✓ Aba 'Sem Matrícula 2026': {len(alunos_sem_matricula)} registros")
    else:
        # Criar aba vazia
        df_vazio = pd.DataFrame({'Mensagem': ['✅ Todos os alunos possuem matrícula!']})
        df_vazio.to_excel(writer, sheet_name='Sem Matrícula 2026', index=False)
        print(f"   ✓ Aba 'Sem Matrícula 2026': Sem pendências")

print("\n" + "="*80)
print("✅ RELATÓRIO GERADO COM SUCESSO!")
print("="*80)
print(f"\n📄 Arquivo: {nome_arquivo}")
print(f"\n📊 Resumo:")
print(f"   • {len(alunos_divergentes)} alunos com série divergente")
print(f"   • {len(alunos_sem_matricula)} alunos sem matrícula em 2026")
print("\n" + "="*80)
