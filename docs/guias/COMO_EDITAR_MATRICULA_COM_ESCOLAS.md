# Como Editar Matrícula e Registrar Escola de Origem/Destino

## 📍 Caminho para Acessar

### Passo 1: Abrir o Sistema
- Execute o arquivo `main.py` ou `executar_sistema.bat`

### Passo 2: Localizar o Aluno
- Na tela principal, você verá uma lista de alunos
- Use a barra de pesquisa para encontrar o aluno desejado

### Passo 3: Abrir Edição do Aluno
- **Clique duas vezes** no aluno na lista, OU
- Selecione o aluno e clique no botão **"Editar"**

### Passo 4: Editar Matrícula
- Na janela de edição do aluno, role até a seção **"Informações da Matrícula"**
- Clique no botão **"Editar Matrícula"**

## 🎯 Funcionalidades Disponíveis

### Na tela de Edição de Matrícula você pode:

1. **Alterar Status**
   - Ativo
   - Evadido
   - Cancelado
   - Transferido
   - Concluído

2. **Alterar Série e Turma**
   - Selecione a nova série no combobox "Série"
   - As turmas disponíveis serão carregadas automaticamente
   - Selecione a turma desejada

3. **Registrar Escola de Origem** (para alunos transferidos de outra escola)
   - No campo "Escola de Origem", selecione a escola
   - Este campo é usado para alunos que VIERAM de outra escola

4. **Registrar Escola de Destino** (para alunos sendo transferidos)
   - No campo "Escola de Destino", selecione a escola
   - Este campo é usado para alunos que ESTÃO INDO para outra escola

5. **Adicionar Nova Escola**
   - Se a escola não estiver na lista, clique no botão **"➕ Nova Escola"**
   - Preencha os dados: Nome (obrigatório), Endereço, INEP, CNPJ e Município
   - Clique em "Salvar"
   - A escola será adicionada automaticamente aos comboboxes

## 💡 Dicas de Uso

### Para Transferências Recebidas (aluno veio de outra escola):
1. Status: **Ativo**
2. Escola de Origem: Selecionar a escola de onde veio
3. Escola de Destino: Deixar vazio

### Para Transferências Expedidas (aluno indo para outra escola):
1. Status: **Transferido**
2. Escola de Origem: Deixar vazio (ou manter se já tinha)
3. Escola de Destino: Selecionar a escola para onde está indo

### Para Alunos Regulares (sem transferência):
1. Status: **Ativo**
2. Escola de Origem: Vazio
3. Escola de Destino: Vazio

## 🗄️ Banco de Dados

As informações são salvas automaticamente na tabela `matriculas`:
- `status` - Status da matrícula
- `turma_id` - ID da turma
- `escola_origem_id` - ID da escola de origem (NULL se não aplicável)
- `escola_destino_id` - ID da escola de destino (NULL se não aplicável)

O histórico de mudanças de status é registrado na tabela `historico_matricula`.

## ⚠️ Observações Importantes

- O campo "Turma" é **obrigatório** ao salvar
- Os campos de escola são **opcionais**
- Ao alterar o status para "Transferido", recomenda-se preencher a "Escola de Destino"
- As 135 escolas já cadastradas no sistema aparecem automaticamente nos comboboxes
- Todas as alterações são registradas com data e hora
