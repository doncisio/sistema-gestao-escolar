# Gerador de Folha de Ponto em PDF

Sistema para geração automática de folhas de ponto em PDF para funcionários, com layout profissional e integração com banco de dados.

## 📋 Características

- ✅ Cabeçalho personalizado com duas imagens (logos) e texto central
- ✅ Dados completos do funcionário (nome, matrícula, cargo, etc.)
- ✅ Tabela de registro de ponto com todos os dias do mês
- ✅ Identificação de dias da semana
- ✅ Linhas alternadas para melhor legibilidade
- ✅ Espaço para assinaturas (empregado e responsável)
- ✅ Integração com banco de dados MySQL
- ✅ Geração automática de nomes de arquivo
- ✅ Layout responsivo e profissional

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- Bibliotecas Python:
  ```bash
  pip install reportlab mysql-connector-python python-dotenv
  ```

### Estrutura de Arquivos

```
gestao/
├── gerar_folha_ponto.py          # Módulo principal
├── teste_folha_ponto.py          # Script de teste interativo
├── exemplo_uso_folha_ponto.py   # Exemplos de uso
├── executar_folha_ponto.bat     # Atalho para execução
├── conexao.py                   # Configuração de BD
├── imagens/
│   ├── logopacosemed.png        # Logo esquerda
│   └── pacologo.png             # Logo direita
└── Modelos/                     # Diretório de saída (criado automaticamente)
```

## 📖 Uso

### Método 1: Script Interativo (Recomendado)

Execute o arquivo batch ou o script Python:

```bash
# Windows
executar_folha_ponto.bat

# Ou diretamente
python teste_folha_ponto.py
```

O menu interativo permite:
1. Listar funcionários cadastrados
2. Gerar folha de ponto
3. Sair

### Método 2: Linha de Comando

```bash
python gerar_folha_ponto.py <funcionario_id> [mes] [ano]

# Exemplos:
python gerar_folha_ponto.py 1              # Mês atual
python gerar_folha_ponto.py 1 12 2025     # Dezembro 2025
```

### Método 3: Importar como Módulo

```python
from gerar_folha_ponto import gerar_folha_ponto_funcionario

# Gerar para o mês atual
arquivo = gerar_folha_ponto_funcionario(funcionario_id=1)

# Gerar para mês específico
arquivo = gerar_folha_ponto_funcionario(
    funcionario_id=1,
    mes=12,
    ano=2025
)

# Gerar com caminho personalizado
arquivo = gerar_folha_ponto_funcionario(
    funcionario_id=1,
    mes=12,
    ano=2025,
    output_path="meu_arquivo.pdf"
)

if arquivo:
    print(f"Arquivo gerado: {arquivo}")
```

### Método 4: Usar a Classe Diretamente

```python
from gerar_folha_ponto import FolhaPontoGenerator

# Criar instância
gerador = FolhaPontoGenerator()

# Gerar folha de ponto
arquivo = gerador.gerar_folha_ponto(
    funcionario_id=1,
    mes=12,
    ano=2025
)
```

## 🎨 Layout do PDF

### Cabeçalho
```
[Logo Esquerda]     FOLHA DE PONTO - MÊS/ANO     [Logo Direita]
```

### Dados do Funcionário
```
Dados do Empregado (a):

Nome: [Nome completo]
Matrícula: [Matrícula] | Admissão: [Data]
Função: [Cargo] | Carga horária: [Horas]
Lotação: [Escola]
Contato: [Telefone] | E-mail: [Email]
```

### Tabela de Ponto
```
┌─────┬─────────┬──────────────┬──────────────┬─────────┬────────────┬─────────────┐
│ Dia │ Entrada │ Início do    │ Fim do       │ Saída   │ Hora Extra │ Assinatura  │
│     │         │ Intervalo    │ Intervalo    │         │            │             │
├─────┼─────────┼──────────────┼──────────────┼─────────┼────────────┼─────────────┤
│ 01  │         │              │              │         │            │             │
│ Seg │         │              │              │         │            │             │
├─────┼─────────┼──────────────┼──────────────┼─────────┼────────────┼─────────────┤
│ 02  │         │              │              │         │            │             │
│ Ter │         │              │              │         │            │             │
└─────┴─────────┴──────────────┴──────────────┴─────────┴────────────┴─────────────┘
```

### Rodapé
```
___________________________          ___________________________
Assinatura do Empregado (a)          Assinatura do Responsável
```

## 🗄️ Banco de Dados

### Tabela `Funcionarios`

O sistema busca os seguintes campos:

- `id` - ID do funcionário (obrigatório)
- `nome` - Nome completo
- `matricula` - Número de matrícula
- `cargo` - Cargo/função
- `data_admissao` - Data de admissão
- `carga_horaria` - Carga horária
- `telefone` - Telefone de contato
- `email` - E-mail
- `escola_id` - ID da escola (FK)

### Tabela `escolas`

- `id` - ID da escola
- `nome` - Nome da escola

## 🔧 Configuração

### Imagens do Cabeçalho

As imagens devem estar no diretório `imagens/`:
- `logopacosemed.png` - Logo esquerda (recomendado: 300x200 pixels)
- `pacologo.png` - Logo direita (recomendado: 300x200 pixels)

### Conexão com Banco de Dados

Configure a conexão no arquivo `conexao.py` ou através de variáveis de ambiente no arquivo `.env`:

```env
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_DATABASE=nome_banco
```

## 📊 Exemplos de Uso Avançado

### Gerar para Múltiplos Funcionários

```python
funcionarios_ids = [1, 2, 3, 4, 5]
mes = 12
ano = 2025

for func_id in funcionarios_ids:
    arquivo = gerar_folha_ponto_funcionario(func_id, mes, ano)
    if arquivo:
        print(f"✓ Gerado para funcionário {func_id}")
```

### Gerar para Todos os Meses do Ano

```python
funcionario_id = 1
ano = 2025

for mes in range(1, 13):
    arquivo = gerar_folha_ponto_funcionario(funcionario_id, mes, ano)
    if arquivo:
        print(f"✓ Gerado para mês {mes:02d}/{ano}")
```

### Integração com Interface Gráfica

```python
# Exemplo com Tkinter
from tkinter import messagebox
import os

def gerar_folha_ponto_gui():
    funcionario_id = combo_funcionario.get()
    mes = combo_mes.get()
    ano = combo_ano.get()
    
    arquivo = gerar_folha_ponto_funcionario(funcionario_id, mes, ano)
    
    if arquivo:
        messagebox.showinfo("Sucesso", f"Folha gerada: {arquivo}")
        if messagebox.askyesno("Abrir", "Deseja abrir o arquivo?"):
            os.startfile(arquivo)
    else:
        messagebox.showerror("Erro", "Não foi possível gerar a folha")
```

## 🐛 Tratamento de Erros

O sistema trata automaticamente:
- Funcionário não encontrado no banco de dados
- Imagens não encontradas (gera PDF sem as imagens)
- Erros de conexão com banco de dados
- Dados incompletos do funcionário (usa valores padrão)

Logs são registrados automaticamente através do módulo `config_logs`.

## 📝 Personalização

### Alterar Cores

Edite a classe `FolhaPontoGenerator`:

```python
# Cabeçalho da tabela
('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003452')),  # Azul escuro

# Linhas alternadas
('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
```

### Alterar Tamanho da Página

```python
from reportlab.lib.pagesizes import LETTER, LEGAL

class FolhaPontoGenerator:
    def __init__(self):
        self.pagesize = LETTER  # ou LEGAL
```

### Alterar Layout

Ajuste as dimensões das colunas da tabela:

```python
tabela = Table(dados_tabela, colWidths=[
    2*cm,    # Dia
    2.5*cm,  # Entrada
    2.5*cm,  # Início do Intervalo
    2.5*cm,  # Fim do Intervalo
    2.5*cm,  # Saída
    2*cm,    # Hora Extra
    3.5*cm   # Assinatura
])
```

## 📄 Arquivos de Saída

Os arquivos são salvos automaticamente no diretório `Modelos/` com o seguinte formato:

```
folha_ponto_[nome_funcionario]_[mes]_[ano].pdf

Exemplo: folha_ponto_João_Silva_12_2025.pdf
```

## 🔍 Logs

Os logs são registrados através do módulo `config_logs`:
- Erros de conexão com banco de dados
- Funcionários não encontrados
- Arquivos gerados com sucesso
- Imagens não encontradas

## 🤝 Contribuindo

Para adicionar novos recursos:

1. Edite `gerar_folha_ponto.py`
2. Adicione testes em `teste_folha_ponto.py`
3. Documente em `exemplo_uso_folha_ponto.py`

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs gerados
2. Confirme que as imagens existem no diretório correto
3. Verifique a conexão com o banco de dados
4. Confirme que o funcionário existe na tabela

## 📜 Licença

Este código é parte do Sistema de Gestão Escolar.

---

**Desenvolvido para:** Sistema de Gestão Escolar  
**Versão:** 1.0  
**Data:** Dezembro 2025
