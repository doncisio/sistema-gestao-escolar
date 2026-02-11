# Lista de Controle de Livros Faltantes por Turma

## 📚 Descrição

Esta funcionalidade permite gerenciar e gerar relatórios de livros didáticos faltantes por turma e disciplina, facilitando o controle de estoque e a solicitação de novos livros. O sistema suporta **1º ao 9º ano** com layouts diferenciados para anos iniciais e finais.

## 🎯 Funcionalidades

### 1. Gerenciar Livros Faltantes
- Interface intuitiva para inserir/editar quantidades de livros faltantes
- Organização por ano letivo, série (1º ao 9º ano) e turma
- Disciplinas dinâmicas conforme o nível:
  - **Anos Iniciais (1º ao 5º ano)**: PRT, MTM, CNC, GEO/HIST, ART
  - **Anos Finais (6º ao 9º ano)**: PRT, MTM, CNC, HST, GEO, ING, ART
- Campo de observações para anotações adicionais
- Campos para editora e coleção de cada livro
- Dados salvos no banco de dados para consulta futura

### 2. Gerar PDF com Relatório
Gera **dois PDFs separados** com layouts otimizados:

#### PDF Anos Iniciais (1º ao 5º ano)
- Formato **Retrato (A4)**
- Página de capa profissional
- Uma página por turma com tabela de livros faltantes
- Disciplinas combinadas (Geografia/História juntas)
- Total de livros faltantes por turma
- Espaço para observações manuscritas

#### PDF Anos Finais (6º ao 9º ano)
- Formato **Paisagem (A4)**
- Layout com mais espaço horizontal
- Disciplinas separadas (História e Geografia independentes)
- Inclusão de Inglês
- Tabela com fontes maiores para melhor legibilidade
- Maior espaço para informações de editora e coleção
- Mais linhas para observações

## 📋 Pré-requisitos

### Instalação da Tabela no Banco de Dados

Antes de usar a funcionalidade, é necessário criar a tabela no banco de dados:

```bash
python executar_migracao_livros_faltantes.py
```

Este comando criará a tabela `livros_faltantes` com a estrutura necessária.

## 🚀 Como Usar

### Passo 1: Cadastrar Livros Faltantes

1. Abra o sistema de gestão escolar
2. No menu principal, clique em **Listas** → **Gerenciar Livros Faltantes**
3. Selecione:
   - **Ano Letivo**: Escolha o ano desejado
   - **Série**: Escolha a série (1º ao 9º ano)
   - **Turma**: Escolha a turma (A, B, C, etc.)
4. Clique em **Carregar Dados** para buscar dados já salvos (se existirem)
5. Preencha as quantidades de livros faltantes para cada disciplina
   - As disciplinas serão exibidas automaticamente conforme a série selecionada
6. Preencha editora e coleção de cada livro (opcional)
7. Adicione observações se necessário
8. Clique em **Salvar**

### Passo 2: Gerar os PDFs

1. No menu principal, clique em **Listas** → **Gerar PDF Livros Faltantes**
2. O sistema gerará automaticamente **dois PDFs**:
   - **Livros_Faltantes_Anos_Iniciais_[ano].pdf** - Para 1º ao 5º ano
   - **Livros_Faltantes_Anos_Finais_[ano].pdf** - Para 6º ao 9º ano
3. Escolha onde salvar cada arquivo
4. Os PDFs serão abertos automaticamente para visualização

## 📊 Estrutura dos Dados

### Disciplinas por Nível

**Anos Iniciais (1º ao 5º ano):**
- **PRT**: Português
- **MTM**: Matemática
- **CNC**: Ciências
- **GEO/HIST**: Geografia/História (combinadas)
- **ART**: Arte

**Anos Finais (6º ao 9º ano):**
- **PRT**: Português
- **MTM**: Matemática
- **CNC**: Ciências
- **HST**: História
- **GEO**: Geografia
- **ING**: Inglês
- **ART**: Arte

### Dados Armazenados

Para cada combinação de ano letivo + série + turma + disciplina:
- Quantidade de livros faltantes
- Editora
- Coleção
- Data de registro
- Data da última atualização
- Usuário que registrou
- Observações

## 🔐 Permissões

Esta funcionalidade está disponível para os perfis:
- **Administrador**
- **Coordenador**

## 📝 Exemplos de Uso

### Caso 1: Início do Ano Letivo
No início do ano letivo, cadastre as quantidades de livros que faltam em cada turma para fazer a solicitação à coordenação/secretaria.

### Caso 2: Controle Mensal
Atualize mensalmente as quantidades conforme livros são recebidos ou a situação muda.

### Caso 3: Relatório para Secretaria
Gere o PDF para enviar à Secretaria de Educação solicitando novos livros.

## 🗂️ Arquivos Criados

```
gestao/
├── db/
│   └── migrations/
│       └── criar_tabela_livros_faltantes.sql      # Migração do banco
│
├── src/
│   ├── ui/
│   │   └── livros_faltantes_window.py             # Interface de gerenciamento
│   │
│   └── relatorios/
│       └── listas/
│           └── lista_livros_faltantes.py           # Gerador de PDF
│
├── executar_migracao_livros_faltantes.py          # Script de migração
└── README_LIVROS_FALTANTES.md                     # Este arquivo
```

## 🛠️ Manutenção

### Adicionar Nova Disciplina

Para adicionar uma nova disciplina:

1. Edite `src/ui/livros_faltantes_window.py`:
   - Adicione a sigla em `DISCIPLINAS_1_5` ou `DISCIPLINAS_6_9`

2. Edite `src/relatorios/listas/lista_livros_faltantes.py`:
   - Adicione a disciplina na lista `disciplinas`
   - Adicione o nome completo no dicionário `nomes_disciplinas`

### Modificar Layout do PDF

Edite o arquivo `src/relatorios/listas/lista_livros_faltantes.py`:
- Função `add_turma_table()`: Modifica o layout da tabela
- Função `add_cover_page()`: Modifica a capa
- Função `create_pdf_buffer()`: Modifica margens e tamanho

## ❓ Solução de Problemas

### Erro: "Tabela livros_faltantes não existe"
**Solução**: Execute o script de migração:
```bash
python executar_migracao_livros_faltantes.py
```

### Erro: "Nenhum dado cadastrado"
**Solução**: Cadastre os dados primeiro em **Listas** → **Gerenciar Livros Faltantes**

### PDF não abre automaticamente
**Solução**: O arquivo é salvo. Verifique a pasta de documentos ou escolha manualmente onde salvar.

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs do sistema em `logs/`
2. Consulte a documentação técnica em `docs/`
3. Entre em contato com o suporte técnico

---

**Data de criação**: 09/02/2026  
**Versão**: 1.0  
**Autor**: Sistema de Gestão Escolar
