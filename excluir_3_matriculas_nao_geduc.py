"""
Script para excluir matrículas do ano letivo 2026 de 3 alunos que não estão no GEDUC
Conforme comparação: apenas no sistema local, não renovaram

Alunos:
1. Aysha Bianca Silva da Cruz - 6º Ano (VESP) - Transferido
2. Henzzo Henrique dos Santos Serra - 7º Ano B (VESP) - Ativo  
3. Ruan Carlos Costa Silva - 7º Ano B (VESP) - Ativo
"""

from db.connection import conectar_bd
import unicodedata

# Lista dos 3 alunos que estão apenas no sistema local
ALUNOS_PARA_EXCLUIR = [
    "Aysha Bianca Silva da Cruz",
    "Henzzo Henrique dos Santos Serra",
    "Ruan Carlos Costa Silva"
]


def normalizar_nome(nome):
    """Remove acentos e converte para maiúsculo"""
    if not nome:
        return ""
    nome_sem_acento = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nome_sem_acento if not unicodedata.combining(c)])
    return nome_sem_acento.upper().strip()


def excluir_matriculas():
    """Exclui matrículas do ano letivo 2026 dos 3 alunos"""
    
    print("="*80)
    print("EXCLUSÃO DE 3 MATRÍCULAS NÃO ENCONTRADAS NO GEDUC - ANO LETIVO 2026")
    print("="*80)
    print(f"\nTotal de alunos a processar: {len(ALUNOS_PARA_EXCLUIR)}")
    print("\nEstes alunos não estão no GEDUC. Vamos excluir apenas a matrícula em 2026.")
    print("Os dados do aluno serão mantidos no sistema.\n")
    
    conn = conectar_bd()
    if not conn:
        print("❌ ERRO: Não foi possível conectar ao banco de dados!")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    # Buscar ID do ano letivo 2026
    cursor.execute("SELECT id FROM anosletivos WHERE ano_letivo = 2026")
    ano_letivo = cursor.fetchone()
    
    if not ano_letivo:
        print("❌ ERRO: Ano letivo 2026 não encontrado!")
        cursor.close()
        conn.close()
        return
    
    ano_letivo_id = ano_letivo['id']
    print(f"✓ Ano letivo 2026 encontrado (ID: {ano_letivo_id})\n")
    
    # Estatísticas
    excluidos = 0
    nao_encontrados = []
    sem_matricula = []
    
    print("Processando alunos:\n")
    
    for idx, nome_aluno in enumerate(ALUNOS_PARA_EXCLUIR, 1):
        nome_normalizado = normalizar_nome(nome_aluno)
        
        # Buscar aluno pelo nome
        cursor.execute("""
            SELECT id, nome 
            FROM Alunos 
            WHERE UPPER(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                nome, 'Á', 'A'), 'É', 'E'), 'Í', 'I'), 'Ó', 'O'), 'Ú', 'U')
            ) = %s
            AND escola_id = 60
        """, (nome_normalizado,))
        
        aluno = cursor.fetchone()
        
        if not aluno:
            print(f"[{idx}] ⚠️  {nome_aluno}")
            print(f"     Aluno não encontrado no banco de dados\n")
            nao_encontrados.append(nome_aluno)
            continue
        
        aluno_id = aluno['id']
        aluno_nome = aluno['nome']
        
        # Buscar matrícula em 2026
        cursor.execute("""
            SELECT id, status, turma_id
            FROM Matriculas 
            WHERE aluno_id = %s AND ano_letivo_id = %s
        """, (aluno_id, ano_letivo_id))
        
        matricula = cursor.fetchone()
        
        if not matricula:
            print(f"[{idx}] ℹ️  {aluno_nome} (ID: {aluno_id})")
            print(f"     Já sem matrícula em 2026\n")
            sem_matricula.append(nome_aluno)
            continue
        
        matricula_id = matricula['id']
        status_matricula = matricula['status']
        
        # Buscar informações da turma para exibir
        turma_info = ""
        if matricula['turma_id']:
            cursor.execute("""
                SELECT t.nome, s.nome as serie, t.turno
                FROM Turmas t
                LEFT JOIN series s ON t.serie_id = s.id
                WHERE t.id = %s
            """, (matricula['turma_id'],))
            turma = cursor.fetchone()
            if turma:
                turma_info = f" - {turma['serie']} {turma['nome']} ({turma['turno']})"
        
        print(f"[{idx}] 🔍 {aluno_nome} (ID: {aluno_id})")
        print(f"     Matrícula ID: {matricula_id} | Status: {status_matricula}{turma_info}")
        
        # 1. Excluir registros relacionados em historico_matricula (se existir)
        cursor.execute("""
            DELETE FROM historico_matricula 
            WHERE matricula_id = %s
        """, (matricula_id,))
        historicos_excluidos = cursor.rowcount
        
        if historicos_excluidos > 0:
            print(f"     ↳ {historicos_excluidos} registro(s) de histórico excluído(s)")
        
        # 2. Excluir a matrícula
        cursor.execute("""
            DELETE FROM Matriculas 
            WHERE id = %s
        """, (matricula_id,))
        
        print(f"     ✅ Matrícula excluída com sucesso!\n")
        excluidos += 1
    
    # Confirmar exclusões
    conn.commit()
    
    print("="*80)
    print("RESUMO")
    print("="*80)
    print(f"Total processado: {len(ALUNOS_PARA_EXCLUIR)}")
    print(f"✅ Matrículas excluídas: {excluidos}")
    print(f"ℹ️  Já sem matrícula: {len(sem_matricula)}")
    print(f"⚠️  Alunos não encontrados: {len(nao_encontrados)}")
    
    if nao_encontrados:
        print("\nAlunos não encontrados:")
        for nome in nao_encontrados:
            print(f"  - {nome}")
    
    cursor.close()
    conn.close()
    
    print("\n✓ Processo concluído!")
    print("="*80)


if __name__ == "__main__":
    print("\n⚠️  ATENÇÃO: Este script vai excluir as matrículas de 2026 de 3 alunos.")
    print("Os dados dos alunos serão mantidos no sistema, apenas a matrícula será removida.\n")
    
    resposta = input("Deseja continuar? (S/N): ").strip().upper()
    
    if resposta == 'S':
        excluir_matriculas()
    else:
        print("\n❌ Operação cancelada pelo usuário.")
