from datetime import datetime
from tkinter import messagebox, ttk
from tkinter import *
import mysql.connector
from mysql.connector import Error
from src.core.conexao import conectar_bd
from tkcalendar import DateEntry
from src.core.seguranca import atualizar_treeview
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Cores
co0 = "#2e2d2b"  # preta
co1 = "#feffff"  # Branca
co2 = "#e5e5e5"  # Cinza
co3 = "#00a095"  # Verde
co4 = "#403d3d"  # Letra
co5 = "#003452"  # Azul
co6 = "#ef5350"  # Vermelho
co7 = "#038cfc"  # azul
co8 = "#263238"  # +verde
co9 = "#e9edf5"  # +verde

# Variável global para armazenar o ID da turma selecionada
selected_turma_id = None

class EditorAluno:
    def __init__(self, frame_detalhes, frame_dados, frame_tabela, treeview, query, aluno_id):
        """
        Inicializa a classe EditorAluno.

        Args:
            frame_detalhes: Frame para os detalhes do aluno.
            frame_dados: Frame para outros dados.
            frame_tabela: Frame para a tabela.
            treeview: Widget Treeview para exibir dados.
            query: Query SQL para buscar dados.
            aluno_id: ID do aluno a ser editado.
        """
        self.frame_detalhes = frame_detalhes
        self.frame_dados = frame_dados
        self.frame_tabela = frame_tabela
        self.treeview = treeview
        self.query = query
        self.aluno_id = aluno_id
        self.conn = None
        self.cursor = None

        # Widgets da interface
        self.l_nome = Label(frame_detalhes, text="Nome *", bg=co1, fg=co4)
        self.l_nome.place(x=4, y=10)
        self.e_nome = Entry(frame_detalhes, width=35, justify='left', relief='solid')
        self.e_nome.place(x=7, y=40)

        self.l_endereco = Label(frame_detalhes, text="Endereço", bg=co1, fg=co4)
        self.l_endereco.place(x=4, y=70)
        self.e_endereco = Entry(frame_detalhes, width=35, justify='left', relief='solid')
        self.e_endereco.place(x=7, y=100)

        self.l_cpf = Label(frame_detalhes, text="CPF *", bg=co1, fg=co4)
        self.l_cpf.place(x=446, y=70)
        self.e_cpf = Entry(frame_detalhes, width=16, justify='left', relief='solid')
        self.e_cpf.place(x=450, y=100)

        self.l_sus = Label(frame_detalhes, text="Cartão SUS", bg=co1, fg=co4)
        self.l_sus.place(x=4, y=130)
        self.e_sus = Entry(frame_detalhes, width=20, justify='left', relief='solid')
        self.e_sus.place(x=7, y=160)

        self.l_sexo = Label(frame_detalhes, text="Sexo", bg=co1, fg=co4)
        self.l_sexo.place(x=190, y=130)
        self.c_sexo = ttk.Combobox(frame_detalhes, width=12, values=('M', 'F'))
        self.c_sexo.place(x=190, y=160)

        self.l_data_nascimento = Label(frame_detalhes, text="Data de Nascimento", bg=co1, fg=co4)
        self.l_data_nascimento.place(x=446, y=10)
        self.c_data_nascimento = DateEntry(frame_detalhes, width=14)
        self.c_data_nascimento.place(x=450, y=40)

        self.l_raca = Label(frame_detalhes, text="Raça", bg=co1, fg=co4)
        self.l_raca.place(x=320, y=130)
        self.c_raca = ttk.Combobox(frame_detalhes, width=12, values=('Branca', 'Preta', 'Parda', 'Amarela', 'Indígena'))
        self.c_raca.place(x=320, y=160)

        self.l_serie = Label(frame_detalhes, text="Série", bg=co1, fg=co4)
        self.l_serie.place(x=4, y=190)
        self.c_serie = ttk.Combobox(frame_detalhes, width=15, values=[])
        self.c_serie.place(x=7, y=220)

        self.l_turno = Label(frame_detalhes, text="Turno", bg=co1, fg=co4)
        self.l_turno.place(x=190, y=190)
        self.c_turno = ttk.Combobox(frame_detalhes, width=15, values=[])
        self.c_turno.place(x=190, y=220)

        self.l_nome_responsavel = Label(frame_detalhes, text="Nome do Responsável", bg=co1, fg=co4)
        self.l_nome_responsavel.place(x=7, y=260)
        self.e_nome_responsavel = Entry(frame_detalhes, width=35, justify='left', relief='solid')
        self.e_nome_responsavel.place(x=10, y=290)

        self.l_parentesco = Label(frame_detalhes, text="Parentesco", bg=co1, fg=co4)
        self.l_parentesco.place(x=350, y=260)
        self.c_parentesco = ttk.Combobox(frame_detalhes, width=15, values=('Pai', 'Mãe', 'Avô', 'Avó', 'Tio', 'Tia', 'Outro'))
        self.c_parentesco.place(x=353, y=290)

        self.l_telefone_responsavel = Label(frame_detalhes, text="Telefone do Responsável", bg=co1, fg=co4)
        self.l_telefone_responsavel.place(x=7, y=320)
        self.e_telefone_responsavel = Entry(frame_detalhes, width=20, justify='left', relief='solid')
        self.e_telefone_responsavel.place(x=10, y=350)

        self.l_rg_responsavel = Label(frame_detalhes, text="RG do Responsável", bg=co1, fg=co4)
        self.l_rg_responsavel.place(x=190, y=320)
        self.e_rg_responsavel = Entry(frame_detalhes, width=15, justify='left', relief='solid')
        self.e_rg_responsavel.place(x=193, y=350)

        self.l_cpf_responsavel = Label(frame_detalhes, text="CPF do Responsável", bg=co1, fg=co4)
        self.l_cpf_responsavel.place(x=350, y=320)
        self.e_cpf_responsavel = Entry(frame_detalhes, width=16, justify='left', relief='solid')
        self.e_cpf_responsavel.place(x=353, y=350)

        self.l_nome_responsavel_2 = Label(frame_detalhes, text="Nome do Segundo Responsável", bg=co1, fg=co4)
        self.l_nome_responsavel_2.place(x=7, y=380)
        self.e_nome_responsavel_2 = Entry(frame_detalhes, width=35, justify='left', relief='solid')
        self.e_nome_responsavel_2.place(x=10, y=410)

        self.l_parentesco_2 = Label(frame_detalhes, text="Parentesco", bg=co1, fg=co4)
        self.l_parentesco_2.place(x=350, y=380)
        self.c_parentesco_2 = ttk.Combobox(frame_detalhes, width=15, values=('Pai', 'Mãe', 'Avô', 'Avó', 'Tio', 'Tia', 'Outro'))
        self.c_parentesco_2.place(x=353, y=410)

        self.l_telefone_responsavel_2 = Label(frame_detalhes, text="Telefone do Segundo Responsável", bg=co1, fg=co4)
        self.l_telefone_responsavel_2.place(x=7, y=440)
        self.e_telefone_responsavel_2 = Entry(frame_detalhes, width=20, justify='left', relief='solid')
        self.e_telefone_responsavel_2.place(x=10, y=470)

        self.l_rg_responsavel_2 = Label(frame_detalhes, text="RG do Segundo Responsável", bg=co1, fg=co4)
        self.l_rg_responsavel_2.place(x=190, y=440)
        self.e_rg_responsavel_2 = Entry(frame_detalhes, width=15, justify='left', relief='solid')
        self.e_rg_responsavel_2.place(x=193, y=470)

        self.l_cpf_responsavel_2 = Label(frame_detalhes, text="CPF do Segundo Responsável", bg=co1, fg=co4)
        self.l_cpf_responsavel_2.place(x=350, y=440)
        self.e_cpf_responsavel_2 = Entry(frame_detalhes, width=16, justify='left', relief='solid')
        self.e_cpf_responsavel_2.place(x=353, y=470)

        try:
            self.conn = conectar_bd()
            if not self.conn:
                raise Exception("Falha ao conectar ao banco de dados.")

            self.cursor = self.conn.cursor(buffered=True)
            self.carregar_series()
            self.carregar_dados_aluno()

            # Adicione o evento de seleção para carregar as turmas quando a série for selecionada
            self.c_serie.bind("<<ComboboxSelected>>", self.on_serie_selecionada)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar ou carregar dados: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Garante que a conexão seja fechada ao sair do contexto."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def carregar_dados_aluno(self):
        """Carrega os dados do aluno e dos responsáveis no formulário."""
        try:
            # 1. Pesquisar turma_id na tabela Matriculas usando aluno_id
            self.cursor.execute("SELECT turma_id FROM matriculas WHERE aluno_id = %s", (self.aluno_id,))
            turma_id_result = self.cursor.fetchone()
            turma_id = turma_id_result[0] if turma_id_result else None

            if turma_id:
                # 2. Pesquisar turno e serie_id na tabela Turmas usando turma_id
                self.cursor.execute("SELECT turno, serie_id FROM turmas WHERE id = %s", (turma_id,))
                turma_info = self.cursor.fetchone()
                if turma_info:
                    turno, serie_id = turma_info

                    # 3. Pesquisar nome na tabela Series usando serie_id
                    self.cursor.execute("SELECT nome FROM series WHERE id = %s", (serie_id,))
                    serie = self.cursor.fetchone()
                    if serie:
                        serie_nome = serie[0]
                    else:
                        serie_nome = "Desconhecida"
                else:
                    turno = "Desconhecido"
                    serie_nome = "Desconhecida"

            # Carregar dados do aluno
            self.cursor.execute("SELECT nome, endereco, cpf, sus, sexo, data_nascimento, raca FROM alunos WHERE id = %s", (self.aluno_id,))
            aluno = self.cursor.fetchone()
            if aluno:
                self.e_nome.delete(0, END)
                self.e_nome.insert(0, str(aluno[0]))
                self.e_endereco.delete(0, END)
                self.e_endereco.insert(0, str(aluno[1]))
                self.e_cpf.delete(0, END)
                self.e_cpf.insert(0, str(aluno[2]))
                self.e_sus.delete(0, END)
                self.e_sus.insert(0, str(aluno[3]))
                self.c_sexo.set(str(aluno[4]))
                self.c_data_nascimento.delete(0, END)
                self.c_data_nascimento.insert(0, str(aluno[5]))
                self.c_raca.set(str(aluno[6]))
                self.c_turno.set(turno)
                self.c_serie.set(serie_nome)

            # Carregar dados dos responsáveis
            self.cursor.execute(
                "SELECT r.id, r.nome, r.grau_parentesco, r.telefone, r.rg, r.cpf "
                "FROM responsaveis r "
                "JOIN responsaveisalunos ra ON r.id = ra.responsavel_id "
                "JOIN alunos a ON ra.aluno_id = a.id "
                "WHERE a.id = %s",
                (self.aluno_id,)
            )
            responsaveis = self.cursor.fetchall()

            for i, responsavel in enumerate(responsaveis):
                if i == 0:
                    self.e_nome_responsavel.delete(0, END)
                    self.e_nome_responsavel.insert(0, str(responsavel[1]))
                    self.c_parentesco.set(str(responsavel[2]))
                    self.e_telefone_responsavel.delete(0, END)
                    self.e_telefone_responsavel.insert(0, str(responsavel[3]))
                    self.e_rg_responsavel.delete(0, END)
                    self.e_rg_responsavel.insert(0, str(responsavel[4]))
                    self.e_cpf_responsavel.delete(0, END)
                    self.e_cpf_responsavel.insert(0, str(responsavel[5]))
                elif i == 1:
                    self.e_nome_responsavel_2.delete(0, END)
                    self.e_nome_responsavel_2.insert(0, str(responsavel[1]))
                    self.c_parentesco_2.set(str(responsavel[2]))
                    self.e_telefone_responsavel_2.delete(0, END)
                    self.e_telefone_responsavel_2.insert(0, str(responsavel[3]))
                    self.e_rg_responsavel_2.delete(0, END)
                    self.e_rg_responsavel_2.insert(0, str(responsavel[4]))
                    self.e_cpf_responsavel_2.delete(0, END)
                    self.e_cpf_responsavel_2.insert(0, str(responsavel[5]))

        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao carregar dados do aluno: {err}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def salvar_aluno(self):
        """Salva as alterações do aluno no banco de dados."""
        try:
            # Coletar os dados do formulário
            nome = self.e_nome.get()
            endereco = self.e_endereco.get()
            cpf = self.e_cpf.get()
            sus = self.e_sus.get()
            sexo = self.c_sexo.get()
            data_nascimento = self.c_data_nascimento.get()
            raca = self.c_raca.get()

            # Validar campos obrigatórios
            if not nome or not cpf:
                raise ValueError("Os campos 'Nome' e 'CPF' são obrigatórios.")

            # Atualizar os dados do aluno no banco de dados
            self.cursor.execute(
                """
                UPDATE alunos
                SET nome = %s, endereco = %s, cpf = %s, sus = %s, sexo = %s, data_nascimento = %s, raca = %s
                WHERE id = %s
                """,
                (nome, endereco, cpf, sus, sexo, data_nascimento, raca, self.aluno_id)
            )
            self.conn.commit()

            # Atualizar o Treeview (se necessário)
            if self.treeview and self.treeview.winfo_exists():
                atualizar_treeview(self.treeview, self.cursor, self.query)

            messagebox.showinfo("Sucesso", "Dados do aluno salvos com sucesso.")

        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao salvar dados do aluno: {err}")
        except ValueError as ve:
            messagebox.showerror("Erro", str(ve))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def salvar_responsaveis(self):
        """Salva as alterações dos responsáveis no banco de dados."""
        try:
            # Função auxiliar para salvar ou atualizar um único responsável
            def salvar_ou_atualizar_responsavel(nome, cpf, parentesco, telefone, rg):
                if not nome:  # Se o nome estiver vazio, não processa
                    return None

                # Verifica se o responsável já existe no banco de dados (usando NOME como chave)
                self.cursor.execute("SELECT id FROM responsaveis WHERE nome = %s", (nome,))
                responsavel_existente = self.cursor.fetchone()
                if responsavel_existente:
                    # Responsável já existe: atualiza os dados do responsável
                    responsavel_id = responsavel_existente[0]
                    self.cursor.execute(
                        """
                        UPDATE responsaveis
                        SET nome = %s, grau_parentesco = %s, telefone = %s, rg = %s
                        WHERE id = %s
                        """,
                        (nome, parentesco, telefone, rg, responsavel_id)
                    )
                else:
                    # Responsável não existe: insere um novo responsável
                    self.cursor.execute(
                        "INSERT INTO responsaveis (nome, grau_parentesco, telefone, rg) VALUES (%s, %s, %s, %s)",
                        (nome, parentesco, telefone, rg)
                    )
                    responsavel_id = self.cursor.lastrowid  # Pega o ID do novo responsável

                return responsavel_id

            # Associar os responsáveis ao aluno na tabela responsaveisalunos
            def associar_responsavel_aluno(responsavel_id):
                if responsavel_id:
                    # Verifica se a associação já existe
                    self.cursor.execute(
                        "SELECT id FROM responsaveisalunos WHERE responsavel_id = %s AND aluno_id = %s",
                        (responsavel_id, self.aluno_id)
                    )
                    associacao_existente = self.cursor.fetchone()

                    if not associacao_existente:
                        # Associa o responsável ao aluno na tabela responsaveisalunos (apenas se não existir)
                        self.cursor.execute(
                            "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s, %s)",
                            (responsavel_id, self.aluno_id)
                        )

            # Salvar ou atualizar o primeiro responsável
            nome_responsavel_1 = self.e_nome_responsavel.get()
            cpf_responsavel_1 = self.e_cpf_responsavel.get()  # CPF não será usado agora
            parentesco_1 = self.c_parentesco.get()
            telefone_1 = self.e_telefone_responsavel.get()
            rg_1 = self.e_rg_responsavel.get()

            responsavel_id_1 = salvar_ou_atualizar_responsavel(nome_responsavel_1, cpf_responsavel_1, parentesco_1, telefone_1, rg_1)

            # Salvar ou atualizar o segundo responsável
            nome_responsavel_2 = self.e_nome_responsavel_2.get()
            cpf_responsavel_2 = self.e_cpf_responsavel_2.get()  # CPF não será usado agora
            parentesco_2 = self.c_parentesco_2.get()
            telefone_2 = self.e_telefone_responsavel_2.get()
            rg_2 = self.e_rg_responsavel_2.get()

            responsavel_id_2 = salvar_ou_atualizar_responsavel(nome_responsavel_2, cpf_responsavel_2, parentesco_2, telefone_2, rg_2)

            # Associar o primeiro responsável ao aluno
            associar_responsavel_aluno(responsavel_id_1)

            # Associar o segundo responsável ao aluno
            associar_responsavel_aluno(responsavel_id_2)

            self.conn.commit()
            messagebox.showinfo("Sucesso", "Dados dos responsáveis salvos com sucesso!")

        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao salvar dados dos responsáveis: {err}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def salvar_tudo(self):
        """Salva os dados do aluno e dos responsáveis."""
        try:
            self.salvar_aluno()
            self.salvar_responsaveis()
            messagebox.showinfo("Sucesso", "Dados do aluno e dos responsáveis salvos com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar os dados: {e}")

    def carregar_series(self):
        """Carrega as séries no combobox."""
        try:
            series = self.obter_series()
            self.c_serie['values'] = [serie[1] for serie in series]
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar séries: {e}")

    def obter_series(self):
        """Obtém a lista de séries do banco de dados."""
        try:
            # Consulta para obter séries vinculadas ao ano letivo 2025
            self.cursor.execute("""
                SELECT s.id, s.nome
                FROM series s
                JOIN turmas t ON s.id = t.serie_id
                JOIN anosletivos a ON t.ano_letivo_id = a.id
                WHERE a.ano_letivo = %s
                GROUP BY s.id, s.nome
            """, (2025,))
            series = self.cursor.fetchall()
            logger.debug("Séries obtidas: %s", series)
            return series
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao obter séries: {err}")
            return []

    def carregar_turmas(self, serie_nome):
        """Carrega as turmas no combobox com base na série selecionada."""
        try:
            self.cursor.execute("SELECT id FROM series WHERE nome = %s", (serie_nome,))
            serie_result = self.cursor.fetchone()
            if serie_result:
                serie_id = serie_result[0]
            else:
                messagebox.showerror("Erro", "Série não encontrada.")
                return

            turmas = self.obter_turmas(serie_id)
            self.c_turno['values'] = [turma[0] for turma in turmas]

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar turmas: {e}")

    def obter_turmas(self, serie_id):
        """Obtém a lista de turmas para uma série específica do banco de dados."""
        try:
            # Consulta para obter turmas vinculadas à série e ao ano letivo 2025
            self.cursor.execute("""
                SELECT t.nome, t.turno
                FROM turmas t
                JOIN anosletivos a ON t.ano_letivo_id = a.id
                WHERE t.serie_id = %s AND a.ano_letivo = %s
            """, (serie_id, 2025))
            turmas = self.cursor.fetchall()
            logger.debug("Turmas obtidas para a série %s: %s", serie_id, turmas)
            return turmas
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao obter turmas: {err}")
            return []

    def obter_turno(self, turma_nome, serie_id):
        """Obtém o turno de uma turma específica do banco de dados."""
        try:
            # Consulta para obter turnos vinculados à turma, série e ano letivo 2025
            if turma_nome:
                self.cursor.execute("""
                    SELECT t.turno
                    FROM turmas t
                    JOIN anosletivos a ON t.ano_letivo_id = a.id
                    WHERE t.nome = %s AND t.serie_id = %s AND a.ano_letivo = %s
                """, (turma_nome, serie_id, 2025))
            else:
                self.cursor.execute("""
                    SELECT DISTINCT t.turno
                    FROM turmas t
                    JOIN anosletivos a ON t.ano_letivo_id = a.id
                    WHERE t.serie_id = %s AND a.ano_letivo = %s
                """, (serie_id, 2025))
            turno = self.cursor.fetchone()
            return turno[0] if turno else None
        except mysql.connector.Error as err:
            messagebox.showerror("Erro", f"Erro ao obter turno: {err}")
            return None

    def on_serie_selecionada(self, event=None):
        """
        Carrega as turmas quando uma série é selecionada no combobox.
        """
        serie_nome = self.c_serie.get()
        if serie_nome:
            self.carregar_turmas(serie_nome)
