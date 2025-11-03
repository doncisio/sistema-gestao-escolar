import mysql.connector
import pandas as pd
from conexao import conectar_bd
import os
import re

# Conectar ao banco de dados
mydb = conectar_bd()
mycursor = mydb.cursor(dictionary=True, buffered=True)  # Usando um cursor buffered e que retorna dicionários

# Definindo a escola_id fixa
escola_id = 13

# Caminho para os arquivos Excel
caminho_dados = "H:/Meu Drive/NADIR_2024/ATAS DIGITALIZADAS/dados historico escolar"  # Ajuste este caminho

# Lista de conceitos válidos
conceitos_validos = ['I', 'R', 'B', 'MB']

# Dicionário para mapear nomes de disciplinas do Excel para o banco de dados
mapeamento_disciplinas = {
    'ARTE': 'ARTES',
    'ENS RELIGIOSO': 'ENS. RELIGIOSO',
    'ENS. RELIGIOSO': 'ENS. RELIGIOSO',
    'ENS RELIGIOSO.1': 'ENS. RELIGIOSO',
    'ED FISICA': 'ED. FÍSICA',
    'ED. FISICA': 'ED. FÍSICA',
    'PORTUGUÊS': 'PORTUGUÊS',
    'MATEMÁTICA': 'MATEMÁTICA',
    'HISTÓRIA': 'HISTÓRIA',
    'GEOGRAFIA': 'GEOGRAFIA',
    'CIÊNCIAS': 'CIÊNCIAS',
    'INGLÊS': 'INGLÊS',
    'FILOSOFIA': 'FILOSOFIA',
    'ARTES': 'ARTES',
    'ÉTICA':  'ÉTICA E CIDADANIA',
}

# Função para verificar se um valor pode ser convertido para decimal
def is_valid_decimal(value):
    try:
        float(value)  # Tenta converter para float
        return True
    except (ValueError, TypeError):
        return False

# Ler todos os arquivos Excel no diretório especificado
for arquivo in os.listdir(caminho_dados):
    if arquivo.endswith('.xlsx') and 'DADOS PARA HISTORICO ESCOLAR' in arquivo and not arquivo.startswith('~$'):
        # Extrai o ano letivo do nome do arquivo (assumindo que está no final)
        ano_letivo = arquivo.split(' ')[-1].split('.')[0]  
        
        # Buscar o ano letivo_id na tabela anosletivos
        mycursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = %s", (ano_letivo,))
        ano_letivo_result = mycursor.fetchone()
        
        if not ano_letivo_result:
            print(f"Ano letivo {ano_letivo} não encontrado na tabela anosletivos.")
            continue  # Pula para o próximo arquivo se não encontrar o ano letivo
        
        ano_letivo_id = ano_letivo_result['id']  # Usando dicionário para acessar pelo nome da coluna
        print(f"Lendo arquivo: {arquivo} para o ano letivo: {ano_letivo_id}")

        # Lê o arquivo Excel
        excel_file = pd.ExcelFile(os.path.join(caminho_dados, arquivo))

        # Iterar sobre cada planilha no arquivo Excel
        for nome_serie in excel_file.sheet_names:
            serie_principal = re.match(r'^\d+º\s(?:ano|Ano)', nome_serie, re.IGNORECASE)
            if serie_principal:
                serie_principal = serie_principal.group(0).title()
            else:
                print(f"Formato inesperado para o nome da série: {nome_serie}")
                serie_principal = nome_serie
            print(f"Lendo planilha: {nome_serie} (Série: {serie_principal})")

            # Buscar serie_id e nivel_id na tabela serie
            mycursor.execute("SELECT id, nivel_id FROM serie WHERE nome = %s", (serie_principal,))
            serie_result = mycursor.fetchone()
            
            if not serie_result:
                print(f"Série {serie_principal} não encontrada na tabela serie.")
                continue  # Pula para a próxima planilha se não encontrar a série
            
            serie_id, nivel_id = serie_result['id'], serie_result['nivel_id']  # Usando dicionário

            # Lê a planilha em um DataFrame
            df = pd.read_excel(excel_file, sheet_name=nome_serie)

            # Imprime os nomes das colunas para verificação
            print("Colunas disponíveis:", df.columns.tolist())

            # Verifica se a coluna 'NOME DO ALUNO' existe
            if 'NOME DO ALUNO' not in df.columns:
                print(f"A coluna 'NOME DO ALUNO' não foi encontrada na planilha '{nome_serie}'.")
                continue  # Pula para a próxima planilha se a coluna não existir

            # Filtra colunas relevantes (desconsidera 'Nº')
            colunas_disciplinas = df.columns[2:]  # Supondo que as duas primeiras colunas são 'Nº' e 'NOME DO ALUNO'
            
            for index, row in df.iterrows():
                nome_aluno = row['NOME DO ALUNO'].strip()  # Usando o nome correto da coluna
                
                # Verificar se o aluno já existe (normalizando o nome)
                mycursor.execute("SELECT id FROM alunos WHERE nome = %s", (nome_aluno,))
                result = mycursor.fetchone()

                if result:
                    id_aluno = result['id']  # Usando dicionário para acessar pelo nome da coluna
                    print(f"Aluno existente: {nome_aluno} com ID: {id_aluno}")

                    # Inserir ou atualizar as médias/conceitos na tabela historico_escolar
                    for disciplina in colunas_disciplinas:
                        valor = row.get(disciplina)  # Tenta obter a média ou conceito

                        if pd.notna(valor):  # Verifica se não é NaN
                            disciplina_normalizada = disciplina.strip().upper()  # Normaliza a disciplina

                            if disciplina_normalizada in mapeamento_disciplinas:
                                disciplina_banco = mapeamento_disciplinas[disciplina_normalizada]
                                
                                try:
                                    # Buscar disciplina_id na tabela disciplinas usando nivel_id e nome da disciplina mapeada
                                    mycursor.execute("SELECT id FROM disciplinas WHERE nome = %s AND nivel_id = %s", (disciplina_banco, nivel_id))
                                    disciplina_result = mycursor.fetchone()

                                    if disciplina_result:
                                        disciplina_id = disciplina_result['id']  # Usando dicionário

                                        if valor in conceitos_validos:  # Se for um conceito válido
                                            mycursor.execute(
                                                "INSERT INTO historico_escolar (aluno_id, disciplina_id, ano_letivo_id, serie_id, escola_id, conceito) VALUES (%s, %s, %s, %s, %s, %s) "
                                                "ON DUPLICATE KEY UPDATE conceito = %s",
                                                (id_aluno,
                                                 disciplina_id,
                                                 ano_letivo_id,
                                                 serie_id,
                                                 escola_id,
                                                 valor,
                                                 valor)
                                            )
                                            print(f"Conceito inserido ou atualizado para {nome_aluno} na disciplina {disciplina}: {valor}.")
                                        else:  # Caso contrário, deve ser uma média
                                            if is_valid_decimal(valor):  # Verifica se é um decimal válido antes de inserir
                                                mycursor.execute(
                                                    "INSERT INTO historico_escolar (aluno_id, disciplina_id, ano_letivo_id, serie_id, escola_id, media) VALUES (%s, %s, %s, %s, %s, %s) "
                                                    "ON DUPLICATE KEY UPDATE media = %s",
                                                    (id_aluno,
                                                     disciplina_id,
                                                     ano_letivo_id,
                                                     serie_id,
                                                     escola_id,
                                                     valor,
                                                     valor)
                                                )
                                                print(f"Média inserida ou atualizada para {nome_aluno} na disciplina {disciplina}: {valor}.")
                                            else:
                                                print(f"Valor inválido '{valor}' encontrado na planilha '{nome_serie}', arquivo '{arquivo}'.")
                                    else:
                                        print(f"Disciplina '{disciplina_banco}' não encontrada para o nível especificado.")
                                except mysql.connector.Error as err:
                                    print(f"Erro ao executar consulta: {err}")
                else:
                    try:
                        mycursor.execute("INSERT INTO alunos (nome) VALUES (%s)", (nome_aluno,))
                        id_aluno = mycursor.lastrowid  
                        print(f"Aluno inserido: {nome_aluno} com novo ID: {id_aluno}")

                        for disciplina in colunas_disciplinas:
                            valor = row.get(disciplina)  # Tenta obter a média ou conceito

                            if pd.notna(valor):  # Verifica se não é NaN
                                disciplina_normalizada = disciplina.strip().upper()  # Normaliza a disciplina

                                if disciplina_normalizada in mapeamento_disciplinas:
                                    disciplina_banco = mapeamento_disciplinas[disciplina_normalizada]
                                    
                                    try:
                                        # Buscar disciplina_id na tabela disciplinas usando nivel_id e nome da disciplina mapeada
                                        mycursor.execute("SELECT id FROM disciplinas WHERE nome = %s AND nivel_id = %s", (disciplina_banco, nivel_id))
                                        disciplina_result = mycursor.fetchone()

                                        if disciplina_result:
                                            disciplina_id = disciplina_result['id']  # Usando dicionário

                                            if valor in conceitos_validos:  # Se for um conceito válido
                                                mycursor.execute(
                                                    "INSERT INTO historico_escolar (aluno_id, disciplina_id, ano_letivo_id, serie_id, escola_id, conceito) VALUES (%s, %s, %s, %s, %s, %s)",
                                                    (id_aluno,
                                                     disciplina_id,
                                                     ano_letivo_id,
                                                     serie_id,
                                                     escola_id,
                                                     valor)
                                                )
                                                print(f"Conceito inserido para {nome_aluno} na disciplina {disciplina}: {valor}.")
                                            else:  # Caso contrário deve ser uma média
                                                if is_valid_decimal(valor):  # Verifica se é um decimal válido antes de inserir
                                                    mycursor.execute(
                                                        "INSERT INTO historico_escolar (aluno_id, disciplina_id, ano_letivo_id, serie_id, escola_id, media) VALUES (%s, %s, %s, %s, %s, %s)",
                                                        (id_aluno,
                                                         disciplina_id,
                                                         ano_letivo_id,
                                                         serie_id,
                                                         escola_id,
                                                         valor)
                                                    )
                                                    print(f"Média inserida para {nome_aluno} na disciplina {disciplina}: {valor}.")
                                                else:
                                                    print(f"Valor inválido '{valor}' encontrado na planilha '{nome_serie}', arquivo '{arquivo}'.")
                                        else:
                                            print(f"Disciplina '{disciplina_banco}' não encontrada para o nível especificado.")
                                    except mysql.connector.Error as err:
                                        print(f"Erro ao executar consulta: {err}")
                    except mysql.connector.Error as err:
                        print(f"Erro ao inserir aluno '{nome_aluno}': {err}")

# Confirmar as inserções no banco de dados
mydb.commit()
print(mycursor.rowcount,"registros inseridos ou atualizados.")

# Fechar a conexão
mycursor.close()
mydb.close()