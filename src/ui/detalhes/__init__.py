"""
Manager para gerenciar o frame de detalhes de alunos e funcionários.
Extrai lógica de UI do main.py - Sprint 16 com estrutura do Sprint 15.

Pacote dividido em:
  exibir  – funções de exibição (detalhes de aluno/funcionário)
  acoes   – criação de botões e wrappers de ação
"""

from tkinter import Frame
from typing import Dict, Optional, Callable

from src.core.config_logs import get_logger

# ── Re-exports de exibir ──────────────────────────────────────────────
from src.ui.detalhes.exibir import (          # noqa: F401
    _get_default_root,
    obter_ano_letivo_atual,
    verificar_matricula_ativa,
    verificar_historico_matriculas,
    exibir_detalhes_item,
    exibir_detalhes_aluno,
    exibir_detalhes_funcionario,
)

# ── Re-exports de acoes ───────────────────────────────────────────────
from src.ui.detalhes.acoes import (           # noqa: F401
    criar_botoes_frame_detalhes,
    criar_menu_boletim,
    criar_botoes_aluno,
    criar_botoes_funcionario,
    editar_aluno_wrapper,
    excluir_aluno_wrapper,
    abrir_historico_wrapper,
    gerar_declaracao_wrapper,
    matricular_aluno_wrapper,
    editar_matricula_wrapper,
    editar_funcionario_wrapper,
    excluir_funcionario_wrapper,
    gerar_declaracao_funcionario_wrapper,
)

logger = get_logger(__name__)


class DetalhesManager:
    """Gerencia o frame de detalhes com botões de ação (mantido para compatibilidade)."""

    def __init__(
        self,
        frame_detalhes: Frame,
        colors: Dict[str, str],
        callbacks: Optional[Dict[str, Callable]] = None
    ):
        """Inicializa o gerenciador de detalhes."""
        self.frame = frame_detalhes
        self.colors = colors
        self.callbacks = callbacks or {}
        self.logger = logger

    def limpar(self) -> None:
        """Limpa todos os widgets do frame de detalhes."""
        try:
            for widget in self.frame.winfo_children():
                widget.destroy()
            self.logger.debug("Frame de detalhes limpo")
        except Exception as e:
            self.logger.exception("Erro ao limpar frame de detalhes")
