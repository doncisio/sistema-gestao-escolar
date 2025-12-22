"""
Copia as disciplinas da escola_id=60 (EM Profª Nadir Nascimento Moraes)
para as 48 escolas inseridas mais recentemente que ainda não possuem disciplinas.
"""
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import get_cursor, get_connection

def identificar_escolas_alvo():
    """Identifica as 48 escolas mais recentes sem disciplinas."""
    with get_cursor() as cur:
        # Buscar as 48 escolas com maior ID que têm id_geduc
        cur.execute("""
            SELECT e.id, e.nome
            FROM escolas e
            WHERE e.id_geduc IS NOT NULL
            ORDER BY e.id DESC
            LIMIT 48
        """)
        candidatas = cur.fetchall()
        
        # Filtrar apenas as que não têm disciplinas
        escolas_sem_disc = []
        for esc in candidatas:
            cur.execute("""
                SELECT COUNT(*) as total
                FROM disciplinas
                WHERE escola_id = %s
            """, (esc['id'],))
            result = cur.fetchone()
            if result['total'] == 0:
                escolas_sem_disc.append(esc)
        
        return escolas_sem_disc

def obter_disciplinas_modelo():
    """Obtém as disciplinas da escola_id=60."""
    with get_cursor() as cur:
        cur.execute("""
            SELECT nome, nivel_id, carga_horaria
            FROM disciplinas
            WHERE escola_id = 60
            ORDER BY id
        """)
        return cur.fetchall()

def copiar_disciplinas():
    """Executa a cópia das disciplinas."""
    print("=" * 100)
    print("CÓPIA DE DISCIPLINAS PARA ESCOLAS NOVAS")
    print("=" * 100)
    
    # 1. Identificar escolas alvo
    print("\n1. Identificando escolas alvo...")
    escolas = identificar_escolas_alvo()
    print(f"   Encontradas {len(escolas)} escolas das 48 mais recentes sem disciplinas\n")
    
    if not escolas:
        print("   Nenhuma escola para processar!")
        return
    
    # Mostrar lista
    print("   Escolas que receberão disciplinas:")
    for esc in escolas:
        print(f"      ID {esc['id']:3} | {esc['nome']}")
    
    # 2. Obter disciplinas modelo
    print("\n2. Obtendo disciplinas modelo da escola_id=60...")
    disciplinas_modelo = obter_disciplinas_modelo()
    print(f"   {len(disciplinas_modelo)} disciplinas encontradas")
    
    # Mostrar resumo
    por_nivel = {}
    for d in disciplinas_modelo:
        nivel = d['nivel_id'] or 0
        if nivel not in por_nivel:
            por_nivel[nivel] = []
        por_nivel[nivel].append(d['nome'])
    
    for nivel, nomes in sorted(por_nivel.items()):
        print(f"      Nível {nivel}: {len(nomes)} disciplinas")
    
    # 3. Confirmação
    print("\n" + "=" * 100)
    print(f"CONFIRMAÇÃO: Serão inseridas {len(disciplinas_modelo)} disciplinas em {len(escolas)} escolas")
    print(f"Total de inserções: {len(disciplinas_modelo) * len(escolas)}")
    print("=" * 100)
    
    resposta = input("\nDeseja continuar? (s/n): ").strip().lower()
    if resposta != 's':
        print("Operação cancelada pelo usuário.")
        return
    
    # 4. Executar inserções
    print("\n3. Executando inserções...")
    
    total_inserido = 0
    with get_connection() as conn:
        cur = conn.cursor()
        
        for esc in escolas:
            for disc in disciplinas_modelo:
                cur.execute("""
                    INSERT INTO disciplinas (nome, nivel_id, carga_horaria, escola_id)
                    VALUES (%s, %s, %s, %s)
                """, (disc['nome'], disc['nivel_id'], disc['carga_horaria'], esc['id']))
                total_inserido += 1
            
            print(f"   ✓ Escola ID {esc['id']:3} | {esc['nome'][:60]:60} | {len(disciplinas_modelo)} disciplinas")
        
        conn.commit()
        print(f"\n   Total de disciplinas inseridas: {total_inserido}")
    
    # 5. Gerar relatório
    print("\n4. Gerando relatório...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    relatorio_path = Path(__file__).parent.parent / 'config' / f'relatorio_copia_disciplinas_{timestamp}.txt'
    
    with open(relatorio_path, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("RELATÓRIO DE CÓPIA DE DISCIPLINAS\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Escola modelo: ID 60 - EM Profª Nadir Nascimento Moraes\n")
        f.write(f"Disciplinas copiadas por escola: {len(disciplinas_modelo)}\n")
        f.write(f"Total de escolas processadas: {len(escolas)}\n")
        f.write(f"Total de inserções: {total_inserido}\n\n")
        
        f.write("=" * 100 + "\n")
        f.write("DISCIPLINAS MODELO (escola_id=60)\n")
        f.write("=" * 100 + "\n\n")
        
        for nivel, nomes in sorted(por_nivel.items()):
            f.write(f"Nível {nivel}:\n")
            for d in disciplinas_modelo:
                if (d['nivel_id'] or 0) == nivel:
                    ch = f"{d['carga_horaria']}h" if d['carga_horaria'] else "N/A"
                    f.write(f"  - {d['nome']:35} | CH: {ch}\n")
            f.write("\n")
        
        f.write("=" * 100 + "\n")
        f.write("ESCOLAS QUE RECEBERAM DISCIPLINAS\n")
        f.write("=" * 100 + "\n\n")
        
        for esc in escolas:
            f.write(f"ID {esc['id']:3} | {esc['nome']}\n")
    
    print(f"   Relatório salvo em: {relatorio_path}")
    
    # 6. Verificação final
    print("\n5. Verificação final...")
    with get_cursor() as cur:
        for esc in escolas[:5]:  # Verificar apenas as primeiras 5 como amostra
            cur.execute("""
                SELECT COUNT(*) as total
                FROM disciplinas
                WHERE escola_id = %s
            """, (esc['id'],))
            result = cur.fetchone()
            print(f"   Escola ID {esc['id']:3}: {result['total']} disciplinas")
    
    print("\n" + "=" * 100)
    print("PROCESSO CONCLUÍDO COM SUCESSO!")
    print("=" * 100)

if __name__ == "__main__":
    copiar_disciplinas()
