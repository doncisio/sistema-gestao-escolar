import os
import sys
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch

# Adiciona o diretório pai ao sys.path para permitir importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mapeamento de turmas para pastas
PASTAS_TURMAS = {
    "1º Ano": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Iniciais\1º Ano",
    "2º Ano": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Iniciais\2º Ano",
    "3º Ano": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Iniciais\3º Ano",
    "4º Ano": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Iniciais\4º Ano",
    "5º Ano": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Iniciais\5º Ano",
    "6º Ano A": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Finais\6º Ano A",
    "6º Ano B": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Finais\6º Ano B",
    "7º Ano": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Finais\7º Ano",
    "8º Ano": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Finais\8º Ano",
    "9º Ano": r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Finais\9º Ano",
}

def criar_pastas_se_nao_existirem():
    """Cria as pastas especificadas no mapeamento, se elas não existirem."""
    for pasta in PASTAS_TURMAS.values():
        if not os.path.exists(pasta):
            os.makedirs(pasta)
            print(f"Pasta criada: {pasta}")

def salvar_pdf(buffer, nome_turma, tipo_documento):
    """Salva o PDF na pasta correspondente à turma."""
    if nome_turma not in PASTAS_TURMAS:
        raise ValueError(f"Turma '{nome_turma}' não mapeada para uma pasta.")

    pasta_destino = PASTAS_TURMAS[nome_turma]
    caminho_pdf = os.path.join(pasta_destino, f"{tipo_documento}_{nome_turma}.pdf")

    with open(caminho_pdf, "wb") as f:
        f.write(buffer.getvalue())

    print(f"PDF salvo em: {caminho_pdf}")

def adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior, tamanho_fonte=12):
    """Adiciona o cabeçalho padrão ao documento."""
    data = [
        [Image(figura_superior, width=1 * inch, height=1 * inch),
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=tamanho_fonte, alignment=1)),
         Image(figura_inferior, width=1.5 * inch, height=1 * inch)]
    ]
    table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
    table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.append(table)

def gerar_documentos():
    """Função principal que gera todos os documentos necessários."""
    from scripts_nao_utilizados.gerar_tabela_notas import lista_notas
    from scripts_nao_utilizados.gerar_tabela_frequencia import lista_frequencia
    from scripts_nao_utilizados.gerar_lista_reuniao import lista_reuniao
    from scripts_nao_utilizados.gerar_lista_alunos import lista_alunos
    from scripts_nao_utilizados.gerar_lista_fardamento import lista_fardamento
    
    print("Iniciando geração de documentos...")
    
    try:
        print("\nGerando tabelas de notas...")
        lista_notas()
        print("Tabelas de notas geradas com sucesso!")
    except Exception as e:
        print(f"Erro ao gerar tabelas de notas: {str(e)}")
    
    try:
        print("\nGerando tabelas de frequência...")
        lista_frequencia()
        print("Tabelas de frequência geradas com sucesso!")
    except Exception as e:
        print(f"Erro ao gerar tabelas de frequência: {str(e)}")
        
    try:
        print("\nGerando listas de reunião...")
        lista_reuniao()
        print("Listas de reunião geradas com sucesso!")
    except Exception as e:
        print(f"Erro ao gerar listas de reunião: {str(e)}")
        
    try:
        print("\nGerando listas de alunos...")
        lista_alunos()
        print("Listas de alunos geradas com sucesso!")
    except Exception as e:
        print(f"Erro ao gerar listas de alunos: {str(e)}")
        
    try:
        print("\nGerando listas de fardamento...")
        lista_fardamento()
        print("Listas de fardamento geradas com sucesso!")
    except Exception as e:
        print(f"Erro ao gerar listas de fardamento: {str(e)}")
    
    print("\nProcesso de geração de documentos concluído!")

if __name__ == "__main__":
    gerar_documentos() 