"""
Exemplo de integração da funcionalidade de importação de códigos INEP
ao menu principal do sistema.

Este é um exemplo de como adicionar a funcionalidade ao menu.
Você pode adaptar conforme a estrutura do seu menu principal.
"""

# OPÇÃO 1: Adicionar ao menu de ações de aluno
# =============================================

# Em src/ui/actions/aluno.py ou similar:

def importar_codigos_inep(self):
    """Abre a interface de importação de códigos INEP"""
    try:
        from src.interfaces.mapeamento_codigo_inep import abrir_interface_mapeamento_inep
        
        # Abrir interface passando a janela principal
        abrir_interface_mapeamento_inep(self.app.janela)
        
        # Após fechar a interface, atualizar a tabela de alunos se necessário
        if hasattr(self.app, 'atualizar_tabela_alunos'):
            self.app.atualizar_tabela_alunos()
            
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Erro", f"Erro ao abrir importação de códigos INEP: {str(e)}")


# OPÇÃO 2: Adicionar como item de menu
# =====================================

# Se você tem um menu tipo "Alunos", adicione:

def criar_menu_alunos(self):
    """Cria o menu de Alunos"""
    # ... código existente ...
    
    # Adicionar item de menu
    menu_alunos.add_command(
        label="Importar Códigos INEP",
        command=self.importar_codigos_inep
    )
    
    # Ou com separador
    menu_alunos.add_separator()
    menu_alunos.add_command(
        label="Importar Códigos INEP...",
        command=self.importar_codigos_inep
    )


# OPÇÃO 3: Adicionar como botão em uma toolbar
# ============================================

# Se você tem uma barra de ferramentas:

from tkinter import Button

btn_importar_inep = Button(
    toolbar_frame,
    text="Importar Códigos INEP",
    command=lambda: abrir_interface_mapeamento_inep(janela_principal),
    font=('Arial 10'),
    bg='#038cfc',
    fg='#ffffff'
)
btn_importar_inep.pack(side='left', padx=5)


# OPÇÃO 4: Adicionar no menu de contexto (clique direito)
# ======================================================

# Se você tem um menu de contexto na tabela de alunos:

def criar_menu_contexto_aluno(self, event):
    """Cria menu de contexto ao clicar com botão direito"""
    menu = Menu(self.tree, tearoff=0)
    
    # ... outros itens do menu ...
    
    menu.add_separator()
    menu.add_command(
        label="Importar Códigos INEP em Massa",
        command=self.importar_codigos_inep
    )
    
    menu.post(event.x_root, event.y_root)


# OPÇÃO 5: Adicionar na tela principal com ícone
# ==============================================

from tkinter import Frame, Label
from PIL import Image, ImageTk

# Criar um card/botão na tela principal
def criar_card_importacao_inep(self, parent_frame):
    """Cria um card para importação de códigos INEP"""
    
    card = Frame(parent_frame, bg='#ffffff', relief='raised', bd=2)
    card.pack(side='left', padx=10, pady=10)
    
    # Título
    Label(
        card,
        text="Importar Códigos INEP",
        font=('Arial 12 bold'),
        bg='#ffffff'
    ).pack(padx=20, pady=(10, 5))
    
    # Descrição
    Label(
        card,
        text="Importar códigos INEP\ndo arquivo Excel",
        font=('Arial 9'),
        bg='#ffffff',
        fg='#666666'
    ).pack(padx=20, pady=5)
    
    # Botão
    Button(
        card,
        text="Abrir",
        command=self.importar_codigos_inep,
        font=('Arial 10 bold'),
        bg='#00a095',
        fg='#ffffff',
        width=15
    ).pack(padx=20, pady=10)
    
    return card


# OPÇÃO 6: Adicionar permissão no RBAC (se usar controle de acesso)
# ================================================================

# Em auth/permissions.py ou similar:

PERMISSIONS = {
    # ... permissões existentes ...
    
    'alunos': {
        'criar': 'Criar novos alunos',
        'editar': 'Editar alunos existentes',
        'excluir': 'Excluir alunos',
        'visualizar': 'Visualizar alunos',
        'importar_inep': 'Importar códigos INEP',  # <- Nova permissão
    }
}

# E use o decorator:
from auth.decorators import requer_permissao

@requer_permissao('alunos.importar_inep')
def importar_codigos_inep(self):
    """Importa códigos INEP (requer permissão)"""
    from src.interfaces.mapeamento_codigo_inep import abrir_interface_mapeamento_inep
    abrir_interface_mapeamento_inep(self.janela)


# EXEMPLO COMPLETO DE INTEGRAÇÃO
# ==============================

class AlunoActionsMixin:
    """Mixin com ações relacionadas a alunos"""
    
    def __init__(self):
        # ... código existente ...
        pass
    
    def cadastrar_novo_aluno(self):
        """Cadastra novo aluno"""
        # ... código existente ...
        pass
    
    def editar_aluno(self):
        """Edita aluno selecionado"""
        # ... código existente ...
        pass
    
    def importar_codigos_inep(self):
        """
        Abre interface para importação de códigos INEP em massa.
        
        Funcionalidade:
        - Carrega arquivo Excel com códigos INEP
        - Mapeia automaticamente nomes com alunos do banco
        - Permite revisão antes de aplicar
        - Atualiza códigos INEP no banco de dados
        """
        try:
            from src.interfaces.mapeamento_codigo_inep import InterfaceConfirmacaoMapeamentoINEP
            from src.core.config_logs import get_logger
            
            logger = get_logger(__name__)
            logger.info("Abrindo interface de importação de códigos INEP")
            
            # Criar interface
            interface = InterfaceConfirmacaoMapeamentoINEP(self.app.janela)
            
            # Aguardar fechamento da janela
            self.app.janela.wait_window(interface.janela)
            
            # Atualizar tabela de alunos após fechamento
            if hasattr(self.app, 'atualizar_tabela_alunos'):
                self.app.atualizar_tabela_alunos()
                logger.info("Tabela de alunos atualizada após importação de códigos INEP")
            
        except ImportError as e:
            from tkinter import messagebox
            messagebox.showerror(
                "Erro de Importação",
                f"Erro ao importar módulo de códigos INEP:\n{str(e)}\n\n"
                f"Verifique se os arquivos foram criados corretamente."
            )
        except Exception as e:
            from tkinter import messagebox
            from src.core.config_logs import get_logger
            
            logger = get_logger(__name__)
            logger.exception(f"Erro ao abrir importação de códigos INEP: {e}")
            
            messagebox.showerror(
                "Erro",
                f"Erro ao abrir importação de códigos INEP:\n{str(e)}"
            )


# TESTE RÁPIDO
# ===========

if __name__ == "__main__":
    """Teste rápido da integração"""
    from tkinter import Tk
    from src.interfaces.mapeamento_codigo_inep import abrir_interface_mapeamento_inep
    
    root = Tk()
    root.withdraw()  # Ocultar janela principal
    
    abrir_interface_mapeamento_inep(root)
