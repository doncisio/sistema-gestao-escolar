# Sistema de Permissões RBAC

**Sistema de Gestão Escolar - Controle de Acesso Baseado em Funções (RBAC)**

## Visão Geral

O sistema implementa controle de acesso baseado em 3 perfis principais:
- **Administrador**: Acesso total ao sistema
- **Coordenador Pedagógico**: Acesso amplo a funcionalidades pedagógicas
- **Professor**: Acesso limitado a funcionalidades de sala de aula

## Perfis do Sistema

### 1. Administrador

**Descrição:** Acesso irrestrito a todas as funcionalidades do sistema.

**Características:**
- Único perfil que pode acessar interface administrativa (escolas, disciplinas, turmas, séries)
- Pode gerenciar usuários e perfis
- Acesso total a relatórios e exportações
- Pode executar transição de ano letivo
- Pode importar/exportar dados do GEDUC

**Módulo de código:** `auth/models.py` → `Perfil.ADMINISTRADOR`

---

### 2. Coordenador Pedagógico

**Descrição:** Coordena atividades pedagógicas da escola.

**Permissões principais:**
- Visualização completa de dados de alunos e funcionários
- Geração de relatórios pedagógicos
- Acesso ao dashboard pedagógico completo
- Gerenciamento de horários escolares
- Cadastro e edição de alunos
- Visualização de frequências e notas
- Emissão de declarações e históricos
- Gerenciamento de livros faltantes

**Restrições:**
- ❌ Não pode acessar interface administrativa (gerenciar escolas/disciplinas/turmas/séries)  
- ❌ Não pode executar transição de ano letivo  
- ❌ Não pode gerenciar usuários  
- ❌ Não pode fazer importação/exportação GEDUC  
- ❌ Acesso limitado a alguns relatórios específicos

---

### 3. Professor

**Descrição:** Professor de sala de aula com acesso limitado às suas turmas.

**Permissões principais:**
- Lançamento de notas (suas disciplinas/turmas)
- Lançamento de frequência (suas turmas)
- Visualização de listas de notas e frequências
- Dashboard filtrado (apenas suas turmas)
- Geração de relatórios básicos de suas turmas

**Restrições:**
- ❌ Não pode cadastrar ou editar alunos  
- ❌ Não pode emitir boletins/históricos/declarações  
- ❌ Não pode acessar dados de outras turmas  
- ❌ Não pode gerenciar horários  
- ❌ Não pode visualizar contatos de responsáveis  
- ❌ Não pode acessar relatórios gerenciais

---

## Matriz de Permissões por Funcionalidade

| Funcionalidade | Admin | Coord | Prof | Módulo/Arquivo |
|---------------|:-----:|:-----:|:----:|----------------|
| **Dashboard Completo** | ✅ | ✅ | 🟨¹ | `src/ui/dashboard.py` |
| **Cadastrar Aluno** | ✅ | ✅ | ❌ | `src/interfaces/cadastro_aluno.py` |
| **Editar Aluno** | ✅ | ✅ | ❌ | `src/interfaces/edicao_aluno.py` |
| **Excluir Aluno** | ✅ | ❌ | ❌ | `src/ui/actions/aluno.py` |
| **Cadastrar Funcionário** | ✅ | ❌ | ❌ | `src/interfaces/cadastro_funcionario.py` |
| **Editar Funcionário** | ✅ | ❌ | ❌ | `src/interfaces/edicao_funcionario.py` |
| **Matricular Aluno** | ✅ | ✅ | ❌ | `src/interfaces/matricula_unificada.py` |
| **Lançar Notas** | ✅ | ❌ | ✅ | `src/interfaces/cadastro_notas.py` |
| **Lançar Frequência** | ✅ | ❌ | ✅ | `src/interfaces/lancamento_frequencia.py` |
| **Cadastrar Faltas** | ✅ | ✅ | ❌ | `src/interfaces/cadastro_faltas.py` |
| **Gerenciar Horários** | ✅ | ✅ | ❌ | `src/interfaces/horarios_escolares.py` |
| **Interface Administrativa** | ✅ | ❌ | ❌ | `src/interfaces/administrativa.py` |
| **Transição Ano Letivo** | ✅ | ❌ | ❌ | `src/interfaces/transicao_ano_letivo.py` |
| **Gestão de Usuários** | ✅ | ❌ | ❌ | `src/ui/gestao_usuarios.py` |
| **Histórico Escolar** | ✅ | ✅ | ❌ | `src/interfaces/historico_escolar.py` |
| **Boletim** | ✅ | ✅ | ❌ | `src/relatorios/boletim.py` |
| **Declarações** | ✅ | ✅ | ❌ | `src/relatorios/declaracao_aluno.py` |
| **Atas Bimestrais** | ✅ | ✅ | ❌ | `src/relatorios/nota_ata.py` |
| **Movimento Mensal** | ✅ | ✅ | ❌ | `src/relatorios/movimento_mensal.py` |
| **Banco de Questões BNCC** | ✅ | ✅ | ✅ | `banco_questoes/` |
| **Importação GEDUC** | ✅ | ❌ | ❌ | `src/importadores/geduc.py` |
| **Exportação GEDUC** | ✅ | ❌ | ❌ | `src/exportadores/geduc_exportador.py` |
| **Gerenciar Licenças** | ✅ | ❌ | ❌ | `src/interfaces/gerenciamento_licencas.py` |
| **Crachás Individuais** | ✅ | ✅ | ❌ | `src/ui/cracha_individual_window.py` |
| **Livros Faltantes** | ✅ | ✅ | ❌ | `src/ui/livros_faltantes_window.py` |
| **Backup Google Drive** | ✅ | ❌ | ❌ | `src/core/seguranca.py` |

**Legendas:**
- ✅ = Acesso completo
- 🟨¹ = Acesso filtrado (professor vê apenas suas turmas)
- ❌ = Sem acesso

---

## Relatórios por Perfil

### Administrador (Todos os Relatórios)

#### Listas
- ✅ Lista Atualizada
- ✅ Lista Atualizada SEMED
- ✅ **Lista Alfabética** (exclusivo Admin)
- ✅ Lista de Reunião
- ✅ Lista de Fardamento
- ✅ Lista de Notas
- ✅ Lista de Frequências
- ✅ Lista de Controle de Livros
- ✅ Contatos de Responsáveis
- ✅ Levantamento de Necessidades
- ✅ Alunos com Transtornos
- ✅ **Transferências Expedidas** (exclusivo Admin)
- ✅ **Transferências Recebidas** (exclusivo Admin)
- ✅ **Exportar Funcionários Excel** (exclusivo Admin)

#### Documentos
- ✅ Boletins Bimestrais
- ✅ Atas (1º-5º, 6º-9º, Geral, 1º-9º)
- ✅ Histórico Escolar
- ✅ Declaração de Aluno
- ✅ Declaração de Funcionário
- ✅ Declaração de Comparecimento
- ✅ Certificados
- ✅ Termo de Responsabilidade
- ✅ Termos "Cuidar dos Olhos"
- ✅ Folha de Ponto
- ✅ Resumo de Ponto

#### Análises
- ✅ Relatório Estatístico de Notas
- ✅ Movimento Mensal
- ✅ Tabela de Docentes
- ✅ Pendências (Análise de Notas)

---

### Coordenador Pedagógico

#### Listas
- ✅ Lista Atualizada
- ✅ Lista de Reunião
- ✅ Lista de Fardamento
- ✅ Lista de Controle de Livros
- ✅ Contatos de Responsáveis
- ✅ Levantamento de Necessidades
- ✅ Alunos com Transtornos

#### Documentos
- ✅ Boletins Bimestrais
- ✅ Atas (1º-5º, 6º-9º, Geral, 1º-9º)
- ✅ Histórico Escolar
- ✅ Declaração de Aluno
- ✅ Declaração de Funcionário
- ✅ Declaração de Comparecimento
- ✅ Certificados
- ✅ Termo de Responsabilidade
- ✅ Termos "Cuidar dos Olhos"

#### Análises
- ✅ Relatório Estatístico de Notas
- ✅ Movimento Mensal
- ✅ Pendências (Análise de Notas)

---

### Professor

#### Listas (Apenas suas turmas)
- ✅ Lista de Notas (suas turmas)
- ✅ Lista de Frequências (suas turmas)

#### Análises
- ✅ Relatório Estatístico de Notas (suas turmas)

---

## Permissões no Banco de Dados

O sistema utiliza a tabela `perfil_permissoes` para gerenciar permissões granulares:

```sql
-- Estrutura simplificada
perfil_permissoes
├── perfil (VARCHAR)           -- 'administrador', 'coordenador', 'professor'
├── permissao_id (INT FK)      -- ID da permissão
└── ativo (BOOLEAN)

permissoes
├── id (INT PK)
├── codigo (VARCHAR)           -- Ex: 'alunos.criar', 'notas.lancar'
├── descricao (VARCHAR)
└── modulo (VARCHAR)
```

### Estrutura de Códigos de Permissão

| Código | Descrição | Módulo |
|--------|-----------|--------|
| `dashboard.completo` | Ver dashboard completo | Dashboard |
| `dashboard.pedagogico` | Ver dashboard pedagógico | Dashboard |
| `dashboard.proprio` | Ver apenas suas turmas | Dashboard |
| `alunos.visualizar` | Visualizar alunos | Alunos |
| `alunos.criar` | Cadastrar alunos | Alunos |
| `alunos.editar` | Editar alunos | Alunos |
| `alunos.excluir` | Excluir alunos | Alunos |
| `funcionarios.visualizar` | Visualizar funcionários | Funcionários |
| `funcionarios.gerenciar` | Gerenciar funcionários | Funcionários |
| `matriculas.gerenciar` | Gerenciar matrículas | Matrículas |
| `notas.visualizar` | Visualizar notas | Notas |
| `notas.lancar` | Lançar/editar notas | Notas |
| `frequencia.lancar` | Lançar frequência | Frequência |
| `horarios.gerenciar` | Gerenciar horários | Horários |
| `relatorios.visualizar` | Ver relatórios | Relatórios |
| `relatorios.gerar` | Gerar relatórios | Relatórios |
| `administrativa.acesso` | Interface administrativa | Admin |
| `usuarios.gerenciar` | Gerenciar usuários | Usuários |
| `sistema.transicao` | Transição ano letivo | Sistema |
| `sistema.backup` | Backup do sistema | Sistema |
| `geduc.importar` | Importar do GEDUC | GEDUC |
| `geduc.exportar` | Exportar para GEDUC | GEDUC |

---

## Verificação de Permissões no Código

### 1. Via Decorador `@require_permissions`

```python
from auth.decorators import require_permissions

@require_permissions(['alunos.criar'])
def cadastrar_aluno():
    # Só executa se usuário tiver a permissão
    pass
```

### 2. Via Objeto `Usuario`

```python
from auth import UsuarioLogado

usuario = UsuarioLogado.obter()

if usuario.tem_permissao('alunos.editar'):
    # Permitir edição
    pass

if usuario.is_admin():
    # Administrador tem todas as permissões
    pass
```

### 3. Via `AcessoControl` (UI)

```python
from auth.guards import AcessoControl

acesso = AcessoControl()

if acesso.pode('notas.lancar'):
    # Mostrar botão de lançar notas
    pass

if acesso.is_admin_ou_coordenador():
    # Funcionalidade para admin ou coordenador
    pass
```

---

## Regras Especiais

### 1. Regra do Administrador

O perfil Administrador **sempre retorna True** em qualquer verificação de permissão. Isso está implementado em:

```python
# auth/models.py
def tem_permissao(self, codigo_permissao: str) -> bool:
    if self.perfil == Perfil.ADMINISTRADOR:
        return True  # Admin tem TODAS as permissões
    return codigo_permissao in self.permissoes
```

### 2. Filtro de Turmas para Professor

Professores só veem dados das turmas em que lecionam. Filtro aplicado em:
- Dashboard (`src/ui/dashboard_professor.py`)
- Lançamento de notas (`src/interfaces/cadastro_notas.py`)
- Lançamento de frequência (`src/interfaces/lancamento_frequencia.py`)

**Implementação:**
```python
if usuario.is_professor():
    # Filtrar apenas turmas onde professor leciona
    turmas = obter_turmas_professor(usuario.funcionario_id)
```

### 3. Primeiro Acesso

Usuários novos (`primeiro_acesso = True`) são forçados a trocar senha antes de acessar qualquer funcionalidade.

**Verificação no login:**
```python
# auth/auth_service.py
if usuario.primeiro_acesso:
    # Abrir janela de trocar senha obrigatória
    abrir_dialog_trocar_senha(usuario)
```

---

## Testes de Permissão

### Testar Acesso de Perfil

```python
# tests/auth/test_permissoes.py
def test_professor_nao_pode_cadastrar_aluno():
    usuario = criar_usuario_teste(perfil=Perfil.PROFESSOR)
    assert not usuario.tem_permissao('alunos.criar')

def test_coordenador_pode_emitir_boletim():
    usuario = criar_usuario_teste(perfil=Perfil.COORDENADOR)
    assert usuario.tem_permissao('relatorios.gerar')

def test_admin_tem_todas_permissoes():
    usuario = criar_usuario_teste(perfil=Perfil.ADMINISTRADOR)
    assert usuario.tem_permissao('qualquer.coisa.aqui')
```

---

## Auditoria de Acesso

O sistema registra logs de acesso em `auth/auth_service.py`:

```python
# Login bem-sucedido
logger.info(f"✅ Login bem-sucedido: {username} ({usuario.perfil_display})")

# Tentativa de acesso sem permissão
logger.warning(f"⚠️  Acesso negado: {usuario.username} tentou {codigo_permissao}")
```

**Logs armazenados em:**  
`logs/app.log` (texto) + Banco de dados (tabela `logs_acesso`)

---

## Considerações de Segurança

1. **Permissões no backend:** Sempre validar permissões no servidor (services), não apenas na UI
2. **Separação de dados:** Professor não deve ter SQL que retorna dados de outras turmas
3. **Auditoria:** Todo acesso a funções críticas deve ser logado
4. **Sessão segura:** Implementar timeout de sessão (recomendado: 30 min de inatividade)
5. **HTTPS:** Para acesso remoto (versão web futura), sempre usar HTTPS

---

## Roadmap de Melhorias

- [ ] Adicionar permissões granulares por módulo na tabela `permissões`
- [ ] Implementar cache de permissões (evitar consultas BD a cada verificação)
- [ ] Adicionar interface para gerenciamento de permissões customizadas
- [ ] Criar perfil "Secretaria" com permissões específicas
- [ ] Implementar timeout de sessão automático
- [ ] Adicionar 2FA (autenticação de dois fatores) para administradores
- [ ] Criar audit trail completo (quem fez o quê quando)

---

> **Última atualização:** 17/02/2026  
> **Arquivos relacionados:** `auth/models.py`, `auth/guards.py`, `auth/decorators.py`, `src/ui/button_factory.py`
