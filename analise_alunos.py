import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from conexao import conectar_bd
from utilitarios.gerenciador_documentos import salvar_documento_sistema
from utilitarios.tipos_documentos import TIPO_LISTA_ATUALIZADA
import traceback
import datetime
import os

def buscar_alunos_lista_atualizada():
    print("\nTentando conectar ao banco de dados...")
    conn = conectar_bd()
    if not conn:
        print("Falha na conexão com o banco de dados")
        return []
    
    try:
        cursor = conn.cursor()
        print("Conexão estabelecida com sucesso")
        
        query = """
        SELECT nome, nis, situacao 
        FROM alunos 
        WHERE escola_id = 60 
        AND ano = 2025 
        AND situacao = 'Ativo'
        """
        print(f"Executando query: {query}")
        cursor.execute(query)
        alunos = cursor.fetchall()
        print(f"Encontrados {len(alunos)} alunos na lista atualizada")
        return alunos
    except Exception as e:
        print(f"Erro ao buscar alunos: {e}")
        print(traceback.format_exc())
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexão fechada")

def buscar_ultimo_ano_historico(nome_aluno):
    print(f"\nBuscando histórico para o aluno: {nome_aluno}")
    conn = conectar_bd()
    if not conn:
        print("Falha na conexão com o banco de dados")
        return None
    
    try:
        cursor = conn.cursor()
        query = """
        SELECT MAX(ano) 
        FROM historico_escolar 
        WHERE nome_aluno = %s 
        AND escola_id = 60
        """
        print(f"Executando query: {query} com parâmetro: {nome_aluno}")
        cursor.execute(query, (nome_aluno,))
        resultado = cursor.fetchone()
        ultimo_ano = resultado[0] if resultado else None
        print(f"Último ano encontrado: {ultimo_ano}")
        return ultimo_ano
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        print(traceback.format_exc())
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def analisar_alunos():
    print("\nIniciando análise dos alunos...")
    try:
        # Lê o arquivo CSV
        print("Lendo arquivo CSV...")
        df = pd.read_csv('registro_frequencia.csv')
        print(f"Total de alunos no CSV: {len(df)}")
        
        # Busca alunos da lista atualizada
        alunos_lista_atualizada = buscar_alunos_lista_atualizada()
        alunos_lista_atualizada_nomes = [aluno[0] for aluno in alunos_lista_atualizada]
        
        # Inicializa listas para categorização
        alunos_na_lista = []
        alunos_fora_lista = []
        alunos_sem_historico = []
        
        # Analisa cada aluno do CSV
        for _, row in df.iterrows():
            nome_aluno = row['Estudante']
            nis = row['NIS']
            
            if nome_aluno in alunos_lista_atualizada_nomes:
                aluno_info = alunos_lista_atualizada[alunos_lista_atualizada_nomes.index(nome_aluno)]
                alunos_na_lista.append({
                    'nome': nome_aluno,
                    'nis': nis,
                    'situacao': aluno_info[2]
                })
            else:
                ultimo_ano = buscar_ultimo_ano_historico(nome_aluno)
                if ultimo_ano:
                    alunos_fora_lista.append({
                        'nome': nome_aluno,
                        'nis': nis,
                        'ultimo_ano': ultimo_ano
                    })
                else:
                    alunos_sem_historico.append({
                        'nome': nome_aluno,
                        'nis': nis
                    })
        
        print("\nResumo da análise:")
        print(f"Alunos na lista atualizada: {len(alunos_na_lista)}")
        print(f"Alunos fora da lista: {len(alunos_fora_lista)}")
        print(f"Alunos sem histórico: {len(alunos_sem_historico)}")
        
        return alunos_na_lista, alunos_fora_lista, alunos_sem_historico
    except Exception as e:
        print(f"Erro na análise dos alunos: {e}")
        print(traceback.format_exc())
        return [], [], []

def criar_tabela_alunos(dados, titulo, colunas):
    try:
        # Cria o cabeçalho da tabela
        tabela_dados = [colunas]
        
        # Adiciona os dados dos alunos
        for aluno in dados:
            linha = [aluno[col.lower()] for col in colunas]
            tabela_dados.append(linha)
        
        # Cria a tabela
        tabela = Table(tabela_dados)
        
        # Define o estilo da tabela
        estilo = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        tabela.setStyle(estilo)
        return tabela
    except Exception as e:
        print(f"Erro ao criar tabela: {e}")
        print(traceback.format_exc())
        return None

def gerar_relatorio():
    print("\nIniciando geração do relatório...")
    try:
        # Cria o buffer para o PDF
        buffer = io.BytesIO()
        
        # Cria o documento
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elementos = []
        
        # Adiciona o título
        estilos = getSampleStyleSheet()
        titulo_estilo = ParagraphStyle(
            'CustomTitle',
            parent=estilos['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        titulo = Paragraph("Relatório de Análise de Alunos", titulo_estilo)
        elementos.append(titulo)
        
        # Analisa os alunos
        alunos_na_lista, alunos_fora_lista, alunos_sem_historico = analisar_alunos()
        
        # Adiciona a seção de alunos na lista atualizada
        if alunos_na_lista:
            subtitulo1 = Paragraph("Alunos na Lista Atualizada", estilos['Heading2'])
            elementos.append(subtitulo1)
            elementos.append(Spacer(1, 12))
            
            tabela1 = criar_tabela_alunos(
                alunos_na_lista,
                "Alunos na Lista Atualizada",
                ['Nome', 'NIS', 'Situação']
            )
            if tabela1:
                elementos.append(tabela1)
                elementos.append(Spacer(1, 20))
        
        # Adiciona a seção de alunos fora da lista
        if alunos_fora_lista:
            subtitulo2 = Paragraph("Alunos Fora da Lista Atualizada", estilos['Heading2'])
            elementos.append(subtitulo2)
            elementos.append(Spacer(1, 12))
            
            tabela2 = criar_tabela_alunos(
                alunos_fora_lista,
                "Alunos Fora da Lista",
                ['Nome', 'NIS', 'Último Ano']
            )
            if tabela2:
                elementos.append(tabela2)
                elementos.append(Spacer(1, 20))
        
        # Adiciona a seção de alunos sem histórico
        if alunos_sem_historico:
            subtitulo3 = Paragraph("Alunos Sem Histórico", estilos['Heading2'])
            elementos.append(subtitulo3)
            elementos.append(Spacer(1, 12))
            
            tabela3 = criar_tabela_alunos(
                alunos_sem_historico,
                "Alunos Sem Histórico",
                ['Nome', 'NIS']
            )
            if tabela3:
                elementos.append(tabela3)
        
        # Constrói o PDF
        print("Construindo o PDF...")
        doc.build(elementos)
        
        # Criar nome do arquivo
        data_atual = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"Analise_Alunos_{data_atual}.pdf"
        caminho_arquivo = os.path.join('documentos_gerados', nome_arquivo)
        
        # Garantir que o diretório existe
        os.makedirs('documentos_gerados', exist_ok=True)
        
        # Salvar o PDF localmente
        print("Salvando o PDF...")
        buffer.seek(0)
        with open(caminho_arquivo, 'wb') as f:
            f.write(buffer.getvalue())
        
        # Criar descrição detalhada
        descricao = f"Relatório de Análise de Alunos {datetime.datetime.now().year}"
        
        # Salvar no sistema de gerenciamento de documentos
        sucesso, mensagem, link = salvar_documento_sistema(
            caminho_arquivo=caminho_arquivo,
            tipo_documento=TIPO_LISTA_ATUALIZADA,
            finalidade="Análise de alunos listados, fora da lista e sem histórico",
            descricao=descricao
        )
        
        if not sucesso:
            from tkinter import messagebox
            messagebox.showwarning("Aviso", 
                               "O relatório foi gerado mas houve um erro ao salvá-lo no sistema:\n" + mensagem)
        
        print("Relatório gerado com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao gerar relatório: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Iniciando o script de análise de alunos...")
    gerar_relatorio() 