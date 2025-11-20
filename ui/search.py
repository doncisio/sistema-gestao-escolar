"""
Módulo de pesquisa para o sistema de gestão escolar.

Extração da função pesquisar() do main.py (Sprint 15).
"""

from tkinter import messagebox
from db.connection import get_connection
from config_logs import get_logger

logger = get_logger(__name__)


def pesquisar_alunos_funcionarios(
    texto_pesquisa: str,
    treeview,
    tabela_frame,
    frame_tabela,
    criar_tabela_func,
    criar_dashboard_func
):
    """
    Pesquisa alunos e funcionários no banco de dados.
    
    Args:
        texto_pesquisa: Texto a ser pesquisado
        treeview: Widget Treeview onde os resultados serão exibidos
        tabela_frame: Frame que contém a tabela
        frame_tabela: Frame pai da tabela
        criar_tabela_func: Função para criar/recriar a tabela
        criar_dashboard_func: Função para mostrar o dashboard
    
    Returns:
        bool: True se a pesquisa foi bem-sucedida
    """
    texto_pesquisa = texto_pesquisa.strip()

    # Garantir que os componentes da tabela existam
    try:
        if treeview is None or not hasattr(treeview, 'winfo_exists') or not treeview.winfo_exists():
            criar_tabela_func()
    except Exception as e:
        logger.exception(f"Erro ao inicializar componentes da tabela: {e}")
        messagebox.showerror("Erro", f"Erro ao preparar a interface de pesquisa: {e}")
        return False

    if not texto_pesquisa:  # Se a busca estiver vazia, mostrar dashboard
        # Ocultar tabela se estiver visível
        try:
            if tabela_frame.winfo_ismapped():
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
        # Remover tudo em frame_tabela e recriar a tabela limpa
        for widget in list(frame_tabela.winfo_children()):
            try:
                widget.destroy()
            except Exception:
                pass

        # Recriar a tabela
        criar_tabela_func()

        # Remover widgets extras (como dashboard)
        for widget in list(frame_tabela.winfo_children()):
            if widget is not tabela_frame:
                try:
                    widget.destroy()
                except Exception:
                    pass

        # Mostrar tabela_frame
        try:
            if not tabela_frame.winfo_ismapped():
                tabela_frame.pack(fill='both', expand=True, padx=5, pady=5)
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"Falha ao preparar área da tabela: {e}")
        messagebox.showerror("Erro", f"Falha ao preparar área da tabela: {e}")
        return False

    # Limpar o Treeview
    try:
        for item in treeview.get_children():
            treeview.delete(item)
    except Exception:
        pass
    
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
                    query_fulltext = """
                        SELECT 'Aluno' as tipo, a.id, a.nome, a.cpf, a.data_nascimento,
                               CONCAT(s.nome_serie, ' - ', t.nome_turma) as info_extra
                        FROM alunos a
                        LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.ativo = TRUE
                        LEFT JOIN turmas t ON m.turma_id = t.id
                        LEFT JOIN series s ON t.serie_id = s.id
                        WHERE MATCH(a.nome, a.nome_mae) AGAINST(%s IN NATURAL LANGUAGE MODE)
                        UNION
                        SELECT 'Funcionário' as tipo, f.id, f.nome, f.cpf, NULL as data_nascimento,
                               f.funcao as info_extra
                        FROM funcionarios f
                        WHERE MATCH(f.nome) AGAINST(%s IN NATURAL LANGUAGE MODE)
                        ORDER BY tipo, nome
                        LIMIT 100
                    """
                    cursor.execute(query_fulltext, (texto_pesquisa, texto_pesquisa))
                    resultados_filtrados = cursor.fetchall()
                    
                except Exception:
                    # Se FULLTEXT falhar, usar LIKE tradicional
                    logger.debug("FULLTEXT não disponível, usando LIKE")
                    query_like = """
                        SELECT 'Aluno' as tipo, a.id, a.nome, a.cpf, a.data_nascimento,
                               CONCAT(COALESCE(s.nome_serie, ''), ' - ', COALESCE(t.nome_turma, '')) as info_extra
                        FROM alunos a
                        LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.ativo = TRUE
                        LEFT JOIN turmas t ON m.turma_id = t.id
                        LEFT JOIN series s ON t.serie_id = s.id
                        WHERE a.nome LIKE %s OR a.nome_mae LIKE %s
                        UNION
                        SELECT 'Funcionário' as tipo, f.id, f.nome, f.cpf, NULL as data_nascimento,
                               f.funcao as info_extra
                        FROM funcionarios f
                        WHERE f.nome LIKE %s
                        ORDER BY tipo, nome
                        LIMIT 100
                    """
                    termo_like = f"%{texto_pesquisa}%"
                    cursor.execute(query_like, (termo_like, termo_like, termo_like))
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
            # Formatar data de nascimento se existir
            data_nasc = resultado[4]
            if data_nasc:
                try:
                    data_nasc = data_nasc.strftime('%d/%m/%Y') if hasattr(data_nasc, 'strftime') else str(data_nasc)
                except:
                    data_nasc = str(data_nasc)
            else:
                data_nasc = ''
            
            # Inserir no treeview
            valores = (
                resultado[0],  # tipo
                resultado[1],  # id
                resultado[2],  # nome
                resultado[3] or '',  # cpf
                data_nasc,     # data_nascimento
                resultado[5] or ''  # info_extra (série-turma ou função)
            )
            treeview.insert("", "end", values=valores)
        
        logger.info(f"Pesquisa realizada: {len(resultados_filtrados)} resultados para '{texto_pesquisa}'")
        return True
        
    except Exception as e:
        logger.exception(f"Erro ao exibir resultados: {e}")
        messagebox.showerror("Erro", f"Erro ao exibir resultados: {e}")
        return False
