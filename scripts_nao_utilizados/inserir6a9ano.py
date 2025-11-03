import mysql.connector
from conexao import conectar_bd

# Conectar ao banco de dados
mydb = conectar_bd()
mycursor = mydb.cursor()

alunos_medias = [
    ('Adrian Gadiel Silva Farias', [100, 95, 100, 90, 80, 100, 100, 90, 90, 100]),
    ('André Filipe Soares Costa', [80, 70, 70, 85, 80, 75, 95, 90, 90, 95]),
    ('Artur Miguel Martins Costa', [80, 75, 90, 85, 80, 85, 100, 90, 90, 100]),
    ('Artur Rodrigues Bêrredo', [75, 61, 85, 8, 80, 80, 80, 90, 90, 80]),
    ('Beatriz Mendes Carvalho', [70, 75, 85, 65, 80, 85, 95, 90, 90, 95]),
    ('Brenda da Cruz Pereira', [70, 75, 90, 85, 80, 80, 95, 90, 90, 95]),
    ('Davi Adriano do Nascimento Lopes', [65, 60, 60, 65, 80, 70, 100, 90, 90, 100]),
    ('Douglas de Aguiar Lima', [85, 80, 80, 80, 80, 75, 100, 90, 90, 100]),
    ('Euryane Gabrielle Sousa Silva', [90, 75, 85, 80, 80, 70, 100, 90, 90, 100]),
    ('Everton Santana Silva', [95, 75, 90, 85, 80, 80, 100, 90, 90, 100]),
    ('Fernanda Reis Martins', [75, 65, 80, 75, 80, 75, 100, 90, 90, 100]),
    ('Flávia Alessandra Cunha Sá', [90, 80, 80, 70, 80, 85, 80, 90, 90, 80]),
    ('Gabriele da Silva Martins', [70, 65, 60, 70, 80, 60, 100, 90, 90, 100]),
    ('Iane Isabelle Nascimento de Sá', [90, 70, 95, 75, 80, 90, 100, 90, 90, 100]),
    ('João Lucas Santana Mota', [90, 85, 95, 95, 80, 90, 100, 90, 90, 100]),
    ('João Pedro Santana Mota', [75, 85, 80, 85, 80, 85, 95, 90, 90, 95]),
    ('Larissa Gabrielly Ramos Barbosa', [100, 80, 100, 90, 90, 100, 100, 90, 90, 100]),
    ('Leanderson Coelho Teixeira', [60, 60, 60, 60, 80, 60, 80, 90, 90, 80]),
    ('Leonora Gusmão Duarte', [90, 75, 95, 85, 80, 100, 100, 90, 90, 100]),
    ('Magno Kawan Oliveira Arouche', [75, 70, 75, 80, 80, 65, 100, 90, 90, 100]),
    ('Maria Eduarda Costa Viana', [75, 70, 70, 60, 80, 75, 100, 90, 90, 100]),
    ('Miguel da Paz Araújo', [70, 65, 75, 80, 80, 70, 95, 90, 90, 95]),
    ('Naelma Mesquita Soares', [60, 80, 70, 70, 80, 75, 100, 90, 90, 100]),
    ('Nayana de Jesus Garrido', [100, 85, 90, 90, 80, 95, 95, 90, 90, 95]),
    ('Nayara de Jesus Garrido', [100, 90, 95, 95, 80, 95, 100, 90, 90, 100]),
    ('Nívea Juanne Pimenta Silva', [90, 100, 85, 85, 80, 75, 100, 90, 90, 100]),
    ('Paulo Ricardo Pinheiro Machado', [70, 70, 75, 75, 80, 75, 100, 90, 90, 100]),
    ('Pedro Lucas de Jesus Brito', [80, 80, 90, 90, 80, 85, 100, 90, 90, 100]),
    ('Rian Felipe Lima Comeia', [95, 75, 95, 95, 80, 90, 100, 90, 90, 100]),
    ('Ryan Silva do Nascimento', [70, 75, 65, 65, 80, 70, 100, 90, 90, 100]),
    ('Sahra Cristina Mesquita Pereira', [85, 85, 75, 75, 80, 75, 100, 90, 90, 100]),
    ('Sara Cristiny Sousa Pinto', [95, 75, 90, 90, 80, 80, 90, 90, 90, 90]),
    ('Serfany Matos da Silva', [95, 70, 80, 80, 80, 65, 100, 90, 90, 100]),
    ('Victor Júlio Ferraz França', [70, 60, 70, 70, 80, 70, 95, 90, 90, 95]),
    ('Victória Karolyne Silva de Pinho', [70, 85, 70, 70, 80, 65, 90, 90, 90, 85]),
    ('Vinicius Sousa de Sousa', [90, 75, 90, 90, 80, 80, 100, 90, 90, 100]),
    ('Welline Freitas da Silva', [100, 90, 100, 100, 80, 100, 100, 90, 90, 100])
]

# Definindo variáveis para o ano letivo e escola
ano_letivo_id = 23 # 2021
serie_id = 11
escola_id = 3

# Ordem das disciplinas conforme especificado: 
ordem_disciplinas = [9,10,13,11,12,19,16,14,15,17]
# ordem_disciplinas = [1,2,5,3,4,6,7,8]

# Inserir alunos e suas médias
for nome_aluno, medias in alunos_medias:
    
    # Verificar se o aluno já existe
    mycursor.execute("SELECT id FROM alunos WHERE nome = %s", (nome_aluno,))
    
    # Ler o resultado da consulta anterior
    result = mycursor.fetchone()  
   
    if result:
        # Se o aluno já existe
        id_aluno = result[0]
        print(f"Aluno existente: {nome_aluno} com ID: {id_aluno}")

        # Inserir ou atualizar as médias na tabela historico_escolar
        for i in range(len(ordem_disciplinas)):
            disciplina_id = ordem_disciplinas[i]
            media = medias[i] 
            mycursor.execute(
                "INSERT INTO historico_escolar (aluno_id, disciplina_id, ano_letivo_id, serie_id, escola_id, media) VALUES (%s, %s, %s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE media = %s",
                (id_aluno,
                disciplina_id,
                ano_letivo_id,
                serie_id,
                escola_id,
                media,
                media)  # O último 'media' é para a cláusula ON DUPLICATE KEY UPDATE
            )
            print(f"Média inserida ou atualizada para {nome_aluno} na disciplina {disciplina_id}: {media}.")
                
    else:
        # Se não existe o aluno ainda
        mycursor.execute("INSERT INTO alunos (nome) VALUES (%s)", (nome_aluno,))
        id_aluno = mycursor.lastrowid  
        print(f"Aluno inserido: {nome_aluno} com novo ID: {id_aluno}")

        # Inserir as médias na tabela historico_escolar para cada disciplina na ordem correta
        for i in range(len(medias)):
            disciplina_id = ordem_disciplinas[i]
            media = medias[i]
            mycursor.execute(
                "INSERT INTO historico_escolar (aluno_id, disciplina_id, ano_letivo_id, serie_id, escola_id, media) VALUES (%s, %s, %s, %s, %s, %s)",
                (id_aluno,
                 disciplina_id,
                 ano_letivo_id,
                 serie_id,
                 escola_id,
                 media)
            )
            print(f"Média inserida para {nome_aluno} na disciplina {disciplina_id}: {media}.")

# Confirmar as inserções no banco de dados
mydb.commit()
print(mycursor.rowcount,"registros inseridos ou atualizados.")

# Fechar a conexão
mycursor.close()
mydb.close()