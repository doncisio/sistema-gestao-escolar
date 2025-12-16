import os
import sys
from typing import List, Dict, Any


# Permite executar este arquivo diretamente (ex: `python alunos_9ano_historico.py`) quando
# o package `src` não está no `PYTHONPATH`. Em ambientes normais o import abaixo funcionará.
try:
    from src.core.conexao import conectar_bd
    from src.core.config_logs import get_logger
except ModuleNotFoundError:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from src.core.conexao import conectar_bd
    from src.core.config_logs import get_logger

logger = get_logger(__name__)


def _obter_ano_id(cursor, ano_letivo: int | None) -> int:
    if ano_letivo is None:
        cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else 1

    # se foi passado um número de ano (ex: 2025)
    if isinstance(ano_letivo, int) and ano_letivo > 1900:
        cursor.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = %s LIMIT 1", (ano_letivo,))
        row = cursor.fetchone()
        if row:
            return row[0]

    # tentar como id
    try:
        cursor.execute("SELECT id FROM AnosLetivos WHERE id = %s LIMIT 1", (ano_letivo,))
        row = cursor.fetchone()
        if row:
            return row[0]
    except Exception:
        pass

    # fallback
    cursor.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
    row = cursor.fetchone()
    return row[0] if row else 1


def _serie_id_para_nome(serie_id: int) -> str:
    """Converte serie_id (3..10) para nome legível: 3->'1º Ano', 4->'2º Ano', ..."""
    try:
        if serie_id is None:
            return ''
        offset = serie_id - 3
        if 0 <= offset <= 7:
            return f"{offset+1}º Ano"
    except Exception:
        pass
    return str(serie_id)


def buscar_alunos_9ano_historico(ano_letivo: int | None = None, escola_id: int = 60) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retorna alunos matriculados e ativos no 9º ano divididos em:
      - 'completo': aqueles que possuem histórico (qualquer escola) para todas as séries 1º ao 8º (serie_id 3..10)
      - 'com_pendencias': aqueles que têm ausência de histórico em pelo menos uma das séries 1..8

    Cada item contém: aluno_id, nome, turma_id, turma_nome, serie_id_atual, series_faltantes (lista de serie_id)
    """
    conn = conectar_bd()
    if conn is None:
        logger.error("Não foi possível conectar ao banco de dados")
        return {'completo': [], 'com_pendencias': []}

    try:
        cursor = conn.cursor()

        ano_id = _obter_ano_id(cursor, ano_letivo)

        # obter ids de séries que representem 9º ano (mesma heurística usada em outros módulos)
        cursor.execute("SELECT id FROM series WHERE nome LIKE %s OR nome LIKE %s OR nome LIKE %s", ('9%', '%9º%', '%9º %'))
        rows = cursor.fetchall()
        series_9_ids = [r[0] for r in rows] if rows else []

        # buscar alunos ativos em turmas de 9º ano
        if series_9_ids:
            placeholders = ','.join(['%s'] * len(series_9_ids))
            query = (
                f"SELECT DISTINCT a.id AS aluno_id, a.nome AS aluno_nome, t.id AS turma_id, t.nome AS turma_nome, t.serie_id, s.nome AS serie_nome "
                f"FROM Alunos a JOIN Matriculas m ON a.id = m.aluno_id JOIN Turmas t ON m.turma_id = t.id LEFT JOIN series s ON t.serie_id = s.id "
                f"WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND t.serie_id IN ({placeholders}) AND (t.escola_id = %s OR a.escola_id = %s)"
            )
            params = [ano_id] + series_9_ids + [escola_id, escola_id]
            cursor.execute(query, params)
        else:
            # fallback por nome
            cursor.execute(
                """
                SELECT DISTINCT a.id AS aluno_id, a.nome AS aluno_nome, t.id AS turma_id, t.nome AS turma_nome, t.serie_id, s.nome AS serie_nome
                FROM Alunos a
                JOIN Matriculas m ON a.id = m.aluno_id
                JOIN Turmas t ON m.turma_id = t.id
                LEFT JOIN series s ON t.serie_id = s.id
                WHERE m.ano_letivo_id = %s AND m.status = 'Ativo' AND (s.nome LIKE '9%%' OR s.nome LIKE '%%9º%%' OR s.nome LIKE '%%9º %') AND (t.escola_id = %s OR a.escola_id = %s)
                """,
                (ano_id, escola_id, escola_id)
            )

        alunos_rows = cursor.fetchall()
        if not alunos_rows:
            return {'completo': [], 'com_pendencias': []}

        # normalizar lista de ids
        aluno_ids = [r[0] if not isinstance(r, dict) else r.get('aluno_id') for r in alunos_rows]

        # séries que correspondem a 1º ao 8º conforme convenção do sistema: serie_id 3..10
        required_serie_ids = list(range(3, 11))

        # buscar histórico escolar para esses alunos nas séries 3..10
        placeholders = ','.join(['%s'] * len(aluno_ids))
        cursor.execute(
            f"SELECT DISTINCT aluno_id, serie_id FROM historico_escolar WHERE aluno_id IN ({placeholders}) AND serie_id BETWEEN %s AND %s",
            tuple(aluno_ids) + (3, 10)
        )
        historico_rows = cursor.fetchall()

        # mapear aluno_id -> set(serie_id)
        historico_map: Dict[int, set] = {}
        for row in historico_rows:
            aluno_id = row[0]
            serie_id = row[1]
            historico_map.setdefault(aluno_id, set()).add(serie_id)

        completo = []
        com_pendencias = []

        for r in alunos_rows:
            if isinstance(r, dict):
                aluno_id = r.get('aluno_id')
                nome = r.get('aluno_nome')
                turma_id = r.get('turma_id')
                turma_nome = r.get('turma_nome')
                serie_atual = r.get('serie_id')
                serie_nome = r.get('serie_nome')
            else:
                # ordem: aluno_id, aluno_nome, turma_id, turma_nome, serie_id
                aluno_id = r[0]
                nome = r[1]
                turma_id = r[2] if len(r) > 2 else None
                turma_nome = r[3] if len(r) > 3 else None
                serie_atual = r[4] if len(r) > 4 else None
                serie_nome = r[5] if len(r) > 5 else None

            presentes = historico_map.get(aluno_id, set())
            faltantes = [s for s in required_serie_ids if s not in presentes]

            item = {
                'aluno_id': aluno_id,
                'nome': nome,
                'turma_id': turma_id,
                'turma_nome': turma_nome,
                'serie_id_atual': serie_atual,
                'serie_nome': serie_nome,
                'series_faltantes': faltantes
            }

            if not faltantes:
                completo.append(item)
            else:
                com_pendencias.append(item)

        return {'completo': completo, 'com_pendencias': com_pendencias}

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    # Chamar explicitamente o ano letivo mais usado nos exemplos para consistência
    ano = 2025
    resultado = buscar_alunos_9ano_historico(ano, 60)
    completo = resultado.get('completo', []) if resultado else []
    pendencias = resultado.get('com_pendencias', []) if resultado else []
    print(f"Alunos com histórico completo: {len(completo)}")
    print(f"Alunos com pendências: {len(pendencias)}")

    # Imprime detalhes das pendências com mapeamento legível
    for item in pendencias:
        aluno_id = item.get('aluno_id')
        nome = item.get('nome')
        series_ids = item.get('series_faltantes') or []
        series_ids_str = '[' + ','.join(str(s) for s in series_ids) + ']' if series_ids else '[]'
        series_nomes = ', '.join(_serie_id_para_nome(s) for s in series_ids)
        if series_nomes:
            print(f"{nome} (aluno_id={aluno_id}) está em com_pendencias com series_faltantes = {series_ids_str}, ou seja, faltam os históricos de {series_nomes}.")
        else:
            print(f"{nome} (aluno_id={aluno_id}) está em com_pendencias com series_faltantes = {series_ids_str}.")





def gerar_lista_9ano_historico_pdf(ano_letivo: int | None = None, escola_id: int = 60) -> str | None:
    """Gera um PDF com a lista de alunos do 9º ano e suas pendências de histórico.

    Retorna o caminho do arquivo salvo quando possível, ou None.
    """
    # imports locais para permitir execução direta do script mesmo sem PYTHONPATH
    import io
    import datetime
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.colors import black, white, grey
    except Exception:
        # reportlab pode não estar instalado no ambiente de teste
        logger.exception('ReportLab não disponível para gerar PDF')
        return None

    try:
        from src.core.config import get_image_path
    except Exception:
        get_image_path = None

    try:
        from src.relatorios.gerar_pdf import salvar_e_abrir_pdf
    except Exception:
        salvar_e_abrir_pdf = None

    resultado = buscar_alunos_9ano_historico(ano_letivo, escola_id)
    if not resultado:
        logger.error("Nenhum resultado retornado pela busca.")
        return None

    todos = resultado['completo'] + resultado['com_pendencias']
    # Constrói tabela de saída
    data: List[List[Any]] = [['Nº', 'Aluno', 'Turma', 'Séries faltantes']]
    for idx, item in enumerate(todos, start=1):
        faltantes_ids = item.get('series_faltantes') or []
        # compactar intervalos consecutivos
        def _compact(ids: List[int]) -> str:
            if not ids:
                return ''
            ids = sorted(ids)
            ranges = []
            start = prev = ids[0]
            for x in ids[1:]:
                if x == prev + 1:
                    prev = x
                    continue
                # finalizar intervalo
                if start == prev:
                    ranges.append((start, start))
                else:
                    ranges.append((start, prev))
                start = prev = x
            # último intervalo
            if start == prev:
                ranges.append((start, start))
            else:
                ranges.append((start, prev))

            parts = []
            for a, b in ranges:
                if a == b:
                    parts.append(_serie_id_para_nome(a))
                else:
                    parts.append(f"{_serie_id_para_nome(a).split()[0]} ao {_serie_id_para_nome(b)}")
            return ', '.join(parts)

        faltantes_texto = _compact(faltantes_ids)
        turma_text = f"{item.get('serie_nome') or ''} {item.get('turma_nome') or ''}".strip()
        data.append([
            idx,
            item.get('nome') or '',
            turma_text,
            faltantes_texto
        ])

    # Cria PDF em buffer e usa A4 com margens reduzidas
    buffer = io.BytesIO()
    left_margin = 18
    right_margin = 18
    top_margin = 12
    bottom_margin = 12
    page_size = A4
    doc = SimpleDocTemplate(buffer, pagesize=page_size, leftMargin=left_margin, rightMargin=right_margin, topMargin=top_margin, bottomMargin=bottom_margin)

    styles = {
        'header': ParagraphStyle('header', fontSize=12, alignment=1),
        'title': ParagraphStyle('title', fontSize=16, alignment=1),
    }

    elements = []
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>LISTA - ALUNOS 9º ANO (HISTÓRICO)</b>",
        f"Ano letivo: {ano_letivo or ''}"
    ]
    figura_inferior = str(get_image_path('logopaco.png')) if get_image_path else None
    if figura_inferior:
        try:
            from reportlab.platypus import Image
            img = Image(figura_inferior, width=3 * inch, height=0.7 * inch)
            elements.append(img)
        except Exception:
            pass

    elements.append(Paragraph('<br/>'.join(cabecalho), styles['header']))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Paragraph(f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['header']))
    elements.append(Spacer(1, 0.25 * inch))

    # Calcula larguras dinâmicas para as 4 colunas (Nº, Aluno, Turma, Séries faltantes)
    page_width, _ = page_size
    usable_width = page_width - (left_margin + right_margin)
    col_props = [0.06, 0.46, 0.12, 0.36]
    col_widths = [usable_width * p for p in col_props]

    table = Table(data, colWidths=col_widths)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ])
    table.setStyle(table_style)
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    # tentar salvar usando helper comum
    saved_path = None
    try:
        if salvar_e_abrir_pdf:
            try:
                saved_path = salvar_e_abrir_pdf(buffer)
            except Exception:
                saved_path = None

        if not saved_path:
            import tempfile
            from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
            from src.utils.utilitarios.tipos_documentos import TIPO_LISTA_ATUALIZADA

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            try:
                tmp.write(buffer.getvalue())
                tmp.close()
                descricao = f"Lista 9º Ano - {ano_letivo or ''}"
                try:
                    salvar_documento_sistema(tmp.name, TIPO_LISTA_ATUALIZADA, funcionario_id=1, finalidade='Secretaria', descricao=descricao)
                    saved_path = tmp.name
                except Exception:
                    if salvar_e_abrir_pdf:
                        buffer.seek(0)
                        salvar_e_abrir_pdf(buffer)
            finally:
                pass
    finally:
        try:
            buffer.close()
        except Exception:
            pass

    return saved_path
