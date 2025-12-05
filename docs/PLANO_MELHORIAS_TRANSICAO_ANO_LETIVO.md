# Plano de Melhorias - Transição de Ano Letivo

## 📋 Resumo da Análise

Este documento apresenta uma análise detalhada do módulo de **Transição de Ano Letivo** do sistema de gestão escolar, identificando pontos de melhoria e propondo soluções.

---

## 📁 Arquivos Analisados

| Arquivo | Descrição |
|---------|-----------|
| `transicao_ano_letivo.py` | Módulo principal com a interface e lógica de transição |
| `ui/action_callbacks.py` | Callbacks que chamam a interface (autenticação) |
| `relatorio_pendencias.py` | Verificação de pendências de notas |
| `check_transicao_stats.py` | Script de verificação de estatísticas |
| `check_transicao_detalhado.py` | Script de análise detalhada |
| `teste_transicao_ano_letivo.py` | Template de testes (incompleto) |

---

## 🔍 Análise das Funções Principais (Ordenado por Prioridade)

### 🔴 PRIORIDADE 1 - Crítico

#### 1. `carregar_estatisticas`
- Conta matrículas ativas, alunos que continuam, reprovados e a excluir
- **Problema**: `escola_id = 60` hardcoded em múltiplos lugares
- **Problema**: Queries SQL complexas duplicadas
- **Impacto**: Sistema não funciona para outras escolas

#### 2. `executar_transicao`
- Realiza a transição efetiva
- **Problema**: Não faz backup automático
- **Problema**: Não registra log detalhado das operações
- **Problema**: Não há rollback granular
- **Impacto**: Risco de perda de dados irreversível

#### 3. `abrir_transicao_ano_letivo` (action_callbacks.py)
- Autenticação antes de abrir interface
- ~~**Problema**: Senha do banco usada para autenticação de usuário~~ ✅ CORRIGIDO
- **Impacto**: Vulnerabilidade de segurança

### 🟠 PRIORIDADE 2 - Importante ✅ CONCLUÍDO (05/12/2025)

#### 4. `carregar_dados_iniciais`
- Carrega ano letivo atual e estatísticas
- ~~**Problema**: Faz múltiplas consultas separadas ao banco~~ ✅ CORRIGIDO
- **Impacto**: Performance e manutenibilidade
- **Solução**: Query otimizada incluindo `data_inicio` e `data_fim`

#### 5. `verificar_fim_do_ano`
- Verifica se a data atual é posterior ao término do ano letivo
- ~~**Problema**: Não considera feriados ou calendário escolar personalizado~~ ✅ CORRIGIDO
- **Impacto**: Flexibilidade do sistema
- **Solução**: Agora usa `data_fim` da tabela `anosletivos` com fallback para 31/12

### 🟡 PRIORIDADE 3 - Menor ✅ CONCLUÍDO (05/12/2025)

#### 6. `InterfaceTransicaoAnoLetivo.__init__`
- Inicializa a interface gráfica com cores e variáveis
- ~~**Problema**: Cores hardcoded, poderiam estar em um arquivo de tema~~ ✅ CORRIGIDO
- **Impacto**: Apenas estético/manutenibilidade
- **Solução**: Cores movidas para `ui/theme.py` com import centralizado

### ✅ PRIORIDADE 4 - OK (Sem alterações necessárias)

#### 7. `verificar_pendencias_bimestrais`
- Checa notas pendentes em todos os bimestres
- **OK**: Boa implementação de validação prévia

#### 8. `simular_transicao`
- Mostra preview das operações que serão realizadas
- **OK**: Boa prática de segurança

#### 9. `confirmar_transicao`
- Solicita confirmação e reautenticação
- **OK**: Dupla confirmação é segura

---

## ⚠️ Problemas Identificados

### 🔴 Críticos

#### 1. **Escola ID Hardcoded**
```python
# Aparece em 15+ lugares no código
AND a.escola_id = 60
AND t.escola_id = 60
```
**Impacto**: Sistema não funciona para outras escolas
**Solução**: Criar parâmetro de escola no construtor ou usar configuração global

#### 2. **Sem Backup Automático**
A operação é irreversível mas não força backup antes de executar.
**Solução**: Implementar backup automático ou verificação de backup recente

#### 3. **Autenticação Fraca**
```python
senha_correta = os.getenv('DB_PASSWORD')
```
Usa a senha do banco de dados para autenticação do usuário.
**Solução**: Usar sistema de permissões próprio ou senha administrativa separada

### 🟠 Importantes

#### 4. **Queries SQL Duplicadas**
As mesmas queries para buscar turmas do 9º ano e alunos ativos aparecem em:
- `carregar_estatisticas`
- `executar_transicao`
- `check_transicao_detalhado.py`

**Solução**: Criar funções utilitárias reutilizáveis

#### 5. **Falta de Logging Estruturado**
Não há logs detalhados das operações realizadas.
**Solução**: Implementar logging com detalhes de cada passo

#### 6. **Não Progressão de Série Automática**
```python
INSERT INTO Matriculas (aluno_id, turma_id, ano_letivo_id, status)
VALUES (%s, %s, %s, 'Ativo')
```
Rematricula na **mesma turma** em vez de promover para a próxima série.
**Solução**: Implementar lógica de progressão de série

#### 7. **Tratamento de Reprovados Incompleto**
Alunos reprovados são rematriculados na mesma turma, mas deveria haver lógica para:
- Manter na mesma série
- Registrar status de "Retido"

### 🟡 Menores

#### 8. **Falta Testes Automatizados**
O arquivo `teste_transicao_ano_letivo.py` é apenas um template vazio.
**Solução**: Implementar testes unitários e de integração

#### 9. **Validação de Data Simples**
Verifica apenas se passou de 31/12, não considera:
- Ano letivo com calendário diferente
- Recesso escolar personalizado

#### 10. **UI Não Responsiva Durante Execução**
Embora use `self.janela.update()`, operações longas podem travar a UI.
**Solução**: Executar em thread separada

---

## 🚀 Plano de Melhorias Proposto

### Fase 1: Correções Críticas (Prioridade Alta)

#### 1.1 Parametrizar Escola ID
```python
# Em config.py ou similar
ESCOLA_ID = int(os.getenv('ESCOLA_ID', 60))

# Uso
class InterfaceTransicaoAnoLetivo:
    def __init__(self, janela_pai, janela_principal, escola_id=None):
        self.escola_id = escola_id or config.ESCOLA_ID
```

#### 1.2 Backup Automático Obrigatório
```python
def verificar_backup_recente(self) -> bool:
    """Verifica se há backup do banco nas últimas 24h"""
    # Implementar verificação de arquivo de backup
    pass

def criar_backup_pre_transicao(self):
    """Cria backup antes de executar a transição"""
    from subprocess import run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivo = f"backup_pre_transicao_{timestamp}.sql"
    # mysqldump command
    pass
```

#### 1.3 Sistema de Autenticação Adequado
```python
# Usar sistema de permissões existente
from ui.auth import verificar_permissao_admin

def abrir_transicao_ano_letivo(self):
    if not verificar_permissao_admin(self.usuario_atual):
        messagebox.showerror("Acesso Negado", "Operação requer permissão de administrador")
        return
```

### Fase 2: Refatoração de Código (Prioridade Média)

#### 2.1 Criar Módulo de Queries Reutilizáveis
```python
# db/queries_transicao.py

class QueriesTransicao:
    @staticmethod
    def get_turmas_9ano(escola_id: int) -> list:
        """Retorna IDs das turmas do 9º ano"""
        pass
    
    @staticmethod
    def get_alunos_ativos(ano_letivo_id: int, escola_id: int) -> list:
        """Retorna alunos com matrícula ativa"""
        pass
    
    @staticmethod
    def get_alunos_reprovados(ano_letivo_id: int, escola_id: int) -> list:
        """Retorna alunos reprovados (média < 60)"""
        pass
```

#### 2.2 Implementar Progressão de Série
```python
def obter_proxima_turma(self, turma_atual_id: int) -> int:
    """Obtém a turma da próxima série para o aluno"""
    # 1º ano A → 2º ano A
    # Considerar turno e nome da turma
    pass

def executar_transicao(self):
    # ...
    for aluno in alunos:
        nova_turma_id = self.obter_proxima_turma(aluno['turma_id'])
        # Se reprovado, manter mesma turma
        if aluno.get('reprovado'):
            nova_turma_id = aluno['turma_id']
        # Criar matrícula
        cursor.execute("""
            INSERT INTO Matriculas (aluno_id, turma_id, ano_letivo_id, status)
            VALUES (%s, %s, %s, 'Ativo')
        """, (aluno['aluno_id'], nova_turma_id, novo_ano_id))
```

#### 2.3 Implementar Logging Detalhado
```python
from config_logs import get_logger
logger = get_logger(__name__)

def executar_transicao(self):
    logger.info(f"Iniciando transição {self.ano_atual['ano_letivo']} → {self.ano_novo['ano_letivo']}")
    
    # Log de cada operação
    logger.info(f"Matrículas encerradas: {total_encerradas}")
    logger.info(f"Alunos rematriculados: {total_rematriculados}")
    logger.info(f"Alunos reprovados: {total_reprovados}")
    
    # Registrar em tabela de auditoria
    self.registrar_auditoria('TRANSICAO_ANO', {
        'ano_origem': self.ano_atual['ano_letivo'],
        'ano_destino': self.ano_novo['ano_letivo'],
        'matriculas_encerradas': total_encerradas,
        # ...
    })
```

### Fase 3: Testes e Validação (Prioridade Média)

#### 3.1 Implementar Testes Unitários
```python
# tests/test_transicao_ano_letivo.py

import pytest
from transicao_ano_letivo import InterfaceTransicaoAnoLetivo

class TestTransicaoAnoLetivo:
    def test_verificar_fim_do_ano_antes_31_12(self):
        """Deve retornar False se ainda não chegou 31/12"""
        pass
    
    def test_verificar_fim_do_ano_depois_31_12(self):
        """Deve retornar True se passou de 31/12"""
        pass
    
    def test_verificar_pendencias_sem_pendencias(self):
        """Deve retornar dict vazio se não há pendências"""
        pass
    
    def test_obter_proxima_turma(self):
        """Deve retornar turma da série seguinte"""
        pass
    
    def test_aluno_reprovado_nao_avanca_serie(self):
        """Aluno reprovado deve permanecer na mesma série"""
        pass
```

#### 3.2 Implementar Modo Dry-Run
```python
def executar_transicao(self, dry_run=False):
    """
    Executa a transição de ano letivo.
    
    Args:
        dry_run: Se True, não faz commit das alterações
    """
    # ...
    if dry_run:
        conn.rollback()
        logger.info("Modo DRY-RUN: alterações descartadas")
    else:
        conn.commit()
```

### Fase 4: Melhorias de UX (Prioridade Baixa)

#### 4.1 Execução em Thread Separada
```python
import threading

def executar_transicao(self):
    self.btn_simular.config(state=DISABLED)
    self.btn_executar.config(state=DISABLED)
    
    def worker():
        try:
            self._executar_transicao_interno()
        except Exception as e:
            self.janela.after(0, lambda: self._mostrar_erro(str(e)))
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
```

#### 4.2 Relatório Detalhado Pós-Transição
```python
def gerar_relatorio_transicao(self, dados: dict) -> str:
    """Gera PDF com relatório detalhado da transição"""
    # Listar todos os alunos processados
    # Status de cada operação
    # Estatísticas finais
    pass
```

#### 4.3 Configuração de Calendário Escolar
```python
# Em config.py
CALENDARIO_ESCOLAR = {
    'inicio_ano_letivo': '02-01',  # 1º de fevereiro
    'fim_ano_letivo': '12-20',     # 20 de dezembro
}

def verificar_fim_do_ano(self) -> bool:
    """Verifica se o ano letivo encerrou baseado no calendário"""
    from config import CALENDARIO_ESCOLAR
    # Implementar verificação com calendário configurável
```

---

## 📊 Cronograma Sugerido

| Fase | Descrição | Tempo Estimado |
|------|-----------|----------------|
| 1 | Correções Críticas | 2-3 dias |
| 2 | Refatoração de Código | 3-5 dias |
| 3 | Testes e Validação | 2-3 dias |
| 4 | Melhorias de UX | 2-3 dias |

**Total**: 9-14 dias de desenvolvimento

---

## 📝 Checklist de Implementação

### Fase 1 - Crítico ✅ CONCLUÍDO (05/12/2025)
- [x] Parametrizar `escola_id` em todas as queries
  - Adicionado `from config import ESCOLA_ID`
  - Classe recebe `escola_id` como parâmetro opcional
  - Todas as 9 queries atualizadas para usar `self.escola_id`
- [x] Implementar verificação/criação de backup
  - Novo método `verificar_backup_recente()` - verifica backups nas últimas 24h
  - Novo método `criar_backup_pre_transicao()` - usa `Seguranca.fazer_backup()`
  - Integração automática no fluxo de confirmação
- [x] Melhorar sistema de autenticação
  - Nova variável de ambiente `ADMIN_TRANSICAO_PASSWORD`
  - Fallback para `DB_PASSWORD` para compatibilidade
  - Mensagens de alerta mais claras
  - Logging de tentativas de acesso
- [x] Adicionar logging estruturado
  - Logger configurado no módulo
  - Log de início com dados da transição
  - Log de cada passo com contadores
  - Log de resumo final com estatísticas
  - Log de erros com rollback

### Fase 2 - Importante ✅ CONCLUÍDO (05/12/2025)
- [x] Otimizar `carregar_dados_iniciais`
  - Query única incluindo `data_inicio` e `data_fim`
  - Removida dependência de `traceback.print_exc()` (usa logger)
- [x] Usar `data_fim` da tabela `anosletivos`
  - `verificar_fim_do_ano()` agora usa campo `data_fim` do banco
  - Fallback para 31/12 se campo não estiver preenchido
  - Logging de qual data está sendo usada
- [ ] Criar módulo `db/queries_transicao.py`
- [ ] Implementar progressão automática de série
- [ ] Criar tabela de auditoria de transições

### Fase 3 - Menor ✅ CONCLUÍDO (05/12/2025)
- [x] Extrair cores para arquivo de tema
  - Cores adicionadas em `ui/theme.py`
  - Import centralizado com fallback
  - Mantida compatibilidade com variáveis `self.co0`, `self.co1`, etc.

### Fase 4 - Testes (Pendente)
- [ ] Criar testes unitários
- [ ] Implementar modo dry-run
- [ ] Testar com dados de homologação

### Fase 5 - UX (Pendente)
- [ ] Executar operações em thread separada
- [ ] Gerar relatório PDF pós-transição
- [ ] ~~Implementar calendário escolar configurável~~ ✅ (resolvido usando `data_fim` da tabela)

---

## 📋 Configuração Necessária

### Nova Variável de Ambiente (Recomendado)

Adicione ao arquivo `.env`:

```env
# Senha administrativa para operações críticas (Transição de Ano)
# Se não definida, usa DB_PASSWORD como fallback
ADMIN_TRANSICAO_PASSWORD=sua_senha_segura_aqui
```

---

## 🔗 Referências

- Arquivo principal: `transicao_ano_letivo.py`
- Autenticação: `ui/action_callbacks.py` (linhas 411-465)
- Pendências: `relatorio_pendencias.py`
- Conexão DB: `db/connection.py`
- Backup: `Seguranca.py`
- Configuração: `config.py` (ESCOLA_ID)
- Tema/Cores: `ui/theme.py`

---

*Documento gerado em: 05/12/2025*
*Última atualização: 05/12/2025 - Fases 1, 2 e 3 implementadas*
*Autor: Análise automatizada do sistema*
