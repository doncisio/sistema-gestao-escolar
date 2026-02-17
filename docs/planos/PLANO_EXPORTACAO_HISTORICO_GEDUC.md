# 📋 Plano de Ação: Exportação de Histórico Escolar para GEDUC

**Data de Criação:** 20/12/2025  
**Objetivo:** Exportar dados do histórico escolar do sistema local para o sistema online GEDUC

---

## 📊 1. ANÁLISE DA SITUAÇÃO ATUAL

### 1.1 Diretório "historico geduc"
O diretório contém arquivos HTML salvos do sistema GEDUC:
- `ficha do aluno.html` - Ficha individual do aluno
- `lista turmas.html` - Lista de turmas
- `login.html` - Página de login
- `turma_id.html` - Dados da turma específica
- Arquivos de recursos (CSS, JS) em subpastas

**Observação:** Estes arquivos são páginas estáticas salvas manualmente, indicando que atualmente há consultas manuais ao GEDUC.

### 1.2 Sistema Local - Estrutura de Dados
O sistema local possui estrutura completa de histórico escolar:

#### Tabela: `historico_escolar`
```sql
- id
- aluno_id
- disciplina_id
- serie_id
- ano_letivo_id
- escola_id
- media (decimal)
- conceito (varchar)
- carga_horaria
```

#### Dados Relacionados
- **Alunos:** id, nome, data_nascimento, sexo, local_nascimento, UF_nascimento, CPF, etc.
- **Disciplinas:** id, nome, carga_horaria
- **Séries:** id, nome
- **Anos Letivos:** id, ano_letivo
- **Escolas:** id, nome, INEP, CNPJ, endereço, município
- **Turmas:** id, nome, turno, serie_id, escola_id
- **Matrículas:** id, aluno_id, turma_id, ano_letivo_id, status

### 1.3 Sistema GEDUC - Capacidades Atuais
O sistema já possui integração parcial com GEDUC através do módulo `src/importadores/geduc.py`:

#### Funcionalidades Existentes (IMPORTAÇÃO):
✅ Login automatizado no GEDUC  
✅ Extração de notas de turmas  
✅ Extração de dados de alunos  
✅ Navegação automatizada por disciplinas e bimestres  
✅ Geração de planilhas Excel com dados extraídos  

#### Limitações Identificadas:
❌ Não há funcionalidade de **EXPORTAÇÃO** (apenas importação)  
❌ Não há envio de dados do sistema local para o GEDUC  
❌ Não há atualização automática de histórico escolar no GEDUC  

---

## 🎯 2. OBJETIVOS DO PROJETO

### 2.1 Objetivo Principal
Criar um sistema automatizado para exportar dados do histórico escolar do banco de dados local para o sistema GEDUC online.

### 2.2 Objetivos Específicos
1. Analisar a interface web do GEDUC para identificar formulários de entrada de dados
2. Desenvolver módulo de exportação de histórico escolar
3. Mapear campos do sistema local para campos do GEDUC
4. Implementar validações e tratamento de erros
5. Criar logs de auditoria das exportações
6. Desenvolver interface gráfica para gestão das exportações

---

## 🔍 3. ANÁLISE TÉCNICA NECESSÁRIA

### 3.1 Reconhecimento do Sistema GEDUC
**Ações necessárias:**

1. **Identificar URLs e Endpoints**
   - URL de cadastro/edição de histórico escolar
   - URL de listagem de alunos
   - URL de registro de notas/conceitos
   - Identificar se há API REST ou apenas interface web

2. **Mapear Formulários HTML**
   - Campos obrigatórios
   - Tipos de dados aceitos
   - Validações client-side
   - Estrutura de SELECTs (disciplinas, séries, etc.)

3. **Analisar Fluxo de Dados**
   - Como o GEDUC armazena histórico escolar
   - Se aceita importação em lote (batch)
   - Formatos de arquivo aceitos (CSV, Excel, XML, JSON)
   - Limite de registros por requisição

4. **Verificar Autenticação e Sessão**
   - Tokens CSRF
   - Cookies de sessão
   - Tempo de expiração da sessão
   - Necessidade de captcha

### 3.2 Mapeamento de Dados

| Campo Sistema Local | Campo GEDUC | Transformação Necessária | Prioridade |
|---------------------|-------------|--------------------------|------------|
| aluno.id | ID_ALUNO | Pode necessitar mapeamento | Alta |
| aluno.nome | NOME_ALUNO | Normalização de caracteres | Alta |
| disciplina.nome | IDTURMASDISP | Buscar ID correspondente | Alta |
| serie.nome | SERIE | Validar nomenclatura | Alta |
| ano_letivo.ano_letivo | ANO_LETIVO | Formato YYYY | Alta |
| historico.media | MEDIA/NOTA | Converter escala se necessário | Alta |
| historico.conceito | CONCEITO | Mapear conceitos (A,B,C,D,E) | Alta |
| escola.inep | ESCOLA_INEP | Chave de vinculação | Média |
| turma.nome | TURMA | Verificar padrão | Média |
| turma.turno | TURNO | Matutino/Vespertino/Noturno | Média |

---

## 📝 4. PLANO DE IMPLEMENTAÇÃO

### FASE 1: Reconhecimento e Prototipação (5-7 dias)

#### Tarefa 1.1: Análise Manual do GEDUC
- [ ] Fazer login manual no GEDUC
- [ ] Navegar até seção de histórico escolar
- [ ] Documentar URLs de todas as páginas relevantes
- [ ] Salvar HTML completo dos formulários de cadastro
- [ ] Identificar campos obrigatórios e opcionais
- [ ] Testar cadastro manual de um registro de histórico

**Entregável:** Documento `MAPEAMENTO_FORMULARIOS_GEDUC.md`

#### Tarefa 1.2: Captura de Requisições
- [ ] Usar DevTools do navegador (Network tab)
- [ ] Capturar requisições POST ao submeter formulário
- [ ] Documentar headers necessários
- [ ] Identificar formato dos payloads
- [ ] Verificar validações server-side

**Entregável:** Arquivo `requisicoes_geduc_exemplo.json`

#### Tarefa 1.3: Desenvolvimento de Script Proof-of-Concept
- [ ] Criar script Python isolado
- [ ] Testar login automatizado
- [ ] Testar preenchimento de 1 registro de histórico
- [ ] Validar sucesso da submissão
- [ ] Tratar erros básicos

**Entregável:** `scripts/poc_exportacao_geduc.py`

---

### FASE 2: Desenvolvimento do Módulo de Exportação (10-15 dias)

#### Tarefa 2.1: Criar Estrutura do Módulo
```python
src/exportadores/
├── __init__.py
├── geduc_exportador.py      # Classe principal
├── geduc_mapeador.py         # Mapeamento de dados
├── geduc_validador.py        # Validações
└── geduc_logger.py           # Logs de exportação
```

#### Tarefa 2.2: Implementar Classe `GEDUCExportador`

**Funcionalidades principais:**
```python
class GEDUCExportador:
    def __init__(self, credenciais):
        """Inicializa exportador com credenciais"""
        
    def conectar(self):
        """Estabelece conexão com GEDUC"""
        
    def exportar_historico_aluno(self, aluno_id):
        """Exporta histórico completo de um aluno"""
        
    def exportar_historico_turma(self, turma_id, ano_letivo_id):
        """Exporta histórico de todos alunos de uma turma"""
        
    def exportar_historico_escola(self, escola_id, ano_letivo_id):
        """Exporta histórico de toda escola em um ano"""
        
    def validar_dados_pre_exportacao(self, dados):
        """Valida dados antes de enviar"""
        
    def rollback_exportacao(self, exportacao_id):
        """Reverte exportação em caso de erro"""
        
    def gerar_relatorio_exportacao(self):
        """Gera relatório de exportação realizada"""
```

#### Tarefa 2.3: Implementar Mapeamento de Dados
```python
class GEDUCMapeador:
    def mapear_aluno(self, aluno_local):
        """Converte dados de aluno do formato local para GEDUC"""
        
    def mapear_disciplina(self, disciplina_local):
        """Mapeia disciplina local para ID no GEDUC"""
        
    def mapear_conceito(self, media):
        """Converte média numérica para conceito"""
        
    def validar_mapeamento(self):
        """Verifica integridade do mapeamento"""
```

#### Tarefa 2.4: Sistema de Validação
```python
class GEDUCValidador:
    def validar_aluno_existe_geduc(self, aluno_id):
        """Verifica se aluno está cadastrado no GEDUC"""
        
    def validar_disciplina_existe(self, disciplina_nome):
        """Verifica se disciplina existe no GEDUC"""
        
    def validar_conceito(self, conceito):
        """Valida formato do conceito"""
        
    def validar_carga_horaria(self, carga_horaria):
        """Valida carga horária"""
```

#### Tarefa 2.5: Sistema de Logs e Auditoria
```sql
CREATE TABLE exportacoes_geduc (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_exportacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_id INT,
    tipo_exportacao VARCHAR(50), -- 'aluno', 'turma', 'escola'
    registros_exportados INT,
    registros_sucesso INT,
    registros_erro INT,
    tempo_execucao INT, -- em segundos
    status VARCHAR(20), -- 'sucesso', 'parcial', 'erro'
    log_detalhes TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE exportacoes_geduc_detalhes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    exportacao_id INT,
    aluno_id INT,
    disciplina_id INT,
    ano_letivo_id INT,
    status VARCHAR(20),
    mensagem_erro TEXT,
    data_tentativa DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exportacao_id) REFERENCES exportacoes_geduc(id),
    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
);
```

---

### FASE 3: Interface Gráfica (5-7 dias)

#### Tarefa 3.1: Criar Interface de Exportação
**Arquivo:** `src/interfaces/exportacao_geduc.py`

**Componentes:**
- [ ] Seleção de escola
- [ ] Seleção de ano letivo
- [ ] Seleção de turma ou aluno individual
- [ ] Opções de exportação (completo/parcial)
- [ ] Preview dos dados a serem exportados
- [ ] Barra de progresso
- [ ] Log de operações em tempo real
- [ ] Botões: Exportar, Cancelar, Ver Relatório

#### Tarefa 3.2: Integração com Menu Principal
```python
# Em main.py ou interface principal
menu_exportacao = tk.Menu(menu_principal, tearoff=0)
menu_principal.add_cascade(label="GEDUC", menu=menu_exportacao)
menu_exportacao.add_command(
    label="Exportar Histórico Escolar",
    command=lambda: abrir_exportacao_geduc()
)
menu_exportacao.add_command(
    label="Relatórios de Exportação",
    command=lambda: abrir_relatorios_geduc()
)
```

---

### FASE 4: Testes e Homologação (7-10 dias)

#### Tarefa 4.1: Testes Unitários
- [ ] Testar mapeamento de dados
- [ ] Testar validações
- [ ] Testar tratamento de erros
- [ ] Testar rollback

#### Tarefa 4.2: Testes de Integração
- [ ] Testar exportação de 1 aluno
- [ ] Testar exportação de 1 turma (30-40 alunos)
- [ ] Testar exportação em lote
- [ ] Testar cancelamento de exportação

#### Tarefa 4.3: Testes de Carga
- [ ] Exportar 100 registros
- [ ] Exportar 500 registros
- [ ] Exportar 1000 registros
- [ ] Medir tempo de execução
- [ ] Verificar consumo de memória

#### Tarefa 4.4: Homologação em Ambiente de Produção
- [ ] Selecionar grupo piloto (1 turma pequena)
- [ ] Realizar exportação supervisionada
- [ ] Validar dados no GEDUC
- [ ] Corrigir inconsistências
- [ ] Obter aprovação dos usuários

---

### FASE 5: Documentação e Treinamento (3-5 dias)

#### Tarefa 5.1: Documentação Técnica
- [ ] Documentar arquitetura do módulo
- [ ] Documentar APIs e classes
- [ ] Criar diagrama de fluxo de dados
- [ ] Documentar mapeamentos de campos

#### Tarefa 5.2: Manual do Usuário
- [ ] Passo a passo para exportação
- [ ] Prints de tela
- [ ] Troubleshooting de erros comuns
- [ ] Perguntas frequentes (FAQ)

#### Tarefa 5.3: Treinamento
- [ ] Preparar apresentação
- [ ] Realizar treinamento presencial/online
- [ ] Gravar vídeo tutorial
- [ ] Criar material de apoio

---

## ⚠️ 5. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| GEDUC não possui API pública | Alta | Alto | Usar web scraping com Selenium (já implementado) |
| Mudanças na interface do GEDUC | Média | Alto | Versionamento do mapeamento, monitoramento de mudanças |
| Limite de requisições (rate limiting) | Média | Médio | Implementar delays entre requisições, exportação em lotes |
| Inconsistência de dados | Alta | Alto | Validações rigorosas pré-exportação, modo dry-run |
| Timeout de sessão | Média | Médio | Renovação automática de sessão, retry logic |
| Dados duplicados no GEDUC | Média | Alto | Verificar existência antes de inserir |
| Perda de conexão durante exportação | Baixa | Alto | Sistema de checkpoint, retomada de exportação |

---

## 🛠️ 6. TECNOLOGIAS E FERRAMENTAS

### Já Disponíveis no Projeto:
- **Selenium WebDriver** - Automação web
- **BeautifulSoup** - Parsing HTML
- **openpyxl** - Manipulação de Excel
- **MySQL/MariaDB** - Banco de dados
- **Tkinter** - Interface gráfica
- **logging** - Sistema de logs

### A Adicionar:
- **requests** - Requisições HTTP (se houver API)
- **pytest** - Testes automatizados
- **schedule** - Agendamento de tarefas (opcional)

---

## 📊 7. ESTIMATIVA DE ESFORÇO

| Fase | Dias Úteis | Horas | Complexidade |
|------|------------|-------|--------------|
| Fase 1: Reconhecimento | 5-7 | 40-56 | Alta |
| Fase 2: Desenvolvimento | 10-15 | 80-120 | Muito Alta |
| Fase 3: Interface | 5-7 | 40-56 | Média |
| Fase 4: Testes | 7-10 | 56-80 | Alta |
| Fase 5: Documentação | 3-5 | 24-40 | Baixa |
| **TOTAL** | **30-44** | **240-352** | - |

**Estimativa:** 6 a 9 semanas de desenvolvimento com 1 desenvolvedor full-time

---

## 🎯 8. CRITÉRIOS DE SUCESSO

### Critérios Funcionais:
✅ Exportar histórico de 1 aluno com 100% de precisão  
✅ Exportar histórico de 1 turma (40 alunos) em menos de 10 minutos  
✅ Taxa de sucesso superior a 95%  
✅ Detecção e tratamento de 100% dos erros conhecidos  
✅ Geração de relatórios de auditoria  

### Critérios Não-Funcionais:
✅ Interface intuitiva (sem necessidade de treinamento extenso)  
✅ Logs detalhados de todas as operações  
✅ Código documentado e testado  
✅ Manual do usuário completo  

---

## 📅 9. PRÓXIMOS PASSOS IMEDIATOS

### Semana 1:
1. **Obter credenciais de acesso ao GEDUC** (ambiente de testes se disponível)
2. **Exploração manual do GEDUC:**
   - Navegar por todas as telas de histórico escolar
   - Identificar onde são cadastrados/editados registros
   - Salvar HTML completo de formulários relevantes
   - Capturar requisições HTTP com DevTools

3. **Análise inicial dos dados locais:**
   - Quantificar registros de histórico a exportar
   - Identificar inconsistências nos dados locais
   - Listar disciplinas que podem não ter equivalente no GEDUC

### Semana 2:
4. **Desenvolver script POC:**
   - Login automatizado
   - Navegação até formulário de histórico
   - Preenchimento de 1 registro
   - Validação de sucesso

5. **Documentar achados:**
   - Criar documento de mapeamento de campos
   - Listar validações necessárias
   - Identificar limitações técnicas

---

## 📞 10. CONTATOS E RESPONSABILIDADES

| Papel | Responsabilidade | Contato |
|-------|------------------|---------|
| Desenvolvedor | Implementação técnica | - |
| Secretário(a) Escolar | Validação de dados, homologação | - |
| Suporte GEDUC | Esclarecimentos sobre sistema | - |
| Gestor TI | Aprovação e recursos | - |

---

## 📚 11. REFERÊNCIAS

### Documentação Interna:
- [src/importadores/geduc.py](../src/importadores/geduc.py) - Módulo atual de importação GEDUC
- [src/interfaces/historico_escolar.py](../src/interfaces/historico_escolar.py) - Interface de histórico local
- [src/relatorios/historico_escolar.py](../src/relatorios/historico_escolar.py) - Geração de PDF

### Arquivos de Referência:
- `historico geduc/` - Páginas salvas do GEDUC (base para análise)

### URLs (a preencher após reconhecimento):
- GEDUC Login: https://semed.geduc.com.br
- GEDUC Histórico: (a identificar)
- GEDUC API Docs: (a verificar se existe)

---

## 📋 CHECKLIST DE VALIDAÇÃO

Antes de iniciar o desenvolvimento, verificar:
- [ ] Acesso ao GEDUC confirmado
- [ ] Permissões de escrita no GEDUC obtidas
- [ ] Backup completo do banco de dados local realizado
- [ ] Ambiente de testes do GEDUC disponível (se existir)
- [ ] Aprovação da gestão para realizar o projeto
- [ ] Recursos (tempo, infraestrutura) alocados

---

**Última Atualização:** 20/12/2025  
**Versão do Documento:** 1.0  
**Status:** Aguardando início da Fase 1
