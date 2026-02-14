import pandas as pd

arquivo = "RELATORIO_MATRICULAS_GEDUC_20260214_075554.xlsx"

print("="*80)
print("PROCURANDO YAN DAVI NO RELATÓRIO")
print("="*80)

# Ler aba de divergentes
df_div = pd.read_excel(arquivo, sheet_name='Séries Divergentes')

# Procurar Yan Davi
yan_div = df_div[df_div['Nome'].str.contains('YAN DAVI', case=False, na=False)]

if len(yan_div) > 0:
    print("\n❌ ENCONTRADO NA ABA DE DIVERGÊNCIAS:")
    print("-"*80)
    for idx, row in yan_div.iterrows():
        print(f"\nLinha {idx + 2} (Excel):")
        print(f"  Nome: {row['Nome']}")
        print(f"  ID: {row['ID']}")
        print(f"  Série Atual (Sistema): {row['Série Atual (Sistema)']}")
        print(f"  Série GEDUC (Correto): {row['Série GEDUC (Correto)']}")
        print(f"  Turma GEDUC ID: {row['Turma GEDUC ID']}")
        print(f"  Data Nasc: {row['Idade (nasc)']}")
else:
    print("\n✅ NÃO encontrado na aba de divergências")

# Verificar na aba de sem matrícula
df_sem = pd.read_excel(arquivo, sheet_name='Sem Matrícula 2026')
yan_sem = df_sem[df_sem['Nome'].str.contains('YAN DAVI', case=False, na=False)]

if len(yan_sem) > 0:
    print("\n❌ ENCONTRADO NA ABA DE SEM MATRÍCULA:")
    print("-"*80)
    for idx, row in yan_sem.iterrows():
        print(f"\nLinha {idx + 2} (Excel):")
        print(f"  Nome: {row['Nome']}")
        print(f"  ID: {row['ID']}")
        print(f"  Série GEDUC (Matricular em): {row['Série GEDUC (Matricular em)']}")
else:
    print("✅ NÃO encontrado na aba de sem matrícula")

print("\n" + "="*80)
