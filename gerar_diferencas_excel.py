"""
Script para gerar arquivo Excel com diferenças entre Atas e Excel
Duas planilhas: 
1. Alunos no Excel mas não nas Atas
2. Alunos nas Atas mas não no Excel
"""
import pandas as pd
from pathlib import Path
import re

def extrair_nomes_da_ata_txt(arquivo_txt):
    """Extrai nomes dos alunos do arquivo txt da ata"""
    nomes = []
    
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    inicio_tabela = False
    
    for linha in linhas:
        if 'Nº NOME SEXO' in linha or 'NOME SEXO' in linha:
            inicio_tabela = True
            continue
        
        if inicio_tabela and ('E para constar' in linha or 'SECRETÁRIO' in linha or 'DIRETOR' in linha):
            break
        
        if inicio_tabela:
            linha_limpa = linha.strip()
            if not linha_limpa:
                continue
            
            match = re.match(r'^(\d+)\s+([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+?)\s+([MF])\s+', linha_limpa)
            
            if match:
                numero = match.group(1)
                nome = match.group(2).strip()
                sexo = match.group(3)
                
                # Verificar se está cancelado
                cancelado = 'CANCELADO' in linha_limpa.upper() or 'Cancelado' in linha_limpa
                
                # Extrair situação (última palavra antes de possível "Cancelado")
                situacao = 'Desconhecido'
                if 'Aprovado' in linha_limpa:
                    situacao = 'Aprovado'
                elif 'Reprovado' in linha_limpa:
                    situacao = 'Reprovado'
                elif 'Transferido' in linha_limpa:
                    situacao = 'Transferido'
                elif cancelado:
                    situacao = 'Cancelado'
                
                if nome and len(nome) > 5 and nome != 'NOME':
                    nomes.append({
                        'numero': int(numero),
                        'nome': nome.upper(),
                        'sexo': sexo,
                        'situacao': situacao,
                        'cancelado': cancelado
                    })
    
    return nomes

def extrair_turma_do_arquivo(arquivo_txt):
    """Extrai o nome da turma do arquivo txt"""
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        texto = f.read()
    
    # Procurar padrão "CURSO: X TURMA: Y"
    match = re.search(r'TURMA:\s*([^\n]+)', texto)
    if match:
        return match.group(1).strip()
    
    # Se não encontrar, usar o nome do arquivo
    return arquivo_txt.stem.upper()

def normalizar_nome(nome):
    """Normaliza nome para comparação"""
    nome = ' '.join(nome.upper().split())
    return nome

def gerar_excel_diferencas():
    """Gera arquivo Excel com as diferenças"""
    diretorio_atas = Path(r"c:\gestao\atas geduc")
    arquivo_excel = diretorio_atas / "RelacaoSituacaoInformadaAluno_22_2_2026.xlsx"
    
    print("=" * 80)
    print("GERANDO ARQUIVO EXCEL COM DIFERENÇAS")
    print("=" * 80)
    
    # Ler Excel
    print("\n📊 Lendo arquivo Excel...")
    df_excel = pd.read_excel(arquivo_excel)
    
    # Identificar colunas
    coluna_nome = None
    coluna_turma = None
    coluna_situacao = None
    
    for col in df_excel.columns:
        if 'nome' in col.lower() and 'aluno' in col.lower():
            coluna_nome = col
        if 'turma' in col.lower() and 'nome' in col.lower():
            coluna_turma = col
        if 'situação' in col.lower() or 'situacao' in col.lower():
            coluna_situacao = col
    
    print(f"   Coluna de nomes: {coluna_nome}")
    print(f"   Coluna de turma: {coluna_turma}")
    print(f"   Coluna de situação: {coluna_situacao}")
    print(f"   Total de registros: {len(df_excel)}")
    
    # Criar dicionário de alunos do Excel
    alunos_excel = {}
    for _, row in df_excel.iterrows():
        nome = str(row[coluna_nome]).strip().upper()
        nome_norm = normalizar_nome(nome)
        alunos_excel[nome_norm] = {
            'nome_original': nome,
            'turma': row[coluna_turma] if coluna_turma else '',
            'situacao': row[coluna_situacao] if coluna_situacao else '',
            'dados': row
        }
    
    # Processar atas
    print("\n📄 Processando atas...")
    arquivos_txt = sorted(diretorio_atas.glob("*.txt"))
    
    alunos_atas = {}
    
    for txt_file in arquivos_txt:
        turma_nome = extrair_turma_do_arquivo(txt_file)
        alunos = extrair_nomes_da_ata_txt(txt_file)
        
        print(f"   {txt_file.name}: {len(alunos)} alunos")
        
        for aluno in alunos:
            nome_norm = normalizar_nome(aluno['nome'])
            alunos_atas[nome_norm] = {
                'nome_original': aluno['nome'],
                'turma': turma_nome,
                'numero': aluno['numero'],
                'sexo': aluno['sexo'],
                'situacao': aluno['situacao'],
                'cancelado': aluno['cancelado']
            }
    
    print(f"\n   Total de alunos únicos nas atas: {len(alunos_atas)}")
    
    # Encontrar diferenças
    print("\n🔍 Identificando diferenças...")
    
    # 1. Alunos no Excel mas não nas Atas
    alunos_excel_nao_atas = []
    for nome_norm, dados in alunos_excel.items():
        if nome_norm not in alunos_atas:
            alunos_excel_nao_atas.append({
                'Nome': dados['nome_original'],
                'Turma': dados['turma'],
                'Situação no Excel': dados['situacao'],
                'Observação': 'Não encontrado nas atas'
            })
    
    # 2. Alunos nas Atas mas não no Excel
    alunos_atas_nao_excel = []
    for nome_norm, dados in alunos_atas.items():
        if nome_norm not in alunos_excel:
            obs = 'Cancelado' if dados['cancelado'] else 'Nome não consta no Excel'
            alunos_atas_nao_excel.append({
                'Nome': dados['nome_original'],
                'Turma': dados['turma'],
                'Número': dados['numero'],
                'Sexo': dados['sexo'],
                'Situação na Ata': dados['situacao'],
                'Observação': obs
            })
    
    print(f"   ⚠️ No Excel mas não nas atas: {len(alunos_excel_nao_atas)}")
    print(f"   ⚠️ Nas atas mas não no Excel: {len(alunos_atas_nao_excel)}")
    
    # Criar DataFrames
    df1 = pd.DataFrame(alunos_excel_nao_atas)
    df2 = pd.DataFrame(alunos_atas_nao_excel)
    
    # Ordenar
    if not df1.empty:
        df1 = df1.sort_values(['Turma', 'Nome'])
    if not df2.empty:
        df2 = df2.sort_values(['Turma', 'Nome'])
    
    # Salvar no Excel
    arquivo_saida = diretorio_atas / "DIFERENCAS_ATAS_EXCEL.xlsx"
    
    print(f"\n💾 Salvando arquivo Excel...")
    
    with pd.ExcelWriter(arquivo_saida, engine='openpyxl') as writer:
        # Planilha 1: No Excel mas não nas Atas
        df1.to_excel(writer, sheet_name='No Excel - Não nas Atas', index=False)
        
        # Planilha 2: Nas Atas mas não no Excel
        df2.to_excel(writer, sheet_name='Nas Atas - Não no Excel', index=False)
        
        # Ajustar largura das colunas
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"   ✅ Arquivo salvo: {arquivo_saida.name}")
    
    # Mostrar resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DAS DIFERENÇAS")
    print("=" * 80)
    
    print(f"\n📋 PLANILHA 1: Alunos NO EXCEL mas NÃO NAS ATAS ({len(df1)})")
    if not df1.empty:
        print("\nPrimeiros 10 registros:")
        for idx, row in df1.head(10).iterrows():
            print(f"   - [{row['Turma']}] {row['Nome']}")
        if len(df1) > 10:
            print(f"   ... e mais {len(df1) - 10}")
    
    print(f"\n📋 PLANILHA 2: Alunos NAS ATAS mas NÃO NO EXCEL ({len(df2)})")
    if not df2.empty:
        print("\nTodos os registros:")
        for idx, row in df2.iterrows():
            status = " [CANCELADO]" if row['Observação'] == 'Cancelado' else ""
            print(f"   - [{row['Turma']}] {row['Nome']}{status}")
    
    print("\n" + "=" * 80)
    print(f"✅ ARQUIVO GERADO COM SUCESSO!")
    print(f"📂 Localização: {arquivo_saida}")
    print("=" * 80)
    
    return arquivo_saida

if __name__ == "__main__":
    try:
        gerar_excel_diferencas()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
