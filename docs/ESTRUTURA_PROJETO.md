# Sistema de Gestão Escolar - Estrutura do Projeto

## 📁 Estrutura de Diretórios

```
c:\gestao\
├── src/                          # Código fonte principal
│   ├── core/                     # Módulos essenciais
│   ├── models/                   # Classes de domínio
│   ├── services/                 # Lógica de negócio
│   ├── ui/                       # Interfaces gráficas
│   ├── utils/                    # Utilitários
│   ├── relatorios/              # Geração de relatórios
│   ├── interfaces/              # Interfaces especializadas
│   ├── gestores/                # Gerenciadores
│   ├── importadores/            # Scripts de importação
│   └── avaliacoes/              # Sistema de avaliações
│
├── scripts/                      # Scripts utilitários
│   ├── manutencao/              # Manutenção de BD
│   ├── migracao/                # Migração de dados
│   ├── diagnostico/             # Análise e verificação
│   ├── exportacao/              # Exportação de dados
│   ├── desenvolvimento/         # Ferramentas dev
│   └── auxiliares/              # Scripts auxiliares
│
├── automacao/                    # Automação
│   ├── batch/                   # Arquivos .bat
│   ├── powershell/              # Scripts PowerShell
│   └── python/                  # Scripts Python
│
├── tests/                       # Testes
├── docs/                        # Documentação
├── config/                      # Configurações
├── assets/                      # Recursos
├── dados/                       # Dados
└── main.py                      # Ponto de entrada
```

## 🎯 Guia Rápido

### Importando Módulos

**Antes:**
```python
from config import perfis_habilitados
from conexao import conectar_bd
```

**Agora:**
```python
from src.core.config import perfis_habilitados
from src.core.conexao import conectar_bd
```

### Localizando Arquivos

| O que procuro? | Onde está? |
|---------------|------------|
| Configurações | `src/core/` |
| Relatórios | `src/relatorios/` |
| Interfaces de cadastro | `src/interfaces/` |
| Scripts de verificação | `scripts/diagnostico/` |
| Scripts de migração | `scripts/migracao/` |
| Arquivos .bat | `automacao/batch/` |
| Testes | `tests/` |
| Documentação | `docs/` |

## 📝 Para Desenvolvedores

1. **Adicionar novo relatório**: `src/relatorios/`
2. **Adicionar nova interface**: `src/interfaces/`
3. **Adicionar script de manutenção**: `scripts/manutencao/`
4. **Adicionar teste**: `tests/`

## 🔧 Manutenção

- Todos os imports foram atualizados automaticamente
- 174 arquivos corrigidos
- 436 imports atualizados
- Estrutura modular e escalável

## 📖 Mais Informações

Consulte [ORGANIZACAO_PROJETO.md](ORGANIZACAO_PROJETO.md) para documentação completa.
