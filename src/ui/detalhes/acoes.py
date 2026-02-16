"""Botões de ação e wrappers para eventos no painel de detalhes."""

import tkinter as tk
from tkinter import Button, Frame, Label, RIDGE, X, EW, messagebox
from typing import Dict, Tuple, Any

from src.core.config_logs import get_logger
from src.services.ano_letivo_service import obter_status_matriculas_por_anos as _obter_status_por_anos_service
from src.services.aluno_service import obter_aluno_por_id as _obter_aluno_por_id_service
from src.ui.detalhes.exibir import (
    _get_default_root,
    verificar_matricula_ativa,
    verificar_historico_matriculas,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Criação de botões
# ---------------------------------------------------------------------------


def criar_botoes_frame_detalhes(
    frame_detalhes: Frame,
    tipo: str,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """Cria botões de ação no frame de detalhes (estrutura Sprint 15)."""
    acoes_frame = Frame(frame_detalhes, bg=colors['co1'])
    acoes_frame.pack(fill=X, padx=10, pady=10)

    for i in range(6):
        acoes_frame.grid_columnconfigure(i, weight=1)

    id_item = values[0]

    if tipo == "Aluno":
        criar_botoes_aluno(acoes_frame, id_item, colors)
    elif tipo == "Funcionário":
        criar_botoes_funcionario(acoes_frame, id_item, colors)


def criar_menu_boletim(
    parent_frame: Frame,
    aluno_id: int,
    anos_letivos: list,
    colors: Dict[str, str],
    col: int
) -> None:
    """Cria um menu suspenso (Combobox) para seleção do ano letivo."""
    from tkinter import StringVar, DISABLED, LEFT
    from tkinter import ttk

    boletim_frame = Frame(parent_frame, bg=colors['co1'])
    boletim_frame.grid(row=0, column=col, padx=5, pady=5)

    anos_info = {}
    try:
        anos_info = _obter_status_por_anos_service(aluno_id, anos_letivos)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao obter informações de anos letivos: {str(e)}")
        logger.error(f"Erro ao obter informações de anos letivos: {str(e)}")

    anos_display = list(anos_info.keys())

    if not anos_display:
        boletim_frame.destroy()
        Button(parent_frame, text="Boletim", state=DISABLED,
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co6'], fg=colors['co7']).grid(row=0, column=col, padx=5, pady=5)
        return

    selected_ano = StringVar()

    Label(boletim_frame, text="Boletim:", font=('Ivy 9'), bg=colors['co1'], fg=colors['co0']).pack(side=LEFT, padx=(0, 5))

    combo_anos = ttk.Combobox(boletim_frame, textvariable=selected_ano, values=anos_display,
                         font=('Ivy 9'), state="readonly", width=15)
    combo_anos.pack(side=LEFT)

    if anos_display:
        combo_anos.current(0)

    def gerar_boletim_selecionado(event=None):
        selected = selected_ano.get()
        if not selected or selected not in anos_info:
            messagebox.showwarning("Aviso", "Por favor, selecione um ano letivo válido.")
            return

        ano_letivo_id, status = anos_info[selected]

        def _worker():
            if status == 'Transferido':
                from src.relatorios.transferencia import gerar_documento_transferencia
                gerar_documento_transferencia(aluno_id, ano_letivo_id)
                return True
            else:
                try:
                    from src.relatorios.boletim import boletim as gerar_boletim
                    return gerar_boletim(aluno_id, ano_letivo_id)
                except Exception:
                    try:
                        import importlib
                        mod = importlib.import_module('boletim')
                        return getattr(mod, 'boletim')(aluno_id, ano_letivo_id)
                    except Exception:
                        raise

        def _on_done(resultado):
            if status == 'Transferido':
                messagebox.showinfo("Aluno Transferido",
                                  f"O aluno teve status 'Transferido' no ano {selected.split(' - ')[0]}.\n"
                                  f"Documento de transferência gerado com sucesso.")
            else:
                if resultado:
                    messagebox.showinfo("Concluído", "Boletim gerado com sucesso.")
                else:
                    messagebox.showwarning("Aviso", "Nenhum dado gerado para o boletim.")

        def _on_error(exc):
            messagebox.showerror("Erro", f"Falha ao gerar documento: {exc}")

        try:
            from src.utils.executor import submit_background
            root = _get_default_root()
            submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=root)
        except Exception:
            def _thread_worker():
                try:
                    res = _worker()
                    try:
                        root = _get_default_root()
                        if root:
                            root.after(0, lambda: _on_done(res))
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        root = _get_default_root()
                        if root:
                            root.after(0, lambda: _on_error(e))
                    except Exception:
                        pass

            from threading import Thread
            Thread(target=_thread_worker, daemon=True).start()

    combo_anos.bind("<<ComboboxSelected>>", gerar_boletim_selecionado)

    Button(boletim_frame, text="Gerar", command=gerar_boletim_selecionado,
           font=('Ivy 9'), bg=colors['co6'], fg=colors['co7'], width=5).pack(side=tk.LEFT, padx=(5, 0))


def criar_botoes_aluno(acoes_frame: Frame, aluno_id: int, colors: Dict[str, str]) -> None:
    """Cria botões específicos para aluno."""
    tem_matricula_ativa = verificar_matricula_ativa(aluno_id)
    tem_historico, anos_letivos = verificar_historico_matriculas(aluno_id)

    Button(acoes_frame, text="Editar", command=lambda: editar_aluno_wrapper(aluno_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co4'], fg=colors['co0']).grid(row=0, column=0, padx=5, pady=5)

    Button(acoes_frame, text="Excluir", command=lambda: excluir_aluno_wrapper(aluno_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co8'], fg=colors['co0']).grid(row=0, column=1, padx=5, pady=5)

    Button(acoes_frame, text="Histórico", command=lambda: abrir_historico_wrapper(aluno_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co5'], fg=colors['co0']).grid(row=0, column=2, padx=5, pady=5)

    col = 3
    if tem_matricula_ativa or tem_historico:
        criar_menu_boletim(acoes_frame, aluno_id, anos_letivos, colors, col)
        col += 1

        if tem_matricula_ativa:
            Button(acoes_frame, text="Declaração", command=lambda: gerar_declaracao_wrapper(aluno_id),
                   width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co2'], fg=colors['co0']).grid(row=0, column=col, padx=5, pady=5)
            col += 1

            Button(acoes_frame, text="Editar Matrícula", command=lambda: editar_matricula_wrapper(aluno_id),
                   width=12, overrelief=RIDGE, font=('Ivy 9 bold'), bg=colors['co3'], fg=colors['co0']).grid(row=0, column=col, padx=5, pady=5)
        else:
            Button(acoes_frame, text="Matricular", command=lambda: matricular_aluno_wrapper(aluno_id),
                  width=10, overrelief=RIDGE, font=('Ivy 9 bold'), bg=colors['co3'], fg=colors['co0']).grid(row=0, column=col, padx=5, pady=5)
    else:
        Button(acoes_frame, text="Matricular", command=lambda: matricular_aluno_wrapper(aluno_id),
              width=10, overrelief=RIDGE, font=('Ivy 9 bold'), bg=colors['co3'], fg=colors['co0']).grid(row=0, column=col, padx=5, pady=5)


def criar_botoes_funcionario(acoes_frame: Frame, funcionario_id: int, colors: Dict[str, str]) -> None:
    """Cria botões específicos para funcionário."""
    Button(acoes_frame, text="Editar", command=lambda: editar_funcionario_wrapper(funcionario_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co4'], fg=colors['co0']).grid(row=0, column=0, padx=5, pady=5)

    Button(acoes_frame, text="Excluir", command=lambda: excluir_funcionario_wrapper(funcionario_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co8'], fg=colors['co0']).grid(row=0, column=1, padx=5, pady=5)

    Button(acoes_frame, text="Declaração", command=lambda: gerar_declaracao_funcionario_wrapper(funcionario_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co2'], fg=colors['co0']).grid(row=0, column=2, padx=5, pady=5)


# ---------------------------------------------------------------------------
# Wrappers de ação
# ---------------------------------------------------------------------------


def editar_aluno_wrapper(aluno_id):
    """Wrapper para editar aluno."""
    try:
        from src.interfaces.edicao_aluno import InterfaceEdicaoAluno
        import tkinter as tk
        root = _get_default_root()
        if root:
            janela_edicao = tk.Toplevel(root)
            InterfaceEdicaoAluno(janela_edicao, aluno_id, janela_principal=root)
    except Exception as e:
        logger.exception(f"Erro ao abrir edição de aluno: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir edição: {e}")


def excluir_aluno_wrapper(aluno_id):
    """Wrapper para excluir aluno."""
    try:
        from src.services.aluno_service import (
            excluir_aluno_com_confirmacao,
            obter_aluno_por_id,
            MatriculaAtivaError,
            AlunoIdInvalidoError,
            AlunoServiceError,
        )

        aluno = obter_aluno_por_id(aluno_id)
        nome_aluno = aluno.get('nome') if aluno else 'Aluno'

        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o aluno {nome_aluno}?\n\n"
            "Esta ação não pode ser desfeita."
        )
        if not resposta:
            return

        try:
            excluir_aluno_com_confirmacao(aluno_id, nome_aluno, confirmado=True)
            messagebox.showinfo("Sucesso", f"Aluno {nome_aluno} excluído com sucesso!")
        except MatriculaAtivaError as e:
            messagebox.showwarning("Aviso", str(e))
        except (AlunoIdInvalidoError, AlunoServiceError) as e:
            messagebox.showerror("Erro", str(e))
    except Exception as e:
        logger.exception(f"Erro ao excluir aluno: {e}")
        messagebox.showerror("Erro", f"Erro ao excluir: {e}")


def abrir_historico_wrapper(aluno_id):
    """Wrapper para abrir histórico do aluno."""
    try:
        from scripts.migracao.integrar_historico_escolar import abrir_historico_aluno
        root = _get_default_root()
        if root:
            abrir_historico_aluno(aluno_id, root)
    except Exception as e:
        logger.exception(f"Erro ao abrir histórico: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir histórico: {e}")


def gerar_declaracao_wrapper(aluno_id):
    """Wrapper para gerar declaração do aluno — abre diálogo de seleção."""
    try:
        import tkinter as tk
        from tkinter import StringVar, Toplevel, Label, OptionMenu, Entry, Button, Frame
        from src.ui.colors import get_colors_dict

        colors = get_colors_dict()
        co0 = colors.get('co0', '#2e2d2b')
        co2 = colors.get('co2', '#4fa882')
        co3 = colors.get('co3', '#e06636')
        co7 = colors.get('co7', '#FFFFFF')

        root = _get_default_root()
        if not root:
            messagebox.showerror("Erro", "Janela principal não encontrada.")
            return

        dialog = Toplevel(root)
        dialog.title("Tipo de Declaração")
        dialog.geometry("380x170")
        dialog.transient(root)
        dialog.focus_force()
        dialog.grab_set()
        dialog.configure(bg=co0)

        opcao = StringVar(dialog)
        opcao.set("Transferência")

        opcoes = ["Transferência", "Bolsa Família", "Trabalho", "Outros"]

        Label(dialog, text="Selecione o tipo de declaração:", font=("Ivy", 12), bg=co0, fg=co7).pack(pady=10)

        option_menu = OptionMenu(dialog, opcao, *opcoes)
        option_menu.config(bg=co0, fg=co7, font=("Ivy", 11))
        option_menu.pack(pady=5)

        motivo_frame = Frame(dialog, bg=co0)
        motivo_frame.pack(pady=5, fill='x', padx=20)

        Label(motivo_frame, text="Especifique o motivo:", font=("Ivy", 11), bg=co0, fg=co7).pack(anchor='w')
        motivo_entry = Entry(motivo_frame, width=40, font=("Ivy", 11))
        motivo_entry.pack(fill='x', pady=5)

        motivo_frame.pack_forget()

        def atualizar_interface(*args):
            if opcao.get() == "Outros":
                motivo_frame.pack(pady=5, fill='x', padx=20)
                dialog.geometry("380x270")
                motivo_entry.focus_set()
            else:
                motivo_frame.pack_forget()
                dialog.geometry("380x170")

        opcao.trace_add("write", atualizar_interface)

        def confirmar():
            opcao_selecionada = opcao.get()

            marcacoes = [[False, False, False, False]]
            if opcao_selecionada in opcoes:
                index = opcoes.index(opcao_selecionada)
                marcacoes[0][index] = True

            motivo_outros_texto = ""
            if opcao_selecionada == "Outros":
                motivo_outros_texto = motivo_entry.get().strip()
                if not motivo_outros_texto:
                    messagebox.showwarning("Aviso", "Por favor, especifique o motivo.")
                    return

            dialog.destroy()

            def _worker():
                from src.relatorios.declaracao_aluno import gerar_declaracao_aluno
                return gerar_declaracao_aluno(aluno_id, marcacoes, motivo_outros_texto)

            def _on_done(resultado):
                try:
                    messagebox.showinfo("Concluído", "Declaração gerada com sucesso.")
                except Exception:
                    pass

            from utils import executor

            def _on_error(exc):
                try:
                    messagebox.showerror("Erro", f"Falha ao gerar declaração: {exc}")
                except Exception:
                    pass

            executor.submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=root)

        btn_frame = Frame(dialog, bg=co0)
        btn_frame.pack(pady=10)

        Button(btn_frame, text="Confirmar", command=confirmar, bg=co2, fg=co0,
               font=("Ivy", 11, "bold"), relief=tk.RAISED, overrelief=tk.RIDGE).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="Cancelar", command=dialog.destroy, bg=co3, fg=co0,
               font=("Ivy", 11, "bold"), relief=tk.RAISED, overrelief=tk.RIDGE).pack(side=tk.LEFT, padx=5)

    except Exception as e:
        logger.exception(f"Erro ao abrir diálogo de declaração: {e}")
        messagebox.showerror("Erro", f"Erro ao gerar declaração: {e}")


def matricular_aluno_wrapper(aluno_id):
    """Wrapper para matricular aluno — abre MatriculaModal."""
    try:
        from src.ui.matricula_modal import MatriculaModal
        from src.ui.colors import get_colors_dict

        root = _get_default_root()

        if not root:
            logger.error("Janela principal não encontrada")
            messagebox.showerror("Erro", "Janela principal não encontrada.")
            return

        dados_aluno = _obter_aluno_por_id_service(aluno_id)
        if dados_aluno is None:
            logger.error(f"Aluno {aluno_id} não encontrado")
            messagebox.showerror("Erro", "Aluno não encontrado.")
            return

        nome_aluno = dados_aluno.get('nome', '') if isinstance(dados_aluno, dict) else dados_aluno[1]

        def ao_matricular_sucesso():
            try:
                logger.info(f"Aluno {nome_aluno} matriculado com sucesso")
                messagebox.showinfo("Sucesso", f"Aluno {nome_aluno} matriculado com sucesso!")
            except Exception as e:
                logger.exception(f"Erro no callback de sucesso: {e}")

        MatriculaModal(
            parent=root,
            aluno_id=aluno_id,
            nome_aluno=nome_aluno,
            colors=get_colors_dict(),
            callback_sucesso=ao_matricular_sucesso
        )

    except Exception as e:
        logger.exception(f"ERRO em matricular_aluno_wrapper: {e}")
        messagebox.showerror("Erro", f"Erro ao matricular: {e}")


def editar_matricula_wrapper(aluno_id):
    """Wrapper para editar matrícula do aluno usando interface unificada."""
    try:
        from src.interfaces.matricula_unificada import abrir_interface_matricula
        from src.ui.colors import get_colors_dict

        root = _get_default_root()

        if not root:
            logger.error("Janela principal não encontrada")
            messagebox.showerror("Erro", "Janela principal não encontrada.")
            return

        dados_aluno = _obter_aluno_por_id_service(aluno_id)
        if dados_aluno is None:
            logger.error(f"Aluno {aluno_id} não encontrado")
            messagebox.showerror("Erro", "Aluno não encontrado.")
            return

        nome_aluno = dados_aluno.get('nome', '') if isinstance(dados_aluno, dict) else dados_aluno[1]

        def ao_editar_sucesso():
            try:
                logger.info(f"Matrícula do aluno {nome_aluno} editada com sucesso")
            except Exception as e:
                logger.exception(f"Erro no callback de sucesso: {e}")

        abrir_interface_matricula(
            parent=root,
            aluno_id=aluno_id,
            nome_aluno=nome_aluno,
            colors=get_colors_dict(),
            callback_sucesso=ao_editar_sucesso
        )

    except Exception as e:
        logger.exception(f"ERRO em editar_matricula_wrapper: {e}")
        messagebox.showerror("Erro", f"Erro ao editar matrícula: {e}")


def editar_funcionario_wrapper(funcionario_id):
    """Wrapper para editar funcionário."""
    try:
        from src.interfaces.edicao_funcionario import InterfaceEdicaoFuncionario
        import tkinter as tk
        root = _get_default_root()
        if root:
            janela_edicao = tk.Toplevel(root)
            InterfaceEdicaoFuncionario(janela_edicao, funcionario_id, janela_principal=root)
    except Exception as e:
        logger.exception(f"Erro ao abrir edição de funcionário: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir edição: {e}")


def excluir_funcionario_wrapper(funcionario_id):
    """Wrapper para excluir funcionário."""
    try:
        from src.services.funcionario_service import excluir_funcionario
        resposta = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este funcionário?")
        if resposta:
            sucesso, mensagem = excluir_funcionario(funcionario_id, verificar_vinculos=True)
            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
            else:
                messagebox.showerror("Erro", mensagem)
    except Exception as e:
        logger.exception(f"Erro ao excluir funcionário: {e}")
        messagebox.showerror("Erro", f"Erro ao excluir: {e}")


def gerar_declaracao_funcionario_wrapper(funcionario_id):
    """Wrapper para gerar declaração do funcionário."""
    logger.warning("Geração de declaração de funcionário ainda não implementada")
    messagebox.showinfo("Aviso", "Geração de declaração de funcionário pendente de implementação.")
