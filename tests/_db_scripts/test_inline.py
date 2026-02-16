"""Teste inline do código de listar_turmas."""
import sys
sys.path.insert(0, 'c:\\gestao')

from db.connection import get_connection
from src.core.config_logs import get_logger

logger = get_logger(__name__)

print("Executando código da função listar_turmas inline...")

ano_letivo_id = None
serie_id = None
turno = None
escola_id = None
aplicar_filtro_perfil = False

try:
    # Obter filtro de turmas baseado no perfil (se aplicável)
    filtro_perfil_sql = ""
    filtro_perfil_params = []
    
    print("Antes do with get_connection()...")
    
    with get_connection() as conn:
        print(f"Dentro do with, conn = {type(conn)}")
        cursor = conn.cursor(dictionary=True)
        print(f"Cursor criado: {type(cursor)}")
        
        # Query base
        query = """
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
                al.ano_letivo as ano_letivo,
                COALESCE(COUNT(DISTINCT m.id), 0) as total_alunos
            FROM turmas t
            LEFT JOIN series s ON t.serie_id = s.id
            LEFT JOIN anosletivos al ON t.ano_letivo_id = al.id
            LEFT JOIN Matriculas m ON m.turma_id = t.id AND m.status = 'Ativo'
        """
        
        # Adicionar filtros
        filtros = []
        params = []
        
        if ano_letivo_id is not None:
            filtros.append("t.ano_letivo_id = %s")
            params.append(ano_letivo_id)
        
        if serie_id is not None:
            filtros.append("t.serie_id = %s")
            params.append(serie_id)
        
        if turno is not None:
            filtros.append("t.turno = %s")
            params.append(turno)
        
        if escola_id is not None:
            filtros.append("t.escola_id = %s")
            params.append(escola_id)
        
        # Adicionar filtro base (WHERE 1=1 para facilitar concatenação)
        if filtros:
            query += " WHERE " + " AND ".join(filtros)
        else:
            query += " WHERE 1=1"
        
        # Aplicar filtro de perfil do usuário (professor vê apenas suas turmas)
        if filtro_perfil_sql:
            query += filtro_perfil_sql
            params.extend(filtro_perfil_params)
        
        query += """
            GROUP BY t.id, t.nome, t.turno, t.capacidade_maxima, 
                     t.ano_letivo_id, t.serie_id, t.escola_id, t.professor_id,
                     s.nome, s.ciclo, al.ano_letivo
            ORDER BY s.ciclo, s.nome, t.turno, t.nome
        """
        
        print("Executando query...")
        try:
            cursor.execute(query, tuple(params))
            print("Execute OK")
        except Exception as exec_err:
            print(f"ERRO no execute: {exec_err}")
            raise
        print("Query executada, buscando resultados...")
        try:
            turmas = cursor.fetchall()
            print(f"Fetch OK: {len(turmas)} resultados")
        except Exception as fetch_err:
            print(f"ERRO no fetchall: {fetch_err}")
            raise
        
        print(f"Turmas obtidas: {len(turmas)}")
        print(f"Primeiras 3: {turmas[:3] if turmas else 'vazio'}")
        
        logger.info(f"Listadas {len(turmas)} turmas (filtros: ano={ano_letivo_id}, serie={serie_id}, turno={turno})")
        # return turmas  # Não pode retornar aqui, só print
        
    print("Saiu do with")
        
except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()

print("Fim do script")

