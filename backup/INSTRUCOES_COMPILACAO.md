# Instruções para Compilação do Sistema de Gerenciamento Escolar

## Pré-requisitos

Antes de iniciar a compilação, verifique se você tem:

1. Python instalado (3.6 ou superior)
2. Todas as dependências do projeto instaladas

## Instalação das Dependências

Para instalar todas as dependências necessárias, execute:

```
pip install -r requirements.txt
```

## Verificação e Correção de Imagens

Antes de compilar, recomendamos verificar se todas as imagens referenciadas no código existem:

### Verificação de Imagens

Execute o script de verificação para encontrar imagens ausentes:

```
python verificar_imagens.py
```

Este script analisará seu código e verificará se todas as imagens referenciadas existem nos locais corretos.

### Correção de Caminhos de Imagens

Se a verificação encontrar problemas, você pode usar o script de correção:

```
python corrigir_caminhos.py
```

Este script interativo irá:
1. Localizar imagens ausentes
2. Encontrar arquivos com o mesmo nome em outros locais
3. Perguntar se deseja copiar as imagens para os diretórios corretos

## Compilação do Executável

### Método Recomendado

1. Execute o arquivo `compilar_exe.bat` com duplo clique
2. O processo irá:
   - Verificar e instalar dependências
   - Verificar as imagens necessárias
   - Compilar o executável
3. O executável será gerado na pasta `dist`

### Método Manual

1. Verifique as imagens: `python verificar_imagens.py`
2. Execute o script de compilação: `python setup.py`

## Customização do Executável

Para personalizar o executável, edite o arquivo `setup.py`:

- `--name=Sistema_Escolar` - Altere para mudar o nome do executável
- `--icon=icon/learning.png` - Altere para mudar o ícone
- `--onefile` - Remove para criar uma pasta com arquivos separados (carrega mais rápido)

## Possíveis Problemas e Soluções

### Imagens não encontradas no executável

Se o executável for executado mas as imagens não aparecerem:

1. Execute `python verificar_imagens.py` para identificar imagens ausentes
2. Execute `python corrigir_caminhos.py` para corrigir os caminhos
3. Compile novamente com `compilar_exe.bat`

### Erro "Failed to execute script"

Este erro pode ocorrer quando:

1. Há importações de módulos que não estão no mesmo diretório
2. Há referências a arquivos externos que não foram incluídos
3. Há problemas de permissão

Solução: Use o método de pasta (`--onefile` removido) para depurar problemas:
Edite `setup.py` e remova a opção `--onefile`.

### Executável muito grande

O executável pode ficar grande (>100MB) porque inclui:
- Python completo
- Todas as bibliotecas (pandas, pillow, etc.)
- Todos os recursos

Este é o comportamento normal do PyInstaller.

## Distribuição

Para distribuir o aplicativo:

1. Copie apenas o arquivo `Sistema_Escolar.exe` da pasta `dist`
2. Distribua para os usuários finais
3. Não é necessário instalar Python nos computadores dos usuários finais 