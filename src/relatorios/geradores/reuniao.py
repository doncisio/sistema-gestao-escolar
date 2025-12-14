from src.core.config_logs import get_logger
from src.core.config import get_image_path
logger = get_logger(__name__)
import io
import os
import pandas as pd
import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, grey
from src.relatorios.listas.lista_atualizada import fetch_student_data
from scripts_nao_utilizados.gerar_documentos import adicionar_cabecalho
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
try:
    from src.services.report_service import _find_image_in_repo
except Exception:
    _find_image_in_repo = None

def gerar_lista_reuniao():
    """Gera um PDF com a lista de reunião dos alunos, agrupados por turma."""
    ano_letivo = 2025
    dados_aluno = fetch_student_data(ano_letivo)
    
    if not dados_aluno:
        logger.info("Nenhum dado de aluno encontrado.")
        return
        
    df = pd.DataFrame(dados_aluno)
    # Definir caminhos das imagens usando get_image_path
    figura_superior = str(get_image_path('logosemed.png'))
    figura_inferior = str(get_image_path('logopaco.jpg'))
    
    cabecalho = [
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>EM PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]

    # Lista de itens da pauta
    pauta_items = [
        "Acolhida",
        "Oração: leitura deleite",
        "Fardamento",
        "Livros",
        "Horário de entrada e saída",
        "Comportamento",
        "Uso do celular",
        "Data de recuperação",
        "Não cumprimento das atividades"
    ]
    
    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        nome_turma_completo = f"{nome_serie} {nome_turma}" if nome_turma else nome_serie
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=36,
            rightMargin=18,
            topMargin=18,
            bottomMargin=18
        )
        elements = []
        
        # Adicionar capa inicial
        adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph("<b>LISTA PARA REUNIÃO</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
        elements.append(Spacer(1, 2.5 * inch))
        elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
        elements.append(PageBreak())
        
        # Extrair nome do professor e filtrar alunos ativos
        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']
        
        # Adicionar cabeçalho da página
        adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior, 11)
        elements.append(Spacer(1, 0.125 * inch))
        
        # Adicionar título da turma
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", 
                                ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))

        # Adicionar a pauta da reunião
        elements.append(Paragraph("<b>PAUTA DA REUNIÃO</b>", ParagraphStyle(name='PautaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.2 * inch))
        
        for item in pauta_items:
            elements.append(Paragraph(f"• {item}", ParagraphStyle(name='PautaItem', fontSize=11, leftIndent=20)))
            elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        # Criar tabela de presença com larguras ajustadas para modo paisagem
        data = [['Nº', 'Nome', 'Telefone', 'Assinatura do Responsável', 'Parentesco']]
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row['NOME DO ALUNO']
            # Garantir que valores adicionados à tabela sejam strings para satisfazer o analisador de tipo
            nome_str = str(nome) if pd.notnull(nome) else ""
            telefones_str = ''
            assinatura = ''
            parentesco = ''
            data.append([str(row_num), nome_str, telefones_str, assinatura, parentesco])
        
        # Ajustando as larguras das colunas para melhor aproveitamento do espaço horizontal
        table = Table(data, colWidths=[0.4 * inch, 3 * inch, 1.5 * inch, 3 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), white),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('GRID', (0, 0), (-1, -1), 1, black)
        ]))
        elements.append(table)
        elements.append(PageBreak())
        
        doc.build(elements)
        buffer.seek(0)
        # Usar o util central de PDF para salvar/mover/upload via API (mantém compatibilidade com testes que mockam `services.utils.pdf.salvar_e_abrir_pdf`)
        # Preferir o helper de PDF (mantém compatibilidade com testes que o mockam).
        try:
            from src.relatorios.gerar_pdf import salvar_e_abrir_pdf as _salvar_helper
        except Exception:
            _salvar_helper = None

        saved_path = None
        try:
            if _salvar_helper:
                try:
                    saved_path = _salvar_helper(buffer)
                except Exception:
                    saved_path = None

            if not saved_path:
                import tempfile
                from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
                from src.utils.utilitarios.tipos_documentos import TIPO_LISTA_REUNIAO

                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                try:
                    tmp.write(buffer.getvalue())
                    tmp.close()
                    descricao = f"Lista para Reunião - {nome_turma_completo}"
                    try:
                        salvar_documento_sistema(tmp.name, TIPO_LISTA_REUNIAO, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
                        saved_path = tmp.name
                    except Exception:
                        # fallback legado: escrever em disco local
                        logger.exception("Falha ao salvar/upload via salvar_documento_sistema; fallback: escrever em disco local")
                        try:
                            fd, path = tempfile.mkstemp(suffix='.pdf')
                            os.close(fd)
                            with open(path, 'wb') as f:
                                f.write(buffer.getvalue())
                            logger.info("PDF gravado em fallback local: %s", path)
                        except Exception:
                            logger.exception("Falha no fallback ao gravar PDF local")
                finally:
                    pass
        finally:
            try:
                buffer.close()
            except Exception:
                pass

if __name__ == "__main__":
    gerar_lista_reuniao() 
