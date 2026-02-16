#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para limpar horários importados"""

import sys
sys.path.insert(0, 'C:\\gestao')

from src.core.conexao import conectar_bd

def limpar_horarios(turma_id=28):
    """Limpa todos os horários importados de uma turma"""
    try:
        conn = conectar_bd()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados")
            return
        
        cursor = conn.cursor()
        
        # Deletar horários
        cursor.execute(
            "DELETE FROM horarios_importados WHERE turma_id = %s",
            (turma_id,)
        )
        
        linhas_deletadas = cursor.rowcount
        conn.commit()
        
        print(f"\n✓ {linhas_deletadas} horários foram removidos da turma ID {turma_id}")
        print(f"Agora você pode reimportar do GEDUC com o ajuste correto do intervalo.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Limpar horários importados')
    parser.add_argument('--turma-id', type=int, default=28, help='ID da turma (padrão: 28)')
    args = parser.parse_args()
    
    limpar_horarios(args.turma_id)
