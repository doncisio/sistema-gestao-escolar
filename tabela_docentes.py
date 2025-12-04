from reportlab.platypus import Image, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import black, HexColor, Color
from reportlab.lib.pagesizes import landscape, letter
import os
from conexao import conectar_bd
from config import get_image_path
from typing import Any, cast
from biblio_editor import create_pdf_buffer, quebra_linha
from gerarPDF import salvar_e_abrir_pdf
import io
from reportlab.platypus import SimpleDocTemplate

# Cache global para imagens e estilos
_IMAGE_CACHE = {}
_STYLE_CACHE = {}

def _get_cached_image(path, width, height):
    """Retorna uma imagem em cache para evitar recarregamento."""
    key = (path, width, height)
    if key not in _IMAGE_CACHE:
        _IMAGE_CACHE[key] = Image(path, width=width, height=height)
    return _IMAGE_CACHE[key]

def _get_cached_style(name, **kwargs):
    """Retorna um estilo em cache para evitar recriação."""
    key = (name, tuple(sorted(kwargs.items())))
    if key not in _STYLE_CACHE:
        _STYLE_CACHE[key] = ParagraphStyle(name=name, **kwargs)
    return _STYLE_CACHE[key]

def buscar_docentes(cursor, escola_id=60):
    """Busca todos os professores da escola"""
    query = """
    SELECT 
        f.id,
        f.nome,
        f.matricula,
        f.data_admissao,
        f.cargo,
        f.funcao,
        f.turno,
        f.carga_horaria,
        f.vinculo,
        f.polivalente,
        GROUP_CONCAT(DISTINCT d.nome SEPARATOR ', ') as disciplinas,
        CASE 
            WHEN f.polivalente = 'sim' THEN 
                CASE 
                    WHEN f.turma IS NOT NULL THEN 
                        (SELECT CONCAT(s.nome, ' ', t.nome) 
                         FROM turmas t 
                         JOIN series s ON t.serie_id = s.id 
                         WHERE t.id = f.turma)
                    WHEN EXISTS (
                        SELECT 1 FROM funcionario_disciplinas fd2 
                        WHERE fd2.funcionario_id = f.id AND fd2.turma_id IS NOT NULL
                    ) THEN
                        (SELECT GROUP_CONCAT(DISTINCT CONCAT(s2.nome, ' ', t2.nome) ORDER BY s2.nome, t2.nome SEPARATOR ', ')
                         FROM funcionario_disciplinas fd3
                         JOIN turmas t2 ON fd3.turma_id = t2.id
                         JOIN series s2 ON t2.serie_id = s2.id
                         WHERE fd3.funcionario_id = f.id AND fd3.turma_id IS NOT NULL)
                    ELSE 'Volante (Todas as Turmas)'
                END
            ELSE 
                GROUP_CONCAT(DISTINCT CONCAT(s.nome, ' ', t.nome) SEPARATOR ', ')
        END AS turmas,
        (SELECT l.motivo FROM licencas l WHERE l.funcionario_id = f.id 
         AND CURRENT_DATE() BETWEEN l.data_inicio AND l.data_fim LIMIT 1) as licenca_motivo,
        (SELECT CONCAT(DATE_FORMAT(l.data_inicio, '%d/%m/%Y'), ' a ', 
                      DATE_FORMAT(l.data_fim, '%d/%m/%Y')) 
         FROM licencas l WHERE l.funcionario_id = f.id 
         AND CURRENT_DATE() BETWEEN l.data_inicio AND l.data_fim LIMIT 1) as licenca_periodo
    FROM 
        funcionarios f
    LEFT JOIN 
        funcionario_disciplinas fd ON f.id = fd.funcionario_id
    LEFT JOIN 
        disciplinas d ON fd.disciplina_id = d.id
    LEFT JOIN 
        funcionario_disciplinas ft ON f.id = ft.funcionario_id
    LEFT JOIN 
        turmas t ON ft.turma_id = t.id
    LEFT JOIN 
        series s ON t.serie_id = s.id
    WHERE 
        f.escola_id = %s
        AND f.cargo = 'Professor@'
    GROUP BY 
        f.id
    ORDER BY 
        f.polivalente DESC,
        f.nome ASC
    """
    cursor.execute(query, (escola_id,))
    return cursor.fetchall()

def gerar_tabela_docentes():
    # Estabelecer conexão com o banco de dados
    conn: Any = conectar_bd()
    cursor = cast(Any, conn).cursor(dictionary=True)
    
    # Buscar dados dos professores
    professores = buscar_docentes(cursor, escola_id=60)
    
    # Criar um novo buffer
    buffer = io.BytesIO()
    
    # Criar documento PDF em modo paisagem
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=18,
        topMargin=10,
        bottomMargin=10
    )
    elements = []
    
    # Definir o cabeçalho
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]
    
    # Adicionar o cabeçalho com cache
    figura_inferior = str(get_image_path('logopaco.png'))
    img_inf = _get_cached_image(figura_inferior, 3 * inch, 0.7 * inch)
    header_style = _get_cached_style('Header', fontSize=12, alignment=1)
    
    data = [
        [img_inf],
        [Paragraph('<br/>'.join(cabecalho), header_style)]
    ]
    table = Table(data, colWidths=[5 * inch])
    table_style = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ])
    table.setStyle(table_style)
    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # Adicionar título
    title_style = _get_cached_style('Title', fontSize=14, alignment=1)
    elements.append(Paragraph("<b>QUADRO DE DOCENTES E DISCIPLINAS PENDENTES da EM Profª Nadir Nascimento Moraes</b>", 
                            title_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Definir estilos para os parágrafos
    styles = getSampleStyleSheet()
    style_cell = _get_cached_style('Cell', fontSize=8, alignment=1)
    style_cell_left = _get_cached_style('CellLeft', fontSize=8, alignment=0)
    
    # Preparar dados da tabela
    headers = ["Nº", "NOME DO SERVIDOR", "CARGO", "SITUAÇÃO FUNCIONAL", "HABILITAÇÃO", "CLASSE REGENTE", quebra_linha("CARGA\nHORÁRIA"), "LICENÇA"]
    data = [headers]
    
    numero = 1  # Inicializa o contador
    for professor in professores:
        licenca_info = ""
        if professor.get('licenca_motivo'):
            licenca_info = professor['licenca_motivo']
        
        habilitacao = ""
        classe_regente_obj = Paragraph("---", style_cell)

        if 'Kevin Anderson' in professor['nome']:
            habilitacao = "INTÉRPRETE DE LIBRAS"
            classe_regente_obj = Paragraph("7º Ano", style_cell)
        elif professor['polivalente'] == 'sim':
            habilitacao = "Polivalente"
            classe_regente_str = professor.get('turmas') or "---"
            
            # Exceção para Josué Alves Bezerra Júnior - adicionar 3º Ano
            if 'Josué Alves Bezerra Júnior' in professor['nome']:
                if '3º Ano' not in classe_regente_str:
                    if classe_regente_str != "---":
                        classe_regente_str = classe_regente_str + ', 3º Ano'
                    else:
                        classe_regente_str = '3º Ano'
            elif "Volante (Todas as Turmas)" in classe_regente_str:
                classe_regente_str = "1º a 5º Ano"
            
            classe_regente_obj = Paragraph(classe_regente_str, style_cell)
        else:
            habilitacao = professor.get('disciplinas') or "---"
            turmas_str = professor.get('turmas')
            
            if turmas_str:
                turmas_list = [t.strip() for t in turmas_str.split(',') if t.strip()]
                
                if len(turmas_list) > 1:
                    # Agrupa as turmas de duas em duas
                    grupos = [turmas_list[i:i+2] for i in range(0, len(turmas_list), 2)]
                    # Formata cada grupo
                    grupos_formatados = []
                    for i, grupo in enumerate(grupos):
                        if i == len(grupos) - 1:  # último grupo
                            if len(grupo) == 2:
                                grupos_formatados.append(f"{grupo[0]} e {grupo[1]}")
                            else:
                                grupos_formatados.append(grupo[0])
                        else:
                            grupos_formatados.append(f"{grupo[0]}, {grupo[1]}")
                    
                    classe_regente_str = '<br/>'.join(grupos_formatados)
                else:
                    classe_regente_str = turmas_list[0]
                classe_regente_obj = Paragraph(classe_regente_str, style_cell)

        row = [
            Paragraph(str(numero), style_cell),
            Paragraph(professor['nome'], style_cell_left),
            Paragraph(professor['cargo'], style_cell),
            Paragraph(professor['vinculo'], style_cell),
            Paragraph(habilitacao, style_cell),
            classe_regente_obj,
            Paragraph(str(professor['carga_horaria']) if professor['carga_horaria'] else "---", style_cell),
            Paragraph(licenca_info or "---", style_cell)
        ]
        data.append(row)
        numero += 1  # Incrementa o contador
    
    # Criar tabela de docentes com larguras ajustadas para paisagem
    col_widths = [0.4*inch, 2.2*inch, 1.0*inch, 1.6*inch, 1.3*inch, 1.3*inch, 1.0*inch, 1.4*inch]
    table_docentes = Table(data, colWidths=col_widths)
    
    # Estilo da tabela de docentes
    cor_cabecalho = HexColor('#1B4F72')
    style_docentes = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), cor_cabecalho),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F0F0F0')]),
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('BOX', (0, 0), (-1, -1), 1, black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, black),
    ])
    
    table_docentes.setStyle(style_docentes)
    elements.append(table_docentes)
    
    # Gera o PDF
    doc.build(elements)
    
    # Fechar conexão com o banco de dados
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass
    try:
        if conn:
            conn.close()
    except Exception:
        pass
    
    # Retorna o buffer
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    buffer = gerar_tabela_docentes()
    if buffer:
        try:
            from gerarPDF import salvar_e_abrir_pdf as _salvar_helper
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
                from utilitarios.gerenciador_documentos import salvar_documento_sistema
                from utilitarios.tipos_documentos import TIPO_LISTA_ATUALIZADA

                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                try:
                    tmp.write(buffer.getvalue())
                    tmp.close()
                    descricao = f"Tabela de Docentes - {datetime.datetime.now().year}"
                    try:
                        salvar_documento_sistema(tmp.name, TIPO_LISTA_ATUALIZADA, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
                        saved_path = tmp.name
                    except Exception:
                        try:
                            if _salvar_helper:
                                buffer.seek(0)
                                _salvar_helper(buffer)
                        except Exception:
                            pass
                finally:
                    pass
        finally:
            try:
                buffer.close()
            except Exception:
                pass