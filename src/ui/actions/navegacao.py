"""Mixin de navegação/abertura de interfaces para o ActionHandler."""

from tkinter import messagebox, Toplevel
import logging

logger = logging.getLogger(__name__)


class NavegacaoActionsMixin:
    """Métodos do ActionHandler para abertura de interfaces secundárias."""

    def abrir_historico_escolar(self):
        """Abre a interface de gerenciamento de histórico escolar."""
        try:
            from src.interfaces.historico_escolar import InterfaceHistoricoEscolar

            janela_historico = Toplevel(self.app.janela)
            janela_historico.title("Histórico Escolar")
            janela_historico.geometry('1200x700')
            janela_historico.configure(background=self.app.colors['co1'])
            janela_historico.focus_set()
            janela_historico.grab_set()

            self.app.janela.withdraw()

            app_historico = InterfaceHistoricoEscolar(janela=janela_historico, janela_pai=self.app.janela)

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
            from src.interfaces.administrativa import InterfaceAdministrativa

            janela_admin = Toplevel(self.app.janela)
            janela_admin.title("Administração do Sistema")
            janela_admin.geometry('1000x600')
            janela_admin.configure(background=self.app.colors['co1'])
            janela_admin.focus_set()
            janela_admin.grab_set()

            self.app.janela.withdraw()

            app_admin = InterfaceAdministrativa(janela_admin, janela_principal=self.app.janela)

            def ao_fechar_admin():
                self.app.janela.deiconify()
                janela_admin.destroy()

            janela_admin.protocol("WM_DELETE_WINDOW", ao_fechar_admin)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir administração: {str(e)}")
            self.logger.error(f"Erro ao abrir administração: {str(e)}")
            self.app.janela.deiconify()
