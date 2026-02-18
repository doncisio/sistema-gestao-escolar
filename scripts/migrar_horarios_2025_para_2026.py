"""
Script para migrar horários do ano letivo 2025 para 2026

Este script copia todos os horários salvos em 2025 para o ano letivo 2026,
permitindo que você use os mesmos horários como base no novo ano.

IMPORTANTE: Execute este script apenas uma vez, após o início de 2026.
"""

import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.conexao import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def migrar_horarios_2025_para_2026():
    """Copia horários de 2025 para 2026"""
    try:
        conn = conectar_bd()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return False
        
        cursor = conn.cursor(dictionary=True)
        
        # Verificar se existe coluna ano_letivo
        cursor.execute("""
            SELECT COUNT(*) as existe FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'horarios_importados' 
            AND COLUMN_NAME = 'ano_letivo'
        """)
        
        tem_coluna = cursor.fetchone()['existe'] > 0
        
        if not tem_coluna:
            print("📝 Coluna ano_letivo não existe. Criando estrutura...")
            
            # Adicionar coluna ano_letivo
            cursor.execute("""
                ALTER TABLE horarios_importados 
                ADD COLUMN ano_letivo INT NOT NULL DEFAULT 2025
            """)
            print("✅ Coluna ano_letivo criada")
            
            # Atualizar índice único - usar novo cursor para evitar "Unread result"
            try:
                cursor2 = conn.cursor()
                
                # Verificar e remover índice antigo
                cursor2.execute("SHOW INDEX FROM horarios_importados WHERE Key_name = 'ux_horario_turma'")
                indices = cursor2.fetchall()
                
                if indices:
                    cursor2.execute("DROP INDEX ux_horario_turma ON horarios_importados")
                    print("🗑️  Índice antigo removido")
                
                cursor2.close()
            except Exception as e:
                logger.warning(f"Aviso ao remover índice antigo: {e}")
            
            cursor.execute("""
                CREATE UNIQUE INDEX ux_horario_turma 
                ON horarios_importados(turma_id, dia, horario, ano_letivo)
            """)
            print("✅ Índice único atualizado")
            
            conn.commit()
            print()
        
        # Contar horários de 2025
        cursor.execute("SELECT COUNT(*) as total FROM horarios_importados WHERE ano_letivo = 2025")
        total_2025 = cursor.fetchone()['total']
        
        if total_2025 == 0:
            print("⚠️  Nenhum horário encontrado para 2025. Nada a migrar.")
            cursor.close()
            conn.close()
            return True
        
        print(f"📋 Encontrados {total_2025} horários de 2025")
        
        # Contar horários já existentes em 2026
        cursor.execute("SELECT COUNT(*) as total FROM horarios_importados WHERE ano_letivo = 2026")
        total_2026 = cursor.fetchone()['total']
        
        if total_2026 > 0:
            print(f"⚠️  Já existem {total_2026} horários cadastrados para 2026.")
            resposta = input("Deseja sobrescrever? (s/N): ").strip().lower()
            if resposta != 's':
                print("❌ Migração cancelada pelo usuário")
                cursor.close()
                conn.close()
                return False
            
            # Deletar horários de 2026 existentes
            cursor.execute("DELETE FROM horarios_importados WHERE ano_letivo = 2026")
            print(f"🗑️  {total_2026} horários de 2026 removidos")
        
        # Copiar horários de 2025 para 2026
        sql = """
            INSERT INTO horarios_importados 
            (turma_id, dia, horario, valor, disciplina_id, professor_id, geduc_turma_id, ano_letivo)
            SELECT turma_id, dia, horario, valor, disciplina_id, professor_id, geduc_turma_id, 2026
            FROM horarios_importados 
            WHERE ano_letivo = 2025
        """
        
        cursor.execute(sql)
        migrados = cursor.rowcount
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Sucesso! {migrados} horários migrados de 2025 para 2026")
        print("\n📝 Próximos passos:")
        print("   1. Abra o sistema de gestão escolar")
        print("   2. Acesse 'Horários Escolares'")
        print("   3. Revise e ajuste os horários para 2026")
        print("   4. Atualize professores se houver mudanças")
        
        return True
        
    except Exception as e:
        logger.exception("Erro ao migrar horários")
        print(f"❌ Erro: {str(e)}")
        return False


if __name__ == "__main__":
    print("="*70)
    print("  MIGRAÇÃO DE HORÁRIOS: 2025 → 2026")
    print("="*70)
    print()
    print("Este script copiará todos os horários do ano letivo 2025 para 2026.")
    print("Os horários servirão como base, podendo ser editados depois.")
    print()
    
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    
    if resposta == 's':
        print()
        sucesso = migrar_horarios_2025_para_2026()
        print()
        
        if sucesso:
            print("="*70)
            print("  MIGRAÇÃO CONCLUÍDA!")
            print("="*70)
        else:
            print("="*70)
            print("  MIGRAÇÃO NÃO CONCLUÍDA")
            print("="*70)
            sys.exit(1)
    else:
        print("\n❌ Migração cancelada pelo usuário")
        sys.exit(0)
