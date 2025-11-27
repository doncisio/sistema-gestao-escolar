#!/usr/bin/env python3
"""
Validação completa pós-correção da importação BNCC
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv('.env')

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST','localhost'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME','redeescola')
)

c = conn.cursor()

print("=" * 70)
print("VALIDAÇÃO COMPLETA PÓS-CORREÇÃO")
print("=" * 70)

# 1. Verificar se descrição está correta (não deve ter códigos BNCC)
print("\n1. Verificando se descrições estão corretas (não devem ter códigos):")
c.execute("""
    SELECT codigo, LEFT(descricao, 80) 
    FROM bncc_habilidades
    WHERE descricao REGEXP '(EF|EM|EI)[0-9]{2}[A-Z]{2}[0-9]{2}'
    LIMIT 5
""")
erros_desc = c.fetchall()
if erros_desc:
    print(f"  ❌ ERRO: {len(erros_desc)} habilidades ainda têm códigos na descrição:")
    for cod, desc in erros_desc:
        print(f"     {cod}: {desc[:60]}")
else:
    print("  ✓ OK: Nenhuma descrição com códigos BNCC encontrada")

# 2. Amostra de descrições corretas
print("\n2. Amostra de descrições (devem ser textos longos):")
c.execute("""
    SELECT codigo, LEFT(descricao, 100)
    FROM bncc_habilidades
    WHERE descricao IS NOT NULL
    LIMIT 3
""")
for cod, desc in c.fetchall():
    print(f"  {cod}: {desc}...")

# 3. Verificar preenchimento dos novos campos
print("\n3. Preenchimento dos novos campos pedagógicos:")
c.execute("""
    SELECT 
      COUNT(*) as total,
      SUM(CASE WHEN unidade_tematica IS NOT NULL AND unidade_tematica != '' THEN 1 ELSE 0 END) as com_unidade,
      SUM(CASE WHEN classificacao IS NOT NULL AND classificacao != '' THEN 1 ELSE 0 END) as com_classif,
      SUM(CASE WHEN objetivos_aprendizagem IS NOT NULL AND objetivos_aprendizagem != '' THEN 1 ELSE 0 END) as com_objetivos,
      SUM(CASE WHEN competencias_relacionadas IS NOT NULL AND competencias_relacionadas != '' THEN 1 ELSE 0 END) as com_competencias,
      SUM(CASE WHEN habilidades_relacionadas IS NOT NULL AND habilidades_relacionadas != '' THEN 1 ELSE 0 END) as com_habilidades_rel,
      SUM(CASE WHEN comentarios IS NOT NULL AND comentarios != '' THEN 1 ELSE 0 END) as com_comentarios,
      SUM(CASE WHEN campo_atuacao IS NOT NULL AND campo_atuacao != '' THEN 1 ELSE 0 END) as com_campo_atuacao
    FROM bncc_habilidades
""")
row = c.fetchone()
total, unid, classif, obj, comp, hab_rel, coment, campo = row
print(f"  Total habilidades: {total}")
print(f"  Com unidade_tematica: {unid} ({100*unid//total if total else 0}%)")
print(f"  Com classificacao: {classif} ({100*classif//total if total else 0}%)")
print(f"  Com objetivos_aprendizagem: {obj} ({100*obj//total if total else 0}%)")
print(f"  Com competencias_relacionadas: {comp} ({100*comp//total if total else 0}%)")
print(f"  Com habilidades_relacionadas: {hab_rel} ({100*hab_rel//total if total else 0}%)")
print(f"  Com comentarios: {coment} ({100*coment//total if total else 0}%)")
print(f"  Com campo_atuacao: {campo} ({100*campo//total if total else 0}%)")

# 4. Amostras dos novos campos
print("\n4. Amostra de registro completo (EF07MA02):")
c.execute("""
    SELECT codigo, LEFT(descricao,80), LEFT(conhecimento_previo,60), unidade_tematica, 
           classificacao, LEFT(objetivos_aprendizagem,80), LEFT(competencias_relacionadas,60)
    FROM bncc_habilidades 
    WHERE codigo = 'EF07MA02'
""")
row = c.fetchone()
if row:
    print(f"  Código: {row[0]}")
    print(f"  Descrição: {row[1]}...")
    print(f"  Conhec.Prévio: {row[2]}")
    print(f"  Unidade: {row[3]}")
    print(f"  Classificação: {row[4]}")
    print(f"  Objetivos: {row[5]}...")
    print(f"  Competências: {row[6]}")

# 5. Distribuição por classificação
print("\n5. Distribuição por classificação (AF/AC):")
c.execute("""
    SELECT classificacao, COUNT(*) as cnt
    FROM bncc_habilidades
    WHERE classificacao IS NOT NULL AND classificacao != ''
    GROUP BY classificacao
    ORDER BY cnt DESC
""")
for classif, cnt in c.fetchall():
    print(f"  {classif}: {cnt} habilidades")

# 6. Estatísticas de pré-requisitos
print("\n6. Estatísticas de relacionamentos:")
c.execute("SELECT COUNT(*) FROM bncc_prerequisitos")
print(f"  Total relacionamentos: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM bncc_prerequisitos WHERE prereq_bncc_id IS NOT NULL")
print(f"  Com ID resolvido: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM bncc_prerequisitos WHERE prereq_bncc_id IS NULL")
print(f"  Órfãos (sem ID): {c.fetchone()[0]}")

conn.close()
print("\n" + "=" * 70)
print("✓ Validação concluída")
print("=" * 70)
