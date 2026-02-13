# Gerador de Certificado de Conclusão em PDF

Este script Python gera certificados de conclusão do Ensino Fundamental em formato PDF para alunos cadastrados no sistema.

## Características

- **Busca automática** dos dados do aluno no banco de dados
- **Layout profissional** com imagem de fundo e brasões
- **Formatação adequada** para certificado oficial
- **Geração rápida** em PDF de alta qualidade
- **Funcionamento offline** - imagens armazenadas localmente
- **Texto justificado** com margens respeitadas
- **Bordas e espaçamento** adequados para impressão

## Instalação das Dependências

Antes de usar o script pela primeira vez, instale as bibliotecas necessárias:

```bash
pip install -r requirements_certificado.txt
```

Ou instale manualmente:

```bash
pip install reportlab
```

## Configuração Inicial (Primeira vez)

### Opção 1: Download automático das imagens (recomendado)

Execute o script de configuração que baixará as imagens necessárias:

```bash
python baixar_imagens_certificado.py
```

Este script irá:
- Criar a pasta `imagens/` se não existir
- Baixar as 3 imagens necessárias (fundo e brasões)
- Verificar se todas foram baixadas com sucesso

### Opção 2: Download manual via PowerShell

```powershell
New-Item -ItemType Directory -Force -Path "imagens"
Invoke-WebRequest -Uri "https://geduc-data.s3.us-east-1.amazonaws.com/logo/fundo_paco.png" -OutFile "imagens\fundo_paco.png"
Invoke-WebRequest -Uri "https://geduc-data.s3.us-east-1.amazonaws.com/logo/pacoCertificado.png" -OutFile "imagens\pacoCertificado.png"
Invoke-WebRequest -Uri "https://geduc-data.s3.us-east-1.amazonaws.com/logo/brasao%20maranhao.png" -OutFile "imagens\brasao maranhao.png"
```

**Importante**: Este passo precisa ser feito **apenas uma vez**. Após baixar as imagens, o sistema funcionará **completamente offline**.

## Uso

### Opção 1: Usando o arquivo batch (Windows)

```cmd
executar_certificado.bat ID_DO_ALUNO
```

Exemplo:
```cmd
executar_certificado.bat 1234
```

Com nome de arquivo personalizado:
```cmd
executar_certificado.bat 1234 "certificado_joao.pdf"
```

### Opção 2: Executando diretamente com Python

```bash
python gerar_certificado_pdf.py ID_DO_ALUNO [arquivo_saida.pdf]
```

Exemplos:
```bash
# Gera na pasta certificados/
python gerar_certificado_pdf.py 1234

# Especifica o nome do arquivo
python gerar_certificado_pdf.py 1234 meu_certificado.pdf

# Especifica caminho completo
python gerar_certificado_pdf.py 1234 "C:\Documentos\certificado_aluno_1234.pdf"
```

### Opção 3: Importando como módulo

```python
from gerar_certificado_pdf import gerar_certificado_pdf

# Gera o certificado
arquivo = gerar_certificado_pdf(aluno_id=1234)
if arquivo:
    print(f"Certificado gerado: {arquivo}")
```

## Estrutura de Dados

O script busca as seguintes informações do banco de dados:

- **Nome do aluno**
- **Data de nascimento**
- **Local de nascimento e UF**
- **Nomes dos responsáveis** (pai e mãe)
- **Nome da escola**
- **Ano letivo**
- **Status da matrícula**

## Saída

Por padrão, os certificados são salvos na pasta `certificados/` com o nome:
```
certificado_aluno_[ID].pdf
```

Exemplo: `certificado_aluno_1234.pdf`

## Formato do Certificado

O certificado segue o modelo oficial com melhorias:

1. **Cabeçalho**: Brasões e identificação da secretaria
2. **Título**: "CERTIFICADO" em destaque
3. **Corpo do texto**: Informações do aluno com **texto justificado**
4. **Data por extenso**: Local e data de emissão
5. **Assinaturas**: Espaço para Secretário(a) e Gestor(a) Escolar
6. **Margens**: 100mm em todos os lados para impressão perfeita
## Personalização

Para personalizar o certificado, edite o arquivo `gerar_certificado_pdf.py`:

- **Fontes**: Altere as variáveis `fonte_titulo` e `fonte_texto`
- **Margens**: Ajuste `margem_esquerda`, `margem_direita`, `margem_superior`, `margem_inferior`
- **Tamanho da fonte**: Modifique `fontSize` no estilo justificado
- **Textos**: Customize os textos do certificado
- **Espaçamento**: Ajuste `leading` para espaçamento entre linhas

## Estrutura de Arquivos

```
gestao/
├── gerar_certificado_pdf.py          # Script principal
├── baixar_imagens_certificado.py    # Script para baixar imagens
├── executar_certificado.bat         # Atalho Windows
├── requirements_certificado.txt     # Dependências
├── README_CERTIFICADO.md           # Esta documentação
├── imagens/                        # Pasta de imagens (criar)
│   ├── fundo_paco.png             # Fundo do certificado
│   ├── pacoCertificado.png        # Brasão da prefeitura
│   └── brasao maranhao.png        # Brasão do Maranhão
└── certificados/                   # PDFs gerados (criado automaticamente)
    └── certificado_aluno_XXX.pdf
```Gothic Bold
- **Fonte texto**: Helvetica 15pt ou Century Gothic
- **Alinhamento**: Justificado para corpo do texto
- **Imagens**: Armazenadas localmente em `imagens/`
- **Brasões**: 70x70mm cada
- **Espaçamento**: Automático e proporcional

## Personalização
### Erro: "Imagem não encontrada"
- Execute `python baixar_imagens_certificado.py` para baixar as imagens
- Verifique se a pasta `imagens/` existe
- Certifique-se de ter as 3 imagens: fundo_paco.png, pacoCertificado.png, brasao maranhao.png

### Texto saindo da página
- As margens estão configuradas para 100mm
- O texto é justificado automaticamente
- Verifique se os nomes não são excessivamente longos

### Bordas não aparecem
- As bordas estão na imagem de fundo (fundo_paco.png)
## Requisitos do Sistema

- Python 3.7+
- MySQL/MariaDB
- Biblioteca: reportlab
- Espaço em disco: ~5MB (imagens + certificados)
- **Não requer conexão com internet após configuração inicial**s
- O certificado ficará idêntico com Helveticao_linhas`

## Resolução de Problemas

### Erro: "Aluno não encontrado"
- Verifique se o ID do aluno está correto
- Confirme se o aluno existe no banco de dados

### Erro de conexão ao banco
- Verifique as configurações no arquivo `.env`
- Confirme se o servidor MySQL está rodando

### Erro: "Century Gothic não encontrada"
- O script usa Helvetica como fallback automaticamente
- Para usar Century Gothic, instale a fonte no Windows

### Imagens não aparecem
- Verifique a conexão com a internet (imagens são baixadas de URLs)
## Exemplo de Uso Completo

```bash
# 1. Instalar dependências (primeira vez)
pip install reportlab

# 2. Baixar imagens necessárias (primeira vez)
python baixar_imagens_certificado.py

# 3. Verificar configuração do banco (.env)
# DB_HOST=localhost
# DB_USER=seu_usuario
# DB_PASSWORD=sua_senha
# DB_NAME=redeescola

# 4. Gerar certificado
python gerar_certificado_pdf.py 782

# 5. Resultado
# ✓ Certificado gerado: certificados\certificado_aluno_782.pdf
```

## Geração em Lote

Para gerar certificados para múltiplos alunos:

```python
from gerar_certificado_pdf import gerar_certificado_pdf

# Lista de IDs de alunos
alunos = [782, 783, 784, 785]

for aluno_id in alunos:
    print(f"Processando aluno {aluno_id}...")
    arquivo = gerar_certificado_pdf(aluno_id)
    if arquivo:
        print(f"  ✓ Gerado: {arquivo}")
    else:
        print(f"  ✗ Erro ao gerar certificado")
``` install -r requirements_certificado.txt

# 2. Verificar configuração do banco (.env)
# DB_HOST=localhost
# DB_USER=seu_usuario
# DB_PASSWORD=sua_senha
# DB_NAME=redeescola

# 3. Gerar certificado
python gerar_certificado_pdf.py 1234

# 4. Resultado
# ✓ Certificado gerado: certificados\certificado_aluno_1234.pdf
```

## Notas

- O script usa formato **paisagem (landscape)** em tamanho A4
- As imagens de fundo e brasões são baixadas automaticamente
- Certifique-se de ter permissão de escrita na pasta de destino
- Para produção em lote, considere implementar um loop sobre múltiplos IDs

## Suporte

Em caso de dúvidas ou problemas, verifique:
1. Os logs do sistema
2. A conexão com o banco de dados
3. As dependências instaladas
4. As permissões de arquivo

---
**Versão**: 1.0  
**Data**: Dezembro 2025
