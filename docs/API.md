# 🔌 Documentação de API

## Services API

### Aluno Service

#### Funções Principais

```python
from services.aluno_service import (
    criar_aluno,
    atualizar_aluno,
    buscar_aluno_por_id,
    listar_alunos,
    excluir_aluno
)

# Criar aluno
def criar_aluno(data: dict) -> Tuple[bool, str]:
    """
    Cria um novo aluno no sistema.
    
    Args:
        data: Dicionário com dados do aluno
            - nome: str (obrigatório, 3-100 caracteres)
            - cpf: str (opcional, 11 dígitos)
            - data_nascimento: date (obrigatório)
            - mae: str (obrigatório)
            - pai: str (opcional)
            - escola_id: int (obrigatório)
            - responsavel_nome: str (obrigatório)
            - responsavel_cpf: str (obrigatório)
            - responsavel_telefone: str (obrigatório)
    
    Returns:
        Tupla (sucesso: bool, mensagem: str)
    
    Raises:
        ValidationError: Se dados inválidos
        DatabaseError: Se erro no banco de dados
    
    Example:
        >>> data = {
        ...     'nome': 'João Silva',
        ...     'data_nascimento': '2010-05-15',
        ...     'mae': 'Maria Silva',
        ...     'escola_id': 60,
        ...     'responsavel_nome': 'Maria Silva',
        ...     'responsavel_cpf': '12345678901',
        ...     'responsavel_telefone': '11987654321'
        ... }
        >>> success, msg = criar_aluno(data)
        >>> print(success, msg)
        True "Aluno criado com sucesso"
    """

# Atualizar aluno
def atualizar_aluno(aluno_id: int, data: dict) -> Tuple[bool, str]:
    """
    Atualiza dados de um aluno existente.
    
    Args:
        aluno_id: ID do aluno
        data: Dicionário com campos a atualizar (todos opcionais)
    
    Returns:
        Tupla (sucesso: bool, mensagem: str)
    
    Example:
        >>> success, msg = atualizar_aluno(1, {'nome': 'João Pedro Silva'})
        >>> print(success, msg)
        True "Aluno atualizado com sucesso"
    """

# Buscar por ID
def buscar_aluno_por_id(aluno_id: int) -> Optional[Dict[str, Any]]:
    """
    Busca aluno por ID.
    
    Args:
        aluno_id: ID do aluno
    
    Returns:
        Dicionário com dados do aluno ou None se não encontrado
    
    Example:
        >>> aluno = buscar_aluno_por_id(1)
        >>> print(aluno['nome'])
        "João Silva"
    """

# Listar alunos
def listar_alunos(
    escola_id: int,
    filtros: Optional[Dict[str, Any]] = None,
    limite: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Lista alunos com filtros opcionais.
    
    Args:
        escola_id: ID da escola
        filtros: Dicionário com filtros:
            - nome: str (busca parcial)
            - turma_id: int
            - serie: str
            - status: str ('Ativo', 'Inativo', 'Transferido')
        limite: Máximo de registros a retornar
        offset: Offset para paginação
    
    Returns:
        Lista de dicionários com dados dos alunos
    
    Example:
        >>> alunos = listar_alunos(
        ...     escola_id=60,
        ...     filtros={'status': 'Ativo', 'serie': '1º Ano'},
        ...     limite=50
        ... )
        >>> print(len(alunos))
        45
    """

# Excluir aluno (soft delete)
def excluir_aluno(aluno_id: int) -> Tuple[bool, str]:
    """
    Exclui aluno logicamente (soft delete).
    
    Args:
        aluno_id: ID do aluno
    
    Returns:
        Tupla (sucesso: bool, mensagem: str)
    
    Example:
        >>> success, msg = excluir_aluno(1)
        >>> print(success, msg)
        True "Aluno excluído com sucesso"
    """
```

### Estatística Service

```python
from services.estatistica_service import (
    obter_estatisticas_alunos,
    obter_estatisticas_turmas,
    obter_estatisticas_completas
)

# Estatísticas de alunos (cached 600s)
def obter_estatisticas_alunos(escola_id: int = 60) -> Dict[str, Any]:
    """
    Retorna estatísticas de alunos com cache de 10 minutos.
    
    Args:
        escola_id: ID da escola (default: 60)
    
    Returns:
        Dicionário com estatísticas:
        {
            'total_alunos': int,
            'alunos_ativos': int,
            'sem_matricula': int,
            'por_turma': List[Dict],
            'por_turno': List[Dict],
            'por_serie': List[Dict]
        }
    
    Example:
        >>> stats = obter_estatisticas_alunos()
        >>> print(stats['total_alunos'])
        450
        >>> print(stats['por_turno'])
        [{'turno': 'Manhã', 'total': 280}, {'turno': 'Tarde', 'total': 170}]
    """

# Estatísticas completas
def obter_estatisticas_completas(escola_id: int = 60) -> Dict[str, Any]:
    """
    Retorna estatísticas completas do sistema.
    
    Returns:
        Dicionário com todas as estatísticas:
        {
            'alunos': Dict,
            'turmas': Dict,
            'funcionarios': Dict,
            'timestamp': datetime
        }
    """
```

### Backup Service

```python
from services.backup_service import (
    fazer_backup,
    restaurar_backup,
    agendar_backup_automatico
)

# Fazer backup
def fazer_backup(filepath: str) -> bool:
    """
    Cria backup do banco de dados.
    
    Args:
        filepath: Caminho onde salvar o backup
    
    Returns:
        True se sucesso, False se falha
    
    Example:
        >>> success = fazer_backup('backup_2025_11_21.sql')
        >>> print(success)
        True
    """

# Restaurar backup
def restaurar_backup(filepath: str) -> bool:
    """
    Restaura banco de dados de um backup.
    
    Args:
        filepath: Caminho do arquivo de backup
    
    Returns:
        True se sucesso, False se falha
    
    Example:
        >>> success = restaurar_backup('backup_2025_11_21.sql')
        >>> print(success)
        True
    """

# Agendar backup automático
def agendar_backup_automatico(
    horarios: List[int] = [14, 17],
    local_path: str = 'backup_redeescola.sql'
) -> None:
    """
    Agenda backups automáticos em horários específicos.
    
    Args:
        horarios: Lista de horas (0-23) para executar backup
        local_path: Caminho para salvar backups
    
    Example:
        >>> agendar_backup_automatico(horarios=[14, 17])
        # Backup será executado às 14:00 e 17:00
    """
```

### Report Service

```python
from services.report_service import (
    gerar_historico_escolar,
    gerar_lista_notas,
    gerar_declaracao_comparecimento
)

# Gerar histórico escolar
def gerar_historico_escolar(aluno_id: int, output_path: Optional[str] = None) -> str:
    """
    Gera PDF com histórico escolar completo.
    
    Args:
        aluno_id: ID do aluno
        output_path: Caminho para salvar PDF (opcional)
    
    Returns:
        Caminho do PDF gerado
    
    Example:
        >>> pdf_path = gerar_historico_escolar(1)
        >>> print(pdf_path)
        "/tmp/historico_joao_silva.pdf"
    """

# Gerar lista de notas
def gerar_lista_notas(
    turma_id: int,
    periodo: str,
    output_path: Optional[str] = None
) -> str:
    """
    Gera PDF com lista de notas da turma.
    
    Args:
        turma_id: ID da turma
        periodo: '1º Bimestre', '2º Bimestre', etc.
        output_path: Caminho para salvar PDF (opcional)
    
    Returns:
        Caminho do PDF gerado
    
    Example:
        >>> pdf_path = gerar_lista_notas(5, '1º Bimestre')
        >>> print(pdf_path)
        "/tmp/notas_turma_5_1bim.pdf"
    """
```

## Models API (Pydantic)

### Aluno Models

```python
from models.aluno import AlunoCreate, AlunoUpdate, AlunoRead
from pydantic import ValidationError

# Criar aluno
try:
    aluno = AlunoCreate(
        nome='João Silva',
        cpf='12345678901',
        data_nascimento='2010-05-15',
        mae='Maria Silva',
        escola_id=60,
        responsavel_nome='Maria Silva',
        responsavel_cpf='12345678901',
        responsavel_telefone='11987654321'
    )
    print(aluno.model_dump())
except ValidationError as e:
    print(e.errors())

# Atualizar aluno (campos opcionais)
aluno_update = AlunoUpdate(
    nome='João Pedro Silva',
    cpf='98765432101'
)

# Ler aluno (com timestamps)
aluno_read = AlunoRead(
    id=1,
    nome='João Silva',
    cpf='12345678901',
    data_nascimento='2010-05-15',
    created_at='2025-01-01T10:00:00',
    updated_at='2025-11-21T14:30:00'
)
```

### Funcionario Models

```python
from models.funcionario import FuncionarioCreate, FuncionarioUpdate, FuncionarioRead

# Criar funcionário
funcionario = FuncionarioCreate(
    nome='Maria Santos',
    cpf='12345678901',
    cargo='Professor',
    email='maria@escola.com',
    telefone='11987654321',
    escola_id=60
)

# Validações automáticas:
# - CPF válido (algoritmo completo)
# - Email formato válido
# - Telefone formato válido
# - Nome mínimo 3 caracteres
```

### Turma Models

```python
from models.turma import TurmaCreate, TurmaUpdate, TurmaRead

# Criar turma
turma = TurmaCreate(
    nome_turma='1º Ano A',
    serie='1º Ano',
    turno_id=1,
    ano_letivo_id=2025,
    escola_id=60
)
```

## Cache API

```python
from utils.cache import CacheManager, cache, dashboard_cache

# Criar cache manager
meu_cache = CacheManager(ttl_seconds=300)  # 5 minutos

# Operações básicas
meu_cache.set('chave', {'data': 'valor'})
valor = meu_cache.get('chave')
meu_cache.invalidate('chave')

# Invalidar por padrão
meu_cache.set('user:1', {'name': 'João'})
meu_cache.set('user:2', {'name': 'Maria'})
meu_cache.invalidate_pattern('user:*')  # Invalida todos os usuários

# Usar decorator
@meu_cache.cached()
def funcao_cara():
    # Processamento pesado
    return resultado

# Estatísticas
stats = meu_cache.get_stats()
print(stats['hits'], stats['misses'], stats['hit_rate'])
```

## Feature Flags API

```python
from utils.feature_flags import get_feature_flags, is_feature_enabled

# Obter instância global
features = get_feature_flags()

# Verificar se feature está habilitada
if is_feature_enabled('novo_dashboard'):
    mostrar_dashboard_v2()
else:
    mostrar_dashboard_v1()

# Habilitar/desabilitar
features.enable('modo_debug')
features.disable('integracao_drive')

# Obter todas as flags
todas = features.get_all_flags()
print(todas)

# Obter flags por categoria
performance_flags = features.get_by_category('performance')
ui_flags = features.get_by_category('ui')

# Registrar callback
def on_flag_change(flag_name: str, enabled: bool):
    print(f"Flag '{flag_name}' agora está {'habilitada' if enabled else 'desabilitada'}")

features.register_callback(on_flag_change)

# Usar decorator
@features.feature('nova_funcionalidade', default=False)
def funcionalidade_experimental():
    # Código só executa se flag estiver habilitada
    pass
```

## Logging API

```python
from config_logs import setup_logging, log_with_context

# Configurar logging
logger = setup_logging(
    app_name='gestao_escolar',
    rotation_type='both',      # 'size', 'time', 'both'
    formatter_type='json'      # 'json', 'key-value', 'simple'
)

# Usar logger
logger.debug("Detalhes de desenvolvimento")
logger.info("Operação normal")
logger.warning("Situação anormal")
logger.error("Erro recuperável")
logger.critical("Erro crítico")

# Log com contexto adicional
log_with_context(
    logger,
    'info',
    'Usuário fez login',
    user_id=123,
    ip_address='192.168.1.100',
    session_id='abc123'
)

# Resultado em JSON:
# {
#     "timestamp": "2025-11-21T14:30:00",
#     "level": "INFO",
#     "message": "Usuário fez login",
#     "user_id": 123,
#     "ip_address": "192.168.1.100",
#     "session_id": "abc123"
# }
```

## Database API

```python
from db.connection import get_cursor
from conexao import inicializar_pool, fechar_pool

# Inicializar pool (uma vez no início)
inicializar_pool()

# Usar cursor com context manager
with get_cursor() as cursor:
    cursor.execute("SELECT * FROM alunos WHERE escola_id = %s", (60,))
    alunos = cursor.fetchall()

# Cursor com auto-commit
with get_cursor(autocommit=True) as cursor:
    cursor.execute(
        "INSERT INTO alunos (nome, escola_id) VALUES (%s, %s)",
        ('João Silva', 60)
    )
    # Commit automático ao final

# Fechar pool (ao encerrar aplicação)
fechar_pool()
```

## UI Components API

### Table Component

```python
from ui.table import TableManager

# Criar tabela
table = TableManager(
    parent=frame,
    columns=['ID', 'Nome', 'Série', 'Status'],
    column_widths=[50, 200, 100, 100],
    on_select=callback_selecao,
    on_double_click=callback_duplo_clique
)

# Adicionar dados
table.insert_row([1, 'João Silva', '1º Ano', 'Ativo'])
table.insert_rows([
    [2, 'Maria Santos', '2º Ano', 'Ativo'],
    [3, 'Pedro Oliveira', '1º Ano', 'Inativo']
])

# Limpar tabela
table.clear()

# Obter seleção
item_id = table.get_selected_id()

# Buscar
table.search('João')
```

### Button Factory

```python
from ui.button_factory import ButtonFactory

# Criar factory
factory = ButtonFactory(app)

# Criar botões
btn_novo = factory.criar_botao_acao(
    parent=frame,
    texto='Novo Aluno',
    comando=callback_novo,
    cor='primary'
)

btn_editar = factory.criar_botao_acao(
    parent=frame,
    texto='Editar',
    comando=callback_editar,
    cor='secondary'
)

btn_excluir = factory.criar_botao_acao(
    parent=frame,
    texto='Excluir',
    comando=callback_excluir,
    cor='danger'
)
```

### Colors

```python
from ui.colors import get_color, COLORS

# Obter cor por nome
cor_primaria = get_color('primary')
cor_secundaria = get_color('secondary')
cor_sucesso = get_color('success')
cor_perigo = get_color('danger')

# Usar diretamente
frame.configure(bg=COLORS.background)
label.configure(fg=COLORS.text_primary)
```

## Exemplos Completos

### Exemplo 1: Criar e Listar Alunos

```python
from services.aluno_service import criar_aluno, listar_alunos
from models.aluno import AlunoCreate

# Criar aluno com validação Pydantic
data = {
    'nome': 'João Silva',
    'data_nascimento': '2010-05-15',
    'mae': 'Maria Silva',
    'escola_id': 60,
    'responsavel_nome': 'Maria Silva',
    'responsavel_cpf': '12345678901',
    'responsavel_telefone': '11987654321'
}

try:
    # Validar dados
    aluno = AlunoCreate(**data)
    
    # Criar no banco
    success, msg = criar_aluno(aluno.model_dump())
    
    if success:
        print(f"✅ {msg}")
        
        # Listar todos os alunos ativos
        alunos = listar_alunos(
            escola_id=60,
            filtros={'status': 'Ativo'}
        )
        
        for aluno in alunos:
            print(f"- {aluno['nome']} ({aluno['serie']})")
    else:
        print(f"❌ {msg}")
        
except ValidationError as e:
    print("Dados inválidos:")
    for error in e.errors():
        print(f"- {error['loc'][0]}: {error['msg']}")
```

### Exemplo 2: Dashboard com Cache

```python
from services.estatistica_service import obter_estatisticas_alunos
from utils.cache import dashboard_cache
import time

# Primeira chamada (sem cache)
start = time.perf_counter()
stats = obter_estatisticas_alunos()
tempo_sem_cache = time.perf_counter() - start
print(f"Sem cache: {tempo_sem_cache*1000:.2f}ms")

# Segunda chamada (com cache)
start = time.perf_counter()
stats = obter_estatisticas_alunos()
tempo_com_cache = time.perf_counter() - start
print(f"Com cache: {tempo_com_cache*1000:.2f}ms")

# Exibir estatísticas
print(f"\nTotal de alunos: {stats['total_alunos']}")
print(f"Alunos ativos: {stats['alunos_ativos']}")
print("\nPor turno:")
for turno in stats['por_turno']:
    print(f"- {turno['turno']}: {turno['total']} alunos")
```

### Exemplo 3: Feature Flags

```python
from utils.feature_flags import get_feature_flags

features = get_feature_flags()

# Habilitar feature temporariamente
if not features.is_enabled('modo_debug'):
    features.enable('modo_debug')
    print("Debug mode ativado")

# Executar código condicional
if features.is_enabled('novo_dashboard'):
    from ui.dashboard_v2 import mostrar_dashboard
    mostrar_dashboard()
else:
    from ui.dashboard import mostrar_dashboard_legado
    mostrar_dashboard_legado()

# Desabilitar ao terminar
features.disable('modo_debug')
```

---

**Última atualização**: 21 de novembro de 2025
