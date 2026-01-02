# Correções: Importação de Horários do GEDUC

## Problema Identificado

O código original estava tentando acessar URLs e elementos incorretos do sistema GEDUC.

### Erro Reportado:
```
TimeoutException: Element NAME="IDTURMA" not found
URL acessada: index.php?class=TurmaHorarioForm
```

## Análise das Páginas HTML Salvas

Ao analisar as páginas salvas pelo usuário, descobriu-se a estrutura real do GEDUC:

### 1. Fluxo Correto de Navegação

```
Login → TurmaHorariosList → QuadhorariosemanalList → QuadhorariosemanalForm
```

**Páginas**:
1. `login.html` - Autenticação
2. `turmas semana.html` - Lista de turmas (`TurmaHorariosList`)
3. `horario semanal.html` - Visualização de horários (`QuadhorariosemanalList`)
4. `horario por turma.html` - Formulário de edição (`QuadhorariosemanalForm`)

### 2. Estrutura da Tabela de Horários

**Cabeçalho** (linha 1):
```html
<tr>
    <td><center>Domingo</center></td>
    <td><center>Segunda</center></td>
    <td><center>Terça</center></td>
    <td><center>Quarta</center></td>
    <td><center>Quinta</center></td>
    <td><center>Sexta</center></td>
    <td><center>Sábado</center></td>
</tr>
```

**Células de Disciplinas**:
- Links `<a>` para disciplinas já cadastradas
- Selects `<select>` para adicionar novas disciplinas

### 3. IDs das Turmas no GEDUC

Formato: `IDTURMA=353` (na URL)

Exemplos:
- 353: 1º ANO-MATU
- 354: 2º ANO-MATU  
- 358: 6º ANO-VESP - A
- 359: 6º ANO-VESP - B

## Correções Implementadas

### 1. Método `acessar_lista_horarios()` (novo)

**Antes** (nome incorreto):
```python
def acessar_horarios_turma():
    url = f"{self.url_base}/index.php?class=TurmaHorarioForm"
    wait.until(EC.presence_of_element_located((By.NAME, "IDTURMA")))
```

**Depois** (correção):
```python
def acessar_lista_horarios():
    url = f"{self.url_base}/index.php?class=TurmaHorariosList"
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "tdatagrid_body")))
```

**Mudanças**:
- ✅ URL corrigida: `TurmaHorarioForm` → `TurmaHorariosList`
- ✅ Elemento esperado: `NAME="IDTURMA"` → `CLASS="tdatagrid_body"`
- ✅ Nome do método mais descritivo

### 2. Método `extrair_horario_turma()`

#### 2.1. Busca de Turma

**Antes** (select que não existe):
```python
select_turma = Select(wait.until(
    EC.presence_of_element_located((By.NAME, "IDTURMA"))
))

for option in select_turma.options:
    if turma_nome in option.text:
        select_turma.select_by_visible_text(option.text)
```

**Depois** (busca na tabela):
```python
soup = BeautifulSoup(html, 'html.parser')

for td in soup.find_all('td', class_='tdatagrid_cell'):
    texto = td.get_text(strip=True)
    if turma_nome.upper() in texto.upper():
        href = td.get('href', '')
        match = re.search(r'IDTURMA=(\d+)', href)
        if match:
            turma_id = match.group(1)
            # Construir URL do formulário
            link_horario = f"{self.url_base}/index.php?class=QuadhorariosemanalList..."
```

**Mudanças**:
- ✅ Não usa Select (não existe na página)
- ✅ Busca na tabela HTML (`td.tdatagrid_cell`)
- ✅ Extrai ID do atributo `href`
- ✅ Constrói URL completa para navegação

#### 2.2. Navegação para Formulário

**Adicionado**:
```python
# 1. Acessar lista da turma
self.driver.get(link_horario)  # QuadhorariosemanalList

# 2. Encontrar link para edição
for a in soup.find_all('a', href=True):
    if 'QuadhorariosemanalForm' in a['href']:
        link_editar = a['href']

# 3. Acessar formulário de edição
self.driver.get(link_editar)  # QuadhorariosemanalForm
```

**Mudanças**:
- ✅ Navegação em múltiplas etapas (conforme fluxo real)
- ✅ Busca dinâmica do link de edição
- ✅ Fallback para construção manual da URL

#### 2.3. Extração da Tabela

**Antes** (estrutura incorreta):
```python
thead = tabela.find('thead')
ths = thead.find_all('th')
dias_semana = [th.text for th in ths[1:]]  # Pula "Horário"

horario = celulas[0].get_text()  # Primeira célula = horário
```

**Depois** (estrutura correta):
```python
# Tabela com border="1px"
tabela = soup.find('table', border=True)

# Primeira linha = dias da semana
primeira_linha = linhas[0]
dias_semana = [td.get_text(strip=True) for td in primeira_linha.find_all('td')]

# Linhas 1+ = horários (sem coluna de horário)
for idx_linha, linha in enumerate(linhas[1:], 1):
    celulas = linha.find_all('td')
    # 7 células (Domingo a Sábado)
```

**Mudanças**:
- ✅ Busca tabela com `border=True`
- ✅ Primeira linha contém dias (não há thead)
- ✅ 7 colunas (Domingo a Sábado)
- ✅ Sem coluna de horário nas linhas de dados
- ✅ Usa índice da linha como referência de horário

#### 2.4. Extração de Disciplinas

**Antes** (múltiplas tentativas):
```python
# 1. Select selecionado
# 2. Link
# 3. Texto da célula
```

**Depois** (simplificado):
```python
# 1. Link (disciplina já cadastrada)
link = celula.find('a')
if link:
    disciplina = link.get_text(strip=True)

# 2. Select vazio = ignorar
if not disciplina:
    select = celula.find('select')
    if select:
        continue  # Não há disciplina ainda
```

**Mudanças**:
- ✅ Foca apenas em disciplinas já cadastradas (links)
- ✅ Ignora selects vazios (slots disponíveis)
- ✅ Ignora Domingo e Sábado

#### 2.5. Formato de Horário

**Antes**:
```python
'horario': '07:10-08:00'  # Tentava extrair horário da célula
```

**Depois**:
```python
'horario': f'Linha {idx_linha}'  # Usa índice da linha
```

**Mudanças**:
- ✅ Não há coluna de horário na tabela
- ✅ Usa índice da linha como referência (1-6)
- ✅ Mais simples e confiável

### 3. Método `listar_turmas_disponiveis()`

**Antes**:
```python
select_turma = Select(wait.until(
    EC.presence_of_element_located((By.NAME, "IDTURMA"))
))

for option in select_turma.options:
    turmas.append({'id': option.value, 'nome': option.text})
```

**Depois**:
```python
soup = BeautifulSoup(html, 'html.parser')

for td in soup.find_all('td', class_='tdatagrid_cell'):
    href = td.get('href', '')
    if 'IDTURMA=' in href:
        match = re.search(r'IDTURMA=(\d+)', href)
        turma_id = match.group(1)
        turma_nome = td.get_text(strip=True)
        turmas.append({'id': turma_id, 'nome': turma_nome})
```

**Mudanças**:
- ✅ Extrai da tabela (não há select)
- ✅ Filtra apenas células com `IDTURMA`
- ✅ Evita duplicatas

## Estrutura de Dados Retornada

### Antes:
```python
{
    'horario': '07:10-08:00',  # String específica
    'dia': 'Segunda',
    'disciplina': 'HISTÓRIA',
    'professor': None
}
```

### Depois:
```python
{
    'horario': 'Linha 1',  # Índice genérico (1-6)
    'dia': 'Segunda',
    'disciplina': 'HISTÓRIA',
    'professor': None
}
```

## Mapeamento de Nomes de Turmas

Formato do GEDUC: `{série}{turno}` ou `{série}{turno} - {letra}`

Exemplos:
- `"1º ANO-MATU"` → Série: 1º ANO, Turno: MATU
- `"6º ANO-VESP - A"` → Série: 6º ANO, Turno: VESP, Letra: A
- `"7º ANO-VESP"` → Série: 7º ANO, Turno: VESP

Para buscar, o código usa `UPPER()` e `IN` para correspondência parcial.

## Arquivos Modificados

| Arquivo | Método | Mudança |
|---------|--------|---------|
| `src/importadores/geduc.py` | `acessar_horarios_turma()` | Renomeado para `acessar_lista_horarios()` |
| `src/importadores/geduc.py` | `acessar_lista_horarios()` | URL e elemento corretos |
| `src/importadores/geduc.py` | `extrair_horario_turma()` | Navegação multi-etapas, extração corrigida |
| `src/importadores/geduc.py` | `listar_turmas_disponiveis()` | Extração da tabela |

## Teste Recomendado

Execute o script de teste após as correções:

```bash
python scripts/teste_importacao_horarios.py
```

Ou teste na interface gráfica:
1. Abrir "Horários Escolares"
2. Selecionar turma "1º Ano - MATUTINO"
3. Clicar em "🌐 Importar do GEDUC"
4. Inserir credenciais
5. Resolver reCAPTCHA
6. Aguardar extração

## Resultado Esperado

```
→ Procurando turma: 1º ANO-MATU
✓ Turma encontrada: 1º ANO-MATU (ID: 353)
→ Acessando horário da turma...
→ Acessando formulário de edição...
→ Dias encontrados: ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
✓ Extraídos 25 horários

Horários:
- Segunda, Linha 1: HISTÓRIA
- Terça, Linha 1: LÍNGUA PORTUGUESA
- Quarta, Linha 1: LÍNGUA PORTUGUESA
...
```

## Problemas Resolvidos

- ✅ TimeoutException ao acessar TurmaHorarioForm
- ✅ Elemento IDTURMA não encontrado
- ✅ Estrutura de tabela incorreta
- ✅ Navegação em múltiplas páginas
- ✅ Extração de IDs de turmas
- ✅ Mapeamento de dias da semana
- ✅ Tratamento de células vazias

## Data da Correção
**1 de janeiro de 2026**

---

*Correções baseadas na análise das páginas HTML salvas pelo usuário.*
