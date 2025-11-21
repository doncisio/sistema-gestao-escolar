"""
Callbacks de ações do sistema de gestão escolar.

Este módulo centraliza os callbacks que antes estavam embutidos
na função criar_acoes() do main.py, organizando-os por categoria.
"""

from tkinter import Toplevel, messagebox
from typing import Callable, Optional, Any
from config_logs import get_logger

logger = get_logger(__name__)


class ReportCallbacks:
    """Callbacks relacionados a relatórios e listas."""
    
    def __init__(self, janela):
        """
        Inicializa os callbacks de relatórios.
        
        Args:
            janela: Janela principal da aplicação
        """
        self.janela = janela
    
    def lista_atualizada(self):
        """Gera lista atualizada de alunos."""
        try:
            # Lazy import para melhor performance
            import Lista_atualizada
            # Importar função de background do ui.dashboard
            from ui.dashboard import run_report_in_background
            
            if hasattr(Lista_atualizada, 'lista_atualizada'):
                run_report_in_background(
                    Lista_atualizada.lista_atualizada, 
                    "Lista Atualizada",
                    janela=self.janela
                )
            else:
                messagebox.showerror("Erro", "Função 'lista_atualizada' não disponível no módulo Lista_atualizada.")
        except Exception as e:
            logger.exception(f"Erro ao gerar lista atualizada: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar a lista: {e}")
    
    def lista_atualizada_semed(self):
        """Gera lista atualizada SEMED."""
        try:
            # Lazy import para melhor performance
            import Lista_atualizada_semed
            # Importar função de background do ui.dashboard
            from ui.dashboard import run_report_in_background
            
            if hasattr(Lista_atualizada_semed, 'lista_atualizada'):
                run_report_in_background(
                    Lista_atualizada_semed.lista_atualizada, 
                    "Lista Atualizada SEMED",
                    janela=self.janela
                )
            else:
                messagebox.showerror("Erro", "Função 'lista_atualizada' não disponível no módulo Lista_atualizada_semed.")
        except Exception as e:
            logger.exception(f"Erro ao gerar lista SEMED: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar a lista: {e}")
    
    def lista_reuniao(self):
        """Gera lista de reunião."""
        try:
            from Lista_reuniao import lista_reuniao as _lista_reuniao
            _lista_reuniao()
        except Exception as e:
            logger.exception(f"Erro ao gerar lista de reunião: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar a lista: {e}")
    
    def lista_notas(self):
        """Gera lista de notas."""
        try:
            from Lista_notas import lista_notas as _lista_notas
            _lista_notas()
        except Exception as e:
            logger.exception(f"Erro ao gerar lista de notas: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar a lista: {e}")
    
    def lista_frequencia(self):
        """Gera lista de frequências."""
        try:
            from lista_frequencia import lista_frequencia as _lista_frequencia
            _lista_frequencia()
        except Exception as e:
            logger.exception(f"Erro ao gerar lista de frequência: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar a lista: {e}")
    
    def relatorio_contatos_responsaveis(self):
        """Gera relatório de contatos de responsáveis."""
        try:
            from Lista_contatos_responsaveis import gerar_pdf_contatos
            from datetime import datetime
            from db.connection import get_cursor
            
            # Obter o ano letivo atual (não o ID)
            ano_letivo = datetime.now().year
            try:
                with get_cursor() as cursor:
                    cursor.execute("SELECT ano_letivo FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo LIMIT 1")
                    resultado = cursor.fetchone()
                    if resultado:
                        ano_letivo = resultado['ano_letivo'] if isinstance(resultado, dict) else resultado[0]
            except Exception as e:
                logger.warning(f"Erro ao buscar ano letivo, usando ano atual: {e}")
            
            gerar_pdf_contatos(ano_letivo)
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório: {e}")
    
    def relatorio_levantamento_necessidades(self):
        """Gera relatório de levantamento de necessidades."""
        try:
            from levantamento_necessidades import gerar_levantamento_necessidades
            gerar_levantamento_necessidades()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório: {e}")
    
    def relatorio_lista_alfabetica(self):
        """Gera lista alfabética de alunos."""
        try:
            from Lista_alunos_alfabetica import lista_alfabetica
            lista_alfabetica()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório: {e}")
    
    def relatorio_alunos_transtornos(self):
        """Gera relatório de alunos com transtornos."""
        try:
            from Lista_alunos_transtornos import lista_alunos_transtornos
            lista_alunos_transtornos()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório: {e}")
    
    def relatorio_termo_responsabilidade(self):
        """Gera termo de responsabilidade."""
        try:
            from termo_responsabilidade_empresa import gerar_termo_responsabilidade
            gerar_termo_responsabilidade()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório: {e}")
    
    def relatorio_tabela_docentes(self):
        """Gera tabela de docentes."""
        try:
            from tabela_docentes import gerar_tabela_docentes
            gerar_tabela_docentes()
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório: {e}")
    
    def relatorio_movimentacao_mensal(self, numero_mes: int):
        """Gera relatório de movimentação mensal."""
        try:
            from movimentomensal import relatorio_movimentacao_mensal
            relatorio_movimentacao_mensal(mes=numero_mes)
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório mensal: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar o relatório: {e}")
    
    def abrir_cadastro_notas(self):
        """Abre interface de cadastro/edição de notas."""
        try:
            self.janela.withdraw()
            
            janela_notas = Toplevel()
            janela_notas.title("Cadastro/Edição de Notas")
            janela_notas.geometry("1000x600")
            janela_notas.grab_set()
            janela_notas.focus_force()
            
            def ao_fechar():
                self.janela.deiconify()
                janela_notas.destroy()
            
            janela_notas.protocol("WM_DELETE_WINDOW", ao_fechar)
            
            from InterfaceCadastroEdicaoNotas import InterfaceCadastroEdicaoNotas
            app_notas = InterfaceCadastroEdicaoNotas(janela_notas, janela_principal=self.janela)
            
        except Exception as e:
            logger.exception(f"Erro ao abrir cadastro de notas: {e}")
            messagebox.showerror("Erro", f"Falha ao abrir interface de notas: {e}")
            self.janela.deiconify()
    
    def abrir_relatorio_analise(self):
        """Abre relatório estatístico de análise de notas."""
        try:
            from relatorio_analise_notas import abrir_relatorio_analise_notas
            abrir_relatorio_analise_notas(janela_principal=self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir relatório de análise: {e}")
            messagebox.showerror("Erro", f"Não foi possível abrir o relatório: {e}")
    
    def abrir_cadastro_faltas(self):
        """Abre interface de cadastro/edição de faltas."""
        try:
            from InterfaceCadastroEdicaoFaltas import abrir_interface_faltas
            abrir_interface_faltas(janela_principal=self.janela)
        except Exception as e:
            logger.exception(f"Erro ao abrir cadastro de faltas: {e}")
            messagebox.showerror("Erro", f"Não foi possível abrir a interface de faltas: {e}")


class RHCallbacks:
    """Callbacks relacionados a RH (folhas de ponto, resumo de ponto, solicitações)."""
    
    def __init__(self, janela):
        """
        Inicializa os callbacks de RH.
        
        Args:
            janela: Janela principal da aplicação
        """
        self.janela = janela
    
    def gerar_folhas_de_ponto(self, numero_mes: int):
        """Gera folhas de ponto para o mês especificado."""
        try:
            from main import gerar_folhas_de_ponto as _gerar_folhas
            _gerar_folhas(numero_mes)
        except Exception as e:
            logger.exception(f"Erro ao gerar folhas de ponto: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar as folhas de ponto: {e}")
    
    def gerar_resumo_ponto(self, numero_mes: int):
        """Gera resumo de ponto para o mês especificado."""
        try:
            from main import gerar_resumo_ponto as _gerar_resumo
            _gerar_resumo(numero_mes)
        except Exception as e:
            logger.exception(f"Erro ao gerar resumo de ponto: {e}")
            messagebox.showerror("Erro", f"Não foi possível gerar o resumo de ponto: {e}")


class CadastroCallbacks:
    """Callbacks relacionados a cadastros (alunos, funcionários)."""
    
    def __init__(self, janela, atualizar_tabela_callback: Optional[Callable] = None):
        """
        Inicializa os callbacks de cadastro.
        
        Args:
            janela: Janela principal da aplicação
            atualizar_tabela_callback: Função para atualizar a tabela após cadastro
        """
        self.janela = janela
        self.atualizar_tabela_callback = atualizar_tabela_callback
    
    def cadastrar_novo_aluno(self):
        """Abre interface de cadastro de novo aluno."""
        try:
            from InterfaceCadastroAluno import InterfaceCadastroAluno
            
            cadastro_window = Toplevel(self.janela)
            cadastro_window.title("Cadastro de Aluno")
            cadastro_window.geometry('950x670')
            cadastro_window.focus_set()
            cadastro_window.grab_set()
            
            app_cadastro = InterfaceCadastroAluno(cadastro_window, self.janela)
            
            def ao_fechar_cadastro():
                # Verificar se um aluno foi cadastrado
                if hasattr(app_cadastro, 'aluno_cadastrado') and app_cadastro.aluno_cadastrado:
                    if self.atualizar_tabela_callback:
                        self.atualizar_tabela_callback()
                
                # Mostrar janela principal novamente
                self.janela.deiconify()
                cadastro_window.destroy()
            
            cadastro_window.protocol("WM_DELETE_WINDOW", ao_fechar_cadastro)
            
            logger.info("Interface de cadastro de aluno aberta")
            
        except Exception as e:
            logger.exception(f"Erro ao abrir cadastro de aluno: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir cadastro de aluno: {str(e)}")
    
    def cadastrar_novo_funcionario(self):
        """Abre interface de cadastro de novo funcionário."""
        try:
            from InterfaceCadastroFuncionario import InterfaceCadastroFuncionario
            
            cadastro_window = Toplevel(self.janela)
            cadastro_window.title("Cadastro de Funcionário")
            cadastro_window.geometry('950x670')
            cadastro_window.focus_set()
            
            app_cadastro = InterfaceCadastroFuncionario(cadastro_window, self.janela)
            
            def ao_fechar_cadastro():
                if hasattr(app_cadastro, 'funcionario_cadastrado') and app_cadastro.funcionario_cadastrado:
                    if self.atualizar_tabela_callback:
                        self.atualizar_tabela_callback()
                
                self.janela.deiconify()
                cadastro_window.destroy()
            
            cadastro_window.protocol("WM_DELETE_WINDOW", ao_fechar_cadastro)
            
            logger.info("Interface de cadastro de funcionário aberta")
            
        except Exception as e:
            logger.exception(f"Erro ao abrir cadastro de funcionário: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir cadastro de funcionário: {str(e)}")


class HistoricoCallbacks:
    """Callbacks relacionados ao histórico escolar."""
    
    def __init__(self, janela):
        self.janela = janela
    
    def abrir_historico_escolar(self):
        """Abre interface de histórico escolar."""
        try:
            from integrar_historico_escolar import abrir_interface_historico
            abrir_interface_historico(self.janela)
            logger.info("Interface de histórico escolar aberta")
        except Exception as e:
            logger.exception(f"Erro ao abrir histórico escolar: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir histórico escolar: {str(e)}")


class AdministrativoCallbacks:
    """Callbacks relacionados à área administrativa."""
    
    def __init__(self, janela):
        self.janela = janela
    
    def abrir_interface_administrativa(self):
        """Abre interface administrativa."""
        try:
            from interface_administrativa import InterfaceAdministrativa
            
            admin_window = Toplevel(self.janela)
            admin_window.title("Administração")
            admin_window.geometry('950x670')
            
            InterfaceAdministrativa(admin_window, self.janela)
            
            logger.info("Interface administrativa aberta")
            
        except Exception as e:
            logger.exception(f"Erro ao abrir interface administrativa: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir interface administrativa: {str(e)}")
    
    def abrir_horarios_escolares(self):
        """Abre interface de horários escolares."""
        try:
            from horarios_escolares import InterfaceHorariosEscolares
            
            horarios_window = Toplevel(self.janela)
            horarios_window.title("Horários Escolares")
            horarios_window.geometry('1200x700')
            
            InterfaceHorariosEscolares(horarios_window, self.janela)
            
            logger.info("Interface de horários escolares aberta")
            
        except Exception as e:
            logger.exception(f"Erro ao abrir horários escolares: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir horários escolares: {str(e)}")
    
    def abrir_transicao_ano_letivo(self):
        """Abre interface de transição de ano letivo com autenticação."""
        try:
            import os
            from dotenv import load_dotenv
            from tkinter import simpledialog
            
            # Carregar senha do banco de dados
            load_dotenv()
            senha_correta = os.getenv('DB_PASSWORD')
            
            # Solicitar senha ao usuário
            senha_digitada = simpledialog.askstring(
                "Autenticação Necessária",
                "Digite a senha do banco de dados para acessar a Transição de Ano Letivo:",
                show='*'
            )
            
            # Verificar se o usuário cancelou
            if senha_digitada is None:
                return
            
            # Verificar senha
            if senha_digitada != senha_correta:
                messagebox.showerror(
                    "Acesso Negado",
                    "Senha incorreta! A transição de ano letivo é uma operação crítica\n"
                    "e requer autenticação para prosseguir."
                )
                return
            
            # Se a senha estiver correta, abrir a interface
            from transicao_ano_letivo import abrir_interface_transicao
            abrir_interface_transicao(janela_principal=self.janela)
            
            logger.info("Interface de transição de ano letivo aberta com sucesso")
            
        except Exception as e:
            logger.exception(f"Erro ao abrir transição de ano letivo: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir transição de ano letivo: {str(e)}")
    
    def abrir_solicitacao_professores(self):
        """Abre interface de solicitação de professores e coordenadores."""
        try:
            from InterfaceSolicitacaoProfessores import abrir_interface_solicitacao
            abrir_interface_solicitacao(janela_principal=self.janela)
            logger.info("Interface de solicitação de professores aberta")
        except Exception as e:
            logger.exception(f"Erro ao abrir solicitação de professores: {e}")
            messagebox.showerror("Erro", f"Não foi possível abrir a solicitação: {e}")


class DeclaracaoCallbacks:
    """Callbacks relacionados a declarações."""
    
    def __init__(self, janela):
        self.janela = janela
    
    def abrir_gerenciador_documentos(self):
        """Abre gerenciador de documentos de funcionários."""
        try:
            from GerenciadorDocumentosFuncionarios import GerenciadorDocumentosFuncionarios
            
            gerenciador_window = Toplevel(self.janela)
            GerenciadorDocumentosFuncionarios(gerenciador_window)
            
            logger.info("Gerenciador de documentos aberto")
            
        except Exception as e:
            logger.exception(f"Erro ao abrir gerenciador de documentos: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir gerenciador: {str(e)}")
    
    def abrir_gerenciador_licencas(self):
        """Abre gerenciador de licenças."""
        try:
            from InterfaceGerenciamentoLicencas import InterfaceGerenciamentoLicencas
            
            licencas_window = Toplevel(self.janela)
            InterfaceGerenciamentoLicencas(licencas_window)
            
            logger.info("Gerenciador de licenças aberto")
            
        except Exception as e:
            logger.exception(f"Erro ao abrir gerenciador de licenças: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir gerenciador: {str(e)}")
    
    def abrir_gerenciador_documentos_sistema(self):
        """Abre gerenciador de documentos do sistema."""
        try:
            from GerenciadorDocumentosSistema import GerenciadorDocumentosSistema
            
            self.janela.withdraw()
            
            janela_docs = Toplevel(self.janela)
            janela_docs.title("Gerenciador de Documentos do Sistema")
            app = GerenciadorDocumentosSistema(janela_docs)
            janela_docs.focus_force()
            janela_docs.grab_set()
            
            def ao_fechar():
                self.janela.deiconify()
                janela_docs.destroy()
            
            janela_docs.protocol("WM_DELETE_WINDOW", ao_fechar)
            
            logger.info("Gerenciador de documentos do sistema aberto")
            
        except Exception as e:
            logger.exception(f"Erro ao abrir gerenciador de documentos do sistema: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir gerenciador: {str(e)}")
            self.janela.deiconify()
    
    def declaracao_comparecimento(self):
        """Abre interface para gerar declaração de comparecimento."""
        try:
            from ui.interfaces_extended import abrir_interface_declaracao_comparecimento
            from declaracao_comparecimento import gerar_declaracao_comparecimento_responsavel
            abrir_interface_declaracao_comparecimento(self.janela, gerar_declaracao_comparecimento_responsavel)
        except Exception as e:
            logger.exception(f"Erro ao abrir declaração de comparecimento: {e}")
            messagebox.showerror("Erro", f"Não foi possível abrir a declaração: {e}")


class ActionCallbacksManager:
    """
    Gerenciador central de todos os callbacks de ação.
    
    Centraliza e organiza todos os callbacks que antes estavam
    embutidos na função criar_acoes() do main.py.
    """
    
    def __init__(self, janela, atualizar_tabela_callback: Optional[Callable] = None):
        """
        Inicializa o gerenciador de callbacks.
        
        Args:
            janela: Janela principal da aplicação
            atualizar_tabela_callback: Função para atualizar a tabela principal
        """
        self.janela = janela
        self.atualizar_tabela_callback = atualizar_tabela_callback
        
        # Inicializar categorias de callbacks
        self.cadastro = CadastroCallbacks(janela, atualizar_tabela_callback)
        self.reports = ReportCallbacks(janela)
        self.historico = HistoricoCallbacks(janela)
        self.administrativo = AdministrativoCallbacks(janela)
        self.declaracao = DeclaracaoCallbacks(janela)
        self.rh = RHCallbacks(janela)
        
        logger.debug("ActionCallbacksManager inicializado com 6 categorias")
    
    # Métodos de conveniência para acesso direto
    
    def cadastrar_novo_aluno(self):
        """Atalho para cadastro.cadastrar_novo_aluno()"""
        return self.cadastro.cadastrar_novo_aluno()
    
    def cadastrar_novo_funcionario(self):
        """Atalho para cadastro.cadastrar_novo_funcionario()"""
        return self.cadastro.cadastrar_novo_funcionario()
    
    def abrir_historico_escolar(self):
        """Atalho para historico.abrir_historico_escolar()"""
        return self.historico.abrir_historico_escolar()
    
    def abrir_interface_administrativa(self):
        """Atalho para administrativo.abrir_interface_administrativa()"""
        return self.administrativo.abrir_interface_administrativa()
    
    def abrir_horarios_escolares(self):
        """Atalho para administrativo.abrir_horarios_escolares()"""
        return self.administrativo.abrir_horarios_escolares()
    
    def abrir_transicao_ano_letivo(self):
        """Atalho para administrativo.abrir_transicao_ano_letivo()"""
        return self.administrativo.abrir_transicao_ano_letivo()
    
    def abrir_gerenciador_documentos(self):
        """Atalho para declaracao.abrir_gerenciador_documentos()"""
        return self.declaracao.abrir_gerenciador_documentos()
    
    def abrir_gerenciador_licencas(self):
        """Atalho para declaracao.abrir_gerenciador_licencas()"""
        return self.declaracao.abrir_gerenciador_licencas()
    
    # Atalhos para relatórios mais comuns
    def lista_atualizada(self):
        """Atalho para reports.lista_atualizada()"""
        return self.reports.lista_atualizada()
    
    def lista_reuniao(self):
        """Atalho para reports.lista_reuniao()"""
        return self.reports.lista_reuniao()
    
    def lista_notas(self):
        """Atalho para reports.lista_notas()"""
        return self.reports.lista_notas()
    
    def abrir_cadastro_notas(self):
        """Atalho para reports.abrir_cadastro_notas()"""
        return self.reports.abrir_cadastro_notas()
    
    def relatorio_contatos_responsaveis(self):
        """Atalho para reports.relatorio_contatos_responsaveis()"""
        return self.reports.relatorio_contatos_responsaveis()
    
    def abrir_cadastro_faltas(self):
        """Atalho para reports.abrir_cadastro_faltas()"""
        return self.reports.abrir_cadastro_faltas()
    
    def lista_atualizada_semed(self):
        """Atalho para reports.lista_atualizada_semed()"""
        return self.reports.lista_atualizada_semed()
    
    def relatorio_movimentacao_mensal(self, numero_mes: int):
        """Atalho para reports.relatorio_movimentacao_mensal()"""
        return self.reports.relatorio_movimentacao_mensal(numero_mes)
    
    def gerar_folhas_de_ponto(self, numero_mes: int):
        """Atalho para rh.gerar_folhas_de_ponto()"""
        return self.rh.gerar_folhas_de_ponto(numero_mes)
    
    def gerar_resumo_ponto(self, numero_mes: int):
        """Atalho para rh.gerar_resumo_ponto()"""
        return self.rh.gerar_resumo_ponto(numero_mes)
    
    def abrir_solicitacao_professores(self):
        """Atalho para administrativo.abrir_solicitacao_professores()"""
        return self.administrativo.abrir_solicitacao_professores()
    
    def declaracao_comparecimento(self):
        """Atalho para declaracao.declaracao_comparecimento()"""
        return self.declaracao.declaracao_comparecimento()
