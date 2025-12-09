# Exemplo de Uso do StorageManager

"""
Este arquivo demonstra como usar o StorageManager
para salvar documentos localmente OU no Google Drive.
"""

from storage_manager import get_storage_manager

# =============================================================================
# EXEMPLO 1: Modo Automático (detecta configuração do .env)
# =============================================================================

# Inicializar gerenciador (lê USAR_GOOGLE_DRIVE do .env)
storage = get_storage_manager()

# Verificar modo ativo
info = storage.obter_info_armazenamento()
print(f"Modo de armazenamento: {info['modo']}")
print(f"Caminho: {info['caminho_armazenamento']}")

# =============================================================================
# EXEMPLO 2: Salvar documento de turma
# =============================================================================

# Salvar lista de presença para uma turma
sucesso, mensagem, caminho = storage.salvar_arquivo(
    arquivo_origem="lista_presenca_temp.pdf",
    categoria="alunos",
    turma="1º Ano",
    nome_arquivo="lista_presenca_janeiro.pdf"
)

if sucesso:
    print(f"✓ {mensagem}")
    print(f"  Salvo em: {caminho}")
else:
    print(f"✗ Erro: {mensagem}")

# =============================================================================
# EXEMPLO 3: Salvar backup do banco de dados
# =============================================================================

from storage_manager import salvar_backup

sucesso, mensagem, caminho = salvar_backup(
    arquivo="backup_redeescola.sql",
    nome="backup_2025_12_09.sql"
)

print(f"{mensagem} - {caminho}")

# =============================================================================
# EXEMPLO 4: Salvar relatório
# =============================================================================

from storage_manager import salvar_relatorio

sucesso, mensagem, caminho = salvar_relatorio(
    arquivo="relatorio_frequencia.pdf",
    tipo="mensais",  # ou "anuais" ou "personalizados"
    nome="frequencia_dezembro_2025.pdf"
)

# =============================================================================
# EXEMPLO 5: Listar arquivos de uma turma
# =============================================================================

arquivos = storage.listar_arquivos(
    categoria="alunos",
    turma="3º Ano"
)

print(f"\nArquivos da turma 3º Ano:")
for arquivo in arquivos:
    print(f"  • {arquivo['nome']} ({arquivo['tamanho']} bytes)")

# =============================================================================
# EXEMPLO 6: Forçar modo específico (ignorar .env)
# =============================================================================

# Forçar modo local
storage_local = get_storage_manager(usar_google_drive=False)

# Forçar modo Google Drive
storage_drive = get_storage_manager(usar_google_drive=True)

# =============================================================================
# EXEMPLO 7: Usar caminho base customizado
# =============================================================================

# Salvar em diretório específico (apenas modo local)
storage_custom = get_storage_manager(
    base_local="D:/DocumentosEscola",
    usar_google_drive=False
)

# =============================================================================
# ESTRUTURA DE PASTAS CRIADA AUTOMATICAMENTE
# =============================================================================

"""
Independente do modo (local ou Drive), a estrutura criada é:

documentos/  (ou Gestao_Escolar/ no Drive)
├── alunos/
│   ├── anos_iniciais/
│   │   ├── 1_ano/
│   │   ├── 2_ano/
│   │   ├── 3_ano/
│   │   ├── 4_ano/
│   │   └── 5_ano/
│   └── anos_finais/
│       ├── 6_ano_a/
│       ├── 6_ano_b/
│       ├── 7_ano/
│       ├── 8_ano/
│       └── 9_ano/
├── funcionarios/
│   ├── professores/
│   ├── administrativo/
│   └── apoio/
├── backup/
├── relatorios/
│   ├── mensais/
│   ├── anuais/
│   └── personalizados/
├── atas/
├── boletins/
├── declaracoes/
└── historicos/
"""

# =============================================================================
# MIGRAÇÃO DE CÓDIGO EXISTENTE
# =============================================================================

"""
Se você tem código que usa caminhos hardcoded do Google Drive:

ANTES:
------
caminho = r"G:\Meu Drive\NADIR_2025\Documentos docentes\Anos Iniciais\1º Ano\lista.pdf"
with open(caminho, 'wb') as f:
    f.write(pdf_data)

DEPOIS:
-------
from storage_manager import salvar_documento_turma

sucesso, msg, caminho = salvar_documento_turma(
    arquivo="temp_lista.pdf",
    turma="1º Ano",
    nome="lista.pdf"
)
"""
