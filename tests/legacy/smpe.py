from src.core.conexao import conectar_bd

def atualizar_historico():
    # Conectar ao banco de dados
    conn = conectar_bd()
    cursor = conn.cursor()

    # 1. Selecionar todos os registros da tabela historico_escolar
    cursor.execute("SELECT disciplina_id, serie_id, escola_id FROM historico_escolar")
    registros = cursor.fetchall()

    for registro in registros:
        disciplina_id, serie_id, escola_id = registro

        # 2. Verificar se a combinação de disciplina_id e escola_id existe na tabela disciplinas
        cursor.execute("""
            SELECT COUNT(*) FROM disciplinas 
            WHERE id = %s AND escola_id = %s
        """, (disciplina_id, escola_id))
        
        existe = cursor.fetchone()[0]

        if existe == 0:  # Se não existir
            # 3. Buscar o nivel_id na tabela serie usando o serie_id
            cursor.execute("SELECT nivel_id FROM series WHERE id = %s", (serie_id,))
            nivel_id = cursor.fetchone()

            if nivel_id is not None:
                nivel_id = nivel_id[0]

                # 4. Obter o nome da disciplina usando disciplina_id na tabela disciplinas
                cursor.execute("SELECT nome FROM disciplinas WHERE id = %s", (disciplina_id,))
                nome_disciplina = cursor.fetchone()

                if nome_disciplina is not None:
                    nome_disciplina = nome_disciplina[0]

                    # 5. Encontrar o novo disciplina_id com base no nome, escola_id e nivel_id
                    cursor.execute("""
                        SELECT id FROM disciplinas 
                        WHERE nome = %s AND escola_id = %s AND nivel_id = %s
                    """, (nome_disciplina, escola_id, nivel_id))
                    
                    novo_disciplina_id = cursor.fetchone()

                    if novo_disciplina_id is not None:
                        novo_disciplina_id = novo_disciplina_id[0]

                        # 6. Atualizar disciplina_id na tabela historico_escolar
                        cursor.execute("""
                            UPDATE historico_escolar 
                            SET disciplina_id = %s 
                            WHERE disciplina_id = %s AND serie_id = %s AND escola_id = %s
                        """, (novo_disciplina_id, disciplina_id, serie_id, escola_id))
                        conn.commit()  # Confirma as alterações no banco de dados

    # Fechar o cursor e a conexão
    cursor.close()
    conn.close()

# Chamar a função para executar a atualização
atualizar_historico()
