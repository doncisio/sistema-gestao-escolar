# Guia de Compilação - Sistema de Gestão Escolar

Este guia explica como transformar o projeto Python em um executável instalável para Windows.

## 📋 Pré-requisitos

### 1. Instalar PyInstaller
```powershell
pip install pyinstaller
```

### 2. Instalar Inno Setup (para criar instalador)
- Baixe em: https://jrsoftware.org/isdl.php
- Instale a versão mais recente (6.0 ou superior)
- Durante a instalação, marque a opção para adicionar ao PATH

### 3. Criar ícone (opcional)
- Crie ou converta um ícone no formato `.ico`
- Salve como `icon.ico` na raiz do projeto
- Ferramentas online: https://convertico.com/

## 🔨 Processo de Compilação

### Passo 1: Criar o Executável

Execute o script de build:

```powershell
python build_exe.py
```

Este script irá:
- Limpar builds anteriores
- Criar arquivo de informações de versão
- Empacotar todos os arquivos necessários
- Gerar o executável em `dist\GestaoEscolar.exe`

**Tempo estimado:** 2-5 minutos dependendo do tamanho do projeto.

### Passo 2: Testar o Executável

Antes de criar o instalador, teste o executável:

```powershell
.\dist\GestaoEscolar.exe
```

Verifique:
- ✅ A aplicação inicia corretamente
- ✅ Conecta ao banco de dados
- ✅ Todas as funcionalidades funcionam
- ✅ Não há erros de imports ou arquivos faltantes

### Passo 3: Criar o Instalador

#### Opção A: Usando Interface Gráfica do Inno Setup
1. Abra o Inno Setup Compiler
2. Clique em "File" → "Open"
3. Selecione `GestaoEscolar.iss`
4. Clique em "Build" → "Compile"
5. O instalador será criado em `installer_output\`

#### Opção B: Usando Linha de Comando
```powershell
# Se Inno Setup foi adicionado ao PATH
iscc GestaoEscolar.iss

# Ou use o caminho completo
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" GestaoEscolar.iss
```

### Passo 4: Testar o Instalador

1. Execute o instalador criado: `installer_output\GestaoEscolar_Setup_v1.0.0.exe`
2. Siga o assistente de instalação
3. Teste a aplicação instalada

## 📦 Estrutura de Arquivos

Após a compilação, você terá:

```
gestao/
├── dist/
│   └── GestaoEscolar.exe          # Executável standalone
├── installer_output/
│   └── GestaoEscolar_Setup_v1.0.0.exe  # Instalador
├── build/                          # Arquivos temporários (pode deletar)
├── build_exe.py                    # Script de build
├── GestaoEscolar.iss              # Script Inno Setup
├── GestaoEscolar.spec             # Spec do PyInstaller (gerado)
└── version_info.txt               # Informações de versão (gerado)
```

## 🔧 Personalização

### Modificar Informações de Versão

Edite `build_exe.py`:

```python
def create_version_file():
    version_info = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),  # Altere aqui
    # ...
```

### Modificar Configurações do Instalador

Edite `GestaoEscolar.iss`:

```ini
#define MyAppVersion "1.0.0"  ; Versão
#define MyAppPublisher "Seu Nome"  ; Editor
#define MyAppURL "https://seu-site.com"  ; URL
```

### Adicionar Mais Arquivos ao Executável

Edite `build_exe.py`, função `collect_data_files()`:

```python
essentials = [
    ('.env.example', '.'),
    ('seu_arquivo.txt', '.'),  # Adicione aqui
]
```

## 🐛 Solução de Problemas

### Erro: "Module not found"
**Solução:** Adicione o módulo à lista `hidden_imports` em `build_exe.py`:

```python
hidden_imports = [
    'mysql.connector',
    'seu_modulo',  # Adicione aqui
]
```

### Executável muito grande
**Soluções:**
1. Use `--onedir` ao invés de `--onefile` (mais rápido, mas múltiplos arquivos)
2. Use UPX para comprimir: `pip install pyinstaller[compression]`
3. Remova dependências não utilizadas do `requirements.txt`

### Erro ao conectar banco de dados
**Solução:** Certifique-se de que o arquivo `.env` está na mesma pasta que o executável.

### Antivírus bloqueando o executável
**Solução:** 
1. Adicione exceção no antivírus
2. Assine digitalmente o executável (requer certificado)
3. Use `--clean` e `--noconfirm` no PyInstaller

### Erro: "Failed to execute script"
**Soluções:**
1. Execute sem `--windowed` para ver mensagens de erro
2. Verifique os logs em `dist\GestaoEscolar.log`
3. Teste importações manualmente

## 📊 Otimizações

### Reduzir Tamanho do Executável

```python
# Em build_exe.py, adicione:
'--exclude-module=matplotlib',
'--exclude-module=numpy',  # Se não usado
'--exclude-module=scipy',   # Se não usado
```

### Melhorar Tempo de Inicialização

1. Use `--onedir` ao invés de `--onefile`
2. Exclua módulos não utilizados
3. Use lazy imports no código Python

### Build Automatizado

Crie um script `build_all.bat`:

```batch
@echo off
echo Limpando builds anteriores...
rmdir /s /q build dist

echo Criando executável...
python build_exe.py

echo Criando instalador...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" GestaoEscolar.iss

echo Concluído!
pause
```

## 🚀 Distribuição

### Checklist Antes de Distribuir

- [ ] Testar instalação em máquina limpa
- [ ] Verificar conexão com banco de dados
- [ ] Testar todas as funcionalidades principais
- [ ] Verificar arquivo `.env.example` está incluído
- [ ] Documentação atualizada
- [ ] Versão correta em todos os arquivos
- [ ] Screenshots/vídeo tutorial (opcional)

### Onde Hospedar o Instalador

1. **GitHub Releases**: Ideal para projetos open source
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   # Upload do .exe na página de releases
   ```

2. **Google Drive**: Para distribuição privada
3. **Site próprio**: Controle total da distribuição

## 📝 Atualizações Futuras

Para versões futuras:

1. Incremente a versão em `build_exe.py` e `GestaoEscolar.iss`
2. Recompile o executável e instalador
3. Teste em máquina com versão antiga instalada
4. Distribua com notas de atualização (changelog)

## 🔐 Assinatura Digital (Opcional)

Para evitar avisos de segurança do Windows:

1. Obtenha um certificado de assinatura de código
2. Use `signtool.exe` do Windows SDK:
   ```powershell
   signtool sign /f certificado.pfx /p senha /t http://timestamp.digicert.com dist\GestaoEscolar.exe
   ```

## 📞 Suporte

Para problemas durante a compilação:
- Verifique os logs em `build/` e `dist/`
- Consulte documentação do PyInstaller: https://pyinstaller.org/
- Consulte documentação do Inno Setup: https://jrsoftware.org/ishelp/

---

**Última atualização:** Dezembro 2025
