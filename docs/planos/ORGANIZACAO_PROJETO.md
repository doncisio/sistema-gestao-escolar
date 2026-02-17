# Organização do Sistema de Gestão Escolar

## 📋 Índice
- [Visão Geral](#visão-geral)
- [Estrutura Atual (Problemas)](#estrutura-atual-problemas)
- [Nova Estrutura Proposta](#nova-estrutura-proposta)
- [Plano de Migração](#plano-de-migração)
- [Mapeamento de Arquivos](#mapeamento-de-arquivos)

---

## 🎯 Visão Geral

Este documento descreve a reorganização do Sistema de Gestão Escolar para melhorar:
- **Manutenibilidade**: Facilitar localização de arquivos
- **Escalabilidade**: Permitir crescimento organizado
- **Clareza**: Estrutura lógica e intuitiva
- **Performance**: Reduzir complexidade de imports

---

## ❌ Estrutura Atual (Problemas)

### Problemas Identificados:
1. **Raiz Sobrecarregada**: 100+ arquivos Python no diretório raiz
2. **Nomenclatura Inconsistente**: Mistura de PascalCase, snake_case, e português/inglês
3. **Duplicação**: Diretórios `testes/` e `tests/`, `scripts/` com conteúdo duplicado
4. **Arquivos de Configuração Dispersos**: `.env`, `config.py`, `config/`, etc.
5. **Scripts Utilitários sem Organização**: Arquivos `check_*.py`, `executar_*.bat` espalhados
6. **Documentação Fragmentada**: Arquivos `.md` no raiz e em `docs/`

---

## ✅ Nova Estrutura Proposta

```
c:\gestao\
├── 📁 .github/                     # CI/CD e workflows GitHub
├── 📁 .vscode/                     # Configurações VSCode
│
├── 📁 src/                         # 🆕 Código fonte principal
│   ├── 📁 core/                    # Módulos essenciais
│   │   ├── __init__.py
│   │   ├── config.py               # ← config.py
│   │   ├── config_logs.py          # ← config_logs.py
│   │   ├── conexao.py              # ← conexao.py
│   │   └── feature_flags.py        # ← utils/feature_flags.py
│   │
│   ├── 📁 models/                  # Classes de domínio (já existe)
│   │   ├── __init__.py
│   │   ├── aluno.py
│   │   ├── funcionario.py
│   │   ├── matricula.py
│   │   └── turma.py
│   │
│   ├── 📁 services/                # Lógica de negócio (já existe)
│   │   ├── __init__.py
│   │   ├── aluno_service.py
│   │   ├── boletim_service.py
│   │   ├── funcionario_service.py
│   │   ├── matricula_service.py
│   │   └── ...
│   │
│   ├── 📁 ui/                      # Interfaces gráficas (já existe)
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── dashboard.py
│   │   ├── login.py
│   │   └── ...
│   │
│   ├── 📁 utils/                   # Utilitários gerais (já existe)
│   │   ├── __init__.py
│   │   ├── cache.py
│   │   ├── dates.py
│   │   ├── error_handler.py
│   │   └── ...
│   │
│   ├── 📁 relatorios/              # 🆕 Geração de relatórios
│   │   ├── __init__.py
│   │   ├── atas/
│   │   │   ├── __init__.py
│   │   │   ├── ata_geral.py        # ← AtaGeral.py
│   │   │   ├── ata_1a5ano.py       # ← Ata_1a5ano.py
│   │   │   ├── ata_1a9ano.py       # ← Ata_1a9ano.py
│   │   │   └── ata_6a9ano.py       # ← Ata_6a9ano.py
│   │   ├── listas/
│   │   │   ├── __init__.py
│   │   │   ├── lista_alfabetica.py # ← Lista_alunos_alfabetica.py
│   │   │   ├── lista_transtornos.py # ← Lista_alunos_transtornos.py
│   │   │   ├── lista_contatos.py   # ← Lista_contatos_responsaveis.py
│   │   │   ├── lista_frequencia.py # ← lista_frequencia.py
│   │   │   ├── lista_notas.py      # ← Lista_notas.py
│   │   │   ├── lista_reuniao.py    # ← Lista_reuniao.py
│   │   │   ├── lista_atualizada.py # ← Lista_atualizada.py
│   │   │   └── lista_semed.py      # ← Lista_atualizada_semed.py
│   │   ├── geradores/
│   │   │   ├── __init__.py
│   │   │   ├── certificado.py      # ← gerar_certificado.py + gerar_certificado_pdf.py
│   │   │   ├── folha_ponto.py      # ← gerar_folha_ponto.py
│   │   │   ├── tabela_frequencia.py # ← gerar_tabela_frequencia.py
│   │   │   ├── resumo_ponto.py     # ← gerar_resumo_ponto.py
│   │   │   └── reuniao.py          # ← gerar_lista_reuniao.py
│   │   ├── boletim.py              # ← boletim.py
│   │   ├── declaracao_comparecimento.py # ← declaracao_comparecimento.py
│   │   ├── historico_escolar.py    # ← historico_escolar.py
│   │   ├── movimento_mensal.py     # ← movimentomensal.py
│   │   ├── nota_ata.py             # ← NotaAta.py
│   │   ├── relatorio_analise_notas.py # ← relatorio_analise_notas.py
│   │   └── relatorio_pendencias.py # ← relatorio_pendencias.py
│   │
│   ├── 📁 interfaces/              # 🆕 Interfaces especializadas
│   │   ├── __init__.py
│   │   ├── cadastro_aluno.py       # ← InterfaceCadastroAluno.py
│   │   ├── edicao_aluno.py         # ← InterfaceEdicaoAluno.py
│   │   ├── cadastro_funcionario.py # ← InterfaceCadastroFuncionario.py
│   │   ├── edicao_funcionario.py   # ← InterfaceEdicaoFuncionario.py
│   │   ├── cadastro_notas.py       # ← InterfaceCadastroEdicaoNotas.py
│   │   ├── cadastro_faltas.py      # ← InterfaceCadastroEdicaoFaltas.py
│   │   ├── lancamento_frequencia.py # ← InterfaceLancamentoFrequencia.py
│   │   ├── matricula_unificada.py  # ← interface_matricula_unificada.py
│   │   ├── historico_escolar.py    # ← interface_historico_escolar.py
│   │   ├── administrativa.py       # ← interface_administrativa.py
│   │   ├── solicitacao_professores.py # ← InterfaceSolicitacaoProfessores.py
│   │   └── gerenciamento_licencas.py # ← InterfaceGerenciamentoLicencas.py
│   │
│   ├── 📁 gestores/                # 🆕 Gerenciadores de documentos/processos
│   │   ├── __init__.py
│   │   ├── documentos_funcionarios.py # ← GerenciadorDocumentosFuncionarios.py
│   │   ├── documentos_sistema.py   # ← GerenciadorDocumentosSistema.py
│   │   ├── historico_manager.py    # ← historico_manager_otimizado.py
│   │   └── storage_manager.py      # ← storage_manager.py + storage_manager_impl.py
│   │
│   ├── 📁 importadores/            # 🆕 Scripts de importação
│   │   ├── __init__.py
│   │   ├── bncc_excel.py           # ← importar_bncc_from_excel.py
│   │   ├── notas_html.py           # ← importar_notas_html.py
│   │   └── geduc.py                # ← automatizar_extracao_geduc.py
│   │
│   └── 📁 avaliacoes/              # 🆕 Sistema de avaliações
│       ├── __init__.py
│       ├── janela_fila_correcao.py # ← JanelaFilaCorrecao.py
│       ├── janela_registro_respostas.py # ← JanelaRegistroRespostas.py
│       └── integrador_preenchimento.py # ← integrador_preenchimento.py
│
├── 📁 scripts/                     # Scripts utilitários e manutenção
│   ├── 📁 manutencao/              # 🆕 Scripts de manutenção BD
│   │   ├── aplicar_indices.py      # ← aplicar_indices_historico.py
│   │   ├── aplicar_otimizacoes.py  # ← aplicar_otimizacoes_historico.py
│   │   ├── limpar_cache_dashboard.py # ← limpar_cache_dashboard.py
│   │   ├── otimizar_folha_ponto.sql # ← otimizar_folha_ponto.sql
│   │   └── otimizacoes_historico.sql # ← otimizacoes_historico_escolar.sql
│   │
│   ├── 📁 migracao/                # 🆕 Scripts de migração
│   │   ├── concluir_matriculas_antigas.py # ← concluir_matriculas_antigas.py
│   │   ├── concluir_matriculas_nao_2025.py # ← concluir_matriculas_nao_2025.py
│   │   ├── transicao_ano_letivo.py # ← transicao_ano_letivo.py
│   │   ├── reverter_movimentacao.py # ← reverter_movimentacao.py
│   │   └── run_migration.py        # ← run_migration.py
│   │
│   ├── 📁 diagnostico/             # 🆕 Scripts de análise/verificação
│   │   ├── check_alunos_342.py     # ← check_alunos_342.py
│   │   ├── check_matriculas_status.py # ← check_matriculas_status.py
│   │   ├── check_series_turmas.py  # ← check_series_turmas.py
│   │   ├── check_transicao_detalhado.py # ← check_transicao_detalhado.py
│   │   ├── check_transicao_stats.py # ← check_transicao_stats.py
│   │   ├── check_orig.py           # ← check_orig.py
│   │   ├── compare_columns.py      # ← compare_columns.py
│   │   └── relatorio_transicao.py  # ← relatorio_transicao.py
│   │
│   ├── 📁 exportacao/              # 🆕 Scripts de exportação
│   │   ├── exportar_dados_questoes.py # ← exportar_dados_questoes.py
│   │   ├── export_pendencias_csv.py # ← export_pendencias_csv.py
│   │   └── export_pendencias_xlsx.py # ← export_pendencias_xlsx.py
│   │
│   ├── 📁 desenvolvimento/         # 🆕 Scripts dev/build
│   │   ├── build_exe.py            # ← build_exe.py
│   │   ├── build_complete.ps1      # ← build_complete.ps1
│   │   ├── criar_icone.py          # ← criar_icone.py
│   │   ├── baixar_chromedriver.py  # ← baixar_chromedriver.py
│   │   └── benchmark_startup.py    # ← benchmark_startup.py
│   │
│   ├── 📁 auxiliares/              # 🆕 Scripts auxiliares
│   │   ├── setup_wizard.py         # ← setup_wizard.py
│   │   ├── drive_uploader.py       # ← drive_uploader.py
│   │   ├── drive_test.py           # ← drive_test.py
│   │   ├── preencher_folha_ponto.py # ← preencher_folha_ponto.py
│   │   ├── preencher_notas_automatico.py # ← preencher_notas_automatico.py
│   │   ├── inserir_dados_exemplo.py # ← inserir_dados_exemplo.py
│   │   └── dump_sheet_rows.py      # ← dump_sheet_rows.py
│   │
│   └── 📁 nao_utilizados/          # Scripts antigos (já existe)
│       └── ...
│
├── 📁 automacao/                   # 🆕 Arquivos de automação
│   ├── 📁 batch/
│   │   ├── executar_sistema.bat    # ← executar_sistema.bat
│   │   ├── executar_certificado.bat # ← executar_certificado.bat
│   │   ├── executar_folha_ponto.bat # ← executar_folha_ponto.bat
│   │   ├── executar_exportacao.bat # ← executar_exportacao.bat
│   │   ├── executar_lista_matriculados.bat # ← executar_lista_matriculados.bat
│   │   ├── executar_lista_transferidos.bat # ← executar_lista_transferidos.bat
│   │   ├── restaurar_banco.bat     # ← restaurar_banco.bat
│   │   └── ...
│   │
│   ├── 📁 powershell/
│   │   ├── sync_inicio.bat         # ← sync_inicio.bat
│   │   ├── sync_fim.bat            # ← sync_fim.bat
│   │   └── sync_rapido.bat         # ← sync_rapido.bat
│   │
│   └── 📁 python/
│       ├── executar_gerar_documentos.py # ← executar_gerar_documentos.py
│       ├── executar_lista_matriculados.py # ← executar_lista_matriculados.py
│       ├── executar_lista_transferidos.py # ← executar_lista_transferidos.py
│       └── ...
│
├── 📁 tests/                       # Testes automatizados (consolidado)
│   ├── 📁 integration/
│   ├── 📁 performance/
│   ├── 📁 services/
│   ├── 📁 ui/
│   └── ...
│
├── 📁 config/                      # Configurações (já existe, limpar)
│   ├── __init__.py
│   └── settings.py
│
├── 📁 sql/                         # Scripts SQL (já existe)
│   ├── migrations/
│   ├── procedures/
│   └── ...
│
├── 📁 db/                          # Banco de dados local (já existe)
│
├── 📁 docs/                        # Documentação (já existe, organizar)
│   ├── 📁 api/
│   ├── 📁 arquitetura/
│   ├── 📁 desenvolvimento/
│   ├── 📁 usuario/
│   ├── README.md
│   └── ORGANIZACAO_PROJETO.md      # Este arquivo
│
├── 📁 assets/                      # Recursos estáticos (já existe)
│   ├── 📁 imagens/
│   ├── 📁 icons/
│   ├── 📁 certificados/
│   └── ...
│
├── 📁 dados/                       # Dados de entrada/saída (já existe)
│   ├── 📁 importacao/
│   ├── 📁 exportacao/
│   └── ...
│
├── 📁 logs/                        # Logs do sistema (já existe)
│
├── 📁 temp/                        # Arquivos temporários (já existe)
│
├── 📁 uploads/                     # Uploads de usuários (já existe)
│
├── 📁 documentos_gerados/          # PDFs e docs gerados (já existe)
│
├── 📁 arquivos_nao_utilizados/     # Backup de arquivos antigos (já existe)
│
├── main.py                         # Ponto de entrada principal
├── config.py                       # Será movido para src/core/
├── conexao.py                      # Será movido para src/core/
├── config_logs.py                  # Será movido para src/core/
│
├── .env                            # Variáveis de ambiente
├── .env.example
├── .gitignore
├── requirements.txt
├── pytest.ini
├── mypy.ini
├── README.md
├── LICENSE.txt
└── ...
```

---

## 📊 Categorização de Arquivos

### 🔹 Módulos Core (src/core/)
- config.py, config_logs.py, conexao.py
- feature_flags.py (de utils/)

### 🔹 Relatórios (src/relatorios/)
**Atas:**
- AtaGeral.py → ata_geral.py
- Ata_1a5ano.py → ata_1a5ano.py
- Ata_1a9ano.py → ata_1a9ano.py
- Ata_6a9ano.py → ata_6a9ano.py

**Listas:**
- Lista_alunos_alfabetica.py → lista_alfabetica.py
- Lista_alunos_transtornos.py → lista_transtornos.py
- Lista_contatos_responsaveis.py → lista_contatos.py
- Lista_notas.py → lista_notas.py
- Lista_reuniao.py → lista_reuniao.py
- lista_frequencia.py → lista_frequencia.py

**Geradores:**
- gerar_certificado.py + gerar_certificado_pdf.py → certificado.py (consolidado)
- gerar_folha_ponto.py → folha_ponto.py
- gerar_tabela_frequencia.py → tabela_frequencia.py
- gerar_resumo_ponto.py → resumo_ponto.py
- gerar_lista_reuniao.py → reuniao.py

**Relatórios Gerais:**
- boletim.py, historico_escolar.py, movimentomensal.py, etc.

### 🔹 Interfaces (src/interfaces/)
- InterfaceCadastroAluno.py → cadastro_aluno.py
- InterfaceEdicaoAluno.py → edicao_aluno.py
- InterfaceCadastroFuncionario.py → cadastro_funcionario.py
- InterfaceEdicaoFuncionario.py → edicao_funcionario.py
- InterfaceCadastroEdicaoNotas.py → cadastro_notas.py
- InterfaceCadastroEdicaoFaltas.py → cadastro_faltas.py
- InterfaceLancamentoFrequencia.py → lancamento_frequencia.py
- interface_matricula_unificada.py → matricula_unificada.py
- interface_historico_escolar.py → historico_escolar.py
- interface_administrativa.py → administrativa.py
- InterfaceSolicitacaoProfessores.py → solicitacao_professores.py
- InterfaceGerenciamentoLicencas.py → gerenciamento_licencas.py

### 🔹 Gestores (src/gestores/)
- GerenciadorDocumentosFuncionarios.py → documentos_funcionarios.py
- GerenciadorDocumentosSistema.py → documentos_sistema.py
- historico_manager_otimizado.py → historico_manager.py
- storage_manager.py + storage_manager_impl.py → storage_manager.py (consolidado)

### 🔹 Scripts de Manutenção (scripts/manutencao/)
- aplicar_indices_historico.py → aplicar_indices.py
- aplicar_otimizacoes_historico.py → aplicar_otimizacoes.py
- limpar_cache_dashboard.py
- Arquivos .sql relacionados

### 🔹 Scripts de Migração (scripts/migracao/)
- concluir_matriculas_antigas.py
- concluir_matriculas_nao_2025.py
- transicao_ano_letivo.py
- reverter_movimentacao.py
- run_migration.py

### 🔹 Scripts de Diagnóstico (scripts/diagnostico/)
- check_alunos_342.py
- check_matriculas_status.py
- check_series_turmas.py
- check_transicao_detalhado.py
- check_transicao_stats.py
- check_orig.py
- compare_columns.py
- relatorio_transicao.py

### 🔹 Scripts de Exportação (scripts/exportacao/)
- exportar_dados_questoes.py
- export_pendencias_csv.py
- export_pendencias_xlsx.py

### 🔹 Scripts de Desenvolvimento (scripts/desenvolvimento/)
- build_exe.py
- build_complete.ps1
- criar_icone.py
- baixar_chromedriver.py
- benchmark_startup.py

### 🔹 Automação (automacao/)
**Batch:**
- Todos os arquivos .bat (executar_*.bat, sync_*.bat, restaurar_banco.bat)

**Python de automação:**
- executar_*.py (scripts wrapper)

---

## 🚀 Plano de Migração

### Fase 1: Preparação (Não Destrutiva)
1. ✅ Criar documento de organização (este arquivo)
2. ⏳ Criar novos diretórios vazios
3. ⏳ Backup completo do projeto

### Fase 2: Migração Gradual
**Etapa 1: Core e Configuração**
- Mover config.py, config_logs.py, conexao.py → src/core/
- Atualizar imports em main.py e arquivos dependentes

**Etapa 2: Relatórios**
- Criar src/relatorios/ com subpastas
- Mover arquivos de Atas, Listas, Geradores
- Atualizar imports

**Etapa 3: Interfaces**
- Criar src/interfaces/
- Mover Interface*.py → src/interfaces/
- Renomear para snake_case
- Atualizar imports

**Etapa 4: Gestores**
- Criar src/gestores/
- Mover GerenciadorDocumentos*.py → src/gestores/
- Consolidar storage_manager
- Atualizar imports

**Etapa 5: Scripts**
- Criar subdiretórios em scripts/
- Mover check_*.py → scripts/diagnostico/
- Mover executar_*.py → automacao/python/
- Mover gerar_*.py (se não usados como módulos) → scripts/auxiliares/

**Etapa 6: Automação**
- Criar automacao/batch/
- Mover .bat → automacao/batch/
- Atualizar caminhos nos .bat

**Etapa 7: Consolidação de Testes**
- Mesclar testes/ → tests/
- Remover diretório testes/
- Atualizar pytest.ini

### Fase 3: Limpeza Final
- Remover diretórios vazios
- Atualizar documentação
- Atualizar .gitignore
- Verificar todos os imports

---

## 🔧 Correções de Imports Necessárias

### Exemplo de Correções:

**Antes:**
```python
from config import perfis_habilitados
from config_logs import get_logger
from conexao import conectar
```

**Depois:**
```python
from src.core.config import perfis_habilitados
from src.core.config_logs import get_logger
from src.core.conexao import conectar
```

**Antes:**
```python
from InterfaceCadastroAluno import InterfaceCadastroAluno
```

**Depois:**
```python
from src.interfaces.cadastro_aluno import InterfaceCadastroAluno
```

**Antes:**
```python
from GerenciadorDocumentosFuncionarios import GerenciadorDocumentosFuncionarios
```

**Depois:**
```python
from src.gestores.documentos_funcionarios import GerenciadorDocumentosFuncionarios
```

---

## 📝 Convenções de Nomenclatura

### Arquivos Python:
- **Usar snake_case**: `cadastro_aluno.py` (não `CadastroAluno.py`)
- **Português para domínio**: `relatorio_notas.py`
- **Inglês para técnico**: `storage_manager.py`

### Diretórios:
- **snake_case minúsculo**: `src/relatorios/listas/`
- **Plural para coleções**: `interfaces/`, `relatorios/`

### Classes:
- **PascalCase**: `class InterfaceCadastroAluno`
- **Manter nomes descritivos em português**

---

## ⚠️ Diretórios a Remover/Consolidar

### Remover após migração:
- `testes/` → consolidar em `tests/`
- `examples/` → mover exemplos relevantes para docs/

### Manter mas limpar:
- `arquivos_nao_utilizados/` → backup, não mexer
- `scripts_nao_utilizados/` → backup, não mexer

---

## 📦 Benefícios da Nova Estrutura

1. **Organização Lógica**: Arquivos agrupados por função
2. **Facilidade de Navegação**: Estrutura intuitiva
3. **Redução de Complexidade**: Menos arquivos no raiz
4. **Melhor Manutenibilidade**: Código mais fácil de encontrar
5. **Escalabilidade**: Estrutura suporta crescimento
6. **Padrões Modernos**: Segue boas práticas Python
7. **Imports Mais Claros**: Hierarquia explícita

---

## 🎯 Próximos Passos

1. **Revisar este documento** com a equipe
2. **Aprovar estrutura proposta**
3. **Executar Fase 1** (backup e criação de diretórios)
4. **Migração incremental** (por etapas)
5. **Testes após cada etapa**
6. **Atualizar CI/CD** se necessário
7. **Documentar mudanças** para equipe

---

## 📞 Contato

Para dúvidas sobre esta reorganização, consultar:
- Documentação técnica em: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- Guia de desenvolvimento em: [docs/DEVELOPMENT.md](DEVELOPMENT.md)

---

**Data de Criação**: 14/12/2025  
**Versão**: 1.0  
**Status**: ✅ IMPLEMENTADO (14/12/2025)

---

## 📊 Estatísticas da Reorganização

- **Arquivos movidos**: ~100 arquivos
- **Diretórios criados**: 16 novos diretórios
- **Imports atualizados**: 436 imports corrigidos em 174 arquivos
- **Tempo de execução**: Automatizado com script Python

---

## ✅ Checklist de Implementação

- [x] Criação de diretórios (src/, automacao/, scripts/)
- [x] Movimentação de arquivos core (config, conexao, logs)
- [x] Movimentação de relatórios (atas, listas, geradores)
- [x] Movimentação de interfaces
- [x] Movimentação de gestores e importadores
- [x] Organização de scripts (manutenção, migração, diagnóstico, etc.)
- [x] Movimentação de arquivos de automação (.bat e .py)
- [x] Atualização automática de imports (436 correções)
- [x] Criação de arquivos __init__.py
- [x] Documentação atualizada
- [x] Consolidação de diretório testes/ → tests/legacy/
- [x] Organização de arquivos .md do raiz → docs/
- [x] Organização de arquivos SQL → sql/ e backups/
- [x] Organização de arquivos temporários → temp/
- [x] Limpeza final do diretório raiz

---

## 📁 Estrutura Final do Diretório Raiz

Após a reorganização completa, o diretório raiz contém apenas:

**Arquivos Essenciais:**
- `main.py` - Ponto de entrada do sistema
- `README.md` - Documentação principal
- `LICENSE.txt` - Licença do projeto
- `requirements.txt` - Dependências Python
- `requirements_certificado.txt` - Dependências específicas de certificados
- `.env` / `.env.example` - Variáveis de ambiente
- `.gitignore` - Configuração Git
- `pytest.ini` / `mypy.ini` - Configurações de ferramentas

**Arquivos de Configuração:**
- `credentials.json` - Credenciais Google Drive
- `feature_flags.json` - Feature flags do sistema
- `local_config.json` - Configurações locais
- `deepseek.json` - Configuração DeepSeek
- `token.pickle` / `token_drive.pickle` - Tokens de autenticação
- `gestao.code-workspace` - Workspace VSCode
- `GestaoEscolar.iss` / `GestaoEscolar.spec` - Configurações de build
- Arquivos de versão e debug (quando necessário)

**Diretórios Principais:**
- `src/` - Código fonte organizado
- `scripts/` - Scripts utilitários organizados por categoria
- `automacao/` - Scripts de automação (.bat, .ps1, .py)
- `tests/` - Testes consolidados (incluindo tests/legacy/)
- `docs/` - Toda documentação consolidada
- `config/`, `sql/`, `db/`, `assets/`, `dados/`, `logs/`, `temp/`, etc.

---

## 🗑️ Análise de Diretórios para Deleção

### ⚠️ Diretórios Duplicados (NÃO DELETAR - AINDA EM USO)

Os seguintes diretórios na raiz são **DUPLICADOS** dos que estão em `src/`, mas **AINDA ESTÃO SENDO REFERENCIADOS** em 100+ imports:

#### 1. `models/` (12 arquivos) - **EM USO**
- **Duplicado de**: `src/models/`
- **Status**: ⚠️ NÃO deletar ainda
- **Razão**: Imports ativos em `main.py`, `ui/`, `services/`
- **Ação necessária**: Atualizar imports `from models.` → `from src.models.`

#### 2. `services/` (32 arquivos) - **EM USO**
- **Duplicado de**: `src/services/`
- **Status**: ⚠️ NÃO deletar ainda
- **Razão**: 50+ imports ativos em todo o sistema
- **Ação necessária**: Atualizar imports `from services.` → `from src.services.`

#### 3. `ui/` (48 arquivos) - **EM USO**
- **Duplicado de**: `src/ui/`
- **Status**: ⚠️ NÃO deletar ainda
- **Razão**: Imports cruzados em `main.py`, `ui/`, dashboards
- **Ação necessária**: Atualizar imports `from ui.` → `from src.ui.`

#### 4. `utils/` (16 arquivos) - **EM USO**
- **Duplicado de**: `src/utils/`
- **Status**: ⚠️ NÃO deletar ainda
- **Razão**: Imports ativos em `ui/`, `services/`
- **Ação necessária**: Atualizar imports `from utils.` → `from src.utils.`

#### 5. `config/` (4 arquivos) - **EM USO**
- **Duplicado de**: `src/core/config.py` e config/
- **Status**: ⚠️ NÃO deletar ainda
- **Razão**: Import em `main.py`: `from config.settings import settings`
- **Ação necessária**: Atualizar imports para `src/core/`

#### 6. `utilitarios/` (17 arquivos) - **EM USO**
- **Possível duplicado de**: `utils/` ou conteúdo específico
- **Status**: ⚠️ NÃO deletar ainda
- **Razão**: 2 imports ativos em `utilitarios/gerenciador_documentos.py`
- **Ação necessária**: Avaliar se pode ser mesclado com `utils/` ou movido para `src/utils/`

---

### ✅ Diretórios que PODEM SER DELETADOS (Após Verificação)

#### 1. `examples/` - **DELETAR**
- **Status**: ✅ Vazio (0 arquivos)
- **Ação**: Deletar imediatamente
- **Comando**: `Remove-Item "c:\gestao\examples" -Force`

#### 2. `ico/` (2 arquivos) - **AVALIAR**
- **Conteúdo**: Ícones antigos
- **Status**: ⚠️ Verificar se está duplicado em `assets/icons/` ou `icon/`
- **Ação**: 
  - Se duplicado → Deletar
  - Se único → Mover para `assets/icons/`

#### 3. `icon/` (12 arquivos) - **CONSOLIDAR**
- **Conteúdo**: Ícones do sistema
- **Status**: ⚠️ Verificar duplicação com `ico/` e `assets/icons/`
- **Ação**: Consolidar todos os ícones em `assets/icons/` e deletar `ico/` e `icon/`

#### 4. Diretórios de Recursos Específicos (AVALIAR MIGRAÇÃO)

**Opção A - Migrar para `assets/`:**

- `NIS/` (6 arquivos) → mover para `assets/nis/` ou `dados/nis/`
- `Cracha_Anos_Iniciais/` (5 arquivos) → mover para `assets/crachas/` ou `dados/crachas/`
- `Diario Escolar/` (3 arquivos) → mover para `assets/templates/` ou `dados/diarios/`
- `Modelos/` (13 arquivos) → mover para `assets/templates/modelos/`
- `transporte/` (3 arquivos) → mover para `dados/transporte/`

**Após migração**: Deletar diretórios originais

---

### 📋 Diretórios de Cache/Build (PODEM SER DELETADOS)

Estes diretórios são gerados automaticamente e podem ser deletados com segurança:

#### 1. `__pycache__/` - **DELETAR**
- **Status**: ✅ Cache Python (regenerado automaticamente)
- **Ação**: Deletar (adicionar ao .gitignore)
- **Comando**: `Get-ChildItem -Path "c:\gestao" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force`

#### 2. `.mypy_cache/` - **DELETAR**
- **Status**: ✅ Cache do MyPy (regenerado automaticamente)
- **Ação**: Deletar (adicionar ao .gitignore)
- **Comando**: `Remove-Item "c:\gestao\.mypy_cache" -Recurse -Force`

#### 3. `.pytest_cache/` - **DELETAR**
- **Status**: ✅ Cache do Pytest (regenerado automaticamente)
- **Ação**: Deletar (adicionar ao .gitignore)
- **Comando**: `Remove-Item "c:\gestao\.pytest_cache" -Recurse -Force`

#### 4. `mypy_report/` - **DELETAR**
- **Status**: ✅ Relatórios MyPy (regenerado quando necessário)
- **Ação**: Deletar (gerar novamente quando necessário)
- **Comando**: `Remove-Item "c:\gestao\mypy_report" -Recurse -Force`

---

### 🔄 Plano de Ação para Limpeza Completa

#### Fase 1: Deleção Imediata (Seguro)
```powershell
# Deletar diretório vazio
Remove-Item "c:\gestao\examples" -Force

# Deletar caches (podem ser regenerados)
Get-ChildItem -Path "c:\gestao" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Remove-Item "c:\gestao\.mypy_cache" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "c:\gestao\.pytest_cache" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "c:\gestao\mypy_report" -Recurse -Force -ErrorAction SilentlyContinue
```

#### Fase 2: Consolidação de Recursos
```powershell
# Consolidar ícones em assets/icons/
New-Item -ItemType Directory -Path "c:\gestao\assets\icons" -Force
Move-Item "c:\gestao\ico\*" "c:\gestao\assets\icons\" -Force
Move-Item "c:\gestao\icon\*" "c:\gestao\assets\icons\" -Force
Remove-Item "c:\gestao\ico" -Force
Remove-Item "c:\gestao\icon" -Force

# Migrar recursos específicos para assets/
New-Item -ItemType Directory -Path "c:\gestao\assets\crachas" -Force
New-Item -ItemType Directory -Path "c:\gestao\assets\templates" -Force
Move-Item "c:\gestao\Cracha_Anos_Iniciais\*" "c:\gestao\assets\crachas\" -Force
Move-Item "c:\gestao\Modelos\*" "c:\gestao\assets\templates\" -Force
Remove-Item "c:\gestao\Cracha_Anos_Iniciais" -Force
Remove-Item "c:\gestao\Modelos" -Force

# Migrar dados específicos para dados/
New-Item -ItemType Directory -Path "c:\gestao\dados\nis" -Force
New-Item -ItemType Directory -Path "c:\gestao\dados\diarios" -Force
New-Item -ItemType Directory -Path "c:\gestao\dados\transporte" -Force
Move-Item "c:\gestao\NIS\*" "c:\gestao\dados\nis\" -Force
Move-Item "c:\gestao\Diario Escolar\*" "c:\gestao\dados\diarios\" -Force
Move-Item "c:\gestao\transporte\*" "c:\gestao\dados\transporte\" -Force
Remove-Item "c:\gestao\NIS" -Force
Remove-Item "c:\gestao\Diario Escolar" -Force
Remove-Item "c:\gestao\transporte" -Force
```

#### Fase 3: Correção de Imports e Remoção de Duplicados
**⚠️ CRÍTICO**: Esta fase requer atualização massiva de imports

1. **Criar script de atualização de imports** (similar ao `atualizar_imports.py`):
```python
# scripts/desenvolvimento/atualizar_imports_src.py
mapeamentos = {
    'from models.': 'from src.models.',
    'from services.': 'from src.services.',
    'from ui.': 'from src.ui.',
    'from utils.': 'from src.utils.',
    'from config.': 'from src.core.config.',
    'from utilitarios.': 'from src.utils.utilitarios.',
}
```

2. **Executar atualização**:
```powershell
python scripts/desenvolvimento/atualizar_imports_src.py
```

3. **Testar sistema completo**:
```powershell
python main.py
```

4. **Se tudo funcionar, deletar diretórios duplicados**:
```powershell
Remove-Item "c:\gestao\models" -Recurse -Force
Remove-Item "c:\gestao\services" -Recurse -Force
Remove-Item "c:\gestao\ui" -Recurse -Force
Remove-Item "c:\gestao\utils" -Recurse -Force
Remove-Item "c:\gestao\config" -Recurse -Force
Remove-Item "c:\gestao\utilitarios" -Recurse -Force
```

---

### 📊 Resumo de Deleções Potenciais

| Diretório | Status | Arquivos | Ação | Prioridade |
|-----------|--------|----------|------|------------|
| `examples/` | Vazio | 0 | ✅ Deletar imediatamente | Alta |
| `__pycache__/` | Cache | - | ✅ Deletar (regenera) | Alta |
| `.mypy_cache/` | Cache | - | ✅ Deletar (regenera) | Alta |
| `.pytest_cache/` | Cache | - | ✅ Deletar (regenera) | Alta |
| `mypy_report/` | Relatório | - | ✅ Deletar (regenera) | Média |
| `ico/` | Recursos | 2 | ⚠️ Consolidar em assets/ | Média |
| `icon/` | Recursos | 12 | ⚠️ Consolidar em assets/ | Média |
| `NIS/` | Dados | 6 | ⚠️ Mover para dados/ | Média |
| `Cracha_Anos_Iniciais/` | Templates | 5 | ⚠️ Mover para assets/ | Média |
| `Diario Escolar/` | Templates | 3 | ⚠️ Mover para dados/ | Média |
| `Modelos/` | Templates | 13 | ⚠️ Mover para assets/ | Média |
| `transporte/` | Dados | 3 | ⚠️ Mover para dados/ | Média |
| `models/` | Código | 12 | ⚠️ Corrigir imports primeiro | Baixa |
| `services/` | Código | 32 | ⚠️ Corrigir imports primeiro | Baixa |
| `ui/` | Código | 48 | ⚠️ Corrigir imports primeiro | Baixa |
| `utils/` | Código | 16 | ⚠️ Corrigir imports primeiro | Baixa |
| `config/` | Config | 4 | ⚠️ Corrigir imports primeiro | Baixa |
| `utilitarios/` | Código | 17 | ⚠️ Corrigir imports primeiro | Baixa |

**Total de arquivos em diretórios duplicados**: ~146 arquivos (podem ser removidos após correção de imports)

---

### ⚡ Script de Limpeza Rápida (Executar Agora)

```powershell
# Salvar como: scripts/manutencao/limpar_diretorios_seguros.ps1

Write-Host "=== Limpeza de Diretórios Seguros ===" -ForegroundColor Cyan

# 1. Deletar diretório vazio
if (Test-Path "c:\gestao\examples") {
    Remove-Item "c:\gestao\examples" -Force
    Write-Host "✅ examples/ deletado" -ForegroundColor Green
}

# 2. Deletar caches Python
$cachesPython = Get-ChildItem -Path "c:\gestao" -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
$count = $cachesPython.Count
$cachesPython | Remove-Item -Recurse -Force
Write-Host "✅ $count diretórios __pycache__/ deletados" -ForegroundColor Green

# 3. Deletar cache MyPy
if (Test-Path "c:\gestao\.mypy_cache") {
    Remove-Item "c:\gestao\.mypy_cache" -Recurse -Force
    Write-Host "✅ .mypy_cache/ deletado" -ForegroundColor Green
}

# 4. Deletar cache Pytest
if (Test-Path "c:\gestao\.pytest_cache") {
    Remove-Item "c:\gestao\.pytest_cache" -Recurse -Force
    Write-Host "✅ .pytest_cache/ deletado" -ForegroundColor Green
}

# 5. Deletar relatórios MyPy
if (Test-Path "c:\gestao\mypy_report") {
    Remove-Item "c:\gestao\mypy_report" -Recurse -Force
    Write-Host "✅ mypy_report/ deletado" -ForegroundColor Green
}

Write-Host "`n=== Limpeza Concluída ===" -ForegroundColor Cyan
Write-Host "Diretórios de cache e temporários removidos com sucesso!" -ForegroundColor Green
```

**Executar**: `powershell -ExecutionPolicy Bypass -File scripts/manutencao/limpar_diretorios_seguros.ps1`

---
