"""
Script para importar os 36 alunos novos do GEDUC para o sistema local
- Importa dados do aluno (nome padronizado, dados pessoais)
- Importa dados dos responsáveis (nome padronizado)
- Vincula responsáveis ao aluno
- NÃO cria matrícula (será feito manualmente)
"""

import json
import unicodedata
from datetime import datetime
from db.connection import conectar_bd

def normalizar_nome_sistema_local(nome):
    """
    Padroniza nome no formato do sistema local:
    Primeira letra de cada palavra maiúscula, resto minúsculo
    Exemplo: 'ANA CLARA SANTOS SILVA' -> 'Ana Clara Santos Silva'
    """
    if not nome:
        return ""
    
    # Remover espaços extras
    nome = ' '.join(nome.split())
    
    # Aplicar capitalização: primeira letra maiúscula, resto minúsculo
    palavras = nome.split()
    palavras_formatadas = []
    
    # Palavras que devem permanecer em minúsculo (preposições, artigos)
    minusculas = ['da', 'de', 'do', 'das', 'dos', 'e']
    
    for palavra in palavras:
        if palavra.lower() in minusculas and len(palavras_formatadas) > 0:
            palavras_formatadas.append(palavra.lower())
        else:
            palavras_formatadas.append(palavra.capitalize())
    
    return ' '.join(palavras_formatadas)


def mapear_raca(raca_geduc):
    """
    Mapeia raça do GEDUC para valores do sistema local
    Sistema local aceita: 'preto', 'pardo', 'branco', 'indígena', 'amarelo'
    """
    if not raca_geduc:
        return 'pardo'
    
    raca_lower = raca_geduc.lower().strip()
    
    # Mapeamento direto
    mapa = {
        'parda': 'pardo',
        'pardo': 'pardo',
        'branca': 'branco',
        'branco': 'branco',
        'preta': 'preto',
        'preto': 'preto',
        'negra': 'preto',
        'negro': 'preto',
        'indígena': 'indígena',
        'indigena': 'indígena',
        'amarela': 'amarelo',
        'amarelo': 'amarelo',
        'não declarada': 'pardo',
        'nao declarada': 'pardo'
    }
    
    return mapa.get(raca_lower, 'pardo')


def inferir_sexo_por_nome(nome):
    """
    Infere o sexo baseado em nomes comuns
    Retorna 'F' para feminino, 'M' para masculino
    """
    if not nome:
        return 'M'
    
    nome_lower = nome.lower()
    primeiro_nome = nome.split()[0].lower()
    
    # Nomes claramente femininos
    nomes_femininos = [
        'ana', 'maria', 'sarah', 'sara', 'rebeca', 'pietra', 'lara', 
        'isadora', 'gabrielly', 'glenda', 'esther', 'marcelly', 'rita',
        'natalia', 'bruna', 'candida', 'yasmin', 'aryella'
    ]
    
    # Nomes claramente masculinos
    nomes_masculinos = [
        'benjamin', 'enzo', 'fernando', 'guilherme', 'henzo', 'igor',
        'joao', 'joão', 'kauan', 'mikael', 'noah', 'deyvison'
    ]
    
    # Verificar primeiro nome
    if primeiro_nome in nomes_femininos:
        return 'F'
    if primeiro_nome in nomes_masculinos:
        return 'M'
    
    # Verificar terminações comuns femininas
    terminacoes_femininas = ['a', 'ella', 'elly', 'bela', 'bella', 'issa', 'isa']
    for term in terminacoes_femininas:
        if primeiro_nome.endswith(term):
            return 'F'
    
    # Verificar terminações comuns masculinas
    terminacoes_masculinas = ['o', 'el', 'son', 'nho']
    for term in terminacoes_masculinas:
        if primeiro_nome.endswith(term):
            return 'M'
    
    # Padrão: masculino (mais conservador)
    return 'M'


def normalizar_nome_comparacao(nome):
    """Remove acentos e converte para maiúsculo para comparação"""
    if not nome:
        return ""
    nfkd = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return nome_sem_acento.upper()


def carregar_alunos_geduc(arquivo='alunos_geduc.json'):
    """Carrega alunos do arquivo JSON do GEDUC"""
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extrair lista de alunos
        alunos = []
        for turma in data.get('turmas', []):
            alunos.extend(turma.get('alunos', []))
        
        return alunos
    except Exception as e:
        print(f"Erro ao carregar arquivo: {e}")
        return []


def buscar_alunos_sistema_local(cursor):
    """Busca todos os alunos do sistema local para comparação"""
    cursor.execute("""
        SELECT id, nome, cpf
        FROM Alunos
    """)
    
    alunos_local = {}
    for row in cursor.fetchall():
        nome_normalizado = normalizar_nome_comparacao(row['nome'])
        alunos_local[nome_normalizado] = {
            'id': row['id'],
            'nome': row['nome'],
            'cpf': row['cpf']
        }
    
    return alunos_local


def inserir_responsavel(cursor, dados_responsavel, conn):
    """Insere ou retorna responsável existente"""
    if not dados_responsavel.get('nome'):
        return None
    
    nome = normalizar_nome_sistema_local(dados_responsavel['nome'])
    cpf = dados_responsavel.get('cpf', '').strip()
    telefone = dados_responsavel.get('telefone', '').strip()
    grau_parentesco = dados_responsavel.get('grau_parentesco', '').strip()
    
    # Verificar se responsável já existe (por CPF se disponível)
    if cpf and cpf != '':
        cursor.execute("SELECT id FROM Responsaveis WHERE cpf = %s", (cpf,))
        result = cursor.fetchone()
        if result:
            return result[0]
    
    # Inserir novo responsável
    cursor.execute("""
        INSERT INTO Responsaveis (nome, cpf, telefone, grau_parentesco)
        VALUES (%s, %s, %s, %s)
    """, (nome, cpf if cpf else None, telefone if telefone else None, grau_parentesco))
    
    return cursor.lastrowid


def vincular_responsavel_aluno(cursor, responsavel_id, aluno_id):
    """Vincula responsável ao aluno"""
    # Verificar se já existe vínculo
    cursor.execute("""
        SELECT id FROM ResponsaveisAlunos 
        WHERE responsavel_id = %s AND aluno_id = %s
    """, (responsavel_id, aluno_id))
    
    if cursor.fetchone():
        return  # Já vinculado
    
    cursor.execute("""
        INSERT INTO ResponsaveisAlunos (responsavel_id, aluno_id)
        VALUES (%s, %s)
    """, (responsavel_id, aluno_id))


def importar_alunos_novos():
    """Importa os 36 alunos novos do GEDUC para o sistema local"""
    
    print("="*80)
    print("IMPORTAÇÃO DE ALUNOS NOVOS DO GEDUC")
    print("="*80)
    print("\nCarregando dados do GEDUC...")
    
    # Carregar alunos do GEDUC
    alunos_geduc = carregar_alunos_geduc()
    if not alunos_geduc:
        print("❌ Erro: Não foi possível carregar alunos do GEDUC")
        return
    
    print(f"✓ {len(alunos_geduc)} alunos carregados do GEDUC\n")
    
    # Conectar ao banco
    conn = conectar_bd()
    if not conn:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    # Buscar alunos já existentes no sistema local
    print("Carregando alunos do sistema local...")
    alunos_local = buscar_alunos_sistema_local(cursor)
    print(f"✓ {len(alunos_local)} alunos no sistema local\n")
    
    # Filtrar apenas alunos novos (que não estão no sistema local)
    alunos_novos = []
    for aluno in alunos_geduc:
        nome_normalizado = normalizar_nome_comparacao(aluno['nome'])
        if nome_normalizado not in alunos_local:
            alunos_novos.append(aluno)
    
    print(f"🆕 {len(alunos_novos)} alunos novos para importar\n")
    print("="*80)
    print("INICIANDO IMPORTAÇÃO")
    print("="*80)
    
    importados = 0
    erros = []
    
    escola_id = 60  # Escola padrão
    
    for idx, aluno_geduc in enumerate(alunos_novos, 1):
        try:
            # Padronizar nome para o sistema local
            nome = normalizar_nome_sistema_local(aluno_geduc['nome'])
            
            # Preparar dados do aluno
            data_nascimento = aluno_geduc.get('data_nascimento')
            if data_nascimento:
                try:
                    # Tentar converter para formato YYYY-MM-DD
                    if isinstance(data_nascimento, str):
                        if '/' in data_nascimento:
                            data_nascimento = datetime.strptime(data_nascimento, '%d/%m/%Y').strftime('%Y-%m-%d')
                except:
                    data_nascimento = None
            
            # Inferir sexo baseado no nome (GEDUC não tem campo sexo)
            sexo = inferir_sexo_por_nome(nome)
            cpf = aluno_geduc.get('cpf', '').strip()
            raca = mapear_raca(aluno_geduc.get('raca', 'pardo'))
            descricao_transtorno = aluno_geduc.get('descricao_transtorno', 'Nenhum')
            
            # Inserir aluno (sem campos mae e pai que não existem na tabela)
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
            
            # Responsável 1 (Mãe)
            if aluno_geduc.get('mae'):
                resp_mae = {
                    'nome': aluno_geduc['mae'],
                    'cpf': aluno_geduc.get('cpf_mae', ''),
                    'telefone': aluno_geduc.get('telefone_mae', ''),
                    'grau_parentesco': 'Mãe'
                }
                resp_id = inserir_responsavel(cursor, resp_mae, conn)
                if resp_id:
                    vincular_responsavel_aluno(cursor, resp_id, aluno_id)
                    responsaveis_inseridos += 1
            
            # Responsável 2 (Pai)
            if aluno_geduc.get('pai'):
                resp_pai = {
                    'nome': aluno_geduc['pai'],
                    'cpf': aluno_geduc.get('cpf_pai', ''),
                    'telefone': aluno_geduc.get('telefone_pai', ''),
                    'grau_parentesco': 'Pai'
                }
                resp_id = inserir_responsavel(cursor, resp_pai, conn)
                if resp_id:
                    vincular_responsavel_aluno(cursor, resp_id, aluno_id)
                    responsaveis_inseridos += 1
            
            # Responsável 3 (Outro)
            if aluno_geduc.get('responsavel'):
                resp_outro = {
                    'nome': aluno_geduc['responsavel'],
                    'cpf': aluno_geduc.get('cpf_responsavel', ''),
                    'telefone': aluno_geduc.get('telefone_responsavel', ''),
                    'grau_parentesco': aluno_geduc.get('grau_parentesco_responsavel', 'Outro')
                }
                resp_id = inserir_responsavel(cursor, resp_outro, conn)
                if resp_id:
                    vincular_responsavel_aluno(cursor, resp_id, aluno_id)
                    responsaveis_inseridos += 1
            
            conn.commit()
            
            print(f"[{idx:02d}] ✅ {nome}")
            print(f"     ID: {aluno_id} | Responsáveis: {responsaveis_inseridos}")
            if cpf:
                print(f"     CPF: {cpf}")
            print()
            
            importados += 1
            
        except Exception as e:
            print(f"[{idx:02d}] ❌ {aluno_geduc['nome']}")
            print(f"     ERRO: {str(e)}")
            print()
            erros.append({
                'aluno': aluno_geduc['nome'],
                'erro': str(e)
            })
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("="*80)
    print("RESUMO DA IMPORTAÇÃO")
    print("="*80)
    print(f"Total de alunos novos: {len(alunos_novos)}")
    print(f"✅ Importados com sucesso: {importados}")
    print(f"❌ Erros: {len(erros)}")
    
    if erros:
        print("\nAlunos com erro:")
        for erro in erros:
            print(f"  - {erro['aluno']}: {erro['erro']}")
    
    print("\n✓ Importação concluída!")
    print("="*80)
    print("\n⚠️  ATENÇÃO: As matrículas devem ser criadas manualmente.")
    print("   Os alunos foram cadastrados, mas ainda não estão matriculados em 2026.\n")


if __name__ == "__main__":
    print("\nEste script vai importar os alunos novos do GEDUC para o sistema local.")
    print("Os nomes serão padronizados no formato do sistema local.")
    print("Matrículas NÃO serão criadas (faça manualmente).\n")
    
    resposta = input("Deseja continuar? (sim/nao): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        importar_alunos_novos()
    else:
        print("\nOperação cancelada pelo usuário.")
