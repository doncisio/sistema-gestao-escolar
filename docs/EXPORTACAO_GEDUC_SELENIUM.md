# Exportação GEDUC - Abordagem com Selenium

**Data:** 20/12/2025  
**Status:** Implementado - Pronto para testes  
**Decisão:** Usar Selenium (reutilizar `AutomacaoGEDUC`)

---

## 🎯 Decisão de Arquitetura

### Descoberta Importante

O sistema **já possui** um módulo robusto de automação do GEDUC:
- **Arquivo:** `src/importadores/geduc.py`
- **Classe:** `AutomacaoGEDUC`
- **Uso atual:** Importar notas do GEDUC para o sistema local
- **Tecnologia:** Selenium WebDriver + Chrome

### Por Que Reutilizar?

✅ **Login já implementado** (com suporte a reCAPTCHA manual)  
✅ **Navegador configurado** (ChromeDriver automático)  
✅ **Tratamento de erros** robusto  
✅ **Logging** integrado  
✅ **Interface já conhece** o padrão (mesma UX)

---

## 📁 Arquitetura Implementada

### Estrutura de Arquivos

```
src/
├── importadores/
│   └── geduc.py                    # AutomacaoGEDUC (existente)
│       └── Importa notas: GEDUC → Sistema Local
│
└── exportadores/
    ├── __init__.py                 # Novo
    └── geduc_exportador.py         # Novo
        └── ExportadorGEDUC (herda AutomacaoGEDUC)
            └── Exporta histórico: Sistema Local → GEDUC
```

### Classe `ExportadorGEDUC`

**Herança:**
```python
class ExportadorGEDUC(AutomacaoGEDUC):
    """Exportador que herda funcionalidades do importador"""
```

**Métodos Herdados:**
- `__init__(headless=False)`
- `iniciar_navegador()` - Inicia Chrome com ChromeDriver
- `fazer_login(usuario, senha)` - Login com reCAPTCHA manual
- `driver` - Instância do Selenium WebDriver

**Métodos Novos:**
- `acessar_cadastro_historico()` - Navega para formulário
- `preencher_historico()` - Preenche campos do formulário
- `salvar_historico()` - Submete e valida resultado
- `_verificar_resultado_salvamento()` - Detecta sucesso/erro

---

## 🔧 Como Funciona

### Fluxo de Exportação

```
┌─────────────────────────────────────┐
│ 1. Interface historico_escolar.py  │
│    Usuário clica "Exportar GEDUC"  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. exportar_historico_aluno()       │
│    Função principal do exportador   │
└──────────────┬──────────────────────┘
               │
               ├─► Inicializar Chrome
               ├─► Login (reCAPTCHA manual)
               ├─► Navegar para formulário
               ├─► Preencher disciplinas
               ├─► Salvar
               └─► Verificar resultado
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Retorna resultado para interface │
│    {sucesso, mensagem, registros}   │
└─────────────────────────────────────┘
```

### Parâmetros da Função Principal

```python
exportar_historico_aluno(
    aluno_id=123,                    # ID local do aluno
    usuario_geduc="seu_usuario",     # Credenciais GEDUC
    senha_geduc="sua_senha",
    dados_historico={
        'idaluno_geduc': 235718,     # ID do aluno no GEDUC
        'idinstituicao': 1318,
        'ano': 2025,
        'idcurso': 4,
        'idcurriculo': 69,
        'disciplinas': [
            {
                'id': '77',
                'cht': '400',
                'media': '8.5',
                'falta': '0',
                'situacao': '0'
            },
            # ... mais disciplinas
        ]
    },
    callback_progresso=lambda msg: print(msg)
)
```

---

## 🧪 Como Testar

### 1. Configurar Credenciais

```powershell
$env:GEDUC_USER = "seu_usuario"
$env:GEDUC_PASS = "sua_senha"
```

### 2. Executar Script de Teste

```powershell
python scripts/testar_exportador_geduc.py
```

### 3. O Que Acontece

1. ✅ Chrome abre automaticamente
2. 🔐 Navega para página de login
3. ⚠️ **VOCÊ PRECISA RESOLVER O reCAPTCHA MANUALMENTE**
4. ✅ Após resolver, clica em "Login"
5. 📝 Navega para formulário de histórico
6. 🔄 Preenche todas as disciplinas
7. 💾 Clica em "Salvar"
8. ✅ Verifica se salvou com sucesso

### 4. Resultado Esperado

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                     TESTE - Exportador GEDUC                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

✓ Usuário configurado: seu_usuario

📋 Dados do teste:
  Aluno ID (GEDUC): 235718
  Instituição: 1318
  Ano: 2025
  Curso: 4
  Disciplinas: 3

⚠️  Continuar com o teste? (s/N): s

════════════════════════════════════════════════════════════════════════════════
INICIANDO EXPORTAÇÃO
════════════════════════════════════════════════════════════════════════════════

  → Iniciando exportação para GEDUC...
  → Iniciando navegador Chrome...
  → Fazendo login no GEDUC...
  → ⚠ ATENÇÃO: Resolva o reCAPTCHA manualmente no navegador!
  → ✓ Login realizado com sucesso
  → Acessando formulário de histórico...
  → ✓ Formulário carregado
  → Preenchendo 3 disciplinas...
  → ✓ Formulário preenchido
  → Salvando histórico...
  → ✓ Exportação concluída com sucesso!

════════════════════════════════════════════════════════════════════════════════
RESULTADO
════════════════════════════════════════════════════════════════════════════════

✅ SUCESSO!
  Registros enviados: 3
  Mensagem: Histórico salvo com sucesso
```

---

## ⚙️ Próximos Passos

### 1. Ajustar Formulário (Tarefa em andamento)

O método `preencher_historico()` tem **estratégias genéricas** para preencher campos.
Pode ser necessário ajustar após **captura real** do formulário:

**Fazer:**
1. Executar teste com dados reais
2. Inspecionar formulário com DevTools
3. Ajustar seletores XPath se necessário
4. Verificar se arrays de disciplinas funcionam

**Possíveis ajustes:**
- Seletores de elementos (`By.NAME`, `By.XPATH`)
- Estrutura de arrays (`IDDISCIPLINAS[]`, `CHT[]`, etc.)
- Botões de ação ("Carregar Disciplinas", "Salvar")
- Detecção de sucesso/erro

### 2. Integrar com Interface

O botão já foi criado em `historico_escolar.py`, mas precisa:

**Código atual (interface):**
```python
def exportar_para_geduc(self):
    # ... validações ...
    from src.exportadores.geduc_exportador import exportar_historico_aluno
    # ... chamada da função ...
```

**Precisa adicionar:**
1. Buscar dados do aluno no banco local
2. Mapear estrutura local → GEDUC
3. Solicitar credenciais ao usuário
4. Construir dicionário `dados_historico`
5. Chamar `exportar_historico_aluno()`

### 3. Mapeamento de Dados

Criar serviço para mapear dados do banco local para formato GEDUC:

```python
# src/services/geduc_mapper.py

def mapear_historico_para_geduc(aluno_id_local: int) -> dict:
    """
    Busca histórico do aluno no banco local
    e converte para formato esperado pelo GEDUC
    """
    # TODO: Implementar
    pass
```

**Perguntas a responder:**
- Como encontrar `idaluno_geduc` a partir do ID local?
- Onde buscar `idcurso`, `idcurriculo`?
- Como mapear disciplinas locais → IDs GEDUC?
- Armazenar vínculo Local ↔ GEDUC em nova tabela?

---

## 📊 Comparação: Selenium vs Requests

| Aspecto | Selenium (Escolhido) | Requests (Alternativa) |
|---------|---------------------|------------------------|
| **Login** | ✅ reCAPTCHA manual funciona | ❌ Difícil contornar reCAPTCHA |
| **Manutenção** | ✅ Reutiliza código existente | ❌ Código novo do zero |
| **Velocidade** | ⚠️ Mais lento (navegador) | ✅ Mais rápido (HTTP direto) |
| **Confiabilidade** | ✅ Simula usuário real | ⚠️ Pode quebrar com mudanças |
| **Debugging** | ✅ Visual, fácil debugar | ❌ Só logs |
| **Dependências** | ⚠️ ChromeDriver necessário | ✅ Apenas `requests` |

**Conclusão:** Selenium vence pela **reutilização** e **facilidade de manutenção**.

---

## 🐛 Troubleshooting

### Erro: "ChromeDriver não encontrado"

**Solução:**
```powershell
pip install webdriver-manager
```

Ou baixar manualmente de:
https://googlechromelabs.github.io/chrome-for-testing/

### Erro: "Timeout no reCAPTCHA"

**Solução:**
- Resolver o reCAPTCHA mais rápido (tempo padrão: 120s)
- Ou aumentar timeout:
  ```python
  exportador.fazer_login(usuario, senha, timeout_recaptcha=300)
  ```

### Erro: "Botão Salvar não encontrado"

**Solução:**
- Inspecionar formulário com DevTools
- Verificar texto do botão (pode ser "Gravar", "Enviar", etc.)
- Ajustar em `salvar_historico()`

### Erro: "Campos não preenchidos"

**Solução:**
- Capturar HTML do formulário
- Ajustar seletores XPath
- Verificar se campos são dinâmicos (gerados por JS)

---

## 📚 Referências

- **Módulo Importador:** [src/importadores/geduc.py](../src/importadores/geduc.py)
- **Módulo Exportador:** [src/exportadores/geduc_exportador.py](../src/exportadores/geduc_exportador.py)
- **Interface:** [src/interfaces/historico_escolar.py](../src/interfaces/historico_escolar.py)
- **Teste:** [scripts/testar_exportador_geduc.py](../scripts/testar_exportador_geduc.py)
- **Análise Fase 1:** [FASE1_MAPEAMENTO_FORMULARIOS_GEDUC.md](FASE1_MAPEAMENTO_FORMULARIOS_GEDUC.md)

---

**Última atualização:** 20/12/2025  
**Status:** ✅ Implementado, aguardando testes  
**Próximo passo:** Executar `testar_exportador_geduc.py` com credenciais reais
