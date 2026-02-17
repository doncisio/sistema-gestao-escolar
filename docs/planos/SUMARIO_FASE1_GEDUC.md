# Sumário Executivo - Fase 1: Análise GEDUC

## Status Geral

**Fase:** 1 - Reconhecimento e Prototipação  
**Data:** 20/01/2025  
**Progresso:** 60% (Tarefa 1.1 concluída)

---

## Descobertas Principais

### ✅ Formulário de Cadastro Identificado

**URL:** `https://semed.geduc.com.br/index.php`  
**Classe:** `DisciplinasHistorico`  
**Método:** `onEdit`  
**Form:** `form_Curriculo` (POST com multipart/form-data)

### 🔑 Parâmetros Obrigatórios

```
IDALUNO        → ID do aluno no GEDUC
IDINSTITUICAO  → ID da escola no GEDUC
ANO            → Ano letivo (ex: 2025)
IDCURSO        → ID da série (ex: 4 = 1º ANO)
IDCURRICULO    → ID do currículo ativo
TIPOESCOLA     → 1 (padrão)
```

### 📊 Estrutura de Disciplinas (Arrays)

O formulário usa **arrays sincronizados** para enviar múltiplas disciplinas:

```python
IDDISCIPLINAS[]  = [77, 78, 79, 80, 81, 82]     # IDs das disciplinas
CHT[]            = [400, 40, 40, 200, 120, 80]   # Cargas horárias
MEDIA[]          = [8.5, 9.0, 8.0, 7.5, 8.5, 9.0] # Médias
FALTA[]          = [0, 2, 0, 5, 3, 1]             # Faltas
SITUACAO[]       = [0, 0, 0, 0, 0, 0]             # 0=Aprovado, 1=Reprovado
```

**Exemplo real encontrado:**
- LÍNGUA PORTUGUESA (ID: 77, CHT: 400)
- ARTE (ID: 78, CHT: 40)
- EDUCAÇÃO FÍSICA (ID: 79, CHT: 40)
- MATEMÁTICA (ID: 80, CHT: 200)
- CIÊNCIAS (ID: 81, CHT: 120)
- GEOGRAFIA (ID: 82, CHT: 80)

---

## Desafios Identificados

### ⚠️ Mapeamento de IDs

**Problema:** Os IDs do sistema local são diferentes dos IDs do GEDUC.

**Solução proposta:** Criar 4 tabelas de mapeamento:

1. `mapeamento_alunos_geduc` - Aluno local ↔ IDALUNO GEDUC
2. `mapeamento_series_geduc` - Série local ↔ IDCURSO GEDUC
3. `mapeamento_disciplinas_geduc` - Disciplina local ↔ IDDISCIPLINAS GEDUC
4. `mapeamento_escolas_geduc` - Escola local ↔ IDINSTITUICAO GEDUC

### 🔐 Autenticação

**Requisitos:**
- Session cookie (PHPSESSID)
- Possível token CSRF
- Headers do navegador
- Framework Adianti com JavaScript customizado

---

## Código de Exemplo

### Estrutura do POST

```python
def enviar_historico_geduc(
    idaluno: int,          # 235718
    idinstituicao: int,    # 1318
    ano: int,              # 2025
    idcurso: int,          # 4 (1º ANO)
    idcurriculo: int,      # 69 (1º ANO Ativo)
    disciplinas: List[Dict]
) -> Response:
    
    data = {
        'IDALUNO': str(idaluno),
        'IDINSTITUICAO': str(idinstituicao),
        'ANO': str(ano),
        'IDESCOLA': '',
        'TIPOESCOLA': '1',
        'VISIVEL': '1',
        'IDCURSO': str(idcurso),
        'IDCURRICULO': str(idcurriculo),
        'IDDISCIPLINAS[]': [d['id'] for d in disciplinas],
        'CHT[]': [d['cht'] for d in disciplinas],
        'MEDIA[]': [d['media'] for d in disciplinas],
        'FALTA[]': [d['falta'] for d in disciplinas],
        'SITUACAO[]': [d['situacao'] for d in disciplinas]
    }
    
    return session.post(
        'https://semed.geduc.com.br/index.php',
        data=data,
        params={
            'class': 'DisciplinasHistorico',
            'method': 'onEdit',
            'IDCURSO': idcurso,
            'ANO': ano,
            'IDALUNO': idaluno,
            'IDINSTITUICAO': idinstituicao,
            'TIPOESCOLA': 1
        }
    )
```

---

## Próximos Passos

### Fase 1 - Tarefas Restantes

- [ ] **Tarefa 1.2:** Capturar requisições POST com DevTools
  - Identificar headers completos
  - Validar formato exato do payload
  - Documentar tokens CSRF (se houver)

- [ ] **Tarefa 1.3:** Criar script de teste POC
  - Implementar em `scripts/poc_exportacao_geduc.py`
  - Testar login automatizado
  - Validar submissão de 1 histórico
  - Verificar resposta de sucesso/erro

### Informações Adicionais Necessárias

- [ ] Lista completa de séries do GEDUC (1º ao 9º, EJA, etc.)
- [ ] Todas as disciplinas por série
- [ ] Validação: média aceita decimal? Quantas casas?
- [ ] Formato de resposta (JSON? HTML? Redirect?)
- [ ] Tratamento de erros do servidor

---

## Documentação Gerada

1. ✅ **FASE1_MAPEAMENTO_FORMULARIOS_GEDUC.md** (este documento)
   - Análise completa dos formulários
   - Estrutura de dados
   - Exemplos de código
   - Tabelas de mapeamento SQL

2. ⏳ **POC Scripts** (próxima tarefa)
   - scripts/poc_exportacao_geduc.py
   - Teste de autenticação
   - Teste de submissão

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| IDs do GEDUC mudam | Baixa | Alto | Criar processo de re-mapeamento automático |
| CSRF tokens | Média | Alto | Extrair token do HTML antes de POST |
| Session expira | Alta | Médio | Implementar renovação automática de sessão |
| Estrutura do form muda | Baixa | Alto | Versionamento do mapeamento |
| Rate limiting | Média | Médio | Implementar delays entre requisições |

---

## Conclusão

A **Fase 1 - Tarefa 1.1** foi concluída com sucesso. Temos:

✅ Estrutura completa do formulário documentada  
✅ Parâmetros obrigatórios identificados  
✅ Exemplo de dados reais do GEDUC  
✅ Proposta de tabelas de mapeamento  
✅ Código Python de exemplo  

**Próximo passo:** Capturar requisições reais com o navegador para validar headers e tokens de segurança.

---

**Estimativa para conclusão da Fase 1:** 3-4 dias úteis  
**Estimativa total do projeto:** 6-9 semanas (conforme planejamento original)
