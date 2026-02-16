"""Funções de exibição de detalhes de alunos e funcionários."""

import tkinter as tk
from tkinter import Frame, Label, BOTH, W, EW
from typing import Dict, Tuple, Any
from datetime import datetime, date

from src.core.config_logs import get_logger
from src.utils.safe import _safe_get
from src.services.ano_letivo_service import obter_ano_letivo_atual_id as _obter_ano_letivo_service
from src.services.aluno_service import (
    verificar_matricula_ativa as _verificar_matricula_service,
    verificar_historico_matriculas as _verificar_historico_service,
    obter_detalhes_matricula_aluno as _obter_detalhes_matricula_service,
)

logger = get_logger(__name__)


def _get_default_root():
    """Retorna a janela principal do Tkinter de forma segura."""
    import tkinter as tk
    try:
        return tk._get_default_root()  # type: ignore[attr-defined]
    except AttributeError:
        return getattr(tk, '_default_root', None)  # type: ignore[attr-defined]


def obter_ano_letivo_atual() -> int:
    """Retorna o ID do ano letivo atual. Delega para ano_letivo_service."""
    return _obter_ano_letivo_service()


def verificar_matricula_ativa(aluno_id: int) -> bool:
    """Verifica matrícula ativa/transferida na escola 60. Delega para aluno_service."""
    try:
        return _verificar_matricula_service(aluno_id)
    except Exception as e:
        logger.exception(f"Erro ao verificar matrícula: {e}")
        return False


def verificar_historico_matriculas(aluno_id: int) -> tuple[bool, list]:
    """Verifica histórico de matrículas do aluno. Delega para aluno_service."""
    try:
        return _verificar_historico_service(aluno_id)
    except Exception as e:
        logger.exception(f"Erro ao verificar histórico: {e}")
        return False, []


def exibir_detalhes_item(
    frame_detalhes: Frame,
    tipo: str,
    item_id: int,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """Exibe detalhes completos de um item selecionado (estrutura Sprint 15)."""
    from src.ui.detalhes.acoes import criar_botoes_frame_detalhes

    try:
        for widget in frame_detalhes.winfo_children():
            widget.destroy()

        criar_botoes_frame_detalhes(frame_detalhes, tipo, values, colors)

        detalhes_info_frame = Frame(frame_detalhes, bg=colors['co1'])
        detalhes_info_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        for i in range(3):
            detalhes_info_frame.grid_columnconfigure(i, weight=1, uniform="col")

        if tipo == "Aluno":
            exibir_detalhes_aluno(detalhes_info_frame, item_id, values, colors)
        elif tipo == "Funcionário":
            exibir_detalhes_funcionario(detalhes_info_frame, values, colors)

        logger.debug(f"Detalhes exibidos para {tipo} ID={item_id}")

    except Exception as e:
        logger.exception(f"Erro ao exibir detalhes: {e}")


def exibir_detalhes_aluno(
    detalhes_info_frame: Frame,
    aluno_id: int,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """Exibe detalhes específicos de um aluno."""
    Label(detalhes_info_frame, text=f"ID: {values[0]}", bg=colors['co1'], fg=colors['co0'],
          font=('Ivy 10 bold'), anchor=W).grid(row=0, column=0, sticky=EW, padx=5, pady=3)
    Label(detalhes_info_frame, text=f"Nome: {values[1]}", bg=colors['co1'], fg=colors['co0'],
          font=('Ivy 10 bold'), anchor=W).grid(row=0, column=1, columnspan=2, sticky=EW, padx=5, pady=3)

    Label(detalhes_info_frame, text=f"Data de Nascimento: {values[4]}", bg=colors['co1'], fg=colors['co0'],
          font=('Ivy 10'), anchor=W).grid(row=1, column=0, sticky=EW, padx=5, pady=3)

    try:
        ano_letivo_id = obter_ano_letivo_atual()
        resultado = _obter_detalhes_matricula_service(aluno_id, ano_letivo_id)

        if resultado:
            nome_mae = resultado.get('nome_mae') if isinstance(resultado, dict) else _safe_get(resultado, 6)
            nome_pai = resultado.get('nome_pai') if isinstance(resultado, dict) else _safe_get(resultado, 7)

            if nome_mae:
                Label(detalhes_info_frame, text=f"Mãe: {nome_mae}", bg=colors['co1'], fg=colors['co0'],
                      font=('Ivy 10'), anchor=W).grid(row=2, column=0, columnspan=2, sticky=EW, padx=5, pady=3)

            if nome_pai:
                Label(detalhes_info_frame, text=f"Pai: {nome_pai}", bg=colors['co1'], fg=colors['co0'],
                      font=('Ivy 10'), anchor=W).grid(row=2, column=2, sticky=EW, padx=5, pady=3)

            status = resultado.get('status') if isinstance(resultado, dict) else _safe_get(resultado, 0)
            data_matricula = resultado.get('data_matricula') if isinstance(resultado, dict) else _safe_get(resultado, 1)
            serie_nome = resultado.get('serie_nome') if isinstance(resultado, dict) else _safe_get(resultado, 2)
            turma_nome = resultado.get('turma_nome') if isinstance(resultado, dict) else _safe_get(resultado, 3)
            turma_id = resultado.get('turma_id') if isinstance(resultado, dict) else _safe_get(resultado, 4)
            data_transferencia = resultado.get('data_transferencia') if isinstance(resultado, dict) else _safe_get(resultado, 5)

            if status == 'Ativo' and data_matricula:
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
                      bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=1, column=1, sticky=EW, padx=5, pady=3)

                if serie_nome:
                    Label(detalhes_info_frame,
                          text=f"Série: {serie_nome}",
                          bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)

                try:
                    if serie_nome and isinstance(serie_nome, str):
                        if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                            turma_completa = f"{serie_nome} {turma_nome}".strip()
                        else:
                            turma_completa = serie_nome
                    else:
                        if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                            turma_completa = turma_nome
                        else:
                            turma_completa = f"Turma {turma_id}" if turma_id else "Não definida"
                except Exception:
                    turma_completa = f"Turma {turma_id}" if turma_id else "Não definida"

                Label(detalhes_info_frame,
                      text=f"Turma: {turma_completa}",
                      bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)

            elif status == 'Transferido' and data_transferencia:
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
                      bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=1, column=1, sticky=EW, padx=5, pady=3)

                if serie_nome:
                    Label(detalhes_info_frame,
                          text=f"Última Série: {serie_nome}",
                          bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)

                if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                    Label(detalhes_info_frame,
                          text=f"Última Turma: {turma_nome}",
                          bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)
                else:
                    turma_texto = f"Última Turma: Turma {turma_id}" if turma_id else "Última Turma: Não definida"
                    Label(detalhes_info_frame,
                          text=turma_texto,
                          bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)

    except Exception as e:
        logger.error(f"Erro ao verificar matrícula: {str(e)}")


def exibir_detalhes_funcionario(
    detalhes_info_frame: Frame,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """Exibe detalhes específicos de um funcionário."""
    Label(detalhes_info_frame, text=f"ID: {values[0]}", bg=colors['co1'], fg=colors['co0'],
          font=('Ivy 10 bold'), anchor=W).grid(row=0, column=0, sticky=EW, padx=5, pady=3)
    Label(detalhes_info_frame, text=f"Nome: {values[1]}", bg=colors['co1'], fg=colors['co0'],
          font=('Ivy 10 bold'), anchor=W).grid(row=0, column=1, columnspan=2, sticky=EW, padx=5, pady=3)

    Label(detalhes_info_frame, text=f"Cargo: {values[3]}", bg=colors['co1'], fg=colors['co0'],
          font=('Ivy 10'), anchor=W).grid(row=1, column=0, columnspan=2, sticky=EW, padx=5, pady=3)
    Label(detalhes_info_frame, text=f"Data de Nascimento: {values[4]}", bg=colors['co1'], fg=colors['co0'],
          font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)
