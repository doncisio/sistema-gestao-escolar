#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar conteúdo correto de EF08MA01 no Excel
"""

import pandas as pd

# Carregar Excel
excel_path = r'C:\gestao\MapasDeFocoBncc_Unificados.xlsx'

# Procurar EF08MA01 em todas as planilhas
sheets = pd.ExcelFile(excel_path).sheet_names

found = False
for sheet in sheets:
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet)
        
        # Procurar por coluna que contém códigos
        codigo_col = None
        for col in df.columns:
            if 'código' in str(col).lower() or 'codigo' in str(col).lower():
                codigo_col = col
                break
        
        if codigo_col:
            mask = df[codigo_col] == 'EF08MA01'
            if mask.any():
                print(f"\n=== Encontrado na planilha: {sheet} ===")
                row = df[mask].iloc[0]
                print("\nColunas disponíveis:")
                for col in df.columns:
                    val = row[col]
                    if pd.notna(val):
                        print(f"\n{col}:")
                        print(f"  {val}")
                found = True
                break
    except Exception as e:
        continue

if not found:
    print("EF08MA01 não encontrado no Excel")
