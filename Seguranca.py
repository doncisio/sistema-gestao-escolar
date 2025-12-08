import os
import subprocess
from dotenv import load_dotenv
import schedule
import threading
import time
from datetime import datetime
from config_logs import get_logger

# Importar settings centralizado
try:
    from config.settings import settings
except ImportError:
    settings = None

logger = get_logger(__name__)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Variável global para controlar o thread de backup
_backup_thread = None
_backup_running = False
_backup_initialized = False  # Flag para evitar inicialização duplicada

def fazer_backup():
    r"""
    Realiza o backup do banco de dados 'redeescola' e salva em dois locais:
    1. Pasta local do projeto
    2. Google Drive (G:\Meu Drive\NADIR_2025\Backup)
    
    :return: True se o backup foi bem-sucedido, False caso contrário.
    """
    caminho_backup_local = "migrations/backup_redeescola.sql"
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

        # Verificar se mysqldump está disponível
        try:
            verificar = subprocess.run(["mysqldump", "--version"], capture_output=True, text=True)
            if verificar.returncode != 0:
                logger.error("mysqldump não está funcionando corretamente")
                return False
        except FileNotFoundError:
            logger.error("mysqldump não encontrado. Verifique se o MySQL está instalado e no PATH do sistema.")
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
        resultado = subprocess.run(comando_backup, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        # Verificar se houve erro
        if resultado.returncode != 0:
            erro_msg = resultado.stderr.strip() if resultado.stderr else "Erro desconhecido"
            logger.error("Falha no mysqldump: %s", erro_msg)
            return False
        
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
    caminho_backup_local = "migrations/backup_redeescola.sql"
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
        # Adicionando init-command para contornar o erro de privilégio SUPER
        comando_restauracao = [
            "mysql",
            f"--user={usuario}",
            f"--password={senha}",
            f"--host={host}",
            "--default-character-set=utf8mb4",
            "--init-command=SET SESSION sql_log_bin=0;",
            "--init-command=SET GLOBAL log_bin_trust_function_creators=1;",
            database
        ]

        # Executar o comando e ler o arquivo de backup como entrada
        try:
            with open(caminho_backup, "r", encoding="utf-8") as arquivo_backup:
                resultado = subprocess.run(
                    comando_restauracao, 
                    stdin=arquivo_backup,
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Verificar se houve erros
                if resultado.returncode != 0:
                    stderr = resultado.stderr
                    # Ignorar apenas o aviso de senha na linha de comando
                    if "Using a password on the command line" in stderr:
                        logger.warning("Aviso: Senha passou pela linha de comando (considere usar arquivo de configuração)")
                    # Se houver erro 1419, tentar com comando alternativo
                    elif "ERROR 1419" in stderr or "SUPER privilege" in stderr:
                        logger.warning("Erro de privilégio SUPER detectado. Tentando método alternativo...")
                        # Tentar sem as flags problemáticas
                        comando_alternativo = [
                            "mysql",
                            f"--user={usuario}",
                            f"--password={senha}",
                            f"--host={host}",
                            "--default-character-set=utf8mb4",
                            database
                        ]
                        with open(caminho_backup, "r", encoding="utf-8") as arquivo_backup:
                            resultado_alt = subprocess.run(
                                comando_alternativo,
                                stdin=arquivo_backup,
                                capture_output=True,
                                text=True,
                                encoding='utf-8',
                                errors='replace'
                            )
                            if resultado_alt.returncode != 0 and "ERROR 1419" in resultado_alt.stderr:
                                logger.error("Erro persistente. O backup contém procedures/functions que requerem privilégios SUPER.")
                                logger.info("Solução: Execute como administrador MySQL ou desabilite binary logging.")
                                return False
                    else:
                        logger.error(f"Erro ao restaurar backup: {stderr}")
                        return False
        except Exception as e:
            logger.error(f"Erro ao abrir arquivo de backup: {e}")
            return False

        logger.info("Restauração realizada com sucesso a partir do arquivo: %s", caminho_backup)
        return True

    except subprocess.CalledProcessError as e:
        logger.exception("Erro ao restaurar o backup: %s", e)
        return False
    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        return False

# Função para atualizar o Treeview
# DEPRECATED: Use utils.ui_callbacks.atualizar_treeview para evitar dependências circulares
def atualizar_treeview(treeview, cursor, query):
    """
    DEPRECATED: Esta função está obsoleta e será removida em versões futuras.
    Use utils.ui_callbacks.atualizar_treeview em vez disso.
    """
    import warnings
    warnings.warn(
        "Seguranca.atualizar_treeview está deprecated. "
        "Use utils.ui_callbacks.atualizar_treeview",
        DeprecationWarning,
        stacklevel=2
    )
    
    from utils.ui_callbacks import atualizar_treeview as new_atualizar_treeview
    return new_atualizar_treeview(treeview, cursor, query)


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
    
    logger.info("Sistema de Backup Automático ativado (14:05 e 17:00)")


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
    
    IMPORTANTE: Previne inicialização duplicada usando flag global _backup_initialized.
    """
    global _backup_thread, _backup_running, _backup_initialized
    
    # Verificar se backup está habilitado via configuração
    if settings and not settings.backup.enabled:
        logger.info("Sistema de backup automático desabilitado via configuração")
        return
    
    # Prevenir inicialização duplicada
    if _backup_initialized:
        logger.warning("Sistema de backup automático já foi inicializado anteriormente. Ignorando chamada duplicada.")
        return
    
    if _backup_thread is not None and _backup_thread.is_alive():
        logger.warning("Sistema de backup automático já está em execução.")
        return
    
    # Configurar o agendamento
    agendar_backup_diario()
    
    # Iniciar a thread do agendador
    _backup_thread = threading.Thread(target=executar_agendador, daemon=True)
    _backup_thread.start()
    
    # Marcar como inicializado
    _backup_initialized = True
    logger.info("✓ Sistema de backup automático iniciado com sucesso")


def parar_backup_automatico(executar_backup_final=True):
    """
    Para o sistema de backup automático.
    
    :param executar_backup_final: Se True, executa um backup final antes de encerrar.
    """
    global _backup_running, _backup_initialized
    
    # Verificar se backup está habilitado
    if settings and not settings.backup.enabled:
        logger.debug("Sistema de backup desabilitado - nada a parar")
        return
    
    if executar_backup_final and _backup_running:
        try:
            logger.info("\n" + "="*70)
            logger.info("Executando backup final antes de encerrar o sistema...")
            logger.info("="*70)
            resultado = fazer_backup()
            if resultado:
                logger.info("[%s] Backup final concluído com sucesso!", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            else:
                logger.warning("[%s] Falha no backup final.", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
            logger.info("="*70 + "\n")
        except Exception as e:
            logger.error(f"Erro ao executar backup final: {e}")
            # Não propagar o erro - permitir que o sistema feche normalmente
    
    _backup_running = False
    _backup_initialized = False
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