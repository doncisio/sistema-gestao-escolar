# 📋 Plano de Implementação de Perfis de Usuário

> **📅 Última atualização**: 28 de Novembro de 2025  
> **🎯 Status Geral**: Fases 1-6 CONCLUÍDAS ✅ | Fase 7 em andamento

---

## 📊 RESUMO DO PROGRESSO

```
┌────────────────────────────────────────────────────────────────────────┐
│                    STATUS DA IMPLEMENTAÇÃO                              │
├────────────────────────────────────────────────────────────────────────┤
│  ✅ Fase 0 - Feature Flag                    CONCLUÍDA                 │
│  ✅ Fase 1 - Infraestrutura de Autenticação  CONCLUÍDA                 │
│  ✅ Fase 2 - Tela de Login                   CONCLUÍDA                 │
│  ✅ Fase 3 - Controle de Acesso              CONCLUÍDA                 │
│  ✅ Fase 4 - Filtro de Dados por Perfil      CONCLUÍDA                 │
│  ✅ Fase 5 - Interface de Gestão de Usuários CONCLUÍDA                 │
│  ✅ Fase 6 - Testes e Ajustes                CONCLUÍDA                 │
│  🔄 Fase 7 - Ativação em Produção            EM ANDAMENTO              │
├────────────────────────────────────────────────────────────────────────┤
│  📁 Arquivos Criados: 15+ arquivos no módulo auth/ e ui/               │
│  🗄️ Tabelas Criadas: usuarios, permissoes, perfil_permissoes,          │
│                       usuario_permissoes, logs_acesso                   │
│  👤 Usuários de Teste: admin, coord_teste, prof_teste                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Objetivo

Adicionar ao Sistema de Gestão Escolar a capacidade de suportar múltiplos perfis de usuário (Administrador/Secretário, Coordenador, Professor), cada um com suas funções e permissões específicas.

---

## 🚦 ESTRATÉGIA DE DESENVOLVIMENTO: Feature Flag

### Premissa Fundamental
> **O sistema deve continuar funcionando normalmente durante todo o desenvolvimento.**  
> O usuário principal (você) continuará usando o sistema no dia a dia, enquanto os novos recursos de perfis são desenvolvidos em paralelo.

### Como funciona

```
┌─────────────────────────────────────────────────────────────────┐
│                    DURANTE O DESENVOLVIMENTO                     │
├─────────────────────────────────────────────────────────────────┤
│  PERFIS_HABILITADOS = False (padrão)                            │
│                                                                  │
│  → Sistema abre DIRETO como hoje (sem tela de login)            │
│  → Todas as funções disponíveis (comportamento atual)           │
│  → Você trabalha normalmente enquanto programa                  │
│  → Código novo fica "adormecido" aguardando ativação            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (Quando tudo estiver pronto)
┌─────────────────────────────────────────────────────────────────┐
│                    APÓS ATIVAR A FEATURE FLAG                    │
├─────────────────────────────────────────────────────────────────┤
│  PERFIS_HABILITADOS = True                                      │
│                                                                  │
│  → Sistema abre com TELA DE LOGIN                               │
│  → Cada usuário vê apenas o que seu perfil permite              │
│  → Controle de acesso ativo                                     │
│  → Logs de auditoria funcionando                                │
└─────────────────────────────────────────────────────────────────┘
```

### Arquivo de Controle: `feature_flags.json`
```json
{
    "perfis_habilitados": true,
    "BANCO_QUESTOES_HABILITADO": false,
    "DASHBOARD_BNCC_HABILITADO": false
}
```

---

## 🎭 Perfis de Usuário Implementados

### 1. **Administrador/Secretário** (Acesso Total) ✅
**Permissões implementadas:**
- ✅ Cadastro, edição e exclusão de alunos
- ✅ Cadastro, edição e exclusão de funcionários
- ✅ Gestão de turmas e matrículas
- ✅ Geração de documentos (declarações, históricos, boletins)
- ✅ Relatórios administrativos
- ✅ Backup e manutenção do sistema
- ✅ Transição de ano letivo
- ✅ Configurações gerais
- ✅ **Gestão de usuários do sistema**

### 2. **Coordenador Pedagógico** (Acesso Pedagógico) ✅
**Permissões implementadas:**
- ✅ Visualizar todos os alunos e turmas
- ✅ Visualizar funcionários (sem edição)
- ✅ Dashboard pedagógico completo
- ✅ Relatórios de desempenho por turma/aluno
- ✅ Relatórios de frequência
- ✅ Visualizar e gerar atas de resultados
- ✅ Acompanhar lançamento de notas dos professores
- ❌ Cadastrar/editar/excluir alunos
- ❌ Cadastrar/editar funcionários
- ❌ Transição de ano letivo
- ❌ Backup do sistema

### 3. **Professor** (Acesso Restrito) ✅
**Permissões implementadas:**
- ✅ Visualizar **apenas suas turmas** vinculadas (via `funcionario_disciplinas`)
- ✅ Visualizar alunos das suas turmas
- ✅ Lançar/editar notas e frequência (suas turmas)
- ✅ Gerar boletins dos seus alunos
- ✅ Relatórios das suas turmas
- ❌ Ver outras turmas/professores
- ❌ Funções administrativas
- ❌ Cadastrar alunos/funcionários
- ❌ Relatórios de outras turmas

---

## ✅ FASES CONCLUÍDAS

### **FASE 0: Feature Flag** ✅ CONCLUÍDA
- [x] Arquivo `feature_flags.json` criado
- [x] Função `perfis_habilitados()` em `config.py`
- [x] Sistema funciona normalmente com flag desativada

### **FASE 1: Infraestrutura de Autenticação** ✅ CONCLUÍDA

#### Arquivos Criados:
```
auth/
├── __init__.py
├── auth_service.py      # Serviço de autenticação com bcrypt
├── decorators.py        # @requer_permissao, @requer_login, @requer_perfil
├── models.py            # Usuario, Perfil, Permissao
├── password_utils.py    # Hash e verificação de senhas
└── usuario_logado.py    # Singleton da sessão atual
```

#### Tabelas SQL Criadas:
- `usuarios` - Usuários do sistema com hash bcrypt
- `permissoes` - 58 permissões cadastradas
- `perfil_permissoes` - Mapeamento perfil → permissões
- `usuario_permissoes` - Permissões personalizadas por usuário
- `logs_acesso` - Logs de login/logout/ações

### **FASE 2: Tela de Login** ✅ CONCLUÍDA

#### Arquivos Criados:
```
ui/
└── login.py             # Interface de login com validação
```

#### Funcionalidades:
- [x] Interface Tkinter com campos usuário/senha
- [x] Validação de credenciais via AuthService
- [x] Exibição de mensagens de erro
- [x] Bloqueio após 5 tentativas (15 min)
- [x] Registro de logs de acesso

### **FASE 3: Controle de Acesso na Interface** ✅ CONCLUÍDA

#### Implementações:
- [x] Decorator `@requer_permissao(permissao)`
- [x] Decorator `@requer_login`
- [x] Decorator `@requer_perfil(perfis)`
- [x] `ControleAcesso` - Classe utilitária para verificações
- [x] Integração com `ButtonFactory` - Botões filtrados por perfil
- [x] Integração com Menu - Menus adaptados por perfil

### **FASE 4: Filtro de Dados por Perfil** ✅ CONCLUÍDA

#### Arquivos Criados/Modificados:
```
services/
├── perfil_filter_service.py  # NOVO - Filtro central por perfil
└── turma_service.py          # MODIFICADO - Suporte a filtro
```

#### Funcionalidades:
- [x] Professor vê apenas suas turmas (via `funcionario_disciplinas`)
- [x] Professor vê apenas alunos das suas turmas
- [x] Coordenador vê todas as turmas
- [x] Admin vê todas as turmas
- [x] `listar_turmas(aplicar_filtro_perfil=True)`

### **FASE 5: Interface de Gestão de Usuários** ✅ CONCLUÍDA

#### Arquivos Criados:
```
ui/
└── gestao_usuarios.py        # Interface CRUD de usuários

services/
└── logs_acesso_service.py    # Serviço de logs de acesso
```

#### Funcionalidades:
- [x] Listar usuários existentes
- [x] Criar novo usuário (vinculado a funcionário)
- [x] Editar perfil de usuário
- [x] Ativar/Desativar usuário
- [x] Resetar senha (manual ou aleatória)
- [x] Busca por nome/username/perfil
- [x] Logs de todas as ações

### **FASE 6: Testes e Ajustes** ✅ CONCLUÍDA

#### Usuários de Teste Criados:
| Username | Perfil | Senha | Funcionário |
|----------|--------|-------|-------------|
| admin | Administrador | Admin@123 | Tarcisio Sousa de Almeida |
| coord_teste | Coordenador | Coord@123 | Laise de Laine Rabelo Viegas |
| prof_teste | Professor | Prof@123 | Fernanda Carneiro Leite |

#### Testes Automatizados:
```
tests/
├── test_fase6_completo.py    # Testes de todas as funcionalidades
└── check_permissoes.py       # Verificação de permissões no BD
```

#### Resultados dos Testes (28/11/2025):
- ✅ Login válido/inválido
- ✅ Permissões por perfil (Admin: 58, Coord: 21, Prof: 17)
- ✅ Filtro de turmas (Admin: 37, Prof: 1)
- ✅ Coordenador somente leitura
- ✅ Admin acesso total
- ✅ Logout e troca de usuário

---

## 🔄 FASE 7: ATIVAÇÃO EM PRODUÇÃO (EM ANDAMENTO)

### Checklist de Ativação:
- [x] Backup completo do banco de dados
- [x] Flag `perfis_habilitados` = true
- [x] Usuários de teste funcionando
- [ ] Criar usuário administrador definitivo (seu usuário)
- [ ] Criar usuários para coordenadores reais
- [ ] Criar usuários para professores reais
- [ ] Testar em ambiente de produção
- [ ] Monitorar primeiros dias de uso
- [ ] Treinar usuários (se necessário)

---

## 🚧 FUNCIONALIDADES PENDENTES / FUTURAS

### 📌 Prioridade Alta - Implementar em Breve

#### 1. Integração com Lançamento de Notas
**Status**: 🔲 Não Iniciado  
**Arquivo**: `ui/lancamento_notas.py` (modificar)

```python
# TODO: Aplicar filtro de turmas para professor
# Professor só pode lançar notas nas suas turmas
# Coordenador pode visualizar mas não editar
```

**Tarefas**:
- [ ] Filtrar turmas por perfil no combo de seleção
- [ ] Bloquear edição para coordenador
- [ ] Aplicar decorator `@requer_permissao('notas.lancar_proprias')`

---

#### 2. Integração com Lançamento de Frequência
**Status**: 🔲 Não Iniciado  
**Arquivo**: `ui/lancamento_frequencia.py` (modificar)

```python
# TODO: Aplicar filtro de turmas para professor
# Professor só pode lançar frequência nas suas turmas
```

**Tarefas**:
- [ ] Filtrar turmas por perfil no combo de seleção
- [ ] Aplicar decorator `@requer_permissao('frequencia.lancar_proprias')`

---

#### 3. Dashboard Adaptado por Perfil
**Status**: 🔲 Não Iniciado  
**Arquivo**: `ui/dashboard.py` (criar/modificar)

```python
# TODO: Dashboard diferente para cada perfil
class DashboardManager:
    def carregar_dados(self, usuario):
        if usuario.is_professor():
            self._dashboard_professor()  # Apenas suas turmas
        elif usuario.is_coordenador():
            self._dashboard_pedagogico()  # Visão pedagógica
        else:
            self._dashboard_completo()   # Visão geral
```

**Tarefas**:
- [ ] Criar `_dashboard_professor()` - métricas das próprias turmas
- [ ] Criar `_dashboard_pedagogico()` - métricas pedagógicas
- [ ] Manter `_dashboard_completo()` - visão administrativa

---

#### 4. Troca de Senha pelo Próprio Usuário
**Status**: 🔲 Não Iniciado  
**Arquivo**: `ui/trocar_senha.py` (criar)

```python
# TODO: Interface para usuário trocar própria senha
class TrocarSenhaWindow:
    def __init__(self, usuario_logado):
        # Campos: senha atual, nova senha, confirmar
        pass
    
    def validar_e_trocar(self):
        # Usar AuthService.alterar_senha()
        pass
```

**Tarefas**:
- [ ] Criar interface Tkinter
- [ ] Validar senha atual antes de trocar
- [ ] Exigir troca no primeiro acesso (`primeiro_acesso = True`)
- [ ] Adicionar botão no menu do usuário

---

#### 5. Timeout de Sessão
**Status**: 🔲 Não Iniciado  
**Arquivo**: `auth/session_manager.py` (criar)

```python
# TODO: Deslogar usuário após período de inatividade
class SessionManager:
    TIMEOUT_MINUTOS = 30
    
    def verificar_timeout(self):
        # Comparar último_acesso com agora
        # Se > TIMEOUT_MINUTOS, fazer logout
        pass
```

**Tarefas**:
- [ ] Criar gerenciador de sessão
- [ ] Atualizar `ultimo_acesso` em cada ação
- [ ] Verificar timeout periodicamente (timer)
- [ ] Mostrar aviso antes de expirar

---

### 📌 Prioridade Média - Melhorias

#### 6. Relatórios Filtrados por Perfil
**Status**: 🔲 Não Iniciado

```python
# TODO: Relatórios respeitam perfil do usuário
# Professor: apenas relatórios das suas turmas
# Coordenador: relatórios pedagógicos
# Admin: todos os relatórios
```

**Arquivos a modificar**:
- [ ] `ui/relatorios.py`
- [ ] `gerar_lista_reuniao.py`
- [ ] `gerarPDF.py`
- [ ] Todos os geradores de relatório

---

#### 7. Histórico de Ações do Usuário
**Status**: 🔲 Não Iniciado  
**Arquivo**: `ui/historico_acoes.py` (criar)

```python
# TODO: Visualizar logs de ações por usuário
class HistoricoAcoesWindow:
    def __init__(self, admin_user):
        # TreeView com logs
        # Filtros: data, usuário, ação
        pass
```

**Tarefas**:
- [ ] Interface para visualizar `logs_acesso`
- [ ] Filtros por data, usuário, tipo de ação
- [ ] Exportar para Excel/PDF
- [ ] Restrito a administradores

---

#### 8. Permissões Personalizadas por Usuário
**Status**: 🔲 Não Iniciado  
**Arquivo**: `ui/gestao_usuarios.py` (expandir)

```python
# TODO: Permitir adicionar/remover permissões específicas
# Usa tabela usuario_permissoes (tipo: 'adicionar' ou 'remover')
```

**Tarefas**:
- [ ] Interface para selecionar permissões extras
- [ ] Usar tabela `usuario_permissoes`
- [ ] Tipo 'adicionar' para dar permissão extra
- [ ] Tipo 'remover' para retirar permissão do perfil

---

### 📌 Prioridade Baixa - Futuro

#### 9. Integração com Banco de Questões BNCC
**Status**: 🔲 Aguardando módulo de questões

```python
# Permissões já cadastradas:
# - questoes.criar
# - questoes.editar_proprias
# - questoes.editar_todas
# - questoes.aprovar
# - avaliacoes.criar
# - avaliacoes.aplicar
```

---

#### 10. Autenticação de Dois Fatores (2FA)
**Status**: 🔲 Futuro

```python
# TODO: Implementar 2FA opcional para admins
# - TOTP (Google Authenticator)
# - Email de confirmação
```

---

#### 11. Recuperação de Senha por Email
**Status**: 🔲 Futuro

```python
# TODO: Enviar link de recuperação por email
# Requer configuração de SMTP
```

---

## 📁 Estrutura de Arquivos Atual

```
gestao/
├── auth/                          # ✅ IMPLEMENTADO
│   ├── __init__.py
│   ├── auth_service.py            # Serviço de autenticação
│   ├── decorators.py              # Decorators de permissão
│   ├── models.py                  # Usuario, Perfil, Permissao
│   ├── password_utils.py          # Hash bcrypt
│   └── usuario_logado.py          # Singleton do usuário atual
│
├── services/
│   ├── perfil_filter_service.py   # ✅ Filtro central por perfil
│   ├── turma_service.py           # ✅ Modificado com filtro
│   └── logs_acesso_service.py     # ✅ Serviço de logs
│
├── ui/
│   ├── login.py                   # ✅ Tela de login
│   ├── gestao_usuarios.py         # ✅ CRUD de usuários
│   ├── button_factory.py          # ✅ Modificado com filtro
│   ├── trocar_senha.py            # 🔲 TODO: Criar
│   └── historico_acoes.py         # 🔲 TODO: Criar
│
├── db/migrations/
│   ├── criar_tabelas_perfis.sql   # ✅ Script SQL completo
│   └── criar_tabela_logs.sql      # ✅ Script SQL logs
│
├── tests/
│   ├── test_fase6_completo.py     # ✅ Testes automatizados
│   └── check_permissoes.py        # ✅ Verificação de permissões
│
├── feature_flags.json             # ✅ Flag de controle
├── config.py                      # ✅ perfis_habilitados()
└── main.py                        # ✅ Integrado com login
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabelas Implementadas:

```sql
-- ✅ usuarios
CREATE TABLE usuarios (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    funcionario_id BIGINT UNSIGNED NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    perfil ENUM('administrador', 'coordenador', 'professor') NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    primeiro_acesso BOOLEAN DEFAULT TRUE,
    tentativas_login INT DEFAULT 0,
    bloqueado_ate DATETIME NULL,
    ultimo_acesso DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ✅ permissoes (58 cadastradas)
CREATE TABLE permissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    descricao VARCHAR(200),
    modulo VARCHAR(50) NOT NULL
);

-- ✅ perfil_permissoes
CREATE TABLE perfil_permissoes (
    perfil ENUM('administrador', 'coordenador', 'professor') NOT NULL,
    permissao_id INT NOT NULL,
    PRIMARY KEY (perfil, permissao_id)
);

-- ✅ usuario_permissoes (para personalizações)
CREATE TABLE usuario_permissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT UNSIGNED NOT NULL,
    permissao_id INT NOT NULL,
    tipo ENUM('adicionar', 'remover') NOT NULL
);

-- ✅ logs_acesso
CREATE TABLE logs_acesso (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT UNSIGNED NULL,
    username_tentativa VARCHAR(50),
    acao VARCHAR(100) NOT NULL,
    detalhes TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📊 Permissões por Perfil

### Resumo:
| Perfil | Total de Permissões | Acesso a Turmas |
|--------|---------------------|-----------------|
| Administrador | 58 (todas) | Todas |
| Coordenador | 21 | Todas (visualização) |
| Professor | 17 | Apenas vinculadas |

### Permissões do Professor:
```
alunos.visualizar_proprios       - Visualizar alunos das próprias turmas
avaliacoes.aplicar              - Aplicar avaliações nas turmas
avaliacoes.criar                - Criar avaliações
bncc.visualizar                 - Visualizar habilidades BNCC
dashboard.proprio               - Visualizar dashboard das próprias turmas
dashboard.visualizar            - Visualizar dashboard
frequencia.lancar_proprias      - Lançar frequência nas próprias turmas
frequencia.visualizar_proprias  - Visualizar frequência das próprias turmas
notas.editar_proprias           - Editar notas das próprias turmas
notas.lancar_proprias           - Lançar notas nas próprias turmas
notas.visualizar_proprias       - Visualizar notas das próprias turmas
questoes.criar                  - Criar questões no banco
questoes.editar_proprias        - Editar apenas questões próprias
relatorios.boletins             - Gerar boletins de alunos
relatorios.gerar_proprios       - Gerar relatórios das próprias turmas
relatorios.visualizar           - Acessar módulo de relatórios
turmas.visualizar_proprias      - Visualizar apenas turmas próprias
```

---

## 🔄 Como Testar

### Script de alternância:
```bash
# Ver status atual
python testar_perfis.py

# Ativar para testar
python testar_perfis.py on

# Desativar
python testar_perfis.py off
```

### Executar testes automatizados:
```bash
cd c:\gestao
python tests\test_fase6_completo.py
```

---

## 📝 Notas de Implementação

### Correções Importantes Realizadas:
1. **`turma_service.py`**: Removidas colunas inexistentes (`s.ciclo`, `capacidade_maxima`, `professor_id`)
2. **`perfil_filter_service.py`**: Removida referência a `t.professor_id`, usa apenas `funcionario_disciplinas`
3. **`gestao_usuarios.py`**: Removido filtro por `f.status` (coluna não existe em `funcionarios`)
4. **`logs_acesso`**: Coluna `username_tentativa` para registrar tentativas de login inválidas

### Vinculação Professor-Turma:
O sistema usa a tabela `funcionario_disciplinas` para determinar quais turmas um professor pode acessar:
```sql
SELECT DISTINCT fd.turma_id 
FROM funcionario_disciplinas fd
WHERE fd.funcionario_id = ?
```

---

*Documento atualizado em: 28 de Novembro de 2025*  
*Sistema de Gestão Escolar - Desenvolvimento Voluntário*
