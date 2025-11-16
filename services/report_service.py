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


def gerar_lista_reuniao() -> bool:
    """Encapsula a chamada ao gerador de lista de reunião (`gerar_lista_reuniao`).

    Em ambientes de teste, pode existir um mock em `sys.modules` — preferimos
    reutilizá-lo. Recarregamos o módulo apenas quando o import for feito agora
    (evita executar código legado durante testes que injetam mocks).
    """
    _mod = sys.modules.get('gerar_lista_reuniao')
    imported_now = False
    if _mod is None:
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

    # Chama o gerador legado (ou o mock injetado em test)
    _mod.gerar_lista_reuniao()
    return True


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
    # Nome do módulo legado é 'Lista_notas'
    _mod = sys.modules.get('Lista_notas')
    imported_now = False
    if _mod is None:
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

    _mod.lista_notas()
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
