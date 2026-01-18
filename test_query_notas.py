from db.connection import get_cursor

with get_cursor() as cursor:
    # Testar a query usada nos arquivos de ata
    cursor.execute("""
        SELECT aluno_id, disciplina_id, media_final as nota
        FROM notas_finais 
        WHERE ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = 2025)
        LIMIT 5
    """)
    
    print("Resultados da query de notas_finais:")
    results = cursor.fetchall()
    print(f"Total de registros retornados: {len(results)}")
    for row in results:
        print(row)
