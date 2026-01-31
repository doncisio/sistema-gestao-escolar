# 🔐 Checklist de Segurança - Repositório Público

## ✅ Correções Aplicadas

### 1. Credenciais Removidas do Código
- ✅ Removidas credenciais GEDUC hardcoded de `src/core/config.py`
- ✅ Removidas credenciais hardcoded de `src/avaliacoes/integrador_preenchimento.py`
- ✅ Configurado para usar variáveis de ambiente `GEDUC_USER` e `GEDUC_PASS`

### 2. Arquivos Sensíveis Removidos do Git
- ✅ `deepseek.json` removido do rastreamento
- ✅ `local_config.json` removido do rastreamento
- ✅ `.gitignore` atualizado para prevenir commits futuros

### 3. Documentação de Segurança
- ✅ Criado `SECURITY.md` com políticas de segurança
- ✅ Atualizado `README.md` com avisos de segurança
- ✅ Atualizado `.env.example` com instruções claras

### 4. Configuração do .gitignore
Adicionados ao `.gitignore`:
- ✅ `.env` e variações
- ✅ `credentials.json`
- ✅ `local_config.json`
- ✅ `deepseek.json`
- ✅ `dados/nis/` (dados pessoais)
- ✅ `temp/` e `uploads/`

## ⚠️ Ações Necessárias Antes de Tornar Público

### 1. Verificar Histórico do Git
```bash
# Verificar se há credenciais no histórico
git grep -i "01813518386" $(git rev-list --all)
git log --all --full-history --source -- deepseek.json
git log --all --full-history --source -- local_config.json
```

### 2. Limpar Histórico (se necessário)
Se encontrar credenciais no histórico, use:

```bash
# Opção 1: BFG Repo Cleaner (recomendado)
java -jar bfg.jar --delete-files deepseek.json
java -jar bfg.jar --delete-files local_config.json
java -jar bfg.jar --replace-text passwords.txt

# Opção 2: git filter-branch (mais complexo)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch deepseek.json local_config.json" \
  --prune-empty --tag-name-filter cat -- --all

# Limpar refs e forçar push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
git push origin --force --tags
```

### 3. Verificar Arquivos Grandes
```bash
# Listar arquivos grandes no repositório
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sed -n 's/^blob //p' | \
  sort --numeric-sort --key=2 | \
  tail -20
```

### 4. Revisar Logs
```bash
# Verificar se há informações sensíveis em logs commitados
git ls-files | grep -E "\.log$|logs/"
```

### 5. Verificar Dados Pessoais
```bash
# Verificar se há CPFs, RGs ou outros dados pessoais
git grep -i "cpf\|rg\|nis" $(git rev-list --all)
```

## 📋 Checklist Final

Antes de executar `git push` para tornar o repositório público:

- [ ] Executei `git status` e não há arquivos `.env`, `credentials.json`, ou `local_config.json`
- [ ] Verifiquei que `src/core/config.py` não contém credenciais hardcoded
- [ ] Verifiquei que `src/avaliacoes/integrador_preenchimento.py` usa variáveis de ambiente
- [ ] Revisei o `.gitignore` e confirmei que está correto
- [ ] Li e entendi o `SECURITY.md`
- [ ] Verifiquei que `.env.example` contém apenas exemplos
- [ ] Executei verificação de histórico do Git (comandos acima)
- [ ] Não há arquivos de log com dados sensíveis
- [ ] Não há backups de banco de dados no repositório
- [ ] Não há dados pessoais de alunos no repositório
- [ ] Criei um backup local antes de tornar público
- [ ] Configurei as variáveis de ambiente no sistema de produção

## 🔄 Após Tornar Público

### Configuração para Novos Usuários

1. **Clone o repositório**
   ```bash
   git clone <url-do-repositorio>
   cd gestao
   ```

2. **Configure o ambiente**
   ```bash
   copy .env.example .env
   # Edite o .env com suas credenciais
   ```

3. **Instale dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o banco de dados**
   - Crie o banco de dados
   - Execute as migrations em `migrations/`
   - Execute os scripts em `db/migrations/`

5. **Execute o sistema**
   ```bash
   python main.py
   ```

## 🚨 Em Caso de Vazamento Acidental

Se credenciais forem acidentalmente commitadas e enviadas para o repositório público:

1. **Ação Imediata:**
   - Altere TODAS as senhas vazadas imediatamente
   - Revogue tokens e chaves de API
   - Notifique a equipe de segurança

2. **Limpar o Repositório:**
   - Use BFG Repo Cleaner para remover do histórico
   - Force push para sobrescrever o histórico
   - Notifique colaboradores para fazer novo clone

3. **Prevenir Futuros Incidentes:**
   - Configure pre-commit hooks com git-secrets
   - Use ferramentas de análise de segurança (GitGuardian, TruffleHog)
   - Revise processo de desenvolvimento

## 📚 Ferramentas Recomendadas

### Análise de Segurança
- [git-secrets](https://github.com/awslabs/git-secrets) - Previne commits de credenciais
- [TruffleHog](https://github.com/trufflesecurity/truffleHog) - Busca credenciais no histórico
- [GitGuardian](https://www.gitguardian.com/) - Monitora repositórios

### Limpeza de Histórico
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) - Limpa histórico do Git
- [git-filter-repo](https://github.com/newren/git-filter-repo) - Alternativa moderna ao filter-branch

### Gerenciamento de Secrets
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Gerencia variáveis de ambiente
- [Azure Key Vault](https://azure.microsoft.com/services/key-vault/) - Vault corporativo
- [HashiCorp Vault](https://www.vaultproject.io/) - Gerenciamento de secrets

---

**Data da Revisão:** 31 de Janeiro de 2026  
**Responsável:** Sistema Automatizado  
**Status:** ✅ Pronto para tornar público (após verificação do histórico)
