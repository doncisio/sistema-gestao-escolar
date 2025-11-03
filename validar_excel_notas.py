"""
Script de validação e visualização de arquivos Excel de notas gerados
"""

import openpyxl
import os
from pathlib import Path

def validar_excel_notas(excel_path):
    """
    Valida a estrutura de um arquivo Excel de notas
    """
    try:
        print(f"\n{'='*70}")
        print(f"VALIDANDO: {os.path.basename(excel_path)}")
        print(f"{'='*70}\n")
        
        # Carregar workbook
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        
        # Informações gerais
        print(f"📋 Nome da planilha: {ws.title}")
        print(f"📏 Dimensões: {ws.max_row} linhas x {ws.max_column} colunas")
        
        # Ler informações do topo
        print(f"\n📌 Informações Extraídas:")
        if ws['A1'].value:
            print(f"   {ws['A1'].value}")
        if ws['A2'].value:
            print(f"   {ws['A2'].value}")
        if ws['A3'].value:
            print(f"   {ws['A3'].value}")
        
        # Encontrar linha de cabeçalho
        linha_header = 4
        for row in range(1, 10):
            if ws.cell(row, 1).value == 'Nº':
                linha_header = row
                break
        
        print(f"\n📊 Cabeçalho (Linha {linha_header}):")
        for col in range(1, 8):
            valor = ws.cell(linha_header, col).value
            if valor:
                print(f"   Col {col}: {valor}")
        
        # Contar alunos
        num_alunos = ws.max_row - linha_header
        print(f"\n👥 Total de alunos: {num_alunos}")
        
        # Mostrar primeiros 5 alunos
        print(f"\n📝 Amostra de Dados (primeiros 5 alunos):")
        print(f"{'-'*70}")
        
        for row in range(linha_header + 1, min(linha_header + 6, ws.max_row + 1)):
            ordem = ws.cell(row, 1).value or ''
            nome = ws.cell(row, 2).value or ''
            nota = ws.cell(row, 3).value or '-'
            
            # Formatar valor
            if isinstance(nota, (int, float)):
                nota = f"{nota:.2f}"
            
            print(f"\n{ordem}. {nome}")
            print(f"   Nota Final: {nota}")
        
        # Estatísticas
        print(f"\n📈 Estatísticas:")
        
        # Calcular estatísticas das notas finais
        notas = []
        for row in range(linha_header + 1, ws.max_row + 1):
            nota = ws.cell(row, 3).value
            if isinstance(nota, (int, float)):
                notas.append(nota)
        
        if notas:
            media_turma = sum(notas) / len(notas)
            maior_nota = max(notas)
            menor_nota = min(notas)
            
            print(f"   Média da turma: {media_turma:.2f}")
            print(f"   Maior nota: {maior_nota:.2f}")
            print(f"   Menor nota: {menor_nota:.2f}")
            
            # Aprovados (nota >= 70.0, já que são médias * 10)
            aprovados = sum(1 for n in notas if n >= 70.0)
            print(f"   Aprovados (≥70.0): {aprovados}/{len(notas)} ({aprovados/len(notas)*100:.1f}%)")
        
        print(f"\n✅ Arquivo válido e estrutura correta!")
        print(f"{'='*70}\n")
        
        wb.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        return False


def listar_e_validar_todos():
    """
    Lista e valida todos os arquivos Excel de notas no diretório
    """
    print("🔍 Procurando arquivos Excel de notas...\n")
    
    # Procurar arquivos
    arquivos = list(Path('.').glob('Template_Notas*.xlsx'))
    
    if not arquivos:
        print("❌ Nenhum arquivo encontrado com o padrão 'Template_Notas*.xlsx'")
        return
    
    print(f"✅ Encontrados {len(arquivos)} arquivo(s):\n")
    for i, arquivo in enumerate(arquivos, 1):
        print(f"   {i}. {arquivo.name}")
    
    # Validar cada arquivo
    print(f"\n{'='*70}")
    print("INICIANDO VALIDAÇÃO")
    print(f"{'='*70}")
    
    for arquivo in arquivos:
        validar_excel_notas(str(arquivo))


def criar_visualizacao_ascii(excel_path):
    """
    Cria uma visualização ASCII da tabela de notas
    """
    try:
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        
        # Encontrar linha de cabeçalho
        linha_header = 4
        for row in range(1, 10):
            if ws.cell(row, 1).value == 'Nº':
                linha_header = row
                break
        
        print(f"\n{'='*90}")
        print(f"VISUALIZAÇÃO: {os.path.basename(excel_path)}")
        print(f"{'='*90}\n")
        
        # Imprimir informações do topo
        for row in range(1, linha_header):
            valor = ws.cell(row, 1).value
            if valor:
                print(f"  {valor}")
        
        print(f"\n{'─'*90}")
        
        # Cabeçalho
        print(f"│ {'Nº':^4} │ {'Nome do Aluno':<45} │ {'Nota':^12} │")
        print(f"{'─'*90}")
        
        # Dados (primeiros 10)
        for row in range(linha_header + 1, min(linha_header + 11, ws.max_row + 1)):
            ordem = str(ws.cell(row, 1).value or '').strip()
            nome = str(ws.cell(row, 2).value or '')[:45]  # Limitar nome
            nota = ws.cell(row, 3).value
            
            # Formatar
            nota_str = f"{nota:.2f}" if isinstance(nota, (int, float)) else "-"
            
            print(f"│ {ordem:>4} │ {nome:<45} │ {nota_str:^12} │")
        
        if ws.max_row > linha_header + 10:
            print(f"│ {'...':<4} │ {'...':<45} │ {'...':<12} │")
        
        print(f"{'─'*90}\n")
        
        wb.close()
        
    except Exception as e:
        print(f"Erro ao criar visualização: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Validar arquivo específico
        arquivo = sys.argv[1]
        if os.path.exists(arquivo):
            validar_excel_notas(arquivo)
            criar_visualizacao_ascii(arquivo)
        else:
            print(f"Arquivo não encontrado: {arquivo}")
    else:
        # Validar todos os arquivos
        listar_e_validar_todos()
