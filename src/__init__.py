"""
Módulo src - Código fonte principal do sistema.

Estrutura:
- core: Configurações e componentes essenciais
- models: Classes de domínio
- services: Lógica de negócio
- ui: Interfaces gráficas
- utils: Utilitários
- relatorios: Geração de relatórios
- interfaces: Interfaces especializadas
- gestores: Gerenciadores de processos
- importadores: Scripts de importação
- avaliacoes: Sistema de avaliações
"""

import sys
import os

# Adicionar diretório src ao path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
