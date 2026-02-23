"""
Script para análise das atas do GEDUC 2025 e situação dos alunos
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

def analisar_situacao_alunos(caminho_excel):
    """Analisa o arquivo Excel com a situação dos alunos"""
    try:
        # Ler o arquivo Excel
        df = pd.read_excel(caminho_excel)
        
        print("=" * 80)
        print("ANÁLISE DA SITUAÇÃO DOS ALUNOS - ANO LETIVO 2025")
        print("=" * 80)
        print(f"\nArquivo: {caminho_excel}")
        print(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("\n" + "=" * 80)
        
        # Informações básicas
        print(f"\n📊 DADOS GERAIS:")
        print(f"   Total de registros: {len(df)}")
        print(f"   Colunas disponíveis: {list(df.columns)}")
        
        # Mostrar primeiras linhas para entender a estrutura
        print("\n📋 ESTRUTURA DOS DADOS:")
        print(df.head(10).to_string())
        
        # Análise por situação (se houver coluna de situação)
        colunas_situacao = [col for col in df.columns if 'situação' in col.lower() or 'situacao' in col.lower() or 'status' in col.lower()]
        
        if colunas_situacao:
            print(f"\n📈 ANÁLISE POR SITUAÇÃO:")
            for col in colunas_situacao:
                print(f"\n   Coluna: {col}")
                contagem = df[col].value_counts()
                print(contagem.to_string())
                print(f"   Total com situação: {df[col].count()}")
                print(f"   Valores nulos: {df[col].isna().sum()}")
        else:
            print(f"\n⚠️  Nenhuma coluna de situação encontrada automaticamente.")
            print(f"   Tentando buscar em todas as colunas...")
            # Mostrar contagem de todas as colunas de texto
            for col in df.columns:
                if df[col].dtype == 'object' and col not in ['Nome do(a) Aluno(a)', 'Identificação única', 'Etapa']:
                    valores_unicos = df[col].nunique()
                    if 1 < valores_unicos < 20:  # Provavelmente uma categoria
                        print(f"\n   Possível coluna categórica: {col}")
                        print(df[col].value_counts().head(10).to_string())
        
        # Análise por turma (se houver coluna de turma)
        colunas_turma = [col for col in df.columns if 'turma' in col.lower() or 'classe' in col.lower() or 'ano' in col.lower()]
        
        if colunas_turma:
            print(f"\n📚 ANÁLISE POR TURMA:")
            for col in colunas_turma:
                print(f"\n   Coluna: {col}")
                contagem = df[col].value_counts().sort_index()
                print(contagem.to_string())
                print(f"   Total de turmas: {df[col].nunique()}")
        
        # Análise cruzada (se houvermos ambas as colunas)
        if colunas_situacao and colunas_turma:
            print(f"\n📊 ANÁLISE CRUZADA (TURMA x SITUAÇÃO):")
            for col_turma in colunas_turma[:1]:  # Primeira coluna de turma
                for col_situacao in colunas_situacao[:1]:  # Primeira coluna de situação
                    tabela_cruzada = pd.crosstab(df[col_turma], df[col_situacao], margins=True)
                    print(f"\n   {col_turma} x {col_situacao}:")
                    print(tabela_cruzada.to_string())
        
        # Salvar relatório detalhado
        return gerar_relatorio_comparativo(df, colunas_turma, colunas_situacao)
        
    except Exception as e:
        print(f"❌ Erro ao analisar arquivo: {e}")
        import traceback
        traceback.print_exc()
        return None

def gerar_relatorio_comparativo(df, colunas_turma, colunas_situacao):
    """Gera relatório comparativo detalhado"""
    
    relatorio = {
        'data_geracao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'total_alunos': len(df),
        'turmas': {},
        'situacoes': {},
        'analise_detalhada': []
    }
    
    # Identificar colunas principais
    col_turma = colunas_turma[0] if colunas_turma else None
    col_nome_turma = None
    for col in colunas_turma:
        if 'nome' in col.lower():
            col_nome_turma = col
            break
    
    col_situacao = colunas_situacao[0] if colunas_situacao else None
    
    if col_turma:
        # Criar mapeamento de código para nome de turma
        mapa_turmas = {}
        if col_nome_turma:
            for _, row in df[[col_turma, col_nome_turma]].drop_duplicates().iterrows():
                mapa_turmas[row[col_turma]] = row[col_nome_turma]
        
        # Análise por turma
        for turma in sorted(df[col_turma].dropna().unique()):
            df_turma = df[df[col_turma] == turma]
            
            info_turma = {
                'codigo': str(turma),
                'nome': mapa_turmas.get(turma, str(turma)),
                'total_alunos': len(df_turma),
                'situacoes': {}
            }
            
            if col_situacao:
                for situacao in df_turma[col_situacao].value_counts().items():
                    info_turma['situacoes'][str(situacao[0])] = int(situacao[1])
            
            relatorio['turmas'][str(turma)] = info_turma
            
            # Adicionar ao relatório detalhado
            relatorio['analise_detalhada'].append({
                'turma': str(turma),
                'nome_turma': mapa_turmas.get(turma, str(turma)),
                'total': len(df_turma),
                'situacoes': info_turma['situacoes']
            })
    
    if col_situacao:
        # Análise geral por situação
        for situacao in df[col_situacao].value_counts().items():
            relatorio['situacoes'][str(situacao[0])] = int(situacao[1])
    
    return relatorio

def criar_relatorio_markdown(relatorio, caminho_saida):
    """Cria relatório em Markdown"""
    
    md_content = f"""# Relatório Comparativo - Atas GEDUC 2025

**Data de Geração:** {relatorio['data_geracao']}

---

## 📊 Resumo Geral

- **Total de Alunos:** {relatorio['total_alunos']}
- **Total de Turmas:** {len(relatorio['turmas'])}

---

## 📈 Situação Geral dos Alunos

"""
    
    if relatorio['situacoes']:
        md_content += "| Situação | Quantidade | Percentual |\n"
        md_content += "|----------|------------|------------|\n"
        
        total = relatorio['total_alunos']
        for situacao, quantidade in sorted(relatorio['situacoes'].items()):
            percentual = (quantidade / total * 100) if total > 0 else 0
            md_content += f"| {situacao} | {quantidade} | {percentual:.2f}% |\n"
    
    md_content += "\n---\n\n## 📚 Análise Detalhada por Turma\n\n"
    
    for item in relatorio['analise_detalhada']:
        nome_exibicao = item.get('nome_turma', item['turma'])
        md_content += f"### {nome_exibicao}\n\n"
        md_content += f"**Código da Turma:** {item['turma']}  \n"
        md_content += f"**Total de Alunos:** {item['total']}\n\n"
        
        if item['situacoes']:
            md_content += "| Situação | Quantidade | Percentual |\n"
            md_content += "|----------|------------|------------|\n"
            
            for situacao, quantidade in sorted(item['situacoes'].items()):
                percentual = (quantidade / item['total'] * 100) if item['total'] > 0 else 0
                md_content += f"| {situacao} | {quantidade} | {percentual:.2f}% |\n"
            
            md_content += "\n"
    
    md_content += """---

## 📋 Observações

Este relatório foi gerado automaticamente a partir dos dados do arquivo Excel.
Para comparação detalhada com as atas em PDF, uma análise manual adicional pode ser necessária.

### Atas Disponíveis
- 1ano.pdf
- 2ano.pdf
- 3ano.pdf
- 4ano.pdf
- 5ano.pdf
- 6anoa.pdf
- 6anob.pdf
- 7ano.pdf
- 8ano.pdf
- 9ano.pdf

---

**Gerado em:** """ + relatorio['data_geracao'] + "\n"
    
    # Salvar arquivo
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"\n✅ Relatório Markdown salvo em: {caminho_saida}")
    
    # Também salvar JSON para referência
    caminho_json = str(caminho_saida).replace('.md', '.json')
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Dados JSON salvos em: {caminho_json}")

if __name__ == "__main__":
    # Caminhos
    diretorio_atas = Path(r"c:\gestao\atas geduc")
    arquivo_excel = diretorio_atas / "RelacaoSituacaoInformadaAluno_22_2_2026.xlsx"
    arquivo_relatorio = diretorio_atas / "RELATORIO_COMPARATIVO_ATAS_2025.md"
    
    # Executar análise
    relatorio = analisar_situacao_alunos(arquivo_excel)
    
    if relatorio:
        criar_relatorio_markdown(relatorio, arquivo_relatorio)
        print("\n" + "=" * 80)
        print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
    else:
        print("\n❌ Análise não pôde ser concluída.")
