"""Tema simples com cores/constantes usadas pela UI centralizada.

Colocar as cores aqui facilita a alteração de aparência e a revisão
durante refactors que movem widgets para `ui/`.
"""

# Cores principais
CO_BG = '#003A70'       # cor principal de fundo (co1)
CO_FG = '#F5F5F5'       # cor de texto (co0)
CO_ACCENT = '#4A86E8'   # cor de destaque/acao (co4)
CO_WARN = '#F7B731'     # cor do botão/aviso (co6)

# Cores para a interface de Transição de Ano Letivo
CO_BRANCO = "#ffffff"       # branco (co0)
CO_AZUL_ESCURO = "#3b5998"  # azul escuro (co1)
CO_VERDE = "#4CAF50"        # verde - sucesso (co2)
CO_VERMELHO = "#f44336"     # vermelho - erro/perigo (co3)
CO_LARANJA = "#ff9800"      # laranja - aviso (co4)
CO_FUNDO_CLARO = "#f0f0f0"  # fundo claro para janelas

# Alias para compatibilidade
CORES_TRANSICAO = {
    'branco': CO_BRANCO,
    'azul_escuro': CO_AZUL_ESCURO,
    'verde': CO_VERDE,
    'vermelho': CO_VERMELHO,
    'laranja': CO_LARANJA,
    'fundo': CO_FUNDO_CLARO,
}
