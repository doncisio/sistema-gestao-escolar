from db.connection import get_cursor

with get_cursor() as cursor:
    cursor.execute('SELECT COUNT(*) as cnt FROM notas_finais')
    result = cursor.fetchone()
    print(f"Registros em notas_finais: {result['cnt']}")
    
    if result['cnt'] > 0:
        cursor.execute('SELECT * FROM notas_finais LIMIT 5')
        print("\nPrimeiros 5 registros:")
        for row in cursor.fetchall():
            print(row)
