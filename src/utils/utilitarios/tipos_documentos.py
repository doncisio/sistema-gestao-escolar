"""
Constantes para tipos de documentos do sistema.
Usar estas constantes ao invés de strings literais para manter consistência.
"""

# Documentos Acadêmicos
TIPO_DECLARACAO = "Declaração"
TIPO_BOLETIM = "Boletim"
TIPO_HISTORICO = "Histórico Escolar"
TIPO_TRANSFERENCIA = "Transferência"
TIPO_ATA = "Ata"

# Listas e Relatórios
TIPO_LISTA_ATUALIZADA = "Lista Atualizada"
TIPO_LISTA_NOTAS = "Lista de Notas"
TIPO_LISTA_FREQUENCIA = "Lista de Frequência"
TIPO_LISTA_REUNIAO = "Lista de Reunião"
TIPO_MOVIMENTO_MENSAL = "Movimento Mensal"

# Documentos Administrativos
TIPO_SOLICITACAO_PROFESSORES = "Solicitação de Professores"
TIPO_FOLHA_PONTO = "Folha de Ponto"
TIPO_RESUMO_PONTO = "Resumo de Ponto"

# Funções auxiliares para categorização
def get_categoria_documento(tipo):
    """Retorna a categoria do documento baseado no tipo"""
    categorias = {
        TIPO_DECLARACAO: "Documentos Acadêmicos",
        TIPO_BOLETIM: "Documentos Acadêmicos",
        TIPO_HISTORICO: "Documentos Acadêmicos",
        TIPO_TRANSFERENCIA: "Documentos Acadêmicos",
        TIPO_ATA: "Documentos Acadêmicos",
        
        TIPO_LISTA_ATUALIZADA: "Listas e Relatórios",
        TIPO_LISTA_NOTAS: "Listas e Relatórios",
        TIPO_LISTA_FREQUENCIA: "Listas e Relatórios",
        TIPO_LISTA_REUNIAO: "Listas e Relatórios",
        TIPO_MOVIMENTO_MENSAL: "Listas e Relatórios",
        
        TIPO_SOLICITACAO_PROFESSORES: "Documentos Administrativos",
        TIPO_FOLHA_PONTO: "Documentos Administrativos",
        TIPO_RESUMO_PONTO: "Documentos Administrativos"
    }
    return categorias.get(tipo, "Outros")