# 👨‍💻 Guia de Desenvolvimento

## Configurando o Ambiente

### 1. Instalar Ferramentas

```bash
# Python 3.12+
python --version

# Git
git --version

# MySQL 8.0+
mysql --version

# Editor recomendado: VS Code
code --version
```

### 2. Clonar e Configurar

```bash
# Clonar repositório
git clone https://github.com/doncisio/sistema-gestao-escolar.git
cd sistema-gestao-escolar

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt
```

### 3. Configurar Banco de Dados

```sql
-- Criar banco
CREATE DATABASE redeescola_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Criar usuário de desenvolvimento
CREATE USER 'gestao_dev'@'localhost' IDENTIFIED BY 'senha_dev';
GRANT ALL PRIVILEGES ON redeescola_dev.* TO 'gestao_dev'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Variáveis de Ambiente

```bash
# .env.development
DB_HOST=localhost
DB_USER=gestao_dev
DB_PASSWORD=senha_dev
DB_NAME=redeescola_dev
DB_PORT=3306

SCHOOL_ID=60
GESTAO_TEST_MODE=true

# Feature flags para desenvolvimento
FEATURE_MODO_DEBUG=true
FEATURE_JSON_LOGS=true
```

## Estrutura de Branches

```
main                    # Produção estável
├── develop             # Desenvolvimento principal
│   ├── feature/*       # Novas funcionalidades
│   ├── bugfix/*        # Correções de bugs
│   ├── hotfix/*        # Correções urgentes
│   └── refactor/*      # Refatorações
└── release/*           # Preparação para release
```

### Workflow Git

```bash
# 1. Criar branch de feature
git checkout develop
git pull origin develop
git checkout -b feature/nome-da-feature

# 2. Desenvolver e commitar
git add .
git commit -m "feat: adiciona validação de CPF"

# 3. Push e Pull Request
git push origin feature/nome-da-feature
# Criar PR no GitHub: feature/nome-da-feature -> develop

# 4. Após aprovação e merge
git checkout develop
git pull origin develop
git branch -d feature/nome-da-feature
```

## Padrões de Código

### Style Guide

Seguimos **PEP 8** com algumas extensões:

```python
# ✅ BOM
def criar_aluno(nome: str, data_nascimento: date) -> Tuple[bool, str]:
    """
    Cria um novo aluno no sistema.
    
    Args:
        nome: Nome completo do aluno
        data_nascimento: Data de nascimento
    
    Returns:
        Tupla (sucesso, mensagem)
    
    Raises:
        ValidationError: Se dados inválidos
    """
    try:
        aluno = AlunoCreate(nome=nome, data_nascimento=data_nascimento)
        # Lógica de criação
        return True, "Aluno criado com sucesso"
    except ValidationError as e:
        logger.error(f"Erro ao criar aluno: {e}")
        return False, f"Dados inválidos: {e}"

# ❌ RUIM
def criar_aluno(nome,data_nascimento):
    aluno = AlunoCreate(nome=nome, data_nascimento=data_nascimento)
    return True,"Aluno criado com sucesso"
```

### Naming Conventions

```python
# Classes: PascalCase
class AlunoService:
    pass

# Funções/métodos: snake_case
def obter_estatisticas_alunos():
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_ALUNOS_POR_TURMA = 35
DB_POOL_SIZE = 10

# Variáveis privadas: _prefixo
class Cache:
    def __init__(self):
        self._cache = {}
        self._ttl = 300

# Type hints sempre
def processar(dados: List[Dict[str, Any]]) -> Optional[str]:
    pass
```

### Docstrings

```python
def funcao_exemplo(
    param1: str,
    param2: int,
    opcional: Optional[bool] = None
) -> Tuple[bool, str]:
    """
    Breve descrição em uma linha.
    
    Descrição detalhada explicando o que a função faz,
    quando usar, e qualquer informação importante.
    
    Args:
        param1: Descrição do primeiro parâmetro
        param2: Descrição do segundo parâmetro
        opcional: Descrição do parâmetro opcional (default: None)
    
    Returns:
        Tupla contendo:
        - bool: True se sucesso, False se falha
        - str: Mensagem descritiva do resultado
    
    Raises:
        ValueError: Se param2 for negativo
        DatabaseError: Se erro ao acessar banco
    
    Example:
        >>> success, msg = funcao_exemplo("teste", 10)
        >>> print(success, msg)
        True "Operação concluída"
    
    Note:
        Esta função faz uso de cache com TTL de 5 minutos.
    """
    pass
```

## Testes

### Estrutura de Testes

```python
# tests/test_aluno_service.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.aluno_service import criar_aluno
from models.aluno import AlunoCreate
from pydantic import ValidationError

class TestAlunoService:
    """Testes para AlunoService"""
    
    @pytest.fixture
    def dados_aluno_valido(self):
        """Fixture com dados válidos de aluno"""
        return {
            'nome': 'João Silva',
            'data_nascimento': '2010-05-15',
            'mae': 'Maria Silva',
            'escola_id': 60,
            'responsavel_nome': 'Maria Silva',
            'responsavel_cpf': '12345678901',
            'responsavel_telefone': '11987654321'
        }
    
    @patch('services.aluno_service.get_cursor')
    def test_criar_aluno_sucesso(self, mock_cursor, dados_aluno_valido):
        """Deve criar aluno com dados válidos"""
        # Arrange
        mock_cursor_obj = MagicMock()
        mock_cursor_obj.__enter__ = Mock(return_value=mock_cursor_obj)
        mock_cursor_obj.__exit__ = Mock(return_value=False)
        mock_cursor.return_value = mock_cursor_obj
        mock_cursor_obj.lastrowid = 1
        
        # Act
        success, msg = criar_aluno(dados_aluno_valido)
        
        # Assert
        assert success is True
        assert 'sucesso' in msg.lower()
        mock_cursor_obj.execute.assert_called_once()
    
    def test_criar_aluno_dados_invalidos(self):
        """Deve falhar com dados inválidos"""
        # Arrange
        dados_invalidos = {'nome': 'Jo'}  # Nome muito curto
        
        # Act & Assert
        with pytest.raises(ValidationError):
            AlunoCreate(**dados_invalidos)
    
    @patch('services.aluno_service.get_cursor')
    def test_criar_aluno_erro_banco(self, mock_cursor, dados_aluno_valido):
        """Deve lidar com erros do banco de dados"""
        # Arrange
        mock_cursor.side_effect = Exception("Erro de conexão")
        
        # Act
        success, msg = criar_aluno(dados_aluno_valido)
        
        # Assert
        assert success is False
        assert 'erro' in msg.lower()
```

### Executar Testes

```bash
# Todos os testes
pytest tests/ -v

# Testes específicos
pytest tests/test_aluno_service.py -v
pytest tests/test_aluno_service.py::TestAlunoService::test_criar_aluno_sucesso -v

# Com cobertura
pytest tests/ --cov=services --cov-report=html

# Testes de performance
pytest tests/performance/ -v --durations=10

# Marcar testes
pytest tests/ -m "slow" -v  # Apenas testes lentos
pytest tests/ -m "not slow" -v  # Excluir testes lentos
```

### Fixtures Compartilhadas

```python
# tests/conftest.py
import pytest
from conexao import inicializar_pool, fechar_pool

@pytest.fixture(scope='session')
def db_pool():
    """Inicializa pool de conexões para testes"""
    inicializar_pool()
    yield
    fechar_pool()

@pytest.fixture
def aluno_factory():
    """Factory para criar alunos de teste"""
    def _create_aluno(**kwargs):
        defaults = {
            'nome': 'Aluno Teste',
            'data_nascimento': '2010-01-01',
            'mae': 'Mãe Teste',
            'escola_id': 60,
            'responsavel_nome': 'Responsável Teste',
            'responsavel_cpf': '12345678901',
            'responsavel_telefone': '11987654321'
        }
        defaults.update(kwargs)
        return defaults
    return _create_aluno
```

## Debugging

### VS Code Launch Configuration

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "env": {
                "GESTAO_TEST_MODE": "true",
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": [
                "tests/",
                "-v"
            ],
            "console": "integratedTerminal"
        }
    ]
}
```

### Logging para Debug

```python
import logging
from config_logs import setup_logging

# Modo debug
logger = setup_logging(
    app_name='gestao_dev',
    rotation_type='size',
    formatter_type='key-value'
)
logger.setLevel(logging.DEBUG)

# Usar logger
logger.debug("Iniciando processamento de aluno")
logger.debug(f"Dados recebidos: {dados}")
logger.debug(f"Query executada: {query}")
```

### Breakpoints

```python
# Usando debugpy
import debugpy
debugpy.breakpoint()

# Usando pdb
import pdb
pdb.set_trace()

# Usando breakpoint() (Python 3.7+)
breakpoint()
```

## Performance

### Profiling

```bash
# Profiling com cProfile
python -m cProfile -o profile.stats main.py

# Analisar resultados
python -m pstats profile.stats
>>> sort time
>>> stats 20

# Profiling com line_profiler
pip install line_profiler
kernprof -l -v script.py
```

### Benchmarking

```python
import time
from statistics import mean, median

def benchmark(func, iterations=100):
    """Benchmark de uma função"""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    
    return {
        'mean': mean(times),
        'median': median(times),
        'min': min(times),
        'max': max(times)
    }

# Uso
stats = benchmark(lambda: obter_estatisticas_alunos(), iterations=50)
print(f"Tempo médio: {stats['mean']*1000:.2f}ms")
```

### Otimização de Queries

```python
# ❌ RUIM - N+1 queries
def listar_alunos_com_turmas():
    alunos = executar_query("SELECT * FROM alunos")
    for aluno in alunos:
        turma = executar_query(
            "SELECT nome_turma FROM turmas WHERE id = %s",
            (aluno['turma_id'],)
        )
        aluno['turma'] = turma['nome_turma']
    return alunos

# ✅ BOM - JOIN
def listar_alunos_com_turmas():
    return executar_query("""
        SELECT a.*, t.nome_turma
        FROM alunos a
        LEFT JOIN turmas t ON a.turma_id = t.id
    """)
```

## CI/CD

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: redeescola_test
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      env:
        DB_HOST: 127.0.0.1
        DB_USER: root
        DB_PASSWORD: root
        DB_NAME: redeescola_test
        GESTAO_TEST_MODE: true
      run: |
        pytest tests/ --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.12
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

```bash
# Instalar pre-commit
pip install pre-commit
pre-commit install

# Executar manualmente
pre-commit run --all-files
```

## Releases

### Versionamento

Seguimos **Semantic Versioning** (SemVer):

```
MAJOR.MINOR.PATCH

1.0.0 → 1.0.1  (bugfix)
1.0.1 → 1.1.0  (nova feature)
1.1.0 → 2.0.0  (breaking change)
```

### Changelog

```markdown
# Changelog

## [1.2.0] - 2025-11-21

### Added
- Sistema de cache inteligente com TTL configurável
- Validação de dados com Pydantic V2
- Feature flags para controle de funcionalidades
- 95+ testes automatizados

### Changed
- Logs agora são estruturados em JSON
- Dashboard com performance 60% melhor

### Fixed
- Correção no cálculo de estatísticas por turno
- Bug na geração de PDFs grandes

### Deprecated
- Função `obter_aluno_legado()` será removida em 2.0.0

### Security
- Implementada validação de CPF com algoritmo completo
```

### Processo de Release

```bash
# 1. Criar branch de release
git checkout develop
git checkout -b release/1.2.0

# 2. Atualizar versão
# Editar __version__ em __init__.py
# Atualizar CHANGELOG.md

# 3. Commit e merge
git add .
git commit -m "chore: release 1.2.0"
git checkout main
git merge release/1.2.0
git tag -a v1.2.0 -m "Release 1.2.0"

# 4. Push
git push origin main
git push origin v1.2.0

# 5. Merge de volta para develop
git checkout develop
git merge main
git push origin develop

# 6. Deletar branch de release
git branch -d release/1.2.0
```

## Boas Práticas

### DRY (Don't Repeat Yourself)

```python
# ❌ RUIM
def criar_aluno(data):
    nome = data['nome']
    cpf = data['cpf']
    # Validar CPF
    if len(cpf) != 11 or not cpf.isdigit():
        return False, "CPF inválido"
    # ...

def atualizar_aluno(id, data):
    if 'cpf' in data:
        cpf = data['cpf']
        # Validar CPF
        if len(cpf) != 11 or not cpf.isdigit():
            return False, "CPF inválido"
    # ...

# ✅ BOM
def validar_cpf(cpf: str) -> bool:
    """Valida formato de CPF"""
    return len(cpf) == 11 and cpf.isdigit()

def criar_aluno(data):
    if not validar_cpf(data['cpf']):
        return False, "CPF inválido"
    # ...

def atualizar_aluno(id, data):
    if 'cpf' in data and not validar_cpf(data['cpf']):
        return False, "CPF inválido"
    # ...
```

### SOLID

```python
# Single Responsibility Principle
class AlunoRepository:
    """Apenas acesso a dados de alunos"""
    def buscar_por_id(self, id): pass
    def salvar(self, aluno): pass

class AlunoValidator:
    """Apenas validação de alunos"""
    def validar(self, aluno): pass

class AlunoService:
    """Apenas lógica de negócio de alunos"""
    def __init__(self, repository, validator):
        self.repo = repository
        self.validator = validator
    
    def criar_aluno(self, data):
        if not self.validator.validar(data):
            return False
        return self.repo.salvar(data)
```

### Error Handling

```python
# ✅ BOM - Específico e informativo
try:
    aluno = criar_aluno(data)
except ValidationError as e:
    logger.error(f"Dados inválidos: {e}")
    return False, f"Erro de validação: {e}"
except DatabaseError as e:
    logger.critical(f"Erro no banco: {e}")
    return False, "Erro ao salvar. Tente novamente."
except Exception as e:
    logger.exception("Erro inesperado ao criar aluno")
    return False, "Erro interno. Contate o suporte."

# ❌ RUIM - Genérico
try:
    aluno = criar_aluno(data)
except:
    return False, "Erro"
```

## Recursos

### Documentação Útil
- [Python Docs](https://docs.python.org/3/)
- [PEP 8](https://peps.python.org/pep-0008/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [pytest Docs](https://docs.pytest.org/)
- [MySQL Docs](https://dev.mysql.com/doc/)

### Ferramentas Recomendadas
- **VS Code** - Editor
- **Black** - Formatador
- **Flake8** - Linter
- **Mypy** - Type checker
- **pytest** - Framework de testes
- **Postman** - Testes de API (futuros)

---

**Última atualização**: 21 de novembro de 2025
