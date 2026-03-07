"""
Interface gráfica para comparação e importação de alunos do GEDUC.

Fluxo:
1. Lê o arquivo JSON gerado pelo scripts/migracao/importar_geduc.py
2. Compara com matrículas ativas do ano letivo corrente (escola_id=60)
3. Exibe lista de alunos presentes no GEDUC mas sem matrícula local
4. Permite selecionar e inserir os alunos escolhidos no banco local
   (com normalização de dados e responsáveis)
"""

import os
import re
import sys
import json
import logging
import unicodedata
import threading
import queue as _queue_mod
from pathlib import Path
from typing import Optional, Dict, List

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ─── caminho raiz ──────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from db.connection import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# ─── cores padrão do sistema ──────────────────────────────────────────────────
CO0 = "#F5F5F5"   # fundo
CO1 = "#003A70"   # azul escuro
CO2 = "#77B341"   # verde
CO3 = "#E74C3C"   # vermelho
CO4 = "#4A86E8"   # azul claro
CO_LINHA_PAR  = "#EBF3FA"
CO_LINHA_IMPAR = "#FFFFFF"

# ─── mapeamentos ──────────────────────────────────────────────────────────────
_PREPOSICOES = {'de', 'da', 'das', 'do', 'dos', 'e', 'em', 'a', 'o', 'ao'}

MAPA_SEXO = {'1': 'M', '2': 'F', 'M': 'M', 'F': 'F'}

MAPA_RACA_ENUM = {
    'Branca': 'branco', 'Preta': 'preto', 'Parda': 'pardo',
    'Amarela': 'amarelo', 'Indígena': 'indígena', 'Não declarada': 'pardo',
}

JSON_PADRAO = str(ROOT_DIR / 'alunos_geduc.json')


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _normalizar(nome: str) -> str:
    if not nome:
        return ''
    nome = unicodedata.normalize('NFKD', str(nome)).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', nome.strip().upper())


def _capitalizar(nome: str) -> str:
    if not nome:
        return ''
    return ' '.join(
        p.capitalize() if i == 0 or p.lower() not in _PREPOSICOES else p.lower()
        for i, p in enumerate(nome.strip().split())
    )


def _formatar_cpf(cpf: str) -> Optional[str]:
    if not cpf:
        return None
    d = re.sub(r'\D', '', str(cpf))
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else (d or None)


def _formatar_tel(tel: str) -> str:
    if not tel:
        return ''
    d = re.sub(r'\D', '', str(tel))
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return tel


class _LogCapture(logging.Handler):
    """Repassa registros de log para uma Queue — usada para exibir progresso na UI."""

    def __init__(self, q: _queue_mod.Queue):
        super().__init__()
        self._q = q

    def emit(self, record: logging.LogRecord):
        try:
            self._q.put_nowait(self.format(record))
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  LÓGICA DE COMPARAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def carregar_json_geduc(caminho: str) -> Dict:
    """Carrega e valida o arquivo JSON do GEDUC."""
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    if 'turmas' not in dados:
        raise ValueError("Formato de JSON inválido: chave 'turmas' ausente.")
    return dados


def obter_alunos_locais_ativos(escola_id: int = 60) -> Dict[str, int]:
    """
    Retorna dicionário {nome_normalizado: aluno_id} de todos os alunos
    com matrícula ativa no ano letivo corrente da escola informada.
    """
    conn = conectar_bd()
    cursor = conn.cursor(buffered=True)
    try:
        # Obter ano letivo corrente (maior ano_letivo ativo)
        cursor.execute(
            "SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1"
        )
        row = cursor.fetchone()
        ano_letivo_id = row[0] if row else None

        if not ano_letivo_id:
            return {}

        cursor.execute("""
            SELECT a.id, a.nome
            FROM alunos a
            INNER JOIN matriculas m ON m.aluno_id = a.id
            WHERE m.status = 'Ativo'
              AND m.ano_letivo_id = %s
              AND a.escola_id = %s
        """, (ano_letivo_id, escola_id))
        return {_normalizar(nome): aid for aid, nome in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def comparar_geduc_local(dados_json: Dict, escola_id: int = 60) -> List[Dict]:
    """
    Retorna lista de alunos presentes no GEDUC mas sem matrícula ativa local.
    Cada item contém os dados normalizados prontos para exibição e inserção.
    """
    locais = obter_alunos_locais_ativos(escola_id)
    apenas_geduc = []

    for turma in dados_json.get('turmas', []):
        turma_id_geduc = turma.get('id', '')
        turma_nome_geduc = turma.get('nome', '')

        for aluno in turma.get('alunos', []):
            nome_norm = _normalizar(aluno.get('nome', ''))
            if not nome_norm:
                continue
            if nome_norm in locais:
                continue  # já está no sistema

            apenas_geduc.append({
                'nome_geduc':        aluno.get('nome', ''),
                'nome_normalizado':  nome_norm,
                'nome_fmt':          _capitalizar(aluno.get('nome', '')),
                'data_nascimento':   aluno.get('data_nascimento', ''),
                'sexo_raw':          str(aluno.get('sexo', '1')),
                'sexo':              MAPA_SEXO.get(str(aluno.get('sexo', '1')), 'M'),
                'cpf_raw':           aluno.get('cpf', ''),
                'cpf_fmt':           _formatar_cpf(aluno.get('cpf', '')),
                'raca':              aluno.get('raca', 'Não declarada'),
                'raca_enum':         MAPA_RACA_ENUM.get(aluno.get('raca', 'Não declarada'), 'pardo'),
                'celular':           _formatar_tel(aluno.get('celular', '')),
                'email':             aluno.get('email', ''),
                'mae':               aluno.get('mae', ''),
                'cpf_mae':           aluno.get('cpf_mae', ''),
                'profissao_mae':     aluno.get('profissao_mae', ''),
                'pai':               aluno.get('pai', ''),
                'cpf_pai':           aluno.get('cpf_pai', ''),
                'profissao_pai':     aluno.get('profissao_pai', ''),
                'outros_nome':       aluno.get('outros_nome', ''),
                'outros_cpf':        aluno.get('outros_cpf', ''),
                'responsavel_tipo':  aluno.get('responsavel_tipo', ''),
                'cid':               aluno.get('cid', ''),
                'tgd':               aluno.get('tgd', '0'),
                'althab':            aluno.get('althab', '0'),
                'descricao_transtorno': aluno.get('descricao_transtorno', 'Nenhum'),
                'inep_escola':       aluno.get('inep_escola', ''),
                'turma_geduc_id':    turma_id_geduc,
                'turma_geduc_nome':  turma_nome_geduc,
            })

    return apenas_geduc


# ══════════════════════════════════════════════════════════════════════════════
#  INSERÇÃO NO BANCO
# ══════════════════════════════════════════════════════════════════════════════

def _inserir_responsavel(cursor, nome: str, cpf: str, telefone: str,
                         parentesco: str) -> Optional[int]:
    cpf_fmt = _formatar_cpf(cpf) if cpf else None
    nome_fmt = _capitalizar(nome) if nome else None
    if not nome_fmt:
        return None

    # Verificar por CPF
    if cpf_fmt:
        cursor.execute("SELECT id FROM responsaveis WHERE cpf = %s", (cpf_fmt,))
        r = cursor.fetchone()
        if r:
            return r[0]

    # Verificar por nome normalizado
    nome_norm = _normalizar(nome_fmt)
    cursor.execute("SELECT id, nome FROM responsaveis")
    for rid, rnome in cursor.fetchall():
        if _normalizar(rnome) == nome_norm:
            return rid

    # Inserir novo
    cursor.execute(
        "INSERT INTO responsaveis (nome, cpf, telefone, grau_parentesco) VALUES (%s,%s,%s,%s)",
        (nome_fmt, cpf_fmt, telefone or '', parentesco)
    )
    return cursor.lastrowid


def inserir_aluno_geduc(dados: Dict, escola_id: int = 60,
                        turma_id_local: Optional[int] = None,
                        ano_letivo_id: Optional[int] = None) -> Dict:
    """
    Insere um aluno GEDUC no banco local.
    Retorna dict com 'sucesso', 'aluno_id', 'mat_id', 'mensagem'.
    """
    conn = conectar_bd()
    cursor = conn.cursor(buffered=True)
    try:
        # Obter ano letivo corrente se não fornecido
        if not ano_letivo_id:
            cursor.execute(
                "SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1"
            )
            row = cursor.fetchone()
            ano_letivo_id = row[0] if row else None
            if not ano_letivo_id:
                return {'sucesso': False, 'mensagem': 'Nenhum ano letivo cadastrado.'}

        # Inserir aluno
        cursor.execute("""
            INSERT INTO alunos
                (nome, data_nascimento, sexo, cpf, raca,
                 descricao_transtorno, escola_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            dados['nome_fmt'],
            dados['data_nascimento'] or None,
            dados['sexo'],
            dados['cpf_fmt'],
            dados['raca_enum'],
            dados.get('descricao_transtorno', 'Nenhum'),
            escola_id,
        ))
        aluno_id = cursor.lastrowid

        # Matricular se turma informada
        mat_id = None
        if turma_id_local and ano_letivo_id:
            cursor.execute("""
                INSERT INTO matriculas
                    (aluno_id, turma_id, data_matricula, ano_letivo_id, status)
                VALUES (%s, %s, CURDATE(), %s, 'Ativo')
            """, (aluno_id, turma_id_local, ano_letivo_id))
            mat_id = cursor.lastrowid

        # Responsáveis
        resp_tipo = dados.get('responsavel_tipo', '0')
        celular = dados.get('celular', '')

        if dados.get('mae'):
            rid = _inserir_responsavel(
                cursor, dados['mae'], dados.get('cpf_mae', ''),
                celular if resp_tipo == '0' else '', 'Mãe'
            )
            if rid:
                cursor.execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s,%s)",
                    (rid, aluno_id)
                )

        if dados.get('pai'):
            rid = _inserir_responsavel(
                cursor, dados['pai'], dados.get('cpf_pai', ''),
                celular if resp_tipo == '1' else '', 'Pai'
            )
            if rid:
                cursor.execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s,%s)",
                    (rid, aluno_id)
                )

        if dados.get('outros_nome'):
            rid = _inserir_responsavel(
                cursor, dados['outros_nome'], dados.get('outros_cpf', ''),
                celular if resp_tipo == '2' else '', 'Outro Responsável'
            )
            if rid:
                cursor.execute(
                    "INSERT INTO responsaveisalunos (responsavel_id, aluno_id) VALUES (%s,%s)",
                    (rid, aluno_id)
                )

        conn.commit()
        return {
            'sucesso': True,
            'aluno_id': aluno_id,
            'mat_id': mat_id,
            'mensagem': f"Inserido com ID {aluno_id}" + (f", matrícula {mat_id}" if mat_id else ""),
        }

    except Exception as e:
        conn.rollback()
        logger.exception(f"Erro ao inserir aluno {dados.get('nome_geduc')}: {e}")
        return {'sucesso': False, 'mensagem': str(e)}
    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  INTERFACE GRÁFICA
# ══════════════════════════════════════════════════════════════════════════════

class InterfaceImportarAlunosGEDUC:
    """
    Janela que compara o JSON do GEDUC com o sistema local e permite
    selecionar e importar os alunos ausentes.
    """

    def __init__(self, janela_pai=None):
        self.janela_pai = janela_pai

        # Janela principal
        if janela_pai:
            self.janela = tk.Toplevel(janela_pai)
        else:
            self.janela = tk.Tk()

        self.janela.title("Importar Alunos do GEDUC")
        self.janela.geometry("1100x760")
        self.janela.configure(bg=CO0)
        self.janela.protocol("WM_DELETE_WINDOW", self._ao_fechar)

        # Centralizar
        self.janela.update_idletasks()
        w, h = 1100, 760
        x = (self.janela.winfo_screenwidth() - w) // 2
        y = (self.janela.winfo_screenheight() - h) // 2
        self.janela.geometry(f"{w}x{h}+{x}+{y}")

        # Estado interno
        self._alunos: List[Dict] = []
        self._vars_sel: List[tk.BooleanVar] = []
        self._turmas_locais: List[Dict] = []
        self._ano_letivo_id: Optional[int] = None
        self._arquivo_json = tk.StringVar(value=JSON_PADRAO)

        self._carregar_turmas_locais()
        self._construir_ui()
        # Inicia polling de log (roda durante toda a vida da janela)
        self.janela.after(300, self._poll_log_queue)

        if janela_pai:
            self.janela.grab_set()
            self.janela.focus_force()

    # ──────────────────────────────── DADOS ──────────────────────────────────

    def _carregar_turmas_locais(self):
        try:
            conn = conectar_bd()
            cursor = conn.cursor(buffered=True)
            cursor.execute(
                "SELECT id FROM anosletivos ORDER BY ano_letivo DESC LIMIT 1"
            )
            row = cursor.fetchone()
            self._ano_letivo_id = row[0] if row else None

            cursor.execute("""
                SELECT t.id, CONCAT(s.nome, CASE WHEN t.nome != '' THEN CONCAT(' ', t.nome) ELSE '' END,
                       ' - ', t.turno) AS descricao
                FROM turmas t
                JOIN series s ON s.id = t.serie_id
                WHERE t.escola_id = 60
                ORDER BY s.nome, t.nome, t.turno
            """)
            self._turmas_locais = [{'id': tid, 'desc': desc} for tid, desc in cursor.fetchall()]
            cursor.close()
            conn.close()
        except Exception as e:
            logger.exception(f"Erro ao carregar turmas: {e}")
            self._turmas_locais = []

    # ──────────────────────────────── UI ─────────────────────────────────────

    def _construir_ui(self):
        # ── cabeçalho ──
        frame_cabecalho = tk.Frame(self.janela, bg=CO1, pady=8)
        frame_cabecalho.pack(fill=tk.X)

        tk.Label(
            frame_cabecalho,
            text="📥  Importar Alunos do GEDUC",
            font=("Arial", 15, "bold"),
            bg=CO1, fg="white",
        ).pack(side=tk.LEFT, padx=20)

        # ══ Etapa 1: Extrair do GEDUC ══
        frame_extr = tk.LabelFrame(
            self.janela,
            text=" ① Extrair dados do GEDUC (Selenium) ",
            font=("Arial", 9, "bold"), bg=CO0, fg=CO1, pady=4, padx=8,
        )
        frame_extr.pack(fill=tk.X, padx=15, pady=(6, 2))

        tk.Label(frame_extr, text="Usuário:", font=("Arial", 9), bg=CO0).grid(
            row=0, column=0, sticky="e", padx=(0, 3), pady=2)
        self._var_usuario = tk.StringVar()
        tk.Entry(frame_extr, textvariable=self._var_usuario,
                 font=("Arial", 10), width=20).grid(row=0, column=1, padx=2, pady=2, sticky="w")

        tk.Label(frame_extr, text="Senha:", font=("Arial", 9), bg=CO0).grid(
            row=0, column=2, sticky="e", padx=(12, 3), pady=2)
        self._var_senha = tk.StringVar()
        tk.Entry(frame_extr, textvariable=self._var_senha,
                 font=("Arial", 10), width=20, show="*").grid(row=0, column=3, padx=2, pady=2, sticky="w")

        self._btn_extrair = tk.Button(
            frame_extr, text="▶  Extrair do GEDUC",
            command=self._extrair_do_geduc,
            bg=CO2, fg="white", font=("Arial", 9, "bold"), cursor="hand2", padx=10)
        self._btn_extrair.grid(row=0, column=4, padx=(14, 4), pady=4)

        tk.Label(
            frame_extr,
            text="Abre o Chrome, faz login no GEDUC e coleta todos os alunos → salva em alunos_geduc.json",
            font=("Arial", 8, "italic"), bg=CO0, fg="#666666",
        ).grid(row=1, column=0, columnspan=5, sticky="w", padx=2, pady=(0, 2))

        # ══ Etapa 2: Comparar e Importar ══
        frame_etapa2 = tk.LabelFrame(
            self.janela,
            text=" ② Comparar e importar ",
            font=("Arial", 9, "bold"), bg=CO0, fg=CO1, pady=4, padx=8,
        )
        frame_etapa2.pack(fill=tk.X, padx=15, pady=(2, 0))

        # ── seleção de arquivo ──
        frame_arq = tk.Frame(frame_etapa2, bg=CO0)
        frame_arq.pack(fill=tk.X)

        tk.Label(frame_arq, text="Arquivo JSON:", font=("Arial", 10, "bold"),
                 bg=CO0, fg=CO1).pack(side=tk.LEFT)

        tk.Entry(frame_arq, textvariable=self._arquivo_json,
                 font=("Arial", 10), width=55).pack(side=tk.LEFT, padx=6)

        tk.Button(frame_arq, text="Procurar", command=self._selecionar_arquivo,
                  bg=CO4, fg="white", font=("Arial", 9, "bold"),
                  cursor="hand2").pack(side=tk.LEFT, padx=4)

        tk.Button(frame_arq, text="🔍 Comparar", command=self._comparar,
                  bg=CO1, fg="white", font=("Arial", 10, "bold"),
                  cursor="hand2", height=1, padx=10).pack(side=tk.LEFT, padx=8)

        # ── turma de destino ──
        frame_turma = tk.Frame(frame_etapa2, bg=CO0, pady=2)
        frame_turma.pack(fill=tk.X)

        tk.Label(frame_turma, text="Turma de destino (para matrícula):",
                 font=("Arial", 10, "bold"), bg=CO0, fg=CO1).pack(side=tk.LEFT)

        self._var_turma = tk.StringVar()
        opcoes_turma = ["— Não matricular —"] + [t['desc'] for t in self._turmas_locais]
        self._combo_turma = ttk.Combobox(
            frame_turma, textvariable=self._var_turma,
            values=opcoes_turma, state="readonly", width=45, font=("Arial", 10)
        )
        self._combo_turma.current(0)
        self._combo_turma.pack(side=tk.LEFT, padx=8)

        # ── status ──
        self._var_status = tk.StringVar(value="Preencha as credenciais e clique em ▶ Extrair, ou carregue um JSON existente.")
        self._lbl_status = tk.Label(
            self.janela, textvariable=self._var_status,
            font=("Arial", 9, "italic"), bg=CO0, fg="#555555", anchor="w"
        )
        self._lbl_status.pack(fill=tk.X, padx=15)

        # ── tabela ──
        frame_tabela = tk.Frame(self.janela, bg=CO0)
        frame_tabela.pack(fill=tk.BOTH, expand=True, padx=15, pady=(4, 0))

        colunas = ("sel", "nome", "nasc", "sexo", "cpf", "raca", "turma_geduc", "mae", "pai", "transtorno")
        larguras = (30, 260, 90, 50, 110, 70, 150, 200, 200, 130)
        titulos  = (" ", "Nome", "Nascimento", "Sexo", "CPF", "Raça",
                    "Turma GEDUC", "Mãe", "Pai", "Transtorno")

        self._tree = ttk.Treeview(
            frame_tabela, columns=colunas, show="headings",
            selectmode="browse", height=18
        )
        for col, larg, tit in zip(colunas, larguras, titulos):
            self._tree.heading(col, text=tit)
            self._tree.column(col, width=larg, minwidth=larg, anchor="w" if larg > 50 else "center")

        self._tree.tag_configure("par",  background=CO_LINHA_PAR)
        self._tree.tag_configure("impar", background=CO_LINHA_IMPAR)
        self._tree.tag_configure("selecionado", background="#D4EDDA")

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self._tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        frame_tabela.rowconfigure(0, weight=1)
        frame_tabela.columnconfigure(0, weight=1)

        self._tree.bind("<Button-1>", self._toggle_selecao)

        # ── rodapé com botões ──
        frame_botoes = tk.Frame(self.janela, bg=CO0, pady=8)
        frame_botoes.pack(fill=tk.X, padx=15)

        self._lbl_contagem = tk.Label(
            frame_botoes, text="", font=("Arial", 10), bg=CO0, fg=CO1
        )
        self._lbl_contagem.pack(side=tk.LEFT)

        tk.Button(
            frame_botoes, text="✅ Selecionar Todos", command=self._selecionar_todos,
            bg=CO4, fg="white", font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT, padx=6)

        tk.Button(
            frame_botoes, text="☐ Desmarcar Todos", command=self._desmarcar_todos,
            bg="#95A5A6", fg="white", font=("Arial", 9, "bold"), cursor="hand2"
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            frame_botoes, text="📥 Inserir Selecionados no Sistema",
            command=self._inserir_selecionados,
            bg=CO2, fg="white", font=("Arial", 11, "bold"),
            cursor="hand2", padx=12, pady=4
        ).pack(side=tk.RIGHT, padx=6)

        tk.Button(
            frame_botoes, text="Fechar", command=self._ao_fechar,
            bg=CO3, fg="white", font=("Arial", 10, "bold"), cursor="hand2"
        ).pack(side=tk.RIGHT, padx=4)

        # ── log ──
        frame_log = tk.Frame(self.janela, bg=CO0)
        frame_log.pack(fill=tk.X, padx=15, pady=(0, 6))

        self._txt_log = tk.Text(
            frame_log, height=4, font=("Consolas", 8),
            bg="#F0F0F0", fg="#333333", state=tk.DISABLED, wrap="word"
        )
        log_scroll = ttk.Scrollbar(frame_log, orient="vertical", command=self._txt_log.yview)
        self._txt_log.configure(yscrollcommand=log_scroll.set)
        self._txt_log.pack(side=tk.LEFT, fill=tk.X, expand=True)
        log_scroll.pack(side=tk.LEFT, fill=tk.Y)

    # ──────────────────────────────── AÇÕES ──────────────────────────────────

    def _extrair_do_geduc(self):
        """Inicia extração do GEDUC via Selenium e exibe progresso em tempo real."""
        usuario = self._var_usuario.get().strip()
        senha = self._var_senha.get().strip()
        if not usuario or not senha:
            messagebox.showerror("Credenciais ausentes",
                                 "Informe o usuário e a senha do GEDUC.",
                                 parent=self.janela)
            return

        arquivo_saida = self._arquivo_json.get().strip() or JSON_PADRAO

        self._btn_extrair.config(state=tk.DISABLED, text="Extraindo…")
        self._var_status.set("Extração iniciada — o Chrome será aberto automaticamente. Aguarde.")
        self._log("=" * 60)
        self._log(f"Iniciando extração do GEDUC → {arquivo_saida}")

        # Criar fila + handler para capturar logs do módulo Selenium
        self._log_queue: _queue_mod.Queue = _queue_mod.Queue()
        handler = _LogCapture(self._log_queue)
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%H:%M:%S'))
        root_log = logging.getLogger()
        root_log.addHandler(handler)
        self._log_handler = handler

        def _executar():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "importar_geduc",
                    ROOT_DIR / "scripts" / "migracao" / "importar_geduc.py",
                )
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[arg-type]
                mod.extrair_alunos_geduc(usuario, senha, arquivo_saida=arquivo_saida)
            except Exception as e:
                logger.exception(f"Erro na extração GEDUC: {e}")
            finally:
                root_log.removeHandler(self._log_handler)
                self.janela.after(0, lambda: self._extracao_concluida(arquivo_saida))

        threading.Thread(target=_executar, daemon=True).start()

    def _poll_log_queue(self):
        """Drena a fila de logs gerados por _LogCapture e exibe na área de log."""
        if hasattr(self, '_log_queue'):
            try:
                while True:
                    msg = self._log_queue.get_nowait()
                    self._log(msg)
            except _queue_mod.Empty:
                pass
        # Reagendar enquanto a janela existir
        try:
            self.janela.after(250, self._poll_log_queue)
        except tk.TclError:
            pass  # janela já destruída

    def _extracao_concluida(self, arquivo_saida: str):
        """Chamado quando a thread de extração termina."""
        self._btn_extrair.config(state=tk.NORMAL, text="▶  Extrair do GEDUC")
        self._arquivo_json.set(arquivo_saida)
        self._log("=" * 60)
        self._log("Extração concluída. Iniciando comparação automática…")
        self._var_status.set("Extração concluída! Comparando com o sistema local…")
        self._comparar()

    def _selecionar_arquivo(self):
        path = filedialog.askopenfilename(
            title="Selecionar arquivo JSON do GEDUC",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            parent=self.janela,
        )
        if path:
            self._arquivo_json.set(path)

    def _comparar(self):
        caminho = self._arquivo_json.get().strip()
        if not caminho or not os.path.exists(caminho):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{caminho}", parent=self.janela)
            return

        self._var_status.set("Comparando... aguarde.")
        self.janela.update()

        def executar():
            try:
                dados = carregar_json_geduc(caminho)
                alunos = comparar_geduc_local(dados, escola_id=60)
                self.janela.after(0, lambda: self._exibir_resultado(alunos, dados))
            except Exception as e:
                self.janela.after(0, lambda: self._var_status.set(f"Erro: {e}"))
                logger.exception(f"Erro na comparação: {e}")

        threading.Thread(target=executar, daemon=True).start()

    def _exibir_resultado(self, alunos: List[Dict], dados_json: Dict):
        self._alunos = alunos
        self._selecionados = set()

        # Limpar tabela
        for item in self._tree.get_children():
            self._tree.delete(item)

        total_geduc = dados_json.get('total_alunos', 0)
        data_extr   = dados_json.get('data_extracao', '')[:10] if dados_json.get('data_extracao') else ''

        for i, a in enumerate(alunos):
            tag = "par" if i % 2 == 0 else "impar"
            self._tree.insert("", "end", iid=str(i), tags=(tag,), values=(
                "☐",
                a['nome_fmt'],
                a['data_nascimento'],
                a['sexo'],
                a['cpf_fmt'] or '',
                a['raca'],
                f"{a['turma_geduc_nome'] or ''} (ID {a['turma_geduc_id']})".strip(),
                _capitalizar(a['mae']) if a.get('mae') else '',
                _capitalizar(a['pai']) if a.get('pai') else '',
                a.get('descricao_transtorno', 'Nenhum'),
            ))

        n = len(alunos)
        self._lbl_contagem.config(
            text=f"{n} aluno{'s' if n != 1 else ''} no GEDUC sem matrícula local"
        )
        self._var_status.set(
            f"JSON: {os.path.basename(caminho := self._arquivo_json.get())} | "
            f"Extração: {data_extr} | Total GEDUC: {total_geduc} | "
            f"Faltando no sistema: {n}"
        )
        self._log(f"Comparação concluída: {n} alunos faltando no sistema local.")

    def _toggle_selecao(self, event):
        region = self._tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self._tree.identify_row(event.y)
        if not row_id:
            return
        try:
            idx = int(row_id)
        except ValueError:
            return

        if idx in self._selecionados:
            self._selecionados.discard(idx)
            vals = list(self._tree.item(row_id, "values"))
            vals[0] = "☐"
            tag = "par" if idx % 2 == 0 else "impar"
            self._tree.item(row_id, values=vals, tags=(tag,))
        else:
            self._selecionados.add(idx)
            vals = list(self._tree.item(row_id, "values"))
            vals[0] = "☑"
            self._tree.item(row_id, values=vals, tags=("selecionado",))

        self._lbl_contagem.config(
            text=f"{len(self._alunos)} no GEDUC sem matrícula | "
                 f"{len(self._selecionados)} selecionados"
        )

    def _selecionar_todos(self):
        if not hasattr(self, '_selecionados'):
            self._selecionados = set()
        for i in range(len(self._alunos)):
            self._selecionados.add(i)
            vals = list(self._tree.item(str(i), "values"))
            vals[0] = "☑"
            self._tree.item(str(i), values=vals, tags=("selecionado",))
        self._lbl_contagem.config(
            text=f"{len(self._alunos)} no GEDUC | {len(self._selecionados)} selecionados"
        )

    def _desmarcar_todos(self):
        if not hasattr(self, '_selecionados'):
            self._selecionados = set()
            return
        for i in self._selecionados:
            vals = list(self._tree.item(str(i), "values"))
            vals[0] = "☐"
            tag = "par" if i % 2 == 0 else "impar"
            self._tree.item(str(i), values=vals, tags=(tag,))
        self._selecionados.clear()
        self._lbl_contagem.config(
            text=f"{len(self._alunos)} no GEDUC | 0 selecionados"
        )

    def _inserir_selecionados(self):
        if not hasattr(self, '_selecionados') or not self._selecionados:
            messagebox.showwarning("Atenção", "Selecione ao menos um aluno.", parent=self.janela)
            return

        # Turma de destino
        idx_turma = self._combo_turma.current()
        turma_id_local = None
        if idx_turma > 0:
            turma_id_local = self._turmas_locais[idx_turma - 1]['id']

        alunos_sel = [self._alunos[i] for i in sorted(self._selecionados)]
        n = len(alunos_sel)

        confirmacao = messagebox.askyesno(
            "Confirmar Inserção",
            f"Inserir {n} aluno{'s' if n != 1 else ''} no sistema local?\n\n"
            + (f"Turma de matrícula: {self._var_turma.get()}\n" if turma_id_local else "Sem matrícula automática.\n")
            + "\nOs dados serão normalizados antes da inserção.",
            parent=self.janela,
        )
        if not confirmacao:
            return

        self._var_status.set("Inserindo alunos... aguarde.")
        self.janela.update()

        def executar():
            ok, erros = 0, 0
            for dados in alunos_sel:
                resultado = inserir_aluno_geduc(
                    dados,
                    escola_id=60,
                    turma_id_local=turma_id_local,
                    ano_letivo_id=self._ano_letivo_id,
                )
                if resultado['sucesso']:
                    ok += 1
                    self.janela.after(
                        0, lambda d=dados, r=resultado:
                        self._log(f"[OK] {d['nome_fmt']} — {r['mensagem']}")
                    )
                else:
                    erros += 1
                    self.janela.after(
                        0, lambda d=dados, r=resultado:
                        self._log(f"[ERRO] {d['nome_fmt']} — {r['mensagem']}")
                    )

            self.janela.after(0, lambda: self._pos_insercao(ok, erros))

        threading.Thread(target=executar, daemon=True).start()

    def _pos_insercao(self, ok: int, erros: int):
        self._var_status.set(f"Inserção concluída: {ok} inseridos, {erros} erros.")
        msg = f"Inserção concluída!\n\n✅ Inseridos: {ok}\n❌ Erros: {erros}"
        if erros:
            messagebox.showwarning("Resultado", msg, parent=self.janela)
        else:
            messagebox.showinfo("Resultado", msg, parent=self.janela)

        # Recomparar para atualizar a lista
        self._comparar()

    def _log(self, msg: str):
        self._txt_log.configure(state=tk.NORMAL)
        self._txt_log.insert(tk.END, msg + "\n")
        self._txt_log.see(tk.END)
        self._txt_log.configure(state=tk.DISABLED)

    def _ao_fechar(self):
        if self.janela_pai:
            self.janela_pai.deiconify()
        self.janela.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def abrir_importacao_alunos_geduc(janela_pai=None):
    """
    Abre a interface de importação de alunos do GEDUC.
    Se janela_pai for fornecida, ela será ocultada durante o uso e
    restaurada ao fechar.
    """
    try:
        if janela_pai:
            janela_pai.withdraw()
        InterfaceImportarAlunosGEDUC(janela_pai=janela_pai)
    except Exception as e:
        logger.exception(f"Erro ao abrir importação de alunos GEDUC: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir interface:\n{e}")
        if janela_pai:
            janela_pai.deiconify()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    InterfaceImportarAlunosGEDUC(janela_pai=root)
    root.mainloop()
