"""
Interface de Gestão de Usuários

Esta interface permite aos administradores:
- Visualizar usuários do sistema
- Criar novos usuários (vinculando a funcionários)
- Editar perfis e permissões
- Desativar/ativar usuários
- Resetar senhas
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict, Any
import hashlib
import secrets

from config_logs import get_logger
from db.connection import get_connection, get_cursor
from auth.usuario_logado import UsuarioLogado

logger = get_logger(__name__)


class GestaoUsuariosWindow:
    """Janela de gestão de usuários do sistema."""
    
    PERFIS = [
        ('administrador', 'Administrador'),
        ('coordenador', 'Coordenador'),
        ('professor', 'Professor')
    ]
    
    def __init__(self, parent):
        """
        Inicializa a janela de gestão de usuários.
        
        Args:
            parent: Janela pai (tk.Tk ou tk.Toplevel)
        """
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Gestão de Usuários")
        self.window.geometry("1000x600")
        self.window.transient(parent)
        
        # Centralizar janela
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"+{x}+{y}")
        
        # Variáveis de estado
        self.usuario_selecionado = None
        
        self._criar_interface()
        self._carregar_usuarios()
        
    def _criar_interface(self):
        """Cria os widgets da interface."""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = ttk.Label(main_frame, text="Gestão de Usuários do Sistema", 
                          font=('Segoe UI', 14, 'bold'))
        titulo.pack(pady=(0, 10))
        
        # Frame de conteúdo (lado a lado)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # === Lado esquerdo: Lista de usuários ===
        left_frame = ttk.LabelFrame(content_frame, text="Usuários Cadastrados", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Barra de busca
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._filtrar_usuarios)
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Treeview de usuários
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('id', 'username', 'nome', 'perfil', 'ativo')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('id', text='ID')
        self.tree.heading('username', text='Usuário')
        self.tree.heading('nome', text='Nome')
        self.tree.heading('perfil', text='Perfil')
        self.tree.heading('ativo', text='Status')
        
        self.tree.column('id', width=50, anchor='center')
        self.tree.column('username', width=120)
        self.tree.column('nome', width=200)
        self.tree.column('perfil', width=100)
        self.tree.column('ativo', width=80, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind de seleção
        self.tree.bind('<<TreeviewSelect>>', self._on_usuario_selecionado)
        
        # === Lado direito: Formulário ===
        right_frame = ttk.LabelFrame(content_frame, text="Dados do Usuário", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Campos do formulário
        form_frame = ttk.Frame(right_frame)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Funcionário (combobox)
        ttk.Label(form_frame, text="Funcionário:").grid(row=0, column=0, sticky='w', pady=5)
        self.funcionario_var = tk.StringVar()
        self.funcionario_combo = ttk.Combobox(form_frame, textvariable=self.funcionario_var, 
                                              width=35, state='readonly')
        self.funcionario_combo.grid(row=0, column=1, pady=5, padx=5)
        
        # Username
        ttk.Label(form_frame, text="Nome de Usuário:").grid(row=1, column=0, sticky='w', pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(form_frame, textvariable=self.username_var, width=37)
        self.username_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Perfil
        ttk.Label(form_frame, text="Perfil:").grid(row=2, column=0, sticky='w', pady=5)
        self.perfil_var = tk.StringVar()
        self.perfil_combo = ttk.Combobox(form_frame, textvariable=self.perfil_var, 
                                         width=35, state='readonly')
        self.perfil_combo['values'] = [p[1] for p in self.PERFIS]
        self.perfil_combo.grid(row=2, column=1, pady=5, padx=5)
        
        # Senha (para criação)
        ttk.Label(form_frame, text="Senha:").grid(row=3, column=0, sticky='w', pady=5)
        self.senha_var = tk.StringVar()
        self.senha_entry = ttk.Entry(form_frame, textvariable=self.senha_var, 
                                     width=37, show='*')
        self.senha_entry.grid(row=3, column=1, pady=5, padx=5)
        
        # Confirmar senha
        ttk.Label(form_frame, text="Confirmar Senha:").grid(row=4, column=0, sticky='w', pady=5)
        self.confirmar_senha_var = tk.StringVar()
        self.confirmar_senha_entry = ttk.Entry(form_frame, textvariable=self.confirmar_senha_var,
                                               width=37, show='*')
        self.confirmar_senha_entry.grid(row=4, column=1, pady=5, padx=5)
        
        # Status (checkbox)
        self.ativo_var = tk.BooleanVar(value=True)
        self.ativo_check = ttk.Checkbutton(form_frame, text="Usuário Ativo", 
                                           variable=self.ativo_var)
        self.ativo_check.grid(row=5, column=1, sticky='w', pady=10, padx=5)
        
        # === Botões de ação ===
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        self.btn_novo = ttk.Button(btn_frame, text="Novo", command=self._novo_usuario, width=15)
        self.btn_novo.pack(pady=3, fill=tk.X)
        
        self.btn_salvar = ttk.Button(btn_frame, text="Salvar", command=self._salvar_usuario, width=15)
        self.btn_salvar.pack(pady=3, fill=tk.X)
        
        self.btn_resetar_senha = ttk.Button(btn_frame, text="Resetar Senha", 
                                            command=self._resetar_senha, width=15)
        self.btn_resetar_senha.pack(pady=3, fill=tk.X)
        
        self.btn_desativar = ttk.Button(btn_frame, text="Desativar", 
                                        command=self._alternar_status, width=15)
        self.btn_desativar.pack(pady=3, fill=tk.X)
        
        # Botão fechar
        ttk.Button(right_frame, text="Fechar", command=self.window.destroy, width=15).pack(
            side=tk.BOTTOM, pady=10)
        
        # Carregar funcionários
        self._carregar_funcionarios()
        
    def _carregar_funcionarios(self):
        """Carrega lista de funcionários para o combobox."""
        try:
            funcionarios = []
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT f.id, f.nome 
                    FROM funcionarios f
                    ORDER BY f.nome
                """)
                funcionarios = cursor.fetchall()
            
            self.funcionarios_dict = {}
            valores = []
            for func in funcionarios:
                if isinstance(func, dict):
                    fid, nome = func['id'], func['nome']
                else:
                    fid, nome = func
                display = f"{nome} (ID: {fid})"
                self.funcionarios_dict[display] = fid
                valores.append(display)
            
            self.funcionario_combo['values'] = valores
            
        except Exception as e:
            logger.exception(f"Erro ao carregar funcionários: {e}")
            self.funcionarios_dict = {}
            self.funcionario_combo['values'] = []
    
    def _carregar_usuarios(self):
        """Carrega lista de usuários do banco de dados."""
        try:
            # Limpar treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.id, u.username, f.nome, u.perfil, u.ativo
                    FROM usuarios u
                    LEFT JOIN funcionarios f ON u.funcionario_id = f.id
                    ORDER BY f.nome
                """)
                usuarios = cursor.fetchall()
            
            self.usuarios_cache = []
            for user in usuarios:
                if isinstance(user, dict):
                    uid = user['id']
                    username = user['username']
                    nome = user['nome'] or 'N/A'
                    perfil = user['perfil']
                    ativo = user['ativo']
                else:
                    uid, username, nome, perfil, ativo = user
                    nome = nome or 'N/A'
                
                status = '✓ Ativo' if ativo else '✗ Inativo'
                perfil_display = perfil.capitalize() if perfil else 'N/A'
                
                self.tree.insert('', tk.END, values=(uid, username, nome, perfil_display, status))
                self.usuarios_cache.append({
                    'id': uid, 'username': username, 'nome': nome,
                    'perfil': perfil, 'ativo': ativo
                })
                
        except Exception as e:
            logger.exception(f"Erro ao carregar usuários: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar usuários: {e}")
    
    def _filtrar_usuarios(self, *args):
        """Filtra usuários na treeview com base no texto de busca."""
        termo = self.search_var.get().lower()
        
        # Limpar e recarregar com filtro
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for user in self.usuarios_cache:
            if (termo in user['username'].lower() or 
                termo in (user['nome'] or '').lower() or
                termo in (user['perfil'] or '').lower()):
                
                status = '✓ Ativo' if user['ativo'] else '✗ Inativo'
                perfil_display = user['perfil'].capitalize() if user['perfil'] else 'N/A'
                self.tree.insert('', tk.END, values=(
                    user['id'], user['username'], user['nome'], perfil_display, status
                ))
    
    def _on_usuario_selecionado(self, event):
        """Callback quando um usuário é selecionado na treeview."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        
        if not values:
            return
        
        user_id = values[0]
        
        # Buscar dados completos do usuário
        try:
            with get_cursor() as cursor:
                cursor.execute("""
                    SELECT u.id, u.username, u.funcionario_id, u.perfil, u.ativo, f.nome
                    FROM usuarios u
                    LEFT JOIN funcionarios f ON u.funcionario_id = f.id
                    WHERE u.id = %s
                """, (user_id,))
                user = cursor.fetchone()
            
            if user:
                if isinstance(user, dict):
                    self.usuario_selecionado = user
                    self.username_var.set(user['username'])
                    self.ativo_var.set(bool(user['ativo']))
                    
                    # Selecionar perfil
                    for codigo, nome in self.PERFIS:
                        if codigo == user['perfil']:
                            self.perfil_var.set(nome)
                            break
                    
                    # Selecionar funcionário
                    if user['funcionario_id']:
                        for display, fid in self.funcionarios_dict.items():
                            if fid == user['funcionario_id']:
                                self.funcionario_var.set(display)
                                break
                else:
                    uid, username, func_id, perfil, ativo, nome = user
                    self.usuario_selecionado = {
                        'id': uid, 'username': username, 
                        'funcionario_id': func_id, 'perfil': perfil, 'ativo': ativo
                    }
                    self.username_var.set(username)
                    self.ativo_var.set(bool(ativo))
                    
                    for codigo, nome_p in self.PERFIS:
                        if codigo == perfil:
                            self.perfil_var.set(nome_p)
                            break
                    
                    if func_id:
                        for display, fid in self.funcionarios_dict.items():
                            if fid == func_id:
                                self.funcionario_var.set(display)
                                break
                
                # Limpar campos de senha
                self.senha_var.set('')
                self.confirmar_senha_var.set('')
                
                # Atualizar texto do botão desativar
                if self.usuario_selecionado['ativo']:
                    self.btn_desativar.config(text='Desativar')
                else:
                    self.btn_desativar.config(text='Ativar')
                    
        except Exception as e:
            logger.exception(f"Erro ao carregar dados do usuário: {e}")
    
    def _novo_usuario(self):
        """Limpa o formulário para criar um novo usuário."""
        self.usuario_selecionado = None
        self.funcionario_var.set('')
        self.username_var.set('')
        self.perfil_var.set('')
        self.senha_var.set('')
        self.confirmar_senha_var.set('')
        self.ativo_var.set(True)
        self.btn_desativar.config(text='Desativar')
        
        # Limpar seleção na treeview
        for item in self.tree.selection():
            self.tree.selection_remove(item)
        
        # Focar no campo de funcionário
        self.funcionario_combo.focus_set()
    
    def _salvar_usuario(self):
        """Salva o usuário (cria novo ou atualiza existente)."""
        # Validações
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Atenção", "Informe o nome de usuário.")
            return
        
        perfil_nome = self.perfil_var.get()
        if not perfil_nome:
            messagebox.showwarning("Atenção", "Selecione um perfil.")
            return
        
        # Converter nome do perfil para código
        perfil = None
        for codigo, nome in self.PERFIS:
            if nome == perfil_nome:
                perfil = codigo
                break
        
        if not perfil:
            messagebox.showwarning("Atenção", "Perfil inválido.")
            return
        
        # Obter funcionário ID
        funcionario_display = self.funcionario_var.get()
        funcionario_id = self.funcionarios_dict.get(funcionario_display) if funcionario_display else None
        
        # Se é novo usuário, exige senha
        if not self.usuario_selecionado:
            senha = self.senha_var.get()
            confirmar = self.confirmar_senha_var.get()
            
            if not senha:
                messagebox.showwarning("Atenção", "Informe a senha.")
                return
            
            if senha != confirmar:
                messagebox.showwarning("Atenção", "As senhas não conferem.")
                return
            
            if len(senha) < 6:
                messagebox.showwarning("Atenção", "A senha deve ter pelo menos 6 caracteres.")
                return
            
            # Criar novo usuário
            self._criar_usuario(username, senha, perfil, funcionario_id)
        else:
            # Atualizar usuário existente
            self._atualizar_usuario(username, perfil, funcionario_id)
    
    def _criar_usuario(self, username: str, senha: str, perfil: str, funcionario_id: Optional[int]):
        """Cria um novo usuário no banco de dados."""
        try:
            # Verificar se username já existe
            with get_cursor() as cursor:
                cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
                if cursor.fetchone():
                    messagebox.showwarning("Atenção", f"O usuário '{username}' já existe.")
                    return
            
            # Hash da senha
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usuarios (username, senha_hash, perfil, funcionario_id, ativo)
                    VALUES (%s, %s, %s, %s, 1)
                """, (username, senha_hash, perfil, funcionario_id))
                conn.commit()
                
            logger.info(f"Usuário '{username}' criado com sucesso")
            messagebox.showinfo("Sucesso", f"Usuário '{username}' criado com sucesso!")
            
            # Registrar log
            self._registrar_log('criar_usuario', f"Criado usuário: {username} ({perfil})")
            
            # Recarregar lista
            self._carregar_usuarios()
            self._novo_usuario()
            
        except Exception as e:
            logger.exception(f"Erro ao criar usuário: {e}")
            messagebox.showerror("Erro", f"Erro ao criar usuário: {e}")
    
    def _atualizar_usuario(self, username: str, perfil: str, funcionario_id: Optional[int]):
        """Atualiza um usuário existente."""
        if not self.usuario_selecionado:
            return
        
        try:
            user_id = self.usuario_selecionado['id']
            
            # Verificar se username já existe (em outro usuário)
            with get_cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM usuarios WHERE username = %s AND id != %s", 
                    (username, user_id)
                )
                if cursor.fetchone():
                    messagebox.showwarning("Atenção", f"O usuário '{username}' já existe.")
                    return
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE usuarios 
                    SET username = %s, perfil = %s, funcionario_id = %s
                    WHERE id = %s
                """, (username, perfil, funcionario_id, user_id))
                conn.commit()
            
            logger.info(f"Usuário '{username}' (ID: {user_id}) atualizado")
            messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!")
            
            # Registrar log
            self._registrar_log('atualizar_usuario', f"Atualizado usuário: {username} ({perfil})")
            
            # Recarregar lista
            self._carregar_usuarios()
            
        except Exception as e:
            logger.exception(f"Erro ao atualizar usuário: {e}")
            messagebox.showerror("Erro", f"Erro ao atualizar usuário: {e}")
    
    def _resetar_senha(self):
        """Reseta a senha do usuário selecionado."""
        if not self.usuario_selecionado:
            messagebox.showwarning("Atenção", "Selecione um usuário.")
            return
        
        # Usar senha informada ou gerar uma aleatória
        nova_senha = self.senha_var.get()
        confirmar = self.confirmar_senha_var.get()
        
        if nova_senha:
            if nova_senha != confirmar:
                messagebox.showwarning("Atenção", "As senhas não conferem.")
                return
            if len(nova_senha) < 6:
                messagebox.showwarning("Atenção", "A senha deve ter pelo menos 6 caracteres.")
                return
        else:
            # Gerar senha aleatória
            nova_senha = secrets.token_urlsafe(8)
        
        username = self.usuario_selecionado['username']
        
        if not messagebox.askyesno("Confirmar", 
                                   f"Deseja resetar a senha do usuário '{username}'?"):
            return
        
        try:
            user_id = self.usuario_selecionado['id']
            senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET senha_hash = %s WHERE id = %s",
                    (senha_hash, user_id)
                )
                conn.commit()
            
            logger.info(f"Senha do usuário '{username}' resetada")
            
            # Registrar log
            self._registrar_log('resetar_senha', f"Senha resetada para: {username}")
            
            # Se gerou senha aleatória, mostrar
            if not self.senha_var.get():
                messagebox.showinfo("Sucesso", 
                                   f"Senha resetada com sucesso!\n\nNova senha: {nova_senha}\n\n"
                                   "Anote esta senha, ela não será mostrada novamente.")
            else:
                messagebox.showinfo("Sucesso", "Senha resetada com sucesso!")
            
            # Limpar campos de senha
            self.senha_var.set('')
            self.confirmar_senha_var.set('')
            
        except Exception as e:
            logger.exception(f"Erro ao resetar senha: {e}")
            messagebox.showerror("Erro", f"Erro ao resetar senha: {e}")
    
    def _alternar_status(self):
        """Ativa ou desativa o usuário selecionado."""
        if not self.usuario_selecionado:
            messagebox.showwarning("Atenção", "Selecione um usuário.")
            return
        
        username = self.usuario_selecionado['username']
        ativo_atual = self.usuario_selecionado['ativo']
        nova_acao = 'desativar' if ativo_atual else 'ativar'
        novo_status = 0 if ativo_atual else 1
        
        if not messagebox.askyesno("Confirmar", 
                                   f"Deseja {nova_acao} o usuário '{username}'?"):
            return
        
        try:
            user_id = self.usuario_selecionado['id']
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET ativo = %s WHERE id = %s",
                    (novo_status, user_id)
                )
                conn.commit()
            
            logger.info(f"Usuário '{username}' {'ativado' if novo_status else 'desativado'}")
            messagebox.showinfo("Sucesso", f"Usuário {'ativado' if novo_status else 'desativado'} com sucesso!")
            
            # Registrar log
            self._registrar_log(f'{nova_acao}_usuario', f"{nova_acao.capitalize()}do usuário: {username}")
            
            # Recarregar lista
            self._carregar_usuarios()
            self._novo_usuario()
            
        except Exception as e:
            logger.exception(f"Erro ao {nova_acao} usuário: {e}")
            messagebox.showerror("Erro", f"Erro ao {nova_acao} usuário: {e}")
    
    def _registrar_log(self, acao: str, detalhes: str):
        """Registra uma ação no log de acesso."""
        try:
            # Obter usuário logado e seu ID
            usuario = UsuarioLogado.get_usuario()
            if not usuario:
                return
            usuario_atual = usuario.id
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO logs_acesso (usuario_id, acao, detalhes)
                    VALUES (%s, %s, %s)
                """, (usuario_atual, acao, detalhes))
                conn.commit()
                
        except Exception as e:
            # Não propagar erro de log
            logger.warning(f"Erro ao registrar log de acesso: {e}")


def abrir_gestao_usuarios(parent):
    """Função de conveniência para abrir a janela de gestão de usuários."""
    return GestaoUsuariosWindow(parent)
