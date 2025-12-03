"""Script temporário para migrar dados de serie para series"""
from db.connection import get_connection

with get_connection() as conn:
    cursor = conn.cursor(dictionary=True)
    
    # Verificar estrutura da tabela serie
    print("=== Estrutura da tabela 'serie' ===")
    cursor.execute('DESCRIBE serie')
    cols_serie = cursor.fetchall()
    for r in cols_serie:
        print(f"  {r['Field']} - {r['Type']}")
    
    # Dropar tabela series existente e recriar com mesma estrutura de serie
    print("\n=== Recriando tabela 'series' com mesma estrutura de 'serie' ===")
    
    # Dropar a tabela series
    cursor.execute('DROP TABLE IF EXISTS series')
    print("Tabela series dropada.")
    
    # Criar tabela series como cópia da estrutura de serie
    cursor.execute('CREATE TABLE series LIKE serie')
    print("Tabela series criada com mesma estrutura de serie.")
    
    # Copiar todos os dados
    cursor.execute('INSERT INTO series SELECT * FROM serie')
    conn.commit()
    print(f"Dados copiados! {cursor.rowcount} registros.")
    
    # Verificar
    print("\n=== Verificação final ===")
    cursor.execute('DESCRIBE series')
    print("Estrutura de series:")
    for r in cursor.fetchall():
        print(f"  {r['Field']} - {r['Type']}")
    
    cursor.execute('SELECT COUNT(*) as total FROM series')
    print(f"\nTotal em series: {cursor.fetchone()['total']}")
