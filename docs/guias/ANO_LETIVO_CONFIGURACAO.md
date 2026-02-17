# Configuração do Ano Letivo Atual

## 📅 Problema Identificado

O sistema estava usando `YEAR(CURDATE())` para determinar o ano letivo atual, o que causava problemas quando:
- O ano civil mudava (ex: 2026) mas o ano letivo ainda era 2025
- O ano letivo começava em fevereiro, mas o sistema já assumia o novo ano em janeiro

## ✅ Solução Implementada

Criamos uma constante centralizada `ANO_LETIVO_ATUAL` no arquivo `src/core/config.py` e exportamos através do `src/core/config/__init__.py`.

### Configuração

```python
# src/core/config.py
ANO_LETIVO_ATUAL = 2025  # Atualizar manualmente quando o ano letivo mudar
```

### Importação

```python
from src.core.config import ANO_LETIVO_ATUAL, get_ano_letivo_atual

# Usar a constante diretamente
ano = ANO_LETIVO_ATUAL  # 2025

# Ou usar a função helper
ano = get_ano_letivo_atual()  # 2025
```

### Função Helper

```python
def get_ano_letivo_atual() -> int:
    """
    Retorna o ano letivo atual configurado no sistema.
    
    IMPORTANTE: Este valor deve ser atualizado manualmente quando 
    o novo ano letivo iniciar.
    
    Returns:
        int: Ano letivo atual (ex: 2025)
    """
    return ANO_LETIVO_ATUAL
```

## 📝 Arquivos Atualizados

Os seguintes arquivos foram atualizados para usar `ANO_LETIVO_ATUAL`:

1. ✅ `src/core/config.py` - Adicionada constante e função helper
2. ✅ `src/interfaces/cadastro_notas.py` - Cadastro/edição de notas
3. ✅ `src/services/aluno_service.py` - Serviço de alunos
4. ✅ `src/services/boletim_service.py` - Serviço de boletins
5. ✅ `src/services/matricula_service.py` - Serviço de matrículas
6. ✅ `src/services/perfil_filter_service.py` - Filtro por perfil
7. ✅ `src/ui/action_callbacks.py` - Callbacks de ações
8. ✅ `src/relatorios/declaracao_aluno.py` - Declarações
9. ✅ `src/relatorios/relatorio_analise_notas.py` - Análise de notas
10. ✅ `src/interfaces/administrativa.py` - Interface administrativa

## 🔄 Como Atualizar o Ano Letivo

Quando o ano letivo 2026 iniciar (geralmente em fevereiro), siga estes passos:

### 1. Atualizar a Constante

Edite o arquivo `src/core/config.py`:

```python
# Antes
ANO_LETIVO_ATUAL = 2025

# Depois
ANO_LETIVO_ATUAL = 2026
```

### 2. Verificar Banco de Dados

Certifique-se de que o ano letivo 2026 existe na tabela `anosletivos`:

```sql
SELECT * FROM anosletivos WHERE ano_letivo = 2026;
```

Se não existir, insira:

```sql
INSERT INTO anosletivos (ano_letivo, numero_dias_aula, data_inicio, data_fim)
VALUES (2026, 200, '2026-02-01', '2026-12-15');
```

### 3. Reiniciar o Sistema

Após atualizar a configuração, reinicie o sistema para que as mudanças tenham efeito.

## ⚠️ Arquivos que Ainda Usam YEAR(CURDATE())

Os seguintes arquivos ainda usam `YEAR(CURDATE())` mas são menos críticos (testes, scripts, etc.):

- `tests/integration/*.py` - Testes de integração
- `src/models/aluno_old.py` - Modelo antigo (deprecated)
- `src/ui/dashboard_coordenador.py` - Dashboard (usa data_inicio/data_fim)
- `src/ui/interfaces_extended.py` - Interfaces estendidas
- `src/relatorios/movimento_mensal.py` - Relatório mensal (usa data específica)

**Nota:** Esses arquivos podem ser atualizados conforme necessário, mas não afetam a funcionalidade principal do sistema.

## 🧪 Verificação

Para verificar se o ano letivo está configurado corretamente:

```python
from src.core.config import get_ano_letivo_atual

ano = get_ano_letivo_atual()
print(f"Ano letivo atual: {ano}")  # Deve imprimir: Ano letivo atual: 2025
```

## 📊 Benefícios

1. **Controle Manual**: Administrador decide quando mudar o ano letivo
2. **Centralizado**: Uma única constante controla todo o sistema
3. **Previsível**: Não muda automaticamente com o ano civil
4. **Fácil Manutenção**: Basta atualizar um arquivo
5. **Rastreável**: Mudança documentada no git

## 🔍 Histórico

- **03/01/2026 - 10:50**: Integração GEDUC atualizada para solicitar ano letivo no login
  - Atualizado `integrador_preenchimento.py` para incluir seleção de ano
  - Função `mudar_ano_letivo()` chamada após login em todas as extrações GEDUC
- **03/01/2026 - 10:42**: Correção do export em `src/core/config/__init__.py` para permitir importação
- **03/01/2026 - 10:35**: Implementação inicial da constante `ANO_LETIVO_ATUAL = 2025`
- **Motivo**: Sistema estava tentando usar ano letivo 2026 que ainda não iniciou
- **Impacto**: Resolução do problema de "nenhuma turma selecionada" no cadastro de notas

---

**Última atualização**: 03 de janeiro de 2026
