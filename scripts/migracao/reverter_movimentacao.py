"""
Script para reverter a movimentação de arquivos não utilizados.
Execute este script caso a movimentação tenha causado problemas.

Uso:
    python reverter_movimentacao.py
    
    ou especificando o timestamp:
    python reverter_movimentacao.py 20251129_211358
"""
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"c:\gestao")
BACKUP_DIR = BASE_DIR / "arquivos_nao_utilizados"


def reverter_movimentacao(timestamp: str = None):
    """Reverte a movimentação de arquivos."""
    
    if timestamp is None:
        # Encontrar o backup mais recente
        backups = sorted([d for d in BACKUP_DIR.iterdir() if d.is_dir()], reverse=True)
        if not backups:
            print("❌ Nenhum backup encontrado.")
            return False
        backup_path = backups[0]
        timestamp = backup_path.name
    else:
        backup_path = BACKUP_DIR / timestamp
    
    if not backup_path.exists():
        print(f"❌ Backup não encontrado: {backup_path}")
        return False
    
    print(f"📁 Revertendo backup: {backup_path}")
    print("=" * 60)
    
    revertidos = []
    erros = []
    
    for arquivo in backup_path.rglob("*.py"):
        rel_path = arquivo.relative_to(backup_path)
        destino = BASE_DIR / rel_path
        
        try:
            # Criar diretório se necessário
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(arquivo), str(destino))
            revertidos.append(str(rel_path))
            print(f"✅ Revertido: {rel_path}")
        except Exception as e:
            erros.append((str(rel_path), str(e)))
            print(f"❌ Erro ao reverter {rel_path}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Total revertidos: {len(revertidos)}")
    print(f"❌ Erros: {len(erros)}")
    
    if len(erros) == 0 and len(revertidos) > 0:
        # Remover diretório de backup vazio
        try:
            shutil.rmtree(backup_path)
            print(f"\n🗑️  Backup removido: {backup_path}")
        except:
            pass
    
    return len(erros) == 0


if __name__ == "__main__":
    timestamp = sys.argv[1] if len(sys.argv) > 1 else None
    reverter_movimentacao(timestamp)
