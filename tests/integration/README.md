# 🧪 Testes de Integração

## 📋 Visão Geral

Esta pasta contém todos os testes de integração end-to-end do sistema de gestão escolar. Os testes validam fluxos completos de negócio, incluindo:

- ✅ Cadastro de aluno → Matrícula → Lançamento de notas → Histórico escolar
- ✅ Backup e restauração de dados
- ✅ Geração de documentos (boletins, declarações, relatórios)
- ✅ Operações de CRUD com funcionários
- ✅ Integração entre módulos

## 🏗️ Estrutura

```
tests/integration/
├── conftest.py                      # Configurações e fixtures compartilhadas
├── test_fluxos_completos.py         # Testes de fluxos end-to-end
├── test_geracao_documentos.py       # Testes de geração de documentos
├── test_matricula_flow.py           # Testes de fluxo de matrícula
└── test_services_sprint8.py         # Testes de services (legado)
```

## 🚀 Executando os Testes

### Opção 1: Executar Todos os Testes

```bash
# Windows PowerShell
python run_integration_tests.py

# Com cobertura
python run_integration_tests.py --coverage

# Com relatório HTML
python run_integration_tests.py --html
```

### Opção 2: Usar pytest Diretamente

```bash
# Executar todos os testes de integração
pytest tests/integration/ -v

# Executar teste específico
pytest tests/integration/test_fluxos_completos.py -v

# Executar apenas testes marcados
pytest tests/integration/ -m integration

# Pular testes lentos
pytest tests/integration/ --skip-slow

# Com cobertura detalhada
pytest tests/integration/ --cov=. --cov-report=html
```

### Opção 3: VS Code

1. Abra o painel de testes (ícone de béquer na barra lateral)
2. Navegue até `tests/integration/`
3. Clique no ícone ▶️ para executar

## 📊 Tipos de Testes

### 1. Testes de Fluxo Completo (`test_fluxos_completos.py`)

Testam jornadas completas de usuário:

```python
def test_fluxo_completo_aluno_matricula_notas_historico():
    """
    Fluxo: Cadastro → Matrícula → Notas → Histórico
    
    1. Cria aluno com dados válidos
    2. Matricula em turma ativa
    3. Lança notas em todas as disciplinas
    4. Gera e valida histórico escolar
    """
```

**Cenários cobertos:**
- ✅ Cadastro completo de aluno com responsável
- ✅ Matrícula em turma
- ✅ Lançamento de notas por bimestre
- ✅ Validação de matrícula duplicada
- ✅ Geração de histórico escolar

### 2. Testes de Backup (`test_fluxos_completos.py`)

Validam sistema de backup e restauração:

```python
def test_backup_criado_com_sucesso():
    """Valida que backup é criado e arquivo existe."""

def test_backup_automatico_agendado():
    """Valida agendamento de backups automáticos."""
```

**Cenários cobertos:**
- ✅ Criação de backup manual
- ✅ Verificação de arquivo de backup
- ✅ Agendamento automático
- ✅ Restauração de dados (quando implementado)

### 3. Testes de Documentos (`test_geracao_documentos.py`)

Testam geração de todos os tipos de documentos:

```python
def test_gerar_boletim_aluno():
    """Valida geração de boletim escolar."""

def test_gerar_declaracao_comparecimento():
    """Valida geração de declaração."""

def test_gerar_historico_escolar():
    """Valida geração de histórico."""
```

**Documentos testados:**
- ✅ Boletins escolares
- ✅ Declarações de comparecimento
- ✅ Históricos escolares
- ✅ Listas de presença
- ✅ Relatórios de notas
- ✅ Relatórios de frequência

### 4. Testes de Performance (`test_geracao_documentos.py`)

Validam performance de operações críticas:

```python
@pytest.mark.slow
def test_gerar_multiplos_boletins_performance():
    """Meta: 50 boletins em <30s"""

@pytest.mark.slow
def test_gerar_relatorio_grande_volume():
    """Meta: 1000+ registros em <10s"""
```

## 🔧 Fixtures Disponíveis

### Fixtures de Banco de Dados

```python
@pytest.fixture
def db_connection():
    """Conexão isolada para cada teste."""

@pytest.fixture
def db_transaction():
    """Transação com rollback automático."""

@pytest.fixture
def limpar_dados_teste():
    """Remove dados de teste após execução."""
```

### Fixtures de Dados

```python
@pytest.fixture
def dados_teste_aluno():
    """Dados válidos para criar aluno de teste."""

@pytest.fixture
def dados_teste_funcionario():
    """Dados válidos para criar funcionário de teste."""

@pytest.fixture
def aluno_real():
    """Obtém aluno real do banco para testes."""

@pytest.fixture
def turma_real():
    """Obtém turma real do banco para testes."""
```

### Fixtures de Mock

```python
@pytest.fixture
def mock_app():
    """Mock da classe Application para testes de UI."""
```

## 🎯 Marcadores de Teste

### `@pytest.mark.integration`
Marca testes de integração end-to-end.

```python
@pytest.mark.integration
def test_fluxo_completo():
    pass
```

### `@pytest.mark.database`
Marca testes que requerem acesso ao banco de dados.

```python
@pytest.mark.database
def test_consulta_banco():
    pass
```

### `@pytest.mark.slow`
Marca testes que demoram mais de 5 segundos.

```python
@pytest.mark.slow
def test_operacao_lenta():
    pass
```

### Executando por marcadores

```bash
# Apenas testes de integração
pytest -m integration

# Apenas testes de banco
pytest -m database

# Pular testes lentos
pytest -m "not slow"
```

## 📝 Convenções e Boas Práticas

### 1. Nomenclatura

```python
# ✅ Bom: Descritivo e específico
def test_cadastro_aluno_com_cpf_duplicado_deve_falhar():
    pass

# ❌ Ruim: Genérico
def test_aluno():
    pass
```

### 2. Estrutura AAA (Arrange-Act-Assert)

```python
def test_exemplo():
    # ARRANGE: Preparar dados de teste
    dados = criar_dados_teste()
    
    # ACT: Executar ação
    resultado = executar_acao(dados)
    
    # ASSERT: Verificar resultado
    assert resultado == esperado
```

### 3. Limpeza de Dados

```python
def test_com_limpeza(limpar_dados_teste):
    """Use fixture limpar_dados_teste para remover dados automaticamente."""
    aluno_id = criar_aluno_teste(...)
    # Teste...
    # Dados serão removidos automaticamente
```

### 4. Isolamento de Testes

```python
# ✅ Cada teste deve ser independente
def test_criar_aluno(db_transaction):
    """Usa transação que faz rollback automático."""
    aluno = criar_aluno(...)
    assert aluno.id > 0
    # Rollback automático ao final
```

### 5. Documentação

```python
def test_exemplo():
    """
    Breve descrição do que o teste valida.
    
    Cenário:
        Dado que tenho um aluno cadastrado
        Quando tento matriculá-lo em uma turma
        Então a matrícula deve ser criada com sucesso
    
    Validações:
        - ID da matrícula é gerado
        - Status inicial é 'Ativo'
        - Data de matrícula é registrada
    """
```

## 🐛 Debugging

### Ver output detalhado

```bash
# Modo verbose
pytest tests/integration/ -v

# Mostrar prints
pytest tests/integration/ -s

# Modo muito verbose
pytest tests/integration/ -vv
```

### Parar no primeiro erro

```bash
pytest tests/integration/ -x
```

### Executar último teste que falhou

```bash
pytest --lf
```

### Pular testes até encontrar falha

```bash
pytest --sw
```

## 📈 Cobertura de Testes

### Gerar relatório de cobertura

```bash
# Terminal
pytest tests/integration/ --cov=. --cov-report=term-missing

# HTML (abre no navegador)
pytest tests/integration/ --cov=. --cov-report=html
start htmlcov/index.html
```

### Meta de Cobertura

- **Atual**: ~15% de testes de integração
- **Meta Sprint 18**: 50%+ de cobertura end-to-end
- **Meta Sprint 22**: 80%+ de cobertura completa

## 🔍 Troubleshooting

### Problema: Testes falham com erro de conexão

**Solução**: Verificar configuração do banco de dados

```bash
# Verificar variáveis de ambiente
echo $env:DB_HOST
echo $env:DB_USER
echo $env:DB_NAME

# Testar conexão
python -c "from db.connection import get_connection; get_connection()"
```

### Problema: Dados de teste não são removidos

**Solução**: Usar fixture `limpar_dados_teste`

```python
def test_exemplo(limpar_dados_teste):
    # Dados serão removidos automaticamente
```

### Problema: Testes lentos demais

**Solução**: Usar marcador `@pytest.mark.slow` e pular quando necessário

```bash
pytest tests/integration/ --skip-slow
```

### Problema: Import errors

**Solução**: Verificar PYTHONPATH

```bash
# Windows PowerShell
$env:PYTHONPATH = "C:\gestao"
pytest tests/integration/
```

## 📚 Recursos Adicionais

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Guia de Testes de Integração](../docs/GUIA_TESTES_INTEGRACAO.md) *(a criar)*

## 🤝 Contribuindo

Ao adicionar novos testes de integração:

1. ✅ Seguir convenções de nomenclatura
2. ✅ Usar fixtures apropriadas
3. ✅ Documentar cenários de teste
4. ✅ Marcar testes lentos com `@pytest.mark.slow`
5. ✅ Garantir limpeza de dados de teste
6. ✅ Adicionar ao relatório de cobertura

---

**Última atualização**: 25/11/2025  
**Responsável**: Equipe de Desenvolvimento  
**Status**: ✅ Ativo
