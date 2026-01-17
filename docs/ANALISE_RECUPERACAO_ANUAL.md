# Análise: Implementação da Recuperação Anual

**Data:** 17 de janeiro de 2026  
**Objetivo:** Analisar a estrutura do banco de dados e o fluxo de dados para implementar a funcionalidade de "Recuperação Anual" (notas finais).

---

## 📊 Estrutura Atual do Banco de Dados

### Tabela `notas`
```sql
CREATE TABLE `notas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ano_letivo_id` int NOT NULL,
  `aluno_id` int NOT NULL,
  `disciplina_id` int NOT NULL,
  `bimestre` enum('1º bimestre','2º bimestre','3º bimestre','4º bimestre'),
  `nota` decimal(4,1) NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `notas_chk_1` CHECK (((`nota` >= 0.0) and (`nota` <= 100.0)))
)
```

**Observação:** A tabela `notas` armazena apenas notas **bimestrais** (1º ao 4º bimestre). Não há campo para armazenar a "média final" ou "nota de recuperação anual".

### Tabela `historico_escolar`
```sql
CREATE TABLE `historico_escolar` (
  `id` int NOT NULL AUTO_INCREMENT,
  `aluno_id` int NOT NULL,
  `disciplina_id` int NOT NULL,
  `media` decimal(4,1) DEFAULT NULL,
  `ano_letivo_id` int NOT NULL,
  `escola_id` int NOT NULL,
  `conceito` varchar(5) DEFAULT NULL,
  `serie_id` int DEFAULT NULL,
  PRIMARY KEY (`id`)
)
```

**Observação:** Esta tabela armazena a **média final anual** de cada aluno por disciplina. É aqui que devem ser gravadas as médias finais após recuperação.

---

## 🔄 Fluxo Atual de Dados

### 1. Notas Bimestrais (Cadastro Regular)
- **Origem:** GEDUC → `RegNotasbimForm`
- **Destino:** Tabela `notas` (bimestre 1º a 4º)
- **Processo:** Extração via automação GEDUC

### 2. Recuperação Bimestral
- **Origem:** GEDUC → `RegNotasbimForm` (página de recuperação bimestral)
- **Destino:** Tabela `notas` (atualiza nota do bimestre)
- **Lógica:** Se `Recuperação >= Média Atual`, então `nota = Recuperação * 10`

### 3. Ata Geral (Cálculo de Médias Finais)
- **Origem:** Tabela `notas` (calcula média dos 4 bimestres)
- **Processo:**
  ```python
  # Exemplo da query SQL (ata_1a5ano.py)
  COALESCE(SUM(CASE WHEN d.nome = 'LÍNGUA PORTUGUESA' ... THEN n.nota END), 0) 
  / NULLIF(COUNT(CASE WHEN d.nome = 'LÍNGUA PORTUGUESA' ... THEN n.nota END), 0)
  ```
- **Arredondamento:** Usa `arredondar_personalizado()` do biblio_editor.py
- **Destino Final:** Tabela `historico_escolar`

**Função de inserção no histórico:**
```python
def inserir_no_historico_escolar(aluno_id, disciplina_id, media, 
                                  ano_letivo_id, escola_id, serie_id):
    # Insere ou atualiza a média final no historico_escolar
    cursor.execute("""
        INSERT INTO historico_escolar 
        (aluno_id, disciplina_id, media, ano_letivo_id, escola_id, serie_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (aluno_id, disciplina_id, media, ano_letivo_id, escola_id, serie_id))
```

---

## ⚙️ Função de Arredondamento

```python
def arredondar_personalizado(n):
    """
    Arredonda a nota e retorna multiplicada por 10 (formato inteiro)
    
    A nota no sistema está multiplicada por 10 (ex: 76.7 representa 7.67)
    
    Exemplos:
        81.6 / 10 = 8.16 -> 8.2 -> 82
        73.3 / 10 = 7.33 -> 7.3 -> 73
        76.7 / 10 = 7.67 -> 7.7 -> 77
        73.5 / 10 = 7.35 -> 7.4 -> 74
    
    Lógica:
    - fracao < 0.3125  -> arredonda para baixo (x.0)
    - 0.3125 <= fracao < 0.8125 -> arredonda para x.5
    - fracao >= 0.8125 -> arredonda para cima (x+1.0)
    """
    from decimal import Decimal
    
    nota_real = Decimal(str(n)) / Decimal('10')
    parte_inteira = int(nota_real // 1)
    fracao = nota_real - Decimal(parte_inteira)
    
    t1 = Decimal('0.3125')
    t2 = Decimal('0.8125')
    
    if fracao < t1:
        resultado = Decimal(parte_inteira)
    elif fracao < t2:
        resultado = Decimal(parte_inteira) + Decimal('0.5')
    else:
        resultado = Decimal(parte_inteira + 1)
    
    return int((resultado * Decimal('10')).to_integral_value())
```

---

## 🎯 Proposta de Implementação: Recuperação Anual

### Problema a Resolver

A página GEDUC `RegNotasFinaisForm` exibe:
- **Média Atual** (média dos 4 bimestres)
- **Recuperação Final** (nota da prova de recuperação anual)
- **Situação** (Aprovado/Reprovado)

**Desafio:** Não temos uma estrutura na tabela `notas` para armazenar a "recuperação final" ou a "média final pós-recuperação".

### Soluções Possíveis

#### **Opção 1: Criar Nova Tabela `notas_finais`** (RECOMENDADA)

```sql
CREATE TABLE `notas_finais` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ano_letivo_id` int NOT NULL,
  `aluno_id` int NOT NULL,
  `disciplina_id` int NOT NULL,
  `media_anual` decimal(4,1) NOT NULL COMMENT 'Média dos 4 bimestres',
  `nota_recuperacao_final` decimal(4,1) DEFAULT NULL COMMENT 'Nota da recuperação final',
  `media_final` decimal(4,1) NOT NULL COMMENT 'Média final (após recuperação se houver)',
  `data_atualizacao` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_aluno_disciplina_ano` (`aluno_id`,`disciplina_id`,`ano_letivo_id`),
  FOREIGN KEY (`aluno_id`) REFERENCES `alunos` (`id`),
  FOREIGN KEY (`disciplina_id`) REFERENCES `disciplinas` (`id`),
  FOREIGN KEY (`ano_letivo_id`) REFERENCES `anosletivos` (`id`),
  CONSTRAINT `notas_finais_chk_1` CHECK (((`media_anual` >= 0.0) and (`media_anual` <= 100.0))),
  CONSTRAINT `notas_finais_chk_2` CHECK (((`media_final` >= 0.0) and (`media_final` <= 100.0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

**Vantagens:**
- ✅ Separação clara entre notas bimestrais e notas finais
- ✅ Mantém histórico de recuperação final
- ✅ Facilita consultas e relatórios
- ✅ Permite rastreamento de mudanças com `data_atualizacao`

#### **Opção 2: Adicionar Coluna na Tabela `notas`** (NÃO RECOMENDADA)

Adicionar um valor especial para bimestre (ex: "Recuperação Final"):

```sql
ALTER TABLE notas 
MODIFY COLUMN bimestre enum('1º bimestre','2º bimestre','3º bimestre','4º bimestre','Recuperação Final');
```

**Desvantagens:**
- ❌ Mistura conceitos diferentes (bimestre x anual)
- ❌ Dificulta queries e relatórios
- ❌ Pode causar confusão no sistema

#### **Opção 3: Usar Apenas `historico_escolar`** (SIMPLICIDADE)

Calcular a média final em tempo real e gravar diretamente no `historico_escolar`:

**Vantagens:**
- ✅ Não requer nova estrutura
- ✅ Sistema já está preparado para usar esta tabela

**Desvantagens:**
- ❌ Perde informação sobre a nota de recuperação final
- ❌ Não permite auditoria de quem fez recuperação
- ❌ Dificulta reprocessamento

---

## 📝 Recomendação Final

### **Implementar Opção 1: Nova Tabela `notas_finais`**

**Motivos:**
1. **Rastreabilidade**: Mantém registro de quem fez recuperação final
2. **Separação de conceitos**: Notas bimestrais ≠ Notas finais
3. **Flexibilidade**: Permite futuras expansões (ex: conceitos, observações)
4. **Auditoria**: Histórico completo de mudanças

### Fluxo de Dados Proposto

```
1. Extração do GEDUC (RegNotasFinaisForm)
   ↓
2. Para cada aluno/disciplina:
   - Extrair: Média Atual, Recuperação Final, Situação
   ↓
3. Calcular média final:
   - Se Recuperação Final existe E Recuperação >= Média Atual:
     * media_final = Recuperação Final * 10
   - Senão:
     * media_final = Média Atual * 10
   ↓
4. Salvar em notas_finais:
   - media_anual = Média Atual * 10
   - nota_recuperacao_final = Recuperação Final * 10 (se existir)
   - media_final = valor calculado
```

### Alterações Necessárias

1. **Criar migration:**
   ```sql
   -- migrations/criar_tabela_notas_finais.sql
   ```

2. **Criar função de extração no AutomacaoGEDUC:**
   ```python
   def extrair_notas_finais_pagina_atual(self):
       """Extrai notas finais da página RegNotasFinaisForm"""
   ```

3. **Criar função de processamento:**
   ```python
   def processar_recuperacao_anual(self):
       """Similar a processar_recuperacao_bimestral"""
   ```

4. **Atualizar Ata Geral:**
   - Consultar `notas_finais` em vez de calcular média manualmente
   - Usar `media_final` diretamente

5. **Adicionar opção no menu:**
   ```python
   menu_geduc.add_command(
       label="📊 Recuperação Anual (Notas Finais)",
       command=self.processar_recuperacao_anual
   )
   ```

---

## 🧪 Testes Necessários

1. ✅ Criar tabela `notas_finais` no ambiente de desenvolvimento
2. ✅ Testar extração de notas do GEDUC (RegNotasFinaisForm)
3. ✅ Validar cálculo de média final com arredondamento
4. ✅ Verificar inserção/atualização em `notas_finais`
5. ✅ Confirmar atualização automática em `historico_escolar`
6. ✅ Testar geração de Ata Geral com novas médias
7. ✅ Validar situação (Aprovado/Reprovado)

---

## ⚠️ Considerações Importantes

### Situação do GEDUC
A coluna "Situação" na página `RegNotasFinaisForm` pode ter valores como:
- Aprovado
- Reprovado
- Em Recuperação
- Aprovado pelo Conselho (?)
- Outros (?)

**Ação:** Verificar todos os valores possíveis durante a extração.

### Arredondamento
- Usar a mesma função `arredondar_personalizado()` para consistência
- Notas sempre multiplicadas por 10 no sistema

### Sincronização
- A Ata Geral deve usar `notas_finais.media_final` quando disponível
- Se `notas_finais` não existir para um aluno, calcular a média dos bimestres (fallback)

### Backup
- Fazer backup do banco antes de aplicar a migration
- Testar em ambiente de desenvolvimento primeiro

---

## 📋 Checklist de Implementação

- [ ] Criar migration `criar_tabela_notas_finais.sql`
- [ ] Aplicar migration no banco de desenvolvimento
- [ ] Implementar `AutomacaoGEDUC.acessar_notas_finais()`
- [ ] Implementar `AutomacaoGEDUC.extrair_notas_finais_pagina_atual()`
- [ ] Criar `CadastroNotas.processar_recuperacao_anual()`
- [ ] Criar função auxiliar `_salvar_notas_finais_banco()`
- [ ] Atualizar Ata Geral para consultar `notas_finais`
- [ ] Adicionar opção no menu GEDUC
- [ ] Testar fluxo completo
- [ ] Documentar processo
- [ ] Aplicar em produção

---

## 📚 Arquivos Envolvidos

- `src/importadores/geduc.py` - Automação GEDUC
- `src/interfaces/cadastro_notas.py` - Interface de cadastro de notas
- `src/relatorios/atas/ata_1a5ano.py` - Ata geral anos iniciais
- `src/relatorios/atas/ata_6a9ano.py` - Ata geral anos finais
- `src/relatorios/atas/ata_1a9ano.py` - Ata geral completa
- `scripts/migracao/inserir_no_historico_escolar.py` - Inserção no histórico
- `scripts/auxiliares/biblio_editor.py` - Funções de arredondamento
- `migrations/` - Nova migration para tabela `notas_finais`

---

**Conclusão:** A implementação da Recuperação Anual requer a criação de uma nova tabela `notas_finais` para armazenar adequadamente as médias finais e notas de recuperação anual. O fluxo de dados deve seguir o padrão já estabelecido para recuperação bimestral, com adaptações para trabalhar com médias anuais em vez de bimestrais.
