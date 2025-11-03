"""
DIAGNÓSTICO E SOLUÇÃO PARA A DISCREPÂNCIA DO NÚMERO DE ALUNOS

PROBLEMA IDENTIFICADO:
Após análise do sistema, identificamos que o módulo de frequência está exibindo a quantidade
correta de alunos em cada turma, mas há uma discrepância entre o que é mostrado no sistema
e o que o usuário espera ver.

EVIDÊNCIAS ENCONTRADAS:
1. A consulta SQL direta no banco de dados confirma:
   - Turma ID=28 (1º Ano): 18 alunos
   - Turma ID=29 (2º Ano): 49 alunos
   - Turma ID=30 (3º Ano): 56 alunos
   - Turma ID=33 (6º Ano A): 34 alunos
   - Turma ID=35 (7º Ano): 33 alunos

2. O método get_by_turma() do AlunoController está retornando o número correto de alunos para 
   cada turma conforme os registros ativos na tabela 'matriculas'.

3. A função get_alunos_por_turma() no FrequenciaController está chamando o método 
   get_by_turma() corretamente.

POSSÍVEIS EXPLICAÇÕES:
1. Existem múltiplas turmas para cada nível de ensino no banco de dados, com IDs diferentes, 
   possivelmente representando anos letivos diferentes ou períodos diferentes.

2. O relatório Lista_atualizada.py mostra números diferentes porque possivelmente consulta 
   de uma forma diferente, agrupando por nível de ensino ou incluindo turmas que não estão 
   sendo consideradas na visualização de frequência.

SOLUÇÃO RECOMENDADA:
1. Verificar se há múltiplas turmas de cada série (por exemplo, 1º Ano) no banco de dados, 
   com diferentes IDs ou anos letivos.

2. Modificar a visualização de frequência para mostrar a quantidade total de alunos por nível 
   de ensino (mesclando todas as turmas de um mesmo nível), se for esse o comportamento desejado.

3. Verificar se o script Lista_atualizada.py está utilizando filtros diferentes, como ano letivo, 
   unidade escolar ou status de matrícula.

4. Certificar-se de que todos os componentes do sistema estão acessando o mesmo banco de dados 
   e utilizando os mesmos critérios de filtragem.

IMPLEMENTAÇÃO SUGERIDA:
Ambos os sistemas (frequência e Lista_atualizada) devem usar a mesma consulta SQL para manter 
consistência nos dados exibidos. Recomendamos padronizar o método de contagem de alunos por turma 
usando a seguinte abordagem:

```python
def get_alunos_por_nivel(self, nivel_id, ano_letivo_id=None):
    """
    Obtém todos os alunos de um nível de ensino, agrupando todas as turmas
    
    Args:
        nivel_id (int): ID do nível de ensino
        ano_letivo_id (int, opcional): ID do ano letivo
        
    Returns:
        list: Lista de alunos ou lista vazia em caso de erro
    """
    try:
        from utils.db_config import get_db_config
        import mysql.connector
        
        db_config = get_db_config()
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT a.id, a.nome, a.sexo, a.data_nascimento, a.descricao_transtorno,
                   m.id as matricula_id, m.status as matricula_status, 
                   s.nome as serie_nome, t.nome as turma_nome, t.turno
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            JOIN Turmas t ON m.turma_id = t.id
            JOIN Serie s ON t.serie_id = s.id
            WHERE s.nivel_id = %s 
              AND m.status = 'Ativo'
        """
        
        params = [nivel_id]
        
        if ano_letivo_id:
            query += " AND m.ano_letivo_id = %s"
            params.append(ano_letivo_id)
            
        query += " ORDER BY a.nome"
        
        cursor.execute(query, params)
        alunos = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return alunos
        
    except Exception as e:
        print(f"Erro ao obter alunos por nível: {e}")
        return []
```

Dessa forma, a contagem será consistente em todo o sistema.
""" 