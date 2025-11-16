"""
Script de Teste - Transição de Ano Letivo
==========================================

Este script permite testar a funcionalidade de transição
antes de aplicar em produção.

IMPORTANTE: Execute em uma cópia do banco de dados!
"""

import mysql.connector
"""

import mysql.connector
from conexao import conectar_bd
from typing import Any, cast
from config_logs import get_logger

logger = get_logger(__name__)

def verificar_situacao_atual():
    """Verifica a situação atual do banco antes da transição"""
    logger.info("\n" + "="*60)
    logger.info("VERIFICAÇÃO DA SITUAÇÃO ATUAL")
    logger.info("="*60)
    
    try:
        conn: Any = conectar_bd()
        if not conn:
            logger.error("❌ Erro: Não foi possível conectar ao banco de dados.")
            return
        
        cursor = cast(Any, conn).cursor(dictionary=True)
        
        # 1. Ano letivo atual
        cursor.execute("""
            SELECT id, ano_letivo 
            FROM anosletivos 
            ORDER BY ano_letivo DESC 
            LIMIT 1
        """)
        ano_atual = cast(Any, cursor.fetchone())
        if not ano_atual:
            logger.error("❌ Erro: não foi possível obter o ano letivo atual.")
            cursor.close()
            conn.close()
            return
        logger.info(f"\n📅 Ano Letivo Atual: {ano_atual['ano_letivo']} (ID: {ano_atual['id']})")
        
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
        
        logger.info(f"\n📊 Matrículas no ano {ano_atual['ano_letivo']}:")
        for row in cast(Any, cursor.fetchall()):
            logger.info(f"   {row['status']}: {row['total']}")
        
        # 3. Alunos únicos ativos
        cursor.execute("""
            SELECT COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = 60
        """, (ano_atual['id'],))
        
        resultado = cast(Any, cursor.fetchone())
        logger.info(f"\n👥 Total de Alunos Únicos (Ativos): {resultado['total']}")
        
        # 4. Alunos que NÃO serão rematriculados
        cursor.execute("""
            SELECT COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status IN ('Transferido', 'Transferida', 'Cancelado', 'Evadido')
            AND a.escola_id = 60
        """, (ano_atual['id'],))
        
        resultado = cast(Any, cursor.fetchone())
        logger.info(f"❌ Alunos que NÃO serão rematriculados: {resultado['total']}")
        
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
        
        logger.info(f"\n📚 Distribuição por Série/Turma:")
        total_geral = 0
        for row in cast(Any, cursor.fetchall()):
            logger.info(f"   {row['serie_turma']}: {row['total_ativos']} alunos")
        logger.info(f"\n📚 Distribuição por Série/Turma:")
        logger.info(f"   ───────────────────")
        logger.info(f"   TOTAL: {total_geral} alunos")
            logger.info(f"   {row['serie_turma']}: {row['total_ativos']} alunos")
        cursor.close()
        logger.info(f"   ───────────────────")
        logger.info(f"   TOTAL: {total_geral} alunos")
        logger.info("\n" + "="*60)
        logger.info("✅ Verificação concluída!")
        logger.info("="*60 + "\n")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Verificação concluída!")
        logger.info("="*60 + "\n")
        traceback.print_exc()

        logger.exception(f"\n❌ Erro ao verificar situação: {str(e)}")
def simular_transicao():
    """Simula a transição mostrando o que seria feito"""
    logger.info("\n" + "="*60)
    logger.info("SIMULAÇÃO DA TRANSIÇÃO")
    logger.info("="*60)
    logger.info("\n" + "="*60)
    logger.info("SIMULAÇÃO DA TRANSIÇÃO")
    logger.info("="*60)
        if not conn:
            logger.error("❌ Erro: Não foi possível conectar ao banco de dados.")
            return
        
            logger.error("❌ Erro: Não foi possível conectar ao banco de dados.")
        
        # Buscar ano atual
        cursor.execute("""
            SELECT id, ano_letivo 
            FROM anosletivos 
            ORDER BY ano_letivo DESC 
            LIMIT 1
        """)
        ano_atual = cast(Any, cursor.fetchone())
        if not ano_atual:
            logger.error("❌ Erro: não foi possível obter o ano letivo atual para simulação.")
            cursor.close()
            conn.close()
        ano_novo = ano_atual['ano_letivo'] + 1
        
        logger.info(f"\n📅 Transição: {ano_atual['ano_letivo']} → {ano_novo}")
        
        # Contar matrículas que serão encerradas
        logger.info(f"\n📅 Transição: {ano_atual['ano_letivo']} → {ano_novo}")
            SELECT COUNT(*) as total
            FROM Matriculas
            WHERE ano_letivo_id = %s
            AND status = 'Ativo'
        """, (ano_atual['id'],))
        
        resultado = cast(Any, cursor.fetchone())
        logger.info(f"\n🔒 Matrículas que serão encerradas (status → 'Concluído'): {resultado['total']}")
        
        # Contar novas matrículas que serão criadas
        logger.info(f"\n🔒 Matrículas que serão encerradas (status → 'Concluído'): {resultado['total']}")
            SELECT COUNT(DISTINCT a.id) as total
            FROM Alunos a
            JOIN Matriculas m ON a.id = m.aluno_id
            WHERE m.ano_letivo_id = %s
            AND m.status = 'Ativo'
            AND a.escola_id = 60
        """, (ano_atual['id'],))
        
        resultado = cast(Any, cursor.fetchone())
        logger.info(f"✨ Novas matrículas que serão criadas: {resultado['total']}")
        
        # Alunos excluídos
        logger.info(f"✨ Novas matrículas que serão criadas: {resultado['total']}")
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
        
        logger.info(f"\n❌ Alunos que NÃO serão rematriculados:")
        for row in cast(Any, cursor.fetchall()):
            logger.info(f"   {row['status']}: {row['total']}")
        logger.info(f"\n❌ Alunos que NÃO serão rematriculados:")
        cursor.close()
            logger.info(f"   {row['status']}: {row['total']}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Simulação concluída!")
        logger.info("⚠️  Esta foi apenas uma simulação. Nenhum dado foi alterado.")
        logger.info("\n" + "="*60)
        logger.info("✅ Simulação concluída!")
        logger.info("⚠️  Esta foi apenas uma simulação. Nenhum dado foi alterado.")
        logger.info("="*60 + "\n")
        import traceback
        traceback.print_exc()
        logger.exception(f"\n❌ Erro na simulação: {str(e)}")

def verificar_proximos_anos():
    """Verifica se o próximo ano já existe no banco"""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE ANOS LETIVOS")
    logger.info("\n" + "="*60)
    logger.info("VERIFICAÇÃO DE ANOS LETIVOS")
    logger.info("="*60)
        conn = conectar_bd()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados.")
            return
            logger.error("❌ Erro: Não foi possível conectar ao banco de dados.")
        cursor = cast(Any, conn).cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, ano_letivo
            FROM anosletivos
            ORDER BY ano_letivo
        """)
        
        print("\n📋 Anos Letivos Cadastrados:")
        for row in cast(Any, cursor.fetchall()):
        logger.info("\n📋 Anos Letivos Cadastrados:")
        
            logger.info(f"   {row['ano_letivo']} (ID: {row['id']})")
        conn.close()
        
        print("\n" + "="*60 + "\n")
        
        logger.info("\n" + "="*60 + "\n")
        print(f"\n❌ Erro: {str(e)}")
        import traceback
        logger.exception(f"\n❌ Erro: {str(e)}")


def menu_principal():
    """Menu principal do teste"""
    while True:
        print("\n" + "="*60)
        logger.info("\n" + "="*60)
        logger.info("TESTE - TRANSIÇÃO DE ANO LETIVO")
        logger.info("="*60)
        logger.info("\n1. Verificar Situação Atual")
        logger.info("2. Simular Transição")
        logger.info("3. Verificar Anos Letivos Cadastrados")
        logger.info("4. Sair")
        logger.info("\n" + "="*60)
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            verificar_situacao_atual()
        elif opcao == "2":
            simular_transicao()
        elif opcao == "3":
            verificar_proximos_anos()
        elif opcao == "4":
            print("\n👋 Encerrando...\n")
            logger.info("\n👋 Encerrando...\n")
        else:
            print("\n❌ Opção inválida! Tente novamente.")
            logger.warning("\n❌ Opção inválida! Tente novamente.")

if __name__ == "__main__":
    logger.warning("\n" + "="*60)
    logger.warning("⚠️  ATENÇÃO: Este é um script de TESTE")
    logger.warning("="*60)
    logger.info("\nEste script NÃO faz alterações no banco de dados.")
    logger.info("Use-o para verificar a situação antes da transição real.")
    logger.warning("\n" + "="*60 + "\n")
    
    input("Pressione ENTER para continuar...")
    
    menu_principal()
