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
# import pandas as pd  # LAZY: importado sob demanda

# Importações para o dashboard com gráficos - LAZY: importados quando necessário
# import matplotlib
# matplotlib.use('TkAgg')  # Backend para integração com Tkinter
# from matplotlib.figure import Figure
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from mpl_toolkits.mplot3d import Axes3D  # Para gráficos 3D
# import numpy as np  # Para cálculos matemáticos do gráfico 3D

# from Funcionario import gerar_declaracao_funcionario  # LAZY
# import Funcionario  # LAZY
# from Gerar_Declaracao_Aluno import gerar_declaracao_aluno  # LAZY
# import Lista_atualizada  # LAZY
# import Lista_atualizada_semed  # LAZY
import Seguranca
from ui.menu import MenuManager
from ui.table import TableManager
from conexao import inicializar_pool, fechar_pool
from db.connection import get_connection
from typing import Any, cast
from integrar_historico_escolar import abrir_interface_historico, abrir_historico_aluno
import aluno
from config_logs import get_logger

# Logger da aplicação
logger = get_logger(__name__)

import json


# -----------------------------------------------------------------------------
# Documentos: pasta base e helpers
# -----------------------------------------------------------------------------
def _get_documents_root() -> str:
    """Retorna a pasta raiz onde os documentos serão gerados.
    Procura a variável de ambiente `DOCUMENTS_SECRETARIA_ROOT` e, se não
    existir, usa por padrão o diretório da aplicação (cwd). Dessa forma a
    estrutura final será `./Documentos Secretaria {ANO}` por padrão.
    """
    # 1) Preferir variável de ambiente quando definida (permite sobrepor sem alterar código)
    try:
        root = os.environ.get('DOCUMENTS_SECRETARIA_ROOT')
        if root:
            return os.path.abspath(root)
    except Exception:
        pass

    # 2) Fallback para constante em `config.py` (facilita usar um caminho embutido)
    try:
        # Import local para evitar possíveis efeitos colaterais na importação do módulo
        import config as _app_config
        default = getattr(_app_config, 'DEFAULT_DOCUMENTS_SECRETARIA_ROOT', None)
        if default:
            return os.path.abspath(default)
    except Exception:
        pass

    # 3) Último recurso: diretório atual da aplicação (cwd)
    return os.path.abspath(os.getcwd())


def _ensure_docs_dirs(ano: Optional[int] = None):
    """Garante que a estrutura de pastas para o ano exista e retorna o path."""
    root = _get_documents_root()
    if ano is None:
        try:
            ano = obter_ano_letivo_atual()
        except Exception:
            ano = datetime.now().year

    pasta_ano = os.path.join(root, f"Documentos Secretaria {int(ano)}")
    subfolders = [
        'Listas', 'Notas', 'Servicos', 'Faltas', 'Pendencias', 'Relatorios Gerais', 'Contatos', 'Outros'
    ]
    try:
        os.makedirs(pasta_ano, exist_ok=True)
        for s in subfolders:
            os.makedirs(os.path.join(pasta_ano, s), exist_ok=True)
    except Exception as e:
        logger.exception("Falha ao criar pastas de documentos: %s", e)
    return pasta_ano


# -----------------------------
# Helpers para configuração do Drive
# -----------------------------
LOCAL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'local_config.json')


def _read_local_config() -> dict:
    try:
        if os.path.exists(LOCAL_CONFIG_PATH):
            with open(LOCAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _write_local_config(d: dict) -> bool:
    try:
        with open(LOCAL_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def _extract_drive_id(s: str) -> Optional[str]:
    if not s:
        return None
    s = s.strip()
    if '/folders/' in s:
        parts = s.split('/folders/')
        if len(parts) > 1:
            return parts[1].split('?')[0].split('/')[0]
    if '/d/' in s:
        parts = s.split('/d/')
        if len(parts) > 1:
            return parts[1].split('/')[0]
    if 'id=' in s:
        parts = s.split('id=')
        if len(parts) > 1:
            return parts[1].split('&')[0]
    # provável id cru
    if len(s) >= 20 and all(c.isalnum() or c in ['-', '_'] for c in s):
        return s
    return None


def get_drive_folder_id() -> Optional[str]:
    # 1) variável de ambiente
    v = os.environ.get('DOCUMENTS_DRIVE_FOLDER_ID')
    if v:
        return _extract_drive_id(v) or v

    # 2) local_config.json
    cfg = _read_local_config()
    if cfg:
        val = cfg.get('drive_folder_id')
        if val:
            val = str(val)
            return _extract_drive_id(val) or val

    # 3) config.py fallback
    try:
        import config as _appcfg
        default = getattr(_appcfg, 'DEFAULT_DRIVE_FOLDER_ID', None)
        if default:
            return _extract_drive_id(default) or default
    except Exception:
        pass

    return None


def _categoria_por_descricao(descricao: str) -> str:
    """Mapeia uma descrição textual para uma subpasta de documentos."""
    d = (descricao or '').lower()
    if 'pendên' in d or 'pendenc' in d or 'pendências' in d:
        return 'Pendencias'
    if 'assinatura' in d or 'nota' in d or 'relatório de notas' in d:
        return 'Notas'
    if 'lista' in d or 'reuni' in d:
        return 'Listas'
    if 'frequência' in d or 'frequencia' in d or 'falt' in d:
        return 'Faltas'
    if 'contato' in d or 'contatos' in d:
        return 'Contatos'
    if 'movimentação' in d or 'movimentacao' in d or 'serviço' in d or 'servicos' in d:
        return 'Servicos'
    if 'geral' in d:
        return 'Relatorios Gerais'
    return 'Outros'


def _run_in_documents_dir(descricao: str, fn):
    """Executa `fn()` com o cwd temporariamente alterado para a pasta apropriada.

    A pasta é: <root>/Documentos Secretaria {ano}/{categoria}
    """
    pasta_ano = _ensure_docs_dirs()
    categoria = _categoria_por_descricao(descricao)
    target = os.path.join(pasta_ano, categoria)
    cwd_before = os.getcwd()
    try:
        os.makedirs(target, exist_ok=True)
        os.chdir(target)
        return fn()
    finally:
        try:
            os.chdir(cwd_before)
        except Exception:
            pass


def _run_report_in_background(fn, descricao: str):
    # Delegar para o módulo de UI (`ui.dashboard`) que oferece janela de progresso
    try:
        from ui.dashboard import run_report_in_background
        return run_report_in_background(fn, descricao, janela=janela, status_label=status_label, co1=co1, co0=co0, co6=co6)
    except Exception:
        # Se falhar (ex.: módulo não disponível), usar fallback mínimo local
        def _worker():
            try:
                # Executa o trabalho dentro da pasta de documentos apropriada
                def _call():
                    return fn()

                res = _run_in_documents_dir(descricao, _call)

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
            # Executar o módulo produtor de buffer dentro da pasta de documentos
            def _call():
                return module_fn()

            res = _run_in_documents_dir(descricao, _call)
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
        import Lista_atualizada  # Lazy import
        if hasattr(Lista_atualizada, 'lista_atualizada'):
            _run_report_in_background(Lista_atualizada.lista_atualizada, "Lista Atualizada")
        else:
            messagebox.showerror("Erro", "Função 'lista_atualizada' não disponível no módulo Lista_atualizada.")
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao gerar Lista Atualizada: {e}")


def lista_atualizada_semed_wrapper():
    try:
        import Lista_atualizada_semed  # Lazy import
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

# TEST_MODE: Usar variável de ambiente para controlar modo de teste
# Define: set GESTAO_TEST_MODE=true (Windows) ou export GESTAO_TEST_MODE=true (Linux)
TEST_MODE = os.environ.get('GESTAO_TEST_MODE', 'false').lower() == 'true'

if TEST_MODE:
    logger.warning("⚠️ SISTEMA EM MODO DE TESTE - Backups automáticos desabilitados")

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


# Importar cores centralizadas
from ui.colors import COLORS, get_colors_dict

# Criar variáveis globais de cores para compatibilidade com código legado
# TODO Sprint 14: Eliminar essas variáveis e usar COLORS diretamente
co0 = COLORS.co0  # Branco suave
co1 = COLORS.co1  # Azul escuro
co2 = COLORS.co2  # Verde
co3 = COLORS.co3  # Rosa/Magenta
co4 = COLORS.co4  # Azul claro
co5 = COLORS.co5  # Laranja
co6 = COLORS.co6  # Amarelo
co7 = COLORS.co7  # Cinza escuro
co8 = COLORS.co8  # Vermelho
co9 = COLORS.co9  # Azul claro

selected_item = None
label_rodape = None
status_label = None
dashboard_manager = None
treeview = None  # type: Optional[ttk.Treeview]
tabela_frame = None  # type: Optional[Frame]


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
dashboard_manager = None  # Será inicializado sob demanda

def criar_dashboard():
    # Inicializa o DashboardManager sob demanda (lazy loading)
    global dashboard_manager
    
    if dashboard_manager is None:
        try:
            from ui.dashboard import DashboardManager
            from services.db_service import DbService
            frame_getter = lambda: globals().get('frame_tabela')
            db_service = DbService(get_connection)
            dashboard_manager = DashboardManager(
                janela=janela, 
                db_service=db_service, 
                frame_getter=frame_getter, 
                cache_ref=_cache_estatisticas_dashboard, 
                escola_id=60,  # ID da escola
                co_bg=co1, 
                co_fg=co0, 
                co_accent=co4
            )
            logger.info(f"✓ DashboardManager instanciado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao instanciar DashboardManager: {e}", exc_info=True)
            return None
    
    # Delega a criação do dashboard ao DashboardManager
    try:
        if dashboard_manager:
            logger.info("Criando dashboard via DashboardManager...")
            return dashboard_manager.criar_dashboard()
        else:
            logger.warning("DashboardManager não disponível, pulando criação do dashboard")
    except Exception as e:
        logger.error(f"Erro ao criar dashboard: {e}")
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
# Instância global do TableManager
table_manager: Optional[TableManager] = None

def criar_tabela():
    """Cria a tabela principal usando TableManager.
    Mantém compatibilidade com código legado que usa globals treeview e tabela_frame.
    """
    global treeview, tabela_frame, table_manager, colunas, df
    
    # Garantir colunas e df padrão caso não estejam definidos ainda
    if 'colunas' not in globals() or not globals().get('colunas'):
        colunas = ['ID', 'Nome']
    if 'df' not in globals() or globals().get('df') is None:
        import pandas as pd  # Lazy import
        df = pd.DataFrame(columns=colunas)
    
    # Criar TableManager se ainda não existe
    if table_manager is None:
        # Dicionário de cores para o TableManager
        colors_dict = {
            'co0': co0,
            'co1': co1,
            'co4': co4
        }
        table_manager = TableManager(parent_frame=frame_tabela, colors=colors_dict)
    
    # Criar tabela com callbacks
    table_manager.criar_tabela(
        colunas=colunas,
        df=df,
        on_select_callback=selecionar_item,
        on_keyboard_callback=on_select
    )
    
    # Atualizar globals para compatibilidade
    treeview = table_manager.treeview
    tabela_frame = table_manager.tabela_frame
    
    # IMPORTANTE: Exibir dashboard por padrão ao invés da tabela
    criar_dashboard()

def selecionar_item(event):
    # Obtém o item selecionado
    if treeview is None:
        return
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
        if treeview is None:
            return
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
    if treeview is not None:
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
        
        def _gerar_declaracao():
            from Funcionario import gerar_declaracao_funcionario  # Lazy import
            return gerar_declaracao_funcionario(id_item)
        
        Button(acoes_frame, text="Declaração", command=_gerar_declaracao,
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=co2, fg=co0).grid(row=0, column=2, padx=5, pady=5)

def verificar_matricula_ativa(aluno_id):
    """
    Verifica se o aluno possui matrícula ativa ou transferida na escola com ID 60 no ano letivo atual.
    
    Args:
        aluno_id: ID do aluno a ser verificado
        
    Returns:
        bool: True se o aluno possui matrícula ativa ou transferida, False caso contrário
    """
    from mysql.connector import Error as MySQLError
    from db.connection import get_cursor
    
    try:
        aluno_id_int = int(str(aluno_id))
    except (ValueError, TypeError) as e:
        logger.error(f"ID de aluno inválido: {aluno_id} - {e}")
        messagebox.showerror("Erro", "ID de aluno inválido.")
        return False
    
    try:
        with get_cursor() as cursor:
            # Obtém o ID do ano letivo atual
            cursor.execute("SELECT id FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
            resultado_ano = cursor.fetchone()

            if not resultado_ano:
                # Se não encontrar o ano letivo atual, tenta obter o ano letivo mais recente
                logger.debug("Ano letivo atual não encontrado, buscando o mais recente")
                cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado_ano = cursor.fetchone()

            if not resultado_ano:
                logger.warning("Nenhum ano letivo encontrado no sistema")
                messagebox.showwarning("Aviso", "Não foi possível determinar o ano letivo atual.")
                return False

            ano_letivo_id = int(str(resultado_ano['id'] if isinstance(resultado_ano, dict) else resultado_ano[0]))
            logger.debug(f"Verificando matrícula para aluno {aluno_id_int} no ano letivo {ano_letivo_id}")

            # Verifica se o aluno possui matrícula ativa ou transferida na escola 60 no ano letivo atual
            cursor.execute("""
                SELECT m.id 
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                WHERE m.aluno_id = %s 
                AND m.ano_letivo_id = %s 
                AND t.escola_id = 60
                AND m.status IN ('Ativo', 'Transferido')
            """, (aluno_id_int, ano_letivo_id))

            resultado = cursor.fetchone()
            tem_matricula = resultado is not None
            
            logger.debug(f"Aluno {aluno_id_int} {'possui' if tem_matricula else 'não possui'} matrícula ativa")
            return tem_matricula
            
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao verificar matrícula do aluno {aluno_id}: {e}")
        messagebox.showerror("Erro", f"Erro ao verificar matrícula: {str(e)}")
        return False
    except Exception as e:
        logger.exception(f"Erro inesperado ao verificar matrícula do aluno {aluno_id}: {e}")
        messagebox.showerror("Erro", f"Erro ao verificar matrícula: {str(e)}")
        return False

def verificar_historico_matriculas(aluno_id):
    """
    Verifica se o aluno já teve alguma matrícula em qualquer escola e em qualquer ano letivo.
    
    Args:
        aluno_id: ID do aluno a ser verificado
        
    Returns:
        tuple: (bool, list) onde:
            - bool: True se o aluno possui histórico de matrícula, False caso contrário
            - list: Lista de tuplas (ano_letivo, ano_letivo_id) com matrícula (vazio se não houver)
    """
    from mysql.connector import Error as MySQLError
    from db.connection import get_cursor
    
    try:
        aluno_id_int = int(str(aluno_id))
    except (ValueError, TypeError) as e:
        logger.error(f"ID de aluno inválido em verificar_historico_matriculas: {aluno_id} - {e}")
        messagebox.showerror("Erro", "ID de aluno inválido.")
        return False, []
    
    try:
        with get_cursor() as cursor:
            # Verifica se o aluno possui matrícula em qualquer ano letivo
            logger.debug(f"Buscando histórico de matrículas para aluno {aluno_id_int}")
            cursor.execute("""
                SELECT DISTINCT al.ano_letivo, al.id, m.status
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                JOIN anosletivos al ON m.ano_letivo_id = al.id
                WHERE m.aluno_id = %s 
                AND m.status IN ('Ativo', 'Transferido')
                ORDER BY al.ano_letivo DESC
            """, (aluno_id_int,))

            resultados = cursor.fetchall()

            # Se não houver resultados, verificar diretamente se há o ano letivo 2024 (ID=1)
            if not resultados:
                logger.debug(f"Nenhuma matrícula ativa encontrada para aluno {aluno_id_int}, verificando ano letivo padrão")
                cursor.execute("SELECT ano_letivo, id FROM anosletivos WHERE id = 1")
                ano_2024 = cursor.fetchone()
                if ano_2024:
                    # Verificar se o aluno tem qualquer matrícula para este ano
                    cursor.execute("""
                        SELECT COUNT(*) FROM matriculas 
                        WHERE aluno_id = %s AND ano_letivo_id = 1
                    """, (aluno_id_int,))
                    resultado_count = cursor.fetchone()
                    count_val = resultado_count['COUNT(*)'] if isinstance(resultado_count, dict) else resultado_count[0]
                    tem_matricula = bool(count_val and int(str(count_val)) > 0)

                    if tem_matricula:
                        ano_val = ano_2024['ano_letivo'] if isinstance(ano_2024, dict) else ano_2024[0]
                        id_val = ano_2024['id'] if isinstance(ano_2024, dict) else ano_2024[1]
                        resultados = [(ano_val, id_val, 'Ativo')]
                        logger.debug(f"Encontrada matrícula no ano letivo padrão para aluno {aluno_id_int}")

            # Se encontrou resultados, retorna True e a lista de anos letivos
            if resultados:
                anos_letivos = []
                for row in resultados:
                    if isinstance(row, dict):
                        anos_letivos.append((row['ano_letivo'], row['id']))
                    else:
                        anos_letivos.append((row[0], row[1]))
                logger.info(f"Aluno {aluno_id_int} possui {len(anos_letivos)} matrícula(s) no histórico")
                return True, anos_letivos
            else:
                # Se ainda não encontrou, busca todos os anos letivos disponíveis
                logger.debug("Nenhuma matrícula encontrada, retornando todos os anos letivos disponíveis")
                cursor.execute("SELECT ano_letivo, id FROM anosletivos ORDER BY ano_letivo DESC")
                todos_anos = cursor.fetchall()

                if todos_anos:
                    anos_list = []
                    for row in todos_anos:
                        if isinstance(row, dict):
                            anos_list.append((row['ano_letivo'], row['id']))
                        else:
                            anos_list.append((row[0], row[1]))
                    return True, anos_list
                return False, []
                
    except MySQLError as e:
        logger.exception(f"Erro MySQL ao verificar histórico de matrículas do aluno {aluno_id}: {e}")
        messagebox.showerror("Erro", f"Erro ao verificar histórico de matrículas: {str(e)}")
        return False, []
    except Exception as e:
        logger.exception(f"Erro inesperado ao verificar histórico de matrículas do aluno {aluno_id}: {e}")
        messagebox.showerror("Erro", f"Erro ao verificar histórico de matrículas: {str(e)}")
        return False, []

def matricular_aluno(aluno_id):
    """
    Abre modal para matricular o aluno.
    
    REFATORADO Sprint 14: Usa ui/matricula_modal.py ao invés de código inline.
    
    Args:
        aluno_id: ID do aluno a ser matriculado
    """
    try:
        from ui.matricula_modal import MatriculaModal
        from ui.colors import get_colors_dict
        
        # Obter nome do aluno
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM alunos WHERE id = %s", (int(str(aluno_id)),))
            resultado_nome = cursor.fetchone()
            cursor.close()

        if resultado_nome is None:
            messagebox.showerror("Erro", "Aluno não encontrado.")
            return
        
        nome_aluno = resultado_nome[0]
        
        # Callback para atualizar tabela após matrícula
        def ao_matricular_sucesso():
            atualizar_tabela_principal()
            logger.info(f"Aluno {nome_aluno} matriculado com sucesso")
        
        # Criar e mostrar modal de matrícula
        MatriculaModal(
            parent=janela,
            aluno_id=aluno_id,
            nome_aluno=nome_aluno,
            colors=get_colors_dict(),
            callback_sucesso=ao_matricular_sucesso
        )
        
    except Exception as e:
        logger.exception(f"Erro ao abrir matrícula: {e}")
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
        if treeview is None:
            messagebox.showerror("Erro", "Tabela não inicializada.")
            return
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
        if treeview is None:
            messagebox.showerror("Erro", "Tabela não inicializada.")
            return
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
                from Gerar_Declaracao_Aluno import gerar_declaracao_aluno  # Lazy import
                return gerar_declaracao_aluno(id_pessoa, marcacoes, motivo_outros)
            elif tipo_pessoa == 'Funcionário':
                from Funcionario import gerar_declaracao_funcionario  # Lazy import
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
            if tabela_frame is not None and tabela_frame.winfo_ismapped():
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
            if tabela_frame is not None and not tabela_frame.winfo_ismapped():
                tabela_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        except Exception:
            pass
    except Exception as e:
        logger.exception("Falha ao preparar área da tabela: %s", e)
        messagebox.showerror("Erro", f"Falha ao preparar área da tabela: {e}")
        return

    # Limpa o Treeview primeiro
    try:
        if treeview is not None:
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
                if treeview is not None:
                    item_id = treeview.insert("", "end", values=resultado)
                    if primeira_chave is None:
                        primeira_chave = item_id
            except Exception as e:
                logger.exception("Erro ao inserir resultado na treeview: %s - Resultado: %s", e, resultado)

        # Forçar atualização visual e foco no primeiro item
        try:
            if treeview is not None:
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
    """
    Cria os botões de ação e menus da aplicação.
    
    REFATORADO Sprint 15: Usa ActionCallbacksManager ao invés de callbacks inline.
    """
    # Inicializar gerenciador de callbacks
    from ui.action_callbacks import ActionCallbacksManager
    callbacks = ActionCallbacksManager(janela, atualizar_tabela_principal)
    
    # Frame para os botões de ação
    botoes_frame = Frame(frame_dados, bg=co1)
    botoes_frame.pack(fill=X, expand=True, padx=10, pady=5)
    
    # Configurar grid do frame de botões
    for i in range(7):  # 7 colunas para acomodar todos os botões
        botoes_frame.grid_columnconfigure(i, weight=1)

    # Botões de ação
    global app_img_cadastro
    try:
        app_img_cadastro = Image.open('icon/plus.png')
        app_img_cadastro = app_img_cadastro.resize((18, 18))
        app_img_cadastro = ImageTk.PhotoImage(app_img_cadastro)
        app_cadastro = Button(botoes_frame, command=callbacks.cadastrar_novo_aluno, image=app_img_cadastro, text="Novo Aluno",
                            compound=LEFT, overrelief=RIDGE, font=('Ivy 11'), bg=co2, fg=co0)
    except FileNotFoundError:
        app_cadastro = Button(botoes_frame, command=callbacks.cadastrar_novo_aluno, text="+ Novo Aluno",
                            compound=LEFT, overrelief=RIDGE, font=('Ivy 11'), bg=co2, fg=co0)
    app_cadastro.grid(row=0, column=0, padx=5, pady=5, sticky=EW)
    if 'app_img_cadastro' in locals():
        setattr(app_cadastro, '_image_ref', app_img_cadastro)
    
    global app_img_funcionario
    try:
        app_img_funcionario = Image.open('icon/video-conference.png')
        app_img_funcionario = app_img_funcionario.resize((18, 18))
        app_img_funcionario = ImageTk.PhotoImage(app_img_funcionario)
        app_funcionario = Button(botoes_frame, command=callbacks.cadastrar_novo_funcionario, image=app_img_funcionario,
                                text="Novo Funcionário", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                                bg=co3, fg=co0)
    except FileNotFoundError:
        app_funcionario = Button(botoes_frame, command=callbacks.cadastrar_novo_funcionario, text="+ Novo Funcionário", 
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
        app_historico = Button(botoes_frame, command=callbacks.abrir_historico_escolar, image=app_img_historico,
                              text="Histórico Escolar", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                              bg=co4, fg=co0)
    except FileNotFoundError:
        app_historico = Button(botoes_frame, command=callbacks.abrir_historico_escolar, text="Histórico Escolar", 
                              compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                              bg=co4, fg=co0)
    app_historico.grid(row=0, column=2, padx=5, pady=5, sticky=EW)
    if 'app_img_historico' in locals():
        setattr(app_historico, '_image_ref', app_img_historico)
    
    # Botão para acessar a interface administrativa
    global app_img_admin
    try:
        app_img_admin = Image.open('icon/settings.png')
        app_img_admin = app_img_admin.resize((18, 18))
        app_img_admin = ImageTk.PhotoImage(app_img_admin)
        app_admin = Button(botoes_frame, command=callbacks.abrir_interface_administrativa, image=app_img_admin,
                          text="Administração", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                          bg=co5, fg=co0)
    except FileNotFoundError:
        app_admin = Button(botoes_frame, command=callbacks.abrir_interface_administrativa, text="Administração", 
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
    listas_menu.add_command(label="Lista Atualizada", command=callbacks.lista_atualizada, font=menu_font)
    listas_menu.add_command(label="Lista Atualizada SEMED", command=callbacks.reports.lista_atualizada_semed, font=menu_font)
    listas_menu.add_command(label="Lista de Reunião", command=callbacks.lista_reuniao, font=menu_font)
    listas_menu.add_command(label="Lista de Notas", command=callbacks.lista_notas, font=menu_font)
    listas_menu.add_command(label="Lista de Frequências", command=callbacks.reports.lista_frequencia, font=menu_font)
    listas_menu.add_separator()
    listas_menu.add_command(label="Contatos de Responsáveis", command=callbacks.relatorio_contatos_responsaveis, font=menu_font)
    listas_menu.add_command(label="Levantamento de Necessidades", command=callbacks.reports.relatorio_levantamento_necessidades, font=menu_font)
    listas_menu.add_command(label="Lista Alfabética", command=callbacks.reports.relatorio_lista_alfabetica, font=menu_font)
    listas_menu.add_command(label="Alunos com Transtornos", command=callbacks.reports.relatorio_alunos_transtornos, font=menu_font)
    listas_menu.add_separator()
    listas_menu.add_command(label="Termo de Responsabilidade", command=callbacks.reports.relatorio_termo_responsabilidade, font=menu_font)
    listas_menu.add_command(label="Tabela de Docentes", command=callbacks.reports.relatorio_tabela_docentes, font=menu_font)
    
    # (Movimento Mensal transferido para o menu 'Serviços')

    # Adicionando o menu à barra de menus
    menu_bar.add_cascade(label="Listas", menu=listas_menu)

    # Adicionando o menu "Notas"
    notas_menu = Menu(menu_bar, tearoff=0)
    notas_menu.add_command(label="Cadastrar/Editar Notas", command=callbacks.abrir_cadastro_notas, font=menu_font)
    notas_menu.add_command(label="Relatório Estatístico de Notas", command=callbacks.reports.abrir_relatorio_analise, font=menu_font)

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

    servicos_menu.add_command(
        label="Solicitação de Professores e Coordenadores",
        command=callbacks.administrativo.abrir_solicitacao_professores,
        font=menu_font
    )

    servicos_menu.add_command(
        label="Gerenciador de Documentos de Funcionários",
        command=callbacks.abrir_gerenciador_documentos,
        font=menu_font
    )

    servicos_menu.add_command(
        label="Gerenciador de Documentos do Sistema",
        command=callbacks.declaracao.abrir_gerenciador_documentos_sistema,
        font=menu_font
    )

    # Importar interface de declaração do módulo
    from ui.interfaces_extended import abrir_interface_declaracao_comparecimento
    from declaracao_comparecimento import gerar_declaracao_comparecimento_responsavel
    
    # Função wrapper para o menu
    def abrir_interface_declaracao_comparecimento_menu():
        """Abre interface para selecionar aluno e gerar declaração de comparecimento"""
        abrir_interface_declaracao_comparecimento(janela, gerar_declaracao_comparecimento_responsavel)

    servicos_menu.add_separator()
    
    servicos_menu.add_command(
        label="Declaração de Comparecimento (Responsável)",
        command=abrir_interface_declaracao_comparecimento_menu,
        font=menu_font
    )

    # Importar interface de crachás do módulo
    from ui.interfaces_extended import abrir_interface_crachas
    
    # Função wrapper (mantida para compatibilidade)
    def _abrir_crachas():
        abrir_interface_crachas(janela)

    servicos_menu.add_command(
        label="Crachás Alunos/Responsáveis",
        command=_abrir_crachas,
        font=menu_font
    )

    # Importar interface de importação do módulo
    from ui.interfaces_extended import abrir_importacao_notas_html
    
    # Função wrapper (mantida para compatibilidade)
    def _abrir_importacao_html():
        abrir_importacao_notas_html(janela)

    servicos_menu.add_command(
        label="Importar Notas do GEDUC (HTML → Excel)",
        command=_abrir_importacao_html,
        font=menu_font
    )
    
    servicos_menu.add_separator()
    servicos_menu.add_command(
        label="🔄 Transição de Ano Letivo",
        command=callbacks.abrir_transicao_ano_letivo,
        font=menu_font
    )

    menu_bar.add_cascade(label="Serviços", menu=servicos_menu)

    # =========================
    # Gerenciamento de Faltas
    # =========================
    faltas_menu = Menu(menu_bar, tearoff=0)

    # Importar diálogos de ponto do módulo
    from ui.dialogs_extended import abrir_dialogo_folhas_ponto, abrir_dialogo_resumo_ponto
    
    # Wrappers para manter compatibilidade com chamadas do menu
    def _abrir_folhas_ponto():
        abrir_dialogo_folhas_ponto(janela, status_label)
    
    def _abrir_resumo_ponto():
        abrir_dialogo_resumo_ponto(janela, status_label)

    # Cadastrar/Editar Faltas de Funcionários
    def abrir_cadastro_faltas():
        try:
            from InterfaceCadastroEdicaoFaltas import abrir_interface_faltas
            abrir_interface_faltas(janela_principal=janela)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a interface de faltas: {e}")

    faltas_menu.add_command(label="Cadastrar/Editar Faltas", command=abrir_cadastro_faltas, font=menu_font)
    faltas_menu.add_separator()
    faltas_menu.add_command(label="Gerar Folhas de Ponto", command=_abrir_folhas_ponto, font=menu_font)
    faltas_menu.add_command(label="Gerar Resumo de Ponto", command=_abrir_resumo_ponto, font=menu_font)

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
    # Importar diálogo de relatório do módulo
    from ui.report_dialogs import abrir_relatorio_avancado as abrir_relatorio_avancado_dialog
    from NotaAta import gerar_relatorio_notas
    
    # Função wrapper
    def abrir_relatorio_avancado():
        abrir_relatorio_avancado_dialog(janela, status_label, gerar_relatorio_notas)
    
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
    # Submenu para Relatórios de Pendências (gerar PDF direto por bimestre/nível + abrir interface)
    relatorios_pendencias_menu = Menu(notas_menu, tearoff=0)

    def _gerar_pendencias_em_bg(bimestre: str, nivel: str):
        """Gera relatório de pendências em background para evitar bloquear a UI."""
        try:
            if status_label is not None:
                status_label.config(text=f"Gerando pendências: {bimestre} ({nivel})...")
            janela.update()
        except Exception:
            pass

        def _worker():
            try:
                from services.report_service import gerar_relatorio_pendencias as svc
                ok = svc(bimestre=bimestre, nivel_ensino=nivel, ano_letivo=datetime.now().year, escola_id=60)
                def _on_done():
                    try:
                        if ok:
                            if status_label is not None:
                                status_label.config(text=f"Pendências geradas: {bimestre} ({nivel})")
                            messagebox.showinfo("Concluído", f"Relatório de pendências gerado: {bimestre} ({nivel})")
                        else:
                            if status_label is not None:
                                status_label.config(text="Nenhuma pendência encontrada.")
                            messagebox.showinfo("Sem pendências", f"Nenhuma pendência encontrada para {bimestre} ({nivel}).")
                    except Exception:
                        pass

                janela.after(0, _on_done)
            except Exception as e:
                def _on_error():
                    messagebox.showerror("Erro", f"Falha ao gerar pendências: {e}")
                    try:
                        if status_label is not None:
                            status_label.config(text="")
                    except Exception:
                        pass
                janela.after(0, _on_error)

        try:
            from utils.executor import submit_background
            submit_background(_worker, janela=janela)
        except Exception:
            from threading import Thread
            Thread(target=_worker, daemon=True).start()

    # Itens por bimestre (iniciais)
    relatorios_pendencias_menu.add_command(label="1º bimestre", command=lambda: _gerar_pendencias_em_bg("1º bimestre", "iniciais"), font=menu_font)
    relatorios_pendencias_menu.add_command(label="2º bimestre", command=lambda: _gerar_pendencias_em_bg("2º bimestre", "iniciais"), font=menu_font)
    relatorios_pendencias_menu.add_command(label="3º bimestre", command=lambda: _gerar_pendencias_em_bg("3º bimestre", "iniciais"), font=menu_font)
    relatorios_pendencias_menu.add_command(label="4º bimestre", command=lambda: _gerar_pendencias_em_bg("4º bimestre", "iniciais"), font=menu_font)
    relatorios_pendencias_menu.add_separator()
    # Itens por bimestre (6º ao 9º)
    relatorios_pendencias_menu.add_command(label="1º bimestre (6º ao 9º ano)", command=lambda: _gerar_pendencias_em_bg("1º bimestre", "finais"), font=menu_font)
    relatorios_pendencias_menu.add_command(label="2º bimestre (6º ao 9º ano)", command=lambda: _gerar_pendencias_em_bg("2º bimestre", "finais"), font=menu_font)
    relatorios_pendencias_menu.add_command(label="3º bimestre (6º ao 9º ano)", command=lambda: _gerar_pendencias_em_bg("3º bimestre", "finais"), font=menu_font)
    relatorios_pendencias_menu.add_command(label="4º bimestre (6º ao 9º ano)", command=lambda: _gerar_pendencias_em_bg("4º bimestre", "finais"), font=menu_font)
    relatorios_pendencias_menu.add_separator()
    relatorios_pendencias_menu.add_command(label="Abrir interface", command=abrir_relatorio_pendencias, font=menu_font)

    notas_menu.add_cascade(label="Relatórios de Pendências", menu=relatorios_pendencias_menu, font=menu_font)

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
        app_horarios = Button(botoes_frame, command=callbacks.abrir_horarios_escolares, image=app_img_horarios,
                             text="Horários", compound=LEFT, overrelief=RIDGE, font=('Ivy 11'),
                             bg=co3, fg=co0)
    except FileNotFoundError:
        app_horarios = Button(botoes_frame, command=callbacks.abrir_horarios_escolares, text="Horários",
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


# DashboardManager será instanciado após criar_frames() para garantir que frame_tabela exista
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
        if treeview is None or not treeview.winfo_exists():
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
            if treeview is not None and treeview.get_children():
                for item in treeview.get_children():
                    treeview.delete(item)
        except TclError as tcl_e:
            logger.error(f"Erro ao limpar treeview: {str(tcl_e)}")
            raise  # Relançar para ser tratado pelo bloco de exceção principal
            
        # Inserir os novos dados
        try:
            if treeview is not None:
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
        if treeview is None:
            messagebox.showerror("Erro", "Tabela não inicializada.")
            return
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
    Abre modal para editar a matrícula do aluno.
    
    REFATORADO Sprint 14: Usa ui/matricula_modal.py ao invés de código inline.
    
    Args:
        aluno_id: ID do aluno a ter matrícula editada
    """
    try:
        from ui.matricula_modal import MatriculaModal
        from ui.colors import get_colors_dict
        
        # Obter nome do aluno
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM alunos WHERE id = %s", (int(str(aluno_id)),))
            resultado_nome = cursor.fetchone()
            cursor.close()

        if resultado_nome is None:
            messagebox.showerror("Erro", "Aluno não encontrado.")
            return
        
        nome_aluno = resultado_nome[0]
        
        # Callback para atualizar tabela após edição
        def ao_editar_sucesso():
            atualizar_tabela_principal()
            logger.info(f"Matrícula do aluno {nome_aluno} editada com sucesso")
        
        # Criar e mostrar modal de matrícula (funciona tanto para criar quanto editar)
        MatriculaModal(
            parent=janela,
            aluno_id=aluno_id,
            nome_aluno=nome_aluno,
            colors=get_colors_dict(),
            callback_sucesso=ao_editar_sucesso
        )
        
    except Exception as e:
        logger.exception(f"Erro ao abrir edição de matrícula: {e}")
        messagebox.showerror("Erro", f"Erro ao preparar edição: {str(e)}")

def selecionar_mes_movimento():
    """Seleciona mês para o relatório de movimentação usando dialogs.py."""
    from ui.dialogs import selecionar_mes
    
    def callback_mes(numero_mes: int):
        relatorio_movimentacao_mensal(numero_mes)
    
    selecionar_mes(
        parent=janela,
        titulo="Selecionar Mês para Relatório",
        callback=callback_mes,
        colors={'co1': co1, 'co0': co0, 'co2': co2, 'co8': co8}
    )

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
    # Criar janela para configuração de relatório avançado (padronizada com Pendências)
    janela_relatorio = Toplevel(janela)
    janela_relatorio.title("Relatório de Notas com Assinatura - Opções Avançadas")
    janela_relatorio.geometry("500x550")
    janela_relatorio.resizable(False, False)
    janela_relatorio.transient(janela)
    janela_relatorio.grab_set()
    janela_relatorio.configure(bg=co0)

    # Variáveis para armazenar as opções
    bimestre_var = StringVar(value="1º bimestre")
    nivel_var = StringVar(value="iniciais")
    ano_letivo_var = IntVar(value=2025)
    status_var = StringVar(value="Ativo")
    incluir_transferidos = BooleanVar(value=False)
    preencher_zeros = BooleanVar(value=False)

    # Usar grid no Toplevel para garantir comportamento previsível (cabecalho, conteudo, rodape)
    janela_relatorio.grid_rowconfigure(0, weight=0)
    janela_relatorio.grid_rowconfigure(1, weight=1)
    janela_relatorio.grid_rowconfigure(2, weight=0)
    janela_relatorio.grid_columnconfigure(0, weight=1)

    # Cabeçalho com destaque (mesmo visual de Pendências)
    frame_cabecalho = Frame(janela_relatorio, bg=co1, pady=15)
    frame_cabecalho.grid(row=0, column=0, sticky=EW)
    Label(frame_cabecalho, text="📄 RELATÓRIO COM ASSINATURA", font=("Arial", 13, "bold"), bg=co1, fg=co0).pack()
    Label(frame_cabecalho, text="Configurações avançadas para geração do relatório de notas com assinatura",
          font=("Arial", 9), bg=co1, fg=co9).pack(pady=(6, 0))

    # Frame principal (conteúdo) - visual igual ao de pendências
    frame_principal = Frame(janela_relatorio, bg=co0, padx=25, pady=18)
    frame_principal.grid(row=1, column=0, sticky=NSEW)

    # Bimestre
    Label(frame_principal, text="Bimestre:", anchor=W, bg=co0, font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=W, pady=8, padx=(0, 10))
    bimestres = ["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
    combo_bimestre = ttk.Combobox(frame_principal, textvariable=bimestre_var, values=bimestres, state="readonly", width=22, font=("Arial", 10))
    combo_bimestre.grid(row=0, column=1, sticky=W, pady=8)

    # Separador visual
    Frame(frame_principal, height=1, bg=co9).grid(row=1, column=0, columnspan=2, sticky=EW, pady=8)

    # Nível de ensino
    Label(frame_principal, text="Nível de ensino:", anchor=W, bg=co0, font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=W, pady=8, padx=(0, 10))
    frame_nivel = Frame(frame_principal, bg=co0)
    frame_nivel.grid(row=2, column=1, sticky=W, pady=8)
    Radiobutton(frame_nivel, text="Séries iniciais (1º ao 5º)", variable=nivel_var, value="iniciais", bg=co0, font=("Arial", 9), activebackground=co0, selectcolor=co4).pack(anchor=W, pady=2)
    Radiobutton(frame_nivel, text="Séries finais (6º ao 9º)", variable=nivel_var, value="finais", bg=co0, font=("Arial", 9), activebackground=co0, selectcolor=co4).pack(anchor=W, pady=2)

    # Separador
    Frame(frame_principal, height=1, bg=co9).grid(row=3, column=0, columnspan=2, sticky=EW, pady=8)

    # Ano letivo
    Label(frame_principal, text="Ano letivo:", anchor=W, bg=co0, font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=W, pady=8, padx=(0, 10))
    anos = ["2023", "2024", "2025", "2026", "2027"]
    combo_ano = ttk.Combobox(frame_principal, textvariable=ano_letivo_var, values=anos, state="readonly", width=22, font=("Arial", 10))
    combo_ano.grid(row=4, column=1, sticky=W, pady=8)

    # Status de matrícula e opção incluir transferidos
    Label(frame_principal, text="Status de matrícula:", anchor=W, bg=co0, font=("Arial", 10, "bold")).grid(row=5, column=0, sticky=W, pady=8, padx=(0, 10))
    frame_status = Frame(frame_principal, bg=co0)
    frame_status.grid(row=5, column=1, sticky=W, pady=8)
    Radiobutton(frame_status, text="Apenas ativos", variable=status_var, value="Ativo", bg=co0, font=("Arial", 9), activebackground=co0).pack(anchor=W)
    Checkbutton(frame_status, text="Incluir transferidos", variable=incluir_transferidos, bg=co0).pack(anchor=W)

    # Opções de exibição
    Label(frame_principal, text="Opções de exibição:", anchor=W, bg=co0, font=("Arial", 10, "bold")).grid(row=6, column=0, sticky=W, pady=8, padx=(0, 10))
    frame_opcoes = Frame(frame_principal, bg=co0)
    frame_opcoes.grid(row=6, column=1, sticky=W, pady=8)
    Checkbutton(frame_opcoes, text="Preencher notas em branco com zeros", variable=preencher_zeros, bg=co0).pack(anchor=W)

    # Observação
    Label(frame_principal, text="Observação:", anchor=W, font=("Arial", 10, "bold"), bg=co0).grid(row=7, column=0, sticky=W, pady=(12, 0))
    Label(frame_principal, text="Este relatório inclui uma coluna para assinatura dos\nresponsáveis e é gerado em modo paisagem.", anchor=W, justify=LEFT, bg=co0).grid(row=7, column=1, sticky=W, pady=(12, 0))

    # Frame para botões (na base) - padronizado com Pendências
    frame_botoes = Frame(janela_relatorio, bg=co0, padx=25, pady=12)
    frame_botoes.grid(row=2, column=0, sticky=EW)
    # Reservar altura fixa para o rodapé para evitar sobreposição com o conteúdo
    try:
        frame_botoes.grid_propagate(False)
        frame_botoes.configure(height=60)
    except Exception:
        pass

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

        # Gerar o relatório em background
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

        try:
            from utils.executor import submit_background
            submit_background(_worker, janela=janela)
        except Exception:
            from threading import Thread
            Thread(target=_worker, daemon=True).start()

    # Criar estilos locais para garantir visibilidade em temas do sistema
    style_rel = ttk.Style(janela_relatorio)
    # Estilo do botão Gerar
    try:
        style_rel.configure("Rel.TButton", background=co5, foreground=co0, font=("Arial", 10, "bold"))
        style_rel.map("Rel.TButton", background=[('active', co6)])
    except Exception:
        pass

    # Estilo do botão Cancelar
    try:
        style_rel.configure("Cancel.TButton", background=co7, foreground=co0, font=("Arial", 10, "bold"))
        style_rel.map("Cancel.TButton", background=[('active', co8)])
    except Exception:
        pass

    # Botões usando ttk (mais consistente com temas do Windows)
    btn_cancelar_rel = ttk.Button(frame_botoes, text="✖ Cancelar", command=janela_relatorio.destroy, style="Cancel.TButton")
    btn_cancelar_rel.pack(side=RIGHT, padx=6)

    btn_gerar_rel = ttk.Button(frame_botoes, text="📄 Gerar", command=gerar_relatorio, style="Rel.TButton")
    btn_gerar_rel.pack(side=RIGHT, padx=6)

    # Adicionar log para confirmar criação dos botões (ajuda em debugging)
    try:
        logger.debug("Botões do Relatório Avançado criados: gerar=%s cancelar=%s", btn_gerar_rel, btn_cancelar_rel)
    except Exception:
        try:
            logger.debug("Botões do Relatório Avançado criados (fallback)")
        except Exception:
            pass

    # Hover: ajustar estilos dinamicamente caso o tema não respeite map()
    def _on_enter_gerar(e):
        try:
            style_rel.configure("Rel.TButton", background=co6)
        except Exception:
            pass

    def _on_leave_gerar(e):
        try:
            style_rel.configure("Rel.TButton", background=co5)
        except Exception:
            pass

    def _on_enter_cancelar(e):
        try:
            style_rel.configure("Cancel.TButton", background=co8)
        except Exception:
            pass

    def _on_leave_cancelar(e):
        try:
            style_rel.configure("Cancel.TButton", background=co7)
        except Exception:
            pass

    btn_gerar_rel.bind("<Enter>", _on_enter_gerar)
    btn_gerar_rel.bind("<Leave>", _on_leave_gerar)
    btn_cancelar_rel.bind("<Enter>", _on_enter_cancelar)
    btn_cancelar_rel.bind("<Leave>", _on_leave_cancelar)

    # Diagnostic: log estado dos botões após a janela renderizar
    def _log_button_stats():
        try:
            vals = {
                'gerar_mapped': btn_gerar_rel.winfo_ismapped(),
                'gerar_viewable': btn_gerar_rel.winfo_viewable(),
                'gerar_reqw': btn_gerar_rel.winfo_reqwidth(),
                'gerar_reqh': btn_gerar_rel.winfo_reqheight(),
                'cancelar_mapped': btn_cancelar_rel.winfo_ismapped(),
                'cancelar_viewable': btn_cancelar_rel.winfo_viewable(),
                'cancelar_reqw': btn_cancelar_rel.winfo_reqwidth(),
                'cancelar_reqh': btn_cancelar_rel.winfo_reqheight(),
            }
            try:
                # Para ttk, tentar obter cores via style lookup
                bg_rel = style_rel.lookup('Rel.TButton', 'background')
                fg_rel = style_rel.lookup('Rel.TButton', 'foreground')
                bg_cancel = style_rel.lookup('Cancel.TButton', 'background')
                fg_cancel = style_rel.lookup('Cancel.TButton', 'foreground')
                vals.update({'rel_bg': bg_rel, 'rel_fg': fg_rel, 'cancel_bg': bg_cancel, 'cancel_fg': fg_cancel})
            except Exception:
                pass
            logger.debug("Relatório Avançado - stats: %s", vals)
        except Exception as e:
            logger.exception("Erro ao logar stats dos botões: %s", e)

    try:
        janela_relatorio.after(200, _log_button_stats)
    except Exception:
        _log_button_stats()
    # Log adicional: verificar estado dos frames pai e gerenciadores de layout
    def _log_parent_frames():
        try:
            stats = {
                'toplevel_mapped': janela_relatorio.winfo_ismapped(),
                'toplevel_viewable': janela_relatorio.winfo_viewable(),
                'cabecalho_mapped': frame_cabecalho.winfo_ismapped() if 'frame_cabecalho' in locals() else None,
                'principal_mapped': frame_principal.winfo_ismapped() if 'frame_principal' in locals() else None,
                'botoes_mapped': frame_botoes.winfo_ismapped() if 'frame_botoes' in locals() else None,
                'botoes_manager': frame_botoes.winfo_manager() if 'frame_botoes' in locals() else None,
                'cabecalho_manager': frame_cabecalho.winfo_manager() if 'frame_cabecalho' in locals() else None,
                'principal_manager': frame_principal.winfo_manager() if 'frame_principal' in locals() else None,
                'toplevel_children': janela_relatorio.winfo_children()
            }
            logger.debug("Relatório Avançado - parent frames: %s", stats)
        except Exception as e:
            logger.exception("Erro ao logar parent frames: %s", e)

    try:
        janela_relatorio.after(250, _log_parent_frames)
    except Exception:
        _log_parent_frames()


def abrir_relatorio_pendencias():
    """
    Abre interface para gerar relatório de pendências de notas
    """
    # Criar janela
    janela_pendencias = Toplevel(janela)
    janela_pendencias.title("Relatório de Pendências de Notas")
    janela_pendencias.geometry("600x480")
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

    # Função para gerar um relatório geral (PDF) com todos os bimestres e turmas
    def gerar_relatorio_geral():
        """Gera um PDF único combinando os relatórios de pendências de todos os
        bimestres (iniciais e finais) para o ano selecionado.

        A implementação reutiliza o serviço `services.report_service.gerar_relatorio_pendencias`
        para gerar os PDFs individuais sem abri-los e, em seguida, concatena-os com
        `PyPDF2.PdfMerger`.
        """

        ano = ano_letivo_var.get()

        # Fechar a janela
        janela_pendencias.destroy()

        # Feedback
        if status_label is not None:
            status_label.config(text=f"Gerando relatório geral de pendências ({ano})...")
        janela.update()

        def _worker_geral():
            try:
                from services import report_service as service
                import relatorio_pendencias as rp
                import os as _os
                from PyPDF2 import PdfMerger

                # Evitar que cada geração abra o PDF no visualizador externo
                try:
                    rp.abrir_pdf_com_programa_padrao = lambda *a, **k: None
                except Exception:
                    pass

                bimestres = ["1º bimestre", "2º bimestre", "3º bimestre", "4º bimestre"]
                niveis = ["iniciais", "finais"]
                gerados = []

                # Garantir que as pastas locais existam para o ano e categorias
                pasta_ano = _ensure_docs_dirs(int(ano) if str(ano).isdigit() else None)
                pendencias_dir = _os.path.join(pasta_ano, 'Pendencias')
                relatorios_dir = _os.path.join(pasta_ano, 'Relatorios Gerais')
                try:
                    _os.makedirs(pendencias_dir, exist_ok=True)
                    _os.makedirs(relatorios_dir, exist_ok=True)
                except Exception:
                    pass

                for b in bimestres:
                    for n in niveis:
                        try:
                            # Executar a geração dentro da pasta de Pendencias para que os PDFs
                            # individuais sejam salvos em: <root>/Documentos Secretaria {ano}/Pendencias
                            def _gen():
                                return service.gerar_relatorio_pendencias(bimestre=b, nivel_ensino=n, ano_letivo=ano, escola_id=60)

                            res = _run_in_documents_dir('Pendencias', _gen)
                            ok = bool(res)
                        except Exception:
                            ok = False

                        # Nome esperado do PDF gerado pelo módulo relatorio_pendencias
                        fname = f"Pendencias_Notas_{b.replace(' ', '_')}_{n}_{ano}.pdf"
                        fpath = _os.path.join(pendencias_dir, fname)
                        if ok and _os.path.exists(fpath):
                            gerados.append(fpath)

                if not gerados:
                    def _no_files():
                        if status_label is not None:
                            status_label.config(text="Nenhum PDF gerado.")
                        messagebox.showinfo("Sem relatórios", "Não foram gerados relatórios para combinar.")
                    janela.after(0, _no_files)
                    return

                # Mesclar PDFs
                merger = PdfMerger()
                for p in gerados:
                    try:
                        merger.append(p)
                    except Exception:
                        pass

                out_name = f"Pendencias_Todas_Bimestres_{ano}.pdf"
                out_path = _os.path.join(relatorios_dir, out_name)
                try:
                    with open(out_path, 'wb') as f_out:
                        merger.write(f_out)
                finally:
                    try:
                        merger.close()
                    except Exception:
                        pass

                def _on_done():
                    try:
                        if status_label is not None:
                            status_label.config(text=f"Relatório geral salvo em: {out_path}")
                    except Exception:
                        pass
                    try:
                        # Tentar abrir com o helper do módulo legado
                        try:
                            rp.abrir_pdf_com_programa_padrao(out_path)
                        except Exception:
                            try:
                                from gerarPDF import salvar_e_abrir_pdf
                                import io
                                with open(out_path, 'rb') as f:
                                    buf = io.BytesIO(f.read())
                                salvar_e_abrir_pdf(buf)
                            except Exception:
                                pass
                    finally:
                        messagebox.showinfo('Relatório Geral', f'Arquivo salvo em:\n{out_path}')

                    # Tentar enviar para o Google Drive (se possível)
                    try:
                        from drive_uploader import upload_file
                        drive_folder_id = get_drive_folder_id()
                        logger.debug("gerar_relatorio_geral: out_path=%s drive_folder_id=%s", out_path, drive_folder_id)
                        if drive_folder_id is None:
                            # Tentar sem parent (vai para raiz da conta do usuário)
                            logger.info("gerar_relatorio_geral: nenhum drive_folder_id configurado; enviando para raiz do Drive")
                            fid, webview = upload_file(out_path, parent_id=None)
                        else:
                            logger.info("gerar_relatorio_geral: enviando para pasta do Drive id=%s", drive_folder_id)
                            fid, webview = upload_file(out_path, parent_id=drive_folder_id)
                        if fid:
                            # Se obtivermos um link webView, mostrá-lo; senão apenas informar ID
                            msg = f"Arquivo enviado ao Drive com sucesso.\nID: {fid}"
                            if webview:
                                msg += f"\nLink: {webview}"
                            try:
                                # Atualizar status e mostrar caixa
                                if status_label is not None:
                                    status_label.config(text=f"Enviado ao Drive (id={fid})")
                                messagebox.showinfo('Upload para Drive', msg)
                            except Exception:
                                pass
                        else:
                            logger.warning("Upload para Drive não ocorreu: retorno None")
                            try:
                                messagebox.showwarning('Upload para Drive', 'Falha ao enviar o arquivo para o Google Drive. Verifique logs e autorização.')
                            except Exception:
                                pass
                    except Exception as e:
                        logger.exception("Erro ao enviar relatório ao Drive: %s", e)

                janela.after(0, _on_done)
            except Exception as e:
                msg = str(e)
                def _on_error():
                    messagebox.showerror('Erro', f'Falha ao gerar Relatório Geral: {msg}')
                    if status_label is not None:
                        status_label.config(text='')
                janela.after(0, _on_error)

        try:
            from utils.executor import submit_background
            submit_background(_worker_geral, janela=janela)
        except Exception:
            from threading import Thread
            Thread(target=_worker_geral, daemon=True).start()
    
    # Botões estilizados
    btn_gerar = Button(frame_botoes, text="📄 Gerar Relatório", command=gerar_relatorio, 
                      width=17, height=1, bg=co5, fg=co0, font=("Arial", 10, "bold"),
                      relief=RAISED, bd=2, cursor="hand2")
    btn_gerar.pack(side=RIGHT, padx=5)

    # Botão para gerar relatório geral (todos os bimestres)
    btn_relatorio_geral = Button(frame_botoes, text="📚 Relatório Geral", command=gerar_relatorio_geral,
                                 width=16, height=1, bg=co4, fg=co0, font=("Arial", 10, "bold"),
                                 relief=RAISED, bd=2, cursor="hand2")
    btn_relatorio_geral.pack(side=RIGHT, padx=5)
    
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

# DashboardManager será inicializado sob demanda quando criar_dashboard() for chamado

criar_logo()
criar_acoes()  # Isso cria os botões principais
criar_pesquisa()
criar_tabela()
criar_rodape()  # Cria o rodapé na parte inferior da janela

# Criar menu contextual usando MenuManager
menu_manager = MenuManager(janela=janela)
menu_manager.criar_menu_contextual(
    treeview=treeview,
    callbacks={'editar': editar_aluno_e_destruir_frames}
)

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
