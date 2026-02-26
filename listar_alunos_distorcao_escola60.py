"""
Script para identificar alunos em distorção idade-série na escola_id=60.

Distorção idade-série: quando o aluno tem 2 ou mais anos a mais que a idade ideal para sua série.

Idades ideais por série (Ensino Fundamental):
- 1º ano: 6 anos
- 2º ano: 7 anos
- 3º ano: 8 anos
- 4º ano: 9 anos
- 5º ano: 10 anos
- 6º ano: 11 anos
- 7º ano: 12 anos
- 8º ano: 13 anos
- 9º ano: 14 anos
"""

from datetime import datetime, date
from db.connection import conectar_bd
from typing import List, Dict
import json

# Configurações
ESCOLA_ID = 60
ANO_LETIVO = 2026

# Mapeamento de série para idade ideal
# Assumindo que serie_id segue o padrão: 3=1ºano, 4=2ºano, etc.
IDADE_IDEAL_POR_SERIE = {
    3: 6,   # 1º ano
    4: 7,   # 2º ano
    5: 8,   # 3º ano
    6: 9,   # 4º ano
    7: 10,  # 5º ano
    8: 11,  # 6º ano
    9: 12,  # 7º ano
    10: 13, # 8º ano
    11: 14  # 9º ano
}

# Anos de distorção considerada significativa
ANOS_DISTORCAO_MINIMA = 2


def calcular_idade_em_ano(data_nascimento: date, ano_referencia: int) -> int:
    """
    Calcula a idade que o aluno terá/teve em determinado ano (31 de dezembro).
    
    Args:
        data_nascimento: Data de nascimento do aluno
        ano_referencia: Ano de referência para cálculo
        
    Returns:
        Idade em anos completos
    """
    # Considera a idade que terá no final do ano letivo (31/12)
    data_referencia = date(ano_referencia, 12, 31)
    idade = data_referencia.year - data_nascimento.year
    return idade


def obter_alunos_ativos_escola(escola_id: int, ano_letivo: int) -> List[Dict]:
    """
    Busca todos os alunos ativos da escola no ano letivo especificado.
    
    Args:
        escola_id: ID da escola
        ano_letivo: Ano letivo
        
    Returns:
        Lista de dicionários com dados dos alunos
    """
    conn = conectar_bd()
    if not conn:
        print("Erro ao conectar ao banco de dados!")
        return []
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT 
                a.id,
                a.nome,
                a.data_nascimento,
                a.cpf,
                a.sexo,
                s.id AS serie_id,
                s.nome AS serie_nome,
                t.id AS turma_id,
                t.nome AS turma_nome,
                t.turno,
                m.id AS matricula_id,
                m.status AS status_matricula,
                m.data_matricula
            FROM 
                Alunos a
            JOIN 
                Matriculas m ON a.id = m.aluno_id
            JOIN 
                Turmas t ON m.turma_id = t.id
            JOIN 
                series s ON t.serie_id = s.id
            JOIN
                AnosLetivos al ON m.ano_letivo_id = al.id
            WHERE 
                a.escola_id = %s
                AND al.ano_letivo = %s
                AND m.status = 'Ativo'
            ORDER BY 
                s.nome, t.nome, a.nome
        """
        
        cursor.execute(query, (escola_id, ano_letivo))
        alunos = cursor.fetchall()
        
        return alunos
        
    except Exception as e:
        print(f"Erro ao buscar alunos: {e}")
        return []
    finally:
        cursor.close()
        conn.close()


def identificar_alunos_em_distorcao(alunos: List[Dict], ano_referencia: int) -> List[Dict]:
    """
    Identifica quais alunos estão em distorção idade-série.
    
    Args:
        alunos: Lista de alunos ativos
        ano_referencia: Ano de referência para cálculo da idade
        
    Returns:
        Lista de alunos em distorção com dados calculados
    """
    alunos_distorcao = []
    
    for aluno in alunos:
        serie_id = aluno['serie_id']
        data_nascimento = aluno['data_nascimento']
        
        # Verifica se temos a idade ideal mapeada para esta série
        if serie_id not in IDADE_IDEAL_POR_SERIE:
            continue
        
        # Verifica se temos data de nascimento
        if not data_nascimento:
            continue
        
        # Calcula idade
        idade_atual = calcular_idade_em_ano(data_nascimento, ano_referencia)
        idade_ideal = IDADE_IDEAL_POR_SERIE[serie_id]
        anos_distorcao = idade_atual - idade_ideal
        
        # Verifica se está em distorção
        if anos_distorcao >= ANOS_DISTORCAO_MINIMA:
            aluno_distorcao = aluno.copy()
            aluno_distorcao['idade_em_2026'] = idade_atual
            aluno_distorcao['idade_ideal'] = idade_ideal
            aluno_distorcao['anos_distorcao'] = anos_distorcao
            alunos_distorcao.append(aluno_distorcao)
    
    return alunos_distorcao


def gerar_relatorio_texto(alunos_distorcao: List[Dict]) -> str:
    """
    Gera relatório em formato texto dos alunos em distorção.
    
    Args:
        alunos_distorcao: Lista de alunos em distorção
        
    Returns:
        String com o relatório formatado
    """
    relatorio = []
    relatorio.append("=" * 100)
    relatorio.append(f"RELATÓRIO DE ALUNOS EM DISTORÇÃO IDADE-SÉRIE")
    relatorio.append(f"Escola ID: {ESCOLA_ID} | Ano Letivo: {ANO_LETIVO}")
    relatorio.append(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    relatorio.append("=" * 100)
    relatorio.append("")
    relatorio.append(f"Total de alunos em distorção: {len(alunos_distorcao)}")
    relatorio.append("")
    
    # Agrupa por série
    alunos_por_serie = {}
    for aluno in alunos_distorcao:
        serie = aluno['serie_nome']
        if serie not in alunos_por_serie:
            alunos_por_serie[serie] = []
        alunos_por_serie[serie].append(aluno)
    
    # Gera relatório por série
    for serie in sorted(alunos_por_serie.keys()):
        alunos_serie = alunos_por_serie[serie]
        relatorio.append("-" * 100)
        relatorio.append(f"{serie} - Total: {len(alunos_serie)} alunos em distorção")
        relatorio.append("-" * 100)
        relatorio.append("")
        
        for idx, aluno in enumerate(alunos_serie, 1):
            relatorio.append(f"{idx}. {aluno['nome']}")
            relatorio.append(f"   ID: {aluno['id']} | CPF: {aluno['cpf'] or 'Não cadastrado'}")
            relatorio.append(f"   Data Nascimento: {aluno['data_nascimento'].strftime('%d/%m/%Y')}")
            relatorio.append(f"   Idade em 2026: {aluno['idade_em_2026']} anos (Ideal: {aluno['idade_ideal']} anos)")
            relatorio.append(f"   Distorção: {aluno['anos_distorcao']} anos")
            relatorio.append(f"   Turma: {aluno['turma_nome']} - Turno: {aluno['turno']}")
            relatorio.append(f"   Sexo: {aluno['sexo']}")
            relatorio.append("")
    
    relatorio.append("=" * 100)
    relatorio.append("FIM DO RELATÓRIO")
    relatorio.append("=" * 100)
    
    return "\n".join(relatorio)


def gerar_relatorio_json(alunos_distorcao: List[Dict]) -> str:
    """
    Gera relatório em formato JSON dos alunos em distorção.
    
    Args:
        alunos_distorcao: Lista de alunos em distorção
        
    Returns:
        String JSON formatada
    """
    # Converte datas para string
    alunos_json = []
    for aluno in alunos_distorcao:
        aluno_dict = aluno.copy()
        if aluno_dict.get('data_nascimento'):
            aluno_dict['data_nascimento'] = aluno_dict['data_nascimento'].strftime('%Y-%m-%d')
        if aluno_dict.get('data_matricula'):
            aluno_dict['data_matricula'] = aluno_dict['data_matricula'].strftime('%Y-%m-%d')
        alunos_json.append(aluno_dict)
    
    resultado = {
        'escola_id': ESCOLA_ID,
        'ano_letivo': ANO_LETIVO,
        'data_geracao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_alunos_distorcao': len(alunos_distorcao),
        'criterio_distorcao': f'{ANOS_DISTORCAO_MINIMA}+ anos acima da idade ideal',
        'alunos': alunos_json
    }
    
    return json.dumps(resultado, ensure_ascii=False, indent=2)


def main():
    """Função principal."""
    print("Buscando alunos ativos da escola...")
    alunos = obter_alunos_ativos_escola(ESCOLA_ID, ANO_LETIVO)
    
    if not alunos:
        print("Nenhum aluno encontrado ou erro ao buscar dados.")
        return
    
    print(f"Total de alunos ativos encontrados: {len(alunos)}")
    print("\nIdentificando alunos em distorção idade-série...")
    
    alunos_distorcao = identificar_alunos_em_distorcao(alunos, ANO_LETIVO)
    
    print(f"\nTotal de alunos em distorção: {len(alunos_distorcao)}")
    
    if not alunos_distorcao:
        print("\n✓ Nenhum aluno em distorção idade-série encontrado!")
        return
    
    # Gera relatórios
    print("\nGerando relatórios...")
    
    # Relatório em texto
    relatorio_txt = gerar_relatorio_texto(alunos_distorcao)
    arquivo_txt = f"DISTORCAO_IDADE_SERIE_ESCOLA_{ESCOLA_ID}_{ANO_LETIVO}.txt"
    with open(arquivo_txt, 'w', encoding='utf-8') as f:
        f.write(relatorio_txt)
    print(f"✓ Relatório em texto salvo: {arquivo_txt}")
    
    # Relatório em JSON
    relatorio_json = gerar_relatorio_json(alunos_distorcao)
    arquivo_json = f"DISTORCAO_IDADE_SERIE_ESCOLA_{ESCOLA_ID}_{ANO_LETIVO}.json"
    with open(arquivo_json, 'w', encoding='utf-8') as f:
        f.write(relatorio_json)
    print(f"✓ Relatório em JSON salvo: {arquivo_json}")
    
    # Exibe resumo no console
    print("\n" + "=" * 80)
    print("RESUMO POR SÉRIE")
    print("=" * 80)
    
    alunos_por_serie = {}
    for aluno in alunos_distorcao:
        serie = aluno['serie_nome']
        if serie not in alunos_por_serie:
            alunos_por_serie[serie] = 0
        alunos_por_serie[serie] += 1
    
    for serie in sorted(alunos_por_serie.keys()):
        print(f"{serie}: {alunos_por_serie[serie]} alunos em distorção")
    
    print("\n✓ Relatórios gerados com sucesso!")


if __name__ == "__main__":
    main()
