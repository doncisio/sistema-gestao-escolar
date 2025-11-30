# ☁️ Plano de Implantação em Nuvem (Cloud/SaaS)

## Visão Geral

Este documento detalha o plano para implantar o Sistema de Gestão Escolar como uma solução **SaaS (Software as a Service)** na nuvem, permitindo que múltiplas escolas utilizem a mesma infraestrutura com isolamento de dados (multi-tenant).

---

## 📊 Análise de Requisitos Cloud

### Motivações para Cloud

1. **Escalabilidade**: Suportar múltiplas escolas/redes de ensino
2. **Alta Disponibilidade**: SLA de 99.9%+
3. **Redução de Custos**: Infraestrutura compartilhada
4. **Manutenção Centralizada**: Atualizações automáticas para todos
5. **Segurança**: Backups automáticos, compliance (LGPD)
6. **Acesso Global**: Sistema acessível de qualquer lugar

### Modelo Multi-Tenant

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MODELO MULTI-TENANT                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Escola A     Escola B     Escola C     Rede Municipal X           │
│   ┌─────┐      ┌─────┐      ┌─────┐      ┌───────────────┐         │
│   │Users│      │Users│      │Users│      │ Escola D      │         │
│   │Data │      │Data │      │Data │      │ Escola E      │         │
│   │Config│     │Config│     │Config│     │ Escola F      │         │
│   └─────┘      └─────┘      └─────┘      │ (Multiescola) │         │
│      │            │            │         └───────────────┘         │
│      └────────────┼────────────┼────────────────┘                  │
│                   │            │                                    │
│                   ▼            ▼                                    │
│         ┌─────────────────────────────────┐                        │
│         │     CAMADA DE ISOLAMENTO        │                        │
│         │   (Tenant ID em todas tabelas)  │                        │
│         └─────────────────────────────────┘                        │
│                           │                                         │
│                           ▼                                         │
│         ┌─────────────────────────────────┐                        │
│         │     BANCO DE DADOS ÚNICO        │                        │
│         │   (Dados isolados por tenant)   │                        │
│         └─────────────────────────────────┘                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Arquitetura Cloud

### Opção 1: AWS (Amazon Web Services)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    Internet                                                          │
│        │                                                             │
│        ▼                                                             │
│   ┌─────────────────────────────────────────┐                       │
│   │         Route 53 (DNS)                   │                       │
│   │     gestao-escolar.com.br               │                       │
│   └────────────────────┬────────────────────┘                       │
│                        │                                             │
│                        ▼                                             │
│   ┌─────────────────────────────────────────┐                       │
│   │         CloudFront (CDN)                 │                       │
│   │     - Frontend React (S3)                │                       │
│   │     - Cache de assets                    │                       │
│   └────────────────────┬────────────────────┘                       │
│                        │                                             │
│        ┌───────────────┴───────────────┐                            │
│        │                               │                             │
│        ▼                               ▼                             │
│   ┌──────────────┐            ┌──────────────┐                      │
│   │   S3 Bucket  │            │     ALB      │                      │
│   │  (Frontend)  │            │ Application  │                      │
│   │              │            │ Load Balancer│                      │
│   └──────────────┘            └──────┬───────┘                      │
│                                      │                               │
│                         ┌────────────┴────────────┐                 │
│                         │                         │                  │
│                         ▼                         ▼                  │
│   ┌──────────────────────────────────────────────────────┐         │
│   │                    ECS Cluster                        │         │
│   │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │         │
│   │  │   API        │  │   API        │  │  Celery    │ │         │
│   │  │   Task 1     │  │   Task 2     │  │  Workers   │ │         │
│   │  │   (Fargate)  │  │   (Fargate)  │  │  (Fargate) │ │         │
│   │  └──────────────┘  └──────────────┘  └────────────┘ │         │
│   └────────────────────────────┬─────────────────────────┘         │
│                                │                                     │
│          ┌─────────────────────┼─────────────────────┐              │
│          │                     │                     │               │
│          ▼                     ▼                     ▼               │
│   ┌────────────┐       ┌────────────┐       ┌────────────┐          │
│   │    RDS     │       │ ElastiCache│       │     S3     │          │
│   │   MySQL    │       │   Redis    │       │  Storage   │          │
│   │  Multi-AZ  │       │            │       │  (Files)   │          │
│   └────────────┘       └────────────┘       └────────────┘          │
│                                                                      │
│   ┌──────────────────────────────────────────────────────┐         │
│   │                  Serviços Auxiliares                  │         │
│   │  CloudWatch │ Secrets Manager │ SES │ SNS │ Lambda   │         │
│   └──────────────────────────────────────────────────────┘         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Opção 2: Google Cloud Platform (GCP)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GCP ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────┐                       │
│   │         Cloud DNS                        │                       │
│   └────────────────────┬────────────────────┘                       │
│                        │                                             │
│                        ▼                                             │
│   ┌─────────────────────────────────────────┐                       │
│   │         Cloud Load Balancing             │                       │
│   │     + Cloud CDN + Cloud Armor           │                       │
│   └────────────────────┬────────────────────┘                       │
│                        │                                             │
│        ┌───────────────┴───────────────┐                            │
│        │                               │                             │
│        ▼                               ▼                             │
│   ┌──────────────┐            ┌──────────────┐                      │
│   │ Cloud Storage│            │ Cloud Run    │                      │
│   │  (Frontend)  │            │  (API)       │                      │
│   └──────────────┘            └──────────────┘                      │
│                                      │                               │
│          ┌───────────────────────────┼───────────────────────────┐  │
│          │                           │                           │   │
│          ▼                           ▼                           ▼   │
│   ┌────────────┐           ┌────────────┐           ┌────────────┐  │
│   │ Cloud SQL  │           │ Memorystore│           │ Cloud Storage│ │
│   │   MySQL    │           │   Redis    │           │   (Files)  │  │
│   └────────────┘           └────────────┘           └────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Opção 3: Azure

```
┌─────────────────────────────────────────────────────────────────────┐
│                       AZURE ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────┐                       │
│   │         Azure DNS + Front Door           │                       │
│   └────────────────────┬────────────────────┘                       │
│                        │                                             │
│        ┌───────────────┴───────────────┐                            │
│        │                               │                             │
│        ▼                               ▼                             │
│   ┌──────────────┐            ┌──────────────┐                      │
│   │ Blob Storage │            │ App Service  │                      │
│   │  (Frontend)  │            │  (API)       │                      │
│   │   + CDN      │            │  Container   │                      │
│   └──────────────┘            └──────────────┘                      │
│                                      │                               │
│          ┌───────────────────────────┼───────────────────────────┐  │
│          │                           │                           │   │
│          ▼                           ▼                           ▼   │
│   ┌────────────┐           ┌────────────┐           ┌────────────┐  │
│   │ Azure SQL  │           │ Azure Cache│           │ Blob Storage│ │
│   │   MySQL    │           │   Redis    │           │   (Files)  │  │
│   └────────────┘           └────────────┘           └────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Arquitetura Multi-Tenant

### Estratégias de Isolamento

#### Opção A: Schema por Tenant (Recomendada para crescimento)
```sql
-- Cada escola tem seu próprio schema
CREATE SCHEMA escola_001;
CREATE SCHEMA escola_002;

-- Tabelas dentro de cada schema
escola_001.alunos
escola_001.funcionarios
escola_002.alunos
escola_002.funcionarios
```

**Vantagens**: Isolamento forte, fácil backup individual
**Desvantagens**: Mais complexo de gerenciar, migrações mais lentas

#### Opção B: Tenant ID em todas as tabelas (Recomendada inicialmente)
```sql
-- Todas as tabelas têm coluna escola_id
CREATE TABLE alunos (
    id INT PRIMARY KEY,
    escola_id INT NOT NULL,  -- Tenant ID
    nome VARCHAR(100),
    ...
    INDEX idx_escola_id (escola_id)
);

-- Queries sempre filtram por escola_id
SELECT * FROM alunos WHERE escola_id = 60;
```

**Vantagens**: Simples de implementar, migrações fáceis
**Desvantagens**: Risco de vazamento se query mal feita

### Middleware de Tenant

```python
# app/middleware/tenant.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware para identificar e validar tenant."""
    
    async def dispatch(self, request: Request, call_next):
        # Extrair tenant do header, subdomain ou JWT
        tenant_id = self._extract_tenant(request)
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant não identificado")
        
        # Validar tenant existe
        if not await self._validate_tenant(tenant_id):
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
        
        # Adicionar tenant ao request state
        request.state.tenant_id = tenant_id
        
        response = await call_next(request)
        return response
    
    def _extract_tenant(self, request: Request) -> int:
        # Opção 1: Header personalizado
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            return int(tenant_header)
        
        # Opção 2: Subdomínio
        host = request.headers.get("host", "")
        if host.count(".") >= 2:
            subdomain = host.split(".")[0]
            return self._subdomain_to_tenant(subdomain)
        
        # Opção 3: Extrair do JWT (após autenticação)
        if hasattr(request.state, "user"):
            return request.state.user.escola_id
        
        return None
    
    async def _validate_tenant(self, tenant_id: int) -> bool:
        # Verificar se tenant existe e está ativo
        # Pode usar cache para performance
        pass
```

### Service com Tenant Awareness

```python
# app/services/base_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

class BaseTenantService:
    """Base service com suporte a multi-tenant."""
    
    def __init__(self, db: AsyncSession, request: Request):
        self.db = db
        self.tenant_id = request.state.tenant_id
    
    def _add_tenant_filter(self, query):
        """Adiciona filtro de tenant automaticamente."""
        # Override nas subclasses para tabelas específicas
        pass


class AlunoService(BaseTenantService):
    async def listar_alunos(self, **kwargs):
        query = select(Aluno).where(Aluno.escola_id == self.tenant_id)
        # ... resto da lógica
```

---

## 📁 Estrutura para Cloud

```
cloud/
├── terraform/                     # Infrastructure as Code
│   ├── environments/
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars
│   │   ├── staging/
│   │   └── production/
│   │
│   ├── modules/
│   │   ├── vpc/
│   │   ├── ecs/
│   │   ├── rds/
│   │   ├── redis/
│   │   ├── s3/
│   │   └── cdn/
│   │
│   └── main.tf
│
├── kubernetes/                    # K8s configs (alternativa ao ECS)
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   │
│   ├── overlays/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   │
│   └── kustomization.yaml
│
├── docker/
│   ├── api/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   ├── worker/
│   │   └── Dockerfile
│   └── nginx/
│       ├── Dockerfile
│       └── nginx.conf
│
├── scripts/
│   ├── deploy.sh
│   ├── rollback.sh
│   ├── migrate.sh
│   └── backup.sh
│
└── .github/
    └── workflows/
        ├── ci.yml
        ├── cd-dev.yml
        ├── cd-staging.yml
        └── cd-production.yml
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/cd-production.yml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: gestao-escolar-api
  ECS_CLUSTER: gestao-escolar-prod
  ECS_SERVICE: api-service

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: pytest tests/ -v --cov

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.build.outputs.image }}
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push image
        id: build
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service ${{ env.ECS_SERVICE }} \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster ${{ env.ECS_CLUSTER }} \
            --services ${{ env.ECS_SERVICE }}

  notify:
    needs: deploy
    runs-on: ubuntu-latest
    if: always()
    
    steps:
      - name: Notify on success
        if: ${{ needs.deploy.result == 'success' }}
        run: |
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -H 'Content-type: application/json' \
            -d '{"text":"✅ Deploy to production successful: ${{ github.ref }}"}'
      
      - name: Notify on failure
        if: ${{ needs.deploy.result == 'failure' }}
        run: |
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -H 'Content-type: application/json' \
            -d '{"text":"❌ Deploy to production failed: ${{ github.ref }}"}'
```

---

## 🔐 Segurança Cloud

### AWS Security Best Practices

```hcl
# terraform/modules/security/main.tf

# WAF para proteção contra ataques comuns
resource "aws_wafv2_web_acl" "main" {
  name        = "gestao-escolar-waf"
  description = "WAF for Gestão Escolar API"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting
  rule {
    name     = "rate-limit"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  # SQL Injection protection
  rule {
    name     = "sql-injection"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLInjection"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "GestaoEscolarWAF"
    sampled_requests_enabled   = true
  }
}

# Security Group restritivo
resource "aws_security_group" "api" {
  name        = "gestao-escolar-api-sg"
  description = "Security group for API"
  vpc_id      = var.vpc_id

  # Apenas ALB pode acessar a API
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# KMS para criptografia
resource "aws_kms_key" "main" {
  description             = "KMS key for Gestão Escolar"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# Secrets Manager para credenciais
resource "aws_secretsmanager_secret" "db_credentials" {
  name       = "gestao-escolar/db-credentials"
  kms_key_id = aws_kms_key.main.id
}
```

### Compliance LGPD

```python
# app/core/lgpd.py
"""
Compliance com LGPD (Lei Geral de Proteção de Dados).
"""

from typing import Dict, Any, List
from datetime import datetime
import hashlib

class LGPDService:
    """Service para compliance com LGPD."""
    
    # Dados sensíveis que precisam de tratamento especial
    SENSITIVE_FIELDS = {
        'cpf', 'rg', 'certidao_nascimento', 'cartao_sus', 'nis',
        'endereco', 'telefone', 'email', 'data_nascimento',
        'deficiencia', 'tipo_deficiencia', 'laudo', 'observacoes'
    }
    
    async def registrar_acesso_dados(
        self,
        user_id: int,
        tenant_id: int,
        entidade: str,
        entidade_id: int,
        campos_acessados: List[str],
        finalidade: str
    ):
        """Registra acesso a dados pessoais para auditoria."""
        log = AccessLog(
            user_id=user_id,
            tenant_id=tenant_id,
            entity_type=entidade,
            entity_id=entidade_id,
            fields_accessed=campos_acessados,
            purpose=finalidade,
            timestamp=datetime.utcnow(),
            ip_address=self._get_client_ip()
        )
        await self.db.add(log)
        await self.db.commit()
    
    async def anonimizar_dados(
        self,
        tenant_id: int,
        entidade: str,
        entidade_id: int
    ) -> Dict[str, Any]:
        """Anonimiza dados pessoais (direito ao esquecimento)."""
        # Implementar lógica de anonimização
        pass
    
    async def exportar_dados_titular(
        self,
        tenant_id: int,
        titular_id: int
    ) -> Dict[str, Any]:
        """Exporta todos os dados de um titular (direito de portabilidade)."""
        # Implementar exportação em formato estruturado
        pass
    
    def mascarar_cpf(self, cpf: str) -> str:
        """Mascara CPF para exibição."""
        if not cpf or len(cpf) != 11:
            return "***.***.***-**"
        return f"{cpf[:3]}.***.***.{cpf[-2:]}"
    
    def mascarar_email(self, email: str) -> str:
        """Mascara email para exibição."""
        if not email or '@' not in email:
            return "***@***.***"
        local, domain = email.split('@')
        return f"{local[:2]}***@{domain}"
```

---

## 💰 Modelo de Precificação SaaS

### Planos de Assinatura

```python
# app/models/subscription.py
from enum import Enum

class SubscriptionPlan(str, Enum):
    FREE = "free"           # Trial/Demo
    BASIC = "basic"         # Pequenas escolas
    PROFESSIONAL = "pro"    # Escolas médias
    ENTERPRISE = "enterprise"  # Redes de ensino

PLAN_LIMITS = {
    SubscriptionPlan.FREE: {
        "max_alunos": 50,
        "max_funcionarios": 10,
        "max_storage_gb": 1,
        "relatorios_mes": 5,
        "suporte": "email",
        "preco_mensal": 0,
    },
    SubscriptionPlan.BASIC: {
        "max_alunos": 300,
        "max_funcionarios": 50,
        "max_storage_gb": 10,
        "relatorios_mes": 50,
        "suporte": "email",
        "preco_mensal": 199,
    },
    SubscriptionPlan.PROFESSIONAL: {
        "max_alunos": 1000,
        "max_funcionarios": 150,
        "max_storage_gb": 50,
        "relatorios_mes": -1,  # Ilimitado
        "suporte": "chat",
        "preco_mensal": 499,
    },
    SubscriptionPlan.ENTERPRISE: {
        "max_alunos": -1,      # Ilimitado
        "max_funcionarios": -1,
        "max_storage_gb": -1,
        "relatorios_mes": -1,
        "suporte": "dedicado",
        "preco_mensal": "custom",  # Negociado
    },
}
```

### Tabela de Preços

| Plano | Alunos | Funcionários | Storage | Preço/mês |
|-------|--------|--------------|---------|-----------|
| Free (Trial) | 50 | 10 | 1 GB | R$ 0 |
| Basic | 300 | 50 | 10 GB | R$ 199 |
| Professional | 1.000 | 150 | 50 GB | R$ 499 |
| Enterprise | Ilimitado | Ilimitado | Ilimitado | Sob consulta |

---

## 📊 Monitoramento e Observabilidade

### Stack de Observabilidade

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.2.0
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3001:3000"

  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

  jaeger:
    image: jaegertracing/all-in-one:1.52
    ports:
      - "16686:16686"  # UI
      - "6831:6831/udp"  # Jaeger agent

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

### Métricas da Aplicação

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Contadores
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status', 'tenant']
)

# Histogramas
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint', 'tenant'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Gauges
active_connections = Gauge(
    'active_db_connections',
    'Number of active database connections',
    ['tenant']
)

# Métricas de negócio
alunos_ativos = Gauge(
    'alunos_ativos_total',
    'Total de alunos ativos',
    ['tenant', 'serie']
)

relatorios_gerados = Counter(
    'relatorios_gerados_total',
    'Total de relatórios gerados',
    ['tenant', 'tipo']
)
```

---

## 📋 Cronograma de Implantação Cloud

### Fase 1: Infraestrutura (3-4 semanas)

#### Semana 1-2: Setup AWS/GCP
- [ ] Criar conta AWS/GCP organizacional
- [ ] Configurar IAM e políticas
- [ ] Criar VPC e subnets
- [ ] Configurar módulos Terraform
- [ ] Setup de CI/CD básico

#### Semana 3-4: Serviços Core
- [ ] Provisionar RDS MySQL
- [ ] Configurar ElastiCache Redis
- [ ] Setup ECS/Cloud Run
- [ ] Configurar S3 para storage
- [ ] Setup de logs e métricas

### Fase 2: Deploy Aplicação (2-3 semanas)

#### Semana 5-6: Deploy API
- [ ] Build e push de imagens Docker
- [ ] Deploy em ambiente de staging
- [ ] Configurar variáveis de ambiente
- [ ] Testes de integração
- [ ] Configurar domínio e SSL

#### Semana 7: Frontend e CDN
- [ ] Deploy frontend no S3/CloudFront
- [ ] Configurar CDN
- [ ] Testes E2E completos
- [ ] Performance tuning

### Fase 3: Multi-Tenant e Segurança (2-3 semanas)

#### Semana 8-9: Multi-Tenant
- [ ] Implementar middleware de tenant
- [ ] Migrar dados existentes
- [ ] Testes de isolamento
- [ ] Configurar onboarding de novos tenants

#### Semana 10: Segurança e Compliance
- [ ] Configurar WAF
- [ ] Implementar LGPD compliance
- [ ] Audit logging
- [ ] Penetration testing

### Fase 4: Go-Live (1-2 semanas)

#### Semana 11-12: Produção
- [ ] Migração final de dados
- [ ] Deploy em produção
- [ ] Monitoramento ativo
- [ ] Suporte ao cliente
- [ ] Documentação final

---

## 💰 Estimativa de Custos Cloud (AWS)

### Custos Mensais Estimados

| Serviço | Especificação | Custo/mês |
|---------|---------------|-----------|
| ECS Fargate | 2 tasks (1 vCPU, 2GB) | $120 |
| RDS MySQL | db.t3.medium Multi-AZ | $150 |
| ElastiCache Redis | cache.t3.micro | $25 |
| ALB | Application Load Balancer | $25 |
| S3 | 100 GB + requests | $10 |
| CloudFront | 100 GB transfer | $15 |
| Route 53 | Hosted zone + queries | $5 |
| CloudWatch | Logs + Metrics | $30 |
| Secrets Manager | 10 secrets | $5 |
| WAF | Web ACL + Rules | $15 |
| **Total Base** | | **~$400/mês** |

### Custos por Número de Tenants

| Tenants | RDS | Redis | ECS | Total/mês |
|---------|-----|-------|-----|-----------|
| 1-10 | db.t3.medium | cache.t3.micro | 2 tasks | ~$400 |
| 10-50 | db.t3.large | cache.t3.small | 4 tasks | ~$700 |
| 50-100 | db.r5.large | cache.m5.large | 6 tasks | ~$1.500 |
| 100+ | db.r5.xlarge Multi-AZ | Cluster | Auto-scale | ~$3.000+ |

---

## ✅ Checklist de Pré-Requisitos Cloud

- [ ] Conta AWS/GCP/Azure criada
- [ ] Cartão de crédito cadastrado
- [ ] Domínio registrado
- [ ] Certificado SSL
- [ ] Equipe treinada em cloud
- [ ] Plano de disaster recovery
- [ ] Política de backup definida
- [ ] Acordo de nível de serviço (SLA)

---

## 📚 Referências

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [LGPD - Lei Geral de Proteção de Dados](http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- [12 Factor App](https://12factor.net/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
