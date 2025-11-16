from config_logs import get_logger
logger = get_logger(__name__)
"""
Script para limpeza de documentos duplicados no banco de dados e Google Drive.

Este script identifica documentos que foram criados múltiplas vezes com as mesmas
características (tipo, aluno/funcionário, finalidade) e mantém apenas a versão mais recente,
removendo as antigas do banco de dados e do Google Drive.

Autor: Sistema de Gestão Escolar
Data: 07/11/2025
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def setup_google_drive():
    """Configura a autenticação com o Google Drive"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def conectar_bd():
    """Conecta ao banco de dados"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            auth_plugin='mysql_native_password'
        )
        if conn.is_connected():
            logger.info("✓ Conectado ao banco de dados com sucesso!")
            return conn
    except Error as e:
        logger.error(f"✗ Erro ao conectar ao banco de dados: {e}")
        return None

def identificar_duplicados(cursor):
    """Identifica documentos duplicados no banco de dados"""
    logger.info("\n🔍 Identificando documentos duplicados...\n")
    
    query = """
        SELECT 
            tipo_documento,
            aluno_id,
            funcionario_id,
            finalidade,
            COUNT(*) as total,
            GROUP_CONCAT(id ORDER BY data_de_upload DESC) as ids,
            GROUP_CONCAT(DATE_FORMAT(data_de_upload, '%d/%m/%Y %H:%i:%s') 
                        ORDER BY data_de_upload DESC 
                        SEPARATOR ' | ') as datas
        FROM documentos_emitidos
        GROUP BY tipo_documento, aluno_id, funcionario_id, finalidade
        HAVING COUNT(*) > 1
        ORDER BY total DESC, tipo_documento
    """
    
    cursor.execute(query)
    duplicados = cursor.fetchall()
    
    return duplicados

def mostrar_relatorio(duplicados):
    """Mostra relatório de duplicados encontrados"""
    if not duplicados:
        logger.info("✓ Nenhum documento duplicado encontrado!")
        return False
    
    total_grupos = len(duplicados)
    total_docs_remover = sum(dup[4] - 1 for dup in duplicados)
    
    logger.info(f"{'='*80}")
    logger.info(f"RELATÓRIO DE DOCUMENTOS DUPLICADOS")
    logger.info(f"{'='*80}\n")
    logger.info(f"Total de grupos duplicados: {total_grupos}")
    logger.info(f"Total de documentos a remover: {total_docs_remover}\n")
    logger.info(f"{'='*80}\n")
    
    for idx, dup in enumerate(duplicados, 1):
        tipo, aluno_id, func_id, finalidade, total, ids_str, datas_str = dup
        
        pessoa = f"Aluno ID: {aluno_id}" if aluno_id else f"Funcionário ID: {func_id}" if func_id else "Sem vínculo"
        final = finalidade if finalidade else "N/A"
        
        logger.info(f"[{idx:3d}] {tipo}")
        logger.info(f"      Pessoa: {pessoa}")
        logger.info(f"      Finalidade: {final}")
        logger.info(f"      Total de versões: {total}")
        logger.info(f"      IDs: {ids_str}")
        logger.info(f"      Datas: {datas_str}")
        logger.info()
    
    logger.info(f"{'='*80}\n")
    return True

def limpar_duplicados(conn, cursor, service, duplicados, modo='simulacao'):
    """
    Remove documentos duplicados
    
    Args:
        modo: 'simulacao' ou 'executar'
    """
    total_removidos = 0
    total_erros = 0
    total_grupos = len(duplicados)
    
    if modo == 'simulacao':
        logger.info("\n🔄 MODO SIMULAÇÃO - Nenhum arquivo será realmente removido\n")
    else:
        logger.info("\n⚠️  MODO EXECUÇÃO - Os arquivos serão PERMANENTEMENTE removidos\n")
    
    logger.info(f"{'='*80}\n")
    
    for idx, dup in enumerate(duplicados, 1):
        tipo, aluno_id, func_id, finalidade, total, ids_str, datas_str = dup
        
        ids = [int(x) for x in ids_str.split(',')]
        # Manter o primeiro ID (mais recente) e remover os outros
        id_manter = ids[0]
        ids_remover = ids[1:]
        
        pessoa = f"Aluno ID: {aluno_id}" if aluno_id else f"Funcionário ID: {func_id}" if func_id else "Sem vínculo"
        
        logger.info(f"[{idx}/{total_grupos}] Processando: {tipo} - {pessoa}")
        logger.info(f"  ✓ Mantendo versão mais recente (ID: {id_manter})")
        logger.info(f"  ⚠ Removendo {len(ids_remover)} versão(ões) antiga(s):")
        
        for doc_id in ids_remover:
            try:
                # Buscar informações do documento
                cursor.execute(
                    "SELECT link_no_drive, nome_arquivo FROM documentos_emitidos WHERE id = %s",
                    (doc_id,)
                )
                resultado = cursor.fetchone()
                
                if resultado:
                    link, nome = resultado
                    logger.info(f"    - ID {doc_id}: {nome}")
                    
                    if modo == 'executar':
                        # Excluir do Google Drive
                        if link:
                            try:
                                if '/d/' in link:
                                    drive_id = link.split('/d/')[1].split('/')[0]
                                elif 'id=' in link:
                                    drive_id = link.split('id=')[1].split('&')[0]
                                else:
                                    drive_id = link.split('/')[-2]
                                
                                service.files().delete(fileId=drive_id).execute()
                                logger.info(f"      ✓ Removido do Google Drive")
                            except Exception as e:
                                logger.error(f"      ⚠ Erro ao remover do Drive: {str(e)[:60]}")
                        
                        # Excluir do banco de dados
                        cursor.execute("DELETE FROM documentos_emitidos WHERE id = %s", (doc_id,))
                        logger.info(f"      ✓ Removido do banco de dados")
                    else:
                        logger.info(f"      [SIMULAÇÃO] Seria removido do Drive e banco")
                    
                    total_removidos += 1
                
            except Exception as e:
                logger.error(f"    ✗ Erro ao processar ID {doc_id}: {str(e)[:60]}")
                total_erros += 1
        
        if modo == 'executar':
            conn.commit()
        
        logger.info()
    
    logger.info(f"{'='*80}")
    logger.info(f"\nRESUMO DA LIMPEZA:")
    logger.info(f"  Grupos processados: {total_grupos}")
    logger.info(f"  Documentos removidos: {total_removidos}")
    logger.info(f"  Erros encontrados: {total_erros}")
    
    if modo == 'simulacao':
        logger.info(f"\n⚠️  Esta foi uma SIMULAÇÃO. Nenhum arquivo foi removido.")
    else:
        logger.info(f"\n✓ Limpeza executada com sucesso!")
    
    logger.info(f"{'='*80}\n")

def main():
    logger.info("\n" + "="*80)
    logger.info(" LIMPEZA DE DOCUMENTOS DUPLICADOS - SISTEMA DE GESTÃO ESCOLAR")
    logger.info("="*80 + "\n")
    
    # Conectar ao banco
    conn = conectar_bd()
    if not conn:
        logger.info("✗ Não foi possível conectar ao banco de dados. Abortando.")
        return
    
    cursor = conn.cursor()
    
    # Conectar ao Google Drive
    logger.info("🔄 Conectando ao Google Drive...")
    try:
        service = setup_google_drive()
        logger.info("✓ Conectado ao Google Drive com sucesso!\n")
    except Exception as e:
        logger.error(f"✗ Erro ao conectar ao Google Drive: {e}")
        cursor.close()
        conn.close()
        return
    
    # Identificar duplicados
    duplicados = identificar_duplicados(cursor)
    
    # Mostrar relatório
    tem_duplicados = mostrar_relatorio(duplicados)
    
    if not tem_duplicados:
        cursor.close()
        conn.close()
        return
    
    # Perguntar o que fazer
    logger.info("O que deseja fazer?")
    logger.info("1 - Executar SIMULAÇÃO (apenas mostra o que seria removido)")
    logger.info("2 - EXECUTAR LIMPEZA (remove permanentemente os duplicados)")
    logger.info("3 - Cancelar")
    
    escolha = input("\nDigite sua escolha (1, 2 ou 3): ").strip()
    
    if escolha == '1':
        limpar_duplicados(conn, cursor, service, duplicados, modo='simulacao')
    elif escolha == '2':
        confirmacao = input("\n⚠️  ATENÇÃO: Esta ação é IRREVERSÍVEL!\nDigite 'CONFIRMAR' para continuar: ")
        if confirmacao == 'CONFIRMAR':
            limpar_duplicados(conn, cursor, service, duplicados, modo='executar')
        else:
            logger.info("\n✗ Operação cancelada.")
    else:
        logger.info("\n✗ Operação cancelada.")
    
    # Fechar conexões
    cursor.close()
    conn.close()
    logger.info("\n✓ Conexões fechadas. Script finalizado.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n✗ Script interrompido pelo usuário.")
    except Exception as e:
        logger.error(f"\n✗ Erro inesperado: {e}")