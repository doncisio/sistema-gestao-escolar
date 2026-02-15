"""
Interface para gerar crachá individual de aluno/responsável.
"""

from tkinter import Toplevel, Frame, Label, Button, messagebox, StringVar
from tkinter.ttk import Combobox
import os
import subprocess
import platform

from src.ui.colors import COLORS
from src.core.config_logs import get_logger
from src.services import cracha_service

logger = get_logger(__name__)


class CrachaIndividualWindow:
    """Janela para seleção de aluno e responsável para gerar crachá individual."""
    
    def __init__(self, janela_pai):
        """
        Inicializa a janela de geração de crachá individual.
        
        Args:
            janela_pai: Janela pai do Tkinter
        """
        self.janela_pai = janela_pai
        self.janela = Toplevel(janela_pai)
        self.janela.title("Gerar Crachá Individual")
        self.janela.geometry("600x400")
        self.janela.configure(bg=COLORS.co1)
        self.janela.resizable(False, False)
        
        # Centralizar na tela
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.janela.winfo_screenheight() // 2) - (400 // 2)
        self.janela.geometry(f"600x400+{x}+{y}")
        
        # Dados
        self.alunos = []
        self.responsaveis = []
        self.aluno_selecionado = None
        self.responsavel_selecionado = None
        
        # Variáveis
        self.var_aluno = StringVar()
        self.var_responsavel = StringVar()
        
        # Criar interface
        self._criar_widgets()
        
        # Carregar dados
        self._carregar_alunos()
    
    def _criar_widgets(self):
        """Cria os widgets da interface."""
        # Frame principal
        frame_principal = Frame(self.janela, bg=COLORS.co1, padx=30, pady=20)
        frame_principal.pack(fill='both', expand=True)
        
        # Título
        Label(
            frame_principal,
            text="Gerar Crachá Individual",
            font=("Arial", 16, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(pady=(0, 20))
        
        # Frame aluno
        frame_aluno = Frame(frame_principal, bg=COLORS.co1)
        frame_aluno.pack(fill='x', pady=10)
        
        Label(
            frame_aluno,
            text="Selecione o Aluno:",
            font=("Arial", 12, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(anchor='w', pady=(0, 5))
        
        self.combo_aluno = Combobox(
            frame_aluno,
            textvariable=self.var_aluno,
            font=("Arial", 11),
            state='readonly',
            width=60
        )
        self.combo_aluno.pack(fill='x')
        self.combo_aluno.bind('<<ComboboxSelected>>', self._on_aluno_selecionado)
        
        # Frame responsável
        frame_resp = Frame(frame_principal, bg=COLORS.co1)
        frame_resp.pack(fill='x', pady=10)
        
        Label(
            frame_resp,
            text="Selecione o Responsável:",
            font=("Arial", 12, "bold"),
            bg=COLORS.co1,
            fg=COLORS.co0
        ).pack(anchor='w', pady=(0, 5))
        
        self.combo_responsavel = Combobox(
            frame_resp,
            textvariable=self.var_responsavel,
            font=("Arial", 11),
            state='disabled',
            width=60
        )
        self.combo_responsavel.pack(fill='x')
        
        # Info adicional
        self.label_info = Label(
            frame_principal,
            text="",
            font=("Arial", 10, "italic"),
            bg=COLORS.co1,
            fg=COLORS.co7,
            wraplength=500,
            justify='left'
        )
        self.label_info.pack(pady=20)
        
        # Frame botões
        frame_botoes = Frame(frame_principal, bg=COLORS.co1)
        frame_botoes.pack(pady=20)
        
        Button(
            frame_botoes,
            text="Gerar Crachá",
            command=self._gerar_cracha,
            bg=COLORS.co2,
            fg=COLORS.co0,
            font=("Arial", 12, "bold"),
            width=15,
            height=2
        ).pack(side='left', padx=10)
        
        Button(
            frame_botoes,
            text="Cancelar",
            command=self.janela.destroy,
            bg=COLORS.co4,
            fg=COLORS.co0,
            font=("Arial", 12),
            width=15,
            height=2
        ).pack(side='left', padx=10)
    
    def _carregar_alunos(self):
        """Carrega a lista de alunos do banco de dados."""
        try:
            self.alunos = cracha_service.obter_alunos_para_selecao()
            
            if not self.alunos:
                messagebox.showwarning(
                    "Aviso",
                    "Nenhum aluno ativo encontrado."
                )
                self.janela.destroy()
                return
            
            # Preencher combobox
            valores = [
                f"{aluno['nome']} - {aluno['serie']} {aluno['turma']} ({aluno['turno']})"
                for aluno in self.alunos
            ]
            self.combo_aluno['values'] = valores
            
            self.label_info.config(
                text=f"Total de {len(self.alunos)} alunos ativos encontrados."
            )
            
        except Exception as e:
            logger.exception("Erro ao carregar alunos")
            messagebox.showerror(
                "Erro",
                f"Erro ao carregar lista de alunos:\n{str(e)}"
            )
            self.janela.destroy()
    
    def _on_aluno_selecionado(self, event=None):
        """Callback quando um aluno é selecionado."""
        idx = self.combo_aluno.current()
        if idx < 0:
            return
        
        self.aluno_selecionado = self.alunos[idx]
        self._carregar_responsaveis()
    
    def _carregar_responsaveis(self):
        """Carrega os responsáveis do aluno selecionado."""
        if not self.aluno_selecionado:
            return
        
        try:
            self.responsaveis = cracha_service.obter_responsaveis_do_aluno(
                self.aluno_selecionado['id']
            )
            
            if not self.responsaveis:
                messagebox.showwarning(
                    "Aviso",
                    f"Nenhum responsável cadastrado para {self.aluno_selecionado['nome']}."
                )
                self.combo_responsavel['state'] = 'disabled'
                self.combo_responsavel['values'] = []
                return
            
            # Preencher combobox de responsáveis
            valores = [
                f"{resp['nome']} - {resp['grau_parentesco'] or 'Não informado'} - Tel: {resp['telefone'] or 'Não informado'}"
                for resp in self.responsaveis
            ]
            self.combo_responsavel['values'] = valores
            self.combo_responsavel['state'] = 'readonly'
            
            # Selecionar o primeiro responsável automaticamente
            self.combo_responsavel.current(0)
            
            self.label_info.config(
                text=f"Aluno: {self.aluno_selecionado['nome']}\n"
                     f"Série/Turma: {self.aluno_selecionado['serie']} {self.aluno_selecionado['turma']}\n"
                     f"{len(self.responsaveis)} responsável(is) encontrado(s)."
            )
            
        except Exception as e:
            logger.exception("Erro ao carregar responsáveis")
            messagebox.showerror(
                "Erro",
                f"Erro ao carregar responsáveis:\n{str(e)}"
            )
    
    def _gerar_cracha(self):
        """Gera o crachá individual."""
        if not self.aluno_selecionado:
            messagebox.showwarning(
                "Aviso",
                "Selecione um aluno."
            )
            return
        
        idx_resp = self.combo_responsavel.current()
        if idx_resp < 0:
            messagebox.showwarning(
                "Aviso",
                "Selecione um responsável."
            )
            return
        
        self.responsavel_selecionado = self.responsaveis[idx_resp]
        
        try:
            # Desabilitar botões durante geração
            self.janela.config(cursor="wait")
            self.janela.update()
            
            # Gerar o crachá
            caminho_pdf = cracha_service.gerar_cracha_individual(
                self.aluno_selecionado['id'],
                self.responsavel_selecionado['id']
            )
            
            if not caminho_pdf:
                messagebox.showerror(
                    "Erro",
                    "Erro ao gerar o crachá. Verifique os logs."
                )
                return
            
            # Sucesso
            self.janela.config(cursor="")
            
            resposta = messagebox.askyesno(
                "Sucesso",
                f"Crachá gerado com sucesso!\n\n"
                f"Aluno: {self.aluno_selecionado['nome']}\n"
                f"Responsável: {self.responsavel_selecionado['nome']}\n\n"
                f"Arquivo salvo em:\n{caminho_pdf}\n\n"
                f"Deseja abrir o arquivo?"
            )
            
            if resposta:
                self._abrir_pdf(caminho_pdf)
            
            # Fechar janela
            self.janela.destroy()
            
        except Exception as e:
            self.janela.config(cursor="")
            logger.exception("Erro ao gerar crachá individual")
            messagebox.showerror(
                "Erro",
                f"Erro ao gerar crachá:\n{str(e)}"
            )
    
    def _abrir_pdf(self, caminho):
        """Abre o PDF com o visualizador padrão do sistema."""
        try:
            if platform.system() == 'Windows':
                os.startfile(caminho)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', caminho])
            else:  # Linux
                subprocess.Popen(['xdg-open', caminho])
        except Exception as e:
            logger.warning(f"Não foi possível abrir o PDF: {e}")
            messagebox.showwarning(
                "Aviso",
                f"Crachá gerado, mas não foi possível abrir automaticamente.\n"
                f"Localização: {caminho}"
            )


def abrir_janela_cracha_individual(janela_pai):
    """
    Abre a janela de geração de crachá individual.
    
    Args:
        janela_pai: Janela pai do Tkinter
    """
    CrachaIndividualWindow(janela_pai)
