# 🔌 Plano de Desenvolvimento da API Backend Compartilhada

## Visão Geral

Este documento detalha o plano para criação de uma **API Backend unificada** que servirá como base para todas as plataformas (Web, Mobile, Desktop). Utilizando **FastAPI** (Python), a API será o coração do sistema multiplataforma.

---

## 📊 Análise do Backend Atual

### Componentes Existentes (Reutilizáveis)

```
gestao/
├── services/                    # ✅ Lógica de negócio - REUTILIZAR
│   ├── aluno_service.py
│   ├── funcionario_service.py
│   ├── estatistica_service.py
│   ├── report_service.py
│   ├── backup_service.py
│   ├── turma_service.py
│   ├── matricula_service.py
│   ├── boletim_service.py
│   └── declaracao_service.py
│
├── models/                      # ✅ Modelos Pydantic - REUTILIZAR
│   ├── aluno.py
│   ├── funcionario.py
│   ├── turma.py
│   └── matricula.py
│
├── db/                          # ✅ Camada de dados - ADAPTAR
│   ├── connection.py
│   └── queries.py
│
├── conexao.py                   # ✅ Pool de conexões - ADAPTAR
├── config.py                    # ✅ Configurações - REUTILIZAR
├── config_logs.py               # ✅ Logging - REUTILIZAR
└── utils/                       # ✅ Utilitários - REUTILIZAR
```

### Benefícios do Reaproveitamento

1. **Lógica de negócio testada**: Services já funcionam em produção
2. **Validação Pydantic**: Modelos prontos para serialização JSON
3. **Pool de conexões**: Infraestrutura de banco de dados pronta
4. **Cache implementado**: Sistema de cache já funcional
5. **Logs estruturados**: Sistema de logging maduro

---

## 🏗️ Arquitetura da API

### Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTES                                     │
├─────────────────────────────────────────────────────────────────────┤
│   Web App    │    Mobile App    │    Desktop App    │    CLI        │
│   (React)    │    (React Native) │    (Tauri)       │    (Scripts)  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS/REST
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (Nginx/Traefik)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Rate Limiting │ SSL Termination │ Load Balancing │ CORS           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     API ROUTERS (v1)                          │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  /alunos │ /funcionarios │ /turmas │ /matriculas │ /notas    │  │
│  │  /frequencia │ /relatorios │ /dashboard │ /auth │ /backup    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               │                                      │
│                               ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     MIDDLEWARE LAYER                          │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  Auth JWT │ Rate Limit │ Logging │ Error Handler │ CORS      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               │                                      │
│                               ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     SERVICE LAYER                             │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  (Reutiliza services existentes do projeto original)          │  │
│  │  AlunoService │ FuncionarioService │ EstatisticaService       │  │
│  │  ReportService │ BackupService │ TurmaService                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               │                                      │
│                               ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     DATA LAYER                                │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  SQLAlchemy ORM │ Connection Pool │ Transactions              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │   MySQL     │    │   Redis     │    │   MinIO     │
    │  Database   │    │   Cache     │    │   Storage   │
    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 📁 Estrutura de Diretórios Detalhada

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py                        # Entry point FastAPI
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                    # Dependencies (DB, Auth, etc)
│   │   │
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py                 # Router principal v1
│   │       │
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── alunos.py          # CRUD + busca avançada
│   │           ├── funcionarios.py    # CRUD + licenças
│   │           ├── turmas.py          # CRUD + alunos por turma
│   │           ├── matriculas.py      # CRUD + transferências
│   │           ├── notas.py           # CRUD + lançamento em lote
│   │           ├── frequencia.py      # CRUD + lançamento em lote
│   │           ├── relatorios.py      # Geração assíncrona de PDFs
│   │           ├── dashboard.py       # Estatísticas e métricas
│   │           ├── auth.py            # Login, logout, refresh
│   │           ├── users.py           # Gestão de usuários
│   │           ├── backup.py          # Backup/restore
│   │           ├── anos_letivos.py    # Anos letivos
│   │           ├── series.py          # Séries
│   │           ├── escolas.py         # Escolas
│   │           └── health.py          # Health check
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                  # Settings com Pydantic
│   │   ├── security.py                # JWT, hashing, permissões
│   │   ├── exceptions.py              # Exceções customizadas
│   │   └── logging.py                 # Configuração de logs
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py                 # SQLAlchemy session
│   │   ├── base.py                    # Base class dos models
│   │   ├── init_db.py                 # Inicialização do banco
│   │   └── repositories/              # Repository pattern
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── aluno_repository.py
│   │       ├── funcionario_repository.py
│   │       └── ...
│   │
│   ├── models/                        # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── aluno.py
│   │   ├── funcionario.py
│   │   ├── turma.py
│   │   ├── matricula.py
│   │   ├── nota.py
│   │   ├── frequencia.py
│   │   ├── user.py
│   │   ├── escola.py
│   │   ├── serie.py
│   │   └── ano_letivo.py
│   │
│   ├── schemas/                       # Pydantic Schemas (DTO)
│   │   ├── __init__.py
│   │   ├── aluno.py                   # AlunoCreate, AlunoRead, AlunoUpdate
│   │   ├── funcionario.py
│   │   ├── turma.py
│   │   ├── matricula.py
│   │   ├── nota.py
│   │   ├── frequencia.py
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── dashboard.py
│   │   ├── relatorio.py
│   │   └── common.py                  # Pagination, Response, etc
│   │
│   ├── services/                      # Business Logic (REUTILIZAR!)
│   │   ├── __init__.py
│   │   ├── aluno_service.py           # Adaptado do original
│   │   ├── funcionario_service.py
│   │   ├── turma_service.py
│   │   ├── matricula_service.py
│   │   ├── nota_service.py
│   │   ├── frequencia_service.py
│   │   ├── estatistica_service.py
│   │   ├── report_service.py
│   │   ├── backup_service.py
│   │   └── email_service.py
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                    # Autenticação
│   │   ├── rate_limit.py              # Rate limiting
│   │   ├── logging.py                 # Request logging
│   │   └── error_handler.py           # Error handling global
│   │
│   ├── tasks/                         # Background tasks (Celery)
│   │   ├── __init__.py
│   │   ├── celery_app.py              # Configuração Celery
│   │   ├── report_tasks.py            # Geração de relatórios
│   │   ├── backup_tasks.py            # Backup automático
│   │   └── email_tasks.py             # Envio de emails
│   │
│   └── utils/
│       ├── __init__.py
│       ├── cache.py                   # Redis cache wrapper
│       ├── pagination.py              # Helpers de paginação
│       ├── validators.py              # Validadores customizados
│       └── formatters.py              # Formatadores
│
├── migrations/                        # Alembic migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Fixtures pytest
│   ├── test_api/
│   │   ├── test_alunos.py
│   │   ├── test_funcionarios.py
│   │   ├── test_auth.py
│   │   └── ...
│   ├── test_services/
│   │   └── ...
│   └── test_integration/
│       └── ...
│
├── scripts/
│   ├── create_superuser.py
│   ├── seed_data.py
│   └── migrate_from_legacy.py
│
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 💻 Implementação Detalhada

### 1. Entry Point (main.py)

```python
# app/main.py
"""
FastAPI Application - Sistema de Gestão Escolar API
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, init_db
from app.middleware.error_handler import add_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para startup e shutdown."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await engine.dispose()


def create_application() -> FastAPI:
    """Factory para criar a aplicação FastAPI."""
    
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="""
        ## Sistema de Gestão Escolar API
        
        API RESTful para o Sistema de Gestão Escolar Municipal.
        
        ### Funcionalidades
        
        * **Alunos** - Cadastro, consulta, atualização e exclusão de alunos
        * **Funcionários** - Gestão de professores e funcionários
        * **Turmas** - Gerenciamento de turmas e séries
        * **Matrículas** - Controle de matrículas e transferências
        * **Notas** - Lançamento e consulta de notas
        * **Frequência** - Controle de presença e faltas
        * **Relatórios** - Geração de relatórios em PDF
        * **Dashboard** - Estatísticas e métricas
        """,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middlewares
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(RateLimitMiddleware)
    
    # Exception handlers
    add_exception_handlers(application)
    
    # Routers
    application.include_router(api_router, prefix=settings.API_V1_STR)
    
    return application


app = create_application()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint com informações da API."""
    return {
        "message": "Sistema de Gestão Escolar API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
```

### 2. Configurações (core/config.py)

```python
# app/core/config.py
"""
Configurações da aplicação usando Pydantic Settings.
"""

from typing import List, Optional
from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Projeto
    PROJECT_NAME: str = "Sistema de Gestão Escolar API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Segurança
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    # Database
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Cache
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 600
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Escola
    SCHOOL_ID: int = 60
    
    # Email (opcional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Celery (Background Tasks)
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Storage (MinIO/S3)
    STORAGE_ENDPOINT: Optional[str] = None
    STORAGE_ACCESS_KEY: Optional[str] = None
    STORAGE_SECRET_KEY: Optional[str] = None
    STORAGE_BUCKET: str = "gestao-escolar"


settings = Settings()
```

### 3. Schemas Pydantic (schemas/aluno.py)

```python
# app/schemas/aluno.py
"""
Schemas Pydantic para Aluno.
Adaptado dos models existentes do projeto.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class AlunoBase(BaseModel):
    """Base schema com campos comuns."""
    
    nome: str = Field(..., min_length=3, max_length=100, description="Nome completo do aluno")
    data_nascimento: date = Field(..., description="Data de nascimento")
    sexo: Optional[str] = Field(None, pattern="^[MF]$", description="M ou F")
    cpf: Optional[str] = Field(None, description="CPF (apenas números)")
    rg: Optional[str] = Field(None, max_length=20, description="RG")
    naturalidade: Optional[str] = Field(None, max_length=100)
    nacionalidade: str = Field(default="Brasileiro", max_length=50)
    
    # Filiação
    mae: str = Field(..., min_length=3, max_length=100, description="Nome da mãe")
    pai: Optional[str] = Field(None, max_length=100, description="Nome do pai")
    
    # Endereço
    endereco: Optional[str] = Field(None, max_length=200)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    uf: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=9)
    
    # Contatos
    telefone: Optional[str] = Field(None, max_length=20)
    telefone_responsavel: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    
    # Informações adicionais
    nis: Optional[str] = Field(None, max_length=20, description="NIS/PIS")
    certidao_nascimento: Optional[str] = Field(None, max_length=50)
    cartao_sus: Optional[str] = Field(None, max_length=20)
    observacoes: Optional[str] = Field(None, max_length=500)
    
    # Necessidades especiais
    deficiencia: Optional[str] = Field(None, max_length=100)
    tipo_deficiencia: Optional[str] = Field(None, max_length=100)
    laudo: Optional[bool] = Field(default=False)
    
    @field_validator('cpf')
    @classmethod
    def validar_cpf(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        # Remover caracteres não numéricos
        cpf = re.sub(r'\D', '', v)
        
        if len(cpf) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        
        # Validar dígitos verificadores
        if cpf == cpf[0] * 11:
            raise ValueError('CPF inválido')
        
        # Validação matemática do CPF
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[9]):
            raise ValueError('CPF inválido')
        
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[10]):
            raise ValueError('CPF inválido')
        
        return cpf
    
    @field_validator('data_nascimento')
    @classmethod
    def validar_idade(cls, v: date) -> date:
        hoje = date.today()
        idade = (hoje - v).days / 365.25
        
        if idade < 3:
            raise ValueError('Aluno deve ter pelo menos 3 anos')
        if idade > 100:
            raise ValueError('Data de nascimento inválida')
        
        return v


class AlunoCreate(AlunoBase):
    """Schema para criação de aluno."""
    
    escola_id: int = Field(..., description="ID da escola")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "nome": "João da Silva",
            "data_nascimento": "2015-05-15",
            "sexo": "M",
            "mae": "Maria da Silva",
            "escola_id": 60
        }
    })


class AlunoUpdate(BaseModel):
    """Schema para atualização parcial de aluno."""
    
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    data_nascimento: Optional[date] = None
    sexo: Optional[str] = Field(None, pattern="^[MF]$")
    cpf: Optional[str] = None
    rg: Optional[str] = None
    naturalidade: Optional[str] = None
    nacionalidade: Optional[str] = None
    mae: Optional[str] = None
    pai: Optional[str] = None
    endereco: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    telefone: Optional[str] = None
    telefone_responsavel: Optional[str] = None
    email: Optional[str] = None
    nis: Optional[str] = None
    certidao_nascimento: Optional[str] = None
    cartao_sus: Optional[str] = None
    observacoes: Optional[str] = None
    deficiencia: Optional[str] = None
    tipo_deficiencia: Optional[str] = None
    laudo: Optional[bool] = None


class AlunoRead(AlunoBase):
    """Schema para leitura de aluno."""
    
    id: int
    escola_id: int
    created_at: datetime
    updated_at: datetime
    
    # Relacionamentos (quando carregados)
    matricula_ativa: Optional["MatriculaSimples"] = None
    
    model_config = ConfigDict(from_attributes=True)


class AlunoSimples(BaseModel):
    """Schema simplificado para listagens."""
    
    id: int
    nome: str
    data_nascimento: date
    mae: str
    
    model_config = ConfigDict(from_attributes=True)


class AlunoComMatricula(AlunoRead):
    """Schema com informações de matrícula."""
    
    turma_nome: Optional[str] = None
    serie_nome: Optional[str] = None
    numero_chamada: Optional[int] = None
    status_matricula: Optional[str] = None


# Para evitar referência circular
class MatriculaSimples(BaseModel):
    id: int
    turma_id: int
    numero_chamada: Optional[int]
    status: str
    
    model_config = ConfigDict(from_attributes=True)


AlunoRead.model_rebuild()
```

### 4. Endpoint de Alunos (api/v1/endpoints/alunos.py)

```python
# app/api/v1/endpoints/alunos.py
"""
Endpoints da API para gestão de alunos.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.schemas.aluno import (
    AlunoCreate, AlunoRead, AlunoUpdate, 
    AlunoSimples, AlunoComMatricula
)
from app.schemas.common import PaginatedResponse, Message
from app.services.aluno_service import AlunoService
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[AlunoSimples],
    summary="Listar alunos",
    description="Retorna lista paginada de alunos com filtros opcionais."
)
async def listar_alunos(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="Registros a pular"),
    limit: int = Query(50, ge=1, le=200, description="Limite de registros"),
    nome: Optional[str] = Query(None, min_length=2, description="Filtrar por nome"),
    turma_id: Optional[int] = Query(None, description="Filtrar por turma"),
    serie_id: Optional[int] = Query(None, description="Filtrar por série"),
    status: Optional[str] = Query(None, description="Status da matrícula"),
    escola_id: Optional[int] = Query(None, description="Filtrar por escola"),
    ano_letivo_id: Optional[int] = Query(None, description="Filtrar por ano letivo"),
    ordenar_por: str = Query("nome", description="Campo para ordenação"),
    ordem: str = Query("asc", pattern="^(asc|desc)$", description="Direção da ordenação"),
):
    """
    Lista alunos com suporte a:
    - Paginação (skip/limit)
    - Filtros por nome, turma, série, status, escola
    - Ordenação customizável
    """
    service = AlunoService(db)
    
    alunos, total = await service.listar_alunos(
        skip=skip,
        limit=limit,
        nome=nome,
        turma_id=turma_id,
        serie_id=serie_id,
        status=status,
        escola_id=escola_id or current_user.escola_id,
        ano_letivo_id=ano_letivo_id,
        ordenar_por=ordenar_por,
        ordem=ordem,
    )
    
    return PaginatedResponse(
        items=alunos,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/busca",
    response_model=List[AlunoSimples],
    summary="Busca rápida de alunos",
    description="Busca rápida por nome para autocomplete."
)
async def buscar_alunos(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
    q: str = Query(..., min_length=2, description="Termo de busca"),
    limit: int = Query(10, ge=1, le=50),
):
    """Busca rápida para autocomplete."""
    service = AlunoService(db)
    return await service.buscar_rapido(q, limit, current_user.escola_id)


@router.get(
    "/{aluno_id}",
    response_model=AlunoRead,
    summary="Buscar aluno por ID",
    description="Retorna dados completos de um aluno específico."
)
async def buscar_aluno(
    aluno_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
):
    """Busca um aluno pelo ID."""
    service = AlunoService(db)
    aluno = await service.buscar_por_id(aluno_id)
    
    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado"
        )
    
    # Verificar acesso à escola
    if aluno.escola_id != current_user.escola_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este aluno"
        )
    
    return aluno


@router.get(
    "/{aluno_id}/completo",
    response_model=AlunoComMatricula,
    summary="Buscar aluno com matrícula",
    description="Retorna dados do aluno com informações da matrícula atual."
)
async def buscar_aluno_completo(
    aluno_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
):
    """Busca aluno com dados de matrícula."""
    service = AlunoService(db)
    aluno = await service.buscar_com_matricula(aluno_id)
    
    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado"
        )
    
    return aluno


@router.post(
    "/",
    response_model=AlunoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar aluno",
    description="Cadastra um novo aluno no sistema."
)
async def criar_aluno(
    aluno_in: AlunoCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo aluno."""
    service = AlunoService(db)
    
    # Verificar CPF duplicado
    if aluno_in.cpf:
        existente = await service.buscar_por_cpf(aluno_in.cpf)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF já cadastrado"
            )
    
    aluno = await service.criar(aluno_in)
    return aluno


@router.put(
    "/{aluno_id}",
    response_model=AlunoRead,
    summary="Atualizar aluno",
    description="Atualiza dados de um aluno existente."
)
async def atualizar_aluno(
    aluno_id: int,
    aluno_in: AlunoUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza um aluno."""
    service = AlunoService(db)
    
    aluno = await service.buscar_por_id(aluno_id)
    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado"
        )
    
    # Verificar permissão
    if aluno.escola_id != current_user.escola_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para editar este aluno"
        )
    
    aluno_atualizado = await service.atualizar(aluno_id, aluno_in)
    return aluno_atualizado


@router.delete(
    "/{aluno_id}",
    response_model=Message,
    summary="Excluir aluno",
    description="Exclui (soft delete) um aluno do sistema."
)
async def excluir_aluno(
    aluno_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
):
    """Exclui um aluno (soft delete)."""
    service = AlunoService(db)
    
    aluno = await service.buscar_por_id(aluno_id)
    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado"
        )
    
    # Verificar permissão
    if aluno.escola_id != current_user.escola_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para excluir este aluno"
        )
    
    await service.excluir(aluno_id)
    return Message(message="Aluno excluído com sucesso")


@router.get(
    "/{aluno_id}/historico",
    summary="Histórico do aluno",
    description="Retorna histórico escolar do aluno."
)
async def historico_aluno(
    aluno_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna histórico escolar do aluno."""
    service = AlunoService(db)
    return await service.obter_historico(aluno_id)


@router.get(
    "/{aluno_id}/notas",
    summary="Notas do aluno",
    description="Retorna todas as notas do aluno."
)
async def notas_aluno(
    aluno_id: int,
    ano_letivo_id: Optional[int] = Query(None),
    bimestre: Optional[int] = Query(None, ge=1, le=4),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna notas do aluno."""
    service = AlunoService(db)
    return await service.obter_notas(aluno_id, ano_letivo_id, bimestre)


@router.get(
    "/{aluno_id}/frequencia",
    summary="Frequência do aluno",
    description="Retorna frequência do aluno."
)
async def frequencia_aluno(
    aluno_id: int,
    ano_letivo_id: Optional[int] = Query(None),
    mes: Optional[int] = Query(None, ge=1, le=12),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna frequência do aluno."""
    service = AlunoService(db)
    return await service.obter_frequencia(aluno_id, ano_letivo_id, mes)
```

### 5. Service Layer (services/aluno_service.py)

```python
# app/services/aluno_service.py
"""
Service de Alunos - Lógica de negócio.
Adaptado do service existente do projeto original.
"""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.aluno import Aluno
from app.models.matricula import Matricula
from app.models.turma import Turma
from app.schemas.aluno import AlunoCreate, AlunoUpdate, AlunoSimples
from app.utils.cache import cache
from app.core.config import settings


class AlunoService:
    """Service para operações com alunos."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def listar_alunos(
        self,
        skip: int = 0,
        limit: int = 50,
        nome: Optional[str] = None,
        turma_id: Optional[int] = None,
        serie_id: Optional[int] = None,
        status: Optional[str] = None,
        escola_id: Optional[int] = None,
        ano_letivo_id: Optional[int] = None,
        ordenar_por: str = "nome",
        ordem: str = "asc",
    ) -> Tuple[List[Aluno], int]:
        """Lista alunos com filtros e paginação."""
        
        # Query base
        query = select(Aluno)
        count_query = select(func.count(Aluno.id))
        
        # Aplicar filtros
        filters = []
        
        if escola_id:
            filters.append(Aluno.escola_id == escola_id)
        
        if nome:
            filters.append(Aluno.nome.ilike(f"%{nome}%"))
        
        if turma_id or serie_id or status or ano_letivo_id:
            # Join com matrículas
            query = query.join(Matricula, Matricula.aluno_id == Aluno.id)
            count_query = count_query.join(Matricula, Matricula.aluno_id == Aluno.id)
            
            if turma_id:
                filters.append(Matricula.turma_id == turma_id)
            
            if serie_id:
                query = query.join(Turma, Turma.id == Matricula.turma_id)
                count_query = count_query.join(Turma, Turma.id == Matricula.turma_id)
                filters.append(Turma.serie_id == serie_id)
            
            if status:
                filters.append(Matricula.status == status)
            
            if ano_letivo_id:
                filters.append(Matricula.ano_letivo_id == ano_letivo_id)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Ordenação
        order_column = getattr(Aluno, ordenar_por, Aluno.nome)
        if ordem == "desc":
            order_column = order_column.desc()
        query = query.order_by(order_column)
        
        # Paginação
        query = query.offset(skip).limit(limit)
        
        # Executar queries
        result = await self.db.execute(query)
        alunos = result.scalars().all()
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        return alunos, total
    
    async def buscar_por_id(self, aluno_id: int) -> Optional[Aluno]:
        """Busca aluno por ID."""
        query = select(Aluno).where(Aluno.id == aluno_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def buscar_com_matricula(self, aluno_id: int) -> Optional[Aluno]:
        """Busca aluno com dados de matrícula."""
        query = (
            select(Aluno)
            .options(
                selectinload(Aluno.matriculas)
                .selectinload(Matricula.turma)
            )
            .where(Aluno.id == aluno_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def buscar_por_cpf(self, cpf: str) -> Optional[Aluno]:
        """Busca aluno por CPF."""
        query = select(Aluno).where(Aluno.cpf == cpf)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def buscar_rapido(
        self, 
        termo: str, 
        limit: int = 10,
        escola_id: Optional[int] = None
    ) -> List[AlunoSimples]:
        """Busca rápida para autocomplete."""
        query = (
            select(Aluno)
            .where(Aluno.nome.ilike(f"%{termo}%"))
            .order_by(Aluno.nome)
            .limit(limit)
        )
        
        if escola_id:
            query = query.where(Aluno.escola_id == escola_id)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def criar(self, aluno_in: AlunoCreate) -> Aluno:
        """Cria um novo aluno."""
        aluno = Aluno(**aluno_in.model_dump())
        self.db.add(aluno)
        await self.db.commit()
        await self.db.refresh(aluno)
        
        # Invalidar cache
        await self._invalidar_cache()
        
        return aluno
    
    async def atualizar(self, aluno_id: int, aluno_in: AlunoUpdate) -> Aluno:
        """Atualiza um aluno."""
        aluno = await self.buscar_por_id(aluno_id)
        if not aluno:
            return None
        
        update_data = aluno_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(aluno, field, value)
        
        await self.db.commit()
        await self.db.refresh(aluno)
        
        # Invalidar cache
        await self._invalidar_cache()
        
        return aluno
    
    async def excluir(self, aluno_id: int) -> bool:
        """Exclui um aluno (soft delete)."""
        aluno = await self.buscar_por_id(aluno_id)
        if not aluno:
            return False
        
        # Soft delete - marcar como inativo
        aluno.ativo = False
        await self.db.commit()
        
        # Invalidar cache
        await self._invalidar_cache()
        
        return True
    
    @cache.cached(ttl=settings.CACHE_TTL_SECONDS)
    async def obter_estatisticas(self, escola_id: int) -> dict:
        """Obtém estatísticas de alunos."""
        # Implementar estatísticas
        pass
    
    async def _invalidar_cache(self):
        """Invalida cache relacionado a alunos."""
        if settings.CACHE_ENABLED:
            await cache.delete_pattern("alunos:*")
            await cache.delete_pattern("dashboard:*")
```

### 6. Autenticação JWT (core/security.py)

```python
# app/core/security.py
"""
Segurança: JWT, hashing, autenticação.
"""

from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.deps import get_db
from app.models.user import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria token JWT de acesso."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Cria token JWT de refresh."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha está correta."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera hash da senha."""
    return pwd_context.hash(password)


def decode_token(token: str) -> Optional[dict]:
    """Decodifica token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Obtém usuário atual a partir do token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Buscar usuário
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo"
        )
    
    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifica se usuário é superusuário."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissões insuficientes"
        )
    return current_user
```

---

## 📋 Cronograma de Implementação

### Fase 1: Infraestrutura Base (2 semanas)

#### Semana 1
- [ ] Criar projeto FastAPI
- [ ] Configurar estrutura de diretórios
- [ ] Configurar SQLAlchemy assíncrono
- [ ] Criar models SQLAlchemy
- [ ] Configurar Alembic migrations
- [ ] Configurar Docker e docker-compose

#### Semana 2
- [ ] Implementar autenticação JWT
- [ ] Configurar middleware de logging
- [ ] Configurar rate limiting
- [ ] Implementar error handlers
- [ ] Configurar Swagger/OpenAPI

### Fase 2: Endpoints CRUD (3 semanas)

#### Semana 3
- [ ] Endpoint de Alunos (CRUD completo)
- [ ] Endpoint de Autenticação
- [ ] Testes unitários alunos
- [ ] Documentação Swagger

#### Semana 4
- [ ] Endpoint de Funcionários
- [ ] Endpoint de Turmas
- [ ] Endpoint de Séries
- [ ] Endpoint de Escolas
- [ ] Testes

#### Semana 5
- [ ] Endpoint de Matrículas
- [ ] Endpoint de Notas
- [ ] Endpoint de Frequência
- [ ] Testes

### Fase 3: Funcionalidades Avançadas (2-3 semanas)

#### Semana 6
- [ ] Endpoint de Dashboard
- [ ] Integrar Redis para cache
- [ ] Estatísticas em tempo real
- [ ] Testes de performance

#### Semana 7
- [ ] Endpoint de Relatórios
- [ ] Configurar Celery para tasks assíncronas
- [ ] Geração de PDFs em background
- [ ] Download de relatórios

#### Semana 8
- [ ] Endpoint de Backup
- [ ] Health checks
- [ ] Métricas (Prometheus)
- [ ] Logs estruturados

### Fase 4: Deploy e Documentação (1-2 semanas)

#### Semana 9
- [ ] Testes E2E completos
- [ ] Deploy em staging
- [ ] Testes de carga (k6/locust)
- [ ] Correção de bugs

#### Semana 10
- [ ] Deploy em produção
- [ ] Monitoramento (Grafana)
- [ ] Documentação final
- [ ] Treinamento da equipe

---

## 🐳 Docker Configuration

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar usuário não-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expor porta
EXPOSE 8000

# Comando de execução
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=db
      - DB_PORT=3306
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME}
      - REDIS_HOST=redis
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./app:/app/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
      - MYSQL_DATABASE=${DB_NAME}
      - MYSQL_USER=${DB_USER}
      - MYSQL_PASSWORD=${DB_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./backup_redeescola.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - DB_HOST=db
      - REDIS_HOST=redis
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - redis

volumes:
  mysql_data:
  redis_data:
```

---

## 📊 Documentação da API (OpenAPI)

A documentação completa da API estará disponível em:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

### Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/alunos` | Listar alunos |
| POST | `/api/v1/alunos` | Criar aluno |
| GET | `/api/v1/alunos/{id}` | Buscar aluno |
| PUT | `/api/v1/alunos/{id}` | Atualizar aluno |
| DELETE | `/api/v1/alunos/{id}` | Excluir aluno |
| GET | `/api/v1/funcionarios` | Listar funcionários |
| GET | `/api/v1/turmas` | Listar turmas |
| POST | `/api/v1/notas/lote` | Lançar notas em lote |
| POST | `/api/v1/frequencia/lote` | Lançar frequência em lote |
| GET | `/api/v1/dashboard/stats` | Estatísticas |
| POST | `/api/v1/relatorios/gerar` | Gerar relatório |
| GET | `/api/v1/health` | Health check |

---

## 💰 Estimativa de Custos

### Desenvolvimento
- **Desenvolvedor Backend**: 8-10 semanas
- **Custo estimado**: R$ 30.000 - R$ 45.000

### Infraestrutura (mensal)

| Serviço | Custo |
|---------|-------|
| VPS API (2 vCPU, 4GB) | R$ 100-150 |
| MySQL Gerenciado | R$ 150-300 |
| Redis | R$ 50-100 |
| CDN/Load Balancer | R$ 50-100 |
| Backup | R$ 50 |
| **Total Mensal** | **R$ 400-700** |

---

## ✅ Checklist de Pré-Requisitos

- [ ] Python 3.12+ instalado
- [ ] Docker e Docker Compose
- [ ] Acesso ao banco de dados MySQL
- [ ] Servidor para hospedagem
- [ ] Conhecimento em FastAPI
- [ ] Conhecimento em SQLAlchemy
- [ ] Backup do banco atual

---

## 📚 Referências

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2](https://docs.pydantic.dev/)
- [Celery](https://docs.celeryq.dev/)
- [Redis](https://redis.io/docs/)
- [Docker](https://docs.docker.com/)
