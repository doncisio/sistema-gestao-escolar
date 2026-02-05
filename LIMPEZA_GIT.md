# 🧹 CHECKLIST DE LIMPEZA PARA PUBLICAÇÃO NO GIT

## ⚠️ CRÍTICO - Fazer ANTES de publicar

### 1. Remover Arquivos com Credenciais
```bash
# Execute estes comandos no terminal:
rm credentials.json
rm deepseek.json  
rm local_config.json
rm temp_admin_check.txt
```

### 2. Limpar Arquivos Temporários
```bash
rm ata_8ano_*.txt
rm sync_for_other_pc.bat.local.backup
rm -rf arquivos_nao_utilizados/uncommitted-changes-*.patch
```

### 3. Revisar e Limpar Documentação

#### Arquivos para REMOVER menções a IA:
- ■ `docs/RESUMO_INTERFACE_UNIFICADA.md` (linha 264)
- ■ `docs/PROPOSTA_BANCO_QUESTOES_BNCC.md` (linhas 792, 1315)
- ■ `docs/PLANO_EXPANSAO_MODULOS_DASHBOARD.md` (linha 1103)
- ■ `docs/MELHORIAS_IMPLEMENTADAS_QUESTOES.md` (linha 272)
- ■ `docs/GERACAO_PDF_AVALIACOES.md` (linha 377)
- ■ `docs/FINALIZACAO_REORGANIZACAO.md` (linhas 170, 279)
- ■ `docs/ESTRUTURA_FINAL.md` (linhas 125, 196)
- ■ `docs/ELIMINACAO_DEPENDENCIAS_CIRCULARES.md` (linha 310)
- ■ `docs/ANALISE_MELHORIAS_SISTEMA.md` (linha 1292)
- ■ `docs/ORGANIZACAO_PROJETO.md` (linha 583)

**Ação sugerida:** Substituir "GitHub Copilot" por "Desenvolvedor" ou simplesmente remover a linha de autoria.

#### Arquivos para DELETAR (conteúdo muito técnico/interno):
- ■ `docs/todos_codigos_sistema.txt` (dump completo do código)
- ■ `docs/lista_arquivos_codigo.txt`
- ■ `docs/lista_arquivos_temp.txt`
- ■ `docs/pytest_full_output.txt`
- ■ `docs/ANALISE_main_py.md.bak`

### 4. Limpar Configurações de Desenvolvimento

#### Remover de `/config`:
```bash
rm config/relatorio_copia_disciplinas_*.txt
rm config/revisao_sincronizacao_escolas_*.csv
rm config/casos_similares_*.csv
```

### 5. Verificar Testes com Senhas Hardcoded

Arquivos que contêm senhas de teste (OK manter, mas revisar):
- `tests/test_filtro_perfil.py` (linha 109, 117) - senha "Prof@123"
- `tests/test_fase6_completo.py` (linha 89) - senha "senha_errada"

**Ação:** Essas são senhas de TESTE, podem permanecer se claramente marcadas como tal.

### 6. Criar Arquivo .env.example

✅ Já está no .gitignore, mas crie um exemplo:
```bash
# Copie de .env.example para .env e preencha com suas credenciais
cp .env.example .env
```

### 7. Verificar .gitignore Atualizado

✅ Já atualizado com:
- deepseek.json
- local_config.json  
- temp_*.txt
- ata_*.txt
- Documentação sensível

---

## 🚀 Comandos para Executar

### Passo 1: Backup de segurança
```powershell
# Faça backup antes de deletar
git status > arquivos_antes_limpeza.txt
```

### Passo 2: Remover arquivos sensíveis
```powershell
# Credenciais
Remove-Item credentials.json -ErrorAction SilentlyContinue
Remove-Item deepseek.json -ErrorAction SilentlyContinue
Remove-Item local_config.json -ErrorAction SilentlyContinue

# Temporários
Remove-Item temp_admin_check.txt -ErrorAction SilentlyContinue
Remove-Item ata_8ano_*.txt -ErrorAction SilentlyContinue
Remove-Item sync_for_other_pc.bat.local.backup -ErrorAction SilentlyContinue

# Docs muito técnicos
Remove-Item docs\todos_codigos_sistema.txt -ErrorAction SilentlyContinue
Remove-Item docs\lista_arquivos_*.txt -ErrorAction SilentlyContinue
Remove-Item docs\pytest_full_output.txt -ErrorAction SilentlyContinue
Remove-Item docs\ANALISE_main_py.md.bak -ErrorAction SilentlyContinue

# Config temporários
Remove-Item config\relatorio_*.txt -ErrorAction SilentlyContinue
Remove-Item config\revisao_*.csv -ErrorAction SilentlyContinue
Remove-Item config\casos_*.csv -ErrorAction SilentlyContinue
```

### Passo 3: Verificar o que será commitado
```powershell
git status
git add .
git status  # Verificar novamente
```

### Passo 4: Verificar se credenciais não vazaram
```powershell
# Buscar por possíveis vazamentos
git grep -i "api_key"
git grep -i "client_secret"
git grep -i "sk-7274"  # Parte da chave DeepSeek
```

---

## 📋 Checklist Final

Antes de fazer push:

- [ ] Removidos todos os arquivos .json com credenciais
- [ ] Limpas menções a "GitHub Copilot", "Claude", "DeepSeek" da documentação
- [ ] Removidos arquivos temporários (temp_*, ata_*, sync_*)
- [ ] .gitignore atualizado
- [ ] .env.example criado
- [ ] README.md atualizado com instruções de instalação
- [ ] Executado `git status` para conferir
- [ ] Executado busca por credenciais no histórico do Git
- [ ] Testado clone fresh em outra pasta para verificar

---

## ⚡ Automação (Script PowerShell)

Quer que eu crie um script PowerShell que faça toda a limpeza automaticamente?
