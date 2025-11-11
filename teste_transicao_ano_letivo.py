"""
Script de Teste - Transição de Ano Letivo
==========================================

Este script permite testar a funcionalidade de transição
antes de aplicar em produção.

IMPORTANTE: Execute em uma cópia do banco de dados!
"""

import mysql.connector
from conexao import conectar_bd


def verificar_situacao_atual():
    """Verifica a situação atual do banco antes da transição"""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DA SITUAÇÃO ATUAL")
    print("="*60)
    
    try:
        conn = conectar_bd()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados.")
            return
        
        cursor = conn.cursor(dictionary=True)
        
        # 1. Ano letivo atual
        cursor.execute("""
            SELECT id, ano_letivo 
            FROM anosletivos 
            ORDER BY ano_letivo DESC 
            LIMIT 1
        """)
        ano_atual = cursor.fetchone()
        print(f"\n📅 Ano Letivo Atual: {ano_atual['ano_letivo']} (ID: {ano_atual['id']})")
        
        # 2. Total de matrículas por status
        cursor.execute("""
            SELECT 
                m.status,
                COUNT(*) as total
            FROM Matriculas m
            WHERE m.ano_letivo_id = %s
            GROUP BY m.status
            ORDER BY total DESC
        """, (ano_atual['id'],))
        
        print(f"\n📊 Matrículas no ano {ano_atual['ano_letivo']}:")
        for row in cursor.fetchall():
            print(f"   {row['status']}: {row['total']}")
        
        # 3. Alunos únicos ativos
        cursor.execute("""
            SELECT COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = 60
        """, (ano_atual['id'],))
        
        resultado = cursor.fetchone()
        print(f"\n👥 Total de Alunos Únicos (Ativos): {resultado['total']}")
        
        # 4. Alunos que NÃO serão rematriculados
        cursor.execute("""
            SELECT COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status IN ('Transferido', 'Transferida', 'Cancelado', 'Evadido')
            AND a.escola_id = 60
        """, (ano_atual['id'],))
        
        resultado = cursor.fetchone()
        print(f"❌ Alunos que NÃO serão rematriculados: {resultado['total']}")
        
        # 5. Distribuição por série/turma
        cursor.execute("""
            SELECT 
                CONCAT(s.nome, ' ', t.nome) as serie_turma,
                COUNT(DISTINCT a.id) as total_ativos
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            JOIN turmas t ON m.turma_id = t.id
            JOIN serie s ON t.serie_id = s.id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = 60
            GROUP BY t.id, s.nome, t.nome
            ORDER BY s.nome, t.nome
        """, (ano_atual['id'],))
        
        print(f"\n📚 Distribuição por Série/Turma:")
        total_geral = 0
        for row in cursor.fetchall():
            print(f"   {row['serie_turma']}: {row['total_ativos']} alunos")
            total_geral += row['total_ativos']
        print(f"   ───────────────────")
        print(f"   TOTAL: {total_geral} alunos")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Verificação concluída!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar situação: {str(e)}")
        import traceback
        traceback.print_exc()


def simular_transicao():
    """Simula a transição mostrando o que seria feito"""
    print("\n" + "="*60)
    print("SIMULAÇÃO DA TRANSIÇÃO")
    print("="*60)
    
    try:
        conn = conectar_bd()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados.")
            return
        
        cursor = conn.cursor(dictionary=True)
        
        # Buscar ano atual
        cursor.execute("""
            SELECT id, ano_letivo 
            FROM anosletivos 
            ORDER BY ano_letivo DESC 
            LIMIT 1
        """)
        ano_atual = cursor.fetchone()
        ano_novo = ano_atual['ano_letivo'] + 1
        
        print(f"\n📅 Transição: {ano_atual['ano_letivo']} → {ano_novo}")
        
        # Contar matrículas que serão encerradas
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM Matriculas
            WHERE ano_letivo_id = %s
            AND status = 'Ativo'
        """, (ano_atual['id'],))
        
        resultado = cursor.fetchone()
        print(f"\n🔒 Matrículas que serão encerradas (status → 'Concluído'): {resultado['total']}")
        
        # Contar novas matrículas que serão criadas
        cursor.execute("""
            SELECT COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = 60
        """, (ano_atual['id'],))
        
        resultado = cursor.fetchone()
        print(f"✨ Novas matrículas que serão criadas: {resultado['total']}")
        
        # Alunos excluídos
        cursor.execute("""
            SELECT 
                m.status,
                COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status IN ('Transferido', 'Transferida', 'Cancelado', 'Evadido')
            AND a.escola_id = 60
            GROUP BY m.status
        """, (ano_atual['id'],))
        
        print(f"\n❌ Alunos que NÃO serão rematriculados:")
        for row in cursor.fetchall():
            print(f"   {row['status']}: {row['total']}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Simulação concluída!")
        print("⚠️  Esta foi apenas uma simulação. Nenhum dado foi alterado.")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro na simulação: {str(e)}")
        import traceback
        traceback.print_exc()


def verificar_proximos_anos():
    """Verifica se o próximo ano já existe no banco"""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE ANOS LETIVOS")
    print("="*60)
    
    try:
        conn = conectar_bd()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados.")
            return
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, ano_letivo
            FROM anosletivos
            ORDER BY ano_letivo
        """)
        
        print("\n📋 Anos Letivos Cadastrados:")
        for row in cursor.fetchall():
            print(f"   {row['ano_letivo']} (ID: {row['id']})")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()


def menu_principal():
    """Menu principal do teste"""
    while True:
        print("\n" + "="*60)
        print("TESTE - TRANSIÇÃO DE ANO LETIVO")
        print("="*60)
        print("\n1. Verificar Situação Atual")
        print("2. Simular Transição")
        print("3. Verificar Anos Letivos Cadastrados")
        print("4. Sair")
        print("\n" + "="*60)
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            verificar_situacao_atual()
        elif opcao == "2":
            simular_transicao()
        elif opcao == "3":
            verificar_proximos_anos()
        elif opcao == "4":
            print("\n👋 Encerrando...\n")
            break
        else:
            print("\n❌ Opção inválida! Tente novamente.")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("⚠️  ATENÇÃO: Este é um script de TESTE")
    print("="*60)
    print("\nEste script NÃO faz alterações no banco de dados.")
    print("Use-o para verificar a situação antes da transição real.")
    print("\n" + "="*60 + "\n")
    
    input("Pressione ENTER para continuar...")
    
    menu_principal()
