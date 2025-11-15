from tkinter import ttk, filedialog, messagebox, Frame, Label, LabelFrame, Button, StringVar, BOTH, X, LEFT, RIGHT, VERTICAL, HORIZONTAL, NSEW, NS, EW, BOTTOM, RAISED, RIDGE, END, Y
import tkinter as tk
import os
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from typing import Any, cast
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import mimetypes
from dotenv import load_dotenv
import webbrowser

class GerenciadorDocumentosSistema:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Documentos do Sistema")
        self.root.geometry("1200x700")
        
        # Definição das cores (mesmas da tela principal)
        self.co0 = "#F5F5F5"  # Branco suave para o fundo
        self.co1 = "#003A70"  # Azul escuro
        self.co2 = "#77B341"  # Verde
        self.co3 = "#E2418E"  # Rosa/Magenta
        self.co4 = "#4A86E8"  # Azul mais claro
        self.co5 = "#F26A25"  # Laranja
        self.co6 = "#F7B731"  # Amarelo
        self.co7 = "#333333"  # Cinza escuro
        self.co8 = "#BF3036"  # Vermelho
        self.co9 = "#6FA8DC"  # Azul claro
        
        # Configurar cores da janela
        self.root.configure(bg=self.co1)
        
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Configurações do Google Drive
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.service = None
        self.setup_google_drive()
        self.setup_database()
        
        self.create_widgets()
        self.carregar_documentos()
    
    def setup_google_drive(self):
        """Configura a autenticação com o Google Drive"""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
    
    def conectar_bd(self):
        """Conecta ao banco de dados usando variáveis de ambiente"""
        try:
            conn = mysql.connector.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                auth_plugin='mysql_native_password'
            )
            if conn.is_connected():
                return conn
        except Error as e:
            messagebox.showerror(
                "Erro de Conexão", 
                f"Erro ao conectar com o banco de dados: {e}"
            )
            return None
    
    def setup_database(self):
        """Configura a conexão com o banco de dados"""
        self.conn = self.conectar_bd()
        if self.conn:
            self.cursor = self.conn.cursor()
        else:
            self.root.destroy()
    
    def create_widgets(self):
        """Cria os elementos da interface"""
        # Frame principal
        main_frame = Frame(self.root, bg=self.co1, padx=10, pady=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Título
        title_frame = Frame(main_frame, bg=self.co1)
        title_frame.pack(fill=X, pady=(0, 20))
        
        Label(title_frame, text="Gerenciador de Documentos do Sistema", 
              font=('Ivy', 16, 'bold'), bg=self.co1, fg=self.co0).pack()
        
        # Frame de filtros
        filter_frame = LabelFrame(main_frame, text="Filtros", padx=10, pady=10,
                                bg=self.co1, fg=self.co0, font=('Ivy', 10, 'bold'))
        filter_frame.pack(fill=X, pady=(0, 10))
        
        # Grid de filtros - Linha 0
        Label(filter_frame, text="Tipo:", bg=self.co1, fg=self.co0,
              font=('Ivy', 10)).grid(row=0, column=0, padx=5, pady=5)
        
        self.tipo_var = StringVar()
        self.tipo_combo = ttk.Combobox(filter_frame, textvariable=self.tipo_var, 
                                     width=30, font=('Ivy', 10))
        self.tipo_combo['values'] = (
            'Todos', 'Declaração', 'Boletim', 'Histórico Escolar', 
            'Lista Atualizada', 'Ata', 'Transferência', 'Outros'
        )
        self.tipo_combo.grid(row=0, column=1, padx=5, pady=5)
        self.tipo_combo.set('Todos')
        
        Label(filter_frame, text="Data:", bg=self.co1, fg=self.co0,
              font=('Ivy', 10)).grid(row=0, column=2, padx=5, pady=5)
        
        self.data_var = StringVar()
        self.data_combo = ttk.Combobox(filter_frame, textvariable=self.data_var,
                                     width=20, font=('Ivy', 10))
        self.data_combo['values'] = (
            'Todos', 'Hoje', 'Últimos 7 dias', 'Último mês', 'Este ano'
        )
        self.data_combo.grid(row=0, column=3, padx=5, pady=5)
        self.data_combo.set('Todos')
        
        # Grid de filtros - Linha 1
        Label(filter_frame, text="Nome:", bg=self.co1, fg=self.co0,
              font=('Ivy', 10)).grid(row=1, column=0, padx=5, pady=5)
        
        self.nome_var = StringVar()
        self.nome_entry = ttk.Entry(filter_frame, textvariable=self.nome_var,
                                    width=32, font=('Ivy', 10))
        self.nome_entry.grid(row=1, column=1, padx=5, pady=5)
        
        Button(filter_frame, text="Filtrar", command=self.carregar_documentos,
               font=('Ivy', 10), bg=self.co4, fg=self.co0,
               relief=RAISED, overrelief=RIDGE).grid(row=1, column=2, padx=5, pady=5)
        
        # Frame da tabela
        table_frame = Frame(main_frame, bg=self.co1)
        table_frame.pack(fill=BOTH, expand=True)
        
        # Configurar estilo da Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview",
                      background=self.co0,
                      foreground=self.co7,
                      fieldbackground=self.co0,
                      font=('Ivy', 10))
        style.configure("Custom.Treeview.Heading",
                      background=self.co1,
                      foreground=self.co0,
                      font=('Ivy', 10, 'bold'))
        
        # Criar Treeview
        columns = ('ID', 'Tipo', 'Nome Arquivo', 'Data Upload', 'Finalidade', 'Descrição', 'Aluno/Funcionário')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                style="Custom.Treeview", height=15)
        
        # Configurar colunas
        self.tree.heading('ID', text='ID')
        self.tree.heading('Tipo', text='Tipo')
        self.tree.heading('Nome Arquivo', text='Nome do Arquivo')
        self.tree.heading('Data Upload', text='Data de Upload')
        self.tree.heading('Finalidade', text='Finalidade')
        self.tree.heading('Descrição', text='Descrição')
        self.tree.heading('Aluno/Funcionário', text='Aluno/Funcionário')
        
        self.tree.column('ID', width=50)
        self.tree.column('Tipo', width=150)
        self.tree.column('Nome Arquivo', width=250)
        self.tree.column('Data Upload', width=150)
        self.tree.column('Finalidade', width=150)
        self.tree.column('Descrição', width=250)
        self.tree.column('Aluno/Funcionário', width=200)
        
        # Scrollbars
        yscroll = ttk.Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        # Layout da tabela e scrollbars
        self.tree.grid(row=0, column=0, sticky=NSEW)
        yscroll.grid(row=0, column=1, sticky=NS)
        xscroll.grid(row=1, column=0, sticky=EW)
        
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)
        
        # Frame de botões (sempre visível na parte inferior)
        button_frame = Frame(main_frame, bg=self.co1)
        button_frame.pack(fill=X, pady=(10, 0), side=BOTTOM)
        
        Button(button_frame, text="Abrir Documento", command=self.abrir_documento,
               font=('Ivy', 10, 'bold'), bg=self.co2, fg=self.co0, width=18,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        
        Button(button_frame, text="Excluir Documento", command=self.excluir_documento,
               font=('Ivy', 10, 'bold'), bg=self.co8, fg=self.co0, width=18,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        
        Button(button_frame, text="Atualizar Lista", command=self.carregar_documentos,
               font=('Ivy', 10, 'bold'), bg=self.co4, fg=self.co0, width=18,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        
        Button(button_frame, text="Relatório Duplicados", command=self.mostrar_relatorio_duplicados,
               font=('Ivy', 10, 'bold'), bg=self.co6, fg=self.co7, width=18,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        
        Button(button_frame, text="Limpar Duplicados", command=self.limpar_duplicados,
               font=('Ivy', 10, 'bold'), bg=self.co5, fg=self.co0, width=18,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
    
    def carregar_documentos(self):
        """Carrega os documentos com base nos filtros selecionados"""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Erro", "Sem conexão com o banco de dados.")
            return
        
        try:
            # Limpar tabela
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Construir a query base
            query = """
                SELECT 
                    d.id, 
                    d.tipo_documento, 
                    d.nome_arquivo, 
                    d.data_de_upload, 
                    d.finalidade, 
                    d.descricao,
                    COALESCE(a.nome, '') as nome_aluno,
                    COALESCE(f.nome, '') as nome_funcionario
                FROM documentos_emitidos d
                LEFT JOIN alunos a ON d.aluno_id = a.id
                LEFT JOIN funcionarios f ON d.funcionario_id = f.id
                WHERE 1=1
            """
            params = []
            
            # Adicionar filtro de tipo
            if self.tipo_var.get() != 'Todos':
                query += " AND tipo_documento = %s"
                params.append(self.tipo_var.get())
            
            # Adicionar filtro de data
            data_filtro = self.data_var.get()
            if data_filtro != 'Todos':
                if data_filtro == 'Hoje':
                    query += " AND DATE(data_de_upload) = CURDATE()"
                elif data_filtro == 'Últimos 7 dias':
                    query += " AND data_de_upload >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
                elif data_filtro == 'Último mês':
                    query += " AND data_de_upload >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
                elif data_filtro == 'Este ano':
                    query += " AND YEAR(data_de_upload) = YEAR(CURDATE())"
            
            # Adicionar filtro de nome (Aluno ou Funcionário)
            nome_filtro = self.nome_var.get().strip()
            if nome_filtro:
                query += " AND (a.nome LIKE %s OR f.nome LIKE %s)"
                params.append(f"%{nome_filtro}%")
                params.append(f"%{nome_filtro}%")
            
            query += " ORDER BY data_de_upload DESC"
            
            # Executar a query
            self.cursor.execute(query, params)
            documentos = self.cursor.fetchall()
            
            # Preencher a tabela
            for doc in documentos:
                id_doc, tipo, nome, data, finalidade, descricao, nome_aluno, nome_funcionario = doc
                # Formatar a data com proteções de tipo (datetime / timestamp / outros)
                if data is None:
                    data_str = ''
                elif isinstance(data, datetime):
                    data_str = data.strftime('%d/%m/%Y %H:%M')
                elif isinstance(data, (int, float)):
                    try:
                        data_str = datetime.fromtimestamp(float(data)).strftime('%d/%m/%Y %H:%M')
                    except Exception:
                        data_str = str(data)
                else:
                    try:
                        data_str = str(data)
                    except Exception:
                        data_str = ''
                # Definir pessoa relacionada
                pessoa = nome_aluno if nome_aluno else nome_funcionario
                self.tree.insert('', 'end', values=(
                    id_doc, tipo, nome, data_str,
                    finalidade if finalidade else '',
                    descricao if descricao else '',
                    pessoa if pessoa else ''
                ))
            
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Erro ao carregar documentos: {e}")
    
    def abrir_documento(self):
        """Abre o documento selecionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Por favor, selecione um documento.")
            return
        
        try:
            item = self.tree.item(selected[0])
            doc_id = item['values'][0]
            
            # Buscar link do documento
            self.cursor.execute(
                "SELECT link_no_drive FROM documentos_emitidos WHERE id = %s",
                (doc_id,)
            )
            resultado = self.cursor.fetchone()
            
            if resultado and resultado[0]:
                webbrowser.open(str(resultado[0]))
            else:
                messagebox.showwarning(
                    "Aviso", 
                    "Link do documento não encontrado no Google Drive."
                )
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir documento: {e}")
    
    def excluir_documento(self):
        """Exclui o documento selecionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Por favor, selecione um documento.")
            return
        
        try:
            item = self.tree.item(selected[0])
            doc_id = item['values'][0]
            nome_arquivo = item['values'][2]
            
            # Confirmar exclusão
            if not messagebox.askyesno(
                "Confirmar Exclusão",
                f"Tem certeza que deseja excluir o documento '{nome_arquivo}'?"
            ):
                return
            
            # Buscar link do Drive
            self.cursor.execute(
                "SELECT link_no_drive FROM documentos_emitidos WHERE id = %s",
                (doc_id,)
            )
            resultado = self.cursor.fetchone()
            
            if resultado and resultado[0]:
                # Extrair ID do arquivo do Drive do link com proteção de tipo
                link = resultado[0]
                link_str = ''
                try:
                    link_str = str(link)
                except Exception:
                    link_str = ''

                drive_id = None
                if '/d/' in link_str:
                    parts = link_str.split('/d/')
                    if len(parts) > 1:
                        drive_id = parts[1].split('/')[0]
                elif 'id=' in link_str:
                    parts = link_str.split('id=')
                    if len(parts) > 1:
                        drive_id = parts[1].split('&')[0]
                elif link_str:
                    # Fallback: pegar último segmento plausível
                    parts = link_str.strip('/').split('/')
                    if parts:
                        drive_id = parts[-1]

                # Tentar excluir do Drive (se possível)
                if drive_id:
                    try:
                        if not self.service:
                            print(f"Erro: serviço do Drive não configurado; não foi possível excluir {drive_id}")
                        else:
                            self.service.files().delete(fileId=drive_id).execute()
                    except Exception as e:
                        print(f"Erro ao excluir do Drive: {e}")
            
            # Excluir do banco de dados
            self.cursor.execute(
                "DELETE FROM documentos_emitidos WHERE id = %s",
                (doc_id,)
            )
            if getattr(self, 'conn', None):
                cast(Any, self.conn).commit()
            
            # Atualizar a tabela
            self.carregar_documentos()
            
            messagebox.showinfo(
                "Sucesso",
                f"Documento '{nome_arquivo}' excluído com sucesso!"
            )
            
        except Exception as e:
            if getattr(self, 'conn', None):
                cast(Any, self.conn).rollback()
            messagebox.showerror("Erro", f"Erro ao excluir documento: {e}")
    
    def identificar_duplicados(self):
        """Identifica documentos duplicados no banco de dados"""
        if not self.conn or not self.conn.is_connected():
            messagebox.showerror("Erro", "Sem conexão com o banco de dados.")
            return []
        
        try:
            # Buscar documentos agrupados por tipo, aluno/funcionário e finalidade
            # Considera duplicados aqueles com mesmas características mas datas diferentes
            query = """
                SELECT 
                    tipo_documento,
                    aluno_id,
                    funcionario_id,
                    finalidade,
                    COUNT(*) as total,
                    GROUP_CONCAT(id ORDER BY data_de_upload DESC) as ids,
                    GROUP_CONCAT(data_de_upload ORDER BY data_de_upload DESC) as datas
                FROM documentos_emitidos
                GROUP BY tipo_documento, aluno_id, funcionario_id, finalidade
                HAVING COUNT(*) > 1
                ORDER BY total DESC, tipo_documento
            """
            
            self.cursor.execute(query)
            duplicados = self.cursor.fetchall()
            
            return duplicados
            
        except mysql.connector.Error as e:
            messagebox.showerror("Erro", f"Erro ao identificar duplicados: {e}")
            return []
    
    def limpar_duplicados(self):
        """Remove documentos duplicados, mantendo apenas o mais recente"""
        if not messagebox.askyesno(
            "Confirmar Limpeza",
            "Esta ação irá identificar documentos duplicados e manter apenas a versão mais recente de cada um.\n\n"
            "Os documentos antigos serão excluídos do banco de dados e do Google Drive.\n\n"
            "Deseja continuar?"
        ):
            return
        
        duplicados = self.identificar_duplicados()
        
        if not duplicados:
            messagebox.showinfo("Limpeza de Duplicados", "Nenhum documento duplicado foi encontrado!")
            return
        
        # Criar janela de progresso
        progresso_window = tk.Toplevel(self.root)
        progresso_window.title("Limpeza de Duplicados")
        progresso_window.geometry("600x400")
        progresso_window.configure(bg=self.co1)
        
        Label(progresso_window, text="Removendo documentos duplicados...", 
              font=('Ivy', 12, 'bold'), bg=self.co1, fg=self.co0).pack(pady=10)
        
        # Text widget para mostrar progresso
        text_widget = tk.Text(progresso_window, height=15, width=70, 
                             font=('Consolas', 9), bg=self.co0, fg=self.co7)
        text_widget.pack(padx=10, pady=10, fill=BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_widget, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        total_removidos = 0
        total_grupos = len(duplicados)
        
        try:
            for idx, dup in enumerate(duplicados, 1):
                tipo, aluno_id, func_id, finalidade, total, ids_str, datas_str = dup
                
                # Garantir que ids_str seja string antes de split
                ids = []
                try:
                    ids = [int(x) for x in str(ids_str).split(',') if x.strip()]
                except Exception:
                    ids = []
                # Manter o primeiro ID (mais recente) e remover os outros
                ids_para_remover = ids[1:]
                
                pessoa = f"Aluno ID: {aluno_id}" if aluno_id else f"Funcionário ID: {func_id}" if func_id else "Sem vínculo"
                
                text_widget.insert(tk.END, f"\n[{idx}/{total_grupos}] {tipo} - {pessoa}\n", "titulo")
                text_widget.insert(tk.END, f"  Total de versões: {total}\n")
                text_widget.insert(tk.END, f"  Mantendo versão mais recente (ID: {ids[0]})\n", "sucesso")
                text_widget.insert(tk.END, f"  Removendo {len(ids_para_remover)} versão(ões) antiga(s)...\n", "aviso")
                
                # Remover versões antigas
                for doc_id in ids_para_remover:
                    try:
                        # Buscar link do Drive
                        self.cursor.execute(
                            "SELECT link_no_drive, nome_arquivo FROM documentos_emitidos WHERE id = %s",
                            (doc_id,)
                        )
                        resultado = self.cursor.fetchone()
                        
                        if resultado and resultado[0]:
                            link = resultado[0]
                            nome = resultado[1]
                            # Extrair file_id com proteção de tipo
                            try:
                                link_str = str(link)
                            except Exception:
                                link_str = ''

                            drive_id = None
                            if '/d/' in link_str:
                                parts = link_str.split('/d/')
                                if len(parts) > 1:
                                    drive_id = parts[1].split('/')[0]
                            elif 'id=' in link_str:
                                parts = link_str.split('id=')
                                if len(parts) > 1:
                                    drive_id = parts[1].split('&')[0]
                            elif link_str:
                                parts = link_str.strip('/').split('/')
                                if parts:
                                    drive_id = parts[-1]

                            try:
                                if drive_id:
                                    if not self.service:
                                        text_widget.insert(tk.END, f"    ⚠ Serviço Drive não configurado; não foi possível remover: {nome}\n", "erro")
                                    else:
                                        self.service.files().delete(fileId=drive_id).execute()
                                        text_widget.insert(tk.END, f"    ✓ Removido do Drive: {nome}\n", "detalhe")
                            except Exception as e:
                                text_widget.insert(tk.END, f"    ⚠ Erro ao remover do Drive: {str(e)[:50]}\n", "erro")
                        
                        # Excluir do banco de dados
                        self.cursor.execute("DELETE FROM documentos_emitidos WHERE id = %s", (doc_id,))
                        total_removidos += 1
                        
                    except Exception as e:
                        text_widget.insert(tk.END, f"    ✗ Erro ao processar ID {doc_id}: {str(e)[:50]}\n", "erro")
                
                # Commit protegido (garantir que conn exista)
                if getattr(self, 'conn', None):
                    cast(Any, self.conn).commit()
                text_widget.see(tk.END)
                progresso_window.update()
            
            # Configurar tags de cores
            text_widget.tag_config("titulo", foreground=self.co1, font=('Consolas', 9, 'bold'))
            text_widget.tag_config("sucesso", foreground=self.co2)
            text_widget.tag_config("aviso", foreground=self.co5)
            text_widget.tag_config("erro", foreground=self.co8)
            text_widget.tag_config("detalhe", foreground=self.co7)
            
            text_widget.insert(tk.END, f"\n{'='*60}\n", "titulo")
            text_widget.insert(tk.END, f"Limpeza concluída!\n", "titulo")
            text_widget.insert(tk.END, f"Total de documentos removidos: {total_removidos}\n", "sucesso")
            text_widget.insert(tk.END, f"Total de grupos processados: {total_grupos}\n", "sucesso")
            text_widget.see(tk.END)
            
            # Botão para fechar
            Button(progresso_window, text="Fechar", command=progresso_window.destroy,
                   font=('Ivy', 10, 'bold'), bg=self.co2, fg=self.co0, width=15,
                   relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(pady=10)
            
            # Atualizar lista de documentos
            self.carregar_documentos()
            
        except Exception as e:
            if getattr(self, 'conn', None):
                cast(Any, self.conn).rollback()
            text_widget.insert(tk.END, f"\n✗ ERRO GERAL: {str(e)}\n", "erro")
            text_widget.see(tk.END)
    
    def mostrar_relatorio_duplicados(self):
        """Mostra relatório de documentos duplicados sem removê-los"""
        duplicados = self.identificar_duplicados()
        
        if not duplicados:
            messagebox.showinfo("Relatório de Duplicados", "Nenhum documento duplicado foi encontrado!")
            return
        
        # Criar janela de relatório
        relatorio_window = tk.Toplevel(self.root)
        relatorio_window.title("Relatório de Documentos Duplicados")
        relatorio_window.geometry("800x600")
        relatorio_window.configure(bg=self.co1)
        
        Label(relatorio_window, text="Documentos Duplicados Encontrados", 
              font=('Ivy', 14, 'bold'), bg=self.co1, fg=self.co0).pack(pady=10)
        
        # Frame para a tabela
        frame_tabela = Frame(relatorio_window, bg=self.co1)
        frame_tabela.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Criar Treeview
        colunas = ('Tipo', 'Pessoa', 'Finalidade', 'Total', 'IDs')
        tree = ttk.Treeview(frame_tabela, columns=colunas, show='headings',
                           style="Custom.Treeview", height=20)
        
        tree.heading('Tipo', text='Tipo Documento')
        tree.heading('Pessoa', text='Aluno/Funcionário')
        tree.heading('Finalidade', text='Finalidade')
        tree.heading('Total', text='Qtd Duplicados')
        tree.heading('IDs', text='IDs no Banco')
        
        tree.column('Tipo', width=150)
        tree.column('Pessoa', width=150)
        tree.column('Finalidade', width=150)
        tree.column('Total', width=100)
        tree.column('IDs', width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame_tabela, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Preencher dados
        total_docs_duplicados = 0
        for dup in duplicados:
            tipo, aluno_id, func_id, finalidade, total, ids_str, datas_str = dup

            pessoa = f"Aluno: {aluno_id}" if aluno_id else f"Func: {func_id}" if func_id else "N/A"
            final = finalidade if finalidade else "N/A"

            tree.insert('', 'end', values=(tipo, pessoa, final, total, ids_str))
            if isinstance(total, int):
                t = total
            elif isinstance(total, float):
                t = int(total)
            elif isinstance(total, str) and total.isdigit():
                t = int(total)
            else:
                try:
                    t = int(str(total))
                except Exception:
                    t = 0
            total_docs_duplicados += max(0, t - 1)
        
        # Frame de informações
        info_frame = Frame(relatorio_window, bg=self.co1)
        info_frame.pack(fill=X, padx=10, pady=10)
        
        Label(info_frame, 
              text=f"Total de grupos duplicados: {len(duplicados)} | Documentos que serão removidos: {total_docs_duplicados}",
              font=('Ivy', 10, 'bold'), bg=self.co1, fg=self.co6).pack()
        
        # Botões
        button_frame = Frame(relatorio_window, bg=self.co1)
        button_frame.pack(pady=10)
        
        Button(button_frame, text="Limpar Duplicados", command=lambda: [relatorio_window.destroy(), self.limpar_duplicados()],
               font=('Ivy', 10, 'bold'), bg=self.co8, fg=self.co0, width=20,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5)
        
        Button(button_frame, text="Fechar", command=relatorio_window.destroy,
               font=('Ivy', 10, 'bold'), bg=self.co4, fg=self.co0, width=20,
               relief=RAISED, overrelief=RIDGE, cursor="hand2").pack(side=LEFT, padx=5)
    
    def __del__(self):
        """Fecha a conexão com o banco ao destruir o objeto"""
        if hasattr(self, 'conn') and self.conn and self.conn.is_connected():
            self.cursor.close()
            self.conn.close()

def main():
    try:
        root = tk.Tk()
        app = GerenciadorDocumentosSistema(root)
        root.mainloop()
    except Exception as e:
        print(f"Erro ao iniciar aplicação: {e}")
        messagebox.showerror("Erro", f"Erro ao iniciar aplicação: {e}")

if __name__ == "__main__":
    main()