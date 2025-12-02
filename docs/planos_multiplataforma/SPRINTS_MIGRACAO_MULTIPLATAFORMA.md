# 🚀 Sprints de Migração Multiplataforma

## Sistema de Gestão Escolar - Roadmap de Desenvolvimento

**Versão:** 1.0  
**Data:** 02 de Dezembro de 2025  
**Estratégia:** Migração Progressiva com Funcionamento Paralelo

---

## 📋 Sumário Executivo

Este documento define as Sprints para migração do Sistema de Gestão Escolar para uma arquitetura multiplataforma moderna. A estratégia central é **manter o sistema atual (Python/Tkinter) funcionando normalmente** durante todo o processo de desenvolvimento, garantindo continuidade operacional para os usuários.

### Princípios Fundamentais

1. **Zero Downtime**: Sistema atual nunca será desligado até aprovação final
2. **Migração Gradual**: Módulos migrados um por vez com validação
3. **Rollback Sempre Disponível**: Possibilidade de voltar ao sistema antigo
4. **Desktop com Tauri**: Aplicação desktop moderna usando Tauri + React
5. **Reutilização de Código**: Services Python existentes serão reaproveitados

---

## 🎯 Visão Geral das Fases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CRONOGRAMA GERAL (24-28 Semanas)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FASE 1: API Backend           ████████████████░░░░░░░░░░░░░░░░ (8 semanas) │
│  Sistema Tkinter funcionando   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
│                                                                              │
│  FASE 2: Web App React         ░░░░░░░░████████████████░░░░░░░░ (8 semanas) │
│  Sistema Tkinter funcionando   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
│                                                                              │
│  FASE 3: Desktop Tauri         ░░░░░░░░░░░░░░░░████████████████ (8 semanas) │
│  Sistema Tkinter funcionando   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ │
│                                                                              │
│  FASE 4: Mobile + Integração   ░░░░░░░░░░░░░░░░░░░░░░░░████████ (4 semanas) │
│  Migração de usuários          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ → ░ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Legenda: ████ = Desenvolvimento ativo | ▓▓▓ = Sistema funcionando | ░░░ = Aguardando
```

---

## 📅 FASE 1: API Backend (8 Semanas)

### Objetivo
Criar a API FastAPI que servirá todas as plataformas, **reutilizando os services Python existentes**.

---

### Sprint 1.1 - Infraestrutura Base
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Configurar projeto FastAPI
- Estruturar arquitetura de diretórios
- Configurar banco de dados (SQLAlchemy async)
- Implementar autenticação JWT

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 1.1.1 | Criar projeto FastAPI com estrutura de diretórios | Alta | 4h |
| 1.1.2 | Configurar SQLAlchemy assíncrono com MySQL | Alta | 8h |
| 1.1.3 | Criar SQLAlchemy models baseados no BD atual | Alta | 16h |
| 1.1.4 | Configurar Alembic para migrations | Média | 4h |
| 1.1.5 | Migrar schemas Pydantic existentes (`models/`) | Alta | 8h |
| 1.1.6 | Implementar autenticação JWT completa | Alta | 16h |
| 1.1.7 | Configurar CORS, middleware de logging | Média | 4h |
| 1.1.8 | Configurar Docker e docker-compose | Média | 8h |
| 1.1.9 | Documentar APIs com Swagger/OpenAPI | Baixa | 4h |
| 1.1.10 | Criar testes de integração base | Alta | 8h |

#### Entregáveis
- [x] Projeto FastAPI rodando em Docker
- [x] Autenticação JWT funcional
- [x] Swagger UI acessível em `/docs`
- [x] Testes de autenticação passando

#### Dependências
- MySQL 8.0+ (já existente)
- Redis (novo)

---

### Sprint 1.2 - Endpoints CRUD Alunos e Funcionários
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Migrar `aluno_service.py` para API
- Migrar `funcionario_service.py` para API
- Garantir paridade de funcionalidades

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 1.2.1 | Adaptar `aluno_service.py` para async | Alta | 8h |
| 1.2.2 | Criar endpoints CRUD alunos | Alta | 12h |
| 1.2.3 | Implementar busca avançada de alunos | Alta | 8h |
| 1.2.4 | Adaptar `funcionario_service.py` para async | Alta | 8h |
| 1.2.5 | Criar endpoints CRUD funcionários | Alta | 12h |
| 1.2.6 | Implementar gestão de licenças | Média | 8h |
| 1.2.7 | Criar testes unitários services | Alta | 8h |
| 1.2.8 | Criar testes E2E endpoints | Alta | 8h |
| 1.2.9 | Documentar endpoints no Swagger | Média | 4h |
| 1.2.10 | Validar paridade com sistema atual | Alta | 4h |

#### Entregáveis
- [x] API de Alunos 100% funcional
- [x] API de Funcionários 100% funcional
- [x] Testes com cobertura > 80%
- [x] Documentação Swagger completa

#### Critérios de Aceite
```python
# Testar paridade de dados
async def test_paridade_alunos():
    # Dados via API
    api_alunos = await api.get("/alunos")
    # Dados via sistema atual
    tkinter_alunos = aluno_service.listar_alunos()
    # Verificar igualdade
    assert len(api_alunos) == len(tkinter_alunos)
```

---

### Sprint 1.3 - Endpoints Turmas, Matrículas e Notas
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Migrar módulos de Turmas e Matrículas
- Migrar módulo de Notas
- Implementar lançamento em lote

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 1.3.1 | Criar endpoints CRUD turmas | Alta | 8h |
| 1.3.2 | Criar endpoints CRUD séries | Alta | 4h |
| 1.3.3 | Criar endpoints CRUD escolas | Média | 4h |
| 1.3.4 | Criar endpoints matrículas | Alta | 12h |
| 1.3.5 | Implementar transferências via API | Alta | 8h |
| 1.3.6 | Criar endpoints CRUD notas | Alta | 8h |
| 1.3.7 | Implementar lançamento de notas em lote | Alta | 12h |
| 1.3.8 | Cálculo automático de médias | Alta | 8h |
| 1.3.9 | Testes de integração | Alta | 8h |
| 1.3.10 | Validação de regras de negócio | Alta | 8h |

#### Entregáveis
- [x] API de Turmas e Matrículas funcional
- [x] API de Notas com lançamento em lote
- [x] Transferências funcionando via API
- [x] Cálculos de médias corretos

---

### Sprint 1.4 - Dashboard, Relatórios e Finalização
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Criar endpoint de estatísticas para Dashboard
- Implementar geração de relatórios PDF
- Configurar cache Redis
- Configurar Celery para tasks assíncronas

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 1.4.1 | Migrar `estatistica_service.py` | Alta | 8h |
| 1.4.2 | Criar endpoint `/dashboard/stats` | Alta | 8h |
| 1.4.3 | Configurar Redis cache | Alta | 8h |
| 1.4.4 | Migrar `report_service.py` | Alta | 8h |
| 1.4.5 | Criar endpoints de relatórios | Alta | 12h |
| 1.4.6 | Configurar Celery para geração assíncrona | Média | 8h |
| 1.4.7 | Criar endpoint de frequência | Alta | 8h |
| 1.4.8 | Criar endpoint de backup | Alta | 8h |
| 1.4.9 | Testes de carga (k6/locust) | Alta | 8h |
| 1.4.10 | Deploy em ambiente staging | Alta | 4h |

#### Entregáveis
- [x] API completa e funcional
- [x] Dashboard com estatísticas em tempo real
- [x] Geração de relatórios PDF
- [x] Cache funcionando
- [x] Deploy em staging

#### Métricas de Performance
| Endpoint | Meta Latência | Meta Throughput |
|----------|---------------|-----------------|
| GET /alunos | < 100ms | 100 req/s |
| POST /notas/lote | < 500ms | 50 req/s |
| GET /dashboard/stats | < 200ms | 50 req/s |
| GET /relatorios/{id}/pdf | < 2s | 10 req/s |

---

## 📅 FASE 2: Web App React (8 Semanas)

### Objetivo
Criar aplicação Web completa em React/TypeScript, consumindo a API desenvolvida na Fase 1.

---

### Sprint 2.1 - Setup e Autenticação
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Configurar projeto React com Vite
- Implementar layout base
- Criar fluxo de autenticação

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 2.1.1 | Criar projeto Vite + React + TypeScript | Alta | 4h |
| 2.1.2 | Configurar Tailwind CSS + Shadcn/ui | Alta | 4h |
| 2.1.3 | Criar layout base (Header, Sidebar, Main) | Alta | 12h |
| 2.1.4 | Configurar React Router | Alta | 4h |
| 2.1.5 | Configurar TanStack Query | Alta | 4h |
| 2.1.6 | Configurar Zustand para estado global | Média | 4h |
| 2.1.7 | Criar cliente API (Axios) | Alta | 4h |
| 2.1.8 | Implementar tela de Login | Alta | 8h |
| 2.1.9 | Implementar AuthContext e proteção de rotas | Alta | 8h |
| 2.1.10 | Criar componentes comuns (Loading, Error, etc) | Alta | 8h |

#### Entregáveis
- [x] Projeto React configurado e rodando
- [x] Layout responsivo funcional
- [x] Login funcionando com JWT
- [x] Rotas protegidas

---

### Sprint 2.2 - Módulo Alunos
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Criar CRUD completo de alunos no frontend
- Implementar busca, filtros e paginação
- Formulários com validação

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 2.2.1 | Criar página de lista de alunos | Alta | 8h |
| 2.2.2 | Implementar DataTable com paginação | Alta | 8h |
| 2.2.3 | Implementar busca e filtros | Alta | 8h |
| 2.2.4 | Criar formulário de cadastro (React Hook Form + Zod) | Alta | 12h |
| 2.2.5 | Criar página de edição | Alta | 8h |
| 2.2.6 | Criar página de detalhes do aluno | Alta | 8h |
| 2.2.7 | Implementar exclusão com confirmação | Média | 4h |
| 2.2.8 | Adicionar foto do aluno | Média | 8h |
| 2.2.9 | Testes de componentes | Alta | 8h |
| 2.2.10 | Validar usabilidade | Média | 4h |

#### Entregáveis
- [x] Módulo Alunos 100% funcional
- [x] Formulários validados
- [x] UX equivalente ou melhor que Tkinter

---

### Sprint 2.3 - Módulos Funcionários, Turmas e Matrículas
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Criar módulo de Funcionários
- Criar módulo de Turmas
- Criar módulo de Matrículas

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 2.3.1 | CRUD Funcionários (lista, form, detalhes) | Alta | 16h |
| 2.3.2 | Gestão de licenças de funcionários | Média | 8h |
| 2.3.3 | CRUD Turmas (lista, form, detalhes) | Alta | 12h |
| 2.3.4 | Visualização de alunos por turma | Alta | 8h |
| 2.3.5 | Módulo de Matrículas | Alta | 12h |
| 2.3.6 | Processo de transferência | Alta | 8h |
| 2.3.7 | Relatório de alunos por turma | Média | 8h |
| 2.3.8 | Testes E2E | Alta | 8h |

#### Entregáveis
- [x] Módulo Funcionários completo
- [x] Módulo Turmas completo
- [x] Módulo Matrículas completo

---

### Sprint 2.4 - Notas, Frequência e Dashboard
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Criar módulo de Notas
- Criar módulo de Frequência
- Criar Dashboard com gráficos

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 2.4.1 | Interface de lançamento de notas | Alta | 12h |
| 2.4.2 | Lançamento em lote de notas | Alta | 8h |
| 2.4.3 | Visualização de boletim | Alta | 8h |
| 2.4.4 | Interface de lançamento de frequência | Alta | 12h |
| 2.4.5 | Resumo de frequência por turma | Média | 8h |
| 2.4.6 | Dashboard com cards de estatísticas | Alta | 8h |
| 2.4.7 | Gráficos interativos (Recharts) | Alta | 12h |
| 2.4.8 | Relatórios e geração de PDFs | Alta | 8h |
| 2.4.9 | Testes finais e polimento | Alta | 8h |
| 2.4.10 | Deploy em staging | Alta | 4h |

#### Entregáveis
- [x] Web App completo e funcional
- [x] Dashboard interativo
- [x] Todos os módulos funcionando
- [x] Deploy em staging para testes

---

## 📅 FASE 3: Desktop Tauri (8 Semanas) ⭐

### Objetivo
Criar aplicação Desktop moderna usando **Tauri + React**, substituindo a interface Tkinter atual, mas **mantendo os services Python como sidecar**.

---

### Sprint 3.1 - Setup Tauri e Integração Python
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Configurar projeto Tauri
- Configurar sidecar Python para reuso de services
- Criar comunicação IPC entre Tauri e Python

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 3.1.1 | Instalar Rust e Tauri CLI | Alta | 2h |
| 3.1.2 | Criar projeto Tauri com React + Vite | Alta | 4h |
| 3.1.3 | Configurar TypeScript e Tailwind | Alta | 4h |
| 3.1.4 | Copiar componentes do Web App | Alta | 8h |
| 3.1.5 | Estruturar sidecar Python | Alta | 8h |
| 3.1.6 | Copiar services existentes para sidecar | Alta | 4h |
| 3.1.7 | Implementar IPC handler em Python | Alta | 12h |
| 3.1.8 | Implementar commands em Rust | Alta | 12h |
| 3.1.9 | Testar comunicação Tauri ↔ Python | Alta | 8h |
| 3.1.10 | Configurar build do sidecar (PyInstaller) | Alta | 8h |

#### Arquitetura do Sidecar

```
┌──────────────────────────────────────────────────────────────┐
│                    TAURI APP (Rust + React)                   │
├──────────────────────────────────────────────────────────────┤
│  Frontend React (UI)  ←→  Tauri Commands (Rust)              │
└─────────────────────────────┬────────────────────────────────┘
                              │ IPC (stdin/stdout)
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    PYTHON SIDECAR                             │
├──────────────────────────────────────────────────────────────┤
│  • aluno_service.py (reutilizado)                            │
│  • funcionario_service.py (reutilizado)                      │
│  • estatistica_service.py (reutilizado)                      │
│  • report_service.py (reutilizado)                           │
│  • conexao.py (reutilizado)                                  │
└──────────────────────────────────────────────────────────────┘
```

#### Entregáveis
- [x] Projeto Tauri funcionando
- [x] Sidecar Python integrado
- [x] Comunicação IPC funcional
- [x] Services Python sendo chamados

---

### Sprint 3.2 - Migração de Funcionalidades Core
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Migrar módulos de Alunos e Funcionários
- Adaptar UI para desktop nativo
- Implementar recursos desktop (menu, atalhos)

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 3.2.1 | Criar TitleBar customizada | Alta | 8h |
| 3.2.2 | Implementar Sidebar navegação | Alta | 8h |
| 3.2.3 | Adaptar módulo Alunos para Tauri | Alta | 12h |
| 3.2.4 | Adaptar módulo Funcionários para Tauri | Alta | 12h |
| 3.2.5 | Adaptar módulo Turmas para Tauri | Alta | 8h |
| 3.2.6 | Implementar menu nativo (File, Edit, etc) | Média | 8h |
| 3.2.7 | Configurar atalhos globais (Ctrl+N, etc) | Média | 8h |
| 3.2.8 | Testes de funcionalidade | Alta | 8h |
| 3.2.9 | Comparar com sistema Tkinter atual | Alta | 4h |

#### Atalhos Implementados
| Atalho | Ação |
|--------|------|
| Ctrl+N | Novo Aluno |
| Ctrl+F | Buscar |
| Ctrl+D | Dashboard |
| Ctrl+B | Backup |
| F5 | Atualizar |
| F1 | Ajuda |

#### Entregáveis
- [x] Módulos core funcionando no Tauri
- [x] UI desktop nativa
- [x] Atalhos de teclado funcionando

---

### Sprint 3.3 - Notas, Frequência e Relatórios
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Migrar módulos de Notas e Frequência
- Implementar geração de relatórios PDF
- Integração com impressora

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 3.3.1 | Adaptar módulo Notas para Tauri | Alta | 12h |
| 3.3.2 | Adaptar módulo Frequência para Tauri | Alta | 12h |
| 3.3.3 | Implementar Dashboard com gráficos | Alta | 12h |
| 3.3.4 | Integrar geração de PDFs via sidecar | Alta | 8h |
| 3.3.5 | Visualizador de PDF integrado | Média | 8h |
| 3.3.6 | Integração com impressora nativa | Alta | 8h |
| 3.3.7 | Diálogos de arquivo nativos | Média | 4h |
| 3.3.8 | Testes de relatórios | Alta | 8h |

#### Entregáveis
- [x] Notas e Frequência funcionando
- [x] Relatórios PDF sendo gerados
- [x] Impressão funcionando

---

### Sprint 3.4 - Recursos Desktop e Distribuição
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Implementar recursos desktop avançados
- Configurar sistema de atualizações
- Preparar builds e instaladores

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 3.4.1 | Implementar System Tray | Média | 8h |
| 3.4.2 | Notificações nativas | Média | 8h |
| 3.4.3 | Backup automático local | Alta | 8h |
| 3.4.4 | Configurar Tauri Updater | Alta | 8h |
| 3.4.5 | Build para Windows (.msi) | Alta | 8h |
| 3.4.6 | Build para macOS (.dmg) | Média | 8h |
| 3.4.7 | Build para Linux (.deb, .AppImage) | Baixa | 8h |
| 3.4.8 | Configurar assinatura de código | Alta | 8h |
| 3.4.9 | Servidor de atualizações | Alta | 8h |
| 3.4.10 | Documentação de instalação | Média | 4h |

#### Comparativo: Tkinter vs Tauri

| Aspecto | Tkinter Atual | Tauri Novo |
|---------|---------------|------------|
| Tamanho instalador | ~200 MB | ~50 MB |
| Memória RAM | ~300 MB | ~100 MB |
| Tempo inicialização | 3-5s | < 1s |
| Interface | Básica | Moderna |
| Atualizações | Manual | Automático |
| Relatórios PDF | ✅ | ✅ (via sidecar) |

#### Entregáveis
- [x] Aplicação Tauri completa
- [x] Instaladores para Windows/macOS/Linux
- [x] Sistema de atualizações funcionando
- [x] Pronto para testes beta

---

## 📅 FASE 4: Mobile + Integração Final (4 Semanas)

### Sprint 4.1 - App Mobile React Native
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando normalmente

#### Objetivos
- Criar app mobile básico com React Native/Expo
- Foco em lançamento de frequência e consultas
- Funcionalidade offline

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 4.1.1 | Criar projeto Expo + TypeScript | Alta | 4h |
| 4.1.2 | Configurar navegação (Expo Router) | Alta | 8h |
| 4.1.3 | Implementar autenticação + biometria | Alta | 8h |
| 4.1.4 | Criar Dashboard resumido | Alta | 8h |
| 4.1.5 | Lançamento de frequência mobile | Alta | 16h |
| 4.1.6 | Consulta de alunos | Alta | 8h |
| 4.1.7 | Modo offline com sync | Alta | 16h |
| 4.1.8 | Push notifications | Média | 8h |
| 4.1.9 | Testes em dispositivos | Alta | 8h |
| 4.1.10 | Build para TestFlight/Play Store | Alta | 8h |

#### Entregáveis
- [x] App mobile funcional
- [x] Frequência pode ser lançada pelo celular
- [x] Funciona offline
- [x] Disponível para testes

---

### Sprint 4.2 - Migração e Go-Live
**Duração:** 2 semanas  
**Status do Sistema Atual:** ✅ Funcionando em PARALELO

#### Objetivos
- Migrar usuários gradualmente
- Treinamento da equipe
- Desativar sistema Tkinter

#### Tarefas

| # | Tarefa | Prioridade | Estimativa |
|---|--------|------------|------------|
| 4.2.1 | Validação final de paridade | Alta | 16h |
| 4.2.2 | Preparar documentação de usuário | Alta | 8h |
| 4.2.3 | Treinamento secretaria | Alta | 8h |
| 4.2.4 | Treinamento professores (mobile) | Alta | 8h |
| 4.2.5 | Migração piloto (1 escola) | Alta | 16h |
| 4.2.6 | Correção de bugs encontrados | Alta | 16h |
| 4.2.7 | Rollout para demais escolas | Alta | 8h |
| 4.2.8 | Monitoramento pós-deploy | Alta | 8h |
| 4.2.9 | Depreciar sistema Tkinter | Média | 4h |
| 4.2.10 | Documentação final | Média | 8h |

#### Cronograma de Migração

```
Semana 1:
├── Dia 1-2: Validação final
├── Dia 3: Treinamento secretaria
├── Dia 4-5: Piloto escola #1

Semana 2:
├── Dia 1-2: Ajustes baseados no piloto
├── Dia 3-4: Rollout demais escolas
├── Dia 5: Sistema Tkinter em modo somente-leitura

Semana 3+ (pós-projeto):
└── Sistema Tkinter pode ser desativado
```

#### Entregáveis
- [x] Todas as escolas usando novo sistema
- [x] Mobile funcionando para professores
- [x] Sistema Tkinter desativado
- [x] Documentação completa

---

## 📊 Resumo de Sprints

| Sprint | Fase | Duração | Foco Principal | Sistema Atual |
|--------|------|---------|----------------|---------------|
| 1.1 | Backend | 2 sem | Infraestrutura API | ✅ Funcionando |
| 1.2 | Backend | 2 sem | CRUD Alunos/Func | ✅ Funcionando |
| 1.3 | Backend | 2 sem | Turmas/Notas | ✅ Funcionando |
| 1.4 | Backend | 2 sem | Dashboard/Relatórios | ✅ Funcionando |
| 2.1 | Web | 2 sem | Setup React | ✅ Funcionando |
| 2.2 | Web | 2 sem | Módulo Alunos | ✅ Funcionando |
| 2.3 | Web | 2 sem | Func/Turmas/Matrículas | ✅ Funcionando |
| 2.4 | Web | 2 sem | Notas/Frequência/Dash | ✅ Funcionando |
| 3.1 | Tauri | 2 sem | Setup + Sidecar Python | ✅ Funcionando |
| 3.2 | Tauri | 2 sem | Módulos Core | ✅ Funcionando |
| 3.3 | Tauri | 2 sem | Notas/Freq/Relatórios | ✅ Funcionando |
| 3.4 | Tauri | 2 sem | Recursos Desktop/Build | ✅ Funcionando |
| 4.1 | Mobile | 2 sem | App React Native | ✅ Funcionando |
| 4.2 | Integração | 2 sem | Migração/Go-Live | ⚠️ Paralelo → Desativado |

**Total: 28 semanas (~7 meses)**

---

## 💰 Estimativa de Custos por Sprint

| Fase | Sprints | Custo Estimado |
|------|---------|----------------|
| Backend (API) | 4 | R$ 30.000 - 45.000 |
| Web (React) | 4 | R$ 35.000 - 50.000 |
| Desktop (Tauri) | 4 | R$ 40.000 - 55.000 |
| Mobile | 2 | R$ 20.000 - 30.000 |
| **TOTAL** | **14** | **R$ 125.000 - 180.000** |

### Custos de Infraestrutura (mensal após go-live)

| Item | Custo/mês |
|------|-----------|
| VPS API | R$ 200-400 |
| MySQL Gerenciado | R$ 150-300 |
| Redis | R$ 50-100 |
| CDN/Storage | R$ 100-200 |
| **Total Mensal** | **R$ 500-1.000** |

---

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Atraso no desenvolvimento | Média | Alto | Buffer de 20% em cada sprint |
| Bugs críticos em produção | Média | Alto | Sistema antigo disponível para rollback |
| Resistência dos usuários | Alta | Médio | Treinamento intensivo, interface similar |
| Problemas de performance | Média | Alto | Testes de carga desde Sprint 1.4 |
| Integração Python/Tauri | Média | Alto | PoC na Sprint 3.1 |

---

## ✅ Definição de Pronto (DoD)

Para cada Sprint ser considerada completa:

- [ ] Código revisado e aprovado
- [ ] Testes automatizados passando (> 80% cobertura)
- [ ] Documentação atualizada
- [ ] Deploy em staging funcionando
- [ ] Validação com stakeholders
- [ ] Sem bugs críticos conhecidos
- [ ] Performance dentro das metas
- [ ] **Sistema Tkinter atual continua funcionando**

---

## 📚 Referências

- [PLANO_GERAL_MULTIPLATAFORMA.md](./PLANO_GERAL_MULTIPLATAFORMA.md)
- [PLANO_API_BACKEND.md](./PLANO_API_BACKEND.md)
- [PLANO_WEB_REACT.md](./PLANO_WEB_REACT.md)
- [PLANO_DESKTOP_TAURI.md](./PLANO_DESKTOP_TAURI.md)
- [PLANO_MOBILE_REACT_NATIVE.md](./PLANO_MOBILE_REACT_NATIVE.md)

---

*Documento criado em: 02 de Dezembro de 2025*  
*Versão: 1.0*
