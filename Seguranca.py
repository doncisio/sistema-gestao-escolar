import os
import subprocess
from dotenv import load_dotenv
import schedule
import threading
import time
from datetime import datetime

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
            print("Erro: Credenciais incompletas no arquivo .env.")
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
        
        print(f"✓ Backup local salvo em: {caminho_backup_local}")

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
                print(f"✓ Backup no Google Drive salvo em: {caminho_backup_drive}")
                backup_drive_ok = True
            else:
                print(f"⚠ Diretório do Google Drive não encontrado: {diretorio_drive}")
                print("  Backup salvo apenas localmente.")
                print("  DICA: Certifique-se de que o Google Drive Desktop está instalado e sincronizando.")
        except PermissionError as e:
            print(f"⚠ Sem permissão para escrever no Google Drive: {e}")
            print("  Backup salvo apenas localmente.")
            print("  DICA: Verifique se você está logado no Google Drive Desktop.")
        except Exception as e:
            print(f"⚠ Erro ao salvar no Google Drive: {e}")
            print("  Backup salvo apenas localmente.")
            print("  DICA: Reinstale o Google Drive Desktop se o problema persistir.")

        print("✓ Backup realizado com sucesso!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Erro ao realizar o backup: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
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
            print(f"Usando backup do Google Drive: {caminho_backup}")
        elif os.path.exists(caminho_backup_local):
            caminho_backup = caminho_backup_local
            print(f"Usando backup local: {caminho_backup}")
        else:
            print("Erro: Nenhum arquivo de backup encontrado!")
            print(f"  - Local: {caminho_backup_local}")
            print(f"  - Drive: {caminho_backup_drive}")
            return False

        # Obter credenciais do arquivo .env
        usuario = os.getenv("DB_USER")
        senha = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_NAME")

        if not all([usuario, senha, host, database]):
            print("Erro: Credenciais incompletas no arquivo .env.")
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

        print(f"Restauração realizada com sucesso a partir do arquivo: {caminho_backup}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Erro ao restaurar o backup: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False

# Função para atualizar o Treeview
def atualizar_treeview(treeview, cursor, query):
    try:
        # Verificar se o Treeview ainda existe
        if not treeview or not treeview.winfo_exists():
            print("Erro: O Treeview não está mais ativo.")
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
        print("Erro ao atualizar o Treeview:", e)


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
        print(f"\n[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Iniciando backup automático...")
        resultado = fazer_backup()
        if resultado:
            print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Backup automático concluído com sucesso!")
        else:
            print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Falha no backup automático.")
    else:
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Fora do horário de backup (14h-19h). Backup não executado.")


def agendar_backup_diario():
    """
    Configura o agendamento do backup para ser executado todos os dias às 14:05 e 17:00.
    O backup só será executado se estiver entre 14h e 19h.
    """
    # Agendar backups diários
    schedule.every().day.at("14:05").do(executar_backup_automatico)
    schedule.every().day.at("17:00").do(executar_backup_automatico)
    
    print("\n" + "="*70)
    print("Sistema de Backup Automático Ativado")
    print("="*70)
    print(f"• Horários de execução: 14:05 e 17:00 (todos os dias)")
    print(f"• Janela de execução permitida: 14:00 - 19:00")
    print(f"• Backup final: Ao fechar o programa")
    print(f"• Status: Aguardando próximo horário de backup...")
    print("="*70 + "\n")


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
        print("Sistema de backup automático já está em execução.")
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
        print("\n" + "="*70)
        print("Executando backup final antes de encerrar o sistema...")
        print("="*70)
        resultado = fazer_backup()
        if resultado:
            print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Backup final concluído com sucesso!")
        else:
            print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Falha no backup final.")
        print("="*70 + "\n")
    
    _backup_running = False
    schedule.clear()
    print("\nSistema de backup automático encerrado.")


def status_backup_automatico():
    """
    Retorna o status do sistema de backup automático.
    """
    global _backup_thread
    
    if _backup_thread is not None and _backup_thread.is_alive():
        proximos_jobs = schedule.get_jobs()
        if proximos_jobs:
            print("\nStatus do Backup Automático:")
            print("="*70)
            print(f"• Sistema: ATIVO")
            print(f"• Thread: Em execução")
            print(f"• Próximos backups agendados: 14:05 e 17:00")
            print(f"• Backup final: Ao fechar o programa")
            print("="*70)
            return True
        else:
            print("\nSistema de backup automático está rodando, mas sem agendamentos.")
            return False
    else:
        print("\nSistema de backup automático NÃO está ativo.")
        return False