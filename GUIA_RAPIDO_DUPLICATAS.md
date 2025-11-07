# 🚀 Guia Rápido - Sistema de Controle de Duplicatas

## ✅ O Problema Foi Resolvido!

Agora o sistema **evita automaticamente** a criação de documentos duplicados quando eles são gerados múltiplas vezes em curto período.

## 🎯 Como Funciona Agora

### Automaticamente (sem precisar fazer nada):
Quando você gera um documento:
- ✅ Se foi gerado há **menos de 5 minutos**: **ATUALIZA** o existente
- ✅ Se foi gerado há **mais de 5 minutos**: **CRIA** um novo

Resultado: **Não acumula mais duplicatas!**

## 🧹 Como Limpar Duplicatas Antigas

### Opção 1: Via Interface (Recomendado)

1. Abra o **Gerenciador de Documentos do Sistema** no menu principal
2. Clique em **"Relatório Duplicados"** (botão amarelo)
   - Veja quantas duplicatas existem
   - Verifique o que será removido
3. Clique em **"Limpar Duplicados"** (botão laranja)
   - Confirme a ação
   - Acompanhe o progresso
   - Pronto! Duplicatas removidas

### Opção 2: Via Script (Para grandes volumes)

1. Abra o PowerShell na pasta do sistema
2. Execute:
   ```powershell
   python limpar_duplicados_documentos.py
   ```
3. Escolha:
   - **1** → Simulação (apenas visualiza)
   - **2** → Executar (remove de verdade)
   - **3** → Cancelar

## 📊 O que Será Mantido/Removido

### ✅ Mantém (sempre):
- A versão **mais recente** de cada documento
- Documentos **únicos** (sem duplicatas)
- Documentos de **tipos diferentes**
- Documentos de **pessoas diferentes**

### ❌ Remove:
- Versões **antigas** de documentos duplicados
- Apenas quando há múltiplas cópias **idênticas**:
  - Mesmo tipo
  - Mesma pessoa (aluno/funcionário)
  - Mesma finalidade

## 💡 Exemplo Prático

**Antes:**
```
Boletim - João Silva - 1º Trimestre - 10:00 ❌
Boletim - João Silva - 1º Trimestre - 10:02 ❌
Boletim - João Silva - 1º Trimestre - 10:05 ❌
Boletim - João Silva - 1º Trimestre - 10:10 ❌
```
4 arquivos no Drive, 4 registros no banco

**Depois da Limpeza:**
```
Boletim - João Silva - 1º Trimestre - 10:10 ✅
```
1 arquivo no Drive (o mais recente), 1 registro no banco

**Economia:** 75% de espaço!

## ⚙️ Configurações

### Alterar Intervalo de Verificação

Edite `utilitarios/gerenciador_documentos.py`:

```python
# Linha ~175
intervalo_minutos=5  # Mude para 2, 10, 15, etc.
```

**Recomendações:**
- **2-3 min**: Documentos rápidos (declarações)
- **5 min**: Padrão (maioria dos casos) ⭐
- **10-15 min**: Documentos complexos (históricos)

## 🔍 Como Verificar se Funcionou

### Teste Simples:
1. Gere um documento (ex: declaração)
2. Gere o mesmo documento novamente **imediatamente**
3. Abra o Gerenciador de Documentos
4. Procure o documento → Deve haver **apenas 1 registro**!

### Verificar Estatísticas:
1. Anote quantos documentos tem agora
2. Clique em "Relatório Duplicados"
3. Faça a limpeza
4. Veja quanto espaço foi economizado

## ⚠️ Avisos Importantes

1. **A limpeza é irreversível** (mas mantém sempre o mais recente)
2. **Faça backup** antes da primeira limpeza completa
3. **Use a simulação** primeiro para ver o que será removido
4. **Arquivos do Drive** vão para lixeira (30 dias de recuperação)

## 🆘 Precisa de Ajuda?

### Mensagem: "Documento atualizado (substituiu versão anterior)"
✅ **Normal!** Sistema evitou criar duplicata

### Mensagem: "Documento salvo com sucesso"
✅ **Normal!** Não havia duplicata recente

### Erro ao conectar Drive
❌ Verifique internet e token.pickle

### Nenhuma duplicata encontrada
✅ **Ótimo!** Banco está limpo

## 📈 Manutenção Recomendada

### Semanal:
- ✅ Verificar relatório de duplicados

### Mensal:
- ✅ Executar limpeza completa

### Trimestral:
- ✅ Revisar intervalo de verificação
- ✅ Analisar padrões de geração

## 🎉 Pronto!

Agora seu sistema:
- ✅ Não cria mais duplicatas desnecessárias
- ✅ Economiza espaço no Drive
- ✅ Mantém o banco organizado
- ✅ Sempre tem a versão mais recente

---

**Dúvidas?** Consulte o arquivo `CONTROLE_DUPLICATAS.md` para documentação completa.
