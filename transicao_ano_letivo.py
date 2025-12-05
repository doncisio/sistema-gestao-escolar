"""
Módulo para Transição de Ano Letivo
Autor: Tarcisio Sousa de Almeida
Data: 11/11/2025

Funcionalidades:
- Encerrar matrículas do ano letivo atual (mudar status para "Concluído")
- Criar novas matrículas para o próximo ano letivo
- Excluir alunos com status: Cancelado, Transferido, Evadido
- Manter apenas alunos ativos para a nova matrícula
- Progressão automática de série (1º ano → 2º ano)
- Geração de relatório PDF pós-transição
"""

import mysql.connector
import threading
import json
import time
from tkinter import (Tk, Toplevel, Frame, Label, LabelFrame, Button,
                     BOTH, LEFT, X, W, E, RIDGE, DISABLED, NORMAL)
from tkinter import ttk, messagebox
from conexao import conectar_bd
from db.connection import get_connection, get_cursor
from db.queries_transicao import (
    QueriesTransicao, 
    QUERY_TURMAS_9ANO, 
    QUERY_CRIAR_ANO_LETIVO,
    QUERY_ENCERRAR_MATRICULAS,
    QUERY_CRIAR_MATRICULA
)
from typing import Any, cast
from datetime import datetime
from typing import Dict, List, Optional
from relatorio_pendencias import buscar_pendencias_notas
from config import ESCOLA_ID
from config_logs import get_logger
import traceback

logger = get_logger(__name__)

# Importar cores do tema centralizado
try:
    from ui.theme import (
        CO_BRANCO, CO_AZUL_ESCURO, CO_VERDE, 
        CO_VERMELHO, CO_LARANJA, CO_FUNDO_CLARO
    )
except ImportError:
    # Fallback se o tema não estiver disponível
    CO_BRANCO = "#ffffff"
    CO_AZUL_ESCURO = "#3b5998"
    CO_VERDE = "#4CAF50"
    CO_VERMELHO = "#f44336"
    CO_LARANJA = "#ff9800"
    CO_FUNDO_CLARO = "#f0f0f0"


class InterfaceTransicaoAnoLetivo:
    """Interface para gerenciar a transição de ano letivo.
    
    Suporta modo dry-run para simulação sem alterações no banco.
    Executa operações longas em thread separada para não travar a UI.
    """
    
    def __init__(self, janela_pai, janela_principal, escola_id: int = None):
        self.janela = janela_pai
        self.janela_principal = janela_principal
        self.escola_id = escola_id if escola_id is not None else ESCOLA_ID
        self.janela.title("Transição de Ano Letivo")
        self.janela.geometry("900x700")
        self.janela.resizable(False, False)
        self.janela.configure(bg=CO_FUNDO_CLARO)
        
        logger.info(f"Inicializando transição de ano letivo para escola_id={self.escola_id}")
        
        # Cores do tema centralizado
        self.co0 = CO_BRANCO       # branco
        self.co1 = CO_AZUL_ESCURO  # azul escuro
        self.co2 = CO_VERDE        # verde
        self.co3 = CO_VERMELHO     # vermelho
        self.co4 = CO_LARANJA      # laranja
        
        # Variáveis de estado
        self._executando = False  # Flag para evitar múltiplas execuções
        self._mapa_turmas: Dict[int, Dict] = {}  # Cache do mapeamento de turmas
        
        # Variáveis
        self.ano_atual: Any = None
        self.ano_novo: Any = None
        self.estatisticas: dict = {}
        
        self.criar_interface()
        self.carregar_dados_iniciais()
    
    def criar_interface(self):
        """Cria a interface gráfica"""
        # Frame principal
        main_frame = Frame(self.janela, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Título
        titulo = Label(main_frame, text="🔄 TRANSIÇÃO DE ANO LETIVO",
                      font=("Arial", 18, "bold"), bg="#f0f0f0", fg=self.co1)
        titulo.pack(pady=(0, 20))
        
        # Aviso importante
        aviso_frame = Frame(main_frame, bg=self.co4, relief=RIDGE, bd=2)
        aviso_frame.pack(fill=X, pady=(0, 20))
        
        Label(aviso_frame, text="⚠️ ATENÇÃO: Esta operação é IRREVERSÍVEL!",
              font=("Arial", 12, "bold"), bg=self.co4, fg=self.co0,
              padx=10, pady=5).pack()
        
        lbl_backup = Label(aviso_frame,
                    text="Certifique-se de fazer BACKUP antes de prosseguir.",
                    font=("Arial", 10), bg=self.co4, fg=self.co0,
                    padx=10)
        lbl_backup.pack(pady=(0, 5))
        
        # Frame de informações
        info_frame = LabelFrame(main_frame, text="Informações do Ano Letivo",
                               font=("Arial", 12, "bold"), bg=self.co0,
                               padx=15, pady=15)
        info_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # Ano letivo atual
        ano_frame = Frame(info_frame, bg=self.co0)
        ano_frame.pack(fill=X, pady=5)
        
        Label(ano_frame, text="Ano Letivo Atual:", font=("Arial", 11, "bold"),
              bg=self.co0, width=20, anchor=W).pack(side=LEFT)
        
        self.label_ano_atual = Label(ano_frame, text="Carregando...",
                                     font=("Arial", 11), bg=self.co0, fg=self.co1)
        self.label_ano_atual.pack(side=LEFT, padx=10)
        
        # Novo ano letivo
        novo_ano_frame = Frame(info_frame, bg=self.co0)
        novo_ano_frame.pack(fill=X, pady=5)
        
        Label(novo_ano_frame, text="Novo Ano Letivo:", font=("Arial", 11, "bold"),
              bg=self.co0, width=20, anchor=W).pack(side=LEFT)
        
        self.label_ano_novo = Label(novo_ano_frame, text="",
                                    font=("Arial", 11), bg=self.co0, fg=self.co2)
        self.label_ano_novo.pack(side=LEFT, padx=10)
        
        # Estatísticas
        stats_frame = LabelFrame(main_frame, text="Estatísticas",
                                font=("Arial", 12, "bold"), bg=self.co0,
                                padx=15, pady=15)
        stats_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # Grid de estatísticas
        self.label_total_matriculas = self.criar_label_stat(
            stats_frame, "Total de Matrículas Ativas:", 0)
        
        self.label_alunos_continuar = self.criar_label_stat(
            stats_frame, "Alunos que Continuarão (1º ao 8º ano):", 1, cor=self.co2)
        
        # Aplicar regra de reprovação a TODAS as turmas; atualizar rótulo
        self.label_alunos_9ano_reprovados = self.criar_label_stat(
            stats_frame, "Alunos Reprovados (média < 60):", 2, cor=self.co4)
        
        self.label_alunos_excluir = self.criar_label_stat(
            stats_frame, "Alunos a Excluir (Transferidos/Cancelados/Evadidos):", 3, cor=self.co3)
        
        # Frame de ações
        acoes_frame = Frame(main_frame, bg="#f0f0f0")
        acoes_frame.pack(fill=X, pady=(10, 0))
        
        # Botões
        btn_frame = Frame(acoes_frame, bg="#f0f0f0")
        btn_frame.pack()
        
        self.btn_simular = Button(btn_frame, text="🔍 Simular Transição",
                                  command=self.simular_transicao,
                                  font=("Arial", 11, "bold"),
                                  bg=self.co4, fg=self.co0,
                                  width=20, height=2, cursor="hand2")
        self.btn_simular.pack(side=LEFT, padx=5)
        
        self.btn_executar = Button(btn_frame, text="✅ Executar Transição",
                                   command=self.confirmar_transicao,
                                   font=("Arial", 11, "bold"),
                                   bg=self.co2, fg=self.co0,
                                   width=20, height=2, cursor="hand2",
                                   state=DISABLED)
        self.btn_executar.pack(side=LEFT, padx=5)
        
        Button(btn_frame, text="❌ Cancelar",
               command=self.fechar,
               font=("Arial", 11),
               bg=self.co3, fg=self.co0,
               width=15, height=2, cursor="hand2").pack(side=LEFT, padx=5)
        
        # Barra de progresso
        self.progresso_frame = Frame(main_frame, bg="#f0f0f0")
        self.progresso_frame.pack(fill=X, pady=(10, 0))
        
        self.label_status = Label(self.progresso_frame, text="",
                                 font=("Arial", 10), bg="#f0f0f0")
        self.label_status.pack()
        
        self.progressbar = ttk.Progressbar(self.progresso_frame,
                                          mode='determinate',
                                          length=400)
        # Não mostra a barra inicialmente
    
    def criar_label_stat(self, parent, texto, row, cor="#333333"):
        """Cria um label de estatística"""
        Label(parent, text=texto, font=("Arial", 10),
              bg=self.co0, anchor=W).grid(row=row, column=0, sticky=W, pady=5)
        
        label_valor = Label(parent, text="0", font=("Arial", 10, "bold"),
                           bg=self.co0, fg=cor, anchor=E)
        label_valor.grid(row=row, column=1, sticky=E, padx=10, pady=5)
        
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=0)
        
        return label_valor
    
    def carregar_dados_iniciais(self):
        """Carrega os dados iniciais do banco de forma otimizada.
        
        Busca o ano letivo atual com suas datas (data_inicio, data_fim) em uma única query.
        """
        try:
            from db.connection import get_cursor

            with get_cursor() as cursor:
                # Buscar ano letivo atual com datas - query otimizada
                cursor.execute("""
                    SELECT id, ano_letivo, data_inicio, data_fim
                    FROM anosletivos 
                    WHERE ano_letivo = YEAR(CURDATE())
                """)
                resultado = cast(Any, cursor.fetchone())

                if not resultado:
                    # Buscar o ano mais recente se não encontrar o atual
                    cursor.execute("""
                        SELECT id, ano_letivo, data_inicio, data_fim
                        FROM anosletivos 
                        ORDER BY ano_letivo DESC 
                        LIMIT 1
                    """)
                    resultado = cast(Any, cursor.fetchone())

            if resultado:
                self.ano_atual = resultado
                self.ano_novo = {
                    'ano_letivo': resultado['ano_letivo'] + 1
                }

                self.label_ano_atual.config(text=f"{resultado['ano_letivo']}")
                self.label_ano_novo.config(text=f"{self.ano_novo['ano_letivo']}")
                
                # Log das datas do ano letivo
                data_fim = resultado.get('data_fim')
                if data_fim:
                    logger.info(f"Ano letivo {resultado['ano_letivo']}: término em {data_fim}")
                else:
                    logger.warning(f"Ano letivo {resultado['ano_letivo']}: data_fim não definida, usando 31/12")

                # Carregar estatísticas
                with get_cursor() as cur_stats:
                    self.carregar_estatisticas(cur_stats)
            else:
                messagebox.showerror("Erro", "Nenhum ano letivo encontrado no sistema.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
            logger.exception(f"Erro ao carregar dados iniciais: {e}")
    
    def carregar_estatisticas(self, cursor):
        """Carrega estatísticas das matrículas"""
        try:
            # Total de matrículas ativas no ano atual
            # Alinhar com o cálculo do dashboard: contar ALUNOS distintos (a.id)
            # que possuem matrícula com status 'Ativo' no ano letivo atual
            cursor.execute("""
                SELECT COUNT(DISTINCT a.id) as total
                FROM Alunos a
                JOIN Matriculas m ON a.id = m.aluno_id
                WHERE m.ano_letivo_id = %s
                AND m.status = 'Ativo'
                AND a.escola_id = %s
            """, (self.ano_atual['id'], self.escola_id))

            resultado = cast(Any, cursor.fetchone())
            total_matriculas = resultado['total'] if resultado else 0
            self.label_total_matriculas.config(text=str(total_matriculas))
            
            # Buscar IDs das turmas do 9º ano
            cursor.execute("""
                SELECT t.id
                FROM turmas t
                JOIN series s ON t.serie_id = s.id
                WHERE s.nome LIKE '9%%'
                AND t.escola_id = %s
            """, (self.escola_id,))
            _rows = cast(Any, cursor.fetchall())
            turmas_9ano = [row['id'] for row in _rows]
            
            # Alunos que continuarão (1º ao 8º ano - apenas Ativos)
            if turmas_9ano:
                cursor.execute("""
                    SELECT COUNT(DISTINCT a.id) as total
                    FROM Alunos a
                    JOIN Matriculas m ON a.id = m.aluno_id
                    WHERE m.ano_letivo_id = %s
                    AND m.status = 'Ativo'
                    AND a.escola_id = %s
                    AND m.turma_id NOT IN ({})
                """.format(','.join(['%s'] * len(turmas_9ano))),
                (self.ano_atual['id'], self.escola_id) + tuple(turmas_9ano))
            else:
                cursor.execute("""
                    SELECT COUNT(DISTINCT a.id) as total
                    FROM Alunos a
                    JOIN Matriculas m ON a.id = m.aluno_id
                    WHERE m.ano_letivo_id = %s
                    AND m.status = 'Ativo'
                    AND a.escola_id = %s
                """, (self.ano_atual['id'], self.escola_id))
            
            resultado = cast(Any, cursor.fetchone())
            alunos_continuar = resultado['total'] if resultado else 0
            self.label_alunos_continuar.config(text=str(alunos_continuar))
            
            # Alunos reprovados (média final < 60) - aplicar a TODAS as turmas
            try:
                if turmas_9ano:
                    # Mesmo se tivermos turmas do 9º ano, verificamos reprovações em todas as turmas
                    cursor.execute("""
                        SELECT COUNT(DISTINCT a.id) as total
                        FROM Alunos a
                        JOIN Matriculas m ON a.id = m.aluno_id
                        LEFT JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = %s
                        WHERE m.ano_letivo_id = %s
                        AND m.status = 'Ativo'
                        AND a.escola_id = %s
                        GROUP BY a.id
                        HAVING (
                            COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
                        ) / 4 < 60 OR AVG(n.nota) IS NULL
                    """, (self.ano_atual['id'], self.ano_atual['id'], self.escola_id))
                    # cursor.fetchone não é suficiente aqui pois o GROUP BY retorna múltiplas linhas;
                    # usar fetchall e contar
                    rows_reprov = cursor.fetchall()
                    alunos_reprovados = len(rows_reprov) if rows_reprov else 0
                else:
                    # Se não houver turmas do 9º (caso raro), aplicar mesma lógica
                    cursor.execute("""
                        SELECT COUNT(DISTINCT a.id) as total
                        FROM Alunos a
                        JOIN Matriculas m ON a.id = m.aluno_id
                        LEFT JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = %s
                        WHERE m.ano_letivo_id = %s
                        AND m.status = 'Ativo'
                        AND a.escola_id = %s
                        GROUP BY a.id
                        HAVING (
                            COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
                        ) / 4 < 60 OR AVG(n.nota) IS NULL
                    """, (self.ano_atual['id'], self.ano_atual['id'], self.escola_id))
                    rows_reprov = cursor.fetchall()
                    alunos_reprovados = len(rows_reprov) if rows_reprov else 0

                self.label_alunos_9ano_reprovados.config(text=str(alunos_reprovados))
            except Exception:
                # Em caso de erro na contagem de reprovações, registrar e continuar
                alunos_reprovados = 0
                self.label_alunos_9ano_reprovados.config(text=str(alunos_reprovados))
            
            # Alunos a excluir (Transferidos, Cancelados, Evadidos)
            cursor.execute("""
                SELECT COUNT(DISTINCT a.id) as total
                FROM Alunos a
                JOIN Matriculas m ON a.id = m.aluno_id
                WHERE m.ano_letivo_id = %s
                AND m.status IN ('Transferido', 'Transferida', 'Cancelado', 'Evadido')
                AND a.escola_id = %s
            """, (self.ano_atual['id'], self.escola_id))
            
            resultado = cast(Any, cursor.fetchone())
            alunos_excluir = resultado['total'] if resultado else 0
            self.label_alunos_excluir.config(text=str(alunos_excluir))
            
            self.estatisticas = {
                'total_matriculas': total_matriculas,
                'alunos_continuar': alunos_continuar,
                'alunos_reprovados': alunos_reprovados,
                'alunos_excluir': alunos_excluir
            }
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar estatísticas: {str(e)}")
            traceback.print_exc()

    def verificar_fim_do_ano(self) -> bool:
        """Verifica se o ano letivo atual já encerrou.

        Usa a data_fim da tabela anosletivos se disponível.
        Caso contrário, usa 31/12 do ano letivo como fallback.
        
        Returns:
            bool: True se a data atual for posterior à data de término do ano letivo
        """
        try:
            if not self.ano_atual or 'ano_letivo' not in self.ano_atual:
                return False
            
            hoje = datetime.now().date()
            
            # Verificar se há data_fim definida na tabela anosletivos
            data_fim = self.ano_atual.get('data_fim')
            
            if data_fim:
                # Converter para date se necessário
                if hasattr(data_fim, 'date'):
                    data_fim = data_fim.date()
                elif isinstance(data_fim, str):
                    data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
                
                logger.debug(f"Verificando fim do ano: hoje={hoje}, data_fim={data_fim}")
                return hoje > data_fim
            else:
                # Fallback: usar 31/12 do ano letivo
                ano = int(self.ano_atual['ano_letivo'])
                fim_ano = datetime(ano, 12, 31).date()
                logger.debug(f"Usando fallback 31/12: hoje={hoje}, fim_ano={fim_ano}")
                return hoje > fim_ano
                
        except Exception as e:
            logger.warning(f"Erro ao verificar fim do ano: {e}")
            return False

    def verificar_pendencias_bimestrais(self) -> Dict:
        """Verifica pendências de notas para os 4 bimestres em iniciais e finais.

        Retorna um dicionário com as pendências (mesmo formato retornado por buscar_pendencias_notas).
        Se vazio, não há pendências.
        """
        all_pend = {}
        try:
            if not self.ano_atual or 'ano_letivo' not in self.ano_atual:
                return {}
            ano_val = int(self.ano_atual['ano_letivo'])
            bimestres = ['1º bimestre', '2º bimestre', '3º bimestre', '4º bimestre']
            niveis = ['iniciais', 'finais']
            for b in bimestres:
                for n in niveis:
                    try:
                        pend = buscar_pendencias_notas(b, n, ano_val, 60)
                        if pend:
                            # mesclar
                            for k, v in pend.items():
                                if k not in all_pend:
                                    all_pend[k] = v
                    except Exception:
                        # se uma checagem falhar, preferimos bloquear a transição
                        return {'erro': {'mensagem': 'Falha ao verificar pendências'}}
        except Exception:
            return {'erro': {'mensagem': 'Falha ao verificar pendências'}}

        return all_pend
    
    def simular_transicao(self):
        """Simula a transição mostrando detalhes do que será feito"""
        if not self.ano_atual or not self.ano_novo:
            messagebox.showerror("Erro", "Dados do ano letivo não carregados.")
            return
        # Antes de habilitar execução, verificar se o ano letivo acabou
        if not self.verificar_fim_do_ano():
            messagebox.showerror(
                "Ano não encerrado",
                "O ano letivo ainda não acabou. A transição só pode ser executada após o término do ano letivo (ex.: depois de 31/12)."
            )
            return

        # Verificar pendências bimestrais (1º ao 4º bimestre, iniciais e finais)
        pendencias = self.verificar_pendencias_bimestrais()
        if pendencias:
            # montar mensagem resumida
            resumo = []
            for chave, info in list(pendencias.items())[:5]:
                serie, turma, turno = chave
                # contar alunos com pendências e disciplinas sem lançamento
                alunos_com_pend = sum(1 for a in info['alunos'].values() if len(a['disciplinas_sem_nota']) > 0)
                disc_sem = len(info.get('disciplinas_sem_lancamento', []))
                resumo.append(f"{serie} {turma} ({turno}): {alunos_com_pend} alunos, {disc_sem} disciplinas sem lançamento")

            mensagem_pend = (
                "Existem pendências de lançamento de notas. \n\n"
                "Verifique o menu 'Gerenciamento de Notas > Relatório de Pendências' e corrija antes de executar a transição.\n\n"
                "Exemplos de turmas com pendências:\n" + "\n".join(resumo)
            )
            messagebox.showerror("Pendências encontradas", mensagem_pend)
            return

        mensagem = f"""
        SIMULAÇÃO DA TRANSIÇÃO DE ANO LETIVO
        {'='*50}
        
        Ano Atual: {self.ano_atual['ano_letivo']}
        Novo Ano: {self.ano_novo['ano_letivo']}
        
        OPERAÇÕES QUE SERÃO REALIZADAS:
        
        1️⃣ Criar novo ano letivo: {self.ano_novo['ano_letivo']}
        
        2️⃣ Encerrar matrículas do ano {self.ano_atual['ano_letivo']}:
           - {self.estatisticas['total_matriculas']} matrículas serão marcadas como "Concluído"
        
        3️⃣ Criar novas matrículas para {self.ano_novo['ano_letivo']}:
           - {self.estatisticas['alunos_continuar']} alunos (1º ao 8º ano) serão rematriculados
                     - {self.estatisticas.get('alunos_reprovados', 0)} alunos REPROVADOS
                         (média < 60) serão rematriculados conforme regra definida
        
        4️⃣ Alunos do 9º ano APROVADOS:
           - NÃO serão rematriculados (concluíram o ensino fundamental)
        
        5️⃣ Alunos que NÃO serão rematriculados:
           - {self.estatisticas['alunos_excluir']} alunos (Transferidos/Cancelados/Evadidos)
        
        {'='*50}
        
        ⚠️ Esta operação NÃO PODE SER DESFEITA!
        
        Deseja habilitar a execução da transição?
        """
        
        resposta = messagebox.askyesno("Simulação da Transição", mensagem)
        
        if resposta:
            self.btn_executar.config(state=NORMAL)
            messagebox.showinfo("Pronto", 
                              "Simulação concluída!\n\n"
                              "O botão 'Executar Transição' foi habilitado.\n"
                              "Clique nele para realizar a transição.")
    
    def verificar_backup_recente(self) -> bool:
        """Verifica se há backup do banco nas últimas 24h.
        
        Returns:
            bool: True se existe backup recente, False caso contrário
        """
        import os
        from pathlib import Path
        
        caminhos_backup = [
            Path("migrations/backup_redeescola.sql"),
            Path(r"G:\Meu Drive\NADIR_2025\Backup\backup_redeescola.sql")
        ]
        
        for caminho in caminhos_backup:
            try:
                if caminho.exists():
                    # Verificar data de modificação
                    mtime = datetime.fromtimestamp(caminho.stat().st_mtime)
                    diferenca = datetime.now() - mtime
                    if diferenca.total_seconds() < 24 * 60 * 60:  # 24 horas
                        logger.info(f"Backup recente encontrado: {caminho} (modificado há {diferenca})")
                        return True
            except Exception as e:
                logger.warning(f"Erro ao verificar backup em {caminho}: {e}")
        
        return False
    
    def criar_backup_pre_transicao(self) -> bool:
        """Cria backup automático antes de executar a transição.
        
        Returns:
            bool: True se o backup foi criado com sucesso, False caso contrário
        """
        try:
            import Seguranca
            
            logger.info("Criando backup pré-transição...")
            self.atualizar_status("Criando backup de segurança...", 5)
            
            resultado = Seguranca.fazer_backup()
            
            if resultado:
                logger.info("✓ Backup pré-transição criado com sucesso!")
                return True
            else:
                logger.error("✗ Falha ao criar backup pré-transição")
                return False
                
        except Exception as e:
            logger.exception(f"Erro ao criar backup: {e}")
            return False
    
    def _carregar_mapa_turmas(self) -> Dict[int, Dict]:
        """Carrega e cacheia o mapeamento de turmas com informações de série.
        
        Returns:
            Dict mapeando turma_id para dados completos da turma
        """
        if not self._mapa_turmas:
            self._mapa_turmas = QueriesTransicao.get_mapa_turmas(self.escola_id)
            logger.debug(f"Mapa de turmas carregado: {len(self._mapa_turmas)} turmas")
        return self._mapa_turmas
    
    def obter_proxima_turma(self, turma_atual_id: int, reprovado: bool = False) -> int:
        """Obtém a turma para o próximo ano letivo.
        
        Para alunos aprovados: promove para a próxima série (1º ano → 2º ano).
        Para alunos reprovados: mantém na mesma turma/série.
        
        Args:
            turma_atual_id: ID da turma atual do aluno
            reprovado: Se True, mantém na mesma turma
            
        Returns:
            ID da turma para matrícula no próximo ano
        """
        # Reprovados ficam na mesma turma
        if reprovado:
            logger.debug(f"Aluno reprovado: mantendo na turma {turma_atual_id}")
            return turma_atual_id
        
        # Buscar próxima turma
        proxima = QueriesTransicao.get_proxima_turma(turma_atual_id, self.escola_id)
        
        if proxima:
            logger.debug(f"Progressão: turma {turma_atual_id} → {proxima}")
            return proxima
        else:
            # Se não encontrar próxima série (ex: 9º ano), manter na mesma
            # Isso não deve acontecer pois 9º ano é excluído antes
            logger.warning(f"Próxima turma não encontrada para {turma_atual_id}, mantendo")
            return turma_atual_id
    
    def _registrar_auditoria(
        self,
        status: str,
        matriculas_encerradas: int,
        matriculas_criadas: int,
        alunos_promovidos: int,
        alunos_retidos: int,
        alunos_concluintes: int,
        detalhes: str = None
    ):
        """Registra a transição na tabela de auditoria.
        
        Args:
            status: 'sucesso', 'erro' ou 'rollback'
            matriculas_encerradas: Total de matrículas encerradas
            matriculas_criadas: Total de novas matrículas
            alunos_promovidos: Alunos que avançaram de série
            alunos_retidos: Alunos reprovados
            alunos_concluintes: Alunos do 9º ano que concluíram
            detalhes: Informações adicionais (JSON ou texto)
        """
        try:
            import os
            usuario = os.getenv('USERNAME', 'sistema')
            
            QueriesTransicao.registrar_auditoria(
                ano_origem=self.ano_atual['ano_letivo'],
                ano_destino=self.ano_novo['ano_letivo'],
                escola_id=self.escola_id,
                usuario=usuario,
                matriculas_encerradas=matriculas_encerradas,
                matriculas_criadas=matriculas_criadas,
                alunos_promovidos=alunos_promovidos,
                alunos_retidos=alunos_retidos,
                alunos_concluintes=alunos_concluintes,
                status=status,
                detalhes=detalhes
            )
        except Exception as e:
            logger.warning(f"Erro ao registrar auditoria (não crítico): {e}")
    
    def confirmar_transicao(self):
        """Confirmação final antes de executar"""
        # Verificar se existe backup recente
        backup_recente = self.verificar_backup_recente()
        
        if backup_recente:
            msg_backup = "✓ Backup recente encontrado (últimas 24h).\n\n"
        else:
            msg_backup = "⚠️ Nenhum backup recente encontrado!\nUm backup será criado automaticamente.\n\n"
        
        resposta = messagebox.askyesno(
            "⚠️ CONFIRMAÇÃO FINAL",
            f"Você está prestes a realizar a transição do ano letivo "
            f"{self.ano_atual['ano_letivo']} para {self.ano_novo['ano_letivo']}.\n\n"
            f"Esta operação é IRREVERSÍVEL!\n\n"
            f"{msg_backup}"
            f"Deseja continuar?",
            icon='warning'
        )
        
        if resposta:
            # Solicitar senha novamente como medida de segurança adicional
            import os
            from dotenv import load_dotenv
            from tkinter import simpledialog
            
            load_dotenv()
            
            # Usar senha administrativa separada, com fallback para senha do banco
            senha_admin = os.getenv('ADMIN_TRANSICAO_PASSWORD')
            if not senha_admin:
                senha_admin = os.getenv('DB_PASSWORD')
                logger.warning("ADMIN_TRANSICAO_PASSWORD não configurada, usando DB_PASSWORD como fallback")
            
            senha_digitada = simpledialog.askstring(
                "Autenticação de Segurança",
                "⚠️ ÚLTIMA CONFIRMAÇÃO ⚠️\n\n"
                "Por segurança, digite novamente a senha administrativa\n"
                "para EXECUTAR a transição:",
                show='*'
            )
            
            # Verificar se o usuário cancelou
            if senha_digitada is None:
                messagebox.showinfo("Cancelado", "Transição cancelada pelo usuário.")
                self.btn_simular.config(state=NORMAL)
                self.btn_executar.config(state=NORMAL)
                return
            
            # Verificar senha
            if senha_digitada != senha_admin:
                messagebox.showerror(
                    "Acesso Negado",
                    "Senha incorreta! A transição foi CANCELADA por segurança."
                )
                logger.warning("Tentativa de executar transição com senha incorreta")
                self.btn_simular.config(state=NORMAL)
                self.btn_executar.config(state=NORMAL)
                return
            
            # Criar backup se não houver um recente
            if not backup_recente:
                if not self.criar_backup_pre_transicao():
                    resposta_continuar = messagebox.askyesno(
                        "⚠️ Falha no Backup",
                        "Não foi possível criar o backup automático.\n\n"
                        "ATENÇÃO: Prosseguir sem backup é MUITO ARRISCADO!\n\n"
                        "Deseja continuar mesmo assim?",
                        icon='warning'
                    )
                    if not resposta_continuar:
                        messagebox.showinfo("Cancelado", "Transição cancelada. Faça o backup manualmente.")
                        self.btn_simular.config(state=NORMAL)
                        self.btn_executar.config(state=NORMAL)
                        return
            
            # Se a senha estiver correta e backup OK, executar a transição
            self.executar_transicao()
    
    def executar_transicao(self, dry_run: bool = False):
        """Executa a transição de ano letivo.
        
        Args:
            dry_run: Se True, simula a transição sem fazer commit (rollback no final)
        """
        if self._executando:
            logger.warning("Transição já em execução, ignorando chamada duplicada")
            return
        
        self._executando = True
        self.btn_simular.config(state=DISABLED)
        self.btn_executar.config(state=DISABLED)
        
        # Executar em thread separada para não travar a UI
        def worker():
            try:
                self._executar_transicao_interno(dry_run)
            except Exception as e:
                logger.exception(f"Erro na thread de transição: {e}")
                self.janela.after(0, lambda: self._mostrar_erro(str(e)))
            finally:
                self._executando = False
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _mostrar_erro(self, mensagem: str):
        """Mostra erro na UI (chamado da thread principal)."""
        messagebox.showerror("Erro", f"Erro ao executar transição:\n{mensagem}")
        self.btn_simular.config(state=NORMAL)
        self.btn_executar.config(state=NORMAL)
    
    def _atualizar_status_seguro(self, mensagem: str, valor: int):
        """Atualiza status de forma thread-safe."""
        self.janela.after(0, lambda: self.atualizar_status(mensagem, valor))
    
    def _executar_transicao_interno(self, dry_run: bool = False):
        """Execução interna da transição (roda em thread separada).
        
        Args:
            dry_run: Se True, faz rollback no final ao invés de commit
        """
        # Atualizar UI de forma segura
        self.janela.after(0, lambda: self.progressbar.pack(pady=10))
        
        modo = "DRY-RUN" if dry_run else "PRODUÇÃO"
        
        # Registrar início e medir tempo
        tempo_inicio = time.time()
        
        logger.info("=" * 60)
        logger.info(f"INICIANDO TRANSIÇÃO DE ANO LETIVO [{modo}]")
        logger.info(f"Ano origem: {self.ano_atual['ano_letivo']}")
        logger.info(f"Ano destino: {self.ano_novo['ano_letivo']}")
        logger.info(f"Escola ID: {self.escola_id}")
        logger.info("=" * 60)
        
        # Contadores para auditoria
        matriculas_encerradas = 0
        alunos_promovidos = 0
        alunos_retidos = 0
        alunos_concluintes = 0
        total_alunos = 0
        
        try:
            # Carregar mapa de turmas para progressão
            self._carregar_mapa_turmas()
            
            # Usar get_connection para controle de transação
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Passo 1: Criar novo ano letivo
                self._atualizar_status_seguro("Criando novo ano letivo...", 10)
                logger.info(f"[Passo 1] Criando ano letivo {self.ano_novo['ano_letivo']}")
                cursor.execute(QUERY_CRIAR_ANO_LETIVO, (self.ano_novo['ano_letivo'],))
                if not dry_run:
                    conn.commit()
                logger.info(f"[Passo 1] ✓ Ano letivo {self.ano_novo['ano_letivo']} criado/verificado")

                # Buscar ID do novo ano
                cursor.execute("""
                    SELECT id FROM anosletivos WHERE ano_letivo = %s
                """, (self.ano_novo['ano_letivo'],))
                _tmp = cast(Any, cursor.fetchone())
                novo_ano_id = _tmp['id']
                logger.info(f"[Passo 1] Novo ano_letivo_id: {novo_ano_id}")

                # Passo 2: Encerrar matrículas antigas
                self._atualizar_status_seguro("Encerrando matrículas do ano anterior...", 30)
                logger.info(f"[Passo 2] Encerrando matrículas do ano {self.ano_atual['ano_letivo']}")
                cursor.execute(QUERY_ENCERRAR_MATRICULAS, (self.ano_atual['id'],))
                matriculas_encerradas = cursor.rowcount
                if not dry_run:
                    conn.commit()
                logger.info(f"[Passo 2] ✓ {matriculas_encerradas} matrículas encerradas")

                # Passo 3: Buscar alunos ativos para rematricular
                self._atualizar_status_seguro("Buscando alunos para rematricular...", 50)
                logger.info("[Passo 3] Buscando alunos para rematricular")

                # Buscar turmas do 9º ano usando query centralizada
                turmas_9ano = QueriesTransicao.get_turmas_9ano(self.escola_id)
                logger.info(f"[Passo 3] Turmas do 9º ano identificadas: {turmas_9ano}")

                # Buscar alunos usando queries centralizadas
                alunos_normais_raw, alunos_reprovados_raw = QueriesTransicao.get_alunos_para_rematricular(
                    self.ano_atual['id'], 
                    self.escola_id, 
                    turmas_9ano
                )
                
                # Converter para lista mutável
                alunos_normais = [dict(a) for a in alunos_normais_raw] if alunos_normais_raw else []
                alunos_reprovados = [dict(a) for a in alunos_reprovados_raw] if alunos_reprovados_raw else []
                
                logger.info(f"[Passo 3] Alunos normais (1º ao 8º): {len(alunos_normais)}")
                logger.info(f"[Passo 3] Alunos reprovados: {len(alunos_reprovados)}")
                
                # IDs dos reprovados para marcação
                ids_reprovados = {a['aluno_id'] for a in alunos_reprovados}
                
                # Combinar alunos, marcando reprovados
                alunos_map: Dict[int, Dict] = {}
                
                for a in alunos_normais:
                    aid = int(a['aluno_id'])
                    a['reprovado'] = aid in ids_reprovados
                    alunos_map[aid] = a
                
                for a in alunos_reprovados:
                    aid = int(a['aluno_id'])
                    if aid not in alunos_map:
                        a['reprovado'] = True
                        alunos_map[aid] = a

                alunos = list(alunos_map.values())
                total_alunos = len(alunos)
                logger.info(f"[Passo 3] ✓ Total de alunos a rematricular: {total_alunos}")

                # Passo 4: Criar novas matrículas COM PROGRESSÃO DE SÉRIE
                self._atualizar_status_seguro(f"Criando {total_alunos} novas matrículas...", 60)
                logger.info(f"[Passo 4] Criando {total_alunos} novas matrículas com progressão de série")

                for i, aluno in enumerate(alunos):
                    turma_atual = aluno['turma_id']
                    reprovado = aluno.get('reprovado', False)
                    
                    # Determinar turma de destino com progressão
                    nova_turma = self.obter_proxima_turma(turma_atual, reprovado=reprovado)
                    
                    # Criar matrícula
                    cursor.execute(QUERY_CRIAR_MATRICULA, (aluno['aluno_id'], nova_turma, novo_ano_id))
                    
                    # Contabilizar
                    if reprovado:
                        alunos_retidos += 1
                    else:
                        alunos_promovidos += 1

                    # Atualizar progresso (thread-safe)
                    if total_alunos > 0:
                        progresso = 60 + (i + 1) / total_alunos * 30
                        self.janela.after(0, lambda p=progresso: setattr(self.progressbar, 'value', p))

                # Contar alunos concluintes (9º ano aprovados)
                alunos_concluintes = self.estatisticas.get('total_matriculas', 0) - total_alunos - self.estatisticas.get('alunos_excluir', 0)
                if alunos_concluintes < 0:
                    alunos_concluintes = 0

                # Commit ou rollback baseado no modo
                if dry_run:
                    conn.rollback()
                    logger.info("[DRY-RUN] Rollback executado - nenhuma alteração foi persistida")
                else:
                    conn.commit()
                    logger.info(f"[Passo 4] ✓ {total_alunos} matrículas criadas com sucesso")
                # Finalizar
                self._atualizar_status_seguro("Transição concluída com sucesso!", 100)

                cursor.close()
                
                # Log de resumo final
                logger.info("=" * 60)
                logger.info(f"TRANSIÇÃO CONCLUÍDA {'[DRY-RUN]' if dry_run else 'COM SUCESSO'}")
                logger.info(f"Resumo:")
                logger.info(f"  - Ano letivo criado: {self.ano_novo['ano_letivo']}")
                logger.info(f"  - Matrículas encerradas: {matriculas_encerradas}")
                logger.info(f"  - Novas matrículas: {total_alunos}")
                logger.info(f"  - Alunos promovidos: {alunos_promovidos}")
                logger.info(f"  - Alunos retidos: {alunos_retidos}")
                logger.info(f"  - Alunos concluintes (9º ano): {alunos_concluintes}")
                logger.info("=" * 60)
                
                # Registrar auditoria
                if not dry_run:
                    self._registrar_auditoria(
                        status='sucesso',
                        matriculas_encerradas=matriculas_encerradas,
                        matriculas_criadas=total_alunos,
                        alunos_promovidos=alunos_promovidos,
                        alunos_retidos=alunos_retidos,
                        alunos_concluintes=alunos_concluintes,
                        detalhes=json.dumps({
                            'ano_origem': self.ano_atual['ano_letivo'],
                            'ano_destino': self.ano_novo['ano_letivo'],
                            'data': datetime.now().isoformat()
                        })
                    )
                
                # Calcular duração
                duracao = time.time() - tempo_inicio
                
                # Gerar relatório PDF
                caminho_pdf = None
                if not dry_run:
                    try:
                        from relatorio_transicao import gerar_relatorio_transicao
                        
                        dados_relatorio = {
                            'matriculas_encerradas': matriculas_encerradas,
                            'matriculas_criadas': total_alunos,
                            'alunos_promovidos': alunos_promovidos,
                            'alunos_retidos': alunos_retidos,
                            'alunos_concluintes': alunos_concluintes,
                            'status': 'sucesso',
                            'duracao_segundos': duracao
                        }
                        
                        caminho_pdf = gerar_relatorio_transicao(
                            ano_origem=self.ano_atual['ano_letivo'],
                            ano_destino=self.ano_novo['ano_letivo'],
                            dados=dados_relatorio,
                            escola_id=self.escola_id,
                            abrir=False  # Abriremos após a mensagem
                        )
                        
                        if caminho_pdf:
                            logger.info(f"Relatório PDF gerado: {caminho_pdf}")
                    except Exception as e:
                        logger.warning(f"Erro ao gerar relatório PDF (não crítico): {e}")
                
                # Mostrar mensagem de sucesso
                msg_modo = "\n\n🔍 MODO DRY-RUN: Nenhuma alteração foi feita no banco." if dry_run else ""
                msg_pdf = f"\n\n📄 Relatório PDF gerado com sucesso!" if caminho_pdf else ""
                
                def mostrar_sucesso():
                    messagebox.showinfo(
                        "✅ Sucesso!",
                        f"Transição de ano letivo concluída com sucesso!\n\n"
                        f"✓ Ano letivo {self.ano_novo['ano_letivo']} criado\n"
                        f"✓ {matriculas_encerradas} matrículas encerradas\n"
                        f"✓ {total_alunos} novas matrículas criadas\n"
                        f"   • {alunos_promovidos} alunos promovidos\n"
                        f"   • {alunos_retidos} alunos retidos (reprovados)\n\n"
                        f"ℹ️ {alunos_concluintes} alunos do 9º ano concluíram o ensino fundamental"
                        f"{msg_modo}{msg_pdf}\n\n"
                        f"O sistema agora está configurado para o ano {self.ano_novo['ano_letivo']}."
                    )
                    
                    # Abrir PDF após a mensagem
                    if caminho_pdf and not dry_run:
                        try:
                            import platform
                            import os as os_mod
                            sistema = platform.system()
                            if sistema == 'Windows':
                                os_mod.startfile(caminho_pdf)
                            elif sistema == 'Darwin':
                                os_mod.system(f'open "{caminho_pdf}"')
                            else:
                                os_mod.system(f'xdg-open "{caminho_pdf}"')
                        except Exception:
                            pass
                    
                    if not dry_run:
                        self.fechar()
                
                self.janela.after(0, mostrar_sucesso)

        except Exception as e:
            logger.exception(f"ERRO na transição de ano letivo: {e}")
            
            # Registrar erro na auditoria
            self._registrar_auditoria(
                status='erro',
                matriculas_encerradas=matriculas_encerradas,
                matriculas_criadas=0,
                alunos_promovidos=0,
                alunos_retidos=0,
                alunos_concluintes=0,
                detalhes=str(e)
            )
            
            self.janela.after(0, lambda: self._mostrar_erro(str(e)))
    
    def atualizar_status(self, mensagem, valor):
        """Atualiza o status e a barra de progresso"""
        self.label_status.config(text=mensagem)
        self.progressbar['value'] = valor
        self.janela.update()
    
    def fechar(self):
        """Fecha a janela e volta para a principal"""
        self.janela.destroy()
        self.janela_principal.deiconify()


def abrir_interface_transicao(janela_principal):
    """Função para abrir a interface de transição"""
    # Ocultar janela principal
    janela_principal.withdraw()
    
    # Criar janela de transição
    janela_transicao = Toplevel(janela_principal)
    janela_transicao.focus_force()
    janela_transicao.grab_set()
    
    # Criar interface
    app = InterfaceTransicaoAnoLetivo(janela_transicao, janela_principal)
    
    # Configurar fechamento
    def ao_fechar():
        janela_principal.deiconify()
        janela_transicao.destroy()
    
    janela_transicao.protocol("WM_DELETE_WINDOW", ao_fechar)


if __name__ == "__main__":
    # Teste da interface
    root = Tk()
    root.withdraw()
    abrir_interface_transicao(root)
    root.mainloop()
