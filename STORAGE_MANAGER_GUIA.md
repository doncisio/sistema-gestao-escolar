# Sistema de Armazenamento - Guia Completo

## 📋 Visão Geral

O `StorageManager` gerencia o salvamento de documentos do sistema de forma unificada, suportando **OU** armazenamento local **OU** Google Drive (escolha exclusiva).

## 🎯 Características

- ✅ **Modo Único**: Local OU Google Drive (não simultâneo)
- ✅ **Mesma Estrutura**: Pastas idênticas em ambos os modos
- ✅ **Auto-detecção**: Lê configuração do `.env` automaticamente
- ✅ **Fallback Inteligente**: Se Drive não disponível, usa local
- ✅ **API Simples**: Funções de conveniência para casos comuns

## ⚙️ Configuração

### Via Assistente de Configuração

Durante a instalação, o wizard pergunta:

```
Escolha onde os documentos serão salvos:

( ) 💾 Armazenamento Local (Recomendado)
( ) ☁️ Google Drive
```

A escolha é salva no `.env`:

```ini
# Armazenamento Local
USAR_GOOGLE_DRIVE=False

# OU Google Drive
USAR_GOOGLE_DRIVE=True
```

### Configuração Manual

Edite o arquivo `.env`:

```ini
# Para armazenamento local
USAR_GOOGLE_DRIVE=False

# Para Google Drive (requer credentials.json)
USAR_GOOGLE_DRIVE=True
```

## 🚀 Uso Básico

### Inicialização

```python
from storage_manager import get_storage_manager

# Auto-detecta modo do .env
storage = get_storage_manager()

# Verificar modo ativo
info = storage.obter_info_armazenamento()
print(f"Modo: {info['modo']}")  # "Local" ou "Google Drive"
```

### Salvar Documentos de Turma

```python
sucesso, mensagem, caminho = storage.salvar_arquivo(
    arquivo_origem="documento.pdf",
    categoria="alunos",
    turma="1º Ano",
    nome_arquivo="lista_presenca.pdf"
)

if sucesso:
    print(f"Salvo em: {caminho}")
```

### Salvar Backup

```python
from storage_manager import salvar_backup

sucesso, msg, caminho = salvar_backup(
    arquivo="backup.sql",
    nome="backup_2025_12_09.sql"
)
```

### Salvar Relatório

```python
from storage_manager import salvar_relatorio

sucesso, msg, caminho = salvar_relatorio(
    arquivo="relatorio.pdf",
    tipo="mensais",  # mensais, anuais, ou personalizados
    nome="frequencia_dezembro.pdf"
)
```

### Listar Arquivos

```python
arquivos = storage.listar_arquivos(
    categoria="alunos",
    turma="3º Ano"
)

for arq in arquivos:
    print(f"{arq['nome']} - {arq['tamanho']} bytes")
```

## 📁 Estrutura de Pastas

Ambos os modos criam a mesma estrutura:

```
📂 Local: ./documentos/
📂 Drive: Google Drive/Gestao_Escolar/

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
```

## 🔄 Funcionamento por Modo

### Modo Local

```python
USAR_GOOGLE_DRIVE=False
```

- ✅ Documentos salvos em `./documentos/`
- ✅ Não requer internet
- ✅ Acesso imediato
- ✅ Controle total dos arquivos

**Ideal para**:
- Instalações standalone
- Ambientes sem internet confiável
- Escolas com servidor local

### Modo Google Drive

```python
USAR_GOOGLE_DRIVE=True
```

- ✅ Documentos salvos no Google Drive
- ✅ Acesso de qualquer lugar
- ✅ Backup automático na nuvem
- ✅ Compartilhamento facilitado

**Requer**:
1. `credentials.json` configurado
2. Autorização OAuth na primeira vez
3. Google Drive Desktop instalado (recomendado)

**Ideal para**:
- Acesso multi-dispositivo
- Equipe distribuída
- Backup automático

## 🔧 API Completa

### Classe Principal

```python
class StorageManager:
    def __init__(
        self,
        base_local: Optional[str] = None,
        usar_google_drive: bool = None
    )
    
    def salvar_arquivo(
        self,
        arquivo_origem: str,
        categoria: str,
        subcategoria: Optional[str] = None,
        nome_arquivo: Optional[str] = None,
        turma: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]
    
    def listar_arquivos(
        self,
        categoria: str,
        subcategoria: Optional[str] = None,
        turma: Optional[str] = None
    ) -> list
    
    def obter_info_armazenamento(self) -> dict
    
    def obter_caminho_turma(self, nome_turma: str) -> Optional[Path]
```

### Funções de Conveniência

```python
# Salvar documento de turma
salvar_documento_turma(
    arquivo: str,
    turma: str,
    nome: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]

# Salvar backup
salvar_backup(
    arquivo: str,
    nome: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]

# Salvar relatório
salvar_relatorio(
    arquivo: str,
    tipo: str = "personalizados",
    nome: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]
```

## 🔀 Migração de Código Legado

### Antes (Hardcoded)

```python
# Código antigo com caminho fixo
PASTAS_TURMAS = {
    "1º Ano": r"G:\Meu Drive\NADIR_2025\Docs\1º Ano",
}

caminho = PASTAS_TURMAS["1º Ano"]
arquivo_final = os.path.join(caminho, "lista.pdf")
shutil.copy("temp.pdf", arquivo_final)
```

### Depois (StorageManager)

```python
# Código novo - funciona local ou Drive
from storage_manager import salvar_documento_turma

sucesso, msg, caminho = salvar_documento_turma(
    arquivo="temp.pdf",
    turma="1º Ano",
    nome="lista.pdf"
)
```

## 🎯 Exemplos Práticos

### Salvar Lista de Reunião

```python
from storage_manager import get_storage_manager

storage = get_storage_manager()

# Gerar PDF
pdf_path = gerar_lista_reuniao_pdf("3º Ano")

# Salvar no sistema
sucesso, msg, caminho = storage.salvar_arquivo(
    arquivo_origem=pdf_path,
    categoria="alunos",
    turma="3º Ano",
    nome_arquivo=f"lista_reuniao_{datetime.now().strftime('%Y%m%d')}.pdf"
)
```

### Salvar Histórico Escolar

```python
sucesso, msg, caminho = storage.salvar_arquivo(
    arquivo_origem="historico_temp.pdf",
    categoria="historicos",
    nome_arquivo=f"historico_aluno_{aluno_id}.pdf"
)
```

### Backup Automático

```python
from storage_manager import salvar_backup
import subprocess
from datetime import datetime

# Fazer dump do MySQL
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f"backup_{timestamp}.sql"

subprocess.run([
    "mysqldump",
    "-u", "user",
    "-p", "password",
    "database",
    "-r", backup_file
])

# Salvar usando StorageManager (local ou Drive)
sucesso, msg, caminho = salvar_backup(backup_file)
```

## ⚠️ Observações Importantes

### Modo Google Drive

1. **Primeira Execução**: Requer autorização OAuth no navegador
2. **Token Salvo**: Autorizações futuras são automáticas
3. **Drive Desktop**: Recomendado para sincronização em tempo real
4. **Sem Drive Desktop**: Usa apenas API (mais lento)

### Modo Local

1. **Permissões**: Garanta que o diretório tem permissões de escrita
2. **Backup**: Configure backup externo (não automático)
3. **Espaço**: Monitore espaço em disco

## 🐛 Troubleshooting

### "Google Drive não disponível"

```
StorageManager: Google Drive não disponível, usando armazenamento local
```

**Causas**:
- `credentials.json` não encontrado
- Bibliotecas Google não instaladas
- Drive Desktop não instalado

**Solução**:
1. Verifique `credentials.json` na raiz do projeto
2. `pip install google-auth google-api-python-client`
3. Instale Google Drive Desktop (opcional)

### "Turma não mapeada"

```python
return False, f"Turma não mapeada: {turma}", None
```

**Solução**: Adicione a turma ao método `obter_caminho_turma()` em `storage_manager.py`

### Trocar de Modo

Para trocar entre Local e Google Drive:

1. Edite `.env`:
   ```ini
   USAR_GOOGLE_DRIVE=True  # ou False
   ```

2. Reinicie a aplicação

3. Documentos antigos não são migrados automaticamente
   - Use script de migração se necessário

## 📊 Comparação de Modos

| Característica | Local | Google Drive |
|----------------|-------|--------------|
| Internet | ❌ Não requer | ✅ Requer |
| Velocidade | ⚡ Instantâneo | 🐌 Depende da conexão |
| Backup | ⚠️ Manual | ✅ Automático |
| Acesso Remoto | ❌ Não | ✅ Sim |
| Custo | ✅ Grátis | ⚠️ Pode ter limites |
| Configuração | ✅ Simples | ⚠️ Requer OAuth |

## 🔒 Segurança

- ✅ Credenciais nunca são armazenadas em código
- ✅ Token OAuth criptografado localmente
- ✅ Permissões baseadas em perfil (futuro)
- ✅ Logs de acesso a arquivos

## 📝 Licença

Este módulo faz parte do Sistema de Gestão Escolar.
Copyright (c) 2025 - MIT License
