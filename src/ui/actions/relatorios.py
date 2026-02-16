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
        """Gera declaração para aluno usando declaracao_service."""
        from src.services.declaracao_service import (
            obter_dados_aluno_para_declaracao,
            validar_dados_declaracao,
            registrar_geracao_declaracao
        )
        from src.relatorios.declaracao_aluno import gerar_declaracao_aluno as gerar_declaracao_aluno_legacy

        try:
            dialog = Toplevel(self.app.janela)
            dialog.title("Tipo de Declaração")
            dialog.geometry("380x220")
            dialog.transient(self.app.janela)
            dialog.focus_force()
            dialog.grab_set()
            dialog.configure(bg=self.app.colors['co0'])

            opcao = StringVar(dialog)
            opcao.set("Transferência")
            opcoes = ["Transferência", "Bolsa Família", "Trabalho", "Outros"]

            Label(dialog, text="Selecione o tipo de declaração:", font=("Ivy", 12),
                  bg=self.app.colors['co0'], fg=self.app.colors['co7']).pack(pady=10)

            option_menu = OptionMenu(dialog, opcao, *opcoes)
            option_menu.config(bg=self.app.colors['co0'], fg=self.app.colors['co7'])
            option_menu.pack(pady=5)

            motivo_frame = Frame(dialog, bg=self.app.colors['co0'])
            motivo_frame.pack(pady=5, fill='x', padx=20)
            Label(motivo_frame, text="Especifique o motivo:", font=("Ivy", 11),
                  bg=self.app.colors['co0'], fg=self.app.colors['co7']).pack(anchor='w')
            motivo_entry = Entry(motivo_frame, width=40, font=("Ivy", 11))
            motivo_entry.pack(fill='x', pady=5)
            motivo_frame.pack_forget()

            def atualizar_interface(*args):
                if opcao.get() == "Outros":
                    motivo_frame.pack(pady=5, fill='x', padx=20)
                    dialog.geometry("380px220")
                    motivo_entry.focus_set()
                else:
                    motivo_frame.pack_forget()
                    dialog.geometry("380x170")

            opcao.trace_add("write", atualizar_interface)

            def confirmar():
                opcao_selecionada = opcao.get()
                motivo_outros = ""

                if opcao_selecionada == "Outros":
                    motivo_outros = motivo_entry.get().strip()
                    if not motivo_outros:
                        messagebox.showwarning("Aviso", "Por favor, especifique o motivo.")
                        return

                dados_aluno = obter_dados_aluno_para_declaracao(aluno_id)
                if not dados_aluno:
                    messagebox.showerror("Erro", "Não foi possível obter dados do aluno.")
                    dialog.destroy()
                    return

                valido, mensagem = validar_dados_declaracao('Aluno', dados_aluno, opcao_selecionada)
                if not valido:
                    messagebox.showwarning("Aviso", mensagem)
                    dialog.destroy()
                    return

                dialog.destroy()

                marcacoes = [[False] * 4 for _ in range(1)]
                if opcao_selecionada in opcoes:
                    index = opcoes.index(opcao_selecionada)
                    marcacoes[0][index] = True

                def _worker():
                    resultado = gerar_declaracao_aluno_legacy(aluno_id, marcacoes, motivo_outros)
                    registrar_geracao_declaracao(
                        pessoa_id=aluno_id,
                        tipo_pessoa='Aluno',
                        tipo_declaracao=opcao_selecionada,
                        motivo_outros=motivo_outros if opcao_selecionada == 'Outros' else None
                    )
                    return resultado

                def _on_done(resultado):
                    messagebox.showinfo("Concluído", "Declaração gerada com sucesso.")

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

            Button(dialog, text="Confirmar", command=confirmar,
                   bg=self.app.colors['co2'], fg=self.app.colors['co0']).pack(pady=10)

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
