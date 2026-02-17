# Feature Flags do Sistema

**Sistema de Gestão Escolar - Controle de Funcionalidades via Feature Flags**

## Visão Geral

O sistema utiliza **Feature Flags** para habilitar/desabilitar funcionalidades dinamicamente sem alterar código. Isso é útil para:

- 🧪 Testes A/B
- 🚀 Rollout gradual de novas features
- 🔧 Desabilitar features com problemas
- 🏗️ Desenvolvimento em produção (dark launch)
- 🎛️ Configuração específica por ambiente

**Módulo:** `src/core/feature_flags.py`

---

## Flags Disponíveis

### Performance

| Flag | Padrão | Descrição |
|------|:------:|-----------|
| `cache_enabled` | ✅ ON | Habilita cache de estatísticas e queries (dashboard, movimento mensal) |

**Impacto quando desligado:**
- Dashboard será recalculado a cada acesso (mais lento)
- Queries repetidas não serão cacheadas
- Útil para depuração de bugs relacionados a cache stale

**Onde é usado:**
- `src/services/estatistica_service.py` → decorador `@dashboard_cache.cached(ttl=600)`

---

### Validação

| Flag | Padrão | Descrição |
|------|:------:|-----------|
| `pydantic_validation` | ✅ ON | Habilita validação Pydantic em services (aluno_service, etc) |

**Impacto quando desligado:**
- Dados não serão validados antes de serem salvos
- ⚠️ **Risco de dados inconsistentes no banco!**
- Pode ser desligado temporariamente para debug ou importação de dados legados

**Onde é usado:**
- `src/services/aluno_service.py` → validação de CPF, email, data de nascimento
- `src/models/aluno.py`, `src/models/funcionario.py`, `src/models/matricula.py`

---

### Logging

| Flag | Padrão | Descrição |
|------|:------:|-----------|
| `json_logs` | ❌ OFF | Usa formato JSON estruturado para logs (ao invés de texto tradicional) |

**Quando habilitado:**
```json
{
  "timestamp": "2026-02-17T14:30:00",
  "level": "INFO",
  "module": "aluno_service",
  "message": "Aluno cadastrado",
  "extra": {
    "aluno_id": 123,
    "user": "admin"
  }
}
```

**Quando desabilitado (padrão):**
```
2026-02-17 14:30:00 INFO aluno_service - Aluno cadastrado
```

**Onde é usado:**
- `src/core/config_logs.py` → `setup_logging()`

---

### Backup

| Flag | Padrão | Descrição |
|------|:------:|-----------|
| `backup_automatico` | ✅ ON | Habilita backup automático do banco MySQL |
| `integracao_drive` | ❌ OFF | Habilita upload de backup para Google Drive |

**`backup_automatico` quando habilitado:**
- Backup SQL criado automaticamente a cada 24h
- Armazenado localmente em `backups/`
- Configurado no `.env`: `BACKUP_ENABLED=True`

**`integracao_drive` quando habilitado:**
- Requer credenciais OAuth2 do Google Drive
- Envia backup para pasta configurada no Drive
- ⚠️ **Cuidado**: expõe dados sensíveis ao Google Cloud

**Onde é usado:**
- `src/core/seguranca.py` → `fazer_backup()`, `fazer_backup_drive()`

---

### UI/Interface

| Flag | Padrão | Descrição |
|------|:------:|-----------|
| `dashboard_avancado` | ✅ ON | Mostra dashboard com estatísticas avançadas (gráficos, KPIs) |

**Quando habilitado (padrão):**
- Dashboard exibe gráfico de pizza (distribuição por série)
- Gráfico de barras empilhadas (movimento mensal)
- KPIs resumidos

**Quando desabilitado:**
- Dashboard simplificado (apenas números)
- Útil para dispositivos com baixa performance gráfica

**Onde é usado:**
- `src/ui/dashboard.py` → linha ~300-550

---

### Debugging

| Flag | Padrão | Descrição |
|------|:------:|-----------|
| `modo_debug` | ❌ OFF | Ativa logs de debug e informações extras na UI |

**Quando habilitado:**
- Nível de log alterado para `DEBUG` (mais verboso)
- Mostra queries SQL nos logs
- Exibe stack traces completas em erros
- ⚠️ **Não usar em produção!** (vazamento de informações sensíveis)

**Onde é usado:**
- `src/core/config_logs.py` → `setup_logging()`
- `db/connection.py` → logging de queries

---

### Features

| Flag | Padrão | Descrição |
|------|:------:|-----------|
| `relatorios_pdf` | ✅ ON | Permite geração de relatórios em PDF (ReportLab) |

**Quando desligado:**
- Botões de geração de PDF ficam ocultos
- Atalho para desabilitar temporariamente se houver problemas com ReportLab
- Útil para debug de relatórios

**Onde é usado:**
- `src/ui/button_factory.py` → menu "Listas"
- `src/relatorios/` → todos os módulos de geração de PDF

---

## Como Usar Feature Flags

### 1. No Código Python

```python
from src.core.feature_flags import FeatureFlags

flags = FeatureFlags()

# Verificar se feature está habilitada
if flags.is_enabled('cache_enabled'):
    # Usar cache
    resultado = cache.get(chave)
else:
    # Buscar direto do banco
    resultado = consultar_banco()

# Verificar com valor padrão
if flags.is_enabled('nova_feature', default=False):
    # Feature experimental
    pass
```

### 2. Via Variável de Ambiente

Variáveis de ambiente têm **prioridade máxima** sobre o arquivo de configuração:

```bash
# .env ou configuração do sistema
FEATURE_CACHE_ENABLED=1
FEATURE_MODO_DEBUG=0
FEATURE_JSON_LOGS=true
```

**Valores aceitos:**
- `1`, `true`, `yes`, `on` → Habilita
- `0`, `false`, `no`, `off` → Desabilita

### 3. Via Arquivo de Configuração

O arquivo `feature_flags.json` na raiz do projeto:

```json
{
  "flags": {
    "cache_enabled": {
      "enabled": true,
      "description": "Habilita cache de estatísticas e queries",
      "category": "performance"
    },
    "modo_debug": {
      "enabled": false,
      "description": "Ativa logs de debug",
      "category": "debug"
    }
  },
  "last_updated": "2026-02-17T14:30:00"
}
```

### 4. Via Interface Administrativa (Futura)

🚧 **Planejado:** Interface GUI para gerenciar flags sem editar JSON.

---

## Ordem de Prioridade

Quando uma flag é verificada, a ordem de prioridade é:

1. **Variável de ambiente** (`FEATURE_CACHE_ENABLED=1`)
2. **Arquivo `feature_flags.json`**
3. **Valor default no código** (`is_enabled('flag', default=True)`)

Isso permite:
- Configuração global via JSON
- Override pontual via .env (ex: modo debug apenas em dev)

---

## API Completa

### Verificar Flag

```python
flags = FeatureFlags()

# Verificar se está habilitada
enabled = flags.is_enabled('cache_enabled')

# Com valor padrão
enabled = flags.is_enabled('nova_feature', default=False)
```

### Habilitar/Desabilitar

```python
# Habilitar
flags.enable('nova_feature', description='Feature experimental', category='features')

# Desabilitar
flags.disable('cache_enabled')
```

### Listar Flags

```python
# Todas as flags
all_flags = flags.get_all()
# Retorna: {'cache_enabled': {'enabled': True, 'description': '...', ...}, ...}

# Apenas flags habilitadas
enabled = flags.get_enabled_flags()
# Retorna: ['cache_enabled', 'pydantic_validation', ...]

# Flags por categoria
perf_flags = flags.get_by_category('performance')
# Retorna: {'cache_enabled': {...}}
```

### Callbacks (Reagir a Mudanças)

```python
def on_cache_change(enabled: bool):
    if enabled:
        print("Cache habilitado!")
        inicializar_cache()
    else:
        print("Cache desabilitado!")
        limpar_cache()

flags.register_callback('cache_enabled', on_cache_change)

# Agora quando cache_enabled mudar, callback será executado
flags.disable('cache_enabled')  # → imprime "Cache desabilitado!"
```

---

## Categorias de Flags

| Categoria | Descrição | Flags |
|-----------|-----------|-------|
| `performance` | Otimizações de performance | `cache_enabled` |
| `validation` | Validação de dados | `pydantic_validation` |
| `logging` | Configurações de log | `json_logs` |
| `backup` | Sistema de backup | `backup_automatico`, `integracao_drive` |
| `ui` | Interface do usuário | `dashboard_avancado` |
| `debug` | Ferramentas de debug | `modo_debug` |
| `features` | Funcionalidades gerais | `relatorios_pdf` |
| `integration` | Integrações externas | `integracao_drive` |

---

## Criando Novas Feature Flags

### 1. Definir no Código

```python
# src/core/feature_flags.py → _get_default_flags()

'minha_nova_feature': {
    'enabled': False,  # Padrão: desabilitada
    'description': 'Descrição clara da feature',
    'category': 'features'  # Categoria apropriada
}
```

### 2. Usar no Código

```python
# src/services/meu_service.py

from src.core.feature_flags import FeatureFlags

flags = FeatureFlags()

def minha_funcao():
    if not flags.is_enabled('minha_nova_feature'):
        logger.warning("Feature 'minha_nova_feature' está desabilitada")
        return None
    
    # Lógica da nova feature
    ...
```

### 3. Documentar

- Adicionar linha na tabela apropriada neste documento
- Explicar impacto quando habilitada/desabilitada
- Listar onde a flag é usada no código

### 4. Testar

```python
# tests/test_feature_flags.py

def test_minha_nova_feature_habilitada():
    flags = FeatureFlags()
    flags.enable('minha_nova_feature')
    
    resultado = minha_funcao()
    assert resultado is not None

def test_minha_nova_feature_desabilitada():
    flags = FeatureFlags()
    flags.disable('minha_nova_feature')
    
    resultado = minha_funcao()
    assert resultado is None
```

---

## Exemplos de Uso Prático

### Rollout Gradual

```python
# Habilitar feature para 10% dos usuários
import random

flags = FeatureFlags()

def usar_novo_algoritmo():
    # Rollout 10%
    if flags.is_enabled('novo_algoritmo') or random.random() < 0.1:
        return algoritmo_novo()
    else:
        return algoritmo_antigo()
```

### Kill Switch

```python
# Desabilitar feature problemática rapidamente

# 1. Detectar problema
if erro_critico_detectado():
    flags.disable('feature_problematica')
    notificar_equipe("Feature desabilitada devido a erro crítico")

# 2. Feature é automaticamente desligada em todo sistema
# 3. Correção aplicada
# 4. Reativar:
flags.enable('feature_problematica')
```

### A/B Testing

```python
# Comparar duas implementações

if flags.is_enabled('algoritmo_a'):
    resultado = algoritmo_a()
    registrar_metricas('algoritmo_a', resultado)
else:
    resultado = algoritmo_b()
    registrar_metricas('algoritmo_b', resultado)
```

---

## Troubleshooting

### Flag não está mudando

1. **Verificar variável de ambiente:**
   ```bash
   echo $FEATURE_CACHE_ENABLED  # Linux/Mac
   echo %FEATURE_CACHE_ENABLED%  # Windows
   ```
   Variável de ambiente sempre tem prioridade!

2. **Verificar arquivo JSON:**
   ```bash
   cat feature_flags.json
   ```
   JSON malformado? O sistema usará flags padrão.

3. **Verificar logs:**
   ```
   2026-02-17 14:30:00 DEBUG feature_flags - Feature flags carregadas de feature_flags.json
   ```

### Flag não existe

```python
# Retorna False por padrão se não existe
flags.is_enabled('flag_inexistente')  # → False

# Ou fornece default explícito
flags.is_enabled('flag_inexistente', default=True)  # → True
```

### Resetar para Padrões

1. Deletar `feature_flags.json`
2. Reiniciar aplicação
3. Arquivo será recriado com flags padrão

---

## Boas Práticas

✅ **FAÇA:**
- Use nomes descritivos (`cache_enabled` ao invés de `flag1`)
- Documente o que a flag faz e onde é usada
- Teste com flag habilitada **e** desabilitada
- Remova flags antigas após feature estabilizada

❌ **NÃO FAÇA:**
- Usar muitas flags (max ~20 flags ativas)
- Deixar flags experimentais pra sempre
- Usar flags para configuração estática (use `.env` ou `config.py`)
- Acumular dívida técnica de flags não removidas

---

## Roadmap

- [ ] Interface GUI para gerenciar flags
- [ ] Suporte a flags por usuário (perfil-específico)
- [ ] Flags com data de expiração automática
- [ ] Métricas de uso de flags (quantas vezes checadas)
- [ ] Sincronização de flags entre instâncias (cluster)
- [ ] Audit trail (quem mudou qual flag quando)

---

> **Última atualização:** 17/02/2026  
> **Arquivo principal:** `src/core/feature_flags.py`  
> **Arquivo de configuração:** `feature_flags.json` (raiz do projeto)
