# Tarefa 1.2: Captura de Requisições HTTP do GEDUC

**Data:** 20/12/2025  
**Status:** Em Andamento  
**Objetivo:** Capturar e documentar requisições POST reais ao sistema GEDUC

---

## 1. Ferramentas Necessárias

### 1.1. Chrome DevTools

**Como acessar:**
1. Abrir Google Chrome
2. Acessar https://semed.geduc.com.br
3. Pressionar F12 ou Ctrl+Shift+I
4. Ir para aba "Network" (Rede)
5. Marcar "Preserve log" para não perder requisições

### 1.2. Alternativas

- **Firefox Developer Tools** (F12 → Rede)
- **Burp Suite** (para análise avançada)
- **Fiddler** (proxy HTTP)

---

## 2. Passo a Passo da Captura

### Etapa 1: Preparação

```bash
# 1. Limpar cache do navegador
# 2. Abrir DevTools (F12)
# 3. Ir para aba "Network"
# 4. Filtrar por "XHR" ou "Fetch"
# 5. Marcar "Preserve log"
```

### Etapa 2: Login

1. Fazer login no GEDUC
2. Capturar a requisição POST de login
3. Anotar:
   - URL completa
   - Headers (especialmente cookies)
   - Payload do POST
   - Response headers

### Etapa 3: Navegação até Cadastro de Notas

1. Navegar: Dashboard → Alunos → Selecionar Aluno → Histórico
2. Capturar TODAS as requisições intermediárias
3. Identificar tokens/cookies que mudam

### Etapa 4: Submissão de Formulário

1. Preencher o formulário de cadastro de notas
2. Clicar em "Salvar" ou botão equivalente
3. **CAPTURAR A REQUISIÇÃO POST**
4. Salvar como HAR file (exportar)

---

## 3. Informações a Documentar

### 3.1. Headers da Requisição

```http
POST /index.php?class=DisciplinasHistorico&method=onEdit&... HTTP/1.1
Host: semed.geduc.com.br
User-Agent: Mozilla/5.0 ...
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3
Accept-Encoding: gzip, deflate, br
Content-Type: application/x-www-form-urlencoded
Content-Length: XXXX
Origin: https://semed.geduc.com.br
Connection: keep-alive
Referer: https://semed.geduc.com.br/index.php?class=...
Cookie: PHPSESSID=XXXXXXXXXX; outro_cookie=YYYYYYYY
Upgrade-Insecure-Requests: 1
```

**Anotar:**
- [ ] Nome do cookie de sessão
- [ ] Presença de token CSRF
- [ ] Headers customizados
- [ ] Referer necessário?

### 3.2. Payload (Form Data)

```
IDALUNO=235718
IDINSTITUICAO=1318
ANO=2025
IDESCOLA=
TIPOESCOLA=1
VISIVEL=1
IDCURSO=4
IDCURRICULO=69
IDDISCIPLINAS[]=77
IDDISCIPLINAS[]=78
IDDISCIPLINAS[]=79
CHT[]=400
CHT[]=40
CHT[]=40
MEDIA[]=8.5
MEDIA[]=9.0
MEDIA[]=8.0
FALTA[]=0
FALTA[]=2
FALTA[]=0
SITUACAO[]=0
SITUACAO[]=0
SITUACAO[]=0
csrf_token=XXXXXXXXXXXX   <-- SE EXISTIR!
```

**Verificar:**
- [ ] Ordem dos campos importa?
- [ ] Encoding dos arrays (`[]` vs `%5B%5D`)
- [ ] Campos adicionais não documentados
- [ ] Token CSRF no payload ou no header?

### 3.3. Response da Requisição

```http
HTTP/1.1 200 OK
Server: nginx/1.18.0
Date: Fri, 20 Dec 2025 15:30:00 GMT
Content-Type: text/html; charset=UTF-8
Transfer-Encoding: chunked
Connection: keep-alive
Set-Cookie: PHPSESSID=NOVO_SESSION_ID; path=/; HttpOnly
X-Powered-By: PHP/7.4.30
Cache-Control: no-cache, must-revalidate
Expires: Sat, 01 Jan 2000 00:00:00 GMT
```

**Corpo da resposta:**
- [ ] JSON?
- [ ] HTML?
- [ ] Redirect (302)?
- [ ] Mensagem de sucesso/erro?

---

## 4. Formato de Exportação

### 4.1. Salvar como HAR

No DevTools:
1. Botão direito na requisição → "Save all as HAR with content"
2. Salvar em: `c:\gestao\historico geduc\capturas\`

### 4.2. Copiar como cURL

1. Botão direito na requisição → "Copy" → "Copy as cURL (bash)"
2. Salvar em arquivo `.txt`

Exemplo:
```bash
curl 'https://semed.geduc.com.br/index.php?class=DisciplinasHistorico&method=onEdit&IDCURSO=4&ANO=2025&IDALUNO=235718&IDINSTITUICAO=1318&TIPOESCOLA=1' \
  -H 'authority: semed.geduc.com.br' \
  -H 'accept: text/html,application/xhtml+xml' \
  -H 'accept-language: pt-BR,pt;q=0.9' \
  -H 'cache-control: max-age=0' \
  -H 'content-type: application/x-www-form-urlencoded' \
  -H 'cookie: PHPSESSID=XXXXXXXXX' \
  -H 'origin: https://semed.geduc.com.br' \
  -H 'referer: https://semed.geduc.com.br/index.php?class=...' \
  -H 'user-agent: Mozilla/5.0 ...' \
  --data-raw 'IDALUNO=235718&IDINSTITUICAO=1318&...'
```

---

## 5. Checklist de Captura

### Requisições Críticas

- [ ] **Login**
  - [ ] URL e método
  - [ ] Campos do formulário
  - [ ] Cookie de sessão criado
  - [ ] Redirect após login

- [ ] **Listagem de Alunos**
  - [ ] Como buscar aluno?
  - [ ] Parâmetros de filtro
  - [ ] Formato da resposta

- [ ] **Carregar Disciplinas**
  - [ ] Ação do botão "Carregar Disciplinas"
  - [ ] Parâmetros enviados
  - [ ] Como recebe lista de disciplinas

- [ ] **Salvar Histórico**
  - [ ] POST completo
  - [ ] Todos os headers
  - [ ] Payload exato
  - [ ] Resposta de sucesso

### Informações de Segurança

- [ ] **CSRF Token**
  - Onde está? (cookie, hidden input, header?)
  - Nome do token
  - Como é gerado/renovado

- [ ] **Session**
  - Nome do cookie
  - Tempo de expiração
  - HttpOnly/Secure flags

- [ ] **Rate Limiting**
  - Há limite de requisições?
  - Delay necessário entre requests?

---

## 6. Análise de JavaScript

### 6.1. Framework Adianti

O GEDUC usa funções JavaScript customizadas. Verificar no código fonte:

```javascript
// Procurar por estas funções:
__adianti_post_data()
__adianti_post_lookup()
tform_send_data()
tcombo_clear()
tcombo_add_option()

// Arquivo principal:
/app/lib/adianti/include/application.js
```

### 6.2. Capturar AJAX

Algumas requisições podem ser AJAX. No DevTools:
1. Filtrar por "XHR"
2. Verificar requisições assíncronas
3. Documentar endpoints AJAX separadamente

---

## 7. Exemplo de Documentação

### Exemplo de Requisição Documentada

```markdown
#### POST - Salvar Histórico

**URL:**
```
POST https://semed.geduc.com.br/index.php?class=DisciplinasHistorico&method=onEdit&IDCURSO=4&ANO=2025&IDALUNO=235718&IDINSTITUICAO=1318&TIPOESCOLA=1
```

**Headers:**
```http
Content-Type: application/x-www-form-urlencoded
Cookie: PHPSESSID=abc123xyz789
Referer: https://semed.geduc.com.br/index.php?class=DisciplinasHistorico&method=onEdit&...
X-Requested-With: XMLHttpRequest
```

**Payload:**
```
IDALUNO=235718&IDINSTITUICAO=1318&ANO=2025&IDESCOLA=&TIPOESCOLA=1&VISIVEL=1&IDCURSO=4&IDCURRICULO=69&IDDISCIPLINAS%5B%5D=77&IDDISCIPLINAS%5B%5D=78&CHT%5B%5D=400&CHT%5B%5D=40&MEDIA%5B%5D=8.5&MEDIA%5B%5D=9.0&FALTA%5B%5D=0&FALTA%5B%5D=2&SITUACAO%5B%5D=0&SITUACAO%5B%5D=0
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Histórico salvo com sucesso",
    "id": 12345
}
```

**Response (Error):**
```json
{
    "success": false,
    "message": "Erro: Campo obrigatório não preenchido"
}
```
```

---

## 8. Ferramentas de Análise

### 8.1. Python para Análise de HAR

```python
import json

# Carregar arquivo HAR
with open('captura_geduc.har', 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# Filtrar requisições POST
posts = [
    entry for entry in har_data['log']['entries']
    if entry['request']['method'] == 'POST'
]

# Analisar cada POST
for post in posts:
    url = post['request']['url']
    headers = post['request']['headers']
    post_data = post['request'].get('postData', {})
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {post_data}")
    print("-" * 80)
```

### 8.2. Script para Comparar Requisições

```python
# Comparar duas capturas para identificar diferenças
import difflib

def comparar_requisicoes(har1, har2):
    # Implementar comparação
    pass
```

---

## 9. Resultados Esperados

Ao final desta tarefa, devemos ter:

1. **Arquivo HAR completo** com todas as requisições
2. **Documento de análise** com:
   - Headers obrigatórios
   - Presença/ausência de CSRF
   - Nome e formato do cookie de sessão
   - Estrutura exata do payload
3. **Scripts de teste** para validar descobertas
4. **cURL examples** para cada requisição crítica

---

## 10. Próximos Passos

Após completar a captura:

1. ✅ Validar descobertas com script POC (Tarefa 1.3)
2. ⏭️ Implementar módulo de autenticação GEDUC
3. ⏭️ Criar classe GEDUCExportador
4. ⏭️ Testar com dados reais (ambiente controlado)

---

**Status:** 🔄 EM ANDAMENTO  
**Responsável:** Equipe de Desenvolvimento  
**Prazo estimado:** 1-2 dias úteis
