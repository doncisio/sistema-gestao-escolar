# 🔄 Guia de Transição de Ano Letivo

## 📋 Visão Geral

Este módulo automatiza o processo de transição entre anos letivos, garantindo que:
- ✅ Matrículas antigas sejam encerradas corretamente
- ✅ Novas matrículas sejam criadas automaticamente
- ✅ Apenas alunos ativos continuem no novo ano
- ✅ Alunos transferidos, cancelados e evadidos sejam excluídos

---

## 🔒 SEGURANÇA

**Este módulo é protegido por senha dupla:**
1. **Senha ao abrir**: Necessária para acessar a interface
2. **Senha ao executar**: Necessária para confirmar a operação

**Senha:** A mesma senha do banco de dados (configurada no arquivo .env)

⚠️ **ATENÇÃO:** A transição de ano letivo é uma operação crítica e irreversível!

---

## ⚠️ IMPORTANTE: Antes de Começar

### 1. **FAÇA BACKUP DO BANCO DE DADOS**
   - Vá em: Menu Principal → Botão "Backup"
   - Aguarde a confirmação do backup
   - **NUNCA pule esta etapa!**

### 2. **Verifique os Dados**
   - Certifique-se de que todos os alunos transferidos estão com status correto
   - Confirme que todos os cancelamentos foram registrados
   - Verifique se as turmas para o próximo ano já estão criadas

### 3. **Escolha o Momento Certo**
   - Realize a transição **APÓS** o encerramento oficial do ano letivo
   - Faça em horário de baixo movimento no sistema
   - Avise outros usuários sobre a manutenção

---

## 🚀 Como Usar

### Passo 1: Acessar a Transição
1. Abra o sistema
2. Vá em: **Menu → Serviços → 🔄 Transição de Ano Letivo**
3. **Digite a senha do banco de dados** quando solicitado
4. Se a senha estiver incorreta, o acesso será negado

### Passo 2: Verificar Informações
A tela mostrará:
- **Ano Letivo Atual**: O ano que será encerrado
- **Novo Ano Letivo**: O ano que será iniciado (automático: ano atual + 1)
- **Estatísticas**:
  - Total de Matrículas Ativas
  - Alunos que Continuarão (1º ao 8º ano - apenas ativos)
  - Alunos do 9º Ano Reprovados (média < 60)
  - Alunos a Excluir (transferidos/cancelados/evadidos)

### Passo 3: Simular a Transição
1. Clique em **"🔍 Simular Transição"**
2. Leia atentamente o resumo apresentado
3. Verifique se os números estão corretos
4. Clique em "Sim" para habilitar a execução

### Passo 4: Executar a Transição
1. Clique em **"✅ Executar Transição"**
2. Leia o aviso final
3. **Confirme que fez o backup**
4. Clique em "Sim" para continuar
5. **Digite novamente a senha do banco de dados** (medida de segurança adicional)
6. Se a senha estiver correta, a transição será executada
7. Se a senha estiver incorreta, a operação será cancelada

### Passo 5: Aguardar Conclusão
- A barra de progresso mostrará o andamento
- **NÃO FECHE O SISTEMA** durante o processo
- Aguarde a mensagem de conclusão

---

## 🔧 O Que o Sistema Faz Automaticamente

### 1. **Criação do Novo Ano Letivo**
   - Cria registro para o próximo ano (ex: 2026)
   - Mantém histórico de anos anteriores

### 2. **Encerramento de Matrículas Antigas**
   - Todas as matrículas com status "Ativo" do ano anterior
   - Mudam para status "Concluído"
   - **Não exclui dados**, apenas atualiza o status

### 3. **Criação de Novas Matrículas**
   - **APENAS para alunos com status "Ativo"**
   - **Alunos do 1º ao 8º ano**: Rematriculados na mesma série
   - **Alunos do 9º ano**:
     - ✅ **REPROVADOS** (média final < 60): Rematriculados no 9º ano
     - ❌ **APROVADOS** (média final ≥ 60): NÃO rematriculados (concluíram)
   - Mantém a mesma turma/série
   - Status inicial: "Ativo"
   - Ano letivo: Novo ano

### 4. **Exclusão Automática**
   Alunos **NÃO** serão rematriculados se tiverem status:
   - ❌ Transferido
   - ❌ Transferida
   - ❌ Cancelado
   - ❌ Evadido
   - ✅ Alunos do 9º ano APROVADOS (concluíram o ensino fundamental)

---

## 📊 Exemplo Prático

**Situação Atual (2025):**
- 250 alunos ativos (1º ao 8º ano)
- 49 alunos ativos (9º ano)
  - 40 aprovados (média ≥ 60)
  - 9 reprovados (média < 60)
- 42 alunos transferidos
- 4 alunos cancelados

**Após a Transição:**
- Ano 2025: 345 matrículas com status "Concluído"
- Ano 2026: 259 novas matrículas com status "Ativo"
  - 250 alunos (1º ao 8º ano)
  - 9 alunos (9º ano reprovados)
- Os 40 alunos do 9º ano aprovados NÃO foram rematriculados (concluíram)
- Os 46 alunos (transferidos + cancelados) NÃO foram rematriculados

---

## ✅ Verificações Pós-Transição

### 1. **Verifique o Novo Ano**
   - Vá para a página principal
   - Confirme que o dashboard mostra o ano 2026
   - Verifique se o total de alunos está correto

### 2. **Consulte as Matrículas**
   - Pesquise alguns alunos
   - Confirme que têm matrícula ativa no novo ano
   - Verifique se os dados estão corretos

### 3. **Confira os Excluídos**
   - Pesquise alunos transferidos
   - Confirme que NÃO têm matrícula no novo ano
   - Verifique se o histórico do ano anterior foi preservado

---

## 🆘 Resolução de Problemas

### Problema: "Nenhum ano letivo encontrado"
**Solução:** 
- Verifique se existe pelo menos um ano cadastrado
- Vá em: Menu → Administração → Anos Letivos

### Problema: "Erro ao conectar ao banco de dados"
**Solução:**
- Verifique a conexão com o banco
- Reinicie o sistema
- Verifique as credenciais em `conexao.py`

### Problema: "Números não batem com o esperado"
**Solução:**
- Verifique os status das matrículas manualmente
- Execute uma consulta SQL para confirmar:
  ```sql
  SELECT status, COUNT(*) 
  FROM Matriculas 
  WHERE ano_letivo_id = [ID_DO_ANO]
  GROUP BY status;
  ```

### Problema: "Preciso desfazer a transição"
**Solução:**
- **Use o backup feito antes da transição**
- Menu → Botão "Restaurar"
- Selecione o backup anterior à transição

---

## 📝 Notas Técnicas

### Status de Matrícula
- **Ativo**: Aluno frequenta regularmente
- **Concluído**: Matrícula encerrada ao fim do ano letivo
- **Transferido/Transferida**: Aluno mudou de escola
- **Cancelado**: Matrícula cancelada
- **Evadido**: Aluno abandonou os estudos

### Estrutura do Banco
```sql
-- Matrículas antigas (ano 2025)
UPDATE Matriculas 
SET status = 'Concluído' 
WHERE ano_letivo_id = 26 AND status = 'Ativo';

-- Novas matrículas (ano 2026)
INSERT INTO Matriculas (aluno_id, turma_id, ano_letivo_id, status)
SELECT aluno_id, turma_id, 27, 'Ativo'
FROM Matriculas
WHERE ano_letivo_id = 26 AND status = 'Concluído';
```

---

## 🔐 Segurança

### Proteção por Senha Dupla
Este módulo possui **dupla verificação de senha** para garantir segurança máxima:

1. **Primeira verificação (ao abrir)**:
   - Necessária para acessar a interface
   - Impede acesso não autorizado ao módulo
   - Senha: mesma do banco de dados (arquivo .env)

2. **Segunda verificação (ao executar)**:
   - Solicitada após clicar em "Executar Transição"
   - Confirma a intenção do usuário
   - Evita execução acidental
   - Senha: mesma do banco de dados (arquivo .env)

**⚠️ Importante:**
- Se você não souber a senha do banco de dados, **NÃO poderá executar a transição**
- A senha está configurada no arquivo `.env` na variável `DB_PASSWORD`
- Esta é uma medida de segurança crítica devido à irreversibilidade da operação

### Backup Automático
- O sistema possui backup automático em 2 horários: 14:05 e 17:00
- Também faz backup ao fechar o sistema
- **MAS faça backup manual antes da transição!**

### Logs
- Todas as operações são registradas
- Em caso de erro, verifique o console do sistema
- Erros são salvos com `traceback` completo

---

## 📞 Suporte

**Desenvolvido por:** Tarcisio Sousa de Almeida  
**Função:** Técnico em Administração Escolar  
**Data:** Novembro/2025

**Em caso de dúvidas:**
1. Consulte este guia
2. Verifique o arquivo `DASHBOARD_IMPLEMENTADO.md`
3. Entre em contato com o suporte técnico

---

## ✨ Dicas Importantes

1. **Faça a transição no início do ano letivo**
   - Não deixe para o meio do ano
   - Evita confusão com dados de múltiplos anos

2. **Revise os status antes da transição**
   - Corrija transferências não registradas
   - Atualize cancelamentos pendentes

3. **Documente o processo**
   - Anote a data da transição
   - Registre quaisquer problemas encontrados
   - Mantenha cópia do backup

4. **Teste em ambiente de desenvolvimento**
   - Se possível, teste em uma cópia do banco
   - Verifique o resultado antes de aplicar em produção

---

**🎯 Objetivo Final:**
Manter o banco de dados organizado, com histórico completo de cada ano letivo, facilitando consultas futuras e relatórios estatísticos.

**✅ Resultado Esperado:**
Sistema pronto para o novo ano letivo com apenas alunos ativos, preservando todo o histórico dos anos anteriores.
