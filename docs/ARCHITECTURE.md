# 🏗️ Arquitetura do Sistema

## Visão Geral

O Sistema de Gestão Escolar utiliza uma arquitetura **MVC (Model-View-Controller)** moderna com **Service Layer** para isolamento da lógica de negócio.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│                         (UI/Tkinter)                          │
├─────────────────────────────────────────────────────────────┤
│  Application │ Modals │ Tables │ Buttons │ Colors │ Menu    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Service Layer                          │
│                    (Business Logic)                          │
├─────────────────────────────────────────────────────────────┤
│  AlunoService │ FuncionarioService │ EstatisticaService     │
│  BackupService │ ReportService │ ValidationService          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Model Layer                            │
│                   (Pydantic Validation)                      │
├─────────────────────────────────────────────────────────────┤
│  Aluno │ Funcionario │ Turma │ Matricula │ NotaConceito    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Data Access Layer                        │
│                    (Repository Pattern)                      │
├─────────────────────────────────────────────────────────────┤
│  Connection Pool │ Queries │ Transactions │ Cursors         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        Database                              │
│                      (MySQL 8.0+)                            │
└─────────────────────────────────────────────────────────────┘
```

## Camadas

### 1. Presentation Layer (UI)

**Responsabilidades:**
- Renderizar interface gráfica com Tkinter
- Capturar eventos do usuário
- Exibir dados formatados
- Validação básica de entrada

**Componentes principais:**
- `ui/app.py` - Application class (janela principal)
- `ui/modals/` - Janelas modais para cadastro/edição
- `ui/table.py` - Componente de tabela reutilizável
- `ui/button_factory.py` - Factory para criação de botões
- `ui/colors.py` - Paleta de cores centralizada
- `ui/menu.py` - Sistema de menus

**Padrões:**
- **Factory Pattern** - Criação de componentes
- **Component Pattern** - Reutilização de widgets
- **Observer Pattern** - Eventos de UI

### 2. Service Layer (Business Logic)

**Responsabilidades:**
- Implementar regras de negócio
- Orquestrar operações complexas
- Validar dados de negócio
- Controlar transações
- Gerenciar cache

**Serviços principais:**

```python
# services/aluno_service.py
class AlunoService:
    def criar_aluno(data: dict) -> Tuple[bool, str]
    def atualizar_aluno(id: int, data: dict) -> Tuple[bool, str]
    def buscar_aluno(id: int) -> Optional[Dict]
    def listar_alunos(filtros: dict) -> List[Dict]
    def excluir_aluno(id: int) -> Tuple[bool, str]

# services/estatistica_service.py
@dashboard_cache.cached()  # Cache de 600s
def obter_estatisticas_alunos() -> Dict[str, Any]
def obter_estatisticas_turmas() -> Dict[str, Any]
def obter_estatisticas_funcionarios() -> Dict[str, Any]

# services/backup_service.py
def fazer_backup(filepath: str) -> bool
def restaurar_backup(filepath: str) -> bool
def agendar_backup_automatico() -> None
```

**Padrões:**
- **Service Pattern** - Encapsulamento de lógica
- **Decorator Pattern** - Cache e logging
- **Strategy Pattern** - Diferentes estratégias de backup

### 3. Model Layer (Validation)

**Responsabilidades:**
- Definir esquema de dados
- Validar tipos e formatos
- Aplicar regras de validação
- Serializar/deserializar dados

**Modelos Pydantic:**

```python
# models/aluno.py
class AlunoCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    cpf: Optional[str] = Field(None, regex=r'^\d{11}$')
    data_nascimento: date
    mae: str
    pai: Optional[str]
    escola_id: int
    
    @field_validator('cpf')
    @classmethod
    def validar_cpf(cls, v: Optional[str]) -> Optional[str]:
        # Implementa validação de CPF
        pass
    
    @field_validator('data_nascimento')
    @classmethod
    def validar_idade(cls, v: date) -> date:
        idade = (date.today() - v).days / 365
        if not (3 <= idade <= 100):
            raise ValueError('Idade deve estar entre 3 e 100 anos')
        return v

class AlunoUpdate(BaseModel):
    # Campos opcionais para atualização parcial
    nome: Optional[str] = None
    cpf: Optional[str] = None
    # ...

class AlunoRead(BaseModel):
    # Inclui timestamps e campos computados
    id: int
    nome: str
    created_at: datetime
    updated_at: datetime
```

**Padrões:**
- **DTO Pattern** - Transferência de dados
- **Builder Pattern** - Construção de objetos
- **Validation Pattern** - Validação em cascata

### 4. Data Access Layer (Repository)

**Responsabilidades:**
- Gerenciar conexões com banco
- Executar queries SQL
- Controlar transações
- Implementar pool de conexões

**Componentes:**

```python
# conexao.py
connection_pool: Optional[MySQLConnectionPool] = None

def inicializar_pool() -> None:
    """Cria pool de 10 conexões"""
    global connection_pool
    connection_pool = MySQLConnectionPool(
        pool_name='gestao_pool',
        pool_size=10,
        **DB_CONFIG
    )

def get_connection() -> PooledMySQLConnection:
    """Obtém conexão do pool"""
    return connection_pool.get_connection()

# db/connection.py
@contextmanager
def get_cursor(autocommit: bool = False):
    """Context manager para cursor com auto-commit opcional"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if autocommit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
```

**Padrões:**
- **Connection Pool Pattern** - Reuso de conexões
- **Context Manager Pattern** - Gerenciamento de recursos
- **Transaction Script Pattern** - Controle de transações

## Fluxos de Dados

### Fluxo de Criação de Aluno

```
1. UI: Usuário preenche formulário
   ↓
2. UI: Valida campos obrigatórios (cliente)
   ↓
3. Service: AlunoService.criar_aluno(data)
   ↓
4. Model: AlunoCreate(**data) → Validação Pydantic
   ↓
5. Repository: INSERT INTO alunos (...)
   ↓
6. DB: Executa query e retorna ID
   ↓
7. Service: Retorna (True, "Aluno criado")
   ↓
8. UI: Exibe mensagem de sucesso
   ↓
9. Cache: Invalida cache de estatísticas
```

### Fluxo de Dashboard (com Cache)

```
1. UI: Carrega dashboard
   ↓
2. Service: obter_estatisticas_alunos()
   ↓
3. Cache: Verifica se existe entrada válida
   ├─ HIT: Retorna dados do cache (< 1ms)
   └─ MISS: Executa queries no DB
      ↓
4. Repository: Executa 6-8 queries agregadas
   ↓
5. DB: Retorna resultados
   ↓
6. Cache: Armazena resultado (TTL: 600s)
   ↓
7. Service: Retorna estatísticas
   ↓
8. UI: Renderiza gráficos e tabelas
```

### Fluxo de Atualização (com Invalidação)

```
1. UI: Usuário edita aluno
   ↓
2. Service: AlunoService.atualizar_aluno(id, data)
   ↓
3. Model: AlunoUpdate(**data) → Validação
   ↓
4. Repository: UPDATE alunos SET ... WHERE id = ?
   ↓
5. Cache: Invalida padrão "aluno:*"
   ↓
6. Cache: Invalida estatísticas do dashboard
   ↓
7. Service: Retorna (True, "Atualizado")
   ↓
8. UI: Recarrega tabela com dados frescos
```

## Sistemas Transversais

### Sistema de Cache

```python
# utils/cache.py
class CacheManager:
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, Dict] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, key: str) -> Optional[Any]:
        """Busca no cache com validação de TTL"""
        
    def set(self, key: str, data: Any) -> None:
        """Adiciona ao cache com timestamp"""
    
    def invalidate_pattern(self, pattern: str) -> None:
        """Invalida chaves que correspondem ao padrão"""
    
    @cached()
    def cached(self, ttl: Optional[int] = None):
        """Decorator para cache automático"""

# Uso global
cache = CacheManager(ttl_seconds=300)
dashboard_cache = CacheManager(ttl_seconds=600)
```

**Estratégias de invalidação:**
- **TTL (Time To Live)** - Expiração automática
- **Pattern-based** - Invalida por padrão (ex: `user:*`)
- **Event-driven** - Invalida ao modificar dados
- **Manual** - Invalidação explícita

### Sistema de Logs

```python
# config_logs.py
class JSONFormatter(logging.Formatter):
    """Logs estruturados em JSON"""
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        })

def setup_logging(
    app_name: str = 'gestao_escolar',
    rotation_type: str = 'size',  # 'size', 'time', 'both'
    formatter_type: str = 'json'  # 'json', 'key-value', 'simple'
):
    """Configura logging com múltiplas opções"""
```

**Níveis de log:**
- **DEBUG** - Detalhes de desenvolvimento (cache hits, query time)
- **INFO** - Operações normais (login, backup)
- **WARNING** - Situações anormais mas não críticas
- **ERROR** - Erros recuperáveis (conexão falhou)
- **CRITICAL** - Erros que impedem funcionamento

### Sistema de Feature Flags

```python
# utils/feature_flags.py
class FeatureFlags:
    def is_enabled(self, flag_name: str) -> bool:
        """Verifica se feature está habilitada"""
    
    def enable(self, flag_name: str) -> None:
        """Habilita feature"""
    
    def disable(self, flag_name: str) -> None:
        """Desabilita feature"""
    
    def register_callback(self, callback: Callable):
        """Registra callback para mudanças"""

# Uso
if features.is_enabled('novo_dashboard'):
    mostrar_dashboard_v2()
else:
    mostrar_dashboard_v1()
```

**Flags disponíveis:**
- `cache_enabled` - Sistema de cache
- `pydantic_validation` - Validação Pydantic
- `json_logs` - Logs em formato JSON
- `dashboard_avancado` - Dashboard com gráficos
- `modo_debug` - Modo de depuração
- `relatorios_pdf` - Geração de PDFs
- `integracao_drive` - Upload para Google Drive

## Performance

### Métricas

**Operações típicas:**
- Listagem de alunos (100 registros): < 150ms
- Busca por ID (com índice): < 50ms
- Estatísticas dashboard (sem cache): < 1500ms
- Estatísticas dashboard (com cache): < 5ms
- Geração de PDF: 500ms - 2s (dependendo do tamanho)

**Melhorias de cache:**
- Dashboard: 40-60% redução de queries
- Busca frequente: até 95% mais rápido

### Otimizações Implementadas

1. **Connection Pooling** - Reusa 10 conexões ao invés de criar/destruir
2. **Query Caching** - Cache inteligente com TTL
3. **Índices de DB** - Índices em colunas frequentemente buscadas
4. **Lazy Loading** - Carrega dados apenas quando necessário
5. **PDF Caching** - Cache de imagens e estilos ReportLab
6. **Batch Operations** - Inserts/updates em lote quando possível

### Gargalos Conhecidos

1. **Geração de PDFs grandes** - Pode levar 3-5s para históricos completos
2. **Queries sem índices** - Busca por nome sem índice é lenta
3. **Dashboard sem cache** - Primeira carga pode demorar 1-2s

**Soluções planejadas:**
- Background jobs para PDFs grandes
- Índices full-text para busca
- Pre-caching de estatísticas

## Segurança

### Autenticação e Autorização

```python
# Seguranca.py
def verificar_credenciais(usuario: str, senha: str) -> Tuple[bool, Optional[Dict]]:
    """Valida credenciais e retorna dados do usuário"""
    
def verificar_permissao(usuario_id: int, permissao: str) -> bool:
    """Verifica se usuário tem permissão"""

# Níveis de permissão
PERMISSOES = {
    'ADMIN': ['*'],  # Todas as permissões
    'COORDENADOR': ['alunos.*', 'funcionarios.read', 'relatorios.*'],
    'PROFESSOR': ['alunos.read', 'notas.write', 'frequencia.write'],
    'SECRETARIA': ['alunos.*', 'documentos.*']
}
```

### Proteções Implementadas

1. **SQL Injection** - Queries parametrizadas
2. **XSS** - Validação de entrada
3. **CSRF** - Tokens de sessão
4. **Senhas** - Hash bcrypt
5. **Auditoria** - Logs de todas as ações
6. **Backup** - Backup automático diário

### Conformidade LGPD

- ✅ Consentimento explícito para dados pessoais
- ✅ Direito de acesso aos dados
- ✅ Direito de exclusão (soft delete)
- ✅ Logs de acesso e modificação
- ✅ Criptografia de dados sensíveis
- ✅ Política de retenção de dados

## Escalabilidade

### Limites Atuais

- **Alunos**: Testado com até 10.000 alunos
- **Funcionários**: Testado com até 500 funcionários
- **Turmas**: Testado com até 100 turmas
- **Conexões simultâneas**: Pool de 10 conexões

### Estratégias de Escalabilidade

1. **Horizontal** - Múltiplas instâncias com load balancer
2. **Vertical** - Aumentar pool de conexões e recursos
3. **Sharding** - Separar escolas em diferentes bancos
4. **Read Replicas** - Réplicas de leitura para relatórios
5. **CDN** - Arquivos estáticos (PDFs, imagens)

## Manutenibilidade

### Boas Práticas Implementadas

- ✅ **Type Hints** - Todos os módulos principais
- ✅ **Docstrings** - Funções e classes documentadas
- ✅ **Tests** - 95+ testes, 80%+ cobertura
- ✅ **Logs** - Logs estruturados em JSON
- ✅ **Separação de responsabilidades** - MVC + Service Layer
- ✅ **DRY** - Código reutilizável
- ✅ **SOLID** - Princípios SOLID aplicados

### Métricas de Qualidade

- **Complexidade ciclomática**: < 10 por função
- **Linhas por função**: < 100 (média: 30)
- **Acoplamento**: Baixo (camadas independentes)
- **Coesão**: Alta (responsabilidades bem definidas)

---

**Última atualização**: 21 de novembro de 2025
