import os
import subprocess
from dotenv import load_dotenv
import schedule
import threading
import time
from datetime import datetime
from src.core.config_logs import get_logger

# Importar settings centralizado
try:
    from src.core.config.settings import settings
except ImportError:
    settings = None

try:
    from src.core.config import ANO_LETIVO_ATUAL
except ImportError:
    from datetime import datetime as _dt
    ANO_LETIVO_ATUAL = _dt.now().year

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
    2. Google Drive (G:\Meu Drive\NADIR {ano}\Backup)
    
    :return: True se o backup foi bem-sucedido, False caso contrário.
    """
    caminho_backup_local = "migrations/backup_redeescola.sql"
    caminho_backup_drive = rf"G:\Meu Drive\NADIR {ANO_LETIVO_ATUAL}\Backup\backup_redeescola.sql"
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
            verificar = subprocess.run(["mysqldump", "--version"], capture_output=True, text=True, timeout=10)
            if verificar.returncode != 0:
                logger.error("mysqldump não está funcionando corretamente")
                return False
        except FileNotFoundError:
            logger.error("mysqldump não encontrado. Verifique se o MySQL está instalado e no PATH do sistema.")
            return False
        except subprocess.TimeoutExpired:
            logger.error("mysqldump --version excedeu o tempo limite")
            return False

        # Comando para fazer o backup usando mysqldump
        # --single-transaction: garante snapshot consistente para tabelas InnoDB
        # --skip-lock-tables: necessário em conjunto com --single-transaction
        comando_backup = [
            "mysqldump",
            f"--user={usuario}",
            f"--password={senha}",
            f"--host={host}",
            "--default-character-set=utf8mb4",
            "--single-transaction",
            "--skip-lock-tables",
            "--result-file=" + caminho_backup_local,
            database
        ]

        # Executar o comando com timeout de 120 segundos
        resultado = subprocess.run(comando_backup, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
        
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

    except subprocess.TimeoutExpired:
        logger.error("Backup excedeu o tempo limite de 120 segundos")
        return False
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
    caminho_backup_drive = rf"G:\Meu Drive\NADIR {ANO_LETIVO_ATUAL}\Backup\backup_redeescola.sql"
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

        # Comando para restaurar o backup usando mysql.
        # --force: continua a execução mesmo após erros não-críticos (ex: falha
        #          na criação de TRIGGER/DEFINER), garantindo que todos os INSERTs
        #          de dados sejam executados mesmo quando triggers não podem ser
        #          recriados por falta de privilégio SUPER.
        comando_restauracao = [
            "mysql",
            f"--user={usuario}",
            f"--password={senha}",
            f"--host={host}",
            "--default-character-set=utf8mb4",
            "--force",
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
        except Exception as e:
            logger.error("Erro ao abrir arquivo de backup: %s", e)
            return False

        stderr = resultado.stderr or ""

        # Extrair linhas de erro reais (ignorar aviso de senha da linha de comando)
        import re as _re
        linhas_erro = [
            l for l in stderr.splitlines()
            if _re.search(r'ERROR\s+\d+', l)
            and "Using a password on the command line" not in l
        ]

        if resultado.returncode != 0 or linhas_erro:
            # Erros de DEFINER/TRIGGER (1218, 1227, 1418, 1419) são não-críticos:
            # os dados são inseridos mesmo assim; apenas o trigger fica ausente.
            codigos_nao_criticos = {'1227', '1418', '1419'}
            erros_criticos = [
                l for l in linhas_erro
                if not any(f'ERROR {c}' in l for c in codigos_nao_criticos)
            ]

            if erros_criticos:
                for linha in erros_criticos:
                    logger.error("Erro crítico na restauração: %s", linha)
                return False

            if linhas_erro:
                logger.warning(
                    "⚠ Restauração concluída com avisos de privilégio DEFINER/TRIGGER "
                    "(dados restaurados, triggers podem estar ausentes): %s",
                    "; ".join(linhas_erro)
                )
        else:
            logger.info("✓ Restauração realizada com sucesso a partir do arquivo: %s", caminho_backup)

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
    
    from src.utils.ui_callbacks import atualizar_treeview as new_atualizar_treeview
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
    
    :param executar_backup_final: Se True, executa um backup final em background.
    """
    global _backup_running, _backup_initialized
    
    # Verificar se backup está habilitado
    if settings and not settings.backup.enabled:
        logger.debug("Sistema de backup desabilitado - nada a parar")
        return
    
    if executar_backup_final and _backup_running:
        try:
            logger.info("Executando backup final em background...")
            # Executar backup em thread separada com timeout para não travar a UI
            backup_thread = threading.Thread(target=_executar_backup_final_thread, daemon=True)
            backup_thread.start()
            # Aguardar no máximo 15 segundos pelo backup
            backup_thread.join(timeout=15)
            if backup_thread.is_alive():
                logger.warning("Backup final excedeu 15s - continuando fechamento sem aguardar")
        except Exception as e:
            logger.error(f"Erro ao executar backup final: {e}")
    
    _backup_running = False
    _backup_initialized = False
    schedule.clear()
    logger.info("Sistema de backup automático encerrado.")


def _executar_backup_final_thread():
    """Executa o backup final em uma thread separada."""
    try:
        resultado = fazer_backup()
        if resultado:
            logger.info("[%s] Backup final concluído com sucesso!", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        else:
            logger.warning("[%s] Falha no backup final.", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    except Exception as e:
        logger.error(f"Erro no backup final em background: {e}")


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