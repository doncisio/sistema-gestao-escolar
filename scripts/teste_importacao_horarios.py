"""
Script de teste para importação de horários do GEDUC

Este script demonstra como usar a nova funcionalidade de importação
de horários do GEDUC para o banco de dados local.

Uso:
    python teste_importacao_horarios.py

Notas:
    - Requer credenciais válidas do GEDUC
    - Necessário resolver reCAPTCHA manualmente
    - ChromeDriver deve estar instalado
"""

import sys
import os

# Adicionar pasta raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.importadores.geduc import AutomacaoGEDUC
from src.core.conexao import conectar_bd
from src.core.config_logs import get_logger

logger = get_logger(__name__)


def listar_turmas_geduc(automacao):
    """Lista todas as turmas disponíveis no GEDUC"""
    print("\n" + "="*60)
    print("LISTANDO TURMAS DISPONÍVEIS NO GEDUC")
    print("="*60 + "\n")
    
    turmas = automacao.listar_turmas_disponiveis()
    
    if not turmas:
        print("❌ Nenhuma turma encontrada")
        return []
    
    print(f"✅ Encontradas {len(turmas)} turmas:\n")
    
    for idx, turma in enumerate(turmas, 1):
        print(f"{idx:3d}. {turma['nome']} (ID: {turma['id']})")
    
    return turmas


def extrair_horario_turma(automacao, turma_nome):
    """Extrai horário de uma turma específica"""
    print("\n" + "="*60)
    print(f"EXTRAINDO HORÁRIO: {turma_nome}")
    print("="*60 + "\n")
    
    dados = automacao.extrair_horario_turma(turma_nome)
    
    if not dados:
        print(f"❌ Não foi possível extrair horário da turma '{turma_nome}'")
        return None
    
    print(f"✅ Turma: {dados['turma_nome']}")
    print(f"✅ ID GEDUC: {dados['turma_id']}")
    print(f"✅ Total de horários: {len(dados['horarios'])}")
    print(f"✅ Timestamp: {dados['timestamp']}")
    print("\n" + "-"*60)
    print("HORÁRIOS EXTRAÍDOS:")
    print("-"*60 + "\n")
    
    # Organizar por dia e horário
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
    horarios_por_dia = {dia: [] for dia in dias}
    
    for h in dados['horarios']:
        if h['dia'] in horarios_por_dia:
            horarios_por_dia[h['dia']].append(h)
    
    # Exibir organizadamente
    for dia in dias:
        if horarios_por_dia[dia]:
            print(f"\n📅 {dia}:")
            for h in sorted(horarios_por_dia[dia], key=lambda x: x['horario']):
                prof_info = f" - Prof. {h['professor']}" if h.get('professor') else ""
                print(f"   {h['horario']}: {h['disciplina']}{prof_info}")
    
    return dados


def salvar_horario_bd(dados_horario, turma_id_local):
    """Salva horários no banco de dados local"""
    print("\n" + "="*60)
    print("SALVANDO NO BANCO DE DADOS")
    print("="*60 + "\n")
    
    try:
        conn = conectar_bd()
        if not conn:
            print("❌ Não foi possível conectar ao banco de dados")
            return False
        
        cursor = conn.cursor()
        
        horarios = dados_horario.get('horarios', [])
        turma_id_geduc = dados_horario.get('turma_id')
        
        print(f"→ Processando {len(horarios)} horários...")
        
        salvos = 0
        disciplinas_nao_encontradas = set()
        
        for horario in horarios:
            dia = horario['dia']
            hora = horario['horario']
            disciplina_nome = horario['disciplina']
            professor_nome = horario.get('professor')
            
            # Buscar ID da disciplina
            disciplina_id = None
            cursor.execute(
                "SELECT id FROM disciplinas WHERE nome LIKE %s LIMIT 1", 
                (f"%{disciplina_nome}%",)
            )
            resultado_disc = cursor.fetchone()
            if resultado_disc:
                disciplina_id = resultado_disc[0]
            else:
                disciplinas_nao_encontradas.add(disciplina_nome)
            
            # Buscar ID do professor
            professor_id = None
            if professor_nome:
                cursor.execute(
                    "SELECT id FROM professores WHERE nome LIKE %s LIMIT 1", 
                    (f"%{professor_nome}%",)
                )
                resultado_prof = cursor.fetchone()
                if resultado_prof:
                    professor_id = resultado_prof[0]
            
            # Valor combinado
            valor = disciplina_nome
            if professor_nome:
                valor = f"{disciplina_nome}\n{professor_nome}"
            
            # Inserir ou atualizar
            sql = """
                INSERT INTO horarios_importados 
                (turma_id, dia, horario, valor, disciplina_id, professor_id, geduc_turma_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                valor = VALUES(valor),
                disciplina_id = VALUES(disciplina_id),
                professor_id = VALUES(professor_id),
                geduc_turma_id = VALUES(geduc_turma_id)
            """
            
            cursor.execute(sql, (
                turma_id_local,
                dia,
                hora,
                valor,
                disciplina_id,
                professor_id,
                turma_id_geduc
            ))
            
            salvos += 1
        
        conn.commit()
        
        print(f"✅ {salvos} horários salvos com sucesso!")
        
        if disciplinas_nao_encontradas:
            print(f"\n⚠️ {len(disciplinas_nao_encontradas)} disciplinas não encontradas no banco local:")
            for disc in sorted(disciplinas_nao_encontradas):
                print(f"   - {disc}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.exception("Erro ao salvar horários")
        print(f"❌ Erro: {str(e)}")
        return False


def main():
    """Função principal de teste"""
    print("\n" + "="*60)
    print("TESTE DE IMPORTAÇÃO DE HORÁRIOS DO GEDUC")
    print("="*60 + "\n")
    
    # Configurações
    usuario = input("Usuário GEDUC: ").strip()
    senha = input("Senha GEDUC: ").strip()
    
    if not usuario or not senha:
        print("❌ Credenciais não fornecidas. Encerrando.")
        return
    
    automacao = None
    
    try:
        # Inicializar automação
        print("\n→ Iniciando navegador...")
        automacao = AutomacaoGEDUC(headless=False)
        
        if not automacao.iniciar_navegador():
            print("❌ Erro ao iniciar navegador")
            return
        
        print("✅ Navegador iniciado")
        
        # Fazer login
        print("\n→ Fazendo login no GEDUC...")
        print("⚠️ Resolva o reCAPTCHA manualmente no navegador!")
        print("⚠️ Você tem 120 segundos para resolver e fazer login\n")
        
        if not automacao.fazer_login(usuario, senha, timeout_recaptcha=120):
            print("❌ Erro no login")
            return
        
        print("✅ Login realizado com sucesso")
        
        # Listar turmas
        turmas = listar_turmas_geduc(automacao)
        
        if not turmas:
            return
        
        # Selecionar turma
        print("\n" + "-"*60)
        escolha = input("\nDigite o número da turma para extrair horários (ou Enter para sair): ").strip()
        
        if not escolha:
            print("Encerrando...")
            return
        
        try:
            idx = int(escolha) - 1
            if idx < 0 or idx >= len(turmas):
                print("❌ Opção inválida")
                return
            
            turma_selecionada = turmas[idx]
            
        except ValueError:
            print("❌ Entrada inválida")
            return
        
        # Extrair horário
        dados = extrair_horario_turma(automacao, turma_selecionada['nome'])
        
        if not dados:
            return
        
        # Perguntar se deseja salvar
        print("\n" + "-"*60)
        salvar = input("\nDeseja salvar no banco de dados? (s/n): ").strip().lower()
        
        if salvar == 's':
            # Solicitar ID da turma local
            turma_id_local = input("Digite o ID da turma no sistema local: ").strip()
            
            try:
                turma_id_local = int(turma_id_local)
                salvar_horario_bd(dados, turma_id_local)
            except ValueError:
                print("❌ ID inválido")
        
        print("\n" + "="*60)
        print("TESTE CONCLUÍDO")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrompido pelo usuário")
        
    except Exception as e:
        logger.exception("Erro durante teste")
        print(f"\n❌ Erro: {str(e)}")
        
    finally:
        if automacao:
            print("\n→ Fechando navegador...")
            automacao.fechar()
            print("✅ Navegador fechado")


if __name__ == "__main__":
    main()
