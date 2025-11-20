"""
Manager para gerenciar o frame de detalhes de alunos e funcionários.
Extrai lógica de UI do main.py.
"""
import tkinter as tk
from tkinter import Button, Frame, Label, RIDGE, X, W
from typing import Dict, Optional, Callable, Tuple, Any
from config_logs import get_logger

logger = get_logger(__name__)


def exibir_detalhes_item(
    frame_detalhes: Frame,
    tipo: str,
    item_id: int,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """
    Exibe detalhes de um item selecionado (aluno ou funcionário).
    
    Args:
        frame_detalhes: Frame onde exibir os detalhes
        tipo: 'Aluno' ou 'Funcionário'
        item_id: ID do item
        values: Tupla com valores do item
        colors: Dicionário de cores
    """
    try:
        # Limpar frame
        for widget in frame_detalhes.winfo_children():
            widget.destroy()
        
        # Frame de informações
        info_frame = Frame(frame_detalhes, bg=colors['co1'], padx=10, pady=10)
        info_frame.pack(fill=X)
        
        # Título
        Label(
            info_frame,
            text=f"{tipo} Selecionado",
            font=('Ivy', 12, 'bold'),
            bg=colors['co1'],
            fg=colors['co0']
        ).pack(anchor=W, pady=(0, 10))
        
        # Exibir informações básicas
        if len(values) >= 3:
            # ID
            Label(
                info_frame,
                text=f"ID: {values[1]}",
                font=('Ivy', 10),
                bg=colors['co1'],
                fg=colors['co0']
            ).pack(anchor=W, pady=2)
            
            # Nome
            Label(
                info_frame,
                text=f"Nome: {values[2]}",
                font=('Ivy', 10),
                bg=colors['co1'],
                fg=colors['co0']
            ).pack(anchor=W, pady=2)
            
            # CPF se disponível
            if len(values) >= 4 and values[3]:
                Label(
                    info_frame,
                    text=f"CPF: {values[3]}",
                    font=('Ivy', 10),
                    bg=colors['co1'],
                    fg=colors['co0']
                ).pack(anchor=W, pady=2)
        
        logger.debug(f"Detalhes exibidos para {tipo} ID={item_id}")
        
    except Exception as e:
        logger.exception(f"Erro ao exibir detalhes: {e}")


class DetalhesManager:
    """Gerencia o frame de detalhes com botões de ação."""
    
    def __init__(
        self,
        frame_detalhes: Frame,
        colors: Dict[str, str],
        callbacks: Dict[str, Callable]
    ):
        """
        Inicializa o gerenciador de detalhes.
        
        Args:
            frame_detalhes: Frame onde os botões serão criados
            colors: Dicionário com cores da aplicação
            callbacks: Dicionário com callbacks para ações
        """
        self.frame = frame_detalhes
        self.colors = colors
        self.callbacks = callbacks
        self.logger = logger
    
    def limpar(self) -> None:
        """Limpa todos os widgets do frame de detalhes."""
        try:
            for widget in self.frame.winfo_children():
                widget.destroy()
            self.logger.debug("Frame de detalhes limpo")
        except Exception as e:
            self.logger.exception("Erro ao limpar frame de detalhes")
    
    def criar_botoes_aluno(
        self,
        aluno_id: int,
        tem_matricula_ativa: bool,
        tem_historico: bool
    ) -> None:
        """
        Cria botões de ação para aluno.
        
        Args:
            aluno_id: ID do aluno
            tem_matricula_ativa: Se o aluno tem matrícula ativa
            tem_historico: Se o aluno tem histórico de matrículas
        """
        try:
            self.limpar()
            
            # Frame para os botões
            acoes_frame = Frame(self.frame, bg=self.colors['co1'])
            acoes_frame.pack(fill=X, padx=10, pady=10)
            
            # Configurar grid
            for i in range(6):
                acoes_frame.grid_columnconfigure(i, weight=1)
            
            # Botões básicos (sempre aparecem)
            col = 0
            
            # Editar
            Button(
                acoes_frame,
                text="Editar",
                command=lambda: self.callbacks.get('editar_aluno', lambda: None)(),
                width=10,
                overrelief=RIDGE,
                font=('Ivy', 9),
                bg=self.colors['co4'],
                fg=self.colors['co0']
            ).grid(row=0, column=col, padx=5, pady=5)
            col += 1
            
            # Excluir
            Button(
                acoes_frame,
                text="Excluir",
                command=lambda: self.callbacks.get('excluir_aluno', lambda: None)(),
                width=10,
                overrelief=RIDGE,
                font=('Ivy', 9),
                bg=self.colors['co8'],
                fg=self.colors['co0']
            ).grid(row=0, column=col, padx=5, pady=5)
            col += 1
            
            # Histórico (sempre aparece)
            Button(
                acoes_frame,
                text="Histórico",
                command=lambda: self.callbacks.get('abrir_historico', lambda: None)(),
                width=10,
                overrelief=RIDGE,
                font=('Ivy', 9),
                bg=self.colors['co5'],
                fg=self.colors['co0']
            ).grid(row=0, column=col, padx=5, pady=5)
            col += 1
            
            # Botões condicionais
            if tem_matricula_ativa or tem_historico:
                # Boletim
                Button(
                    acoes_frame,
                    text="Boletim",
                    command=lambda: self.callbacks.get('abrir_boletim', lambda: None)(),
                    width=10,
                    overrelief=RIDGE,
                    font=('Ivy', 9),
                    bg=self.colors['co6'],
                    fg=self.colors['co0']
                ).grid(row=0, column=col, padx=5, pady=5)
                col += 1
                
                if tem_matricula_ativa:
                    # Declaração
                    Button(
                        acoes_frame,
                        text="Declaração",
                        command=lambda: self.callbacks.get('gerar_declaracao', lambda: None)(),
                        width=10,
                        overrelief=RIDGE,
                        font=('Ivy', 9),
                        bg=self.colors['co2'],
                        fg=self.colors['co0']
                    ).grid(row=0, column=col, padx=5, pady=5)
                    col += 1
                    
                    # Editar Matrícula
                    Button(
                        acoes_frame,
                        text="Editar Matrícula",
                        command=lambda: self.callbacks.get('editar_matricula', lambda: None)(),
                        width=12,
                        overrelief=RIDGE,
                        font=('Ivy', 9, 'bold'),
                        bg=self.colors['co3'],
                        fg=self.colors['co0']
                    ).grid(row=0, column=col, padx=5, pady=5)
                else:
                    # Matricular (sem matrícula ativa mas com histórico)
                    Button(
                        acoes_frame,
                        text="Matricular",
                        command=lambda: self.callbacks.get('matricular_aluno', lambda: None)(),
                        width=10,
                        overrelief=RIDGE,
                        font=('Ivy', 9, 'bold'),
                        bg=self.colors['co3'],
                        fg=self.colors['co0']
                    ).grid(row=0, column=col, padx=5, pady=5)
            else:
                # Matricular (sem matrícula e sem histórico)
                Button(
                    acoes_frame,
                    text="Matricular",
                    command=lambda: self.callbacks.get('matricular_aluno', lambda: None)(),
                    width=10,
                    overrelief=RIDGE,
                    font=('Ivy', 9, 'bold'),
                    bg=self.colors['co3'],
                    fg=self.colors['co0']
                ).grid(row=0, column=col, padx=5, pady=5)
            
            self.logger.debug(f"Botões de aluno criados (matrícula ativa: {tem_matricula_ativa})")
            
        except Exception as e:
            self.logger.exception("Erro ao criar botões de aluno")
    
    def criar_botoes_funcionario(self, funcionario_id: int) -> None:
        """
        Cria botões de ação para funcionário.
        
        Args:
            funcionario_id: ID do funcionário
        """
        try:
            self.limpar()
            
            # Frame para os botões
            acoes_frame = Frame(self.frame, bg=self.colors['co1'])
            acoes_frame.pack(fill=X, padx=10, pady=10)
            
            # Configurar grid
            for i in range(3):
                acoes_frame.grid_columnconfigure(i, weight=1)
            
            # Editar
            Button(
                acoes_frame,
                text="Editar",
                command=lambda: self.callbacks.get('editar_funcionario', lambda: None)(),
                width=10,
                overrelief=RIDGE,
                font=('Ivy', 9),
                bg=self.colors['co4'],
                fg=self.colors['co0']
            ).grid(row=0, column=0, padx=5, pady=5)
            
            # Excluir
            Button(
                acoes_frame,
                text="Excluir",
                command=lambda: self.callbacks.get('excluir_funcionario', lambda: None)(),
                width=10,
                overrelief=RIDGE,
                font=('Ivy', 9),
                bg=self.colors['co8'],
                fg=self.colors['co0']
            ).grid(row=0, column=1, padx=5, pady=5)
            
            # Declaração
            Button(
                acoes_frame,
                text="Declaração",
                command=lambda: self.callbacks.get('gerar_declaracao_funcionario', lambda: None)(),
                width=10,
                overrelief=RIDGE,
                font=('Ivy', 9),
                bg=self.colors['co2'],
                fg=self.colors['co0']
            ).grid(row=0, column=2, padx=5, pady=5)
            
            self.logger.debug(f"Botões de funcionário criados para ID {funcionario_id}")
            
        except Exception as e:
            self.logger.exception("Erro ao criar botões de funcionário")
    
    def criar_botoes_por_tipo(
        self,
        tipo: str,
        item_id: int,
        tem_matricula_ativa: bool = False,
        tem_historico: bool = False
    ) -> None:
        """
        Cria botões apropriados baseado no tipo de item.
        
        Args:
            tipo: 'Aluno' ou 'Funcionário'
            item_id: ID do item
            tem_matricula_ativa: Se o aluno tem matrícula ativa
            tem_historico: Se o aluno tem histórico
        """
        try:
            if tipo == 'Aluno':
                self.criar_botoes_aluno(item_id, tem_matricula_ativa, tem_historico)
            elif tipo == 'Funcionário':
                self.criar_botoes_funcionario(item_id)
            else:
                self.logger.warning(f"Tipo desconhecido: {tipo}")
                self.limpar()
                
        except Exception as e:
            self.logger.exception(f"Erro ao criar botões para tipo {tipo}")
