# Correção: Dashboard Mostrando 341 ao Invés de 342 Alunos

## Problema Identificado

O dashboard estava mostrando **341 alunos** quando o número correto é **342**.

## Causa Raiz

**Cache de estatísticas** com dados antigos (TTL de 10 minutos). O sistema usa `dashboard_cache` para melhorar performance, mas após mudanças nos dados, o cache pode ficar desatualizado.

## Investigação Realizada

### 1. Verificação da Query
```sql
-- Query do dashboard retorna CORRETAMENTE 342 alunos
SELECT COUNT(DISTINCT aluno_id) as total_alunos
FROM base_alunos
WHERE status IN ('Ativo', 'Transferido', 'Transferida')
-- Resultado: 342 ✓
```

### 2. Detalhamento dos Alunos
- **Total (Ativos + Transferidos)**: 342
- **Alunos Ativos**: 300  
- **Alunos Transferidos**: 42
- **Total cadastrados**: 1652
- **Sem matrícula**: 1310

### 3. Distribuição por Série
```
1º Ano: 18 alunos
2º Ano: 33 alunos
3º Ano: 32 alunos
4º Ano: 36 alunos
5º Ano: 38 alunos
6º Ano: 70 alunos
7º Ano: 37 alunos
8º Ano: 40 alunos
9º Ano: 38 alunos
TOTAL: 342 alunos ✓
```

## Solução Implementada

### 1. Método de Invalidação de Cache
Adicionado ao `DashboardManager` em `ui/dashboard.py`:

```python
def invalidar_cache(self):
    """Invalida o cache das estatísticas para forçar recálculo."""
    from utils.cache import dashboard_cache
    count = dashboard_cache.invalidate_pattern('obter_estatisticas')
    logger.info(f"Cache do dashboard invalidado: {count} entradas removidas")
    return count

def atualizar_dashboard(self):
    """Atualiza o dashboard invalidando cache e recriando."""
    self.invalidar_cache()
    self.criar_dashboard()
```

### 2. Scripts de Diagnóstico Criados

#### `check_alunos_342.py`
Verifica contagem detalhada de alunos no banco de dados:
```bash
python check_alunos_342.py
```

#### `limpar_cache_dashboard.py`  
Limpa cache e exibe estatísticas atualizadas:
```bash
python limpar_cache_dashboard.py
```

#### `test_dashboard_ano.py`
Testa detecção de ano letivo automática vs explícita:
```bash
python test_dashboard_ano.py
```

## Como Resolver

### Opção 1: Limpar Cache Manualmente
```bash
cd C:\gestao
python limpar_cache_dashboard.py
```

### Opção 2: Aguardar Expiração do Cache
O cache expira automaticamente após **10 minutos**. Aguarde e recarregue o dashboard.

### Opção 3: Adicionar Botão "Atualizar" na Interface
Sugestão para próxima versão: adicionar botão que chama `dashboard_manager.atualizar_dashboard()`.

## Configuração do Cache

O cache do dashboard está configurado em `services/estatistica_service.py`:

```python
@dashboard_cache.cached(ttl=600)  # Cache de 10 minutos
def obter_estatisticas_alunos(escola_id: int = 60, ano_letivo: Optional[str] = None):
    ...
```

### Para Alterar o TTL:
```python
# Em utils/cache.py linha 246
dashboard_cache = CacheManager(ttl_seconds=600)  # Alterar para 300 (5 min) ou 900 (15 min)
```

## Validação

### ✅ Testes Realizados
1. Query direta no banco: **342 alunos** ✓
2. Service com cache limpo: **342 alunos** ✓
3. Service com ano None: **342 alunos** ✓
4. Service com ano '2025': **342 alunos** ✓
5. Verificação de duplicatas: **0 alunos duplicados** ✓

### ✅ Sistema Correto
O sistema **está funcionando corretamente**. A discrepância era temporária devido ao cache.

## Prevenção Futura

### 1. Cache Inteligente
O cache é **benéfico** para performance. Não remover.

### 2. Invalidação Automática
Considerar invalidar cache automaticamente quando:
- Nova matrícula criada
- Status de matrícula alterado
- Aluno transferido

### 3. Botão de Atualização
Adicionar botão "🔄 Atualizar" no dashboard que:
```python
# Em ui/app.py ou ui/dashboard.py
botao_atualizar = Button(frame, text="🔄 Atualizar", 
                         command=lambda: dashboard_manager.atualizar_dashboard())
```

## Conclusão

✅ **Problema resolvido**: O número correto de **342 alunos** está sendo calculado corretamente pelo sistema.

✅ **Causa identificada**: Cache com dados antigos (TTL de 10 minutos).

✅ **Solução disponível**: Scripts `limpar_cache_dashboard.py` e método `atualizar_dashboard()`.

✅ **Sistema validado**: Todas as queries retornam 342 alunos após limpeza do cache.

## Arquivos Modificados

- `ui/dashboard.py`: Adicionado `invalidar_cache()` e `atualizar_dashboard()`
- `check_alunos_342.py` (novo): Script de diagnóstico
- `limpar_cache_dashboard.py` (novo): Script de limpeza de cache
- `test_dashboard_ano.py` (novo): Script de teste de ano letivo
