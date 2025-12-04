from reportlab.platypus import Image, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import black, HexColor
from reportlab.lib.pagesizes import letter, landscape
import os
from conexao import conectar_bd
from config import get_image_path
from gerarPDF import salvar_e_abrir_pdf
import io
from reportlab.platypus import SimpleDocTemplate
from typing import Any, cast

def buscar_professores(cursor, escola_id=60):
    """Busca todos os professores da escola com informações detalhadas"""
    query = """
    SELECT 
        f.nome,
        f.cpf,
        f.cargo,
        f.carga_horaria,
        f.vinculo,
        f.email,
        f.telefone,
        f.turno,
        GROUP_CONCAT(DISTINCT d.nome SEPARATOR ', ') as disciplinas
    FROM 
        funcionarios f
    LEFT JOIN 
        funcionario_disciplinas fd ON f.id = fd.funcionario_id
    LEFT JOIN 
        disciplinas d ON fd.disciplina_id = d.id
    WHERE 
        f.escola_id = %s
        AND f.cargo = 'Professor@'
    GROUP BY 
        f.id
    ORDER BY 
        f.nome ASC
    """
    cursor.execute(query, (escola_id,))
    professores = cursor.fetchall()
    
    # Adiciona o intérprete de libras manualmente
    interprete = {
        'nome': 'Kevin Anderson Dantas Quintão',
        'cpf': '051.502.143-10',
        'cargo': 'Interprete de Libras',
        'carga_horaria': '20h',
        'vinculo': 'Efetivo',
        'email': 'kevin.a.dantas@gmail.com',
        'telefone': '984296467',
        'disciplinas': None,
        'turno': 'Vespertino'
    }
    professores.append(interprete)
    
    return professores

def buscar_coordenadores(cursor, escola_id=60):
    """Busca todos os coordenadores da escola"""
    query = """
    SELECT 
        f.nome,
        f.turno,
        f.carga_horaria,
        f.vinculo,
        f.email,
        f.telefone,
        f.cargo
    FROM 
        funcionarios f
    WHERE 
        f.escola_id = %s
        AND (f.cargo LIKE '%Coordenador%' OR f.cargo LIKE '%Monitor%')
    ORDER BY 
        f.cargo ASC,
        f.nome ASC
    """
    cursor.execute(query, (escola_id,))
    return cursor.fetchall()

def buscar_gestores(cursor, escola_id=60):
    """Busca os gestores da escola"""
    query = """
    SELECT 
        f.nome,
        f.cargo,
        f.email,
        f.telefone
    FROM 
        funcionarios f
    WHERE 
        f.escola_id = %s
        AND (f.cargo = 'Gestor Escolar' OR f.cargo = 'Gestor@ Adjunto@')
    ORDER BY 
        f.cargo DESC,
        f.nome ASC
    """
    cursor.execute(query, (escola_id,))
    return cursor.fetchall()

def buscar_tutores(cursor, escola_id=60):
    """Busca todos os tutores e seus alunos atendidos"""
    query = """
    SELECT 
        f.nome,
        f.email,
        f.telefone,
        COUNT(faa.aluno_id) as total_alunos,
        CASE 
            WHEN f.id = 173 THEN 'Em licença médica'
            ELSE NULL
        END as observacao
    FROM 
        funcionarios f
    LEFT JOIN 
        funcionario_aluno_ano faa ON f.id = faa.funcionario_id
    WHERE 
        f.escola_id = %s
        AND f.cargo = 'Tutor/Cuidador'
        AND (faa.data_fim IS NULL OR faa.data_fim > CURDATE())
    GROUP BY 
        f.id, f.nome, f.email, f.telefone
    ORDER BY 
        f.nome ASC
    """
    cursor.execute(query, (escola_id,))
    return cursor.fetchall()

def formatar_cpf(cpf):
    """Formata o CPF para o padrão 000.000.000-00"""
    if not cpf:
        return "---"
    # Remove caracteres não numéricos
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def gerar_levantamento_necessidades():
    # Estabelecer conexão com o banco de dados
    conn: Any = conectar_bd()
    if not conn:
        raise RuntimeError("Não foi possível conectar ao banco de dados")
    cursor: Any = cast(Any, conn).cursor(dictionary=True)
    
    # Buscar dados
    professores = buscar_professores(cursor)
    coordenadores = buscar_coordenadores(cursor)
    gestores = buscar_gestores(cursor)
    
    # Criar um novo buffer
    buffer = io.BytesIO()
    
    # Criar documento PDF em modo paisagem
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    elements = []
    
    # Definir estilos
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12
    )
    
    # Definir o cabeçalho
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]
    
    # Adicionar o cabeçalho
    figura_inferior = str(get_image_path('logopaco.png'))
    data = [
        [Image(figura_inferior, width=3 * inch, height=0.7 * inch)],
        [Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1))]
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
    elements.append(Paragraph("<b>LEVANTAMENTO DETALHADO DE NECESSIDADES DE PROFESSORES E QUADRO FUNCIONAL</b>", 
                            ParagraphStyle(name='Title', fontSize=14, alignment=1)))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Adicionar tabela de disciplinas pendentes
    elements.append(Paragraph("<b>COMPONENTES CURRICULARES PENDENTES</b>", style_normal))
    
    # Tabela de disciplinas pendentes
    headers = ["Componente Curricular", "Carga Horária Pendente"]
    data = [headers]
    
    # Exemplo de disciplinas pendentes - você pode ajustar conforme necessário
    disciplinas_pendentes = [
        ["HISTÓRIA", "7h"]
    ]
    
    data.extend(disciplinas_pendentes)
    
    table_pendentes = Table(data)
    style_pendentes = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1B4F72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F0F0F0')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6)
    ])
    table_pendentes.setStyle(style_pendentes)
    elements.append(table_pendentes)
    elements.append(Spacer(1, 0.3 * inch))
    
    # 1. Professores Atuantes
    elements.append(Paragraph("<b>1. PROFESSORES ATUANTES</b>", style_normal))
    
    # Definir estilo padrão para todas as tabelas
    style_padrao = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1B4F72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), 'white'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F0F0F0')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6)
    ])
    
    # Separar professores por turno
    professores_matutino = []
    professores_vespertino = []
    
    for prof in professores:
        # Formata as disciplinas com quebra de linha
        if prof['nome'] == 'Kevin Anderson Dantas Quintão':
            disciplinas = "INTÉRPRETE DE LIBRAS"
        else:
            disciplinas = prof['disciplinas'] or "Polivalente"
            if disciplinas != "Polivalente":
                disciplinas = "<br/>".join(d.strip() for d in disciplinas.split(','))
            
            # Adiciona observação para Ana Patrícia
            if prof['nome'] == 'Ana Patrícia Rodrigues Araújo':
                disciplinas = f"{disciplinas}<br/><i>(Em Cessão)</i>"
            
        row = [
            prof['nome'],
            formatar_cpf(prof['cpf']),
            Paragraph(disciplinas, style_normal),
            str(prof['carga_horaria']) if prof['carga_horaria'] else "---",
            prof['vinculo'] or "---",
            prof['email'] or "---",
            prof['telefone'] or "---"
        ]
        
        # Adiciona à lista apropriada baseado no turno
        if prof['turno'] == 'Vespertino':
            professores_vespertino.append(row)
        else:  # Matutino ou sem turno definido
            professores_matutino.append(row)
    
    # Função auxiliar para criar tabela de professores
    def criar_tabela_professores(professores, titulo):
        if not professores:
            elements.append(Paragraph(f"<i>Não há professores {titulo}.</i>", style_normal))
            elements.append(Spacer(1, 0.3 * inch))
            return
            
        headers = ["Nome Completo", "CPF", "Componente Curricular", "Carga Horária", "Vínculo", "E-mail", "Telefone"]
        data = [headers] + professores
        
        table_prof = Table(data)
        table_prof.setStyle(style_padrao)
        elements.append(table_prof)
        elements.append(Spacer(1, 0.3 * inch))
    
    # Adicionar tabela de professores matutino
    elements.append(Paragraph("<b>Professores do Turno Matutino</b>", style_normal))
    elements.append(Spacer(1, 0.1 * inch))
    criar_tabela_professores(professores_matutino, "no turno matutino")
    
    # Adicionar tabela de professores vespertino
    elements.append(Paragraph("<b>Professores do Turno Vespertino</b>", style_normal))
    elements.append(Spacer(1, 0.1 * inch))
    criar_tabela_professores(professores_vespertino, "no turno vespertino")
    
    # 2. Equipe de Apoio e Gestão
    elements.append(Paragraph("<b>2. EQUIPE DE APOIO E GESTÃO</b>", style_normal))
    
    # Tabela de coordenadores
    headers = ["Nome Completo", "Cargo", "Turno", "Carga Horária", "Vínculo", "E-mail", "Telefone"]
    data = [headers]
    
    # Adiciona a monitora de assuntos escolares
    data.append([
        "Alana Jadhe Lima Coimbra",
        "Monitor(a) de Assuntos Escolares",
        "---",
        "---",
        "---",
        "---",
        "---"
    ])
    
    # Adiciona os coordenadores do banco de dados
    for coord in coordenadores:
        row = [
            coord['nome'],
            coord['cargo'],
            coord['turno'] or "---",
            str(coord['carga_horaria']) if coord['carga_horaria'] else "---",
            coord['vinculo'] or "---",
            coord['email'] or "---",
            coord['telefone'] or "---"
        ]
        data.append(row)
    
    # Só adiciona a tabela se houver coordenadores
    if len(data) > 1:  # Mais de 1 porque o primeiro item é o header
        table_coord = Table(data)
        table_coord.setStyle(style_padrao)
        elements.append(table_coord)
        elements.append(Spacer(1, 0.3 * inch))
    else:
        # Adiciona uma mensagem informando que não há coordenadores
        elements.append(Paragraph("<i>Não há coordenadores cadastrados.</i>", style_normal))
        elements.append(Spacer(1, 0.3 * inch))
    
    # 3. Necessidade e Atuação de Tutores
    elements.append(Paragraph("<b>3. NECESSIDADE E ATUAÇÃO DE TUTORES</b>", style_normal))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Perguntas sobre tutores
    perguntas = [
        "a. Há necessidade de Tutor(es)? <b>Sim</b>",
        "b. Há tutor(es) atuando atualmente? <b>Sim</b>"
    ]
    
    for pergunta in perguntas:
        elements.append(Paragraph(pergunta, style_normal))
        elements.append(Spacer(1, 0.1 * inch))
    
    elements.append(Spacer(1, 0.2 * inch))
    
    # Tabela de tutores
    headers = ["Nome Completo", "Quantidade de Estudantes Atendidos", "E-mail", "Contato Telefônico", "Observação"]
    data = [headers]
    
    tutores = buscar_tutores(cursor)
    for tutor in tutores:
        row = [
            tutor['nome'],
            str(tutor['total_alunos']),
            tutor['email'] or "---",
            tutor['telefone'] or "---",
            tutor['observacao'] or "---"
        ]
        data.append(row)
    
    if len(data) > 1:
        table_tutores = Table(data)
        table_tutores.setStyle(style_padrao)
        elements.append(table_tutores)
    else:
        elements.append(Paragraph("<i>Não há tutores cadastrados.</i>", style_normal))
    
    elements.append(Spacer(1, 0.3 * inch))
    
    # 4. Gestão da Escola
    elements.append(Paragraph("<b>4. GESTÃO DA ESCOLA</b>", style_normal))
    elements.append(Spacer(1, 0.1 * inch))
    
    # # Adiciona as perguntas sobre gestão
    # perguntas = [
    #     "a. Gestor(a) Geral:",
    #     "b. Gestor(a) Adjunto(s):",
    #     "c. Contatos Atualizados:",
    #     "   i. E-mail atualizado",
    #     "   ii. Contato telefônico atualizado"
    # ]
    
    # for pergunta in perguntas:
    #     elements.append(Paragraph(pergunta, style_normal))
    #     elements.append(Spacer(1, 0.1 * inch))
    
    # elements.append(Spacer(1, 0.2 * inch))
    
    # Tabela de gestores
    headers = ["Nome Completo", "Cargo", "E-mail", "Telefone"]
    data = [headers]
    
    for gestor in gestores:
        # Identifica o cargo baseado no nome
        if gestor['nome'] == "Rosiane de Jesus Santos Melo":
            cargo = "Gestora Adjunta"
        else:
            cargo = "Gestora Geral"
            
        row = [
            gestor['nome'],
            cargo,
            gestor['email'] or "---",
            gestor['telefone'] or "---"
        ]
        data.append(row)
    
    table_gest = Table(data)
    table_gest.setStyle(style_padrao)
    elements.append(table_gest)
    
    # Gera o PDF
    doc.build(elements)
    
    # Fechar conexão com o banco de dados
    try:
        cast(Any, cursor).close()
    except Exception:
        pass
    try:
        cast(Any, conn).close()
    except Exception:
        pass
    
    # Salvar e abrir o PDF
    buffer.seek(0)
    try:
        saved_path = salvar_e_abrir_pdf(buffer)
        return saved_path
    except Exception as e:
        raise RuntimeError(f"Erro ao salvar PDF: {e}")
    finally:
        try:
            buffer.close()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        saved_path = gerar_levantamento_necessidades()
        print(f"PDF gerado com sucesso: {saved_path}")
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")
        import traceback
        traceback.print_exc()
