import csv
import datetime
from src.relatorios.relatorio_pendencias import buscar_pendencias_notas

OUTPUT = 'pendencias_por_bimestre.csv'
ESOLA_ID = 60

bimestres = ['1º bimestre', '2º bimestre', '3º bimestre', '4º bimestre']
niveis = ['iniciais', 'finais']

rows = []
for b in bimestres:
    for n in niveis:
        try:
            pend = buscar_pendencias_notas(b, n, None, ESOLA_ID)
        except Exception as e:
            print(f"Erro ao buscar pendências para {b} / {n}: {e}")
            pend = {}

        # pend is a dict keyed by (serie, turma, turno)
        for chave, info in pend.items():
            serie, turma, turno = chave
            disciplinas_sem_lanc = sorted(list(info.get('disciplinas_sem_lancamento', []))) if info.get('disciplinas_sem_lancamento') else []
            # alunos com pendências
            for aluno_id, aluno_info in info.get('alunos', {}).items():
                disc_sem_nota = sorted(list(set(aluno_info.get('disciplinas_sem_nota', []))))
                if not disc_sem_nota:
                    continue
                rows.append({
                    'bimestre': b,
                    'nivel': n,
                    'serie': serie,
                    'turma': turma,
                    'turno': turno,
                    'aluno_id': aluno_id,
                    'aluno_nome': aluno_info.get('nome'),
                    'disciplinas_sem_nota': ';'.join(disc_sem_nota),
                    'disciplinas_sem_lancamento': ';'.join(disciplinas_sem_lanc)
                })
            # também registrar caso existam disciplinas sem lançamento mesmo que nenhum aluno esteja listado
            # registrar caso existam disciplinas sem lançamento mesmo que nenhum aluno tenha pendência de nota
            has_alunos_com_pend = any(len(a.get('disciplinas_sem_nota', [])) > 0 for a in info.get('alunos', {}).values())
            if disciplinas_sem_lanc and not has_alunos_com_pend:
                rows.append({
                    'bimestre': b,
                    'nivel': n,
                    'serie': serie,
                    'turma': turma,
                    'turno': turno,
                    'aluno_id': '',
                    'aluno_nome': '',
                    'disciplinas_sem_nota': '',
                    'disciplinas_sem_lancamento': ';'.join(disciplinas_sem_lanc)
                })

# escrever CSV
fieldnames = ['bimestre','nivel','serie','turma','turno','aluno_id','aluno_nome','disciplinas_sem_nota','disciplinas_sem_lancamento']
with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print(f"Arquivo gerado: {OUTPUT} ({len(rows)} linhas) - {datetime.datetime.now()}")
