from conexao import conectar_bd

def atualizar_historico():
    # Conectar ao banco de dados
    conn = conectar_bd()
    if not conn:
        print("Erro: não foi possível conectar ao banco de dados.")
        return

    cursor = conn.cursor()
    assert cursor is not None

    def safe_int(x, default=0):
        """Converte valores comuns para int com fallback seguro.

        Aceita ints, floats e strings que representem números. Retorna
        `default` para outros tipos (date, set, None, etc.).
        """
        if isinstance(x, int):
            return x
        if isinstance(x, float):
            try:
                return int(x)
            except Exception:
                return default
        if isinstance(x, str):
            try:
                return int(x)
            except Exception:
                try:
                    return int(float(x))
                except Exception:
                    return default
        return default

    def safe_str(x, default=''):
        """Converte valores para string de forma segura, retorna `default` quando não possível."""
        if x is None:
            return default
        if isinstance(x, str):
            return x
        try:
            return str(x)
        except Exception:
            return default

    # 1. Selecionar todos os registros da tabela historico_escolar
    cursor.execute("SELECT disciplina_id, serie_id, escola_id FROM historico_escolar")
    registros = cursor.fetchall()

    for registro in registros:
        disciplina_id, serie_id, escola_id = registro

        # 2. Verificar se a combinação de disciplina_id e escola_id existe na tabela disciplinas
        # Garantir tipos primitivos esperados pelo driver (int)
        disciplina_id_param = safe_int(disciplina_id, 0)
        escola_id_param = safe_int(escola_id, 0)

        cursor.execute("""
            SELECT COUNT(*) FROM disciplinas 
            WHERE id = %s AND escola_id = %s
        """, (disciplina_id_param, escola_id_param))

        r = cursor.fetchone()
        existe = r[0] if r and r[0] is not None else 0

        if existe == 0:  # Se não existir
            # 3. Buscar o nivel_id na tabela serie usando o serie_id
            serie_id_param = safe_int(serie_id, 0)

            cursor.execute("SELECT nivel_id FROM serie WHERE id = %s", (serie_id_param,))
            r = cursor.fetchone()
            nivel_id = r[0] if r and r[0] is not None else None

            # 4. Obter o nome da disciplina usando disciplina_id na tabela disciplinas
            cursor.execute("SELECT nome FROM disciplinas WHERE id = %s", (disciplina_id_param,))
            r = cursor.fetchone()
            nome_disciplina = r[0] if r and r[0] is not None else None

            # 5. Encontrar o novo disciplina_id com base no nome, escola_id e nivel_id
            escola_id_param = safe_int(escola_id, 0)
            nivel_id_param = safe_int(nivel_id, 0)

            # Se não há nome encontrado, não faz sentido procurar o id correspondente
            if not nome_disciplina:
                continue

            nome_disciplina_str = safe_str(nome_disciplina)

            cursor.execute("""
                SELECT id FROM disciplinas 
                WHERE nome = %s AND escola_id = %s AND nivel_id = %s
            """, (nome_disciplina_str, escola_id_param, nivel_id_param))

            r = cursor.fetchone()
            novo_disciplina_id = r[0] if r and r[0] is not None else None

            # 6. Atualizar disciplina_id na tabela historico_escolar
            if novo_disciplina_id is not None:
                novo_id_param = safe_int(novo_disciplina_id, 0)
                disciplina_old_param = safe_int(disciplina_id, 0)
                serie_id_param = safe_int(serie_id, 0)
                escola_id_param = safe_int(escola_id, 0)

                cursor.execute("""
                    UPDATE historico_escolar 
                    SET disciplina_id = %s 
                    WHERE disciplina_id = %s AND serie_id = %s AND escola_id = %s
                """, (novo_id_param, disciplina_old_param, serie_id_param, escola_id_param))
                conn.commit()  # Confirma as alterações no banco de dados

    # Fechar o cursor e a conexão
    cursor.close()
    conn.close()

# Chamar a função para executar a atualização
atualizar_historico()