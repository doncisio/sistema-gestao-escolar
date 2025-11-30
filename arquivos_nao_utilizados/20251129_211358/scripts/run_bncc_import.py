#!/usr/bin/env python3
"""
Helper script para executar a importação BNCC com credenciais interativas ou de .env
Uso:
  python scripts/run_bncc_import.py [--sheet SHEET_NAME]
"""
import argparse
import getpass
import os
import sys
from pathlib import Path
import subprocess

# tentar carregar .env se existir (usando python-dotenv se disponível)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parents[1] / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded .env from {env_path}")
except ImportError:
    pass

def get_credentials():
    """Obtém credenciais de env vars ou pede interativamente."""
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', '3306'))
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_NAME', 'redeescola')
    
    if not user:
        user = input(f"DB User (default: root): ").strip() or 'root'
    if not password:
        password = getpass.getpass(f"DB Password for {user}@{host}: ")
    
    return host, port, user, password, database

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Executar importação BNCC com credenciais seguras')
    parser.add_argument('--sheet', default=None, help='Nome da sheet a importar (opcional, padrão: todas)')
    parser.add_argument('--file', default=str(Path(__file__).resolve().parents[1] / 'MapasDeFocoBncc_Unificados.xlsx'))
    args = parser.parse_args()
    
    host, port, user, password, database = get_credentials()
    
    script_path = Path(__file__).resolve().parents[1] / 'importar_bncc_from_excel.py'
    
    cmd = [
        sys.executable,
        str(script_path),
        '--file', args.file,
        '--host', host,
        '--port', str(port),
        '--user', user,
        '--database', database,
        '--password', password
    ]
    
    if args.sheet:
        cmd.extend(['--sheet', args.sheet])
    
    print(f"Executando importação BNCC...")
    print(f"  File: {args.file}")
    print(f"  Sheet: {args.sheet or 'TODAS'}")
    print(f"  Database: {user}@{host}:{port}/{database}")
    print()
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
