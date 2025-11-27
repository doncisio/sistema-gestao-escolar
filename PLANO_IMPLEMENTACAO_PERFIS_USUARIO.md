# 📋 Plano de Implementação de Perfis de Usuário

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
    "PERFIS_HABILITADOS": false,
    "BANCO_QUESTOES_HABILITADO": false,
    "DASHBOARD_BNCC_HABILITADO": false
}
```

### Implementação no código
```python
# config.py ou feature_flags.py
import json
from pathlib import Path

def carregar_feature_flags():
    arquivo = Path(__file__).parent / 'feature_flags.json'
    if arquivo.exists():
        with open(arquivo, 'r') as f:
            return json.load(f)
    return {"PERFIS_HABILITADOS": False}

FLAGS = carregar_feature_flags()

def perfis_habilitados() -> bool:
    return FLAGS.get("PERFIS_HABILITADOS", False)
```

### Uso no main.py (após implementação completa)
```python
from feature_flags import perfis_habilitados

def main():
    if perfis_habilitados():
        # Novo fluxo: exige login
        login_window = LoginWindow()
        usuario = login_window.mostrar()
        if not usuario:
            return
        app = Application(usuario=usuario)
    else:
        # Fluxo atual: abre direto (você continua usando assim)
        app = Application()
    
    app.run()
```

### Benefícios desta abordagem
- ✅ **Zero interrupção**: Sistema funciona 100% durante desenvolvimento
- ✅ **Testes seguros**: Pode testar login/perfis sem afetar uso diário
- ✅ **Rollback fácil**: Se algo der errado, basta desativar a flag
- ✅ **Ativação controlada**: Você decide quando ativar cada recurso
- ✅ **Desenvolvimento incremental**: Implementa aos poucos sem pressa

---

## 📊 Situação Atual

### Como o sistema funciona hoje:
- **Perfil único**: O sistema atualmente opera como um aplicativo desktop monousuário
- **Sem autenticação**: Não há tela de login ou verificação de credenciais
- **Acesso total**: Todas as funcionalidades estão disponíveis para qualquer usuário
- **Tabela `funcionarios`**: Contém campo `cargo` que identifica a função do profissional
- **Cargos existentes**: Administrador do Sistema, Gestor Escolar, Professor@, Especialista (Coordenadora), etc.

### Estrutura de cargos atual (banco de dados):
```
- Administrador do Sistemas
- Gestor Escolar
- Professor@
- Auxiliar administrativo
- Agente de Portaria
- Merendeiro
- Auxiliar de serviços gerais
- Técnico em Administração Escolar
- Especialista (Coordenadora)
- Tutor/Cuidador
- Vigia Noturno
- Interprete de Libras
```

---

## 🎭 Perfis de Usuário Propostos

### 1. **Administrador/Secretário** (Acesso Total)
**Funções atuais do sistema que permanecem:**
- ✅ Cadastro, edição e exclusão de alunos
- ✅ Cadastro, edição e exclusão de funcionários
- ✅ Gestão de turmas e matrículas
- ✅ Geração de documentos (declarações, históricos, boletins)
- ✅ Relatórios administrativos
- ✅ Backup e manutenção do sistema
- ✅ Transição de ano letivo
- ✅ Configurações gerais

### 2. **Coordenador Pedagógico** (Acesso Pedagógico)
**Funções propostas:**
- ✅ Visualizar todos os alunos e turmas
- ✅ Visualizar funcionários (sem edição)
- ✅ Dashboard pedagógico completo
- ✅ Relatórios de desempenho por turma/aluno
- ✅ Relatórios de frequência
- ✅ Relatórios por habilidades BNCC (quando implementado)
- ✅ Visualizar e gerar atas de resultados
- ✅ Acompanhar lançamento de notas dos professores
- ❌ Cadastrar/editar/excluir alunos
- ❌ Cadastrar/editar funcionários
- ❌ Transição de ano letivo
- ❌ Backup do sistema

### 3. **Professor** (Acesso Restrito)
**Funções propostas:**
- ✅ Visualizar **apenas suas turmas** vinculadas
- ✅ Visualizar alunos das suas turmas
- ✅ Lançar/editar notas e frequência (suas turmas)
- ✅ Gerar boletins dos seus alunos
- ✅ Relatórios das suas turmas
- ✅ Cadastrar questões no banco (quando implementado)
- ✅ Gerar avaliações (quando implementado)
- ❌ Ver outras turmas/professores
- ❌ Funções administrativas
- ❌ Cadastrar alunos/funcionários
- ❌ Relatórios de outras turmas

---

## 🛠️ Etapas de Implementação

### **FASE 1: Infraestrutura de Autenticação** (Prioridade Alta)
*Estimativa: 2-3 dias*

#### Etapa 1.1: Criar tabela de usuários
```sql
CREATE TABLE usuarios (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    funcionario_id BIGINT UNSIGNED NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    perfil ENUM('administrador', 'coordenador', 'professor') NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_acesso DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id),
    INDEX idx_username (username),
    INDEX idx_perfil (perfil)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### Etapa 1.2: Criar tabela de permissões
```sql
CREATE TABLE permissoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    descricao VARCHAR(200),
    modulo VARCHAR(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE perfil_permissoes (
    perfil ENUM('administrador', 'coordenador', 'professor') NOT NULL,
    permissao_id INT NOT NULL,
    PRIMARY KEY (perfil, permissao_id),
    FOREIGN KEY (permissao_id) REFERENCES permissoes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### Etapa 1.3: Inserir permissões base
```sql
INSERT INTO permissoes (codigo, descricao, modulo) VALUES
-- Módulo Alunos
('alunos.visualizar', 'Visualizar lista de alunos', 'alunos'),
('alunos.criar', 'Cadastrar novos alunos', 'alunos'),
('alunos.editar', 'Editar dados de alunos', 'alunos'),
('alunos.excluir', 'Excluir alunos', 'alunos'),
('alunos.documentos', 'Gerar documentos de alunos', 'alunos'),

-- Módulo Funcionários
('funcionarios.visualizar', 'Visualizar funcionários', 'funcionarios'),
('funcionarios.criar', 'Cadastrar funcionários', 'funcionarios'),
('funcionarios.editar', 'Editar funcionários', 'funcionarios'),
('funcionarios.excluir', 'Excluir funcionários', 'funcionarios'),

-- Módulo Turmas
('turmas.visualizar', 'Visualizar turmas', 'turmas'),
('turmas.visualizar_proprias', 'Visualizar apenas turmas próprias', 'turmas'),
('turmas.gerenciar', 'Gerenciar turmas', 'turmas'),

-- Módulo Notas
('notas.visualizar', 'Visualizar notas', 'notas'),
('notas.lancar', 'Lançar notas', 'notas'),
('notas.lancar_proprias', 'Lançar notas apenas das próprias turmas', 'notas'),
('notas.editar_todas', 'Editar notas de qualquer turma', 'notas'),

-- Módulo Frequência
('frequencia.visualizar', 'Visualizar frequência', 'frequencia'),
('frequencia.lancar', 'Lançar frequência', 'frequencia'),
('frequencia.lancar_proprias', 'Lançar frequência apenas das próprias turmas', 'frequencia'),

-- Módulo Relatórios
('relatorios.visualizar', 'Visualizar relatórios', 'relatorios'),
('relatorios.gerar_todos', 'Gerar relatórios de toda escola', 'relatorios'),
('relatorios.gerar_proprios', 'Gerar relatórios apenas das próprias turmas', 'relatorios'),

-- Módulo Sistema
('sistema.backup', 'Realizar backup', 'sistema'),
('sistema.transicao_ano', 'Executar transição de ano letivo', 'sistema'),
('sistema.configuracoes', 'Acessar configurações', 'sistema'),
('sistema.usuarios', 'Gerenciar usuários', 'sistema'),

-- Módulo Dashboard
('dashboard.completo', 'Visualizar dashboard completo', 'dashboard'),
('dashboard.pedagogico', 'Visualizar dashboard pedagógico', 'dashboard'),
('dashboard.proprio', 'Visualizar dashboard das próprias turmas', 'dashboard');
```

#### Etapa 1.4: Criar módulo de autenticação
**Arquivo:** `auth/auth_service.py`
```python
# Estrutura proposta
class AuthService:
    @staticmethod
    def hash_senha(senha: str) -> str: ...
    
    @staticmethod
    def verificar_senha(senha: str, hash: str) -> bool: ...
    
    @staticmethod
    def login(username: str, senha: str) -> Optional[Usuario]: ...
    
    @staticmethod
    def tem_permissao(usuario: Usuario, permissao: str) -> bool: ...
    
    @staticmethod
    def logout(): ...
```

**Arquivo:** `auth/usuario_logado.py`
```python
# Singleton para armazenar usuário da sessão atual
class UsuarioLogado:
    _instance = None
    usuario: Optional[Usuario] = None
    permissoes: List[str] = []
    
    @classmethod
    def get_instance(cls): ...
    
    @classmethod
    def set_usuario(cls, usuario): ...
    
    @classmethod
    def tem_permissao(cls, permissao: str) -> bool: ...
```

---

### **FASE 2: Tela de Login** (Prioridade Alta)
*Estimativa: 1-2 dias*

#### Etapa 2.1: Criar interface de login
**Arquivo:** `ui/login.py`
```python
class LoginWindow:
    """Janela de login do sistema"""
    
    def __init__(self):
        self.janela = Tk()
        self.janela.title("Login - Sistema de Gestão Escolar")
        # ... interface com campos usuário e senha
    
    def validar_login(self): ...
    def on_login_sucesso(self, usuario): ...
    def mostrar_erro(self, mensagem): ...
```

#### Etapa 2.2: Modificar ponto de entrada (main.py)
```python
def main():
    # Mostrar tela de login primeiro
    login_window = LoginWindow()
    usuario = login_window.mostrar()
    
    if usuario:
        # Armazenar usuário logado
        UsuarioLogado.set_usuario(usuario)
        
        # Iniciar aplicação principal
        app = Application(usuario=usuario)
        app.run()
```

---

### **FASE 3: Controle de Acesso na Interface** (Prioridade Alta)
*Estimativa: 3-4 dias*

#### Etapa 3.1: Criar decorator de permissão
**Arquivo:** `auth/decorators.py`
```python
def requer_permissao(permissao: str):
    """Decorator para verificar permissão antes de executar função"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not UsuarioLogado.tem_permissao(permissao):
                messagebox.showerror(
                    "Acesso Negado",
                    f"Você não tem permissão para esta ação.\n"
                    f"Permissão necessária: {permissao}"
                )
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

#### Etapa 3.2: Modificar MenuManager para filtrar menus
**Arquivo:** `ui/menu.py` (modificação)
```python
class MenuManager:
    def criar_menu_principal(self, perfil: str):
        """Cria menu baseado no perfil do usuário"""
        
        if perfil == 'administrador':
            self._criar_menu_completo()
        elif perfil == 'coordenador':
            self._criar_menu_coordenador()
        elif perfil == 'professor':
            self._criar_menu_professor()
```

#### Etapa 3.3: Modificar ButtonFactory para filtrar botões
**Arquivo:** `ui/button_factory.py` (modificação)
```python
class ButtonFactory:
    def criar_botoes(self, usuario: Usuario):
        """Cria botões baseados nas permissões do usuário"""
        botoes = []
        
        if UsuarioLogado.tem_permissao('alunos.criar'):
            botoes.append(self._btn_novo_aluno())
        
        if UsuarioLogado.tem_permissao('funcionarios.criar'):
            botoes.append(self._btn_novo_funcionario())
        
        # ... continua para cada botão
```

#### Etapa 3.4: Aplicar decorators nas funções de ação
**Arquivo:** `ui/action_callbacks.py` (modificação)
```python
class ActionCallbacksManager:
    
    @requer_permissao('alunos.criar')
    def novo_aluno(self):
        """Cadastrar novo aluno"""
        ...
    
    @requer_permissao('alunos.editar')
    def editar_aluno(self):
        """Editar aluno selecionado"""
        ...
    
    @requer_permissao('sistema.transicao_ano')
    def abrir_transicao_ano(self):
        """Abre interface de transição de ano letivo"""
        ...
```

---

### **FASE 4: Filtro de Dados por Perfil** (Prioridade Média)
*Estimativa: 2-3 dias*

#### Etapa 4.1: Professor vê apenas suas turmas
**Modificar:** `db/queries.py`
```python
def get_turmas_usuario(usuario_id: int, perfil: str) -> List[Dict]:
    """Retorna turmas baseado no perfil"""
    if perfil == 'professor':
        # Apenas turmas vinculadas ao professor
        return query_turmas_professor(usuario_id)
    else:
        # Todas as turmas
        return query_todas_turmas()
```

#### Etapa 4.2: Filtrar alunos por turmas do professor
**Modificar:** `services/aluno_service.py`
```python
def listar_alunos(usuario: Usuario) -> List[Dict]:
    """Lista alunos baseado no perfil do usuário"""
    if usuario.perfil == 'professor':
        turmas_professor = get_turmas_professor(usuario.funcionario_id)
        return query_alunos_por_turmas(turmas_professor)
    else:
        return query_todos_alunos()
```

#### Etapa 4.3: Adaptar dashboard por perfil
**Modificar:** `ui/dashboard.py`
```python
class DashboardManager:
    def carregar_dados(self, usuario: Usuario):
        if usuario.perfil == 'professor':
            self._carregar_dashboard_professor(usuario.funcionario_id)
        elif usuario.perfil == 'coordenador':
            self._carregar_dashboard_coordenador()
        else:
            self._carregar_dashboard_completo()
```

---

### **FASE 5: Interface de Gestão de Usuários** (Prioridade Média)
*Estimativa: 2-3 dias*

#### Etapa 5.1: Criar tela de cadastro de usuários
**Arquivo:** `ui/gestao_usuarios.py`
```python
class InterfaceGestaoUsuarios:
    """Interface para administradores gerenciarem usuários do sistema"""
    
    def __init__(self, root):
        self.root = root
        # Lista de funcionários
        # Formulário para criar usuário
        # Opções de perfil
        # Botões: Criar, Editar, Desativar, Resetar Senha
```

#### Etapa 5.2: CRUD de usuários
- Criar usuário (vincular a funcionário existente)
- Editar perfil/permissões
- Desativar/ativar usuário
- Resetar senha

#### Etapa 5.3: Logs de acesso
```sql
CREATE TABLE logs_acesso (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id BIGINT UNSIGNED NOT NULL,
    acao VARCHAR(100) NOT NULL,
    detalhes TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

---

### **FASE 6: Testes e Ajustes** (Prioridade Alta)
*Estimativa: 2-3 dias*

#### Etapa 6.1: Criar usuários de teste
- 1 Administrador
- 1 Coordenador
- 2 Professores (com turmas diferentes)

#### Etapa 6.2: Testar cenários
- [ ] Login com credenciais válidas/inválidas
- [ ] Acesso a funções permitidas/bloqueadas por perfil
- [ ] Professor vê apenas suas turmas
- [ ] Coordenador vê todas turmas mas não edita alunos
- [ ] Administrador tem acesso total
- [ ] Logout e troca de usuário

#### Etapa 6.3: Documentar
- Manual do usuário por perfil
- Documentação técnica das APIs de autenticação

---

## 📁 Estrutura de Arquivos Proposta

```
gestao/
├── auth/                          # NOVO - Módulo de autenticação
│   ├── __init__.py
│   ├── auth_service.py            # Serviço de autenticação
│   ├── decorators.py              # Decorators de permissão
│   ├── usuario_logado.py          # Singleton do usuário atual
│   └── models.py                  # Models de Usuario/Permissao
│
├── ui/
│   ├── login.py                   # NOVO - Tela de login
│   ├── gestao_usuarios.py         # NOVO - CRUD de usuários
│   ├── app.py                     # MODIFICAR - Receber usuario
│   ├── menu.py                    # MODIFICAR - Filtrar por perfil
│   ├── button_factory.py          # MODIFICAR - Filtrar por permissão
│   └── action_callbacks.py        # MODIFICAR - Aplicar decorators
│
├── db/
│   └── migrations/                # NOVO - Migrações SQL
│       ├── 001_criar_usuarios.sql
│       ├── 002_criar_permissoes.sql
│       └── 003_criar_logs_acesso.sql
│
├── main.py                        # MODIFICAR - Login antes da app
└── ...
```

---

## ⏱️ Cronograma Estimado

| Fase | Descrição | Duração | Dependências |
|------|-----------|---------|--------------|
| 1 | Infraestrutura de Autenticação | 2-3 dias | - |
| 2 | Tela de Login | 1-2 dias | Fase 1 |
| 3 | Controle de Acesso na Interface | 3-4 dias | Fase 2 |
| 4 | Filtro de Dados por Perfil | 2-3 dias | Fase 3 |
| 5 | Interface de Gestão de Usuários | 2-3 dias | Fase 3 |
| 6 | Testes e Ajustes | 2-3 dias | Todas |

**Total estimado: 12-18 dias úteis**

---

## ⚠️ Considerações Importantes

### Segurança
1. **Senhas**: Usar bcrypt ou argon2 para hash de senhas
2. **Sessão**: Implementar timeout de sessão
3. **Logs**: Registrar todas as ações críticas
4. **Backup**: Incluir tabelas de usuários no backup

### Migração
1. **Usuário inicial**: Criar pelo menos 1 admin no primeiro deploy
2. **Funcionários existentes**: Não criar usuários automaticamente
3. **Compatibilidade**: Manter sistema funcionando sem login durante transição (feature flag)

### UX
1. **Mensagens claras**: Informar quando ação está bloqueada e por quê
2. **Interface adaptada**: Não mostrar botões/menus que usuário não pode usar
3. **Perfil visível**: Mostrar nome e perfil do usuário logado na interface

---

## 🔗 Integração com Banco de Questões BNCC

Quando o módulo de Banco de Questões for implementado, os perfis terão:

### Professor
- ✅ Criar questões próprias
- ✅ Editar questões próprias
- ✅ Visualizar questões públicas/escola
- ✅ Gerar avaliações para suas turmas
- ✅ Lançar resultados das suas avaliações

### Coordenador
- ✅ Revisar e aprovar questões
- ✅ Visualizar todas as questões
- ✅ Relatórios de desempenho por habilidade
- ✅ Dashboard pedagógico BNCC
- ❌ Criar questões (opcional)

### Administrador
- ✅ Tudo acima
- ✅ Gerenciar visibilidade de questões
- ✅ Importar/exportar banco de questões
- ✅ Configurar parâmetros do módulo

---

## ✅ Checklist de Implementação

### Fase 0 - Preparação (Feature Flag)
- [ ] Atualizar `feature_flags.json` com `PERFIS_HABILITADOS: false`
- [ ] Criar função `perfis_habilitados()` em `config.py`
- [ ] Garantir que sistema abre normalmente com flag desativada

### Fase 1 - Infraestrutura
- [ ] Criar script SQL das tabelas de usuários
- [ ] Criar script SQL das tabelas de permissões
- [ ] Inserir permissões base
- [ ] Criar módulo `auth/`
- [ ] Implementar `AuthService`
- [ ] Implementar `UsuarioLogado`
- [ ] Criar testes unitários básicos
- [ ] **Verificar**: Sistema continua funcionando normalmente? ✓

### Fase 2 - Login
- [ ] Criar `ui/login.py`
- [ ] Design da interface de login
- [ ] Integrar com `AuthService`
- [ ] Modificar `main.py` (com verificação de feature flag)
- [ ] Testar fluxo de login (ativando flag temporariamente)
- [ ] **Verificar**: Sistema continua funcionando normalmente? ✓

### Fase 3 - Controle de Acesso
- [ ] Criar decorator `@requer_permissao`
- [ ] Aplicar em `action_callbacks.py` (com bypass quando flag desativada)
- [ ] Modificar `MenuManager` (com bypass quando flag desativada)
- [ ] Modificar `ButtonFactory` (com bypass quando flag desativada)
- [ ] Testar bloqueios (ativando flag temporariamente)
- [ ] **Verificar**: Sistema continua funcionando normalmente? ✓

### Fase 4 - Filtro de Dados
- [ ] Modificar queries de turmas (com bypass quando flag desativada)
- [ ] Modificar queries de alunos (com bypass quando flag desativada)
- [ ] Adaptar dashboard (com bypass quando flag desativada)
- [ ] Testar visualização por perfil
- [ ] **Verificar**: Sistema continua funcionando normalmente? ✓

### Fase 5 - Gestão de Usuários
- [ ] Criar interface de gestão
- [ ] Implementar CRUD
- [ ] Implementar logs de acesso
- [ ] Testar funcionalidades admin
- [ ] **Verificar**: Sistema continua funcionando normalmente? ✓

### Fase 6 - Testes Finais (com Feature Flag ATIVADA)
- [ ] Criar usuários de teste (Admin, Coordenador, Professor)
- [ ] Ativar flag `PERFIS_HABILITADOS = true`
- [ ] Testar login com cada perfil
- [ ] Testar todas as restrições de acesso
- [ ] Testar fluxos completos de cada perfil
- [ ] Documentar comportamentos

### Fase 7 - Ativação em Produção
- [ ] Backup completo do banco de dados
- [ ] Criar usuário administrador definitivo (seu usuário)
- [ ] Criar usuários para coordenadores e professores
- [ ] Ativar flag permanentemente
- [ ] Monitorar primeiros dias de uso
- [ ] Treinar usuários (se necessário)

---

## 🔄 Como Testar Durante o Desenvolvimento

### Teste rápido de perfis (sem afetar uso diário)

```python
# No terminal Python ou em um script de teste:
import json

# Ativar temporariamente para testar
with open('feature_flags.json', 'w') as f:
    json.dump({"PERFIS_HABILITADOS": True}, f)

# Executar testes...

# Desativar para voltar ao normal
with open('feature_flags.json', 'w') as f:
    json.dump({"PERFIS_HABILITADOS": False}, f)
```

### Script auxiliar: `testar_perfis.py`
```python
"""Script para alternar feature flag de perfis"""
import json
import sys

ARQUIVO = 'feature_flags.json'

def ler_flags():
    try:
        with open(ARQUIVO, 'r') as f:
            return json.load(f)
    except:
        return {}

def salvar_flags(flags):
    with open(ARQUIVO, 'w') as f:
        json.dump(flags, f, indent=4)

if __name__ == '__main__':
    flags = ler_flags()
    atual = flags.get('PERFIS_HABILITADOS', False)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'on':
            flags['PERFIS_HABILITADOS'] = True
            print("✅ Perfis ATIVADOS - Sistema vai exigir login")
        elif sys.argv[1] == 'off':
            flags['PERFIS_HABILITADOS'] = False
            print("⭕ Perfis DESATIVADOS - Sistema abre direto")
        salvar_flags(flags)
    else:
        status = "ATIVADO ✅" if atual else "DESATIVADO ⭕"
        print(f"Status atual: {status}")
        print("Uso: python testar_perfis.py [on|off]")
```

### Uso no dia a dia
```bash
# Ver status atual
python testar_perfis.py

# Ativar para testar novos recursos
python testar_perfis.py on

# Desativar para usar sistema normalmente
python testar_perfis.py off
```

---

## 📝 Notas Finais

Este plano foi desenhado para permitir **desenvolvimento contínuo sem interrupção do uso diário** do sistema.

### Regras de ouro durante o desenvolvimento:
1. **Sempre** mantenha `PERFIS_HABILITADOS = false` como padrão
2. **Teste** novas funcionalidades ativando a flag temporariamente
3. **Desative** a flag após cada sessão de testes
4. **Só ative** permanentemente quando TUDO estiver testado e aprovado

### Recomendação de implementação:
1. Comece pela **Fase 0 e 1** (infraestrutura)
2. Implemente **Fase 2** (login) e teste isoladamente
3. Vá adicionando **Fases 3-5** gradualmente
4. Faça **Fase 6** (testes completos) com calma
5. Só execute **Fase 7** (ativação) quando tiver confiança total

---

*Documento criado em: Novembro de 2025*  
*Sistema de Gestão Escolar - Desenvolvimento Voluntário*
