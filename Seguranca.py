import os
import subprocess
from dotenv import load_dotenv
import schedule
import threading
import time
from datetime import datetime
from config_logs import get_logger

logger = get_logger(__name__)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Variável global para controlar o thread de backup
_backup_thread = None
_backup_running = False

def fazer_backup():
    r"""
    Realiza o backup do banco de dados 'redeescola' e salva em dois locais:
    1. Pasta local do projeto
    2. Google Drive (G:\Meu Drive\NADIR_2025\Backup)
    
    :return: True se o backup foi bem-sucedido, False caso contrário.
    """
    caminho_backup_local = "backup_redeescola.sql"
    caminho_backup_drive = r"G:\Meu Drive\NADIR_2025\Backup\backup_redeescola.sql"
    try:
        # Obter credenciais do arquivo .env
        usuario = os.getenv("DB_USER")
        senha = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_NAME")

        if not all([usuario, senha, host, database]):
            logger.error("Erro: Credenciais incompletas no arquivo .env.")
            return False

        # Comando para fazer o backup usando mysqldump
        comando_backup = [
            "mysqldump",
            f"--user={usuario}",
            f"--password={senha}",
            f"--host={host}",
            "--default-character-set=utf8mb4",
            "--result-file=" + caminho_backup_local,
            database
        ]

        # Executar o comando (resultado será salvo diretamente no arquivo)
        resultado = subprocess.run(comando_backup, capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
        
        logger.info("✓ Backup local salvo em: %s", caminho_backup_local)

        # Copiar backup para o Google Drive (se o diretório existir)
        backup_drive_ok = False
        try:
            # Verificar se o diretório do Google Drive existe
            diretorio_drive = os.path.dirname(caminho_backup_drive)
            if os.path.exists(diretorio_drive):
                # Ler o arquivo local e salvar no Drive
                with open(caminho_backup_local, "r", encoding="utf-8") as arquivo_origem:
                    backup_content = arquivo_origem.read()
                with open(caminho_backup_drive, "w", encoding="utf-8") as arquivo_destino:
                    arquivo_destino.write(backup_content)
                logger.info("✓ Backup no Google Drive salvo em: %s", caminho_backup_drive)
                backup_drive_ok = True
            else:
                logger.warning("⚠ Diretório do Google Drive não encontrado: %s", diretorio_drive)
                logger.info("  Backup salvo apenas localmente.")
                logger.info("  DICA: Certifique-se de que o Google Drive Desktop está instalado e sincronizando.")
        except PermissionError as e:
            logger.warning("⚠ Sem permissão para escrever no Google Drive: %s", e)
            logger.info("  Backup salvo apenas localmente.")
            logger.info("  DICA: Verifique se você está logado no Google Drive Desktop.")
        except Exception as e:
            logger.exception("⚠ Erro ao salvar no Google Drive: %s", e)
            logger.info("  Backup salvo apenas localmente.")
            logger.info("  DICA: Reinstale o Google Drive Desktop se o problema persistir.")
        logger.info("✓ Backup realizado com sucesso!")
        return True

    except subprocess.CalledProcessError as e:
        logger.exception("Erro ao realizar o backup: %s", e)
        return False
    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        return False


def restaurar_backup():
    r"""
    Restaura o banco de dados 'redeescola' a partir de um arquivo SQL de backup.
    Procura primeiro no Google Drive, depois localmente.
    
    :return: True se a restauração foi bem-sucedida, False caso contrário.
    """
    caminho_backup_local = "backup_redeescola.sql"
    caminho_backup_drive = r"G:\Meu Drive\NADIR_2025\Backup\backup_redeescola.sql"
    try:
        # Determinar qual arquivo de backup usar (prioridade: Drive > Local)
        if os.path.exists(caminho_backup_drive):
            caminho_backup = caminho_backup_drive
            logger.info("Usando backup do Google Drive: %s", caminho_backup)
        elif os.path.exists(caminho_backup_local):
            caminho_backup = caminho_backup_local
            logger.info("Usando backup local: %s", caminho_backup)
        else:
            logger.error("Erro: Nenhum arquivo de backup encontrado!")
            logger.info("  - Local: %s", caminho_backup_local)
            logger.info("  - Drive: %s", caminho_backup_drive)
            return False

        # Obter credenciais do arquivo .env
        usuario = os.getenv("DB_USER")
        senha = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_NAME")

        if not all([usuario, senha, host, database]):
            logger.error("Erro: Credenciais incompletas no arquivo .env.")
            return False

        # Comando para restaurar o backup usando mysql
        comando_restauracao = [
            "mysql",
            f"--user={usuario}",
            f"--password={senha}",
            f"--host={host}",
            "--default-character-set=utf8mb4",
            database
        ]

        # Executar o comando e ler o arquivo de backup como entrada
        with open(caminho_backup, "r", encoding="utf-8") as arquivo_backup:
            subprocess.run(comando_restauracao, stdin=arquivo_backup, 
                         capture_output=True, text=True, encoding='utf-8', 
                         errors='replace', check=True)

        logger.info("Restauração realizada com sucesso a partir do arquivo: %s", caminho_backup)
        return True

    except subprocess.CalledProcessError as e:
        logger.exception("Erro ao restaurar o backup: %s", e)
        return False
    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        return False

# Função para atualizar o Treeview
def atualizar_treeview(treeview, cursor, query):
    try:
        # Verificar se o Treeview ainda existe
        if not treeview or not treeview.winfo_exists():
            logger.error("Erro: O Treeview não está mais ativo.")
            return

        # Limpar os itens existentes no Treeview
        for item in treeview.get_children():
            treeview.delete(item)

        # Executar a consulta SQL e preencher o Treeview
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            treeview.insert("", "end", values=row)
    except Exception as e:
        logger.error("Erro ao atualizar o Treeview:", e)


# ============================================================================
# SISTEMA DE BACKUP AUTOMÁTICO
# ============================================================================

def executar_backup_automatico():
    """
    Executa o backup automático se estiver dentro do horário permitido (14h-19h).
    Esta função é chamada pelo agendador.
    """
    hora_atual = datetime.now().hour
    
    # Verificar se está dentro do horário permitido (14h às 19h)
    if 14 <= hora_atual < 19:
        logger.info("\n[%s] Iniciando backup automático...", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        resultado = fazer_backup()
        if resultado:
            logger.info("[%s] Backup automático concluído com sucesso!", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        else:
            logger.warning("[%s] Falha no backup automático.", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    else:
        logger.info("[%s] Fora do horário de backup (14h-19h). Backup não executado.", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))


def agendar_backup_diario():
    """
    Configura o agendamento do backup para ser executado todos os dias às 14:05 e 17:00.
    O backup só será executado se estiver entre 14h e 19h.
    """
    # Agendar backups diários
    schedule.every().day.at("14:05").do(executar_backup_automatico)
    schedule.every().day.at("17:00").do(executar_backup_automatico)
    
    logger.info("\n" + "="*70)
    logger.info("Sistema de Backup Automático Ativado")
    logger.info("="*70)
    logger.info("• Horários de execução: 14:05 e 17:00 (todos os dias)")
    logger.info("• Janela de execução permitida: 14:00 - 19:00")
    logger.info("• Backup final: Ao fechar o programa")
    logger.info("• Status: Aguardando próximo horário de backup...")
    logger.info("="*70 + "\n")


def executar_agendador():
    """
    Função que roda em uma thread separada para executar o agendador.
    Verifica a cada minuto se há tarefas agendadas para executar.
    """
    global _backup_running
    _backup_running = True
    
    while _backup_running:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada 1 minuto


def iniciar_backup_automatico():
    """
    Inicia o sistema de backup automático em uma thread separada.
    Esta função deve ser chamada no main.py após a inicialização da interface.
    """
    global _backup_thread, _backup_running
    
    if _backup_thread is not None and _backup_thread.is_alive():
        logger.warning("Sistema de backup automático já está em execução.")
        return
    
    # Configurar o agendamento
    agendar_backup_diario()
    
    # Iniciar a thread do agendador
    _backup_thread = threading.Thread(target=executar_agendador, daemon=True)
    _backup_thread.start()


def parar_backup_automatico(executar_backup_final=True):
    """
    Para o sistema de backup automático.
    
    :param executar_backup_final: Se True, executa um backup final antes de encerrar.
    """
    global _backup_running
    
    if executar_backup_final and _backup_running:
        logger.info("\n" + "="*70)
        logger.info("Executando backup final antes de encerrar o sistema...")
        logger.info("="*70)
        resultado = fazer_backup()
        if resultado:
            logger.info("[%s] Backup final concluído com sucesso!", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        else:
            logger.warning("[%s] Falha no backup final.", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        logger.info("="*70 + "\n")
    
    _backup_running = False
    schedule.clear()
    logger.info("\nSistema de backup automático encerrado.")


def status_backup_automatico():
    """
    Retorna o status do sistema de backup automático.
    """
    global _backup_thread
    
    if _backup_thread is not None and _backup_thread.is_alive():
        proximos_jobs = schedule.get_jobs()
        if proximos_jobs:
            logger.info("\nStatus do Backup Automático:")
            logger.info("="*70)
            logger.info("• Sistema: ATIVO")
            logger.info("• Thread: Em execução")
            logger.info("• Próximos backups agendados: 14:05 e 17:00")
            logger.info("• Backup final: Ao fechar o programa")
            logger.info("="*70)
            return True
        else:
            logger.info("\nSistema de backup automático está rodando, mas sem agendamentos.")
            return False
    else:
        logger.info("\nSistema de backup automático NÃO está ativo.")
        return False