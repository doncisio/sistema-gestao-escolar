# Fase 1: Mapeamento dos Formulários GEDUC

**Data:** 2025-01-20  
**Status:** Em Andamento  
**Responsável:** Sistema de Exportação Histórico Escolar → GEDUC

---

## 1. Visão Geral

Este documento registra a análise completa dos formulários e estruturas de dados do sistema GEDUC online, necessários para implementar a exportação de históricos escolares do sistema local.

### 1.1. Arquivos HTML Analisados

| Arquivo | URL Original | Classe GEDUC | Parâmetros |
|---------|-------------|--------------|------------|
| `login.html` | N/A | LoginForm | - |
| `lista alunos.html` | `index.php?class=FichaAlunoForm&method=onReload` | FichaAlunoForm | `IDALUNO`, `IDTURMA`, `CLASSEOLD`, `METHODOLD` |
| `historico aluno_id.html` | `index.php?class=HistoricoAcadList&method=onReload` | HistoricoAcadList | `IDALUNO` |
| `cadastro das notas.html` | `index.php?class=DisciplinasHistorico&method=onEdit` | DisciplinasHistorico | `IDCURSO`, `ANO`, `IDALUNO`, `IDINSTITUICAO`, `TIPOESCOLA` |
| `info escola.html` | N/A | - | - |
| `lista turmas.html` | N/A | TurmaList | - |
| `ficha do aluno.html` | N/A | FichaAlunoForm | - |
| `turma_id.html` | N/A | TurmaForm | - |

---

## 2. Formulário de Cadastro de Notas (DisciplinasHistorico)

### 2.1. URL e Método

```
URL: https://semed.geduc.com.br/index.php
Classe: DisciplinasHistorico
Método: onEdit
Método HTTP: POST
Form Name: form_Curriculo
Form ID: form_Curriculo
Enctype: multipart/form-data
```

### 2.2. Parâmetros de URL (GET)

| Parâmetro | Tipo | Obrigatório | Exemplo | Descrição |
|-----------|------|-------------|---------|-----------|
| `class` | string | Sim | `DisciplinasHistorico` | Classe controladora |
| `method` | string | Sim | `onEdit` | Método da classe |
| `IDCURSO` | int | Sim | `4` | ID do curso/série |
| `ANO` | int | Sim | `2025` | Ano letivo |
| `IDALUNO` | int | Sim | `235718` | ID do aluno no GEDUC |
| `IDINSTITUICAO` | int | Sim | `1318` | ID da instituição |
| `TIPOESCOLA` | int | Sim | `1` | Tipo da escola |

### 2.3. Campos Ocultos (Hidden)

```html
<input name="IDALUNO" type="hidden" value="235718">
<input name="IDINSTITUICAO" type="hidden" value="1318">
<input name="ANO" type="hidden" value="2025">
<input name="IDESCOLA" type="hidden" value="">
<input name="TIPOESCOLA" type="hidden" value="1">
```

### 2.4. Campos do Formulário Principal

| Campo | Nome | Tipo | Widget | Obrigatório | Valores | Descrição |
|-------|------|------|--------|-------------|---------|-----------|
| Curso Visível | `VISIVEL` | radio | tradiobutton | Não | `0` (NÃO), `1` (SIM) | Define visibilidade do curso |
| Série/Curso | `IDCURSO` | select | tcombo | Sim | IDs de cursos | Seleção da série |
| Currículo | `IDCURRICULO` | select | tcombo | Sim | IDs de currículos | Currículo associado |

**Exemplo de opções de IDCURSO:**
```javascript
<option value="4" selected="1">1º ANO</option>
```

**Exemplo de opções de IDCURRICULO:**
```javascript
<option value="0">Selecione uma opção</option>
<option value="69">1º ANO (Ativo)</option>
<option value="82">MC 1° ANO INTEGRAL (Ativo)</option>
```

### 2.5. Grid de Disciplinas (Arrays)

A tabela de disciplinas usa arrays para permitir múltiplas disciplinas em uma única submissão:

```html
<table class="tdatagrid_table" id="tdatagrid_1108444027">
  <thead>
    <tr>
      <th> </th>
      <th>COMPONENTE CURRICULAR</th>
      <th>CHT</th>
      <th>MÉDIA</th>
      <th>FALTA</th>
      <th>SITUAÇÃO</th>
    </tr>
  </thead>
  <tbody>
    <!-- Linha para cada disciplina -->
  </tbody>
</table>
```

#### 2.5.1. Campos por Linha de Disciplina

| Campo | Nome Array | Tipo | Widget | Largura | Validação | Descrição |
|-------|-----------|------|--------|---------|-----------|-----------|
| ID Disciplina | `IDDISCIPLINAS[]` | hidden | thidden | - | - | ID da disciplina (ex: 77, 78, 79...) |
| Componente | - | text | - | 59% | read-only | Nome da disciplina (ex: "LÍNGUA PORTUGUESA") |
| CHT | `CHT[]` | text | tentry | 50px | numérico | Carga Horária Total (ex: 400, 40, 120) |
| Média | `MEDIA[]` | text | tentry | 50px | numérico | Média final (vazio inicialmente) |
| Falta | `FALTA[]` | text | tentry | 50px | numérico | Total de faltas (vazio inicialmente) |
| Situação | `SITUACAO[]` | select | tcombo | - | 0 ou 1 | `0` = Aprovado, `1` = Reprovado |

#### 2.5.2. Exemplo de Dados (1ª Linha)

```html
<tr class="tdatagrid_row_even">
  <td><input name="IDDISCIPLINAS[]" value="77" type="hidden"></td>
  <td>LÍNGUA PORTUGUESA</td>
  <td><input name="CHT[]" value="400" style="width:50px;"></td>
  <td><input name="MEDIA[]" value="" style="width:50px;"></td>
  <td><input name="FALTA[]" value="" style="width:50px;"></td>
  <td>
    <select name="SITUACAO[]">
      <option value=""></option>
      <option value="0">Aprovado</option>
      <option value="1">Reprovado</option>
    </select>
  </td>
</tr>
```

#### 2.5.3. Exemplo de Disciplinas Encontradas

```
1. LÍNGUA PORTUGUESA (ID: 77, CHT: 400)
2. ARTE (ID: 78, CHT: 40)
3. EDUCAÇÃO FÍSICA (ID: 79, CHT: 40)
4. MATEMÁTICA (ID: 80, CHT: 200)
5. CIÊNCIAS (ID: 81, CHT: 120)
6. GEOGRAFIA (ID: 82, CHT: 80)
```

### 2.6. Botão de Ação

```html
<button id="tbutton_buttonCarregar" name="buttonCarregar" 
        onclick="Adianti.waitMessage = 'Carregando';
                 __adianti_post_data('form_Curriculo', 
                 'class=DisciplinasHistorico&method=onEdit&IDCURSO=4&ANO=2025&IDALUNO=235718&IDINSTITUICAO=1318&TIPOESCOLA=1&CARREGAR=1');
                 return false;">
  <i class="fas fa-reply-all red"></i>
  Carregar Disciplinas
</button>
```

**Parâmetro adicional:** `CARREGAR=1` (indica que é para carregar as disciplinas)

---

## 3. Estrutura de POST Esperada

### 3.1. Formato do Payload

Quando o formulário é submetido, o payload POST deve conter:

```python
{
    # Campos ocultos
    'IDALUNO': '235718',
    'IDINSTITUICAO': '1318',
    'ANO': '2025',
    'IDESCOLA': '',
    'TIPOESCOLA': '1',
    
    # Campos visíveis
    'VISIVEL': '1',
    'IDCURSO': '4',
    'IDCURRICULO': '69',
    
    # Arrays de disciplinas (sincronizados por índice)
    'IDDISCIPLINAS[]': ['77', '78', '79', '80', '81', '82'],
    'CHT[]': ['400', '40', '40', '200', '120', '80'],
    'MEDIA[]': ['8.5', '9.0', '8.0', '7.5', '8.5', '9.0'],
    'FALTA[]': ['0', '2', '0', '5', '3', '1'],
    'SITUACAO[]': ['0', '0', '0', '0', '0', '0']
}
```

### 3.2. Exemplo com requests Python

```python
import requests
from typing import List, Dict

def enviar_historico_geduc(
    idaluno: int,
    idinstituicao: int,
    ano: int,
    idcurso: int,
    idcurriculo: int,
    disciplinas: List[Dict[str, str]],
    session: requests.Session
) -> requests.Response:
    """
    Envia histórico escolar para GEDUC.
    
    Args:
        idaluno: ID do aluno no GEDUC
        idinstituicao: ID da instituição
        ano: Ano letivo
        idcurso: ID do curso/série
        idcurriculo: ID do currículo
        disciplinas: Lista de dicts com {id, cht, media, falta, situacao}
        session: Sessão autenticada
    
    Returns:
        Response object
    """
    url = "https://semed.geduc.com.br/index.php"
    
    # Prepara arrays sincronizados
    data = {
        'IDALUNO': str(idaluno),
        'IDINSTITUICAO': str(idinstituicao),
        'ANO': str(ano),
        'IDESCOLA': '',
        'TIPOESCOLA': '1',
        'VISIVEL': '1',
        'IDCURSO': str(idcurso),
        'IDCURRICULO': str(idcurriculo),
        'IDDISCIPLINAS[]': [],
        'CHT[]': [],
        'MEDIA[]': [],
        'FALTA[]': [],
        'SITUACAO[]': []
    }
    
    # Adiciona disciplinas
    for disc in disciplinas:
        data['IDDISCIPLINAS[]'].append(disc['id'])
        data['CHT[]'].append(disc['cht'])
        data['MEDIA[]'].append(disc['media'])
        data['FALTA[]'].append(disc['falta'])
        data['SITUACAO[]'].append(disc['situacao'])
    
    # Envia POST
    response = session.post(
        url,
        data=data,
        params={
            'class': 'DisciplinasHistorico',
            'method': 'onEdit',
            'IDCURSO': idcurso,
            'ANO': ano,
            'IDALUNO': idaluno,
            'IDINSTITUICAO': idinstituicao,
            'TIPOESCOLA': 1
        },
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )
    
    return response
```

---

## 4. Fluxo de Navegação

### 4.1. Sequência de Acesso

```
1. Login → LoginForm
   ↓
2. Dashboard → DashboardAbertura
   ↓
3. Alunos → FichaAlunoForm (lista de alunos)
   ↓
4. Selecionar Aluno → FichaAlunoForm?IDALUNO=X
   ↓
5. Histórico → HistoricoAcadList?IDALUNO=X
   ↓
6. Cadastrar Notas → DisciplinasHistorico?IDCURSO=X&ANO=X&IDALUNO=X...
```

### 4.2. JavaScript/AJAX

O sistema usa o framework **Adianti** com funções JavaScript customizadas:

```javascript
// Enviar dados do formulário
__adianti_post_data('form_Curriculo', 'class=DisciplinasHistorico&method=onEdit&...');

// Enviar lookup (busca)
__adianti_post_lookup('form_Curriculo', 'class=DisciplinasHistorico&method=verificaCurriculo&static=1', ...);

// Popular combobox
tcombo_clear('form_Curriculo', 'IDCURRICULO', true);
tcombo_add_option('form_Curriculo', 'IDCURRICULO', '69', '1º ANO (Ativo)');

// Enviar dados para campo específico
tform_send_data('form_Curriculo', 'IDALUNO', '235718', true, '0');
tform_send_data_by_id('form_Curriculo', 'IDALUNO', '235718', true, '0');
```

---

## 5. Mapeamento: Banco Local → GEDUC

### 5.1. Tabelas Locais vs Parâmetros GEDUC

| Tabela Local | Campo Local | Parâmetro GEDUC | Tipo | Observações |
|--------------|-------------|-----------------|------|-------------|
| `alunos` | `id` | - | - | Precisa mapear para `IDALUNO` do GEDUC |
| `alunos` | `nome` | - | - | Usado para buscar aluno no GEDUC |
| `historico_escolar` | `aluno_id` | `IDALUNO` | int | ID do GEDUC, não local |
| `historico_escolar` | `anoletivo_id` | `ANO` | int | Ano letivo |
| `historico_escolar` | `serie_id` | `IDCURSO` | int | Mapear série local → ID GEDUC |
| `historico_escolar` | `disciplina_id` | `IDDISCIPLINAS[]` | array | Mapear disciplina local → ID GEDUC |
| `historico_escolar` | `carga_horaria` | `CHT[]` | array | Carga horária total |
| `historico_escolar` | `nota_final` | `MEDIA[]` | array | Média final |
| `historico_escolar` | `faltas` | `FALTA[]` | array | Total de faltas |
| `historico_escolar` | `situacao` | `SITUACAO[]` | array | Aprovado (0) / Reprovado (1) |
| `escolas` | `id` | `IDINSTITUICAO` | int | ID da escola no GEDUC |
| - | - | `IDCURRICULO` | int | Buscar currículo ativo para a série |
| - | - | `TIPOESCOLA` | int | `1` (padrão) |
| - | - | `VISIVEL` | int | `1` (SIM) ou `0` (NÃO) |

### 5.2. Tabelas de Mapeamento Necessárias

Precisaremos criar tabelas auxiliares para armazenar os relacionamentos:

```sql
-- Mapear alunos locais para GEDUC
CREATE TABLE IF NOT EXISTS mapeamento_alunos_geduc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id INT NOT NULL,              -- ID local
    geduc_idaluno INT NOT NULL,         -- ID no GEDUC
    data_mapeamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id),
    UNIQUE KEY (aluno_id)
);

-- Mapear séries locais para GEDUC
CREATE TABLE IF NOT EXISTS mapeamento_series_geduc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serie_id INT NOT NULL,              -- ID local
    geduc_idcurso INT NOT NULL,         -- ID no GEDUC
    nome_local VARCHAR(100),
    nome_geduc VARCHAR(100),
    data_mapeamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (serie_id) REFERENCES series(id),
    UNIQUE KEY (serie_id)
);

-- Mapear disciplinas locais para GEDUC
CREATE TABLE IF NOT EXISTS mapeamento_disciplinas_geduc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    disciplina_id INT NOT NULL,         -- ID local
    geduc_iddisciplina INT NOT NULL,    -- ID no GEDUC
    serie_id INT,                       -- Disciplina pode variar por série
    nome_local VARCHAR(100),
    nome_geduc VARCHAR(100),
    data_mapeamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id),
    FOREIGN KEY (serie_id) REFERENCES series(id),
    UNIQUE KEY (disciplina_id, serie_id)
);

-- Mapear escolas locais para GEDUC
CREATE TABLE IF NOT EXISTS mapeamento_escolas_geduc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    escola_id INT NOT NULL,             -- ID local
    geduc_idinstituicao INT NOT NULL,   -- ID no GEDUC
    nome_local VARCHAR(200),
    nome_geduc VARCHAR(200),
    data_mapeamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (escola_id) REFERENCES escolas(id),
    UNIQUE KEY (escola_id)
);
```

---

## 6. Validações Identificadas

### 6.1. Validações de Campos

| Campo | Tipo Validação | Regra | Mensagem de Erro Esperada |
|-------|----------------|-------|---------------------------|
| `IDCURSO` | Obrigatório | Deve estar selecionado | "Selecione uma série" |
| `IDCURRICULO` | Obrigatório | Deve estar selecionado | "Selecione um currículo" |
| `CHT[]` | Numérico | Inteiro positivo | "Carga horária inválida" |
| `MEDIA[]` | Numérico | 0.0 - 10.0 | "Média deve estar entre 0 e 10" |
| `FALTA[]` | Numérico | Inteiro ≥ 0 | "Número de faltas inválido" |
| `SITUACAO[]` | Enum | 0, 1, ou vazio | "Situação inválida" |

### 6.2. Validações de Negócio

1. **Arrays Sincronizados:** Todos os arrays (`IDDISCIPLINAS[]`, `CHT[]`, `MEDIA[]`, `FALTA[]`, `SITUACAO[]`) devem ter o mesmo tamanho
2. **Disciplinas do Currículo:** As disciplinas devem corresponder ao currículo selecionado
3. **Ano Letivo:** O ano deve estar dentro do período permitido pela instituição
4. **Aluno Ativo:** O aluno deve existir e estar ativo no sistema GEDUC

---

## 7. Próximos Passos da Fase 1

### 7.1. Tarefa 1.2 - Captura de Requisições (Pendente)

- [ ] Usar DevTools do navegador para capturar requisições POST reais
- [ ] Documentar headers completos (cookies, tokens CSRF, etc.)
- [ ] Identificar possíveis campos anti-CSRF
- [ ] Validar formato exato do payload

### 7.2. Tarefa 1.3 - Script de Teste (Pendente)

- [ ] Criar `scripts/poc_exportacao_geduc.py`
- [ ] Implementar login automatizado
- [ ] Testar preenchimento de 1 registro
- [ ] Validar resposta de sucesso/erro

### 7.3. Documentação Adicional Necessária

- [ ] Mapeamento completo de todas as séries (1º ao 9º ano, EJA, etc.)
- [ ] Lista completa de disciplinas por série
- [ ] Regras de validação de média (pode ser decimal? quantas casas?)
- [ ] Formato de data/hora aceito (se houver campos de data)
- [ ] Tratamento de conceitos vs notas numéricas

---

## 8. Observações Importantes

### 8.1. Framework Adianti

O GEDUC usa o framework **Adianti**, que:
- Gera IDs únicos para widgets (ex: `tcombo_1093829297`)
- Usa prefixos em classes CSS: `tfield`, `tcombo`, `tentry`, `thidden`
- Tem funções JavaScript customizadas para submissão AJAX
- Mantém estado via hidden inputs

### 8.2. Session e Cookies

⚠️ **ATENÇÃO:** É necessário manter a sessão autenticada:
- Cookie de sessão (provavelmente `PHPSESSID`)
- Possível token CSRF
- Headers específicos do navegador

### 8.3. Encoding

- **Charset:** UTF-8
- **Content-Type:** `application/x-www-form-urlencoded` ou `multipart/form-data`
- **Accept-Language:** pt-BR

---

## 9. Glossário GEDUC

| Termo GEDUC | Significado | Equivalente Local |
|-------------|-------------|-------------------|
| IDALUNO | ID único do aluno | aluno_id (mas diferente) |
| IDCURSO | ID da série/curso | serie_id (mas diferente) |
| IDCURRICULO | ID do currículo (grade curricular) | - (não existe) |
| IDINSTITUICAO | ID da escola | escola_id (mas diferente) |
| IDDISCIPLINAS | ID da disciplina | disciplina_id (mas diferente) |
| CHT | Carga Horária Total | carga_horaria |
| MEDIA | Média final | nota_final |
| FALTA | Total de faltas | faltas |
| SITUACAO | Status aprovação | situacao |
| TIPOESCOLA | Tipo da escola (1=regular) | - |
| VISIVEL | Curso visível no histórico | - |

---

**Documento criado em:** 2025-01-20  
**Última atualização:** 2025-01-20  
**Responsável:** Sistema de Gestão Escolar - Módulo GEDUC
