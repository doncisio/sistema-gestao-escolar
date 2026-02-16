"""
Queries SQL centralizadas e reutilizáveis

Este módulo contém queries SQL parametrizadas organizadas por domínio:
- Alunos
- Matrículas
- Turmas
- Séries
- Funcionários
- Anos Letivos

Benefícios:
- Eliminação de SQL inline duplicado
- Facilita manutenção e auditoria
- Queries otimizadas e testadas
- Documentação centralizada
"""

# ============================================================================
# QUERIES DE ALUNOS
# ============================================================================

QUERY_LISTAR_ALUNOS = """
    SELECT 
        a.id,
        a.nome,
        a.cpf,
        a.data_nascimento,
        a.mae,
        a.pai,
        a.escola_id,
        a.responsavel_nome,
        a.responsavel_cpf,
        a.responsavel_telefone,
        a.endereco,
        a.bairro,
        a.cidade,
        a.estado
    FROM alunos a
    WHERE a.escola_id = %s
    ORDER BY a.nome
"""

QUERY_BUSCAR_ALUNO_POR_ID = """
    SELECT 
        a.id,
        a.nome,
        a.data_nascimento,
        a.local_nascimento,
        a.UF_nascimento,
        a.endereco,
        a.sus,
        a.sexo,
        a.cpf,
        a.nis,
        a.raca,
        a.escola_id,
        a.descricao_transtorno,
        m.id as matricula_id,
        m.status as matricula_status,
        t.nome as turma_nome,
        s.nome as serie_nome,
        al.ano as ano_letivo
    FROM alunos a
    LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.status = 'Ativo'
    LEFT JOIN turmas t ON m.turma_id = t.id
    LEFT JOIN series s ON t.serie_id = s.id
    LEFT JOIN anosletivos al ON m.ano_letivo_id = al.id
    WHERE a.id = %s
"""

QUERY_BUSCAR_ALUNOS_POR_NOME = """
    SELECT 
        a.id,
        a.nome,
        a.cpf,
        a.data_nascimento,
        a.mae,
        a.pai,
        m.status as status_matricula,
        t.nome as turma,
        s.nome as serie
    FROM alunos a
    LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.status = 'Ativo'
    LEFT JOIN turmas t ON m.turma_id = t.id
    LEFT JOIN series s ON t.serie_id = s.id
    WHERE a.nome LIKE %s OR a.cpf LIKE %s
    ORDER BY a.nome
"""

QUERY_ALUNOS_ATIVOS = """
    SELECT DISTINCT
        a.id,
        a.nome,
        a.cpf,
        a.data_nascimento,
        a.mae,
        t.nome as turma,
        s.nome as serie,
        m.status
    FROM alunos a
    JOIN matriculas m ON a.id = m.aluno_id
    JOIN turmas t ON m.turma_id = t.id
    JOIN series s ON t.serie_id = s.id
    WHERE m.status = 'Ativo' AND m.ano_letivo_id = %s
    ORDER BY s.ordem, t.nome, a.nome
"""

# ============================================================================
# QUERIES DE MATRÍCULAS
# ============================================================================

QUERY_LISTAR_MATRICULAS = """
    SELECT 
        m.id,
        m.aluno_id,
        m.turma_id,
        m.ano_letivo_id,
        m.status,
        m.data_matricula,
        a.nome as aluno_nome,
        t.nome as turma_nome,
        s.nome as serie_nome,
        al.ano as ano_letivo
    FROM matriculas m
    JOIN alunos a ON m.aluno_id = a.id
    JOIN turmas t ON m.turma_id = t.id
    JOIN series s ON t.serie_id = s.id
    JOIN anosletivos al ON m.ano_letivo_id = al.id
    WHERE m.ano_letivo_id = %s
    ORDER BY s.ordem, t.nome, a.nome
"""

QUERY_VERIFICAR_MATRICULA_ATIVA = """
    SELECT m.id, m.status, t.nome as turma, s.nome as serie
    FROM matriculas m
    JOIN turmas t ON m.turma_id = t.id
    JOIN series s ON t.serie_id = s.id
    WHERE m.aluno_id = %s AND m.ano_letivo_id = %s
    LIMIT 1
"""

QUERY_HISTORICO_MATRICULAS = """
    SELECT 
        m.id,
        m.status,
        m.data_matricula,
        t.nome as turma,
        s.nome as serie,
        al.ano as ano_letivo
    FROM matriculas m
    JOIN turmas t ON m.turma_id = t.id
    JOIN series s ON t.serie_id = s.id
    JOIN anosletivos al ON m.ano_letivo_id = al.id
    WHERE m.aluno_id = %s
    ORDER BY al.ano DESC, m.data_matricula DESC
"""

QUERY_MATRICULAS_POR_TURMA = """
    SELECT 
        m.id,
        m.aluno_id,
        m.status,
        a.nome as aluno_nome,
        a.data_nascimento
    FROM matriculas m
    JOIN alunos a ON m.aluno_id = a.id
    WHERE m.turma_id = %s AND m.status = 'Ativo'
    ORDER BY a.nome
"""

# ============================================================================
# QUERIES DE TURMAS
# ============================================================================

QUERY_LISTAR_TURMAS = """
    SELECT 
        t.id,
        t.nome,
        t.turno,
        t.capacidade_maxima,
        t.ano_letivo_id,
        t.serie_id,
        t.escola_id,
        t.professor_id,
        s.nome as serie_nome,
        s.ciclo as serie_ciclo,
        al.ano as ano_letivo,
        COALESCE(COUNT(DISTINCT m.id), 0) as total_alunos
    FROM turmas t
    LEFT JOIN series s ON t.serie_id = s.id
    LEFT JOIN anosletivos al ON t.ano_letivo_id = al.id
    LEFT JOIN matriculas m ON m.turma_id = t.id AND m.status = 'Ativo'
    WHERE t.ano_letivo_id = %s
    GROUP BY t.id, t.nome, t.turno, t.capacidade_maxima, 
             t.ano_letivo_id, t.serie_id, t.escola_id, t.professor_id,
             s.nome, s.ciclo, al.ano
    ORDER BY s.ciclo, s.nome, t.turno, t.nome
"""

QUERY_TURMAS_POR_SERIE = """
    SELECT id, nome, turno, capacidade_maxima
    FROM turmas
    WHERE serie_id = %s AND ano_letivo_id = %s
    ORDER BY turno, nome
"""

QUERY_TURMA_COM_DETALHES = """
    SELECT 
        t.id,
        t.nome,
        t.turno,
        t.capacidade_maxima,
        t.ano_letivo_id,
        t.serie_id,
        s.nome as serie_nome,
        s.ciclo as serie_ciclo,
        al.ano as ano_letivo,
        f.nome as professor_nome,
        COALESCE(COUNT(DISTINCT m.id), 0) as total_alunos
    FROM turmas t
    LEFT JOIN series s ON t.serie_id = s.id
    LEFT JOIN anosletivos al ON t.ano_letivo_id = al.id
    LEFT JOIN funcionarios f ON t.professor_id = f.id
    LEFT JOIN matriculas m ON m.turma_id = t.id AND m.status = 'Ativo'
    WHERE t.id = %s
    GROUP BY t.id, t.nome, t.turno, t.capacidade_maxima, 
             t.ano_letivo_id, t.serie_id, s.nome, s.ciclo, al.ano, f.nome
"""

# ============================================================================
# QUERIES DE SÉRIES
# ============================================================================

QUERY_LISTAR_SERIES = """
    SELECT id, nome, ciclo, ordem
    FROM series
    ORDER BY ordem, nome
"""

QUERY_SERIES_POR_CICLO = """
    SELECT id, nome, ciclo, ordem
    FROM series
    WHERE ciclo = %s
    ORDER BY ordem, nome
"""

QUERY_SERIE_POR_ID = """
    SELECT id, nome, ciclo, ordem
    FROM series
    WHERE id = %s
"""

QUERY_PROXIMA_SERIE = """
    SELECT id, nome, ciclo, ordem
    FROM series
    WHERE ordem > %s
    ORDER BY ordem
    LIMIT 1
"""

QUERY_ESTATISTICAS_SERIE = """
    SELECT 
        s.id,
        s.nome,
        s.ciclo,
        COUNT(DISTINCT t.id) as total_turmas,
        COALESCE(SUM(t.capacidade_maxima), 0) as capacidade_total,
        COUNT(DISTINCT m.id) as total_alunos,
        COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN m.id END) as alunos_ativos
    FROM series s
    LEFT JOIN turmas t ON s.id = t.serie_id AND t.ano_letivo_id = %s
    LEFT JOIN Matriculas m ON t.id = m.turma_id
    WHERE s.id = %s
    GROUP BY s.id, s.nome, s.ciclo
"""

# ============================================================================
# QUERIES DE FUNCIONÁRIOS
# ============================================================================

QUERY_LISTAR_FUNCIONARIOS = """
    SELECT 
        f.id,
        f.nome,
        f.cpf,
        f.cargo,
        f.data_admissao,
        f.telefone,
        f.email,
        f.escola_id
    FROM funcionarios f
    WHERE f.escola_id = %s
    ORDER BY f.nome
"""

QUERY_FUNCIONARIO_POR_ID = """
    SELECT 
        f.id,
        f.matricula,
        f.data_admissao,
        f.nome,
        f.cpf,
        f.carga_horaria,
        f.vinculo,
        f.cargo,
        f.funcao,
        f.turno,
        f.turma,
        f.telefone,
        f.whatsapp,
        f.email,
        f.polivalente,
        f.data_nascimento,
        f.endereco_logradouro,
        f.endereco_numero,
        f.endereco_complemento,
        f.endereco_bairro,
        f.endereco_cidade,
        f.endereco_estado,
        f.endereco_cep,
        f.escola_id,
        f.volante,
        COUNT(DISTINCT t.id) as total_turmas
    FROM funcionarios f
    LEFT JOIN turmas t ON f.id = t.professor_id
    WHERE f.id = %s
    GROUP BY f.id
"""

QUERY_BUSCAR_FUNCIONARIOS = """
    SELECT 
        f.id,
        f.nome,
        f.cpf,
        f.cargo,
        f.telefone,
        f.email
    FROM funcionarios f
    WHERE (f.nome LIKE %s OR f.cpf LIKE %s OR f.cargo LIKE %s)
        AND f.escola_id = %s
    ORDER BY f.nome
"""

QUERY_FUNCIONARIOS_POR_CARGO = """
    SELECT 
        f.id,
        f.nome,
        f.cpf,
        f.cargo,
        f.telefone
    FROM Funcionarios f
    WHERE f.cargo = %s AND f.escola_id = %s
    ORDER BY f.nome
"""

# ============================================================================
# QUERIES DE ANOS LETIVOS
# ============================================================================

QUERY_ANO_LETIVO_ATUAL = """
    SELECT id, ano, data_inicio, data_fim
    FROM anosletivos
    WHERE CURDATE() BETWEEN data_inicio AND data_fim
    LIMIT 1
"""

QUERY_LISTAR_ANOS_LETIVOS = """
    SELECT id, ano, data_inicio, data_fim
    FROM anosletivos
    ORDER BY ano DESC
"""

QUERY_ANO_LETIVO_POR_ANO = """
    SELECT id, ano, data_inicio, data_fim
    FROM anosletivos
    WHERE ano = %s
    LIMIT 1
"""

# ============================================================================
# QUERIES DE ESTATÍSTICAS E DASHBOARD
# ============================================================================

QUERY_ESTATISTICAS_ALUNOS = """
    SELECT 
        COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN a.id END) as total_ativos,
        COUNT(DISTINCT CASE WHEN m.status IN ('Transferido', 'Transferida') THEN a.id END) as total_transferidos
    FROM alunos a
    JOIN matriculas m ON a.id = m.aluno_id
    JOIN turmas t ON m.turma_id = t.id
    WHERE m.ano_letivo_id = %s AND a.escola_id = %s
"""

QUERY_ESTATISTICAS_POR_SERIE = """
    SELECT 
        s.id,
        s.nome as serie,
        s.ciclo,
        COUNT(DISTINCT t.id) as total_turmas,
        COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN m.aluno_id END) as alunos_ativos
    FROM series s
    LEFT JOIN turmas t ON s.id = t.serie_id AND t.ano_letivo_id = %s
    LEFT JOIN Matriculas m ON t.id = m.turma_id
    WHERE t.escola_id = %s OR t.escola_id IS NULL
    GROUP BY s.id, s.nome, s.ciclo
    HAVING total_turmas > 0
    ORDER BY s.ordem
"""

QUERY_ESTATISTICAS_POR_TURNO = """
    SELECT 
        t.turno,
        COUNT(DISTINCT t.id) as total_turmas,
        COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN m.aluno_id END) as total_alunos
    FROM turmas t
    LEFT JOIN Matriculas m ON t.id = m.turma_id
    WHERE t.ano_letivo_id = %s AND t.escola_id = %s
    GROUP BY t.turno
    ORDER BY t.turno
"""

# ============================================================================
# QUERIES DE NOTAS E FREQUÊNCIA
# ============================================================================

QUERY_NOTAS_ALUNO = """
    SELECT 
        n.id,
        n.disciplina,
        n.bimestre,
        n.nota,
        n.conceito,
        n.observacao
    FROM notas n
    WHERE n.aluno_id = %s AND n.ano_letivo_id = %s
    ORDER BY n.disciplina, n.bimestre
"""

QUERY_FREQUENCIA_ALUNO = """
    SELECT 
        f.mes,
        f.dias_letivos,
        f.dias_presentes,
        f.dias_ausentes,
        ROUND((f.dias_presentes / f.dias_letivos) * 100, 2) as percentual_presenca
    FROM frequencia f
    WHERE f.aluno_id = %s AND f.ano_letivo_id = %s
    ORDER BY f.mes
"""

# ============================================================================
# QUERIES DE DOCUMENTOS E LOGS
# ============================================================================

QUERY_HISTORICO_DOCUMENTOS_ALUNO = """
    SELECT 
        d.id,
        d.tipo_documento,
        d.data_geracao,
        d.gerado_por,
        f.nome as gerado_por_nome
    FROM documentos_gerados d
    LEFT JOIN Funcionarios f ON d.gerado_por = f.id
    WHERE d.aluno_id = %s
    ORDER BY d.data_geracao DESC
    LIMIT 50
"""

QUERY_LOG_ACOES_USUARIO = """
    SELECT 
        l.id,
        l.acao,
        l.descricao,
        l.data_hora,
        f.nome as usuario_nome
    FROM logs_sistema l
    LEFT JOIN Funcionarios f ON l.usuario_id = f.id
    WHERE l.usuario_id = %s
    ORDER BY l.data_hora DESC
    LIMIT 100
"""

# ============================================================================
# FUNÇÕES AUXILIARES PARA CONSTRUÇÃO DE QUERIES DINÂMICAS
# ============================================================================

def adicionar_filtros_aluno(filtros_dict: dict) -> tuple[str, list]:
    """
    Constrói cláusulas WHERE dinâmicas para filtros de aluno.
    
    Args:
        filtros_dict: Dicionário com filtros (nome, cpf, serie_id, turma_id, status)
    
    Returns:
        Tupla (clausula_where, parametros)
    """
    clausulas = []
    parametros = []
    
    if filtros_dict.get('nome'):
        clausulas.append("a.nome LIKE %s")
        parametros.append(f"%{filtros_dict['nome']}%")
    
    if filtros_dict.get('cpf'):
        clausulas.append("a.cpf LIKE %s")
        parametros.append(f"%{filtros_dict['cpf']}%")
    
    if filtros_dict.get('serie_id'):
        clausulas.append("s.id = %s")
        parametros.append(filtros_dict['serie_id'])
    
    if filtros_dict.get('turma_id'):
        clausulas.append("t.id = %s")
        parametros.append(filtros_dict['turma_id'])
    
    if filtros_dict.get('status'):
        clausulas.append("m.status = %s")
        parametros.append(filtros_dict['status'])
    
    where_clause = " AND ".join(clausulas) if clausulas else "1=1"
    
    return where_clause, parametros


def adicionar_filtros_turma(filtros_dict: dict) -> tuple[str, list]:
    """
    Constrói cláusulas WHERE dinâmicas para filtros de turma.
    
    Args:
        filtros_dict: Dicionário com filtros (serie_id, turno, ano_letivo_id)
    
    Returns:
        Tupla (clausula_where, parametros)
    """
    clausulas = []
    parametros = []
    
    if filtros_dict.get('serie_id'):
        clausulas.append("t.serie_id = %s")
        parametros.append(filtros_dict['serie_id'])
    
    if filtros_dict.get('turno'):
        clausulas.append("t.turno = %s")
        parametros.append(filtros_dict['turno'])
    
    if filtros_dict.get('ano_letivo_id'):
        clausulas.append("t.ano_letivo_id = %s")
        parametros.append(filtros_dict['ano_letivo_id'])
    
    if filtros_dict.get('escola_id'):
        clausulas.append("t.escola_id = %s")
        parametros.append(filtros_dict['escola_id'])
    
    where_clause = " AND ".join(clausulas) if clausulas else "1=1"
    
    return where_clause, parametros
