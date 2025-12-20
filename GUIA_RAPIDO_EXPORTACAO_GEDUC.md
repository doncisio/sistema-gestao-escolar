# 🚀 Guia Rápido - Exportação para GEDUC

**Versão:** 1.0  
**Data:** 20/12/2025  
**Status:** Fase 1 - Mapeamento e POC

---

## 📋 Visão Geral

Este guia fornece instruções passo a passo para configurar e executar a exportação de dados do sistema de gestão escolar local para o sistema GEDUC online.

---

## ⚙️ Pré-requisitos

- [ ] Python 3.8 ou superior instalado
- [ ] Acesso ao sistema GEDUC online
- [ ] Credenciais válidas (usuário e senha)
- [ ] Navegador com DevTools (Chrome ou Firefox)
- [ ] Conexão estável com a internet

### Pacotes Python Necessários

```bash
pip install requests beautifulsoup4 lxml
```

---

## 📂 Estrutura de Arquivos

```
c:\gestao\
├── docs/
│   ├── TAREFA_1.2_CAPTURA_REQUISICOES.md      # Guia de captura
│   ├── TEMPLATE_REQUISICOES_CAPTURADAS.md     # Template para documentar
│   └── FASE1_MAPEAMENTO_FORMULARIOS_GEDUC.md  # Análise completa
├── scripts/
│   ├── poc_exportacao_geduc.py                # Script POC principal
│   ├── analisador_har.py                      # Analisador de capturas
│   └── testar_conexao_geduc.py                # Teste de conectividade
└── historico geduc/
    └── capturas/                              # Arquivos HAR salvos aqui
```

---

## 🎯 Etapas de Execução

### **Etapa 1: Testar Conectividade** ✅

Verifique se consegue acessar o GEDUC:

```bash
python scripts/testar_conexao_geduc.py
```

**Resultado esperado:**
```
RESULTADO: ✓ Conexão bem-sucedida
```

---

### **Etapa 2: Capturar Requisições HTTP** 🔍

#### 2.1. Preparação

1. Abrir Chrome/Firefox
2. Pressionar **F12** para abrir DevTools
3. Ir para aba **Network** (Rede)
4. ✅ Marcar **"Preserve log"** (Preservar log)
5. ✅ Limpar requisições anteriores (ícone 🚫)

#### 2.2. Captura do Login

1. Acessar: https://semed.geduc.com.br
2. **Fazer login** com suas credenciais
3. Na aba Network, localizar a requisição POST do login
4. Botão direito → **Copy** → **Copy as cURL**
5. Salvar em arquivo de texto

#### 2.3. Captura do Cadastro de Notas

1. Navegar até: **Alunos → Histórico Escolar → Cadastro de Notas**
2. Preencher formulário com **dados de teste**
3. Clicar em **Salvar**
4. Na aba Network, localizar requisição para `DisciplinasHistorico`
5. Botão direito → **Save all as HAR with content**
6. Salvar em: `c:\gestao\historico geduc\capturas\geduc_captura.har`

#### 2.4. Informações Críticas a Observar

✅ **Nome do cookie de sessão** (geralmente PHPSESSID)  
✅ **Presença de token CSRF** (no form ou header)  
✅ **Estrutura dos arrays** (IDDISCIPLINAS[], CHT[], etc.)  
✅ **Headers obrigatórios** (Referer, Origin, etc.)  
✅ **Formato da resposta** (JSON, HTML, redirect?)

---

### **Etapa 3: Analisar Captura** 📊

Execute o analisador de HAR:

```bash
python scripts/analisador_har.py "historico geduc/capturas/geduc_captura.har"
```

**O que o script faz:**
- Lista todas as requisições POST
- Identifica cookies de sessão
- Detecta tokens CSRF
- Extrai estrutura de payloads
- Gera exemplos de cURL

**Resultado:**
- Relatório completo no terminal
- Informações prontas para documentar

---

### **Etapa 4: Documentar Descobertas** 📝

1. Abrir template:
   ```
   c:\gestao\docs\TEMPLATE_REQUISICOES_CAPTURADAS.md
   ```

2. Preencher com informações da análise:
   - URLs exatas
   - Headers obrigatórios
   - Estrutura do payload
   - Exemplos de resposta
   - Presença/ausência de CSRF

3. Salvar como:
   ```
   c:\gestao\docs\RESULTADO_CAPTURA_GEDUC.md
   ```

---

### **Etapa 5: Atualizar Script POC** 🔧

Com base nas descobertas, editar:

```
c:\gestao\scripts\poc_exportacao_geduc.py
```

**Modificações necessárias:**

1. **Método `fazer_login()`:**
   ```python
   # Atualizar estrutura do POST de login
   login_data = {
       'campo_usuario': usuario,  # Nome real do campo
       'campo_senha': senha,      # Nome real do campo
       # Adicionar outros campos descobertos
   }
   ```

2. **CSRF Token:**
   ```python
   # Se token CSRF for necessário
   if self.csrf_token:
       login_data['nome_do_token_csrf'] = self.csrf_token
   ```

3. **Método `enviar_historico()`:**
   ```python
   # Ajustar headers conforme captura
   headers = {
       'Content-Type': 'application/x-www-form-urlencoded',
       'Referer': '...',  # Valor exato capturado
       # Adicionar headers obrigatórios
   }
   ```

---

### **Etapa 6: Configurar Credenciais** 🔐

**Opção 1: Variáveis de Ambiente (Recomendado)**

```powershell
$env:GEDUC_USER = "seu_usuario"
$env:GEDUC_PASS = "sua_senha"
```

**Opção 2: Arquivo de Configuração**

Criar `c:\gestao\local_config.json`:
```json
{
    "geduc": {
        "usuario": "seu_usuario",
        "senha": "sua_senha"
    }
}
```

⚠️ **IMPORTANTE:** Nunca commitar credenciais no Git!

---

### **Etapa 7: Executar POC** 🚀

```bash
python scripts/poc_exportacao_geduc.py
```

**Testes executados:**
1. ✅ Conexão básica
2. ✅ Login
3. ✅ Envio de histórico

**Resultado esperado:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        POC - Exportação GEDUC                                ║
║                         Tarefa 1.3 - Fase 1                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

TESTE 1: Conexão Básica
✓ Conexão básica OK

TESTE 2: Login
✓ Login bem-sucedido

TESTE 3: Envio de Histórico
✓ Histórico enviado com sucesso

════════════════════════════════════════════════════════════════════════════════
RESUMO DOS TESTES
════════════════════════════════════════════════════════════════════════════════
Conexão Básica......................................... ✓ PASSOU
Login.................................................. ✓ PASSOU
Envio Histórico........................................ ✓ PASSOU
════════════════════════════════════════════════════════════════════════════════
Total: 3/3 testes passaram
🎉 Todos os testes passaram!
```

---

### **Etapa 8: Integração com Interface** 🖥️

Após POC validado, criar módulo final:

```
c:\gestao\src\exportadores\geduc_exportador.py
```

**Estrutura do módulo:**
```python
def exportar_historico_aluno(aluno_id: int) -> dict:
    """
    Exporta histórico escolar de um aluno para o GEDUC.
    
    Args:
        aluno_id: ID do aluno no sistema local
        
    Returns:
        {
            'sucesso': bool,
            'registros_enviados': int,
            'id_exportacao': str,
            'erro': str (se houver)
        }
    """
    # Implementação baseada no POC validado
    pass
```

O botão na interface já está configurado para chamar esta função!

---

## 🐛 Solução de Problemas

### Erro: "Falha na conexão"

**Causa:** Sem acesso à internet ou firewall bloqueando  
**Solução:** Verificar conectividade e configurações de proxy

### Erro: "Login falhou"

**Causa:** Credenciais incorretas ou estrutura de login mudou  
**Solução:** 
1. Validar credenciais no navegador
2. Recapturar requisição de login
3. Atualizar POC com nova estrutura

### Erro: "Resposta inesperada do servidor"

**Causa:** Estrutura da API mudou ou dados inválidos  
**Solução:**
1. Verificar logs detalhados
2. Recapturar requisição de envio
3. Comparar payload enviado vs. capturado

### Erro: "ImportError" ao executar interface

**Causa:** Módulo `geduc_exportador` ainda não criado  
**Solução:** 
1. Completar POC primeiro
2. Criar módulo em `src/exportadores/`
3. Implementar função `exportar_historico_aluno()`

---

## 📊 Checklist de Progresso

### Fase 1 - Análise e POC

- [x] Tarefa 1.1: Análise completa de formulários GEDUC
- [ ] **Tarefa 1.2: Capturar requisições HTTP**
  - [ ] Login capturado
  - [ ] Cadastro de notas capturado
  - [ ] Arquivo HAR salvo
  - [ ] Análise executada
  - [ ] Resultados documentados
- [ ] **Tarefa 1.3: Script POC funcional**
  - [ ] POC criado
  - [ ] Credenciais configuradas
  - [ ] Login validado
  - [ ] Envio de teste bem-sucedido
  - [ ] Todos os testes passando

### Fase 2 - Implementação (Futuro)

- [ ] Módulo `geduc_exportador.py` criado
- [ ] Integração com banco de dados local
- [ ] Mapeamento de dados (local → GEDUC)
- [ ] Tratamento de erros robusto
- [ ] Logging completo
- [ ] Testes unitários

### Fase 3 - Produção (Futuro)

- [ ] Validação com dados reais
- [ ] Interface de usuário finalizada
- [ ] Documentação completa
- [ ] Deploy em produção

---

## 📞 Referências

- **Documentação Completa:** [docs/FASE1_MAPEAMENTO_FORMULARIOS_GEDUC.md](docs/FASE1_MAPEAMENTO_FORMULARIOS_GEDUC.md)
- **Guia de Captura:** [docs/TAREFA_1.2_CAPTURA_REQUISICOES.md](docs/TAREFA_1.2_CAPTURA_REQUISICOES.md)
- **Template de Documentação:** [docs/TEMPLATE_REQUISICOES_CAPTURADAS.md](docs/TEMPLATE_REQUISICOES_CAPTURADAS.md)

---

## 🎓 Dicas Importantes

1. **Sempre teste com dados fictícios primeiro**
2. **Documente cada descoberta imediatamente**
3. **Salve os arquivos HAR - são evidências importantes**
4. **Não commite credenciais no Git**
5. **Faça backup antes de modificar código em produção**

---

**Última atualização:** 20/12/2025  
**Versão do guia:** 1.0  
**Status:** Em desenvolvimento - Fase 1
