# Requisições HTTP Capturadas - GEDUC

**Data da Captura:** _____/_____/2025  
**Navegador Utilizado:** Chrome / Firefox  
**Versão do Sistema GEDUC:** __________

---

## 1. Requisição de Login

### 1.1. Endpoint

```
URL: https://semed.geduc.com.br/______________________________
Método: POST
```

### 1.2. Headers

```http
Content-Type: ___________________________________
Cookie: __________________________________________
Referer: _________________________________________
Origin: __________________________________________
User-Agent: ______________________________________
[Outros headers importantes]:
_____________________________________________________
```

### 1.3. Payload

```
Campos do formulário:
- login: ______________
- password: ___________
- [outros campos]: ____
```

**Payload codificado:**
```
_____________________________________________________
_____________________________________________________
```

### 1.4. Resposta

**Status Code:** _______

**Headers da Resposta:**
```http
Set-Cookie: __________________________________________
Location: ____________________________________________
[Outros headers]:
_____________________________________________________
```

**Corpo da Resposta (se aplicável):**
```
_____________________________________________________
_____________________________________________________
```

### 1.5. Observações sobre Login

- [ ] Cookie de sessão criado? Nome: ______________
- [ ] Token CSRF presente? Onde: ________________
- [ ] Redirect após login? Para onde: ___________
- [ ] Validação no cliente (JavaScript)?
- [ ] Outros detalhes importantes:

_____________________________________________________
_____________________________________________________

---

## 2. Navegação até Cadastro de Notas

### 2.1. Sequência de Navegação

1. Login → __________________________________________
2. Dashboard → _____________________________________
3. __________________ → ____________________________
4. __________________ → Cadastro de Notas

### 2.2. Requisições Intermediárias Importantes

**Requisição 1:**
```
URL: _________________________________________________
Método: GET / POST
Propósito: ___________________________________________
```

**Requisição 2:**
```
URL: _________________________________________________
Método: GET / POST
Propósito: ___________________________________________
```

### 2.3. Como Carregar Lista de Disciplinas

**Endpoint:**
```
URL: _________________________________________________
Método: _______________
```

**Parâmetros:**
```
IDCURSO: __________
ANO: ______________
IDALUNO: __________
[Outros]: _________
```

**Resposta:**
```json
{
  // Estrutura da resposta
}
```

---

## 3. Submissão de Histórico/Notas

### 3.1. Endpoint Principal

```
URL Base: https://semed.geduc.com.br/index.php
Query Parameters:
  - class: DisciplinasHistorico
  - method: onEdit / onSave (confirmar qual)
  - IDCURSO: _______
  - ANO: ___________
  - IDALUNO: _______
  - IDINSTITUICAO: _______
  - TIPOESCOLA: ____
  - [Outros parâmetros]: ___________

URL Completa Exemplo:
_____________________________________________________
```

### 3.2. Headers da Requisição

```http
POST /index.php?class=... HTTP/1.1
Host: semed.geduc.com.br
Content-Type: application/x-www-form-urlencoded
Content-Length: ________
Cookie: PHPSESSID=_____________; [outros cookies]
Referer: ________________________________________________
Origin: https://semed.geduc.com.br
X-Requested-With: ______________________________________
[CSRF Token no header?]: ________________________________
[Outros headers]:
_____________________________________________________
```

### 3.3. Payload Completo

#### Campos Simples

```
IDALUNO=_____________
IDINSTITUICAO=_______
ANO=_________________
IDESCOLA=____________
TIPOESCOLA=__________
VISIVEL=_____________
IDCURSO=_____________
IDCURRICULO=_________
[Token CSRF?]=_______
[Outros campos]:
_____________________________________________________
```

#### Arrays de Disciplinas

**Exemplo com 3 disciplinas:**

```
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

[Outros arrays?]:
_____________________________________________________
```

**Payload Raw (URL-encoded):**
```
_____________________________________________________
_____________________________________________________
_____________________________________________________
```

### 3.4. Resposta da Submissão

**Status Code:** _______

**Headers:**
```http
Content-Type: ________________________________________
[Outros headers]:
_____________________________________________________
```

**Corpo da Resposta (Sucesso):**
```
Formato: JSON / HTML / Texto / XML (circular)

_____________________________________________________
_____________________________________________________
```

**Corpo da Resposta (Erro):**
```
_____________________________________________________
_____________________________________________________
```

### 3.5. Indicadores de Sucesso/Erro

**Como identificar sucesso:**
- [ ] Status code 200
- [ ] Mensagem específica no corpo: "______________"
- [ ] Redirect para: _____________________________
- [ ] JSON com campo: ____________________________
- [ ] Outro: _____________________________________

**Como identificar erro:**
- [ ] Status code diferente de 200
- [ ] Mensagem de erro contém: __________________
- [ ] Campo de erro JSON: _______________________
- [ ] Outro: _____________________________________

---

## 4. Descobertas sobre CSRF

### 4.1. Token CSRF Encontrado?

- [ ] SIM
- [ ] NÃO
- [ ] Incerto

**Se SIM:**

**Nome do token:** ___________________________________

**Localização:**
- [ ] Cookie
- [ ] Hidden input no HTML
- [ ] Header HTTP (nome: _____________)
- [ ] Campo do POST (nome: _____________)

**Valor de exemplo:** ________________________________

**Como é gerado:**
_____________________________________________________

**Quando é renovado:**
_____________________________________________________

### 4.2. Validação do Token

**É validado pelo servidor?**
- [ ] SIM - requisição falha sem token
- [ ] NÃO - funciona sem token
- [ ] Incerto

**Testes realizados:**
_____________________________________________________

---

## 5. Cookies e Sessão

### 5.1. Cookie de Sessão

**Nome:** ____________________________________________

**Propriedades:**
- [ ] HttpOnly
- [ ] Secure
- [ ] SameSite: _____________________________________

**Tempo de expiração:** _____________________________

**Exemplo de valor:** ________________________________

### 5.2. Outros Cookies Importantes

1. **Nome:** ________________ | **Propósito:** _______
2. **Nome:** ________________ | **Propósito:** _______
3. **Nome:** ________________ | **Propósito:** _______

### 5.3. Teste de Persistência

**Cookie permanece após:**
- [ ] Fechar aba
- [ ] Fechar navegador
- [ ] Logout
- [ ] Timeout (quanto tempo?: ______)

---

## 6. JavaScript e Framework

### 6.1. Framework Identificado

**Nome:** Adianti Framework / Outro: _________________

**Versão:** __________________________________________

**Arquivos JS principais:**
- _____________________________________________________
- _____________________________________________________

### 6.2. Funções JavaScript Relevantes

```javascript
// Função de envio do formulário
function nome_funcao() {
    // Código capturado
}

// Outras funções importantes
_____________________________________________________
```

### 6.3. Requisições AJAX

**Há requisições AJAX além do POST principal?**
- [ ] SIM
- [ ] NÃO

**Se SIM, listar:**
1. URL: ______________ | Propósito: ________________
2. URL: ______________ | Propósito: ________________

---

## 7. Validações e Regras de Negócio

### 7.1. Validações no Cliente

- [ ] Campos obrigatórios verificados no JS
- [ ] Formato de dados validado (números, datas)
- [ ] Soma de cargas horárias
- [ ] Outros: _______________________________________

### 7.2. Validações no Servidor

**Mensagens de erro encontradas:**
1. ____________________________________________________
2. ____________________________________________________
3. ____________________________________________________

### 7.3. Limites e Restrições

- **Máximo de disciplinas por requisição:** _________
- **Tamanho máximo do payload:** __________________
- **Rate limiting detectado?** [ ] SIM [ ] NÃO
- **Outros limites:** ________________________________

---

## 8. Exemplos de cURL

### 8.1. Login

```bash
curl 'https://semed.geduc.com.br/...' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Cookie: ...' \
  --data-raw 'login=...&password=...'
```

### 8.2. Salvar Histórico

```bash
curl 'https://semed.geduc.com.br/index.php?class=DisciplinasHistorico&method=...' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -H 'Cookie: PHPSESSID=...' \
  -H 'Referer: ...' \
  --data-raw 'IDALUNO=...&IDDISCIPLINAS%5B%5D=...'
```

---

## 9. Arquivos de Evidência

### 9.1. Arquivos HAR

- [ ] `geduc_login_20251220.har` - Captura do login
- [ ] `geduc_historico_20251220.har` - Captura completa
- [ ] Outros: _______________________________________

### 9.2. Screenshots

- [ ] Tela de login
- [ ] DevTools Network tab
- [ ] Formulário de cadastro preenchido
- [ ] Resposta de sucesso

**Localização:** `c:\gestao\historico geduc\capturas\`

---

## 10. Conclusões e Próximos Passos

### 10.1. Principais Descobertas

1. ____________________________________________________
2. ____________________________________________________
3. ____________________________________________________

### 10.2. Pontos de Atenção

⚠️ ____________________________________________________
⚠️ ____________________________________________________

### 10.3. Checklist de Implementação

- [ ] Estrutura de login confirmada
- [ ] CSRF token tratado (se aplicável)
- [ ] Arrays de disciplinas no formato correto
- [ ] Headers obrigatórios identificados
- [ ] Indicadores de sucesso/erro claros
- [ ] Pronto para implementar no POC

### 10.4. Próximas Ações

1. Atualizar `poc_exportacao_geduc.py` com descobertas
2. Testar POC com credenciais reais
3. Validar envio de histórico completo
4. Implementar módulo final em `src/exportadores/`

---

**Captura realizada por:** ___________________________  
**Data de conclusão:** _____/_____/2025  
**Status:** ⬜ Em andamento | ⬜ Concluída | ⬜ Validada
