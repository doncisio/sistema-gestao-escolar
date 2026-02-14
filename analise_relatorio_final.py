import pandas as pd

arquivo = "RELATORIO_MATRICULAS_GEDUC_20260214_075554.xlsx"

print("="*80)
print("ANÁLISE DO RELATÓRIO - EXEMPLOS DE DIVERGÊNCIAS")
print("="*80)

# Ler aba de divergentes
df_div = pd.read_excel(arquivo, sheet_name='Séries Divergentes')

print(f"\nTotal de divergências: {len(df_div)}\n")
print("Primeiros 15 casos:\n")
print("-"*80)

for i, row in df_div.head(15).iterrows():
    print(f"{i+1}. {row['Nome']}")
    print(f"   Sistema Local: {row['Série Atual (Sistema)']}")
    print(f"   GEDUC:         {row['Série GEDUC (Correto)']}")
    print(f"   Idade (nasc):  {row['Idade (nasc)']}")
    print()

print("="*80)
print("ANÁLISE DOS 76 ALUNOS SEM MATRÍCULA")
print("="*80)

df_sem = pd.read_excel(arquivo, sheet_name='Sem Matrícula 2026')

print(f"\nTotal sem matrícula: {len(df_sem)}\n")

# Contar por série
print("Distribuição por série:\n")
serie_counts = df_sem['Série GEDUC (Matricular em)'].value_counts()
for serie, qtd in serie_counts.items():
    print(f"  {serie}: {qtd} alunos")

print("\n" + "="*80)
print("PRIMEIROS 20 ALUNOS SEM MATRÍCULA")
print("="*80 + "\n")

for i, row in df_sem.head(20).iterrows():
    print(f"{i+1}. {row['Nome']} (ID: {row['ID']})")
    print(f"   Matricular em: {row['Série GEDUC (Matricular em)']}")
    print(f"   Data Nasc: {row['Data Nascimento']}")
    print()
