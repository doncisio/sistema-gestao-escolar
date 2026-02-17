"""Relatórios diversos: crachás, pendências, movimentação, matrículas, reunião."""

import os
import sys
from typing import Optional, Any, cast, Tuple

from src.core.config_logs import get_logger
from src.services.reports._utils import _find_image_in_repo, _ensure_legacy_module

logger = get_logger(__name__)


def gerar_crachas_para_todos_os_alunos() -> str:
    """Executa a geração de crachás usando o módulo ``gerar_cracha``."""
    from src.services import cracha_service
    return cracha_service.gerar_crachas_todos_alunos()


def gerar_relatorio_pendencias(bimestre: str, nivel_ensino: str, ano_letivo: int, escola_id: int = 60) -> bool:
    """Encapsula a geração do relatório de pendências."""
    try:
        from src.relatorios.relatorio_pendencias import gerar_pdf_pendencias  # type: ignore
    except ImportError:
        logger.exception("Não foi possível importar relatorio_pendencias")
        raise

    resultado = gerar_pdf_pendencias(
        bimestre=bimestre,
        nivel_ensino=nivel_ensino,
        ano_letivo=ano_letivo,
        escola_id=escola_id
    )
    return bool(resultado)


def gerar_relatorio_movimentacao_mensal(numero_mes: int) -> bool:
    """Encapsula o gerador de movimentação mensal."""
    try:
        _mov = _ensure_legacy_module('movimentomensal', required=['relatorio_movimentacao_mensal'], candidate_filename='movimentomensal.py')
    except Exception:
        logger.exception("Módulo 'movimentomensal' não disponível para gerar relatório de movimentação mensal")
        raise

    resultado = _mov.relatorio_movimentacao_mensal(numero_mes)
    try:
        return bool(resultado)
    except Exception:
        return True


def gerar_relatorio_matriculas(escola_id: Optional[int] = None, ano_letivo: Optional[int] = None, *args, **kwargs) -> Tuple[bool, Optional[Any]]:
    """Wrapper compatível para geração de relatório de matrículas."""
    _mod = sys.modules.get('relatorio_matriculas') or sys.modules.get('gerar_relatorio_matriculas')
    if _mod is not None:
        if hasattr(_mod, 'gerar_relatorio_matriculas'):
            resultado = cast(Any, _mod).gerar_relatorio_matriculas(escola_id=escola_id, ano_letivo=ano_letivo, *args, **kwargs)
            if isinstance(resultado, tuple):
                success = bool(resultado[0]) if len(resultado) > 0 else True
                data = resultado[1] if len(resultado) > 1 else None
                return success, data
            if isinstance(resultado, dict) or isinstance(resultado, list) or isinstance(resultado, str):
                return True, resultado
            if isinstance(resultado, bool):
                return resultado, None
            return bool(resultado), None
        raise AttributeError("Módulo injetado não possui 'gerar_relatorio_matriculas'")

    try:
        _leg = _ensure_legacy_module('relatorio_matriculas', candidate_filename='relatorio_matriculas.py')
        if hasattr(_leg, 'gerar_relatorio_matriculas'):
            resultado = cast(Any, _leg).gerar_relatorio_matriculas(escola_id=escola_id, ano_letivo=ano_letivo, *args, **kwargs)
            if isinstance(resultado, tuple):
                success = bool(resultado[0]) if len(resultado) > 0 else True
                data = resultado[1] if len(resultado) > 1 else None
                return success, data
            if isinstance(resultado, dict) or isinstance(resultado, list) or isinstance(resultado, str):
                return True, resultado
            if isinstance(resultado, bool):
                return resultado, None
            return bool(resultado), None
    except Exception:
        pass

    return True, None


def gerar_lista_reuniao() -> bool:
    """Wrapper testável para ``gerar_lista_reuniao``."""
    _mod = sys.modules.get('gerar_lista_reuniao')
    if _mod is not None:
        if hasattr(_mod, 'gerar_lista_reuniao'):
            cast(Any, _mod).gerar_lista_reuniao()
            return True
        raise AttributeError("Módulo 'gerar_lista_reuniao' injetado não possui 'gerar_lista_reuniao'")

    try:
        return _impl_gerar_lista_reuniao()
    except Exception:
        try:
            _mod = _ensure_legacy_module('gerar_lista_reuniao', required=['gerar_lista_reuniao'], candidate_filename='gerar_lista_reuniao.py')
        except Exception:
            logger.exception("Módulo 'gerar_lista_reuniao' não disponível para gerar lista de reunião")
            raise

        if not hasattr(_mod, 'gerar_lista_reuniao'):
            raise AttributeError("Módulo 'gerar_lista_reuniao' não possui 'gerar_lista_reuniao'")

        cast(Any, _mod).gerar_lista_reuniao()
        return True


# ---------------------------------------------------------------------------
# Implementação migrada
# ---------------------------------------------------------------------------


def _impl_gerar_lista_reuniao(dados_aluno=None, ano_letivo: Optional[int] = None, out_dir: Optional[str] = None, pastas_turmas=None, criar_pastas_func=None, adicionar_cabecalho_func=None) -> bool:
    """Implementação migrada do gerador ``gerar_lista_reuniao``."""
    import pandas as pd
    import io
    import datetime
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    from src.services.utils.pdf import salvar_e_abrir_pdf, create_pdf_buffer

    if dados_aluno is None:
        if ano_letivo is None:
            ano_letivo = 2025
        try:
            from src.relatorios.listas.lista_atualizada import fetch_student_data
            dados_aluno = fetch_student_data(ano_letivo)
        except Exception:
            logger.exception('Não foi possível obter dados dos alunos para gerar_lista_reuniao')
            raise

    if not dados_aluno:
        logger.info('Nenhum dado de aluno encontrado para gerar_lista_reuniao')
        return False

    df = pd.DataFrame(dados_aluno)

    if criar_pastas_func:
        try:
            criar_pastas_func()
        except Exception:
            logger.exception('Falha ao criar pastas via criar_pastas_func')

    diretorio_principal = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    figura_superior = _find_image_in_repo('logosemed.png') or ''
    figura_inferior = _find_image_in_repo('logopaco.jpg') or ''

    cabecalho = [
        "PREFEITURA MUNICIPAL DE PAÇO DO LUMIAR",
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>EM PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 06.003.636/0001-73</b>"
    ]

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

    accept_all = pastas_turmas is None

    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        nome_turma_completo = f"{nome_serie} {nome_turma}" if nome_turma else nome_serie

        if (not accept_all) and (nome_turma_completo not in pastas_turmas):
            logger.info(f"Turma '{nome_turma_completo}' não mapeada em pastas_turmas — pulando")
            continue

        doc, buffer = create_pdf_buffer(
            pagesize=landscape(letter),
            topMargin=18,
            bottomMargin=18
        )
        elements = []

        if adicionar_cabecalho_func:
            try:
                adicionar_cabecalho_func(elements, cabecalho, figura_superior, figura_inferior)
            except Exception:
                logger.exception('Falha ao executar adicionar_cabecalho_func')
        else:
            try:
                import gerar_lista_reuniao as legacy  # type: ignore
                if hasattr(legacy, 'adicionar_cabecalho'):
                    legacy.adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
            except Exception:
                pass

        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph("<b>LISTA PARA REUNIÃO</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
        elements.append(Spacer(1, 2.5 * inch))
        elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
        elements.append(PageBreak())

        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']

        if adicionar_cabecalho_func:
            try:
                adicionar_cabecalho_func(elements, cabecalho, figura_superior, figura_inferior, 11)
            except Exception:
                logger.exception('Falha ao executar adicionar_cabecalho_func (pagina)')

        elements.append(Spacer(1, 0.125 * inch))
        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=12, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))

        elements.append(Paragraph("<b>PAUTA DA REUNIÃO</b>", ParagraphStyle(name='PautaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.2 * inch))
        for item in pauta_items:
            elements.append(Paragraph(f"• {item}", ParagraphStyle(name='PautaItem', fontSize=11, leftIndent=20)))
            elements.append(Spacer(1, 0.1 * inch))

        elements.append(Spacer(1, 0.2 * inch))

        data = [['Nº', 'Nome', 'Telefone', 'Assinatura do Responsável', 'Parentesco']]
        for row_num, (index, row) in enumerate(turma_df.iterrows(), start=1):
            nome = row.get('NOME DO ALUNO') if isinstance(row, dict) else row['NOME DO ALUNO']
            nome_str = str(nome) if pd.notnull(nome) else ""
            telefones_str = ''
            assinatura = ''
            parentesco = ''
            data.append([str(row_num), nome_str, telefones_str, assinatura, parentesco])

        table = Table(data, colWidths=[0.4 * inch, 3 * inch, 1.5 * inch, 3 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        elements.append(PageBreak())

        doc.build(elements)

        if out_dir:
            filename = os.path.join(out_dir, f"{nome_turma_completo}_Reuniao.pdf")
        else:
            filename = None

        try:
            from src.services.utils.pdf import salvar_e_abrir_pdf as salvar_helper

            saved_path = None
            if salvar_helper is not None:
                try:
                    saved_path = cast(Any, salvar_helper)(buffer, filename) if filename is not None else cast(Any, salvar_helper)(buffer)
                except TypeError:
                    try:
                        saved_path = cast(Any, salvar_helper)(buffer)
                    except Exception:
                        saved_path = None
                except Exception:
                    logger.exception('Helper de PDF disponível, mas falhou ao salvar em memória')
                    saved_path = None

            if not saved_path:
                import tempfile
                try:
                    if filename:
                        temp_path = filename
                    else:
                        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                        temp_path = tf.name
                        tf.close()

                    buffer.seek(0)
                    with open(temp_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    saved_path = temp_path
                except Exception:
                    logger.exception('Falha ao escrever PDF temporário para registro')
                    saved_path = None

            if saved_path:
                try:
                    from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
                    from src.utils.utilitarios.tipos_documentos import TIPO_LISTA_REUNIAO
                    finalidade = 'Secretaria'
                    descricao = f'Lista de Reunião - {nome_turma_completo}'
                    sucesso, mensagem, link = salvar_documento_sistema(
                        saved_path,
                        TIPO_LISTA_REUNIAO,
                        aluno_id=None,
                        funcionario_id=1,
                        finalidade=finalidade,
                        descricao=descricao,
                    )
                    if sucesso:
                        logger.info('Documento registrado no sistema: %s', link)
                    else:
                        logger.warning('Falha ao registrar documento no sistema: %s', mensagem)
                except Exception:
                    logger.exception('Erro ao tentar registrar documento no sistema de documentos')

        except Exception:
            logger.exception('Erro inesperado ao salvar/registrar PDF')

    return True
