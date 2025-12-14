# Sistema de Gestão Escolar

Sistema completo para gestão de escolas, incluindo matrículas, frequência, notas, relatórios e muito mais.

## 🚀 Quick Start

```bash
# Executar o sistema
python main.py

# Ou usar o arquivo .bat
automacao\batch\executar_sistema.bat
```

## 📁 Estrutura do Projeto

```
c:\gestao\
├── src/                 # Código fonte principal
├── scripts/             # Scripts utilitários
├── automacao/           # Automação (.bat, PowerShell, Python)
├── tests/              # Testes
├── docs/               # Documentação
├── config/             # Configurações
├── assets/             # Recursos
└── main.py             # Ponto de entrada
```

**📖 Para detalhes completos, consulte:**
- [ESTRUTURA_PROJETO.md](ESTRUTURA_PROJETO.md) - Guia rápido da estrutura
- [docs/ORGANIZACAO_PROJETO.md](docs/ORGANIZACAO_PROJETO.md) - Documentação completa
- [RELATORIO_REORGANIZACAO_FINAL.md](RELATORIO_REORGANIZACAO_FINAL.md) - Detalhes da reorganização

## ✨ Recursos

- ✅ Gestão de alunos e matrículas
- ✅ Controle de frequência e notas
- ✅ Geração de relatórios e documentos
- ✅ Sistema de avaliações BNCC
- ✅ Gestão de funcionários
- ✅ Dashboards para coordenadores e professores
- ✅ Backup automático
- ✅ Sistema de perfis de usuário

## 🔧 Configuração

1. Configure o arquivo `.env` com suas credenciais
2. Execute `python main.py` para iniciar
3. Consulte `docs/` para documentação detalhada

## 📚 Documentação

- **Guia Rápido**: [ESTRUTURA_PROJETO.md](ESTRUTURA_PROJETO.md)
- **Documentação Completa**: [docs/ORGANIZACAO_PROJETO.md](docs/ORGANIZACAO_PROJETO.md)
- **Arquitetura**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Desenvolvimento**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

## 🎯 Principais Módulos

### src/core/
Configurações essenciais, conexão com BD, logs

### src/relatorios/
Geração de atas, listas, boletins, certificados

### src/interfaces/
Interfaces de cadastro, edição e gerenciamento

### scripts/
Scripts de manutenção, migração, diagnóstico e desenvolvimento

### automacao/
Arquivos .bat e scripts para automação de tarefas

## 🧪 Testes

```bash
# Executar todos os testes
pytest tests/

# Teste específico
python -m pytest tests/test_specific.py
```

## 📦 Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
python scripts/auxiliares/setup_wizard.py
```

## 🔄 Reorganização Recente

O projeto foi reorganizado em 14/12/2025 para melhor organização e manutenibilidade.
- ✅ 120+ arquivos reorganizados
- ✅ 31 novos diretórios criados
- ✅ 436 imports corrigidos automaticamente
- ✅ Estrutura modular e escalável

Para detalhes, consulte: [RELATORIO_REORGANIZACAO_FINAL.md](RELATORIO_REORGANIZACAO_FINAL.md)

## 📄 Licença

Ver [LICENSE.txt](LICENSE.txt)

## 👥 Contribuindo

1. Consulte a estrutura do projeto em [ESTRUTURA_PROJETO.md](ESTRUTURA_PROJETO.md)
2. Siga as convenções de código (snake_case para arquivos)
3. Documente suas alterações
4. Execute os testes antes de commitar

---

**Status**: ✅ Em Produção  
**Última Reorganização**: 14/12/2025  
**Python**: 3.8+
