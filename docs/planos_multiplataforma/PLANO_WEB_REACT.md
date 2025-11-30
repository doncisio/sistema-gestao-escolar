# 🌐 Plano de Migração para Plataforma Web (React/TypeScript)

## Visão Geral

Este documento detalha o plano completo para migração do Sistema de Gestão Escolar atual (Python/Tkinter) para uma aplicação web moderna utilizando **React** com **TypeScript** no frontend e **FastAPI** (Python) no backend.

---

## 📊 Análise do Sistema Atual

### Stack Atual
- **Frontend**: Tkinter (Python)
- **Backend**: Python (lógica embutida na UI)
- **Banco de Dados**: MySQL 8.0+
- **Arquitetura**: MVC com Service Layer

### Pontos Fortes a Preservar
1. ✅ Arquitetura em camadas bem definida
2. ✅ Service Layer já implementado (`services/`)
3. ✅ Modelos Pydantic para validação (`models/`)
4. ✅ Pool de conexões MySQL (`conexao.py`)
5. ✅ Sistema de cache inteligente
6. ✅ Feature flags configuráveis
7. ✅ Logs estruturados

### Funcionalidades a Migrar
- Gestão de Alunos (CRUD completo)
- Gestão de Funcionários
- Matrículas e Turmas
- Sistema de Notas e Frequência
- Dashboard com Estatísticas
- Geração de Relatórios PDF
- Sistema de Autenticação
- Backup do Banco de Dados

---

## 🏗️ Arquitetura Proposta

### Diagrama de Arquitetura Web

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React/TypeScript)                  │
├─────────────────────────────────────────────────────────────────────┤
│  React 18 │ TypeScript │ TanStack Query │ Tailwind CSS │ Shadcn/ui │
│  React Router │ React Hook Form │ Zod │ Zustand │ Recharts        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/REST API + WebSocket
┌─────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY (Nginx)                         │
├─────────────────────────────────────────────────────────────────────┤
│     Load Balancer │ SSL Termination │ Rate Limiting │ CORS         │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI/Python)                        │
├─────────────────────────────────────────────────────────────────────┤
│  FastAPI │ SQLAlchemy │ Pydantic V2 │ Alembic │ Celery │ Redis     │
│  JWT Auth │ Middleware │ Background Tasks │ WebSockets              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        INFRAESTRUTURA                                │
├─────────────────────────────────────────────────────────────────────┤
│     MySQL 8.0+ │ Redis (Cache) │ MinIO (Arquivos) │ Docker         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Diretórios

### Backend (FastAPI)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Ponto de entrada FastAPI
│   ├── config.py                  # Configurações da aplicação
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependências (DB, Auth)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router principal v1
│   │       └── endpoints/
│   │           ├── alunos.py      # CRUD Alunos
│   │           ├── funcionarios.py
│   │           ├── turmas.py
│   │           ├── matriculas.py
│   │           ├── notas.py
│   │           ├── frequencia.py
│   │           ├── relatorios.py
│   │           ├── dashboard.py
│   │           └── auth.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py            # JWT, hashing
│   │   ├── config.py              # Settings Pydantic
│   │   └── exceptions.py          # Exceções customizadas
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py             # SQLAlchemy session
│   │   ├── base.py                # Base class models
│   │   └── init_db.py             # Inicialização
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── aluno.py
│   │   ├── funcionario.py
│   │   ├── turma.py
│   │   ├── matricula.py
│   │   ├── nota.py
│   │   ├── frequencia.py
│   │   └── user.py
│   │
│   ├── schemas/                   # Pydantic schemas (reutilizar existentes!)
│   │   ├── __init__.py
│   │   ├── aluno.py               # AlunoCreate, AlunoRead, AlunoUpdate
│   │   ├── funcionario.py
│   │   ├── turma.py
│   │   ├── matricula.py
│   │   ├── nota.py
│   │   ├── frequencia.py
│   │   ├── token.py
│   │   └── user.py
│   │
│   ├── services/                  # REUTILIZAR services existentes!
│   │   ├── __init__.py
│   │   ├── aluno_service.py       # Adaptar do atual
│   │   ├── funcionario_service.py
│   │   ├── estatistica_service.py
│   │   ├── report_service.py
│   │   └── backup_service.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── cache.py               # Redis cache
│       ├── feature_flags.py       # Reutilizar existente
│       └── pdf_generator.py       # ReportLab
│
├── migrations/                    # Alembic
│   └── versions/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_alunos.py
│   └── ...
│
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

### Frontend (React/TypeScript)

```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
│       └── images/
│
├── src/
│   ├── index.tsx                  # Entry point
│   ├── App.tsx                    # Root component
│   ├── vite-env.d.ts
│   │
│   ├── api/                       # Comunicação com backend
│   │   ├── client.ts              # Axios/Fetch configurado
│   │   ├── endpoints/
│   │   │   ├── alunos.ts
│   │   │   ├── funcionarios.ts
│   │   │   ├── turmas.ts
│   │   │   ├── matriculas.ts
│   │   │   ├── notas.ts
│   │   │   ├── frequencia.ts
│   │   │   ├── relatorios.ts
│   │   │   ├── dashboard.ts
│   │   │   └── auth.ts
│   │   └── index.ts
│   │
│   ├── components/                # Componentes reutilizáveis
│   │   ├── ui/                    # Shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── table.tsx
│   │   │   ├── modal.tsx
│   │   │   ├── select.tsx
│   │   │   ├── date-picker.tsx
│   │   │   ├── toast.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── MainLayout.tsx
│   │   │
│   │   ├── common/
│   │   │   ├── DataTable.tsx      # Tabela genérica
│   │   │   ├── SearchBar.tsx
│   │   │   ├── Pagination.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── ConfirmDialog.tsx
│   │   │
│   │   └── forms/
│   │       ├── AlunoForm.tsx
│   │       ├── FuncionarioForm.tsx
│   │       ├── TurmaForm.tsx
│   │       ├── MatriculaForm.tsx
│   │       ├── NotaForm.tsx
│   │       └── FrequenciaForm.tsx
│   │
│   ├── features/                  # Módulos por funcionalidade
│   │   ├── alunos/
│   │   │   ├── AlunoList.tsx
│   │   │   ├── AlunoDetails.tsx
│   │   │   ├── AlunoCreate.tsx
│   │   │   ├── AlunoEdit.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── useAlunos.ts
│   │   │   │   └── useAlunoMutation.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── funcionarios/
│   │   │   └── ...
│   │   │
│   │   ├── turmas/
│   │   │   └── ...
│   │   │
│   │   ├── matriculas/
│   │   │   └── ...
│   │   │
│   │   ├── notas/
│   │   │   └── ...
│   │   │
│   │   ├── frequencia/
│   │   │   └── ...
│   │   │
│   │   ├── dashboard/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── StatCards.tsx
│   │   │   ├── Charts.tsx
│   │   │   └── hooks/
│   │   │       └── useDashboardStats.ts
│   │   │
│   │   ├── relatorios/
│   │   │   ├── RelatorioList.tsx
│   │   │   ├── RelatorioViewer.tsx
│   │   │   └── ...
│   │   │
│   │   └── auth/
│   │       ├── Login.tsx
│   │       ├── hooks/
│   │       │   └── useAuth.ts
│   │       └── AuthContext.tsx
│   │
│   ├── hooks/                     # Hooks globais
│   │   ├── useDebounce.ts
│   │   ├── useLocalStorage.ts
│   │   ├── useMediaQuery.ts
│   │   └── usePagination.ts
│   │
│   ├── lib/                       # Utilitários
│   │   ├── utils.ts
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   │
│   ├── store/                     # Estado global (Zustand)
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── index.ts
│   │
│   ├── styles/
│   │   ├── globals.css
│   │   └── tailwind.css
│   │
│   └── types/                     # TypeScript types
│       ├── aluno.ts
│       ├── funcionario.ts
│       ├── turma.ts
│       ├── matricula.ts
│       ├── nota.ts
│       ├── frequencia.ts
│       ├── user.ts
│       └── api.ts
│
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
├── .eslintrc.js
├── .prettierrc
└── Dockerfile
```

---

## 🔄 Mapeamento de Funcionalidades

### Migração de Componentes Tkinter → React

| Componente Tkinter | Componente React | Biblioteca |
|-------------------|------------------|------------|
| `Tk()` / `Toplevel()` | `App.tsx` / Modais | React Router DOM |
| `Frame` | `<div>` / Componente | Tailwind CSS |
| `Button` | `<Button>` | Shadcn/ui |
| `Entry` | `<Input>` | Shadcn/ui |
| `Label` | `<Label>` / `<p>` | Shadcn/ui |
| `Listbox` | `<Select>` | Shadcn/ui |
| `Treeview` (tabela) | `<DataTable>` | TanStack Table |
| `messagebox` | `<Toast>` / `<AlertDialog>` | Shadcn/ui |
| `filedialog` | `<input type="file">` | HTML nativo |
| `DateEntry` | `<DatePicker>` | Shadcn/ui + date-fns |
| `Scrollbar` | CSS overflow | Tailwind CSS |
| `Menu` | `<NavigationMenu>` | Shadcn/ui |
| `Combobox` | `<Combobox>` | Shadcn/ui |

### Migração de Services (Python → Python/FastAPI)

| Service Atual | Endpoint API | Método |
|--------------|--------------|--------|
| `aluno_service.criar_aluno()` | `POST /api/v1/alunos` | Create |
| `aluno_service.buscar_aluno()` | `GET /api/v1/alunos/{id}` | Read |
| `aluno_service.listar_alunos()` | `GET /api/v1/alunos` | List |
| `aluno_service.atualizar_aluno()` | `PUT /api/v1/alunos/{id}` | Update |
| `aluno_service.excluir_aluno()` | `DELETE /api/v1/alunos/{id}` | Delete |
| `estatistica_service.obter_estatisticas_*()` | `GET /api/v1/dashboard/stats` | Dashboard |
| `report_service.*` | `GET /api/v1/relatorios/*` | Relatórios |

---

## 📋 Cronograma de Implementação

### Fase 1: Infraestrutura Base (2-3 semanas)

#### Semana 1: Backend Base
- [ ] Criar projeto FastAPI com estrutura de diretórios
- [ ] Configurar SQLAlchemy com MySQL existente
- [ ] Migrar models Pydantic existentes para schemas
- [ ] Criar SQLAlchemy models
- [ ] Configurar Alembic para migrations
- [ ] Implementar autenticação JWT
- [ ] Configurar CORS e middleware

#### Semana 2: Frontend Base
- [ ] Criar projeto Vite + React + TypeScript
- [ ] Configurar Tailwind CSS e Shadcn/ui
- [ ] Criar layout base (Header, Sidebar, MainContent)
- [ ] Configurar React Router
- [ ] Implementar AuthContext e proteção de rotas
- [ ] Criar tela de Login
- [ ] Configurar TanStack Query

#### Semana 3: Integração
- [ ] Configurar Docker Compose (Backend + Frontend + MySQL)
- [ ] Configurar proxy de desenvolvimento
- [ ] Testar fluxo de autenticação completo
- [ ] Documentar APIs com Swagger/OpenAPI

### Fase 2: CRUD Principal (3-4 semanas)

#### Semana 4-5: Módulo Alunos
- [ ] Backend: Endpoints CRUD alunos
- [ ] Backend: Migrar `aluno_service.py`
- [ ] Frontend: Lista de alunos com paginação
- [ ] Frontend: Formulário de cadastro/edição
- [ ] Frontend: Detalhes do aluno
- [ ] Frontend: Busca avançada
- [ ] Testes E2E

#### Semana 6: Módulo Funcionários
- [ ] Backend: Endpoints CRUD funcionários
- [ ] Backend: Migrar `funcionario_service.py`
- [ ] Frontend: Lista, formulário, detalhes
- [ ] Testes

#### Semana 7: Módulos Turmas e Matrículas
- [ ] Backend: Endpoints turmas e matrículas
- [ ] Backend: Migrar services relacionados
- [ ] Frontend: Interfaces de gestão
- [ ] Testes

### Fase 3: Funcionalidades Avançadas (3-4 semanas)

#### Semana 8-9: Notas e Frequência
- [ ] Backend: Endpoints notas e frequência
- [ ] Frontend: Interface de lançamento de notas
- [ ] Frontend: Interface de frequência
- [ ] Cálculos automáticos (médias, faltas)
- [ ] Testes

#### Semana 10: Dashboard
- [ ] Backend: Endpoint de estatísticas
- [ ] Backend: Migrar cache Redis
- [ ] Frontend: Dashboard com gráficos (Recharts)
- [ ] Frontend: Cards de estatísticas
- [ ] Atualização em tempo real (opcional)

#### Semana 11: Relatórios
- [ ] Backend: Geração de PDFs (ReportLab)
- [ ] Backend: Download assíncrono (Celery)
- [ ] Frontend: Lista de relatórios disponíveis
- [ ] Frontend: Visualização e download
- [ ] Testes

### Fase 4: Polimento e Deploy (2 semanas)

#### Semana 12: QA e Otimização
- [ ] Testes de carga
- [ ] Otimização de queries
- [ ] Revisão de segurança
- [ ] Correção de bugs
- [ ] Documentação final

#### Semana 13: Deploy
- [ ] Configurar ambiente de produção
- [ ] Deploy inicial (staging)
- [ ] Testes em produção
- [ ] Migração de dados
- [ ] Go-live

---

## 💻 Detalhamento Técnico

### Backend: Exemplo de Endpoint

```python
# backend/app/api/v1/endpoints/alunos.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.aluno import AlunoCreate, AlunoRead, AlunoUpdate
from app.services.aluno_service import AlunoService

router = APIRouter()


@router.get("/", response_model=List[AlunoRead])
async def listar_alunos(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    nome: Optional[str] = None,
    turma_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user = Depends(deps.get_current_user)
):
    """
    Lista alunos com filtros e paginação.
    """
    service = AlunoService(db)
    alunos = service.listar_alunos(
        skip=skip,
        limit=limit,
        nome=nome,
        turma_id=turma_id,
        status=status
    )
    return alunos


@router.post("/", response_model=AlunoRead, status_code=201)
async def criar_aluno(
    aluno_in: AlunoCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Cria um novo aluno.
    """
    service = AlunoService(db)
    aluno = service.criar_aluno(aluno_in)
    return aluno


@router.get("/{aluno_id}", response_model=AlunoRead)
async def buscar_aluno(
    aluno_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Busca um aluno por ID.
    """
    service = AlunoService(db)
    aluno = service.buscar_aluno(aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return aluno


@router.put("/{aluno_id}", response_model=AlunoRead)
async def atualizar_aluno(
    aluno_id: int,
    aluno_in: AlunoUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Atualiza um aluno existente.
    """
    service = AlunoService(db)
    aluno = service.atualizar_aluno(aluno_id, aluno_in)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return aluno


@router.delete("/{aluno_id}", status_code=204)
async def excluir_aluno(
    aluno_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Exclui um aluno (soft delete).
    """
    service = AlunoService(db)
    success = service.excluir_aluno(aluno_id)
    if not success:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
```

### Frontend: Exemplo de Componente

```tsx
// frontend/src/features/alunos/AlunoList.tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Pagination } from '@/components/common/Pagination'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { alunosApi } from '@/api/endpoints/alunos'
import { useDebounce } from '@/hooks/useDebounce'
import type { Aluno } from '@/types/aluno'

export function AlunoList() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<string>('ativo')
  
  const debouncedSearch = useDebounce(search, 300)
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['alunos', page, debouncedSearch, status],
    queryFn: () => alunosApi.listar({
      skip: (page - 1) * 20,
      limit: 20,
      nome: debouncedSearch || undefined,
      status: status || undefined,
    }),
  })
  
  if (isLoading) return <LoadingSpinner />
  if (error) return <div>Erro ao carregar alunos</div>
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Alunos</h1>
        <Button onClick={() => navigate('/alunos/novo')}>
          Novo Aluno
        </Button>
      </div>
      
      <div className="flex gap-4">
        <Input
          placeholder="Buscar por nome..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ativo">Ativo</SelectItem>
            <SelectItem value="inativo">Inativo</SelectItem>
            <SelectItem value="transferido">Transferido</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Nome</TableHead>
            <TableHead>Matrícula</TableHead>
            <TableHead>Turma</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.items.map((aluno: Aluno) => (
            <TableRow key={aluno.id}>
              <TableCell>{aluno.nome}</TableCell>
              <TableCell>{aluno.matricula}</TableCell>
              <TableCell>{aluno.turma?.nome}</TableCell>
              <TableCell>{aluno.status}</TableCell>
              <TableCell>
                <Button
                  variant="ghost"
                  onClick={() => navigate(`/alunos/${aluno.id}`)}
                >
                  Ver
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => navigate(`/alunos/${aluno.id}/editar`)}
                >
                  Editar
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      
      <Pagination
        currentPage={page}
        totalPages={Math.ceil((data?.total || 0) / 20)}
        onPageChange={setPage}
      />
    </div>
  )
}
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://user:password@db:3306/redeescola
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app

  db:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
      - MYSQL_DATABASE=redeescola
      - MYSQL_USER=${DB_USER}
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backup_redeescola.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  mysql_data:
  redis_data:
```

---

## 🔐 Segurança

### Medidas de Segurança

1. **Autenticação JWT**
   - Tokens com expiração curta (15 min access, 7 dias refresh)
   - Rotação de tokens
   - Blacklist de tokens revogados

2. **CORS**
   - Origens permitidas configuráveis
   - Credentials habilitados apenas quando necessário

3. **Rate Limiting**
   - Limite por IP e por usuário
   - Proteção contra força bruta

4. **Validação**
   - Pydantic no backend
   - Zod no frontend
   - Sanitização de inputs

5. **HTTPS**
   - SSL/TLS obrigatório em produção
   - Certificados Let's Encrypt

6. **Headers de Segurança**
   - CSP (Content Security Policy)
   - X-Frame-Options
   - X-Content-Type-Options

---

## 📊 Métricas de Sucesso

| Métrica | Atual (Tkinter) | Meta (Web) |
|---------|-----------------|------------|
| Tempo de carregamento | 3-5s | < 1s |
| Latência de API | N/A | < 100ms |
| Uptime | Local | 99.9% |
| Usuários simultâneos | 1 | 100+ |
| Dispositivos | Desktop | Desktop + Tablet + Mobile |
| Acessibilidade | Limitada | WCAG 2.1 AA |

---

## 💰 Estimativa de Custos

### Desenvolvimento
- **Desenvolvedor Full Stack**: 12-13 semanas
- **Custo estimado**: R$ 40.000 - R$ 60.000

### Infraestrutura (mensal)
| Serviço | Custo Mensal |
|---------|--------------|
| VPS (2 vCPU, 4GB RAM) | R$ 100-200 |
| Backup MySQL | R$ 50 |
| CDN | R$ 50-100 |
| SSL Certificate | Gratuito (Let's Encrypt) |
| Domínio | R$ 40/ano |
| **Total Mensal** | **~R$ 200-400** |

---

## ✅ Checklist de Pré-Requisitos

- [ ] Equipe com conhecimento em React/TypeScript
- [ ] Equipe com conhecimento em FastAPI/Python
- [ ] Servidor para hospedagem (VPS ou Cloud)
- [ ] Domínio registrado
- [ ] Backup do banco de dados atual
- [ ] Documentação de regras de negócio
- [ ] Aprovação de stakeholders

---

## 📚 Referências

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TanStack Query](https://tanstack.com/query)
- [Shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pydantic V2](https://docs.pydantic.dev/)
