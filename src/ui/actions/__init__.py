"""
Módulo de handlers de ações da interface.
Encapsula a lógica de ações do usuário (botões, menus, etc.) do main.py.

Pacote dividido em:
  aluno        – CRUD e busca de alunos
  funcionario  – CRUD e busca de funcionários
  matricula    – matrícula / edição de matrícula
  relatorios   – geração de históricos, boletins, declarações
  navegacao    – abertura de interfaces secundárias
"""

from tkinter import messagebox
import logging

from src.ui.actions.aluno import AlunoActionsMixin
from src.ui.actions.funcionario import FuncionarioActionsMixin
from src.ui.actions.matricula import MatriculaActionsMixin
from src.ui.actions.relatorios import RelatorioActionsMixin
from src.ui.actions.navegacao import NavegacaoActionsMixin

logger = logging.getLogger(__name__)


class ActionHandler(
    AlunoActionsMixin,
    FuncionarioActionsMixin,
    MatriculaActionsMixin,
    RelatorioActionsMixin,
    NavegacaoActionsMixin,
):
    """
    Gerenciador de ações da interface principal.
    Encapsula handlers para botões e eventos do usuário.
    """

    def __init__(self, app):
        """
        Inicializa o handler de ações.

        Args:
            app: Instância da Application com acesso a janela, colors, table_manager, etc.
        """
        self.app = app
        self.logger = logger
        self.detalhes_manager = None
        self._configurar_detalhes_manager()

    # ------------------------------------------------------------------
    # Infraestrutura (mantida aqui por ser o ponto de entrada)
    # ------------------------------------------------------------------

    def _configurar_detalhes_manager(self):
        """Configura o gerenciador de detalhes se o frame existir."""
        try:
            if hasattr(self.app, 'frame_detalhes') and self.app.frame_detalhes:
                from src.ui.detalhes import DetalhesManager

                callbacks = {
                    'editar_aluno': self.editar_aluno,
                    'excluir_aluno': self.excluir_aluno,
                    'editar_funcionario': self.editar_funcionario,
                    'excluir_funcionario': lambda: self._excluir_funcionario(),
                    'gerar_historico': lambda aluno_id: self._gerar_historico(aluno_id),
                    'gerar_boletim': lambda aluno_id: self._gerar_boletim(aluno_id),
                    'gerar_declaracao_aluno': lambda aluno_id: self._gerar_declaracao_aluno(aluno_id),
                    'gerar_declaracao_funcionario': lambda funcionario_id: self._gerar_declaracao_funcionario(funcionario_id),
                    'matricular_aluno': lambda aluno_id: self._matricular_aluno(aluno_id),
                    'editar_matricula': lambda aluno_id: self._editar_matricula(aluno_id),
                }

                self.detalhes_manager = DetalhesManager(
                    frame_detalhes=self.app.frame_detalhes,
                    colors=self.app.colors,
                    callbacks=callbacks
                )
                self.logger.info("DetalhesManager configurado com sucesso")
        except Exception as e:
            self.logger.error(f"Erro ao configurar DetalhesManager: {e}")
            self.detalhes_manager = None

    def pesquisar(self, termo: str):
        """Pesquisa alunos/funcionários com base no termo fornecido."""
        try:
            if not self.app.table_manager:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return

            if not termo or not termo.strip():
                self._atualizar_tabela()
                return

            # TODO: Implementar lógica de pesquisa
            self.logger.info(f"Pesquisando por: {termo}")
            messagebox.showinfo("Info", f"Pesquisa por '{termo}' - Implementação pendente")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao pesquisar: {str(e)}")
            self.logger.error(f"Erro ao pesquisar: {str(e)}")

    def _atualizar_tabela(self):
        """Helper interno para atualizar dados da tabela."""
        if self.app.table_manager:
            try:
                self.listar_alunos_ativos()
            except Exception as e:
                self.logger.error(f"Erro ao atualizar tabela: {str(e)}")
