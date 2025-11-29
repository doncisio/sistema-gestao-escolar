"""
Factory para criação de botões e menus da aplicação.

Este módulo extrai a lógica de criação de botões da função criar_acoes()
do main.py, organizando em uma classe reutilizável e testável.
"""

from tkinter import Frame, Button, Menu, LEFT, RIGHT, RIDGE, X, EW
from tkinter import messagebox
from PIL import Image, ImageTk
from typing import Optional, Callable, Dict, Any
from config_logs import get_logger
from config import perfis_habilitados
from auth.decorators import ControleAcesso

logger = get_logger(__name__)


class ButtonFactory:
    """
    Factory para criação de botões e menus da interface principal.
    
    Encapsula a lógica de criação de botões, menus e suas imagens,
    que antes estava na função criar_acoes() do main.py.
    """
    
    def __init__(self, janela, frame_dados, callbacks, colors: Dict[str, str]):
        """
        Inicializa o ButtonFactory.
        
        Args:
            janela: Janela principal Tk
            frame_dados: Frame onde os botões serão criados
            callbacks: Instância de ActionCallbacksManager com os callbacks
            colors: Dicionário com cores da aplicação (co0-co9)
        """
        self.janela = janela
        self.frame_dados = frame_dados
        self.callbacks = callbacks
        self.colors = colors
        
        # Armazenar referências de imagens para evitar garbage collection
        self._image_refs = {}
        
        logger.debug("ButtonFactory inicializado")
    
    def _load_image(self, path: str, size: tuple = (18, 18)) -> Optional[Any]:
        """
        Carrega e redimensiona uma imagem.
        
        Args:
            path: Caminho do arquivo de imagem
            size: Tupla (largura, altura) para redimensionamento
            
        Returns:
            ImageTk.PhotoImage ou None se não encontrado
        """
        try:
            img = Image.open(path)
            img = img.resize(size)
            photo = ImageTk.PhotoImage(img)
            # Armazenar referência
            self._image_refs[path] = photo
            return photo
        except FileNotFoundError:
            logger.warning(f"Imagem não encontrada: {path}")
            return None
        except Exception as e:
            logger.error(f"Erro ao carregar imagem {path}: {e}")
            return None
    
    def _create_button(self, parent, text: str, command: Callable, 
                       icon_path: Optional[str] = None, bg_color: Optional[str] = None,
                       **kwargs) -> Button:
        """
        Cria um botão com ou sem ícone.
        
        Args:
            parent: Widget pai onde o botão será criado
            text: Texto do botão
            command: Função callback ao clicar
            icon_path: Caminho opcional do ícone
            bg_color: Cor de fundo do botão
            **kwargs: Argumentos adicionais para Button()
            
        Returns:
            Button criado
        """
        # Configurações padrão
        btn_config = {
            'text': text,
            'command': command,
            'compound': LEFT,
            'overrelief': RIDGE,
            'font': ('Ivy 11'),
            'bg': bg_color or self.colors['co4'],
            'fg': self.colors['co0']
        }
        btn_config.update(kwargs)
        
        # Adicionar ícone se disponível
        if icon_path:
            img = self._load_image(icon_path)
            if img:
                btn_config['image'] = img
        
        btn = Button(parent, **btn_config)
        
        # Manter referência da imagem no botão
        if icon_path and icon_path in self._image_refs:
            btn._image_ref = self._image_refs[icon_path]  # type: ignore
        
        return btn
    
    def criar_botoes_principais(self) -> Frame:
        """
        Cria os botões principais da aplicação.
        
        Os botões são criados apenas se o usuário tem permissão para
        a ação correspondente (quando perfis estão habilitados).
        
        Returns:
            Frame contendo os botões
        """
        # Frame para os botões de ação
        botoes_frame = Frame(self.frame_dados, bg=self.colors['co1'])
        botoes_frame.pack(fill=X, expand=True, padx=10, pady=5)
        
        # Configurar grid do frame de botões
        for i in range(7):  # 7 colunas para acomodar todos os botões
            botoes_frame.grid_columnconfigure(i, weight=1)
        
        # Controle de acesso para verificar permissões
        acesso = ControleAcesso()
        coluna = 0
        botoes_criados = 0
        
        # Botão Novo Aluno (requer permissão alunos.criar)
        if acesso.pode('alunos.criar'):
            btn_aluno = self._create_button(
                botoes_frame,
                text="Novo Aluno",
                command=self.callbacks.cadastrar_novo_aluno,
                icon_path='icon/plus.png',
                bg_color=self.colors['co2']
            )
            btn_aluno.grid(row=0, column=coluna, padx=5, pady=5, sticky=EW)
            coluna += 1
            botoes_criados += 1
        
        # Botão Novo Funcionário (requer permissão funcionarios.criar)
        if acesso.pode('funcionarios.criar'):
            btn_funcionario = self._create_button(
                botoes_frame,
                text="Novo Funcionário",
                command=self.callbacks.cadastrar_novo_funcionario,
                icon_path='icon/video-conference.png',
                bg_color=self.colors['co3']
            )
            btn_funcionario.grid(row=0, column=coluna, padx=5, pady=5, sticky=EW)
            coluna += 1
            botoes_criados += 1
        
        # Botão Histórico Escolar (requer permissão alunos.documentos)
        if acesso.pode('alunos.documentos'):
            btn_historico = self._create_button(
                botoes_frame,
                text="Histórico Escolar",
                command=self.callbacks.abrir_historico_escolar,
                icon_path='icon/notebook.png',
                bg_color=self.colors['co4']
            )
            btn_historico.grid(row=0, column=coluna, padx=5, pady=5, sticky=EW)
            coluna += 1
            botoes_criados += 1
        
        # Botão Administração (requer perfil administrador ou coordenador)
        if acesso.is_admin_ou_coordenador():
            btn_admin = self._create_button(
                botoes_frame,
                text="Administração",
                command=self.callbacks.abrir_interface_administrativa,
                icon_path='icon/learning.png',
                bg_color=self.colors['co5']
            )
            btn_admin.grid(row=0, column=coluna, padx=5, pady=5, sticky=EW)
            coluna += 1
            botoes_criados += 1
        
        # Botão Backup (requer permissão sistema.backup)
        if acesso.pode('sistema.backup'):
            btn_backup = self._create_button(
                botoes_frame,
                text="Backup",
                command=lambda: self._fazer_backup(),
                icon_path='icon/book.png',
                bg_color=self.colors['co6']
            )
            btn_backup.grid(row=0, column=coluna, padx=5, pady=5, sticky=EW)
            coluna += 1
            botoes_criados += 1
        
        # Botão Restaurar (requer permissão sistema.backup)
        if acesso.pode('sistema.backup'):
            btn_restaurar = self._create_button(
                botoes_frame,
                text="Restaurar",
                command=lambda: self._restaurar_backup(),
                icon_path='icon/update.png',
                bg_color=self.colors['co9']
            )
            btn_restaurar.grid(row=0, column=coluna, padx=5, pady=5, sticky=EW)
            coluna += 1
            botoes_criados += 1
        
        # Botão Horários (todos podem visualizar horários)
        if acesso.pode('turmas.visualizar'):
            btn_horarios = self._create_button(
                botoes_frame,
                text="Horários",
                command=self.callbacks.abrir_horarios_escolares,
                icon_path='icon/video-conference.png',
                bg_color=self.colors['co3']
            )
            btn_horarios.grid(row=0, column=coluna, padx=5, pady=5, sticky=EW)
            coluna += 1
            botoes_criados += 1
        
        logger.debug(f"Botões principais criados ({botoes_criados} botões)")
        return botoes_frame
    
    def _fazer_backup(self):
        """Callback para o botão de backup."""
        try:
            import Seguranca
            Seguranca.fazer_backup()
        except Exception as e:
            logger.exception(f"Erro ao fazer backup: {e}")
            messagebox.showerror("Erro", f"Erro ao fazer backup: {e}")
    
    def _restaurar_backup(self):
        """Callback para o botão de restaurar."""
        try:
            import Seguranca
            Seguranca.restaurar_backup()
        except Exception as e:
            logger.exception(f"Erro ao restaurar backup: {e}")
            messagebox.showerror("Erro", f"Erro ao restaurar backup: {e}")
    
    def criar_menu_bar(self) -> Menu:
        """
        Cria a barra de menus completa da aplicação.
        
        Os menus e itens são criados baseados nas permissões do usuário
        quando o sistema de perfis está habilitado.
        
        Returns:
            Menu configurado
        """
        menu_font = ('Ivy', 12)
        acesso = ControleAcesso()
        
        # Barra de menu principal
        menu_bar = Menu(self.janela)
        
        # ========== MENU 1: LISTAS (todos podem ver relatórios) ==========
        if acesso.pode('relatorios.visualizar'):
            listas_menu = Menu(menu_bar, tearoff=0, font=menu_font)
            listas_menu.add_command(
                label="Lista Atualizada",
                command=self.callbacks.lista_atualizada,
                font=menu_font
            )
            listas_menu.add_command(
                label="Lista Atualizada SEMED",
                command=self.callbacks.lista_atualizada_semed,
                font=menu_font
            )
            listas_menu.add_command(
                label="Lista de Reunião",
                command=self.callbacks.lista_reuniao,
                font=menu_font
            )
            listas_menu.add_command(
                label="Lista de Notas",
                command=self.callbacks.lista_notas,
                font=menu_font
            )
            listas_menu.add_command(
                label="Lista de Frequências",
                command=self.callbacks.reports.lista_frequencia,
                font=menu_font
            )
            listas_menu.add_separator()
            listas_menu.add_command(
                label="Contatos de Responsáveis",
                command=self.callbacks.relatorio_contatos_responsaveis,
                font=menu_font
            )
            listas_menu.add_command(
                label="Levantamento de Necessidades",
                command=self.callbacks.reports.relatorio_levantamento_necessidades,
                font=menu_font
            )
            listas_menu.add_command(
                label="Lista Alfabética",
                command=self.callbacks.reports.relatorio_lista_alfabetica,
                font=menu_font
            )
            listas_menu.add_command(
                label="Alunos com Transtornos",
                command=self.callbacks.reports.relatorio_alunos_transtornos,
                font=menu_font
            )
            listas_menu.add_separator()
            listas_menu.add_command(
                label="Transferências Expedidas",
                command=self.callbacks.reports.relatorio_lista_transferidos,
                font=menu_font
            )
            listas_menu.add_command(
                label="Transferências Recebidas",
                command=self.callbacks.reports.relatorio_lista_matriculados_depois,
                font=menu_font
            )
            listas_menu.add_separator()
            listas_menu.add_command(
                label="Termo de Responsabilidade",
                command=self.callbacks.reports.relatorio_termo_responsabilidade,
                font=menu_font
            )
            menu_bar.add_cascade(label="Listas", menu=listas_menu, font=menu_font)
        
        # ========== MENU 2: GERENCIAMENTO DE NOTAS (requer permissão notas) ==========
        if acesso.pode_alguma(['notas.visualizar', 'notas.lancar']):
            notas_menu = Menu(menu_bar, tearoff=0, font=menu_font)
            
            # Cadastrar/Editar Notas só aparece se pode lançar notas
            if acesso.pode('notas.lancar'):
                notas_menu.add_command(
                    label="Cadastrar/Editar Notas",
                    command=self.callbacks.abrir_cadastro_notas,
                    font=menu_font
                )
            
            notas_menu.add_command(
                label="Relatório Estatístico de Notas",
                command=lambda: self._abrir_relatorio_analise(),
                font=menu_font
            )
        
            # Adicionar os bimestres - Anos Iniciais (1º ao 5º ano)
            notas_menu.add_separator()
            notas_menu.add_command(
                label="1º bimestre",
                command=lambda: self._nota_bimestre("1º bimestre"),
                font=menu_font
            )
            notas_menu.add_command(
                label="2º bimestre",
                command=lambda: self._nota_bimestre("2º bimestre"),
                font=menu_font
            )
            notas_menu.add_command(
                label="3º bimestre",
                command=lambda: self._nota_bimestre("3º bimestre"),
                font=menu_font
            )
            notas_menu.add_command(
                label="4º bimestre",
                command=lambda: self._nota_bimestre("4º bimestre"),
                font=menu_font
            )
            
            # Adicionar os bimestres - Anos Finais (6º ao 9º ano)
            notas_menu.add_separator()
            notas_menu.add_command(
                label="1º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2("1º bimestre"),
                font=menu_font
            )
            notas_menu.add_command(
                label="2º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2("2º bimestre"),
                font=menu_font
            )
            notas_menu.add_command(
                label="3º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2("3º bimestre"),
                font=menu_font
            )
            notas_menu.add_command(
                label="4º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2("4º bimestre"),
                font=menu_font
            )
            
            notas_menu.add_separator()
            notas_menu.add_command(
                label="Relatório Avançado",
                command=lambda: self._abrir_relatorio_avancado(),
                font=menu_font
            )
            
            # Submenu: Relatórios com Assinatura
            notas_menu.add_separator()
            relatorios_assinatura_menu = Menu(notas_menu, tearoff=0, font=menu_font)
            relatorios_assinatura_menu.add_command(
                label="1º bimestre",
                command=lambda: self._nota_bimestre_com_assinatura("1º bimestre"),
                font=menu_font
            )
            relatorios_assinatura_menu.add_command(
                label="2º bimestre",
                command=lambda: self._nota_bimestre_com_assinatura("2º bimestre"),
                font=menu_font
            )
            relatorios_assinatura_menu.add_command(
                label="3º bimestre",
                command=lambda: self._nota_bimestre_com_assinatura("3º bimestre"),
                font=menu_font
            )
            relatorios_assinatura_menu.add_command(
                label="4º bimestre",
                command=lambda: self._nota_bimestre_com_assinatura("4º bimestre"),
                font=menu_font
            )
            relatorios_assinatura_menu.add_separator()
            relatorios_assinatura_menu.add_command(
                label="1º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2_com_assinatura("1º bimestre"),
                font=menu_font
            )
            relatorios_assinatura_menu.add_command(
                label="2º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2_com_assinatura("2º bimestre"),
                font=menu_font
            )
            relatorios_assinatura_menu.add_command(
                label="3º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2_com_assinatura("3º bimestre"),
                font=menu_font
            )
            relatorios_assinatura_menu.add_command(
                label="4º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2_com_assinatura("4º bimestre"),
                font=menu_font
            )
            relatorios_assinatura_menu.add_separator()
            relatorios_assinatura_menu.add_command(
                label="Relatório Avançado",
                command=lambda: self._abrir_relatorio_avancado_com_assinatura(),
                font=menu_font
            )
            notas_menu.add_cascade(
                label="Relatórios com Assinatura",
                menu=relatorios_assinatura_menu,
                font=menu_font
            )
            
            notas_menu.add_separator()
            notas_menu.add_command(
                label="Ata Geral",
                command=lambda: self._abrir_interface_ata(),
                font=menu_font
            )
            
            notas_menu.add_separator()
            
            # Submenu: Relatórios de Pendências
            pendencias_menu = Menu(notas_menu, tearoff=0, font=menu_font)
            pendencias_menu.add_command(
                label="1º bimestre",
                command=lambda: self._gerar_pendencias_em_bg("1º bimestre", "iniciais"),
                font=menu_font
            )
            pendencias_menu.add_command(
                label="2º bimestre",
                command=lambda: self._gerar_pendencias_em_bg("2º bimestre", "iniciais"),
                font=menu_font
            )
            pendencias_menu.add_command(
                label="3º bimestre",
                command=lambda: self._gerar_pendencias_em_bg("3º bimestre", "iniciais"),
                font=menu_font
            )
            pendencias_menu.add_command(
                label="4º bimestre",
                command=lambda: self._gerar_pendencias_em_bg("4º bimestre", "iniciais"),
                font=menu_font
            )
            pendencias_menu.add_separator()
            pendencias_menu.add_command(
                label="1º bimestre (6º ao 9º ano)",
                command=lambda: self._gerar_pendencias_em_bg("1º bimestre", "finais"),
                font=menu_font
            )
            pendencias_menu.add_command(
                label="2º bimestre (6º ao 9º ano)",
                command=lambda: self._gerar_pendencias_em_bg("2º bimestre", "finais"),
                font=menu_font
            )
            pendencias_menu.add_command(
                label="3º bimestre (6º ao 9º ano)",
                command=lambda: self._gerar_pendencias_em_bg("3º bimestre", "finais"),
                font=menu_font
            )
            pendencias_menu.add_command(
                label="4º bimestre (6º ao 9º ano)",
                command=lambda: self._gerar_pendencias_em_bg("4º bimestre", "finais"),
                font=menu_font
            )
            pendencias_menu.add_separator()
            pendencias_menu.add_command(
                label="Abrir interface",
                command=lambda: self._abrir_relatorio_pendencias(),
                font=menu_font
            )
            notas_menu.add_cascade(
                label="Relatórios de Pendências",
                menu=pendencias_menu,
                font=menu_font
            )
            
            menu_bar.add_cascade(label="Gerenciamento de Notas", menu=notas_menu, font=menu_font)
        
        # ========== MENU 3: SERVIÇOS ==========
        servicos_menu = Menu(menu_bar, tearoff=0, font=menu_font)
        
        # Dashboard (todos podem ver)
        if acesso.pode('dashboard.completo') or acesso.pode('dashboard.pedagogico') or acesso.pode('dashboard.proprio'):
            servicos_menu.add_command(
                label="📊 Ver Dashboard",
                command=lambda: self._mostrar_dashboard(),
                font=menu_font
            )
            servicos_menu.add_separator()
        
        # Submenu: Movimento Mensal (apenas admin/coordenador)
        if acesso.is_admin_ou_coordenador():
            movimento_mensal_menu = Menu(servicos_menu, tearoff=0, font=menu_font)
            movimento_mensal_menu.add_command(
                label="Gerar Relatório",
                command=lambda: self._selecionar_mes_movimento(),
                font=menu_font
            )
            servicos_menu.add_cascade(
                label="Movimento Mensal",
                menu=movimento_mensal_menu,
                font=menu_font
            )
        
        # Solicitação de Professores (apenas admin)
        if acesso.is_admin():
            servicos_menu.add_command(
                label="Solicitação de Professores e Coordenadores",
                command=self.callbacks.abrir_solicitacao_professores,
                font=menu_font
            )
        
        # Gerenciador de Documentos de Funcionários (admin/coordenador)
        if acesso.is_admin_ou_coordenador():
            servicos_menu.add_command(
                label="Gerenciador de Documentos de Funcionários",
                command=self.callbacks.abrir_gerenciador_documentos,
                font=menu_font
            )
        
        # Gerenciador de Documentos do Sistema (admin)
        if acesso.is_admin():
            servicos_menu.add_command(
                label="Gerenciador de Documentos do Sistema",
                command=lambda: self._abrir_gerenciador_documentos_sistema(),
                font=menu_font
            )
        
        # Declaração de Comparecimento (todos podem gerar)
        if acesso.pode('alunos.documentos'):
            servicos_menu.add_command(
                label="Declaração de Comparecimento (Responsável)",
                command=self.callbacks.declaracao_comparecimento,
                font=menu_font
            )
            servicos_menu.add_command(
                label="Crachás Alunos/Responsáveis",
                command=lambda: self._abrir_crachas(),
                font=menu_font
            )
        
        # Importar Notas (admin/coordenador)
        if acesso.is_admin_ou_coordenador():
            servicos_menu.add_command(
                label="Importar Notas do GEDUC (HTML → Excel)",
                command=lambda: self._abrir_importacao_notas_html(),
                font=menu_font
            )
        
        # Transição de Ano Letivo (apenas admin)
        if acesso.pode('sistema.transicao_ano'):
            servicos_menu.add_separator()
            servicos_menu.add_command(
                label="🔄 Transição de Ano Letivo",
                command=self.callbacks.abrir_transicao_ano_letivo,
                font=menu_font
            )
        
        menu_bar.add_cascade(label="Serviços", menu=servicos_menu, font=menu_font)
        
        # ========== MENU 4: GERENCIAMENTO DE FALTAS ==========
        if acesso.pode_alguma(['frequencia.visualizar', 'frequencia.lancar', 'frequencia.lancar_proprias']):
            faltas_menu = Menu(menu_bar, tearoff=0, font=menu_font)
            
            # Lançamento de Frequência de Alunos (professor e admin)
            if acesso.pode_alguma(['frequencia.lancar_proprias', 'frequencia.lancar']):
                faltas_menu.add_command(
                    label="📋 Lançar Frequência de Alunos",
                    command=self.callbacks.abrir_lancamento_frequencia_alunos,
                    font=menu_font
                )
                faltas_menu.add_separator()
            
            # Cadastrar/Editar Faltas de Funcionários (apenas admin)
            if acesso.pode('frequencia.lancar'):
                faltas_menu.add_command(
                    label="Cadastrar/Editar Faltas (Funcionários)",
                    command=self.callbacks.abrir_cadastro_faltas,
                    font=menu_font
                )
                faltas_menu.add_separator()
            
            # Folhas e Resumo de Ponto (admin)
            if acesso.is_admin():
                faltas_menu.add_command(
                    label="Gerar Folhas de Ponto",
                    command=lambda: self._abrir_dialogo_folhas_ponto(),
                    font=menu_font
                )
                faltas_menu.add_command(
                    label="Gerar Resumo de Ponto",
                    command=lambda: self._abrir_dialogo_resumo_ponto(),
                    font=menu_font
                )
            
            menu_bar.add_cascade(label="Gerenciamento de Faltas", menu=faltas_menu, font=menu_font)
        
        # ========== MENU 5: BANCO DE QUESTÕES (quando habilitado) ==========
        from config import banco_questoes_habilitado
        if banco_questoes_habilitado():
            # Professores, coordenadores e admins podem acessar
            if acesso.pode_alguma(['frequencia.lancar_proprias', 'frequencia.lancar', 'sistema.usuarios']):
                questoes_menu = Menu(menu_bar, tearoff=0, font=menu_font)
                
                questoes_menu.add_command(
                    label="📚 Banco de Questões BNCC",
                    command=lambda: self._abrir_banco_questoes(),
                    font=menu_font
                )
                
                menu_bar.add_cascade(label="📚 Avaliações", menu=questoes_menu, font=menu_font)
        
        # ========== MENU 6: DOCUMENTOS DA ESCOLA (todos podem ver) ==========
        documentos_menu = Menu(menu_bar, tearoff=0, font=menu_font)
        documentos_menu.add_command(
            label="Estatuto da Escola",
            command=lambda: self._abrir_documento_escola('estatuto'),
            font=menu_font
        )
        documentos_menu.add_command(
            label="PPP da Escola",
            command=lambda: self._abrir_documento_escola('ppp'),
            font=menu_font
        )
        documentos_menu.add_command(
            label="CNPJ da Escola",
            command=lambda: self._abrir_documento_escola('cnpj'),
            font=menu_font
        )
        menu_bar.add_cascade(label="Documentos da Escola", menu=documentos_menu, font=menu_font)
        
        # ========== MENU 7: USUÁRIO (quando perfis habilitados) ==========
        if perfis_habilitados():
            usuario_menu = Menu(menu_bar, tearoff=0, font=menu_font)
            
            # Info do usuário
            nome_usuario = acesso.get_nome_usuario()
            perfil_atual = acesso.get_perfil_atual()
            perfil_display = perfil_atual.title() if perfil_atual else "N/A"
            
            usuario_menu.add_command(
                label=f"👤 {nome_usuario}",
                command=lambda: None,
                font=menu_font,
                state='disabled'
            )
            usuario_menu.add_command(
                label=f"📋 Perfil: {perfil_display}",
                command=lambda: None,
                font=menu_font,
                state='disabled'
            )
            usuario_menu.add_separator()
            
            # Trocar senha
            usuario_menu.add_command(
                label="🔑 Trocar Senha",
                command=lambda: self._abrir_troca_senha(),
                font=menu_font
            )
            usuario_menu.add_separator()
            
            # Gestão de Usuários (apenas admin)
            if acesso.pode('sistema.usuarios'):
                usuario_menu.add_command(
                    label="⚙️ Gestão de Usuários",
                    command=lambda: self._abrir_gestao_usuarios(),
                    font=menu_font
                )
                usuario_menu.add_separator()
            
            # Logout
            usuario_menu.add_command(
                label="🚪 Sair",
                command=lambda: self._fazer_logout(),
                font=menu_font
            )
            
            menu_bar.add_cascade(label="👤 Usuário", menu=usuario_menu, font=menu_font)
        
        logger.debug(f"Barra de menus criada (perfis_habilitados={perfis_habilitados()})")
        return menu_bar
    
    def _abrir_troca_senha(self):
        """Abre janela para trocar senha."""
        try:
            from ui.login import TrocaSenhaWindow
            from auth.usuario_logado import UsuarioLogado

            usuario = UsuarioLogado.get_usuario()
            if not usuario:
                messagebox.showwarning("Atenção", "Nenhum usuário logado para trocar senha.")
                return

            # abrir janela de troca de senha para o usuário atual
            TrocaSenhaWindow(self.janela, usuario)
        except Exception as e:
            logger.exception(f"Erro ao abrir troca de senha: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir troca de senha: {e}")
    
    def _abrir_gestao_usuarios(self):
        """Abre interface de gestão de usuários."""
        try:
            from ui.gestao_usuarios import abrir_gestao_usuarios
            abrir_gestao_usuarios(self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir gestão de usuários: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir gestão de usuários: {e}")
    
    def _abrir_banco_questoes(self):
        """Abre a interface do Banco de Questões BNCC."""
        try:
            from banco_questoes.ui import abrir_banco_questoes
            abrir_banco_questoes(janela_principal=self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir banco de questões: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir banco de questões: {e}")
    
    def _fazer_logout(self):
        """Realiza logout e fecha a aplicação."""
        try:
            from auth.auth_service import AuthService
            from auth.usuario_logado import UsuarioLogado
            
            resposta = messagebox.askyesno(
                "Confirmar Logout",
                "Deseja realmente sair do sistema?"
            )
            
            if resposta:
                # Fazer logout (registrar com usuário atual)
                from auth.usuario_logado import UsuarioLogado
                usuario = UsuarioLogado.get_usuario()
                if usuario:
                    AuthService.logout(usuario)
                UsuarioLogado.limpar()
                
                # Fechar janela principal
                self.janela.quit()
                self.janela.destroy()
                
                logger.info("Logout realizado com sucesso")
        except Exception as e:
            logger.exception(f"Erro ao fazer logout: {e}")
            messagebox.showerror("Erro", f"Erro ao fazer logout: {e}")
    
    def _gerar_relatorio_notas_wrapper(self):
        """Wrapper para gerar relatório de notas"""
        try:
            from services.report_service import gerar_relatorio_notas
            gerar_relatorio_notas()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório de notas: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")
    
    def _gerar_relatorio_notas_com_assinatura_wrapper(self):
        """Wrapper para gerar relatório de notas com assinatura"""
        try:
            from abrir_relatorio_avancado_com_assinatura import main as gerar_relatorio_com_assinatura  # type: ignore
            gerar_relatorio_com_assinatura()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório de notas: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")
    
    def _abrir_relatorio_avancado(self):
        """Wrapper para abrir relatório avançado"""
        try:
            from abrir_relatorio_avancado_com_assinatura import main as abrir_relatorio_avancado  # type: ignore
            abrir_relatorio_avancado()
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório avançado: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir relatório: {e}")
    
    def _abrir_relatorio_pendencias(self):
        """Wrapper para abrir relatório de pendências"""
        try:
            from services.report_service import gerar_relatorio_pendencias
            # TODO: Adicionar parâmetros apropriados
            logger.warning("Relatório de pendências precisa de implementação dos parâmetros")
            messagebox.showinfo("Info", "Função em implementação - parâmetros necessários")
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório de pendências: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir relatório: {e}")
    
    def _gerar_declaracao_generica(self):
        """Wrapper para gerar declaração genérica"""
        try:
            from Gerar_Declaracao_Aluno import main as gerar_declaracao  # type: ignore
            gerar_declaracao()
        except Exception as e:
            logger.exception(f"Erro ao gerar declaração: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declaração: {e}")
    
    def _abrir_relatorio_analise(self):
        """Wrapper para abrir relatório estatístico de análise de notas"""
        try:
            from relatorio_analise_notas import abrir_relatorio_analise_notas
            abrir_relatorio_analise_notas(janela_principal=self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório de análise: {e}")
            messagebox.showerror("Erro", f"Não foi possível abrir o relatório: {e}")
    
    def _selecionar_mes_movimento(self):
        """Wrapper para seleção de mês de movimento mensal"""
        try:
            from tkinter import Menu
            from datetime import datetime
            
            menu_meses = Menu(self.janela, tearoff=0)
            mes_atual = datetime.now().month
            
            meses = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ]
            
            meses_disponiveis = meses[:mes_atual]
            
            for i, mes in enumerate(meses_disponiveis, 1):
                menu_meses.add_command(
                    label=mes,
                    command=lambda m=i: self.callbacks.relatorio_movimentacao_mensal(m)
                )
            
            try:
                x = self.janela.winfo_pointerx()
                y = self.janela.winfo_pointery()
                menu_meses.post(x, y)
            except:
                menu_meses.post(self.janela.winfo_rootx() + 100, self.janela.winfo_rooty() + 100)
        except Exception as e:
            logger.exception(f"Erro ao abrir menu de movimento mensal: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir menu: {e}")
    
    def _abrir_gerenciador_documentos_sistema(self):
        """Wrapper para abrir gerenciador de documentos do sistema"""
        try:
            self.janela.withdraw()
            
            from tkinter import Toplevel
            from GerenciadorDocumentosSistema import GerenciadorDocumentosSistema
            
            janela_docs = Toplevel(self.janela)
            janela_docs.title("Gerenciador de Documentos do Sistema")
            app = GerenciadorDocumentosSistema(janela_docs)
            janela_docs.focus_force()
            janela_docs.grab_set()
            
            def ao_fechar():
                self.janela.deiconify()
                janela_docs.destroy()
            
            janela_docs.protocol("WM_DELETE_WINDOW", ao_fechar)
        except Exception as e:
            logger.exception(f"Erro ao abrir gerenciador de documentos do sistema: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir gerenciador: {e}")
            self.janela.deiconify()
    
    def _abrir_crachas(self):
        """Wrapper para abrir interface de crachás"""
        try:
            from ui.interfaces_extended import abrir_interface_crachas
            abrir_interface_crachas(self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir interface de crachás: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir crachás: {e}")
    
    def _abrir_importacao_notas_html(self):
        """Wrapper para abrir importação de notas do HTML"""
        try:
            self.janela.withdraw()
            from importar_notas_html import interface_importacao
            interface_importacao(janela_pai=self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir importação de notas: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir importação: {e}")
            self.janela.deiconify()
    
    def _mostrar_dashboard(self):
        """Mostra o dashboard com estatísticas de alunos"""
        try:
            # Obter referência ao app através do callback manager
            # O app é passado via janela ou podemos acessar através de um atributo
            app = getattr(self.janela, '_app_instance', None)
            
            if app and app.dashboard_manager:
                # Limpar frame da tabela
                if 'frame_tabela' in app.frames:
                    for widget in app.frames['frame_tabela'].winfo_children():
                        widget.destroy()
                
                # Criar dashboard
                app.dashboard_manager.criar_dashboard()
                logger.info("Dashboard exibido com sucesso")
            else:
                messagebox.showwarning("Aviso", "Dashboard não está disponível no momento.")
                logger.warning("Dashboard manager não inicializado")
                
        except Exception as e:
            logger.exception(f"Erro ao mostrar dashboard: {e}")
            messagebox.showerror("Erro", f"Erro ao mostrar dashboard: {e}")
    
    def _abrir_dialogo_folhas_ponto(self):
        """Wrapper para abrir diálogo de folhas de ponto"""
        try:
            from ui.dialogs_extended import abrir_dialogo_folhas_ponto
            abrir_dialogo_folhas_ponto(self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir diálogo de folhas de ponto: {e}")
            messagebox.showerror("Erro", f"Erro: {e}")
    
    def _abrir_dialogo_resumo_ponto(self):
        """Wrapper para abrir diálogo de resumo de ponto"""
        try:
            from ui.dialogs_extended import abrir_dialogo_resumo_ponto
            abrir_dialogo_resumo_ponto(self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir diálogo de resumo de ponto: {e}")
            messagebox.showerror("Erro", f"Erro: {e}")
    
    def _abrir_documento_escola(self, chave: str):
        """Wrapper para abrir documentos da escola no Google Drive"""
        try:
            import webbrowser
            
            links = {
                'estatuto': 'https://drive.google.com/file/d/14piUCRRxRlfh1EC_LiT_npmbPkOkgUS4/view?usp=sharing',
                'ppp': 'https://drive.google.com/file/d/1SDDy5PnxbTyDbqbfGKhLDrdRgdozGt-1/view?usp=sharing',
                'cnpj': 'https://drive.google.com/file/d/1-pW8FK7bq2v-vLFfczvqQv4lUw-MlF2r/view?usp=sharing',
            }
            
            link = links.get(chave)
            if not link:
                messagebox.showwarning("Documento não configurado", "Documento não encontrado.")
                return
            
            webbrowser.open(link)
        except Exception as e:
            logger.exception(f"Erro ao abrir documento da escola: {e}")
            messagebox.showerror("Erro ao abrir documento", str(e))
    
    def configurar_interface(self):
        """
        Configura a interface completa (botões + menus).
        
        Este é o método principal que deve ser chamado para criar
        toda a interface de ações da aplicação.
        """
        # Criar botões principais
        self.criar_botoes_principais()
        
        # Criar e configurar barra de menus
        menu_bar = self.criar_menu_bar()
        self.janela.config(menu=menu_bar)
        
        logger.debug("Interface de ações configurada (botões + menus)")
    
    # ========== WRAPPERS PARA MENU GERENCIAMENTO DE NOTAS ==========
    
    def _nota_bimestre(self, bimestre: str, preencher_nulos: bool = False):
        """Wrapper para gerar nota de bimestre (1º ao 5º ano)"""
        try:
            import NotaAta
            NotaAta.nota_bimestre(bimestre=bimestre, preencher_nulos=preencher_nulos)
        except Exception as e:
            logger.exception(f"Erro ao gerar nota bimestre: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar nota de bimestre: {e}")
    
    def _nota_bimestre2(self, bimestre: str, preencher_nulos: bool = False):
        """Wrapper para gerar nota de bimestre (6º ao 9º ano)"""
        try:
            import NotaAta
            NotaAta.nota_bimestre2(bimestre=bimestre, preencher_nulos=preencher_nulos)
        except Exception as e:
            logger.exception(f"Erro ao gerar nota bimestre 2: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar nota de bimestre: {e}")
    
    def _nota_bimestre_com_assinatura(self, bimestre: str, preencher_nulos: bool = False):
        """Wrapper para gerar nota de bimestre com assinatura (1º ao 5º ano)"""
        try:
            import NotaAta
            NotaAta.nota_bimestre_com_assinatura(bimestre=bimestre, preencher_nulos=preencher_nulos)
        except Exception as e:
            logger.exception(f"Erro ao gerar nota bimestre com assinatura: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar nota de bimestre: {e}")
    
    def _nota_bimestre2_com_assinatura(self, bimestre: str, preencher_nulos: bool = False):
        """Wrapper para gerar nota de bimestre com assinatura (6º ao 9º ano)"""
        try:
            import NotaAta
            NotaAta.nota_bimestre2_com_assinatura(bimestre=bimestre, preencher_nulos=preencher_nulos)
        except Exception as e:
            logger.exception(f"Erro ao gerar nota bimestre 2 com assinatura: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar nota de bimestre: {e}")
    
    def _abrir_relatorio_avancado_com_assinatura(self):
        """Wrapper para abrir relatório avançado com assinatura"""
        try:
            from abrir_relatorio_avancado_com_assinatura import abrir_relatorio_avancado_com_assinatura
            abrir_relatorio_avancado_com_assinatura(janela=self.janela, status_label=None)
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório avançado com assinatura: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir relatório: {e}")
    
    def _abrir_interface_ata(self):
        """Wrapper para abrir interface de Ata Geral"""
        try:
            from AtaGeral import abrir_interface_ata
            abrir_interface_ata(janela_pai=self.janela, status_label=None)
        except Exception as e:
            logger.exception(f"Erro ao abrir interface de Ata: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir interface de Ata Geral: {e}")
    
    def _gerar_pendencias_em_bg(self, bimestre: str, nivel: str):
        """Gera relatório de pendências em background"""
        try:
            from datetime import datetime
            from threading import Thread
            
            logger.info(f"Gerando pendências: {bimestre} ({nivel})")
            
            def _worker():
                try:
                    from services.report_service import gerar_relatorio_pendencias
                    ok = gerar_relatorio_pendencias(
                        bimestre=bimestre,
                        nivel_ensino=nivel,
                        ano_letivo=datetime.now().year,
                        escola_id=60
                    )
                    
                    def _on_done():
                        if ok:
                            messagebox.showinfo(
                                "Concluído",
                                f"Relatório de pendências gerado: {bimestre} ({nivel})"
                            )
                        else:
                            messagebox.showinfo(
                                "Sem pendências",
                                f"Nenhuma pendência encontrada para {bimestre} ({nivel})."
                            )
                    
                    self.janela.after(0, _on_done)
                    
                except Exception as e:
                    logger.exception(f"Erro ao gerar pendências: {e}")
                    
                    def _on_error():
                        messagebox.showerror("Erro", f"Falha ao gerar pendências: {e}")
                    
                    self.janela.after(0, _on_error)
            
            Thread(target=_worker, daemon=True).start()
            
        except Exception as e:
            logger.exception(f"Erro ao iniciar geração de pendências: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar pendências: {e}")

