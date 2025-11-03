# Relatório Estatístico de Análise de Notas

## Descrição
Sistema completo de análise estatística de notas dos alunos com visualizações gráficas, identificação de pendências e rankings de desempenho.

## Funcionalidades

### 📊 Visão Geral
- **Estatísticas Gerais**:
  - Total de notas registradas
  - Média geral da turma
  - Maior e menor nota
  - Desvio padrão
  - Número de aprovados e reprovados
  - Notas pendentes (vazias)

- **Gráficos**:
  - Histograma de distribuição de notas
  - Gráfico de pizza mostrando taxa de aprovação/reprovação

### 📚 Análise por Disciplina
- Lista detalhada de cada disciplina com:
  - Média da disciplina
  - Maior e menor nota
  - Número de aprovados e reprovados
  - Comparação visual entre disciplinas

### ⚠️ Pendências
Identifica três tipos de problemas:

1. **Notas Vazias**: Alunos que ainda não possuem notas registradas
2. **Abaixo da Média**: Alunos com notas inferiores a 60 pontos
3. **Risco de Reprovação**: Alunos com 2 ou mais disciplinas abaixo da média

### 🏆 Rankings
- **Top 10 Melhores Médias**: Destaca os alunos com melhor desempenho
- **10 Alunos que Necessitam Atenção**: Identifica alunos com as menores médias para intervenção pedagógica

## Como Usar

1. **Acesso ao Relatório**:
   - No menu principal, clique em **"Gerenciamento de Notas"**
   - Selecione **"Relatório Estatístico de Notas"**

2. **Filtrar Dados**:
   - Selecione o **Nível de Ensino**
   - Selecione a **Série**
   - Selecione a **Turma** (ou "Todas" para análise geral)
   - Selecione o **Bimestre** (ou "Todos" para análise anual)

3. **Gerar Relatório**:
   - Clique no botão **"🔍 Gerar Relatório"**
   - Navegue pelas abas para explorar diferentes análises

## Requisitos Técnicos

### Dependências Python
O sistema requer as seguintes bibliotecas Python:

```bash
# Instalar matplotlib para gráficos
pip install matplotlib

# Instalar numpy para cálculos estatísticos
pip install numpy

# Outras dependências já existentes no sistema:
# - tkinter (já incluído no Python)
# - mysql-connector-python (já instalado)
# - pandas (já instalado)
```

### Instalação Rápida
Execute o seguinte comando no terminal (PowerShell):

```powershell
pip install matplotlib numpy
```

## Estrutura de Dados

O relatório analisa dados das seguintes tabelas do banco de dados:
- `notas`: Contém as notas dos alunos por disciplina e bimestre
- `alunos`: Informações dos alunos
- `disciplinas`: Lista de disciplinas
- `turmas`: Turmas organizadas por série e turno
- `matriculas`: Vínculo entre alunos e turmas

## Benefícios Pedagógicos

1. **Identificação Precoce**: Detecta alunos em dificuldade antes que seja tarde demais
2. **Acompanhamento Visual**: Gráficos facilitam a compreensão do desempenho geral
3. **Intervenção Direcionada**: Rankings ajudam a priorizar ações pedagógicas
4. **Gestão de Pendências**: Lista completa de notas faltantes para cobrança
5. **Análise Comparativa**: Permite comparar desempenho entre turmas e disciplinas

## Interpretação dos Dados

### Cores e Indicadores
- 🟢 **Verde**: Desempenho satisfatório (≥ 60)
- 🔴 **Vermelho**: Desempenho insatisfatório (< 60)
- 🔵 **Azul**: Informações neutras
- 🟣 **Rosa**: Pendências e alertas

### Medalhas no Ranking
- 🥇 **1º Lugar**: Melhor média geral
- 🥈 **2º Lugar**: Segunda melhor média
- 🥉 **3º Lugar**: Terceira melhor média

## Exemplos de Uso

### Caso 1: Reunião Pedagógica
Use a **Visão Geral** para apresentar o desempenho geral da turma e identificar tendências.

### Caso 2: Recuperação Bimestral
Use a aba **Pendências → Abaixo da Média** para listar alunos que precisam de recuperação.

### Caso 3: Planejamento de Intervenção
Use a aba **Rankings → Necessitam Atenção** para priorizar acompanhamento individual.

### Caso 4: Fechamento de Bimestre
Use a aba **Pendências → Notas Vazias** para cobrar professores que não lançaram notas.

## Solução de Problemas

### Erro ao Gerar Gráficos
Se aparecer erro relacionado a matplotlib:
```powershell
pip install --upgrade matplotlib
```

### Gráficos Não Aparecem
Certifique-se de que você selecionou uma turma com notas cadastradas.

### Dados Inconsistentes
Verifique se:
- As notas estão corretamente vinculadas ao ano letivo atual
- Os alunos estão matriculados na turma selecionada
- As disciplinas estão cadastradas para o nível de ensino correto

## Manutenção

Para melhores resultados:
1. Mantenha as notas sempre atualizadas
2. Revise regularmente as pendências
3. Use o relatório para reuniões mensais de acompanhamento
4. Exporte os dados quando necessário para análises externas

## Suporte

Em caso de dúvidas ou problemas:
1. Verifique se todas as dependências estão instaladas
2. Consulte os logs de erro no console
3. Certifique-se de que o banco de dados está acessível
4. Entre em contato com o administrador do sistema

---

**Desenvolvido para**: Sistema de Gerenciamento Escolar  
**Versão**: 1.0  
**Data**: Novembro de 2025
