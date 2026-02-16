"""Relatórios de histórico escolar e séries faltantes."""

import os
import sys
from typing import Optional, Any, cast, Tuple

from src.core.config_logs import get_logger
from src.services.reports._utils import _ensure_legacy_module

logger = get_logger(__name__)


def gerar_historico_escolar(aluno_id: int) -> Tuple[bool, Optional[str]]:
    """Wrapper compatível para geração de histórico escolar."""
    _mod = sys.modules.get('gerar_historico_escolar') or sys.modules.get('historico_escolar')
    if _mod is not None:
        if hasattr(_mod, 'gerar_historico_escolar'):
            resultado = cast(Any, _mod).gerar_historico_escolar(aluno_id=aluno_id)
            if isinstance(resultado, tuple):
                return (bool(resultado[0]), resultado[1] if len(resultado) > 1 and isinstance(resultado[1], str) else None)
            if isinstance(resultado, str):
                return True, resultado
            return bool(resultado), None

    try:
        _leg = _ensure_legacy_module('historico_escolar', candidate_filename='historico_escolar.py')
        if hasattr(_leg, 'gerar_historico_escolar'):
            resultado = cast(Any, _leg).gerar_historico_escolar(aluno_id=aluno_id)
            if isinstance(resultado, tuple):
                return (bool(resultado[0]), resultado[1] if len(resultado) > 1 and isinstance(resultado[1], str) else None)
            if isinstance(resultado, str):
                return True, resultado
            return bool(resultado), None
    except Exception:
        pass

    return True, None


def gerar_relatorio_series_faltantes() -> bool:
    """Wrapper testável para ``gerar_relatorio_series_faltantes``."""
    _mod = sys.modules.get('gerar_relatorio_series_faltantes')
    if _mod is not None:
        if hasattr(_mod, 'gerar_relatorio_series_faltantes'):
            cast(Any, _mod).gerar_relatorio_series_faltantes()
            return True
        raise AttributeError("Módulo 'gerar_relatorio_series_faltantes' injetado não possui 'gerar_relatorio_series_faltantes'")

    try:
        return _impl_gerar_relatorio_series_faltantes()
    except Exception:
        try:
            _mod = _ensure_legacy_module('gerar_relatorio_series_faltantes', required=['gerar_relatorio_series_faltantes'], candidate_filename='gerar_relatorio_series_faltantes.py')
        except Exception:
            logger.exception("Módulo 'gerar_relatorio_series_faltantes' não disponível para gerar relatório")
            raise

        if not hasattr(_mod, 'gerar_relatorio_series_faltantes'):
            raise AttributeError("Módulo 'gerar_relatorio_series_faltantes' não possui 'gerar_relatorio_series_faltantes'")

        cast(Any, _mod).gerar_relatorio_series_faltantes()
        return True


def _impl_gerar_relatorio_series_faltantes(alunos_ativos=None, historico_lookup=None, out_dir: str = 'documentos_gerados') -> bool:
    """Implementação migrada do gerador ``gerar_relatorio_series_faltantes``."""
    import calendar
    import time
    try:
        from src.services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf
    except Exception:
        try:
            from src.relatorios.gerar_pdf import create_pdf_buffer, salvar_e_abrir_pdf
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para relatorio_series_faltantes')
            raise

    conn = None
    try:
        if alunos_ativos is None:
            try:
                from src.core.conexao import conectar_bd
                conn = conectar_bd()
            except Exception:
                conn = None

            if conn is None:
                raise RuntimeError('Não foi possível conectar ao BD para gerar relatorio_series_faltantes')

            cursor = conn.cursor(dictionary=True)
            try:
                query_alunos_ativos = """
                SELECT DISTINCT 
                    m.aluno_id,
                    al.nome as nome_aluno,
                    t.serie_id as serie_atual
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN alunos al ON al.id = m.aluno_id
                WHERE m.ano_letivo_id = %s 
                AND m.status = 'Ativo'
                ORDER BY t.serie_id, al.nome;
                """
                cursor.execute(query_alunos_ativos, (26,))
                alunos_ativos = cursor.fetchall()
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass

        if historico_lookup is None:
            historico_lookup = {}
            if conn is None:
                try:
                    from src.core.conexao import conectar_bd
                    conn = conectar_bd()
                except Exception:
                    conn = None

        def _get_field(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            try:
                return obj[key]
            except Exception:
                return None

            if conn is not None:
                cursor = conn.cursor(dictionary=True)
                try:
                    query_historico = """
                    SELECT 
                        h.aluno_id,
                        h.serie_id,
                        a.ano_letivo,
                        e.nome AS escola_nome,
                        e.municipio AS escola_municipio,
                        CASE
                            WHEN COUNT(h.media) = 0 AND COUNT(h.conceito) > 0 THEN 'Promovido(a)'
                            WHEN MIN(h.media) >= 48 THEN 'Promovido(a)'
                            WHEN MIN(h.media) < 48 THEN 'Retido(a)'
                        END AS situacao_final
                    FROM 
                        historico_escolar h
                    JOIN 
                        anosletivos a ON h.ano_letivo_id = a.id
                    JOIN 
                        escolas e ON h.escola_id = e.id
                    WHERE 
                        h.aluno_id = %s
                    GROUP BY 
                        h.aluno_id, h.serie_id, a.ano_letivo, e.nome, e.municipio;
                    """
                    for aluno in alunos_ativos:
                        aluno_id = _get_field(aluno, 'aluno_id')
                        cursor.execute(query_historico, (aluno_id,))
                        historico_lookup[aluno_id] = cursor.fetchall()
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass

        alunos_incompletos = []
        alunos_completos = []
        for aluno in alunos_ativos:
            aluno_id = aluno.get('aluno_id') if isinstance(aluno, dict) else None
            historico = historico_lookup.get(aluno_id, [])
            series_existentes = {registro['serie_id']: registro for registro in historico}
            serie_atual = aluno.get('serie_atual') if isinstance(aluno, dict) else None
            series_faltantes = []
            if serie_atual is None:
                continue
            for serie_id in range(3, serie_atual + 1):
                if serie_id not in series_existentes:
                    series_faltantes.append(serie_id)

            if series_faltantes:
                for serie_faltante in series_faltantes:
                    alunos_incompletos.append({
                        'aluno_id': aluno_id,
                        'nome_aluno': _get_field(aluno, 'nome_aluno'),
                        'serie_atual': serie_atual,
                        'serie_faltante': serie_faltante
                    })
            else:
                situacao_final = historico[-1]['situacao_final'] if historico else 'Sem histórico'
                alunos_completos.append({
                    'aluno_id': aluno_id,
                    'nome_aluno': _get_field(aluno, 'nome_aluno'),
                    'serie_atual': serie_atual,
                    'situacao_final': situacao_final
                })

        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import datetime
        timestamp = int(time.time())
        filename = os.path.join(out_dir, f"relatorio_series_faltantes_{timestamp}.pdf")

        doc, buffer = create_pdf_buffer()
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=30)
        subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontSize=14, spaceAfter=20, textColor=colors.HexColor('#444444'))

        elements.append(Paragraph("Relatório de Histórico Escolar", title_style))
        elements.append(Paragraph(f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
        elements.append(Spacer(1, 30))

        elements.append(Paragraph("Alunos com Histórico Incompleto", subtitle_style))
        elements.append(Spacer(1, 10))
        if alunos_incompletos:
            dados_incompleto = [['ID Aluno', 'Nome do Aluno', 'Série Atual', 'Série Faltante']]
            for a in alunos_incompletos:
                dados_incompleto.append([str(a['aluno_id']), a['nome_aluno'], str(a['serie_atual']), str(a['serie_faltante'])])
            table_incompleto = Table(dados_incompleto)
            table_incompleto.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9999')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table_incompleto)
        else:
            elements.append(Paragraph("Nenhum aluno com histórico incompleto encontrado.", styles['Normal']))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Alunos com Histórico Completo", subtitle_style))
        elements.append(Spacer(1, 10))
        if alunos_completos:
            dados_completo = [['ID Aluno', 'Nome do Aluno', 'Série Atual', 'Situação Final']]
            for a in alunos_completos:
                dados_completo.append([str(a['aluno_id']), a['nome_aluno'], str(a['serie_atual']), a['situacao_final']])
            table_completo = Table(dados_completo)
            table_completo.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#99FF99')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table_completo)
        else:
            elements.append(Paragraph("Nenhum aluno com histórico completo encontrado.", styles['Normal']))

        doc.build(elements)
        salvar_e_abrir_pdf(buffer)
        return True
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
