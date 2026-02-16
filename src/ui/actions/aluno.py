"""Mixin de ações de aluno para o ActionHandler."""

from tkinter import messagebox, Toplevel
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class AlunoActionsMixin:
    """Métodos do ActionHandler relacionados a alunos (CRUD + busca)."""

    def cadastrar_novo_aluno(self):
        """Abre a interface de cadastro de novo aluno."""
        try:
            from src.interfaces.cadastro_aluno import InterfaceCadastroAluno

            janela_cadastro = Toplevel(self.app.janela)
            janela_cadastro.title("Cadastrar Novo Aluno")
            janela_cadastro.geometry('950x670')
            janela_cadastro.configure(background=self.app.colors['co1'])
            janela_cadastro.focus_set()
            janela_cadastro.grab_set()

            self.app.janela.withdraw()

            app_cadastro = InterfaceCadastroAluno(janela_cadastro, janela_principal=self.app.janela)

            def ao_fechar_cadastro():
                self.app.janela.deiconify()
                if self.app.table_manager:
                    self._atualizar_tabela()
                janela_cadastro.destroy()

            janela_cadastro.protocol("WM_DELETE_WINDOW", ao_fechar_cadastro)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir cadastro: {str(e)}")
            self.logger.error(f"Erro ao abrir cadastro: {str(e)}")
            self.app.janela.deiconify()

    def editar_aluno(self):
        """Abre a interface de edição do aluno selecionado usando modal."""
        from src.ui.aluno_modal import abrir_aluno_modal

        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return

            item_selecionado = self.app.table_manager.get_selected_item()

            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um aluno para editar")
                return

            aluno_id = item_selecionado[0]

            abrir_aluno_modal(
                parent=self.app.janela,
                aluno_id=aluno_id,
                colors=self.app.cores,
                callback_sucesso=self._atualizar_tabela
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir edição: {str(e)}")
            self.logger.error(f"Erro ao abrir edição: {str(e)}")
            self.app.janela.deiconify()

    def excluir_aluno(self, callback_sucesso: Optional[Callable] = None):
        """Exclui o aluno selecionado após confirmação."""
        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return

            item_selecionado = self.app.table_manager.get_selected_item()

            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um aluno para excluir")
                return

            aluno_id = item_selecionado[0]
            nome_aluno = item_selecionado[1] if len(item_selecionado) > 1 else "Desconhecido"

            from src.services.aluno_service import (
                excluir_aluno_com_confirmacao,
                MatriculaAtivaError,
                AlunoIdInvalidoError,
                AlunoServiceError,
            )

            resposta = messagebox.askyesno(
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir o aluno {nome_aluno}?\n\n"
                "Esta ação não pode ser desfeita."
            )
            if not resposta:
                return

            try:
                excluir_aluno_com_confirmacao(
                    aluno_id,
                    nome_aluno,
                    callback_sucesso=callback_sucesso or self._atualizar_tabela,
                    confirmado=True,
                )
                messagebox.showinfo("Sucesso", f"Aluno {nome_aluno} excluído com sucesso!")
                if self.app.table_manager:
                    self._atualizar_tabela()
            except MatriculaAtivaError as e:
                messagebox.showwarning("Aviso", str(e))
            except (AlunoIdInvalidoError, AlunoServiceError) as e:
                messagebox.showerror("Erro", str(e))

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir aluno: {str(e)}")
            self.logger.error(f"Erro ao excluir aluno: {str(e)}")

    def buscar_aluno(self, termo: str):
        """Busca alunos usando o serviço e atualiza tabela."""
        try:
            from src.services.aluno_service import buscar_alunos

            if not termo or not termo.strip():
                self._atualizar_tabela()
                return

            resultados = buscar_alunos(termo)

            if self.app.table_manager:
                self.app.table_manager.atualizar_dados(resultados)
                self.logger.info(f"Busca por '{termo}' retornou {len(resultados)} resultado(s)")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar: {str(e)}")
            self.logger.exception(f"Erro ao buscar aluno: {e}")

    def listar_alunos_ativos(self):
        """Lista alunos com matrícula ativa na tabela."""
        try:
            from src.services.aluno_service import listar_alunos_ativos

            alunos = listar_alunos_ativos()

            if self.app.table_manager:
                self.app.table_manager.atualizar_dados(alunos)
                self.logger.info(f"Listados {len(alunos)} aluno(s) ativo(s)")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao listar alunos: {str(e)}")
            self.logger.exception(f"Erro ao listar alunos ativos: {e}")

    def ver_detalhes_aluno(self):
        """Mostra detalhes do aluno selecionado em um frame lateral."""
        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return

            item_selecionado = self.app.table_manager.get_selected_item()

            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um aluno para ver detalhes")
                return

            # TODO: Implementar exibição de detalhes no frame lateral
            aluno_id = item_selecionado[0]
            self.logger.info(f"Visualizando detalhes do aluno ID: {aluno_id}")
            messagebox.showinfo("Info", f"Detalhes do aluno ID {aluno_id} - Implementação pendente")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir detalhes: {str(e)}")
            self.logger.error(f"Erro ao exibir detalhes: {str(e)}")
