# Análise de Importação de Dados do GEDUC para o Sistema Local

**Data:** 08 de fevereiro de 2026  
**Objetivo:** Analisar os dados disponíveis nos arquivos HTML do GEDUC e mapear para a estrutura do banco de dados local

## 📋 1. ARQUIVOS ANALISADOS

### 1.1 Arquivo TurmaList.html
- **Localização:** `C:\gestao\cadastros\TurmaList.html`
- **Tipo:** Lista de turmas do GEDUC
- **Status:** Arquivo muito grande, necessita extração específica dos dados

### 1.2 Arquivo AlunoForm.html
- **Localização:** `C:\gestao\cadastros\AlunoForm.html`
- **Tipo:** Formulário detalhado de cadastro do aluno
- **Status:** Analisado com sucesso

---

## 📊 2. CAMPOS DISPONÍVEIS NO GEDUC (AlunoForm.html)

### 2.1 IDENTIFICAÇÃO BÁSICA
| Campo GEDUC | Tipo | Obrigatório | Descrição |
|-------------|------|-------------|-----------|
| `FOTO` | File | Não | Foto do aluno |
| `NOME` | Text | Sim | Nome completo do aluno |
| `DT_NASCIMENTO` | Date | Sim | Data de nascimento (formato: dd/mm/aaaa) |
| `SEXO` | Radio | Sim | 1=Masculino, 2=Feminino |
| `CPF` | Text | Não | CPF do aluno (11 dígitos) |
| `CODIGOINEP` | Text | Não | Código INEP do aluno |
| `INEPESCOLA` | Text | Não | Código INEP da escola |

### 2.2 FILIAÇÃO E RESPONSÁVEIS
| Campo GEDUC | Tipo | Obrigatório | Descrição |
|-------------|------|-------------|-----------|
| `RESPONSAVEL` | Radio | Sim | 0=Mãe, 1=Pai, 2=Outros, 3=Aluno |
| **Dados da Mãe:** ||||
| `FILIACAO_MAE` | Text | Não | Nome da mãe |
| `PROFISSAO_MAE` | Text | Não | Profissão da mãe |
| `CPFMAE` | Text | Não | CPF da mãe (11 dígitos) |
| `NASCIMENTOMAE` | Date | Não | Data nascimento da mãe |
| **Dados do Pai:** ||||
| `FILIACAO_PAI` | Text | Não | Nome do pai |
| `PROFISSAO_PAI` | Text | Não | Profissão do pai |
| `CPFPAI` | Text | Não | CPF do pai (11 dígitos) |
| `NASCIMENTOPAI` | Date | Não | Data nascimento do pai |
| **Outros Responsáveis:** ||||
| `OUTROS_NOME` | Text | Não | Nome do outro responsável |
| `OUTROS_PROFISSAO` | Text | Não | Profissão |
| `OUTROS_CPF` | Text | Não | CPF |
| `OUTROS_NASCIMENTO` | Date | Não | Data nascimento |
| `EMAIL_RESP` | Text | Não | E-mail do responsável |
| `CELULAR` | Text | Sim | Telefone celular |
| `FONE_COM` | Text | Não | Telefone comercial |

### 2.3 DADOS RACIAIS/ÉTNICOS
| Campo GEDUC | Tipo | Obrigatório | Descrição |
|-------------|------|-------------|-----------|
| `COR` | Radio | Sim | 0=Não declarada, 1=Branca, 2=Preta, 3=Parda, 4=Amarela, 5=Indígena |
| `IDPOVO_INDIGENA` | Select | Condicional | ID do povo indígena (se COR=5) |
| `NACIONALIDADE` | Radio | Sim | Brasileira/Brasileiro-exterior/Estrangeira |
| `PAISORIGEM` | Select | Condicional | País de origem (se estrangeiro) |

### 2.4 NATURALIDADE
| Campo GEDUC | Tipo | Obrigatório | Descrição |
|-------------|------|-------------|-----------|
| `ESTADO` | Select | Sim | Estado de nascimento |
| `NATURALIDADE` | Select | Sim | Município de nascimento (código IBGE) |

### 2.5 ALIMENTAÇÃO E SAÚDE
| Campo GEDUC | Tipo | Obrigatório | Descrição |
|-------------|------|-------------|-----------|
| `RESTRICAOALIMENTAR` | Radio | Sim | 0=Não, 1=Sim |
| `ALTURA` | Text | Não | Altura em cm (3 dígitos) |
| `PESO_CORPORAL` | Text | Não | Peso em kg (3 dígitos) |
| `TAMANHO_CALCADO` | Select | Não | Tamanho do calçado |

### 2.6 EDUCAÇÃO ESPECIAL
| Campo GEDUC | Tipo | Obrigatório | Descrição |
|-------------|------|-------------|-----------|
| `LOCAL_ATENDIMENTO` | Radio | Sim | 1=Não recebe, 2=Em Hospital, 3=Em Domicílio |
| `POSSDEFICIENCIA` | Radio | Sim | 0=Não, 1=Sim, 2=Em Avaliação |
| `CID` | Text | Condicional | Código CID (se possui deficiência) |
| `LAUDO` | File | Condicional | Arquivo do laudo médico |
| **Tipos de Deficiência:** | Checkbox[] | Condicional | |
| - CEGUEIRA | | | Valor: 1 |
| - BAIXA VISÃO | | | Valor: 2 |
| - SURDEZ | | | Valor: 3 |
| - DEFICIÊNCIA AUDITIVA | | | Valor: 4 |
| - DEFICIÊNCIA INTELECTUAL | | | Valor: 5 |
| - DEFICIÊNCIA FÍSICA | | | Valor: 6 |
| - DEFICIÊNCIA MULTIPLA | | | Valor: 7 |
| - SURDOCEGUEIRA | | | Valor: 8 |
| - OUTROS | | | Valor: 9 |
| - VISÃO MONOCULAR | | | Valor: 10 |
| `TGD` | Select | Não | Transtorno Global do Desenvolvimento |
| `ALTHAB` | Radio | Não | Altas Habilidades: 0=Não, 1=Sim |

### 2.7 TRANSTORNOS DE APRENDIZAGEM
| Campo GEDUC | Tipo | Descrição |
|-------------|------|-----------|
| `TGDEDU[]` | Checkbox[] | Transtornos: |
| - TDAH | | Valor: 1 |
| - Dislexia | | Valor: 2 |
| - Disgrafia/Disortografia | | Valor: 3 |
| - Dislalia | | Valor: 4 |
| - Discalculia | | Valor: 5 |
| - TPAC | | Valor: 6 |
| - Nenhuma Opção | | Valor: 7 |

### 2.8 DOCUMENTAÇÃO (ABA ESPECÍFICA)
*Dados disponíveis mas não completamente visíveis no HTML analisado*

### 2.9 ENDEREÇO (ABA ESPECÍFICA)
*Dados disponíveis mas não completamente visíveis no HTML analisado*

### 2.10 ANEXOS (ABA ESPECÍFICA)
*Permite anexar documentos diversos*

---

## 🗄️ 3. ESTRUTURA DO BANCO DE DADOS LOCAL

### 3.1 Tabela `alunos` (Principal)

Baseado na análise do código do sistema local, a estrutura é:

```sql
CREATE TABLE alunos (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    
    -- Identificação Básica
    nome VARCHAR(200) NOT NULL,
    data_nascimento DATE NOT NULL,
    sexo ENUM('M', 'F') NOT NULL,
    local_nascimento VARCHAR(100),
    UF_nascimento CHAR(2),
    
    -- Documentação
    cpf VARCHAR(11),
    nis VARCHAR(20),
    sus VARCHAR(20),  -- Cartão SUS
    rg VARCHAR(20),
    
    -- Filiação
    mae VARCHAR(200),
    pai VARCHAR(200),
    
    -- Endereço
    endereco TEXT,
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado CHAR(2),
    cep VARCHAR(9),
    
    -- Informações Adicionais
    raca VARCHAR(50),
    descricao_transtorno TEXT,
    
    -- Vínculo Institucional
    escola_id INT,
    
    -- Timestamps
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Chaves estrangeiras
    FOREIGN KEY (escola_id) REFERENCES escolas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 3.2 Tabela `responsaveis` (Relacionada)

```sql
CREATE TABLE responsaveis (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(200),
    telefone VARCHAR(20),
    rg VARCHAR(20),
    cpf VARCHAR(11),
    grau_parentesco VARCHAR(50)
) ENGINE=InnoDB;
```

### 3.3 Tabela `responsaveisalunos` (Relacionamento N:N)

```sql
CREATE TABLE responsaveisalunos (
    responsavel_id INT,
    aluno_id BIGINT UNSIGNED,
    FOREIGN KEY (responsavel_id) REFERENCES responsaveis(id),
    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
) ENGINE=InnoDB;
```

### 3.4 Tabela `matriculas` (Vínculo com Turmas)

```sql
CREATE TABLE matriculas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id BIGINT UNSIGNED,
    turma_id INT,
    ano_letivo_id INT,
    status ENUM('Ativo', 'Inativo', 'Transferido', 'Concluído'),
    data_matricula DATE,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id),
    FOREIGN KEY (turma_id) REFERENCES turmas(id),
    FOREIGN KEY (ano_letivo_id) REFERENCES anosletivos(id)
) ENGINE=InnoDB;
```

---

## 🔄 4. MAPEAMENTO GEDUC → SISTEMA LOCAL

### 4.1 Mapeamento Direto

| Campo GEDUC | Campo Local | Transformação |
|-------------|-------------|---------------|
| `NOME` | `alunos.nome` | Direto |
| `DT_NASCIMENTO` | `alunos.data_nascimento` | Converter dd/mm/aaaa → aaaa-mm-dd |
| `SEXO` | `alunos.sexo` | 1→'M', 2→'F' |
| `CPF` | `alunos.cpf` | Direto (validar 11 dígitos) |
| `FILIACAO_MAE` | `alunos.mae` | Direto |
| `FILIACAO_PAI` | `alunos.pai` | Direto |
| `NATURALIDADE` | `alunos.local_nascimento` | Buscar nome do município pelo código IBGE |
| `ESTADO` | `alunos.UF_nascimento` | Buscar sigla UF pelo código |
| `CELULAR` | `responsaveis.telefone` | Criar registro responsável |

### 4.2 Campos que Precisam de Tratamento Especial

#### 4.2.1 Cor/Raça
- **GEDUC:** Radio button com 6 opções (0-5)
- **Local:** Campo `alunos.raca` (VARCHAR)
- **Transformação necessária:**
  ```python
  mapa_raca = {
      '0': 'Não declarada',
      '1': 'Branca',
      '2': 'Preta',
      '3': 'Parda',
      '4': 'Amarela',
      '5': 'Indígena'
  }
  ```

#### 4.2.2 Responsáveis
- **GEDUC:** Tem campos separados para Mãe, Pai e Outros
- **Local:** Tabela `responsaveis` + `responsaveisalunos`
- **Transformação:**
  1. Criar registro em `responsaveis` para cada responsável informado
  2. Vincular na tabela `responsaveisalunos`
  3. Usar campo `RESPONSAVEL` (radio) para definir o responsável principal

#### 4.2.3 Deficiências e Transtornos
- **GEDUC:** Múltiplos checkboxes e campos específicos
- **Local:** Campo `alunos.descricao_transtorno` (TEXT)
- **Transformação:**
  1. Concatenar todas as deficiências selecionadas
  2. Incluir CID se informado
  3. Adicionar transtornos de aprendizagem
  
  Exemplo de saída:
  ```
  Deficiências: BAIXA VISÃO, DEFICIÊNCIA AUDITIVA
  CID: H54.0
  Transtornos: TDAH, Dislexia
  Laudo: [anexo]
  ```

#### 4.2.4 Escola
- **GEDUC:** Campo `INEPESCOLA` com código INEP
- **Local:** Campo `alunos.escola_id` (INT)
- **Transformação:**
  1. Buscar na tabela `escolas` pelo código INEP
  2. Se não existir, precisa criar ou usar escola padrão

---

## 📝 5. CAMPOS DO GEDUC NÃO MAPEADOS NO SISTEMA LOCAL

### 5.1 Dados que Serão PERDIDOS na Importação

| Campo GEDUC | Motivo |
|-------------|--------|
| `CODIGOINEP` | Não há campo correspondente em `alunos` |
| `EMAIL_RESP` | Não há campo em `responsaveis` |
| `PROFISSAO_MAE` | Não há campo em `alunos` ou `responsaveis` |
| `PROFISSAO_PAI` | Não há campo em `alunos` ou `responsaveis` |
| `CPFMAE` | Poderia ir para `responsaveis.cpf` |
| `CPFPAI` | Poderia ir para `responsaveis.cpf` |
| `NASCIMENTOMAE` | Não há campo |
| `NASCIMENTOPAI` | Não há campo |
| `RESTRICAOALIMENTAR` | Não há campo |
| `ALTURA` | Não há campo |
| `PESO_CORPORAL` | Não há campo |
| `TAMANHO_CALCADO` | Não há campo |
| `LOCAL_ATENDIMENTO` | Não há campo |
| `ALTHAB` (Altas Habilidades) | Não há campo específico |
| `AUXILIOAVALIACOES[]` | Não há campo |
| `IDPOVO_INDIGENA` | Não há campo |
| `PAISORIGEM` | Não há campo |

### 5.2 Sugestão de Melhorias no BD Local

Para importar TODOS os dados do GEDUC, seria necessário:

1. **Estender tabela `alunos`:**
```sql
ALTER TABLE alunos ADD COLUMN (
    codigo_inep VARCHAR(20),
    restricao_alimentar BOOLEAN,
    altura INT,
    peso INT,
    tamanho_calcado VARCHAR(5),
    local_atendimento ENUM('Escola', 'Hospital', 'Domicilio'),
    altas_habilidades BOOLEAN,
    pais_origem VARCHAR(100),
    povo_indigena VARCHAR(100)
);
```

2. **Estender tabela `responsaveis`:**
```sql
ALTER TABLE responsaveis ADD COLUMN (
    email VARCHAR(100),
    profissao VARCHAR(100),
    data_nascimento DATE
);
```

---

## 🔧 6. CAMPOS DO SISTEMA LOCAL SEM CORRESPONDÊNCIA NO GEDUC

| Campo Local | Solução |
|-------------|---------|
| `alunos.nis` | Deixar NULL ou buscar outro lugar |
| `alunos.rg` | Deixar NULL inicialmente |
| `alunos.endereco` | Ver aba ENDEREÇO do GEDUC |
| `alunos.bairro` | Ver aba ENDEREÇO do GEDUC |
| `alunos.cidade` | Pode usar NATURALIDADE temporariamente |
| `alunos.cep` | Ver aba ENDEREÇO do GEDUC |
| `responsaveis.rg` | Deixar NULL |

---

## 📋 7. DADOS NECESSÁRIOS PARA IMPORTAÇÃO COMPLETA

### 7.1 Dados Mínimos (Obrigatórios)

Para criar um aluno no sistema local, **PRECISAMOS OBRIGATORIAMENTE**:

✅ **Do GEDUC:**
- `NOME` → `alunos.nome`
- `DT_NASCIMENTO` → `alunos.data_nascimento`
- `SEXO` → `alunos.sexo`
- `FILIACAO_MAE` → `alunos.mae`

✅ **Informação adicional necessária (não vem do GEDUC):**
- `escola_id` → Precisa definir/mapear

### 7.2 Dados Complementares Importantes

🔶 **Altamente Recomendados:**
- `CPF`
- `CELULAR` (para criar responsável)
- `NATURALIDADE` + `ESTADO`
- `COR` (raça)
- Dados de responsáveis

🔶 **Opcionais mas úteis:**
- Foto do aluno
- Dados de deficiências
- Endereço completo

---

## 🎯 8. ESTRATÉGIA DE IMPORTAÇÃO RECOMENDADA

### Fase 1: Análise dos HTMLs
1. ✅ Extrair lista de alunos do `TurmaList.html`
2. ✅ Para cada aluno, extrair dados detalhados do `AlunoForm.html`
3. ⚠️ Necessário desenvolver parser HTML (BeautifulSoup ou similar)

### Fase 2: Validação dos Dados
1. Validar CPF (formato e unicidade)
2. Validar data de nascimento
3. Validar campos obrigatórios
4. Mapear escola (por código INEP ou nome)

### Fase 3: Importação Incremental
1. **Importar alunos básicos:**
   - Apenas campos obrigatórios
   - Criar registros em `alunos`
   
2. **Importar responsáveis:**
   - Criar em `responsaveis`
   - Vincular em `responsaveisalunos`
   
3. **Importar dados complementares:**
   - Deficiências (campo `descricao_transtorno`)
   - Endereço (se disponível)
   
4. **Importar matrículas:**
   - Vincular com turmas existentes
   - Criar registros em `matriculas`

### Fase 4: Tratamento de Conflitos
- Verificar alunos duplicados (por CPF ou nome+data nascimento)
- Atualizar dados existentes ou criar novos
- Log de erros e avisos

---

## 💻 9. ESTRUTURA DO SCRIPT DE IMPORTAÇÃO

```python
class ImportadorGEDUC:
    def __init__(self):
        self.connection = conectar_bd()
        self.erros = []
        self.avisos = []
        self.importados = 0
        
    def extrair_dados_html(self, arquivo_html):
        """Extrai dados do HTML usando BeautifulSoup"""
        pass
        
    def validar_dados(self, dados):
        """Valida campos obrigatórios e formatos"""
        pass
        
    def mapear_escola(self, codigo_inep):
        """Encontra escola_id pelo código INEP"""
        pass
        
    def importar_aluno(self, dados_geduc):
        """Importa um aluno completo"""
        # 1. Validar
        # 2. Criar aluno
        # 3. Criar responsáveis
        # 4. Vincular responsáveis
        # 5. Criar matrícula (se houver turma)
        pass
        
    def gerar_relatorio(self):
        """Gera relatório da importação"""
        pass
```

---

## ⚠️ 10. PONTOS DE ATENÇÃO

### 10.1 Dados Sensíveis
- CPFs devem ser validados e únicos
- Laudos médicos são arquivos anexos (precisam ser salvos)
- Fotos dos alunos precisam tratamento especial

### 10.2 Integridade Referencial
- Verificar se escola existe antes de importar
- Verificar se turma existe para criar matrícula
- Verificar ano letivo ativo

### 10.3 Performance
- Importação em lote (transações)
- Progress bar para acompanhamento
- Log detalhado de erros

### 10.4 Dados Incompletos
- Definir valores padrão para campos não obrigatórios
- Permitir importação parcial com avisos
- Possibilitar complementação manual posterior

---

## 📊 11. PRÓXIMOS PASSOS

### 11.1 Desenvolvimento Técnico
1. ⬜ Criar parser para TurmaList.html (extrair lista de alunos)
2. ⬜ Criar parser para AlunoForm.html (extrair dados detalhados)
3. ⬜ Implementar validações de dados
4. ⬜ Implementar mapeamento GEDUC → Local
5. ⬜ Criar interface de importação
6. ⬜ Implementar logs e relatórios

### 11.2 Melhorias no Banco de Dados
1. ⬜ Avaliar adicionar campos do GEDUC ao BD local
2. ⬜ Criar tabela de histórico de importações
3. ⬜ Adicionar campos de metadados (origem, data importação)

### 11.3 Testes
1. ⬜ Testar com amostra pequena de alunos
2. ⬜ Validar dados importados
3. ⬜ Testar rollback em caso de erro
4. ⬜ Validar integridade referencial

---

## 📞 12. DÚVIDAS PARA O USUÁRIO

Antes de prosseguir com a implementação, precisamos definir:

1. **Dados opcionais do GEDUC:**
   - Deseja importar dados de saúde (altura, peso, calçado)?
   - Deseja importar dados de profissão dos pais?
   - Deseja salvar fotos e laudos médicos?

2. **Estrutura do banco:**
   - Aceita estender tabelas `alunos` e `responsaveis` com novos campos?
   - Ou prefere importar apenas dados que já têm campos correspondentes?

3. **Tratamento de conflitos:**
   - Como tratar alunos duplicados? (Atualizar ou ignorar?)
   - Como definir a escola padrão se não encontrar por código INEP?

4. **Acesso aos dados:**
   - Os arquivos HTML já estão todos salvos localmente?
   - Ou precisa desenvolver scraper para baixar do GEDUC?

5. **Modo de importação:**
   - Importação única (migração) ou sincronização periódica?
   - Necessita manter vínculo com GEDUC para atualizações futuras?

---

**Documento gerado em:** 08/02/2026  
**Próxima ação:** Aguardando definições do usuário para prosseguir com desenvolvimento
