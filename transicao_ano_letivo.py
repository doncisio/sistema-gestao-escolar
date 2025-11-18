"""
Módulo para Transição de Ano Letivo
Autor: Tarcisio Sousa de Almeida
Data: 11/11/2025

Funcionalidades:
- Encerrar matrículas do ano letivo atual (mudar status para "Concluído")
- Criar novas matrículas para o próximo ano letivo
- Excluir alunos com status: Cancelado, Transferido, Evadido
- Manter apenas alunos ativos para a nova matrícula
"""

import mysql.connector
from tkinter import (Tk, Toplevel, Frame, Label, LabelFrame, Button,
                     BOTH, LEFT, X, W, E, RIDGE, DISABLED, NORMAL)
from tkinter import ttk, messagebox
from conexao import conectar_bd
from db.connection import get_connection, get_cursor
from typing import Any, cast
from datetime import datetime
from typing import Dict
from relatorio_pendencias import buscar_pendencias_notas
import traceback


class InterfaceTransicaoAnoLetivo:
    """Interface para gerenciar a transição de ano letivo"""
    
    def __init__(self, janela_pai, janela_principal):
        self.janela = janela_pai
        self.janela_principal = janela_principal
        self.janela.title("Transição de Ano Letivo")
        self.janela.geometry("900x700")
        self.janela.resizable(False, False)
        self.janela.configure(bg="#f0f0f0")
        
        # Cores
        self.co0 = "#ffffff"  # branco
        self.co1 = "#3b5998"  # azul escuro
        self.co2 = "#4CAF50"  # verde
        self.co3 = "#f44336"  # vermelho
        self.co4 = "#ff9800"  # laranja
        
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
        """Carrega os dados iniciais do banco"""
        try:
            from db.connection import get_cursor

            with get_cursor() as cursor:
                # Buscar ano letivo atual
                cursor.execute("""
                    SELECT id, ano_letivo 
                    FROM anosletivos 
                    WHERE ano_letivo = YEAR(CURDATE())
                """)
                resultado = cast(Any, cursor.fetchone())

                if not resultado:
                    # Buscar o ano mais recente
                    cursor.execute("""
                        SELECT id, ano_letivo 
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

                # Carregar estatísticas (reabre cursor dentro da função)
                # carregar_estatisticas espera receber um cursor, então abrimos um temporário
                with get_cursor() as cur_stats:
                    self.carregar_estatisticas(cur_stats)
            else:
                messagebox.showerror("Erro", "Nenhum ano letivo encontrado no sistema.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar dados: {str(e)}")
            traceback.print_exc()
    
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
            """, (self.ano_atual['id'], 60))

            resultado = cast(Any, cursor.fetchone())
            total_matriculas = resultado['total'] if resultado else 0
            self.label_total_matriculas.config(text=str(total_matriculas))
            
            # Buscar IDs das turmas do 9º ano
            cursor.execute("""
                SELECT t.id
                FROM turmas t
                JOIN serie s ON t.serie_id = s.id
                WHERE s.nome LIKE '9%'
                AND t.escola_id = 60
            """)
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
                    AND a.escola_id = 60
                    AND m.turma_id NOT IN ({})
                """.format(','.join(['%s'] * len(turmas_9ano))),
                (self.ano_atual['id'],) + tuple(turmas_9ano))
            else:
                cursor.execute("""
                    SELECT COUNT(DISTINCT a.id) as total
                    FROM Alunos a
                    JOIN Matriculas m ON a.id = m.aluno_id
                    WHERE m.ano_letivo_id = %s
                    AND m.status = 'Ativo'
                    AND a.escola_id = 60
                """, (self.ano_atual['id'],))
            
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
                        AND a.escola_id = 60
                        GROUP BY a.id
                        HAVING (
                            COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
                        ) / 4 < 60 OR AVG(n.nota) IS NULL
                    """, (self.ano_atual['id'], self.ano_atual['id']))
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
                        AND a.escola_id = 60
                        GROUP BY a.id
                        HAVING (
                            COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
                        ) / 4 < 60 OR AVG(n.nota) IS NULL
                    """, (self.ano_atual['id'], self.ano_atual['id']))
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
                AND a.escola_id = 60
            """, (self.ano_atual['id'],))
            
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
        """Verifica se o ano letivo atual já passou do último dia do ano.

        Retorna True se a data atual for posterior a 31/12 do ano letivo atual.
        """
        try:
            if not self.ano_atual or 'ano_letivo' not in self.ano_atual:
                return False
            ano = int(self.ano_atual['ano_letivo'])
            fim_ano = datetime(ano, 12, 31).date()
            hoje = datetime.now().date()
            return hoje > fim_ano
        except Exception:
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
    
    def confirmar_transicao(self):
        """Confirmação final antes de executar"""
        resposta = messagebox.askyesno(
            "⚠️ CONFIRMAÇÃO FINAL",
            f"Você está prestes a realizar a transição do ano letivo "
            f"{self.ano_atual['ano_letivo']} para {self.ano_novo['ano_letivo']}.\n\n"
            f"Esta operação é IRREVERSÍVEL!\n\n"
            f"Você fez BACKUP do banco de dados?\n\n"
            f"Deseja continuar?",
            icon='warning'
        )
        
        if resposta:
            # Solicitar senha novamente como medida de segurança adicional
            import os
            from dotenv import load_dotenv
            from tkinter import simpledialog
            
            load_dotenv()
            senha_correta = os.getenv('DB_PASSWORD')
            
            senha_digitada = simpledialog.askstring(
                "Autenticação de Segurança",
                "Por segurança, digite novamente a senha do banco de dados\n"
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
            if senha_digitada != senha_correta:
                messagebox.showerror(
                    "Acesso Negado",
                    "Senha incorreta! A transição foi CANCELADA por segurança."
                )
                self.btn_simular.config(state=NORMAL)
                self.btn_executar.config(state=NORMAL)
                return
            
            # Se a senha estiver correta, executar a transição
            self.executar_transicao()
    
    def executar_transicao(self):
        """Executa a transição de ano letivo"""
        self.btn_simular.config(state=DISABLED)
        self.btn_executar.config(state=DISABLED)
        
        self.progressbar.pack(pady=10)
        self.progressbar['value'] = 0
        
        try:
            # Usar get_connection para garantir fechamento e controle de transação
            with get_connection() as conn:
                cursor = conn.cursor(dictionary=True)

                # Passo 1: Criar novo ano letivo
                self.atualizar_status("Criando novo ano letivo...", 10)
                cursor.execute("""
                    INSERT INTO anosletivos (ano_letivo)
                    VALUES (%s)
                    ON DUPLICATE KEY UPDATE ano_letivo = ano_letivo
                """, (self.ano_novo['ano_letivo'],))
                conn.commit()

                # Buscar ID do novo ano
                cursor.execute("""
                    SELECT id FROM anosletivos WHERE ano_letivo = %s
                """, (self.ano_novo['ano_letivo'],))
                _tmp = cast(Any, cursor.fetchone())
                novo_ano_id = _tmp['id']

                # Passo 2: Encerrar matrículas antigas
                self.atualizar_status("Encerrando matrículas do ano anterior...", 30)
                cursor.execute("""
                    UPDATE Matriculas
                    SET status = 'Concluído'
                    WHERE ano_letivo_id = %s
                    AND status = 'Ativo'
                """, (self.ano_atual['id'],))
                conn.commit()

                # Passo 3: Buscar alunos ativos para rematricular
                self.atualizar_status("Buscando alunos para rematricular...", 50)

                # Buscar turmas do 9º ano
                cursor.execute("""
                    SELECT t.id
                    FROM turmas t
                    JOIN serie s ON t.serie_id = s.id
                    WHERE s.nome LIKE '9%'
                    AND t.escola_id = 60
                """)
                _rows = cast(Any, cursor.fetchall())
                turmas_9ano = [row['id'] for row in _rows]

                # Buscar alunos que NÃO são do 9º ano (esses vão para o próximo ano)
                cursor.execute("""
                    SELECT DISTINCT 
                        a.id as aluno_id,
                        m.turma_id
                    FROM Alunos a
                    JOIN Matriculas m ON a.id = m.aluno_id
                    WHERE m.ano_letivo_id = %s
                    AND m.status = 'Concluído'
                    AND a.escola_id = 60
                    AND m.turma_id NOT IN ({})
                """.format(','.join(['%s'] * len(turmas_9ano)) if turmas_9ano else "0"), 
                (self.ano_atual['id'],) + tuple(turmas_9ano) if turmas_9ano else (self.ano_atual['id'],))

                alunos_normais = cast(Any, cursor.fetchall())

                # Buscar alunos REPROVADOS (média < 60) em todas as turmas
                cursor.execute("""
                    SELECT DISTINCT 
                        a.id as aluno_id,
                        m.turma_id,
                        (
                            COALESCE(AVG(CASE WHEN n.bimestre = '1º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '2º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '3º bimestre' THEN n.nota END), 0) +
                            COALESCE(AVG(CASE WHEN n.bimestre = '4º bimestre' THEN n.nota END), 0)
                        ) / 4 as media_final
                    FROM Alunos a
                    JOIN Matriculas m ON a.id = m.aluno_id
                    LEFT JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = %s
                    WHERE m.ano_letivo_id = %s
                    AND m.status = 'Concluído'
                    AND a.escola_id = 60
                    GROUP BY a.id, m.turma_id
                    HAVING media_final < 60 OR media_final IS NULL
                """, (self.ano_atual['id'], self.ano_atual['id']))

                alunos_reprovados = cast(Any, cursor.fetchall())

                # Combinar todos os alunos que serão rematriculados, evitando duplicatas
                alunos_map = {}
                for a in alunos_normais:
                    alunos_map[int(a['aluno_id'])] = a

                for a in alunos_reprovados:
                    aid = int(a['aluno_id'])
                    if aid not in alunos_map:
                        alunos_map[aid] = a

                alunos = list(alunos_map.values())
                total_alunos = len(alunos)

                # Passo 4: Criar novas matrículas
                self.atualizar_status(f"Criando {total_alunos} novas matrículas...", 60)

                for i, aluno in enumerate(alunos):
                    cursor.execute("""
                        INSERT INTO Matriculas (aluno_id, turma_id, ano_letivo_id, status)
                        VALUES (%s, %s, %s, 'Ativo')
                    """, (aluno['aluno_id'], aluno['turma_id'], novo_ano_id))

                    # Atualizar progresso
                    progresso = 60 + (i + 1) / total_alunos * 30
                    self.progressbar['value'] = progresso
                    self.janela.update()

                conn.commit()

                # Finalizar
                self.atualizar_status("Transição concluída com sucesso!", 100)

                cursor.close()

                messagebox.showinfo(
                    "✅ Sucesso!",
                    f"Transição de ano letivo concluída com sucesso!\n\n"
                    f"✓ Ano letivo {self.ano_novo['ano_letivo']} criado\n"
                    f"✓ {self.estatisticas['total_matriculas']} matrículas encerradas\n"
                    f"✓ {total_alunos} novas matrículas criadas\n"
                    f"   • {self.estatisticas['alunos_continuar']} alunos (1º ao 8º ano)\n"
                    f"   • {self.estatisticas.get('alunos_reprovados', 0)} alunos reprovados\n\n"
                    f"ℹ️ Observação: Alunos do 9º ano aprovados não serão rematriculados\n"
                    f"   (concluíram o ensino fundamental)\n\n"
                    f"O sistema agora está configurado para o ano {self.ano_novo['ano_letivo']}.")

                self.fechar()

        except Exception as e:
            try:
                if 'conn' in locals() and conn:
                    conn.rollback()
            except Exception:
                pass
            messagebox.showerror("Erro", f"Erro ao executar transição:\n{str(e)}")
            traceback.print_exc()
            self.btn_simular.config(state=NORMAL)
            self.btn_executar.config(state=NORMAL)
    
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
