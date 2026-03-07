"""
Factory para criação de botões e menus da aplicação.

Este módulo extrai a lógica de criação de botões da função criar_acoes()
do main.py, organizando em uma classe reutilizável e testável.
"""

from tkinter import Frame, Button, Menu, LEFT, RIGHT, RIDGE, X, EW
from tkinter import messagebox
from typing import Callable, Optional
from PIL import Image, ImageTk
from auth.decorators import ControleAcesso
from src.core.config_logs import get_logger

logger = get_logger(__name__)
from src.core.config import perfis_habilitados, ANO_LETIVO_ATUAL


class ButtonFactory:
    """Factory para criação de botões e menus da aplicação.

    Nota: stub mínimo de inicialização para manter compatibilidade com o código
    que espera atributos como `janela`, `frame_dados`, `callbacks` e `colors`.
    """

    def __init__(self, janela=None, frame_dados=None, callbacks=None, colors=None):
        self.janela = janela
        self.frame_dados = frame_dados
        self.callbacks = callbacks
        self.colors = colors or {
            'co0': '#000000', 'co1': '#ffffff', 'co2': '#f0f0f0', 'co3': '#f0f0f0',
            'co4': '#f0f0f0', 'co5': '#f0f0f0', 'co6': '#f0f0f0', 'co9': '#f0f0f0'
        }
        self._image_refs = {}
    
    def _load_image(self, path: str, size: tuple = None):
        """
        Carrega uma imagem de um arquivo local e redimensiona para o tamanho adequado.
        
        Args:
            path: Caminho relativo ou absoluto da imagem
            size: Tupla (largura, altura) para redimensionar. Se None, usa (20, 20) por padrão.
            
        Returns:
            ImageTk.PhotoImage ou None
        """
        try:
            import os
            # Se o caminho não for absoluto, buscar na raiz do projeto
            if not os.path.isabs(path):
                # Obter diretório raiz do projeto (2 níveis acima de ui/)
                # c:\gestao\src\ui -> c:\gestao\src
                src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                abs_path = os.path.join(src_root, path)
                
                # Se não encontrar e o caminho começa com 'icon/', procurar também em src/icon/
                if not os.path.exists(abs_path) and path.startswith('icon/'):
                    # Já estamos em src/, então icon/ está aqui mesmo
                    pass
            else:
                abs_path = path
            
            if not os.path.exists(abs_path):
                logger.warning(f"Imagem não encontrada: {path} (procurado em: {abs_path})")
                return None
            
            img = Image.open(abs_path)
            
            # Aplicar tamanho padrão de 20x20 se não especificado (ideal para botões)
            if size is None:
                size = (20, 20)
            
            # Redimensionar mantendo qualidade usando LANCZOS
            img = img.resize(size, Image.Resampling.LANCZOS)
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
            from src.core import seguranca
            seguranca.fazer_backup()
        except Exception as e:
            logger.exception(f"Erro ao fazer backup: {e}")
            messagebox.showerror("Erro", f"Erro ao fazer backup: {e}")
    
    def _restaurar_backup(self):
        """Callback para o botão de restaurar."""
        try:
            from src.core import seguranca
            seguranca.restaurar_backup()
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
        # cache de perfis para evitar chamadas repetidas
        is_admin = acesso.is_admin()
        is_coordenador = acesso.is_coordenador()
        is_professor = acesso.is_professor()
        
        # Barra de menu principal
        menu_bar = Menu(self.janela)
        
        # ========== MENU 1: LISTAS (todos podem ver relatórios) ==========
        if acesso.pode('relatorios.visualizar'):
            listas_menu = Menu(menu_bar, tearoff=0, font=menu_font)

            # Dashboard (Admin/Coord/Professor)
            if acesso.pode('dashboard.completo') or acesso.pode('dashboard.pedagogico') or acesso.pode('dashboard.proprio'):
                listas_menu.add_command(
                    label="📊 Ver Dashboard",
                    command=lambda: self._mostrar_dashboard(),
                    font=menu_font
                )
                listas_menu.add_separator()

            # Lista Atualizada (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Lista Atualizada",
                    command=self.callbacks.lista_atualizada,
                    font=menu_font
                )

            # Lista Atualizada SEMED (Admin)
            if is_admin:
                listas_menu.add_command(
                    label="Lista Atualizada SEMED",
                    command=self.callbacks.lista_atualizada_semed,
                    font=menu_font
                )
                
                listas_menu.add_command(
                    label="Exportar Funcionários (Excel)",
                    command=self.callbacks.exportar_funcionarios_excel,
                    font=menu_font
                )

            # Lista de Reunião (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Lista de Reunião",
                    command=self.callbacks.lista_reuniao,
                    font=menu_font
                )

            # Lista de Fardamento (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Lista de Fardamento",
                    command=self.callbacks.lista_fardamento,
                    font=menu_font
                )

            # Lista de Notas (Admin, Professor)
            if is_admin or is_professor:
                listas_menu.add_command(
                    label="Lista de Notas",
                    command=self.callbacks.lista_notas,
                    font=menu_font
                )

            # Lista de Frequências (Admin, Professor)
            if is_admin or is_professor:
                listas_menu.add_command(
                    label="Lista de Frequências",
                    command=self.callbacks.reports.lista_frequencia,
                    font=menu_font
                )

            # Lista de Controle de Livros (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Lista de Controle de Livros",
                    command=lambda: self._abrir_lista_controle_livros(),
                    font=menu_font
                )

            listas_menu.add_separator()

            # Contatos de Responsáveis (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Contatos de Responsáveis",
                    command=self.callbacks.relatorio_contatos_responsaveis,
                    font=menu_font
                )

            # Levantamento de Necessidades (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Levantamento de Necessidades",
                    command=self.callbacks.reports.relatorio_levantamento_necessidades,
                    font=menu_font
                )

            # Lista Alfabética (Admin)
            if is_admin:
                listas_menu.add_command(
                    label="Lista Alfabética",
                    command=self.callbacks.reports.relatorio_lista_alfabetica,
                    font=menu_font
                )

            # Alunos com Transtornos (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Alunos com Transtornos",
                    command=self.callbacks.reports.relatorio_alunos_transtornos,
                    font=menu_font
                )

            # Lista de Distorção de Fluxo (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Mapeamento - Distorção de Fluxo",
                    command=self.callbacks.reports.lista_distorcao_fluxo,
                    font=menu_font
                )

            # Lista de Não Rematriculados (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Alunos Não Rematriculados",
                    command=self.callbacks.reports.lista_nao_rematriculados,
                    font=menu_font
                )

            listas_menu.add_separator()

            # Transferências (Admin)
            if is_admin:
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

            # Termo de Responsabilidade (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Termo de Responsabilidade",
                    command=self.callbacks.reports.relatorio_termo_responsabilidade,
                    font=menu_font
                )

            listas_menu.add_separator()

            # Livros Faltantes (Admin, Coordenador)
            if is_admin or is_coordenador:
                listas_menu.add_command(
                    label="Gerenciar Livros Faltantes",
                    command=self._abrir_gerenciar_livros_faltantes,
                    font=menu_font
                )
                listas_menu.add_command(
                    label="Imprimir Livros Faltantes (PDF)",
                    command=self._gerar_pdf_livros_faltantes,
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
            # Submenu: Relatório Avançado (padronizado com assinaturas/pendências)
            relatorio_avancado_menu = Menu(notas_menu, tearoff=0, font=menu_font)
            relatorio_avancado_menu.add_command(
                label="1º bimestre",
                command=lambda: self._nota_bimestre("1º bimestre"),
                font=menu_font
            )
            relatorio_avancado_menu.add_command(
                label="2º bimestre",
                command=lambda: self._nota_bimestre("2º bimestre"),
                font=menu_font
            )
            relatorio_avancado_menu.add_command(
                label="3º bimestre",
                command=lambda: self._nota_bimestre("3º bimestre"),
                font=menu_font
            )
            relatorio_avancado_menu.add_command(
                label="4º bimestre",
                command=lambda: self._nota_bimestre("4º bimestre"),
                font=menu_font
            )
            relatorio_avancado_menu.add_separator()
            relatorio_avancado_menu.add_command(
                label="1º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2("1º bimestre"),
                font=menu_font
            )
            relatorio_avancado_menu.add_command(
                label="2º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2("2º bimestre"),
                font=menu_font
            )
            relatorio_avancado_menu.add_command(
                label="3º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2("3º bimestre"),
                font=menu_font
            )
            relatorio_avancado_menu.add_command(
                label="4º bimestre (6º ao 9º ano)",
                command=lambda: self._nota_bimestre2("4º bimestre"),
                font=menu_font
            )
            relatorio_avancado_menu.add_separator()
            relatorio_avancado_menu.add_command(
                label="Abrir interface",
                command=lambda: self._abrir_relatorio_avancado(),
                font=menu_font
            )
            notas_menu.add_cascade(
                label="Relatório Avançado",
                menu=relatorio_avancado_menu,
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
                label="Abrir interface",
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
        
        # ========== MENU 3: SERVIÇOS (apenas administradores) ==========
        if acesso.is_admin():
            servicos_menu = Menu(menu_bar, tearoff=0, font=menu_font)
            
            # Submenu: Movimento Mensal
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
        
            # Solicitação de Professores
            servicos_menu.add_command(
                label="Solicitação de Professores e Coordenadores",
                command=self.callbacks.abrir_solicitacao_professores,
                font=menu_font
            )
            
            # Gerenciador de Documentos de Funcionários
            servicos_menu.add_command(
                label="Gerenciador de Documentos de Funcionários",
                command=self.callbacks.abrir_gerenciador_documentos,
                font=menu_font
            )
            
            # Gerenciador de Documentos do Sistema
            servicos_menu.add_command(
                label="Gerenciador de Documentos do Sistema",
                command=lambda: self._abrir_gerenciador_documentos_sistema(),
                font=menu_font
            )
        
            # Declaração de Comparecimento
            servicos_menu.add_command(
                label="Declaração de Comparecimento (Responsável)",
                command=self.callbacks.declaracao_comparecimento,
                font=menu_font
            )
            # Submenu: Declarações do Ano Anterior
            declaracoes_menu = Menu(servicos_menu, tearoff=0, font=menu_font)
            declaracoes_menu.add_command(
                label="1º Ano",
                command=lambda: self._servicos_gerar_declaracoes_1ano(),
                font=menu_font
            )
            declaracoes_menu.add_command(
                label="2º Ano",
                command=lambda: self._servicos_gerar_declaracoes_2ano(),
                font=menu_font
            )
            declaracoes_menu.add_command(
                label="3º Ano",
                command=lambda: self._servicos_gerar_declaracoes_3ano(),
                font=menu_font
            )
            declaracoes_menu.add_command(
                label="4º Ano",
                command=lambda: self._servicos_gerar_declaracoes_4ano(),
                font=menu_font
            )
            declaracoes_menu.add_command(
                label="5º Ano",
                command=lambda: self._servicos_gerar_declaracoes_5ano(),
                font=menu_font
            )
            declaracoes_menu.add_separator()
            declaracoes_menu.add_command(
                label="6º Ano",
                command=lambda: self._servicos_gerar_declaracoes_6ano(),
                font=menu_font
            )
            declaracoes_menu.add_command(
                label="7º Ano",
                command=lambda: self._servicos_gerar_declaracoes_7ano(),
                font=menu_font
            )
            declaracoes_menu.add_command(
                label="8º Ano",
                command=lambda: self._servicos_gerar_declaracoes_8ano(),
                font=menu_font
            )
            declaracoes_menu.add_command(
                label="9º Ano",
                command=lambda: self._servicos_gerar_declaracoes_9ano(),
                font=menu_font
            )
            servicos_menu.add_cascade(
                label="Declarações do Ano Anterior",
                menu=declaracoes_menu,
                font=menu_font
            )
            # Gerar Certificados em Lote (9º Ano)
            servicos_menu.add_command(
                label="Gerar Certificados do 9º Ano",
                command=lambda: self._servicos_gerar_certificados_9ano(),
                font=menu_font
            )
            # Lista de Históricos Pendentes (novo)
            servicos_menu.add_command(
                label="Lista de Históricos Pendentes",
                command=lambda: self._servicos_lista_historicos_pendentes(),
                font=menu_font
            )
            servicos_menu.add_command(
                label="Crachás Alunos/Responsáveis",
                command=lambda: self._abrir_crachas(),
                font=menu_font
            )
            servicos_menu.add_command(
                label="Crachá Individual (Aluno + Responsável)",
                command=lambda: self._abrir_cracha_individual(),
                font=menu_font
            )
            
            # Submenu: Termo Cuidar dos Olhos
            termo_olhos_menu = Menu(servicos_menu, tearoff=0, font=menu_font)
            
            # Adicionar opção "Todas as Turmas"
            termo_olhos_menu.add_command(
                label="📄 Todas as Turmas",
                command=self.callbacks.reports.termo_cuidar_olhos,
                font=menu_font
            )
            termo_olhos_menu.add_separator()
            
            # Adicionar opções por turma dinamicamente
            try:
                from src.relatorios.geradores.termo_cuidar_olhos import obter_turmas_ativas
                turmas = obter_turmas_ativas()
                
                if turmas:
                    for turma in turmas:
                        turma_id = turma['turma_id']
                        serie = turma['nome_serie']
                        nome_turma = turma['nome_turma']
                        turno = turma['turno']
                        total = turma['total_alunos']
                        
                        label_turma = f"{serie} - Turma {nome_turma} ({turno}) - {total} alunos"
                        
                        # Criar lambda com default arguments para capturar valores
                        termo_olhos_menu.add_command(
                            label=label_turma,
                            command=lambda tid=turma_id, nome=label_turma: 
                                self.callbacks.reports.termo_cuidar_olhos_turma(tid, nome),
                            font=menu_font
                        )
                else:
                    termo_olhos_menu.add_command(
                        label="(Nenhuma turma ativa encontrada)",
                        state='disabled',
                        font=menu_font
                    )
            except Exception as e:
                logger.warning(f"Erro ao carregar turmas para menu: {e}")
                termo_olhos_menu.add_command(
                    label="(Erro ao carregar turmas)",
                    state='disabled',
                    font=menu_font
                )
            
            # Adicionar separador e opções para funcionários
            termo_olhos_menu.add_separator()
            termo_olhos_menu.add_command(
                label="📋 Professores",
                command=self.callbacks.reports.termo_cuidar_olhos_professores,
                font=menu_font
            )
            termo_olhos_menu.add_command(
                label="📋 Demais Servidores",
                command=self.callbacks.reports.termo_cuidar_olhos_servidores,
                font=menu_font
            )
            
            # Adicionar separador e opções de planilhas de levantamento
            termo_olhos_menu.add_separator()
            termo_olhos_menu.add_command(
                label="📊 Planilha de Levantamento - Estudantes",
                command=self.callbacks.reports.planilha_cuidar_olhos_estudantes,
                font=menu_font
            )
            termo_olhos_menu.add_command(
                label="📊 Planilha de Levantamento - Professores/Servidores",
                command=self.callbacks.reports.planilha_cuidar_olhos_profissionais,
                font=menu_font
            )
            
            servicos_menu.add_cascade(
                label="Termo Cuidar dos Olhos",
                menu=termo_olhos_menu,
                font=menu_font
            )
            
            # Importar Notas
            servicos_menu.add_separator()
            servicos_menu.add_command(
                label="Importar Notas do GEDUC (HTML → Excel)",
                command=lambda: self._abrir_importacao_notas_html(),
                font=menu_font
            )
            servicos_menu.add_command(
                label="📥 Importar Alunos do GEDUC",
                command=lambda: self._abrir_importacao_alunos_geduc(),
                font=menu_font
            )
            
            # Transição de Ano Letivo
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
        from src.core.config import banco_questoes_habilitado
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
        documentos_menu.add_command(
            label="Regimento Escolar",
            command=lambda: self._abrir_documento_escola('regimento'),
            font=menu_font
        )
        documentos_menu.add_separator()
        documentos_menu.add_command(
            label="📄 Gerar Documentos SMTT",
            command=lambda: self._abrir_geracao_smtt(),
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
        
        # ========== MENU AJUDA: Atualizações e informações ==========
        try:
            ajuda_menu = Menu(menu_bar, tearoff=0, font=menu_font)
            ajuda_menu.add_command(
                label="Atualizar Sistema",
                command=lambda: self._atualizar_sistema(),
                font=menu_font
            )
            menu_bar.add_cascade(label="Ajuda", menu=ajuda_menu, font=menu_font)
        except Exception:
            # Não falhar a criação da barra inteira por conta do menu de ajuda
            logger.exception("Falha ao criar menu Ajuda")

        logger.debug(f"Barra de menus criada (perfis_habilitados={perfis_habilitados()})")
        return menu_bar
    
    def _abrir_troca_senha(self):
        """Abre janela para trocar senha."""
        try:
            from src.ui.login import TrocaSenhaWindow
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
            from src.ui.gestao_usuarios import abrir_gestao_usuarios
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

    def _atualizar_sistema(self):
        """Atualiza o sistema.

        Se estiver no Windows e existir `sync_rapido.bat` na raiz do projeto, executa-o.
        Caso contrário, tenta o fluxo git como fallback.
        """
        try:
            import subprocess
            import os
            import sys

            # Diretório raiz do projeto (onde está sync_rapido.bat ou scripts/sync_rapido.py)
            repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            # Se Windows e existir batch de sincronização, usar ele
            # Preferir script Python cross-platform se existir
            py_script = os.path.join(repo_dir, 'scripts', 'sync_rapido.py')
            bat_path = os.path.join(repo_dir, 'sync_rapido.bat')
            if os.path.exists(py_script):
                messagebox.showinfo("Atualizar Sistema", f"Executando sincronização via: {py_script}")
                proc = subprocess.run([sys.executable, py_script], cwd=repo_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if proc.returncode == 0:
                    messagebox.showinfo("Atualizar Sistema", "Sincronização concluída com sucesso.\nDeseja reiniciar a aplicação agora?")
                    reiniciar = messagebox.askyesno("Reiniciar", "Deseja reiniciar a aplicação agora para aplicar as atualizações?")
                    if reiniciar:
                        try:
                            os.execv(sys.executable, [sys.executable] + sys.argv)
                        except Exception as e:
                            logger.exception(f"Erro ao reiniciar: {e}")
                            messagebox.showerror("Erro", f"Não foi possível reiniciar automaticamente: {e}")
                    return
                else:
                    logger.error(f"sync_rapido.py falhou: {proc.stdout}\n{proc.stderr}")
                    messagebox.showerror("Erro", f"Falha ao executar sync_rapido.py:\n{proc.stderr or proc.stdout}")
                    return

            if os.name == 'nt' and os.path.exists(bat_path):
                messagebox.showinfo("Atualizar Sistema", f"Executando sincronização via: {bat_path}")
                # Executar o .bat e capturar saída
                proc = subprocess.run([bat_path], cwd=repo_dir, capture_output=True, text=True, shell=True, encoding='utf-8', errors='replace')
                if proc.returncode == 0:
                    messagebox.showinfo("Atualizar Sistema", "Sincronização concluída com sucesso.\nDeseja reiniciar a aplicação agora?")
                    reiniciar = messagebox.askyesno("Reiniciar", "Deseja reiniciar a aplicação agora para aplicar as atualizações?")
                    if reiniciar:
                        try:
                            os.execv(sys.executable, [sys.executable] + sys.argv)
                        except Exception as e:
                            logger.exception(f"Erro ao reiniciar: {e}")
                            messagebox.showerror("Erro", f"Não foi possível reiniciar automaticamente: {e}")
                    return
                else:
                    logger.error(f"sync_rapido.bat falhou: {proc.stdout}\n{proc.stderr}")
                    messagebox.showerror("Erro", f"Falha ao executar sync_rapido.bat:\n{proc.stderr or proc.stdout}")
                    return

            # Fallback: tentar git diretamente (mesmo comportamento anterior)
            p = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
            branch = p.stdout.strip() if p.returncode == 0 else "main"

            messagebox.showinfo("Atualizar Sistema", "Verificando atualizações no servidor...")
            fetch = subprocess.run(["git", "fetch", "--all"], cwd=repo_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if fetch.returncode != 0:
                logger.error(f"Git fetch falhou: {fetch.stderr}")
                messagebox.showerror("Erro", f"Falha ao verificar atualizações:\n{fetch.stderr}")
                return

            revlist = subprocess.run(["git", "rev-list", "--count", f"HEAD..origin/{branch}"], cwd=repo_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
            has_updates = False
            if revlist.returncode == 0:
                try:
                    count = int(revlist.stdout.strip() or "0")
                    has_updates = count > 0
                except Exception:
                    has_updates = False

            if not has_updates:
                messagebox.showinfo("Atualizar Sistema", "Nenhuma atualização disponível.")
                return

            pull = subprocess.run(["git", "pull", "--rebase", "origin", branch], cwd=repo_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if pull.returncode != 0:
                logger.error(f"Git pull falhou: {pull.stderr}")
                messagebox.showerror("Erro ao atualizar", f"Falha ao atualizar o sistema:\n{pull.stderr}\n\nVerifique manualmente no diretório: {repo_dir}")
                return

            messagebox.showinfo("Atualizar Sistema", "Sistema atualizado com sucesso.\nDeseja reiniciar a aplicação agora?")
            reiniciar = messagebox.askyesno("Reiniciar", "Deseja reiniciar a aplicação agora para aplicar as atualizações?")
            if reiniciar:
                try:
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                except Exception as e:
                    logger.exception(f"Erro ao reiniciar: {e}")
                    messagebox.showerror("Erro", f"Não foi possível reiniciar automaticamente: {e}")

        except Exception as e:
            logger.exception(f"Erro ao atualizar sistema: {e}")
            messagebox.showerror("Erro", f"Erro ao atualizar o sistema: {e}")
    
    def _gerar_relatorio_notas_wrapper(self):
        """Wrapper para gerar relatório de notas"""
        try:
            from src.services.report_service import gerar_relatorio_notas
            gerar_relatorio_notas()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório de notas: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")
    
    def _gerar_relatorio_notas_com_assinatura_wrapper(self):
        """Wrapper para gerar relatório de notas com assinatura"""
        try:
            from src.relatorios.relatorio_avancado_assinatura import abrir_relatorio_avancado_com_assinatura as gerar_relatorio_com_assinatura
            gerar_relatorio_com_assinatura(janela=self.janela, status_label=None)
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório de notas: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")
    
    def _abrir_relatorio_avancado(self):
        """Wrapper para abrir relatório avançado"""
        try:
            from src.ui.report_dialogs import abrir_relatorio_avancado
            from src.services.report_service import gerar_relatorio_notas
            abrir_relatorio_avancado(janela_pai=self.janela, status_label=None, gerar_func=gerar_relatorio_notas)
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório avançado: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir relatório: {e}")
    
    def _abrir_relatorio_pendencias(self):
        """Wrapper para abrir relatório de pendências com tratamento específico de mensagens"""
        try:
            from src.ui.report_dialogs import abrir_relatorio_avancado
            from src.services.report_service import gerar_relatorio_pendencias
            from tkinter import messagebox

            # Adaptador: a interface de relatório avançado passa (bimestre, nivel_ensino, ano_letivo,
            # status_matricula, preencher_nulos). O gerador de pendências espera (bimestre, nivel_ensino,
            # ano_letivo, escola_id). Ignoramos os parâmetros extras e usamos escola padrão.
            def _gerar_pendencias_adapter(bimestre, nivel_ensino, ano_letivo, status_matricula=None, preencher_nulos=False):
                try:
                    resultado = gerar_relatorio_pendencias(bimestre=bimestre, nivel_ensino=nivel_ensino, ano_letivo=ano_letivo)
                    if not resultado:
                        # Quando retorna False, significa que não há pendências
                        nivel_texto = "séries iniciais" if nivel_ensino == "iniciais" else "séries finais"
                        messagebox.showinfo(
                            "Sem pendências", 
                            f"Parabéns! Não há pendências de notas para o {bimestre} nas {nivel_texto}.\n\n"
                            f"Todas as notas já foram lançadas para o ano letivo {ano_letivo}."
                        )
                    return resultado
                except ValueError as e:
                    # Quando há erro de turmas não encontradas, mostrar mensagem específica
                    messagebox.showerror("Dados não encontrados", str(e))
                    return False

            abrir_relatorio_avancado(janela_pai=self.janela, status_label=None, gerar_func=_gerar_pendencias_adapter)
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório de pendências: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir relatório: {e}")
    
    def _gerar_declaracao_generica(self):
        """Wrapper para gerar declaração genérica"""
        try:
            # Tenta importar o script legacy (caso exista) para compatibilidade.
            try:
                from Gerar_Declaracao_Aluno import main as gerar_declaracao  # type: ignore
            except Exception:
                # Caso não exista, usar o novo módulo de relatórios
                from src.relatorios.declaracao_aluno import gerar_declaracao_aluno as gerar_declaracao

            # Se a função for a nova `gerar_declaracao_aluno` que requer parâmetros,
            # informar ao usuário que esta ação deve ser feita por aluno nos detalhes.
            if gerar_declaracao is None:
                messagebox.showinfo("Aviso", "Geração genérica de declaração não disponível neste contexto.")
                return

            # Se for a função legacy `main()` ela aceitará execução direta.
            try:
                gerar_declaracao()
            except TypeError:
                # Função requer parâmetros — informar ao usuário.
                messagebox.showinfo("Aviso", "Esta opção não está disponível. Gere declarações por aluno na tela de detalhes.")

        except Exception as e:
            logger.exception(f"Erro ao gerar declaração: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declaração: {e}")

    def _servicos_gerar_declaracoes_1ano(self):
        """Gera declarações em lote para alunos do 1º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 1º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            from src.gestores.servicos_lote_documentos import gerar_declaracoes_1ano_combinadas

            arquivo = gerar_declaracoes_1ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote (1º ano): {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_declaracoes_2ano(self):
        """Gera declarações em lote para alunos do 2º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 2º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            from src.gestores.servicos_lote_documentos import gerar_declaracoes_2ano_combinadas

            arquivo = gerar_declaracoes_2ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote (2º ano): {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_declaracoes_3ano(self):
        """Gera declarações em lote para alunos do 3º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 3º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            from src.gestores.servicos_lote_documentos import gerar_declaracoes_3ano_combinadas

            arquivo = gerar_declaracoes_3ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote (3º ano): {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_declaracoes_7ano(self):
        """Gera declarações em lote para alunos do 7º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 7º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            from src.gestores.servicos_lote_documentos import gerar_declaracoes_7ano_combinadas

            arquivo = gerar_declaracoes_7ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote (7º ano): {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_declaracoes_8ano(self):
        """Gera declarações em lote para alunos do 8º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 8º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            from src.gestores.servicos_lote_documentos import gerar_declaracoes_8ano_combinadas

            arquivo = gerar_declaracoes_8ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote (8º ano): {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_declaracoes_9ano(self):
        """Gera declarações em lote para alunos do 9º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 9º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            # Gerar declarações combinadas em um único arquivo usando o novo util
            from src.gestores.servicos_lote_documentos import gerar_declaracoes_9ano_combinadas

            arquivo = gerar_declaracoes_9ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_declaracoes_5ano(self):
        """Gera declarações em lote para alunos do 5º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 5º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            # Gerar declarações combinadas em um único arquivo usando o util correspondente
            from src.gestores.servicos_lote_documentos import gerar_declaracoes_5ano_combinadas

            arquivo = gerar_declaracoes_5ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote (5º ano): {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_declaracoes_4ano(self):
        """Gera declarações em lote para alunos do 4º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 4º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            # Gerar declarações combinadas em um único arquivo usando o util correspondente
            from src.gestores.servicos_lote_documentos import gerar_declaracoes_4ano_combinadas

            arquivo = gerar_declaracoes_4ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote (4º ano): {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_declaracoes_6ano(self):
        """Gera declarações em lote para alunos do 6º ano (matriculados e ativos)."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar declarações para todos os alunos do 6º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            # Gerar declarações combinadas em um único arquivo usando o util correspondente
            from src.gestores.servicos_lote_documentos import gerar_declaracoes_6ano_combinadas

            arquivo = gerar_declaracoes_6ano_combinadas()
            if arquivo:
                messagebox.showinfo("Concluído", f"Declarações combinadas geradas: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar declarações combinadas. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de declarações em lote (6º ano): {e}")
            messagebox.showerror("Erro", f"Erro ao gerar declarações: {e}")

    def _servicos_gerar_certificados_9ano(self):
        """Gera certificados em lote para alunos do 9º ano (matriculados e ativos) em um único PDF."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar certificados para todos os alunos do 9º ano matriculados e ativos?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            # Gerar certificados combinados em um único arquivo usando o util otimizado
            from src.gestores.servicos_lote_documentos import gerar_certificados_9ano_combinados

            arquivo = gerar_certificados_9ano_combinados()
            if arquivo:
                messagebox.showinfo("Concluído", f"Certificados combinados gerados: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar certificados combinados. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro no processo de geração de certificados em lote: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar certificados: {e}")

    def _servicos_lista_historicos_pendentes(self):
        """Gera a lista de históricos pendentes (ano letivo atual) e salva o PDF."""
        try:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Gerar a Lista de Históricos Pendentes para o ano letivo atual?\n\nIsso pode demorar. Deseja continuar?"
            )
            if not resposta:
                return

            # Determinar ano e escola
            try:
                from src.core.config.settings import settings
                # Usar settings.app.ano_letivo se definido; caso contrário, usar ANO_LETIVO_ATUAL
                ano = getattr(settings.app, 'ano_letivo', None) or ANO_LETIVO_ATUAL
                escola_id = getattr(settings.app, 'escola_id', 60)
            except Exception:
                ano = ANO_LETIVO_ATUAL
                escola_id = 60

            # Gerar usando o relatório implementado
            from src.relatorios.listas.alunos_9ano_historico import gerar_lista_9ano_historico_pdf

            arquivo = gerar_lista_9ano_historico_pdf(ano_letivo=ano, escola_id=escola_id)
            if arquivo:
                messagebox.showinfo("Concluído", f"Lista de Históricos Pendentes gerada: {arquivo}")
            else:
                messagebox.showerror("Erro", "Falha ao gerar a lista. Verifique os logs.")

        except Exception as e:
            logger.exception(f"Erro ao gerar lista de históricos pendentes: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar a lista: {e}")
    
    def _abrir_relatorio_analise(self):
        """Wrapper para abrir relatório estatístico de análise de notas"""
        try:
            from src.relatorios.relatorio_analise_notas import abrir_relatorio_analise_notas
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
            from src.gestores.documentos_sistema import GerenciadorDocumentosSistema
            
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
            from src.ui.interfaces_extended import abrir_interface_crachas
            abrir_interface_crachas(self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir interface de crachás: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir crachás: {e}")
    
    def _abrir_cracha_individual(self):
        """Wrapper para abrir interface de crachá individual"""
        try:
            from src.ui.cracha_individual_window import abrir_janela_cracha_individual
            abrir_janela_cracha_individual(self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir interface de crachá individual: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir crachá individual: {e}")
    
    def _abrir_importacao_notas_html(self):
        """Wrapper para abrir importação de notas do HTML"""
        try:
            self.janela.withdraw()
            from src.importadores.notas_html import interface_importacao
            interface_importacao(janela_pai=self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir importação de notas: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir importação: {e}")
            self.janela.deiconify()

    def _abrir_importacao_alunos_geduc(self):
        """Wrapper para abrir importação de alunos do GEDUC"""
        try:
            from src.importadores.alunos_geduc import abrir_importacao_alunos_geduc
            abrir_importacao_alunos_geduc(janela_pai=self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir importação de alunos GEDUC: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir interface:\n{e}")
            self.janela.deiconify()
    
    def _mostrar_dashboard(self):
        """Mostra o dashboard adaptado ao perfil do usuário."""
        try:
            # Obter referência ao app através do callback manager
            app = getattr(self.janela, '_app_instance', None)
            
            if app and app.dashboard_manager:
                # Limpar frame da tabela
                if 'frame_tabela' in app.frames:
                    for widget in app.frames['frame_tabela'].winfo_children():
                        widget.destroy()
                
                # Criar dashboard adaptado por perfil
                usuario = getattr(app, 'usuario', None)
                app.dashboard_manager.criar_dashboard_por_perfil(usuario)
                logger.info(f"Dashboard exibido para perfil: {usuario.perfil if usuario else 'administrador'}")
            else:
                messagebox.showwarning("Aviso", "Dashboard não está disponível no momento.")
                logger.warning("Dashboard manager não inicializado")
                
        except Exception as e:
            logger.exception(f"Erro ao mostrar dashboard: {e}")
            messagebox.showerror("Erro", f"Erro ao mostrar dashboard: {e}")
    
    def _abrir_dialogo_folhas_ponto(self):
        """Wrapper para abrir diálogo de folhas de ponto"""
        try:
            # Abrir o diálogo que permite escolher mês e pasta de saída (com implementação adaptada)
            from src.ui.dialogs_extended import abrir_dialogo_folhas_ponto
            abrir_dialogo_folhas_ponto(self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir diálogo de folhas de ponto: {e}")
            messagebox.showerror("Erro", f"Erro: {e}")
    
    def _abrir_dialogo_resumo_ponto(self):
        """Wrapper para abrir diálogo de resumo de ponto"""
        try:
            from src.ui.dialogs_extended import abrir_dialogo_resumo_ponto
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
                'regimento': 'https://drive.google.com/file/d/1ZveeqGkp0HzfQDf6zrNfEAiuKvPgrWtN/view?pli=1',
            }
            
            link = links.get(chave)
            if not link:
                messagebox.showwarning("Documento não configurado", "Documento não encontrado.")
                return
            
            webbrowser.open(link)
        except Exception as e:
            logger.exception(f"Erro ao abrir documento da escola: {e}")
            messagebox.showerror("Erro ao abrir documento", str(e))

    def _abrir_geracao_smtt(self):
        """Abre a interface para gerar documentos SMTT preenchidos"""
        try:
            from src.relatorios.geradores.preencher_smtt import abrir_interface_smtt
            abrir_interface_smtt()
        except Exception as e:
            logger.exception(f"Erro ao abrir geração de documentos SMTT: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir interface SMTT:\n{str(e)}")

    def _abrir_lista_controle_livros(self):
        """Abre/gera as listas de controle de livros (recebidos e devolvidos)."""
        try:
            from src.relatorios.listas import Lista_controle_livros
            # Chama a função que gera os dois PDFs
            Lista_controle_livros.gerar_controle_livros()
        except Exception as e:
            logger.exception(f"Erro ao gerar Lista de Controle de Livros: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar Lista de Controle de Livros: {e}")
    
    def _abrir_gerenciar_livros_faltantes(self):
        """Abre interface para gerenciar livros faltantes por turma."""
        try:
            from src.ui.livros_faltantes_window import abrir_livros_faltantes
            abrir_livros_faltantes(janela_principal=self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir gerenciamento de livros faltantes: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir gerenciamento de livros faltantes: {e}")
    
    def _gerar_pdf_livros_faltantes(self):
        """Gera PDF com lista de livros faltantes por turma."""
        try:
            from src.relatorios.listas.lista_livros_faltantes import gerar_pdf_livros_faltantes
            gerar_pdf_livros_faltantes()
        except Exception as e:
            logger.exception(f"Erro ao gerar PDF de livros faltantes: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar PDF de livros faltantes: {e}")
    
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
            from src.relatorios.nota_ata import nota_bimestre
            nota_bimestre(bimestre=bimestre, preencher_nulos=preencher_nulos)
        except Exception as e:
            logger.exception(f"Erro ao gerar nota bimestre: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar nota de bimestre: {e}")
    
    def _nota_bimestre2(self, bimestre: str, preencher_nulos: bool = False):
        """Wrapper para gerar nota de bimestre (6º ao 9º ano)"""
        try:
            from src.relatorios.nota_ata import nota_bimestre2
            nota_bimestre2(bimestre=bimestre, preencher_nulos=preencher_nulos)
        except Exception as e:
            logger.exception(f"Erro ao gerar nota bimestre 2: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar nota de bimestre: {e}")
    
    def _nota_bimestre_com_assinatura(self, bimestre: str, preencher_nulos: bool = False):
        """Wrapper para gerar nota de bimestre com assinatura (1º ao 5º ano)"""
        try:
            from src.relatorios.nota_ata import nota_bimestre_com_assinatura
            nota_bimestre_com_assinatura(bimestre=bimestre, preencher_nulos=preencher_nulos)
        except Exception as e:
            logger.exception(f"Erro ao gerar nota bimestre com assinatura: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar nota de bimestre: {e}")
    
    def _nota_bimestre2_com_assinatura(self, bimestre: str, preencher_nulos: bool = False):
        """Wrapper para gerar nota de bimestre com assinatura (6º ao 9º ano)"""
        try:
            from src.relatorios.nota_ata import nota_bimestre2_com_assinatura
            nota_bimestre2_com_assinatura(bimestre=bimestre, preencher_nulos=preencher_nulos)
        except Exception as e:
            logger.exception(f"Erro ao gerar nota bimestre 2 com assinatura: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar nota de bimestre: {e}")
    
    def _abrir_relatorio_avancado_com_assinatura(self):
        """Wrapper para abrir relatório avançado com assinatura"""
        try:
            from src.relatorios.relatorio_avancado_assinatura import abrir_relatorio_avancado_com_assinatura
            abrir_relatorio_avancado_com_assinatura(janela=self.janela, status_label=None)
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório avançado com assinatura: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir relatório: {e}")
    
    def _abrir_interface_ata(self):
        """Wrapper para abrir interface de Ata Geral"""
        try:
            from src.relatorios.atas.ata_geral import abrir_interface_ata
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
                    from src.services.report_service import gerar_relatorio_pendencias
                    ok = gerar_relatorio_pendencias(
                        bimestre=bimestre,
                        nivel_ensino=nivel,
                        ano_letivo=ANO_LETIVO_ATUAL,
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

