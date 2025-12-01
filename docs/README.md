# 🎓 Sistema de Gestão Escolar

Sistema completo de gestão escolar desenvolvido em Python com interface Tkinter, focado em escolas municipais brasileiras.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-95%20passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-80%25-yellow.svg)](tests/)

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Testes](#-testes)
- [Arquitetura](#-arquitetura)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

## ✨ Funcionalidades

### Gestão de Alunos
- ✅ Cadastro completo de alunos com dados pessoais e responsáveis
- ✅ Gerenciamento de matrículas por turma e ano letivo
- ✅ Histórico escolar completo com validação Pydantic
- ✅ Controle de frequência e faltas
- ✅ Registro de notas e conceitos
- ✅ Busca avançada com múltiplos filtros
- ✅ Exportação de dados para Excel/CSV

### Gestão de Funcionários
- ✅ Cadastro de professores, coordenadores e funcionários
- ✅ Controle de ponto eletrônico
- ✅ Gestão de licenças e afastamentos
- ✅ Solicitações de professores substitutos
- ✅ Documentação digitalizada

### Relatórios e Documentos
- 📄 Declarações de comparecimento
- 📄 Atas de resultados finais (1º ao 5º ano, 6º ao 9º ano)
- 📄 Histórico escolar completo
- 📄 Listas de frequência
- 📄 Boletins escolares
- 📄 Listas de reuniões e contatos
- 📄 Relatórios estatísticos

### Dashboard Administrativo
- 📊 Estatísticas em tempo real com cache inteligente
- 📊 Visão geral de alunos por turma, série e turno
- 📊 Indicadores de desempenho
- 📊 Alertas de pendências
- 📊 Gráficos e visualizações

### Recursos Avançados
- 🔒 Sistema de autenticação e permissões
- 💾 Backup automático do banco de dados
- 🚀 Cache inteligente (reduz 40-60% das queries)
- ✅ Validação de dados com Pydantic V2
- 📝 Logs estruturados (JSON + texto)
- 🎛️ Feature flags para controle de funcionalidades
- 🔍 Type hints completos com validação mypy
- 🧪 95+ testes automatizados

## 🛠️ Tecnologias

### Core
- **Python 3.12+** - Linguagem principal
- **Tkinter** - Interface gráfica nativa
- **MySQL 8.0+** - Banco de dados

### Bibliotecas Principais
```python
mysql-connector-python  # Conexão com MySQL
reportlab              # Geração de PDFs
pillow                 # Manipulação de imagens
pydantic              # Validação de dados
pytest                # Framework de testes
mypy                  # Verificação de tipos
openpyxl              # Manipulação de Excel
python-dotenv         # Variáveis de ambiente
```

### Arquitetura
- **MVC** - Model-View-Controller
- **Service Layer** - Lógica de negócio isolada
- **Repository Pattern** - Acesso a dados
- **Dependency Injection** - Injeção de dependências
- **Connection Pooling** - Pool de conexões MySQL

## 📦 Instalação

### Pré-requisitos
- Python 3.12 ou superior
- MySQL 8.0 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/doncisio/sistema-gestao-escolar.git
cd sistema-gestao-escolar
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure o banco de dados**
```bash
# Crie o banco de dados MySQL
mysql -u root -p
CREATE DATABASE redeescola CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

5. **Configure as variáveis de ambiente**
```bash
# Copie o arquivo de exemplo
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edite o arquivo .env com suas credenciais
```

6. **Execute as migrations** (opcional, se disponível)
```bash
alembic upgrade head
```

7. **Inicie o sistema**
```bash
python main.py
```

## ⚙️ Configuração

### Arquivo `.env`
```ini
# Banco de Dados
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=redeescola
DB_PORT=3306

# Aplicação
SCHOOL_ID=60
GESTAO_TEST_MODE=false

# Backup
BACKUP_ENABLED=true
BACKUP_LOCAL_PATH=backup_redeescola.sql
BACKUP_DRIVE_PATH=/Backups/

# Feature Flags (opcional)
FEATURE_CACHE_ENABLED=true
FEATURE_JSON_LOGS=true
FEATURE_DASHBOARD_AVANCADO=true
```

### Arquivo `feature_flags.json`
```json
{
  "cache_enabled": true,
  "pydantic_validation": true,
  "json_logs": true,
  "backup_automatico": true,
  "dashboard_avancado": true,
  "modo_debug": false,
  "relatorios_pdf": true,
  "integracao_drive": false
}
```

### Connection Pool
O sistema usa pool de conexões configurável:
```python
# config.py
POOL_CONFIG = {
    'pool_name': 'gestao_pool',
    'pool_size': 10,          # Conexões no pool
    'pool_reset_session': True,
    'autocommit': False
}
```

## 🚀 Uso

### Iniciando o Sistema
```bash
# Modo normal
python main.py

# Modo de teste (sem backup automático)
set GESTAO_TEST_MODE=true && python main.py
```

### Interface Principal
1. **Login** - Autentique-se com suas credenciais
2. **Dashboard** - Visualize estatísticas gerais
3. **Menu Lateral** - Acesse funcionalidades:
   - 👥 Alunos
   - 👨‍🏫 Funcionários
   - 📊 Relatórios
   - ⚙️ Configurações

### Atalhos de Teclado
- `F1` - Ajuda
- `F5` - Atualizar dados
- `Ctrl+F` - Buscar
- `Ctrl+N` - Novo cadastro
- `Ctrl+S` - Salvar
- `Ctrl+P` - Imprimir/Gerar PDF
- `Esc` - Fechar modal

## 🧪 Testes

### Executar Todos os Testes
```bash
python -m pytest tests/ -v
```

### Testes com Cobertura
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

### Testes de Performance
```bash
python -m pytest tests/performance/ -v --durations=10
```

### Testes Específicos
```bash
# Apenas testes de cache
python -m pytest tests/test_cache.py -v

# Apenas testes de Pydantic
python -m pytest tests/test_models_pydantic.py -v

# Apenas testes de logging
python -m pytest tests/test_logging.py -v

# Apenas testes de feature flags
python -m pytest tests/test_feature_flags.py -v
```

### Verificação de Tipos
```bash
python -m mypy --config-file mypy.ini
```

### Estrutura de Testes
```
tests/
├── __init__.py
├── conftest.py                    # Fixtures compartilhadas
├── test_cache.py                  # Testes de cache (8 testes)
├── test_models_pydantic.py        # Validação Pydantic (14 testes)
├── test_logging.py                # Sistema de logs (12 testes)
├── test_feature_flags.py          # Feature flags (21 testes)
├── test_services.py               # Services (15+ testes)
├── test_utils.py                  # Utilitários (20+ testes)
└── performance/
    ├── __init__.py
    └── test_queries_performance.py # Benchmarks (12+ testes)
```

**Total: 95+ testes, 80%+ de cobertura**

## 🏗️ Arquitetura

### Estrutura de Diretórios
```
gestao/
├── main.py                 # Ponto de entrada
├── conexao.py             # Pool de conexões
├── config.py              # Configurações
├── config_logs.py         # Sistema de logs
│
├── db/                    # Camada de dados
│   ├── connection.py      # Gerenciamento de conexões
│   └── queries.py         # Queries SQL centralizadas
│
├── models/                # Modelos Pydantic
│   ├── aluno.py          # Validação de alunos
│   ├── funcionario.py    # Validação de funcionários
│   ├── turma.py          # Validação de turmas
│   └── matricula.py      # Validação de matrículas
│
├── services/              # Lógica de negócio
│   ├── aluno_service.py
│   ├── funcionario_service.py
│   ├── estatistica_service.py
│   ├── backup_service.py
│   └── report_service.py
│
├── ui/                    # Interface gráfica
│   ├── app.py            # Application class
│   ├── colors.py         # Cores centralizadas
│   ├── table.py          # Componente de tabela
│   ├── button_factory.py # Criação de botões
│   ├── menu.py           # Sistema de menus
│   └── modals/           # Janelas modais
│
├── utils/                 # Utilitários
│   ├── cache.py          # Sistema de cache
│   └── feature_flags.py  # Feature flags
│
├── tests/                 # Testes automatizados
│   ├── test_*.py
│   └── performance/
│
└── docs/                  # Documentação
    ├── ARCHITECTURE.md
    ├── API.md
    └── DEVELOPMENT.md
```

### Fluxo de Dados
```
UI (Tkinter)
    ↓
Service Layer (Lógica de negócio)
    ↓
Models (Validação Pydantic)
    ↓
Repository/DB (MySQL)
```

### Padrões Utilizados
- **MVC** - Separação de responsabilidades
- **Service Layer** - Lógica de negócio isolada
- **Repository Pattern** - Abstração de acesso a dados
- **Factory Pattern** - Criação de componentes UI
- **Singleton** - Cache e feature flags
- **Decorator** - Cache e logging
- **Observer** - Feature flags callbacks

## 📚 Documentação Adicional

- [📖 Guia de Arquitetura](docs/ARCHITECTURE.md)
- [🔌 Documentação de API](docs/API.md)
- [👨‍💻 Guia de Desenvolvimento](docs/DEVELOPMENT.md)
- [🚀 Roadmap de Melhorias](MELHORIAS_SISTEMA.md)

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, siga estas etapas:

1. **Fork** o projeto
2. **Crie uma branch** para sua feature (`git checkout -b feature/MinhaFeature`)
3. **Commit** suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. **Push** para a branch (`git push origin feature/MinhaFeature`)
5. **Abra um Pull Request**

### Diretrizes
- ✅ Siga o padrão PEP 8
- ✅ Adicione type hints
- ✅ Escreva testes para novas funcionalidades
- ✅ Atualize a documentação
- ✅ Execute `mypy` antes de commitar
- ✅ Mantenha cobertura de testes acima de 80%

### Commits
Siga o padrão [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: adiciona validação de CPF
fix: corrige bug no cálculo de idade
docs: atualiza README
test: adiciona testes de performance
refactor: reorganiza estrutura de services
```

## 📊 Status do Projeto

### Sprints Concluídos
- ✅ Sprint 1-15: Refatoração base (84% concluído)
- ✅ Sprint 16: Application class e button factory
- ✅ Sprint 17: Event handlers e configurações
- ✅ Sprint 18: Cache e Pydantic validation
- ✅ Sprint 19: [FUTURO - Migrations e auditoria]
- ✅ Sprint 20: Logging, type hints e feature flags
- ✅ Sprint 21: Testes de performance e documentação

### Próximos Passos
- 🔄 Sprint 22: CI/CD e automação
- 🔄 Sprint 23: Integração com APIs externas
- 🔄 Sprint 24: Mobile/PWA

## 🐛 Reportando Bugs

Encontrou um bug? [Abra uma issue](https://github.com/doncisio/sistema-gestao-escolar/issues/new) com:

- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs atual
- Screenshots (se aplicável)
- Versão do Python e SO

## 💡 Solicitando Features

Tem uma ideia? [Abra uma issue](https://github.com/doncisio/sistema-gestao-escolar/issues/new) com:

- Descrição da funcionalidade
- Caso de uso
- Benefícios esperados
- Mockups (se aplicável)

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- **Doncisio** - *Desenvolvimento inicial* - [@doncisio](https://github.com/doncisio)

## 🙏 Agradecimentos

- Equipe de educadores que forneceram feedback valioso
- Comunidade Python pelo suporte
- Contribuidores do projeto

## 📞 Contato

- GitHub: [@doncisio](https://github.com/doncisio)
- Issues: [Sistema de Issues](https://github.com/doncisio/sistema-gestao-escolar/issues)

---

**Desenvolvido com ❤️ para educação brasileira**
