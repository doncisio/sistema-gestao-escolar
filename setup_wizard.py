"""
Script de configuração inicial do Sistema de Gestão Escolar.
Executado automaticamente após a instalação para configurar banco de dados.
"""
import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from mysql.connector import Error
from config_logs import get_logger

# Logger
logger = get_logger(__name__)

class ConfiguracaoInicial:
    def __init__(self):
        self.janela = tk.Tk()
        self.janela.title("Configuração Inicial - Sistema de Gestão Escolar")
        self.janela.geometry("700x600")
        self.janela.resizable(False, False)
        
        # Centralizar janela
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.janela.winfo_screenheight() // 2) - (600 // 2)
        self.janela.geometry(f"700x600+{x}+{y}")
        
        self.pagina_atual = 0
        self.config = {}
        self.criar_interface()
        
    def criar_interface(self):
        # Frame principal
        self.container = ttk.Frame(self.janela, padding="20")
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(
            self.container,
            text="Bem-vindo ao Sistema de Gestão Escolar",
            font=("Arial", 16, "bold")
        )
        titulo.pack(pady=(0, 20))
        
        # Frame para páginas
        self.frame_pagina = ttk.Frame(self.container)
        self.frame_pagina.pack(fill=tk.BOTH, expand=True)
        
        # Botões de navegação
        frame_botoes = ttk.Frame(self.container)
        frame_botoes.pack(pady=(20, 0), fill=tk.X)
        
        self.btn_voltar = ttk.Button(
            frame_botoes,
            text="← Voltar",
            command=self.pagina_anterior
        )
        self.btn_voltar.pack(side=tk.LEFT)
        
        self.btn_proximo = ttk.Button(
            frame_botoes,
            text="Próximo →",
            command=self.proxima_pagina
        )
        self.btn_proximo.pack(side=tk.RIGHT)
        
        self.mostrar_pagina_0_boas_vindas()
        
    def limpar_frame_pagina(self):
        for widget in self.frame_pagina.winfo_children():
            widget.destroy()
    
    def mostrar_pagina_0_boas_vindas(self):
        self.limpar_frame_pagina()
        self.btn_voltar.config(state=tk.DISABLED)
        
        texto = """Este assistente irá guiá-lo na configuração inicial do sistema.

Vamos configurar:
  1. Instalação do MySQL Server (se necessário)
  2. Criação do banco de dados
  3. Configurações da escola
  4. Integração com Google Drive (opcional)

Clique em 'Próximo' para começar."""
        
        label = ttk.Label(
            self.frame_pagina,
            text=texto,
            justify=tk.LEFT,
            font=("Arial", 11)
        )
        label.pack(pady=30)
        
    def mostrar_pagina_1_mysql(self):
        self.limpar_frame_pagina()
        self.btn_voltar.config(state=tk.NORMAL)
        
        ttk.Label(
            self.frame_pagina,
            text="Passo 1: MySQL Server",
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 20))
        
        # Verificar se MySQL está instalado
        mysql_instalado = self.verificar_mysql_instalado()
        
        if mysql_instalado:
            ttk.Label(
                self.frame_pagina,
                text="✓ MySQL Server já está instalado!",
                foreground="green",
                font=("Arial", 11)
            ).pack(anchor=tk.W, pady=10)
        else:
            ttk.Label(
                self.frame_pagina,
                text="MySQL Server não foi encontrado no sistema.",
                foreground="orange",
                font=("Arial", 11)
            ).pack(anchor=tk.W, pady=10)
            
            frame_opcoes = ttk.LabelFrame(self.frame_pagina, text="Opções de Instalação", padding=10)
            frame_opcoes.pack(fill=tk.BOTH, expand=True, pady=10)
            
            ttk.Label(
                frame_opcoes,
                text="Escolha uma opção:",
                font=("Arial", 10, "bold")
            ).pack(anchor=tk.W, pady=(0, 10))
            
            btn_baixar = ttk.Button(
                frame_opcoes,
                text="🌐 Baixar MySQL Community Server",
                command=self.abrir_download_mysql
            )
            btn_baixar.pack(fill=tk.X, pady=5)
            
            ttk.Label(
                frame_opcoes,
                text="Ou instale manualmente:",
                font=("Arial", 9)
            ).pack(anchor=tk.W, pady=(10, 5))
            
            btn_xampp = ttk.Button(
                frame_opcoes,
                text="💾 Baixar XAMPP (MySQL + phpMyAdmin)",
                command=lambda: self.abrir_url("https://www.apachefriends.org/download.html")
            )
            btn_xampp.pack(fill=tk.X, pady=5)
            
            ttk.Label(
                frame_opcoes,
                text="\n⚠️ Após a instalação, reinicie este assistente.",
                foreground="red",
                font=("Arial", 9, "italic")
            ).pack(anchor=tk.W, pady=10)
    
    def mostrar_pagina_2_banco(self):
        self.limpar_frame_pagina()
        
        ttk.Label(
            self.frame_pagina,
            text="Passo 2: Configuração do Banco de Dados",
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 20))
        
        # Formulário
        frame_form = ttk.Frame(self.frame_pagina)
        frame_form.pack(fill=tk.BOTH, expand=True)
        
        campos = [
            ("Host:", "db_host", "localhost"),
            ("Porta:", "db_port", "3306"),
            ("Usuário Root:", "db_root_user", "root"),
            ("Senha Root:", "db_root_password", ""),
            ("Nome do Banco:", "db_name", "gestao_escolar"),
            ("Novo Usuário:", "db_user", "gestao_user"),
            ("Senha do Usuário:", "db_password", ""),
        ]
        
        self.entries = {}
        for i, (label, key, default) in enumerate(campos):
            ttk.Label(frame_form, text=label).grid(row=i, column=0, sticky=tk.W, pady=5, padx=(0, 10))
            
            if "senha" in label.lower() or "password" in key:
                entry = ttk.Entry(frame_form, width=40, show="*")
            else:
                entry = ttk.Entry(frame_form, width=40)
            
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky=tk.W, pady=5)
            self.entries[key] = entry
        
        # Botão testar conexão
        frame_botoes = ttk.Frame(frame_form)
        frame_botoes.grid(row=len(campos), column=0, columnspan=2, pady=20)
        
        ttk.Button(
            frame_botoes,
            text="🔌 Testar Conexão",
            command=self.testar_conexao
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            frame_botoes,
            text="🗄️ Criar Banco de Dados",
            command=self.criar_banco_dados
        ).pack(side=tk.LEFT, padx=5)
        
        # Label de status
        self.label_status_db = ttk.Label(frame_form, text="", font=("Arial", 9))
        self.label_status_db.grid(row=len(campos)+1, column=0, columnspan=2, pady=10)
    
    def mostrar_pagina_3_escola(self):
        self.limpar_frame_pagina()
        
        ttk.Label(
            self.frame_pagina,
            text="Passo 3: Informações da Escola",
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 20))
        
        frame_form = ttk.Frame(self.frame_pagina)
        frame_form.pack(fill=tk.BOTH, expand=True)
        
        campos = [
            ("ID da Escola:", "escola_id", "1"),
            ("Nome da Escola:", "escola_nome", ""),
            ("Modo de Teste:", "test_mode", "False"),
        ]
        
        for i, (label, key, default) in enumerate(campos):
            ttk.Label(frame_form, text=label).grid(row=i, column=0, sticky=tk.W, pady=5, padx=(0, 10))
            
            if key == "test_mode":
                var = tk.StringVar(value=default)
                combo = ttk.Combobox(frame_form, textvariable=var, values=["True", "False"], width=37, state="readonly")
                combo.grid(row=i, column=1, sticky=tk.W, pady=5)
                self.entries[key] = var
            else:
                entry = ttk.Entry(frame_form, width=40)
                entry.insert(0, default)
                entry.grid(row=i, column=1, sticky=tk.W, pady=5)
                self.entries[key] = entry
    
    def mostrar_pagina_4_google_drive(self):
        self.limpar_frame_pagina()
        
        ttk.Label(
            self.frame_pagina,
            text="Passo 4: Modo de Armazenamento de Documentos",
            font=("Arial", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 20))
        
        texto = """Escolha onde os documentos serão salvos:

OPÇÃO 1: Armazenamento Local
  • Documentos salvos no computador local
  • Não requer internet
  • Recomendado para uso offline

OPÇÃO 2: Google Drive
  • Documentos salvos no Google Drive
  • Acesso de qualquer lugar
  • Backup automático na nuvem
  • Requer credenciais OAuth 2.0"""
        
        ttk.Label(
            self.frame_pagina,
            text=texto,
            justify=tk.LEFT,
            font=("Arial", 10)
        ).pack(anchor=tk.W, pady=10)
        
        # Frame para seleção de modo
        frame_modo = ttk.LabelFrame(self.frame_pagina, text="Escolha o Modo", padding=10)
        frame_modo.pack(fill=tk.X, pady=20)
        
        self.var_modo_storage = tk.StringVar(value="local")
        
        ttk.Radiobutton(
            frame_modo,
            text="💾 Armazenamento Local (Recomendado)",
            variable=self.var_modo_storage,
            value="local",
            command=self._atualizar_opcoes_storage
        ).pack(anchor=tk.W, pady=5)
        
        ttk.Radiobutton(
            frame_modo,
            text="☁️ Google Drive",
            variable=self.var_modo_storage,
            value="drive",
            command=self._atualizar_opcoes_storage
        ).pack(anchor=tk.W, pady=5)
        
        # Frame para configuração do Google Drive (inicialmente oculto)
        self.frame_drive_config = ttk.LabelFrame(
            self.frame_pagina,
            text="Configuração do Google Drive",
            padding=10
        )
        self.frame_drive_config.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            self.frame_drive_config,
            text="Selecione o arquivo credentials.json:",
            font=("Arial", 9)
        ).pack(anchor=tk.W, pady=(0, 5))
        
        frame_arquivo = ttk.Frame(self.frame_drive_config)
        frame_arquivo.pack(fill=tk.X, pady=5)
        
        self.entry_credentials = ttk.Entry(frame_arquivo, width=50)
        self.entry_credentials.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            frame_arquivo,
            text="📁 Selecionar",
            command=self.selecionar_credentials
        ).pack(side=tk.LEFT)
        
        # Link para tutorial
        link = ttk.Label(
            self.frame_drive_config,
            text="📖 Como obter credentials.json?",
            foreground="blue",
            cursor="hand2",
            font=("Arial", 9, "underline")
        )
        link.pack(anchor=tk.W, pady=10)
        link.bind("<Button-1>", lambda e: self.abrir_url("https://developers.google.com/drive/api/quickstart/python"))
        
        # Inicializar visibilidade
        self._atualizar_opcoes_storage()
    
    def mostrar_pagina_5_finalizar(self):
        self.limpar_frame_pagina()
        self.btn_proximo.config(text="✓ Concluir", command=self.finalizar)
        
        ttk.Label(
            self.frame_pagina,
            text="Configuração Concluída!",
            font=("Arial", 14, "bold"),
            foreground="green"
        ).pack(anchor=tk.W, pady=(0, 20))
        
        texto = """Tudo pronto para usar o Sistema de Gestão Escolar!

Resumo da configuração:"""
        
        ttk.Label(
            self.frame_pagina,
            text=texto,
            justify=tk.LEFT,
            font=("Arial", 11)
        ).pack(anchor=tk.W, pady=10)
        
        # Mostrar resumo
        frame_resumo = ttk.LabelFrame(self.frame_pagina, text="Resumo", padding=10)
        frame_resumo.pack(fill=tk.BOTH, expand=True, pady=10)
        
        resumo = f"""✓ Banco de Dados: {self.config.get('db_name', 'N/A')}
✓ Host: {self.config.get('db_host', 'N/A')}
✓ Escola: {self.config.get('escola_nome', 'N/A')}
✓ Armazenamento: {self.config.get('modo_storage', 'Local').upper()}
{f"✓ Google Drive: Configurado" if self.config.get('credentials_path') else ""}"""
        
        ttk.Label(
            frame_resumo,
            text=resumo,
            justify=tk.LEFT,
            font=("Courier", 10)
        ).pack(anchor=tk.W)
    
    def verificar_mysql_instalado(self):
        try:
            result = subprocess.run(
                ["mysql", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def abrir_download_mysql(self):
        self.abrir_url("https://dev.mysql.com/downloads/mysql/")
    
    def abrir_url(self, url):
        import webbrowser
        webbrowser.open(url)
    
    def testar_conexao(self):
        try:
            conexao = mysql.connector.connect(
                host=self.entries['db_host'].get(),
                port=int(self.entries['db_port'].get()),
                user=self.entries['db_root_user'].get(),
                password=self.entries['db_root_password'].get()
            )
            
            if conexao.is_connected():
                self.label_status_db.config(
                    text="✓ Conexão bem-sucedida!",
                    foreground="green"
                )
                conexao.close()
                messagebox.showinfo("Sucesso", "Conexão com MySQL estabelecida com sucesso!")
        except Error as e:
            self.label_status_db.config(
                text=f"✗ Erro: {str(e)}",
                foreground="red"
            )
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao MySQL:\n\n{str(e)}")
    
    def criar_banco_dados(self):
        try:
            # Conectar como root
            conexao = mysql.connector.connect(
                host=self.entries['db_host'].get(),
                port=int(self.entries['db_port'].get()),
                user=self.entries['db_root_user'].get(),
                password=self.entries['db_root_password'].get()
            )
            
            cursor = conexao.cursor()
            
            # Criar banco de dados
            db_name = self.entries['db_name'].get()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            # Criar usuário
            db_user = self.entries['db_user'].get()
            db_password = self.entries['db_password'].get()
            
            cursor.execute(f"DROP USER IF EXISTS '{db_user}'@'localhost'")
            cursor.execute(f"CREATE USER '{db_user}'@'localhost' IDENTIFIED BY '{db_password}'")
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{db_user}'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
            conexao.commit()
            cursor.close()
            conexao.close()
            
            self.label_status_db.config(
                text="✓ Banco de dados criado com sucesso!",
                foreground="green"
            )
            
            # Salvar configurações
            for key in ['db_host', 'db_port', 'db_name', 'db_user', 'db_password']:
                self.config[key] = self.entries[key].get()
            
            messagebox.showinfo(
                "Sucesso",
                f"Banco de dados '{db_name}' criado com sucesso!\nUsuário '{db_user}' configurado com permissões."
            )
            
        except Error as e:
            self.label_status_db.config(
                text=f"✗ Erro: {str(e)}",
                foreground="red"
            )
            messagebox.showerror("Erro", f"Erro ao criar banco de dados:\n\n{str(e)}")
    
    def _atualizar_opcoes_storage(self):
        """Mostra/oculta opções de Google Drive conforme seleção."""
        if self.var_modo_storage.get() == "drive":
            self.frame_drive_config.pack(fill=tk.X, pady=10)
        else:
            self.frame_drive_config.pack_forget()
    
    def selecionar_credentials(self):
        arquivo = filedialog.askopenfilename(
            title="Selecionar credentials.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if arquivo:
            self.entry_credentials.delete(0, tk.END)
            self.entry_credentials.insert(0, arquivo)
            self.config['credentials_path'] = arquivo
    
    def salvar_config_env(self):
        """Salva configurações no arquivo .env"""
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        
        # Determinar se usa Google Drive
        usar_drive = self.config.get('modo_storage', 'local') == 'drive' and self.config.get('credentials_path')
        
        linhas = [
            "# Configuração do Banco de Dados",
            f"DB_HOST={self.config.get('db_host', 'localhost')}",
            f"DB_PORT={self.config.get('db_port', '3306')}",
            f"DB_USER={self.config.get('db_user', 'gestao_user')}",
            f"DB_PASSWORD={self.config.get('db_password', '')}",
            f"DB_NAME={self.config.get('db_name', 'gestao_escolar')}",
            "",
            "# Configuração da Escola",
            f"ESCOLA_ID={self.config.get('escola_id', '1')}",
            f"ESCOLA_NOME={self.config.get('escola_nome', 'Minha Escola')}",
            "",
            "# Modo de Teste",
            f"GESTAO_TEST_MODE={self.config.get('test_mode', 'False')}",
            "",
            "# Armazenamento de Documentos",
            f"USAR_GOOGLE_DRIVE={'True' if usar_drive else 'False'}",
        ]
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(linhas))
        
        # Copiar credentials.json se modo Drive e fornecido
        if usar_drive and self.config.get('credentials_path'):
            import shutil
            destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
            try:
                shutil.copy2(self.config['credentials_path'], destino)
                logger.info("credentials.json copiado com sucesso")
            except Exception as e:
                logger.warning(f"Erro ao copiar credentials.json: {e}")
    
    def proxima_pagina(self):
        self.pagina_atual += 1
        
        if self.pagina_atual == 1:
            self.mostrar_pagina_1_mysql()
        elif self.pagina_atual == 2:
            self.mostrar_pagina_2_banco()
        elif self.pagina_atual == 3:
            # Salvar configs do banco
            for key in ['db_host', 'db_port', 'db_name', 'db_user', 'db_password']:
                if key in self.entries:
                    if isinstance(self.entries[key], tk.StringVar):
                        self.config[key] = self.entries[key].get()
                    else:
                        self.config[key] = self.entries[key].get()
        elif self.pagina_atual == 4:
            # Salvar configs da escola
            for key in ['escola_id', 'escola_nome', 'test_mode']:
                if key in self.entries:
                    if isinstance(self.entries[key], tk.StringVar):
                        self.config[key] = self.entries[key].get()
                    else:
                        self.config[key] = self.entries[key].get()
            
            # Salvar modo de storage
            self.config['modo_storage'] = self.var_modo_storage.get()

            # Exibir página de configuração do armazenamento
            self.mostrar_pagina_4_google_drive()
        elif self.pagina_atual == 5:
            self.mostrar_pagina_5_finalizar()
    
    def pagina_anterior(self):
        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            
            if self.pagina_atual == 0:
                self.mostrar_pagina_0_boas_vindas()
            elif self.pagina_atual == 1:
                self.mostrar_pagina_1_mysql()
            elif self.pagina_atual == 2:
                self.mostrar_pagina_2_banco()
            elif self.pagina_atual == 3:
                self.mostrar_pagina_3_escola()
            elif self.pagina_atual == 4:
                self.mostrar_pagina_4_google_drive()
    
    def finalizar(self):
        try:
            self.salvar_config_env()
            messagebox.showinfo(
                "Configuração Concluída",
                "O sistema foi configurado com sucesso!\n\n"
                "O Sistema de Gestão Escolar será iniciado agora."
            )
            self.janela.destroy()
        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Erro ao salvar configurações:\n\n{str(e)}"
            )
    
    def executar(self):
        self.janela.mainloop()


if __name__ == '__main__':
    app = ConfiguracaoInicial()
    app.executar()
