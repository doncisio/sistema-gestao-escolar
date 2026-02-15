from __future__ import annotations
from datetime import datetime, date
import calendar
from typing import Optional, Union


def nome_mes_pt(mes_num: int, capitalize: bool = True) -> str:
    meses = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }
    nome = meses.get(mes_num, str(mes_num))
    if not capitalize:
        return nome.lower()
    return nome


def formatar_data(data_valor: Optional[Union[str, datetime, date]]) -> str:
    """Formata uma data para o padrão dd/mm/aaaa.

    Aceita objetos `datetime.date`, `datetime.datetime` ou strings em formatos
    comuns retornados pelo banco. Em caso de erro retorna a representação str().
    """
    if not data_valor:
        return ""
    if isinstance(data_valor, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
            try:
                d = datetime.strptime(data_valor, fmt)
                return d.strftime("%d/%m/%Y")
            except Exception:
                continue
        return data_valor
    try:
        # datetime or date
        return data_valor.strftime("%d/%m/%Y")
    except Exception:
        return str(data_valor)


def formatar_data_extenso(data: Optional[Union[date, datetime]] = None) -> str:
    """Formata data por extenso em português (ex: '3 de outubro de 2025').

    Se `data` for None, utiliza a data atual.
    """
    if data is None:
        data = date.today()
    if isinstance(data, datetime):
        data = data.date()

    meses = {
        1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
        5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
        9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
    }

    return f"{data.day} de {meses.get(data.month, str(data.month))} de {data.year}"


def periodo_mes_referencia(mes: int, ano: int) -> str:
    """Retorna período do mês no formato '1 a <ultimo> de <Mês> de <ano>'."""
    ultimo = calendar.monthrange(ano, mes)[1]
    return f"1 a {ultimo} de {nome_mes_pt(mes)} de {ano}"


def get_nome_mes(numero_mes: int, uppercase: bool = True) -> str:
    """Retorna o nome do mês para usos que esperam MAIÚSCULAS (compatibilidade).

    Ex.: get_nome_mes(1) -> 'JANEIRO'
    """
    nome = nome_mes_pt(numero_mes, capitalize=True)
    return nome.upper() if uppercase else nome


def aplicar_mascara_data(entry_widget) -> None:
    """
    Aplica máscara de formatação automática DD/MM/AAAA a um Entry widget.
    
    Comportamento:
    - Ao digitar 2 dígitos (DD), adiciona "/" automaticamente
    - Ao digitar 4 dígitos (DD/MM), adiciona "/" automaticamente
    - Filtra apenas números (ignora letras e caracteres especiais)
    - Formato final: DD/MM/AAAA
    
    Args:
        entry_widget: Widget Entry do tkinter
    """
    def formatar_data_input(event):
        # Ignora teclas especiais de navegação
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Tab', 'Return'):
            return
        
        # Pega o conteúdo atual
        conteudo = entry_widget.get()
        
        # Filtra apenas números
        apenas_numeros = ''.join(c for c in conteudo if c.isdigit())
        
        # Limita a 8 dígitos (DDMMAAAA)
        if len(apenas_numeros) > 8:
            apenas_numeros = apenas_numeros[:8]
        
        # Formata com as barras
        novo_conteudo = ''
        for i, char in enumerate(apenas_numeros):
            if i == 2 or i == 4:
                novo_conteudo += '/'
            novo_conteudo += char
        
        # Atualiza o campo se houver mudança
        if novo_conteudo != conteudo:
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, novo_conteudo)
            # Posiciona o cursor no final
            entry_widget.icursor('end')
    
    # Vincula o evento de tecla ao entry
    entry_widget.bind('<KeyRelease>', formatar_data_input)
