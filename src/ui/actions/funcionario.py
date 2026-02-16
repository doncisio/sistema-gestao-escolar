"""Mixin de ações de funcionário para o ActionHandler."""

from tkinter import messagebox, Toplevel
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FuncionarioActionsMixin:
    """Métodos do ActionHandler relacionados a funcionários (CRUD + busca)."""

    def cadastrar_novo_funcionario(self):
        """Abre a interface de cadastro de novo funcionário."""
        try:
            from src.interfaces.cadastro_funcionario import InterfaceCadastroFuncionario

            janela_cadastro = Toplevel(self.app.janela)
            janela_cadastro.title("Cadastrar Novo Funcionário")
            janela_cadastro.geometry('950x670')
            janela_cadastro.configure(background=self.app.colors['co1'])
            janela_cadastro.focus_set()
            janela_cadastro.grab_set()

            self.app.janela.withdraw()

            app_cadastro = InterfaceCadastroFuncionario(janela_cadastro, janela_principal=self.app.janela)

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

    def editar_funcionario(self):
        """Abre a interface de edição do funcionário selecionado usando modal."""
        from src.ui.funcionario_modal import abrir_funcionario_modal

        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return

            item_selecionado = self.app.table_manager.get_selected_item()

            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para editar")
                return

            funcionario_id = item_selecionado[0]

            abrir_funcionario_modal(
                parent=self.app.janela,
                funcionario_id=funcionario_id,
                colors=self.app.cores,
                callback_sucesso=self._atualizar_tabela
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir edição: {str(e)}")
            self.logger.error(f"Erro ao abrir edição de funcionário: {str(e)}")
            self.app.janela.deiconify()

    def buscar_funcionario(self, termo: str):
        """Busca funcionários usando o serviço."""
        try:
            from src.services.funcionario_service import buscar_funcionario

            if not termo or not termo.strip():
                self.listar_funcionarios()
                return

            resultados = buscar_funcionario(termo)

            if self.app.table_manager:
                self.app.table_manager.atualizar_dados(resultados)
                self.logger.info(f"Busca funcionário por '{termo}' retornou {len(resultados)} resultado(s)")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar funcionário: {str(e)}")
            self.logger.exception(f"Erro ao buscar funcionário: {e}")

    def listar_funcionarios(self, cargo: Optional[str] = None):
        """Lista funcionários na tabela."""
        try:
            from src.services.funcionario_service import listar_funcionarios

            funcionarios = listar_funcionarios(cargo=cargo)

            if self.app.table_manager:
                self.app.table_manager.atualizar_dados(funcionarios)
                self.logger.info(f"Listados {len(funcionarios)} funcionário(s)")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao listar funcionários: {str(e)}")
            self.logger.exception(f"Erro ao listar funcionários: {e}")

    def excluir_funcionario(self):
        """Exclui funcionário selecionado (versão pública) após confirmação."""
        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return

            item_selecionado = self.app.table_manager.get_selected_item()

            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para excluir")
                return

            funcionario_id = item_selecionado[0]
            nome = item_selecionado[1] if len(item_selecionado) > 1 else "Funcionário"

            resposta = messagebox.askyesno(
                "Confirmar Exclusão",
                f"Deseja realmente excluir o funcionário:\n\n{nome}?\n\n"
                "Esta ação não pode ser desfeita."
            )

            if not resposta:
                return

            from src.services.funcionario_service import excluir_funcionario

            sucesso, mensagem = excluir_funcionario(funcionario_id, verificar_vinculos=True)

            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
                self._atualizar_tabela()
            else:
                messagebox.showerror("Erro", mensagem)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir funcionário: {str(e)}")
            self.logger.exception(f"Erro ao excluir funcionário: {e}")

    def _excluir_funcionario(self):
        """Exclui funcionário selecionado (callback interno do DetalhesManager)."""
        from src.services.funcionario_service import excluir_funcionario, obter_funcionario_por_id

        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return

            item_selecionado = self.app.table_manager.get_selected_item()

            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para excluir")
                return

            funcionario_id = item_selecionado[0]

            funcionario = obter_funcionario_por_id(funcionario_id)
            if not funcionario:
                messagebox.showerror("Erro", "Funcionário não encontrado")
                return

            nome_funcionario = funcionario.get('nome', 'Desconhecido')

            resposta = messagebox.askyesno(
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir o funcionário '{nome_funcionario}'?\n\n"
                f"Esta ação não pode ser desfeita.",
                icon='warning'
            )

            if not resposta:
                return

            sucesso, mensagem = excluir_funcionario(funcionario_id, verificar_vinculos=True)

            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
                self._atualizar_tabela()
            else:
                messagebox.showerror("Erro", mensagem)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir funcionário: {str(e)}")
            self.logger.exception(f"Erro ao excluir funcionário: {e}")
