# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Não Lançado]

### Planejado
- Relatório de Conselho de Classe
- Alertas automáticos de frequência (limiar de faltas)
- Importação de alunos via CSV/Excel
- Dark mode
- Filtros avançados na tabela principal

## [2.0.0] - 2026-01-15

### Adicionado
- Sistema de configuração centralizada com Settings (Pydantic)
- Feature flags para habilitar/desabilitar funcionalidades
- Dashboard com gráfico de pizza por série/turma
- Gráfico de movimento mensal (barras empilhadas)
- Sistema de autenticação com perfis (Admin, Coordenador, Professor)
- Gerenciamento de licenças de funcionários
- Importador de horários do GEDUC via Selenium
- Exportador de dados para GEDUC
- Banco de questões BNCC com interface completa
- Sistema de avaliações com gabaritos e correção
- Backup automático para Google Drive
- Pool de conexões MySQL com retry automático
- Logging estruturado com níveis configuráveis
- Dashboard específico para coordenador e professor
- Crachás individuais de alunos
- Controle de livros faltantes
- 20+ relatórios em PDF (boletins, atas, declarações, históricos)

### Modificado
- Refatoração completa de `main.py` com validação de settings no startup
- Migração de `services/report_service.py` (2163 linhas) para package `services/reports/`
- Divisão de `ui/detalhes.py` em package `ui/detalhes/` (exibir.py, acoes.py)
- Divisão de `ui/actions.py` em mixins por domínio (aluno, funcionario, matricula, etc)
- Unificação de acesso ao banco via `db/connection.py` (get_cursor, get_connection)
- Padronização de imports (src.* em todo projeto)
- Cache do dashboard com TTL de 10 minutos
- Otimização de queries SELECT eliminando SELECT *

### Corrigido
- Movimento mensal mostrando 66 ao invés de 295 alunos (data_matricula NULL)
- Dashboard mostrando 341 ao invés de 342 alunos (query de transferidos incorreta)
- Queries com `services.X` ao invés de `src.services.X` em testes
- 5 falhas de teste em `test_utils.py`
- 231 linhas de patches incorretos em 12 arquivos de teste
- Imports circulares entre módulos
- Memory leaks no pool de conexões

### Removido
- 20 testes obsoletos movidos para `tests/_obsoletos/`
- 21 scripts dependentes de DB movidos para `tests/_db_scripts/`
- Dependências circulares entre módulos

## [1.0.0] - 2025-03-01

### Adicionado
- Versão inicial do sistema
- CRUD de alunos, funcionários e matrículas
- Cadastro de notas e frequência
- Interface administrativa (escolas, disciplinas, turmas, séries)
- Relatórios básicos (listas, declarações)
- Histórico escolar
- Grade de horários
- Transição de ano letivo

---

## Tipos de mudanças
- **Adicionado** para novas funcionalidades
- **Modificado** para mudanças em funcionalidades existentes
- **Depreciado** para funcionalidades que serão removidas
- **Removido** para funcionalidades removidas
- **Corrigido** para correções de bugs
- **Segurança** para correções de vulnerabilidades

## Links de Comparação
[Não Lançado]: https://github.com/seu-usuario/gestao-escolar/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/seu-usuario/gestao-escolar/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/seu-usuario/gestao-escolar/releases/tag/v1.0.0
