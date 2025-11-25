# ATUALIZAÇÃO DAS LISTAS DE TRANSFERÊNCIA COM ESCOLA ORIGEM/DESTINO

## 📋 Resumo das Alterações

As listas de transferência foram atualizadas para incluir informações sobre as escolas de origem e destino dos alunos transferidos.

## 🔄 Arquivos Modificados

### 1. Lista_atualizada.py
**Função:** `fetch_student_data()`

**Alteração:** Adicionadas colunas na query SQL:
- `ESCOLA_ORIGEM` - Nome da escola de origem (via LEFT JOIN com escolas)
- `ESCOLA_DESTINO` - Nome da escola de destino (via LEFT JOIN com escolas)

```sql
LEFT JOIN escolas e_origem ON m.escola_origem_id = e_origem.id
LEFT JOIN escolas e_destino ON m.escola_destino_id = e_destino.id
```

### 2. movimentomensal.py

#### Função: `gerar_lista_alunos_transferidos()`
**Título do relatório:** "TRANSFERÊNCIAS EXPEDIDAS"

**Alterações:**
- ✅ Adicionada coluna "Escola Destino" na tabela PDF
- ✅ Exibe o nome da escola para onde o aluno foi transferido
- ✅ Mostra "N/I" (Não Informado) quando não houver escola de destino cadastrada
- ✅ Ajustadas larguras das colunas para acomodar a nova informação

**Layout da tabela:**
| Nº | Nome | Série/Turma | Turno | Data Transferência | **Escola Destino** | Telefones |
|----|------|-------------|-------|-------------------|-------------------|-----------|

#### Função: `gerar_lista_alunos_matriculados_depois()`
**Título do relatório:** "TRANSFERÊNCIAS RECEBIDAS"

**Alterações:**
- ✅ Adicionada coluna "Escola Origem" na tabela PDF
- ✅ Exibe o nome da escola de onde o aluno veio
- ✅ Mostra "N/I" (Não Informado) quando não houver escola de origem cadastrada
- ✅ Ajustadas larguras das colunas para acomodar a nova informação
- ✅ Query SQL atualizada para incluir LEFT JOIN com escolas

**Layout da tabela:**
| Nº | Nome | Série/Turma | Turno | Data Matrícula | **Escola Origem** | Situação | Telefones |
|----|------|-------------|-------|----------------|------------------|----------|-----------|

## 🎨 Formatação

- **Fonte escola:** 8pt (ParagraphStyle 'Escola')
- **Alinhamento:** Esquerda
- **Quebra de linha:** Automática quando o nome da escola for longo
- **Placeholder:** "N/I" quando não houver informação

## 🔍 Como Funciona

### Para Transferidos (Expedidas):
1. Busca alunos com status "Transferido" ou "Transferida"
2. Obtém a escola de destino do campo `escola_destino_id` na tabela matriculas
3. Exibe o nome da escola na coluna "Escola Destino"

### Para Matriculados Depois (Recebidas):
1. Busca alunos matriculados após a data de início do ano letivo
2. Obtém a escola de origem do campo `escola_origem_id` na tabela matriculas
3. Exibe o nome da escola na coluna "Escola Origem"

## 📊 Larguras das Colunas

### Lista de Transferidos (Expedidas):
```python
colWidths=[
    0.3 * inch,  # Nº
    1.8 * inch,  # Nome (reduzido)
    0.7 * inch,  # Série/Turma
    0.5 * inch,  # Turno
    0.8 * inch,  # Data Transferência
    1.7 * inch,  # Escola Destino (NOVO)
    1.4 * inch   # Telefones
]
```

### Lista de Matriculados Depois (Recebidas):
```python
colWidths=[
    0.3 * inch,  # Nº
    1.7 * inch,  # Nome (reduzido)
    0.7 * inch,  # Série/Turma
    0.5 * inch,  # Turno
    0.7 * inch,  # Data Matrícula
    1.5 * inch,  # Escola Origem (NOVO)
    0.7 * inch,  # Situação
    1.1 * inch   # Telefones
]
```

## 🧪 Como Testar

### Opção 1: Menu Principal (RECOMENDADO)
Acesse o sistema principal e vá até o menu **Listas**:
- **Transferências Expedidas** - Lista de alunos transferidos com escola destino
- **Transferências Recebidas** - Lista de alunos matriculados depois com escola origem

### Opção 2: Script de teste
```bash
# Execute o arquivo .bat
executar_teste_listas_escolas.bat

# Ou execute diretamente:
python testar_listas_com_escolas.py
```

### Opção 3: Scripts originais
```bash
# Lista de transferidos
python executar_lista_transferidos.py

# Lista de matriculados depois
python executar_lista_matriculados_depois.py
```

## ✅ Verificações Realizadas

- [x] Query SQL atualizada em `Lista_atualizada.py`
- [x] LEFT JOIN adicionado para escolas (origem e destino)
- [x] Função `gerar_lista_alunos_transferidos()` atualizada
- [x] Função `gerar_lista_alunos_matriculados_depois()` atualizada
- [x] Larguras de colunas ajustadas
- [x] Tratamento de valores NULL (exibe "N/I")
- [x] Formatação consistente (fonte 8pt)
- [x] Script de teste criado
- [x] PDFs em modo paisagem (landscape)
- [x] Callbacks adicionados em `action_callbacks.py`
- [x] Menu "Listas" atualizado com novos itens

## 🎯 Resultado Esperado

### Antes:
- Lista não mostrava de onde o aluno veio ou para onde foi
- Difícil rastrear a movimentação entre escolas

### Depois:
- **Transferidos:** Mostra para qual escola o aluno foi transferido
- **Matriculados:** Mostra de qual escola o aluno veio
- Facilita o acompanhamento e controle de transferências
- Melhora a gestão de movimentação de alunos

## 💡 Observações Importantes

1. **Dados Anteriores:** Transferências antigas sem escola cadastrada exibirão "N/I"
2. **Cadastro:** Use a interface unificada de matrícula para informar origem/destino
3. **Obrigatoriedade:** Os campos NÃO são obrigatórios (NULL permitido)
4. **Integração:** Funciona em conjunto com a interface unificada de matrícula

## 📝 Próximos Passos

Para aproveitar ao máximo a nova funcionalidade:

1. ✅ Teste as listas geradas
2. ✅ Verifique o layout no PDF
3. ✅ Ao cadastrar novas transferências, informe a escola origem/destino
4. ✅ Atualize registros antigos conforme necessário

## 🔗 Arquivos Relacionados

- `Lista_atualizada.py` - Query principal de dados
- `movimentomensal.py` - Geração de relatórios
- `interface_matricula_unificada.py` - Cadastro de origem/destino
- `executar_lista_transferidos.py` - Gera PDF de transferidos
- `executar_lista_matriculados_depois.py` - Gera PDF de matriculados
- `testar_listas_com_escolas.py` - Script de teste (NOVO)
- `executar_teste_listas_escolas.bat` - Executável de teste (NOVO)
- `ui/action_callbacks.py` - Callbacks dos menus (ATUALIZADO)
- `ui/button_factory.py` - Menu Listas da interface principal (ATUALIZADO)

---

**Data:** 2025
**Versão:** 1.1
**Status:** ✅ Implementado, Testado e Integrado ao Menu Principal
