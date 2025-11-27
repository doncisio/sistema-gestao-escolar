# Sistema de Banco de Questões baseado na BNCC

## 🤝 APRESENTAÇÃO À SEMED

### Sobre o Projeto

Esta proposta é apresentada pela equipe de desenvolvimento voluntário do **Sistema de Gestão Escolar**, um projeto **100% sem fins lucrativos** que tem como único objetivo o **progresso da educação do município**.

**Características do projeto:**
- ✨ Desenvolvimento **voluntário** e **gratuito**
- 🎯 Foco exclusivo na **melhoria da qualidade educacional**
- 🤝 Construído em **colaboração com educadores** do município
- 🔓 Código aberto e transparente
- 📚 Alinhado às diretrizes da **BNCC** e políticas educacionais nacionais
- 💰 **Sem custos** para o município ou escolas

### Propósito desta Proposta

Submetemos esta proposta à análise da **SEMED** antes de consultarmos a equipe pedagógica, buscando:

1. **Validação institucional** da iniciativa
2. **Alinhamento** com as diretrizes e prioridades da Secretaria
3. **Autorização** para prosseguir com consultas às equipes pedagógicas
4. **Feedback** sobre adequação às necessidades do município
5. **Apoio institucional** para implementação piloto (se aprovado)

---

## 📋 VISÃO GERAL

Sistema para criação, armazenamento, busca e aplicação de questões (avaliações, provas, exercícios) vinculadas às habilidades da BNCC, permitindo que professores criem avaliações alinhadas ao currículo e acompanhem o desenvolvimento de competências dos alunos.

---

## 🎯 OBJETIVOS

### Objetivos Principais
1. **Alinhamento curricular**: Garantir que todas as questões estejam vinculadas a habilidades BNCC específicas
2. **Facilitação do trabalho docente**: Reduzir tempo de elaboração de avaliações
3. **Progressão de aprendizagem**: Permitir acompanhamento da evolução do aluno por habilidade
4. **Banco colaborativo**: Professores podem compartilhar e reutilizar questões de qualidade
5. **Análise pedagógica**: Identificar habilidades com maior/menor domínio por turma/aluno

### Benefícios
- ✅ Avaliações sempre alinhadas à BNCC
- ✅ Redução de retrabalho (reutilização de questões)
- ✅ Diagnóstico preciso de dificuldades por habilidade
- ✅ Geração automática de provas com critérios pedagógicos
- ✅ Relatórios de desempenho por competência/habilidade
- ✅ Integração com planejamento de aulas
- ✅ **Sistema offline-first**: funciona sem necessidade de dispositivos móveis dos alunos

---

## 🏆 BENEFÍCIOS PARA O MUNICÍPIO E REDE DE ENSINO

### Para a Gestão Educacional (SEMED)

1. **Indicadores de Qualidade**
   - Dados consolidados sobre desempenho por habilidade BNCC
   - Identificação de escolas que necessitam apoio pedagógico específico
   - Relatórios gerenciais para tomada de decisão
   - Acompanhamento de metas e objetivos educacionais

2. **Alinhamento Curricular**
   - Garantia de cobertura das habilidades BNCC em toda rede
   - Padronização de critérios avaliativos
   - Facilita avaliações diagnósticas municipais
   - Suporte a políticas de equidade educacional

3. **Economia de Recursos**
   - Sem custos de licenciamento ou mensalidades
   - Redução de gastos com cópias e impressões
   - Otimização do tempo pedagógico
   - Reutilização de materiais de qualidade

4. **Transparência e Accountability**
   - Rastreabilidade das avaliações
   - Dados objetivos para prestação de contas
   - Evidências de alinhamento às políticas nacionais

### Para as Escolas

1. **Autonomia Pedagógica**
   - Professores criam e adaptam questões à realidade local
   - Banco próprio de materiais avaliativos
   - Compartilhamento interno facilitado

2. **Qualidade das Avaliações**
   - Questões revisadas e validadas
   - Estatísticas de desempenho para ajustes
   - Diversidade de tipos e níveis de questões

3. **Eficiência Administrativa**
   - Geração automatizada de provas
   - Correção facilitada (questões objetivas)
   - Relatórios prontos para conselhos de classe

### Para os Professores

1. **Redução de Carga de Trabalho**
   - Menos tempo elaborando questões do zero
   - Reutilização de questões aprovadas
   - Geração automática de avaliações

2. **Apoio Pedagógico**
   - Sugestões de questões por habilidade
   - Banco colaborativo com colegas
   - Recursos didáticos integrados

3. **Desenvolvimento Profissional**
   - Análise de dados para reflexão sobre prática
   - Compartilhamento de boas práticas
   - Feedback sobre efetividade das questões

### Para os Estudantes

1. **Aprendizagem de Qualidade**
   - Avaliações bem elaboradas e justas
   - Feedback específico por habilidade
   - Identificação precisa de dificuldades

2. **Progressão Clara**
   - Acompanhamento da evolução em cada habilidade
   - Intervenções pedagógicas direcionadas
   - Reconhecimento de avanços

---

## 🗄️ ESTRUTURA DO BANCO DE DADOS

### 1. Tabela: `questoes`
Armazena as questões do banco.

```sql
CREATE TABLE questoes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(50) UNIQUE DEFAULT NULL COMMENT 'Código único da questão (ex: MAT-EF07MA02-001)',
  
  -- Conteúdo
  enunciado TEXT NOT NULL,
  tipo_questao ENUM('multipla_escolha', 'verdadeiro_falso', 'dissertativa', 'dissertativa_curta', 'associacao', 'lacuna') NOT NULL,
  gabarito_texto TEXT DEFAULT NULL COMMENT 'Resposta esperada para dissertativas',
  nivel_dificuldade ENUM('muito_facil', 'facil', 'medio', 'dificil', 'muito_dificil') DEFAULT 'medio',
  
  -- Vinculação BNCC
  bncc_id BIGINT UNSIGNED NOT NULL COMMENT 'Habilidade principal avaliada',
  bncc_secundarias JSON DEFAULT NULL COMMENT 'Array de IDs de habilidades secundárias',
  
  -- Metadados pedagógicos
  componente_curricular VARCHAR(100) NOT NULL COMMENT 'Matemática, Língua Portuguesa, etc',
  ano_escolar VARCHAR(50) NOT NULL COMMENT '7º ano, 8º ano, etc',
  bimestre TINYINT UNSIGNED DEFAULT NULL COMMENT '1-4',
  unidade_tematica VARCHAR(255) DEFAULT NULL,
  objeto_conhecimento VARCHAR(255) DEFAULT NULL,
  
  -- Classificação
  tags JSON DEFAULT NULL COMMENT 'Array de tags: ["frações", "problemas", "contexto-cotidiano"]',
  area_aplicacao VARCHAR(100) DEFAULT NULL COMMENT 'Simulado, diagnóstica, formativa, somativa',
  contexto VARCHAR(255) DEFAULT NULL COMMENT 'Situação-problema, exercício, desafio',
  
  -- Recursos
  imagem_url VARCHAR(500) DEFAULT NULL COMMENT 'URL da imagem principal (DEPRECATED - usar questoes_arquivos)',
  video_url VARCHAR(500) DEFAULT NULL COMMENT 'URL do vídeo (DEPRECATED - usar questoes_arquivos)',
  anexos JSON DEFAULT NULL COMMENT 'Array de URLs de arquivos anexos (DEPRECATED - usar questoes_arquivos)',
  
  -- Estatísticas de uso
  vezes_aplicada INT UNSIGNED DEFAULT 0,
  taxa_acerto DECIMAL(5,2) DEFAULT NULL COMMENT 'Percentual médio de acerto (0-100)',
  tempo_medio_resposta INT UNSIGNED DEFAULT NULL COMMENT 'Tempo em segundos',
  
  -- Controle
  autor_id BIGINT UNSIGNED NOT NULL COMMENT 'ID do professor que criou',
  revisor_id BIGINT UNSIGNED DEFAULT NULL,
  status ENUM('rascunho', 'revisao', 'aprovada', 'arquivada') DEFAULT 'rascunho',
  visibilidade ENUM('privada', 'escola', 'rede', 'publica') DEFAULT 'privada',
  
  -- Timestamps
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY (id),
  KEY idx_questoes_bncc (bncc_id),
  KEY idx_questoes_componente (componente_curricular),
  KEY idx_questoes_ano (ano_escolar),
  KEY idx_questoes_autor (autor_id),
  KEY idx_questoes_status (status),
  KEY idx_questoes_nivel (nivel_dificuldade),
  FULLTEXT KEY ft_questoes_enunciado (enunciado),
  
  CONSTRAINT fk_questoes_bncc FOREIGN KEY (bncc_id) REFERENCES bncc_habilidades(id),
  CONSTRAINT fk_questoes_autor FOREIGN KEY (autor_id) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 2. Tabela: `questoes_arquivos`
Armazena imagens, vídeos e anexos vinculados a questões e alternativas.

```sql
CREATE TABLE questoes_arquivos (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  questao_id BIGINT UNSIGNED NOT NULL,
  alternativa_id BIGINT UNSIGNED DEFAULT NULL COMMENT 'NULL = arquivo da questão principal',
  
  -- Arquivo
  tipo_arquivo ENUM('imagem', 'video', 'audio', 'documento', 'outro') NOT NULL DEFAULT 'imagem',
  nome_original VARCHAR(255) NOT NULL COMMENT 'Nome do arquivo enviado pelo usuário',
  nome_arquivo VARCHAR(255) NOT NULL COMMENT 'Nome único gerado pelo sistema (com hash)',
  caminho_relativo VARCHAR(500) NOT NULL COMMENT 'uploads/questoes/2025/11/abc123.jpg',
  tamanho_bytes INT UNSIGNED NOT NULL,
  mime_type VARCHAR(100) NOT NULL COMMENT 'image/jpeg, video/mp4, etc',
  
  -- Metadados (para imagens)
  largura INT UNSIGNED DEFAULT NULL,
  altura INT UNSIGNED DEFAULT NULL,
  
---

### 4. Tabela: `avaliacoes` COMMENT 'Texto alternativo / descrição da imagem',
  
  uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  uploaded_by BIGINT UNSIGNED NOT NULL,
  
  PRIMARY KEY (id),
  KEY idx_arquivo_questao (questao_id),
  KEY idx_arquivo_alternativa (alternativa_id),
  KEY idx_arquivo_tipo (tipo_arquivo),
  
  CONSTRAINT fk_arquivo_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
  CONSTRAINT fk_arquivo_alternativa FOREIGN KEY (alternativa_id) REFERENCES questoes_alternativas(id) ON DELETE CASCADE,
  CONSTRAINT fk_arquivo_uploader FOREIGN KEY (uploaded_by) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índice para buscar todos os arquivos de uma questão (incluindo alternativas)
CREATE INDEX idx_arquivo_questao_completo ON questoes_arquivos(questao_id, alternativa_id, posicao);
```

**Exemplos de uso**:
- **Imagem no enunciado**: `questao_id=123, alternativa_id=NULL, tipo_arquivo='imagem'`
- **Imagem na alternativa A**: `questao_id=123, alternativa_id=456, tipo_arquivo='imagem'`
- **Múltiplas imagens**: usar campo `posicao` (1, 2, 3...)
- **Vídeo explicativo**: `tipo_arquivo='video'`

---

### 3. Tabela: `questoes_alternativas`
Para questões de múltipla escolha.

```sql
CREATE TABLE questoes_alternativas (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  questao_id BIGINT UNSIGNED NOT NULL,
  letra CHAR(1) NOT NULL COMMENT 'A, B, C, D, E',
  texto TEXT NOT NULL,
  correta BOOLEAN NOT NULL DEFAULT FALSE,
  feedback TEXT DEFAULT NULL COMMENT 'Explicação do porquê está certa/errada',
  ordem TINYINT UNSIGNED NOT NULL DEFAULT 0,
  
  PRIMARY KEY (id),
  UNIQUE KEY uk_questao_letra (questao_id, letra),
  KEY idx_alt_correta (questao_id, correta),
  
  CONSTRAINT fk_alt_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```
---

### 5. Tabela: `avaliacoes_questoes`
### 3. Tabela: `avaliacoes`
Provas/testes compostos por múltiplas questões.

```sql
CREATE TABLE avaliacoes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  titulo VARCHAR(255) NOT NULL,
  descricao TEXT DEFAULT NULL,
  
  -- Configuração
  tipo_avaliacao ENUM('diagnostica', 'formativa', 'somativa', 'simulado', 'recuperacao') NOT NULL,
  componente_curricular VARCHAR(100) NOT NULL,
  ano_escolar VARCHAR(50) NOT NULL,
  bimestre TINYINT UNSIGNED DEFAULT NULL,
  
  -- Pontuação
  pontuacao_total DECIMAL(6,2) NOT NULL DEFAULT 10.00,
  nota_minima_aprovacao DECIMAL(6,2) DEFAULT NULL,
  
  -- Tempo
  tempo_limite INT UNSIGNED DEFAULT NULL COMMENT 'Tempo em minutos',
---

### 6. Tabela: `avaliacoes_aplicadas`
  -- Configurações de aplicação
  embaralhar_questoes BOOLEAN DEFAULT FALSE,
  embaralhar_alternativas BOOLEAN DEFAULT FALSE,
  mostrar_gabarito BOOLEAN DEFAULT FALSE,
  mostrar_feedback BOOLEAN DEFAULT FALSE,
  permitir_consulta BOOLEAN DEFAULT FALSE,
  
  -- Controle
  professor_id BIGINT UNSIGNED NOT NULL,
  status ENUM('rascunho', 'agendada', 'em_andamento', 'finalizada', 'arquivada') DEFAULT 'rascunho',
  
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY (id),
  KEY idx_aval_professor (professor_id),
  KEY idx_aval_tipo (tipo_avaliacao),
  KEY idx_aval_data (data_aplicacao),
  
  CONSTRAINT fk_aval_professor FOREIGN KEY (professor_id) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
---

### 7. Tabela: `respostas_alunos`

### 4. Tabela: `avaliacoes_questoes`
Relacionamento N:N entre avaliações e questões.

```sql
CREATE TABLE avaliacoes_questoes (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  avaliacao_id BIGINT UNSIGNED NOT NULL,
  questao_id BIGINT UNSIGNED NOT NULL,
  
  ordem TINYINT UNSIGNED NOT NULL,
  pontuacao DECIMAL(6,2) NOT NULL COMMENT 'Pontos que vale essa questão nesta avaliação',
  obrigatoria BOOLEAN DEFAULT TRUE,
  
  PRIMARY KEY (id),
  UNIQUE KEY uk_aval_questao_ordem (avaliacao_id, ordem),
  KEY idx_aval_questoes (avaliacao_id, questao_id),
  
  CONSTRAINT fk_avq_avaliacao FOREIGN KEY (avaliacao_id) REFERENCES avaliacoes(id) ON DELETE CASCADE,
  CONSTRAINT fk_avq_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 5. Tabela: `avaliacoes_aplicadas`
Registro de aplicação de avaliações para turmas.

```sql
CREATE TABLE avaliacoes_aplicadas (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  avaliacao_id BIGINT UNSIGNED NOT NULL,
  turma_id BIGINT UNSIGNED NOT NULL,
  
  data_inicio DATETIME NOT NULL,
  data_fim DATETIME DEFAULT NULL,
  status ENUM('agendada', 'em_andamento', 'finalizada', 'cancelada') DEFAULT 'agendada',
  
  PRIMARY KEY (id),
  KEY idx_aval_apl_turma (turma_id),
  KEY idx_aval_apl_status (status),
---

### 8. Tabela: `questoes_favoritas`IGN KEY (turma_id) REFERENCES turmas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 6. Tabela: `respostas_alunos`
Respostas dos alunos às questões.

```sql
CREATE TABLE respostas_alunos (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  avaliacao_aplicada_id BIGINT UNSIGNED NOT NULL,
  aluno_id BIGINT UNSIGNED NOT NULL,
  questao_id BIGINT UNSIGNED NOT NULL,
  
  -- Resposta
  resposta_texto TEXT DEFAULT NULL COMMENT 'Para dissertativas',
  alternativa_escolhida CHAR(1) DEFAULT NULL COMMENT 'A, B, C, D, E para múltipla escolha',
  
  -- Correção
  correta BOOLEAN DEFAULT NULL COMMENT 'NULL = não corrigida, TRUE/FALSE = corrigida',
  pontos_obtidos DECIMAL(6,2) DEFAULT NULL,
  feedback_professor TEXT DEFAULT NULL,
  
  -- Timestamps
  iniciada_em DATETIME DEFAULT NULL,
  respondida_em DATETIME DEFAULT NULL,
  corrigida_em DATETIME DEFAULT NULL,
  corrigida_por BIGINT UNSIGNED DEFAULT NULL,
  
  -- Metadados
  tempo_resposta INT UNSIGNED DEFAULT NULL COMMENT 'Tempo em segundos',
  tentativas TINYINT UNSIGNED DEFAULT 1,
  
  PRIMARY KEY (id),
  UNIQUE KEY uk_resposta_aluno_questao (avaliacao_aplicada_id, aluno_id, questao_id),
  KEY idx_resp_aluno (aluno_id),
  KEY idx_resp_questao (questao_id),
  KEY idx_resp_correta (correta),
  
  CONSTRAINT fk_resp_aval_aplicada FOREIGN KEY (avaliacao_aplicada_id) REFERENCES avaliacoes_aplicadas(id),
  CONSTRAINT fk_resp_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id),
  CONSTRAINT fk_resp_questao FOREIGN KEY (questao_id) REFERENCES questoes(id),
  CONSTRAINT fk_resp_corretor FOREIGN KEY (corrigida_por) REFERENCES funcionarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

### 7. Tabela: `questoes_favoritas`
Professores podem favoritar questões para acesso rápido.

```sql
CREATE TABLE questoes_favoritas (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  questao_id BIGINT UNSIGNED NOT NULL,
  professor_id BIGINT UNSIGNED NOT NULL,
  pasta VARCHAR(100) DEFAULT NULL COMMENT 'Organização em pastas',
  anotacoes TEXT DEFAULT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY (id),
  UNIQUE KEY uk_fav_questao_professor (questao_id, professor_id),
  KEY idx_fav_professor (professor_id),
  
  CONSTRAINT fk_fav_questao FOREIGN KEY (questao_id) REFERENCES questoes(id) ON DELETE CASCADE,
  CONSTRAINT fk_fav_professor FOREIGN KEY (professor_id) REFERENCES funcionarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 📁 GESTÃO DE IMAGENS E ARQUIVOS

### Estratégia de Armazenamento

#### **Opção 1: Armazenamento Local (Recomendado para MVP)**

**Estrutura de pastas**:
```
uploads/
├── questoes/
│   ├── 2025/
│   │   ├── 01/
│   │   │   ├── abc123def456_original.jpg
│   │   │   ├── abc123def456_thumb.jpg     (thumbnail 150x150)
│   │   │   ├── abc123def456_medium.jpg    (800px largura)
│   │   │   └── abc123def456_large.jpg     (1200px largura)
│   │   ├── 02/
│   │   └── ...
│   └── 2026/
└── temp/
    └── uploads_pendentes/
```

**Vantagens**:
- ✅ Simples de implementar
- ✅ Sem custos adicionais de cloud
- ✅ Controle total sobre os arquivos
- ✅ Rápido para acessar localmente

**Desvantagens**:
- ⚠️ Requer backup manual
- ⚠️ Não escala para múltiplos servidores (sem NFS/share)
- ⚠️ Precisa dimensionar armazenamento do servidor

---

#### **Opção 2: Armazenamento em Cloud (Produção em escala)**

**Serviços recomendados**:
1. **AWS S3** (pago, robusto)
2. **Google Cloud Storage** (pago, integração fácil)
3. **Azure Blob Storage** (pago)
4. **MinIO** (gratuito, open-source, self-hosted, compatível com S3)

**Estrutura no S3/MinIO**:
```
bucket: sistema-questoes-bncc
├── questoes/
│   ├── 2025/11/abc123def456.jpg
│   ├── 2025/11/abc123def456_thumb.jpg
│   └── ...
```

**Vantagens**:
- ✅ Escalável infinitamente
- ✅ CDN integrado (entrega rápida)
- ✅ Backup automático
- ✅ Redundância geográfica
- ✅ Suporte a múltiplos servidores

**Desvantagens**:
- ⚠️ Custo mensal (variável por GB)
- ⚠️ Dependência de internet
- ⚠️ Complexidade maior na configuração

---

### Fluxo de Upload

#### **1. Upload pelo Professor**

```python
# Pseudocódigo do fluxo

def upload_imagem_questao(file, questao_id, usuario_id):
    """
    1. Validação do arquivo
    """
    # Validar tipo MIME
    if file.mime_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
        raise ValidationError("Tipo de arquivo não suportado")
    
    # Validar tamanho (máx 5MB para imagens)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("Arquivo maior que 5MB")
    
    # Validar dimensões (opcional)
    img = Image.open(file)
    if img.width > 4000 or img.height > 4000:
        raise ValidationError("Imagem muito grande (máx 4000x4000)")
    
    """
    2. Gerar nome único
    """
    # Hash SHA256 do conteúdo + timestamp
    hash_content = hashlib.sha256(file.read()).hexdigest()[:16]
    timestamp = int(time.time())
    extensao = file.filename.split('.')[-1]
    nome_unico = f"{hash_content}_{timestamp}.{extensao}"
    
    """
    3. Criar thumbnails/versões redimensionadas
    """
    versoes = {
        'original': img,
        'large': redimensionar(img, max_width=1200),
        'medium': redimensionar(img, max_width=800),
        'thumb': redimensionar(img, max_width=150, crop_square=True)
    }
    
    """
    4. Salvar arquivos
    """
    ano_mes = datetime.now().strftime('%Y/%m')
    caminho_base = f"uploads/questoes/{ano_mes}"
    
    for versao, imagem in versoes.items():
        if versao == 'original':
            caminho = f"{caminho_base}/{nome_unico}"
        else:
            caminho = f"{caminho_base}/{hash_content}_{timestamp}_{versao}.{extensao}"
        
        # Salvar no filesystem ou S3
        salvar_arquivo(imagem, caminho)
    
    """
    5. Registrar no banco de dados
    """
    arquivo = QuestaoArquivo(
        questao_id=questao_id,
        alternativa_id=None,
        tipo_arquivo='imagem',
        nome_original=file.filename,
        nome_arquivo=nome_unico,
        caminho_relativo=f"questoes/{ano_mes}/{nome_unico}",
        tamanho_bytes=file.size,
        mime_type=file.mime_type,
        largura=img.width,
        altura=img.height,
        posicao=1,
        uploaded_by=usuario_id
    )
    db.session.add(arquivo)
    db.session.commit()
    
    return arquivo.id
```

---

#### **2. Exibição no Frontend**

**HTML com lazy loading**:
```html
<!-- Questão com imagem -->
<div class="questao">
    <h3>Questão 5</h3>
    <p class="enunciado">
        Observe a figura abaixo e responda:
    </p>
    
    <!-- Imagem responsiva -->
    <figure class="questao-imagem">
        <img 
            src="/uploads/questoes/2025/11/abc123_thumb.jpg" 
            data-src="/uploads/questoes/2025/11/abc123_medium.jpg"
            data-full="/uploads/questoes/2025/11/abc123_original.jpg"
            alt="Gráfico de barras mostrando distribuição"
            loading="lazy"
            onclick="ampliarImagem(this)"
            class="img-fluid"
        />
        <figcaption>Figura 1: Distribuição de frequências</figcaption>
    </figure>
    
    <div class="alternativas">
        <!-- Alternativa com imagem -->
        <label>
            <input type="radio" name="q5" value="A">
            <span class="letra">A)</span>
            <img 
                src="/uploads/questoes/2025/11/xyz789_thumb.jpg"
                alt="Alternativa A"
                class="alternativa-img"
            />
        </label>
        <!-- ... outras alternativas ... -->
    </div>
</div>

<script>
// Modal para ampliar imagem
function ampliarImagem(img) {
    const modal = document.getElementById('modal-imagem');
    const modalImg = document.getElementById('img-ampliada');
    modal.style.display = "block";
    modalImg.src = img.dataset.full; // Carrega versão original
}
</script>
```

---

#### **3. Geração de PDF (questões impressas)**

**Considerações**:
- Imagens devem ser **embutidas** no PDF (não referências externas)
- Redimensionar para caber na página (A4)
- Manter proporção original
- Qualidade suficiente para impressão (150-300 DPI)

```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph

def gerar_pdf_avaliacao(avaliacao_id):
    # Buscar questões da avaliação
    questoes = Questao.query.join(AvaliacaoQuestao).filter(
        AvaliacaoQuestao.avaliacao_id == avaliacao_id
    ).all()
    
    # Criar PDF
    pdf = SimpleDocTemplate(f"avaliacao_{avaliacao_id}.pdf", pagesize=A4)
    elementos = []
    
    for i, questao in enumerate(questoes):
        # Enunciado
        elementos.append(Paragraph(f"<b>Questão {i+1}</b>"))
        elementos.append(Paragraph(questao.enunciado))
        
        # Imagens da questão
        arquivos = QuestaoArquivo.query.filter_by(
            questao_id=questao.id,
            alternativa_id=None,
            tipo_arquivo='imagem'
        ).order_by(QuestaoArquivo.posicao).all()
        
        for arquivo in arquivos:
            # Usar versão 'medium' para PDF (equilíbrio tamanho/qualidade)
            caminho_img = f"uploads/{arquivo.caminho_relativo.replace(arquivo.nome_arquivo, arquivo.nome_arquivo.replace('.', '_medium.'))}"
            
            # Redimensionar para caber na largura da página (com margem)
            img = Image(caminho_img, width=450, height=None, kind='proportional')
            elementos.append(img)
            
            if arquivo.legenda:
                elementos.append(Paragraph(f"<i>{arquivo.legenda}</i>"))
        
        # Alternativas (se houver)
        # ...
    
    pdf.build(elementos)
```

---

### Otimizações de Performance

#### **1. Lazy Loading**
- Carregar thumbnails primeiro
- Carregar imagens full-size apenas quando necessário (scroll, clique)

#### **2. Cache de Imagens**
```python
# Configurar cache HTTP no servidor (nginx/apache)
# Exemplo nginx:
location /uploads/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

#### **3. WebP para Web, JPEG para PDF**
- Converter para WebP no upload (menor tamanho, mesma qualidade)
- Manter JPEG/PNG original para PDFs (compatibilidade)

```python
from PIL import Image

def converter_para_webp(caminho_original):
    img = Image.open(caminho_original)
    caminho_webp = caminho_original.rsplit('.', 1)[0] + '.webp'
    img.save(caminho_webp, 'webp', quality=85)
    return caminho_webp
```

#### **4. CDN (Produção)**
- Usar CloudFlare, AWS CloudFront ou similar
- Cachear imagens globalmente
- Reduz latência e carga no servidor

---

### Segurança

#### **1. Validação Rigorosa**
```python
ALLOWED_MIME_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp'],
    'application/pdf': ['.pdf'],  # Para anexos
}

MAX_FILE_SIZE = {
    'imagem': 5 * 1024 * 1024,      # 5MB
    'video': 50 * 1024 * 1024,      # 50MB
    'documento': 10 * 1024 * 1024,  # 10MB
}

def validar_arquivo(file):
    # Verificar extensão
    ext = file.filename.rsplit('.', 1)[-1].lower()
    
    # Verificar MIME type real (não confiar no que cliente envia)
    mime = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # Voltar ao início
    
    if mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Tipo {mime} não permitido")
    
    if f".{ext}" not in ALLOWED_MIME_TYPES[mime]:
        raise ValidationError("Extensão não corresponde ao tipo de arquivo")
    
    # Verificar tamanho
    file.seek(0, 2)  # Ir para o final
    size = file.tell()
    file.seek(0)  # Voltar ao início
    
    if size > MAX_FILE_SIZE['imagem']:
        raise ValidationError("Arquivo muito grande")
```

#### **2. Isolamento de Arquivos**
- **NUNCA** permitir acesso direto a uploads via URL previsível
**Recursos Adicionais**:
- **PDFs**: ReportLab ou WeasyPrint
- **Imagens**: Pillow (PIL) para processamento e redimensionamento
- **Upload**: Flask-Uploads ou Django-Storages
- **Thumbnails**: sorl-thumbnail (Django) ou Flask-Thumbnails
- **Storage Cloud**: boto3 (AWS S3) ou google-cloud-storage
- **Storage Local**: MinIO (compatível S3, self-hosted)
- **Validação MIME**: python-magic
- **OCR (futuro)**: Tesseract OCR + pytesseract
- **IA (futuro)**: OpenAI API ou modelos locais (Llama, GPT)
def servir_imagem_questao(arquivo_id):
    arquivo = QuestaoArquivo.query.get_or_404(arquivo_id)
    questao = arquivo.questao
    
    # Verificar permissão
    if not usuario_pode_ver_questao(current_user, questao):
        abort(403)
    
    # Servir arquivo
    return send_file(
        f"uploads/{arquivo.caminho_relativo}",
        mimetype=arquivo.mime_type
    )
```

#### **3. Sanitização de Nomes**
```python
import re
from werkzeug.utils import secure_filename

def sanitizar_nome_arquivo(filename):
    # Remove caracteres especiais
    filename = secure_filename(filename)
    # Remove acentos
    filename = unidecode(filename)
    # Apenas alfanuméricos, hífen e underscore
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return filename
```

---

### Backup e Recuperação

#### **Estratégia de Backup**

**Opção 1: Backup Local**
```bash
# Cron diário (00:00)
0 0 * * * rsync -av /var/www/uploads/ /mnt/backup/uploads_$(date +\%Y\%m\%d)/
```

**Opção 2: Backup para Cloud**
```bash
# Sync com S3 (AWS CLI)
0 2 * * * aws s3 sync /var/www/uploads/ s3://backup-questoes-bncc/uploads/
```

**Opção 3: Backup Incremental (Duplicity)**
```bash
duplicity /var/www/uploads file:///mnt/backup/duplicity/uploads
```

#### **Retenção**:
- Diário: últimos 7 dias
- Semanal: últimos 4 semanas
- Mensal: últimos 12 meses

---

### Migração de Dados

Se já existem imagens em `imagem_url` (VARCHAR):

```sql
-- Migração de dados antigos
INSERT INTO questoes_arquivos (
    questao_id, 
    alternativa_id,
    tipo_arquivo,
    nome_original,
    nome_arquivo,
    caminho_relativo,
    tamanho_bytes,
    mime_type,
    uploaded_by,
    uploaded_at
)
SELECT 
    id,
    NULL,
    'imagem',
    SUBSTRING_INDEX(imagem_url, '/', -1),  -- Nome do arquivo
    SUBSTRING_INDEX(imagem_url, '/', -1),
    REPLACE(imagem_url, '/uploads/', ''),  -- Caminho relativo
    0,  -- Tamanho desconhecido (preencher depois)
    'image/jpeg',  -- Assumir JPEG (validar depois)
    autor_id,
    created_at
FROM questoes
WHERE imagem_url IS NOT NULL AND imagem_url != '';
```

---

### Interface de Upload

**HTML do formulário**:
```html
<div class="upload-area">
    <label for="imagem-questao">Adicionar Imagem</label>
    <input 
        type="file" 
        id="imagem-questao" 
        accept="image/jpeg,image/png,image/gif,image/webp"
        multiple
    />
    <div class="preview-area" id="preview-imagens">
        <!-- Previews aparecem aqui -->
    </div>
</div>

<script>
document.getElementById('imagem-questao').addEventListener('change', function(e) {
    const files = e.target.files;
    const preview = document.getElementById('preview-imagens');
    preview.innerHTML = '';
    
    for (let file of files) {
        // Validar tamanho
        if (file.size > 5 * 1024 * 1024) {
            alert(`${file.name} é muito grande (máx 5MB)`);
            continue;
        }
        
        // Preview
        const reader = new FileReader();
        reader.onload = function(event) {
            const img = document.createElement('img');
            img.src = event.target.result;
            img.style.maxWidth = '200px';
            preview.appendChild(img);
        };
        reader.readAsDataURL(file);
        
        // Upload via AJAX
        const formData = new FormData();
        formData.append('imagem', file);
        formData.append('questao_id', questaoId);
        
        fetch('/api/questoes/upload-imagem', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Upload concluído:', data.arquivo_id);
        });
    }
});
</script>
```

---

## 🔍 FUNCIONALIDADES PRINCIPAIS

### 1. **Cadastro de Questões**
**Fluxo**:
1. Professor seleciona componente curricular e ano escolar
2. Sistema sugere habilidades BNCC relevantes
3. Professor vincula habilidade(s) à questão
4. Preenche enunciado, tipo, alternativas (se aplicável), gabarito
5. Define metadados: dificuldade, tags, contexto
6. Salva como rascunho ou submete para revisão

**Recursos**:
- ✅ Editor de texto rico (negrito, itálico, fórmulas matemáticas)
- ✅ Upload de imagens/anexos
- ✅ Pré-visualização da questão
- ✅ Validação de gabarito (obrigatório)
- ✅ Sugestão de tags baseadas no conteúdo (IA/ML)

---

### 2. **Busca e Filtros Avançados**

**Critérios de busca**:
- Habilidade BNCC (código ou descrição)
- Componente curricular
- Ano escolar
- Nível de dificuldade
- Tipo de questão
- Tags
- Autor
- Taxa de acerto (faixa)
- Texto livre (busca no enunciado)

**Exemplo de interface**:
```
┌─────────────────────────────────────────┐
│ Buscar Questões                         │
├─────────────────────────────────────────┤
│ Componente: [Matemática ▼]              │
│ Ano: [7º ano ▼]                         │
│ Habilidade BNCC: [EF07MA02 - Resolver...│
│ Dificuldade: [Todas ▼]                  │
│ Tipo: [Todas ▼]                         │
│ Tags: [frações] [+]                     │
│ Texto: [________________________________│
│                                         │
│ [Buscar] [Limpar filtros]               │
└─────────────────────────────────────────┘

Resultados: 23 questões encontradas
┌─────────────────────────────────────────┐
│ MAT-EF07MA02-001 | Dificuldade: Média   │
│ "Calcular 30% de R$ 250..."             │
│ Habilidade: EF07MA02 | Tipo: Múlt.Esc.  │
│ Taxa acerto: 78% | Aplicada: 45x        │
│ [Ver] [Adicionar] [★ Favoritar]         │
└─────────────────────────────────────────┘
```

---

### 3. **Geração Automática de Avaliações**

**Fluxo automatizado**:
1. Professor define:
   - Componente e ano
   - Habilidades a avaliar (ou seleciona "todas do bimestre")
   - Número de questões por habilidade
   - Distribuição de dificuldade (ex: 30% fácil, 50% média, 20% difícil)
   - Tipos de questão (ex: 80% múltipla escolha, 20% dissertativa)
   - Pontuação total
2. Sistema gera automaticamente selecionando questões que atendem aos critérios
3. Professor revisa, pode substituir questões manualmente
4. Salva e aplica à(s) turma(s)

**Algoritmo de seleção**:
- Priorizar questões com boa taxa de acerto (não muito fácil/difícil)
- Evitar questões já aplicadas recentemente para a mesma turma
- Balancear diversidade de contextos/tags
- Garantir cobertura de todas as habilidades solicitadas

---

### 4. **Aplicação de Avaliações**

**Modo de aplicação: IMPRESSO (offline)**

> ⚠️ **Importante**: Considerando a política da rede de ensino que proíbe uso de celular/tablet na escola, o sistema foi projetado para funcionar 100% no formato impresso, com gestão e análise feitas pelos professores via sistema web.

**Fluxo de aplicação**:
1. **Professor**: monta avaliação no sistema (via computador)
2. **Sistema**: gera PDF formatado e otimizado para impressão
3. **Secretaria/Coordenação**: imprime avaliações
4. **Alunos**: respondem em papel (formato tradicional)
5. **Professor**: lança resultados no sistema
6. **Sistema**: gera relatórios automáticos de desempenho

**Recursos do modo impresso**:
- ✅ Geração de PDF formatado profissionalmente (A4)
- ✅ Versões embaralhadas (A, B, C, D) para evitar cópia
- ✅ Folha de respostas para leitura ótica (opcional, futuro)
- ✅ Cabeçalho personalizado (escola, turma, data, instruções)
- ✅ Espaço adequado para respostas dissertativas
- ✅ Gabarito do professor em arquivo separado
- ✅ Layout responsivo (adapta questões longas)
- ✅ Qualidade de impressão otimizada (economia de tinta)

---

### 5. **Correção e Lançamento de Resultados**

**Fluxo de correção (formato impresso)**:

**Múltipla escolha**:
1. Professor corrige provas com gabarito impresso
2. Lança respostas dos alunos no sistema via interface web
3. Sistema calcula automaticamente:
   - Pontuação por questão
   - Nota final
   - Estatísticas por alternativa (quantos escolheram A, B, C, D, E)
   - Desempenho por habilidade BNCC

**Interface de lançamento de notas (múltipla escolha)**:
- ✅ Tela otimizada: digita-se apenas a letra marcada por cada aluno
- ✅ Atalhos de teclado para agilizar (A, B, C, D, E + Enter)
- ✅ Validação automática (alertas para questões não preenchidas)
- ✅ Progresso visual (quantos alunos faltam)
- ✅ Salvamento automático a cada aluno

**Dissertativas**:
1. Professor corrige provas fisicamente (escrita em papel)
2. Lança pontuações no sistema via interface web:
   - Gabarito sugerido exibido ao lado
   - Campo para pontuação parcial
   - Campo para feedback individualizado (opcional)
   - Opção de usar rubrica/critérios pré-definidos
3. Sistema registra e gera estatísticas

**Recursos para agilizar correção**:
- ✅ Correção em lote (lançar notas de toda a turma)
- ✅ Comentários padrão salvos (reutilização de feedbacks comuns)
- ✅ Correção por questão (corrigir questão 1 de todos os alunos, depois questão 2, etc.)
- ✅ Modo offline: lançar notas mesmo sem internet (sincroniza depois)

---

### 6. **Relatórios e Análises**

#### A) **Relatório por Aluno**
```
Aluno: João Silva | 7º Ano B | Matemática | 2º Bimestre

┌──────────────────────────────────────────────────────────┐
│ Avaliação: Prova Bimestral - 15/10/2025                 │
│ Nota: 7.5/10.0 | Acertos: 8/12 questões                 │
├──────────────────────────────────────────────────────────┤
│ DESEMPENHO POR HABILIDADE:                               │
│                                                          │
│ EF07MA02 (Porcentagens)          ████████░░ 80% (4/5)   │
│ EF07MA10 (Álgebra)               ███░░░░░░░ 33% (1/3)   │
│ EF07MA15 (Estatística)           ██████████ 100% (3/3)  │
│ EF07MA22 (Geometria)             ░░░░░░░░░░  0% (0/1)   │
├──────────────────────────────────────────────────────────┤
│ DIFICULDADES IDENTIFICADAS:                              │
│ • Álgebra: resolução de equações                        │
│ • Geometria: construção de figuras                      │
│                                                          │
│ RECOMENDAÇÕES:                                           │
│ • Exercícios extras: EF07MA10                           │
│ • Recuperação paralela: Geometria básica                │
└──────────────────────────────────────────────────────────┘
```

#### B) **Relatório por Turma**
```
Turma: 7º Ano B | Professor: Maria Santos | Matemática

┌──────────────────────────────────────────────────────────┐
│ Avaliação: Prova Bimestral - 15/10/2025                 │
│ Média da turma: 6.8/10.0 | Aprovação: 72% (23/32 alunos)│
├──────────────────────────────────────────────────────────┤
│ HABILIDADES COM MAIOR DIFICULDADE:                       │
│                                                          │
│ 1. EF07MA10 (Álgebra)           Taxa acerto: 45%        │
│    → 18 alunos abaixo da média                          │
│                                                          │
│ 2. EF07MA22 (Geometria)         Taxa acerto: 52%        │
│    → 15 alunos abaixo da média                          │
│                                                          │
│ HABILIDADES BEM CONSOLIDADAS:                            │
│                                                          │
│ 1. EF07MA15 (Estatística)       Taxa acerto: 88%        │
│ 2. EF07MA02 (Porcentagens)      Taxa acerto: 81%        │
├──────────────────────────────────────────────────────────┤
│ AÇÕES SUGERIDAS:                                         │
│ • Aula de reforço: Álgebra (foco em equações)          │
│ • Material complementar: Geometria espacial             │
│ • Recuperação para 9 alunos com nota < 5.0              │
└──────────────────────────────────────────────────────────┘
```

#### C) **Relatório por Questão**
- Taxa de acerto
- Tempo médio de resposta
- Distribuição de escolha por alternativa (múltipla escolha)
- Identificar questões problemáticas (muito fácil/difícil/ambígua)

---

## 🚀 FUNCIONALIDADES AVANÇADAS (FUTURAS)

### 1. **Importação de Questões Externas**
- Parser de PDFs de provas (OCR + IA)
- Importação de bancos do MEC/INEP
- Integração com plataformas (Khan Academy, Google Forms)

### 2. **Inteligência Artificial**
- **Sugestão de questões**: baseado em histórico do aluno/turma
- **Geração automática**: IA cria questões baseadas em habilidades BNCC
- **Correção assistida**: sugestão de pontuação para dissertativas
- **Detecção de plágio**: entre respostas de alunos
- **Análise de dificuldade**: predição de taxa de acerto antes da aplicação

### 3. **Relatórios Visuais e Certificados**
- Certificados de conquista de habilidades para alunos (impressos)
- Gráficos de progressão individual (para reuniões com pais)
- Relatórios comparativos de turmas
- Mapas de calor de desempenho por habilidade

### 4. **Personalização e Recuperação**
- Geração automática de listas de exercícios personalizadas para recuperação
- Sugestão de questões baseadas em dificuldades identificadas nas avaliações
- Banco de exercícios extras por habilidade para impressão

### 5. **Colaboração**
- Banco compartilhado entre escolas da rede
- Sistema de revisão por pares
- Comentários e avaliações de questões por outros professores
- Ranking de qualidade de questões (baseado em uso + feedback)

### 6. **Integração com Planejamento**
- Vincular questões ao plano de aula
- Sugerir questões ao criar planejamento semanal
- Dashboard unificado: planejamento → aplicação → correção → análise

---

## 🎨 INTERFACE DO USUÁRIO

### Telas Principais

#### 1. **Dashboard Professor**
```
┌─────────────────────────────────────────────────────────┐
│ Banco de Questões                              [Ajuda]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [📝 Nova Questão] [📄 Nova Avaliação] [⭐ Favoritas]   │
│                                                         │
│ MINHAS ESTATÍSTICAS:                                    │
│ ┌───────────┬───────────┬───────────┬───────────┐      │
│ │ Questões  │ Avaliações│ Aplicadas │Taxa Acerto│      │
│ │    47     │     8     │    23     │   76.5%   │      │
│ └───────────┴───────────┴───────────┴───────────┘      │
│                                                         │
│ AVISOS:                                                 │
│ • 3 avaliações pendentes de correção                   │
│ • 12 questões em revisão                               │
│                                                         │
│ ATALHOS RÁPIDOS:                                        │
│ [🔍 Buscar Questões] [📊 Relatórios] [👥 Minha Turma]  │
└─────────────────────────────────────────────────────────┘
```

#### 2. **Criar/Editar Questão**
```
┌─────────────────────────────────────────────────────────┐
│ Nova Questão                           [Salvar] [Cancelar]
├─────────────────────────────────────────────────────────┤
│ Componente: [Matemática ▼]  Ano: [7º ano ▼]            │
│                                                         │
│ Habilidade BNCC: [Buscar...]                            │
│ ✓ EF07MA02 - Resolver e elaborar problemas...          │
│ + Adicionar habilidade secundária                       │
│                                                         │
│ Tipo: ( ) Múltipla Escolha (•) Dissertativa ( ) V/F    │
│ Dificuldade: [Média ▼]                                  │
│                                                         │
│ Enunciado:                                              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [B] [I] [U] [∑] [📷] [📎]                            │ │
│ │                                                     │ │
│ │ Em uma loja, um produto custa R$ 250,00. Durante   │ │
│ │ uma promoção, o preço teve um desconto de 30%.     │ │
│ │ Qual o valor final do produto?                     │ │
│ │                                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Alternativas:                                           │
│ (•) A) R$ 75,00                                         │
│ ( ) B) R$ 175,00    [✏️ Feedback]                       │
│ ( ) C) R$ 220,00                                        │
│ ( ) D) R$ 280,00                                        │
│                                                         │
│ Tags: [porcentagem] [desconto] [problema] [+]          │
│ Contexto: [Situação cotidiana ▼]                        │
│                                                         │
│ [Pré-visualizar] [Salvar Rascunho] [Enviar p/ Revisão] │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 MÉTRICAS DE QUALIDADE

### Questões
- **Taxa de uso**: questões nunca usadas podem ser de baixa qualidade
- **Taxa de acerto média**: questões com 0% ou 100% precisam revisão
- **Tempo médio**: identificar questões muito longas/curtas
- **Feedback de professores**: avaliações e comentários

### Avaliações
- **Distribuição de notas**: curva normal esperada
- **Consistência interna**: correlação entre questões (Alpha de Cronbach)
- **Poder discriminatório**: questões que separam bons/maus alunos

---

## 🔒 SEGURANÇA E PRIVACIDADE

### Controles de Acesso
- **Professores**: criar/editar questões próprias, buscar aprovadas
- **Coordenadores**: revisar/aprovar questões, acessar banco completo
- **Alunos**: apenas responder questões de avaliações aplicadas
- **Administradores**: acesso total

### Visibilidade de Questões
1. **Privada**: apenas autor vê
2. **Escola**: professores da mesma escola
3. **Rede**: professores de toda a rede municipal/estadual
4. **Pública**: qualquer professor cadastrado

### Proteção de Conteúdo
- Watermark em questões compartilhadas
- Log de acesso e uso
- Versionamento de questões (histórico de edições)

---

## 🛠️ IMPLEMENTAÇÃO TÉCNICA

### Stack Recomendada
**Backend**:
- Python + Flask/Django (já em uso no sistema)
- MySQL (estrutura já existente)
- Celery para tarefas assíncronas (geração de PDFs, relatórios)

**Frontend**:
- HTML5 + CSS3 + JavaScript
- Editor WYSIWYG: TinyMCE ou CKEditor
- Charts: Chart.js ou D3.js
- Framework: Bootstrap ou Tailwind CSS

**Recursos Adicionais**:
- **PDFs**: ReportLab ou WeasyPrint
- **Imagens**: Pillow para processamento
- **OCR (futuro)**: Tesseract OCR
- **IA (futuro)**: OpenAI API ou modelos locais (Llama, GPT)

### Módulos Python

```
banco_questoes/
├── __init__.py
├── models/
│   ├── questao.py
│   ├── avaliacao.py
│   ├── resposta.py
│   └── relatorio.py
├── controllers/
│   ├── questoes_controller.py
│   ├── avaliacoes_controller.py
│   ├── correcao_controller.py
│   └── relatorios_controller.py
├── services/
│   ├── busca_service.py          # Busca e filtros
│   ├── geracao_automatica.py     # Gerador de provas
│   ├── correcao_service.py       # Lógica de correção
│   ├── estatisticas_service.py   # Cálculos estatísticos
│   └── pdf_service.py            # Geração de PDFs
├── utils/
│   ├── bncc_helper.py            # Integração com tabela BNCC
│   ├── validadores.py
│   └── formatadores.py
└── views/
    ├── questoes.html
    ├── avaliacoes.html
    ├── correcao.html
    └── relatorios.html
```

---

## 📅 ROADMAP DE IMPLEMENTAÇÃO

### Fase 1 - MVP (2-3 meses)
✅ Estrutura do banco de dados  
✅ CRUD de questões (múltipla escolha apenas)  
✅ Busca básica (por habilidade, ano, componente)  
✅ Criação manual de avaliações  
✅ Aplicação impressa (geração de PDF)  
✅ Lançamento manual de notas  
✅ Relatório básico por aluno/turma  

### Fase 2 - Expansão (3-4 meses)
✅ Questões dissertativas  
✅ Correção online para dissertativas  
✅ Geração automática de avaliações  
✅ Filtros avançados de busca  
✅ Sistema de tags e favoritos  
✅ Estatísticas de uso de questões  
✅ Relatórios avançados (por habilidade)  

### Fase 3 - Avançado (4-6 meses)
✅ Interface otimizada para lançamento rápido de notas  
✅ Leitura ótica de folhas de resposta (OMR) via scanner  
✅ Dashboard interativo com gráficos  
✅ Sistema de revisão de questões  
✅ Banco compartilhado entre escolas  
✅ Exportação de relatórios (Excel, PDF)  
✅ Geração de certificados e relatórios visuais para alunos  

### Fase 4 - Inteligência e Integração (6+ meses)
✅ Sugestão inteligente de questões baseada em histórico  
✅ Análise preditiva de desempenho (identificar alunos em risco)  
✅ Importação automática de questões via OCR (scanear provas em papel)  
✅ Geração de listas de recuperação personalizadas  
✅ Integração com planejamento de aulas  
✅ Sistema de recomendação de intervenções pedagógicas  

---

## 💡 DIFERENCIAIS COMPETITIVOS

1. **Alinhamento Total à BNCC**: todas as questões vinculadas a habilidades reais
2. **Análise Pedagógica Profunda**: relatórios por habilidade, não apenas por nota
3. **Banco Colaborativo Local**: professores da rede compartilham conhecimento
4. **Integração com Sistema Existente**: aproveita cadastros, turmas, notas já existentes
5. **100% Compatível com Política da Rede**: sistema projetado para formato impresso, sem necessidade de dispositivos móveis dos alunos
6. **Offline-First**: professores podem trabalhar sem internet, sincroniza depois
7. **Economia de Tempo**: mesmo no formato impresso, reduz tempo de elaboração em 50-70%
8. **Gratuito e Customizável**: software livre, adaptável às necessidades da rede

---

## 🎓 CASOS DE USO PRÁTICOS

### Caso 1: Avaliação Diagnóstica
**Contexto**: Início do ano letivo, professor quer mapear conhecimentos prévios.

**Fluxo**:
1. Professor acessa "Nova Avaliação" → "Diagnóstica"
2. Seleciona "7º ano - Matemática - Habilidades do 6º ano"
3. Sistema gera automaticamente 15 questões cobrindo principais habilidades do ano anterior
4. Professor revisa, ajusta pontuação, aplica à turma
5. Após correção, sistema gera relatório mostrando:
   - Habilidades bem consolidadas na turma
   - Habilidades que precisam ser retomadas
   - Alunos que precisam acompanhamento individualizado

### Caso 2: Prova Bimestral
**Contexto**: Professor precisa elaborar prova bimestral.

**Fluxo**:
1. Professor busca questões filtrando:
   - Habilidades trabalhadas no bimestre (lista pré-definida no planejamento)
   - Dificuldade: 30% fácil, 50% média, 20% difícil
   - Tipos variados: 70% múltipla escolha, 30% dissertativa
2. Sistema sugere 12 questões que atendem aos critérios
3. Professor substitui 2 questões por outras do banco
4. Configura pontuação total (10.0), tempo (90min), permite consulta a fórmulas
5. Gera PDF e aplica impressa
6. Após aplicação, lança notas no sistema
7. Sistema gera automaticamente boletim + relatório de desempenho por habilidade

### Caso 3: Recuperação Paralela
**Contexto**: Aluno com dificuldade em habilidade específica.

**Fluxo**:
1. Sistema identifica automaticamente no relatório: "João tem 30% de acerto em EF07MA10"
2. Professor busca questões: EF07MA10 + dificuldade "fácil" + tipo "exercício"
3. Sistema gera PDF com lista de 10 exercícios progressivos
4. Imprime e aplica individualmente para João
5. João resolve em papel, professor corrige
6. Professor lança resultado no sistema: 7/10 acertos (70%)
7. Sistema registra melhoria e atualiza relatório individual
8. Professor marca habilidade como "em recuperação bem-sucedida"

---

## 📚 RECURSOS COMPLEMENTARES

### Tutoriais
- Vídeo: "Como criar sua primeira questão"
- PDF: "Boas práticas na elaboração de questões"
- FAQ: Dúvidas frequentes

### Banco de Exemplos
- 100 questões modelo por componente curricular
- Questões comentadas (o que torna uma questão boa/ruim)
- Gabaritos comentados

### Comunidade
- Fórum de discussão entre professores
- Sessões de formação continuada sobre avaliação
- Grupos de trabalho para criação colaborativa

---

## ✅ CHECKLIST DE VALIDAÇÃO

Antes de lançar, validar:

- [ ] Todas as habilidades BNCC estão cadastradas e corretas
- [ ] Sistema suporta todos os componentes curriculares da escola
- [ ] Geração de PDF está formatada corretamente
- [ ] Correção automática funciona 100%
- [ ] Relatórios apresentam dados precisos
- [ ] Performance: busca com 1000+ questões é rápida (<2s)
- [ ] Backup automático de questões e respostas
- [ ] Treinamento de professores concluído
- [ ] Manual do usuário disponível
- [ ] Suporte técnico configurado

---

## 🎯 INDICADORES DE SUCESSO

### KPIs Operacionais
- **Adoção**: 80% dos professores usam o sistema regularmente
- **Engajamento**: média de 5+ questões criadas por professor/mês
- **Qualidade**: 90% das questões com taxa de acerto entre 40-80%
- **Eficiência**: redução de 50% no tempo de elaboração de provas

### KPIs Pedagógicos
- **Alinhamento**: 100% das avaliações vinculadas a habilidades BNCC
- **Diagnóstico**: identificação precoce de dificuldades em 90% dos casos
- **Recuperação**: melhoria de 30% em notas após uso de relatórios
- **Progressão**: aumento de 15% na taxa de aprovação anual

---

## 📖 CONCLUSÃO

O **Sistema de Banco de Questões baseado na BNCC** é uma ferramenta estratégica para:

1. **Garantir qualidade pedagógica**: avaliações sempre alinhadas ao currículo
2. **Empoderar professores**: menos tempo administrativo, mais tempo pedagógico
3. **Personalizar aprendizagem**: diagnóstico preciso de dificuldades individuais
4. **Valorizar o conhecimento coletivo**: banco colaborativo entre docentes
5. **Tomar decisões baseadas em dados**: relatórios precisos guiam intervenções

**Próximo passo**: Validar escopo com equipe pedagógica e iniciar Fase 1 (MVP).

---

---

# 💬 CONSULTA À EQUIPE PEDAGÓGICA

## Prezados Professores e Coordenadores,

Estamos desenvolvendo um **Sistema de Banco de Questões baseado na BNCC** para nossa rede de ensino, com o objetivo de facilitar a elaboração de avaliações, compartilhar conhecimento entre docentes e acompanhar com precisão o desenvolvimento de competências e habilidades dos nossos alunos.

Antes de iniciarmos a implementação, **gostaríamos muito de ouvir a opinião de vocês**, que são os principais usuários deste sistema. Sua experiência prática e suas necessidades diárias são fundamentais para garantir que o sistema realmente atenda às demandas da nossa rede.

---

## 📋 QUESTÕES PARA REFLEXÃO E FEEDBACK

### 1. **Sobre a Proposta Geral**

**Questão**: Considerando sua experiência atual na elaboração de avaliações, quais são as **principais dificuldades** que você enfrenta no dia a dia?

- [ ] Falta de tempo para criar questões originais
- [ ] Dificuldade em alinhar questões com habilidades BNCC específicas
- [ ] Falta de um repositório organizado de questões
- [ ] Dificuldade em variar o nível de dificuldade
- [ ] Retrabalho (criar questões semelhantes repetidamente)
- [ ] Dificuldade em analisar resultados por habilidade/competência
- [ ] Outro: _________________________________

---

### 2. **Banco Colaborativo de Questões**

**Questão**: Você estaria disposto(a) a **compartilhar questões criadas por você** com outros professores da rede, sabendo que também teria acesso a questões criadas por colegas?

- [ ] **Sim, totalmente**. Acredito que a colaboração enriquece o trabalho de todos.
- [ ] **Sim, mas com restrições**. Por exemplo: apenas após revisão, ou só com professores da mesma escola.
- [ ] **Talvez**. Preciso entender melhor como funcionaria (autoria, créditos, qualidade).
- [ ] **Não**. Prefiro manter minhas questões privadas.

**Comentários adicionais**: ___________________________________________

---

### 3. **Funcionalidades Prioritárias**

**Questão**: Das funcionalidades propostas abaixo, quais você considera **ESSENCIAIS** para o seu trabalho? (Marque até 5)

- [ ] Cadastro de questões com vinculação à BNCC
- [ ] Busca de questões por habilidade/ano/componente
- [ ] Geração automática de avaliações (sistema monta a prova)
- [ ] Geração de PDF formatado para impressão (versões A, B, C, D)
- [ ] Interface rápida para lançamento de notas
- [ ] Relatórios de desempenho por aluno
- [ ] Relatórios de desempenho por turma
- [ ] Análise por habilidade BNCC (quais habilidades a turma domina/não domina)
- [ ] Sistema de favoritos (salvar questões preferidas)
- [ ] Upload de imagens nas questões
- [ ] Banco de questões dissertativas
- [ ] Estatísticas de uso (taxa de acerto, tempo médio)
- [ ] Leitura óptica de folhas de resposta (futuro)
- [ ] Outro: _________________________________

---

### 4. **Tipos de Questões**

**Questão**: Quais **tipos de questões** você mais utiliza em suas avaliações atualmente?

- [ ] Múltipla escolha
- [ ] Verdadeiro ou Falso
- [ ] Dissertativas longas (com desenvolvimento de raciocínio)
- [ ] Dissertativas curtas (respostas objetivas)
- [ ] Associação (ligar colunas)
- [ ] Preencher lacunas
- [ ] Outro: _________________________________

**Qual desses tipos você gostaria de priorizar no sistema?** _________________

---

### 5. **Geração Automática de Avaliações**

**Questão**: Você utilizaria uma funcionalidade que **gera automaticamente uma avaliação** baseada em critérios que você define (ex: "10 questões de Matemática do 7º ano, 50% média e 50% difícil, cobrindo habilidades do 2º bimestre")?

- [ ] **Sim, com certeza!** Isso economizaria muito tempo.
- [ ] **Sim, mas gostaria de revisar e ajustar** antes de aplicar.
- [ ] **Talvez**. Preciso ver como funciona na prática.
- [ ] **Não**. Prefiro selecionar manualmente questão por questão.

**Por quê?** ___________________________________________

---

### 6. **Formato de Aplicação (Impressa)**

> **Nota**: Considerando a política da rede que proíbe uso de celular/tablet, o sistema foi desenvolvido para **formato 100% impresso**.

**Questão**: Quais recursos você considera essenciais na geração de provas impressas?

- [ ] Versões embaralhadas (A, B, C, D) para evitar cópia
- [ ] Cabeçalho personalizado com informações da escola/turma
- [ ] Espaço adequado para respostas dissertativas
- [ ] Folha de respostas separada (tipo gabarito óptico)
- [ ] Gabarito do professor em arquivo separado
- [ ] Layout otimizado (economia de papel/tinta)
- [ ] Instruções claras no topo da prova
- [ ] Outro: _________________________________

**Você teria interesse em sistema de leitura óptica (scanner) para agilizar lançamento de notas futuramente?**

- [ ] Sim, seria muito útil
- [ ] Sim, mas depende do custo
- [ ] Não vejo necessidade
- [ ] Não sei o que é leitura óptica

---

### 7. **Análise de Desempenho por Habilidade BNCC**

**Questão**: Atualmente, você consegue identificar com precisão **quais habilidades da BNCC** seus alunos dominam e quais precisam ser retrabalhadas?

- [ ] **Sim, facilmente**. Tenho controle detalhado.
- [ ] **Parcialmente**. Faço algum acompanhamento, mas é trabalhoso.
- [ ] **Não**. Analiso apenas a nota geral, não por habilidade.

**Você considera importante ter relatórios automáticos mostrando desempenho por habilidade?**

- [ ] Sim, seria extremamente útil
- [ ] Sim, mas não é prioridade
- [ ] Não acho necessário

---

### 8. **Tempo de Elaboração de Avaliações**

**Questão**: Quanto tempo, em média, você leva para **elaborar uma avaliação completa** (buscar/criar questões, formatar, revisar)?

- [ ] Menos de 1 hora
- [ ] 1 a 2 horas
- [ ] 2 a 4 horas
- [ ] 4 a 6 horas
- [ ] Mais de 6 horas

**Com um banco de questões organizado e ferramentas automáticas, quanto tempo você acredita que poderia economizar?**

- [ ] Até 30%
- [ ] 30% a 50%
- [ ] 50% a 70%
- [ ] Mais de 70%

---

### 9. **Capacitação e Treinamento**

**Questão**: Para utilizar um sistema novo como este, você se sentiria confortável com:

- [ ] **Tutorial em vídeo** (5-10 minutos por funcionalidade)
- [ ] **Manual em PDF** (passo a passo com imagens)
- [ ] **Treinamento presencial** (2-4 horas em grupo)
- [ ] **Suporte online** (chat, e-mail, WhatsApp)
- [ ] **Aprendo sozinho(a)** explorando o sistema

**Quanto tempo você estaria disposto(a) a investir em capacitação inicial?**

- [ ] 1 hora
- [ ] 2-3 horas
- [ ] 4-6 horas
- [ ] Mais de 6 horas

---

### 10. **Preocupações e Desafios**

**Questão**: Quais são suas **principais preocupações** em relação à implementação deste sistema?

- [ ] Dificuldade de uso / curva de aprendizado
- [ ] Tempo necessário para cadastrar questões inicialmente
- [ ] Qualidade das questões compartilhadas por outros professores
- [ ] Dependência de tecnologia / internet
- [ ] Privacidade e segurança das informações
- [ ] Resistência à mudança de rotina
- [ ] Outro: _________________________________

**Como o sistema poderia minimizar essas preocupações?**
___________________________________________

---

### 11. **Sugestões e Ideias**

**Questão aberta**: Existe alguma **funcionalidade, recurso ou característica** que você gostaria de ver no sistema e que não foi mencionada nesta proposta?

___________________________________________
___________________________________________
___________________________________________

---

### 12. **Comprometimento com o Projeto**

**Questão**: Você estaria disposto(a) a participar como **usuário piloto** (testador) do sistema nas fases iniciais, fornecendo feedback para melhorias?

- [ ] Sim, tenho interesse em participar ativamente
- [ ] Sim, mas com disponibilidade limitada
- [ ] Talvez, dependendo da demanda de tempo
- [ ] Não tenho disponibilidade no momento

---

## 📝 INFORMAÇÕES DO RESPONDENTE (OPCIONAL)

Para contextualizarmos melhor as respostas:

- **Nome**: ___________________________________
- **Função**: 
  - [ ] Professor(a)
  - [ ] Coordenador(a) Pedagógico(a)
  - [ ] Diretor(a)
  - [ ] Outro: _________________________________
- **Componente(s) Curricular(es)**: ___________________________________
- **Ano(s) que leciona/coordena**: ___________________________________
- **Escola**: ___________________________________
- **Tempo de experiência na rede**: 
  - [ ] Menos de 1 ano
  - [ ] 1-3 anos
  - [ ] 3-5 anos
  - [ ] 5-10 anos
  - [ ] Mais de 10 anos

---

## 🎯 PRÓXIMOS PASSOS

### Após Aprovação da SEMED

1. **Consulta à Equipe Pedagógica**
   - Apresentação da proposta aos coordenadores pedagógicos
   - Coleta de feedback e sugestões de adequações
   - Ajustes conforme orientações pedagógicas

2. **Validação Técnica**
   - Revisão dos requisitos técnicos com equipe de TI (se houver)
   - Avaliação de infraestrutura necessária
   - Planejamento de integração com sistemas existentes

3. **Projeto Piloto**
   - Seleção de escola(s) piloto em conjunto com SEMED
   - Implementação gradual com acompanhamento contínuo
   - Coleta de métricas e feedback dos usuários

4. **Expansão Gradual**
   - Ajustes baseados no piloto
   - Capacitação de professores
   - Expansão para outras escolas da rede

### Compromisso com Transparência

- 📊 **Relatórios periódicos** de desenvolvimento e uso
- 🗣️ **Canais abertos** para sugestões e melhorias
- 📝 **Documentação completa** disponível
- 🤝 **Colaboração constante** com equipes pedagógicas

---

## 💡 CONSIDERAÇÕES FINAIS

### Por que este projeto é importante?

O Sistema de Banco de Questões BNCC representa uma **oportunidade única** de:

1. **Modernizar práticas pedagógicas** mantendo o foco na qualidade
2. **Valorizar o trabalho docente** através de ferramentas que facilitam seu dia a dia
3. **Potencializar resultados educacionais** com diagnósticos precisos
4. **Construir um patrimônio pedagógico** da rede municipal
5. **Garantir alinhamento curricular** sistemático à BNCC

### Nossa Motivação

Acreditamos que **educação pública de qualidade** é a base para transformação social. Este projeto é nossa forma de contribuir, usando tecnologia como **ferramenta de empoderamento** dos educadores e **melhoria da aprendizagem** dos estudantes.

### Solicitação

Solicitamos respeitosamente a **análise e aprovação** desta proposta pela SEMED, para que possamos:

- ✅ Prosseguir com consultas às equipes pedagógicas
- ✅ Iniciar desenvolvimento das funcionalidades
- ✅ Planejar implementação piloto
- ✅ Contribuir efetivamente com a educação do município

---

## 📞 CONTATO PARA ESCLARECIMENTOS

Para dúvidas, sugestões ou esclarecimentos sobre esta proposta, estamos à disposição através dos canais de comunicação já estabelecidos com a Secretaria.

**Equipe de Desenvolvimento Voluntário**  
**Sistema de Gestão Escolar**  
_Novembro de 2025_

---

_"A educação é a arma mais poderosa que você pode usar para mudar o mundo."_ - Nelson Mandela

---

## 🙏 AGRADECIMENTO

**Muito obrigado pela sua participação!**

Seu feedback é essencial para construirmos um sistema que realmente atenda às necessidades da nossa rede de ensino. Todas as sugestões serão cuidadosamente analisadas e consideradas no planejamento e desenvolvimento do projeto.

**Prazo para envio das respostas**: _____________

**Enviar para**: _______________ (e-mail/formulário/coordenação)

---

## 📊 PRÓXIMOS PASSOS

Após a coleta e análise dos feedbacks:

1. **Consolidação das respostas** (1 semana)
2. **Ajuste da proposta** com base nas sugestões (1 semana)
3. **Apresentação da proposta revisada** para validação final
4. **Início do desenvolvimento** da Fase 1 (MVP)
5. **Seleção de usuários piloto** para testes iniciais

**Contamos com vocês para construir juntos esta ferramenta!** 🚀
