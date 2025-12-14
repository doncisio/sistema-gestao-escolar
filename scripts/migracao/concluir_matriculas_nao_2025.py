"""Script para concluir matrículas mantendo apenas as ativas do ano 2025 da escola 60.

Este script identifica e conclui matrículas que:
1. São de anos letivos anteriores a 2025 (de qualquer escola)
2. São de outras escolas (mesmo que sejam de 2025)

Mantém ATIVAS apenas matrículas:
- Da escola 60 (Nadir Nascimento Moraes)
- Do ano letivo 2025

NÃO altera matrículas com status protegido:
- Evadido / Evadida
- Transferido / Transferida
- Concluído / Concluida (já concluídas)

Uso:
  - Dry-run (padrão): mostra o que seria atualizado
      python concluir_matriculas_nao_2025.py

  - Aplicar alterações no banco:
      python concluir_matriculas_nao_2025.py --apply

Opções:
  --escola ID         : ID da escola principal (padrão: 60)
  --ano ANO           : Ano letivo de referência (padrão: 2025)
  --limit N           : Limitar processamento para testes
  --stats             : Mostrar apenas estatísticas

Observação: faça backup antes de rodar `--apply` em produção.
"""
from __future__ import annotations
import argparse
from typing import List, Tuple, Optional
from db.connection import get_connection
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Status que devem ser definidos como concluído
CONCLUDED_STATUS = 'Concluído'

# Status que NÃO devem ser alterados (manter como estão)
STATUS_PROTEGIDOS = (
    'Evadido', 'Evadida', 
    'Transferido', 'Transferida',
    'Concluído', 'Concluida',
)


def obter_estatisticas_gerais(ano: int = 2025, escola_id: int = 60) -> dict:
    """
    Retorna estatísticas gerais sobre as matrículas de todo o sistema.
    """
    stats = {}
    status_protegidos_sql = ', '.join(['%s'] * len(STATUS_PROTEGIDOS))
    
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Total de matrículas ativas no sistema
        cur.execute("SELECT COUNT(*) FROM matriculas WHERE status = 'Ativo'")
        stats['total_ativas'] = cur.fetchone()[0]
        
        # Matrículas ativas da escola principal no ano de referência
        cur.execute("""
            SELECT COUNT(*) FROM matriculas m
            JOIN alunos al ON m.aluno_id = al.id
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            WHERE m.status = 'Ativo' 
            AND a.ano_letivo = %s 
            AND al.escola_id = %s
        """, (ano, escola_id))
        stats['ativas_escola_ano'] = cur.fetchone()[0]
        
        # Matrículas ativas de anos anteriores (todas as escolas)
        cur.execute("""
            SELECT COUNT(*) FROM matriculas m
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            WHERE m.status = 'Ativo' 
            AND a.ano_letivo != %s
        """, (ano,))
        stats['ativas_anos_anteriores'] = cur.fetchone()[0]
        
        # Matrículas ativas de outras escolas no ano atual
        cur.execute("""
            SELECT COUNT(*) FROM matriculas m
            JOIN alunos al ON m.aluno_id = al.id
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            WHERE m.status = 'Ativo' 
            AND a.ano_letivo = %s 
            AND al.escola_id != %s
        """, (ano, escola_id))
        stats['ativas_outras_escolas'] = cur.fetchone()[0]
        
        # Detalhamento por escola (matrículas ativas)
        cur.execute("""
            SELECT al.escola_id, e.nome, a.ano_letivo, COUNT(*) as qtd
            FROM matriculas m
            JOIN alunos al ON m.aluno_id = al.id
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            LEFT JOIN escolas e ON al.escola_id = e.id
            WHERE m.status = 'Ativo'
            GROUP BY al.escola_id, e.nome, a.ano_letivo
            ORDER BY a.ano_letivo DESC, qtd DESC
        """)
        stats['detalhamento_escolas'] = cur.fetchall()
        
        # Total que será concluído
        stats['total_para_concluir'] = stats['ativas_anos_anteriores'] + stats['ativas_outras_escolas']
        
    return stats


def obter_matriculas_para_concluir_global(
    ano: int = 2025, 
    escola_id: int = 60, 
    limit: Optional[int] = None
) -> List[Tuple[int, int, str, int, int, str]]:
    """
    Retorna lista de matrículas que devem ser concluídas.
    
    Critérios (OR):
    1. Matrículas de anos anteriores ao ano de referência (qualquer escola)
    2. Matrículas de outras escolas (mesmo no ano de referência)
    
    E cujo status NÃO é protegido (Evadido, Transferido, Concluído)
    
    Retorna: lista de tuplas (matricula_id, aluno_id, nome_aluno, ano_letivo, escola_id, status)
    """
    
    status_protegidos_sql = ', '.join(['%s'] * len(STATUS_PROTEGIDOS))
    
    query = f"""
        SELECT 
            m.id AS matricula_id,
            m.aluno_id,
            al.nome AS nome_aluno,
            a.ano_letivo,
            al.escola_id,
            m.status
        FROM matriculas m
        JOIN alunos al ON m.aluno_id = al.id
        JOIN anosletivos a ON m.ano_letivo_id = a.id
        WHERE m.status NOT IN ({status_protegidos_sql})
        AND (
            a.ano_letivo != %s
            OR al.escola_id != %s
        )
        ORDER BY a.ano_letivo DESC, al.escola_id, al.nome
    """
    
    if limit:
        query += f" LIMIT {int(limit)}"
    
    params = list(STATUS_PROTEGIDOS) + [ano, escola_id]
    
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        return rows


def concluir_matriculas_global(
    ano: int = 2025, 
    escola_id: int = 60, 
    apply: bool = False,
    limit: Optional[int] = None
) -> Tuple[int, int]:
    """
    Atualiza o status das matrículas para 'Concluído':
    1. Matrículas de anos anteriores (todas as escolas)
    2. Matrículas de outras escolas (mesmo no ano atual)
    
    Mantém ativas apenas: escola_id + ano
    
    Returns:
        Tuple[int, int]: (matrículas de anos anteriores atualizadas, matrículas de outras escolas atualizadas)
    """
    
    status_protegidos_sql = ', '.join(['%s'] * len(STATUS_PROTEGIDOS))
    
    if not apply:
        # Mostrar prévia
        matriculas = obter_matriculas_para_concluir_global(ano, escola_id, limit)
        
        if not matriculas:
            print("Nenhuma matrícula encontrada para atualização.")
            return 0, 0
        
        print(f"\n{'='*90}")
        print(f"MATRÍCULAS QUE SERÃO ATUALIZADAS PARA '{CONCLUDED_STATUS}':")
        print(f"{'='*90}")
        print(f"{'ID':<8} {'Aluno':<10} {'Nome':<35} {'Ano':<6} {'Escola':<8} {'Status':<12}")
        print(f"{'-'*90}")
        
        for mat_id, aluno_id, nome, ano_letivo, esc_id, status in matriculas[:25]:
            nome_truncado = nome[:33] + '..' if len(nome) > 35 else nome
            print(f"{mat_id:<8} {aluno_id:<10} {nome_truncado:<35} {ano_letivo:<6} {esc_id:<8} {status:<12}")
        
        if len(matriculas) > 25:
            print(f"... e mais {len(matriculas) - 25} matrículas")
        
        print(f"\nTotal de matrículas a atualizar: {len(matriculas)}")
        print(f"\n[DRY-RUN] Nenhuma alteração foi aplicada. Use --apply para executar.")
        return 0, 0
    
    # Aplicar as alterações em duas etapas
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Etapa 1: Concluir matrículas de anos anteriores (todas as escolas)
        query1 = f"""
            UPDATE matriculas m
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            SET m.status = %s
            WHERE a.ano_letivo != %s
            AND m.status NOT IN ({status_protegidos_sql})
        """
        params1 = [CONCLUDED_STATUS, ano] + list(STATUS_PROTEGIDOS)
        cur.execute(query1, tuple(params1))
        updated_anos = cur.rowcount
        
        # Etapa 2: Concluir matrículas de outras escolas no ano atual
        query2 = f"""
            UPDATE matriculas m
            JOIN alunos al ON m.aluno_id = al.id
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            SET m.status = %s
            WHERE a.ano_letivo = %s
            AND al.escola_id != %s
            AND m.status NOT IN ({status_protegidos_sql})
        """
        params2 = [CONCLUDED_STATUS, ano, escola_id] + list(STATUS_PROTEGIDOS)
        cur.execute(query2, tuple(params2))
        updated_escolas = cur.rowcount
        
        try:
            conn.commit()
            print(f"\n[APLICADO] Matrículas atualizadas para '{CONCLUDED_STATUS}':")
            print(f"  - Anos anteriores: {updated_anos}")
            print(f"  - Outras escolas: {updated_escolas}")
            print(f"  - Total: {updated_anos + updated_escolas}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao aplicar alterações: {e}")
            raise
    
    return updated_anos, updated_escolas


def verificar_resultado(ano: int = 2025, escola_id: int = 60):
    """
    Verifica o resultado final após a execução.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Total de matrículas ativas
        cur.execute("SELECT COUNT(*) FROM matriculas WHERE status = 'Ativo'")
        total_ativas = cur.fetchone()[0]
        
        # Matrículas ativas da escola/ano
        cur.execute("""
            SELECT COUNT(*) FROM matriculas m
            JOIN alunos al ON m.aluno_id = al.id
            JOIN anosletivos a ON m.ano_letivo_id = a.id
            WHERE m.status = 'Ativo' 
            AND a.ano_letivo = %s 
            AND al.escola_id = %s
        """, (ano, escola_id))
        ativas_escola_ano = cur.fetchone()[0]
        
        print(f"\n{'='*50}")
        print("VERIFICAÇÃO DO RESULTADO")
        print(f"{'='*50}")
        print(f"Total de matrículas ativas: {total_ativas}")
        print(f"Matrículas ativas (escola {escola_id}, ano {ano}): {ativas_escola_ano}")
        
        if total_ativas == ativas_escola_ano:
            print(f"\n✅ SUCESSO! Apenas matrículas da escola {escola_id} do ano {ano} estão ativas.")
        else:
            print(f"\n⚠️  ATENÇÃO: Ainda há {total_ativas - ativas_escola_ano} matrículas ativas de outras fontes.")


def main():
    parser = argparse.ArgumentParser(
        description="Concluir matrículas mantendo apenas as ativas da escola/ano especificados"
    )
    parser.add_argument(
        "--apply", 
        action="store_true", 
        help="Aplica as alterações no banco (padrão: dry-run)"
    )
    parser.add_argument(
        "--escola", 
        type=int, 
        default=60, 
        help="ID da escola principal - matrículas ativas serão mantidas apenas desta escola (padrão: 60)"
    )
    parser.add_argument(
        "--ano", 
        type=int, 
        default=2025, 
        help="Ano letivo de referência - matrículas ativas serão mantidas apenas deste ano (padrão: 2025)"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        help="Limitar processamento a N matrículas (para testes)"
    )
    parser.add_argument(
        "--stats", 
        action="store_true", 
        help="Mostrar apenas estatísticas sem processar"
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("SCRIPT: CONCLUIR MATRÍCULAS - MANTER APENAS ESCOLA/ANO ESPECÍFICOS")
    print("="*80)
    print(f"Escola principal: {args.escola}")
    print(f"Ano de referência: {args.ano}")
    print(f"Apenas matrículas da ESCOLA {args.escola} do ANO {args.ano} permanecerão ativas")
    print(f"Status protegidos (não serão alterados): {', '.join(STATUS_PROTEGIDOS)}")
    print("="*80)
    
    # Mostrar estatísticas
    print("\n📊 ESTATÍSTICAS ATUAIS:")
    print("-"*50)
    stats = obter_estatisticas_gerais(args.ano, args.escola)
    
    print(f"Total de matrículas ativas no sistema: {stats['total_ativas']}")
    print(f"  - Escola {args.escola}, ano {args.ano}: {stats['ativas_escola_ano']} (serão MANTIDAS)")
    print(f"  - Anos anteriores: {stats['ativas_anos_anteriores']} (serão CONCLUÍDAS)")
    print(f"  - Outras escolas (ano {args.ano}): {stats['ativas_outras_escolas']} (serão CONCLUÍDAS)")
    print(f"\nTotal a ser concluído: {stats['total_para_concluir']}")
    print(f"Total que permanecerá ativo: {stats['ativas_escola_ano']}")
    
    if stats['detalhamento_escolas']:
        print("\n📋 Detalhamento por escola/ano (matrículas ativas):")
        for esc_id, esc_nome, ano_letivo, qtd in stats['detalhamento_escolas']:
            marcador = "✅" if esc_id == args.escola and ano_letivo == args.ano else "❌"
            esc_nome_curto = (esc_nome[:40] + '..') if esc_nome and len(esc_nome) > 42 else (esc_nome or 'N/A')
            print(f"  {marcador} Escola {esc_id} ({esc_nome_curto}), {ano_letivo}: {qtd}")
    
    if args.stats:
        print("\n[--stats] Apenas estatísticas foram exibidas.")
        return
    
    # Processar matrículas
    if args.apply:
        print("\n⚠️  MODO APPLY: As alterações serão gravadas no banco de dados!")
        print(f"    Serão concluídas {stats['total_para_concluir']} matrículas.")
        print(f"    Permanecerão ativas apenas {stats['ativas_escola_ano']} matrículas.")
        resposta = input("\nDeseja continuar? (s/N): ")
        if resposta.lower() != 's':
            print("Operação cancelada pelo usuário.")
            return
    else:
        print("\n[DRY-RUN] Simulando alterações (use --apply para executar de verdade)")
    
    updated_anos, updated_escolas = concluir_matriculas_global(
        ano=args.ano, 
        escola_id=args.escola, 
        apply=args.apply,
        limit=args.limit
    )
    
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80)
    
    if args.apply:
        print(f"✅ {updated_anos + updated_escolas} matrículas foram atualizadas para '{CONCLUDED_STATUS}'")
        print(f"   - Anos anteriores: {updated_anos}")
        print(f"   - Outras escolas: {updated_escolas}")
        
        # Verificar resultado
        verificar_resultado(args.ano, args.escola)
    else:
        print(f"📝 {stats['total_para_concluir']} matrículas seriam atualizadas")
        print("   Execute com --apply para aplicar as alterações.")


if __name__ == '__main__':
    main()
