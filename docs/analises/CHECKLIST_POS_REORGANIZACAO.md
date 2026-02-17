# ✅ Checklist Pós-Reorganização

Use este checklist para garantir que tudo está funcionando após a reorganização.

## 🔍 Verificações Imediatas

- [ ] **Testar main.py**
  ```bash
  python main.py
  ```
  ✅ Sistema deve iniciar sem erros

- [ ] **Verificar imports**
  ```bash
  python -c "from src.core.config_logs import get_logger; print('OK')"
  ```
  ✅ Deve imprimir "OK"

- [ ] **Executar testes básicos**
  ```bash
  pytest tests/ -v --maxfail=1
  ```
  ✅ Testes devem passar (ou mostrar erros já existentes)

## 📝 Tarefas de Organização

- [ ] **Revisar arquivos .bat**
  - Verificar se `automacao/batch/executar_sistema.bat` funciona
  - Ajustar caminhos se necessário (ver [GUIA_ATUALIZACAO_BAT.md](GUIA_ATUALIZACAO_BAT.md))

- [ ] **Consolidar diretório testes/**
  - Decidir se mantém `testes/` separado ou move tudo para `tests/`
  - Se mover, executar:
    ```bash
    Move-Item testes/* tests/
    Remove-Item testes/
    ```

- [ ] **Atualizar .gitignore** (se necessário)
  - Adicionar novos diretórios como `src/__pycache__/`
  - Verificar se `temp/`, `logs/`, etc estão ignorados

- [ ] **Criar backup**
  ```bash
  # Fazer commit das alterações
  git add .
  git commit -m "Reorganização completa do projeto"
  ```

## 🔧 Ajustes de Configuração

- [ ] **Verificar arquivos de configuração**
  - [ ] `.env` ainda acessível
  - [ ] `config/settings.py` funcionando
  - [ ] Caminhos de assets/imagens corretos

- [ ] **Atualizar IDEs/Editores**
  - [ ] Atualizar paths no VSCode/PyCharm
  - [ ] Reindexar projeto
  - [ ] Verificar linter/formatter

## 📚 Documentação

- [ ] **Ler documentação criada**
  - [ ] [ESTRUTURA_PROJETO.md](ESTRUTURA_PROJETO.md)
  - [ ] [docs/ORGANIZACAO_PROJETO.md](docs/ORGANIZACAO_PROJETO.md)
  - [ ] [RELATORIO_REORGANIZACAO_FINAL.md](RELATORIO_REORGANIZACAO_FINAL.md)

- [ ] **Atualizar README principal** (se houver informações antigas)

- [ ] **Comunicar equipe** sobre nova estrutura

## 🚀 CI/CD (Se Aplicável)

- [ ] **Atualizar pipelines**
  - [ ] Ajustar paths em workflows do GitHub Actions
  - [ ] Atualizar scripts de build
  - [ ] Verificar deploys automáticos

- [ ] **Atualizar Docker** (se usar)
  - [ ] Dockerfile com novos paths
  - [ ] docker-compose.yml atualizado

## 🧪 Testes Funcionais

- [ ] **Testar funcionalidades principais**
  - [ ] Login de usuário
  - [ ] Cadastro de aluno
  - [ ] Geração de boletim
  - [ ] Lançamento de notas
  - [ ] Exportação de relatórios

- [ ] **Verificar integrações**
  - [ ] Conexão com banco de dados
  - [ ] Upload de arquivos
  - [ ] Geração de PDFs
  - [ ] Drive/Cloud (se configurado)

## 📊 Limpeza (Opcional)

- [ ] **Remover arquivos obsoletos**
  - [ ] Verificar `arquivos_nao_utilizados/`
  - [ ] Limpar `temp/` se necessário
  - [ ] Revisar logs antigos em `logs/`

- [ ] **Otimizar .gitignore**
  ```
  __pycache__/
  *.pyc
  *.pyo
  src/__pycache__/
  scripts/__pycache__/
  automacao/__pycache__/
  ```

## ✅ Validação Final

- [ ] **Sistema funcionando 100%**
- [ ] **Todos os imports corretos**
- [ ] **Documentação atualizada**
- [ ] **Equipe comunicada**
- [ ] **Backup/commit realizado**

---

## 🎯 Ao Completar Este Checklist

Você terá:
- ✅ Sistema reorganizado e funcionando
- ✅ Documentação completa e atualizada
- ✅ Testes validados
- ✅ Equipe informada
- ✅ Backup seguro

## 📞 Precisa de Ajuda?

Consulte:
1. [ESTRUTURA_PROJETO.md](ESTRUTURA_PROJETO.md) - Guia rápido
2. [docs/ORGANIZACAO_PROJETO.md](docs/ORGANIZACAO_PROJETO.md) - Documentação completa
3. [GUIA_ATUALIZACAO_BAT.md](GUIA_ATUALIZACAO_BAT.md) - Ajuda com .bat

---

**Data**: 14/12/2025  
**Status**: Reorganização Concluída ✅
