"""
Módulo de handlers de ações da interface.
Encapsula a lógica de ações do usuário (botões, menus, etc.) do main.py.
"""

from tkinter import messagebox, Toplevel
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)


class ActionHandler:
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
        
    def cadastrar_novo_aluno(self):
        """Abre a interface de cadastro de novo aluno."""
        try:
            from InterfaceCadastroAluno import InterfaceCadastroAluno
            
            janela_cadastro = Toplevel(self.app.janela)
            janela_cadastro.title("Cadastrar Novo Aluno")
            janela_cadastro.geometry('950x670')
            janela_cadastro.configure(background=self.app.colors['co1'])
            janela_cadastro.focus_set()
            janela_cadastro.grab_set()
            
            # Esconder janela principal
            self.app.janela.withdraw()
            
            # Criar interface de cadastro
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
        """Abre a interface de edição do aluno selecionado."""
        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return
                
            item_selecionado = self.app.table_manager.get_selected_item()
            
            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um aluno para editar")
                return
            
            aluno_id = item_selecionado[0]  # ID é o primeiro valor
            
            from InterfaceEdicaoAluno import InterfaceEdicaoAluno
            
            janela_edicao = Toplevel(self.app.janela)
            janela_edicao.title(f"Editar Aluno - ID: {aluno_id}")
            janela_edicao.geometry('950x670')
            janela_edicao.configure(background=self.app.colors['co1'])
            janela_edicao.focus_set()
            janela_edicao.grab_set()
            
            # Esconder janela principal
            self.app.janela.withdraw()
            
            # Criar interface de edição
            app_edicao = InterfaceEdicaoAluno(janela_edicao, aluno_id, janela_principal=self.app.janela)
            
            def ao_fechar_edicao():
                self.app.janela.deiconify()
                if self.app.table_manager:
                    self._atualizar_tabela()
                janela_edicao.destroy()
            
            janela_edicao.protocol("WM_DELETE_WINDOW", ao_fechar_edicao)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir edição: {str(e)}")
            self.logger.error(f"Erro ao abrir edição: {str(e)}")
            self.app.janela.deiconify()
    
    def excluir_aluno(self, callback_sucesso: Optional[Callable] = None):
        """
        Exclui o aluno selecionado após confirmação.
        
        Args:
            callback_sucesso: Função a ser chamada após exclusão bem-sucedida
        """
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
            
            # Usar serviço de alunos para exclusão (já inclui confirmação)
            from services.aluno_service import excluir_aluno_com_confirmacao
            
            resultado = excluir_aluno_com_confirmacao(
                aluno_id,
                nome_aluno,
                callback_sucesso=callback_sucesso or self._atualizar_tabela
            )
            
            if resultado:
                if self.app.table_manager:
                    self._atualizar_tabela()
            # Mensagens já são exibidas pelo serviço
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir aluno: {str(e)}")
            self.logger.error(f"Erro ao excluir aluno: {str(e)}")
    
    def cadastrar_novo_funcionario(self):
        """Abre a interface de cadastro de novo funcionário."""
        try:
            from InterfaceCadastroFuncionario import InterfaceCadastroFuncionario
            
            janela_cadastro = Toplevel(self.app.janela)
            janela_cadastro.title("Cadastrar Novo Funcionário")
            janela_cadastro.geometry('950x670')
            janela_cadastro.configure(background=self.app.colors['co1'])
            janela_cadastro.focus_set()
            janela_cadastro.grab_set()
            
            # Esconder janela principal
            self.app.janela.withdraw()
            
            # Criar interface de cadastro
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
    
    def buscar_funcionario(self, termo: str):
        """
        Busca funcionários usando o serviço.
        
        Args:
            termo: Termo de busca (nome ou CPF)
        """
        try:
            from services.funcionario_service import buscar_funcionario
            
            if not termo or not termo.strip():
                # Se vazio, listar todos
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
        """
        Lista funcionários na tabela.
        
        Args:
            cargo: Filtrar por cargo (opcional)
        """
        try:
            from services.funcionario_service import listar_funcionarios
            
            funcionarios = listar_funcionarios(cargo=cargo)
            
            if self.app.table_manager:
                self.app.table_manager.atualizar_dados(funcionarios)
                self.logger.info(f"Listados {len(funcionarios)} funcionário(s)")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao listar funcionários: {str(e)}")
            self.logger.exception(f"Erro ao listar funcionários: {e}")
    
    def excluir_funcionario(self):
        """Exclui funcionário selecionado após confirmação."""
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
            
            # Confirmar exclusão
            resposta = messagebox.askyesno(
                "Confirmar Exclusão",
                f"Deseja realmente excluir o funcionário:\n\n{nome}?\n\n"
                "Esta ação não pode ser desfeita."
            )
            
            if not resposta:
                return
            
            from services.funcionario_service import excluir_funcionario
            
            sucesso, mensagem = excluir_funcionario(funcionario_id, verificar_vinculos=True)
            
            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
                self._atualizar_tabela()
            else:
                messagebox.showerror("Erro", mensagem)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir funcionário: {str(e)}")
            self.logger.exception(f"Erro ao excluir funcionário: {e}")
    
    def abrir_historico_escolar(self):
        """Abre a interface de gerenciamento de histórico escolar."""
        try:
            from interface_historico_otimizada import InterfaceHistoricoOtimizada
            
            janela_historico = Toplevel(self.app.janela)
            janela_historico.title("Histórico Escolar")
            janela_historico.geometry('1200x700')
            janela_historico.configure(background=self.app.colors['co1'])
            janela_historico.focus_set()
            janela_historico.grab_set()
            
            # Esconder janela principal
            self.app.janela.withdraw()
            
            # Criar interface de histórico
            app_historico = InterfaceHistoricoOtimizada(janela_historico, janela_principal=self.app.janela)
            
            def ao_fechar_historico():
                self.app.janela.deiconify()
                janela_historico.destroy()
                
            janela_historico.protocol("WM_DELETE_WINDOW", ao_fechar_historico)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir histórico: {str(e)}")
            self.logger.error(f"Erro ao abrir histórico: {str(e)}")
            self.app.janela.deiconify()
    
    def abrir_interface_administrativa(self):
        """Abre a interface administrativa do sistema."""
        try:
            from interface_administrativa import InterfaceAdministrativa
            
            janela_admin = Toplevel(self.app.janela)
            janela_admin.title("Administração do Sistema")
            janela_admin.geometry('1000x600')
            janela_admin.configure(background=self.app.colors['co1'])
            janela_admin.focus_set()
            janela_admin.grab_set()
            
            # Esconder janela principal
            self.app.janela.withdraw()
            
            # Criar interface administrativa
            app_admin = InterfaceAdministrativa(janela_admin, janela_principal=self.app.janela)
            
            def ao_fechar_admin():
                self.app.janela.deiconify()
                janela_admin.destroy()
                
            janela_admin.protocol("WM_DELETE_WINDOW", ao_fechar_admin)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir administração: {str(e)}")
            self.logger.error(f"Erro ao abrir administração: {str(e)}")
            self.app.janela.deiconify()
    
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
            # Por enquanto, apenas log
            aluno_id = item_selecionado[0]
            self.logger.info(f"Visualizando detalhes do aluno ID: {aluno_id}")
            messagebox.showinfo("Info", f"Detalhes do aluno ID {aluno_id} - Implementação pendente")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir detalhes: {str(e)}")
            self.logger.error(f"Erro ao exibir detalhes: {str(e)}")
    
    def pesquisar(self, termo: str):
        """
        Pesquisa alunos/funcionários com base no termo fornecido.
        
        Args:
            termo: Termo de busca (nome, matrícula, CPF, etc.)
        """
        try:
            if not self.app.table_manager:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return
            
            if not termo or not termo.strip():
                # Se termo vazio, atualizar para mostrar todos
                self._atualizar_tabela()
                return
            
            # TODO: Implementar lógica de pesquisa
            # Por enquanto, apenas log
            self.logger.info(f"Pesquisando por: {termo}")
            messagebox.showinfo("Info", f"Pesquisa por '{termo}' - Implementação pendente")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao pesquisar: {str(e)}")
            self.logger.error(f"Erro ao pesquisar: {str(e)}")
    
    def matricular_aluno_modal(self):
        """Abre modal para matricular aluno selecionado."""
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
            
            # Importar serviços
            from services.matricula_service import (
                obter_ano_letivo_atual,
                verificar_matricula_existente,
                obter_series_disponiveis,
                obter_turmas_por_serie,
                matricular_aluno
            )
            from tkinter import ttk
            
            # Verificar ano letivo
            ano_letivo_id = obter_ano_letivo_atual()
            if not ano_letivo_id:
                messagebox.showerror("Erro", "Ano letivo atual não encontrado")
                return
            
            # Verificar se já tem matrícula
            matricula_existente = verificar_matricula_existente(aluno_id, ano_letivo_id)
            if matricula_existente and matricula_existente.get('status') == 'Ativo':
                messagebox.showwarning(
                    "Aviso",
                    f"Aluno já possui matrícula ativa:\n"
                    f"Série: {matricula_existente.get('serie')}\n"
                    f"Turma: {matricula_existente.get('turma')}"
                )
                return
            
            # Criar janela modal
            janela_matricula = Toplevel(self.app.janela)
            janela_matricula.title(f"Matricular Aluno - {nome_aluno}")
            janela_matricula.geometry('400x250')
            janela_matricula.configure(bg=self.app.colors['co1'])
            janela_matricula.transient(self.app.janela)
            janela_matricula.grab_set()
            
            from tkinter import Label, Frame
            
            # Frame principal
            frame = Frame(janela_matricula, bg=self.app.colors['co1'], padx=20, pady=20)
            frame.pack(fill='both', expand=True)
            
            # Label aluno
            Label(frame, text=f"Aluno: {nome_aluno}", bg=self.app.colors['co1'], 
                  font=("Arial", 11, "bold")).pack(anchor='w', pady=(0, 15))
            
            # Série
            Label(frame, text="Série:", bg=self.app.colors['co1']).pack(anchor='w')
            series = obter_series_disponiveis()
            serie_var = ttk.Combobox(frame, state="readonly", width=30)
            serie_var['values'] = [s['nome'] for s in series]
            serie_var.pack(pady=(5, 15))
            
            # Turma
            Label(frame, text="Turma:", bg=self.app.colors['co1']).pack(anchor='w')
            turma_var = ttk.Combobox(frame, state="readonly", width=30)
            turma_var.pack(pady=(5, 20))
            
            # Atualizar turmas quando série mudar
            def atualizar_turmas(event=None):
                if not serie_var.get():
                    return
                    
                # Encontrar ID da série selecionada
                serie_nome = serie_var.get()
                serie_id = next((s['id'] for s in series if s['nome'] == serie_nome), None)
                
                if serie_id:
                    turmas = obter_turmas_por_serie(serie_id, ano_letivo_id)
                    turma_var['values'] = [t['nome'] for t in turmas]
                    # Guardar referência às turmas para buscar ID depois
                    turma_var._turmas_data = turmas
                else:
                    turma_var['values'] = []
            
            serie_var.bind('<<ComboboxSelected>>', atualizar_turmas)
            
            # Botões
            from tkinter import Button
            frame_botoes = Frame(frame, bg=self.app.colors['co1'])
            frame_botoes.pack(pady=(10, 0))
            
            def confirmar_matricula():
                if not serie_var.get() or not turma_var.get():
                    messagebox.showwarning("Aviso", "Selecione série e turma")
                    return
                
                # Encontrar ID da turma
                turma_nome = turma_var.get()
                turmas_data = getattr(turma_var, '_turmas_data', [])
                turma_id = next((t['id'] for t in turmas_data if t['nome'] == turma_nome), None)
                
                if not turma_id:
                    messagebox.showerror("Erro", "Turma não encontrada")
                    return
                
                # Matricular
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
    
    def buscar_aluno(self, termo: str):
        """
        Busca alunos usando o serviço e atualiza tabela.
        
        Args:
            termo: Termo de busca (nome ou CPF)
        """
        try:
            from services.aluno_service import buscar_alunos
            
            if not termo or not termo.strip():
                # Se vazio, mostrar todos
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
            from services.aluno_service import listar_alunos_ativos
            
            alunos = listar_alunos_ativos()
            
            if self.app.table_manager:
                self.app.table_manager.atualizar_dados(alunos)
                self.logger.info(f"Listados {len(alunos)} aluno(s) ativo(s)")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao listar alunos: {str(e)}")
            self.logger.exception(f"Erro ao listar alunos ativos: {e}")
    
    def _atualizar_tabela(self):
        """Helper interno para atualizar dados da tabela."""
        if self.app.table_manager:
            try:
                # Atualizar com lista de alunos ativos
                self.listar_alunos_ativos()
            except Exception as e:
                self.logger.error(f"Erro ao atualizar tabela: {str(e)}")
