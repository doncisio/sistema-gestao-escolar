# Guia de Uso: Importação de Códigos INEP

## Visão Geral

Este guia explica como usar a nova funcionalidade de importação de códigos INEP (Identificação Única) dos alunos a partir de um arquivo Excel.

## Passos

### 1. Executar a Migration do Banco de Dados

Antes de usar a funcionalidade, é necessário adicionar o campo `codigo_inep` na tabela de alunos.

Execute o seguinte comando SQL no banco de dados:

```sql
SOURCE C:/gestao/migrations/adicionar_campo_codigo_inep.sql;
```

Ou execute manualmente:

```sql
ALTER TABLE alunos 
ADD COLUMN codigo_inep VARCHAR(20) NULL AFTER cpf;

CREATE INDEX idx_alunos_codigo_inep ON alunos(codigo_inep);

ALTER TABLE alunos 
MODIFY COLUMN codigo_inep VARCHAR(20) NULL COMMENT 'Código INEP - Identificação Única do aluno';
```

### 2. Preparar o Arquivo Excel

O arquivo Excel deve ter as seguintes colunas:

- **Nome da turma**: Nome da turma do aluno
- **Identificação única**: Código INEP (número de identificação)
- **Nome do(a) Aluno(a)**: Nome completo do aluno

Exemplo:

| Nome da turma | Identificação única | Nome do(a) Aluno(a) |
|---------------|---------------------|---------------------|
| 1º ANO-MATU   | 203203598327        | ALESSANDRO PEREIRA ALVES |
| 1º ANO-MATU   | 202852288891        | ALEXYA MARIA ALVES FERREIRA |

### 3. Abrir a Interface de Mapeamento

Existem duas formas de abrir a interface:

#### Opção A: Via Menu Principal (após integração)

Se a funcionalidade foi integrada ao menu principal, acesse:

**Menu → Alunos → Importar Códigos INEP**

#### Opção B: Via Script Standalone

Execute o seguinte comando no terminal:

```bash
cd C:\gestao
python -m src.interfaces.mapeamento_codigo_inep
```

### 4. Selecionar o Arquivo Excel

1. Clique no botão **"📂 Selecionar Arquivo Excel"**
2. Navegue até o arquivo `codigo inep.xlsx` (ou outro arquivo com o mesmo formato)
3. Selecione o arquivo

### 5. Processar o Mapeamento

1. Clique no botão **"🔄 Processar Mapeamento"**
2. O sistema irá:
   - Carregar os dados do Excel
   - Buscar os alunos no banco de dados
   - Comparar os nomes usando algoritmo de similaridade
   - Classificar os mapeamentos como:
     - **CONFIRMADO**: Similaridade ≥ 85% (verde)
     - **REVISAR**: Similaridade < 85% (amarelo)

### 6. Revisar os Mapeamentos

A tabela mostrará os seguintes dados:

- **✓**: Checkbox indicando se o mapeamento será aplicado
- **Nome no Excel**: Nome do aluno no arquivo Excel
- **Nome no Banco**: Nome do aluno encontrado no banco de dados
- **Código INEP**: Código a ser inserido
- **Turma**: Turma do aluno
- **Similaridade**: Percentual de similaridade entre os nomes
- **Status**: CONFIRMADO ou REVISAR

**Ações disponíveis:**

- **Duplo clique** em uma linha: Alterna entre aplicar/não aplicar aquele mapeamento
- **Marcar Todos**: Seleciona todos os mapeamentos
- **Desmarcar Todos**: Desseleciona todos os mapeamentos
- **Buscar**: Filtra a tabela por nome
- **Filtrar por Status**: Mostra apenas confirmados, para revisar, ou todos

### 7. Aplicar os Mapeamentos

1. Revise cuidadosamente os mapeamentos marcados
2. Clique no botão **"✓ Aplicar Mapeamentos Selecionados"**
3. Confirme a operação quando solicitado
4. O sistema atualizará o banco de dados

### 8. Verificar os Resultados

Após a aplicação, você pode verificar os códigos INEP:

- **Interface de Cadastro de Aluno**: O campo "Código INEP" estará disponível
- **Interface de Edição de Aluno**: O campo mostrará o código importado

## Cadastro Manual de Código INEP

Se você não deseja usar a importação em massa, pode cadastrar o código INEP manualmente ao:

1. **Cadastrar um novo aluno**: Preencha o campo "Código INEP" no formulário
2. **Editar um aluno existente**: Atualize o campo "Código INEP" na tela de edição

## Algoritmo de Similaridade

O sistema usa o algoritmo **SequenceMatcher** para comparar os nomes. Ele:

1. Normaliza os nomes (remove acentos, converte para maiúsculas)
2. Compara as sequências de caracteres
3. Retorna um valor entre 0 e 1 (0% a 100%)

**Limite padrão**: 85% de similaridade para confirmar automaticamente

## Tratamento de Conflitos

- Se um aluno já possui código INEP, ele será mostrado na coluna "Código INEP Atual"
- Você pode decidir se deseja sobrescrever ou não
- Mapeamentos sem correspondência no banco serão mostrados como "NÃO ENCONTRADO"

## Logs

Todos os processos são registrados no arquivo de log do sistema:

```
C:\gestao\logs\app.log
```

## Troubleshooting

### Erro ao carregar Excel

- Verifique se o arquivo tem as colunas corretas
- Verifique se o arquivo não está aberto em outro programa
- Verifique a extensão do arquivo (.xlsx ou .xls)

### Erro ao conectar ao banco

- Verifique se o banco de dados está rodando
- Verifique as credenciais de conexão
- Verifique se a migration foi executada

### Nenhum mapeamento encontrado

- Verifique se os nomes no Excel estão escritos corretamente
- Verifique se os alunos existem no banco de dados
- Ajuste o limite de similaridade se necessário

## Suporte

Em caso de problemas, consulte os logs ou entre em contato com o suporte técnico.

---

**Data de criação:** 21/02/2026  
**Versão:** 1.0
