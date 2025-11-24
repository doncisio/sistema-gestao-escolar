"""
Manager para gerenciar o frame de detalhes de alunos e funcionários.
Extrai lógica de UI do main.py - Sprint 16 com estrutura do Sprint 15.
"""
import tkinter as tk
from tkinter import Button, Frame, Label, RIDGE, X, W, BOTH, EW, messagebox
from typing import Dict, Optional, Callable, Tuple, Any
from datetime import datetime, date
from config_logs import get_logger
from db.connection import get_connection
from utils.safe import converter_para_int_seguro, _safe_get, _safe_slice

logger = get_logger(__name__)

def obter_ano_letivo_atual() -> int:
    """Retorna o ID do ano letivo atual."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM anosletivos WHERE YEAR(CURDATE()) = ano_letivo")
            resultado = cursor.fetchone()
            
            if not resultado:
                cursor.execute("SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1")
                resultado = cursor.fetchone()
            
            cursor.close()
            
            if resultado:
                return int(str(resultado['id'] if isinstance(resultado, dict) else resultado[0]))
            return 1
    except Exception as e:
        logger.error(f"Erro ao obter ano letivo atual: {e}")
        return 1


def verificar_matricula_ativa(aluno_id: int) -> bool:
    """
    Verifica se o aluno possui matrícula ativa ou transferida na escola com ID 60 no ano letivo atual.
    
    Args:
        aluno_id: ID do aluno a ser verificado
        
    Returns:
        bool: True se o aluno possui matrícula ativa ou transferida
    """
    try:
        aluno_id_int = converter_para_int_seguro(aluno_id)
        if aluno_id_int is None:
            return False
        
        with get_connection() as conn:
            cursor = conn.cursor()
            ano_letivo_id = obter_ano_letivo_atual()
            
            cursor.execute("""
                SELECT m.id 
                FROM matriculas m
                JOIN turmas t ON m.turma_id = t.id
                WHERE m.aluno_id = %s 
                AND m.ano_letivo_id = %s 
                AND t.escola_id = 60
                AND m.status IN ('Ativo', 'Transferido')
            """, (aluno_id_int, ano_letivo_id))
            
            resultado = cursor.fetchone()
            cursor.close()
            return resultado is not None
            
    except Exception as e:
        logger.exception(f"Erro ao verificar matrícula: {e}")
        return False


def verificar_historico_matriculas(aluno_id: int) -> tuple[bool, list]:
    """
    Verifica se o aluno já teve alguma matrícula em qualquer escola e ano letivo.
    
    Args:
        aluno_id: ID do aluno
        
    Returns:
        Tupla (tem_historico, lista_de_tuplas) onde lista contém (ano_letivo, ano_letivo_id)
    """
    try:
        aluno_id_int = converter_para_int_seguro(aluno_id)
        if aluno_id_int is None:
            return False, []
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT al.ano_letivo, al.id
                FROM matriculas m
                JOIN anosletivos al ON m.ano_letivo_id = al.id
                WHERE m.aluno_id = %s
                ORDER BY al.ano_letivo DESC
            """, (aluno_id_int,))
            
            resultados = cursor.fetchall()
            cursor.close()
            
            if resultados:
                # Retornar lista de tuplas (ano_letivo, ano_letivo_id)
                anos_letivos = [(r[0], r[1]) if isinstance(r, tuple) else (r['ano_letivo'], r['id']) for r in resultados]
                return True, anos_letivos
            return False, []
            
    except Exception as e:
        logger.exception(f"Erro ao verificar histórico: {e}")
        return False, []


def exibir_detalhes_item(
    frame_detalhes: Frame,
    tipo: str,
    item_id: int,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """
    Exibe detalhes completos de um item selecionado (estrutura Sprint 15).
    
    Args:
        frame_detalhes: Frame onde exibir os detalhes
        tipo: 'Aluno' ou 'Funcionário'
        item_id: ID do item
        values: Tupla com valores (id, nome, tipo, cargo, data_nascimento)
        colors: Dicionário de cores
    """
    try:
        # Limpar frame
        for widget in frame_detalhes.winfo_children():
            widget.destroy()
        
        # Criar botões de ação primeiro
        criar_botoes_frame_detalhes(frame_detalhes, tipo, values, colors)
        
        # Frame para exibir os detalhes em grid (abaixo dos botões)
        detalhes_info_frame = Frame(frame_detalhes, bg=colors['co1'])
        detalhes_info_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Configurar o grid para 3 colunas
        for i in range(3):
            detalhes_info_frame.grid_columnconfigure(i, weight=1, uniform="col")
        
        if tipo == "Aluno":
            exibir_detalhes_aluno(detalhes_info_frame, item_id, values, colors)
        elif tipo == "Funcionário":
            exibir_detalhes_funcionario(detalhes_info_frame, values, colors)
        
        logger.debug(f"Detalhes exibidos para {tipo} ID={item_id}")
        
    except Exception as e:
        logger.exception(f"Erro ao exibir detalhes: {e}")


def exibir_detalhes_aluno(
    detalhes_info_frame: Frame,
    aluno_id: int,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """Exibe detalhes específicos de um aluno."""
    # Linha 0: ID e Nome
    Label(detalhes_info_frame, text=f"ID: {values[0]}", bg=colors['co1'], fg=colors['co0'], 
          font=('Ivy 10 bold'), anchor=W).grid(row=0, column=0, sticky=EW, padx=5, pady=3)
    Label(detalhes_info_frame, text=f"Nome: {values[1]}", bg=colors['co1'], fg=colors['co0'], 
          font=('Ivy 10 bold'), anchor=W).grid(row=0, column=1, columnspan=2, sticky=EW, padx=5, pady=3)
    
    # Linha 1: Data de Nascimento
    Label(detalhes_info_frame, text=f"Data de Nascimento: {values[4]}", bg=colors['co1'], fg=colors['co0'], 
          font=('Ivy 10'), anchor=W).grid(row=1, column=0, sticky=EW, padx=5, pady=3)
    
    # Buscar informações de matrícula e responsáveis
    cursor = None
    try:
        with get_connection() as conn:
            if conn is None:
                logger.error("Erro: Não foi possível conectar ao banco de dados.")
                return
            cursor = conn.cursor()
            
            ano_letivo_id = obter_ano_letivo_atual()
            
            # CONSULTA OTIMIZADA: Buscar todos os dados de uma vez
            cursor.execute("""
                SELECT 
                    m.status, 
                    m.data_matricula,
                    s.nome as serie_nome,
                    t.nome as turma_nome,
                    t.id as turma_id,
                    (SELECT hm.data_mudanca 
                     FROM historico_matricula hm 
                     WHERE hm.matricula_id = m.id 
                     AND hm.status_novo IN ('Transferido', 'Transferida')
                     ORDER BY hm.data_mudanca DESC 
                     LIMIT 1) as data_transferencia,
                    GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Mãe' THEN r.nome END) as nome_mae,
                    GROUP_CONCAT(DISTINCT CASE WHEN r.grau_parentesco = 'Pai' THEN r.nome END) as nome_pai
                FROM alunos a
                LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = %s AND m.status IN ('Ativo', 'Transferido')
                LEFT JOIN turmas t ON m.turma_id = t.id AND t.escola_id = 60
                LEFT JOIN serie s ON t.serie_id = s.id
                LEFT JOIN responsaveisalunos ra ON a.id = ra.aluno_id
                LEFT JOIN responsaveis r ON ra.responsavel_id = r.id AND r.grau_parentesco IN ('Mãe', 'Pai')
                WHERE a.id = %s
                GROUP BY m.id, m.status, m.data_matricula, s.nome, t.nome, t.id
                ORDER BY m.data_matricula DESC
                LIMIT 1
            """, (ano_letivo_id, converter_para_int_seguro(aluno_id)))
            
            resultado = cursor.fetchone()
            
            # Processar responsáveis
            nome_mae = _safe_get(resultado, 6)
            nome_pai = _safe_get(resultado, 7)
            
            # Exibir nomes dos pais na linha 2
            if nome_mae:
                Label(detalhes_info_frame, text=f"Mãe: {nome_mae}", bg=colors['co1'], fg=colors['co0'], 
                      font=('Ivy 10'), anchor=W).grid(row=2, column=0, columnspan=2, sticky=EW, padx=5, pady=3)
            
            if nome_pai:
                Label(detalhes_info_frame, text=f"Pai: {nome_pai}", bg=colors['co1'], fg=colors['co0'], 
                      font=('Ivy 10'), anchor=W).grid(row=2, column=2, sticky=EW, padx=5, pady=3)
            
            if resultado:
                vals = _safe_slice(resultado, 0, 6)
                if len(vals) < 6:
                    vals = vals + [None] * (6 - len(vals))
                status, data_matricula, serie_nome, turma_nome, turma_id, data_transferencia = vals
                
                if status == 'Ativo' and data_matricula:
                    # Formatar data de matrícula
                    try:
                        if isinstance(data_matricula, str):
                            data_formatada = datetime.strptime(data_matricula, '%Y-%m-%d').strftime('%d/%m/%Y')
                        elif isinstance(data_matricula, (datetime, date)):
                            data_formatada = data_matricula.strftime('%d/%m/%Y')
                        else:
                            data_formatada = str(data_matricula)
                    except Exception:
                        data_formatada = str(data_matricula)
                    
                    Label(detalhes_info_frame, 
                          text=f"Data de Matrícula: {data_formatada}", 
                          bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=1, column=1, sticky=EW, padx=5, pady=3)
                    
                    if serie_nome:
                        Label(detalhes_info_frame, 
                              text=f"Série: {serie_nome}", 
                              bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)

                    # Mostrar um único rótulo "Turma:" que combina série + turma quando apropriado.
                    # Se `nome_turma` estiver vazio ou apenas espaços, exibir apenas a série.
                    try:
                        if serie_nome and isinstance(serie_nome, str):
                            if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                                turma_completa = f"{serie_nome} {turma_nome}".strip()
                            else:
                                turma_completa = serie_nome
                        else:
                            if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                                turma_completa = turma_nome
                            else:
                                turma_completa = f"Turma {turma_id}" if turma_id else "Não definida"
                    except Exception:
                        turma_completa = f"Turma {turma_id}" if turma_id else "Não definida"

                    Label(detalhes_info_frame, 
                          text=f"Turma: {turma_completa}", 
                          bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)
                
                elif status == 'Transferido' and data_transferencia:
                    # Formatar data de transferência
                    try:
                        if isinstance(data_transferencia, str):
                            data_transf_formatada = datetime.strptime(data_transferencia, '%Y-%m-%d').strftime('%d/%m/%Y')
                        elif isinstance(data_transferencia, (datetime, date)):
                            data_transf_formatada = data_transferencia.strftime('%d/%m/%Y')
                        else:
                            data_transf_formatada = str(data_transferencia)
                    except Exception:
                        data_transf_formatada = str(data_transferencia)
                    
                    Label(detalhes_info_frame, 
                          text=f"Data de Transferência: {data_transf_formatada}", 
                          bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=1, column=1, sticky=EW, padx=5, pady=3)
                    
                    if serie_nome:
                        Label(detalhes_info_frame, 
                              text=f"Última Série: {serie_nome}", 
                              bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)
                    
                    if turma_nome and isinstance(turma_nome, str) and turma_nome.strip():
                        Label(detalhes_info_frame, 
                              text=f"Última Turma: {turma_nome}", 
                              bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)
                    else:
                        turma_texto = f"Última Turma: Turma {turma_id}" if turma_id else "Última Turma: Não definida"
                        Label(detalhes_info_frame, 
                              text=turma_texto, 
                              bg=colors['co1'], fg=colors['co0'], font=('Ivy 10'), anchor=W).grid(row=3, column=0, sticky=EW, padx=5, pady=3)
    
    except Exception as e:
        logger.error(f"Erro ao verificar matrícula: {str(e)}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass


def exibir_detalhes_funcionario(
    detalhes_info_frame: Frame,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """Exibe detalhes específicos de um funcionário."""
    # Linha 0: ID e Nome
    Label(detalhes_info_frame, text=f"ID: {values[0]}", bg=colors['co1'], fg=colors['co0'], 
          font=('Ivy 10 bold'), anchor=W).grid(row=0, column=0, sticky=EW, padx=5, pady=3)
    Label(detalhes_info_frame, text=f"Nome: {values[1]}", bg=colors['co1'], fg=colors['co0'], 
          font=('Ivy 10 bold'), anchor=W).grid(row=0, column=1, columnspan=2, sticky=EW, padx=5, pady=3)
    
    # Linha 1: Cargo e Data de Nascimento
    Label(detalhes_info_frame, text=f"Cargo: {values[3]}", bg=colors['co1'], fg=colors['co0'], 
          font=('Ivy 10'), anchor=W).grid(row=1, column=0, columnspan=2, sticky=EW, padx=5, pady=3)
    Label(detalhes_info_frame, text=f"Data de Nascimento: {values[4]}", bg=colors['co1'], fg=colors['co0'], 
          font=('Ivy 10'), anchor=W).grid(row=1, column=2, sticky=EW, padx=5, pady=3)


def criar_botoes_frame_detalhes(
    frame_detalhes: Frame,
    tipo: str,
    values: Tuple[Any, ...],
    colors: Dict[str, str]
) -> None:
    """
    Cria botões de ação no frame de detalhes (estrutura Sprint 15).
    
    Args:
        frame_detalhes: Frame onde criar os botões
        tipo: 'Aluno' ou 'Funcionário'
        values: Tupla com valores do item
        colors: Dicionário de cores
    """
    # Frame para os botões
    acoes_frame = Frame(frame_detalhes, bg=colors['co1'])
    acoes_frame.pack(fill=X, padx=10, pady=10)
    
    # Configurar grid do frame de ações
    for i in range(6):
        acoes_frame.grid_columnconfigure(i, weight=1)
    
    # Obter o ID do item selecionado
    id_item = values[0]
    
    if tipo == "Aluno":
        criar_botoes_aluno(acoes_frame, id_item, colors)
    elif tipo == "Funcionário":
        criar_botoes_funcionario(acoes_frame, id_item, colors)


def criar_menu_boletim(
    parent_frame: Frame,
    aluno_id: int,
    anos_letivos: list,
    colors: Dict[str, str],
    col: int
) -> None:
    """
    Cria um menu suspenso (Combobox) para seleção do ano letivo diretamente na interface.
    
    Args:
        parent_frame: Frame onde o menu será adicionado
        aluno_id: ID do aluno
        anos_letivos: Lista de tuplas (ano_letivo, ano_letivo_id)
        colors: Dicionário de cores
        col: Coluna onde posicionar o combobox
    """
    from tkinter import StringVar, DISABLED, LEFT
    from tkinter import ttk
    
    # Criar frame para conter o label e o combobox
    boletim_frame = Frame(parent_frame, bg=colors['co1'])
    boletim_frame.grid(row=0, column=col, padx=5, pady=5)
    
    # Criar dicionário para mapear anos letivos e status
    anos_info = {}
    
    cursor = None
    try:
        with get_connection() as conn:
            if conn is None:
                messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
                return
            cursor = conn.cursor()
            
            for ano_letivo, ano_letivo_id in anos_letivos:
                # Obter o status da matrícula para este ano letivo
                cursor.execute("""
                    SELECT m.status
                    FROM matriculas m
                    JOIN turmas t ON m.turma_id = t.id
                    WHERE m.aluno_id = %s 
                    AND m.ano_letivo_id = %s 
                    ORDER BY m.data_matricula DESC
                    LIMIT 1
                """, (converter_para_int_seguro(aluno_id), converter_para_int_seguro(ano_letivo_id) or 1))
                
                status_result = cursor.fetchone()
                status = status_result[0] if status_result else "Desconhecido"
                
                # Armazenar informações no dicionário
                anos_info[f"{ano_letivo} - {status}"] = (ano_letivo_id, status)
    
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao obter informações de anos letivos: {str(e)}")
        logger.error(f"Erro ao obter informações de anos letivos: {str(e)}")
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
    
    # Lista de anos para mostrar no combobox
    anos_display = list(anos_info.keys())
    
    if not anos_display:
        # Se não conseguiu obter anos, destruir o frame vazio e mostrar botão desabilitado
        boletim_frame.destroy()
        Button(parent_frame, text="Boletim", state=DISABLED,
               width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co6'], fg=colors['co7']).grid(row=0, column=col, padx=5, pady=5)
        return
    
    # Criar variável para armazenar a seleção
    selected_ano = StringVar()
    
    # Label "Boletim:"
    Label(boletim_frame, text="Boletim:", font=('Ivy 9'), bg=colors['co1'], fg=colors['co0']).pack(side=LEFT, padx=(0, 5))
    
    # Configurar o combobox
    combo_anos = ttk.Combobox(boletim_frame, textvariable=selected_ano, values=anos_display,
                         font=('Ivy 9'), state="readonly", width=15)
    combo_anos.pack(side=LEFT)
    
    # Selecionar o primeiro item por padrão
    if anos_display:
        combo_anos.current(0)
    
    # Função para gerar o boletim quando um ano letivo for selecionado
    def gerar_boletim_selecionado(event=None):
        selected = selected_ano.get()
        if not selected or selected not in anos_info:
            messagebox.showwarning("Aviso", "Por favor, selecione um ano letivo válido.")
            return
        
        ano_letivo_id, status = anos_info[selected]
        
        # Decidir qual tipo de documento gerar com base no status
        # Gerar em background para não bloquear a UI
        def _worker():
            if status == 'Transferido':
                from transferencia import gerar_documento_transferencia
                gerar_documento_transferencia(aluno_id, ano_letivo_id)
                return True
            else:
                import boletim
                return boletim.boletim(aluno_id, ano_letivo_id)
        
        def _on_done(resultado):
            if status == 'Transferido':
                messagebox.showinfo("Aluno Transferido", 
                                  f"O aluno teve status 'Transferido' no ano {selected.split(' - ')[0]}.\n"
                                  f"Documento de transferência gerado com sucesso.")
            else:
                if resultado:
                    messagebox.showinfo("Concluído", "Boletim gerado com sucesso.")
                else:
                    messagebox.showwarning("Aviso", "Nenhum dado gerado para o boletim.")
        
        def _on_error(exc):
            messagebox.showerror("Erro", f"Falha ao gerar documento: {exc}")
        
        try:
            # Tentar usar executor em background
            from utils.executor import submit_background
            import tkinter as tk
            root = tk._default_root
            submit_background(_worker, on_done=_on_done, on_error=_on_error, janela=root)
        except Exception:
            # Fallback: executar em Thread
            def _thread_worker():
                try:
                    res = _worker()
                    try:
                        import tkinter as tk
                        root = tk._default_root
                        if root:
                            root.after(0, lambda: _on_done(res))
                    except Exception:
                        pass
                except Exception as e:
                    try:
                        import tkinter as tk
                        root = tk._default_root
                        if root:
                            root.after(0, lambda: _on_error(e))
                    except Exception:
                        pass
            
            from threading import Thread
            Thread(target=_thread_worker, daemon=True).start()
    
    # Vincular a função ao evento de seleção no combobox
    combo_anos.bind("<<ComboboxSelected>>", gerar_boletim_selecionado)
    
    # Adicionar botão "Gerar" ao lado do combobox
    Button(boletim_frame, text="Gerar", command=gerar_boletim_selecionado,
           font=('Ivy 9'), bg=colors['co6'], fg=colors['co7'], width=5).pack(side=LEFT, padx=(5, 0))


def criar_botoes_aluno(acoes_frame: Frame, aluno_id: int, colors: Dict[str, str]) -> None:
    """Cria botões específicos para aluno."""
    # Verifica se o aluno possui matrícula ativa ou transferida
    tem_matricula_ativa = verificar_matricula_ativa(aluno_id)
    
    # Verifica se o aluno possui histórico de matrículas
    tem_historico, anos_letivos = verificar_historico_matriculas(aluno_id)
    
    # Botões básicos (sempre aparecem)
    Button(acoes_frame, text="Editar", command=lambda: editar_aluno_wrapper(aluno_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co4'], fg=colors['co0']).grid(row=0, column=0, padx=5, pady=5)
    
    Button(acoes_frame, text="Excluir", command=lambda: excluir_aluno_wrapper(aluno_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co8'], fg=colors['co0']).grid(row=0, column=1, padx=5, pady=5)
    
    # Histórico sempre aparece
    Button(acoes_frame, text="Histórico", command=lambda: abrir_historico_wrapper(aluno_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co5'], fg=colors['co0']).grid(row=0, column=2, padx=5, pady=5)
    
    # Botões condicionais
    col = 3
    if tem_matricula_ativa or tem_historico:
        # Criar menu de boletim (combobox inline)
        criar_menu_boletim(acoes_frame, aluno_id, anos_letivos, colors, col)
        col += 1
        
        if tem_matricula_ativa:
            # Declaração
            Button(acoes_frame, text="Declaração", command=lambda: gerar_declaracao_wrapper(aluno_id),
                   width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co2'], fg=colors['co0']).grid(row=0, column=col, padx=5, pady=5)
            col += 1
            
            # Editar Matrícula
            Button(acoes_frame, text="Editar Matrícula", command=lambda: editar_matricula_wrapper(aluno_id),
                   width=12, overrelief=RIDGE, font=('Ivy 9 bold'), bg=colors['co3'], fg=colors['co0']).grid(row=0, column=col, padx=5, pady=5)
        else:
            # Matricular (sem matrícula ativa mas com histórico)
            Button(acoes_frame, text="Matricular", command=lambda: matricular_aluno_wrapper(aluno_id),
                  width=10, overrelief=RIDGE, font=('Ivy 9 bold'), bg=colors['co3'], fg=colors['co0']).grid(row=0, column=col, padx=5, pady=5)
    else:
        # Matricular (sem matrícula e sem histórico)
        Button(acoes_frame, text="Matricular", command=lambda: matricular_aluno_wrapper(aluno_id),
              width=10, overrelief=RIDGE, font=('Ivy 9 bold'), bg=colors['co3'], fg=colors['co0']).grid(row=0, column=col, padx=5, pady=5)


def criar_botoes_funcionario(acoes_frame: Frame, funcionario_id: int, colors: Dict[str, str]) -> None:
    """Cria botões específicos para funcionário."""
    Button(acoes_frame, text="Editar", command=lambda: editar_funcionario_wrapper(funcionario_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co4'], fg=colors['co0']).grid(row=0, column=0, padx=5, pady=5)
    
    Button(acoes_frame, text="Excluir", command=lambda: excluir_funcionario_wrapper(funcionario_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co8'], fg=colors['co0']).grid(row=0, column=1, padx=5, pady=5)
    
    Button(acoes_frame, text="Declaração", command=lambda: gerar_declaracao_funcionario_wrapper(funcionario_id),
           width=10, overrelief=RIDGE, font=('Ivy 9'), bg=colors['co2'], fg=colors['co0']).grid(row=0, column=2, padx=5, pady=5)


# Wrappers para ações (serão implementados no main.py ou conectados via callbacks)
def editar_aluno_wrapper(aluno_id):
    """Wrapper para editar aluno."""
    try:
        from InterfaceEdicaoAluno import InterfaceEdicaoAluno
        import tkinter as tk
        # Obter janela principal (root)
        root = tk._default_root
        if root:
            InterfaceEdicaoAluno(root, aluno_id)
    except Exception as e:
        logger.exception(f"Erro ao abrir edição de aluno: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir edição: {e}")


def excluir_aluno_wrapper(aluno_id):
    """Wrapper para excluir aluno."""
    try:
        import aluno
        resposta = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este aluno?")
        if resposta:
            aluno.deletar_aluno(aluno_id)
            messagebox.showinfo("Sucesso", "Aluno excluído com sucesso!")
    except Exception as e:
        logger.exception(f"Erro ao excluir aluno: {e}")
        messagebox.showerror("Erro", f"Erro ao excluir: {e}")


def abrir_historico_wrapper(aluno_id):
    """Wrapper para abrir histórico do aluno."""
    try:
        from integrar_historico_escolar import abrir_historico_aluno
        import tkinter as tk
        root = tk._default_root
        if root:
            abrir_historico_aluno(aluno_id, root)
    except Exception as e:
        logger.exception(f"Erro ao abrir histórico: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir histórico: {e}")


def boletim_wrapper(aluno_id):
    """Wrapper para abrir boletim do aluno."""
    try:
        # Import do módulo de boletim
        import boletim
        boletim.boletim(aluno_id)
    except Exception as e:
        logger.exception(f"Erro ao abrir boletim: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir boletim: {e}")


def gerar_declaracao_wrapper(aluno_id):
    """Wrapper para gerar declaração do aluno - abre diálogo de seleção."""
    try:
        import tkinter as tk
        from tkinter import StringVar, Toplevel, Label, OptionMenu, Entry, Button, Frame
        from ui.colors import get_colors_dict
        
        colors = get_colors_dict()
        co0 = colors.get('co0', '#2e2d2b')
        co2 = colors.get('co2', '#4fa882')
        co3 = colors.get('co3', '#e06636')
        co7 = colors.get('co7', '#FFFFFF')
        
        root = tk._default_root
        if not root:
            messagebox.showerror("Erro", "Janela principal não encontrada.")
            return
        
        # Criar diálogo para selecionar tipo de declaração
        dialog = Toplevel(root)
        dialog.title("Tipo de Declaração")
        dialog.geometry("380x170")
        dialog.transient(root)
        dialog.focus_force()
        dialog.grab_set()
        dialog.configure(bg=co0)
        
        # Variável para armazenar a opção selecionada
        opcao = StringVar(dialog)
        opcao.set("Transferência")  # Valor padrão
        
        opcoes = ["Transferência", "Bolsa Família", "Trabalho", "Outros"]
        
        Label(dialog, text="Selecione o tipo de declaração:", font=("Ivy", 12), bg=co0, fg=co7).pack(pady=10)
        
        option_menu = OptionMenu(dialog, opcao, *opcoes)
        option_menu.config(bg=co0, fg=co7, font=("Ivy", 11))
        option_menu.pack(pady=5)
        
        # Frame para o campo de motivo (inicialmente oculto)
        motivo_frame = Frame(dialog, bg=co0)
        motivo_frame.pack(pady=5, fill='x', padx=20)
        
        Label(motivo_frame, text="Especifique o motivo:", font=("Ivy", 11), bg=co0, fg=co7).pack(anchor='w')
        motivo_entry = Entry(motivo_frame, width=40, font=("Ivy", 11))
        motivo_entry.pack(fill='x', pady=5)
        
        # Inicialmente oculta o frame de motivo
        motivo_frame.pack_forget()
        
        # Função para atualizar a visibilidade do campo de motivo
        def atualizar_interface(*args):
            if opcao.get() == "Outros":
                motivo_frame.pack(pady=5, fill='x', padx=20)
                dialog.geometry("380x270")
                motivo_entry.focus_set()
            else:
                motivo_frame.pack_forget()
                dialog.geometry("380x170")
        
        # Associar a função ao evento de mudança da opção
        opcao.trace_add("write", atualizar_interface)
        
        def confirmar():
            opcao_selecionada = opcao.get()
            
            # Criar marcações baseado na opção
            marcacoes = [[False, False, False, False]]
            if opcao_selecionada in opcoes:
                index = opcoes.index(opcao_selecionada)
                marcacoes[0][index] = True
            
            # Capturar o motivo se for a opção "Outros"
            motivo_outros_texto = ""
            if opcao_selecionada == "Outros":
                motivo_outros_texto = motivo_entry.get().strip()
                if not motivo_outros_texto:
                    messagebox.showwarning("Aviso", "Por favor, especifique o motivo.")
                    return
            
            dialog.destroy()
            
            # Executar geração em background
            def _worker():
                from Gerar_Declaracao_Aluno import gerar_declaracao_aluno
                return gerar_declaracao_aluno(aluno_id, marcacoes, motivo_outros_texto)
            
            def _on_done(resultado):
                try:
                    messagebox.showinfo("Concluído", "Declaração gerada com sucesso.")
                except Exception:
                    pass
            
            from utils import executor
            executor.submit_background(_worker, _on_done)
        
        # Botões de ação
        btn_frame = Frame(dialog, bg=co0)
        btn_frame.pack(pady=10)
        
        Button(btn_frame, text="Confirmar", command=confirmar, bg=co2, fg=co0, 
               font=("Ivy", 11, "bold"), relief=tk.RAISED, overrelief=tk.RIDGE).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="Cancelar", command=dialog.destroy, bg=co3, fg=co0, 
               font=("Ivy", 11, "bold"), relief=tk.RAISED, overrelief=tk.RIDGE).pack(side=tk.LEFT, padx=5)
        
    except Exception as e:
        logger.exception(f"Erro ao abrir diálogo de declaração: {e}")
        messagebox.showerror("Erro", f"Erro ao gerar declaração: {e}")


def matricular_aluno_wrapper(aluno_id):
    """Wrapper para matricular aluno - abre MatriculaModal."""
    try:
        from ui.matricula_modal import MatriculaModal
        from ui.colors import get_colors_dict
        from db.connection import get_connection
        import tkinter as tk
        
        root = tk._default_root
        
        if not root:
            logger.error("Janela principal não encontrada")
            messagebox.showerror("Erro", "Janela principal não encontrada.")
            return
        
        # Obter nome do aluno
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM alunos WHERE id = %s", (int(str(aluno_id)),))
            resultado_nome = cursor.fetchone()
            cursor.close()
        
        if resultado_nome is None:
            logger.error(f"Aluno {aluno_id} não encontrado")
            messagebox.showerror("Erro", "Aluno não encontrado.")
            return
        
        nome_aluno = resultado_nome[0]
        
        # Callback para atualizar interface após matrícula (Sprint 15)
        def ao_matricular_sucesso():
            try:
                logger.info(f"Aluno {nome_aluno} matriculado com sucesso")
                messagebox.showinfo("Sucesso", f"Aluno {nome_aluno} matriculado com sucesso!")
            except Exception as e:
                logger.exception(f"Erro no callback de sucesso: {e}")
        
        # Criar e mostrar modal de matrícula
        MatriculaModal(
            parent=root,
            aluno_id=aluno_id,
            nome_aluno=nome_aluno,
            colors=get_colors_dict(),
            callback_sucesso=ao_matricular_sucesso
        )
        
    except Exception as e:
        logger.exception(f"ERRO em matricular_aluno_wrapper: {e}")
        messagebox.showerror("Erro", f"Erro ao matricular: {e}")


def editar_matricula_wrapper(aluno_id):
    """Wrapper para editar matrícula do aluno."""
    try:
        from ui.matricula_modal import MatriculaModal
        from ui.colors import get_colors_dict
        import tkinter as tk
        from db.connection import get_connection
        
        root = tk._default_root
        
        if not root:
            logger.error("Janela principal não encontrada")
            messagebox.showerror("Erro", "Janela principal não encontrada.")
            return
        
        # Obter nome do aluno
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM alunos WHERE id = %s", (int(str(aluno_id)),))
            resultado_nome = cursor.fetchone()
            cursor.close()
        
        if resultado_nome is None:
            logger.error(f"Aluno {aluno_id} não encontrado")
            messagebox.showerror("Erro", "Aluno não encontrado.")
            return
        
        nome_aluno = resultado_nome[0]
        
        # Callback para atualizar interface após edição (Sprint 15)
        def ao_editar_sucesso():
            try:
                logger.info(f"Matrícula do aluno {nome_aluno} editada com sucesso")
                messagebox.showinfo("Sucesso", f"Matrícula de {nome_aluno} atualizada com sucesso!")
            except Exception as e:
                logger.exception(f"Erro no callback de sucesso: {e}")
        
        # Criar e mostrar modal de matrícula (funciona para criar e editar)
        MatriculaModal(
            parent=root,
            aluno_id=aluno_id,
            nome_aluno=nome_aluno,
            colors=get_colors_dict(),
            callback_sucesso=ao_editar_sucesso
        )
        
    except Exception as e:
        logger.exception(f"ERRO em editar_matricula_wrapper: {e}")
        messagebox.showerror("Erro", f"Erro ao editar matrícula: {e}")


def editar_funcionario_wrapper(funcionario_id):
    """Wrapper para editar funcionário."""
    try:
        from InterfaceEdicaoFuncionario import InterfaceEdicaoFuncionario
        import tkinter as tk
        root = tk._default_root
        if root:
            InterfaceEdicaoFuncionario(root, funcionario_id)
    except Exception as e:
        logger.exception(f"Erro ao abrir edição de funcionário: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir edição: {e}")


def excluir_funcionario_wrapper(funcionario_id):
    """Wrapper para excluir funcionário."""
    try:
        import Funcionario
        resposta = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este funcionário?")
        if resposta:
            Funcionario.deletar_funcionario(funcionario_id)
            messagebox.showinfo("Sucesso", "Funcionário excluído com sucesso!")
    except Exception as e:
        logger.exception(f"Erro ao excluir funcionário: {e}")
        messagebox.showerror("Erro", f"Erro ao excluir: {e}")


def gerar_declaracao_funcionario_wrapper(funcionario_id):
    """Wrapper para gerar declaração do funcionário."""
    try:
        from Funcionario import gerar_declaracao_funcionario
        gerar_declaracao_funcionario(funcionario_id)
    except Exception as e:
        logger.exception(f"Erro ao gerar declaração: {e}")
        messagebox.showerror("Erro", f"Erro ao gerar declaração: {e}")


class DetalhesManager:
    """Gerencia o frame de detalhes com botões de ação (mantido para compatibilidade)."""
    
    def __init__(
        self,
        frame_detalhes: Frame,
        colors: Dict[str, str],
        callbacks: Dict[str, Callable] = None
    ):
        """Inicializa o gerenciador de detalhes."""
        self.frame = frame_detalhes
        self.colors = colors
        self.callbacks = callbacks or {}
        self.logger = logger
    
    def limpar(self) -> None:
        """Limpa todos os widgets do frame de detalhes."""
        try:
            for widget in self.frame.winfo_children():
                widget.destroy()
            self.logger.debug("Frame de detalhes limpo")
        except Exception as e:
            self.logger.exception("Erro ao limpar frame de detalhes")
