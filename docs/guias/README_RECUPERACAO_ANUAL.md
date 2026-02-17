# Recuperação Anual (Notas Finais) - Guia de Uso

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação](#instalação)
3. [Como Usar](#como-usar)
4. [Estrutura de Dados](#estrutura-de-dados)
5. [Processo de Cálculo](#processo-de-cálculo)
6. [Solução de Problemas](#solução-de-problemas)

---

## 🎯 Visão Geral

A funcionalidade de **Recuperação Anual** permite importar as médias finais e notas de recuperação anual do GEDUC para o sistema local.

### O que faz:

- ✅ Extrai médias anuais de todas as turmas do GEDUC
- ✅ Extrai notas de recuperação final
- ✅ Calcula e armazena a média final (considerando recuperação)
- ✅ Armazena dados na tabela notas_finais
- ✅ Prepara dados para geração da Ata Geral

### Diferenças da Recuperação Bimestral:

| Aspecto | Recuperação Bimestral | Recuperação Anual |
|---------|----------------------|-------------------|
| **Origem** | RegNotasbimForm | RegNotasFinaisForm |
| **Dados** | Nota de recuperação por bimestre | Média anual + recuperação final |
| **Armazenamento** | Tabela `notas` | Tabela `notas_finais` |
| **Atualização** | Substitui nota do bimestre | Cria registro de média final |

---

## 🔧 Instalação

### Passo 1: Aplicar Migration

Antes de usar a funcionalidade pela primeira vez, é necessário criar a tabela `notas_finais` no banco de dados.

**Opção A - Via Script Python:**

```bash
python scripts/aplicar_migration_notas_finais.py
```

**Opção B - Via MySQL diretamente:**

```bash
mysql -u usuario -p nome_banco < migrations/criar_tabela_notas_finais.sql
```

### Passo 2: Verificar Instalação

Verifique se a tabela foi criada com sucesso:

```sql
DESCRIBE notas_finais;
```

Você deve ver as seguintes colunas:
- `id`
- `ano_letivo_id`
- `aluno_id`
- `disciplina_id`
- `media_anual`
- `nota_recuperacao_final`
- `media_final`
- `data_atualizacao`

---

## 📖 Como Usar

### 1. Acessar o Menu

No sistema, vá para:

```
Cadastro de Notas → Menu GEDUC → 📊 Recuperação Anual (Notas Finais)
```

### 2. Inserir Credenciais

Quando solicitado, forneça:
- **Usuário GEDUC**
- **Senha GEDUC**
- **Ano Letivo** (padrão: 2025)

### 3. Confirmar Processamento

Uma mensagem aparecerá mostrando o que será feito:

```
📊 PROCESSAMENTO DE RECUPERAÇÃO ANUAL

⚙️ Este processo irá:
1. Fazer login no GEDUC
2. Acessar a página de Notas Finais
3. Buscar TODAS as turmas da escola
4. Para cada turma, processar TODAS as disciplinas
5. Extrair: Média Anual + Recuperação Final
6. Salvar na tabela 'notas_finais'

⏱️ Tempo estimado: 5-15 minutos

⚠️ ATENÇÃO: Isso irá processar TODAS as turmas!

Continuar?
```

Clique em **Sim** para prosseguir.

### 4. Acompanhar Progresso

Uma janela de log mostrará o progresso em tempo real:

```
============================================================
PROCESSAMENTO DE RECUPERAÇÃO ANUAL
============================================================

→ Buscando todas as turmas do sistema...
✓ 10 turmas encontradas no banco de dados

→ Iniciando navegador...
✓ Navegador iniciado

→ Fazendo login no GEDUC...
✓ Login realizado

→ Mudando para ano letivo 2025...
✓ Ano letivo alterado para 2025

→ Acessando notas finais...
✓ Página de notas finais carregada

→ Carregando turmas do GEDUC...
✓ 10 turmas no GEDUC

============================================================
TURMA 1/10:  - MATUTINO
============================================================
→ Buscando no GEDUC: 1º ANO MATUTINO
✓ Match exato: 1º ANO-MATU
✓ Turma local: ID 1, Nível: 2
✓ 25 alunos no banco local
✓ 8 disciplinas encontradas

  [1/8] LÍNGUA PORTUGUESA
    ✓ 25 registros extraídos
    ✓ 25 alunos atualizados

  [2/8] MATEMÁTICA
    ✓ 25 registros extraídos
    ✓ 25 alunos atualizados
    
... (continua para todas as disciplinas e turmas)
```

### 5. Conclusão

Ao final, será exibido um resumo:

```
============================================================
RECUPERAÇÃO ANUAL CONCLUÍDA!
============================================================
🏫 Turmas processadas: 10/10
📚 Disciplinas processadas: 80
✅ Alunos atualizados: 2000
============================================================
```

---

## 🗄️ Estrutura de Dados

### Tabela `notas_finais`

```sql
CREATE TABLE notas_finais (
  id INT PRIMARY KEY AUTO_INCREMENT,
  ano_letivo_id INT NOT NULL,
  aluno_id INT NOT NULL,
  disciplina_id INT NOT NULL,
  media_anual DECIMAL(4,1) NOT NULL,           -- Média dos 4 bimestres (x10)
  nota_recuperacao_final DECIMAL(4,1) NULL,    -- Nota da recuperação final (x10)
  media_final DECIMAL(4,1) NOT NULL,           -- Média final após recuperação (x10)
  data_atualizacao TIMESTAMP,
  UNIQUE KEY (aluno_id, disciplina_id, ano_letivo_id)
)
```

### Exemplo de Registro:

| Campo | Valor | Significado |
|-------|-------|-------------|
| `aluno_id` | 123 | ID do aluno |
| `disciplina_id` | 5 | Matemática |
| `ano_letivo_id` | 1 | 2025 |
| `media_anual` | 55.0 | Média dos 4 bimestres = 5.5 |
| `nota_recuperacao_final` | 70.0 | Recuperação final = 7.0 |
| `media_final` | 70.0 | Média final = 7.0 (usou recuperação) |

**Observações:**
- As notas são multiplicadas por 10 para compatibilidade com o sistema
- `media_final` = `nota_recuperacao_final` se recuperação >= média anual
- `media_final` = `media_anual` se não há recuperação ou recuperação < média

---

## 🧮 Processo de Cálculo

### 1. Extração do GEDUC

Para cada aluno em cada disciplina, o sistema extrai:
- **Média Atual**: Média dos 4 bimestres (escala 0-10)
- **Recuperação Final**: Nota da prova de recuperação anual (escala 0-10)

### 2. Cálculo da Média Final

```python
# Converter para escala 0-100 (sistema interno)
media_anual_bruta = media_atual * 10

if recuperacao_final >= media_atual:
    # Usar recuperação como média final
    media_final_bruta = recuperacao_final * 10
    nota_recuperacao_bruta = recuperacao_final * 10
else:
    # Usar média anual
    media_final_bruta = media_anual_bruta
    nota_recuperacao_bruta = None

# Arredondar usando função personalizada
media_anual = arredondar_personalizado(media_anual_bruta)
media_final = arredondar_personalizado(media_final_bruta)
```

### 3. Arredondamento

O sistema usa `arredondar_personalizado()` com as seguintes regras:

```python
# Nota em escala 0-100, divide por 10 para trabalhar
nota_real = nota / 10  # Ex: 73.5 → 7.35

# Separa parte inteira e decimal
parte_inteira = 7
fracao = 0.35

# Aplica limiares:
if fracao < 0.3125:
    resultado = 7.0  # Arredonda para baixo
elif fracao < 0.8125:
    resultado = 7.5  # Arredonda para meio
else:
    resultado = 8.0  # Arredonda para cima

# Retorna multiplicado por 10
return 75  # (7.5 * 10)
```

**Exemplos:**
- 73.3 → 7.33 → 7.3 → **73**
- 73.5 → 7.35 → 7.4 → **74**
- 76.7 → 7.67 → 7.7 → **77**
- 81.6 → 8.16 → 8.2 → **82**

---

## 🔍 Solução de Problemas

### Problema: "Turma não encontrada no banco local"

**Causa:** O nome da turma no GEDUC não corresponde ao nome no banco local.

**Solução:**
1. Verifique os nomes das turmas no banco local
2. Compare com os nomes no GEDUC
3. Se necessário, ajuste os nomes para corresponder

### Problema: "Disciplina não encontrada no banco local"

**Causa:** A disciplina existe no GEDUC mas não está cadastrada no banco local para aquele nível de ensino.

**Solução:**
1. Verifique se a disciplina está cadastrada
2. Verifique se o `nivel_id` está correto
3. Cadastre a disciplina se necessário

### Problema: "Sem média atual - IGNORADO"

**Causa:** O aluno não tem média registrada no GEDUC para aquela disciplina.

**Solução:**
- Isso é esperado para alunos transferidos ou evadidos
- Verifique se o aluno deveria ter notas
- Se sim, lance as notas no GEDUC primeiro

### Problema: "Erro ao conectar ao banco de dados"

**Causa:** Problema na conexão com o banco de dados.

**Solução:**
1. Verifique se o MySQL está rodando
2. Verifique as credenciais em `config/settings.py`
3. Teste a conexão manualmente

### Problema: "Tabela notas_finais não existe"

**Causa:** A migration não foi aplicada.

**Solução:**
```bash
python scripts/aplicar_migration_notas_finais.py
```

---

## 📊 Consultas Úteis

### Verificar médias finais de um aluno

```sql
SELECT 
    a.nome AS aluno,
    d.nome AS disciplina,
    nf.media_anual / 10 AS media_anual,
    nf.nota_recuperacao_final / 10 AS recuperacao,
    nf.media_final / 10 AS media_final
FROM notas_finais nf
JOIN alunos a ON nf.aluno_id = a.id
JOIN disciplinas d ON nf.disciplina_id = d.id
WHERE a.id = 123
AND nf.ano_letivo_id = 1;
```

### Listar alunos que fizeram recuperação final

```sql
SELECT 
    a.nome AS aluno,
    COUNT(*) AS disciplinas_em_recuperacao
FROM notas_finais nf
JOIN alunos a ON nf.aluno_id = a.id
WHERE nf.nota_recuperacao_final IS NOT NULL
AND nf.ano_letivo_id = 1
GROUP BY a.nome
ORDER BY disciplinas_em_recuperacao DESC;
```

### Comparar média anual vs média final

```sql
SELECT 
    a.nome,
    d.nome AS disciplina,
    nf.media_anual / 10 AS antes,
    nf.media_final / 10 AS depois,
    (nf.media_final - nf.media_anual) / 10 AS melhoria
FROM notas_finais nf
JOIN alunos a ON nf.aluno_id = a.id
JOIN disciplinas d ON nf.disciplina_id = d.id
WHERE nf.nota_recuperacao_final IS NOT NULL
AND nf.ano_letivo_id = 1
ORDER BY melhoria DESC;
```

---

## 🎓 Integração com Ata Geral

Após processar a recuperação anual, a **Ata Geral** utilizará automaticamente os dados da tabela `notas_finais` em vez de calcular as médias manualmente.

### Próximos Passos (Futuro):

- [ ] Atualizar `ata_1a5ano.py` para consultar `notas_finais`
- [ ] Atualizar `ata_6a9ano.py` para consultar `notas_finais`
- [ ] Atualizar `ata_1a9ano.py` para consultar `notas_finais`
- [ ] Adicionar opção de fallback (calcular se não houver em `notas_finais`)

---

## 📝 Notas de Versão

### Versão 1.0 (17/01/2026)

**Novo:**
- ✨ Nova tabela `notas_finais`
- ✨ Função de extração de notas finais do GEDUC
- ✨ Processamento automático de todas as turmas
- ✨ Armazenamento de médias finais e recuperação
- ✨ Menu "Recuperação Anual (Notas Finais)"
- ✨ Script de migration
- ✨ Documentação completa

**Características:**
- 🔄 Mesmo arredondamento da recuperação bimestral
- 📊 Suporte a médias finais com e sem recuperação
- 🔍 Logs detalhados de processamento
- ✅ Validação de dados em todas as etapas

---

## 📚 Referências

- [Análise Completa](ANALISE_RECUPERACAO_ANUAL.md)
- Migration: `migrations/criar_tabela_notas_finais.sql`
- Código: `src/interfaces/cadastro_notas.py`
- Automação: `src/importadores/geduc.py`

---

**Última atualização:** 17 de janeiro de 2026
