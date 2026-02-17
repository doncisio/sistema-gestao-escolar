"""Relatórios de boletim e notas."""

import os
import sys
import importlib
from typing import Optional, Any, cast, Tuple

from src.core.config_logs import get_logger
from src.services.reports._utils import _ensure_legacy_module

logger = get_logger(__name__)


def gerar_relatorio_avancado_com_assinatura(bimestre: str, nivel_ensino: str, ano_letivo: int,
                                            status_matricula, preencher_nulos: bool) -> bool:
    """Encapsula a chamada ao gerador de relatório de notas com assinatura."""
    _mod = sys.modules.get('NotaAta')
    if _mod is not None:
        if hasattr(_mod, 'gerar_relatorio_notas_com_assinatura'):
            return bool(cast(Any, _mod).gerar_relatorio_notas_com_assinatura(
                bimestre=bimestre,
                nivel_ensino=nivel_ensino,
                ano_letivo=ano_letivo,
                status_matricula=status_matricula,
                preencher_nulos=preencher_nulos
            ))
        raise AttributeError("Módulo 'NotaAta' injetado não possui 'gerar_relatorio_notas_com_assinatura'")

    try:
        return _impl_gerar_relatorio_notas_com_assinatura(
            bimestre=bimestre,
            nivel_ensino=nivel_ensino,
            ano_letivo=ano_letivo,
            status_matricula=status_matricula,
            preencher_nulos=preencher_nulos
        )
    except NotImplementedError:
        pass
    except Exception:
        pass

    try:
        _mod = _ensure_legacy_module('NotaAta', required=['gerar_relatorio_notas_com_assinatura'], candidate_filename='NotaAta.py')
    except Exception:
        logger.exception("Não foi possível carregar NotaAta para gerar relatório avançado")
        raise

    if not hasattr(_mod, 'gerar_relatorio_notas_com_assinatura'):
        raise AttributeError("Módulo 'NotaAta' não possui 'gerar_relatorio_notas_com_assinatura'")

    resultado = cast(Any, _mod).gerar_relatorio_notas_com_assinatura(
        bimestre=bimestre,
        nivel_ensino=nivel_ensino,
        ano_letivo=ano_letivo,
        status_matricula=status_matricula,
        preencher_nulos=preencher_nulos
    )
    return bool(resultado)


def gerar_relatorio_notas(*args, **kwargs) -> Tuple[bool, Optional[Any]]:
    """Encapsula a chamada ao gerador de relatórios de notas (``NotaAta.gerar_relatorio_notas``)."""
    try:
        _mod = _ensure_legacy_module('NotaAta', required=['gerar_relatorio_notas'], candidate_filename='NotaAta.py')
    except Exception:
        logger.exception("Módulo 'NotaAta' não disponível para gerar relatório de notas")
        raise

    if not hasattr(_mod, 'gerar_relatorio_notas'):
        raise AttributeError("Módulo 'NotaAta' não possui 'gerar_relatorio_notas'")

    resultado = _mod.gerar_relatorio_notas(*args, **kwargs)
    try:
        if isinstance(resultado, tuple):
            success = bool(resultado[0]) if len(resultado) > 0 else True
            data = resultado[1] if len(resultado) > 1 else None
            return success, data
        if isinstance(resultado, str):
            return True, resultado
        if isinstance(resultado, bool):
            return resultado, None
        if resultado is None:
            return True, None
        return bool(resultado), None
    except Exception:
        return True, None


def gerar_boletim(aluno_id: int, ano_letivo_id: Optional[int]) -> Tuple[bool, Optional[str]]:
    """Gera o boletim para o aluno especificado delegando para ``boletim.boletim``."""
    try:
        from src.relatorios.boletim import boletim as _gerar_boletim  # type: ignore
    except ImportError:
        logger.exception("Não foi possível importar módulo 'boletim' para gerar boletim")
        raise

    try:
        _m = sys.modules.get('boletim')
        if _m is not None:
            importlib.reload(_m)
    except Exception:
        pass

    resultado = _gerar_boletim(aluno_id, ano_letivo_id)

    try:
        if isinstance(resultado, tuple):
            success = bool(resultado[0]) if len(resultado) > 0 else True
            path = resultado[1] if len(resultado) > 1 and isinstance(resultado[1], str) else None
            return success, path
        if isinstance(resultado, str):
            return True, resultado
        if isinstance(resultado, bool):
            return resultado, None
        if resultado is None:
            return True, None
        return bool(resultado), None
    except Exception:
        return True, None


def gerar_boletim_interno(aluno_id: int, ano_letivo_id: int) -> bool:
    """Alias para ``gerar_boletim`` — retorna apenas booleano."""
    sucesso, _caminho = gerar_boletim(aluno_id, ano_letivo_id)
    return bool(sucesso)


def gerar_lista_notas() -> bool:
    """Encapsula a chamada ao gerador de lista de notas (``Lista_notas.lista_notas``)."""
    _mod = sys.modules.get('Lista_notas')
    if _mod is not None:
        if hasattr(_mod, 'lista_notas'):
            cast(Any, _mod).lista_notas()
            return True
        raise AttributeError("Módulo 'Lista_notas' injetado não possui 'lista_notas'")

    try:
        return _impl_lista_notas()
    except NotImplementedError:
        pass
    except Exception:
        pass

    try:
        _mod = _ensure_legacy_module('Lista_notas', required=['lista_notas'], candidate_filename='Lista_notas.py')
    except Exception:
        logger.exception("Módulo 'Lista_notas' não disponível para gerar lista de notas")
        raise

    if not hasattr(_mod, 'lista_notas'):
        raise AttributeError("Módulo 'Lista_notas' não possui 'lista_notas'")

    cast(Any, _mod).lista_notas()
    return True


# ---------------------------------------------------------------------------
# Implementações migradas
# ---------------------------------------------------------------------------


def _impl_gerar_relatorio_notas_com_assinatura(*args, **kwargs) -> bool:
    """Implementação migrada e testável para gerar_relatorio_notas_com_assinatura."""
    bimestre = kwargs.get('bimestre') if 'bimestre' in kwargs else (args[0] if len(args) > 0 else None)
    nivel_ensino = kwargs.get('nivel_ensino') if 'nivel_ensino' in kwargs else (args[1] if len(args) > 1 else None)
    ano_letivo = kwargs.get('ano_letivo') if 'ano_letivo' in kwargs else (args[2] if len(args) > 2 else None)
    status_matricula = kwargs.get('status_matricula')
    preencher_nulos = kwargs.get('preencher_nulos')

    dados = kwargs.get('dados')

    if dados is None:
        raise NotImplementedError("_impl_gerar_relatorio_notas_com_assinatura requer 'dados' injetados")

    from src.services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf

    import tempfile
    import pandas as pd

    try:
        legacy = _ensure_legacy_module('NotaAta', candidate_filename='NotaAta.py')
    except Exception:
        raise NotImplementedError("Não foi possível carregar módulo 'NotaAta' para implementação in-process")

    nivel = nivel_ensino or kwargs.get('nivel_ensino')
    if isinstance(nivel, str):
        nivel = nivel
    else:
        nivel = str(nivel)

    preencher_nulos_flag = preencher_nulos if 'preencher_nulos' in locals() else kwargs.get('preencher_nulos', False)

    dados = dados if 'dados' in locals() else kwargs.get('dados')

    if dados is None:
        raise NotImplementedError("_impl_gerar_relatorio_notas_com_assinatura requer 'dados' injetados para operar in-process")

    try:
        if nivel in ("finais", "fundamental_finais"):
            disciplinas = legacy.obter_disciplinas_finais()
            tipo_ensino = 'fundamental_finais'
        else:
            disciplinas = legacy.obter_disciplinas_iniciais()
            tipo_ensino = 'fundamental_iniciais'
    except Exception:
        disciplinas = []
        tipo_ensino = 'fundamental_iniciais'

    df = None
    try:
        df = legacy.processar_dados_alunos(dados, disciplinas, preencher_nulos_flag)
    except Exception:
        try:
            df = pd.DataFrame(dados)
        except Exception:
            df = None

    try:
        out_dir = kwargs.get('out_dir')
        if out_dir:
            tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=out_dir)
            tmpfile.close()
            filename = tmpfile.name
        else:
            fd, filename = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)

        need_in_memory = False
        if df is None:
            need_in_memory = True
        else:
            required_cols = {'NOME_SERIE', 'NOME_TURMA', 'TURNO'}
            if not required_cols.issubset(set(df.columns)):
                need_in_memory = True

        if not need_in_memory and hasattr(legacy, 'gerar_documento_pdf_com_assinatura'):
            legacy.gerar_documento_pdf_com_assinatura(df, kwargs.get('bimestre', ''), filename, disciplinas, tipo_ensino, kwargs.get('ano_letivo'))
        elif not need_in_memory and hasattr(legacy, 'gerar_documento_pdf'):
            legacy.gerar_documento_pdf(df, kwargs.get('bimestre', ''), filename, disciplinas, tipo_ensino, kwargs.get('ano_letivo'))
        else:
            from src.services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf
            from reportlab.platypus import Paragraph, Spacer
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.units import inch

            doc, buffer = create_pdf_buffer()
            elements = []
            elements.append(Paragraph(f"Relatório de Notas - {nivel} - {kwargs.get('ano_letivo')}", ParagraphStyle(name='Title', fontSize=14)))
            elements.append(Spacer(1, 0.2 * inch))
            try:
                doc.build(elements)
            except Exception:
                pass

            saved_path = None
            try:
                from src.services.utils.pdf import salvar_e_abrir_pdf as salvar_helper

                if salvar_helper is not None:
                    try:
                        if 'filename' in locals() and filename:
                            saved_path = cast(Any, salvar_helper)(buffer, filename)
                        else:
                            saved_path = cast(Any, salvar_helper)(buffer)
                    except TypeError:
                        try:
                            saved_path = cast(Any, salvar_helper)(buffer)
                        except Exception:
                            saved_path = None
                    except Exception:
                        logger.exception('Helper de PDF disponível, mas falhou ao salvar em memória')
                        saved_path = None

                import os as _os
                import tempfile as _temp
                if not saved_path:
                    if 'filename' in locals() and filename and _os.path.exists(filename):
                        saved_path = filename
                    else:
                        try:
                            tf = _temp.NamedTemporaryFile(delete=False, suffix='.pdf')
                            tf.close()
                            buffer.seek(0)
                            with open(tf.name, 'wb') as f:
                                f.write(buffer.getvalue())
                            saved_path = tf.name
                        except Exception:
                            logger.exception('Falha ao escrever PDF temporário para registro')
                            saved_path = None

                if saved_path:
                    try:
                        from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
                        from src.utils.utilitarios.tipos_documentos import TIPO_LISTA_NOTAS
                        finalidade = 'Secretaria'
                        descricao = f'Relatório de Notas - {tipo_ensino} - {kwargs.get("ano_letivo")}'
                        sucesso, mensagem, link = salvar_documento_sistema(
                            saved_path,
                            TIPO_LISTA_NOTAS,
                            aluno_id=None,
                            funcionario_id=1,
                            finalidade=finalidade,
                            descricao=descricao,
                        )
                        if sucesso:
                            logger.info('Documento registrado no sistema: %s', link)
                            try:
                                if _os.path.exists(saved_path) and _os.path.dirname(saved_path) == _temp.gettempdir():
                                    _os.remove(saved_path)
                            except Exception:
                                pass
                        else:
                            logger.warning('Falha ao registrar documento no sistema: %s', mensagem)
                    except Exception:
                        logger.exception('Erro ao tentar registrar documento no sistema de documentos')
            except Exception:
                logger.exception('Erro inesperado ao salvar/registrar PDF (relatorio_notas)')

        return True
    except NotImplementedError:
        raise
    except Exception:
        logger.exception('Falha na implementação in-process de gerar_relatorio_notas_com_assinatura')
        raise


def _impl_lista_notas(dados_aluno=None, ano_letivo: Optional[int] = None, out_dir: Optional[str] = None) -> bool:
    """Implementação migrada para ``Lista_notas.lista_notas``."""
    import io
    import datetime
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    from src.services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf

    if dados_aluno is None:
        if ano_letivo is None:
            ano_letivo = datetime.datetime.now().year
        try:
            from src.relatorios.listas.lista_atualizada import fetch_student_data
            dados_aluno = fetch_student_data(ano_letivo)
        except Exception:
            raise NotImplementedError("_impl_lista_notas não conseguiu obter dados; usar fallback legado")

    if not dados_aluno:
        logger.info('Nenhum dado de aluno encontrado para lista_notas (impl)')
        return False

    doc, buffer = create_pdf_buffer()
    elements = []
    elements.append(Paragraph('<b>LISTA DE NOTAS</b>', ParagraphStyle(name='Title', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.2 * inch))

    table_data = [['Nº', 'Nome do Aluno']]
    for i, aluno in enumerate(dados_aluno, start=1):
        nome = None
        if isinstance(aluno, dict):
            nome = aluno.get('NOME DO ALUNO') or aluno.get('nome_aluno')
        else:
            try:
                nome = aluno['NOME DO ALUNO']
            except Exception:
                nome = str(aluno)
        nome_str = str(nome) if nome is not None else ''
        table_data.append([str(i), nome_str])

    table = Table(table_data, colWidths=[0.5 * inch, 6 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(table)

    doc.build(elements)

    try:
        saved_path = None
        from src.services.utils.pdf import salvar_e_abrir_pdf as salvar_helper

        if salvar_helper is not None:
            try:
                saved_path = cast(Any, salvar_helper)(buffer)
            except TypeError:
                try:
                    saved_path = cast(Any, salvar_helper)(buffer, None)
                except Exception:
                    saved_path = None
            except Exception:
                logger.exception('Helper de PDF disponível, mas falhou ao salvar em memória')
                saved_path = None

        import os as _os
        import tempfile as _temp
        if not saved_path:
            try:
                if out_dir:
                    filename = os.path.join(out_dir, f"lista_notas_{int(datetime.datetime.now().timestamp())}.pdf")
                    buffer.seek(0)
                    with open(filename, 'wb') as f:
                        f.write(buffer.getvalue())
                    saved_path = filename
                else:
                    tf = _temp.NamedTemporaryFile(delete=False, suffix='.pdf')
                    tf.close()
                    buffer.seek(0)
                    with open(tf.name, 'wb') as f:
                        f.write(buffer.getvalue())
                    saved_path = tf.name
            except Exception:
                logger.exception('Falha ao escrever PDF temporário para lista_notas')
                saved_path = None

        if saved_path:
            try:
                from src.utils.utilitarios.gerenciador_documentos import salvar_documento_sistema
                from src.utils.utilitarios.tipos_documentos import TIPO_LISTA_NOTAS
                finalidade = 'Secretaria'
                descricao = f'Lista de Notas - {int(datetime.datetime.now().timestamp())}'
                sucesso, mensagem, link = salvar_documento_sistema(
                    saved_path,
                    TIPO_LISTA_NOTAS,
                    aluno_id=None,
                    funcionario_id=1,
                    finalidade=finalidade,
                    descricao=descricao,
                )
                if sucesso:
                    logger.info('Documento registrado no sistema: %s', link)
                    try:
                        if _os.path.exists(saved_path) and _os.path.dirname(saved_path) == _temp.gettempdir():
                            _os.remove(saved_path)
                    except Exception:
                        pass
                else:
                    logger.warning('Falha ao registrar documento no sistema: %s', mensagem)
            except Exception:
                logger.exception('Erro ao tentar registrar documento no sistema de documentos')
    except Exception:
        logger.exception('Falha inesperada ao salvar/registrar lista_notas')

    return True
