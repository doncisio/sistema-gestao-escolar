"""
Módulo para gerar Declaração de Comparecimento de Responsável
Baseado na estrutura existente do sistema
"""
import os
import io
import datetime
from reportlab.lib.pagesizes import letter
from src.core.config import get_image_path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import TableStyle
from src.core.conexao import conectar_bd
from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
from tkinter import messagebox
from typing import Any, cast
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def obter_dados_responsavel_aluno(cursor, aluno_id):
    """
    Obtém os dados do aluno e seus responsáveis para a declaração de comparecimento
    """
    # Primeiro tenta obter o ano letivo atual
    cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = YEAR(CURDATE())")
    ano_atual = cursor.fetchone()
    
    if not ano_atual:
        cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
        ano_atual = cursor.fetchone()
        
    ano_letivo_id = ano_atual[0] if ano_atual else 1
    
    # Buscar dados do aluno, matrícula e responsável
    query = """
        SELECT 
            a.nome AS nome_aluno,
            a.cpf AS cpf_aluno,
            s.nome AS nome_serie,
            t.nome AS nome_turma,
            t.turno AS turno,
            r.nome AS nome_responsavel,
            r.cpf AS cpf_responsavel,
            e.nome AS nome_escola,
            e.endereco AS endereco_escola,
            e.inep AS inep_escola,
            e.cnpj AS cnpj_escola,
            e.municipio AS municipio_escola
        FROM 
            Alunos a
        LEFT JOIN 
            Matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s
        LEFT JOIN 
            Turmas t ON m.turma_id = t.id
        LEFT JOIN 
            series s ON t.serie_id = s.id
        LEFT JOIN
            Escolas e ON a.escola_id = e.id
        LEFT JOIN
            responsaveisalunos ra ON a.id = ra.aluno_id
        LEFT JOIN
            responsaveis r ON ra.responsavel_id = r.id
        WHERE
            a.id = %s
        LIMIT 1;
    """
    
    cursor.execute(query, (ano_letivo_id, aluno_id))
    resultado = cursor.fetchone()
    
    return resultado


def criar_cabecalho_escola(dados):
    """Cria o cabeçalho padrão da escola"""
    nome_escola = dados[7] if dados else ""
    inep_escola = dados[9] if dados else ""
    cnpj_escola = dados[10] if dados else ""
    
    return [
        "ESTADO DO MARANHÃO",
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        f"<b>{nome_escola}</b>",
        f"<b>INEP: {inep_escola}</b>",
        f"<b>CNPJ: {cnpj_escola}</b>"
    ]


def gerar_declaracao_comparecimento_responsavel(aluno_id, data_comparecimento=None, motivo="reunião escolar", 
                                                nome_responsavel_param=None, turno_reuniao="Matutino"):
    """
    Gera uma declaração de comparecimento do responsável de um aluno
    
    Args:
        aluno_id (int): ID do aluno
        data_comparecimento (datetime): Data do comparecimento (padrão: hoje)
        motivo (str): Motivo do comparecimento
        nome_responsavel_param (str): Nome específico do responsável a ser usado
        turno_reuniao (str): Turno da reunião (Matutino ou Vespertino)
    """
    try:
        conn = conectar_bd()
        if conn is None:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
            return
        cursor = cast(Any, conn).cursor()
        
        # Obter dados
        dados = obter_dados_responsavel_aluno(cursor, aluno_id)
        
        cursor.close()
        conn.close()
        
        if not dados:
            messagebox.showerror("Erro", "Não foi possível obter os dados do aluno.")
            return
        
        # Extrair dados
        nome_aluno = dados[0]
        nome_serie = dados[2] if dados[2] else "Série não informada"
        nome_turma = dados[3] if dados[3] else ""
        turno = dados[4] if dados[4] else "MAT"
        
        # Usar o responsável informado ou o padrão do banco
        if nome_responsavel_param:
            nome_responsavel = nome_responsavel_param
            # Buscar CPF do responsável selecionado
            cpf_responsavel = None
            conn_temp = conectar_bd()
            if conn_temp is None:
                # Não conseguimos abrir conexão temporária; manter cpf_responsavel como None
                logger.warning("Aviso: não foi possível conectar ao banco para buscar CPF do responsável")
            else:
                try:
                    cursor_temp = cast(Any, conn_temp).cursor()
                    cursor_temp.execute("""
                        SELECT r.cpf 
                        FROM responsaveis r
                        INNER JOIN responsaveisalunos ra ON r.id = ra.responsavel_id
                        WHERE ra.aluno_id = %s AND r.nome = %s
                        LIMIT 1
                    """, (aluno_id, nome_responsavel_param))
                    result = cursor_temp.fetchone()
                    cpf_responsavel = result[0] if result else None
                except Exception:
                    cpf_responsavel = None
                finally:
                    try:
                        cursor_temp.close()
                    except Exception:
                        pass
                    try:
                        conn_temp.close()
                    except Exception:
                        pass
        else:
            nome_responsavel = dados[5] if dados[5] else "Responsável"
            cpf_responsavel = dados[6]
        
        nome_escola = dados[7]
        endereco_escola = dados[8]
        municipio_escola = dados[11]
        
        # Formatar turma
        turma_completa = f"{nome_serie} {nome_turma}".strip()
        
        # Turno da turma (do banco de dados)
        turno_turma = turno if turno else "Não informado"
        
        # Turno da reunião (selecionado pelo usuário)
        turno_reuniao_texto = turno_reuniao
        
        # Data do comparecimento
        if data_comparecimento is None:
            data_comparecimento = datetime.datetime.now()
        
        # Formatar data por extenso usando util consolidado
        from src.utils.dates import formatar_data_extenso
        data_extenso = formatar_data_extenso(data_comparecimento)
        
        # Criar nome do arquivo
        data_arquivo = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Garantir que o nome do responsável seja string segura para arquivo
        safe_nome_responsavel = (str(nome_responsavel) if nome_responsavel else "Responsavel").replace(' ', '_')
        nome_arquivo = f"Declaracao_Comparecimento_{safe_nome_responsavel}_{data_arquivo}.pdf"
        caminho_arquivo = os.path.join('documentos_gerados', nome_arquivo)
        os.makedirs('documentos_gerados', exist_ok=True)
        
        # Criar PDF
        buffer = io.BytesIO()
        criar_pdf_declaracao_comparecimento(
            buffer, 
            dados, 
            nome_aluno, 
            nome_responsavel, 
            cpf_responsavel,
            turma_completa, 
            turno_turma, 
            turno_reuniao_texto,
            data_extenso,
            motivo
        )
        
        # Salvar arquivo
        with open(caminho_arquivo, 'wb') as f:
            f.write(buffer.getvalue())
        
        # Salvar no sistema de documentos
        descricao = f"Declaração de Comparecimento de Responsável - {nome_responsavel} - Aluno: {nome_aluno}"
        finalidade = "Declaração de Comparecimento de Responsável"
        
        sucesso, mensagem, link = salvar_documento_sistema(
            caminho_arquivo=caminho_arquivo,
            tipo_documento="DECL-RESP",
            aluno_id=aluno_id,
            finalidade=finalidade,
            descricao=descricao
        )
        
        if not sucesso:
            messagebox.showwarning("Aviso", 
                                 "O documento foi gerado mas houve um erro ao salvá-lo no sistema:\n" + mensagem)
        
        # Abrir o PDF
        buffer.seek(0)
        salvar_e_abrir_pdf(buffer)
        
        messagebox.showinfo("Sucesso", f"Declaração de comparecimento gerada com sucesso!")
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao gerar declaração de comparecimento: {str(e)}")
        logger.exception("Erro detalhado: %s", e)


def criar_pdf_declaracao_comparecimento(buffer, dados, nome_aluno, nome_responsavel, cpf_responsavel,
                                        turma, turno_turma, turno_reuniao, data_extenso, motivo):
    """
    Cria o PDF da declaração de comparecimento
    
    Args:
        buffer: Buffer para escrever o PDF
        dados: Dados da escola
        nome_aluno: Nome do aluno
        nome_responsavel: Nome do responsável
        cpf_responsavel: CPF do responsável
        turma: Turma do aluno
        turno_turma: Turno da turma do aluno (do banco de dados)
        turno_reuniao: Turno da reunião (selecionado pelo usuário)
        data_extenso: Data por extenso
        motivo: Motivo do comparecimento
    """
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=85,
        rightMargin=56,
        topMargin=85,
        bottomMargin=56
    )
    
    elements = []
    
    # Cabeçalho
    cabecalho = criar_cabecalho_escola(dados)
    
    # Imagens
    figura_superior = str(get_image_path('pacologo.png'))
    figura_inferior = str(get_image_path('logopacobranco.png'))
    
    # Tabela do cabeçalho
    data_cabecalho = [
        [Image(figura_superior, width=1 * inch, height=1 * inch),
         Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
         Image(figura_inferior, width=1.5 * inch, height=1 * inch)]
    ]
    
    table = Table(data_cabecalho, colWidths=[1.32 * inch, 4.5 * inch, 1.32 * inch])
    table_style = TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')])
    table.setStyle(table_style)
    elements.append(table)
    
    elements.append(Spacer(1, 0.5 * inch))
    
    # Título
    elements.append(Paragraph("<b>DECLARAÇÃO DE COMPARECIMENTO</b>", 
                            ParagraphStyle(name='Titulo', fontSize=16, alignment=1)))
    
    elements.append(Spacer(1, 0.5 * inch))
    
    # Estilo do texto
    style_texto = ParagraphStyle(
        name='TextoDeclaracao',
        fontSize=12,
        alignment=4,  # Justificado
        leading=18
    )
    
    # Corpo da declaração
    # Definir horário baseado no turno da reunião
    horario_reuniao = ""
    if turno_reuniao.lower() == "matutino":
        horario_reuniao = "de 8:00h às 11:30h"
    elif turno_reuniao.lower() == "vespertino":
        horario_reuniao = "de 14:00h às 17:30h"
    
    texto = f"""
    Declaramos para os devidos fins que o(a) Sr(a). <b>{nome_responsavel}</b>{f', CPF: {cpf_responsavel}' if cpf_responsavel else ''}, 
    responsável pelo(a) aluno(a) <b>{nome_aluno}</b>, da turma <b>{turma}</b>, turno <b>{turno_turma}</b>, 
    compareceu nesta instituição de ensino no dia <b>{data_extenso}</b>, no turno <b>{turno_reuniao.lower()} {horario_reuniao}</b>, para {motivo}.
    """
    
    elements.append(Paragraph(texto, style_texto))
    
    elements.append(Spacer(1, 0.5 * inch))
    
    # Data de emissão
    data_emissao_extenso = datetime.datetime.now().strftime('%d de %B de %Y')
    meses_pt = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    for eng, pt in meses_pt.items():
        data_emissao_extenso = data_emissao_extenso.replace(eng, pt)
    
    elements.append(Paragraph(f"Paço do Lumiar – MA, {data_emissao_extenso}.",
                            ParagraphStyle(name='Data', fontSize=12, alignment=2)))
    
    elements.append(Spacer(1, 1.2 * inch))
    
    # Assinatura
    elements.append(Paragraph("______________________________________",
                            ParagraphStyle(name='Assinatura', fontSize=12, alignment=1)))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("GESTOR(A)",
                            ParagraphStyle(name='CargoAssinatura', fontSize=12, alignment=1)))
    
    # Rodapé
    endereco_escola = dados[8] if dados else ""
    municipio_escola = dados[11] if dados else ""
    rodape_texto = f"{endereco_escola} - {municipio_escola}."
    
    def rodape(canvas, doc):
        width, height = letter
        canvas.saveState()
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(width / 2, 0.75 * inch, rodape_texto)
        canvas.restoreState()
    
    # Build PDF
    doc.build(elements, onFirstPage=rodape, onLaterPages=rodape)


# Função auxiliar para abrir interface de geração
def abrir_interface_declaracao_comparecimento(aluno_id, janela_pai):
    """
    Abre uma interface para o usuário escolher os parâmetros da declaração
    """
    from tkinter import Toplevel, Frame, Label, Entry, Button
    from tkcalendar import DateEntry
    
    # Cores do sistema
    co0 = "#F5F5F5"
    co1 = "#003A70"
    co2 = "#77B341"
    co4 = "#4A86E8"
    
    janela = Toplevel(janela_pai)
    janela.title("Declaração de Comparecimento")
    janela.geometry("500x300")
    janela.configure(bg=co1)
    janela.transient(janela_pai)
    janela.focus_force()
    janela.grab_set()
    
    frame = Frame(janela, bg=co1, padx=20, pady=20)
    frame.pack(fill='both', expand=True)
    
    # Título
    Label(frame, text="Gerar Declaração de Comparecimento", 
          font=("Arial", 14, "bold"), bg=co1, fg=co0).pack(pady=(0, 20))
    
    # Data do comparecimento
    Label(frame, text="Data do Comparecimento:", bg=co1, fg=co0, 
          font=("Arial", 11)).pack(anchor='w', pady=(10, 5))
    
    data_entry = DateEntry(frame, width=30, background='darkblue', 
                          foreground='white', borderwidth=2, 
                          date_pattern='dd/mm/yyyy')
    data_entry.pack(pady=(0, 10))
    
    # Motivo
    Label(frame, text="Motivo do Comparecimento:", bg=co1, fg=co0, 
          font=("Arial", 11)).pack(anchor='w', pady=(10, 5))
    
    motivo_entry = Entry(frame, width=40, font=("Arial", 11))
    motivo_entry.insert(0, "reunião escolar")
    motivo_entry.pack(pady=(0, 20))
    
    # Função para gerar
    def gerar():
        data_selecionada = data_entry.get_date()
        motivo = motivo_entry.get()
        janela.destroy()
        gerar_declaracao_comparecimento_responsavel(aluno_id, data_selecionada, motivo)
    
    # Botões
    frame_botoes = Frame(frame, bg=co1)
    frame_botoes.pack(fill='x', pady=(20, 0))
    
    Button(frame_botoes, text="Gerar", command=gerar, 
           bg=co2, fg=co0, font=("Arial", 11, "bold"), 
           width=12).pack(side='left', padx=5)
    
    Button(frame_botoes, text="Cancelar", command=janela.destroy,
           bg=co4, fg=co0, font=("Arial", 11), 
           width=12).pack(side='right', padx=5)


if __name__ == "__main__":
    # Teste
    logger.info("Módulo de Declaração de Comparecimento carregado com sucesso!")
