"""
Módulo de interface modal para matrícula de alunos.
Interface desacoplada que usa services/matricula_service.py.
"""

from tkinter import Toplevel, Label, Frame, Button, messagebox, StringVar
from tkinter import ttk
from typing import Optional, Callable, Dict, List
import logging
from src.utils.dates import aplicar_mascara_data

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
        """Cria a interface do modal (estilo Sprint 15 - backup)."""
        try:
            # Importar serviços
            from src.services.matricula_service import (
                obter_ano_letivo_atual,
                obter_series_disponiveis
            )
            from datetime import datetime
            from tkinter import Entry, W, X, BOTH, StringVar
            
            # Verificar ano letivo
            self.ano_letivo_id = obter_ano_letivo_atual()
            if not self.ano_letivo_id:
                messagebox.showerror("Erro", "Ano letivo atual não encontrado")
                return
            
            # Obter ano letivo
            from db.connection import get_connection
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ano_letivo FROM anosletivos WHERE id = %s", (self.ano_letivo_id,))
                resultado = cursor.fetchone()
                ano_letivo = resultado[0] if resultado else "Atual"
                cursor.close()
            
            # Criar janela (estilo backup Sprint 15)
            self.janela = Toplevel(self.parent)
            self.janela.title(f"Matricular Aluno - {self.nome_aluno}")
            self.janela.geometry('500x520')
            self.janela.configure(background=self.colors.get('co1', '#003A70'))
            self.janela.transient(self.parent)
            self.janela.focus_force()
            self.janela.grab_set()
            
            # Frame principal
            frame_matricula = Frame(
                self.janela,
                bg=self.colors.get('co1', '#003A70'),
                padx=20,
                pady=20
            )
            frame_matricula.pack(fill=BOTH, expand=True)
            
            # Título
            Label(
                frame_matricula,
                text="Matrícula de Aluno",
                font=("Arial", 14, "bold"),
                bg=self.colors.get('co1', '#003A70'),
                fg=self.colors.get('co7', '#333333')
            ).pack(pady=(0, 20))
            
            # Informações do aluno
            info_frame = Frame(frame_matricula, bg=self.colors.get('co1', '#003A70'))
            info_frame.pack(fill=X, pady=10)
            
            Label(
                info_frame,
                text=f"Aluno: {self.nome_aluno}",
                font=("Arial", 12),
                bg=self.colors.get('co1', '#003A70'),
                fg=self.colors.get('co4', '#4A86E8')
            ).pack(anchor=W)
            
            Label(
                info_frame,
                text=f"Ano Letivo: {ano_letivo}",
                font=("Arial", 12),
                bg=self.colors.get('co1', '#003A70'),
                fg=self.colors.get('co4', '#4A86E8')
            ).pack(anchor=W)
            
            # Selecionar Série
            serie_frame = Frame(frame_matricula, bg=self.colors.get('co1', '#003A70'))
            serie_frame.pack(fill=X, pady=10)
            
            Label(
                serie_frame,
                text="Série:",
                bg=self.colors.get('co1', '#003A70'),
                fg=self.colors.get('co4', '#4A86E8')
            ).pack(anchor=W, pady=(5, 0))
            
            self.serie_var = StringVar()
            self.cb_serie = ttk.Combobox(
                serie_frame,
                textvariable=self.serie_var,
                width=40,
                state="readonly"
            )
            self.cb_serie.pack(fill=X, pady=(0, 5))
            
            # Selecionar Turma
            turma_frame = Frame(frame_matricula, bg=self.colors.get('co1', '#003A70'))
            turma_frame.pack(fill=X, pady=10)
            
            Label(
                turma_frame,
                text="Turma:",
                bg=self.colors.get('co1', '#003A70'),
                fg=self.colors.get('co4', '#4A86E8')
            ).pack(anchor=W, pady=(5, 0))
            
            self.turma_var = StringVar()
            self.cb_turma = ttk.Combobox(
                turma_frame,
                textvariable=self.turma_var,
                width=40,
                state="readonly"
            )
            self.cb_turma.pack(fill=X, pady=(0, 5))
            
            # Data da matrícula
            data_frame = Frame(frame_matricula, bg=self.colors.get('co1', '#003A70'))
            data_frame.pack(fill=X, pady=10)
            
            Label(
                data_frame,
                text="Data da Matrícula (dd/mm/aaaa):",
                bg=self.colors.get('co1', '#003A70'),
                fg=self.colors.get('co4', '#4A86E8')
            ).pack(anchor=W, pady=(5, 0))
            
            self.data_matricula_var = StringVar()
            self.data_matricula_var.set(datetime.now().strftime('%d/%m/%Y'))
            entry_data_matricula = Entry(
                data_frame,
                textvariable=self.data_matricula_var,
                width=42,
                font=("Arial", 10)
            )
            entry_data_matricula.pack(fill=X, pady=(0, 5))
            aplicar_mascara_data(entry_data_matricula)
            
            # Status da matrícula
            status_frame = Frame(frame_matricula, bg=self.colors.get('co1', '#003A70'))
            status_frame.pack(fill=X, pady=10)
            
            Label(
                status_frame,
                text="Status:",
                bg=self.colors.get('co1', '#003A70'),
                fg=self.colors.get('co4', '#4A86E8')
            ).pack(anchor=W, pady=(5, 0))
            
            self.status_var = StringVar()
            self.cb_status = ttk.Combobox(
                status_frame,
                textvariable=self.status_var,
                width=40,
                state="readonly",
                values=['Ativo', 'Transferido', 'Evadido', 'Concluído']
            )
            self.cb_status.pack(fill=X, pady=(0, 5))
            self.cb_status.set('Ativo')  # Valor padrão
            
            # Carregar séries
            self._carregar_series()

            # Vincular evento de mudança de série
            self.cb_serie.bind('<<ComboboxSelected>>', lambda e: self._carregar_turmas())

            # Se já houver matrícula, preencher os campos (série, turma, data)
            # IMPORTANTE: Fazer isso DEPOIS de carregar séries/turmas
            self._preencher_matricula_existente()
            
            # Botões
            btn_frame = Frame(frame_matricula, bg=self.colors.get('co1', '#003A70'))
            btn_frame.pack(pady=20)
            
            # Determinar texto do botão baseado na existência de matrícula
            texto_botao = "Matricular"
            if hasattr(self, 'matricula_existente') and self.matricula_existente:
                texto_botao = "Salvar"
            
            Button(
                btn_frame,
                text=texto_botao,
                command=self._confirmar_matricula,
                font=("Arial", 10, "bold"),
                bg=self.colors.get('co2', '#77B341'),
                fg='#ffffff',
                width=14,
                relief='raised'
            ).pack(side='left', padx=5)
            
            Button(
                btn_frame,
                text="Cancelar",
                command=self.janela.destroy,
                font=("Arial", 10),
                bg=self.colors.get('co8', '#BF3036'),
                fg='#ffffff',
                width=14,
                relief='raised'
            ).pack(side='left', padx=5)
            
            # Focar no primeiro campo
            self.cb_serie.focus()
            
        except Exception as e:
            self.logger.exception(f"Erro ao criar interface de matrícula: {e}")
            messagebox.showerror("Erro", f"Erro ao criar interface: {str(e)}")
    
    def _carregar_series(self):
        """Carrega as séries disponíveis."""
        try:
            from src.services.matricula_service import obter_series_disponiveis
            
            series = obter_series_disponiveis()
            
            if not series:
                self.logger.error("Nenhuma série disponível")
                messagebox.showerror("Erro", "Não há séries disponíveis para matrícula")
                return
            
            # Criar dicionário série_nome -> série_id
            self.series_map = {s['nome']: s['id'] for s in series}
            
            # Configurar combobox
            self.cb_serie['values'] = list(self.series_map.keys())
            
            # NÃO selecionar automaticamente - será feito em _selecionar_serie_inicial()
            
        except Exception as e:
            self.logger.exception(f"Erro ao carregar séries: {e}")
            messagebox.showerror("Erro", "Erro ao carregar séries")
    
    def _carregar_turmas(self, event=None):
        """Carrega turmas da série selecionada."""
        turmas = []
        try:
            # Garantir para o analisador de tipos que as variáveis foram inicializadas
            assert self.serie_var is not None
            assert self.turma_var is not None
            assert self.ano_letivo_id is not None, "ano_letivo_id não definido"

            serie_nome = self.serie_var.get()
            if not serie_nome:
                return
            
            serie_id = self.series_map.get(serie_nome)
            if not serie_id:
                return
            
            from db.connection import get_connection
            
            # Buscar turmas da série no ano letivo atual (escola_id=60)
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT id, COALESCE(NULLIF(nome, ''), turno) as nome_turma
                    FROM turmas 
                    WHERE serie_id = %s 
                    AND ano_letivo_id = %s 
                    AND escola_id = 60
                    ORDER BY turno, nome
                """, (serie_id, self.ano_letivo_id))
                turmas = cursor.fetchall()
                cursor.close()
            
            if not turmas:
                self.cb_turma['values'] = []
                self.turma_var.set('')
                # NÃO mostrar aviso aqui - será tratado em _selecionar_serie_inicial
                return
            
            # Se houver apenas 1 turma, renomear para "Única"
            if len(turmas) == 1:
                turmas[0]['nome_turma'] = 'Única'
            
            # Criar dicionário turma_nome -> turma_id
            self.turmas_map = {t['nome_turma']: t['id'] for t in turmas}
            
            # Configurar combobox
            self.cb_turma['values'] = list(self.turmas_map.keys())
            if self.cb_turma['values']:
                self.cb_turma.current(0)  # Selecionar primeira turma
                
        except Exception as e:
            self.logger.exception(f"Erro ao carregar turmas: {e}")
            messagebox.showerror("Erro", "Erro ao carregar turmas")
    
    def _atualizar_turmas(self, event=None):
        """Atualiza lista de turmas quando série é selecionada (mantido para compatibilidade)."""
        # Método mantido para compatibilidade, mas agora usa _carregar_turmas
        self._carregar_turmas(event)
    
    def _preencher_matricula_existente(self):
        """Preenche os campos se já existir matrícula para o aluno."""
        try:
            # Garantir que variáveis essenciais foram inicializadas
            assert self.ano_letivo_id is not None, "ano_letivo_id não definido"
            assert self.serie_var is not None
            assert self.turma_var is not None
            assert self.data_matricula_var is not None
            assert self.status_var is not None
            from src.services.matricula_service import obter_matricula_aluno
            from datetime import datetime
            
            matricula = obter_matricula_aluno(self.aluno_id, self.ano_letivo_id)
            
            # Guardar flag de matrícula existente
            self.matricula_existente = matricula is not None
            
            if not matricula:
                # Se não há matrícula, selecionar primeira série que tenha turmas
                self._selecionar_serie_inicial()
                return
            
            # Preencher status
            status_db = matricula.get('status', 'Ativo')
            self.status_var.set(status_db)
            
            # Preencher data
            data_db = matricula.get('data_matricula')
            
            if data_db:
                try:
                    if hasattr(data_db, 'strftime'):
                        data_str = data_db.strftime('%d/%m/%Y')
                    else:
                        data_str = datetime.strptime(str(data_db)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
                    self.data_matricula_var.set(data_str)
                except Exception as e:
                    self.logger.warning(f"Erro ao converter data_matricula: {e}")
            
            # Preencher série
            serie_name = matricula.get('serie')
            
            if serie_name and hasattr(self, 'series_map'):
                if serie_name in self.series_map:
                    self.serie_var.set(serie_name)
                    
                    # Recarregar turmas da série selecionada
                    self._carregar_turmas()
            
            # Preencher turma
            turma_name = matricula.get('turma')
            turma_id_db = matricula.get('turma_id')
            
            if hasattr(self, 'turmas_map'):
                # Se houver apenas 1 turma, ela foi renomeada para "Única"
                if len(self.turmas_map) == 1:
                    self.turma_var.set('Única')
                elif turma_name and turma_name in self.turmas_map:
                    self.turma_var.set(turma_name)
                elif turma_id_db:
                    # Procurar pelo ID
                    for nome, idv in self.turmas_map.items():
                        if idv == turma_id_db:
                            self.turma_var.set(nome)
                            break
            
        except Exception as e:
            self.logger.error(f"Erro ao preencher matrícula existente: {e}", exc_info=True)
    
    def _selecionar_serie_inicial(self):
        """Seleciona primeira série que tenha turmas cadastradas."""
        try:
            from db.connection import get_connection

            # Garantir que a combobox, variáveis e o ano letivo foram inicializados
            assert hasattr(self, 'cb_serie')
            assert self.serie_var is not None
            assert self.ano_letivo_id is not None, "ano_letivo_id não definido"
            
            # Percorrer séries até encontrar uma com turmas
            for serie_nome in self.cb_serie['values']:
                serie_id = self.series_map.get(serie_nome)
                if not serie_id:
                    continue
                
                # Verificar se há turmas para esta série
                with get_connection() as conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT COUNT(*) as total
                        FROM turmas 
                        WHERE serie_id = %s 
                        AND ano_letivo_id = %s 
                        AND escola_id = 60
                    """, (serie_id, self.ano_letivo_id))
                    resultado = cursor.fetchone()
                    cursor.close()
                    
                    total = resultado['total'] if resultado else 0
                    
                    if total > 0:
                        # Encontrou série com turmas!
                        self.serie_var.set(serie_nome)
                        self._carregar_turmas()
                        return
            
            # Se chegou aqui, nenhuma série tem turmas
            if self.cb_serie['values']:
                self.serie_var.set(self.cb_serie['values'][0])
                self._carregar_turmas()
            
        except Exception as e:
            self.logger.error(f"Erro ao selecionar série inicial: {e}", exc_info=True)
    
    def _confirmar_matricula(self):
        """Confirma e executa a matrícula."""
        try:
            # Garantir que variáveis de formulário foram inicializadas
            assert self.serie_var is not None
            assert self.turma_var is not None
            assert self.data_matricula_var is not None
            assert self.status_var is not None
            assert hasattr(self, 'turmas_map')
            from datetime import datetime
            
            # Validar campos
            if not self.serie_var.get():
                messagebox.showwarning("Aviso", "Selecione a série")
                self.cb_serie.focus()
                return
            
            if not self.turma_var.get():
                messagebox.showwarning("Aviso", "Selecione a turma")
                self.cb_turma.focus()
                return
            
            # Validar data
            data_str = self.data_matricula_var.get().strip()
            if not data_str:
                messagebox.showwarning("Aviso", "Informe a data da matrícula")
                return
            
            # Validar status
            status = self.status_var.get()
            if not status:
                messagebox.showwarning("Aviso", "Selecione o status")
                return
            
            # Tentar converter a data
            try:
                data_matricula = datetime.strptime(data_str, '%d/%m/%Y')
            except ValueError:
                messagebox.showerror("Erro", "Data inválida. Use o formato dd/mm/aaaa")
                return
            
            # Obter IDs usando os dicionários
            turma_nome = self.turma_var.get()
            turma_id = self.turmas_map.get(turma_nome)
            
            if not turma_id:
                messagebox.showerror("Erro", "Turma não encontrada")
                return
            
            # Matricular usando serviço
            from src.services.matricula_service import matricular_aluno
            
            sucesso, mensagem = matricular_aluno(
                self.aluno_id,
                turma_id,
                self.ano_letivo_id,
                status=status,
                data_matricula=data_matricula.strftime('%Y-%m-%d')
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
