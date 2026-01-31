# 🔒 Política de Segurança

## Informações Sensíveis

Este repositório **NÃO DEVE** conter:

### ❌ Nunca Commitar

- **Credenciais de banco de dados** (usuário, senha, host)
- **Tokens e chaves de API**
- **Credenciais do GEDUC** (usuário e senha)
- **Arquivos de configuração local** (.env, local_config.json, deepseek.json)
- **Arquivos de credenciais do Google** (credentials.json, token.pickle)
- **Dados pessoais de alunos** (NIS, documentos, fotos)
- **Logs com informações sensíveis**
- **Backups de banco de dados**

### ✅ Arquivos Seguros para Commit

- `.env.example` (com valores de exemplo)
- Código-fonte sem credenciais hardcoded
- Documentação
- Estrutura SQL (sem dados reais)
- Testes unitários (com dados mock)

## Configuração de Variáveis de Ambiente

### Arquivo .env (Local - Não Versionado)

Crie um arquivo `.env` na raiz do projeto com base no `.env.example`:

```bash
# Banco de Dados
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha_forte_aqui
DB_NAME=nome_do_banco
DB_POOL_SIZE=5

# Aplicação
ESCOLA_ID=60
ANO_LETIVO=2026
GESTAO_TEST_MODE=false

# GEDUC (usar variáveis de ambiente)
GEDUC_USER=seu_usuario_geduc
GEDUC_PASS=sua_senha_geduc

# Logs
LOG_LEVEL=INFO
```

### Variáveis de Ambiente do Sistema

Para ambientes de produção, configure as variáveis diretamente no sistema:

**Windows (PowerShell como Administrador):**
```powershell
[System.Environment]::SetEnvironmentVariable('DB_PASSWORD', 'sua_senha', 'Machine')
[System.Environment]::SetEnvironmentVariable('GEDUC_USER', 'seu_usuario', 'Machine')
[System.Environment]::SetEnvironmentVariable('GEDUC_PASS', 'sua_senha', 'Machine')
```

**Linux/Mac:**
```bash
export DB_PASSWORD="sua_senha"
export GEDUC_USER="seu_usuario"
export GEDUC_PASS="sua_senha"
```

## Boas Práticas de Segurança

### 1. Senhas Fortes
- Mínimo de 12 caracteres
- Combinar letras maiúsculas, minúsculas, números e símbolos
- Nunca usar senhas padrão ou sequenciais

### 2. Banco de Dados
- Usar usuário específico com privilégios mínimos necessários
- Nunca usar o usuário `root` em produção
- Ativar SSL/TLS para conexões remotas
- Fazer backups regulares em local seguro

### 3. Código
- Nunca fazer hardcode de credenciais
- Usar sempre variáveis de ambiente
- Validar e sanitizar todas as entradas de usuário
- Usar prepared statements para prevenir SQL Injection

### 4. Deploy
- Verificar que `.gitignore` está funcionando: `git status`
- Antes de tornar público, verificar histórico do Git: `git log --all --full-history --source`
- Considerar usar `git filter-branch` ou `BFG Repo-Cleaner` para remover credenciais do histórico

### 5. Acesso ao Sistema
- Ativar sistema de perfis de usuário (`perfis_habilitados: true` em `feature_flags.json`)
- Definir senhas fortes para todos os usuários
- Revisar permissões regularmente
- Manter logs de acesso atualizados

## Checklist de Segurança Antes de Tornar Público

- [ ] Arquivo `.env` não está no repositório
- [ ] Arquivo `credentials.json` não está no repositório
- [ ] Arquivos `local_config.json` e `deepseek.json` não estão no repositório
- [ ] Não há senhas hardcoded em `src/core/config.py`
- [ ] `.gitignore` está configurado corretamente
- [ ] `.env.example` contém apenas valores de exemplo
- [ ] Backups de banco de dados não estão no repositório
- [ ] Logs não contêm informações sensíveis
- [ ] Dados pessoais de alunos não estão no repositório
- [ ] README contém instruções claras de configuração
- [ ] Histórico do Git foi verificado para credenciais acidentais

## Verificação do Histórico do Git

Para verificar se há credenciais no histórico:

```bash
# Procurar por padrões sensíveis
git grep -i "password\|senha\|secret\|api_key" $(git rev-list --all)

# Verificar arquivos que já foram deletados
git log --all --full-history --source -- credentials.json
git log --all --full-history --source -- .env
```

## Remover Credenciais do Histórico

Se credenciais foram commitadas acidentalmente:

```bash
# Usando BFG Repo-Cleaner (recomendado)
java -jar bfg.jar --delete-files credentials.json
java -jar bfg.jar --replace-text passwords.txt  # arquivo com senhas para substituir

# Limpar e forçar push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin --force --all
```

## Reportar Vulnerabilidades

Se você encontrar vulnerabilidades de segurança neste projeto:

1. **NÃO** abra uma issue pública
2. Entre em contato diretamente com os mantenedores
3. Forneça detalhes sobre a vulnerabilidade
4. Aguarde confirmação antes de divulgar publicamente

## Recursos Adicionais

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Git Secrets](https://github.com/awslabs/git-secrets)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security.html)

---

**Última atualização:** Janeiro 2026
