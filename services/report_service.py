import os
import sys
import importlib
from typing import Optional, Any, cast

from config_logs import get_logger
logger = get_logger(__name__)


def gerar_crachas_para_todos_os_alunos() -> str:
    """Executa a geração de crachás usando o módulo `gerar_cracha`.

    Retorna o caminho da pasta onde os crachás foram salvos.

    Levanta ImportError se o módulo não estiver disponível e propaga
    outras exceções para o chamador tratar (UI/worker).
    """
    # Adicionar o diretório scripts_nao_utilizados ao path
    scripts_dir = os.path.join(os.getcwd(), "scripts_nao_utilizados")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    try:
        import gerar_cracha  # type: ignore
    except ImportError:
        logger.exception("Módulo gerar_cracha não disponível")
        raise

    # tentar recarregar o módulo quando possível, mas ignore falhas de reload
    try:
        importlib.reload(gerar_cracha)
    except Exception:
        pass

    # Executa a função principal do gerador (pode demorar)
    gerar_cracha.gerar_crachas_para_todos_os_alunos()

    caminho = os.path.join(os.getcwd(), "Cracha_Anos_Iniciais")
    return caminho


def gerar_relatorio_avancado_com_assinatura(bimestre: str, nivel_ensino: str, ano_letivo: int,
                                            status_matricula, preencher_nulos: bool) -> bool:
    """Encapsula a chamada ao gerador de relatório de notas com assinatura.

    Retorna True se o relatório foi gerado com sucesso, False caso contrário.
    Propaga exceções para o chamador para tratamento de UI.
    """
    # O gerador principal está em NotaAta.py (ou módulo equivalente)
    try:
        from NotaAta import gerar_relatorio_notas_com_assinatura  # type: ignore
    except ImportError:
        logger.exception("Não foi possível importar NotaAta para gerar relatório avançado")
        raise

    resultado = gerar_relatorio_notas_com_assinatura(
        bimestre=bimestre,
        nivel_ensino=nivel_ensino,
        ano_letivo=ano_letivo,
        status_matricula=status_matricula,
        preencher_nulos=preencher_nulos
    )
    return bool(resultado)


def gerar_relatorio_notas(*args, **kwargs) -> bool:
    """Encapsula a chamada ao gerador de relatórios de notas (`NotaAta.gerar_relatorio_notas`).

    Permite injeção de mocks em testes via `sys.modules`. Recarrega o módulo apenas
    quando o import for realizado agora (evita executar código legado durante testes).
    """
    _mod = sys.modules.get('NotaAta')
    imported_now = False
    if _mod is None:
        try:
            import NotaAta as _mod  # type: ignore
            imported_now = True
        except ImportError:
            logger.exception("Módulo 'NotaAta' não disponível para gerar relatório de notas")
            raise

    if imported_now:
        try:
            _m = sys.modules.get('NotaAta')
            if _m is not None:
                importlib.reload(_m)
        except Exception:
            pass

    if not hasattr(_mod, 'gerar_relatorio_notas'):
        raise AttributeError("Módulo 'NotaAta' não possui 'gerar_relatorio_notas'")

    resultado = _mod.gerar_relatorio_notas(*args, **kwargs)
    try:
        return bool(resultado)
    except Exception:
        return True


def gerar_relatorio_pendencias(bimestre: str, nivel_ensino: str, ano_letivo: int, escola_id: int = 60) -> bool:
    """Encapsula a geração do relatório de pendências.

    Retorna True se gerou, False se não há pendências. Propaga exceções para o chamador.
    """
    try:
        from relatorio_pendencias import gerar_pdf_pendencias  # type: ignore
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
    """Encapsula o gerador de movimentação mensal.

    Retorna o resultado booleano do gerador legado ou True/False conforme apropriado.
    Propaga ImportError se o módulo não estiver disponível.
    """
    # Em ambientes de teste pode haver um módulo mock já em sys.modules;
    # preferimos reutilizá-lo para permitir injeção de mocks.
    _mov = sys.modules.get('movimentomensal')
    imported_now = False
    if _mov is None:
        try:
            import movimentomensal as _mov
            imported_now = True
        except ImportError:
            logger.exception("Módulo 'movimentomensal' não disponível para gerar relatório de movimentação mensal")
            raise

    # Só recarregar quando importamos o módulo agora; se já havia um mock
    # em `sys.modules` preferimos não recarregá-lo (evita executar código legado
    # ao rodar testes que injetam mocks).
    if imported_now:
        try:
            _m = sys.modules.get('movimentomensal')
            if _m is not None:
                importlib.reload(_m)
        except Exception:
            pass

    # Chama a função do módulo legado (pode levantar exceções)
    resultado = _mov.relatorio_movimentacao_mensal(numero_mes)
    # Normalizar retorno para bool quando aplicável
    try:
        return bool(resultado)
    except Exception:
        return True


def gerar_boletim(aluno_id: int, ano_letivo_id: Optional[int]) -> bool:
    """Gera o boletim para o aluno especificado delegando para `boletim.boletim`.

    Retorna True se a função foi invocada com sucesso (não necessariamente indica
    sucesso do IO interno). Propaga exceções de importação para o chamador.
    """
    try:
        from boletim import boletim as _gerar_boletim  # type: ignore
    except ImportError:
        logger.exception("Não foi possível importar módulo 'boletim' para gerar boletim")
        raise

    # tentar recarregar o módulo quando possível, mas ignore falhas de reload
    try:
        _m = sys.modules.get('boletim')
        if _m is not None:
            importlib.reload(_m)
    except Exception:
        pass

    # Delegar a geração (pode levantar exceções durante execução)
    # Alguns chamadores podem passar `None` para `ano_letivo_id` como sinal
    # para o módulo legado escolher o ano por padrão. Repasse como recebido.
    _gerar_boletim(aluno_id, ano_letivo_id)
    return True


def gerar_boletim_interno(aluno_id: int, ano_letivo_id: int) -> bool:
    """Compatibilidade: alias para `gerar_boletim` usado por alguns handlers."""
    return gerar_boletim(aluno_id, ano_letivo_id)



def gerar_lista_frequencia() -> bool:
    """Encapsula a chamada ao gerador de lista de frequência (`lista_frequencia`).

    Segue mesma estratégia de import/mocks que outras funções de service:
    - Reutiliza módulo presente em `sys.modules` quando disponível (testes podem injetar mock)
    - Recarrega apenas quando o import for feito agora (evita executar código legado em testes)
    """
    # Primeiro, permita que testes injetem um mock em `sys.modules`.
    _mod = sys.modules.get('lista_frequencia')
    imported_now = False
    if _mod is not None:
        # se houver mock, use-o diretamente (não recarregamos mocks)
        if not hasattr(_mod, 'lista_frequencia'):
            raise AttributeError("Módulo 'lista_frequencia' injetado não possui 'lista_frequencia'")
        _mod.lista_frequencia()
        return True

    # Se não houver mock, tente usar a implementação migrada (serviço).
    try:
        return _impl_lista_frequencia()
    except Exception:
        # Se a implementação interna falhar, recorra ao módulo legado como último recurso.
        try:
            import lista_frequencia as _mod  # type: ignore
            imported_now = True
        except ImportError:
            logger.exception("Módulo 'lista_frequencia' não disponível para gerar lista de frequência")
            raise

        if imported_now:
            try:
                _m = sys.modules.get('lista_frequencia')
                if _m is not None:
                    importlib.reload(_m)
            except Exception:
                pass

        if not hasattr(_mod, 'lista_frequencia'):
            raise AttributeError("Módulo 'lista_frequencia' não possui 'lista_frequencia'")

        _mod.lista_frequencia()
        return True


def gerar_tabela_frequencia() -> bool:
    """Encapsula o gerador de tabela/frequência.

    Estratégia:
    - Reutiliza um mock presente em `sys.modules` quando disponível (permite testes);
    - Tenta a implementação migrada `_impl_gerar_tabela_frequencia()` (mais segura para testes);
    - Em último caso, importa o módulo legado e delega para ele.
    """
    _mod = sys.modules.get('gerar_tabela_frequencia')
    if _mod is not None:
        # aceitar módulos legados ou mocks que exponham `lista_frequencia`
        if hasattr(_mod, 'lista_frequencia'):
            cast(Any, _mod).lista_frequencia()
            return True
        # ou função com nome alternativo
        if hasattr(_mod, 'gerar_tabela_frequencia'):
            cast(Any, _mod).gerar_tabela_frequencia()
            return True

    # Tentar a implementação migrada (serviço em-processo)
    try:
        return _impl_gerar_tabela_frequencia()
    except Exception:
        # fallback para o módulo legado como último recurso
        imported_now = False
        try:
            import gerar_tabela_frequencia as _mod  # type: ignore
            imported_now = True
        except ImportError:
            logger.exception("Módulo 'gerar_tabela_frequencia' não disponível para gerar tabela de frequência")
            raise

        if imported_now:
            try:
                _m = sys.modules.get('gerar_tabela_frequencia')
                if _m is not None:
                    importlib.reload(_m)
            except Exception:
                pass

        if hasattr(_mod, 'lista_frequencia'):
            cast(Any, _mod).lista_frequencia()
            return True
        if hasattr(_mod, 'gerar_tabela_frequencia'):
            cast(Any, _mod).gerar_tabela_frequencia()
            return True

        raise AttributeError("Módulo 'gerar_tabela_frequencia' não possui função conhecida para gerar a tabela de frequência")


def _impl_gerar_tabela_frequencia() -> bool:
    """Implementação migrada do gerador de tabela/frequência.

    Esta versão tenta usar `Lista_atualizada.fetch_student_data` e os helpers de
    PDF centralizados (`services.utils.pdf`). Retorna True em sucesso.
    """
    # imports locais para manter o import do serviço barato
    import pandas as pd
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import os
    import datetime

    try:
        from Lista_atualizada import fetch_student_data
    except Exception:
        logger.exception('Não foi possível importar fetch_student_data para gerar_tabela_frequencia')
        raise

    try:
        from services.utils.pdf import salvar_e_abrir_pdf, create_pdf_buffer
    except Exception:
        try:
            from gerarPDF import salvar_e_abrir_pdf, create_pdf_buffer
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para gerar_tabela_frequencia')
            raise

    ano_letivo = datetime.datetime.now().year
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        logger.info('Nenhum dado de aluno encontrado para gerar_tabela_frequencia')
        return False

    df = pd.DataFrame(dados_aluno)

    figura_superior = os.path.join(os.path.dirname(__file__), '..', 'logopacobranco.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), '..', 'logopaco.jpg')

    doc, buffer = create_pdf_buffer()
    elements = []

    style_total = ParagraphStyle(name='TotalStyle', parent=None, fontSize=10, alignment=1, wordWrap='CJK')
    style_transferencia = ParagraphStyle(name='TransferenciaStyle', parent=None, fontSize=10, alignment=1, textColor=colors.red, wordWrap='CJK')

    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        if turma_df.empty:
            continue

        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ''

        data = [
            [Image(figura_inferior, width=1.25 * inch, height=.75 * inch),
             Paragraph('<br/>'.join([
                 "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
                 "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
                 "<b>INEP: 21008485</b>",
                 "<b>CNPJ: 01.394.462/0001-01</b>"
             ]), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
             Image(figura_superior, width=1.5 * inch, height=1 * inch)]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))

        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {ano_letivo}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<b>PROFESSOR(A): {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=14, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        total_masculino = turma_df[turma_df['SEXO'] == 'M'].shape[0]
        total_feminino = turma_df[turma_df['SEXO'] == 'F'].shape[0]
        total_transferidos = turma_df[turma_df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])].shape[0]
        elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TRANSFERIDOS: {total_transferidos}", ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        texto_total_vertical = '<br/>'.join(list("TOTAL"))
        datas = pd.date_range(start=f'{ano_letivo}-01-01', periods=25).date
        tabela_frequencia = [['Nº', 'Nome'] + ['' for _ in datas] + [Paragraph(texto_total_vertical, style_total)]]

        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]

        for i, (_, row) in enumerate(turma_df.iterrows(), start=1):
            if row.get('SITUAÇÃO') in ['Transferido', 'Transferida']:
                data_transferencia = row.get('DATA_TRANSFERENCIA')
                data_transferencia = data_transferencia.strftime('%d/%m/%Y') if data_transferencia else "Data não disponível"
                texto_transferencia = f"{row.get('SITUAÇÃO')} em {data_transferencia}"
                linha = [i, row.get('NOME DO ALUNO')] + [''] * (len(datas) + 1)
                linha[2] = Paragraph(texto_transferencia, style_transferencia)
                table_style.append(('SPAN', (2, i), (-1, i)))
            else:
                linha = [i, row.get('NOME DO ALUNO')] + [''] * len(datas) + ['']
            tabela_frequencia.append(linha)

        row_heights = [1 * inch]
        row_heights.extend([0.25 * inch] * (len(tabela_frequencia) - 1))
        table = Table(tabela_frequencia, colWidths=[0.282 * inch, 3 * inch] + [0.25 * inch] * len(datas) + [0.35 * inch], rowHeights=row_heights)
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(PageBreak())

    doc.build(elements)
    salvar_e_abrir_pdf(buffer)
    return True

    # Se não houver mock, tente usar a implementação migrada (serviço).
    try:
        # Implementação migrada em-processo (evita executar código legado por import)
        return _impl_lista_frequencia()
    except Exception:
        # Se a implementação interna falhar, recorra ao módulo legado como último recurso.
        imported_now = False
        try:
            import lista_frequencia as _mod  # type: ignore
            imported_now = True
        except ImportError:
            logger.exception("Módulo 'lista_frequencia' não disponível para gerar lista de frequência")
            raise

        if imported_now:
            try:
                _m = sys.modules.get('lista_frequencia')
                if _m is not None:
                    importlib.reload(_m)
            except Exception:
                pass

        if not hasattr(_mod, 'lista_frequencia'):
            raise AttributeError("Módulo 'lista_frequencia' não possui 'lista_frequencia'")

        _mod.lista_frequencia()
        return True


def _impl_lista_frequencia() -> bool:
    """Implementação migrada de `lista_frequencia`.

    Esta função contém a versão ported do gerador de lista de frequência.
    Mantemos-a dentro do serviço para permitir testes e evitar executar
    código legado no import time.
    """
    # Importações locais — mantidas aqui para reduzir impacto no import do módulo
    import pandas as pd
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import os
    import datetime

    try:
        from Lista_atualizada import fetch_student_data
    except Exception:
        logger.exception('Não foi possível importar fetch_student_data para lista_frequencia')
        raise

    try:
        from services.utils.pdf import salvar_e_abrir_pdf, create_pdf_buffer
    except Exception:
        # Fallback: tentar importar do módulo legado `gerarPDF` para compatibilidade
        try:
            from gerarPDF import salvar_e_abrir_pdf, create_pdf_buffer
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para lista_frequencia')
            raise

    ano_letivo = datetime.datetime.now().year
    dados_aluno = fetch_student_data(ano_letivo)
    if not dados_aluno:
        logger.info('Nenhum dado de aluno encontrado para lista_frequencia')
        return False

    df = pd.DataFrame(dados_aluno)

    # Informações do cabeçalho
    cabecalho = [
        "SECRETARIA MUNICIPAL DE EDUCAÇÃO",
        "<b>ESCOLA MUNICIPAL PROFª. NADIR NASCIMENTO MORAES</b>",
        "<b>INEP: 21008485</b>",
        "<b>CNPJ: 01.394.462/0001-01</b>"
    ]

    figura_superior = os.path.join(os.path.dirname(__file__), '..', 'logopacobranco.png')
    figura_inferior = os.path.join(os.path.dirname(__file__), '..', 'logopaco.jpg')

    doc, buffer = create_pdf_buffer()
    elements = []

    style_total = ParagraphStyle(name='TotalStyle', parent=None, fontSize=10, alignment=1, wordWrap='CJK')
    style_transferencia = ParagraphStyle(name='TransferenciaStyle', parent=None, fontSize=10, alignment=1, textColor=colors.red, wordWrap='CJK')

    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        if turma_df.empty:
            continue

        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else ''

        data = [
            [Image(figura_inferior, width=1.25 * inch, height=.75 * inch),
             Paragraph('<br/>'.join(cabecalho), ParagraphStyle(name='Header', fontSize=12, alignment=1)),
             Image(figura_superior, width=1.5 * inch, height=1 * inch)]
        ]
        table = Table(data, colWidths=[1.32 * inch, 4 * inch, 1.32 * inch])
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elements.append(table)
        elements.append(Spacer(1, 0.25 * inch))

        elements.append(Paragraph(f"<b>Turma: {nome_serie} {nome_turma} - Turno: {turno} - {datetime.datetime.now().year}</b>", ParagraphStyle(name='TurmaTitulo', fontSize=14, alignment=1)))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<b>PROFESSOR(A): {nome_professor} </b>", ParagraphStyle(name='ProfessoraTitulo', fontSize=14, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        total_masculino = turma_df[turma_df['SEXO'] == 'M'].shape[0]
        total_feminino = turma_df[turma_df['SEXO'] == 'F'].shape[0]
        total_transferidos = turma_df[turma_df['SITUAÇÃO'].isin(['Transferido', 'Transferida'])].shape[0]
        elements.append(Paragraph(f"TOTAIS: MASCULINO ({total_masculino}) FEMININO ({total_feminino}) - TRANSFERIDOS: {total_transferidos}", ParagraphStyle(name='TotaisAlunos', fontSize=12, alignment=0)))
        elements.append(Spacer(1, 0.15 * inch))

        texto_total_vertical = '<br/>'.join(list("TOTAL"))
        datas = pd.date_range(start=f'{ano_letivo}-01-01', periods=25).date
        tabela_frequencia = [['Nº', 'Nome'] + ['' for _ in datas] + [Paragraph(texto_total_vertical, style_total)]]

        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]

        for i, (_, row) in enumerate(turma_df.iterrows(), start=1):
            if row.get('SITUAÇÃO') in ['Transferido', 'Transferida']:
                data_transferencia = row.get('DATA_TRANSFERENCIA')
                data_transferencia = data_transferencia.strftime('%d/%m/%Y') if data_transferencia else "Data não disponível"
                texto_transferencia = f"{row.get('SITUAÇÃO')} em {data_transferencia}"
                linha = [i, row.get('NOME DO ALUNO')] + [''] * (len(datas) + 1)
                linha[2] = Paragraph(texto_transferencia, style_transferencia)
                table_style.append(('SPAN', (2, i), (-1, i)))
            else:
                linha = [i, row.get('NOME DO ALUNO')] + [''] * len(datas) + ['']
            tabela_frequencia.append(linha)

        row_heights = [1 * inch]
        row_heights.extend([0.25 * inch] * (len(tabela_frequencia) - 1))
        table = Table(tabela_frequencia, colWidths=[0.282 * inch, 3 * inch] + [0.25 * inch] * len(datas) + [0.35 * inch], rowHeights=row_heights)
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(PageBreak())

    doc.build(elements)
    salvar_e_abrir_pdf(buffer)
    return True


def gerar_lista_notas() -> bool:
    """Encapsula a chamada ao gerador de lista de notas (`Lista_notas.lista_notas`).

    Usa `sys.modules` para permitir injeção de mocks em testes e recarrega o
    módulo apenas quando importado agora, evitando executar código legado em
    testes que injetam mocks.
    """
    # Permitir injeção de mock em `sys.modules` para testes
    _mod = sys.modules.get('Lista_notas')
    if _mod is not None:
        if hasattr(_mod, 'lista_notas'):
            cast(Any, _mod).lista_notas()
            return True
        raise AttributeError("Módulo 'Lista_notas' injetado não possui 'lista_notas'")

    # Tentar a implementação migrada em-processo (teste-friendly)
    try:
        return _impl_lista_notas()
    except NotImplementedError:
        # Ainda não portado completamente — caímos para o fallback legado
        pass
    except Exception:
        # Se a implementação interna falhar, recorrer ao módulo legado
        pass

    # Fallback: importar e delegar ao módulo legado
    imported_now = False
    try:
        import Lista_notas as _mod  # type: ignore
        imported_now = True
    except ImportError:
        logger.exception("Módulo 'Lista_notas' não disponível para gerar lista de notas")
        raise

    if imported_now:
        try:
            _m = sys.modules.get('Lista_notas')
            if _m is not None:
                importlib.reload(_m)
        except Exception:
            pass

    if not hasattr(_mod, 'lista_notas'):
        raise AttributeError("Módulo 'Lista_notas' não possui 'lista_notas'")

    cast(Any, _mod).lista_notas()
    return True


def gerar_resumo_ponto(*args, **kwargs) -> bool:
    """Encapsula a chamada ao gerador de resumo de ponto.

    Estratégia:
    - Reutiliza mocks injetados em `sys.modules` quando presentes (permite testes);
    - Tenta usar a implementação migrada `_impl_gerar_resumo_ponto()` (quando disponível);
    - Em último caso, recorre ao módulo legado `gerar_resumo_ponto`.
    """
    # Primeiro, permitir que testes injetem um mock em `sys.modules`.
    _mod = sys.modules.get('gerar_resumo_ponto')
    if _mod is not None:
        if hasattr(_mod, 'gerar_resumo_ponto'):
            cast(Any, _mod).gerar_resumo_ponto(*args, **kwargs)
            return True
        raise AttributeError("Módulo 'gerar_resumo_ponto' injetado não possui 'gerar_resumo_ponto'")

    # Tentar a implementação migrada em-processo (evita executar código legado por import)
    try:
        return _impl_gerar_resumo_ponto(*args, **kwargs)
    except NotImplementedError:
        # Ainda não portado — caímos para o fallback legado
        pass
    except Exception:
        # Se a implementação interna falhar, recorrer ao módulo legado
        pass

    # Fallback: importar e delegar ao módulo legado
    imported_now = False
    try:
        import gerar_resumo_ponto as _mod  # type: ignore
        imported_now = True
    except ImportError:
        logger.exception("Módulo 'gerar_resumo_ponto' não disponível para gerar resumo de ponto")
        raise

    if imported_now:
        try:
            _m = sys.modules.get('gerar_resumo_ponto')
            if _m is not None:
                importlib.reload(_m)
        except Exception:
            pass

    if not hasattr(_mod, 'gerar_resumo_ponto'):
        raise AttributeError("Módulo 'gerar_resumo_ponto' não possui 'gerar_resumo_ponto'")

    resultado = cast(Any, _mod).gerar_resumo_ponto(*args, **kwargs)
    try:
        return bool(resultado)
    except Exception:
        return True


def gerar_folhas_de_ponto(*args, **kwargs) -> bool:
    """Encapsula a chamada a `preencher_folha_ponto.gerar_folhas_de_ponto`.

    Segue a mesma estratégia usada pelos demais serviços:
    - Reutiliza um módulo presente em `sys.modules` quando disponível (permite mocks em testes);
    - Importa o módulo apenas se não existir em `sys.modules`;
    - Recarrega o módulo apenas quando o import for realizado agora (evita executar código legado em testes).
    """
    _mod = sys.modules.get('preencher_folha_ponto')
    imported_now = False
    if _mod is None:
        try:
            import preencher_folha_ponto as _mod  # type: ignore
            imported_now = True
        except ImportError:
            logger.exception("Módulo 'preencher_folha_ponto' não disponível para gerar folhas de ponto")
            raise

    if imported_now:
        try:
            _m = sys.modules.get('preencher_folha_ponto')
            if _m is not None:
                importlib.reload(_m)
        except Exception:
            pass

    if not hasattr(_mod, 'gerar_folhas_de_ponto'):
        raise AttributeError("Módulo 'preencher_folha_ponto' não possui 'gerar_folhas_de_ponto'")

    resultado = _mod.gerar_folhas_de_ponto(*args, **kwargs)
    try:
        return bool(resultado)
    except Exception:
        return True


def _impl_gerar_folhas_de_ponto(*args, **kwargs) -> bool:
    """Implementação migrada (in-process) para `preencher_folha_ponto.gerar_folhas_de_ponto`.

    Aceita parâmetros injetáveis para facilitar testes:
    - `profissionais`: lista de dicts com pelo menos campo `nome` (se fornecido, evita acesso ao DB)
    - `mes` e `ano`: quando relevante para o nome do arquivo/título
    - `out_dir`: diretório para fallback de escrita de arquivo

    Se `profissionais` não for fornecido, esta implementação levanta
    `NotImplementedError` para forçar o fallback ao módulo legado.
    """
    # parâmetros básicos
    import datetime
    import io
    import os

    if len(args) >= 2:
        mes = args[0]
        ano = args[1]
    else:
        mes = kwargs.get('mes', datetime.datetime.now().month)
        ano = kwargs.get('ano', datetime.datetime.now().year)

    profissionais = kwargs.get('profissionais')
    out_dir = kwargs.get('out_dir')

    if profissionais is None:
        # Não temos como buscar dados sem acionar o código legado — sinalizamos
        # para que o wrapper faça o fallback para o módulo original.
        raise NotImplementedError("_impl_gerar_folhas_de_ponto requer 'profissionais' injetados")

    # helpers de PDF (tentar helpers centralizados, fallback legado)
    try:
        from services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf
    except Exception:
        try:
            from gerarPDF import create_pdf_buffer, salvar_e_abrir_pdf
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para gerar_folhas_de_ponto')
            raise

    # imports de desenho locais
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    # montar documento em memória
    doc, buffer = create_pdf_buffer()
    elements = []
    elements.append(Paragraph(f"FOLHAS DE PONTO - {mes}/{ano}", ParagraphStyle(name='Title', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.2 * inch))

    # tabela básica
    table_data = [['Nº', 'Nome', 'Função']]
    for i, p in enumerate(profissionais, start=1):
        if isinstance(p, dict):
            nome = p.get('nome') or p.get('nome_profissional') or p.get('Nome') or ''
            func = p.get('funcao') or p.get('cargo') or ''
        else:
            nome = str(p)
            func = ''
        table_data.append([str(i), str(nome), str(func)])

    table = Table(table_data, colWidths=[0.5 * inch, 4 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(table)

    # gerar e salvar
    doc.build(elements)
    try:
        salvar_e_abrir_pdf(buffer)
    except Exception:
        # fallback para escrita em disco se for fornecido out_dir
        try:
            if out_dir:
                filename = os.path.join(out_dir, f"folhas_ponto_{mes}_{ano}_{int(datetime.datetime.now().timestamp())}.pdf")
                buffer.seek(0)
                with open(filename, 'wb') as f:
                    f.write(buffer.getvalue())
                logger.info(f"PDF salvo em (fallback): {filename}")
            else:
                logger.exception('Falha ao salvar PDF e sem out_dir para fallback')
        except Exception:
            logger.exception('Falha final ao salvar PDF em fallback')

    return True


def gerar_relatorio_series_faltantes() -> bool:
    """Wrapper testável para `gerar_relatorio_series_faltantes`.

    Estratégia de import/mocks semelhante a outros serviços:
    - Reutiliza um mock em `sys.modules` quando presente;
    - Tenta usar `_impl_gerar_relatorio_series_faltantes()` (implementação migrada);
    - Em último caso, importa e delega para o módulo legado.
    """
    _mod = sys.modules.get('gerar_relatorio_series_faltantes')
    if _mod is not None:
        if hasattr(_mod, 'gerar_relatorio_series_faltantes'):
            cast(Any, _mod).gerar_relatorio_series_faltantes()
            return True
        raise AttributeError("Módulo 'gerar_relatorio_series_faltantes' injetado não possui 'gerar_relatorio_series_faltantes'")

    # Tentar implementação migrada
    try:
        return _impl_gerar_relatorio_series_faltantes()
    except Exception:
        # fallback para módulo legado
        imported_now = False
        try:
            import gerar_relatorio_series_faltantes as _mod  # type: ignore
            imported_now = True
        except ImportError:
            logger.exception("Módulo 'gerar_relatorio_series_faltantes' não disponível para gerar relatório")
            raise

        if imported_now:
            try:
                _m = sys.modules.get('gerar_relatorio_series_faltantes')
                if _m is not None:
                    importlib.reload(_m)
            except Exception:
                pass

        if not hasattr(_mod, 'gerar_relatorio_series_faltantes'):
            raise AttributeError("Módulo 'gerar_relatorio_series_faltantes' não possui 'gerar_relatorio_series_faltantes'")

        cast(Any, _mod).gerar_relatorio_series_faltantes()
        return True


def _impl_gerar_relatorio_series_faltantes(alunos_ativos=None, historico_lookup=None, out_dir: str = 'documentos_gerados') -> bool:
    """Implementação migrada do gerador `gerar_relatorio_series_faltantes`.

    Parâmetros injetáveis (úteis para testes):
    - `alunos_ativos`: lista de dicts com chaves `aluno_id`, `nome_aluno`, `serie_atual`.
    - `historico_lookup`: dict mapping aluno_id -> list of historico records (dicts com 'serie_id' and 'situacao_final').
    - `out_dir`: diretório de saída para os PDFs (usado pelo helper de salvar).

    Quando `alunos_ativos` não é fornecido, conecta ao BD e faz as consultas conforme o legado.
    """
    import calendar
    import time
    # Import helpers de PDF
    try:
        from services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf
    except Exception:
        try:
            from gerarPDF import create_pdf_buffer, salvar_e_abrir_pdf
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para relatorio_series_faltantes')
            raise

    conn = None
    try:
        # Obter ou consultar alunos ativos
        if alunos_ativos is None:
            try:
                from conexao import conectar_bd
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
                # manter compatibilidade: usar ano_letivo_id genérico (60 era escola id elsewhere)
                cursor.execute(query_alunos_ativos, (26,))
                alunos_ativos = cursor.fetchall()
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass

        # Obter historico lookup se não fornecido
        if historico_lookup is None:
            historico_lookup = {}
            # se temos conexão, buscar historico por aluno
            if conn is None:
                try:
                    from conexao import conectar_bd
                    conn = conectar_bd()
                except Exception:
                    conn = None

        # Helper local para acessar campos de objetos retornados pelo DB
        def _get_field(obj, key):
            if isinstance(obj, dict):
                return obj.get(key)
            try:
                # tratar tuplas/listas/dicts com __getitem__
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

        # Processar e montar listas
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

        # Gerar PDF em memória
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        import datetime
        timestamp = int(time.time())
        filename = os.path.join(out_dir, f"relatorio_series_faltantes_{timestamp}.pdf")

        doc, buffer = create_pdf_buffer()
        elements = []
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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

        # build and save
        doc.build(elements)
        salvar_e_abrir_pdf(buffer)
        return True
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def gerar_lista_reuniao() -> bool:
    """Wrapper testável para `gerar_lista_reuniao`.

    Prefere um mock em `sys.modules` quando presente; tenta `_impl_gerar_lista_reuniao` e
    por fim recorre ao módulo legado.
    """
    _mod = sys.modules.get('gerar_lista_reuniao')
    if _mod is not None:
        if hasattr(_mod, 'gerar_lista_reuniao'):
            cast(Any, _mod).gerar_lista_reuniao()
            return True
        raise AttributeError("Módulo 'gerar_lista_reuniao' injetado não possui 'gerar_lista_reuniao'")

    try:
        return _impl_gerar_lista_reuniao()
    except Exception:
        # fallback para módulo legado
        imported_now = False
        try:
            import gerar_lista_reuniao as _mod  # type: ignore
            imported_now = True
        except ImportError:
            logger.exception("Módulo 'gerar_lista_reuniao' não disponível para gerar lista de reunião")
            raise

        if imported_now:
            try:
                _m = sys.modules.get('gerar_lista_reuniao')
                if _m is not None:
                    importlib.reload(_m)
            except Exception:
                pass

        if not hasattr(_mod, 'gerar_lista_reuniao'):
            raise AttributeError("Módulo 'gerar_lista_reuniao' não possui 'gerar_lista_reuniao'")

        cast(Any, _mod).gerar_lista_reuniao()
        return True


def _impl_gerar_lista_reuniao(dados_aluno=None, ano_letivo: Optional[int] = None, out_dir: Optional[str] = None, pastas_turmas=None, criar_pastas_func=None, adicionar_cabecalho_func=None) -> bool:
    """Implementação migrada do gerador `gerar_lista_reuniao`.

    Parâmetros injetáveis (úteis em testes):
    - `dados_aluno`: lista de dicts com os campos esperados pelo gerador (evita DB).
    - `ano_letivo`: ano a ser passado para `fetch_student_data` quando `dados_aluno` não for fornecido.
    - `out_dir`: diretório de saída (quando necessário para compatibilidade).
    - `pastas_turmas`: coleção de nomes de turmas válidas; se fornecida, turmas não mapeadas serão puladas.
    - `criar_pastas_func`: função opcional para criar pastas (se a lógica externa precisar).
    - `adicionar_cabecalho_func`: função que adiciona cabeçalho aos `elements` (fallback para legado se não fornecida).

    Retorna True em sucesso.
    """
    import pandas as pd
    import io
    import datetime
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    # helpers de PDF
    try:
        from services.utils.pdf import salvar_e_abrir_pdf
    except Exception:
        try:
            from gerarPDF import salvar_e_abrir_pdf
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para gerar_lista_reuniao')
            raise

    # carregar dados ou usar o fornecido
    if dados_aluno is None:
        if ano_letivo is None:
            ano_letivo = 2025
        try:
            from Lista_atualizada import fetch_student_data
            dados_aluno = fetch_student_data(ano_letivo)
        except Exception:
            logger.exception('Não foi possível obter dados dos alunos para gerar_lista_reuniao')
            raise

    if not dados_aluno:
        logger.info('Nenhum dado de aluno encontrado para gerar_lista_reuniao')
        return False

    df = pd.DataFrame(dados_aluno)

    # permissões/estrutura de pastas (opcional)
    if criar_pastas_func:
        try:
            criar_pastas_func()
        except Exception:
            logger.exception('Falha ao criar pastas via criar_pastas_func')

    # localizar imagens
    diretorio_principal = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    figura_superior = os.path.join(diretorio_principal, "logosemed.png")
    figura_inferior = os.path.join(diretorio_principal, "logopaco.jpg")

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

    # pastas_turmas: se não fornecido, aceitamos todas
    accept_all = pastas_turmas is None

    for (nome_serie, nome_turma, turno), turma_df in df.groupby(['NOME_SERIE', 'NOME_TURMA', 'TURNO']):
        nome_turma_completo = f"{nome_serie} {nome_turma}" if nome_turma else nome_serie

        if (not accept_all) and (nome_turma_completo not in pastas_turmas):
            logger.info(f"Turma '{nome_turma_completo}' não mapeada em pastas_turmas — pulando")
            continue

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

        # cabeçalho
        if adicionar_cabecalho_func:
            try:
                adicionar_cabecalho_func(elements, cabecalho, figura_superior, figura_inferior)
            except Exception:
                logger.exception('Falha ao executar adicionar_cabecalho_func')
        else:
            # tentar reaproveitar função do legado quando disponível
            try:
                import gerar_lista_reuniao as legacy  # type: ignore
                if hasattr(legacy, 'adicionar_cabecalho'):
                    legacy.adicionar_cabecalho(elements, cabecalho, figura_superior, figura_inferior)
            except Exception:
                # sem cabeçalho, prosseguir
                pass

        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph("<b>LISTA PARA REUNIÃO</b>", ParagraphStyle(name='Capa', fontSize=24, alignment=1)))
        elements.append(Spacer(1, 2.5 * inch))
        elements.append(Paragraph(f"<b>{datetime.datetime.now().year}</b>", ParagraphStyle(name='Ano', fontSize=18, alignment=1)))
        elements.append(PageBreak())

        nome_professor = turma_df['NOME_PROFESSOR'].iloc[0] if not turma_df['NOME_PROFESSOR'].isnull().all() else 'Sem Professor'
        turma_df = turma_df[turma_df['SITUAÇÃO'] == 'Ativo']

        # cabeçalho da página
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

        # salvar: use helper centralizado; informe filename quando out_dir fornecido
        if out_dir:
            filename = os.path.join(out_dir, f"{nome_turma_completo}_Reuniao.pdf")
        else:
            filename = None

        try:
            # chamar helper centralizado sem passar filename (algumas versões não aceitam o argumento)
            salvar_e_abrir_pdf(buffer)
        except Exception:
            # tentar fallback para escrita direta como último recurso
            try:
                if filename:
                    buffer.seek(0)
                    with open(filename, 'wb') as f:
                        f.write(buffer.getvalue())
                    logger.info(f"PDF salvo em (fallback): {filename}")
                else:
                    logger.exception('Falha ao salvar PDF e sem filename para fallback')
            except Exception:
                logger.exception('Falha final ao salvar PDF')

    return True


def _impl_gerar_resumo_ponto(*args, **kwargs) -> bool:
    """Implementação migrada do gerador `gerar_resumo_ponto`.

    Assinatura compatível com o wrapper: `_impl_gerar_resumo_ponto(mes, ano, **opts)`.

    Parâmetros opcionais via `kwargs` (úteis para testes):
    - `profissionais`: lista pronta de profissionais (evita acesso ao DB)
    - `escola`: dict com dados da escola (evita acesso ao DB)
    - `base2_path`, `base3_path`, `base4_path`: caminhos para os PDFs base

    Retorna True em sucesso. Em caso de erro, propaga exceções para o chamador.
    """
    import io
    import tempfile
    import importlib

    if len(args) < 2:
        raise TypeError("_impl_gerar_resumo_ponto espera pelo menos (mes, ano)")
    mes = args[0]
    ano = args[1]

    profissionais = kwargs.get('profissionais')
    escola = kwargs.get('escola')
    base2_path = kwargs.get('base2_path')
    base3_path = kwargs.get('base3_path')
    base4_path = kwargs.get('base4_path')

    # helpers de PDF
    try:
        from services.utils.pdf import salvar_e_abrir_pdf
    except Exception:
        try:
            from gerarPDF import salvar_e_abrir_pdf
        except Exception:
            raise

    # Importar o módulo legado para reusar helpers de desenho e consultas.
    # Testes podem injetar mocks em `sys.modules`; se o mock não fornecer as
    # funções necessárias, carregamos o arquivo fonte original diretamente
    # para garantir que temos as implementações.
    legacy = importlib.import_module('gerar_resumo_ponto')

    def _ensure_legacy_module(mod):
        required = [
            'nome_mes_pt',
            'desenhar_bloco_escola',
            'desenhar_tabela_profissionais',
            'consultar_profissionais',
            'consultar_escola',
            '_encontrar_arquivo_base',
        ]
        if all(hasattr(mod, name) for name in required):
            return mod
        # Carregar diretamente do arquivo fonte do projeto
        import importlib.util
        import os as _os
        repo_root = _os.path.abspath(os.getcwd())
        candidate = _os.path.join(repo_root, 'gerar_resumo_ponto.py')
        if not _os.path.isfile(candidate):
            return mod
        spec = importlib.util.spec_from_file_location('gerar_resumo_ponto_real', candidate)
        if spec is None:
            return mod
        real = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            return mod
        spec.loader.exec_module(real)  # type: ignore
        return real

    legacy = _ensure_legacy_module(legacy)

    # Obter dados (pode ser injetado para testes)
    conn_provided = kwargs.get('conn')
    conn = None
    try:
        if profissionais is None or escola is None:
            # Se não foram fornecidos, usamos as funções do módulo legado
            # e a conexão padrão. Evitamos fechar a conexão se ela foi fornecida.
            if conn_provided is not None:
                conn = conn_provided
            else:
                try:
                    from conexao import conectar_bd

                    conn = conectar_bd()
                except Exception:
                    conn = None

            if profissionais is None:
                profissionais = legacy.consultar_profissionais(conn, mes, ano)
            if escola is None:
                escola = legacy.consultar_escola(conn, 60)

    finally:
        if conn is not None and conn_provided is None:
            try:
                conn.close()
            except Exception:
                pass

    # Preparar periodos e ordenar / dividir profissionais conforme legacy
    import calendar
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    periodo = f"1 a {ultimo_dia} de {legacy.nome_mes_pt(mes)} de {ano}"

    # prioridade e ordenação (reúso do legacy)
    import unicodedata as _ud

    def _sem_acentos(txt: str) -> str:
        return "".join(ch for ch in _ud.normalize("NFD", txt) if _ud.category(ch) != "Mn")

    prioridade = [
        "Leandro Fonseca Lima",
        "Rosiane de Jesus Santos Melo",
    ]
    prioridade_norm = [_sem_acentos(n).casefold() for n in prioridade]

    def _key(p):
        nome = str(p.get("nome", ""))
        nome_norm = _sem_acentos(nome).casefold()
        try:
            idx = prioridade_norm.index(nome_norm)
            return (0, idx)
        except ValueError:
            return (1, nome_norm)

    profissionais = sorted(profissionais, key=_key)

    bloco1 = list(enumerate(profissionais[:17], start=1))
    bloco2 = list(enumerate(profissionais[17:40], start=18))
    bloco3 = list(enumerate(profissionais[40:], start=41))

    # localizar templates base, se não fornecidos
    if base2_path is None:
        base2_path = legacy._encontrar_arquivo_base("Resumo de Frequencia2.pdf", "Resumo de Frequência2.pdf")
    if base3_path is None:
        base3_path = legacy._encontrar_arquivo_base("Resumo de Frequencia3.pdf", "Resumo de Frequência3.pdf")
    if base4_path is None:
        base4_path = legacy._encontrar_arquivo_base("Resumo de Frequencia4.pdf", "Resumo de Frequência4.pdf")

    # Função para criar overlay a partir de um template e blocos
    from reportlab.pdfgen import canvas
    from PyPDF2 import PdfReader, PdfWriter

    # Página 2
    reader2 = PdfReader(base2_path)
    p2 = reader2.pages[0]
    largura2 = float(p2.mediabox.width)
    altura2 = float(p2.mediabox.height)

    packet2 = io.BytesIO()
    can2 = canvas.Canvas(packet2, pagesize=(largura2, altura2))
    # desenhar bloco escola e tabela (reaproveitar funções do módulo legado)
    y_after_escola = legacy.desenhar_bloco_escola(can2, escola, largura2, altura2, altura2 - 98, mes, ano)
    legacy.desenhar_tabela_profissionais(can2, bloco1, largura2, altura2, altura2 - 250)
    can2.save()
    packet2.seek(0)
    overlay2 = PdfReader(packet2)
    pagina2 = PdfReader(base2_path).pages[0]
    pagina2.merge_page(overlay2.pages[0])

    # Página 3
    reader3 = PdfReader(base3_path)
    p3 = reader3.pages[0]
    largura3 = float(p3.mediabox.width)
    altura3 = float(p3.mediabox.height)

    packet3 = io.BytesIO()
    can3 = canvas.Canvas(packet3, pagesize=(largura3, altura3))
    legacy.desenhar_tabela_profissionais(can3, bloco2, largura3, altura3, altura3 - 140)
    can3.save()
    packet3.seek(0)
    overlay3 = PdfReader(packet3)
    pagina3 = PdfReader(base3_path).pages[0]
    pagina3.merge_page(overlay3.pages[0])

    # Página 4 (opcional)
    pagina4 = None
    if bloco3:
        reader4 = PdfReader(base4_path)
        p4 = reader4.pages[0]
        largura4 = float(p4.mediabox.width)
        altura4 = float(p4.mediabox.height)

        packet4 = io.BytesIO()
        can4 = canvas.Canvas(packet4, pagesize=(largura4, altura4))
        legacy.desenhar_tabela_profissionais(can4, bloco3, largura4, altura4, altura4 - 140)
        can4.save()
        packet4.seek(0)
        overlay4 = PdfReader(packet4)
        pagina4 = PdfReader(base4_path).pages[0]
        pagina4.merge_page(overlay4.pages[0])

    # Montar writer em memória
    wfinal = PdfWriter()
    wfinal.add_page(pagina2)
    if bloco2:
        wfinal.add_page(pagina3)
    if bloco3 and pagina4 is not None:
        wfinal.add_page(pagina4)

    out_buf = io.BytesIO()
    wfinal.write(out_buf)
    out_buf.seek(0)

    # Salvar usando helper centralizado (escreve em arquivo temporário e retorna path)
    salvar_e_abrir_pdf(out_buf)
    return True


def _impl_lista_notas(dados_aluno=None, ano_letivo: Optional[int] = None, out_dir: Optional[str] = None) -> bool:
    """Implementação migrada para `Lista_notas.lista_notas`.

    Parâmetros injetáveis para testes:
    - `dados_aluno`: lista de dicts com ao menos `aluno_id` e `NOME DO ALUNO`.
    - `ano_letivo`: ano para busca quando `dados_aluno` não for fornecido.
    - `out_dir`: diretório de saída (opcional, usado apenas no fallback de salvar).

    A implementação é simples: monta um PDF com a lista de alunos fornecida.
    Se `dados_aluno` não for fornecido e não for possível obter via `Lista_atualizada.fetch_student_data`,
    a função levanta `NotImplementedError` para sinalizar que o fallback legado deve ser usado.
    """
    import io
    import datetime
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    # helpers de PDF
    try:
        from services.utils.pdf import create_pdf_buffer, salvar_e_abrir_pdf
    except Exception:
        try:
            from gerarPDF import create_pdf_buffer, salvar_e_abrir_pdf
        except Exception:
            logger.exception('Não foi possível importar helpers de PDF para lista_notas')
            raise

    if dados_aluno is None:
        if ano_letivo is None:
            ano_letivo = datetime.datetime.now().year
        try:
            from Lista_atualizada import fetch_student_data
            dados_aluno = fetch_student_data(ano_letivo)
        except Exception:
            # Não conseguimos obter os dados sem acionar o legacy — indicar que não foi implementado
            raise NotImplementedError("_impl_lista_notas não conseguiu obter dados; usar fallback legado")

    if not dados_aluno:
        logger.info('Nenhum dado de aluno encontrado para lista_notas (impl)')
        return False

    # Construir PDF básico com nomes
    doc, buffer = create_pdf_buffer()
    elements = []
    elements.append(Paragraph('<b>LISTA DE NOTAS</b>', ParagraphStyle(name='Title', fontSize=16, alignment=1)))
    elements.append(Spacer(1, 0.2 * inch))

    # Cabeçalho tabela
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

    # salvar/abrir
    try:
        salvar_e_abrir_pdf(buffer)
    except Exception:
        # fallback para salvar em disco se out_dir fornecido
        try:
            if out_dir:
                filename = os.path.join(out_dir, f"lista_notas_{int(datetime.datetime.now().timestamp())}.pdf")
                buffer.seek(0)
                with open(filename, 'wb') as f:
                    f.write(buffer.getvalue())
                logger.info(f"PDF salvo em (fallback): {filename}")
            else:
                logger.exception('Falha ao salvar PDF e sem out_dir para fallback')
        except Exception:
            logger.exception('Falha final ao salvar PDF em fallback')

    return True
