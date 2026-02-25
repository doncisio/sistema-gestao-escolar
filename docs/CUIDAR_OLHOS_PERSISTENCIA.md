# Persistência de Seleções - Programa Cuidar dos Olhos

## 📋 Descrição

Implementação de persistência no banco de dados para as seleções dos termos do **Programa Cuidar dos Olhos**. As seleções de estudantes e profissionais agora são salvas no banco de dados MySQL ao invés de arquivos JSON temporários.

## ✨ Benefícios

- ✅ **Persistência robusta**: Dados salvos permanentemente no banco de dados
- ✅ **Recuperação futura**: Seleções podem ser recuperadas a qualquer momento
- ✅ **Histórico por ano letivo**: Mantém registro das seleções de cada ano
- ✅ **Integridade referencial**: Foreign keys garantem consistência dos dados
- ✅ **Melhor performance**: Consultas otimizadas com índices

## 🗄️ Estrutura do Banco de Dados

### Tabela: `cuidar_olhos_selecoes`

```sql
CREATE TABLE cuidar_olhos_selecoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo ENUM('estudante', 'profissional') NOT NULL,
    aluno_id BIGINT UNSIGNED NULL,
    responsavel_id BIGINT UNSIGNED NULL,
    funcionario_id BIGINT UNSIGNED NULL,
    categoria VARCHAR(50) NULL,
    selecionado BOOLEAN DEFAULT TRUE,
    ano_letivo INT NOT NULL,
    data_selecao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

### Campos

- **tipo**: Tipo de seleção (`estudante` ou `profissional`)
- **aluno_id**: ID do aluno (quando tipo = estudante)
- **responsavel_id**: ID do responsável (quando tipo = estudante)
- **funcionario_id**: ID do funcionário (quando tipo = profissional)
- **categoria**: Categoria do profissional (`professor` ou `servidor`)
- **selecionado**: Indica se está atualmente selecionado
- **ano_letivo**: Ano letivo da seleção
- **data_selecao**: Data e hora da primeira seleção
- **data_atualizacao**: Data e hora da última atualização

## 🚀 Instalação

### 1. Criar a Tabela

Execute o script Python para criar a tabela no banco de dados:

```bash
python criar_tabela_cuidar_olhos.py
```

Ou execute diretamente o SQL:

```bash
mysql -u [usuario] -p [banco] < sql/criar_tabela_cuidar_olhos_selecoes.sql
```

## 📝 Como Funciona

### Salvamento Automático

As seleções são salvas automaticamente no banco de dados sempre que o usuário:
- Marca/desmarca um checkbox
- Usa "Selecionar Todos"
- Usa "Desmarcar Todos"
- Usa "Inverter Seleção"
- Seleciona por série (estudantes) ou categoria (profissionais)

### Recuperação Automática

Quando o usuário abre a interface de seleção, o sistema:
1. Busca seleções salvas do ano letivo atual
2. Restaura automaticamente os checkboxes marcados
3. Exibe uma mensagem informando quantas seleções foram restauradas

### Limpeza de Seleções

O usuário pode limpar todas as seleções através do botão "Limpar Seleções":
- Conta quantas seleções existem
- Solicita confirmação
- Remove as seleções do banco de dados

## 📂 Arquivos Modificados

### Criados

- `sql/criar_tabela_cuidar_olhos_selecoes.sql` - Script SQL da tabela
- `criar_tabela_cuidar_olhos.py` - Script Python para executar migração
- `docs/CUIDAR_OLHOS_PERSISTENCIA.md` - Esta documentação

### Modificados

- `src/ui/planilha_estudantes_window.py`
  - `_salvar_selecoes()`: Salva no BD
  - `_carregar_selecoes_salvas()`: Carrega do BD
  - `_limpar_selecoes_salvas()`: Remove do BD

- `src/ui/planilha_profissionais_window.py`
  - `_salvar_selecoes()`: Salva no BD
  - `_carregar_selecoes_salvas()`: Carrega do BD
  - `_limpar_selecoes_salvas()`: Remove do BD

## 🔍 Consultas Úteis

### Ver todas as seleções de estudantes do ano atual

```sql
SELECT 
    a.nome as aluno,
    r.nome as responsavel,
    s.data_selecao,
    s.data_atualizacao
FROM cuidar_olhos_selecoes s
JOIN alunos a ON s.aluno_id = a.id
JOIN responsaveis r ON s.responsavel_id = r.id
WHERE s.tipo = 'estudante'
AND s.ano_letivo = 2026
AND s.selecionado = TRUE
ORDER BY a.nome;
```

### Ver todas as seleções de profissionais do ano atual

```sql
SELECT 
    f.nome as profissional,
    s.categoria,
    s.data_selecao,
    s.data_atualizacao
FROM cuidar_olhos_selecoes s
JOIN Funcionarios f ON s.funcionario_id = f.id
WHERE s.tipo = 'profissional'
AND s.ano_letivo = 2026
AND s.selecionado = TRUE
ORDER BY f.nome;
```

### Estatísticas por ano letivo

```sql
SELECT 
    ano_letivo,
    tipo,
    COUNT(*) as total_selecoes
FROM cuidar_olhos_selecoes
WHERE selecionado = TRUE
GROUP BY ano_letivo, tipo
ORDER BY ano_letivo DESC, tipo;
```

## 🔄 Migração de Dados Antigos (Se Necessário)

Se existiam arquivos JSON com seleções antigas em `temp/`, eles não serão mais utilizados. As novas seleções começam do zero no banco de dados.

## ⚠️ Importante

- As seleções são específicas por **ano letivo**
- Seleções de anos anteriores são mantidas no banco (histórico)
- Apenas seleções do ano letivo atual são carregadas automaticamente
- As foreign keys garantem que se um aluno/responsável/funcionário for deletado, suas seleções também serão removidas (CASCADE)

## 🐛 Troubleshooting

### Erro ao salvar seleções

Verifique se:
1. A tabela foi criada corretamente
2. O banco de dados está acessível
3. As foreign keys existem (tabelas `alunos`, `responsaveis`, `Funcionarios`)

### Seleções não são restauradas

Verifique se:
1. O ano letivo está correto (`ANO_LETIVO_ATUAL`)
2. Existem seleções salvas no banco para o ano atual
3. Os registros têm `selecionado = TRUE`

## 📊 Logs

As operações são registradas nos logs do sistema:
- Salvamento: `DEBUG` - "Seleções salvas no BD: X itens"
- Carregamento: `INFO` - "Seleções carregadas do BD: X de Y itens encontrados"
- Limpeza: `INFO` - "Seleções limpas do BD: X itens"
- Erros: `WARNING` ou `ERROR` conforme o caso

---

**Data de Implementação**: 25 de fevereiro de 2026  
**Versão**: 1.0
