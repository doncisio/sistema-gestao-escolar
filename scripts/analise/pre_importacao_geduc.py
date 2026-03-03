"""
Análise PRÉ-IMPORTAÇÃO do GEDUC
Simula exatamente o que importar_geduc.py fará, sem modificar nada no banco.
"""
import json
import sys
import re
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db.connection import conectar_bd


def normalizar_nome(nome: str) -> str:
    """Mesma lógica usada no importador"""
    if not nome:
        return ""
    nome_sem_acento = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nome_sem_acento if not unicodedata.combining(c)])
    nome_upper = nome_sem_acento.upper()
    nome_limpo = re.sub(r'[^A-Z\s]', '', nome_upper)
    return ' '.join(nome_limpo.split())


def main():
    arquivo_json = 'alunos_geduc.json'

    print("=" * 80)
    print("PRÉ-ANÁLISE DE IMPORTAÇÃO DO GEDUC")
    print("(Simulação — nenhum dado será alterado)")
    print("=" * 80)

    # Carregar JSON
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {arquivo_json}")
        return

    # Listar todos dos alunos do JSON por turma
    alunos_geduc = []
    for turma in dados.get('turmas', []):
        for aluno in turma.get('alunos', []):
            alunos_geduc.append({
                'nome': aluno['nome'],
                'nome_normalizado': aluno.get('nome_normalizado') or normalizar_nome(aluno['nome']),
                'cpf': (aluno.get('cpf') or '').strip(),
                'data_nascimento': aluno.get('data_nascimento'),
                'raca': aluno.get('raca'),
                'transtorno': aluno.get('descricao_transtorno', 'Nenhum'),
                'inep_escola': aluno.get('inep_escola'),
                'turma': turma['nome'],
            })

    print(f"\n📄 Arquivo: {arquivo_json}")
    print(f"📅 Data extração: {dados.get('data_extracao', 'N/A')}")
    print(f"📚 Turmas: {len(dados.get('turmas', []))}")
    print(f"👥 Total alunos no arquivo: {len(alunos_geduc)}")

    # Conectar BD
    conn = conectar_bd()
    if not conn:
        print("❌ Sem conexão com o banco!")
        return

    cursor = conn.cursor()

    # Carregar TODOS os alunos do banco (mesma lógica do importador)
    cursor.execute("SELECT id, nome FROM alunos")
    alunos_banco = cursor.fetchall()

    nomes_banco = {}  # nome_normalizado -> (id, nome_original)
    for aluno_id, nome in alunos_banco:
        chave = normalizar_nome(nome)
        nomes_banco[chave] = (aluno_id, nome)

    # Buscar ano letivo 2026
    cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2026 LIMIT 1")
    row = cursor.fetchone()
    ano_letivo_id = row[0] if row else None

    if ano_letivo_id:
        cursor.execute("""
            SELECT m.aluno_id, t.nome as turma, m.status
            FROM matriculas m
            LEFT JOIN turmas t ON m.turma_id = t.id
            WHERE m.ano_letivo_id = %s
        """, (ano_letivo_id,))
        matriculas_2026 = {row[0]: {'turma': row[1], 'status': row[2]} for row in cursor.fetchall()}
    else:
        matriculas_2026 = {}

    # Buscar escolas por INEP
    cursor.execute("SELECT id, inep, nome FROM escolas WHERE inep IS NOT NULL")
    escolas_por_inep = {row[1]: (row[0], row[2]) for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    # ---- Classificar cada aluno ----
    novos = []
    sem_nascimento = []
    duplicados = []

    for aluno in alunos_geduc:
        chave = aluno['nome_normalizado']

        if chave in nomes_banco:
            aluno_local_id, aluno_local_nome = nomes_banco[chave]
            mat = matriculas_2026.get(aluno_local_id)
            duplicados.append({
                **aluno,
                'id_local': aluno_local_id,
                'nome_local': aluno_local_nome,
                'matricula_2026': mat,
            })
        elif not aluno.get('data_nascimento'):
            sem_nascimento.append(aluno)
        else:
            # Determinar escola que seria usada
            escola_info = escolas_por_inep.get(aluno.get('inep_escola'), None)
            aluno['escola_destino'] = f"{escola_info[1]} (ID:{escola_info[0]})" if escola_info else "Primeira escola (padrão)"
            novos.append(aluno)

    # ---- Relatório ----
    print("\n" + "=" * 80)
    print("RESULTADO DA SIMULAÇÃO")
    print("=" * 80)
    print(f"  ✅ Serão IMPORTADOS (novos):         {len(novos):>4}")
    print(f"  ⏭️  Serão IGNORADOS (já existem):     {len(duplicados):>4}")
    print(f"  ❌ Com ERRO (sem data nascimento):   {len(sem_nascimento):>4}")
    print(f"  ─────────────────────────────────────────")
    print(f"  📊 Total analisado:                  {len(alunos_geduc):>4}")

    # --- Alunos que serão importados ---
    if novos:
        print(f"\n{'=' * 80}")
        print(f"✅ NOVOS ALUNOS A IMPORTAR ({len(novos)})")
        print(f"{'=' * 80}")
        com_transtorno = [a for a in novos if a['transtorno'] != 'Nenhum']
        for idx, aluno in enumerate(novos, 1):
            transtorno_tag = f"  🏥 {aluno['transtorno']}" if aluno['transtorno'] != 'Nenhum' else ''
            print(f"  {idx:03d}. {aluno['nome']:<50} [{aluno['turma']}]{transtorno_tag}")
            print(f"       Nascimento: {aluno['data_nascimento'] or 'N/A'}  CPF: {aluno['cpf'] or 'SEM CPF'}  Escola: {aluno['escola_destino']}")

        if com_transtorno:
            print(f"\n  🏥 Alunos com transtorno/deficiência: {len(com_transtorno)}")
            for a in com_transtorno:
                print(f"     • {a['nome']:50} → {a['transtorno']}")

    # --- Duplicados ---
    if duplicados:
        print(f"\n{'=' * 80}")
        print(f"⏭️  JÁ EXISTEM NO SISTEMA — SERÃO IGNORADOS ({len(duplicados)})")
        print(f"{'=' * 80}")
        sem_mat = [d for d in duplicados if not d['matricula_2026']]
        com_mat = [d for d in duplicados if d['matricula_2026']]
        print(f"  Com matrícula em 2026:    {len(com_mat)}")
        print(f"  SEM matrícula em 2026:    {len(sem_mat)}  ⚠️")
        if sem_mat:
            print(f"\n  ⚠️  Estos já estão no banco MAS SEM matrícula 2026:")
            for idx, d in enumerate(sem_mat, 1):
                print(f"  {idx:03d}. {d['nome_local']:<50} (ID: {d['id_local']})")
                if d['nome_local'] != d['nome']:
                    print(f"       Nome no GEDUC: {d['nome']}")

    # --- Sem data de nascimento ---
    if sem_nascimento:
        print(f"\n{'=' * 80}")
        print(f"❌ SEM DATA DE NASCIMENTO — SERÃO PULADOS ({len(sem_nascimento)})")
        print(f"{'=' * 80}")
        for idx, aluno in enumerate(sem_nascimento, 1):
            print(f"  {idx:02d}. {aluno['nome']}")

    # --- Resumo final ---
    print(f"\n{'=' * 80}")
    print("PRÓXIMOS PASSOS")
    print(f"{'=' * 80}")
    if novos:
        print(f"  👤 Rode a importação para cadastrar {len(novos)} novos alunos")
    if any(not d['matricula_2026'] for d in duplicados):
        qtd = sum(1 for d in duplicados if not d['matricula_2026'])
        print(f"  📝 {qtd} alunos já cadastrados ainda precisam de matrícula para 2026")
    if sem_nascimento:
        print(f"  ⚠️  {len(sem_nascimento)} alunos precisam ter data de nascimento corrigida no GEDUC antes de importar")
    print("=" * 80)


if __name__ == '__main__':
    main()
