# Sistema de Controle de Duplicatas de Documentos

## 📋 Visão Geral

Este sistema implementa controles para evitar a criação excessiva de documentos duplicados e fornece ferramentas para limpar duplicatas existentes.

## 🚀 Funcionalidades Implementadas

### 1. Controle Automático de Duplicatas no Upload

**Localização:** `utilitarios/gerenciador_documentos.py`

O sistema agora verifica automaticamente se um documento similar foi criado recentemente antes de criar um novo registro.

**Como funciona:**
- Quando um documento é salvo, o sistema verifica se existe outro documento com:
  - Mesmo tipo
  - Mesmo aluno/funcionário
  - Mesma finalidade
  - Criado nos **últimos 5 minutos** (configurável)

- Se encontrar um documento similar recente:
  - ✅ **Atualiza** o documento existente (substitui o arquivo no Drive)
  - ✅ Remove o arquivo antigo do Google Drive
  - ✅ Mantém apenas 1 registro no banco de dados
  - ✅ Economiza espaço de armazenamento

- Se NÃO encontrar:
  - ✅ Cria um novo registro normalmente

**Parâmetro configurável:**
```python
# No arquivo gerenciador_documentos.py
intervalo_minutos=5  # Altere este valor para mudar o intervalo
```

### 2. Interface de Gerenciamento de Duplicados

**Localização:** `GerenciadorDocumentosSistema.py`

Adicionados 2 novos botões na interface:

#### 🔍 Relatório Duplicados (Botão Amarelo)
- Analisa o banco de dados em busca de documentos duplicados
- Mostra relatório detalhado sem remover nada
- Exibe:
  - Tipo de documento
  - Aluno/Funcionário relacionado
  - Quantidade de duplicatas
  - IDs dos documentos

#### 🧹 Limpar Duplicados (Botão Laranja)
- Remove documentos duplicados mantendo apenas o mais recente
- Exibe janela de progresso com:
  - Lista de documentos sendo processados
  - Status de remoção (Drive e Banco)
  - Resumo final com totais
- **Ação irreversível** - pede confirmação antes de executar

### 3. Script de Limpeza em Lote

**Localização:** `limpar_duplicados_documentos.py`

Script standalone para fazer limpeza inicial de duplicados.

**Modos de operação:**

#### Modo 1: Simulação
```bash
python limpar_duplicados_documentos.py
# Escolha: 1
```
- Mostra o que seria removido **sem remover nada**
- Útil para verificar antes de executar

#### Modo 2: Execução
```bash
python limpar_duplicados_documentos.py
# Escolha: 2
# Digite: CONFIRMAR
```
- Remove permanentemente os documentos duplicados
- Requer confirmação digitando "CONFIRMAR"

## 📊 Critérios de Duplicatas

Documentos são considerados duplicados quando possuem:
1. **Mesmo tipo de documento** (ex: "Declaração", "Boletim")
2. **Mesmo aluno_id** OU **mesmo funcionario_id**
3. **Mesma finalidade**

O sistema mantém sempre a **versão mais recente** (data_de_upload mais atual).

## 🔧 Estrutura das Novas Funções

### Em `gerenciador_documentos.py`:

```python
verificar_documento_recente()
# Verifica se existe documento similar recente

atualizar_documento_existente()
# Atualiza documento existente ao invés de criar novo

salvar_documento()
# Modificada para usar as funções acima
```

### Em `GerenciadorDocumentosSistema.py`:

```python
identificar_duplicados()
# Busca duplicados no banco de dados

limpar_duplicados()
# Remove duplicados com interface de progresso

mostrar_relatorio_duplicados()
# Exibe relatório sem remover
```

## 💡 Exemplos de Uso

### Exemplo 1: Geração Múltipla de Boletins
**Antes:**
- Usuário gera boletim às 10:00
- Usuário gera boletim às 10:02 (mesmo aluno)
- Usuário gera boletim às 10:04 (mesmo aluno)
- **Resultado:** 3 arquivos no Drive, 3 registros no banco

**Depois:**
- Usuário gera boletim às 10:00 → Cria novo
- Usuário gera boletim às 10:02 → Atualiza o das 10:00
- Usuário gera boletim às 10:04 → Atualiza novamente
- **Resultado:** 1 arquivo no Drive, 1 registro no banco (sempre o mais atual)

### Exemplo 2: Limpeza de Histórico
```
Situação:
- 50 declarações do mesmo aluno criadas em sequência
- Todas com mesma finalidade

Ação via interface:
1. Clicar em "Relatório Duplicados"
2. Ver que há 49 duplicatas (mantém 1)
3. Clicar em "Limpar Duplicados"
4. Confirmar
5. Sistema remove 49 arquivos do Drive e 49 registros do banco
6. Mantém apenas a versão mais recente
```

## ⚙️ Configurações Recomendadas

### Intervalo de Verificação
- **5 minutos** (padrão): Bom para maioria dos casos
- **10 minutos**: Se os documentos demoram para gerar
- **2 minutos**: Se quer controle mais rígido

### Quando Fazer Limpeza Completa
- Após implementar o sistema (limpar duplicatas antigas)
- Mensalmente como manutenção preventiva
- Quando o banco ficar muito grande

## 🔒 Segurança

### Proteções Implementadas:
1. ✅ Sempre mantém o documento mais recente
2. ✅ Pede confirmação antes de remover
3. ✅ Modo simulação disponível
4. ✅ Log detalhado de todas as ações
5. ✅ Transações no banco (rollback em caso de erro)

### O que NÃO é removido:
- ❌ Documentos de tipos diferentes
- ❌ Documentos de alunos/funcionários diferentes
- ❌ Documentos com finalidades diferentes
- ❌ Documentos únicos (sem duplicatas)

## 📈 Benefícios

### Armazenamento
- ✅ Reduz drasticamente uso do Google Drive
- ✅ Diminui tamanho do banco de dados
- ✅ Evita atingir limites de quota

### Performance
- ✅ Consultas mais rápidas no banco
- ✅ Menos arquivos para gerenciar
- ✅ Interface mais responsiva

### Organização
- ✅ Um único documento por tipo/pessoa/finalidade
- ✅ Sempre a versão mais atualizada
- ✅ Histórico limpo e organizado

## 🐛 Solução de Problemas

### Erro: "Token expirado"
**Solução:** O sistema renova automaticamente. Se persistir, delete `token.pickle` e autentique novamente.

### Erro: "Não foi possível excluir do Drive"
**Solução:** Arquivo já foi removido manualmente. O sistema remove do banco normalmente.

### Duplicados não são detectados
**Verifique:**
- Tipo de documento está exatamente igual?
- Aluno/Funcionário ID são os mesmos?
- Finalidade está igual (ou ambas NULL)?

## 📝 Notas Técnicas

### Banco de Dados
- Usa `GROUP BY` com `GROUP_CONCAT` para identificar duplicados
- Query otimizada com índices em: tipo_documento, aluno_id, funcionario_id
- Ordenação por data_de_upload DESC para manter o mais recente

### Google Drive
- API v3 utilizada
- Permissões configuradas automaticamente
- Arquivo movido para lixeira (pode recuperar até 30 dias)

### Logs
- Impressos no console durante execução
- Janela de progresso mostra detalhes em tempo real
- Recomenda-se redirecionar output para arquivo em produção

## 🔄 Próximas Melhorias Sugeridas

1. [ ] Agendamento automático de limpeza (cron/task scheduler)
2. [ ] Exportar relatório de duplicados para Excel
3. [ ] Notificação por email após limpeza
4. [ ] Dashboard com estatísticas de armazenamento
5. [ ] Histórico de limpezas realizadas

---

**Última atualização:** 07/11/2025  
**Versão:** 1.0  
**Autor:** Sistema de Gestão Escolar
