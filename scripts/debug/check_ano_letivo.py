from db.connection import get_cursor

with get_cursor() as cursor:
    cursor.execute('SELECT id, ano_letivo FROM anosletivos WHERE ano_letivo = 2025')
    result = cursor.fetchone()
    if result:
        print(f"Ano letivo 2025 tem ID: {result['id']}")
    else:
        print("Ano letivo 2025 não encontrado!")
        
    cursor.execute('SELECT * FROM anosletivos')
    print("\nTodos os anos letivos:")
    for row in cursor.fetchall():
        print(f"ID {row['id']}: {row['ano_letivo']}")
