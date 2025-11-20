"""
Módulo de handlers de ações da interface.
Encapsula a lógica de ações do usuário (botões, menus, etc.) do main.py.
"""

from tkinter import messagebox, Toplevel, Label, Frame, Button, StringVar, OptionMenu, Entry
from typing import Optional, Callable, Dict
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
        self.detalhes_manager = None
        self._configurar_detalhes_manager()
    
    def _configurar_detalhes_manager(self):
        """Configura o gerenciador de detalhes se o frame existir."""
        try:
            # Só configura se app tiver frame_detalhes
            if hasattr(self.app, 'frame_detalhes') and self.app.frame_detalhes:
                from ui.detalhes import DetalhesManager
                
                # Criar dicionário de callbacks para os botões
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
        """Abre a interface de edição do aluno selecionado usando modal."""
        from ui.aluno_modal import abrir_aluno_modal
        
        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return
                
            item_selecionado = self.app.table_manager.get_selected_item()
            
            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um aluno para editar")
                return
            
            aluno_id = item_selecionado[0]  # ID é o primeiro valor
            
            # Usar modal de edição
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
    
    def editar_funcionario(self):
        """Abre a interface de edição do funcionário selecionado usando modal."""
        from ui.funcionario_modal import abrir_funcionario_modal
        
        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return
                
            item_selecionado = self.app.table_manager.get_selected_item()
            
            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para editar")
                return
            
            funcionario_id = item_selecionado[0]  # ID é o primeiro valor
            
            # Usar modal de edição
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
                    setattr(turma_var, '_turmas_data', turmas)
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
    
    # ===== Métodos stub para callbacks do DetalhesManager =====
    # Esses métodos serão implementados progressivamente
    
    def _excluir_funcionario(self):
        """Exclui funcionário selecionado usando funcionario_service."""
        from services.funcionario_service import excluir_funcionario, obter_funcionario_por_id
        
        try:
            if not self.app.table_manager or not self.app.table_manager.tree:
                messagebox.showwarning("Aviso", "Tabela não inicializada")
                return
            
            item_selecionado = self.app.table_manager.get_selected_item()
            
            if not item_selecionado:
                messagebox.showwarning("Aviso", "Selecione um funcionário para excluir")
                return
            
            funcionario_id = item_selecionado[0]
            
            # Buscar dados do funcionário
            funcionario = obter_funcionario_por_id(funcionario_id)
            if not funcionario:
                messagebox.showerror("Erro", "Funcionário não encontrado")
                return
            
            nome_funcionario = funcionario.get('nome', 'Desconhecido')
            
            # Confirmar exclusão
            resposta = messagebox.askyesno(
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir o funcionário '{nome_funcionario}'?\n\n"
                f"Esta ação não pode ser desfeita.",
                icon='warning'
            )
            
            if not resposta:
                return
            
            # Excluir funcionário
            sucesso, mensagem = excluir_funcionario(funcionario_id, verificar_vinculos=True)
            
            if sucesso:
                messagebox.showinfo("Sucesso", mensagem)
                self._atualizar_tabela()
            else:
                messagebox.showerror("Erro", mensagem)
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir funcionário: {str(e)}")
            self.logger.exception(f"Erro ao excluir funcionário: {e}")
    
    def _gerar_historico(self, aluno_id: int):
        """Gera histórico escolar do aluno."""
        from historico_escolar import historico_escolar
        
        try:
            # Worker para geração em background
            def _worker():
                # historico_escolar retorna buffer ou None
                return historico_escolar(aluno_id)
            
            def _on_done(resultado):
                if resultado:
                    messagebox.showinfo("Concluído", "Histórico escolar gerado com sucesso.")
                else:
                    messagebox.showwarning("Aviso", "Nenhum dado disponível para o histórico.")
            
            def _on_error(exc):
                messagebox.showerror("Erro", f"Falha ao gerar histórico: {exc}")
            
            try:
                from utils.executor import submit_background
                submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=self.app.janela)
            except Exception:
                from threading import Thread
                def _thread_worker():
                    try:
                        res = _worker()
                        self.app.janela.after(0, lambda: _on_done(res))
                    except Exception as e:
                        self.app.janela.after(0, lambda: _on_error(e))
                Thread(target=_thread_worker, daemon=True).start()
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar histórico: {str(e)}")
            self.logger.exception(f"Erro ao gerar histórico: {e}")
    
    def _gerar_boletim(self, aluno_id: int):
        """Gera boletim do aluno usando boletim_service."""
        from services.boletim_service import gerar_boletim_ou_transferencia
        
        try:
            # Worker para geração em background
            def _worker():
                return gerar_boletim_ou_transferencia(aluno_id)
            
            def _on_done(resultado):
                sucesso, mensagem = resultado
                if sucesso:
                    messagebox.showinfo("Concluído", mensagem)
                else:
                    messagebox.showwarning("Aviso", mensagem)
            
            def _on_error(exc):
                messagebox.showerror("Erro", f"Falha ao gerar documento: {exc}")
            
            try:
                from utils.executor import submit_background
                submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=self.app.janela)
            except Exception:
                from threading import Thread
                def _thread_worker():
                    try:
                        res = _worker()
                        self.app.janela.after(0, lambda: _on_done(res))
                    except Exception as e:
                        self.app.janela.after(0, lambda: _on_error(e))
                Thread(target=_thread_worker, daemon=True).start()
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar boletim: {str(e)}")
            self.logger.exception(f"Erro ao gerar boletim: {e}")
    
    def _gerar_declaracao_aluno(self, aluno_id: int):
        """Gera declaração para aluno usando declaracao_service."""
        from services.declaracao_service import (
            obter_dados_aluno_para_declaracao,
            validar_dados_declaracao,
            registrar_geracao_declaracao
        )
        from Gerar_Declaracao_Aluno import gerar_declaracao_aluno as gerar_declaracao_aluno_legacy
        from tkinter import StringVar, OptionMenu, Entry
        
        try:
            # Dialog para selecionar tipo de declaração
            dialog = Toplevel(self.app.janela)
            dialog.title("Tipo de Declaração")
            dialog.geometry("380x220")
            dialog.transient(self.app.janela)
            dialog.focus_force()
            dialog.grab_set()
            dialog.configure(bg=self.app.colors['co0'])
            
            opcao = StringVar(dialog)
            opcao.set("Transferência")
            opcoes = ["Transferência", "Bolsa Família", "Trabalho", "Outros"]
            
            Label(dialog, text="Selecione o tipo de declaração:", font=("Ivy", 12), 
                  bg=self.app.colors['co0'], fg=self.app.colors['co7']).pack(pady=10)
            
            option_menu = OptionMenu(dialog, opcao, *opcoes)
            option_menu.config(bg=self.app.colors['co0'], fg=self.app.colors['co7'])
            option_menu.pack(pady=5)
            
            # Frame para motivo "Outros"
            motivo_frame = Frame(dialog, bg=self.app.colors['co0'])
            motivo_frame.pack(pady=5, fill='x', padx=20)
            Label(motivo_frame, text="Especifique o motivo:", font=("Ivy", 11), 
                  bg=self.app.colors['co0'], fg=self.app.colors['co7']).pack(anchor='w')
            motivo_entry = Entry(motivo_frame, width=40, font=("Ivy", 11))
            motivo_entry.pack(fill='x', pady=5)
            motivo_frame.pack_forget()
            
            def atualizar_interface(*args):
                if opcao.get() == "Outros":
                    motivo_frame.pack(pady=5, fill='x', padx=20)
                    dialog.geometry("380px220")
                    motivo_entry.focus_set()
                else:
                    motivo_frame.pack_forget()
                    dialog.geometry("380x170")
            
            opcao.trace_add("write", atualizar_interface)
            
            def confirmar():
                opcao_selecionada = opcao.get()
                motivo_outros = ""
                
                if opcao_selecionada == "Outros":
                    motivo_outros = motivo_entry.get().strip()
                    if not motivo_outros:
                        messagebox.showwarning("Aviso", "Por favor, especifique o motivo.")
                        return
                
                # Obter dados via service
                dados_aluno = obter_dados_aluno_para_declaracao(aluno_id)
                if not dados_aluno:
                    messagebox.showerror("Erro", "Não foi possível obter dados do aluno.")
                    dialog.destroy()
                    return
                
                # Validar dados
                valido, mensagem = validar_dados_declaracao('Aluno', dados_aluno, opcao_selecionada)
                if not valido:
                    messagebox.showwarning("Aviso", mensagem)
                    dialog.destroy()
                    return
                
                dialog.destroy()
                
                # Preparar marcações para função legacy
                marcacoes = [[False] * 4 for _ in range(1)]
                if opcao_selecionada in opcoes:
                    index = opcoes.index(opcao_selecionada)
                    marcacoes[0][index] = True
                
                # Worker para geração em background
                def _worker():
                    resultado = gerar_declaracao_aluno_legacy(aluno_id, marcacoes, motivo_outros)
                    # Registrar auditoria
                    registrar_geracao_declaracao(
                        pessoa_id=aluno_id,
                        tipo_pessoa='Aluno',
                        tipo_declaracao=opcao_selecionada,
                        motivo_outros=motivo_outros if opcao_selecionada == 'Outros' else None
                    )
                    return resultado
                
                def _on_done(resultado):
                    messagebox.showinfo("Concluído", "Declaração gerada com sucesso.")
                
                def _on_error(exc):
                    messagebox.showerror("Erro", f"Falha ao gerar declaração: {exc}")
                
                try:
                    from utils.executor import submit_background
                    submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=self.app.janela)
                except Exception:
                    from threading import Thread
                    def _thread_worker():
                        try:
                            res = _worker()
                            self.app.janela.after(0, lambda: _on_done(res))
                        except Exception as e:
                            self.app.janela.after(0, lambda: _on_error(e))
                    Thread(target=_thread_worker, daemon=True).start()
            
            Button(dialog, text="Confirmar", command=confirmar, 
                   bg=self.app.colors['co2'], fg=self.app.colors['co0']).pack(pady=10)
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir diálogo de declaração: {str(e)}")
            self.logger.exception(f"Erro ao gerar declaração de aluno: {e}")
    
    def _gerar_declaracao_funcionario(self, funcionario_id: int):
        """Gera declaração para funcionário usando declaracao_service."""
        from services.declaracao_service import (
            obter_dados_funcionario_para_declaracao,
            validar_dados_declaracao,
            registrar_geracao_declaracao
        )
        from Funcionario import gerar_declaracao_funcionario as gerar_declaracao_funcionario_legacy
        
        try:
            # Obter dados via service
            dados_funcionario = obter_dados_funcionario_para_declaracao(funcionario_id)
            if not dados_funcionario:
                messagebox.showerror("Erro", "Não foi possível obter dados do funcionário.")
                return
            
            # Validar dados
            valido, mensagem = validar_dados_declaracao('Funcionário', dados_funcionario, 'Trabalho')
            if not valido:
                messagebox.showwarning("Aviso", mensagem)
                return
            
            # Worker para geração em background
            def _worker():
                resultado = gerar_declaracao_funcionario_legacy(funcionario_id)
                # Registrar auditoria
                registrar_geracao_declaracao(
                    pessoa_id=funcionario_id,
                    tipo_pessoa='Funcionário',
                    tipo_declaracao='Trabalho',
                    motivo_outros=None
                )
                return resultado
            
            def _on_done(resultado):
                messagebox.showinfo("Concluído", "Declaração gerada com sucesso.")
            
            def _on_error(exc):
                messagebox.showerror("Erro", f"Falha ao gerar declaração: {exc}")
            
            try:
                from utils.executor import submit_background
                submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=self.app.janela)
            except Exception:
                from threading import Thread
                def _thread_worker():
                    try:
                        res = _worker()
                        self.app.janela.after(0, lambda: _on_done(res))
                    except Exception as e:
                        self.app.janela.after(0, lambda: _on_error(e))
                Thread(target=_thread_worker, daemon=True).start()
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar declaração: {str(e)}")
            self.logger.exception(f"Erro ao gerar declaração de funcionário: {e}")
    
    def _matricular_aluno(self, aluno_id: int):
        """Matricula aluno usando MatriculaModal."""
        from ui.matricula_modal import abrir_matricula_modal
        from services.aluno_service import obter_aluno_por_id
        
        try:
            # Buscar nome do aluno
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
        """Edita matrícula do aluno usando MatriculaModal."""
        from ui.matricula_modal import abrir_matricula_modal
        from services.aluno_service import obter_aluno_por_id
        
        try:
            # Buscar nome do aluno
            aluno = obter_aluno_por_id(aluno_id)
            if not aluno:
                messagebox.showerror("Erro", "Aluno não encontrado")
                return
            
            nome_aluno = aluno.get('nome', 'Desconhecido')
            
            # Modal detecta automaticamente se aluno já tem matrícula
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
