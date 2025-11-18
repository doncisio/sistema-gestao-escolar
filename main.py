import sys
import os
import webbrowser
import traceback
from typing import Optional, Union, Tuple, Any, List, Dict
from datetime import datetime, date, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tkinter import Tk, Frame, Label, Button, Entry, Toplevel, StringVar, IntVar, BooleanVar, OptionMenu, Radiobutton, Checkbutton, NSEW, EW, NS, W, E, X, Y, BOTH, TRUE, FALSE, LEFT, RIGHT, BOTTOM, TOP, RAISED, RIDGE, SOLID, HORIZONTAL, DISABLED, NORMAL, Menu
from tkinter import ttk
from tkinter.ttk import Style, Progressbar, Separator
from tkinter import messagebox
from tkinter import TclError  # Importar TclError explicitamente para tratamento de erros
from PIL import ImageTk, Image
import pandas as pd

# Importações para o dashboard com gráficos
import matplotlib
matplotlib.use('TkAgg')  # Backend para integração com Tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D  # Para gráficos 3D
import numpy as np  # Para cálculos matemáticos do gráfico 3D

from Funcionario import gerar_declaracao_funcionario
import Funcionario
from Gerar_Declaracao_Aluno import gerar_declaracao_aluno
import Lista_atualizada
import Lista_atualizada_semed
import Seguranca
from conexao import inicializar_pool, fechar_pool
from db.connection import get_connection
from typing import Any, cast
from integrar_historico_escolar import abrir_interface_historico, abrir_historico_aluno
import aluno
from config_logs import get_logger

# Logger da aplicação
logger = get_logger(__name__)


def _run_report_in_background(fn, descricao: str):
    # Delegar para o módulo de UI (`ui.dashboard`) que oferece janela de progresso
    try:
        from ui.dashboard import run_report_in_background
        return run_report_in_background(fn, descricao, janela=janela, status_label=status_label, co1=co1, co0=co0, co6=co6)
    except Exception:
        # Se falhar (ex.: módulo não disponível), usar fallback mínimo local
        def _worker():
            try:
                res = fn()
                try:
                    if status_label is not None:
                        status_label.config(text=f"{descricao} gerado com sucesso.")
                except Exception:
                    pass
                try:
                    messagebox.showinfo(descricao, f"{descricao} gerado com sucesso.")
                except Exception:
                    pass
                return res
            except Exception as e:
                try:
                    messagebox.showerror(f"Erro - {descricao}", f"Falha ao gerar {descricao}: {e}")
                except Exception:
                    pass
                return None

        from threading import Thread
        Thread(target=_worker, daemon=True).start()


def _run_report_module_returning_buffer(module_fn, descricao: str):
    """Helper: para módulos que retornam um `BytesIO` buffer.
    Chama `module_fn()` em background e, quando recebe o buffer,
    salva/abre o PDF via `gerarPDF.salvar_e_abrir_pdf` (no worker).
    Retorna o caminho do arquivo salvo para o on_done do wrapper.
    """
    try:
        from ui.dashboard import run_report_module_returning_buffer
        return run_report_module_returning_buffer(module_fn, descricao, janela=janela, status_label=status_label, co1=co1, co0=co0, co6=co6)
    except Exception:
        # Fallback local
        def _worker():
            res = module_fn()
            if not res:
                return None
            try:
                from gerarPDF import salvar_e_abrir_pdf
                return salvar_e_abrir_pdf(res)
            except Exception:
                raise

        _run_report_in_background(_worker, descricao)


def relatorio_levantamento_necessidades():
    try:
        import levantamento_necessidades as _lev
    except Exception:
        _lev = None

    if _lev and hasattr(_lev, 'gerar_levantamento_necessidades'):
        try:
            _run_report_module_returning_buffer(_lev.gerar_levantamento_necessidades, "Levantamento de Necessidades")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao agendar levantamento de necessidades: {e}")
    else:
        messagebox.showerror("Erro", "Função 'gerar_levantamento_necessidades' não disponível. Verifique o módulo 'levantamento_necessidades'.")


def relatorio_contatos_responsaveis():
    try:
        import Lista_contatos_responsaveis as _cont
    except Exception:
        _cont = None

    if _cont and hasattr(_cont, 'gerar_pdf_contatos'):
        try:
            # A função `gerar_pdf_contatos` requer o parâmetro `ano_letivo` (ex.: 2025).
            # `obter_ano_letivo_atual()` retorna o ID do registro em AnosLetivos,
            # então precisamos converter esse ID para o valor do ano (coluna `ano_letivo`)
            # que o gerador espera receber.
            ano_param = None
            try:
                ano_id = obter_ano_letivo_atual()
                with get_connection() as _conn:
                    if _conn is not None:
                        _cur = _conn.cursor()
                        _cur.execute("SELECT ano_letivo FROM AnosLetivos WHERE id = %s", (int(str(ano_id)),))
                        _res = _cur.fetchone()
                        try:
                            _cur.close()
                        except Exception:
                            pass
                        if _res and _res[0] is not None:
                            try:
                                ano_param = int(str(_res[0]))
                            except Exception:
                                ano_param = None
            except Exception:
                ano_param = None

            # Fallback: usar o ano corrente se não conseguimos determinar o ano
            if not ano_param:
                from datetime import datetime as _dt
                ano_param = _dt.now().year

            _run_report_module_returning_buffer(lambda: _cont.gerar_pdf_contatos(ano_param), "Contatos de Responsáveis")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao agendar relatório de contatos: {e}")
    else:
        messagebox.showerror("Erro", "Função 'gerar_pdf_contatos' não disponível. Verifique o módulo 'Lista_contatos_responsaveis'.")


def relatorio_lista_alfabetica():
    try:
        import Lista_alunos_alfabetica as _alf
    except Exception:
        _alf = None

    if _alf and hasattr(_alf, 'lista_alfabetica'):
        try:
            _run_report_in_background(_alf.lista_alfabetica, "Lista Alfabética")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao agendar lista alfabética: {e}")
    else:
        messagebox.showerror("Erro", "Função 'lista_alfabetica' não disponível. Verifique o módulo 'Lista_alunos_alfabetica'.")


def relatorio_alunos_transtornos():
    try:
        import Lista_alunos_transtornos as _tr
    except Exception:
        _tr = None

    if _tr and hasattr(_tr, 'lista_alunos_transtornos'):
        try:
            _run_report_in_background(_tr.lista_alunos_transtornos, "Alunos com Transtornos")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao agendar relatório de transtornos: {e}")
    else:
        messagebox.showerror("Erro", "Função 'lista_alunos_transtornos' não disponível. Verifique o módulo 'Lista_alunos_transtornos'.")


def relatorio_termo_responsabilidade():
    try:
        import termo_responsabilidade_empresa as _term
    except Exception:
        _term = None

    if _term and hasattr(_term, 'gerar_termo_responsabilidade'):
        try:
            _fn = cast(Any, _term).gerar_termo_responsabilidade
            _run_report_in_background(_fn, "Termo de Responsabilidade")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao agendar termo de responsabilidade: {e}")
    else:
        messagebox.showerror("Erro", "Função 'gerar_termo_responsabilidade' não disponível. Verifique o módulo 'termo_responsabilidade_empresa'.")


def relatorio_tabela_docentes():
    try:
        import tabela_docentes as _td
    except Exception:
        _td = None

    if _td and hasattr(_td, 'gerar_tabela_docentes'):
        try:
            _run_report_module_returning_buffer(cast(Any, _td).gerar_tabela_docentes, "Tabela de Docentes")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao agendar tabela de docentes: {e}")
    else:
        messagebox.showerror("Erro", "Função 'gerar_tabela_docentes' não disponível. Verifique o módulo 'tabela_docentes'.")

# Import seguro para a interface de cadastro/edição de notas
try:
    import InterfaceCadastroEdicaoNotas as _InterfaceCadastroEdicaoNotas
except Exception:
    _InterfaceCadastroEdicaoNotas = None
# Import opcional de relatórios de movimentação mensal.
# Se o módulo não estiver disponível em tempo de import, definimos a
# variável como None para evitar avisos de nome não definido e permitir
# tratamento condicional em tempo de execução.
try:
    import movimentomensal
except Exception:
    movimentomensal = None
try:
    import boletim as _boletim_module
except Exception:
    _boletim_module = None

# Import seguro para gerar listas de reunião (wrapper)
try:
    import gerar_lista_reuniao as _gerar_lista_reuniao
except Exception:
    _gerar_lista_reuniao = None

# Import seguro para funções de notas (NotaAta)
try:
    import NotaAta as _NotaAta
except Exception:
    _NotaAta = None

# Serviço de relatórios centralizado (módulos legados delegados para services)
try:
    from services import report_service
except Exception:
    report_service = None

# Import seguro para a interface de Ata Geral
try:
    import AtaGeral as _AtaGeral
except Exception:
    _AtaGeral = None

def lista_reuniao():
    """Wrapper seguro para gerar a lista de reunião.
    Se o módulo estiver disponível, chama `gerar_lista_reuniao.gerar_lista_reuniao()`;
    caso contrário, mostra uma mensagem de erro amigável.
    """
    # Primeira opção: delegar para o serviço centralizado, se disponível
    if report_service is not None and hasattr(report_service, 'gerar_lista_reuniao'):
        try:
            logger.info("Chamando report_service.gerar_lista_reuniao() via menu")
            # Cast para Any para ajudar o verificador de tipos (Pylance) a entender
            # que `report_service` não é None no ramo protegido pelo if acima.
            resultado = cast(Any, report_service).gerar_lista_reuniao()
            logger.info("report_service.gerar_lista_reuniao() retornou: %s", resultado)
            return resultado
        except Exception as e:
            # Logar traceback completo para diagnóstico quando chamado pela UI
            logger.exception("Erro ao chamar report_service.gerar_lista_reuniao(): %s", e)
            # Mostrar mensagem mais informativa ao usuário
            tb = traceback.format_exc()
            messagebox.showerror("Erro", f"Falha ao gerar lista de reunião: {e}\n\nDetalhes técnicos foram registrados no log.")
            return None

    # Fallback: usar o módulo legado já importado de forma segura
    if _gerar_lista_reuniao and hasattr(_gerar_lista_reuniao, 'gerar_lista_reuniao'):
        # Bind the legacy function to a local variable (cast to Any) so the
        # background worker receives a concrete callable and static analyzers
        # (Pylance) do not complain about optional member access inside a lambda.
        _fn = cast(Any, _gerar_lista_reuniao).gerar_lista_reuniao
        _run_report_in_background(_fn, "Lista de Reunião")
        return None
    else:
        messagebox.showerror("Erro", "Função 'gerar_lista_reuniao' não disponível. Verifique o módulo 'gerar_lista_reuniao'.")
        return None

# Import seguro para lista de notas
try:
    import Lista_notas as _lista_notas
except Exception:
    _lista_notas = None

def lista_notas():
    """Wrapper seguro para gerar a lista de notas.
    Chama `Lista_notas.lista_notas()` se disponível; caso contrário exibe erro.
    """
    # Tenta delegar para o serviço centralizado quando disponível
    if report_service is not None and hasattr(report_service, 'gerar_lista_notas'):
        try:
            return report_service.gerar_lista_notas()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar lista de notas: {e}")
            return None

    # Fallback para módulo legado
    if _lista_notas and hasattr(_lista_notas, 'lista_notas'):
        _fn = cast(Any, _lista_notas).lista_notas
        _run_report_in_background(_fn, "Lista de Notas")
        return None
    else:
        messagebox.showerror("Erro", "Função 'lista_notas' não disponível. Verifique o módulo 'Lista_notas'.")
        return None

# Import seguro para lista de frequência
try:
    import lista_frequencia as _lista_frequencia
except Exception:
    _lista_frequencia = None

def lista_frequencia():
    """Wrapper seguro para gerar a lista de frequência.
    Chama `lista_frequencia.lista_frequencia()` se disponível; caso contrário exibe erro.
    """
    # Tenta delegar para o serviço centralizado quando disponível
    if report_service is not None and hasattr(report_service, 'gerar_lista_frequencia'):
        try:
            return report_service.gerar_lista_frequencia()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar lista de frequência: {e}")
            return None

    # Fallback para módulo legado
    if _lista_frequencia and hasattr(_lista_frequencia, 'lista_frequencia'):
        _fn = cast(Any, _lista_frequencia).lista_frequencia
        _run_report_in_background(_fn, "Lista de Frequência")
        return None


def lista_atualizada_wrapper():
    try:
        if hasattr(Lista_atualizada, 'lista_atualizada'):
            _run_report_in_background(Lista_atualizada.lista_atualizada, "Lista Atualizada")
        else:
            messagebox.showerror("Erro", "Função 'lista_atualizada' não disponível no módulo Lista_atualizada.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao gerar Lista Atualizada: {e}")


def lista_atualizada_semed_wrapper():
    try:
        if hasattr(Lista_atualizada_semed, 'lista_atualizada'):
            _run_report_in_background(Lista_atualizada_semed.lista_atualizada, "Lista Atualizada SEMED")
        else:
            messagebox.showerror("Erro", "Função 'lista_atualizada' não disponível no módulo Lista_atualizada_semed.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao gerar Lista Atualizada SEMED: {e}")
    # NOTE: Não usar `else:` aqui — bloco `else` em `try/except/else` executa quando
    # não houve exceção, o que causava a exibição indevida de uma mensagem de erro
    # mesmo quando a geração foi agendada com sucesso. Removido para comportamento correto.

def gerar_relatorio_notas(*args, **kwargs):
    """Wrapper para `NotaAta.gerar_relatorio_notas`"""
    # Primeira opção: delegar para o service centralizado quando disponível
    if report_service is not None and hasattr(report_service, 'gerar_relatorio_notas'):
        try:
            return report_service.gerar_relatorio_notas(*args, **kwargs)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório de notas: {e}")
            return None

    # Fallback para o módulo legado
    if _NotaAta and hasattr(_NotaAta, 'gerar_relatorio_notas'):
        try:
            return _NotaAta.gerar_relatorio_notas(*args, **kwargs)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório de notas: {e}")
            return None
    else:
        messagebox.showerror("Erro", "Função 'gerar_relatorio_notas' não disponível. Verifique o módulo 'NotaAta'.")
        return None

def gerar_relatorio_notas_com_assinatura(*args, **kwargs):
    """Wrapper para `NotaAta.gerar_relatorio_notas_com_assinatura`"""
    if _NotaAta and hasattr(_NotaAta, 'gerar_relatorio_notas_com_assinatura'):
        try:
            return _NotaAta.gerar_relatorio_notas_com_assinatura(*args, **kwargs)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório com assinatura: {e}")
            return None
    else:
        messagebox.showerror("Erro", "Função 'gerar_relatorio_notas_com_assinatura' não disponível. Verifique o módulo 'NotaAta'.")
        return None

def relatorio_movimentacao_mensal(numero_mes):
    # Tenta delegar para o serviço centralizado quando disponível
    if report_service is not None and hasattr(report_service, 'gerar_relatorio_movimentacao_mensal'):
        try:
            return report_service.gerar_relatorio_movimentacao_mensal(numero_mes)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório de movimentação: {e}")
            return None

    # Fallback para módulo legado
    if movimentomensal and hasattr(movimentomensal, 'relatorio_movimentacao_mensal'):
        try:
            return movimentomensal.relatorio_movimentacao_mensal(numero_mes)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório de movimentação: {e}")
            return None

    messagebox.showerror("Erro", "Função 'relatorio_movimentacao_mensal' não disponível. Verifique o módulo 'movimentomensal' ou o serviço de relatórios.")
    return None

def boletim(aluno_id, ano_letivo_id=None):
    # Tenta delegar para o serviço centralizado quando disponível
    if report_service is not None and hasattr(report_service, 'gerar_boletim'):
        try:
            report_service.gerar_boletim(aluno_id, ano_letivo_id)
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar boletim: {e}")
            return None

    # Fallback para módulo legado quando o service não estiver disponível
    if _boletim_module and hasattr(_boletim_module, 'boletim'):
        try:
            return _boletim_module.boletim(aluno_id, ano_letivo_id)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar boletim: {e}")
            return None

    messagebox.showerror("Erro", "Função 'boletim' não disponível. Verifique o módulo 'boletim' ou o serviço de relatórios.")
    return None

def nota_bimestre(bimestre=None, preencher_nulos=False):
    if _NotaAta and hasattr(_NotaAta, 'nota_bimestre'):
        return _NotaAta.nota_bimestre(bimestre, preencher_nulos=preencher_nulos)
    else:
        messagebox.showerror("Erro", "Função 'nota_bimestre' não disponível. Verifique o módulo 'NotaAta'.")
        return None

def nota_bimestre2(bimestre=None, preencher_nulos=False):
    if _NotaAta and hasattr(_NotaAta, 'nota_bimestre2'):
        return _NotaAta.nota_bimestre2(bimestre, preencher_nulos=preencher_nulos)
    else:
        messagebox.showerror("Erro", "Função 'nota_bimestre2' não disponível. Verifique o módulo 'NotaAta'.")
        return None

def nota_bimestre_com_assinatura(bimestre=None, preencher_nulos=False):
    if _NotaAta and hasattr(_NotaAta, 'nota_bimestre_com_assinatura'):
        return _NotaAta.nota_bimestre_com_assinatura(bimestre, preencher_nulos=preencher_nulos)
    else:
        messagebox.showerror("Erro", "Função 'nota_bimestre_com_assinatura' não disponível. Verifique o módulo 'NotaAta'.")
        return None

def nota_bimestre2_com_assinatura(bimestre=None, preencher_nulos=False):
    if _NotaAta and hasattr(_NotaAta, 'nota_bimestre2_com_assinatura'):
        return _NotaAta.nota_bimestre2_com_assinatura(bimestre, preencher_nulos=preencher_nulos)
    else:
        messagebox.showerror("Erro", "Função 'nota_bimestre2_com_assinatura' não disponível. Verifique o módulo 'NotaAta'.")
        return None

def abrir_interface_ata(janela_pai=None, status_label=None):
    if _AtaGeral and hasattr(_AtaGeral, 'abrir_interface_ata'):
        try:
            return _AtaGeral.abrir_interface_ata(janela_pai, status_label)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao abrir interface de Ata: {e}")
            return None
    else:
        # Tenta import dinâmico como fallback
        try:
            from AtaGeral import abrir_interface_ata as _abrir_ata_dyn
            return _abrir_ata_dyn(janela_pai, status_label)
        except Exception as e:
            messagebox.showerror("Erro", f"Função 'abrir_interface_ata' não disponível: {e}")
            return None

# Flag de teste: quando True, desativa o sistema de backup automático
# para permitir testes manuais da interface sem que o app feche automaticamente.
# Defina para False antes de commitar para produção.
# Variáveis globais de fallback para evitar avisos estáticos
query = None

TEST_MODE = True

# Importar utilitários compartilhados
from utils.safe import converter_para_int_seguro, _safe_get, _safe_slice

def obter_ano_letivo_atual() -> int:
    """Retorna o `id` do ano letivo atual. Se não encontrar, retorna o id do ano letivo mais recente.

    Usa `get_connection()` para consultar a tabela `AnosLetivos`.
    Em caso de erro retorna `1` como fallback seguro.
    """
    try:
        with get_connection() as conn:
            if conn is None:
                return 1
            cur = conn.cursor()
            cur.execute("SELECT id FROM AnosLetivos WHERE ano_letivo = YEAR(CURDATE())")
            res = cur.fetchone()
            if not res:
                cur.execute("SELECT id FROM AnosLetivos ORDER BY ano_letivo DESC LIMIT 1")
                res = cur.fetchone()
            try:
                cur.close()
            except Exception:
                pass
            # Usar conversor seguro para evitar passar tipos inesperados (ex.: date)
            return converter_para_int_seguro(res[0]) if res and res[0] is not None else 1
    except Exception as e:
        logger.error(f"Erro ao obter ano letivo atual: {e}")
        return 1
from horarios_escolares import InterfaceHorariosEscolares
from tkinter import filedialog
try:
    from preencher_folha_ponto import gerar_folhas_de_ponto as _gerar_folhas_de_ponto_legacy, nome_mes_pt as nome_mes_pt_folha
except Exception:
    _gerar_folhas_de_ponto_legacy = None
    # Fallback: usar utilitário consolidado para nome do mês
    from utils.dates import nome_mes_pt as nome_mes_pt_folha
# Import seguro para resumo de ponto — importamos o módulo como fallback
try:
    from gerar_resumo_ponto import nome_mes_pt as nome_mes_pt_resumo  # type: ignore
    import gerar_resumo_ponto as _gerar_resumo_ponto  # type: ignore
except Exception:
    _gerar_resumo_ponto = None
    # Fallback: usar utilitário consolidado para nome do mês
    from utils.dates import nome_mes_pt as nome_mes_pt_resumo


def gerar_resumo_ponto(*args, **kwargs):
    """Wrapper para `gerar_resumo_ponto.gerar_resumo_ponto`.

    Primeiro tenta delegar ao `report_service` se disponível; caso contrário
    usa o módulo legado `gerar_resumo_ponto` quando presente.
    """
    # Delegar para service quando disponível
    if report_service is not None and hasattr(report_service, 'gerar_resumo_ponto'):
        try:
            return report_service.gerar_resumo_ponto(*args, **kwargs)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar resumo de ponto: {e}")
            return None

    # Fallback para o módulo legado
    if _gerar_resumo_ponto and hasattr(_gerar_resumo_ponto, 'gerar_resumo_ponto'):
        try:
            return _gerar_resumo_ponto.gerar_resumo_ponto(*args, **kwargs)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar resumo de ponto: {e}")
            return None

    messagebox.showerror("Erro", "Função 'gerar_resumo_ponto' não disponível. Verifique o módulo 'gerar_resumo_ponto' ou o serviço de relatórios.")
    return None


def gerar_folhas_de_ponto(*args, **kwargs):
    """Wrapper para `preencher_folha_ponto.gerar_folhas_de_ponto`.

    Primeiro tenta delegar ao `report_service` se disponível; caso contrário
    usa o módulo legado `preencher_folha_ponto` quando presente.
    """
    # Delegar para service quando disponível
    if report_service is not None and hasattr(report_service, 'gerar_folhas_de_ponto'):
        try:
            return report_service.gerar_folhas_de_ponto(*args, **kwargs)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar folhas de ponto: {e}")
            return None

    # Fallback para o módulo legado
    if _gerar_folhas_de_ponto_legacy and hasattr(_gerar_folhas_de_ponto_legacy, 'gerar_folhas_de_ponto'):
        try:
            return _gerar_folhas_de_ponto_legacy(*args, **kwargs)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar folhas de ponto: {e}")
            return None

    messagebox.showerror("Erro", "Função 'gerar_folhas_de_ponto' não disponível. Verifique o módulo 'preencher_folha_ponto' ou o serviço de relatórios.")
    return None
from GerenciadorDocumentosFuncionarios import GerenciadorDocumentosFuncionarios
from declaracao_comparecimento import gerar_declaracao_comparecimento_responsavel


# NOVAS Cores
co0 = "#F5F5F5"  # Branco suave para o fundo (substituindo o branco puro)
co1 = "#003A70"  # Azul escuro (mantido para identidade visual)
co2 = "#77B341"  # Verde (mantido)
co3 = "#E2418E"  # Rosa/Magenta (mantido)
co4 = "#4A86E8"  # Azul mais claro (substituindo o azul médio para melhor contraste)
co5 = "#F26A25"  # Laranja (mantido)
co6 = "#F7B731"  # Amarelo (mantido)
co7 = "#333333"  # Cinza escuro (substituindo o preto para suavizar)
co8 = "#BF3036"  # Vermelho (mantido)
co9 = "#6FA8DC"  # Azul claro (substituindo o azul claro anterior para melhor harmonia)
selected_item = None
label_rodape = None
status_label = None
dashboard_manager = None


# ============================================================================
# MELHORIA 4: Inicializar Connection Pool
# Inicializa o pool de conexões no início da aplicação para melhor performance
# ============================================================================
logger.info("Inicializando sistema...")
inicializar_pool()


# Criar a janela
janela = Tk()
# Tentar obter o nome da escola a partir do banco; usar fallback simples se falhar
try:
    nome_escola = "Escola"
    try:
        with get_connection() as _conn:
            _cur = _conn.cursor()
            _cur.execute("SELECT nome FROM Escolas WHERE id = %s", (60,))
            _res = _cur.fetchone()
            if _res and _res[0]:
                nome_escola = str(_res[0])
            try:
                _cur.close()
            except Exception:
                pass
    except Exception:
        # Se qualquer erro de BD ocorrer, manter o fallback
        nome_escola = "Escola"
except Exception:
    nome_escola = "Escola"

janela.title(f"Sistema de Gerenciamento da {nome_escola}")
janela.geometry('850x670')
janela.configure(background=co1)
janela.resizable(width=TRUE, height=TRUE)

# Configurar a janela para expandir
janela.grid_rowconfigure(0, weight=0)  # Logo (não expande verticalmente)
janela.grid_rowconfigure(1, weight=0)  # Separador (não expande)
janela.grid_rowconfigure(2, weight=0)  # Dados (não expande)
janela.grid_rowconfigure(3, weight=0)  # Separador (não expande)
janela.grid_rowconfigure(4, weight=1)  # Detalhes (expande)
janela.grid_rowconfigure(5, weight=0)  # Separador (não expande)
janela.grid_rowconfigure(6, weight=1)  # Tabela (expande)
janela.grid_rowconfigure(7, weight=0)  # Separador (não expande)
janela.grid_rowconfigure(8, weight=0)  # Rodapé (não expande)

# Configuração da coluna principal para expandir
janela.grid_columnconfigure(0, weight=1)  # Coluna principal (expande horizontalmente)

style = Style(janela)
style.theme_use("clam")

# Configuração de estilos personalizados
style.configure("TButton", background=co4, foreground=co0, font=('Ivy', 10))
style.configure("TLabel", background=co1, foreground=co0, font=('Ivy', 10))
style.configure("TEntry", background=co0, font=('Ivy', 10))
style.map("TButton", background=[('active', co2)], foreground=[('active', co0)])


# Frames
def criar_frames():
    global frame_logo, frame_dados, frame_detalhes, frame_tabela
    
    # Criar os frames
    frame_logo = Frame(janela, height=70, bg=co0)  # Alterado para fundo branco (co0) e aumentado a altura
    frame_logo.grid(row=0, column=0, pady=0, padx=0, sticky=NSEW)
    frame_logo.grid_propagate(False)  # Impede que o frame mude de tamanho com base no conteúdo
    frame_logo.grid_columnconfigure(0, weight=1)  # Permite que o conteúdo do frame se expanda horizontalmente

    ttk.Separator(janela, orient=HORIZONTAL).grid(row=1, columnspan=1, sticky=EW)

    frame_dados = Frame(janela, height=65, bg=co1)
    frame_dados.grid(row=2, column=0, pady=0, padx=0, sticky=NSEW)

    ttk.Separator(janela, orient=HORIZONTAL).grid(row=3, columnspan=1, sticky=EW)

    frame_detalhes = Frame(janela, bg=co1)
    frame_detalhes.grid(row=4, column=0, pady=0, padx=10, sticky=NSEW)
    
    # Configurar frame_detalhes para expandir
    frame_detalhes.grid_columnconfigure(0, weight=1)
    frame_detalhes.grid_rowconfigure(0, weight=1)

    frame_tabela = Frame(janela, bg=co1)
    frame_tabela.grid(row=6, column=0, pady=0, padx=10, sticky=NSEW)
    
    # Configurar frame_tabela para expandir
    frame_tabela.grid_columnconfigure(0, weight=1)
    
    # Separador 4 (entre a tabela e o rodapé)
    ttk.Separator(janela, orient=HORIZONTAL).grid(row=7, column=0, sticky=EW)

# ============================================================================
# MELHORIA 1: Dashboard com Gráfico de Pizza
# ============================================================================

# Variável global para controlar o canvas do dashboard
dashboard_canvas = None

def criar_dashboard():
    # Delega a criação do dashboard ao DashboardManager (instanciado mais abaixo).
    try:
        if 'dashboard_manager' in globals() and dashboard_manager:
            return dashboard_manager.criar_dashboard()
    except Exception:
        pass
    return None

def atualizar_dashboard():
    """
    Força a atualização do cache e recria o dashboard.
    """
    try:
        if 'dashboard_manager' in globals() and dashboard_manager:
            dashboard_manager.atualizar_dashboard()
            messagebox.showinfo("Dashboard", "Dashboard atualizado com sucesso!")
            return
    except Exception:
        pass

    # Fallback: limpar cache e recriar via função antiga
    _cache_estatisticas_dashboard['timestamp'] = None
    _cache_estatisticas_dashboard['dados'] = None
    criar_dashboard()
    messagebox.showinfo("Dashboard", "Dashboard atualizado com sucesso!")

def criar_tabela():
    global treeview, tabela_frame
    # Nota: Esta função não realiza operações diretas ao banco de dados.
    # Dados e exibição são construídos a partir de estruturas em memória (ex.: `df`).
    # Não é necessário abrir/fechar conexões aqui; manter o padrão de conexões curtas em outras funções.
    
    # Frame para conter a tabela e sua barra de rolagem
    tabela_frame = Frame(frame_tabela)
    # NÃO fazer pack aqui - será controlado pelo sistema de pesquisa
    
    # Configurando o gerenciador de layout
    tabela_frame.grid_rowconfigure(0, weight=1)
    tabela_frame.grid_columnconfigure(0, weight=1)
    
    # Criar um estilo
    style = ttk.Style()
    style.configure("mystyle.Treeview", highlightthickness=0, bd=0, font=('Calibri', 11))
    style.configure("mystyle.Treeview.Heading", font=('Calibri', 13, 'bold'), background=co1, foreground=co0)
    
    # Configurar cores para linhas selecionadas
    style.map('mystyle.Treeview',
        background=[('selected', co4)],
        foreground=[('selected', co0)])
    
    style.layout("mystyle.Treeview", [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])
    
    # Garantir colunas e df padrão caso não estejam definidos ainda
    global colunas, df
    # Usar globals().get para evitar referência a variável possivelmente não associada
    if 'colunas' not in globals() or not globals().get('colunas'):
        colunas = ['ID', 'Nome']
    if 'df' not in globals() or globals().get('df') is None:
        df = pd.DataFrame(columns=colunas)

    # Criação do Treeview com barras de rolagem
    treeview = ttk.Treeview(tabela_frame, style="mystyle.Treeview", columns=colunas, show='headings')
    
    # Configurar barras de rolagem
    vsb = ttk.Scrollbar(tabela_frame, orient="vertical", command=treeview.yview)
    hsb = ttk.Scrollbar(tabela_frame, orient="horizontal", command=treeview.xview)
    treeview.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    # Posicionar os componentes
    treeview.grid(row=0, column=0, sticky=NSEW)
    vsb.grid(row=0, column=1, sticky=NS)
    hsb.grid(row=1, column=0, sticky=EW)
    
    # Configuração das colunas
    for col in colunas:
        treeview.heading(col, text=col, anchor=W)
        treeview.column(col, width=120, anchor=W)
    
    # Adicionar dados iniciais
    for i, row in df.iterrows():
        row = list(row)
        # Padronizar data de nascimento (índice 4)
        if row[4]:
            try:
                if isinstance(row[4], str):
                    # Tenta converter string para data
                    data = datetime.strptime(row[4], '%Y-%m-%d')
                elif isinstance(row[4], (datetime, date)):
                    data = row[4]
                else:
                    continue  # Pula se não for um tipo de data válido
                row[4] = data.strftime('%d/%m/%Y')
            except Exception:
                pass  # Se não conseguir converter, deixa como está
        treeview.insert("", "end", values=row)
    
    # Vincular evento de clique único e duplo
    treeview.bind("<ButtonRelease-1>", selecionar_item)
    treeview.bind("<Double-1>", selecionar_item)
    
    # Vincular eventos de teclado para navegação
    treeview.bind("<Up>", on_select)
    treeview.bind("<Down>", on_select)
    treeview.bind("<Prior>", on_select)  # Page Up
    treeview.bind("<Next>", on_select)   # Page Down
    treeview.bind("<Home>", on_select)   # Home
    treeview.bind("<End>", on_select)    # End
    
    # Adicionar dica/instrução visual para o usuário
    instrucao_label = Label(frame_tabela, text="Clique ou use as setas do teclado para selecionar um item", 
                         font=('Ivy 10 italic'), bg=co1, fg=co0)
    # NÃO fazer pack do label - será mostrado junto com a tabela quando necessário
    
    # IMPORTANTE: Exibir dashboard por padrão ao invés da tabela
    criar_dashboard()

def selecionar_item(event):
    # Obtém o item selecionado
    item = treeview.identify_row(event.y)
    if not item:
        return
    
    # Seleciona o item na tabela visualmente
    treeview.selection_set(item)
    
    # Obtém os valores do item
    valores = treeview.item(item, "values")
    if not valores:
        return
    
    # Obtém o ID e o tipo (aluno ou funcionário)
    id_item = valores[0]
    tipo_item = valores[2]
    
    # Primeiro, definir o título no frame_logo e limpar apenas o frame_detalhes
    # Não redefinimos todos os frames para evitar recriar a pesquisa
    for widget in frame_detalhes.winfo_children():
        widget.destroy()
    
    # Carregar a nova imagem e definir o título apropriado
    global app_lp, app_img_voltar
    
    # Limpar o frame do logo antes de adicionar o título
    for widget in frame_logo.winfo_children():
        widget.destroy()
    
    # Criar um frame dentro do frame_logo para o título
    titulo_frame = Frame(frame_logo, bg=co0)  # Alterado para fundo branco
    titulo_frame.pack(fill=BOTH, expand=True)
    
    try:
        app_lp = Image.open('icon/learning.png')
        app_lp = app_lp.resize((30, 30))
        app_lp = ImageTk.PhotoImage(app_lp)
        app_logo = Label(titulo_frame, image=app_lp, text=f"Detalhes: {valores[1]}", compound=LEFT,
                        anchor=W, font=('Ivy 15 bold'), bg=co0, fg=co1, padx=10, pady=5)  # Alterado para fundo branco e texto azul
        # Manter referência à imagem para evitar garbage collection
        setattr(app_logo, '_image_ref', app_lp)
        app_logo.pack(fill=X, expand=True)
    except:
        # Fallback sem ícone
        app_logo = Label(titulo_frame, text=f"Detalhes: {valores[1]}", 
                        anchor=W, font=('Ivy 15 bold'), bg=co0, fg=co1, padx=10, pady=5)  # Alterado para fundo branco e texto azul
        app_logo.pack(fill=X, expand=True)
    
    # Adiciona os botões de ações específicas para o item selecionado
    criar_botoes_frame_detalhes(tipo_item, valores)
    
    # Mostra outros detalhes do item em formato de grid (múltiplas colunas)
    detalhes_info_frame = Frame(frame_detalhes, bg=co1)
    detalhes_info_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
    
    # Configurar o grid para 3 colunas
    for i in range(3):
        detalhes_info_frame.grid_columnconfigure(i, weight=1, uniform="col")
    
    if tipo_item == "Aluno":
        # Linha 1: ID, Nome e Data de Nascimento
        Label(detalhes_info_frame, text=f"ID: {valores[0]}", bg=co1, fg=co0, 
              font=('Ivy 10 bold'), anchor=W).grid(row=0, column=0, sticky=EW, padx=5, pady=3)
        Label(detalhes_info_frame, text=f"Nome: {valores[1]}", bg=co1, fg=co0, 
              font=('Ivy 10 bold'), anchor=W).grid(row=0, column=1, columnspan=2, sticky=EW, padx=5, pady=3)
        
        Label(detalhes_info_frame, text=f"Data de Nascimento: {valores[4]}", bg=co1, fg=co0, 
              font=('Ivy 10'), anchor=W).grid(row=1, column=0, sticky=EW, padx=5, pady=3)
        
        # ============================================================================
        # OTIMIZAÇÃO 3: Consulta consolidada em uma única query
        # Busca responsáveis E matrícula em uma única ida ao banco
        # ============================================================================
        cursor = None
        try:
            with get_connection() as conn:
                if conn is None:
                    logger.error("Erro: Não foi possível conectar ao banco de dados.")
                    return
                cursor = conn.cursor()

                # Usar o ano letivo do cache
                ano_letivo_id = obter_ano_letivo_atual()

                # CONSULTA OTIMIZADA: Buscar todos os dados necessários de uma só vez
                cursor.execute("""
                SELECT 
                    -- Dados da matrícula
                    m.status, 
                    m.data_matricula,
                    s.nome as serie_nome,
                    t.nome as turma_nome,
                    t.id as turma_id,
                    -- Data de transferência (subquery)
                    (SELECT hm.data_mudanca 
                     FROM historico_matricula hm 
                     WHERE hm.matricula_id = m.id 
                     AND hm.status_novo IN ('Transferido', 'Transferida')
                     ORDER BY hm.data_mudanca DESC 
                     LIMIT 1) as data_transferencia,
                    -- Responsáveis (usando GROUP_CONCAT para pegar em uma query)
                    GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Mãe' THEN r.nome END) as nome_mae,
                    GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Pai' THEN r.nome END) as nome_pai
                FROM alunos a
                LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s AND m.status IN ('Ativo', 'Transferido')
                LEFT JOIN turmas t ON m.turma_id = t.id AND t.escola_id = 60
                LEFT JOIN serie s ON t.serie_id = s.id
                LEFT JOIN responsaveisalunos ra ON a.id = ra.aluno_id
                LEFT JOIN responsaveis r ON ra.responsavel_id = r.id AND r.grau_parentesco IN ('Mãe', 'Pai')
                WHERE a.id = %s
                GROUP BY m.id, m.status, m.data_matricula, s.nome, t.nome, t.id
                ORDER BY m.data_matricula DESC
                LIMIT 1
            """, (ano_letivo_id, converter_para_int_seguro(id_item)))
            
            resultado = cursor.fetchone()
            
            # Processar responsáveis (extração segura)
            nome_mae = _safe_get(resultado, 6)
            nome_pai = _safe_get(resultado, 7)
            
            # Exibir nomes dos pais na linha 2
            if nome_mae:
                Label(detalhes_info_frame, text=f"Mãe: {nome_mae}", bg=co1, fg=co0, 
                      font=('Ivy 10'), anchor=W).grid(row=2, column=0, columnspan=2, sticky=EW, padx=5, pady=3)
            
            if nome_pai:
                Label(detalhes_info_frame, text=f"Pai: {nome_pai}", bg=co1, fg=co0, 
                      font=('Ivy 10'), anchor=W).grid(row=2, column=2, sticky=EW, padx=5, pady=3)
            
            if resultado:
                vals = _safe_slice(resultado, 0, 6)
                if len(vals) < 6:
                    vals = vals + [None] * (6 - len(vals))
                status, data_matricula, serie_nome, turma_nome, turma_id, data_transferencia = vals

                row_atual = 3  # Começar na linha 3, pois linhas 0, 1 e 2 já foram usadas

                if status == 'Ativo' and data_matricula:
                    # Formatar data de matrícula adequadamente
                    try:
                        if isinstance(data_matricula, str):
                            data_formatada = datetime.strptime(data_matricula, '%Y-%m-%d').strftime('%d/%m/%Y')
                        elif isinstance(data_matricula, (datetime, date)):
                            data_formatada = data_matricula.strftime('%d/%m/%Y')
                        else:
                            data_formatada = str(data_matricula)
                    except Exception:
                        data_formatada = str(data_matricula)

                    Label(detalhes_info_frame, 
                          text=f"Data de Matrícula: {data_formatada}", 
                          bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=1, column=1, sticky=EW, padx=5, pady=3)

                    # Adicionar informações de série e turma para alunos ativos
                    if serie_nome:
                        Label(detalhes_info_frame, 
                              text=f"Série: {serie_nome}", 
                              bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)

                    if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                        Label(detalhes_info_frame, 
                              text=f"Turma: {turma_nome}", 
                              bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=2, column=0, sticky=EW, padx=5, pady=3)
                    else:
                        # Se o nome da turma estiver vazio, mostrar "Turma Única" ou o ID
                        # Já temos o turma_id da consulta anterior
                        turma_texto = f"Turma: Turma {turma_id}" if turma_id else "Turma: Não definida"
                        Label(detalhes_info_frame, 
                              text=turma_texto, 
                              bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=2, column=0, sticky=EW, padx=5, pady=3)

                elif status == 'Transferido' and data_transferencia:
                    # Formatar data de transferência adequadamente
                    try:
                        if isinstance(data_transferencia, str):
                            data_transf_formatada = datetime.strptime(data_transferencia, '%Y-%m-%d').strftime('%d/%m/%Y')
                        elif isinstance(data_transferencia, (datetime, date)):
                            data_transf_formatada = data_transferencia.strftime('%d/%m/%Y')
                        else:
                            data_transf_formatada = str(data_transferencia)
                    except Exception:
                        data_transf_formatada = str(data_transferencia)

                    Label(detalhes_info_frame, 
                          text=f"Data de Transferência: {data_transf_formatada}", 
                          bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=1, column=1, sticky=EW, padx=5, pady=3)

                    # Para alunos transferidos, também mostrar a série/turma da última matrícula
                    if serie_nome:
                        Label(detalhes_info_frame, 
                              text=f"Última Série: {serie_nome}", 
                              bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)

                    if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                        Label(detalhes_info_frame, 
                              text=f"Última Turma: {turma_nome}", 
                              bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)
                    else:
                        # Se o nome da turma estiver vazio, mostrar "Turma Única" ou o ID
                        # Já temos o turma_id da consulta anterior
                        turma_texto = f"Última Turma: Turma {turma_id}" if turma_id else "Última Turma: Não definida"
                        Label(detalhes_info_frame, 
                              text=turma_texto, 
                              bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)
        
        except Exception as e:
            logger.error(f"Erro ao verificar matrícula: {str(e)}")
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass
                
    elif tipo_item == "Funcionário":
        # Linha 1: ID e Nome
        Label(detalhes_info_frame, text=f"ID: {valores[0]}", bg=co1, fg=co0, 
              font=('Ivy 10 bold'), anchor=W).grid(row=0, column=0, sticky=EW, padx=5, pady=3)
        Label(detalhes_info_frame, text=f"Nome: {valores[1]}", bg=co1, fg=co0, 
              font=('Ivy 10 bold'), anchor=W).grid(row=0, column=1, columnspan=2, sticky=EW, padx=5, pady=3)
        
        # Linha 2: Cargo e Data de Nascimento
        Label(detalhes_info_frame, text=f"Cargo: {valores[3]}", bg=co1, fg=co0, 
              font=('Ivy 10'), anchor=W).grid(row=1, column=0, columnspan=2, sticky=EW, padx=5, pady=3)
        Label(detalhes_info_frame, text=f"Data de Nascimento: {valores[4]}", bg=co1, fg=co0, 
              font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)

def on_select(event):
    # Função para eventos de teclado - aguarda um pouco para a seleção ser atualizada
    # Usa after() para garantir que a seleção do treeview seja atualizada primeiro
    def processar_selecao():
        # Obtém o item atualmente selecionado
        selected_items = treeview.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        
        # Obtém os valores do item
        valores = treeview.item(item, "values")
        if not valores:
            return
        
        # Obtém o ID e o tipo (aluno ou funcionário)
        id_item = valores[0]
        tipo_item = valores[2]
        
        # Limpar frames necessários
        for widget in frame_logo.winfo_children():
            widget.destroy()
        
        for widget in frame_detalhes.winfo_children():
            widget.destroy()
        
        # Criar um frame dentro do frame_logo para o título
        titulo_frame = Frame(frame_logo, bg=co0)
        titulo_frame.pack(fill=BOTH, expand=True)
        
        try:
            app_lp = Image.open('icon/learning.png')
            app_lp = app_lp.resize((30, 30))
            app_lp = ImageTk.PhotoImage(app_lp)
            titulo_texto = f"Detalhes do {tipo_item}"
            app_logo = Label(titulo_frame, image=app_lp, text=titulo_texto, compound=LEFT,
                            anchor=W, font=('Ivy 15 bold'), bg=co0, fg=co1, padx=10, pady=5)
            # Manter referência à imagem para evitar garbage collection
            setattr(app_logo, '_image_ref', app_lp)
            app_logo.pack(fill=X, expand=True)
        except:
            titulo_texto = f"Detalhes do {tipo_item}"
            app_logo = Label(titulo_frame, text=titulo_texto, 
                            anchor=W, font=('Ivy 15 bold'), bg=co0, fg=co1, padx=10, pady=5)
            app_logo.pack(fill=X, expand=True)
        
        # Criar botões de ação primeiro (no topo)
        criar_botoes_frame_detalhes(tipo_item, valores)
        
        # Frame para exibir os detalhes em grid (abaixo dos botões)
        detalhes_info_frame = Frame(frame_detalhes, bg=co1)
        detalhes_info_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Configurar o grid para 3 colunas
        for i in range(3):
            detalhes_info_frame.grid_columnconfigure(i, weight=1, uniform="col")
        
        # Exibir informações conforme o tipo
        if tipo_item == "Aluno":
            # Linha 1: ID, Nome
            Label(detalhes_info_frame, text=f"ID: {valores[0]}", bg=co1, fg=co0, 
                  font=('Ivy 10 bold'), anchor=W).grid(row=0, column=0, sticky=EW, padx=5, pady=3)
            Label(detalhes_info_frame, text=f"Nome: {valores[1]}", bg=co1, fg=co0, 
                  font=('Ivy 10 bold'), anchor=W).grid(row=0, column=1, columnspan=2, sticky=EW, padx=5, pady=3)
            
            Label(detalhes_info_frame, text=f"Data de Nascimento: {valores[4]}", bg=co1, fg=co0, 
                  font=('Ivy 10'), anchor=W).grid(row=1, column=0, sticky=EW, padx=5, pady=3)
            
            # ============================================================================
            # OTIMIZAÇÃO 3: Consulta consolidada (mesmo padrão da função selecionar_item)
            # ============================================================================
            cursor = None
            try:
                with get_connection() as conn:
                    if conn is None:
                        logger.error("Erro: Não foi possível conectar ao banco de dados.")
                        return
                    cursor = conn.cursor()

                    # Usar o ano letivo do cache
                    ano_letivo_id = obter_ano_letivo_atual()

                    # CONSULTA OTIMIZADA: Buscar todos os dados necessários de uma só vez
                    cursor.execute("""
                    SELECT 
                        -- Dados da matrícula
                        m.status, 
                        m.data_matricula,
                        s.nome as serie_nome,
                        t.nome as turma_nome,
                        t.id as turma_id,
                        -- Data de transferência (subquery)
                        (SELECT hm.data_mudanca 
                         FROM historico_matricula hm 
                         WHERE hm.matricula_id = m.id 
                         AND hm.status_novo IN ('Transferido', 'Transferida')
                         ORDER BY hm.data_mudanca DESC 
                         LIMIT 1) as data_transferencia,
                        -- Responsáveis
                        GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Mãe' THEN r.nome END) as nome_mae,
                        GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Pai' THEN r.nome END) as nome_pai
                    FROM alunos a
                    LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s AND m.status IN ('Ativo', 'Transferido')
                    LEFT JOIN turmas t ON m.turma_id = t.id AND t.escola_id = 60
                    LEFT JOIN serie s ON t.serie_id = s.id
                    LEFT JOIN responsaveisalunos ra ON a.id = ra.aluno_id
                    LEFT JOIN responsaveis r ON ra.responsavel_id = r.id AND r.grau_parentesco IN ('Mãe', 'Pai')
                    WHERE a.id = %s
                    GROUP BY m.id, m.status, m.data_matricula, s.nome, t.nome, t.id
                    ORDER BY m.data_matricula DESC
                    LIMIT 1
                """, (ano_letivo_id, converter_para_int_seguro(id_item)))
                
                resultado = cursor.fetchone()
                
                # Processar responsáveis (extração segura)
                nome_mae = _safe_get(resultado, 6)
                nome_pai = _safe_get(resultado, 7)
                
                # Exibir nomes dos pais na linha 2
                if nome_mae:
                    Label(detalhes_info_frame, text=f"Mãe: {nome_mae}", bg=co1, fg=co0, 
                          font=('Ivy 10'), anchor=W).grid(row=2, column=0, columnspan=2, sticky=EW, padx=5, pady=3)
                
                if nome_pai:
                    Label(detalhes_info_frame, text=f"Pai: {nome_pai}", bg=co1, fg=co0, 
                          font=('Ivy 10'), anchor=W).grid(row=2, column=2, sticky=EW, padx=5, pady=3)
                
                if resultado:
                    vals = _safe_slice(resultado, 0, 6)
                    if len(vals) < 6:
                        vals = vals + [None] * (6 - len(vals))
                    status, data_matricula, serie_nome, turma_nome, turma_id, data_transferencia = vals
                    
                    if status == 'Ativo' and data_matricula:
                        # Formatar data de matrícula adequadamente
                        try:
                            if isinstance(data_matricula, str):
                                data_formatada = datetime.strptime(data_matricula, '%Y-%m-%d').strftime('%d/%m/%Y')
                            elif isinstance(data_matricula, (datetime, date)):
                                data_formatada = data_matricula.strftime('%d/%m/%Y')
                            else:
                                data_formatada = str(data_matricula)
                        except Exception:
                            data_formatada = str(data_matricula)
                            
                        Label(detalhes_info_frame, 
                              text=f"Data de Matrícula: {data_formatada}", 
                              bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=1, column=1, sticky=EW, padx=5, pady=3)
                        
                        # Adicionar informações de série e turma para alunos ativos
                        if serie_nome:
                            Label(detalhes_info_frame, 
                                  text=f"Série: {serie_nome}", 
                                  bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)
                        
                        if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                            Label(detalhes_info_frame, 
                                  text=f"Turma: {turma_nome}", 
                                  bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)
                        else:
                            # Se o nome da turma estiver vazio, usar o ID
                            turma_texto = f"Turma: Turma {turma_id}" if turma_id else "Turma: Não definida"
                            Label(detalhes_info_frame, 
                                  text=turma_texto, 
                                  bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)
                    
                    elif status == 'Transferido' and data_transferencia:
                        # Formatar data de transferência adequadamente
                        try:
                            if isinstance(data_transferencia, str):
                                data_transf_formatada = datetime.strptime(data_transferencia, '%Y-%m-%d').strftime('%d/%m/%Y')
                            elif isinstance(data_transferencia, (datetime, date)):
                                data_transf_formatada = data_transferencia.strftime('%d/%m/%Y')
                            else:
                                data_transf_formatada = str(data_transferencia)
                        except Exception:
                            data_transf_formatada = str(data_transferencia)
                            
                        Label(detalhes_info_frame, 
                              text=f"Data de Transferência: {data_transf_formatada}", 
                              bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=1, column=1, sticky=EW, padx=5, pady=3)
                        
                        # Para alunos transferidos, também mostrar a série/turma da última matrícula
                        if serie_nome:
                            Label(detalhes_info_frame, 
                                  text=f"Última Série: {serie_nome}", 
                                  bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)
                        
                        if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                            Label(detalhes_info_frame, 
                                  text=f"Última Turma: {turma_nome}", 
                                  bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=2, column=0, sticky=EW, padx=5, pady=3)
                        else:
                            # Se o nome da turma estiver vazio, usar o ID
                            turma_texto = f"Última Turma: Turma {turma_id}" if turma_id else "Última Turma: Não definida"
                            Label(detalhes_info_frame, 
                                  text=turma_texto, 
                                  bg=co1, fg=co0, font=('Ivy 10'), anchor=W).grid(row=2, column=0, sticky=EW, padx=5, pady=3)
            
            except Exception as e:
                logger.error(f"Erro ao verificar matrícula: {str(e)}")
            finally:
                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass
                    
        elif tipo_item == "Funcionário":
            # Linha 1: ID e Nome
            Label(detalhes_info_frame, text=f"ID: {valores[0]}", bg=co1, fg=co0, 
                  font=('Ivy 10 bold'), anchor=W).grid(row=0, column=0, sticky=EW, padx=5, pady=3)
            Label(detalhes_info_frame, text=f"Nome: {valores[1]}", bg=co1, fg=co0, 
                  font=('Ivy 10 bold'), anchor=W).grid(row=0, column=1, columnspan=2, sticky=EW, padx=5, pady=3)
            
            # Linha 2: Cargo e Data de Nascimento
            Label(detalhes_info_frame, text=f"Cargo: {valores[3]}", bg=co1, fg=co0, 
                  font=('Ivy 10'), anchor=W).grid(row=1, column=0, columnspan=2, sticky=EW, padx=5, pady=3)
            Label(detalhes_info_frame, text=f"Data de Nascimento: {valores[4]}", bg=co1, fg=co0, 
                  font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)
    
    # Agendar processamento após a seleção ser atualizada
    treeview.after(10, processar_selecao)

def criar_botoes_frame_detalhes(tipo, values):
    # Limpa quaisquer botões existentes antes de criar novos
    for widget in frame_detalhes.winfo_children():
        widget.destroy()

    # Frame para os botões
    acoes_frame = Frame(frame_detalhes, bg=co1)
    acoes_frame.pack(fill=X, padx=10, pady=10)

    # Configurar grid do frame de ações
    for i in range(6):  # Aumentado para 6 colunas para acomodar o botão de matrícula
        acoes_frame.grid_columnconfigure(i, weight=1)

    # Obter o ID do item selecionado
    id_item = values[0]

    if tipo == "Aluno":
        # Verifica se o aluno possui matrícula ativa ou transferida no ano letivo atual
        tem_matricula_ativa = verificar_matricula_ativa(id_item)
        
        # Verifica se o aluno possui histórico de matrículas em qualquer ano letivo
        tem_historico, _ = verificar_historico_matriculas(id_item)
        
        # Botões para alunos
        Button(acoes_frame, text="Editar", command=lambda: editar_aluno_e_destruir_frames(),
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co4, fg=co0).grid(row=0, column=0, padx=5, pady=5)
        
        Button(acoes_frame, text="Excluir", command=lambda: excluir_aluno_com_confirmacao(id_item),
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co8, fg=co0).grid(row=0, column=1, padx=5, pady=5)
        
        # Histórico sempre aparece
        Button(acoes_frame, text="Histórico", command=lambda: abrir_historico_aluno(id_item, janela),
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co5, fg=co0).grid(row=0, column=2, padx=5, pady=5)
        
        # Se tem matrícula ativa ou histórico, mostrar botão de Boletim
        if tem_matricula_ativa or tem_historico:
            # Substituir o botão de Boletim por um menu suspenso
            criar_menu_boletim(acoes_frame, id_item, tem_matricula_ativa)
            
            # Se tem matrícula ativa, mostrar também botão de Declaração e Editar Matrícula
            if tem_matricula_ativa:
                Button(acoes_frame, text="Declaração", command=lambda: gerar_declaracao(id_item),
                       width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co2, fg=co0).grid(row=0, column=4, padx=5, pady=5)
                       
                # Adicionar botão Editar Matrícula em vez de Matricular
                Button(acoes_frame, text="Editar Matrícula", command=lambda: editar_matricula(id_item),
                       width=12, overrelief=RIDGE, font=('Ivy 9 bold'), bg=co3, fg=co0).grid(row=0, column=5, padx=5, pady=5)
            # Se não tem matrícula ativa mas tem histórico, mostrar botão de Matricular
            else:
                Button(acoes_frame, text="Matricular", command=lambda: matricular_aluno(id_item),
                      width=10, overrelief=RIDGE, font=('Ivy 9 bold'), bg=co3, fg=co0).grid(row=0, column=4, padx=5, pady=5)
        # Se não tem nem matrícula ativa nem histórico
        else:
            # Adiciona botão de Matrícula
            Button(acoes_frame, text="Matricular", command=lambda: matricular_aluno(id_item),
                  width=10, overrelief=RIDGE, font=('Ivy 9 bold'), bg=co3, fg=co0).grid(row=0, column=3, padx=5, pady=5)
    
    elif tipo == "Funcionário":
        # Botões para funcionários
        Button(acoes_frame, text="Editar", command=lambda: editar_funcionario_e_destruir_frames(),
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co4, fg=co0).grid(row=0, column=0, padx=5, pady=5)
        
        Button(acoes_frame, text="Excluir", command=lambda: excluir_funcionario_com_confirmacao(id_item),
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co8, fg=co0).grid(row=0, column=1, padx=5, pady=5)
        
        Button(acoes_frame, text="Declaração", command=lambda: gerar_declaracao_funcionario(id_item),
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co2, fg=co0).grid(row=0, column=2, padx=5, pady=5)

def verificar_matricula_ativa(aluno_id):
    """
    Verifica se o aluno possui matrícula ativa ou transferida na escola com ID 60 no ano letivo atual.
    
    Args:
        aluno_id: ID do aluno a ser verificado
        
    Returns:
        bool: True se o aluno possui matrícula ativa ou transferida, False caso contrário
    """
    try:
        # Usar o context manager para garantir fechamento da conexão
        with get_connection() as conn:
            if conn is None:
                return False
            cursor = conn.cursor()
            try:
                # Obtém o ID do ano letivo atual
                cursor.execute("SELECT id FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
                resultado_ano = cursor.fetchone()

                if not resultado_ano:
                    # Se não encontrar o ano letivo atual, tenta obter o ano letivo mais recente
                    cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                    resultado_ano = cursor.fetchone()

                if not resultado_ano:
                    messagebox.showwarning("Aviso", "Não foi possível determinar o ano letivo atual.")
                    return False

                ano_letivo_id = resultado_ano[0]

                # Verifica se o aluno possui matrícula ativa ou transferida na escola 60 no ano letivo atual
                cursor.execute("""
                    SELECT m.id 
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    WHERE m.aluno_id = %s 
                    AND m.ano_letivo_id = %s 
                    AND t.escola_id = 60
                    AND m.status IN ('Ativo', 'Transferido')
                """, (int(str(aluno_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1))

                resultado = cursor.fetchone()

                return resultado is not None
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar matrícula: {str(e)}")
        logger.error(f"Erro ao verificar matrícula: {str(e)}")
        return False

def verificar_historico_matriculas(aluno_id):
    """
    Verifica se o aluno já teve alguma matrícula em qualquer escola e em qualquer ano letivo.
        SELECT 
        f.id AS id,
        f.nome AS nome,
        'Funcionário' AS tipo,
        f.cargo AS cargo,
        f.data_nascimento AS data_nascimento
    FROM 
        Funcionarios f
    WHERE 
        f.cargo IN ('Administrador do Sistemas','Gestor Escolar','Professor@','Auxiliar administrativo',
            'Agente de Portaria','Merendeiro','Auxiliar de serviços gerais','Técnico em Administração Escolar',
            'Especialista (Coordenadora)','Tutor/Cuidador', 'Interprete de Libras')
    UNION
    SELECT
        a.id AS id,
        a.nome AS nome,
        'Aluno' AS tipo,
        NULL AS cargo,
        a.data_nascimento AS data_nascimento
    FROM
        Alunos a
    WHERE 
        a.escola_id = 60
    ORDER BY 
        tipo, 
        nome;
    Args:
        aluno_id: ID do aluno a ser verificado
        
    Returns:
        bool: True se o aluno possui histórico de matrícula, False caso contrário
        list: Lista de tuplas (ano_letivo, ano_letivo_id) com matrícula (vazio se não houver)
    """
    try:
        with get_connection() as conn:
            if conn is None:
                return False, []
            cursor = cast(Any, conn).cursor()
            try:
                # Verifica se o aluno possui matrícula em qualquer ano letivo
                cursor.execute("""
                    SELECT DISTINCT al.ano_letivo, al.id, m.status
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN anosletivos al ON m.ano_letivo_id = al.id
                    WHERE m.aluno_id = %s 
                    AND m.status IN ('Ativo', 'Transferido')
                    ORDER BY al.ano_letivo DESC
                """, (aluno_id,))

                resultados = cursor.fetchall()

                # Se não houver resultados, verificar diretamente se há o ano letivo 2024 (ID=1)
                if not resultados:
                    cursor.execute("SELECT ano_letivo, id FROM anosletivos WHERE id = 1")
                    ano_2024 = cursor.fetchone()
                    if ano_2024:
                        # Verificar se o aluno tem qualquer matrícula para este ano
                        cursor.execute("""
                            SELECT COUNT(*) FROM matriculas 
                            WHERE aluno_id = %s AND ano_letivo_id = 1
                        """, (int(str(aluno_id)),))
                        resultado_count = cursor.fetchone()
                        tem_matricula = bool(resultado_count and resultado_count[0] and int(str(resultado_count[0])) > 0)

                        if tem_matricula:
                            resultados = [(ano_2024[0], ano_2024[1], 'Ativo')]

                # Se encontrou resultados, retorna True e a lista de anos letivos
                if resultados:
                    anos_letivos = [(ano, id_ano) for ano, id_ano, _ in resultados]
                    return True, anos_letivos
                else:
                    # Se ainda não encontrou, busca todos os anos letivos disponíveis
                    cursor.execute("SELECT ano_letivo, id FROM anosletivos ORDER BY ano_letivo DESC")
                    todos_anos = cursor.fetchall()

                    if todos_anos:
                        return True, todos_anos
                    return False, []
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar histórico de matrículas: {str(e)}")
        logger.error(f"Erro ao verificar histórico de matrículas: {str(e)}")
        return False, []

def matricular_aluno(aluno_id):
    """
    Abre uma janela para matricular o aluno na escola com ID 60.
    Args:
        aluno_id: ID do aluno a ser matriculado
    """
    try:
        # Obter informações do aluno e do ano letivo atual usando conexões curtas
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM alunos WHERE id = %s", (int(str(aluno_id)),))
            resultado_nome = cursor.fetchone()
            cursor.close()

        if resultado_nome is None:
            messagebox.showerror("Erro", "Aluno não encontrado.")
            return
        nome_aluno = resultado_nome[0]

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, ano_letivo FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
            resultado_ano = cursor.fetchone()
            if not resultado_ano:
                cursor.execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado_ano = cursor.fetchone()
            cursor.close()

        if not resultado_ano:
            messagebox.showwarning("Aviso", "Não foi possível determinar o ano letivo atual.")
            return

        ano_letivo_id, ano_letivo = resultado_ano

        # Cria a janela de matrícula
        janela_matricula = Toplevel(janela)
        janela_matricula.title(f"Matricular Aluno - {nome_aluno}")
        janela_matricula.geometry("500x450")
        janela_matricula.configure(background=co1)
        janela_matricula.transient(janela)
        janela_matricula.focus_force()
        janela_matricula.grab_set()

        # Frame principal
        frame_matricula = Frame(janela_matricula, bg=co1, padx=20, pady=20)
        frame_matricula.pack(fill=BOTH, expand=True)

        # Título
        Label(frame_matricula, text=f"Matrícula de Aluno", 
              font=("Arial", 14, "bold"), bg=co1, fg=co7).pack(pady=(0, 20))

        # Informações do aluno
        info_frame = Frame(frame_matricula, bg=co1)
        info_frame.pack(fill=X, pady=10)

        Label(info_frame, text=f"Aluno: {nome_aluno}", 
              font=("Arial", 12), bg=co1, fg=co4).pack(anchor=W)

        Label(info_frame, text=f"Ano Letivo: {ano_letivo}", 
              font=("Arial", 12), bg=co1, fg=co4).pack(anchor=W)

        # Selecionar Série
        serie_frame = Frame(frame_matricula, bg=co1)
        serie_frame.pack(fill=X, pady=10)

        Label(serie_frame, text="Série:", bg=co1, fg=co4).pack(anchor=W, pady=(5, 0))
        serie_var = StringVar()
        cb_serie = ttk.Combobox(serie_frame, textvariable=serie_var, width=40)
        cb_serie.pack(fill=X, pady=(0, 5))

        # Selecionar Turma
        turma_frame = Frame(frame_matricula, bg=co1)
        turma_frame.pack(fill=X, pady=10)

        Label(turma_frame, text="Turma:", bg=co1, fg=co4).pack(anchor=W, pady=(5, 0))
        turma_var = StringVar()
        cb_turma = ttk.Combobox(turma_frame, textvariable=turma_var, width=40)
        cb_turma.pack(fill=X, pady=(0, 5))

        # Data da matrícula
        data_frame = Frame(frame_matricula, bg=co1)
        data_frame.pack(fill=X, pady=10)

        Label(data_frame, text="Data da Matrícula (dd/mm/aaaa):", bg=co1, fg=co4).pack(anchor=W, pady=(5, 0))
        data_matricula_var = StringVar()
        # Definir data atual como padrão
        from datetime import datetime
        data_matricula_var.set(datetime.now().strftime('%d/%m/%Y'))
        entry_data_matricula = Entry(data_frame, textvariable=data_matricula_var, width=42, font=("Arial", 10))
        entry_data_matricula.pack(fill=X, pady=(0, 5))

        # Dicionários para mapear nomes para IDs
        series_map = {}
        turmas_map = {}

        # Função para carregar séries
        def carregar_series():
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DISTINCT s.id, s.nome 
                        FROM serie s
                        JOIN turmas t ON s.id = t.serie_id
                        WHERE t.escola_id = 60
                        AND t.ano_letivo_id = %s
                        ORDER BY s.nome
                    """, (int(str(ano_letivo_id)) if ano_letivo_id is not None else 1,))
                    series = cursor.fetchall()
                    cursor.close()

                if not series:
                    messagebox.showwarning("Aviso", "Não foram encontradas séries para a escola selecionada no ano letivo atual.")
                    return

                series_map.clear()
                for serie in series:
                    series_map[serie[1]] = serie[0]

                cb_serie['values'] = list(series_map.keys())

                # Limpar seleção de turma
                cb_turma.set("")
                cb_turma['values'] = []

                # Selecionar automaticamente se houver apenas uma série
                if len(series_map) == 1:
                    serie_nome = list(series_map.keys())[0]
                    cb_serie.set(serie_nome)
                    # Carregar turmas automaticamente para a única série
                    carregar_turmas()

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar séries: {str(e)}")

        # Função para carregar turmas com base na série selecionada
        def carregar_turmas(event=None):
            serie_nome = serie_var.get()
            if not serie_nome:
                logger.warning("Série não selecionada")
                return

            if serie_nome not in series_map:
                logger.warning(f"Série '{serie_nome}' não encontrada no mapeamento: {series_map}")
                return

            serie_id = series_map[serie_nome]

            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, nome, serie_id
                        FROM turmas 
                        WHERE serie_id = %s AND escola_id = 60 AND ano_letivo_id = %s
                        ORDER BY nome
                    """, (int(str(serie_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1))

                    turmas = cursor.fetchall()
                    cursor.close()

                if not turmas:
                    messagebox.showwarning("Aviso", f"Não foram encontradas turmas para a série {serie_nome}.")
                    return

                turmas_map.clear()
                for turma in turmas:
                    turma_id, turma_nome, turma_serie_id = turma
                    if not turma_nome or str(turma_nome).strip() == "":
                        if len(turmas) == 1:
                            turma_nome = f"Turma Única"
                        else:
                            turma_nome = f"Turma {turma_id}"
                    turmas_map[turma_nome] = turma_id

                turmas_nomes = list(turmas_map.keys())
                cb_turma['values'] = turmas_nomes

                if len(turmas_map) == 1:
                    turma_nome = turmas_nomes[0]
                    cb_turma.set(turma_nome)
                    turma_var.set(turma_nome)
                    logger.info(f"Turma selecionada automaticamente: '{turma_nome}'")
                else:
                    cb_turma.set("")
                    turma_var.set("")

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar turmas: {str(e)}")
                logger.error(f"Erro detalhado: {str(e)}")

        # Vincular evento ao combobox de série
        cb_serie.bind("<<ComboboxSelected>>", carregar_turmas)

        # Função para salvar a matrícula
        def salvar_matricula():
            serie_nome = serie_var.get()
            turma_nome = turma_var.get()
            data_str = data_matricula_var.get()

            logger.debug(f"Série selecionada: '{serie_nome}', Turma selecionada: '{turma_nome}'")
            logger.debug(f"Séries disponíveis: {list(series_map.keys())}")
            logger.debug(f"Turmas disponíveis: {list(turmas_map.keys())}")

            if len(turmas_map) == 1 and (not turma_nome or turma_nome not in turmas_map):
                turma_nome = list(turmas_map.keys())[0]
                turma_var.set(turma_nome)
                logger.info(f"Turma ajustada automaticamente para: '{turma_nome}'")

            if not serie_nome or serie_nome not in series_map:
                messagebox.showwarning("Aviso", "Por favor, selecione uma série válida.")
                return

            if not turma_nome or turma_nome not in turmas_map:
                messagebox.showwarning("Aviso", f"Por favor, selecione uma turma válida. Valor atual: '{turma_nome}'")
                return

            # Validar data
            try:
                from datetime import datetime
                data_obj = datetime.strptime(data_str, '%d/%m/%Y')
                data_formatada = data_obj.strftime('%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Erro", "Data inválida! Use o formato dd/mm/aaaa (exemplo: 28/10/2025)")
                return

            turma_id = turmas_map[turma_nome]

            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT id, status 
                        FROM matriculas 
                        WHERE aluno_id = %s AND ano_letivo_id = %s
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (int(str(aluno_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1)
                    )
                    registro_existente = cursor.fetchone()

                    if registro_existente:
                        matricula_id, status_atual = registro_existente
                        cursor.execute(
                            """
                            UPDATE matriculas 
                            SET turma_id = %s, status = 'Ativo', data_matricula = CURDATE()
                            WHERE id = %s
                            """,
                            (int(str(turma_id)), int(str(matricula_id)) if matricula_id is not None else 0)
                        )
                        try:
                            cursor.execute(
                                """
                                INSERT INTO historico_matricula (matricula_id, status_anterior, status_novo, data_mudanca)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (int(str(matricula_id)) if matricula_id is not None else 0, str(status_atual) if status_atual is not None else '', 'Ativo', data_formatada)
                            )
                        except Exception as hist_err:
                            logger.error(f"Falha ao registrar histórico da matrícula (update): {hist_err}")
                    else:
                        cursor.execute(
                            """
                            INSERT INTO matriculas (aluno_id, turma_id, data_matricula, ano_letivo_id, status)
                            VALUES (%s, %s, CURDATE(), %s, 'Ativo')
                            """,
                            (int(str(aluno_id)), int(str(turma_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1)
                        )

                        novo_matricula_id = cursor.lastrowid
                        try:
                            cursor.execute(
                                """
                                INSERT INTO historico_matricula (matricula_id, status_anterior, status_novo, data_mudanca)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (novo_matricula_id, None, 'Ativo', data_formatada)
                            )
                        except Exception as hist_err:
                            logger.error(f"Falha ao registrar histórico da matrícula (insert): {hist_err}")

                    conn.commit()
                    cursor.close()

                messagebox.showinfo("Sucesso", f"Aluno {nome_aluno} matriculado/atualizado com sucesso na turma {turma_nome}!")
                janela_matricula.destroy()
                criar_botoes_frame_detalhes("Aluno", [aluno_id, nome_aluno, "Aluno", None, None])

            except Exception as e:
                try:
                    conn.rollback()
                except Exception:
                    pass
                messagebox.showerror("Erro", f"Erro ao realizar matrícula: {str(e)}")

        # Função ao fechar a janela de matrícula
        def ao_fechar_janela():
            janela_matricula.destroy()

        # Configurar ação de fechamento da janela
        janela_matricula.protocol("WM_DELETE_WINDOW", ao_fechar_janela)

        # Botões
        botoes_frame = Frame(frame_matricula, bg=co1)
        botoes_frame.pack(fill=X, pady=20)

        Button(botoes_frame, text="Salvar", command=salvar_matricula,
              font=('Ivy 10 bold'), bg=co3, fg=co1, width=15).pack(side=LEFT, padx=5)

        Button(botoes_frame, text="Cancelar", command=ao_fechar_janela,
              font=('Ivy 10'), bg=co6, fg=co1, width=15).pack(side=RIGHT, padx=5)

        # Carregar séries ao abrir a janela
        carregar_series()

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao preparar matrícula: {str(e)}")

def excluir_aluno_com_confirmacao(aluno_id):
    # Pergunta ao usuário para confirmar a exclusão
    resposta = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este aluno?")
    
    if resposta:
        try:
            # Executa a exclusão
            # `aluno.excluir_aluno` aceita `query` por compatibilidade, mas
            # não usa o parâmetro internamente. Passar `None` evita
            # referência a variável indefinida aqui e mantém a chamada válida.
            resultado = aluno.excluir_aluno(aluno_id, treeview, None)
            
            if resultado:
                messagebox.showinfo("Sucesso", "Aluno excluído com sucesso.")
                # Atualizar a tabela principal
                atualizar_tabela_principal()
                # Volta para a tela principal
                voltar()
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o aluno.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir aluno: {str(e)}")
            logger.error(f"Erro ao excluir aluno: {str(e)}")

def excluir_funcionario_com_confirmacao(funcionario_id):
    # Pergunta ao usuário para confirmar a exclusão
    resposta = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este funcionário?")
    
    if resposta:
        try:
            with get_connection() as conexao:
                if conexao is None:
                    messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                    return False
                cursor = conexao.cursor()
                try:
                    # Verifica se o funcionário existe
                    cursor.execute("SELECT nome FROM funcionarios WHERE id = %s", (funcionario_id,))
                    funcionario = cursor.fetchone()

                    if not funcionario:
                        messagebox.showerror("Erro", "Funcionário não encontrado.")
                        return False

                    # Exclui associações com funcionario_disciplinas
                    cursor.execute("DELETE FROM funcionario_disciplinas WHERE funcionario_id = %s", (funcionario_id,))

                    # Exclui o funcionário
                    cursor.execute("DELETE FROM funcionarios WHERE id = %s", (funcionario_id,))
                    conexao.commit()

                    messagebox.showinfo("Sucesso", "Funcionário excluído com sucesso.")

                    # Atualizar a tabela principal
                    atualizar_tabela_principal()

                    # Volta para a tela principal
                    voltar()

                    return True
                except Exception as e:
                    # Tenta rollback se suportado
                    try:
                        conexao.rollback()
                    except Exception:
                        pass
                    messagebox.showerror("Erro", f"Erro ao excluir funcionário: {str(e)}")
                    logger.error(f"Erro ao excluir funcionário: {str(e)}")
                    return False
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir funcionário: {str(e)}")
            logger.error(f"Erro ao excluir funcionário: {str(e)}")
            return False

def editar_aluno_e_destruir_frames():
    # Obter o ID do aluno selecionado na tabela
    try:
        item_selecionado = treeview.focus()
        valores = treeview.item(item_selecionado, "values")
        
        if not valores:
            messagebox.showwarning("Aviso", "Selecione um aluno para editar")
            return
        
        aluno_id = valores[0]  # Assumindo que o ID é o primeiro valor
        
        # Abrir a interface de edição em uma nova janela
        janela_edicao = Toplevel(janela)
        from InterfaceEdicaoAluno import InterfaceEdicaoAluno
        
        # Configurar a janela de edição antes de criar a interface
        janela_edicao.title(f"Editar Aluno - ID: {aluno_id}")
        janela_edicao.geometry('950x670')
        janela_edicao.configure(background=co1)
        janela_edicao.focus_set()  # Dar foco à nova janela
        janela_edicao.grab_set()   # Torna a janela modal
        
        # Esconder a janela principal
        janela.withdraw()
        
        # Criar a interface de edição após configurar a janela
        app_edicao = InterfaceEdicaoAluno(janela_edicao, aluno_id, janela_principal=janela)
        
        # Atualizar a tabela quando a janela de edição for fechada
        def ao_fechar_edicao():
            # Restaurar a janela principal
            janela.deiconify()
            # Atualizar a tabela para refletir as alterações
            atualizar_tabela_principal()
            # Destruir a janela de edição
            janela_edicao.destroy()
        
        # Configurar evento para quando a janela for fechada
        janela_edicao.protocol("WM_DELETE_WINDOW", ao_fechar_edicao)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir interface de edição: {str(e)}")
        logger.error(f"Erro ao abrir interface de edição: {str(e)}")
        # Se ocorrer erro, garantir que a janela principal esteja visível
        janela.deiconify()

def gerar_declaracao(id_pessoa=None):
    global selected_item
    
    # Declarar tipo_pessoa no escopo externo
    tipo_pessoa = None
    
    # Se o ID não foi fornecido, tenta obter do item selecionado
    if id_pessoa is None:
        selected_item = treeview.focus()
        if not selected_item:
            messagebox.showerror("Erro", "Nenhum usuário selecionado.")
            return
            
        item = treeview.item(selected_item)
        values = item['values']
        
        if len(values) < 3:
            messagebox.showerror("Erro", "Não foi possível obter os dados do usuário selecionado.")
            return
            
        id_pessoa, tipo_pessoa = values[0], values[2]
    else:
        # Se o ID foi fornecido diretamente, precisamos determinar o tipo da pessoa
        try:
            with get_connection() as conn:
                if conn is None:
                    messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                    return
                cursor = conn.cursor()
                try:
                    # Verificar se é um aluno
                    cursor.execute("SELECT id FROM alunos WHERE id = %s", (id_pessoa,))
                    if cursor.fetchone():
                        tipo_pessoa = 'Aluno'
                    else:
                        # Verificar se é um funcionário
                        cursor.execute("SELECT id FROM funcionarios WHERE id = %s", (id_pessoa,))
                        if cursor.fetchone():
                            tipo_pessoa = 'Funcionário'
                        else:
                            messagebox.showerror("Erro", "ID não corresponde a nenhum usuário cadastrado.")
                            return
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao verificar o tipo de usuário: {str(e)}")
            return

    marcacoes = [[False] * 4 for _ in range(1)]
    motivo_outros = ""

    # Criar uma janela de diálogo para selecionar o tipo de declaração
    dialog = Toplevel(janela)
    dialog.title("Tipo de Declaração")
    dialog.geometry("380x220")
    dialog.transient(janela)
    dialog.focus_force()
    dialog.grab_set()
    dialog.configure(bg=co0)
    
    # Variável para armazenar a opção selecionada
    opcao = StringVar(dialog)
    opcao.set("Transferência")  # Valor padrão
    
    opcoes = [
        "Transferência", "Bolsa Família", "Trabalho", "Outros"
    ]
    
    Label(dialog, text="Selecione o tipo de declaração:", font=("Ivy", 12), bg=co0, fg=co7).pack(pady=10)
    
    option_menu = OptionMenu(dialog, opcao, *opcoes)
    option_menu.config(bg=co0, fg=co7)
    option_menu.pack(pady=5)
    
    # Frame para o campo de motivo (inicialmente oculto)
    motivo_frame = Frame(dialog, bg=co0)
    motivo_frame.pack(pady=5, fill='x', padx=20)
    
    Label(motivo_frame, text="Especifique o motivo:", font=("Ivy", 11), bg=co0, fg=co7).pack(anchor='w')
    motivo_entry = Entry(motivo_frame, width=40, font=("Ivy", 11))
    motivo_entry.pack(fill='x', pady=5)
    
    # Inicialmente oculta o frame de motivo
    motivo_frame.pack_forget()
    
    # Função para atualizar a visibilidade do campo de motivo
    def atualizar_interface(*args):
        if opcao.get() == "Outros":
            motivo_frame.pack(pady=5, fill='x', padx=20)
            dialog.geometry("380x220")
            motivo_entry.focus_set()
        else:
            motivo_frame.pack_forget()
            dialog.geometry("380x170")
    
    # Associar a função ao evento de mudança da opção
    opcao.trace_add("write", atualizar_interface)
    
    def confirmar():
        # Declarar acesso à variável do escopo externo
        nonlocal tipo_pessoa
        
        opcao_selecionada = opcao.get()
        
        if opcao_selecionada in opcoes:
            index = opcoes.index(opcao_selecionada)
            linha = 0
            coluna = index
            marcacoes[linha][coluna] = True
        
        # Capturar o motivo se for a opção "Outros"
        motivo_outros = ""
        if opcao_selecionada == "Outros":
            motivo_outros = motivo_entry.get().strip()
            if not motivo_outros:
                messagebox.showwarning("Aviso", "Por favor, especifique o motivo.")
                return
        
        # Executar geração da declaração em background para não bloquear a UI
        def _worker():
            if tipo_pessoa == 'Aluno':
                return gerar_declaracao_aluno(id_pessoa, marcacoes, motivo_outros)
            elif tipo_pessoa == 'Funcionário':
                return gerar_declaracao_funcionario(id_pessoa)
            else:
                raise RuntimeError('Tipo de usuário desconhecido')

        def _on_done(resultado):
            try:
                if resultado is True or resultado is None:
                    # Alguns geradores retornam None; considerar sucesso se não houve exceção
                    if status_label is not None:
                        status_label.config(text="Declaração gerada com sucesso.")
                    messagebox.showinfo("Concluído", "Declaração gerada com sucesso.")
                else:
                    # Se o worker retornou caminho ou objeto, mostrar informação genérica
                    if status_label is not None:
                        status_label.config(text="Declaração gerada com sucesso.")
                    messagebox.showinfo("Concluído", f"Declaração gerada: {resultado}")
            except Exception:
                # Evitar que exceções aqui quebrem a UI
                pass

        def _on_error(exc):
            messagebox.showerror("Erro", f"Falha ao gerar declaração: {exc}")
            if status_label is not None:
                status_label.config(text="")

        # Fechar diálogo antes de submeter a tarefa de background
        dialog.destroy()

        try:
            from utils.executor import submit_background
            submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=janela)
        except Exception:
            # Fallback seguro: executar em Thread e agendar callbacks via janela.after
            def _thread_worker():
                try:
                    res = _worker()
                    try:
                        janela.after(0, lambda: _on_done(res))
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        janela.after(0, lambda: _on_error(e))
                    except Exception:
                        pass

            from threading import Thread
            Thread(target=_thread_worker, daemon=True).start()
    
    Button(dialog, text="Confirmar", command=confirmar, bg=co2, fg=co0).pack(pady=10)

def criar_logo():
    # Limpa o frame do logo antes de adicionar novos widgets
    for widget in frame_logo.winfo_children():
        widget.destroy()
        
    # Frame para o cabeçalho/logo
    logo_frame = Frame(frame_logo, bg=co0)  # Alterado para fundo branco (co0)
    logo_frame.pack(fill=BOTH, expand=True, padx=0, pady=0)
    
    # Configura para expandir
    logo_frame.grid_columnconfigure(0, weight=1)  # Logo (menor peso)
    logo_frame.grid_columnconfigure(1, weight=5)  # Título (maior peso)
    
    # Logo
    global app_logo
    try:
        # Tenta carregar a imagem do logo
        app_img = Image.open('logopaco.png')  # Tenta usar um logo existente
        app_img = app_img.resize((200, 50))  # Aumentado o tamanho para melhor visualização
        app_logo = ImageTk.PhotoImage(app_img)
        
        # Ícone da escola
        app_logo_label = Label(logo_frame, image=app_logo, text=" ", bg=co0, fg=co7)  # Alterado o fundo para branco
        app_logo_label.grid(row=0, column=0, sticky=W, padx=10)
    except FileNotFoundError:
        try:
            # Tenta carregar outro logo
            app_img = Image.open('icon/book.png')
            app_img = app_img.resize((45, 45))
            app_logo = ImageTk.PhotoImage(app_img)
            
            # Ícone da escola
            app_logo_label = Label(logo_frame, image=app_logo, text=" ", bg=co0, fg=co7)  # Alterado o fundo para branco
            app_logo_label.grid(row=0, column=0, sticky=W, padx=10)
        except:
            # Fallback quando a imagem não é encontrada
            app_logo_label = Label(logo_frame, text="LOGO", font=("Ivy 15 bold"), bg=co0, fg=co7)  # Alterado o fundo para branco
            app_logo_label.grid(row=0, column=0, sticky=W, padx=10)

    # Título da escola
    escola_label = Label(logo_frame, text=str(nome_escola).upper(), font=("Ivy 15 bold"), bg=co0, fg=co1)  # Alterado o fundo para branco e texto para azul
    escola_label.grid(row=0, column=1, sticky=W, padx=10)

def criar_pesquisa():
    # Frame para a barra de pesquisa
    pesquisa_frame = Frame(frame_dados, bg=co1)
    pesquisa_frame.pack(fill=X, expand=True, padx=10, pady=5)
    
    # Configura pesquisa_frame para expandir horizontalmente
    pesquisa_frame.grid_columnconfigure(0, weight=3)  # Entrada de pesquisa
    pesquisa_frame.grid_columnconfigure(1, weight=1)  # Botão de pesquisa
    
    # Entrada para pesquisa
    global e_nome_pesquisa
    e_nome_pesquisa = Entry(pesquisa_frame, width=45, justify='left', relief=SOLID, bg=co0)
    e_nome_pesquisa.grid(row=0, column=0, padx=5, pady=5, sticky=EW)
    
    # Vincula o evento de pressionar Enter à função de pesquisa
    e_nome_pesquisa.bind("<Return>", pesquisar)

    # Botão para pesquisar
    botao_pesquisar = Button(pesquisa_frame, command=lambda:pesquisar(), text="Pesquisar", 
                            font=('Ivy 10 bold'), relief=RAISED, overrelief=RIDGE, bg=co4, fg=co0)
    botao_pesquisar.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

def pesquisar(event=None):
    texto_pesquisa = e_nome_pesquisa.get().strip()  # Obtém o texto da pesquisa (sem lower() para FULLTEXT)

    # Garantir que vamos manipular as variáveis globais corretamente
    global tabela_frame, treeview, dashboard_canvas

    # Garantir que os componentes da tabela existam (cria se necessário)
    try:
        if 'tabela_frame' not in globals() or tabela_frame is None:
            criar_tabela()
        if 'treeview' not in globals() or not getattr(treeview, 'winfo_exists', lambda: False)():
            criar_tabela()
    except Exception as e:
        logger.exception("Erro ao inicializar componentes da tabela: %s", e)
        messagebox.showerror("Erro", f"Erro ao preparar a interface de pesquisa: {e}")
        return

    if not texto_pesquisa:  # Se a busca estiver vazia, mostrar dashboard
        # Ocultar tabela se estiver visível
        try:
            if tabela_frame.winfo_ismapped():
                tabela_frame.pack_forget()
        except Exception:
            pass

        # Limpar frame_tabela e mostrar dashboard
        try:
            for widget in list(frame_tabela.winfo_children()):
                if widget != tabela_frame:
                    try:
                        widget.destroy()
                    except Exception:
                        pass
        except Exception:
            pass

        criar_dashboard()
        return


    # Há texto de pesquisa: garantir que dashboard ou outros widgets não cubram a tabela
    try:
        # Remover tudo em frame_tabela e recriar a tabela limpa para evitar sobreposição
        for widget in list(frame_tabela.winfo_children()):
            try:
                widget.destroy()
            except Exception:
                pass

        # Recriar a tabela (garante que tabela_frame e treeview existam)
        criar_tabela()

        # Se o criar_tabela adicionou o dashboard, removemos novamente deixando apenas `tabela_frame`
        for widget in list(frame_tabela.winfo_children()):
            if widget is not tabela_frame:
                try:
                    widget.destroy()
                except Exception:
                    pass

        # resetar referência global ao canvas do dashboard
        try:
            dashboard_canvas = None
        except Exception:
            pass

        # Mostrar tabela_frame
        try:
            if not tabela_frame.winfo_ismapped():
                tabela_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        except Exception:
            pass
    except Exception as e:
        logger.exception("Falha ao preparar área da tabela: %s", e)
        messagebox.showerror("Erro", f"Falha ao preparar área da tabela: {e}")
        return

    # Limpa o Treeview primeiro
    try:
        for item in treeview.get_children():
            treeview.delete(item)
    except Exception:
        # Se não existir itens ou treeview, continuar
        pass
    
    # ============================================================================
    # OTIMIZAÇÃO 5: Pesquisa com FULLTEXT (mais rápida que LIKE)
    # Busca diretamente no banco com índice FULLTEXT para melhor performance
    # ============================================================================
    resultados_filtrados = []
    try:
        with get_connection() as conn:
            if conn is None:
                raise Exception("Falha ao conectar ao banco de dados")
            cursor = conn.cursor()
            try:
                # Tentar usar FULLTEXT primeiro (mais rápido)
                # Se falhar (índice não existe), usar LIKE tradicional
                try:
                    # Query otimizada com FULLTEXT
                    query_fulltext = """
                    SELECT 
                        f.id AS id,
                        f.nome AS nome,
                        'Funcionário' AS tipo,
                        f.cargo AS cargo,
                        f.data_nascimento AS data_nascimento,
                        MATCH(f.nome) AGAINST(%s IN NATURAL LANGUAGE MODE) AS relevancia
                    FROM 
                        Funcionarios f
                    WHERE 
                        MATCH(f.nome) AGAINST(%s IN NATURAL LANGUAGE MODE)
                        AND f.cargo IN ('Administrador do Sistemas','Gestor Escolar','Professor@','Auxiliar administrativo',
                            'Agente de Portaria','Merendeiro','Auxiliar de serviços gerais','Técnico em Administração Escolar',
                            'Especialista (Coordenadora)','Tutor/Cuidador', 'Interprete de Libras')
                    UNION ALL
                    SELECT
                        a.id AS id,
                        a.nome AS nome,
                        'Aluno' AS tipo,
                        NULL AS cargo,
                        a.data_nascimento AS data_nascimento,
                        MATCH(a.nome) AGAINST(%s IN NATURAL LANGUAGE MODE) AS relevancia
                    FROM
                        Alunos a
                    WHERE 
                        MATCH(a.nome) AGAINST(%s IN NATURAL LANGUAGE MODE)
                        AND a.escola_id = 60
                    ORDER BY 
                        relevancia DESC, tipo, nome;
                    """

                    cursor.execute(query_fulltext, (texto_pesquisa, texto_pesquisa, texto_pesquisa, texto_pesquisa))
                    resultados_filtrados = cursor.fetchall()

                    # Remover coluna de relevância antes de exibir
                    resultados_filtrados = [row[:-1] for row in resultados_filtrados]

                # `Error` não estava importado aqui; capturamos qualquer exceção
                # e tratamos o caso de FULLTEXT como fallback para LIKE.
                except Exception as e:
                    # Se FULLTEXT falhar, usar LIKE tradicional (fallback)
                    if "Can't find FULLTEXT index" in str(e) or "function" in str(e).lower():
                        query_like = """
                        SELECT 
                            f.id AS id,
                            f.nome AS nome,
                            'Funcionário' AS tipo,
                            f.cargo AS cargo,
                            f.data_nascimento AS data_nascimento
                        FROM 
                            Funcionarios f
                        WHERE 
                            f.nome LIKE %s
                            AND f.cargo IN ('Administrador do Sistemas','Gestor Escolar','Professor@','Auxiliar administrativo',
                                'Agente de Portaria','Merendeiro','Auxiliar de serviços gerais','Técnico em Administração Escolar',
                                'Especialista (Coordenadora)','Tutor/Cuidador', 'Interprete de Libras')
                        UNION ALL
                        SELECT
                            a.id AS id,
                            a.nome AS nome,
                            'Aluno' AS tipo,
                            NULL AS cargo,
                            a.data_nascimento AS data_nascimento
                        FROM
                            Alunos a
                        WHERE 
                            a.nome LIKE %s
                            AND a.escola_id = 60
                        ORDER BY 
                            tipo, nome;
                        """

                        termo_like = f'%{texto_pesquisa}%'
                        cursor.execute(query_like, (termo_like, termo_like))
                        resultados_filtrados = cursor.fetchall()
                    else:
                        raise  # Re-lançar outros erros
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao realizar pesquisa no banco: {str(e)}")
        return
    
    # Adiciona os resultados filtrados ao Treeview
    if resultados_filtrados:
        primeira_chave = None
        for resultado in resultados_filtrados:
            # Normalizar o resultado para uma lista de valores (suporta tuple/list/dict/valor)
            if isinstance(resultado, dict):
                resultado = list(resultado.values())
            elif isinstance(resultado, (list, tuple)):
                resultado = list(resultado)
            else:
                resultado = [resultado]

            # Verifica se há campo de data na posição 4 e formata
            if len(resultado) > 4 and resultado[4]:
                try:
                    if isinstance(resultado[4], str):
                        data = datetime.strptime(resultado[4], '%Y-%m-%d')
                    elif isinstance(resultado[4], (datetime, date)):
                        data = resultado[4]
                    else:
                        data = None

                    if data:
                        resultado[4] = data.strftime('%d/%m/%Y')
                except Exception:
                    pass

            try:
                item_id = treeview.insert("", "end", values=resultado)
                if primeira_chave is None:
                    primeira_chave = item_id
            except Exception as e:
                logger.exception("Erro ao inserir resultado na treeview: %s - Resultado: %s", e, resultado)

        # Forçar atualização visual e foco no primeiro item
        try:
            treeview.update_idletasks()
            if primeira_chave:
                treeview.selection_set(primeira_chave)
                treeview.focus(primeira_chave)
                treeview.see(primeira_chave)
        except Exception:
            pass
    else:
        # Exibe mensagem quando não há resultados
        messagebox.showinfo("Pesquisa", "Nenhum resultado encontrado para a pesquisa.")

# Função para redefinir os frames
def redefinir_frames(titulo):
    # Destruir widgets específicos nos frames, preservando os botões no frame_dados
    for widget in frame_logo.winfo_children():
        widget.destroy()
    
    for widget in frame_detalhes.winfo_children():
        widget.destroy()
        
    for widget in frame_tabela.winfo_children():
        widget.destroy()
        
    # No frame_dados, preservamos a barra de pesquisa
    # Vamos identificar e guardar o frame de pesquisa para não destruí-lo
    search_frame_to_preserve = None
    for widget in frame_dados.winfo_children():
        if isinstance(widget, Frame) and widget.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, Entry):
                    # Este é provavelmente o frame de pesquisa
                    search_frame_to_preserve = widget
                    break
    
    # Agora removemos todos os widgets exceto o frame de pesquisa
    for widget in frame_dados.winfo_children():
        if widget != search_frame_to_preserve:
            widget.destroy()
    
    # Carregar a nova imagem e definir o título apropriado
    global app_lp, app_img_voltar
    
    # Criar um frame dentro do frame_logo para o título
    titulo_frame = Frame(frame_logo, bg=co0)  # Alterado para fundo branco
    titulo_frame.pack(fill=BOTH, expand=True)
    
    try:
        app_lp = Image.open('icon/learning.png')
        app_lp = app_lp.resize((30, 30))
        app_lp = ImageTk.PhotoImage(app_lp)
        app_logo = Label(titulo_frame, image=app_lp, text=titulo, compound=LEFT,
                        anchor=W, font=('Ivy 15 bold'), bg=co0, fg=co1, padx=10, pady=5)  # Alterado para fundo branco e texto azul
        app_logo.pack(fill=X, expand=True)
    except:
        # Fallback sem ícone
        app_logo = Label(titulo_frame, text=titulo, 
                        anchor=W, font=('Ivy 15 bold'), bg=co0, fg=co1, padx=10, pady=5)  # Alterado para fundo branco e texto azul
        app_logo.pack(fill=X, expand=True)
    
    # Criar um frame separado para o botão de voltar
    voltar_frame = Frame(frame_dados, bg=co1)
    voltar_frame.pack(side=LEFT, padx=10, pady=5)
    
    try:
        app_img_voltar = Image.open('icon/left.png')
        app_img_voltar = app_img_voltar.resize((25, 25))
        app_img_voltar = ImageTk.PhotoImage(app_img_voltar)
        app_voltar = Button(voltar_frame, command=voltar, image=app_img_voltar,
                        compound=LEFT, overrelief=RIDGE, bg=co1, fg=co0)
    except FileNotFoundError:
        app_voltar = Button(voltar_frame, command=voltar, text="←",
                        overrelief=RIDGE, bg=co1, fg=co0, font=('Ivy 12 bold'))
    app_voltar.pack(side=LEFT)
    
    # Garantir que o frame_detalhes esteja visível
    frame_detalhes.pack_propagate(False)
    frame_detalhes.config(width=850, height=200)  # Definir altura mínima para o frame de detalhes

def criar_acoes():
    # Frame para os botões de ação
    botoes_frame = Frame(frame_dados, bg=co1)
    botoes_frame.pack(fill=X, expand=True, padx=10, pady=5)
    
    # Configurar grid do frame de botões
    for i in range(7):  # 7 colunas para acomodar todos os botões
        botoes_frame.grid_columnconfigure(i, weight=1)

    # Função para cadastrar novo aluno
    def cadastrar_novo_aluno():
        # Abrir a interface de cadastro em uma nova janela
        from InterfaceCadastroAluno import InterfaceCadastroAluno
        cadastro_window = Toplevel(janela)
        cadastro_window.title("Cadastro de Aluno")
        cadastro_window.geometry('950x670')
        cadastro_window.focus_set()  # Dar foco à nova janela
        cadastro_window.grab_set()   # Torna a janela modal
        
        # Criar instância da interface de cadastro passando a janela principal
        app_cadastro = InterfaceCadastroAluno(cadastro_window, janela)
        
        # Definir função para atualizar os dados quando a janela de cadastro for fechada
        def ao_fechar_cadastro():
            # Verificar se um aluno foi cadastrado
            if hasattr(app_cadastro, 'aluno_cadastrado') and app_cadastro.aluno_cadastrado:
                # Atualizar a tabela principal com os dados mais recentes
                atualizar_tabela_principal()
            
            # Mostrar a janela principal novamente
            janela.deiconify()
            
            # Destruir a janela de cadastro
            cadastro_window.destroy()
        
        # Configurar evento para quando a janela for fechada
        # Obs: Este evento só será executado se o usuário fechar a janela pelo X, 
        # e não através do botão de salvar ou voltar
        cadastro_window.protocol("WM_DELETE_WINDOW", ao_fechar_cadastro)

    # Função para cadastrar novo funcionário
    def cadastrar_novo_funcionario():
        # Abrir a interface de cadastro em uma nova janela
        from InterfaceCadastroFuncionario import InterfaceCadastroFuncionario
        cadastro_window = Toplevel(janela)
        cadastro_window.title("Cadastro de Funcionário")
        cadastro_window.geometry('950x670')
        cadastro_window.focus_set()  # Dar foco à nova janela
        
        # Criar instância da interface de cadastro passando a janela principal
        app_cadastro = InterfaceCadastroFuncionario(cadastro_window, janela)

    # Função para abrir a interface de histórico escolar
    def abrir_historico():
        abrir_interface_historico(janela)

    # Botões de ação
    global app_img_cadastro
    try:
        app_img_cadastro = Image.open('icon/plus.png')
        app_img_cadastro = app_img_cadastro.resize((18, 18))
        app_img_cadastro = ImageTk.PhotoImage(app_img_cadastro)
        app_cadastro = Button(botoes_frame, command=cadastrar_novo_aluno, image=app_img_cadastro, text="Novo Aluno",
                            compound=LEFT, overrelief=RIDGE, font=('Ivy 11'), bg=co2, fg=co0)
    except FileNotFoundError:
        app_cadastro = Button(botoes_frame, command=cadastrar_novo_aluno, text="+ Novo Aluno",
                            compound=LEFT, overrelief=RIDGE, font=('Ivy 11'), bg=co2, fg=co0)
    app_cadastro.grid(row=0, column=0, padx=5, pady=5, sticky=EW)
    if 'app_img_cadastro' in locals():
        setattr(app_cadastro, '_image_ref', app_img_cadastro)
    
    global app_img_funcionario
    try:
        app_img_funcionario = Image.open('icon/video-conference.png')
        app_img_funcionario = app_img_funcionario.resize((18, 18))
        app_img_funcionario = ImageTk.PhotoImage(app_img_funcionario)
        app_funcionario = Button(botoes_frame, command=cadastrar_novo_funcionario, image=app_img_funcionario,
                                text="Novo Funcionário", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                                bg=co3, fg=co0)
    except FileNotFoundError:
        app_funcionario = Button(botoes_frame, command=cadastrar_novo_funcionario, text="+ Novo Funcionário", 
                                compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                                bg=co3, fg=co0)
    app_funcionario.grid(row=0, column=1, padx=5, pady=5, sticky=EW)
    if 'app_img_funcionario' in locals():
        setattr(app_funcionario, '_image_ref', app_img_funcionario)
    
    global app_img_matricula
    try:
        app_img_matricula = Image.open('icon/book.png')
        app_img_matricula = app_img_matricula.resize((18, 18))
        app_img_matricula = ImageTk.PhotoImage(app_img_matricula)
    except FileNotFoundError:
        # Cria uma imagem vazia para evitar erros em botões que usam app_img_matricula
        app_img_matricula = None
        
    # Botão para acessar a interface de histórico escolar
    global app_img_historico
    try:
        app_img_historico = Image.open('icon/history.png')
        app_img_historico = app_img_historico.resize((18, 18))
        app_img_historico = ImageTk.PhotoImage(app_img_historico)
        app_historico = Button(botoes_frame, command=abrir_historico, image=app_img_historico,
                              text="Histórico Escolar", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                              bg=co4, fg=co0)
    except FileNotFoundError:
        app_historico = Button(botoes_frame, command=abrir_historico, text="Histórico Escolar", 
                              compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                              bg=co4, fg=co0)
    app_historico.grid(row=0, column=2, padx=5, pady=5, sticky=EW)
    if 'app_img_historico' in locals():
        setattr(app_historico, '_image_ref', app_img_historico)
    
    # Função para abrir a interface administrativa
    def abrir_interface_administrativa():
        from interface_administrativa import InterfaceAdministrativa
        admin_window = Toplevel(janela)
        admin_window.title("Administração - Escolas, Disciplinas e Cargas Horárias")
        admin_window.geometry('950x670')
        InterfaceAdministrativa(admin_window, janela)

    # Botão para acessar a interface administrativa
    global app_img_admin
    try:
        app_img_admin = Image.open('icon/settings.png')
        app_img_admin = app_img_admin.resize((18, 18))
        app_img_admin = ImageTk.PhotoImage(app_img_admin)
        app_admin = Button(botoes_frame, command=abrir_interface_administrativa, image=app_img_admin,
                          text="Administração", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                          bg=co5, fg=co0)
    except FileNotFoundError:
        app_admin = Button(botoes_frame, command=abrir_interface_administrativa, text="Administração", 
                          compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                          bg=co5, fg=co0)
    app_admin.grid(row=0, column=3, padx=5, pady=5, sticky=EW)
    if 'app_img_admin' in locals():
        setattr(app_admin, '_image_ref', app_img_admin)
    
    def relatorio():
        # Criar menu de meses
        menu_meses = Menu(janela, tearoff=0)
        
        # Obter mês atual
        mes_atual = datetime.now().month
        
        # Lista de meses (gerada a partir do utilitário compartilhado)
        try:
            meses = [nome_mes_pt_folha(i) for i in range(1, 13)]
        except Exception:
            meses = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ]
        
        # Filtrar apenas os meses até o atual
        meses_disponiveis = meses[:mes_atual]
        
        # Adicionar meses ao menu
        for i, mes in enumerate(meses_disponiveis, 1):
            # Chamada segura via wrapper
            menu_meses.add_command(
                label=mes,
                command=lambda m=i: relatorio_movimentacao_mensal(m)
            )
        
        # Mostrar o menu na posição do mouse
        try:
            x = janela.winfo_pointerx()
            y = janela.winfo_pointery()
            menu_meses.post(x, y)
        except:
            # Se não conseguir obter a posição do mouse, mostrar no centro da janela
            menu_meses.post(janela.winfo_rootx() + 100, janela.winfo_rooty() + 100)

    # Definindo a fonte para o menu
    menu_font = ('Ivy', 12)  # Altere o tamanho conforme necessário

    # Criar o menu
    menu_bar = Menu(janela)

    

    # Adicionando o menu "Listas"
    listas_menu = Menu(menu_bar, tearoff=0)

    # Aplicando a fonte às opções do menu
    listas_menu.add_command(label="Lista Atualizada", command=lambda: lista_atualizada_wrapper(), font=menu_font)
    listas_menu.add_command(label="Lista Atualizada SEMED", command=lambda: lista_atualizada_semed_wrapper(), font=menu_font)
    listas_menu.add_command(label="Lista de Reunião", command=lambda: lista_reuniao(), font=menu_font)
    listas_menu.add_command(label="Lista de Notas", command=lambda: lista_notas(), font=menu_font)
    listas_menu.add_command(label="Lista de Frequências", command=lambda: lista_frequencia(), font=menu_font)
    listas_menu.add_separator()
    listas_menu.add_command(label="Contatos de Responsáveis", command=lambda: relatorio_contatos_responsaveis(), font=menu_font)
    listas_menu.add_command(label="Levantamento de Necessidades", command=lambda: relatorio_levantamento_necessidades(), font=menu_font)
    listas_menu.add_command(label="Lista Alfabética", command=lambda: relatorio_lista_alfabetica(), font=menu_font)
    listas_menu.add_command(label="Alunos com Transtornos", command=lambda: relatorio_alunos_transtornos(), font=menu_font)
    listas_menu.add_separator()
    listas_menu.add_command(label="Termo de Responsabilidade", command=lambda: relatorio_termo_responsabilidade(), font=menu_font)
    listas_menu.add_command(label="Tabela de Docentes", command=lambda: relatorio_tabela_docentes(), font=menu_font)
    
    # (Movimento Mensal transferido para o menu 'Serviços')

    # Adicionando o menu à barra de menus
    menu_bar.add_cascade(label="Listas", menu=listas_menu)

    # Adicionando o menu "Notas"
    notas_menu = Menu(menu_bar, tearoff=0)
    notas_menu.add_command(label="Cadastrar/Editar Notas", command=lambda: abrir_cadastro_notas(), font=menu_font)
    notas_menu.add_command(label="Relatório Estatístico de Notas", command=lambda: abrir_relatorio_analise(), font=menu_font)
    
    # Função para abrir a interface de cadastro de notas
    def abrir_cadastro_notas():
        # Esconder a janela principal
        janela.withdraw()
        
        # Criar janela de nível superior
        janela_notas = Toplevel()
        janela_notas.title("Cadastro/Edição de Notas")
        janela_notas.geometry("1000x600")
        janela_notas.grab_set()  # Torna a janela modal
        janela_notas.focus_force()
        
        # Configurar evento de fechamento da janela
        def ao_fechar():
            janela.deiconify()  # Mostrar a janela principal novamente
            janela_notas.destroy()
            
        janela_notas.protocol("WM_DELETE_WINDOW", ao_fechar)
        
        # Criar interface de cadastro de notas
        if _InterfaceCadastroEdicaoNotas:
            try:
                app_notas = _InterfaceCadastroEdicaoNotas.InterfaceCadastroEdicaoNotas(janela_notas, janela_principal=janela)
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao abrir interface de notas: {e}")
                janela.deiconify()
                return
        else:
            # Tenta import dinâmico como fallback e mostra erro amigável se falhar
            try:
                from InterfaceCadastroEdicaoNotas import InterfaceCadastroEdicaoNotas as _ICEN
                app_notas = _ICEN(janela_notas, janela_principal=janela)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível abrir a interface de cadastro/edição de notas: {e}")
                janela.deiconify()
                return
    
    # Função para abrir o relatório estatístico de análise de notas
    def abrir_relatorio_analise():
        try:
            from relatorio_analise_notas import abrir_relatorio_analise_notas
            abrir_relatorio_analise_notas(janela_principal=janela)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o relatório: {e}")
            import traceback
            traceback.print_exc()

    def abrir_gerenciador_horarios():
        # Esconder a janela principal
        janela.withdraw()
        
        # Criar janela de nível superior
        janela_horarios = Toplevel()
        
        # Configurar evento de fechamento da janela
        def ao_fechar():
            janela.deiconify()  # Mostrar a janela principal novamente
            janela_horarios.destroy()
            
        janela_horarios.protocol("WM_DELETE_WINDOW", ao_fechar)
        
        # Criar interface de horários escolares
        app_horarios = InterfaceHorariosEscolares(
            janela_horarios, janela_principal=janela)

    # Adicionando o menu à barra de menus
    menu_bar.add_cascade(label="Gerenciamento de Notas", menu=notas_menu)

    # =========================
    # Serviços
    # =========================
    servicos_menu = Menu(menu_bar, tearoff=0)

    # Criar submenu para Movimento Mensal (moved from 'Listas')
    movimento_mensal_menu = Menu(servicos_menu, tearoff=0)
    movimento_mensal_menu.add_command(label="Gerar Relatório", command=selecionar_mes_movimento, font=menu_font)
    servicos_menu.add_cascade(label="Movimento Mensal", menu=movimento_mensal_menu, font=menu_font)

    def abrir_solicitacao_professores():
        try:
            from InterfaceSolicitacaoProfessores import abrir_interface_solicitacao
            abrir_interface_solicitacao(janela_principal=janela)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a solicitação: {e}")

    # Função para abrir o gerenciador de documentos de funcionários
    def abrir_gerenciador_documentos():
        # Esconder a janela principal
        janela.withdraw()
        
        # Criar janela do gerenciador
        janela_docs = Toplevel(janela)
        janela_docs.title("Gerenciador de Documentos de Funcionários")
        app = GerenciadorDocumentosFuncionarios(janela_docs)
        janela_docs.focus_force()
        janela_docs.grab_set()
        
        # Função para quando a janela for fechada
        def ao_fechar():
            janela.deiconify()  # Mostrar a janela principal novamente
            janela_docs.destroy()
            
        # Configurar o evento de fechamento
        janela_docs.protocol("WM_DELETE_WINDOW", ao_fechar)

    # Função para abrir o gerenciador de documentos do sistema
    def abrir_gerenciador_documentos_sistema():
        # Esconder a janela principal
        janela.withdraw()
        
        # Criar janela do gerenciador
        janela_docs = Toplevel(janela)
        janela_docs.title("Gerenciador de Documentos do Sistema")
        from GerenciadorDocumentosSistema import GerenciadorDocumentosSistema
        app = GerenciadorDocumentosSistema(janela_docs)
        janela_docs.focus_force()
        janela_docs.grab_set()
        
        # Função para quando a janela for fechada
        def ao_fechar():
            janela.deiconify()  # Mostrar a janela principal novamente
            janela_docs.destroy()
            
        # Configurar o evento de fechamento
        janela_docs.protocol("WM_DELETE_WINDOW", ao_fechar)

    servicos_menu.add_command(
        label="Solicitação de Professores e Coordenadores",
        command=abrir_solicitacao_professores,
        font=menu_font
    )

    servicos_menu.add_command(
        label="Gerenciador de Documentos de Funcionários",
        command=abrir_gerenciador_documentos,
        font=menu_font
    )

    servicos_menu.add_command(
        label="Gerenciador de Documentos do Sistema",
        command=abrir_gerenciador_documentos_sistema,
        font=menu_font
    )

    # Função para abrir a interface de declaração de comparecimento
    def abrir_interface_declaracao_comparecimento_menu():
        """Abre interface para selecionar aluno e gerar declaração de comparecimento"""
        from tkinter import Toplevel, Frame, Label, Entry, Button, Listbox, Scrollbar, END
        from tkcalendar import DateEntry
        
        # Ocultar janela principal
        janela.withdraw()
        
        # Criar janela
        janela_decl = Toplevel(janela)
        janela_decl.title("Declaração de Comparecimento de Responsável")
        janela_decl.geometry("600x600")
        janela_decl.configure(bg=co1)
        
        # Restaurar janela principal quando fechar
        def ao_fechar():
            janela_decl.destroy()
            janela.deiconify()
        
        janela_decl.protocol("WM_DELETE_WINDOW", ao_fechar)
        janela_decl.focus_force()
        
        frame_principal = Frame(janela_decl, bg=co1, padx=20, pady=20)
        frame_principal.pack(fill='both', expand=True)
        
        # Título
        Label(frame_principal, text="Gerar Declaração de Comparecimento", 
              font=("Arial", 14, "bold"), bg=co1, fg=co0).pack(pady=(0, 15))
        
        # Frame de pesquisa
        frame_pesquisa = Frame(frame_principal, bg=co1)
        frame_pesquisa.pack(fill='x', pady=(0, 10))
        
        Label(frame_pesquisa, text="Pesquisar Aluno:", bg=co1, fg=co0, 
              font=("Arial", 11)).pack(anchor='w', pady=(0, 5))
        
        pesquisa_entry = Entry(frame_pesquisa, width=50, font=("Arial", 11))
        pesquisa_entry.pack(fill='x', pady=(0, 5))
        
        # Frame para lista de alunos
        frame_lista = Frame(frame_principal, bg=co1)
        frame_lista.pack(fill='both', expand=True, pady=(0, 10))
        
        Label(frame_lista, text="Selecione o Aluno:", bg=co1, fg=co0, 
              font=("Arial", 11)).pack(anchor='w', pady=(0, 5))
        
        # Listbox com scrollbar
        scrollbar = Scrollbar(frame_lista)
        scrollbar.pack(side='right', fill='y')
        
        listbox_alunos = Listbox(frame_lista, font=("Arial", 10), 
                                yscrollcommand=scrollbar.set, height=10)
        listbox_alunos.pack(fill='both', expand=True)
        scrollbar.config(command=listbox_alunos.yview)
        
        # Dicionário para mapear índice -> ID do aluno
        alunos_dict = {}
        
        # Variável para armazenar o aluno selecionado
        aluno_selecionado_id = {'id': None}
        
        # Função para carregar alunos
        def carregar_alunos(filtro=""):
            listbox_alunos.delete(0, END)
            alunos_dict.clear()

            try:
                with get_connection() as conn:
                    if conn is None:
                        messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                        return
                    cursor = conn.cursor()
                    try:
                        # Obter ano letivo atual
                        cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = YEAR(CURDATE())")
                        ano_atual = cursor.fetchone()

                        if not ano_atual:
                            cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                            ano_atual = cursor.fetchone()

                        ano_letivo_id = ano_atual[0] if ano_atual else 1

                        if filtro:
                            query = """
                                SELECT DISTINCT a.id, a.nome, s.nome as serie, t.nome as turma
                                FROM alunos a
                                INNER JOIN matriculas m ON a.id = m.aluno_id
                                INNER JOIN turmas t ON m.turma_id = t.id
                                INNER JOIN serie s ON t.serie_id = s.id
                                WHERE a.escola_id = 60 
                                AND m.ano_letivo_id = %s
                                AND m.status IN ('Ativo', 'Transferido')
                                AND a.nome LIKE %s
                                ORDER BY a.nome
                            """
                            cursor.execute(query, (int(str(ano_letivo_id)) if ano_letivo_id is not None else 1, f"%{filtro}%"))
                        else:
                            query = """
                                SELECT DISTINCT a.id, a.nome, s.nome as serie, t.nome as turma
                                FROM alunos a
                                INNER JOIN matriculas m ON a.id = m.aluno_id
                                INNER JOIN turmas t ON m.turma_id = t.id
                                INNER JOIN serie s ON t.serie_id = s.id
                                WHERE a.escola_id = 60 
                                AND m.ano_letivo_id = %s
                                AND m.status IN ('Ativo', 'Transferido')
                                ORDER BY a.nome
                            """
                            cursor.execute(query, (int(str(ano_letivo_id)) if ano_letivo_id is not None else 1,))

                        resultados = cursor.fetchall()

                        for idx, (aluno_id, nome, serie, turma) in enumerate(resultados):
                            info_adicional = ""
                            if serie:
                                info_adicional = f" - {serie}"
                                if turma:
                                    info_adicional += f" {turma}"

                            texto = f"{nome}{info_adicional}"
                            listbox_alunos.insert(END, texto)
                            alunos_dict[idx] = aluno_id
                    finally:
                        try:
                            cursor.close()
                        except Exception:
                            pass

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar alunos: {str(e)}")
        
        # Carregar alunos inicialmente
        carregar_alunos()
        
        # Vincular pesquisa
        def pesquisar(event=None):
            filtro = pesquisa_entry.get()
            carregar_alunos(filtro)
        
        pesquisa_entry.bind("<KeyRelease>", pesquisar)
        
        # Frame para parâmetros
        frame_params = Frame(frame_principal, bg=co1)
        frame_params.pack(fill='x', pady=(10, 0))
        
        # Label para mostrar aluno selecionado
        Label(frame_params, text="Aluno Selecionado:", bg=co1, fg=co0, 
              font=("Arial", 11, "bold")).grid(row=0, column=0, sticky='w', pady=5, columnspan=2)
        
        aluno_selecionado_label = Label(frame_params, text="Nenhum aluno selecionado", 
                                       bg=co1, fg=co2, font=("Arial", 10))
        aluno_selecionado_label.grid(row=1, column=0, sticky='w', pady=5, columnspan=2)
        
        # Seleção de Responsável
        Label(frame_params, text="Responsável:", bg=co1, fg=co0, 
              font=("Arial", 11)).grid(row=2, column=0, sticky='w', pady=5)
        
        responsavel_var = StringVar()
        combo_responsavel = ttk.Combobox(frame_params, textvariable=responsavel_var, 
                                        width=30, state='readonly')
        combo_responsavel.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Turno
        Label(frame_params, text="Turno da Reunião:", bg=co1, fg=co0, 
              font=("Arial", 11)).grid(row=3, column=0, sticky='w', pady=5)
        
        turno_var = StringVar(value="Matutino")
        combo_turno = ttk.Combobox(frame_params, textvariable=turno_var, 
                                   width=15, state='readonly',
                                   values=["Matutino", "Vespertino"])
        combo_turno.grid(row=3, column=1, sticky='w', padx=(10, 0), pady=5)
        
        Label(frame_params, text="Data do Comparecimento:", bg=co1, fg=co0, 
              font=("Arial", 11)).grid(row=4, column=0, sticky='w', pady=5)
        
        data_entry = DateEntry(frame_params, width=20, background='darkblue', 
                              foreground='white', borderwidth=2, 
                              date_pattern='dd/mm/yyyy')
        data_entry.grid(row=4, column=1, sticky='w', padx=(10, 0), pady=5)
        
        Label(frame_params, text="Motivo:", bg=co1, fg=co0, 
              font=("Arial", 11)).grid(row=5, column=0, sticky='w', pady=5)
        
        motivo_entry = Entry(frame_params, width=30, font=("Arial", 11))
        motivo_entry.insert(0, "reunião escolar")
        motivo_entry.grid(row=5, column=1, sticky='w', padx=(10, 0), pady=5)
        
        # Função para carregar responsáveis quando um aluno for selecionado
        def on_aluno_select(event):
            selecao = listbox_alunos.curselection()
            if not selecao:
                return
            
            idx = selecao[0]
            aluno_id = alunos_dict.get(idx)
            
            # Salvar o ID do aluno selecionado
            aluno_selecionado_id['id'] = aluno_id
            
            # Mostrar nome do aluno selecionado
            nome_aluno = listbox_alunos.get(idx)
            aluno_selecionado_label.config(text=f"✓ {nome_aluno}", fg=co2)
            
            if aluno_id:
                try:
                    with get_connection() as conn:
                        if conn is None:
                            logger.error("Erro: Não foi possível conectar ao banco de dados.")
                            return
                        cursor = conn.cursor()
                        try:
                            # Buscar responsáveis do aluno
                            query = """
                                SELECT DISTINCT 
                                    r.nome,
                                    r.cpf
                                FROM responsaveis r
                                INNER JOIN responsaveisalunos ra ON r.id = ra.responsavel_id
                                WHERE ra.aluno_id = %s
                            """
                            cursor.execute(query, (aluno_id,))
                            resultados = cursor.fetchall()

                            responsaveis = []
                            # Adicionar todos os responsáveis encontrados
                            for row in resultados:
                                if row and row[0]:
                                    responsaveis.append(row[0])
                        finally:
                            try:
                                cursor.close()
                            except Exception:
                                pass

                    # Atualizar combobox
                    if responsaveis:
                        combo_responsavel['values'] = responsaveis
                        combo_responsavel.set(responsaveis[0])
                    else:
                        combo_responsavel['values'] = ["Responsável não cadastrado"]
                        combo_responsavel.set("Responsável não cadastrado")
                except Exception as e:
                    logger.error(f"Erro ao carregar responsáveis: {str(e)}")
        
        # Vincular evento de seleção
        listbox_alunos.bind("<<ListboxSelect>>", on_aluno_select)
        
        # Função para gerar
        def gerar():
            # Usar o ID do aluno salvo em vez da seleção da listbox
            aluno_id = aluno_selecionado_id['id']
            
            if not aluno_id:
                messagebox.showwarning("Aviso", "Por favor, selecione um aluno.")
                return
            
            responsavel_selecionado = responsavel_var.get()
            if not responsavel_selecionado or responsavel_selecionado == "Responsável não cadastrado":
                messagebox.showwarning("Aviso", "Por favor, selecione um responsável válido.")
                return
            
            turno_selecionado = turno_var.get()
            if not turno_selecionado:
                messagebox.showwarning("Aviso", "Por favor, selecione o turno da reunião.")
                return
            
            data_selecionada = data_entry.get_date()
            motivo = motivo_entry.get()
            
            # Passar os novos parâmetros para a função
            gerar_declaracao_comparecimento_responsavel(
                aluno_id, data_selecionada, motivo, 
                responsavel_selecionado, turno_selecionado
            )
            
            # Fechar interface e restaurar janela principal
            janela_decl.destroy()
            janela.deiconify()
        
        # Botões
        frame_botoes = Frame(frame_principal, bg=co1)
        frame_botoes.pack(fill='x', pady=(15, 0))
        
        Button(frame_botoes, text="Gerar Declaração", command=gerar, 
               bg=co2, fg=co0, font=("Arial", 11, "bold"), 
               width=18).pack(side='left', padx=5)
        
        Button(frame_botoes, text="Cancelar", command=janela_decl.destroy,
               bg=co4, fg=co0, font=("Arial", 11), 
               width=12).pack(side='right', padx=5)

    servicos_menu.add_separator()
    
    servicos_menu.add_command(
        label="Declaração de Comparecimento (Responsável)",
        command=abrir_interface_declaracao_comparecimento_menu,
        font=menu_font
    )

    # Função para gerar crachás
    def abrir_interface_crachas():
        """Abre uma interface para gerar crachás de alunos e responsáveis de forma não bloqueante.

        Cria a janela de progresso no thread principal e executa a geração em background.
        """
        resposta = messagebox.askyesno(
            "Gerar Crachás",
            "Deseja gerar crachás para todos os alunos ativos?\n\n"
            "Os crachás serão salvos na pasta 'Cracha_Anos_Iniciais', "
            "organizados por série e turma."
        )

        if not resposta:
            return

        # Ocultar janela principal temporariamente
        janela.withdraw()

        # Criar janela de progresso (UI deve ser criada no thread principal)
        janela_progresso = Toplevel(janela)
        janela_progresso.title("Gerando Crachás")
        janela_progresso.geometry("400x150")
        janela_progresso.resizable(False, False)
        janela_progresso.configure(bg=co1)

        # Centralizar na tela
        janela_progresso.update_idletasks()
        x = (janela_progresso.winfo_screenwidth() // 2) - (400 // 2)
        y = (janela_progresso.winfo_screenheight() // 2) - (150 // 2)
        janela_progresso.geometry(f"400x150+{x}+{y}")

        frame_prog = Frame(janela_progresso, bg=co1, padx=20, pady=20)
        frame_prog.pack(fill=BOTH, expand=True)

        Label(frame_prog, text="Gerando crachás...", font=("Arial", 12, "bold"), bg=co1, fg=co0).pack(pady=10)
        Label(frame_prog, text="Aguarde, isso pode levar alguns minutos.", font=("Arial", 10), bg=co1, fg=co0).pack(pady=5)

        progresso = Progressbar(frame_prog, mode='indeterminate', length=300)
        progresso.pack(pady=10)
        try:
            progresso.start(10)
        except Exception:
            pass

        janela_progresso.update()

        # Trabalho pesado em background
        def _worker():
            success = False
            error_msg = None
            caminho = None
            try:
                # Usar o serviço centralizado para gerar crachás
                from services.report_service import gerar_crachas_para_todos_os_alunos as service_gerar
                caminho = service_gerar()
                success = True
            except Exception as e:
                success = False
                error_msg = e

            # Atualizar UI no thread principal
            def _on_done():
                try:
                    progresso.stop()
                except Exception:
                    pass
                try:
                    janela_progresso.destroy()
                except Exception:
                    pass
                # Restaurar janela principal
                try:
                    janela.deiconify()
                except Exception:
                    pass

                if not success:
                    if isinstance(error_msg, ImportError):
                        messagebox.showerror("Erro de Importação", f"Não foi possível importar o módulo de geração de crachás:\n{error_msg}")
                    else:
                        messagebox.showerror("Erro", f"Erro ao gerar crachás:\n{error_msg}")
                    return

                # Sucesso: avisar e abrir pasta
                caminho_crachas = caminho or os.path.join(os.getcwd(), "Cracha_Anos_Iniciais")
                messagebox.showinfo(
                    "Sucesso",
                    f"Crachás gerados com sucesso!\n\n"
                    f"Os arquivos foram salvos em:\n{caminho_crachas}\n\n"
                    f"A pasta será aberta automaticamente."
                )

                try:
                    import subprocess
                    import platform
                    if platform.system() == 'Windows':
                        os.startfile(caminho_crachas)
                    elif platform.system() == 'Darwin':
                        subprocess.Popen(['open', caminho_crachas])
                    else:
                        subprocess.Popen(['xdg-open', caminho_crachas])
                except Exception:
                    # Problema ao abrir a pasta não é crítico
                    logger.warning(f"Não foi possível abrir a pasta dos crachás: {caminho_crachas}")

            janela.after(0, _on_done)

        try:
            from utils.executor import submit_background
            submit_background(_worker, janela=janela)
        except Exception:
            from threading import Thread
            Thread(target=_worker, daemon=True).start()

    servicos_menu.add_command(
        label="Crachás Alunos/Responsáveis",
        command=abrir_interface_crachas,
        font=menu_font
    )

    # Função para abrir importação de notas do HTML
    def abrir_importacao_notas_html():
        """Abre interface para importar notas de arquivo HTML do GEDUC"""
        try:
            # Ocultar janela principal
            janela.withdraw()
            
            # Importar e executar o módulo de importação
            from importar_notas_html import interface_importacao
            
            # Passa a referência da janela principal
            interface_importacao(janela_pai=janela)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir importação de notas: {e}")
            janela.deiconify()

    servicos_menu.add_command(
        label="Importar Notas do GEDUC (HTML → Excel)",
        command=abrir_importacao_notas_html,
        font=menu_font
    )
    
    # Função para abrir a transição de ano letivo
    def abrir_transicao_ano_letivo():
        """Abre interface para transição de ano letivo"""
        import os
        from dotenv import load_dotenv
        from tkinter import simpledialog
        
        # Carregar senha do banco de dados
        load_dotenv()
        senha_correta = os.getenv('DB_PASSWORD')
        
        # Solicitar senha ao usuário
        senha_digitada = simpledialog.askstring(
            "Autenticação Necessária",
            "Digite a senha do banco de dados para acessar a Transição de Ano Letivo:",
            show='*'
        )
        
        # Verificar se o usuário cancelou
        if senha_digitada is None:
            return
        
        # Verificar senha
        if senha_digitada != senha_correta:
            messagebox.showerror(
                "Acesso Negado",
                "Senha incorreta! A transição de ano letivo é uma operação crítica\n"
                "e requer autenticação para prosseguir."
            )
            return
        
        # Se a senha estiver correta, abrir a interface
        try:
            from transicao_ano_letivo import abrir_interface_transicao
            abrir_interface_transicao(janela_principal=janela)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir transição de ano letivo: {e}")
            traceback.print_exc()
    
    servicos_menu.add_separator()
    servicos_menu.add_command(
        label="🔄 Transição de Ano Letivo",
        command=abrir_transicao_ano_letivo,
        font=menu_font
    )

    menu_bar.add_cascade(label="Serviços", menu=servicos_menu)

    # =========================
    # Gerenciamento de Faltas
    # =========================
    faltas_menu = Menu(menu_bar, tearoff=0)

    def abrir_dialogo_folhas_ponto():
        dialog = Toplevel(janela)
        dialog.title("Gerar Folhas de Ponto")
        dialog.geometry("380x200")
        dialog.resizable(False, False)
        dialog.transient(janela)
        dialog.grab_set()

        mes_var = IntVar(value=datetime.today().month)
        ano_var = IntVar(value=datetime.today().year)
        pasta_var = StringVar(value=os.getcwd())

        frame = Frame(dialog, padx=15, pady=15)
        frame.pack(fill=BOTH, expand=True)

        Label(frame, text="Mês:").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Spinbox(frame, from_=1, to=12, width=5, textvariable=mes_var).grid(row=0, column=1, sticky=W)

        Label(frame, text="Ano:").grid(row=1, column=0, sticky=W, pady=5)
        ttk.Spinbox(frame, from_=2020, to=2100, width=7, textvariable=ano_var).grid(row=1, column=1, sticky=W)

        Label(frame, text="Pasta de saída:").grid(row=2, column=0, sticky=W, pady=5)
        entrada_pasta = Entry(frame, textvariable=pasta_var, width=28)
        entrada_pasta.grid(row=2, column=1, sticky=W)

        def escolher_pasta():
            pasta = filedialog.askdirectory()
            if pasta:
                pasta_var.set(pasta)

        Button(frame, text="Escolher…", command=escolher_pasta).grid(row=2, column=2, padx=5)

        def gerar():
            dialog.destroy()
            try:
                try:
                    from services.utils.templates import find_template
                    base_pdf = find_template("folha de ponto.pdf")
                except Exception:
                    base_pdf = os.path.join(os.getcwd(), "Modelos", "folha de ponto.pdf")
                    if not os.path.isfile(base_pdf):
                        base_pdf = os.path.join(os.getcwd(), "folha de ponto.pdf")
                if not os.path.isfile(base_pdf):
                    messagebox.showerror("Erro", f"Arquivo base não encontrado: {base_pdf}")
                    return
                mes = mes_var.get()
                ano = ano_var.get()
                nome_mes = nome_mes_pt_folha(mes)
                saida = os.path.join(pasta_var.get(), f"Folhas_de_Ponto_{nome_mes}_{ano}.pdf")
                if status_label is not None:
                    status_label.config(text=f"Gerando folhas de ponto de {nome_mes}/{ano}…")

                def _worker():
                    # Executa a geração em background e retorna o caminho de saída
                    gerar_folhas_de_ponto(base_pdf, saida, mes_referencia=mes, ano_referencia=ano)
                    return saida

                try:
                    _run_report_in_background(_worker, f"Folhas de Ponto {nome_mes}/{ano}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao agendar geração das folhas de ponto: {e}")
            except Exception as e:
                if status_label is not None:
                    status_label.config(text="")
                messagebox.showerror("Erro", str(e))

        botoes = Frame(dialog, padx=15, pady=10)
        botoes.pack(fill=X)
        Button(botoes, text="Cancelar", command=dialog.destroy).pack(side=RIGHT, padx=5)
        Button(botoes, text="Gerar", command=gerar, bg=co5, fg=co0).pack(side=RIGHT)

    def abrir_dialogo_resumo_ponto():
        dialog = Toplevel(janela)
        dialog.title("Gerar Resumo de Ponto")
        dialog.geometry("320x160")
        dialog.resizable(False, False)
        dialog.transient(janela)
        dialog.grab_set()

        mes_var = IntVar(value=datetime.today().month)
        ano_var = IntVar(value=datetime.today().year)

        frame = Frame(dialog, padx=15, pady=15)
        frame.pack(fill=BOTH, expand=True)

        Label(frame, text="Mês:").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Spinbox(frame, from_=1, to=12, width=5, textvariable=mes_var).grid(row=0, column=1, sticky=W)

        Label(frame, text="Ano:").grid(row=1, column=0, sticky=W, pady=5)
        ttk.Spinbox(frame, from_=2020, to=2100, width=7, textvariable=ano_var).grid(row=1, column=1, sticky=W)

        def gerar():
            dialog.destroy()
            try:
                mes = mes_var.get()
                ano = ano_var.get()
                nome_mes = nome_mes_pt_resumo(mes)
                if status_label is not None:
                    status_label.config(text=f"Gerando resumo de ponto de {nome_mes}/{ano}…")

                def _worker():
                    gerar_resumo_ponto(mes, ano)
                    return None

                try:
                    _run_report_in_background(_worker, f"Resumo de Ponto {nome_mes}/{ano}")
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao agendar resumo de ponto: {e}")
            except Exception as e:
                if status_label is not None:
                    status_label.config(text="")
                messagebox.showerror("Erro", str(e))

        botoes = Frame(dialog, padx=15, pady=10)
        botoes.pack(fill=X)
        Button(botoes, text="Cancelar", command=dialog.destroy).pack(side=RIGHT, padx=5)
        Button(botoes, text="Gerar", command=gerar, bg=co5, fg=co0).pack(side=RIGHT)

    # Cadastrar/Editar Faltas de Funcionários
    def abrir_cadastro_faltas():
        try:
            from InterfaceCadastroEdicaoFaltas import abrir_interface_faltas
            abrir_interface_faltas(janela_principal=janela)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a interface de faltas: {e}")

    faltas_menu.add_command(label="Cadastrar/Editar Faltas", command=abrir_cadastro_faltas, font=menu_font)
    faltas_menu.add_separator()
    faltas_menu.add_command(label="Gerar Folhas de Ponto", command=abrir_dialogo_folhas_ponto, font=menu_font)
    faltas_menu.add_command(label="Gerar Resumo de Ponto", command=abrir_dialogo_resumo_ponto, font=menu_font)

    menu_bar.add_cascade(label="Gerenciamento de Faltas", menu=faltas_menu)
    
    # --- Menu: Documentos da Escola (posicionado após Gerenciamento de Faltas) ---
    documentos_menu = Menu(menu_bar, tearoff=0)

    def abrir_documento_da_escola(chave):
        """Abre os documentos oficiais da escola no navegador usando links do Google Drive."""
        links = {
            'estatuto': 'https://drive.google.com/file/d/14piUCRRxRlfh1EC_LiT_npmbPkOkgUS4/view?usp=sharing',
            'ppp': 'https://drive.google.com/file/d/1SDDy5PnxbTyDbqbfGKhLDrdRgdozGt-1/view?usp=sharing',
            'cnpj': 'https://drive.google.com/file/d/1-pW8FK7bq2v-vLFfczvqQv4lUw-MlF2r/view?usp=sharing',
        }

        link = links.get(chave)
        if not link:
            messagebox.showwarning("Documento não configurado", "Documento não encontrado.")
            return

        try:
            webbrowser.open(link)
        except Exception as e:
            messagebox.showerror("Erro ao abrir documento", str(e))

    documentos_menu.add_command(label="Estatuto da Escola", command=lambda: abrir_documento_da_escola('estatuto'), font=menu_font)
    documentos_menu.add_command(label="PPP da Escola", command=lambda: abrir_documento_da_escola('ppp'), font=menu_font)
    documentos_menu.add_command(label="CNPJ da Escola", command=lambda: abrir_documento_da_escola('cnpj'), font=menu_font)

    menu_bar.add_cascade(label="Documentos da Escola", menu=documentos_menu)

    # Função para abrir interface de relatório avançado
    def abrir_relatorio_avancado():
        # Criar janela para configuração de relatório avançado
        janela_relatorio = Toplevel(janela)
        janela_relatorio.title("Relatório de Notas - Opções Avançadas")
        janela_relatorio.geometry("500x350")
        janela_relatorio.resizable(False, False)
        janela_relatorio.transient(janela)  # Torna a janela dependente da principal
        janela_relatorio.grab_set()  # Torna a janela modal
        
        # Variáveis para armazenar as opções
        bimestre_var = StringVar(value="1º bimestre")
        nivel_var = StringVar(value="iniciais")
        ano_letivo_var = IntVar(value=2025)
        status_var = StringVar(value="Ativo")
        incluir_transferidos = BooleanVar(value=False)
        preencher_zeros = BooleanVar(value=False)
        
        # Frame principal
        frame_principal = Frame(janela_relatorio, padx=20, pady=20)
        frame_principal.pack(fill=BOTH, expand=True)
        
        # Título
        Label(frame_principal, text="Configurar Relatório de Notas", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=W)
        
        # Bimestre
        Label(frame_principal, text="Bimestre:", anchor=W).grid(row=1, column=0, sticky=W, pady=5)
        bimestres = ["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
        combo_bimestre = ttk.Combobox(frame_principal, textvariable=bimestre_var, values=bimestres, state="readonly", width=20)
        combo_bimestre.grid(row=1, column=1, sticky=W, pady=5)
        
        # Nível de ensino
        Label(frame_principal, text="Nível de ensino:", anchor=W).grid(row=2, column=0, sticky=W, pady=5)
        frame_nivel = Frame(frame_principal)
        frame_nivel.grid(row=2, column=1, sticky=W, pady=5)
        Radiobutton(frame_nivel, text="Séries iniciais (1º ao 5º)", variable=nivel_var, value="iniciais").pack(anchor=W)
        Radiobutton(frame_nivel, text="Séries finais (6º ao 9º)", variable=nivel_var, value="finais").pack(anchor=W)
        
        # Ano letivo
        Label(frame_principal, text="Ano letivo:", anchor=W).grid(row=3, column=0, sticky=W, pady=5)
        anos = ["2023", "2024", "2025", "2026", "2027"]
        combo_ano = ttk.Combobox(frame_principal, textvariable=ano_letivo_var, values=anos, state="readonly", width=20)
        combo_ano.grid(row=3, column=1, sticky=W, pady=5)
        
        # Status de matrícula
        Label(frame_principal, text="Status de matrícula:", anchor=W).grid(row=4, column=0, sticky=W, pady=5)
        frame_status = Frame(frame_principal)
        frame_status.grid(row=4, column=1, sticky=W, pady=5)
        Radiobutton(frame_status, text="Apenas ativos", variable=status_var, value="Ativo").pack(anchor=W)
        Checkbutton(frame_status, text="Incluir transferidos", variable=incluir_transferidos).pack(anchor=W)
        
        # Opções de exibição
        Label(frame_principal, text="Opções de exibição:", anchor=W).grid(row=5, column=0, sticky=W, pady=5)
        frame_opcoes = Frame(frame_principal)
        frame_opcoes.grid(row=5, column=1, sticky=W, pady=5)
        Checkbutton(frame_opcoes, text="Preencher notas em branco com zeros", variable=preencher_zeros).pack(anchor=W)
        
        # Frame para botões
        frame_botoes = Frame(janela_relatorio, padx=20, pady=15)
        frame_botoes.pack(fill=X)
        
        # Função para gerar o relatório
        def gerar_relatorio():
            bimestre = bimestre_var.get()
            nivel = nivel_var.get()
            ano = ano_letivo_var.get()
            preencher_com_zeros = preencher_zeros.get()
            
            # Configurar status de matrícula
            if incluir_transferidos.get():
                status = ["Ativo", "Transferido"]
            else:
                status = status_var.get()
            
            # Fechar a janela
            janela_relatorio.destroy()
            
            # Exibir feedback ao usuário
            if status_label is not None:
                status_label.config(text=f"Gerando relatório de notas para {bimestre} ({nivel})...")
            janela.update()
            
            # Gerar o relatório
            try:
                resultado = gerar_relatorio_notas(
                    bimestre=bimestre,
                    nivel_ensino=nivel,
                    ano_letivo=ano,
                    status_matricula=status,
                    preencher_nulos=preencher_com_zeros
                )
                
                if resultado:
                    if status_label is not None:
                        status_label.config(text=f"Relatório gerado com sucesso!")
                else:
                    if status_label is not None:
                        status_label.config(text=f"Nenhum dado encontrado para o relatório.")
                    messagebox.showwarning("Sem dados", f"Não foram encontrados dados para o {bimestre} no nível {nivel}.")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao gerar relatório: {str(e)}")
                if status_label is not None:
                    status_label.config(text="")
        
        # Botões
        Button(frame_botoes, text="Cancelar", command=janela_relatorio.destroy, width=10).pack(side=RIGHT, padx=5)
        Button(frame_botoes, text="Gerar", command=gerar_relatorio, width=10, bg=co5, fg=co0).pack(side=RIGHT, padx=5)
    
    # Adicionar as opções dos bimestres e Ata Geral ao menu
    notas_menu.add_separator()
    notas_menu.add_command(label="1º bimestre", command=lambda: nota_bimestre("1º bimestre"), font=menu_font)
    notas_menu.add_command(label="2º bimestre", command=lambda: nota_bimestre("2º bimestre"), font=menu_font)
    notas_menu.add_command(label="3º bimestre", command=lambda: nota_bimestre("3º bimestre"), font=menu_font)
    notas_menu.add_command(label="4º bimestre", command=lambda: nota_bimestre("4º bimestre"), font=menu_font)
    
    # Adicionando separador para as opções de séries finais
    notas_menu.add_separator()
    notas_menu.add_command(label="1º bimestre (6º ao 9º ano)", command=lambda: nota_bimestre2("1º bimestre"), font=menu_font)
    notas_menu.add_command(label="2º bimestre (6º ao 9º ano)", command=lambda: nota_bimestre2("2º bimestre"), font=menu_font)
    notas_menu.add_command(label="3º bimestre (6º ao 9º ano)", command=lambda: nota_bimestre2("3º bimestre"), font=menu_font)
    notas_menu.add_command(label="4º bimestre (6º ao 9º ano)", command=lambda: nota_bimestre2("4º bimestre"), font=menu_font)
    notas_menu.add_separator()
    notas_menu.add_command(label="Relatório Avançado", command=abrir_relatorio_avancado, font=menu_font)
    
    # Adicionar submenu para relatórios com assinatura de responsáveis
    relatorios_assinatura_menu = Menu(notas_menu, tearoff=0)
    relatorios_assinatura_menu.add_command(label="1º bimestre", command=lambda: nota_bimestre_com_assinatura("1º bimestre"), font=menu_font)
    relatorios_assinatura_menu.add_command(label="2º bimestre", command=lambda: nota_bimestre_com_assinatura("2º bimestre"), font=menu_font)
    relatorios_assinatura_menu.add_command(label="3º bimestre", command=lambda: nota_bimestre_com_assinatura("3º bimestre"), font=menu_font)
    relatorios_assinatura_menu.add_command(label="4º bimestre", command=lambda: nota_bimestre_com_assinatura("4º bimestre"), font=menu_font)
    relatorios_assinatura_menu.add_separator()
    relatorios_assinatura_menu.add_command(label="1º bimestre (6º ao 9º ano)", command=lambda: nota_bimestre2_com_assinatura("1º bimestre"), font=menu_font)
    relatorios_assinatura_menu.add_command(label="2º bimestre (6º ao 9º ano)", command=lambda: nota_bimestre2_com_assinatura("2º bimestre"), font=menu_font)
    relatorios_assinatura_menu.add_command(label="3º bimestre (6º ao 9º ano)", command=lambda: nota_bimestre2_com_assinatura("3º bimestre"), font=menu_font)
    relatorios_assinatura_menu.add_command(label="4º bimestre (6º ao 9º ano)", command=lambda: nota_bimestre2_com_assinatura("4º bimestre"), font=menu_font)
    relatorios_assinatura_menu.add_separator()
    relatorios_assinatura_menu.add_command(label="Relatório Avançado", command=abrir_relatorio_avancado_com_assinatura, font=menu_font)
    
    notas_menu.add_cascade(label="Relatórios com Assinatura", menu=relatorios_assinatura_menu, font=menu_font)
    
    notas_menu.add_separator()
    notas_menu.add_command(label="Ata Geral", command=lambda: abrir_interface_ata(janela, status_label), font=menu_font)
    notas_menu.add_separator()
    notas_menu.add_command(label="Relatório de Pendências", command=abrir_relatorio_pendencias, font=menu_font)

    # Configurando o menu na janela
    janela.config(menu=menu_bar)

    # Botão de Backup usando o mesmo padrão dos outros botões
    if app_img_matricula:
        backup_button = Button(botoes_frame, command=lambda: Seguranca.fazer_backup(), image=app_img_matricula,
                           text="Backup", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                           bg=co6, fg=co7)
    else:
        backup_button = Button(botoes_frame, command=lambda: Seguranca.fazer_backup(), text="Backup",
                           overrelief=RIDGE, font=('Ivy 11'), bg=co6, fg=co7)
    backup_button.grid(row=0, column=4, padx=5, pady=5, sticky=EW)

    # Botão de Restaurar usando o mesmo padrão
    if app_img_matricula:
        restaurar_button = Button(botoes_frame, command=lambda: Seguranca.restaurar_backup(), image=app_img_matricula,
                              text="Restaurar", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                              bg=co9, fg=co0)
    else:
        restaurar_button = Button(botoes_frame, command=lambda: Seguranca.restaurar_backup(), text="Restaurar",
                              overrelief=RIDGE, font=('Ivy 11'), bg=co9, fg=co0)
    restaurar_button.grid(row=0, column=5, padx=5, pady=5, sticky=EW)
    
    # Botão de Horários (NOVO)
    try:
        app_img_horarios = Image.open("icon/plus-square-fill.png")
        app_img_horarios = app_img_horarios.resize((18, 18))
        app_img_horarios = ImageTk.PhotoImage(app_img_horarios)
        app_horarios = Button(botoes_frame, command=abrir_gerenciador_horarios, image=app_img_horarios,
                             text="Horários", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                             bg=co3, fg=co0)
    except FileNotFoundError:
        app_horarios = Button(botoes_frame, command=abrir_gerenciador_horarios, text="Horários",
                             compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                             bg=co3, fg=co0)
    app_horarios.grid(row=0, column=6, padx=5, pady=5, sticky=EW)
    if 'app_img_horarios' in locals():
        setattr(app_horarios, '_image_ref', app_img_horarios)

    # Remover o OptionMenu e variáveis relacionadas
    def opcao_selecionada(value):
        if value == "Ata Geral":
            abrir_interface_ata(janela, status_label)
        else:
            nota_bimestre(value)

    # Rodapé
    criar_rodape()

def criar_rodape():
    """Cria o rodapé na parte inferior da janela."""
    global label_rodape, status_label
    
    # Remove qualquer rodapé existente
    if label_rodape is not None:
        label_rodape.destroy()
    
    # Cria um frame para o rodapé
    frame_rodape = Frame(janela, bg=co1)
    frame_rodape.grid(row=8, column=0, pady=5, sticky=EW)
    
    # Cria o novo rodapé
    label_rodape = Label(frame_rodape, text="Criado por Tarcisio Sousa de Almeida, Técnico em Administração Escolar", 
                         font=('Ivy 10'), bg=co1, fg=co0)
    label_rodape.pack(side=LEFT, padx=10)
    
    # Indicador de backup automático
    backup_status = Label(frame_rodape, text="🔄 Backup automático: ATIVO (14:05 e 17:00 + ao fechar)", 
                         font=('Ivy 9 italic'), bg=co1, fg=co2)
    backup_status.pack(side=LEFT, padx=20)
    
    # Adiciona status_label para mensagens
    status_label = Label(frame_rodape, text="", font=('Ivy 10'), bg=co1, fg=co0)
    status_label.pack(side=RIGHT, padx=10)

def destruir_frames():
    for widget in frame_detalhes.winfo_children():
        widget.destroy()
    for widget in frame_tabela.winfo_children():
        widget.destroy()
    for widget in frame_dados.winfo_children():
        widget.destroy()
    for widget in frame_logo.winfo_children():
        widget.destroy()
        
    # Recria o rodapé para garantir que ele seja sempre exibido
    criar_rodape()

def voltar():
    # Limpar apenas os conteúdos necessários
    for widget in frame_detalhes.winfo_children():
        widget.destroy()
    for widget in frame_tabela.winfo_children():
        widget.destroy()
    
    # Recriar o logo principal
    global app_logo
    for widget in frame_logo.winfo_children():
        widget.destroy()
    
    criar_logo()
    
    # Verificar se já existe um campo de pesquisa
    pesquisa_existe = False
    for widget in frame_dados.winfo_children():
        if isinstance(widget, Frame) and widget.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, Entry):
                    # Campo de pesquisa encontrado
                    pesquisa_existe = True
                    break
    
    # Remover widgets que não são a pesquisa
    for widget in frame_dados.winfo_children():
        if isinstance(widget, Frame) and not any(isinstance(child, Entry) for child in widget.winfo_children()):
            widget.destroy()
        elif not isinstance(widget, Frame):
            widget.destroy()
    
    # Criar pesquisa apenas se não existir
    if not pesquisa_existe:
        criar_pesquisa()
    
    # Atualizar a tabela com os dados mais recentes ao invés de apenas recriar
    atualizar_tabela_principal()
    
    # Garantir que o frame_detalhes esteja limpo e com tamanho adequado
    frame_detalhes.config(height=100)
    
    # Adicionar uma mensagem de instrução no frame_detalhes
    instrucao_label = Label(frame_detalhes, text="Selecione um item na tabela para visualizar as opções disponíveis", 
                         font=('Ivy 11 italic'), bg=co1, fg=co0)
    instrucao_label.pack(pady=20)

def verificar_e_gerar_boletim(aluno_id, ano_letivo_id=None):
    """
    Verifica o status do aluno e gera o documento apropriado.
    Se o aluno estiver transferido, gera o documento de transferência,
    caso contrário, gera o boletim normal.
    
    Args:
        aluno_id: ID do aluno
        ano_letivo_id: ID opcional do ano letivo. Se não for fornecido, usará o ano letivo atual.
    """
    cursor = None
    try:
        with get_connection() as conn:
            if conn is None:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                return
            cursor = conn.cursor()

            # Se o ano_letivo_id não foi fornecido, obtém o ID do ano letivo atual
            if ano_letivo_id is None:
                cursor.execute("SELECT id FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
                resultado_ano = cursor.fetchone()

                if not resultado_ano:
                    # Se não encontrar o ano letivo atual, tenta obter o ano letivo mais recente
                    cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                    resultado_ano = cursor.fetchone()

                if not resultado_ano:
                    messagebox.showwarning("Aviso", "Não foi possível determinar o ano letivo atual.")
                    return False

                ano_letivo_id = _safe_get(resultado_ano, 0, 1)

            # Verifica o status da matrícula do aluno no ano letivo especificado
            cursor.execute("""
            SELECT m.status, a.nome, al.ano_letivo
            FROM matriculas m
            JOIN turmas t ON m.turma_id = t.id
            JOIN alunos a ON m.aluno_id = a.id
            JOIN anosletivos al ON m.ano_letivo_id = al.id
            WHERE m.aluno_id = %s 
            AND m.ano_letivo_id = %s 
            AND t.escola_id = 60
            AND m.status IN ('Ativo', 'Transferido')
            ORDER BY m.data_matricula DESC
            LIMIT 1
        """, (int(str(aluno_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1))
        
        resultado = cursor.fetchone()
        
        if not resultado:
            messagebox.showwarning("Aviso", "Não foi possível determinar o status da matrícula do aluno para o ano letivo selecionado.")
            return False
        
        status_matricula = _safe_get(resultado, 0)
        nome_aluno = _safe_get(resultado, 1)
        ano_letivo = _safe_get(resultado, 2)
        
        # Decidir qual documento gerar baseado no status
        # Gerar em background para não bloquear a UI
        def _worker():
            if status_matricula == 'Transferido':
                from transferencia import gerar_documento_transferencia
                gerar_documento_transferencia(aluno_id, ano_letivo_id)
                return True
            else:
                return boletim(aluno_id, ano_letivo_id)

        def _on_done(resultado):
            if status_matricula == 'Transferido':
                messagebox.showinfo("Aluno Transferido", 
                                    f"O aluno {nome_aluno} está com status 'Transferido' no ano letivo {ano_letivo}.\n"
                                    f"Documento de transferência gerado com sucesso.")
            else:
                if resultado:
                    if status_label is not None:
                        status_label.config(text="Boletim gerado com sucesso.")
                    messagebox.showinfo("Concluído", "Boletim gerado com sucesso.")
                else:
                    if status_label is not None:
                        status_label.config(text="")
                    messagebox.showwarning("Aviso", "Nenhum dado gerado para o boletim.")

        def _on_error(exc):
            messagebox.showerror("Erro", f"Falha ao gerar documento: {exc}")
            if status_label is not None:
                status_label.config(text="")

        try:
            from utils.executor import submit_background
            submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=janela)
        except Exception:
            def _thread_worker():
                try:
                    res = _worker()
                    try:
                        janela.after(0, lambda: _on_done(res))
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        janela.after(0, lambda: _on_error(e))
                    except Exception:
                        pass

            from threading import Thread
            Thread(target=_thread_worker, daemon=True).start()
            
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar status e gerar boletim: {str(e)}")
        logger.error(f"Erro ao verificar status e gerar boletim: {str(e)}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

def criar_menu_contextual():
    menu_contextual = Menu(janela, tearoff=0)
    menu_contextual.add_command(label="Editar", command=editar_aluno_e_destruir_frames)
    # Outros itens do menu...
    
    def mostrar_menu(event):
        try:
            menu_contextual.tk_popup(event.x_root, event.y_root)
        finally:
            menu_contextual.grab_release()
    
    treeview.bind("<Button-3>", mostrar_menu)  # Clique direito

# ============================================================================
# OTIMIZAÇÃO 4: Cache de resultados para atualização incremental
# ============================================================================
from typing import Dict, List, Any, Optional

_cache_dados_tabela: Dict[str, Any] = {
    'timestamp': None,
    'dados': None,
    'hash': None
}

# ============================================================================
# MELHORIA 1: Dashboard com Estatísticas de Alunos
# Cache para dados estatísticos do dashboard (atualização a cada 5 minutos)
# ============================================================================
_cache_estatisticas_dashboard: Dict[str, Any] = {
    'timestamp': None,
    'dados': None
}

def obter_estatisticas_alunos():
    """
    Retorna estatísticas de alunos matriculados e ativos do ano corrente.
    Usa cache de 5 minutos para melhorar performance.
    
    Returns:
        dict: {
            'total_matriculados': int,
            'total_ativos': int,
            'total_transferidos': int,
            'por_serie': [{'serie': str, 'quantidade': int, 'ativos': int}, ...]
        }
    """
    import time
    
    tempo_atual = time.time()
    
    # Verificar cache (5 minutos = 300 segundos)
    if _cache_estatisticas_dashboard['timestamp']:
        tempo_decorrido = tempo_atual - _cache_estatisticas_dashboard['timestamp']
        if tempo_decorrido < 300:  # 5 minutos
            return _cache_estatisticas_dashboard['dados']
    
    # Buscar dados atualizados usando o context manager de conexão
    try:
        with get_connection() as conn:
            if conn is None:
                return None
            cursor = conn.cursor()
            try:
                # Obter ano letivo atual do cache
                ano_letivo_id = obter_ano_letivo_atual()

                escola_id = 60  # ID fixo da escola

                # Query otimizada para obter todas as estatísticas de uma vez
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN a.id END) as total_ativos,
                        COUNT(DISTINCT CASE WHEN m.status IN ('Transferido', 'Transferida') THEN a.id END) as total_transferidos
                    FROM Alunos a
                    JOIN Matriculas m ON a.id = m.aluno_id
                    JOIN turmas t ON m.turma_id = t.id
                    WHERE m.ano_letivo_id = %s 
                    AND a.escola_id = %s
                    AND m.status IN ('Ativo', 'Transferido', 'Transferida')
                """, (ano_letivo_id, escola_id))

                resultado_geral = cursor.fetchone()
                if resultado_geral:
                    total_ativos = converter_para_int_seguro(resultado_geral[0])
                    total_transferidos = converter_para_int_seguro(resultado_geral[1])
                else:
                    total_ativos = 0
                    total_transferidos = 0
                # garantir inteiros válidos
                try:
                    total_ativos = int(total_ativos)
                except Exception:
                    total_ativos = 0
                try:
                    total_transferidos = int(total_transferidos)
                except Exception:
                    total_transferidos = 0
                total_matriculados = total_ativos + total_transferidos

                # Estatísticas por série E TURMA - conta ALUNOS ÚNICOS e ATIVOS
                cursor.execute("""
                    SELECT 
                        CONCAT(s.nome, ' ', t.nome) as serie_turma,
                        COUNT(DISTINCT a.id) as quantidade,
                        COUNT(DISTINCT CASE WHEN m.status = 'Ativo' THEN a.id END) as ativos
                    FROM Alunos a
                    JOIN Matriculas m ON a.id = m.aluno_id
                    JOIN turmas t ON m.turma_id = t.id
                    JOIN serie s ON t.serie_id = s.id
                    WHERE m.ano_letivo_id = %s 
                    AND a.escola_id = %s
                    AND m.status = 'Ativo'
                    GROUP BY t.id, s.nome, t.nome
                    ORDER BY s.nome, t.nome
                """, (ano_letivo_id, escola_id))

                por_serie = []
                for row in cursor.fetchall():
                    try:
                        quantidade = converter_para_int_seguro(row[1])
                        ativos = converter_para_int_seguro(row[2])
                    except Exception:
                        quantidade = 0
                        ativos = 0
                    por_serie.append({
                        'serie': row[0],
                        'quantidade': quantidade,
                        'ativos': ativos
                    })

                # Montar resultado
                dados = {
                    'total_matriculados': total_matriculados,
                    'total_ativos': total_ativos,
                    'total_transferidos': total_transferidos,
                    'por_serie': por_serie
                }

                # Atualizar cache
                _cache_estatisticas_dashboard['dados'] = dados
                _cache_estatisticas_dashboard['timestamp'] = tempo_atual

                return dados
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return None


# Instanciar o DashboardManager se possível (injeta dependências necessárias)
try:
    from ui.dashboard import DashboardManager
    from services.db_service import DbService
    frame_getter = lambda: globals().get('frame_tabela')
    db_service = DbService(get_connection)
    dashboard_manager = DashboardManager(janela, db_service, obter_estatisticas_alunos, frame_getter, _cache_estatisticas_dashboard, co_bg=co1, co_fg=co0, co_accent=co4)
except Exception:
    dashboard_manager = None

def atualizar_tabela_principal(forcar_atualizacao=False):
    """
    Atualiza a tabela principal com os dados mais recentes do banco de dados.
    Útil para refletir alterações como novos cadastros, edições ou exclusões.
    
    Args:
        forcar_atualizacao (bool): Se True, ignora o cache e força a atualização
    """
    try:
        # Verificar se temos uma treeview válida antes de tentar atualizar
        if 'treeview' not in globals() or not treeview.winfo_exists():
            logger.warning("Treeview não existe, não é possível atualizar")
            return False
        
        # Verificar cache (evita recargas desnecessárias)
        import time
        import hashlib
        
        tempo_atual = time.time()
        
        # Se a última atualização foi há menos de 2 segundos, não atualizar
        if not forcar_atualizacao and _cache_dados_tabela['timestamp']:
            tempo_decorrido = tempo_atual - _cache_dados_tabela['timestamp']
            if tempo_decorrido < 2.0:
                logger.debug(f"Cache ainda válido ({tempo_decorrido:.1f}s), pulando atualização")
                return True
            
        # Conectar ao banco de dados
        cursor = None
        with get_connection() as conn:
                if conn is None:
                    messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                    return False
                cursor = conn.cursor()

                # Executar a consulta otimizada para obter dados atualizados
                # Se a variável global 'query' não estiver definida, não atualizar
                if 'query' not in globals() or not globals().get('query'):
                    logger.warning("Variável 'query' não definida; pulando atualização de tabela")
                    return False
                # Usar a variável global `query` via globals() e assegurar ao verificador de tipos
                # que se trata de uma string (cast) — já garantimos acima que 'query' existe e é truthy.
                _q = globals().get('query')
                cursor.execute(cast(str, _q))

                # Atualizar a variável global de resultados
                global resultados
                novos_resultados = cursor.fetchall()

                # Calcular hash dos novos dados para verificar mudanças
                dados_str = str(novos_resultados)
                novo_hash = hashlib.md5(dados_str.encode()).hexdigest()

                # Se os dados não mudaram, não precisa atualizar a interface
                if not forcar_atualizacao and _cache_dados_tabela['hash'] == novo_hash:
                    logger.debug("Dados não mudaram, mantendo interface atual")
                    _cache_dados_tabela['timestamp'] = tempo_atual
                    return True

                # Dados mudaram, atualizar cache
                _cache_dados_tabela['dados'] = novos_resultados
                _cache_dados_tabela['hash'] = novo_hash
                _cache_dados_tabela['timestamp'] = tempo_atual

                resultados = novos_resultados
            
        # Limpar tabela atual usando try/except para cada operação crítica
        try:
            # Verificar se tem itens antes de tentar limpar
            if treeview.get_children():
                for item in treeview.get_children():
                    treeview.delete(item)
        except TclError as tcl_e:
            logger.error(f"Erro ao limpar treeview: {str(tcl_e)}")
            raise  # Relançar para ser tratado pelo bloco de exceção principal
            
        # Inserir os novos dados
        try:
            for resultado in resultados:
                resultado = list(resultado)
                if resultado[4]:
                    try:
                        if isinstance(resultado[4], str):
                            data = datetime.strptime(resultado[4], '%Y-%m-%d')
                        else:
                            data = resultado[4]
                        if isinstance(data, (datetime, date)):
                            resultado[4] = data.strftime('%d/%m/%Y')
                    except Exception:
                        pass
                treeview.insert("", "end", values=resultado)
        except TclError as tcl_e:
            logger.error(f"Erro ao inserir dados na treeview: {str(tcl_e)}")
            raise  # Relançar para ser tratado pelo bloco de exceção principal
            
        # Fechar cursor (a conexão é fechada pelo context manager)
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        
        logger.info("Tabela atualizada com sucesso!")
        return True
        
    except TclError as e:
        # Tratamento específico para erros do Tkinter
        logger.error(f"Erro do Tkinter ao atualizar tabela: {str(e)}")
        
        # Fechar conexões primeiro
        if 'cursor' in locals() and cursor:
            cursor.close()
            
        # Não tentar recriar a interface, apenas registrar o erro
        return False
    
    except Exception as e:
        logger.error(f"Erro ao atualizar tabela: {str(e)}")
        # Não mostrar messagebox para evitar loops de erro
        
        # Garantir que a conexão seja fechada mesmo em caso de erro
        if 'cursor' in locals() and cursor:
            cursor.close()
        
        return False

def editar_funcionario_e_destruir_frames():
    # Obter o ID do funcionário selecionado na tabela
    try:
        item_selecionado = treeview.focus()
        valores = treeview.item(item_selecionado, "values")
        
        if not valores:
            messagebox.showwarning("Aviso", "Selecione um funcionário para editar")
            return
        
        funcionario_id = valores[0]  # Assumindo que o ID é o primeiro valor
        
        # Abrir a interface de edição em uma nova janela
        janela_edicao = Toplevel(janela)
        from InterfaceEdicaoFuncionario import InterfaceEdicaoFuncionario
        
        # Configurar a janela de edição antes de criar a interface
        janela_edicao.title(f"Editar Funcionário - ID: {funcionario_id}")
        janela_edicao.geometry('950x670')
        janela_edicao.configure(background=co1)
        janela_edicao.focus_set()  # Dar foco à nova janela
        
        # Criar a interface de edição após configurar a janela
        # A classe InterfaceEdicaoFuncionario já gerencia o fechamento e atualização
        app_edicao = InterfaceEdicaoFuncionario(janela_edicao, funcionario_id, janela_principal=janela)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir interface de edição: {str(e)}")
        logger.error(f"Erro ao abrir interface de edição: {str(e)}")
        # Se ocorrer erro, garantir que a janela principal esteja visível
        if janela.winfo_viewable() == 0:
            janela.deiconify()

def selecionar_ano_para_boletim(aluno_id):
    """
    Exibe uma janela com um menu suspenso para o usuário selecionar o ano letivo antes de gerar o boletim.
    
    Args:
        aluno_id: ID do aluno
    """
    # Obter informações do aluno e anos letivos dentro do contexto de conexão
    cursor = None
    try:
        with get_connection() as conn:
            if conn is None:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                return
            cursor = conn.cursor()

            # Obter nome do aluno
            cursor.execute("SELECT nome FROM alunos WHERE id = %s", (aluno_id,))
            resultado_nome = cursor.fetchone()
            if resultado_nome is None:
                messagebox.showerror("Erro", "Aluno não encontrado.")
                return
            nome_aluno = resultado_nome[0]

            # Obter anos letivos nos quais o aluno teve matrícula
            tem_historico, anos_letivos = verificar_historico_matriculas(aluno_id)

            if not tem_historico or not anos_letivos:
                messagebox.showwarning("Aviso", "Não foram encontradas matrículas para este aluno.")
                return

            # Preparar janela de seleção (a interface não depende de manter a conexão aberta)
            janela_selecao = Toplevel(janela)
            janela_selecao.title(f"Selecionar Ano Letivo - {nome_aluno}")
            janela_selecao.geometry("400x300")
            janela_selecao.configure(background=co1)
            janela_selecao.transient(janela)
            janela_selecao.focus_force()
            janela_selecao.grab_set()
        
        # Frame principal
        frame_selecao = Frame(janela_selecao, bg=co1, padx=20, pady=20)
        frame_selecao.pack(fill=BOTH, expand=True)
        
        # Título
        titulo = Label(frame_selecao, text=f"Selecionar Ano Letivo para Boletim", 
                     font=("Arial", 14, "bold"), bg=co1, fg=co0)
        titulo.pack(pady=(0, 20))
        
        # Informações do aluno
        Label(frame_selecao, text=f"Aluno: {nome_aluno}", 
             font=("Arial", 12), bg=co1, fg=co0).pack(anchor=W, pady=5)
        
        # Criar dicionário para mapear anos letivos e status
        anos_info = {}
        for ano_info in anos_letivos:
            ano_letivo, ano_letivo_id = ano_info
            
            # Obter o status da matrícula para este ano letivo
            cursor.execute("""
                SELECT m.status
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                WHERE m.aluno_id = %s 
                AND m.ano_letivo_id = %s 
                ORDER BY m.data_matricula DESC
                LIMIT 1
            """, (int(str(aluno_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1))
            
            status_result = cursor.fetchone()
            status = status_result[0] if status_result else "Desconhecido"
            
            # Armazenar informações no dicionário
            anos_info[f"{ano_letivo} - {status}"] = (ano_letivo_id, status)
        
        # Frame para o combobox
        combo_frame = Frame(frame_selecao, bg=co1)
        combo_frame.pack(fill=X, pady=15)
        
        Label(combo_frame, text="Selecione o ano letivo:", 
             font=("Arial", 11), bg=co1, fg=co0).pack(anchor=W, pady=(0, 5))
        
        # Criar variável para armazenar a seleção
        selected_ano = StringVar()
        
        # Lista de anos para mostrar no combobox
        anos_display = list(anos_info.keys())
        
        # Configurar o combobox
        combo_anos = ttk.Combobox(combo_frame, textvariable=selected_ano, values=anos_display,
                                font=("Arial", 11), state="readonly", width=30)
        combo_anos.pack(fill=X, pady=5)
        
        # Selecionar o primeiro item por padrão
        if anos_display:
            combo_anos.current(0)
        
        # Frame para informações (mostrar status da matrícula selecionada)
        info_frame = Frame(frame_selecao, bg=co1)
        info_frame.pack(fill=X, pady=10)
        
        status_label = Label(info_frame, text="", font=("Arial", 11), bg=co1, fg=co0)
        status_label.pack(anchor=W, pady=5)
        
        # Atualizar informações quando o usuário selecionar um ano letivo
        def atualizar_info(*args):
            selected = selected_ano.get()
            if selected in anos_info:
                _, status = anos_info[selected]
                if status == "Transferido":
                    status_label.config(text=f"Observação: Aluno transferido no ano letivo selecionado")
                else:
                    status_label.config(text="")
        
        # Vincular função ao evento de seleção
        selected_ano.trace_add("write", atualizar_info)
        
        # Chamar função uma vez para configuração inicial
        atualizar_info()
        
        # Frame para botões
        botoes_frame = Frame(frame_selecao, bg=co1)
        botoes_frame.pack(fill=X, pady=15)
        
        # Função para gerar o boletim com o ano letivo selecionado
        def gerar_boletim_selecionado():
            selected = selected_ano.get()
            if not selected or selected not in anos_info:
                messagebox.showwarning("Aviso", "Por favor, selecione um ano letivo válido.")
                return
            
            ano_letivo_id, status = anos_info[selected]
            
            # Fechar a janela de seleção
            janela_selecao.destroy()
            
            # Decidir qual tipo de documento gerar com base no status
            # Gerar em background para não bloquear a UI
            def _worker():
                if status == 'Transferido':
                    ano_letivo = selected.split(' - ')[0]
                    # Nota: comunicação ao usuário será feita no on_done
                    from transferencia import gerar_documento_transferencia
                    gerar_documento_transferencia(aluno_id, ano_letivo_id)
                    return True
                else:
                    return boletim(aluno_id, ano_letivo_id)

            def _on_done(resultado):
                if status == 'Transferido':
                    messagebox.showinfo("Aluno Transferido", 
                                        f"O aluno {nome_aluno} teve status 'Transferido' no ano {selected.split(' - ')[0]}.\n"
                                        f"Documento de transferência gerado com sucesso.")
                else:
                    if resultado:
                        if status_label is not None:
                            status_label.config(text="Boletim gerado com sucesso.")
                        messagebox.showinfo("Concluído", "Boletim gerado com sucesso.")
                    else:
                        if status_label is not None:
                            status_label.config(text="")
                        messagebox.showwarning("Aviso", "Nenhum dado gerado para o boletim.")

            def _on_error(exc):
                messagebox.showerror("Erro", f"Falha ao gerar documento: {exc}")
                if status_label is not None:
                    status_label.config(text="")

            try:
                from utils.executor import submit_background
                submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=janela)
            except Exception:
                # Fallback: executar em Thread e agendar callbacks via `janela.after`
                def _thread_worker():
                    try:
                        res = _worker()
                        try:
                            janela.after(0, lambda: _on_done(res))
                        except Exception:
                            pass
                    except Exception as e:
                        try:
                            janela.after(0, lambda: _on_error(e))
                        except Exception:
                            pass

                from threading import Thread
                Thread(target=_thread_worker, daemon=True).start()
        
        # Botões
        Button(botoes_frame, text="Gerar Boletim", command=gerar_boletim_selecionado,
              font=('Ivy 10 bold'), bg=co6, fg=co7, width=15).pack(side=LEFT, padx=5)
        
        Button(botoes_frame, text="Cancelar", command=janela_selecao.destroy,
              font=('Ivy 10'), bg=co8, fg=co0, width=15).pack(side=RIGHT, padx=5)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao preparar seleção de ano letivo: {str(e)}")
        logger.error(f"Erro ao preparar seleção de ano letivo: {str(e)}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

def criar_menu_boletim(parent_frame, aluno_id, tem_matricula_ativa):
    """
    Cria um menu suspenso (Combobox) para seleção do ano letivo diretamente na interface principal.
    
    Args:
        parent_frame: Frame onde o menu será adicionado
        aluno_id: ID do aluno
        tem_matricula_ativa: Flag que indica se o aluno tem matrícula ativa
    """
    # Obter anos letivos nos quais o aluno teve matrícula
    tem_historico, anos_letivos = verificar_historico_matriculas(aluno_id)
    
    if not tem_historico or not anos_letivos:
        # Se não tem histórico, simplesmente adicionar um botão desabilitado
        Button(parent_frame, text="Boletim", state=DISABLED,
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co6, fg=co7).grid(row=0, column=3, padx=5, pady=5)
        return
    
    # Criar frame para conter o botão e o combobox
    boletim_frame = Frame(parent_frame, bg=co1)
    boletim_frame.grid(row=0, column=3, padx=5, pady=5)
    
    # Criar dicionário para mapear anos letivos e status
    anos_info = {}
    
    cursor = None
    try:
        with get_connection() as conn:
            if conn is None:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                return
            cursor = conn.cursor()

            for ano_letivo, ano_letivo_id in anos_letivos:
                # Obter o status da matrícula para este ano letivo
                cursor.execute("""
                    SELECT m.status
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    WHERE m.aluno_id = %s 
                    AND m.ano_letivo_id = %s 
                    ORDER BY m.data_matricula DESC
                    LIMIT 1
                """, (int(str(aluno_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1))

                status_result = cursor.fetchone()
                status = status_result[0] if status_result else "Desconhecido"

                # Armazenar informações no dicionário
                anos_info[f"{ano_letivo} - {status}"] = (ano_letivo_id, status)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao obter informações de anos letivos: {str(e)}")
        logger.error(f"Erro ao obter informações de anos letivos: {str(e)}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
    
    # Lista de anos para mostrar no combobox
    anos_display = list(anos_info.keys())
    
    # Criar variável para armazenar a seleção
    selected_ano = StringVar()
    
    # Label para o botão
    Label(boletim_frame, text="Boletim:", font=('Ivy 9'), bg=co1, fg=co0).pack(side=LEFT, padx=(0, 5))
    
    # Configurar o combobox
    combo_anos = ttk.Combobox(boletim_frame, textvariable=selected_ano, values=anos_display,
                            font=('Ivy 9'), state="readonly", width=15)
    combo_anos.pack(side=LEFT)
    
    # Selecionar o primeiro item por padrão
    if anos_display:
        combo_anos.current(0)
    
    # Função para gerar o boletim quando um ano letivo for selecionado
    def gerar_boletim_selecionado(event=None):
        selected = selected_ano.get()
        if not selected or selected not in anos_info:
            messagebox.showwarning("Aviso", "Por favor, selecione um ano letivo válido.")
            return
        
        ano_letivo_id, status = anos_info[selected]
        
        # Decidir qual tipo de documento gerar com base no status
        # Gerar em background para não bloquear a UI
        def _worker():
            if status == 'Transferido':
                from transferencia import gerar_documento_transferencia
                gerar_documento_transferencia(aluno_id, ano_letivo_id)
                return True
            else:
                return boletim(aluno_id, ano_letivo_id)

        def _on_done(resultado):
            if status == 'Transferido':
                messagebox.showinfo("Aluno Transferido", 
                                    f"O aluno teve status 'Transferido' no ano {selected.split(' - ')[0]}.\n"
                                    f"Documento de transferência gerado com sucesso.")
            else:
                if resultado:
                    if status_label is not None:
                        status_label.config(text="Boletim gerado com sucesso.")
                    messagebox.showinfo("Concluído", "Boletim gerado com sucesso.")
                else:
                    if status_label is not None:
                        status_label.config(text="")
                    messagebox.showwarning("Aviso", "Nenhum dado gerado para o boletim.")

        def _on_error(exc):
            messagebox.showerror("Erro", f"Falha ao gerar documento: {exc}")
            if status_label is not None:
                status_label.config(text="")

        try:
            from utils.executor import submit_background
            submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=janela)
        except Exception:
            def _thread_worker():
                try:
                    res = _worker()
                    try:
                        janela.after(0, lambda: _on_done(res))
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        janela.after(0, lambda: _on_error(e))
                    except Exception:
                        pass

            from threading import Thread
            Thread(target=_thread_worker, daemon=True).start()
    
    # Vincular a função ao evento de seleção no combobox
    combo_anos.bind("<<ComboboxSelected>>", gerar_boletim_selecionado)
    
    # Adicionar um botão de gerar para melhor usabilidade
    Button(boletim_frame, text="Gerar", command=gerar_boletim_selecionado,
           font=('Ivy 9'), bg=co6, fg=co7, width=5).pack(side=LEFT, padx=(5, 0))

def editar_matricula(aluno_id):
    """
    Abre uma janela para editar a matrícula do aluno.
    
    Args:
        aluno_id: ID do aluno a ser editado
    """
    # Inicializa variáveis que serão usadas pela UI
    try:
        # Buscar informações iniciais em conexão curta
        with get_connection() as conn_init:
            if conn_init is None:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                return
            cur_init = conn_init.cursor()
            cur_init.execute("SELECT nome FROM alunos WHERE id = %s", (aluno_id,))
            resultado_nome = cur_init.fetchone()
            if not resultado_nome:
                messagebox.showerror("Erro", "Aluno não encontrado.")
                try:
                    cur_init.close()
                except Exception:
                    pass
                return
            nome_aluno = resultado_nome[0]

            # Obter ano letivo atual ou mais recente
            cur_init.execute("SELECT id, ano_letivo FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
            resultado_ano = cur_init.fetchone()
            if not resultado_ano:
                cur_init.execute("SELECT id, ano_letivo FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado_ano = cur_init.fetchone()
            if not resultado_ano:
                try:
                    cur_init.close()
                except Exception:
                    pass
                messagebox.showwarning("Aviso", "Não foi possível determinar o ano letivo atual.")
                return
            ano_letivo_id, ano_letivo = resultado_ano

            # Obter matrícula mais recente do aluno para o ano letivo (independente do status)
            cur_init.execute("""
                SELECT m.id, m.turma_id, m.status, t.nome as turma_nome, s.nome as serie_nome, s.id as serie_id
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN serie s ON t.serie_id = s.id
                WHERE m.aluno_id = %s AND m.ano_letivo_id = %s
                ORDER BY m.data_matricula DESC, m.id DESC
                LIMIT 1
            """, (int(str(aluno_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1))
            resultado_matricula = cur_init.fetchone()
            try:
                cur_init.close()
            except Exception:
                pass

        if not resultado_matricula:
            messagebox.showwarning("Aviso", "Não foi encontrada matrícula para este aluno no ano letivo atual.")
            return

        matricula_id, turma_id_atual, status_atual, turma_nome_atual, serie_nome_atual, serie_id_atual = resultado_matricula

        # Cria a janela de edição de matrícula
        janela_matricula = Toplevel(janela)
        janela_matricula.title(f"Editar Matrícula - {nome_aluno}")
        janela_matricula.geometry("500x600")
        janela_matricula.configure(background=co1)
        janela_matricula.transient(janela)
        janela_matricula.focus_force()
        janela_matricula.grab_set()

        # Frame principal
        frame_matricula = Frame(janela_matricula, bg=co1, padx=20, pady=20)
        frame_matricula.pack(fill=BOTH, expand=True)

        # Título e informações iniciais
        Label(frame_matricula, text=f"Edição de Matrícula", font=("Arial", 14, "bold"), bg=co1, fg=co7).pack(pady=(0, 20))
        info_frame = Frame(frame_matricula, bg=co1)
        info_frame.pack(fill=X, pady=10)
        Label(info_frame, text=f"Aluno: {nome_aluno}", font=("Arial", 12), bg=co1, fg=co4).pack(anchor=W)
        Label(info_frame, text=f"Ano Letivo: {ano_letivo}", font=("Arial", 12), bg=co1, fg=co4).pack(anchor=W)
        Label(info_frame, text=f"Status Atual: {status_atual}", font=("Arial", 12), bg=co1, fg=co4).pack(anchor=W)

        # Séries / Turmas / Status UI
        serie_frame = Frame(frame_matricula, bg=co1)
        serie_frame.pack(fill=X, pady=10)
        Label(serie_frame, text="Série:", bg=co1, fg=co4).pack(anchor=W, pady=(5, 0))
        serie_var = StringVar()
        cb_serie = ttk.Combobox(serie_frame, textvariable=serie_var, width=40)
        cb_serie.pack(fill=X, pady=(0, 5))

        turma_frame = Frame(frame_matricula, bg=co1)
        turma_frame.pack(fill=X, pady=10)
        Label(turma_frame, text="Turma:", bg=co1, fg=co4).pack(anchor=W, pady=(5, 0))
        turma_var = StringVar()
        cb_turma = ttk.Combobox(turma_frame, textvariable=turma_var, width=40)
        cb_turma.pack(fill=X, pady=(0, 5))

        status_frame = Frame(frame_matricula, bg=co1)
        status_frame.pack(fill=X, pady=10)
        Label(status_frame, text="Novo Status:", bg=co1, fg=co4).pack(anchor=W, pady=(5, 0))
        status_var = StringVar()
        status_opcoes = ['Ativo', 'Evadido', 'Cancelado', 'Transferido', 'Concluído']
        cb_status = ttk.Combobox(status_frame, textvariable=status_var, values=status_opcoes, width=40)
        cb_status.pack(fill=X, pady=(0, 5))
        status_var.set(str(status_atual) if status_atual is not None else "")

        # Data da mudança de status
        data_frame = Frame(frame_matricula, bg=co1)
        data_frame.pack(fill=X, pady=10)
        Label(data_frame, text="Data da Mudança de Status (dd/mm/aaaa):", bg=co1, fg=co4).pack(anchor=W, pady=(5, 0))
        data_mudanca_var = StringVar()
        from datetime import datetime
        data_mudanca_var.set(datetime.now().strftime('%d/%m/%Y'))
        entry_data_mudanca = Entry(data_frame, textvariable=data_mudanca_var, width=42, font=("Arial", 10))
        entry_data_mudanca.pack(fill=X, pady=(0, 5))

        series_map = {}
        turmas_map = {}

        # Função para carregar séries (usa conexão curta)
        def carregar_series():
            nonlocal series_map, turmas_map
            try:
                with get_connection() as conn:
                    if conn is None:
                        messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                        return
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT DISTINCT s.id, s.nome 
                        FROM serie s
                        JOIN turmas t ON s.id = t.serie_id
                        WHERE t.escola_id = 60
                        AND t.ano_letivo_id = %s
                        ORDER BY s.nome
                    """, (int(str(ano_letivo_id)) if ano_letivo_id is not None else 1,))
                    series = cur.fetchall()
                    try:
                        cur.close()
                    except Exception:
                        pass

                if not series:
                    messagebox.showwarning("Aviso", "Não foram encontradas séries para a escola selecionada no ano letivo atual.")
                    return

                series_map.clear()
                for serie in series:
                    series_map[serie[1]] = serie[0]
                cb_serie['values'] = list(series_map.keys())

                # Selecionar a série atual do aluno
                if serie_nome_atual in series_map:
                    serie_var.set(str(serie_nome_atual) if serie_nome_atual is not None else "")
                    carregar_turmas()
                elif len(series_map) == 1:
                    serie_nome = list(series_map.keys())[0]
                    cb_serie.set(serie_nome)
                    carregar_turmas()

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar séries: {str(e)}")

        # Função para carregar turmas com base na série selecionada (usa conexão curta)
        def carregar_turmas(event=None):
            nonlocal turmas_map
            serie_nome = serie_var.get()
            if not serie_nome:
                return
            if serie_nome not in series_map:
                return
            serie_id = series_map[serie_nome]
            try:
                with get_connection() as conn:
                    if conn is None:
                        messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                        return
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT id, nome, serie_id
                        FROM turmas 
                        WHERE serie_id = %s AND escola_id = 60 AND ano_letivo_id = %s
                        ORDER BY nome
                    """, (int(str(serie_id)), int(str(ano_letivo_id)) if ano_letivo_id is not None else 1))
                    turmas = cur.fetchall()
                    try:
                        cur.close()
                    except Exception:
                        pass

                if not turmas:
                    messagebox.showwarning("Aviso", f"Não foram encontradas turmas para a série {serie_nome}.")
                    return

                turmas_map.clear()
                for turma in turmas:
                    turma_id, turma_nome, turma_serie_id = turma
                    if not turma_nome or str(turma_nome).strip() == "":
                        turma_nome = f"Turma {turma_id}" if len(turmas) > 1 else "Turma Única"
                    turmas_map[turma_nome] = turma_id

                turmas_nomes = list(turmas_map.keys())
                cb_turma['values'] = turmas_nomes

                if serie_id == serie_id_atual and turma_nome_atual in turmas_map:
                    turma_var.set(str(turma_nome_atual) if turma_nome_atual is not None else "")
                elif len(turmas_map) == 1:
                    cb_turma.set(turmas_nomes[0])
                else:
                    cb_turma.set("")

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar turmas: {str(e)}")

        cb_serie.bind("<<ComboboxSelected>>", carregar_turmas)

        # Função para salvar a edição da matrícula (usa conexão curta com commit)
        def salvar_edicao_matricula():
            serie_nome = serie_var.get()
            turma_nome = turma_var.get()
            novo_status = status_var.get()
            data_str = data_mudanca_var.get()

            if not serie_nome or serie_nome not in series_map:
                messagebox.showwarning("Aviso", "Por favor, selecione uma série válida.")
                return
            if not turma_nome or turma_nome not in turmas_map:
                messagebox.showwarning("Aviso", f"Por favor, selecione uma turma válida. Valor atual: '{turma_nome}'")
                return
            if not novo_status:
                messagebox.showwarning("Aviso", "Por favor, selecione um status válido.")
                return

            try:
                from datetime import datetime
                data_obj = datetime.strptime(data_str, '%d/%m/%Y')
                data_formatada = data_obj.strftime('%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Erro", "Data inválida! Use o formato dd/mm/aaaa (exemplo: 28/10/2025)")
                return

            turma_id = turmas_map[turma_nome]

            try:
                with get_connection() as conn:
                    if conn is None:
                        messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                        return
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT id FROM historico_matricula 
                        WHERE matricula_id = %s 
                        AND status_anterior = %s 
                        AND status_novo = %s
                        ORDER BY id DESC
                        LIMIT 1
                    """, (int(str(matricula_id)) if matricula_id is not None else 0, str(status_atual) if status_atual is not None else '', novo_status))
                    historico_existente = cur.fetchone()

                    if historico_existente:
                        cur.execute("""
                            UPDATE historico_matricula 
                            SET data_mudanca = %s
                            WHERE id = %s
                        """, (data_formatada, int(str(historico_existente[0])) if historico_existente and historico_existente[0] is not None else 0))
                    else:
                        cur.execute("""
                            INSERT INTO historico_matricula (matricula_id, status_anterior, status_novo, data_mudanca)
                            VALUES (%s, %s, %s, %s)
                        """, (int(str(matricula_id)) if matricula_id is not None else 0, str(status_atual) if status_atual is not None else '', novo_status, data_formatada))

                    if turma_id != turma_id_atual:
                        cur.execute("""
                            UPDATE matriculas 
                            SET turma_id = %s, status = %s
                            WHERE id = %s
                        """, (int(str(turma_id)), novo_status, int(str(matricula_id)) if matricula_id is not None else 0))
                    else:
                        cur.execute("""
                            UPDATE matriculas 
                            SET status = %s
                            WHERE id = %s
                        """, (novo_status, int(str(matricula_id)) if matricula_id is not None else 0))

                    try:
                        conn.commit()
                    except Exception:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                    try:
                        cur.close()
                    except Exception:
                        pass

                messagebox.showinfo("Sucesso", f"Matrícula do aluno {nome_aluno} atualizada com sucesso!")
                janela_matricula.destroy()
                criar_botoes_frame_detalhes("Aluno", [aluno_id, nome_aluno, "Aluno", None, None])

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar matrícula: {str(e)}")

        def ao_fechar_janela():
            try:
                janela_matricula.destroy()
            except Exception:
                pass

        # Botões
        botoes_frame = Frame(frame_matricula, bg=co1)
        botoes_frame.pack(fill=X, pady=20)
        Button(botoes_frame, text="Salvar", command=salvar_edicao_matricula,
              font=('Ivy 10 bold'), width=10, bg=co3, fg=co0, overrelief=RIDGE).pack(side=LEFT, padx=10)
        Button(botoes_frame, text="Cancelar", command=ao_fechar_janela,
              font=('Ivy 10'), width=10, bg=co8, fg=co0, overrelief=RIDGE).pack(side=LEFT, padx=10)

        # Carregar séries ao iniciar
        carregar_series()

        # Callback de fechamento
        janela_matricula.protocol("WM_DELETE_WINDOW", ao_fechar_janela)

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir edição de matrícula: {str(e)}")
        logger.error(f"Erro detalhado: {str(e)}")

def selecionar_mes_movimento():
    # Criar uma nova janela
    janela_mes = Toplevel()
    janela_mes.title("Selecionar Mês")
    janela_mes.geometry("300x200")
    janela_mes.configure(background=co1)
    janela_mes.resizable(False, False)
    
    # Centralizar a janela
    janela_mes.transient(janela)
    janela_mes.grab_set()
    
    # Frame para o conteúdo
    frame_mes = Frame(janela_mes, bg=co1)
    frame_mes.pack(expand=True, fill=BOTH, padx=20, pady=20)
    
    # Label de instrução
    Label(frame_mes, text="Selecione o mês para o relatório:", 
          font=('Ivy', 12), bg=co1, fg=co0).pack(pady=10)
    
    # Lista de meses (gerada a partir do utilitário centralizado)
    try:
        meses = [nome_mes_pt_folha(i) for i in range(1, 13)]
    except Exception:
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
    
    # Obter mês atual
    mes_atual = datetime.now().month
    
    # Filtrar apenas os meses até o atual
    meses_disponiveis = meses[:mes_atual]
    
    # Variável para armazenar a seleção
    mes_selecionado = StringVar(value=meses[mes_atual - 1])
    
    # Criar combobox com os meses disponíveis
    combo_mes = ttk.Combobox(frame_mes, values=meses_disponiveis, 
                            textvariable=mes_selecionado,
                            state="readonly",
                            font=('Ivy', 12))
    combo_mes.current(mes_atual - 1)  # -1 porque o índice começa em 0
    combo_mes.pack(pady=10)
    
    def confirmar():
        # Converter o nome do mês para seu número correspondente
        nome_mes = mes_selecionado.get()
        numero_mes = meses.index(nome_mes) + 1  # +1 porque o índice começa em 0
        janela_mes.destroy()
        relatorio_movimentacao_mensal(numero_mes)
    
    def cancelar():
        janela_mes.destroy()
    
    # Frame para os botões
    frame_botoes = Frame(frame_mes, bg=co1)
    frame_botoes.pack(pady=20)
    
    # Botões
    Button(frame_botoes, text="Confirmar", command=confirmar,
           font=('Ivy', 10), bg=co2, fg=co0, width=10).pack(side=LEFT, padx=5)
    Button(frame_botoes, text="Cancelar", command=cancelar,
           font=('Ivy', 10), bg=co8, fg=co0, width=10).pack(side=LEFT, padx=5)

def relatorio():
    # Criar menu de meses
    menu_meses = Menu(janela, tearoff=0)
    
    # Obter mês atual
    mes_atual = datetime.now().month
    
    # Lista de meses (gerada a partir do utilitário centralizado)
    try:
        meses = [nome_mes_pt_folha(i) for i in range(1, 13)]
    except Exception:
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
    
    # Filtrar apenas os meses até o atual
    meses_disponiveis = meses[:mes_atual]
    
    # Adicionar meses ao menu
    for i, mes in enumerate(meses_disponiveis, 1):
        menu_meses.add_command(
            label=mes,
            command=lambda m=i: relatorio_movimentacao_mensal(m)
        )
    
    # Mostrar o menu na posição do mouse
    try:
        x = janela.winfo_pointerx()
        y = janela.winfo_pointery()
        menu_meses.post(x, y)
    except:
        # Se não conseguir obter a posição do mouse, mostrar no centro da janela
        menu_meses.post(janela.winfo_rootx() + 100, janela.winfo_rooty() + 100)

def abrir_relatorio_avancado_com_assinatura():
    # Criar janela para configuração de relatório avançado
    janela_relatorio = Toplevel(janela)
    janela_relatorio.title("Relatório de Notas com Assinatura - Opções Avançadas")
    janela_relatorio.geometry("550x350")
    janela_relatorio.resizable(False, False)
    janela_relatorio.transient(janela)  # Torna a janela dependente da principal
    janela_relatorio.grab_set()  # Torna a janela modal
    
    # Variáveis para armazenar as opções
    bimestre_var = StringVar(value="1º bimestre")
    nivel_var = StringVar(value="iniciais")
    ano_letivo_var = IntVar(value=2025)
    status_var = StringVar(value="Ativo")
    incluir_transferidos = BooleanVar(value=False)
    preencher_zeros = BooleanVar(value=False)
    
    # Frame principal
    frame_principal = Frame(janela_relatorio, padx=20, pady=20)
    frame_principal.pack(fill=BOTH, expand=True)
    
    # Título
    Label(frame_principal, text="Configurar Relatório de Notas com Assinatura", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=W)
    
    # Bimestre
    Label(frame_principal, text="Bimestre:", anchor=W).grid(row=1, column=0, sticky=W, pady=5)
    bimestres = ["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
    combo_bimestre = ttk.Combobox(frame_principal, textvariable=bimestre_var, values=bimestres, state="readonly", width=20)
    combo_bimestre.grid(row=1, column=1, sticky=W, pady=5)
    
    # Nível de ensino
    Label(frame_principal, text="Nível de ensino:", anchor=W).grid(row=2, column=0, sticky=W, pady=5)
    frame_nivel = Frame(frame_principal)
    frame_nivel.grid(row=2, column=1, sticky=W, pady=5)
    Radiobutton(frame_nivel, text="Séries iniciais (1º ao 5º)", variable=nivel_var, value="iniciais").pack(anchor=W)
    Radiobutton(frame_nivel, text="Séries finais (6º ao 9º)", variable=nivel_var, value="finais").pack(anchor=W)
    
    # Ano letivo
    Label(frame_principal, text="Ano letivo:", anchor=W).grid(row=3, column=0, sticky=W, pady=5)
    anos = ["2023", "2024", "2025", "2026", "2027"]
    combo_ano = ttk.Combobox(frame_principal, textvariable=ano_letivo_var, values=anos, state="readonly", width=20)
    combo_ano.grid(row=3, column=1, sticky=W, pady=5)
    
    # Status de matrícula
    Label(frame_principal, text="Status de matrícula:", anchor=W).grid(row=4, column=0, sticky=W, pady=5)
    frame_status = Frame(frame_principal)
    frame_status.grid(row=4, column=1, sticky=W, pady=5)
    Radiobutton(frame_status, text="Apenas ativos", variable=status_var, value="Ativo").pack(anchor=W)
    Checkbutton(frame_status, text="Incluir transferidos", variable=incluir_transferidos).pack(anchor=W)
    
    # Opções de exibição
    Label(frame_principal, text="Opções de exibição:", anchor=W).grid(row=5, column=0, sticky=W, pady=5)
    frame_opcoes = Frame(frame_principal)
    frame_opcoes.grid(row=5, column=1, sticky=W, pady=5)
    Checkbutton(frame_opcoes, text="Preencher notas em branco com zeros", variable=preencher_zeros).pack(anchor=W)
    
    # Informação adicional sobre relatórios com assinatura
    Label(frame_principal, text="Observação:", anchor=W, font=("Arial", 10, "bold")).grid(row=6, column=0, sticky=W, pady=(15, 0))
    Label(frame_principal, text="Este relatório inclui uma coluna para assinatura dos\nresponsáveis e é gerado em modo paisagem.", 
          anchor=W, justify=LEFT).grid(row=6, column=1, sticky=W, pady=(15, 0))
    
    # Frame para botões
    frame_botoes = Frame(janela_relatorio, padx=20, pady=15)
    frame_botoes.pack(fill=X)
    
    # Função para gerar o relatório
    def gerar_relatorio():
        bimestre = bimestre_var.get()
        nivel = nivel_var.get()
        ano = ano_letivo_var.get()
        preencher_com_zeros = preencher_zeros.get()
        
        # Configurar status de matrícula
        if incluir_transferidos.get():
            status = ["Ativo", "Transferido"]
        else:
            status = status_var.get()
        
        # Fechar a janela
        janela_relatorio.destroy()
        
        # Exibir feedback ao usuário
        if status_label is not None:
            status_label.config(text=f"Gerando relatório de notas com assinatura para {bimestre} ({nivel})...")
        janela.update()
        
        # Gerar o relatório em background para não bloquear a UI
        def _worker():
            try:
                from services.report_service import gerar_relatorio_avancado_com_assinatura as service_gerar
                resultado = service_gerar(
                    bimestre=bimestre,
                    nivel_ensino=nivel,
                    ano_letivo=ano,
                    status_matricula=status,
                    preencher_nulos=preencher_com_zeros
                )

                def _on_done():
                    if resultado:
                        if status_label is not None:
                            status_label.config(text="Relatório com assinatura gerado com sucesso!")
                    else:
                        if status_label is not None:
                            status_label.config(text="Nenhum dado encontrado para o relatório.")
                        messagebox.showwarning("Sem dados", f"Não foram encontrados dados para o {bimestre} no nível {nivel}.")

                janela.after(0, _on_done)
            except Exception as e:
                def _on_error():
                    messagebox.showerror("Erro", f"Falha ao gerar relatório: {str(e)}")
                    if status_label is not None:
                        status_label.config(text="")

                janela.after(0, _on_error)

        from threading import Thread
        Thread(target=_worker, daemon=True).start()
    
    # Botões
    Button(frame_botoes, text="Cancelar", command=janela_relatorio.destroy, width=10).pack(side=RIGHT, padx=5)
    Button(frame_botoes, text="Gerar", command=gerar_relatorio, width=10, bg=co5, fg=co0).pack(side=RIGHT, padx=5)


def abrir_relatorio_pendencias():
    """
    Abre interface para gerar relatório de pendências de notas
    """
    # Criar janela
    janela_pendencias = Toplevel(janela)
    janela_pendencias.title("Relatório de Pendências de Notas")
    janela_pendencias.geometry("550x480")
    janela_pendencias.resizable(False, False)
    janela_pendencias.transient(janela)
    janela_pendencias.grab_set()
    janela_pendencias.configure(bg=co0)
    
    # Variáveis
    bimestre_var = StringVar(value="3º bimestre")
    nivel_var = StringVar(value="iniciais")
    ano_letivo_var = IntVar(value=2025)
    
    # Frame de cabeçalho com cor destaque
    frame_cabecalho = Frame(janela_pendencias, bg=co1, pady=15)
    frame_cabecalho.pack(fill=X)
    
    Label(frame_cabecalho, text="📊 RELATÓRIO DE PENDÊNCIAS", 
          font=("Arial", 14, "bold"), bg=co1, fg=co0).pack()
    Label(frame_cabecalho, text="Identifique alunos sem notas e disciplinas não lançadas", 
          font=("Arial", 9), bg=co1, fg=co9).pack(pady=(5, 0))
    
    # Frame principal
    frame_principal = Frame(janela_pendencias, bg=co0, padx=25, pady=20)
    frame_principal.pack(fill=BOTH, expand=True)
    
    # Bimestre
    Label(frame_principal, text="Bimestre:", anchor=W, bg=co0, 
          font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=W, pady=8, padx=(0, 10))
    bimestres = ["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
    combo_bimestre = ttk.Combobox(frame_principal, textvariable=bimestre_var, 
                                   values=bimestres, state="readonly", width=22, font=("Arial", 10))
    combo_bimestre.grid(row=0, column=1, sticky=W, pady=8)
    
    # Separador
    Frame(frame_principal, height=1, bg=co9).grid(row=1, column=0, columnspan=2, sticky=EW, pady=8)
    
    # Nível de ensino
    Label(frame_principal, text="Nível de ensino:", anchor=W, bg=co0,
          font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=W, pady=8, padx=(0, 10))
    frame_nivel = Frame(frame_principal, bg=co0)
    frame_nivel.grid(row=2, column=1, sticky=W, pady=8)
    Radiobutton(frame_nivel, text="Séries iniciais (1º ao 5º)", 
                variable=nivel_var, value="iniciais", bg=co0, 
                font=("Arial", 9), activebackground=co0,
                selectcolor=co4).pack(anchor=W, pady=2)
    Radiobutton(frame_nivel, text="Séries finais (6º ao 9º)", 
                variable=nivel_var, value="finais", bg=co0,
                font=("Arial", 9), activebackground=co0,
                selectcolor=co4).pack(anchor=W, pady=2)
    
    # Separador
    Frame(frame_principal, height=1, bg=co9).grid(row=3, column=0, columnspan=2, sticky=EW, pady=8)
    
    # Ano letivo
    Label(frame_principal, text="Ano letivo:", anchor=W, bg=co0,
          font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=W, pady=8, padx=(0, 10))
    anos = ["2023", "2024", "2025", "2026", "2027"]
    combo_ano = ttk.Combobox(frame_principal, textvariable=ano_letivo_var, 
                             values=anos, state="readonly", width=22, font=("Arial", 10))
    combo_ano.grid(row=4, column=1, sticky=W, pady=8)
    
    # Frame informativo
    frame_info = Frame(frame_principal, bg=co9, relief=SOLID, borderwidth=1)
    frame_info.grid(row=5, column=0, columnspan=2, sticky=EW, pady=(15, 0))
    
    Label(frame_info, text="ℹ️ Informação", font=("Arial", 9, "bold"), 
          bg=co9, fg=co1).pack(anchor=W, padx=10, pady=(5, 2))
    Label(frame_info, text="• Alunos sem notas lançadas em disciplinas específicas", 
          font=("Arial", 8), bg=co9, fg=co7, justify=LEFT).pack(anchor=W, padx=10)
    Label(frame_info, text="• Disciplinas sem nenhum lançamento de notas", 
          font=("Arial", 8), bg=co9, fg=co7, justify=LEFT).pack(anchor=W, padx=10, pady=(0, 5))
    
    # Frame para botões
    frame_botoes = Frame(janela_pendencias, bg=co0, padx=25, pady=15)
    frame_botoes.pack(fill=X)
    
    # Função para gerar o relatório
    def gerar_relatorio():
        bimestre = bimestre_var.get()
        nivel = nivel_var.get()
        ano = ano_letivo_var.get()
        
        # Fechar a janela
        janela_pendencias.destroy()
        
        # Exibir feedback
        if status_label is not None:
            status_label.config(text=f"Gerando relatório de pendências para {bimestre} ({nivel})...")
        janela.update()
        
            # Gerar o relatório em background para não bloquear a UI
        def _worker_pendencias():
            try:
                from services.report_service import gerar_relatorio_pendencias as service_pendencias
                resultado = service_pendencias(
                    bimestre=bimestre,
                    nivel_ensino=nivel,
                    ano_letivo=ano,
                    escola_id=60
                )

                def _on_done():
                    if resultado:
                        if status_label is not None:
                            status_label.config(text="Relatório de pendências gerado com sucesso!")
                    else:
                        if status_label is not None:
                            status_label.config(text="Nenhuma pendência encontrada.")
                        messagebox.showinfo("Sem pendências", 
                                           f"Não foram encontradas pendências para o {bimestre} no nível {nivel}.")

                janela.after(0, _on_done)
            except Exception as e:
                def _on_error():
                    messagebox.showerror("Erro", f"Falha ao gerar relatório: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    if status_label is not None:
                        status_label.config(text="")

                janela.after(0, _on_error)

        try:
            from utils.executor import submit_background
            submit_background(_worker_pendencias, janela=janela)
        except Exception:
            from threading import Thread
            Thread(target=_worker_pendencias, daemon=True).start()

    # Função para exportar todas as pendências para Excel (arquivo gerado no workspace)
    def exportar_excel():
        """Abre diálogo 'Salvar como' e executa o gerador de pendências em background.

        Se o usuário selecionar um arquivo existente, o path será passado ao
        `export_pendencias_xlsx.py` via variável de ambiente `EXPORT_PENDENCIAS_OUT`.
        """

        # Pergunta ao usuário onde salvar o arquivo
        try:
            destino = filedialog.asksaveasfilename(defaultextension='.xlsx',
                                                   filetypes=[('Arquivos Excel', '*.xlsx')],
                                                   initialfile='pendencias_por_bimestre.xlsx',
                                                   title='Salvar relatório de pendências como...')
        except Exception:
            destino = None

        # Se o usuário cancelar, não prosseguir
        if not destino:
            return

        def _worker_export():
            try:
                # Fornecer o destino via variável de ambiente para o script de export
                import runpy
                import os as _os
                _os.environ['EXPORT_PENDENCIAS_OUT'] = destino

                # Executa o script que gera o XLSX no working dir do app
                runpy.run_path(str(os.path.join(os.getcwd(), 'export_pendencias_xlsx.py')),
                                run_name='__main__')

                def _on_done():
                    try:
                        if status_label is not None:
                            status_label.config(text=f'Arquivo Excel salvo em: {destino}')
                    except Exception:
                        pass
                    messagebox.showinfo('Exportar Excel', f'Arquivo salvo em:\n{destino}')

                janela.after(0, _on_done)
            except Exception as e:
                msg = str(e)
                def _on_error():
                    messagebox.showerror('Erro', f'Falha ao gerar Excel: {msg}')
                janela.after(0, _on_error)

        try:
            from utils.executor import submit_background
            submit_background(_worker_export, janela=janela)
        except Exception:
            from threading import Thread
            Thread(target=_worker_export, daemon=True).start()
    
    # Botões estilizados
    btn_gerar = Button(frame_botoes, text="📄 Gerar Relatório", command=gerar_relatorio, 
                      width=17, height=1, bg=co5, fg=co0, font=("Arial", 10, "bold"),
                      relief=RAISED, bd=2, cursor="hand2")
    btn_gerar.pack(side=RIGHT, padx=5)

    # Botão para exportar Excel com todas as pendências por bimestre
    btn_export = Button(frame_botoes, text="📥 Exportar Excel", command=exportar_excel,
                        width=16, height=1, bg=co4, fg=co0, font=("Arial", 10, "bold"),
                        relief=RAISED, bd=2, cursor="hand2")
    btn_export.pack(side=RIGHT, padx=5)
    
    btn_cancelar = Button(frame_botoes, text="✖ Cancelar", command=janela_pendencias.destroy, 
                         width=12, height=1, bg=co7, fg=co0, font=("Arial", 10, "bold"),
                         relief=RAISED, bd=2, cursor="hand2")
    btn_cancelar.pack(side=RIGHT, padx=5)
    
    # Efeitos hover nos botões
    def on_enter_gerar(e):
        btn_gerar['background'] = co6
    
    def on_leave_gerar(e):
        btn_gerar['background'] = co5
    
    def on_enter_cancelar(e):
        btn_cancelar['background'] = co8
    
    def on_leave_cancelar(e):
        btn_cancelar['background'] = co7
    
    btn_gerar.bind("<Enter>", on_enter_gerar)
    btn_gerar.bind("<Leave>", on_leave_gerar)
    btn_cancelar.bind("<Enter>", on_enter_cancelar)
    btn_cancelar.bind("<Leave>", on_leave_cancelar)


# Função para fechar o programa com backup final
def ao_fechar_programa():
    """
    Função chamada quando o usuário fecha a janela principal.
    Executa um backup final antes de encerrar o programa.
    """
    try:
        # Parar o sistema de backup automático e executar backup final (pule em TEST_MODE)
        if not TEST_MODE:
            Seguranca.parar_backup_automatico(executar_backup_final=True)
    except Exception as e:
        logger.error(f"Erro ao executar backup final: {e}")
    finally:
        # ============================================================================
        # MELHORIA 4: Fechar Connection Pool ao encerrar
        # ============================================================================
        try:
            fechar_pool()
        except Exception as e:
            logger.error(f"Erro ao fechar connection pool: {e}")
        
        # Fechar a janela
        janela.destroy()


# Iniciando a interface gráfica
criar_frames()
criar_logo()
criar_acoes()  # Isso cria os botões principais
criar_pesquisa()
criar_tabela()
criar_rodape()  # Cria o rodapé na parte inferior da janela
criar_menu_contextual()

# Iniciar o sistema de backup automático (pule quando em modo de teste)
if not TEST_MODE:
    try:
        Seguranca.iniciar_backup_automatico()
    except Exception as e:
        logger.error(f"Erro ao iniciar backup automático: {e}")

# Configurar o protocolo de fechamento da janela
janela.protocol("WM_DELETE_WINDOW", ao_fechar_programa)

# Mainloop
janela.mainloop()
