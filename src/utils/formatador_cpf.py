"""
Utilitário para formatação automática de CPF em campos de entrada (Entry).
Formata CPF no padrão NNN.NNN.NNN-NN enquanto o usuário digita.
"""
from tkinter import StringVar


def formatar_cpf_auto(event):
    """
    Formata automaticamente o CPF enquanto o usuário digita.
    Aplica o formato: NNN.NNN.NNN-NN
    
    Args:
        event: Evento do tkinter (contém o widget Entry)
    """
    widget = event.widget
    
    # Prevenir recursão
    if hasattr(widget, '_formatando_cpf') and widget._formatando_cpf:
        return
    
    widget._formatando_cpf = True
    
    try:
        texto = widget.get()
        
        # Salva a posição atual do cursor
        cursor_pos = widget.index("insert")
        
        # Conta quantos dígitos existem antes do cursor
        texto_antes_cursor = texto[:cursor_pos]
        digitos_antes_cursor = len(''.join(filter(str.isdigit, texto_antes_cursor)))
        
        # Remove tudo que não é dígito
        apenas_numeros = ''.join(filter(str.isdigit, texto))
        
        # Limita a 11 dígitos
        apenas_numeros = apenas_numeros[:11]
        
        # Formata conforme o tamanho
        if len(apenas_numeros) <= 3:
            texto_formatado = apenas_numeros
        elif len(apenas_numeros) <= 6:
            texto_formatado = f"{apenas_numeros[:3]}.{apenas_numeros[3:]}"
        elif len(apenas_numeros) <= 9:
            texto_formatado = f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:]}"
        else:
            texto_formatado = f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"
        
        # Só atualiza se o texto mudou
        if texto != texto_formatado:
            # Atualiza o texto
            widget.delete(0, "end")
            widget.insert(0, texto_formatado)
            
            # Calcula a nova posição do cursor
            # Conta caracteres no texto formatado até atingir o número de dígitos desejado
            nova_pos = 0
            digitos_contados = 0
            
            for i, char in enumerate(texto_formatado):
                if digitos_contados >= digitos_antes_cursor:
                    break
                if char.isdigit():
                    digitos_contados += 1
                nova_pos = i + 1
            
            # Posiciona o cursor
            widget.icursor(nova_pos)
    finally:
        widget._formatando_cpf = False


def aplicar_formatacao_cpf(entry_widget):
    """
    Aplica formatação automática de CPF em um widget Entry.
    
    Args:
        entry_widget: Widget Entry do tkinter
    """
    # Remove qualquer binding anterior de KeyRelease
    entry_widget.unbind('<KeyRelease>')
    # Aplica o novo binding
    entry_widget.bind('<KeyRelease>', formatar_cpf_auto)


def obter_cpf_limpo(texto_cpf):
    """
    Remove formatação do CPF, retornando apenas os dígitos.
    
    Args:
        texto_cpf: CPF formatado ou não
        
    Returns:
        String com apenas os dígitos do CPF
    """
    if not texto_cpf:
        return ""
    return ''.join(filter(str.isdigit, texto_cpf))


def obter_cpf_formatado(texto_cpf):
    """
    Retorna o CPF no formato NNN.NNN.NNN-NN.
    
    Args:
        texto_cpf: CPF (formatado ou não)
        
    Returns:
        CPF formatado ou string vazia se inválido
    """
    apenas_numeros = obter_cpf_limpo(texto_cpf)
    
    if len(apenas_numeros) != 11:
        return ""
    
    return f"{apenas_numeros[:3]}.{apenas_numeros[3:6]}.{apenas_numeros[6:9]}-{apenas_numeros[9:]}"
