"""
Módulo para preencher templates PDF da pasta SMTT com dados do sistema.
Templates preenchidos com: ano letivo atual, gestor geral e turmas.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

from src.core.conexao import conectar_bd
from src.core.config import ANO_LETIVO_ATUAL, PROJECT_ROOT
from src.core.config_logs import get_logger
from db.connection import get_cursor
from tkinter import messagebox

logger = get_logger(__name__)


def buscar_gestor_geral(escola_id: int = 60) -> Optional[Dict[str, Any]]:
    """
    Busca dados do gestor geral da escola.
    Prioriza quem tem função 'Gestor Geral', senão busca por cargo 'Gestor Escolar'.
    
    Args:
        escola_id: ID da escola (padrão: 60)
        
    Returns:
        Dicionário com dados do gestor ou None
    """
    try:
        with get_cursor() as cursor:
            # Buscar primeiro por função "Gestor Geral"
            cursor.execute("""
                SELECT 
                    nome,
                    cpf,
                    email,
                    telefone,
                    cargo,
                    funcao
                FROM funcionarios
                WHERE escola_id = %s 
                AND (
                    funcao = 'Gestor Geral' 
                    OR (cargo = 'Gestor Escolar' AND funcao IS NULL)
                )
                ORDER BY 
                    CASE WHEN funcao = 'Gestor Geral' THEN 1 ELSE 2 END
                LIMIT 1
            """, (escola_id,))
            
            resultado = cursor.fetchone()
            if resultado:
                logger.info(f"Gestor encontrado: {resultado.get('nome', 'N/A') if isinstance(resultado, dict) else resultado[0]}")
                return resultado
            
            logger.warning("Nenhum gestor geral encontrado")
            return None
            
    except Exception as e:
        logger.exception(f"Erro ao buscar gestor geral: {e}")
        return None


def buscar_dados_ano_letivo(ano_letivo: int = None) -> Optional[Dict[str, Any]]:
    """
    Busca dados do ano letivo.
    
    Args:
        ano_letivo: Ano letivo a buscar (padrão: ANO_LETIVO_ATUAL)
        
    Returns:
        Dicionário com dados do ano letivo ou None
    """
    if ano_letivo is None:
        ano_letivo = ANO_LETIVO_ATUAL
        
    try:
        with get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id,
                    ano_letivo,
                    data_inicio,
                    data_fim,
                    numero_dias_aula
                FROM anosletivos
                WHERE ano_letivo = %s
                LIMIT 1
            """, (ano_letivo,))
            
            resultado = cursor.fetchone()
            if resultado:
                logger.info(f"Ano letivo encontrado: {ano_letivo}")
                return resultado
            
            logger.warning(f"Ano letivo {ano_letivo} não encontrado")
            return None
            
    except Exception as e:
        logger.exception(f"Erro ao buscar ano letivo: {e}")
        return None


def buscar_turmas_escola(escola_id: int = 60, ano_letivo_id: int = None) -> List[Dict[str, Any]]:
    """
    Busca todas as turmas da escola no ano letivo.
    
    Args:
        escola_id: ID da escola (padrão: 60)
        ano_letivo_id: ID do ano letivo (padrão: ano atual)
        
    Returns:
        Lista de dicionários com dados das turmas
    """
    try:
        with get_cursor() as cursor:
            # Se não forneceu ano_letivo_id, buscar o atual
            if ano_letivo_id is None:
                dados_ano = buscar_dados_ano_letivo()
                if dados_ano:
                    ano_letivo_id = dados_ano.get('id') if isinstance(dados_ano, dict) else dados_ano[0]
                else:
                    logger.error("Não foi possível determinar o ano letivo")
                    return []
            
            cursor.execute("""
                SELECT 
                    t.id,
                    t.nome as turma_nome,
                    t.turno,
                    s.nome as serie_nome,
                    COUNT(DISTINCT m.aluno_id) as total_alunos
                FROM turmas t
                JOIN series s ON t.serie_id = s.id
                LEFT JOIN matriculas m ON t.id = m.turma_id 
                    AND m.status = 'Ativo'
                    AND m.ano_letivo_id = %s
                WHERE t.escola_id = %s
                AND t.ano_letivo_id = %s
                GROUP BY t.id, t.nome, t.turno, s.nome
                ORDER BY s.nome, t.nome, t.turno
            """, (ano_letivo_id, escola_id, ano_letivo_id))
            
            turmas = cursor.fetchall()
            logger.info(f"Encontradas {len(turmas)} turmas")
            return turmas
            
    except Exception as e:
        logger.exception(f"Erro ao buscar turmas: {e}")
        return []


def criar_overlay_preenchido(template_path: str, dados: Dict[str, Any]) -> io.BytesIO:
    """
    Cria um overlay PDF com os dados preenchidos.
    
    Args:
        template_path: Caminho do template PDF
        dados: Dicionário com dados para preencher
        
    Returns:
        BytesIO com o PDF do overlay
    """
    # Criar buffer em memória
    packet = io.BytesIO()
    
    # Criar canvas para desenhar texto
    can = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    
    # Determinar qual template estamos preenchendo
    nome_arquivo = os.path.basename(template_path).lower()
    
    # Configurar fonte
    can.setFillColor(black)
    can.setFont("Helvetica", 10)
    
    # Preencher campos específicos baseado no template
    if 'curso' in nome_arquivo:
        # Template de curso
        ano_letivo = dados.get('ano_letivo', ANO_LETIVO_ATUAL)
        can.drawString(100, height - 200, f"Ano Letivo: {ano_letivo}")
        
        # Adicionar informações das turmas
        y_pos = height - 250
        turmas = dados.get('turmas', [])
        for i, turma in enumerate(turmas[:10]):  # Limitar a 10 turmas
            serie = turma.get('serie_nome', 'N/A') if isinstance(turma, dict) else turma[3]
            nome_turma = turma.get('turma_nome', 'N/A') if isinstance(turma, dict) else turma[1]
            turno = turma.get('turno', 'N/A') if isinstance(turma, dict) else turma[2]
            texto = f"{serie} - Turma {nome_turma} ({turno})"
            can.drawString(100, y_pos - (i * 20), texto)
    
    elif 'instituicao' in nome_arquivo:
        # Template de instituição
        gestor = dados.get('gestor')
        if gestor:
            nome_gestor = gestor.get('nome', 'N/A') if isinstance(gestor, dict) else gestor[0]
            can.drawString(100, height - 200, f"Gestor: {nome_gestor}")
        
        ano_letivo = dados.get('ano_letivo', ANO_LETIVO_ATUAL)
        can.drawString(100, height - 230, f"Ano Letivo: {ano_letivo}")
    
    elif 'representante' in nome_arquivo:
        # Template de representante
        gestor = dados.get('gestor')
        if gestor:
            nome_gestor = gestor.get('nome', 'N/A') if isinstance(gestor, dict) else gestor[0]
            cpf_gestor = gestor.get('cpf', 'N/A') if isinstance(gestor, dict) else gestor[1]
            telefone_gestor = gestor.get('telefone', 'N/A') if isinstance(gestor, dict) else gestor[3]
            email_gestor = gestor.get('email', 'N/A') if isinstance(gestor, dict) else gestor[2]
            
            can.drawString(100, height - 200, f"Nome: {nome_gestor}")
            can.drawString(100, height - 230, f"CPF: {cpf_gestor}")
            can.drawString(100, height - 260, f"Telefone: {telefone_gestor}")
            can.drawString(100, height - 290, f"Email: {email_gestor}")
    
    can.save()
    
    packet.seek(0)
    return packet


def preencher_pdf(template_path: str, output_path: str, dados: Dict[str, Any]) -> bool:
    """
    Preenche um PDF template com dados e salva o resultado.
    
    Args:
        template_path: Caminho do template PDF original
        output_path: Caminho onde salvar o PDF preenchido
        dados: Dicionário com dados para preencher
        
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        # Verificar se o template existe
        if not os.path.exists(template_path):
            logger.error(f"Template não encontrado: {template_path}")
            return False
        
        # Ler o PDF template
        template_pdf = PdfReader(template_path)
        
        # Criar overlay com os dados
        overlay_packet = criar_overlay_preenchido(template_path, dados)
        overlay_pdf = PdfReader(overlay_packet)
        
        # Criar PDF de saída
        output_pdf = PdfWriter()
        
        # Mesclar cada página
        for page_num in range(len(template_pdf.pages)):
            page = template_pdf.pages[page_num]
            
            # Se temos overlay para esta página, adicionar
            if page_num < len(overlay_pdf.pages):
                page.merge_page(overlay_pdf.pages[page_num])
            
            output_pdf.add_page(page)
        
        # Salvar PDF preenchido
        with open(output_path, 'wb') as output_file:
            output_pdf.write(output_file)
        
        logger.info(f"PDF preenchido salvo: {output_path}")
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao preencher PDF: {e}")
        return False


def gerar_documentos_smtt(escola_id: int = 60) -> Tuple[int, int]:
    """
    Gera todos os documentos SMTT preenchidos.
    
    Args:
        escola_id: ID da escola (padrão: 60)
        
    Returns:
        Tupla (sucesso, total) com quantidade de arquivos gerados e total
    """
    try:
        # Buscar dados necessários
        logger.info("Buscando dados do sistema...")
        
        dados_ano = buscar_dados_ano_letivo()
        if not dados_ano:
            messagebox.showerror("Erro", "Ano letivo atual não encontrado no sistema.")
            return (0, 0)
        
        gestor = buscar_gestor_geral(escola_id)
        if not gestor:
            messagebox.showwarning("Aviso", "Gestor geral não encontrado. Os documentos serão gerados sem essas informações.")
        
        turmas = buscar_turmas_escola(escola_id)
        if not turmas:
            messagebox.showwarning("Aviso", "Nenhuma turma encontrada para o ano letivo atual.")
        
        # Preparar dados para preenchimento
        ano_letivo = dados_ano.get('ano_letivo', ANO_LETIVO_ATUAL) if isinstance(dados_ano, dict) else dados_ano[1]
        
        dados = {
            'ano_letivo': ano_letivo,
            'gestor': gestor,
            'turmas': turmas,
            'data_geracao': datetime.now().strftime('%d/%m/%Y')
        }
        
        # Diretórios
        pasta_smtt = os.path.join(PROJECT_ROOT, 'SMTT')
        pasta_saida = os.path.join(PROJECT_ROOT, 'documentos_gerados', 'SMTT')
        
        # Criar pasta de saída se não existir
        os.makedirs(pasta_saida, exist_ok=True)
        
        # Templates disponíveis
        templates = ['curso.pdf', 'instituicao.pdf', 'representante.pdf']
        
        sucesso = 0
        total = len(templates)
        
        # Processar cada template
        for template_nome in templates:
            template_path = os.path.join(pasta_smtt, template_nome)
            
            if not os.path.exists(template_path):
                logger.warning(f"Template não encontrado: {template_path}")
                continue
            
            # Nome do arquivo de saída
            nome_base = template_nome.replace('.pdf', '')
            output_nome = f"{nome_base}_preenchido_{ano_letivo}.pdf"
            output_path = os.path.join(pasta_saida, output_nome)
            
            logger.info(f"Processando {template_nome}...")
            
            if preencher_pdf(template_path, output_path, dados):
                sucesso += 1
                logger.info(f"✓ {template_nome} processado com sucesso")
            else:
                logger.error(f"✗ Erro ao processar {template_nome}")
        
        # Mostrar resultado
        if sucesso > 0:
            messagebox.showinfo(
                "Sucesso",
                f"Documentos SMTT gerados com sucesso!\n\n"
                f"Processados: {sucesso} de {total}\n"
                f"Pasta: {pasta_saida}"
            )
            
            # Abrir pasta de saída
            import webbrowser
            webbrowser.open(pasta_saida)
        else:
            messagebox.showerror(
                "Erro",
                f"Nenhum documento foi gerado com sucesso.\n"
                f"Verifique os logs para mais detalhes."
            )
        
        return (sucesso, total)
        
    except Exception as e:
        logger.exception(f"Erro ao gerar documentos SMTT: {e}")
        messagebox.showerror("Erro", f"Erro ao gerar documentos SMTT:\n{str(e)}")
        return (0, 0)


def abrir_interface_smtt():
    """
    Interface simples para gerar documentos SMTT.
    Pode ser expandida futuramente para permitir seleções.
    """
    try:
        from tkinter import Toplevel, Label, Button, Frame
        import tkinter as tk
        
        # Criar janela
        janela = Toplevel()
        janela.title("Gerar Documentos SMTT")
        janela.geometry("450x250")
        janela.resizable(False, False)
        
        # Centralizar janela
        janela.update_idletasks()
        width = janela.winfo_width()
        height = janela.winfo_height()
        x = (janela.winfo_screenwidth() // 2) - (width // 2)
        y = (janela.winfo_screenheight() // 2) - (height // 2)
        janela.geometry(f'{width}x{height}+{x}+{y}')
        
        # Frame principal
        frame = Frame(janela, padx=20, pady=20)
        frame.pack(expand=True, fill='both')
        
        # Título
        titulo = Label(
            frame,
            text="Gerar Documentos SMTT",
            font=('Arial', 14, 'bold')
        )
        titulo.pack(pady=(0, 15))
        
        # Descrição
        descricao = Label(
            frame,
            text="Os documentos serão preenchidos com:\n\n"
                 f"• Ano Letivo: {ANO_LETIVO_ATUAL}\n"
                 "• Dados do Gestor Geral\n"
                 "• Lista de Turmas Ativas",
            font=('Arial', 10),
            justify='left'
        )
        descricao.pack(pady=10)
        
        # Função para gerar
        def gerar():
            janela.destroy()
            gerar_documentos_smtt()
        
        # Botões
        frame_botoes = Frame(frame)
        frame_botoes.pack(pady=20)
        
        btn_gerar = Button(
            frame_botoes,
            text="Gerar Documentos",
            command=gerar,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=20,
            pady=10
        )
        btn_gerar.pack(side='left', padx=5)
        
        btn_cancelar = Button(
            frame_botoes,
            text="Cancelar",
            command=janela.destroy,
            bg='#f44336',
            fg='white',
            font=('Arial', 10),
            padx=20,
            pady=10
        )
        btn_cancelar.pack(side='left', padx=5)
        
    except Exception as e:
        logger.exception(f"Erro ao abrir interface SMTT: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir interface:\n{str(e)}")


if __name__ == "__main__":
    # Teste
    gerar_documentos_smtt()
