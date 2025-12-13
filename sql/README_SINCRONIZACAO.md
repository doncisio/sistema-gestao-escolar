# SINCRONIZAÇÃO DE DADOS - BANCO DE QUESTÕES

## 📋 Arquivos Gerados

- **`dados_questoes_YYYYMMDD_HHMMSS.sql`**: Arquivo SQL completo com estrutura e dados
- **`exportar_dados_questoes.py`**: Script Python para gerar exportação atualizada

## 📊 Conteúdo Exportado

O arquivo SQL contém:

1. ✅ **Tabelas**: 
   - `textos_base` - Textos e imagens base para avaliações
   - `avaliacoes_textos_base` - Relacionamento avaliação ↔ textos

2. ✅ **Dados Atuais**:
   - 4 textos base de exemplo
   - 9 questões (5 dissertativas + 4 múltipla escolha)
   - Todas as alternativas das questões de múltipla escolha

## 🔄 Como Sincronizar Entre PCs

### **PC de Origem (onde você está agora)**

1. ✅ Execute `exportar_dados_questoes.py` (já feito)
2. 📋 Copie o arquivo `.sql` gerado em `c:\gestao\sql\`
3. 💾 Transfira para o outro PC via:
   - Pen drive
   - Google Drive / OneDrive
   - Email
   - Rede local

### **PC de Destino (onde você quer importar)**

#### **Opção 1: Via MySQL Command Line**
```bash
mysql -u root -p redeescola < "caminho\dados_questoes_20251213_063610.sql"
```

#### **Opção 2: Via phpMyAdmin**
1. Acesse phpMyAdmin
2. Selecione o banco `redeescola`
3. Clique em "Importar"
4. Escolha o arquivo `.sql`
5. Clique em "Executar"

#### **Opção 3: Via HeidiSQL / MySQL Workbench**
1. Conecte ao banco `redeescola`
2. Arquivo → Executar arquivo SQL
3. Selecione o arquivo `.sql`
4. Execute

## ⚠️ IMPORTANTE - Sobre IDs e Duplicatas

### **Comportamento do Script:**

- **Textos Base**: APAGA todos (`DELETE FROM textos_base`) e insere novamente com IDs originais
- **Questões**: NÃO apaga, apenas insere novas (usa variáveis @questao_X_id para mapear)
- **Alternativas**: Vinculadas às novas questões através das variáveis

### **Se você quiser SUBSTITUIR todas as questões:**

Adicione esta linha ANTES de importar:
```sql
DELETE FROM questoes_alternativas;
DELETE FROM avaliacoes_questoes;
DELETE FROM questoes;
```

### **Se você quiser MESCLAR (manter existentes + adicionar novas):**

- Importe normalmente
- As questões terão novos IDs
- Pode haver duplicatas (mesmo conteúdo, IDs diferentes)

## 🔧 Gerando Nova Exportação

Se você fez mudanças e quer exportar novamente:

```bash
python c:\gestao\exportar_dados_questoes.py
```

Um novo arquivo será criado com timestamp atualizado.

## 📝 Estrutura dos Dados

### Textos Base
- ID 1-2: Versões longas (primeira inserção)
- ID 3-4: Versões curtas (segunda inserção - para testes)

### Questões
- ID 2: Questão antiga (História)
- ID 3-5: Primeira leva de testes
- ID 6-10: Segunda leva completa (2 dissertativas + 3 múltipla escolha)

## 🎯 Próximos Passos Após Importação

1. ✅ Abra o sistema: `python main.py`
2. ✅ Acesse "Banco de Questões BNCC"
3. ✅ Verifique na aba "Textos Base" se os 4 textos apareceram
4. ✅ Verifique na aba "Minhas Questões" se as 9 questões apareceram
5. ✅ Teste criar uma avaliação usando os textos e questões importados

## 🐛 Troubleshooting

### Erro: "Table 'textos_base' doesn't exist"
- Certifique-se de executar o script completo (ele cria as tabelas)

### Erro: "Duplicate entry for key 'PRIMARY'"
- Você já tem dados com os mesmos IDs
- Solução: Apague antes (`DELETE FROM textos_base; DELETE FROM questoes;`)

### Erro: "Foreign key constraint fails"
- Verifique se as tabelas `escolas` e `funcionarios` existem
- Verifique se `escola_id=60` e `autor_id=1` existem no seu banco

### IDs diferentes no outro PC
- Normal se você não apagou as tabelas antes
- As questões terão novos IDs sequenciais
- Funciona normalmente, apenas os números serão diferentes

## 📞 Suporte

Se tiver problemas, verifique:
1. Conexão com o banco de dados
2. Permissões do usuário MySQL
3. Existência das tabelas dependentes (escolas, funcionarios)
4. Logs de erro do MySQL/MariaDB
