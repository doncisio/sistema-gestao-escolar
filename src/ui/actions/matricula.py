"""Mixin de ações de matrícula para o ActionHandler."""

from tkinter import messagebox, Toplevel, Label, Frame, Button
import logging

logger = logging.getLogger(__name__)


class MatriculaActionsMixin:
    """Métodos do ActionHandler relacionados a matrícula."""

    def matricular_aluno_modal(self):
        """Abre modal para matricular aluno selecionado (inline com série+turma)."""
        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return

            item_selecionado = self.app.table_manager.get_selected_item()

            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um aluno para matricular")
                return

            aluno_id = item_selecionado[0]
            nome_aluno = item_selecionado[1] if len(item_selecionado) > 1 else "Aluno"

            from src.services.matricula_service import (
                obter_ano_letivo_atual,
                verificar_matricula_existente,
                obter_series_disponiveis,
                obter_turmas_por_serie,
                matricular_aluno
            )
            from tkinter import ttk

            ano_letivo_id = obter_ano_letivo_atual()
            if not ano_letivo_id:
                messagebox.showerror("Erro", "Ano letivo atual não encontrado")
                return

            matricula_existente = verificar_matricula_existente(aluno_id, ano_letivo_id)
            if matricula_existente and matricula_existente.get('status') == 'Ativo':
                messagebox.showwarning(
                    "Aviso",
                    f"Aluno já possui matrícula ativa:\n"
                    f"Série: {matricula_existente.get('serie')}\n"
                    f"Turma: {matricula_existente.get('turma')}"
                )
                return

            janela_matricula = Toplevel(self.app.janela)
            janela_matricula.title(f"Matricular Aluno - {nome_aluno}")
            janela_matricula.geometry('400x250')
            janela_matricula.configure(bg=self.app.colors['co1'])
            janela_matricula.transient(self.app.janela)
            janela_matricula.grab_set()

            frame = Frame(janela_matricula, bg=self.app.colors['co1'], padx=20, pady=20)
            frame.pack(fill='both', expand=True)

            Label(frame, text=f"Aluno: {nome_aluno}", bg=self.app.colors['co1'],
                  font=("Arial", 11, "bold")).pack(anchor='w', pady=(0, 15))

            Label(frame, text="Série:", bg=self.app.colors['co1']).pack(anchor='w')
            series = obter_series_disponiveis()
            serie_var = ttk.Combobox(frame, state="readonly", width=30)
            serie_var['values'] = [s['nome'] for s in series]
            serie_var.pack(pady=(5, 15))

            Label(frame, text="Turma:", bg=self.app.colors['co1']).pack(anchor='w')
            turma_var = ttk.Combobox(frame, state="readonly", width=30)
            turma_var.pack(pady=(5, 20))

            def atualizar_turmas(event=None):
                if not serie_var.get():
                    return
                serie_nome = serie_var.get()
                serie_id = next((s['id'] for s in series if s['nome'] == serie_nome), None)
                if serie_id:
                    turmas = obter_turmas_por_serie(serie_id, ano_letivo_id)
                    turma_var['values'] = [t['nome'] for t in turmas]
                    setattr(turma_var, '_turmas_data', turmas)
                else:
                    turma_var['values'] = []

            serie_var.bind('<<ComboboxSelected>>', atualizar_turmas)

            frame_botoes = Frame(frame, bg=self.app.colors['co1'])
            frame_botoes.pack(pady=(10, 0))

            def confirmar_matricula():
                if not serie_var.get() or not turma_var.get():
                    messagebox.showwarning("Aviso", "Selecione série e turma")
                    return

                turma_nome = turma_var.get()
                turmas_data = getattr(turma_var, '_turmas_data', [])
                turma_id = next((t['id'] for t in turmas_data if t['nome'] == turma_nome), None)

                if not turma_id:
                    messagebox.showerror("Erro", "Turma não encontrada")
                    return

                sucesso, mensagem = matricular_aluno(aluno_id, turma_id, ano_letivo_id)

                if sucesso:
                    messagebox.showinfo("Sucesso", mensagem)
                    janela_matricula.destroy()
                    self._atualizar_tabela()
                else:
                    messagebox.showerror("Erro", mensagem)

            Button(frame_botoes, text="Matricular", command=confirmar_matricula,
                   bg=self.app.colors['co2'], fg=self.app.colors['co1'],
                   font=("Arial", 10, "bold"), width=12).pack(side='left', padx=5)

            Button(frame_botoes, text="Cancelar", command=janela_matricula.destroy,
                   bg=self.app.colors['co7'], fg=self.app.colors['co1'],
                   font=("Arial", 10), width=12).pack(side='left', padx=5)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir matrícula: {str(e)}")
            self.logger.exception(f"Erro ao matricular aluno: {e}")

    def _matricular_aluno(self, aluno_id: int):
        """Matricula aluno usando MatriculaModal (callback do DetalhesManager)."""
        from src.ui.matricula_modal import abrir_matricula_modal
        from src.services.aluno_service import obter_aluno_por_id

        try:
            aluno = obter_aluno_por_id(aluno_id)
            if not aluno:
                messagebox.showerror("Erro", "Aluno não encontrado")
                return

            nome_aluno = aluno.get('nome', 'Desconhecido')

            abrir_matricula_modal(
                parent=self.app.janela,
                aluno_id=aluno_id,
                nome_aluno=nome_aluno,
                colors=self.app.colors,
                callback_sucesso=self._atualizar_tabela
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir matrícula: {str(e)}")
            self.logger.exception(f"Erro ao matricular aluno: {e}")

    def _editar_matricula(self, aluno_id: int):
        """Edita matrícula do aluno usando MatriculaModal (callback do DetalhesManager)."""
        from src.ui.matricula_modal import abrir_matricula_modal
        from src.services.aluno_service import obter_aluno_por_id

        try:
            aluno = obter_aluno_por_id(aluno_id)
            if not aluno:
                messagebox.showerror("Erro", "Aluno não encontrado")
                return

            nome_aluno = aluno.get('nome', 'Desconhecido')

            abrir_matricula_modal(
                parent=self.app.janela,
                aluno_id=aluno_id,
                nome_aluno=nome_aluno,
                colors=self.app.colors,
                callback_sucesso=self._atualizar_tabela
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao editar matrícula: {str(e)}")
            self.logger.exception(f"Erro ao editar matrícula: {e}")
