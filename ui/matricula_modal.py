"""
Módulo de interface modal para matrícula de alunos.
Interface desacoplada que usa services/matricula_service.py.
"""

from tkinter import Toplevel, Label, Frame, Button, messagebox, StringVar
from tkinter import ttk
from typing import Optional, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)


class MatriculaModal:
    """
    Interface modal para matrícula de alunos.
    Usa matricula_service para lógica de negócio.
    """
    
    def __init__(
        self, 
        parent, 
        aluno_id: int, 
        nome_aluno: str,
        colors: Dict[str, str],
        callback_sucesso: Optional[Callable] = None
    ):
        """
        Inicializa modal de matrícula.
        
        Args:
            parent: Janela pai (Tkinter)
            aluno_id: ID do aluno a matricular
            nome_aluno: Nome do aluno
            colors: Dicionário de cores da aplicação
            callback_sucesso: Função chamada após matrícula bem-sucedida
        """
        self.parent = parent
        self.aluno_id = aluno_id
        self.nome_aluno = nome_aluno
        self.colors = colors
        self.callback_sucesso = callback_sucesso
        self.logger = logger
        
        self.janela = None
        self.serie_var = None
        self.turma_var = None
        self.series = []
        self.ano_letivo_id = None
        
        self._criar_interface()
    
    def _criar_interface(self):
        """Cria a interface do modal."""
        try:
            # Importar serviços
            from services.matricula_service import (
                obter_ano_letivo_atual,
                verificar_matricula_existente,
                obter_series_disponiveis
            )
            
            # Verificar ano letivo
            self.ano_letivo_id = obter_ano_letivo_atual()
            if not self.ano_letivo_id:
                messagebox.showerror("Erro", "Ano letivo atual não encontrado")
                return
            
            # Verificar matrícula existente
            matricula_existente = verificar_matricula_existente(self.aluno_id, self.ano_letivo_id)
            if matricula_existente and matricula_existente.get('status') == 'Ativo':
                messagebox.showwarning(
                    "Aviso",
                    f"Aluno já possui matrícula ativa:\n"
                    f"Série: {matricula_existente.get('serie')}\n"
                    f"Turma: {matricula_existente.get('turma')}"
                )
                return
            
            # Criar janela
            self.janela = Toplevel(self.parent)
            self.janela.title(f"Matricular Aluno - {self.nome_aluno}")
            self.janela.geometry('450x320')
            self.janela.configure(bg=self.colors.get('co1', '#ffffff'))
            self.janela.transient(self.parent)
            self.janela.grab_set()
            self.janela.resizable(False, False)
            
            # Frame principal com padding
            frame_principal = Frame(
                self.janela, 
                bg=self.colors.get('co1', '#ffffff'),
                padx=30,
                pady=25
            )
            frame_principal.pack(fill='both', expand=True)
            
            # Cabeçalho
            Label(
                frame_principal,
                text="📝 Matrícula de Aluno",
                bg=self.colors.get('co1', '#ffffff'),
                fg=self.colors.get('co7', '#000000'),
                font=("Arial", 14, "bold")
            ).pack(pady=(0, 5))
            
            Label(
                frame_principal,
                text=f"Aluno: {self.nome_aluno}",
                bg=self.colors.get('co1', '#ffffff'),
                fg=self.colors.get('co4', '#666666'),
                font=("Arial", 10)
            ).pack(pady=(0, 20))
            
            # Separador
            Frame(
                frame_principal,
                height=2,
                bg=self.colors.get('co9', '#cccccc')
            ).pack(fill='x', pady=(0, 20))
            
            # Série
            frame_serie = Frame(frame_principal, bg=self.colors.get('co1', '#ffffff'))
            frame_serie.pack(fill='x', pady=(0, 15))
            
            Label(
                frame_serie,
                text="Série:",
                bg=self.colors.get('co1', '#ffffff'),
                fg=self.colors.get('co7', '#000000'),
                font=("Arial", 10, "bold")
            ).pack(anchor='w')
            
            self.series = obter_series_disponiveis()
            self.serie_var = ttk.Combobox(
                frame_serie,
                state="readonly",
                width=35,
                font=("Arial", 10)
            )
            self.serie_var['values'] = [s['nome'] for s in self.series]
            self.serie_var.pack(pady=(5, 0))
            self.serie_var.bind('<<ComboboxSelected>>', self._atualizar_turmas)
            
            # Turma
            frame_turma = Frame(frame_principal, bg=self.colors.get('co1', '#ffffff'))
            frame_turma.pack(fill='x', pady=(0, 25))
            
            Label(
                frame_turma,
                text="Turma:",
                bg=self.colors.get('co1', '#ffffff'),
                fg=self.colors.get('co7', '#000000'),
                font=("Arial", 10, "bold")
            ).pack(anchor='w')
            
            self.turma_var = ttk.Combobox(
                frame_turma,
                state="readonly",
                width=35,
                font=("Arial", 10)
            )
            self.turma_var.pack(pady=(5, 0))
            
            # Botões
            frame_botoes = Frame(frame_principal, bg=self.colors.get('co1', '#ffffff'))
            frame_botoes.pack()
            
            Button(
                frame_botoes,
                text="✓ Matricular",
                command=self._confirmar_matricula,
                bg=self.colors.get('co2', '#4CAF50'),
                fg='#ffffff',
                font=("Arial", 10, "bold"),
                width=14,
                cursor='hand2',
                relief='flat',
                padx=10,
                pady=8
            ).pack(side='left', padx=5)
            
            Button(
                frame_botoes,
                text="✗ Cancelar",
                command=self.janela.destroy,
                bg=self.colors.get('co7', '#999999'),
                fg='#ffffff',
                font=("Arial", 10),
                width=14,
                cursor='hand2',
                relief='flat',
                padx=10,
                pady=8
            ).pack(side='left', padx=5)
            
            # Focar no primeiro campo
            self.serie_var.focus()
            
        except Exception as e:
            self.logger.exception(f"Erro ao criar interface de matrícula: {e}")
            messagebox.showerror("Erro", f"Erro ao criar interface: {str(e)}")
    
    def _atualizar_turmas(self, event=None):
        """Atualiza lista de turmas quando série é selecionada."""
        try:
            from services.matricula_service import obter_turmas_por_serie
            
            if not self.serie_var or not self.serie_var.get():
                return
            
            if not self.ano_letivo_id:
                return
            
            # Encontrar ID da série selecionada
            serie_nome = self.serie_var.get()
            serie_id = next((s['id'] for s in self.series if s['nome'] == serie_nome), None)
            
            if not serie_id:
                self.logger.warning(f"ID da série '{serie_nome}' não encontrado")
                return
            
            # Buscar turmas
            turmas = obter_turmas_por_serie(serie_id, self.ano_letivo_id)
            
            if not turmas:
                messagebox.showwarning(
                    "Aviso",
                    f"Não há turmas disponíveis para a série '{serie_nome}'"
                )
                if self.turma_var:
                    self.turma_var['values'] = []
                return
            
            # Atualizar combobox
            if self.turma_var:
                self.turma_var['values'] = [t['nome'] for t in turmas]
                self.turma_var.set('')  # Limpar seleção anterior
                
                # Guardar referência às turmas para buscar ID depois
                self.turma_var._turmas_data = turmas  # type: ignore
            
            self.logger.debug(f"Carregadas {len(turmas)} turma(s) para série {serie_nome}")
            
        except Exception as e:
            self.logger.exception(f"Erro ao atualizar turmas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar turmas: {str(e)}")
    
    def _confirmar_matricula(self):
        """Confirma e executa a matrícula."""
        try:
            # Validar campos
            if not self.serie_var or not self.serie_var.get():
                messagebox.showwarning("Aviso", "Selecione a série")
                if self.serie_var:
                    self.serie_var.focus()
                return
            
            if not self.turma_var or not self.turma_var.get():
                messagebox.showwarning("Aviso", "Selecione a turma")
                if self.turma_var:
                    self.turma_var.focus()
                return
            
            # Encontrar ID da turma
            turma_nome = self.turma_var.get()
            turmas_data = getattr(self.turma_var, '_turmas_data', [])
            turma_id = next((t['id'] for t in turmas_data if t['nome'] == turma_nome), None)
            
            if not turma_id:
                messagebox.showerror("Erro", "Turma não encontrada. Tente novamente.")
                return
            
            # Matricular usando serviço
            from services.matricula_service import matricular_aluno
            
            sucesso, mensagem = matricular_aluno(
                self.aluno_id,
                turma_id,
                self.ano_letivo_id,
                status='Ativo'
            )
            
            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
                
                # Chamar callback se fornecido
                if self.callback_sucesso:
                    try:
                        self.callback_sucesso()
                    except Exception as e:
                        self.logger.error(f"Erro ao executar callback: {e}")
                
                # Fechar modal
                if self.janela:
                    self.janela.destroy()
            else:
                messagebox.showerror("Erro", mensagem)
            
        except Exception as e:
            self.logger.exception(f"Erro ao confirmar matrícula: {e}")
            messagebox.showerror("Erro", f"Erro ao matricular: {str(e)}")


def abrir_matricula_modal(
    parent,
    aluno_id: int,
    nome_aluno: str,
    colors: Dict[str, str],
    callback_sucesso: Optional[Callable] = None
):
    """
    Função helper para abrir modal de matrícula.
    
    Args:
        parent: Janela pai
        aluno_id: ID do aluno
        nome_aluno: Nome do aluno
        colors: Dicionário de cores
        callback_sucesso: Callback após sucesso
    """
    MatriculaModal(parent, aluno_id, nome_aluno, colors, callback_sucesso)
