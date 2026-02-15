"""
Módulo de interfaces estendidas.
Contém interfaces complexas para declarações, crachás e importação.
Extraído do main.py (Sprint 15 Fase 2).
"""

from tkinter import (Toplevel, Frame, Label, Entry, Button, Listbox, Scrollbar, 
                     messagebox, StringVar, END, BOTH, X, W)
from tkinter import ttk
from tkcalendar import DateEntry
import os
from src.core.config_logs import get_logger
from db.connection import get_connection
from src.utils.dates import aplicar_mascara_data
from datetime import datetime

logger = get_logger(__name__)


def abrir_interface_declaracao_comparecimento(janela_pai, gerar_declaracao_func):
    """
    Abre interface para selecionar aluno e gerar declaração de comparecimento.
    
    Args:
        janela_pai: Janela principal do Tkinter
        gerar_declaracao_func: Função que gera a declaração (recebe aluno_id, data, motivo, responsavel, turno)
    """
    from src.ui.colors import COLORS
    
    # Ocultar janela principal
    janela_pai.withdraw()
    
    # Criar janela
    janela_decl = Toplevel(janela_pai)
    janela_decl.title("Declaração de Comparecimento de Responsável")
    janela_decl.geometry("600x600")
    janela_decl.configure(bg=COLORS.co1)
    
    # Restaurar janela principal quando fechar
    def ao_fechar():
        janela_decl.destroy()
        janela_pai.deiconify()
    
    janela_decl.protocol("WM_DELETE_WINDOW", ao_fechar)
    janela_decl.focus_force()
    
    frame_principal = Frame(janela_decl, bg=COLORS.co1, padx=20, pady=20)
    frame_principal.pack(fill='both', expand=True)
    
    # Título
    Label(frame_principal, text="Gerar Declaração de Comparecimento", 
          font=("Arial", 14, "bold"), bg=COLORS.co1, fg=COLORS.co0).pack(pady=(0, 15))
    
    # Frame de pesquisa
    frame_pesquisa = Frame(frame_principal, bg=COLORS.co1)
    frame_pesquisa.pack(fill='x', pady=(0, 10))
    
    Label(frame_pesquisa, text="Pesquisar Aluno:", bg=COLORS.co1, fg=COLORS.co0, 
          font=("Arial", 11)).pack(anchor='w', pady=(0, 5))
    
    pesquisa_entry = Entry(frame_pesquisa, width=50, font=("Arial", 11))
    pesquisa_entry.pack(fill='x', pady=(0, 5))
    
    # Frame para lista de alunos
    frame_lista = Frame(frame_principal, bg=COLORS.co1)
    frame_lista.pack(fill='both', expand=True, pady=(0, 10))
    
    Label(frame_lista, text="Selecione o Aluno:", bg=COLORS.co1, fg=COLORS.co0, 
          font=("Arial", 11)).pack(anchor='w', pady=(0, 5))
    
    # Listbox com scrollbar
    scrollbar = Scrollbar(frame_lista)
    scrollbar.pack(side='right', fill='y')
    
    listbox_alunos = Listbox(frame_lista, font=("Arial", 10), 
                            yscrollcommand=scrollbar.set, height=10)
    listbox_alunos.pack(fill='both', expand=True)
    scrollbar.config(command=listbox_alunos.yview)
    
    # Dicionário para mapear índice -> ID do aluno
    alunos_dict = {}
    
    # Variável para armazenar o aluno selecionado
    aluno_selecionado_id = {'id': None}
    
    # Função para carregar alunos
    def carregar_alunos(filtro=""):
        listbox_alunos.delete(0, END)
        alunos_dict.clear()

        try:
            with get_connection() as conn:
                if conn is None:
                    messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                    return
                cursor = conn.cursor()
                try:
                    from src.core.config import ANO_LETIVO_ATUAL
                    
                    # Obter ano letivo configurado e verificar se ainda está ativo
                    cursor.execute("SELECT id, data_fim FROM anosletivos WHERE ano_letivo = %s", (ANO_LETIVO_ATUAL,))
                    ano_atual = cursor.fetchone()

                    ano_letivo_id = None
                    if ano_atual:
                        ano_id = ano_atual[0]
                        data_fim = ano_atual[1]
                        
                        # Se não tem data_fim OU ainda não passou, usa este ano
                        if data_fim is None:
                            ano_letivo_id = ano_id
                        else:
                            cursor.execute("SELECT CURDATE() <= %s as ainda_ativo", (data_fim,))
                            ainda_ativo = cursor.fetchone()
                            if ainda_ativo and ainda_ativo[0]:
                                ano_letivo_id = ano_id

                    # Se o ano configurado já encerrou, busca o próximo ativo
                    if ano_letivo_id is None:
                        cursor.execute("""
                            SELECT id FROM anosletivos 
                            WHERE CURDATE() BETWEEN data_inicio AND data_fim
                            ORDER BY ano_letivo DESC 
                            LIMIT 1
                        """)
                        ano_atual = cursor.fetchone()
                        if ano_atual:
                            ano_letivo_id = ano_atual[0]

                    # Fallback final: ano mais recente
                    if ano_letivo_id is None:
                        cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                        ano_atual = cursor.fetchone()
                        ano_letivo_id = ano_atual[0] if ano_atual else 1
                    else:
                        ano_letivo_id = ano_letivo_id if ano_letivo_id else 1

                    if filtro:
                        query = """
                            SELECT DISTINCT a.id, a.nome, s.nome as serie, t.nome as turma
                            FROM alunos a
                            INNER JOIN matriculas m ON a.id = m.aluno_id
                            INNER JOIN turmas t ON m.turma_id = t.id
                            INNER JOIN series s ON t.serie_id = s.id
                            WHERE a.escola_id = 60 
                            AND m.ano_letivo_id = %s
                            AND m.status IN ('Ativo', 'Transferido')
                            AND a.nome LIKE %s
                            ORDER BY a.nome
                        """
                        cursor.execute(query, (int(str(ano_letivo_id)) if ano_letivo_id is not None else 1, f"%{filtro}%"))
                    else:
                        query = """
                            SELECT DISTINCT a.id, a.nome, s.nome as serie, t.nome as turma
                            FROM alunos a
                            INNER JOIN matriculas m ON a.id = m.aluno_id
                            INNER JOIN turmas t ON m.turma_id = t.id
                            INNER JOIN series s ON t.serie_id = s.id
                            WHERE a.escola_id = 60 
                            AND m.ano_letivo_id = %s
                            AND m.status IN ('Ativo', 'Transferido')
                            ORDER BY a.nome
                        """
                        cursor.execute(query, (int(str(ano_letivo_id)) if ano_letivo_id is not None else 1,))

                    resultados = cursor.fetchall()

                    for idx, (aluno_id, nome, serie, turma) in enumerate(resultados):
                        info_adicional = ""
                        if serie:
                            info_adicional = f" - {serie}"
                            if turma:
                                info_adicional += f" {turma}"

                        texto = f"{nome}{info_adicional}"
                        listbox_alunos.insert(END, texto)
                        alunos_dict[idx] = aluno_id
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar alunos: {str(e)}")
    
    # Carregar alunos inicialmente
    carregar_alunos()
    
    # Vincular pesquisa
    def pesquisar(event=None):
        filtro = pesquisa_entry.get()
        carregar_alunos(filtro)
    
    pesquisa_entry.bind("<KeyRelease>", pesquisar)
    
    # Frame para parâmetros
    frame_params = Frame(frame_principal, bg=COLORS.co1)
    frame_params.pack(fill='x', pady=(10, 0))
    
    # Label para mostrar aluno selecionado
    Label(frame_params, text="Aluno Selecionado:", bg=COLORS.co1, fg=COLORS.co0, 
          font=("Arial", 11, "bold")).grid(row=0, column=0, sticky='w', pady=5, columnspan=2)
    
    aluno_selecionado_label = Label(frame_params, text="Nenhum aluno selecionado", 
                                   bg=COLORS.co1, fg=COLORS.co2, font=("Arial", 10))
    aluno_selecionado_label.grid(row=1, column=0, sticky='w', pady=5, columnspan=2)
    
    # Seleção de Responsável
    Label(frame_params, text="Responsável:", bg=COLORS.co1, fg=COLORS.co0, 
          font=("Arial", 11)).grid(row=2, column=0, sticky='w', pady=5)
    
    responsavel_var = StringVar()
    combo_responsavel = ttk.Combobox(frame_params, textvariable=responsavel_var, 
                                    width=30, state='readonly')
    combo_responsavel.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=5)
    
    # Turno
    Label(frame_params, text="Turno da Reunião:", bg=COLORS.co1, fg=COLORS.co0, 
          font=("Arial", 11)).grid(row=3, column=0, sticky='w', pady=5)
    
    turno_var = StringVar(value="Matutino")
    combo_turno = ttk.Combobox(frame_params, textvariable=turno_var, 
                               width=15, state='readonly',
                               values=["Matutino", "Vespertino"])
    combo_turno.grid(row=3, column=1, sticky='w', padx=(10, 0), pady=5)
    
    Label(frame_params, text="Data do Comparecimento (DD/MM/AAAA):", bg=COLORS.co1, fg=COLORS.co0, 
          font=("Arial", 11)).grid(row=4, column=0, sticky='w', pady=5)
    
    data_var = StringVar(value=datetime.now().strftime('%d/%m/%Y'))
    data_entry = Entry(frame_params, textvariable=data_var, width=22, font=("Arial", 11))
    data_entry.grid(row=4, column=1, sticky='w', padx=(10, 0), pady=5)
    aplicar_mascara_data(data_entry)
    
    Label(frame_params, text="Motivo:", bg=COLORS.co1, fg=COLORS.co0, 
          font=("Arial", 11)).grid(row=5, column=0, sticky='w', pady=5)
    
    motivo_entry = Entry(frame_params, width=30, font=("Arial", 11))
    motivo_entry.insert(0, "reunião escolar")
    motivo_entry.grid(row=5, column=1, sticky='w', padx=(10, 0), pady=5)
    
    # Função para carregar responsáveis quando um aluno for selecionado
    def on_aluno_select(event):
        selecao = listbox_alunos.curselection()
        if not selecao:
            return
        
        idx = selecao[0]
        aluno_id = alunos_dict.get(idx)
        
        # Salvar o ID do aluno selecionado
        aluno_selecionado_id['id'] = aluno_id
        
        # Mostrar nome do aluno selecionado
        nome_aluno = listbox_alunos.get(idx)
        aluno_selecionado_label.config(text=f"✓ {nome_aluno}", fg=COLORS.co2)
        
        if aluno_id:
            try:
                with get_connection() as conn:
                    if conn is None:
                        logger.error("Erro: Não foi possível conectar ao banco de dados.")
                        return
                    cursor = conn.cursor()
                    try:
                        # Buscar responsáveis do aluno
                        query = """
                            SELECT DISTINCT 
                                r.nome,
                                r.cpf
                            FROM responsaveis r
                            INNER JOIN responsaveisalunos ra ON r.id = ra.responsavel_id
                            WHERE ra.aluno_id = %s
                        """
                        cursor.execute(query, (aluno_id,))
                        resultados = cursor.fetchall()

                        responsaveis = []
                        # Adicionar todos os responsáveis encontrados
                        for row in resultados:
                            if row and row[0]:
                                responsaveis.append(row[0])
                    finally:
                        try:
                            cursor.close()
                        except Exception:
                            pass

                # Atualizar combobox
                if responsaveis:
                    combo_responsavel['values'] = responsaveis
                    combo_responsavel.set(responsaveis[0])
                else:
                    combo_responsavel['values'] = ["Responsável não cadastrado"]
                    combo_responsavel.set("Responsável não cadastrado")
            except Exception as e:
                logger.error(f"Erro ao carregar responsáveis: {str(e)}")
    
    # Vincular evento de seleção
    listbox_alunos.bind("<<ListboxSelect>>", on_aluno_select)
    
    # Função para gerar
    def gerar():
        # Usar o ID do aluno salvo em vez da seleção da listbox
        aluno_id = aluno_selecionado_id['id']
        
        if not aluno_id:
            messagebox.showwarning("Aviso", "Por favor, selecione um aluno.")
            return
        
        responsavel_selecionado = responsavel_var.get()
        if not responsavel_selecionado or responsavel_selecionado == "Responsável não cadastrado":
            messagebox.showwarning("Aviso", "Por favor, selecione um responsável válido.")
            return
        
        turno_selecionado = turno_var.get()
        if not turno_selecionado:
            messagebox.showwarning("Aviso", "Por favor, selecione o turno da reunião.")
            return
        
        # Converter data de DD/MM/AAAA para objeto date
        data_str = data_var.get().strip()
        try:
            data_selecionada = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Erro", "Data inválida! Use o formato DD/MM/AAAA.")
            return
            
        motivo = motivo_entry.get()
        
        # Passar os novos parâmetros para a função
        gerar_declaracao_func(
            aluno_id, data_selecionada, motivo, 
            responsavel_selecionado, turno_selecionado
        )
        
        # Fechar interface e restaurar janela principal
        janela_decl.destroy()
        janela_pai.deiconify()
    
    # Botões
    frame_botoes = Frame(frame_principal, bg=COLORS.co1)
    frame_botoes.pack(fill='x', pady=(15, 0))
    
    Button(frame_botoes, text="Gerar Declaração", command=gerar, 
           bg=COLORS.co2, fg=COLORS.co0, font=("Arial", 11, "bold"), 
           width=18).pack(side='left', padx=5)
    
    Button(frame_botoes, text="Cancelar", command=janela_decl.destroy,
           bg=COLORS.co4, fg=COLORS.co0, font=("Arial", 11), 
           width=12).pack(side='right', padx=5)


def abrir_interface_crachas(janela_pai):
    """
    Abre interface para gerar crachás de alunos e responsáveis.
    Executa geração em background para não bloquear a UI.
    
    Args:
        janela_pai: Janela principal do Tkinter
    """
    from tkinter.ttk import Progressbar
    from src.ui.colors import COLORS
    
    resposta = messagebox.askyesno(
        "Gerar Crachás",
        "Deseja gerar crachás para todos os alunos ativos?\n\n"
        "Os crachás serão salvos na pasta 'assets/crachas', "
        "organizados por série e turma."
    )

    if not resposta:
        return

    # Ocultar janela principal temporariamente
    janela_pai.withdraw()

    # Criar janela de progresso (UI deve ser criada no thread principal)
    janela_progresso = Toplevel(janela_pai)
    janela_progresso.title("Gerando Crachás")
    janela_progresso.geometry("400x150")
    janela_progresso.resizable(False, False)
    janela_progresso.configure(bg=COLORS.co1)

    # Centralizar na tela
    janela_progresso.update_idletasks()
    x = (janela_progresso.winfo_screenwidth() // 2) - (400 // 2)
    y = (janela_progresso.winfo_screenheight() // 2) - (150 // 2)
    janela_progresso.geometry(f"400x150+{x}+{y}")

    frame_prog = Frame(janela_progresso, bg=COLORS.co1, padx=20, pady=20)
    frame_prog.pack(fill=BOTH, expand=True)

    Label(frame_prog, text="Gerando crachás...", font=("Arial", 12, "bold"), 
          bg=COLORS.co1, fg=COLORS.co0).pack(pady=10)
    Label(frame_prog, text="Aguarde, isso pode levar alguns minutos.", font=("Arial", 10), 
          bg=COLORS.co1, fg=COLORS.co0).pack(pady=5)

    progresso = Progressbar(frame_prog, mode='indeterminate', length=300)
    progresso.pack(pady=10)
    try:
        progresso.start(10)
    except Exception:
        pass

    janela_progresso.update()

    # Trabalho pesado em background
    def _worker():
        try:
            # Usar o serviço centralizado para gerar crachás
            from src.services.report_service import gerar_crachas_para_todos_os_alunos as service_gerar
            caminho = service_gerar()
            return caminho
        except Exception as e:
            raise e

    # Callback de sucesso - executado na thread principal
    def _on_done(caminho):
        try:
            progresso.stop()
        except Exception:
            pass
        try:
            janela_progresso.destroy()
        except Exception:
            pass
        # Restaurar janela principal
        try:
            janela_pai.deiconify()
        except Exception:
            pass

        # Sucesso: avisar e abrir pasta
        from src.core.config import PROJECT_ROOT
        caminho_crachas = caminho or str(PROJECT_ROOT / 'assets' / 'crachas')
        messagebox.showinfo(
            "Sucesso",
            f"Crachás gerados com sucesso!\n\n"
            f"Os arquivos foram salvos em:\n{caminho_crachas}\n\n"
            f"A pasta será aberta automaticamente."
        )

        try:
            import subprocess
            import platform
            if platform.system() == 'Windows':
                os.startfile(caminho_crachas)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', caminho_crachas])
            else:
                subprocess.Popen(['xdg-open', caminho_crachas])
        except Exception:
            # Problema ao abrir a pasta não é crítico
            logger.warning(f"Não foi possível abrir a pasta dos crachás: {caminho_crachas}")

    # Callback de erro - executado na thread principal
    def _on_error(exc):
        try:
            progresso.stop()
        except Exception:
            pass
        try:
            janela_progresso.destroy()
        except Exception:
            pass
        # Restaurar janela principal
        try:
            janela_pai.deiconify()
        except Exception:
            pass
        
        if isinstance(exc, ImportError):
            messagebox.showerror("Erro de Importação", 
                                f"Não foi possível importar o módulo de geração de crachás:\n{exc}")
        else:
            messagebox.showerror("Erro", f"Erro ao gerar crachás:\n{exc}")

    try:
        from src.utils.executor import submit_background
        submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=janela_pai)
    except Exception:
        from threading import Thread
        Thread(target=_worker, daemon=True).start()


def abrir_importacao_notas_html(janela_pai):
    """
    Abre interface para importar notas de arquivo HTML do GEDUC.
    
    Args:
        janela_pai: Janela principal do Tkinter
    """
    try:
        # Ocultar janela principal
        janela_pai.withdraw()
        
        # Importar e executar o módulo de importação
        from src.importadores.notas_html import interface_importacao
        
        # Passa a referência da janela principal
        interface_importacao(janela_pai=janela_pai)
        
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir importação de notas: {e}")
        janela_pai.deiconify()
