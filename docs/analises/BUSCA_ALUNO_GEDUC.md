# Busca de Aluno no GEDUC - Como Funciona

**Data:** 20/12/2025  
**Módulo:** `src/exportadores/geduc_exportador.py`

---

## 🎯 Problema Resolvido

**Antes:**
- Precisava saber o `idaluno_geduc` (ID do aluno no GEDUC)
- ID local do sistema ≠ ID no GEDUC
- Não havia forma automática de descobrir o ID

**Agora:**
- ✅ Busca automática por nome do aluno
- ✅ Normalização automática (remove acentos, maiúsculas)
- ✅ Mesmo padrão usado no importador de notas

---

## 📝 Como Usar

### Opção 1: Fornecendo Nome do Aluno (Recomendado)

```python
from src.exportadores.geduc_exportador import exportar_historico_aluno

resultado = exportar_historico_aluno(
    aluno_id=123,  # ID local
    usuario_geduc="usuario",
    senha_geduc="senha",
    dados_historico={
        # NÃO precisa fornecer idaluno_geduc
        'nome_aluno': 'João da Silva',  # Sistema busca automaticamente
        
        'idinstituicao': 1318,
        'ano': 2025,
        'idcurso': 4,
        'idcurriculo': 69,
        'disciplinas': [...]
    }
)
```

### Opção 2: Fornecendo ID Direto (Se já conhecido)

```python
resultado = exportar_historico_aluno(
    aluno_id=123,
    usuario_geduc="usuario",
    senha_geduc="senha",
    dados_historico={
        'idaluno_geduc': 235718,  # ID conhecido do GEDUC
        
        'idinstituicao': 1318,
        'ano': 2025,
        # ... resto dos dados
    }
)
```

---

## 🔍 Normalização de Nome

### Função: `ExportadorGEDUC.normalizar_nome()`

**O que faz:**
1. Remove acentuação (á → a, ç → c, ñ → n)
2. Converte para MAIÚSCULAS
3. Remove sufixos comuns:
   - `(Transferencia Externa)`
   - `(TRANSFERIDO)`
   - `(EVADIDO)`
   - E variações

**Exemplos:**

| Nome Original | Nome Normalizado |
|--------------|------------------|
| `João da Silva` | `JOAO DA SILVA` |
| `María José` | `MARIA JOSE` |
| `José (TRANSFERIDO)` | `JOSE` |
| `André Luís - Evadido` | `ANDRE LUIS` |

---

## 🔎 Processo de Busca

### Método: `ExportadorGEDUC.buscar_aluno_por_nome()`

**Passo a passo:**

```
1. Normalizar nome
   'João da Silva' → 'JOAO DA SILVA'

2. Acessar página de busca
   URL: /index.php?class=FichaAlunoForm

3. Preencher campo de busca
   Campo: NOME (ou variações)

4. Executar busca
   Clicar em botão ou submit do form

5. Procurar resultado
   XPath: //a[contains(text(), 'JOAO DA SILVA')]

6. Extrair ID da URL
   Regex: [?&]IDALUNO=(\d+)
   Exemplo: ?IDALUNO=235718 → 235718

7. Retornar dados
   {
     'id': 235718,
     'nome': 'JOAO DA SILVA',
     'nome_busca': 'JOAO DA SILVA'
   }
```

---

## ⚙️ Integração com Interface

### No arquivo `historico_escolar.py`

O método `exportar_para_geduc()` já existe. Precisa apenas:

```python
def exportar_para_geduc(self):
    # 1. Validar que tem aluno selecionado
    if not self.aluno_id:
        messagebox.showerror("Erro", "Selecione um aluno!")
        return
    
    # 2. Buscar nome do aluno no banco local
    cursor = self.conexao.cursor()
    cursor.execute("SELECT nome FROM alunos WHERE idaluno = ?", (self.aluno_id,))
    resultado = cursor.fetchone()
    
    if not resultado:
        messagebox.showerror("Erro", "Aluno não encontrado!")
        return
    
    nome_aluno = resultado[0]
    
    # 3. Buscar dados do histórico
    # TODO: Implementar busca de disciplinas, notas, etc.
    
    # 4. Montar dados_historico
    dados_historico = {
        'nome_aluno': nome_aluno,  # Sistema busca ID automaticamente
        'idinstituicao': 1318,     # TODO: Obter do config
        'ano': 2025,               # TODO: Obter do contexto
        'idcurso': 4,              # TODO: Mapear série → ID curso GEDUC
        'idcurriculo': 69,         # TODO: Obter do GEDUC ou config
        'disciplinas': [           # TODO: Buscar do banco
            # ...
        ]
    }
    
    # 5. Solicitar credenciais
    credenciais = self._solicitar_credenciais_geduc()
    if not credenciais:
        return
    
    # 6. Executar exportação
    from src.exportadores.geduc_exportador import exportar_historico_aluno
    
    resultado = exportar_historico_aluno(
        aluno_id=self.aluno_id,
        usuario_geduc=credenciais['usuario'],
        senha_geduc=credenciais['senha'],
        dados_historico=dados_historico,
        callback_progresso=self._atualizar_progresso
    )
    
    # 7. Exibir resultado
    if resultado['sucesso']:
        messagebox.showinfo("Sucesso", resultado['mensagem'])
    else:
        messagebox.showerror("Erro", resultado['erro'])
```

---

## 🧪 Testando Busca Isoladamente

```python
from src.exportadores.geduc_exportador import ExportadorGEDUC

# 1. Criar exportador
exportador = ExportadorGEDUC(headless=False)

# 2. Iniciar navegador
exportador.iniciar_navegador()

# 3. Fazer login
exportador.fazer_login("usuario", "senha")

# 4. Buscar aluno
resultado = exportador.buscar_aluno_por_nome("João da Silva")

if resultado:
    print(f"Aluno encontrado!")
    print(f"  ID: {resultado['id']}")
    print(f"  Nome: {resultado['nome']}")
else:
    print("Aluno não encontrado")

# 5. Fechar
exportador.fechar()
```

---

## ⚠️ Observações Importantes

### 1. Nome Deve Ser Exato

A busca no GEDUC usa `contains()`, mas funciona melhor com nome completo:

✅ **Funciona:**
- `JOAO DA SILVA`
- `MARIA JOSE SANTOS`

⚠️ **Pode não funcionar:**
- `JOAO` (muitos resultados)
- `SILVA` (sobrenome comum)

### 2. Variações de Nome

Se o aluno estiver cadastrado com nome ligeiramente diferente:

**Sistema Local:** `João da Silva`  
**GEDUC:** `João Silva` (sem "da")

A busca pode falhar. Solução:
- Ajustar nome no banco local
- Ou implementar busca fuzzy (match parcial)

### 3. Múltiplos Resultados

Se houver múltiplos alunos com mesmo nome, o sistema pega o **primeiro** da lista.

**Solução futura:**
- Adicionar parâmetros extras (matrícula, data nascimento)
- Confirmar com usuário em caso de duplicidade

### 4. Campo de Busca

A URL e nome do campo podem variar entre versões do GEDUC:

**Atualmente testado:**
- URL: `/index.php?class=FichaAlunoForm`
- Campo: `NOME`

**Se mudar, ajustar em:**
```python
# Linha ~XX do geduc_exportador.py
url_busca = f"{self.url_base}/index.php?class=FichaAlunoForm"
campo_busca = wait.until(
    EC.presence_of_element_located((By.NAME, "NOME"))
)
```

---

## 🎓 Comparação com Importador

| Aspecto | Importador (cadastro_notas.py) | Exportador (geduc_exportador.py) |
|---------|-------------------------------|----------------------------------|
| **Direção** | GEDUC → Sistema Local | Sistema Local → GEDUC |
| **Busca** | Extrai lista completa de alunos | Busca aluno individual |
| **Normalização** | `normalizar_nome()` inline | `ExportadorGEDUC.normalizar_nome()` |
| **ID** | Extrai do HTML da tabela | Extrai da URL do link |
| **Uso** | Importar notas de turma inteira | Exportar histórico de 1 aluno |

**Código compartilhado:**
- Lógica de normalização (idêntica)
- Remoção de sufixos (mesma lista)
- Conversão para maiúsculas sem acentos

---

## 📊 Fluxo Completo de Exportação

```
┌──────────────────────────────┐
│ Interface: Botão Exportar    │
└──────────┬───────────────────┘
           │
           ├─► Busca nome no banco local
           │   SELECT nome FROM alunos WHERE idaluno = ?
           │
           ├─► Monta dados_historico
           │   { 'nome_aluno': 'JOAO', ... }
           │
           ├─► Chama exportar_historico_aluno()
           │
           ▼
┌──────────────────────────────┐
│ ExportadorGEDUC              │
├──────────────────────────────┤
│ 1. Login (reCAPTCHA manual)  │
│ 2. Busca aluno por nome      │
│    ├─► Normaliza: JOAO       │
│    ├─► Busca no GEDUC        │
│    └─► Extrai ID: 235718     │
│ 3. Acessa formulário         │
│    URL: ?IDALUNO=235718      │
│ 4. Preenche disciplinas      │
│ 5. Salva                     │
│ 6. Verifica sucesso          │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Retorna resultado            │
│ { sucesso: true,             │
│   mensagem: "..." }          │
└──────────────────────────────┘
```

---

**Última atualização:** 20/12/2025  
**Status:** ✅ Implementado e testável  
**Próximo passo:** Completar integração com `historico_escolar.py`
