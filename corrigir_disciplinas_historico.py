"""
Script para corrigir as disciplinas no histórico escolar verificando o nivel_id correto.

Regra:
- Séries 1 ao 5 (nivel_id = 2) - Séries Iniciais
- Séries 6 ao 9 (nivel_id = 3) - Séries Finais
"""

from db.connection import get_connection
from src.core.config_logs import get_logger

logger = get_logger(__name__)

def obter_nivel_id_por_serie(serie_id, cursor):
    """Obtém o nivel_id correto baseado na série."""
    cursor.execute("""
        SELECT s.nome, n.id as nivel_id, n.nome as nivel_nome
        FROM series s
        JOIN niveisensino n ON s.nivel_id = n.id
        WHERE s.id = %s
    """, (serie_id,))
    
    resultado = cursor.fetchone()
    if resultado:
        return resultado['nivel_id'], resultado['nome'], resultado['nivel_nome']
    return None, None, None

def corrigir_disciplinas_historico():
    """
    Corrige as disciplinas no histórico escolar para usar o nivel_id correto
    de acordo com a série do aluno.
    """
    print("="*80)
    print("CORREÇÃO DE DISCIPLINAS NO HISTÓRICO ESCOLAR")
    print("="*80)
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Buscar todos os registros do histórico escolar
            cursor.execute("""
                SELECT 
                    h.id,
                    h.aluno_id,
                    h.disciplina_id,
                    h.serie_id,
                    h.ano_letivo_id,
                    h.escola_id,
                    d.nome as disciplina_nome,
                    d.nivel_id as disciplina_nivel_id,
                    d.carga_horaria as disciplina_carga,
                    s.nome as serie_nome,
                    s.nivel_id as serie_nivel_id,
                    a.nome as aluno_nome
                FROM historico_escolar h
                JOIN disciplinas d ON h.disciplina_id = d.id
                JOIN series s ON h.serie_id = s.id
                JOIN Alunos a ON h.aluno_id = a.id
                ORDER BY h.aluno_id, h.ano_letivo_id, h.serie_id
            """)
            
            registros = cursor.fetchall()
            total_registros = len(registros)
            
            print(f"\nTotal de registros no histórico: {total_registros}")
            print("\nVerificando inconsistências...\n")
            
            # Agrupar problemas por tipo
            problemas = {
                'nivel_errado': [],
                'disciplina_inexistente': []
            }
            
            for reg in registros:
                # Verificar se a disciplina tem o nivel_id correto para a série
                if reg['disciplina_nivel_id'] != reg['serie_nivel_id']:
                    problemas['nivel_errado'].append(reg)
            
            # Mostrar resumo dos problemas
            print(f"Registros com nível errado: {len(problemas['nivel_errado'])}")
            
            if len(problemas['nivel_errado']) == 0:
                print("\n✅ Nenhuma inconsistência encontrada!")
                return
            
            # Mostrar alguns exemplos
            print("\n--- EXEMPLOS DE PROBLEMAS ---")
            for i, reg in enumerate(problemas['nivel_errado'][:10]):
                print(f"\n{i+1}. Aluno: {reg['aluno_nome']}")
                print(f"   Série: {reg['serie_nome']} (nivel_id={reg['serie_nivel_id']})")
                print(f"   Disciplina: {reg['disciplina_nome']} (nivel_id={reg['disciplina_nivel_id']}, "
                      f"carga={reg['disciplina_carga']}h, escola_id={reg['escola_id']}) ❌")
            
            if len(problemas['nivel_errado']) > 10:
                print(f"\n   ... e mais {len(problemas['nivel_errado']) - 10} registros")
            
            # Perguntar se deseja corrigir
            print("\n" + "="*80)
            resposta = input("\nDeseja corrigir estes problemas? (s/n): ").lower()
            
            if resposta != 's':
                print("Operação cancelada.")
                return
            
            # Corrigir os problemas
            print("\n--- INICIANDO CORREÇÃO ---\n")
            corrigidos = 0
            nao_encontrados = 0
            erros = 0
            
            for reg in problemas['nivel_errado']:
                try:
                    # Buscar a disciplina equivalente com o nivel_id correto DA MESMA ESCOLA
                    cursor.execute("""
                        SELECT id, nome, carga_horaria
                        FROM disciplinas
                        WHERE nome = %s 
                          AND nivel_id = %s 
                          AND escola_id = %s
                        LIMIT 1
                    """, (reg['disciplina_nome'], reg['serie_nivel_id'], reg['escola_id']))
                    
                    disciplina_correta = cursor.fetchone()
                    
                    if disciplina_correta:
                        # Atualizar o disciplina_id do registro
                        cursor.execute("""
                            UPDATE historico_escolar
                            SET disciplina_id = %s
                            WHERE id = %s
                        """, (disciplina_correta['id'], reg['id']))
                        
                        print(f"✓ Aluno {reg['aluno_nome']}: {reg['disciplina_nome']} "
                              f"(disciplina_id alterado | nivel {reg['disciplina_nivel_id']} → {reg['serie_nivel_id']} | "
                              f"carga {reg['disciplina_carga']}h → {disciplina_correta['carga_horaria']}h)")
                        corrigidos += 1
                    else:
                        print(f"✗ Disciplina '{reg['disciplina_nome']}' não encontrada para escola_id={reg['escola_id']}, nível {reg['serie_nivel_id']}")
                        nao_encontrados += 1
                        
                except Exception as e:
                    logger.exception(f"Erro ao corrigir registro {reg['id']}: {e}")
                    erros += 1
            
            # Commit das alterações
            conn.commit()
            
            # Mostrar resumo
            print("\n" + "="*80)
            print("RESUMO DA CORREÇÃO")
            print("="*80)
            print(f"Total de problemas encontrados: {len(problemas['nivel_errado'])}")
            print(f"Registros corrigidos: {corrigidos}")
            print(f"Disciplinas não encontradas: {nao_encontrados}")
            print(f"Erros: {erros}")
            print("="*80)
            
            if nao_encontrados > 0:
                print("\n⚠️  ATENÇÃO: Algumas disciplinas não foram encontradas para o nível correto.")
                print("   Isso pode indicar que essas disciplinas não existem no cadastro")
                print("   para o nível de ensino correspondente.")
                
            if corrigidos > 0:
                print(f"\n✅ {corrigidos} registros foram corrigidos com sucesso!")
            
    except Exception as e:
        logger.exception(f"Erro ao corrigir disciplinas: {e}")
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    corrigir_disciplinas_historico()
