"""Mixin de geração de relatórios/documentos para o ActionHandler."""

from tkinter import messagebox, Toplevel, Label, Frame, Button, StringVar, OptionMenu, Entry
import logging

logger = logging.getLogger(__name__)


class RelatorioActionsMixin:
    """Métodos do ActionHandler relacionados a geração de documentos."""

    def _gerar_historico(self, aluno_id: int):
        """Gera histórico escolar do aluno."""
        from src.relatorios.historico_escolar import historico_escolar

        try:
            def _worker():
                return historico_escolar(aluno_id)

            def _on_done(resultado):
                if resultado:
                    messagebox.showinfo("Concluído", "Histórico escolar gerado com sucesso.")
                else:
                    messagebox.showwarning("Aviso", "Nenhum dado disponível para o histórico.")

            def _on_error(exc):
                messagebox.showerror("Erro", f"Falha ao gerar histórico: {exc}")

            try:
                from src.utils.executor import submit_background
                submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=self.app.janela)
            except Exception:
                from threading import Thread
                def _thread_worker():
                    try:
                        res = _worker()
                        self.app.janela.after(0, lambda: _on_done(res))
                    except Exception as e:
                        self.app.janela.after(0, lambda: _on_error(e))
                Thread(target=_thread_worker, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar histórico: {str(e)}")
            self.logger.exception(f"Erro ao gerar histórico: {e}")

    def _gerar_boletim(self, aluno_id: int):
        """Gera boletim do aluno usando boletim_service."""
        from src.services.boletim_service import gerar_boletim_ou_transferencia

        try:
            def _worker():
                return gerar_boletim_ou_transferencia(aluno_id)

            def _on_done(resultado):
                sucesso, mensagem = resultado
                if sucesso:
                    messagebox.showinfo("Concluído", mensagem)
                else:
                    messagebox.showwarning("Aviso", mensagem)

            def _on_error(exc):
                messagebox.showerror("Erro", f"Falha ao gerar documento: {exc}")

            try:
                from src.utils.executor import submit_background
                submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=self.app.janela)
            except Exception:
                from threading import Thread
                def _thread_worker():
                    try:
                        res = _worker()
                        self.app.janela.after(0, lambda: _on_done(res))
                    except Exception as e:
                        self.app.janela.after(0, lambda: _on_error(e))
                Thread(target=_thread_worker, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar boletim: {str(e)}")
            self.logger.exception(f"Erro ao gerar boletim: {e}")

    def _gerar_declaracao_aluno(self, aluno_id: int):
        """Gera declaração para aluno — local (PDF) ou via GEduc (autenticado)."""
        from src.services.declaracao_service import (
            obter_dados_aluno_para_declaracao,
            validar_dados_declaracao,
            registrar_geracao_declaracao
        )
        from src.relatorios.declaracao_aluno import gerar_declaracao_aluno as gerar_declaracao_aluno_legacy

        try:
            dialog = Toplevel(self.app.janela)
            dialog.title("Tipo de Declaração")
            dialog.geometry("420x260")
            dialog.resizable(False, False)
            dialog.transient(self.app.janela)
            dialog.focus_force()
            dialog.grab_set()
            dialog.configure(bg=self.app.colors['co0'])

            opcao = StringVar(dialog)
            opcao.set("Bolsa Família")
            # "Transferência" não é suportada pelo gerador GEduc automatizado
            opcoes = ["Transferência", "Bolsa Família", "Trabalho", "Outros"]

            Label(dialog, text="Selecione o tipo de declaração:", font=("Ivy", 12),
                  bg=self.app.colors['co0'], fg=self.app.colors['co7']).pack(pady=(14, 4))

            option_menu = OptionMenu(dialog, opcao, *opcoes)
            option_menu.config(bg=self.app.colors['co0'], fg=self.app.colors['co7'], width=22)
            option_menu.pack(pady=4)

            motivo_frame = Frame(dialog, bg=self.app.colors['co0'])
            Label(motivo_frame, text="Especifique o motivo:", font=("Ivy", 11),
                  bg=self.app.colors['co0'], fg=self.app.colors['co7']).pack(anchor='w')
            motivo_entry = Entry(motivo_frame, width=40, font=("Ivy", 11))
            motivo_entry.pack(fill='x', pady=4)

            btn_geduc_ref: list = []

            def atualizar_interface(*args):
                selecionado = opcao.get()
                if selecionado == "Outros":
                    motivo_frame.pack(pady=4, fill='x', padx=20)
                    dialog.geometry("420x310")
                    motivo_entry.focus_set()
                else:
                    motivo_frame.pack_forget()
                    dialog.geometry("420x260")
                if btn_geduc_ref:
                    state = "disabled" if selecionado == "Transferência" else "normal"
                    btn_geduc_ref[0].config(state=state)

            opcao.trace_add("write", atualizar_interface)

            def _validar_e_obter_dados():
                opcao_selecionada = opcao.get()
                motivo_outros = ""
                if opcao_selecionada == "Outros":
                    motivo_outros = motivo_entry.get().strip()
                    if not motivo_outros:
                        messagebox.showwarning("Aviso", "Por favor, especifique o motivo.")
                        return None
                dados_aluno = obter_dados_aluno_para_declaracao(aluno_id)
                if not dados_aluno:
                    messagebox.showerror("Erro", "Não foi possível obter dados do aluno.")
                    dialog.destroy()
                    return None
                valido, mensagem = validar_dados_declaracao('Aluno', dados_aluno, opcao_selecionada)
                if not valido:
                    messagebox.showwarning("Aviso", mensagem)
                    dialog.destroy()
                    return None
                return opcao_selecionada, motivo_outros

            # ── Gerar Local (PDF) ─────────────────────────────────────────
            def gerar_local():
                resultado = _validar_e_obter_dados()
                if resultado is None:
                    return
                opcao_selecionada, motivo_outros = resultado
                dialog.destroy()

                marcacoes = [[False] * 4 for _ in range(1)]
                if opcao_selecionada in opcoes:
                    marcacoes[0][opcoes.index(opcao_selecionada)] = True

                def _worker():
                    res = gerar_declaracao_aluno_legacy(aluno_id, marcacoes, motivo_outros)
                    registrar_geracao_declaracao(
                        pessoa_id=aluno_id,
                        tipo_pessoa='Aluno',
                        tipo_declaracao=opcao_selecionada,
                        motivo_outros=motivo_outros if opcao_selecionada == 'Outros' else None
                    )
                    return res

                def _on_done(_res):
                    messagebox.showinfo("Concluído", "Declaração gerada com sucesso.")

                def _on_error(exc):
                    messagebox.showerror("Erro", f"Falha ao gerar declaração: {exc}")

                try:
                    from src.utils.executor import submit_background
                    submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=self.app.janela)
                except Exception:
                    from threading import Thread
                    def _t():
                        try:
                            r = _worker()
                            self.app.janela.after(0, lambda: _on_done(r))
                        except Exception as e:
                            self.app.janela.after(0, lambda: _on_error(e))
                    Thread(target=_t, daemon=True).start()

            # ── Pedir credenciais GEduc ───────────────────────────────────
            def _pedir_credenciais_geduc():
                """Abre diálogo pedindo usuário/senha do GEduc. Retorna (user, senha) ou None."""
                from src.core.config import GEDUC_DEFAULT_USER, GEDUC_DEFAULT_PASS
                import os

                usuario_salvo = os.environ.get("GEDUC_USER", GEDUC_DEFAULT_USER)
                senha_salva = os.environ.get("GEDUC_PASS", GEDUC_DEFAULT_PASS)

                cred_dialog = Toplevel(self.app.janela)
                cred_dialog.title("Credenciais do GEduc")
                cred_dialog.geometry("340x220")
                cred_dialog.resizable(False, False)
                cred_dialog.transient(self.app.janela)
                cred_dialog.grab_set()
                cred_dialog.focus_force()
                cred_dialog.configure(bg=self.app.colors['co0'])

                Label(cred_dialog, text="Login do GEduc",
                      font=("Ivy", 12, "bold"),
                      bg=self.app.colors['co0'],
                      fg=self.app.colors['co7']).pack(pady=(14, 8))

                frame_campos = Frame(cred_dialog, bg=self.app.colors['co0'])
                frame_campos.pack(padx=20, fill='x')

                Label(frame_campos, text="Usuário:", font=("Ivy", 11),
                      bg=self.app.colors['co0'], fg=self.app.colors['co7']).grid(row=0, column=0, sticky='w', pady=4)
                entry_user = Entry(frame_campos, font=("Ivy", 11), width=24)
                entry_user.insert(0, usuario_salvo)
                entry_user.grid(row=0, column=1, pady=4, padx=(8, 0))

                Label(frame_campos, text="Senha:", font=("Ivy", 11),
                      bg=self.app.colors['co0'], fg=self.app.colors['co7']).grid(row=1, column=0, sticky='w', pady=4)
                entry_pass = Entry(frame_campos, font=("Ivy", 11), width=24, show="*")
                entry_pass.insert(0, senha_salva)
                entry_pass.grid(row=1, column=1, pady=4, padx=(8, 0))

                resultado_cred: list = [None]

                def confirmar_cred():
                    u = entry_user.get().strip()
                    p = entry_pass.get().strip()
                    if not u or not p:
                        messagebox.showwarning("Aviso", "Preencha usuário e senha.", parent=cred_dialog)
                        return
                    resultado_cred[0] = (u, p)
                    cred_dialog.destroy()

                def cancelar_cred():
                    cred_dialog.destroy()

                entry_user.bind("<Return>", lambda _: entry_pass.focus_set())
                entry_pass.bind("<Return>", lambda _: confirmar_cred())

                btn_frame_cred = Frame(cred_dialog, bg=self.app.colors['co0'])
                btn_frame_cred.pack(pady=14)
                Button(btn_frame_cred, text="Entrar", command=confirmar_cred,
                       bg=self.app.colors['co2'], fg=self.app.colors['co0'],
                       font=("Ivy", 11), width=10).pack(side='left', padx=6)
                Button(btn_frame_cred, text="Cancelar", command=cancelar_cred,
                       bg=self.app.colors['co0'], fg=self.app.colors['co7'],
                       font=("Ivy", 11), width=10).pack(side='left', padx=6)

                cred_dialog.wait_window()
                return resultado_cred[0]

            # ── Gerar no GEduc (autenticado) ──────────────────────────────
            def gerar_geduc():
                resultado = _validar_e_obter_dados()
                if resultado is None:
                    return
                opcao_selecionada, motivo_outros = resultado

                credenciais = _pedir_credenciais_geduc()
                if credenciais is None:
                    return
                usuario_geduc, senha_geduc = credenciais

                dialog.destroy()

                def _worker_geduc():
                    from src.importadores.geduc import AutomacaoGEDUC
                    automacao = AutomacaoGEDUC(headless=False)
                    try:
                        if not automacao.iniciar_navegador():
                            return False
                        if not automacao.fazer_login(usuario_geduc, senha_geduc):
                            return False
                        sucesso = automacao.gerar_declaracao(
                            aluno_id=aluno_id,
                            tipo_declaracao=opcao_selecionada,
                            motivo_outros=motivo_outros,
                        )
                        if sucesso:
                            registrar_geracao_declaracao(
                                pessoa_id=aluno_id,
                                tipo_pessoa='Aluno',
                                tipo_declaracao=opcao_selecionada,
                                motivo_outros=motivo_outros if opcao_selecionada == 'Outros' else None
                            )
                        return sucesso
                    finally:
                        pass  # Não fecha o navegador — usuário salva/imprime o PDF

                def _on_done_geduc(sucesso):
                    if sucesso:
                        messagebox.showinfo(
                            "GEduc",
                            "Declaração gerada no GEduc com sucesso!\n"
                            "O PDF autenticado está disponível no navegador."
                        )
                    else:
                        messagebox.showerror(
                            "GEduc",
                            "Não foi possível gerar a declaração no GEduc.\n"
                            "Verifique o navegador e os logs para detalhes."
                        )

                def _on_error_geduc(exc):
                    messagebox.showerror("Erro GEduc", f"Falha na automação do GEduc:\n{exc}")

                try:
                    from src.utils.executor import submit_background
                    submit_background(
                        _worker_geduc,
                        on_done=_on_done_geduc,
                        on_error=_on_error_geduc,
                        janela=self.app.janela
                    )
                except Exception:
                    from threading import Thread
                    def _t():
                        try:
                            r = _worker_geduc()
                            self.app.janela.after(0, lambda: _on_done_geduc(r))
                        except Exception as e:
                            self.app.janela.after(0, lambda: _on_error_geduc(e))
                    Thread(target=_t, daemon=True).start()

            # ── Botões ────────────────────────────────────────────────────
            btn_frame = Frame(dialog, bg=self.app.colors['co0'])
            btn_frame.pack(pady=16)

            Button(
                btn_frame,
                text="Gerar Local (PDF)",
                command=gerar_local,
                bg=self.app.colors['co2'],
                fg=self.app.colors['co0'],
                font=("Ivy", 11),
                width=18,
            ).grid(row=0, column=0, padx=8)

            btn_geduc = Button(
                btn_frame,
                text="Gerar no GEduc",
                command=gerar_geduc,
                bg='#1565C0',
                fg='white',
                font=("Ivy", 11),
                width=18,
                state="normal",
            )
            btn_geduc.grid(row=0, column=1, padx=8)
            btn_geduc_ref.append(btn_geduc)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir diálogo de declaração: {str(e)}")
            self.logger.exception(f"Erro ao gerar declaração de aluno: {e}")

    def _gerar_declaracao_funcionario(self, funcionario_id: int):
        """Gera declaração para funcionário usando declaracao_service."""
        from src.services.declaracao_service import (
            obter_dados_funcionario_para_declaracao,
            validar_dados_declaracao,
            registrar_geracao_declaracao
        )

        try:
            dados_funcionario = obter_dados_funcionario_para_declaracao(funcionario_id)
            if not dados_funcionario:
                messagebox.showerror("Erro", "Não foi possível obter dados do funcionário.")
                return

            valido, mensagem = validar_dados_declaracao('Funcionário', dados_funcionario, 'Trabalho')
            if not valido:
                messagebox.showwarning("Aviso", mensagem)
                return

            def _worker():
                self.logger.warning("Geração de declaração de funcionário ainda não implementada")
                registrar_geracao_declaracao(
                    pessoa_id=funcionario_id,
                    tipo_pessoa='Funcionário',
                    tipo_declaracao='Trabalho',
                    motivo_outros=None
                )
                return None

            def _on_done(resultado):
                messagebox.showinfo("Aviso", "Geração de declaração de funcionário pendente de implementação.")

            def _on_error(exc):
                messagebox.showerror("Erro", f"Falha ao gerar declaração: {exc}")

            try:
                from src.utils.executor import submit_background
                submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=self.app.janela)
            except Exception:
                from threading import Thread
                def _thread_worker():
                    try:
                        res = _worker()
                        self.app.janela.after(0, lambda: _on_done(res))
                    except Exception as e:
                        self.app.janela.after(0, lambda: _on_error(e))
                Thread(target=_thread_worker, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar declaração: {str(e)}")
            self.logger.exception(f"Erro ao gerar declaração de funcionário: {e}")
