"""
Módulo de pesquisa para o sistema de gestão escolar.

Extração da função pesquisar() do main.py (Sprint 15).
"""

from tkinter import messagebox
from datetime import datetime, date
from db.connection import get_connection
from config_logs import get_logger

logger = get_logger(__name__)


def pesquisar_alunos_funcionarios(
    texto_pesquisa: str,
    get_treeview_func,
    get_tabela_frame_func,
    frame_tabela,
    criar_tabela_func,
    criar_dashboard_func
):
    """
    Pesquisa alunos e funcionários no banco de dados.
    
    Args:
        texto_pesquisa: Texto a ser pesquisado
        get_treeview_func: Função que retorna o widget Treeview atual
        get_tabela_frame_func: Função que retorna o frame da tabela atual
        frame_tabela: Frame pai da tabela
        criar_tabela_func: Função para criar/recriar a tabela
        criar_dashboard_func: Função para mostrar o dashboard
    
    Returns:
        bool: True se a pesquisa foi bem-sucedida
    """
    texto_pesquisa = texto_pesquisa.strip()
    
    # Obter referências atuais
    treeview = get_treeview_func()
    tabela_frame = get_tabela_frame_func()

    # Garantir que os componentes da tabela existam
    try:
        if treeview is None or not hasattr(treeview, 'winfo_exists') or not treeview.winfo_exists():
            criar_tabela_func()
            # Obter novas referências após recriar
            treeview = get_treeview_func()
            tabela_frame = get_tabela_frame_func()
    except Exception as e:
        logger.exception(f"Erro ao inicializar componentes da tabela: {e}")
        messagebox.showerror("Erro", f"Erro ao preparar a interface de pesquisa: {e}")
        return False

    if not texto_pesquisa:  # Se a busca estiver vazia, mostrar dashboard
        # Ocultar tabela se estiver visível
        try:
            if tabela_frame and tabela_frame.winfo_ismapped():
                tabela_frame.pack_forget()
        except Exception:
            pass

        # Limpar frame_tabela e mostrar dashboard
        try:
            for widget in list(frame_tabela.winfo_children()):
                if widget != tabela_frame:
                    try:
                        widget.destroy()
                    except Exception:
                        pass
        except Exception:
            pass

        criar_dashboard_func()
        return True

    # Há texto de pesquisa: preparar tabela
    try:
        # Remover dashboard se estiver visível
        for widget in list(frame_tabela.winfo_children()):
            if widget is not tabela_frame:
                try:
                    widget.destroy()
                except Exception:
                    pass

        # Garantir que tabela_frame está visível
        if tabela_frame and not tabela_frame.winfo_ismapped():
            tabela_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Verificar se treeview precisa ser recriado
        if treeview is None or not treeview.winfo_exists():
            # Recriar a tabela se o treeview não existe mais
            criar_tabela_func()
            # Obter nova referência ao treeview
            treeview = get_treeview_func()
            if treeview is None:
                logger.error("Falha ao obter treeview após recriar tabela")
                return False
        
    except Exception as e:
        logger.exception(f"Falha ao preparar área da tabela: {e}")
        messagebox.showerror("Erro", f"Falha ao preparar área da tabela: {e}")
        return False

    # Limpar o Treeview
    try:
        for item in treeview.get_children():
            treeview.delete(item)
    except Exception as e:
        logger.exception(f"Erro ao limpar treeview: {e}")
        # Se não conseguir limpar, tentar recriar
        try:
            criar_tabela_func()
            treeview = get_treeview_func()
            if treeview is None:
                logger.error("Falha ao recriar treeview após erro na limpeza")
                return False
            # Tentar limpar novamente
            for item in treeview.get_children():
                treeview.delete(item)
        except Exception as e2:
            logger.exception(f"Falha ao recriar treeview: {e2}")
            return False
    
    # Buscar no banco de dados
    resultados_filtrados = []
    try:
        with get_connection() as conn:
            if conn is None:
                raise Exception("Falha ao conectar ao banco de dados")
            cursor = conn.cursor()
            try:
                # Tentar usar FULLTEXT primeiro (mais rápido)
                try:
                    # Query otimizada com FULLTEXT - ESTRUTURA CORRIGIDA
                    query_fulltext = """
                    SELECT 
                        f.id AS id,
                        f.nome AS nome,
                        'Funcionário' AS tipo,
                        f.funcao AS cargo,
                        f.data_nascimento AS data_nascimento
                    FROM 
                        funcionarios f
                    WHERE 
                        MATCH(f.nome) AGAINST(%s IN NATURAL LANGUAGE MODE)
                    UNION ALL
                    SELECT
                        a.id AS id,
                        a.nome AS nome,
                        'Aluno' AS tipo,
                        NULL AS cargo,
                        a.data_nascimento AS data_nascimento
                    FROM
                        alunos a
                    WHERE 
                        MATCH(a.nome) AGAINST(%s IN NATURAL LANGUAGE MODE)
                    ORDER BY 
                        tipo, nome
                    """
                    cursor.execute(query_fulltext, (texto_pesquisa, texto_pesquisa))
                    resultados_filtrados = cursor.fetchall()
                    
                except Exception:
                    # Se FULLTEXT falhar, usar LIKE tradicional
                    logger.debug("FULLTEXT não disponível, usando LIKE")
                    query_like = """
                    SELECT 
                        f.id AS id,
                        f.nome AS nome,
                        'Funcionário' AS tipo,
                        f.funcao AS cargo,
                        f.data_nascimento AS data_nascimento
                    FROM 
                        funcionarios f
                    WHERE 
                        f.nome LIKE %s
                    UNION ALL
                    SELECT
                        a.id AS id,
                        a.nome AS nome,
                        'Aluno' AS tipo,
                        NULL AS cargo,
                        a.data_nascimento AS data_nascimento
                    FROM
                        alunos a
                    WHERE 
                        a.nome LIKE %s
                    ORDER BY 
                        tipo, nome
                    LIMIT 100
                    """
                    termo_like = f"%{texto_pesquisa}%"
                    cursor.execute(query_like, (termo_like, termo_like))
                    resultados_filtrados = cursor.fetchall()
                
                cursor.close()
                
            except Exception as e:
                logger.exception(f"Erro na query de pesquisa: {e}")
                raise
                
    except Exception as e:
        logger.exception(f"Erro ao pesquisar no banco: {e}")
        messagebox.showerror("Erro", f"Erro ao realizar a pesquisa: {e}")
        return False

    # Exibir resultados no Treeview
    if not resultados_filtrados:
        messagebox.showinfo("Pesquisa", f"Nenhum resultado encontrado para '{texto_pesquisa}'")
        return True

    try:
        for resultado in resultados_filtrados:
            # Normalizar resultado para lista
            if isinstance(resultado, dict):
                resultado = list(resultado.values())
            elif isinstance(resultado, (list, tuple)):
                resultado = list(resultado)
            else:
                resultado = [resultado]
            
            # Formatar data de nascimento se existir (índice 4)
            if len(resultado) > 4 and resultado[4]:
                try:
                    if isinstance(resultado[4], str):
                        data = datetime.strptime(resultado[4], '%Y-%m-%d')
                    elif isinstance(resultado[4], (datetime, date)):
                        data = resultado[4]
                    else:
                        data = None
                    
                    if data:
                        resultado[4] = data.strftime('%d/%m/%Y')
                except Exception:
                    pass
            
            # Inserir no treeview - estrutura: (id, nome, tipo, cargo, data_nascimento)
            treeview.insert("", "end", values=resultado)
        
        logger.info(f"Pesquisa realizada: {len(resultados_filtrados)} resultados para '{texto_pesquisa}'")
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao exibir resultados: {e}")
        messagebox.showerror("Erro", f"Erro ao exibir resultados: {e}")
        return False
