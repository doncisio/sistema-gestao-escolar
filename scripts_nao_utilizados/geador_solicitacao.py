import pandas as pd

# Função para ler o arquivo .txt e converter em DataFrame
def ler_arquivo_txt(arquivo_txt):
    # Ler o arquivo .txt e criar um DataFrame
    df = pd.read_csv(arquivo_txt, sep=",", header=0, encoding='utf-8', quotechar='"', skipinitialspace=True)
    
    # Retornar o DataFrame
    return df

# Função para salvar o DataFrame em um arquivo Excel
def salvar_para_excel(df, arquivo_excel):
    df.to_excel(arquivo_excel, index=False)

# Nome do arquivo .txt e do arquivo Excel de saída (mesma pasta)
arquivo_txt = 'Alunos.txt'
arquivo_excel = 'Alunos.xlsx'

# Ler o arquivo .txt e converter em DataFrame
df = ler_arquivo_txt(arquivo_txt)

# Salvar o DataFrame em um arquivo Excel
salvar_para_excel(df, arquivo_excel)

print(f"Arquivo Excel '{arquivo_excel}' gerado com sucesso!")
