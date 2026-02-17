# Guia de Troubleshooting

**Sistema de Gestão Escolar - Resolução de Problemas Comuns**

> 🆘 Este guia ajuda a diagnosticar e resolver problemas frequentes no sistema.

---

## Índice

1. [Problemas de Conexão com Banco de Dados](#1-problemas-de-conexão-com-banco-de-dados)
2. [Erros de Importação e Dependências](#2-erros-de-importação-e-dependências)
3. [Problemas de Interface (Tkinter)](#3-problemas-de-interface-tkinter)
4. [Autenticação e Permissões](#4-autenticação-e-permissões)
5. [Backup e Restauração](#5-backup-e-restauração)
6. [Performance e Lentidão](#6-performance-e-lentidão)
7. [Erros de Importação GEDUC](#7-erros-de-importação-geduc)
8. [Análise de Logs](#8-análise-de-logs)
9. [Migração de Dados](#9-migração-de-dados)
10. [Problemas com Relatórios PDF](#10-problemas-com-relatórios-pdf)

---

## 1. Problemas de Conexão com Banco de Dados

### ❌ **Erro: "Can't connect to MySQL server"**

**Sintomas:**
```
ERROR pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on 'localhost' (10061)")
```

**Causas possíveis:**

1. **MySQL não está rodando**
   ```powershell
   # Verificar serviço
   Get-Service -Name MySQL*
   
   # Iniciar serviço
   Start-Service -Name MySQL80  # Ajustar nome do serviço
   ```

2. **Configurações incorretas no `.env`**
   ```bash
   # Verificar arquivo .env na raiz do projeto
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=sua_senha
   DB_NAME=redeescola
   ```

3. **Firewall bloqueando porta 3306**
   ```powershell
   # Verificar regra de firewall
   Get-NetFirewallRule -DisplayName "*MySQL*"
   
   # Permitir conexão
   New-NetFirewallRule -DisplayName "MySQL" -Direction Inbound -LocalPort 3306 -Protocol TCP -Action Allow
   ```

4. **MySQL configurado para aceitar apenas conexões locais**
   ```sql
   -- Verificar bind-address no my.ini
   -- Localização: C:\ProgramData\MySQL\MySQL Server 8.0\my.ini
   bind-address=0.0.0.0  # Permitir conexões externas
   ```

---

### ❌ **Erro: "Too many connections"**

**Sintomas:**
```
ERROR pymysql.err.OperationalError: (1040, 'Too many connections')
```

**Diagnóstico:**
```sql
-- Verificar conexões atuais
SHOW PROCESSLIST;

-- Verificar máximo de conexões
SHOW VARIABLES LIKE 'max_connections';
```

**Soluções:**

1. **Aumentar limite de conexões (temporário):**
   ```sql
   SET GLOBAL max_connections = 200;
   ```

2. **Aumentar limite de conexões (permanente):**
   ```ini
   # Editar my.ini
   [mysqld]
   max_connections = 200
   ```

3. **Verificar pool de conexões no código:**
   ```python
   # db/connection.py
   # Verificar se pool_size está muito alto
   pool = create_pool(
       ...,
       maxsize=10,  # Reduzir se necessário
       ...
   )
   ```

4. **Forçar fechamento de conexões ociosas:**
   ```sql
   -- Matar conexões ociosas há mais de 1h
   SELECT CONCAT('KILL ', id, ';') 
   FROM information_schema.processlist 
   WHERE Time > 3600 AND User = 'redeescola';
   ```

---

### ❌ **Erro: "Lost connection to MySQL server during query"**

**Sintomas:**
```
ERROR pymysql.err.OperationalError: (2013, 'Lost connection to MySQL server during query')
```

**Causas possíveis:**

1. **Query muito longa ou timeout:**
   ```ini
   # Editar my.ini
   [mysqld]
   wait_timeout = 600
   max_allowed_packet = 64M
   ```

2. **Conexão instável:**
   ```python
   # Verificar se há retry no código
   # db/connection.py → usar @retry(tries=3, delay=2)
   ```

3. **Problema de rede (servidor remoto):**
   ```powershell
   # Testar conexão TCP
   Test-NetConnection -ComputerName seu_servidor -Port 3306
   ```

---

## 2. Erros de Importação e Dependências

### ❌ **Erro: "ModuleNotFoundError: No module named 'X'"**

**Sintomas:**
```
ModuleNotFoundError: No module named 'pydantic'
```

**Solução:**

1. **Verificar ambiente virtual ativo:**
   ```powershell
   # Ativar ambiente virtual
   .\venv\Scripts\Activate.ps1
   
   # Verificar se está ativo (prompt deve mostrar "(venv)")
   ```

2. **Instalar dependências:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Verificar versão do Python:**
   ```powershell
   python --version  # Deve ser 3.12+
   ```

4. **Reinstalar pacote específico:**
   ```powershell
   pip install --upgrade --force-reinstall pydantic
   ```

---

### ❌ **Erro: "ImportError: cannot import name 'X' from 'Y' (circular import)"**

**Sintomas:**
```
ImportError: cannot import name 'obter_usuario_logado' from 'auth.usuario_logado'
```

**Diagnóstico:**

1. **Identificar ciclo de importação:**
   ```powershell
   # Executar com modo debug
   python -v main.py 2> import_debug.log
   
   # Buscar "import" no log
   Select-String -Path import_debug.log -Pattern "circular"
   ```

2. **Padrão comum:** `service A → service B → service A`

**Soluções:**

1. **Mover import para dentro da função:**
   ```python
   # ❌ ERRADO: Import no topo
   from services.aluno_service import obter_aluno
   
   def minha_funcao():
       aluno = obter_aluno(123)
   
   # ✅ CORRETO: Import lazy
   def minha_funcao():
       from services.aluno_service import obter_aluno
       aluno = obter_aluno(123)
   ```

2. **Criar módulo intermediário:**
   ```python
   # src/core/utils.py (sem dependências)
   def funcao_compartilhada():
       ...
   
   # Ambos services importam de utils (sem ciclo)
   from core.utils import funcao_compartilhada
   ```

3. **Usar injeção de dependências:**
   ```python
   # Ao invés de importar service diretamente
   def processar(aluno_service):  # Recebe como parâmetro
       aluno = aluno_service.obter(123)
   ```

---

### ❌ **Erro: "AttributeError: module has no attribute"**

**Sintomas:**
```
AttributeError: module 'auth.auth_service' has no attribute 'verificar_permissao'
```

**Causas possíveis:**

1. **Cache de módulo desatualizado:**
   ```powershell
   # Excluir cache do Python
   Get-ChildItem -Path . -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
   Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
   ```

2. **Função realmente não existe:**
   ```python
   # Verificar se função foi renomeada ou removida
   # Buscar no histórico Git:
   git log -p -S "verificar_permissao" -- auth/auth_service.py
   ```

3. **Import parcial:**
   ```python
   # ❌ ERRADO
   import auth.auth_service
   auth.auth_service.verificar_permissao()  # Pode falhar
   
   # ✅ CORRETO
   from auth.auth_service import verificar_permissao
   verificar_permissao()
   ```

---

## 3. Problemas de Interface (Tkinter)

### ❌ **Erro: "TclError: couldn't connect to display"** (Linux)

**Solução:**
```bash
# Instalar bibliotecas X11
sudo apt-get install python3-tk

# Configurar DISPLAY
export DISPLAY=:0
```

---

### ❌ **Erro: "Application not responding / Freeze"**

**Sintomas:**
- Interface trava ao carregar relatórios
- Botões não respondem
- CPU 100%

**Causas:**

1. **Operação bloqueante no thread principal:**
   ```python
   # ❌ ERRADO: Query pesada no thread da UI
   def carregar_dados():
       alunos = buscar_todos_alunos()  # 10.000 registros, 5s
       self.atualizar_tabela(alunos)
   
   # ✅ CORRETO: Usar threading
   import threading
   
   def carregar_dados():
       def worker():
           alunos = buscar_todos_alunos()
           self.root.after(0, lambda: self.atualizar_tabela(alunos))
       
       threading.Thread(target=worker, daemon=True).start()
       self.mostrar_loading()
   ```

2. **Loop infinito ou recursão:**
   ```python
   # Verificar logs para stack overflow
   # Adicionar limite de recursão temporário:
   import sys
   sys.setrecursionlimit(100)  # Forçar erro rápido
   ```

**Solução para debug:**
```python
# Adicionar timeout em operações longas
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import timeout_decorator

@timeout_decorator.timeout(5)  # 5 segundos máximo
def operacao_pesada():
    ...
```

---

### ❌ **Erro: "Error in Tkinter callback / Button not working"**

**Sintomas:**
```
Exception in Tkinter callback
AttributeError: 'NoneType' object has no attribute 'get'
```

**Diagnóstico:**
```python
# Adicionar try/except em callbacks
def on_button_click():
    try:
        # Código do botão
        ...
    except Exception as e:
        logger.error(f"Erro no callback: {e}", exc_info=True)
        messagebox.showerror("Erro", str(e))
```

**Causas comuns:**
1. Widget destruído antes do callback
2. Variável não inicializada
3. Permissão negada (verificar RBAC)

---

## 4. Autenticação e Permissões

### ❌ **Erro: "Usuário não autenticado"**

**Sintomas:**
- Tela de login aparece novamente após autenticar
- Função `obter_usuario_logado()` retorna `None`

**Diagnóstico:**
```python
# Verificar se login foi registrado
from auth.usuario_logado import obter_usuario_logado

user = obter_usuario_logado()
print(f"Usuário: {user}")  # Deve imprimir nome, não None
```

**Soluções:**

1. **Verificar se `definir_usuario_logado()` foi chamado:**
   ```python
   # auth/auth_service.py → fazer_login()
   from auth.usuario_logado import definir_usuario_logado
   
   def fazer_login(usuario, senha):
       # ... validação ...
       definir_usuario_logado(usuario)  # ← Crítico!
       return True
   ```

2. **Verificar escopo global:**
   ```python
   # auth/usuario_logado.py
   _usuario_logado = None  # Deve ser global
   
   def definir_usuario_logado(usuario):
       global _usuario_logado
       _usuario_logado = usuario
   ```

---

### ❌ **Erro: "Acesso negado / Permissão insuficiente"**

**Sintomas:**
```
PermissionError: Usuário 'joao' não tem permissão 'alunos.excluir'
```

**Diagnóstico:**

1. **Verificar permissões do perfil:**
   ```sql
   -- Buscar perfil do usuário
   SELECT p.nome, p.permissoes 
   FROM usuarios u
   JOIN perfis p ON u.perfil_id = p.id
   WHERE u.login = 'joao';
   
   -- Ver permissões (JSON)
   -- Ex: {"dashboard.visualizar": true, "alunos.editar": true}
   ```

2. **Comparar com permissões necessárias:**
   ```python
   # Ver docs/RBAC_PERMISSOES.md
   # Verificar matriz de permissões por perfil
   ```

**Soluções:**

1. **Adicionar permissão ao perfil:**
   ```sql
   -- Editar JSON de permissões
   UPDATE perfis 
   SET permissoes = JSON_MERGE_PATCH(
       permissoes, 
       '{"alunos.excluir": true}'
   )
   WHERE nome = 'Coordenador';
   ```

2. **Alterar perfil do usuário:**
   ```sql
   UPDATE usuarios 
   SET perfil_id = (SELECT id FROM perfis WHERE nome = 'Administrador')
   WHERE login = 'joao';
   ```

3. **Desabilitar verificação (apenas desenvolvimento):**
   ```python
   # auth/guards.py
   BYPASS_PERMISSIONS = True  # ⚠️ Apenas para debug!
   ```

---

### ❌ **Erro: "Senha incorreta após trocar no primeiro acesso"**

**Causa:** Hash bcrypt não foi gerado corretamente.

**Diagnóstico:**
```sql
-- Verificar formato da senha
SELECT login, senha FROM usuarios WHERE login = 'joao';

-- Se começar com $2b$ → bcrypt correto
-- Se for texto plano → senha sem hash! (INSEGURO)
```

**Solução:**
```python
# Rehashing de senha
from auth.password_utils import hash_password

nova_senha_hash = hash_password('NovaSenha123')

# SQL:
UPDATE usuarios SET senha = '<cola_hash_aqui>' WHERE login = 'joao';
```

---

## 5. Backup e Restauração

### ❌ **Erro: "mysqldump: command not found"**

**Solução:**

1. **Adicionar MySQL ao PATH:**
   ```powershell
   # Adicionar ao PATH (permanente)
   $env:Path += ";C:\Program Files\MySQL\MySQL Server 8.0\bin"
   
   # Testar
   mysqldump --version
   ```

2. **Usar caminho absoleto no código:**
   ```python
   # src/core/seguranca.py
   MYSQLDUMP_PATH = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
   ```

---

### ❌ **Erro: "Backup travado / Muito lento"**

**Sintomas:**
- Backup demora mais de 10 minutos
- Arquivo `.sql` muito grande (>500MB)

**Diagnóstico:**
```powershell
# Ver tamanho das tabelas
```
```sql
SELECT 
    table_name, 
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS "Size (MB)"
FROM information_schema.TABLES
WHERE table_schema = 'redeescola'
ORDER BY (data_length + index_length) DESC;
```

**Soluções:**

1. **Backup incremental (apenas dados novos):**
   ```bash
   # Backup apenas inserções/updates desde ontem
   mysqldump --where="data_modificacao >= CURDATE() - INTERVAL 1 DAY" ...
   ```

2. **Excluir tabelas de log temporário:**
   ```bash
   mysqldump --ignore-table=redeescola.logs --ignore-table=redeescola.cache ...
   ```

3. **Backup comprimido:**
   ```bash
   mysqldump redeescola | gzip > backup.sql.gz
   ```

4. **Limpar dados antigos antes do backup:**
   ```sql
   -- Deletar logs antigos (>90 dias)
   DELETE FROM logs WHERE data < DATE_SUB(NOW(), INTERVAL 90 DAY);
   
   -- Limpar cache
   TRUNCATE TABLE cache_estatisticas;
   ```

---

### ❌ **Erro ao Restaurar: "Duplicate entry" ou "Unknown database"**

**Sintomas:**
```
ERROR 1062 (23000): Duplicate entry '123' for key 'PRIMARY'
ERROR 1049 (42000): Unknown database 'redeescola'
```

**Soluções:**

1. **Criar banco antes de restaurar:**
   ```sql
   CREATE DATABASE IF NOT EXISTS redeescola;
   USE redeescola;
   ```

2. **Forçar recriação (CUIDADO: apaga tudo):**
   ```sql
   DROP DATABASE IF EXISTS redeescola;
   CREATE DATABASE redeescola;
   ```
   ```powershell
   mysql -u root -p redeescola < backup.sql
   ```

3. **Restaurar apenas estrutura:**
   ```bash
   mysqldump --no-data redeescola > estrutura.sql
   mysql -u root -p < estrutura.sql
   ```

4. **Restaurar apenas dados:**
   ```bash
   mysqldump --no-create-info redeescola > dados.sql
   mysql -u root -p redeescola < dados.sql
   ```

---

## 6. Performance e Lentidão

### ❌ **Dashboard demora >10 segundos para carregar**

**Diagnóstico:**

1. **Ativar query log:**
   ```python
   # db/connection.py
   # Descomentar linha de log:
   logger.debug(f"Query: {query} | Params: {params}")
   ```

2. **Verificar queries lentas no MySQL:**
   ```sql
   -- Ativar slow query log
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 1;  -- Queries > 1s
   
   -- Ver queries lentas
   -- Log em: C:\ProgramData\MySQL\MySQL Server 8.0\Data\slow-query.log
   ```

3. **Usar EXPLAIN para analisar query:**
   ```sql
   EXPLAIN SELECT * FROM matriculas WHERE ano_letivo = 2026;
   ```

**Soluções:**

1. **Criar índices:**
   ```sql
   -- Índice em ano_letivo (usado frequentemente)
   CREATE INDEX idx_ano_letivo ON matriculas(ano_letivo);
   
   -- Índice composto
   CREATE INDEX idx_ano_serie ON matriculas(ano_letivo, serie_id);
   ```

2. **Habilitar cache:**
   ```python
   # Verificar feature flag
   from src.core.feature_flags import FeatureFlags
   flags = FeatureFlags()
   
   if not flags.is_enabled('cache_enabled'):
       flags.enable('cache_enabled')
   ```

3. **Otimizar query:**
   ```python
   # ❌ LENTO: N+1 queries
   alunos = obter_todos_alunos()
   for aluno in alunos:
       turma = obter_turma(aluno.turma_id)  # Query por aluno!
   
   # ✅ RÁPIDO: 1 query com JOIN
   alunos_com_turmas = obter_alunos_com_turma()  # JOIN único
   ```

4. **Limpar cache de estatísticas:**
   ```python
   # Limpar cache manualmente
   python limpar_cache_dashboard.py
   ```

---

### ❌ **Sistema trava ao gerar relatório com 5.000+ alunos**

**Sintomas:**
- Memória sobe para >2GB
- Relatório PDF não gera

**Soluções:**

1. **Paginação:**
   ```python
   # Gerar relatório em lotes
   BATCH_SIZE = 500
   for offset in range(0, total, BATCH_SIZE):
       alunos = obter_alunos(limit=BATCH_SIZE, offset=offset)
       adicionar_ao_pdf(alunos)
   ```

2. **Filtrar dados antes de buscar:**
   ```sql
   -- Ao invés de buscar tudo
   SELECT * FROM alunos WHERE ano_letivo = 2026 AND status = 'Ativo';
   ```

3. **Desabilitar feature flags pesadas:**
   ```python
   # Desativar validação Pydantic temporariamente
   flags.disable('pydantic_validation')
   ```

---

## 7. Erros de Importação GEDUC

### ❌ **Erro: "Formato JSON inválido"**

**Sintomas:**
```
json.JSONDecodeError: Expecting property name enclosed in double quotes
```

**Solução:**

1. **Validar JSON:**
   ```powershell
   # Usar jq (instalar: choco install jq)
   jq . alunos_geduc.json
   
   # Ou Python
   python -m json.tool alunos_geduc.json
   ```

2. **Identificar linha com erro:**
   ```python
   import json
   
   with open('alunos_geduc.json', 'r', encoding='utf-8') as f:
       try:
           data = json.load(f)
       except json.JSONDecodeError as e:
           print(f"Erro na linha {e.lineno}, coluna {e.colno}: {e.msg}")
   ```

3. **Corrigir problemas comuns:**
   - Aspas simples ao invés de duplas: `{'nome': 'João'}` → `{"nome": "João"}`
   - Vírgula extra: `{"a": 1, "b": 2,}` → `{"a": 1, "b": 2}`
   - Caracteres especiais não escapados: `"texto com "aspas""` → `"texto com \"aspas\""`

---

### ❌ **Erro: "Aluno não importado - CPF duplicado"**

**Sintomas:**
```
ERROR: Aluno 'João Silva' não importado - CPF '123.456.789-00' já existe
```

**Diagnóstico:**
```sql
-- Verificar duplicatas
SELECT cpf, COUNT(*) 
FROM alunos 
GROUP BY cpf 
HAVING COUNT(*) > 1;
```

**Soluções:**

1. **Atualizar ao invés de inserir:**
   ```python
   # importar_geduc.py
   # Usar UPSERT ao invés de INSERT
   ON DUPLICATE KEY UPDATE nome = VALUES(nome), ...
   ```

2. **Mesclar registros duplicados:**
   ```sql
   -- Manter o mais recente
   DELETE a1 FROM alunos a1
   INNER JOIN alunos a2 
   WHERE a1.id < a2.id AND a1.cpf = a2.cpf;
   ```

3. **Ignorar duplicados na importação:**
   ```python
   # Adicionar flag --skip-duplicates
   python importar_geduc.py --skip-duplicates
   ```

---

## 8. Análise de Logs

### Como Analisar Logs do Sistema

**Localização:** `logs/app.log`, `logs/app.log.1`, ...

**Estrutura:**
```
2026-02-17 14:30:45,123 - INFO - aluno_service - Aluno 123 cadastrado com sucesso
2026-02-17 14:31:10,456 - ERROR - db.connection - Erro ao executar query: [ERRO DETALILHADO]
```

**Formato:** `<timestamp> - <nível> - <módulo> - <mensagem>`

---

### Filtrar Logs por Nível

```powershell
# Apenas erros
Select-String -Path logs\app.log -Pattern "ERROR"

# Apenas de um módulo específico
Select-String -Path logs\app.log -Pattern "aluno_service"

# Erros de hoje
$hoje = Get-Date -Format "yyyy-MM-dd"
Select-String -Path logs\app.log -Pattern "$hoje.*ERROR"

# Top 10 erros mais frequentes
Select-String -Path logs\app.log -Pattern "ERROR" | 
    ForEach-Object { $_.Line -replace '.*ERROR - ', '' } | 
    Group-Object | 
    Sort-Object Count -Descending | 
    Select-Object -First 10 Name, Count
```

---

### Ativar Modo Debug

```python
# 1. Via feature flag
from src.core.feature_flags import FeatureFlags
flags = FeatureFlags()
flags.enable('modo_debug')

# 2. Via ambiente
# .env:
FEATURE_MODO_DEBUG=1

# 3. Via código (temporário)
# src/core/config_logs.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Logs de debug incluem:**
- Queries SQL executadas
- Parâmetros de funções
- Stack traces completas
- Valores de variáveis

**⚠️ Atenção:** Modo debug pode vazar senhas/tokens nos logs. **Apenas use em desenvolvimento!**

---

## 9. Migração de Dados

### ❌ **Erro: "Foreign key constraint fails"**

**Sintomas:**
```
ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails
```

**Causa:** Tentativa de inserir registro com FK inexistente.

**Exemplo:**
```sql
-- Inserir matrícula com serie_id = 99 (série não existe)
INSERT INTO matriculas (aluno_id, serie_id) VALUES (1, 99);
-- Erro! serie_id 99 não existe em series
```

**Solução:**

1. **Verificar FK antes de inserir:**
   ```sql
   -- Verificar se série existe
   SELECT id FROM series WHERE id = 99;
   -- Se não retornar nada, criar série primeiro
   ```

2. **Desabilitar FKs temporariamente (CUIDADO!):**
   ```sql
   SET FOREIGN_KEY_CHECKS = 0;
   -- ... inserções ...
   SET FOREIGN_KEY_CHECKS = 1;
   ```

3. **Inserir dependências primeiro:**
   ```python
   # Ordem correta:
   # 1. escolas
   # 2. series
   # 3. turmas (depende de escolas + series)
   # 4. alunos
   # 5. matriculas (depende de alunos + turmas)
   ```

---

## 10. Problemas com Relatórios PDF

### ❌ **Erro: "ReportLab não encontrado"**

**Solução:**
```powershell
pip install reportlab
```

---

### ❌ **Erro: "Fonte não encontrada / Caracteres estranhos"**

**Sintomas:**
- Acentos aparecem como `???` ou `□`
- Nome com "João" vira "Jo�o"

**Solução:**

1. **Usar fonte com suporte UTF-8:**
   ```python
   from reportlab.pdfbase import pdfmetrics
   from reportlab.pdfbase.ttfonts import TTFont
   
   # Registrar fonte DejaVu
   pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
   
   # Usar na geração
   canvas.setFont('DejaVu', 12)
   ```

2. **Verificar encoding:**
   ```python
   # Abrir arquivo com encoding correto
   with open('dados.txt', 'r', encoding='utf-8') as f:
       texto = f.read()
   ```

---

### ❌ **PDF gerado está incompleto**

**Sintomas:**
- Relatório com 50 alunos mostra apenas 10
- Última página cortada

**Solução:**

1. **Verificar limite de registros:**
   ```python
   # Remover LIMIT na query
   alunos = obter_alunos()  # Sem limit=10
   ```

2. **Adicionar paginação automática:**
   ```python
   from reportlab.platypus import SimpleDocTemplate, PageBreak
   
   story = []
   for i, aluno in enumerate(alunos):
       story.append(Paragraph(aluno.nome))
       if (i + 1) % 30 == 0:  # Nova página a cada 30
           story.append(PageBreak())
   
   doc.build(story)
   ```

---

## Comandos Úteis

### Verificar Estado do Sistema

```powershell
# Serviço MySQL
Get-Service -Name MySQL80

# Processos Python rodando
Get-Process python

# Portas em uso
Get-NetTCPConnection -LocalPort 3306

# Espaço em disco
Get-PSDrive C

# Logs recentes
Get-Content logs\app.log -Tail 50
```

### Resetar Sistema (Desenvolvimento)

```powershell
# ⚠️ CUIDADO: Apaga todos os dados!

# 1. Parar aplicação
# 2. Recriar banco
mysql -u root -p -e "DROP DATABASE redeescola; CREATE DATABASE redeescola;"

# 3. Rodar migrações
python -m db.migrations.run_migrations

# 4. Inserir dados de teste
mysql -u root -p redeescola < dados/insercoes.sql

# 5. Limpar cache
Remove-Item -Recurse -Force __pycache__
Remove-Item feature_flags.json

# 6. Reiniciar aplicação
python main.py
```

---

## Suporte Avançado

### Quando Nada Funciona

1. **Coletar informações completas:**
   ```powershell
   # Criar pasta de diagnóstico
   New-Item -ItemType Directory -Path diagnostico
   
   # Copiar logs
   Copy-Item logs\* diagnostico\
   
   # Exportar configuração (sem senhas!)
   Get-Content .env | Select-String -NotMatch "PASSWORD" > diagnostico\config.txt
   
   # Versões instaladas
   python --version > diagnostico\versoes.txt
   pip list >> diagnostico\versoes.txt
   mysql --version >> diagnostico\versoes.txt
   
   # Comprimir
   Compress-Archive -Path diagnostico\* -DestinationPath diagnostico.zip
   ```

2. **Verificar issues conhecidas:**
   - `docs/analises/` → análises de problemas anteriores
   - `CHANGELOG.md` → bugs corrigidos por versão

3. **Modo de recuperação:**
   ```powershell
   # Iniciar sem UI (apenas console)
   python -c "from db.connection import test_connection; test_connection()"
   ```

4. **Rollback para versão estável:**
   ```powershell
   git log --oneline  # Ver commits recentes
   git checkout <hash_commit_funcionando>
   ```

---

## Checklist de Diagnóstico

Antes de reportar um bug, verificar:

- [ ] MySQL está rodando?
- [ ] Arquivo `.env` configurado corretamente?
- [ ] Ambiente virtual ativo?
- [ ] Dependências instaladas (`pip list`)?
- [ ] Cache limpo (`__pycache__` deletado)?
- [ ] Logs verificados (`logs/app.log`)?
- [ ] Permissões do usuário corretas?
- [ ] Espaço em disco suficiente (>1GB)?
- [ ] Versão do Python é 3.12+?
- [ ] Firewall não está bloqueando?

---

> **Última atualização:** 17/02/2026  
> **Para mais ajuda:** Ver [CONTRIBUTING.md](../CONTRIBUTING.md) ou abrir issue no projeto.
