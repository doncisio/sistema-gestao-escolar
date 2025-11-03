import PyPDF2
import re
import os
from datetime import datetime

# Caminho do arquivo PDF
pdf_path = "calendário.pdf"

# Verificar se o arquivo existe
if not os.path.exists(pdf_path):
    print(f"Erro: O arquivo '{pdf_path}' não foi encontrado.")
    exit(1)

try:
    # Abrir o arquivo PDF
    with open(pdf_path, 'rb') as file:
        # Criar um objeto PDFReader
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Número de páginas no PDF
        num_pages = len(pdf_reader.pages)
        print(f"O PDF tem {num_pages} página(s).")
        
        # Extrair texto de todas as páginas
        full_text = ""
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            full_text += page.extract_text()
        
        # Lista de meses em português
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", 
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        
        # Padrões para detectar eventos
        # Este padrão procura por dias seguido de um texto de evento
        # Exemplo: "10 | Início do 1º período letivo"
        evento_pattern = re.compile(r'(\d{1,2})\s*\|\s*([^|]+?)(?=\d{1,2}\s*\||$|\n)', re.IGNORECASE)
        
        # Padrão para cabeçalhos de mês (em maiúsculas ou com caracteres especiais ao redor)
        mes_pattern = re.compile(r'([A-ZÇÃÕÁÉÍÓÚÂÊÎÔÛ]+\s*[A-ZÇÃÕÁÉÍÓÚÂÊÎÔÛ]+O)\s*', re.IGNORECASE)
        
        # Encontrar eventos no texto
        eventos_por_mes = {}
        mes_atual = None
        
        # Primeiro vamos identificar os meses no texto
        linhas = full_text.split('\n')
        for linha in linhas:
            linha = linha.strip()
            
            # Verificar se é um cabeçalho de mês
            mes_match = mes_pattern.search(linha)
            if mes_match:
                mes_texto = mes_match.group(1).lower()
                
                # Encontrar o mês correspondente na nossa lista
                for mes in meses:
                    if mes in mes_texto.lower():
                        mes_atual = mes.capitalize()
                        if mes_atual not in eventos_por_mes:
                            eventos_por_mes[mes_atual] = []
                        break
            
            # Se temos um mês atual, procurar por eventos nesta linha
            if mes_atual:
                eventos_matches = evento_pattern.finditer(linha)
                for match in eventos_matches:
                    dia = match.group(1)
                    descricao = match.group(2).strip()
                    
                    # Ignorar eventos que parecem ser dias da semana ou letras soltas
                    if len(descricao) > 3 and not re.match(r'^[DSTQ]$', descricao):
                        eventos_por_mes[mes_atual].append({
                            'dia': dia,
                            'descricao': descricao
                        })
        
        # Imprimir eventos encontrados
        print("\nEventos acadêmicos encontrados no calendário escolar:\n")
        
        if eventos_por_mes:
            for mes, eventos in sorted(eventos_por_mes.items(), 
                                      key=lambda x: meses.index(x[0].lower())):
                print(f"=== {mes.upper()} ===")
                if eventos:
                    for evento in sorted(eventos, key=lambda x: int(x['dia'])):
                        print(f"Dia {evento['dia']}: {evento['descricao']}")
                else:
                    print("Nenhum evento encontrado para este mês.")
                print()
        else:
            print("Nenhum evento acadêmico foi encontrado no calendário.")

except Exception as e:
    print(f"Erro ao processar o PDF: {e}") 