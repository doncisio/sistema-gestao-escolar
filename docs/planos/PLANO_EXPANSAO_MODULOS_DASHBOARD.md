# 📋 Plano de Expansão: Dashboards por Perfil e Novos Módulos

> **📅 Data de Criação**: 30 de Novembro de 2025  
> **📅 Última Atualização**: 30 de Novembro de 2025  
> **🎯 Objetivo**: Expandir o sistema com dashboards específicos por perfil e novos módulos (Transporte, Merenda/SAE, BI, Censo Escolar)

---

## 📊 RESUMO EXECUTIVO

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PLANO DE EXPANSÃO DO SISTEMA                        │
├────────────────────────────────────────────────────────────────────────┤
│  📈 PARTE 1 - Dashboards por Perfil ✅ IMPLEMENTADO                   │
│     ├── Dashboard Administrador (Existente) ✅                        │
│     ├── Dashboard Coordenador Pedagógico ✅                           │
│     └── Dashboard Professor ✅                                        │
│                                                                        │
│  🚌 PARTE 2 - Módulo Transporte Escolar                               │
│     ├── Cadastro de Veículos e Rotas 🔲                               │
│     ├── Alunos Usuários de Transporte 🔲                              │
│     └── Dashboard de Transporte 🔲                                    │
│                                                                        │
│  🍽️ PARTE 3 - Módulo Merenda/SAE                                      │
│     ├── Controle de Estoque 🔲                                        │
│     ├── Cardápio e Planejamento 🔲                                    │
│     └── Relatórios Nutricionais 🔲                                    │
│                                                                        │
│  📊 PARTE 4 - Módulo BI (Business Intelligence)                       │
│     ├── Indicadores de Desempenho 🔲                                  │
│     ├── Relatórios Comparativos 🔲                                    │
│     └── Exportação de Dados 🔲                                        │
│                                                                        │
│  📋 PARTE 5 - Módulo Censo Escolar                                    │
│     ├── Coleta de Dados INEP 🔲                                       │
│     ├── Validação e Consistência 🔲                                   │
│     └── Exportação para Educacenso 🔲                                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 PARTE 1: DASHBOARDS POR PERFIL DE USUÁRIO ✅ IMPLEMENTADO

### 1.1 Dashboard Atual (Administrador) ✅

**Localização**: `ui/dashboard.py`

**Funcionalidades existentes**:
- Gráfico de pizza: Distribuição de alunos por série/turma
- Movimento mensal (entradas/saídas)
- Estatísticas gerais de matrícula
- Visão completa de toda a escola

---

### 1.2 Dashboard do Coordenador Pedagógico ✅ IMPLEMENTADO

**Arquivo criado**: `ui/dashboard_coordenador.py`

**Objetivo**: Fornecer visão pedagógica focada em desempenho acadêmico

#### Componentes do Dashboard:

```python
# Estrutura proposta para o dashboard do coordenador
class DashboardCoordenador:
    """
    Dashboard específico para coordenadores pedagógicos.
    Foco: métricas pedagógicas e acompanhamento de desempenho.
    """
    
    def __init__(self, janela, db_service, escola_id, ano_letivo):
        self.janela = janela
        self.db_service = db_service
        self.escola_id = escola_id
        self.ano_letivo = ano_letivo
    
    def criar_dashboard(self, frame_pai):
        """Cria o dashboard do coordenador."""
        pass
    
    # === SEÇÃO 1: VISÃO GERAL PEDAGÓGICA ===
    def _card_media_geral_escola(self):
        """Card com média geral da escola por disciplina."""
        pass
    
    def _card_taxa_aprovacao_reprovacao(self):
        """Card com taxa de aprovação/reprovação por série."""
        pass
    
    def _card_frequencia_geral(self):
        """Card com frequência média por turma."""
        pass
    
    # === SEÇÃO 2: GRÁFICOS DE DESEMPENHO ===
    def _grafico_evolucao_notas_bimestral(self):
        """Gráfico de linha: evolução das médias por bimestre."""
        pass
    
    def _grafico_comparativo_turmas(self):
        """Gráfico de barras: comparativo de desempenho entre turmas."""
        pass
    
    def _grafico_distribuicao_notas(self):
        """Histograma: distribuição de notas (quantos alunos em cada faixa)."""
        pass
    
    # === SEÇÃO 3: ALERTAS E PENDÊNCIAS ===
    def _lista_alunos_baixo_desempenho(self):
        """Lista de alunos com média abaixo de 6.0."""
        pass
    
    def _lista_alunos_baixa_frequencia(self):
        """Lista de alunos com frequência abaixo de 75%."""
        pass
    
    def _lista_turmas_pendencias_notas(self):
        """Lista de turmas com notas pendentes de lançamento."""
        pass
    
    # === SEÇÃO 4: FILTROS ===
    def _filtro_por_serie(self):
        """Filtrar dashboard por série específica."""
        pass
    
    def _filtro_por_disciplina(self):
        """Filtrar dashboard por disciplina específica."""
        pass
    
    def _filtro_por_bimestre(self):
        """Filtrar dashboard por bimestre."""
        pass
```

#### Tabelas do Banco Necessárias:
- `notas` (já existe)
- `faltas_bimestrais` (já existe)
- `matriculas` (já existe)
- `turmas` (já existe)

#### Queries SQL Necessárias:

```sql
-- Média geral por disciplina
SELECT d.nome AS disciplina,
       ROUND(AVG(n.nota), 2) AS media
FROM notas n
JOIN disciplinas d ON n.disciplina_id = d.id
WHERE n.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = YEAR(CURDATE()))
GROUP BY d.id
ORDER BY media DESC;

-- Taxa de aprovação por série
SELECT s.nome AS serie,
       COUNT(CASE WHEN m.status = 'Aprovado' THEN 1 END) AS aprovados,
       COUNT(CASE WHEN m.status = 'Reprovado' THEN 1 END) AS reprovados,
       COUNT(*) AS total,
       ROUND(COUNT(CASE WHEN m.status = 'Aprovado' THEN 1 END) * 100.0 / COUNT(*), 1) AS taxa_aprovacao
FROM matriculas m
JOIN series s ON m.serie_id = s.id
WHERE m.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = YEAR(CURDATE()))
GROUP BY s.id;

-- Alunos com baixo desempenho
SELECT a.nome, s.nome AS serie, t.turma,
       ROUND(AVG(n.nota), 2) AS media_geral
FROM alunos a
JOIN matriculas m ON a.id = m.aluno_id
JOIN series s ON m.serie_id = s.id
JOIN turmas t ON m.turma_id = t.id
JOIN notas n ON a.id = n.aluno_id AND n.ano_letivo_id = m.ano_letivo_id
WHERE m.ano_letivo_id = (SELECT id FROM anosletivos WHERE ano_letivo = YEAR(CURDATE()))
  AND m.status = 'Ativo'
GROUP BY a.id
HAVING media_geral < 6.0
ORDER BY media_geral ASC;
```

---

### 1.3 Dashboard do Professor 🔲

**Arquivo a criar**: `ui/dashboard_professor.py`

**Objetivo**: Visão focada nas turmas do professor logado

#### Componentes do Dashboard:

```python
# Estrutura proposta para o dashboard do professor
class DashboardProfessor:
    """
    Dashboard específico para professores.
    Foco: turmas e disciplinas do professor logado.
    """
    
    def __init__(self, janela, db_service, funcionario_id, ano_letivo):
        self.janela = janela
        self.db_service = db_service
        self.funcionario_id = funcionario_id  # ID do professor logado
        self.ano_letivo = ano_letivo
    
    def criar_dashboard(self, frame_pai):
        """Cria o dashboard do professor."""
        pass
    
    # === SEÇÃO 1: MINHAS TURMAS ===
    def _lista_minhas_turmas(self):
        """Cards com as turmas do professor e quantidade de alunos."""
        pass
    
    def _card_total_alunos(self):
        """Total de alunos sob responsabilidade do professor."""
        pass
    
    # === SEÇÃO 2: LANÇAMENTOS PENDENTES ===
    def _card_notas_pendentes(self):
        """Quantidade de notas que faltam lançar por turma/bimestre."""
        pass
    
    def _card_frequencias_pendentes(self):
        """Frequências pendentes de lançamento."""
        pass
    
    # === SEÇÃO 3: DESEMPENHO DAS TURMAS ===
    def _grafico_media_minhas_turmas(self):
        """Gráfico de barras: média de cada turma que leciono."""
        pass
    
    def _grafico_frequencia_minhas_turmas(self):
        """Gráfico: frequência média por turma."""
        pass
    
    # === SEÇÃO 4: AÇÕES RÁPIDAS ===
    def _btn_lancar_notas(self):
        """Botão rápido para lançar notas."""
        pass
    
    def _btn_lancar_frequencia(self):
        """Botão rápido para lançar frequência."""
        pass
    
    def _btn_gerar_boletins(self):
        """Botão rápido para gerar boletins da turma."""
        pass
```

#### Integração com Sistema de Perfis:

**Arquivo a modificar**: `ui/dashboard.py`

```python
# Adicionar ao DashboardManager existente
def criar_dashboard_por_perfil(self, usuario):
    """
    Cria dashboard apropriado baseado no perfil do usuário.
    
    Args:
        usuario: Objeto UsuarioLogado com informações do perfil
    """
    if usuario is None:
        # Perfis desabilitados - mostrar dashboard completo
        self.criar_dashboard()
        return
    
    if usuario.is_admin():
        # Dashboard administrativo completo
        self.criar_dashboard()
    
    elif usuario.is_coordenador():
        # Dashboard pedagógico
        from ui.dashboard_coordenador import DashboardCoordenador
        dash = DashboardCoordenador(
            self.janela, 
            self.db_service, 
            self.escola_id, 
            self.ano_letivo
        )
        dash.criar_dashboard(self.frame_getter())
    
    elif usuario.is_professor():
        # Dashboard do professor
        from ui.dashboard_professor import DashboardProfessor
        dash = DashboardProfessor(
            self.janela,
            self.db_service,
            usuario.funcionario_id,
            self.ano_letivo
        )
        dash.criar_dashboard(self.frame_getter())
```

---

## 🚌 PARTE 2: MÓDULO TRANSPORTE ESCOLAR

### 2.1 Estrutura de Pastas

```
gestao/
├── transporte/
│   ├── __init__.py
│   ├── models.py           # Dataclasses: Veiculo, Rota, PontoParada
│   ├── services.py         # CRUD e lógica de negócio
│   ├── interfaces.py       # Interfaces Tkinter
│   └── relatorios.py       # Geração de relatórios
```

### 2.2 Tabelas do Banco de Dados

```sql
-- Veículos da frota escolar
CREATE TABLE transporte_veiculos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    placa VARCHAR(10) NOT NULL UNIQUE,
    tipo ENUM('Ônibus', 'Van', 'Micro-ônibus') NOT NULL,
    capacidade INT NOT NULL,
    ano_fabricacao YEAR,
    motorista_id BIGINT UNSIGNED,
    status ENUM('Ativo', 'Manutenção', 'Inativo') DEFAULT 'Ativo',
    km_atual DECIMAL(10,1) DEFAULT 0,
    ultima_revisao DATE,
    proxima_revisao DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (motorista_id) REFERENCES Funcionarios(id)
);

-- Rotas de transporte
CREATE TABLE transporte_rotas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    turno ENUM('Matutino', 'Vespertino', 'Noturno', 'Integral') NOT NULL,
    veiculo_id INT,
    km_total DECIMAL(10,2),
    tempo_estimado_min INT,
    horario_saida TIME,
    horario_chegada TIME,
    ativa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (veiculo_id) REFERENCES transporte_veiculos(id)
);

-- Pontos de parada
CREATE TABLE transporte_pontos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rota_id INT NOT NULL,
    ordem INT NOT NULL,
    descricao VARCHAR(200) NOT NULL,
    endereco VARCHAR(255),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    horario_previsto TIME,
    FOREIGN KEY (rota_id) REFERENCES transporte_rotas(id),
    UNIQUE KEY (rota_id, ordem)
);

-- Alunos usuários de transporte
CREATE TABLE transporte_alunos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id BIGINT UNSIGNED NOT NULL,
    rota_id INT NOT NULL,
    ponto_embarque_id INT,
    ponto_desembarque_id INT,
    ano_letivo_id INT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id),
    FOREIGN KEY (rota_id) REFERENCES transporte_rotas(id),
    FOREIGN KEY (ponto_embarque_id) REFERENCES transporte_pontos(id),
    FOREIGN KEY (ponto_desembarque_id) REFERENCES transporte_pontos(id),
    FOREIGN KEY (ano_letivo_id) REFERENCES anosletivos(id),
    UNIQUE KEY (aluno_id, ano_letivo_id)
);

-- Registro de ocorrências
CREATE TABLE transporte_ocorrencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    veiculo_id INT,
    rota_id INT,
    tipo ENUM('Atraso', 'Acidente', 'Manutenção', 'Outro') NOT NULL,
    descricao TEXT NOT NULL,
    data_ocorrencia DATETIME NOT NULL,
    resolvido BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    registrado_por BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (veiculo_id) REFERENCES transporte_veiculos(id),
    FOREIGN KEY (rota_id) REFERENCES transporte_rotas(id),
    FOREIGN KEY (registrado_por) REFERENCES Funcionarios(id)
);
```

### 2.3 Funcionalidades do Módulo

#### 2.3.1 Cadastro de Veículos
- [x] Cadastrar novo veículo
- [x] Editar dados do veículo
- [x] Associar motorista
- [x] Registrar quilometragem
- [x] Controle de manutenção

#### 2.3.2 Gestão de Rotas
- [x] Criar/editar rotas
- [x] Definir pontos de parada
- [x] Associar veículo à rota
- [x] Definir horários

#### 2.3.3 Alunos Usuários
- [x] Vincular aluno a rota
- [x] Definir pontos de embarque/desembarque
- [x] Lista de alunos por rota
- [x] Lista de alunos por ponto

#### 2.3.4 Dashboard de Transporte
```python
class DashboardTransporte:
    """Dashboard específico do módulo de transporte."""
    
    def criar_dashboard(self, frame):
        # Cards de resumo
        self._card_total_alunos_transporte()
        self._card_total_veiculos_ativos()
        self._card_km_total_mes()
        
        # Gráfico de ocupação por rota
        self._grafico_ocupacao_rotas()
        
        # Lista de manutenções pendentes
        self._lista_manutencoes_proximas()
        
        # Ocorrências recentes
        self._lista_ocorrencias_recentes()
```

### 2.4 Relatórios do Transporte

1. **Lista de Alunos por Rota** - PDF com alunos, endereço e ponto de parada
2. **Mapa de Rotas** - Visualização dos pontos de parada
3. **Controle de Manutenção** - Veículos com revisão pendente
4. **Histórico de Ocorrências** - Relatório mensal de ocorrências

---

## 🍽️ PARTE 3: MÓDULO MERENDA/SAE (Serviço de Alimentação Escolar)

### 3.1 Estrutura de Pastas

```
gestao/
├── merenda/
│   ├── __init__.py
│   ├── models.py           # Dataclasses: Alimento, Cardapio, Estoque
│   ├── services.py         # CRUD e lógica de negócio
│   ├── interfaces.py       # Interfaces Tkinter
│   ├── nutricao.py         # Cálculos nutricionais
│   └── relatorios.py       # Geração de relatórios
```

### 3.2 Tabelas do Banco de Dados

```sql
-- Categorias de alimentos
CREATE TABLE sae_categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT
);

-- Cadastro de alimentos
CREATE TABLE sae_alimentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nome VARCHAR(200) NOT NULL,
    categoria_id INT,
    unidade_medida ENUM('kg', 'L', 'unidade', 'pacote', 'lata', 'caixa') NOT NULL,
    calorias_por_100g DECIMAL(10,2),
    proteinas_por_100g DECIMAL(10,2),
    carboidratos_por_100g DECIMAL(10,2),
    gorduras_por_100g DECIMAL(10,2),
    perecivel BOOLEAN DEFAULT TRUE,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES sae_categorias(id)
);

-- Fornecedores
CREATE TABLE sae_fornecedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    razao_social VARCHAR(200) NOT NULL,
    cnpj VARCHAR(18) UNIQUE,
    contato VARCHAR(100),
    telefone VARCHAR(20),
    email VARCHAR(100),
    endereco TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Estoque de alimentos
CREATE TABLE sae_estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alimento_id INT NOT NULL,
    quantidade DECIMAL(10,3) NOT NULL,
    lote VARCHAR(50),
    data_entrada DATE NOT NULL,
    data_validade DATE,
    fornecedor_id INT,
    preco_unitario DECIMAL(10,2),
    nota_fiscal VARCHAR(50),
    escola_id INT NOT NULL DEFAULT 60,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alimento_id) REFERENCES sae_alimentos(id),
    FOREIGN KEY (fornecedor_id) REFERENCES sae_fornecedores(id)
);

-- Movimentação de estoque
CREATE TABLE sae_movimentacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estoque_id INT NOT NULL,
    tipo ENUM('entrada', 'saida', 'perda', 'ajuste') NOT NULL,
    quantidade DECIMAL(10,3) NOT NULL,
    motivo VARCHAR(200),
    data_movimentacao DATETIME NOT NULL,
    registrado_por BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estoque_id) REFERENCES sae_estoque(id),
    FOREIGN KEY (registrado_por) REFERENCES Funcionarios(id)
);

-- Cardápios
CREATE TABLE sae_cardapios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    semana INT,
    aprovado BOOLEAN DEFAULT FALSE,
    aprovado_por BIGINT UNSIGNED,
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aprovado_por) REFERENCES Funcionarios(id)
);

-- Itens do cardápio (refeições por dia)
CREATE TABLE sae_cardapio_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cardapio_id INT NOT NULL,
    dia_semana ENUM('Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta') NOT NULL,
    tipo_refeicao ENUM('Desjejum', 'Lanche Manhã', 'Almoço', 'Lanche Tarde', 'Jantar') NOT NULL,
    descricao_refeicao TEXT NOT NULL,
    calorias_total DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cardapio_id) REFERENCES sae_cardapios(id),
    UNIQUE KEY (cardapio_id, dia_semana, tipo_refeicao)
);

-- Ingredientes de cada refeição
CREATE TABLE sae_cardapio_ingredientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    alimento_id INT NOT NULL,
    quantidade_per_capita DECIMAL(10,3) NOT NULL COMMENT 'Quantidade por aluno',
    unidade_medida VARCHAR(20),
    FOREIGN KEY (item_id) REFERENCES sae_cardapio_itens(id),
    FOREIGN KEY (alimento_id) REFERENCES sae_alimentos(id)
);

-- Controle diário de refeições servidas
CREATE TABLE sae_refeicoes_servidas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data DATE NOT NULL,
    tipo_refeicao ENUM('Desjejum', 'Lanche Manhã', 'Almoço', 'Lanche Tarde', 'Jantar') NOT NULL,
    quantidade_servida INT NOT NULL,
    sobra_kg DECIMAL(10,3),
    observacoes TEXT,
    registrado_por BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (registrado_por) REFERENCES Funcionarios(id),
    UNIQUE KEY (data, tipo_refeicao)
);
```

### 3.3 Funcionalidades do Módulo

#### 3.3.1 Gestão de Estoque
- [x] Cadastrar entrada de alimentos
- [x] Registrar saída para preparo
- [x] Controle de validade
- [x] Alertas de estoque baixo
- [x] Inventário mensal

#### 3.3.2 Planejamento de Cardápio
- [x] Criar cardápio semanal
- [x] Calcular quantidade de ingredientes
- [x] Verificar disponibilidade em estoque
- [x] Aprovar cardápio

#### 3.3.3 Controle Nutricional
- [x] Cálculo de calorias por refeição
- [x] Cálculo de macro-nutrientes
- [x] Verificar se atende PNAE (Programa Nacional de Alimentação Escolar)

### 3.4 Dashboard de Merenda

```python
class DashboardMerenda:
    """Dashboard do módulo de alimentação escolar."""
    
    def criar_dashboard(self, frame):
        # Cards de resumo
        self._card_refeicoes_servidas_mes()
        self._card_custo_per_capita()
        self._card_itens_vencimento_proximo()
        
        # Gráfico de refeições servidas por dia
        self._grafico_refeicoes_diarias()
        
        # Gráfico de consumo por categoria
        self._grafico_consumo_categoria()
        
        # Alertas
        self._lista_alertas_estoque()
        self._lista_itens_vencendo()
```

### 3.5 Relatórios do SAE

1. **Mapa de Consumo Mensal** - Alimentos utilizados no mês
2. **Relatório Nutricional** - Análise nutricional do cardápio
3. **Controle de Custos** - Custo per capita por refeição
4. **Itens Próximos do Vencimento** - Lista para ação preventiva
5. **Prestação de Contas PNAE** - Formato exigido pelo FNDE

---

## 📊 PARTE 4: MÓDULO BI (BUSINESS INTELLIGENCE)

### 4.1 Estrutura de Pastas

```
gestao/
├── bi/
│   ├── __init__.py
│   ├── indicadores.py      # Cálculo de indicadores
│   ├── comparativos.py     # Análises comparativas
│   ├── exportacao.py       # Exportação de dados
│   └── dashboard_bi.py     # Interface de BI
```

### 4.2 Indicadores Educacionais

#### 4.2.1 Indicadores de Matrícula
```python
class IndicadoresMatricula:
    """Indicadores relacionados a matrículas."""
    
    def taxa_matricula_por_faixa_etaria(self):
        """Porcentagem de crianças matriculadas vs população em idade escolar."""
        pass
    
    def taxa_evasao(self):
        """Porcentagem de alunos que abandonaram durante o ano."""
        pass
    
    def taxa_transferencia(self):
        """Porcentagem de transferências (entrada e saída)."""
        pass
    
    def evolucao_matriculas_historico(self):
        """Comparativo de matrículas nos últimos 5 anos."""
        pass
```

#### 4.2.2 Indicadores de Desempenho
```python
class IndicadoresDesempenho:
    """Indicadores de desempenho acadêmico."""
    
    def taxa_aprovacao_reprovacao(self):
        """Por série/ano."""
        pass
    
    def taxa_distorcao_idade_serie(self):
        """Alunos com idade superior à esperada para a série."""
        pass
    
    def media_geral_por_disciplina(self):
        """Comparativo entre disciplinas."""
        pass
    
    def evolucao_ideb(self):
        """Se disponível, mostrar evolução do IDEB."""
        pass
```

#### 4.2.3 Indicadores de Frequência
```python
class IndicadoresFrequencia:
    """Indicadores de frequência escolar."""
    
    def taxa_frequencia_media(self):
        """Frequência média por turma/série."""
        pass
    
    def infrequencia_critica(self):
        """Alunos com frequência abaixo de 75%."""
        pass
    
    def correlacao_frequencia_desempenho(self):
        """Análise de correlação entre frequência e notas."""
        pass
```

### 4.3 Dashboard de BI

```python
class DashboardBI:
    """Dashboard de Business Intelligence."""
    
    def criar_dashboard(self, frame):
        # === SEÇÃO 1: KPIs PRINCIPAIS ===
        self._kpi_total_alunos()
        self._kpi_taxa_aprovacao()
        self._kpi_media_frequencia()
        self._kpi_distorcao_idade_serie()
        
        # === SEÇÃO 2: GRÁFICOS COMPARATIVOS ===
        self._grafico_evolucao_matriculas_5_anos()
        self._grafico_aprovacao_por_serie()
        self._grafico_desempenho_por_disciplina()
        
        # === SEÇÃO 3: ANÁLISES AVANÇADAS ===
        self._mapa_calor_desempenho()  # Série x Disciplina
        self._analise_tendencias()
        
        # === SEÇÃO 4: EXPORTAÇÃO ===
        self._btn_exportar_excel()
        self._btn_exportar_pdf()
        self._btn_exportar_csv()
```

### 4.4 Funcionalidades de Exportação

```python
class ExportadorDados:
    """Exportação de dados para análise externa."""
    
    def exportar_excel(self, dados, nome_arquivo):
        """Exporta dados para Excel com múltiplas abas."""
        pass
    
    def exportar_csv(self, dados, nome_arquivo):
        """Exporta dados para CSV."""
        pass
    
    def exportar_pdf_relatorio(self, dados, template):
        """Gera relatório em PDF formatado."""
        pass
    
    def exportar_json_api(self, dados):
        """Exporta para integração com outros sistemas."""
        pass
```

---

## 📋 PARTE 5: MÓDULO CENSO ESCOLAR

### 5.1 Estrutura de Pastas

```
gestao/
├── censo/
│   ├── __init__.py
│   ├── models.py           # Modelos de dados do Censo
│   ├── validadores.py      # Validação conforme regras INEP
│   ├── exportador.py       # Exportação formato Educacenso
│   ├── importador.py       # Importação de retorno
│   └── interfaces.py       # Interface de gestão
```

### 5.2 Tabelas Auxiliares do Censo

```sql
-- Dados complementares para o Censo (que não existem no cadastro padrão)
CREATE TABLE censo_dados_complementares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id BIGINT UNSIGNED NOT NULL UNIQUE,
    
    -- Dados socioeconômicos
    renda_familiar ENUM('Até 1 SM', '1-2 SM', '2-3 SM', '3-5 SM', 'Acima 5 SM'),
    bolsa_familia BOOLEAN DEFAULT FALSE,
    bpc BOOLEAN DEFAULT FALSE,  -- Benefício de Prestação Continuada
    
    -- Dados de transporte
    utiliza_transporte_escolar BOOLEAN DEFAULT FALSE,
    tipo_transporte ENUM('Público Municipal', 'Público Estadual', 'Privado', 'Outro'),
    
    -- Dados de saúde/necessidades especiais
    possui_deficiencia BOOLEAN DEFAULT FALSE,
    tipo_deficiencia VARCHAR(200),
    possui_transtorno BOOLEAN DEFAULT FALSE,
    tipo_transtorno VARCHAR(200),
    possui_altas_habilidades BOOLEAN DEFAULT FALSE,
    
    -- Recursos necessários
    recurso_ledor BOOLEAN DEFAULT FALSE,
    recurso_transcricao BOOLEAN DEFAULT FALSE,
    recurso_interprete_libras BOOLEAN DEFAULT FALSE,
    recurso_guia_interprete BOOLEAN DEFAULT FALSE,
    recurso_ampliacao BOOLEAN DEFAULT FALSE,
    recurso_braille BOOLEAN DEFAULT FALSE,
    
    -- Outros dados
    local_diferenciado ENUM('Área remanescente quilombo', 'Terra indígena', 'Assentamento', 'Comunidade tradicional'),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (aluno_id) REFERENCES alunos(id)
);

-- Dados complementares de funcionários para o Censo
CREATE TABLE censo_funcionarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    funcionario_id BIGINT UNSIGNED NOT NULL UNIQUE,
    
    -- Formação
    escolaridade ENUM('Fund. Incompleto', 'Fund. Completo', 'Médio Incompleto', 'Médio Completo', 'Superior Incompleto', 'Superior Completo', 'Pós-Graduação'),
    curso_formacao VARCHAR(200),
    instituicao_formacao VARCHAR(200),
    ano_conclusao YEAR,
    
    -- Pós-graduação
    possui_especializacao BOOLEAN DEFAULT FALSE,
    possui_mestrado BOOLEAN DEFAULT FALSE,
    possui_doutorado BOOLEAN DEFAULT FALSE,
    
    -- Disciplinas que leciona (para professores)
    disciplinas_censo TEXT COMMENT 'Códigos INEP separados por vírgula',
    
    -- Situação funcional
    vinculo ENUM('Concursado', 'Contratado', 'CLT', 'Voluntário', 'Terceirizado'),
    carga_horaria_semanal INT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (funcionario_id) REFERENCES Funcionarios(id)
);

-- Histórico de exportações do Censo
CREATE TABLE censo_exportacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ano_censo YEAR NOT NULL,
    tipo_exportacao ENUM('Inicial', 'Retificação', 'Situação Aluno') NOT NULL,
    data_exportacao DATETIME NOT NULL,
    arquivo_gerado VARCHAR(255),
    quantidade_registros INT,
    erros_encontrados INT DEFAULT 0,
    status ENUM('Pendente', 'Enviado', 'Processado', 'Rejeitado') DEFAULT 'Pendente',
    observacoes TEXT,
    exportado_por BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exportado_por) REFERENCES Funcionarios(id)
);
```

### 5.3 Funcionalidades do Módulo

#### 5.3.1 Coleta de Dados
- [x] Completar dados de alunos para o Censo
- [x] Completar dados de funcionários
- [x] Validar campos obrigatórios
- [x] Identificar registros incompletos

#### 5.3.2 Validação
```python
class ValidadorCenso:
    """Validação conforme regras do INEP."""
    
    def validar_aluno(self, aluno):
        """Valida dados do aluno conforme Censo."""
        erros = []
        
        # CPF obrigatório
        if not aluno.cpf:
            erros.append("CPF não informado")
        elif not self._validar_cpf(aluno.cpf):
            erros.append("CPF inválido")
        
        # Data de nascimento
        if not aluno.data_nascimento:
            erros.append("Data de nascimento não informada")
        
        # Nome da mãe
        if not aluno.nome_mae:
            erros.append("Nome da mãe não informado")
        
        # Cor/Raça
        if not aluno.cor_raca:
            erros.append("Cor/Raça não informada")
        
        # Nacionalidade
        if not aluno.nacionalidade:
            erros.append("Nacionalidade não informada")
        
        return erros
    
    def validar_escola(self):
        """Valida dados da escola conforme Censo."""
        pass
    
    def validar_turma(self, turma):
        """Valida dados da turma conforme Censo."""
        pass
    
    def gerar_relatorio_inconsistencias(self):
        """Gera relatório com todas as inconsistências encontradas."""
        pass
```

#### 5.3.3 Exportação para Educacenso
```python
class ExportadorEducacenso:
    """Gera arquivo no formato exigido pelo Educacenso/INEP."""
    
    def exportar_registro_00(self):
        """Registro 00 - Dados da Escola."""
        pass
    
    def exportar_registro_10(self):
        """Registro 10 - Cadastro de Turma."""
        pass
    
    def exportar_registro_20(self):
        """Registro 20 - Cadastro de Profissional."""
        pass
    
    def exportar_registro_30(self):
        """Registro 30 - Cadastro de Aluno."""
        pass
    
    def exportar_registro_40(self):
        """Registro 40 - Matrícula do Aluno."""
        pass
    
    def exportar_registro_50(self):
        """Registro 50 - Docência."""
        pass
    
    def exportar_registro_60(self):
        """Registro 60 - Situação do Aluno (final do ano)."""
        pass
```

### 5.4 Dashboard do Censo

```python
class DashboardCenso:
    """Dashboard para acompanhamento do Censo Escolar."""
    
    def criar_dashboard(self, frame):
        # === STATUS GERAL ===
        self._card_progresso_preenchimento()
        self._card_registros_pendentes()
        self._card_erros_validacao()
        
        # === DETALHAMENTO ===
        self._tabela_alunos_incompletos()
        self._tabela_funcionarios_incompletos()
        
        # === AÇÕES ===
        self._btn_validar_tudo()
        self._btn_exportar_educacenso()
        self._btn_gerar_relatorio()
```

### 5.5 Cronograma do Censo

| Período | Atividade |
|---------|-----------|
| Janeiro-Abril | Coleta de dados complementares |
| Maio | Validação e correção de inconsistências |
| Junho-Julho | Primeira exportação (Censo Inicial) |
| Agosto | Correções e retificações |
| Novembro-Dezembro | Situação do Aluno (final do ano) |

---

## 🗂️ CRONOGRAMA DE IMPLEMENTAÇÃO

### Fase 1: Dashboards por Perfil (Prioridade ALTA)
| Semana | Atividade | Esforço |
|--------|-----------|---------|
| 1 | Criar `dashboard_coordenador.py` | 3 dias |
| 1-2 | Criar `dashboard_professor.py` | 3 dias |
| 2 | Integrar com `DashboardManager` existente | 1 dia |
| 2 | Testes e ajustes | 1 dia |

### Fase 2: Módulo Censo Escolar (Prioridade ALTA)
| Semana | Atividade | Esforço |
|--------|-----------|---------|
| 3 | Criar tabelas do Censo | 1 dia |
| 3-4 | Criar módulo `censo/` | 3 dias |
| 4 | Validadores e exportador | 3 dias |
| 5 | Interface e dashboard | 2 dias |
| 5 | Testes e documentação | 1 dia |

### Fase 3: Módulo Transporte (Prioridade MÉDIA)
| Semana | Atividade | Esforço |
|--------|-----------|---------|
| 6 | Criar tabelas de transporte | 1 dia |
| 6-7 | Criar módulo `transporte/` | 4 dias |
| 7-8 | Interface e dashboard | 3 dias |
| 8 | Relatórios | 2 dias |

### Fase 4: Módulo Merenda/SAE (Prioridade MÉDIA)
| Semana | Atividade | Esforço |
|--------|-----------|---------|
| 9 | Criar tabelas SAE | 1 dia |
| 9-10 | Criar módulo `merenda/` | 4 dias |
| 10-11 | Interface e dashboard | 3 dias |
| 11 | Relatórios e cálculos nutricionais | 2 dias |

### Fase 5: Módulo BI (Prioridade BAIXA)
| Semana | Atividade | Esforço |
|--------|-----------|---------|
| 12 | Criar módulo `bi/` | 3 dias |
| 12-13 | Implementar indicadores | 3 dias |
| 13 | Dashboard BI | 2 dias |
| 13 | Exportação de dados | 2 dias |

---

## 📝 OBSERVAÇÕES TÉCNICAS

### Padrões a Seguir

1. **Estrutura de Módulos**: Seguir padrão existente (`banco_questoes/`, `auth/`)
2. **Services**: Usar pattern de services para lógica de negócio
3. **Interfaces**: Seguir padrão de `interface_*.py` existente
4. **Dashboards**: Seguir padrão de `ui/dashboard.py`
5. **Feature Flags**: Adicionar flags para cada módulo novo em `feature_flags.json`

### Feature Flags a Adicionar

```json
{
    "modulo_transporte": {
        "enabled": false,
        "description": "Habilita módulo de transporte escolar"
    },
    "modulo_merenda_sae": {
        "enabled": false,
        "description": "Habilita módulo de merenda/SAE"
    },
    "modulo_bi": {
        "enabled": false,
        "description": "Habilita módulo de Business Intelligence"
    },
    "modulo_censo": {
        "enabled": false,
        "description": "Habilita módulo de Censo Escolar"
    },
    "dashboard_coordenador": {
        "enabled": false,
        "description": "Habilita dashboard específico do coordenador"
    },
    "dashboard_professor": {
        "enabled": false,
        "description": "Habilita dashboard específico do professor"
    }
}
```

### Permissões a Adicionar

| Código | Descrição | Módulo |
|--------|-----------|--------|
| `transporte.visualizar` | Visualizar dados de transporte | transporte |
| `transporte.gerenciar` | Gerenciar veículos e rotas | transporte |
| `merenda.visualizar` | Visualizar cardápios e estoque | merenda |
| `merenda.gerenciar` | Gerenciar estoque e cardápios | merenda |
| `censo.visualizar` | Visualizar dados do Censo | censo |
| `censo.exportar` | Exportar dados para Educacenso | censo |
| `bi.visualizar` | Visualizar dashboard de BI | bi |
| `bi.exportar` | Exportar relatórios de BI | bi |

---

## ✅ PRÓXIMOS PASSOS IMEDIATOS

1. **Aprovar este plano** com o usuário
2. **Começar pela Fase 1** (Dashboards por Perfil) - menor esforço, maior impacto visual
3. **Criar branch** para cada fase de desenvolvimento
4. **Documentar** cada módulo conforme implementado

---

> **Autor**: GitHub Copilot  
> **Data**: 30/11/2025  
> **Versão**: 1.0
