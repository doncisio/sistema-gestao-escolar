# Guia de Integração: InterfaceCadastroEdicaoNotas + Banco de Questões

Data: 14/12/2025

## Objetivo

Integrar a interface existente de notas (`InterfaceCadastroEdicaoNotas.py`) com o sistema de avaliações do banco de questões, permitindo:
- Seleção de avaliação por turma/disciplina/bimestre
- Registro de respostas de alunos (objetivas e dissertativas)
- Correção automática de questões objetivas
- Fila de correção para questões dissertativas
- Cálculo automático de notas

---

## 1. Arquivos criados

### DDL (Banco de dados)
- `db/migrations/adicionar_tabelas_avaliacoes_respostas.sql`
  - Tabelas: `avaliacoes_alunos`, `respostas_questoes`
  - Views: `vw_desempenho_alunos`, `vw_fila_correcao`
  - Procedures: `calcular_nota_avaliacao_aluno`
  - Triggers: `trg_resposta_corrigida_atualiza_nota`

### Serviço (Backend)
- `banco_questoes/resposta_service.py`
  - Classe `RespostaService` com métodos:
    - `criar_avaliacao_aluno()` - Cria registro de avaliação por aluno
    - `registrar_resposta_objetiva()` - Registra e auto-corrige
    - `registrar_resposta_dissertativa()` - Registra para correção manual
    - `corrigir_resposta()` - Correção manual com comentário
    - `calcular_nota_total()` - Recalcula nota total
    - `buscar_fila_correcao()` - Lista respostas pendentes
    - `buscar_respostas_aluno()` - Busca respostas de um aluno
    - `finalizar_avaliacao_aluno()` - Marca como finalizada

---

## 2. Fluxo de trabalho proposto

### Modo 1: Lançamento rápido (uso atual - sem avaliações)
**Permanece inalterado** para professores que não usam o banco de questões:
- Seleciona turma, disciplina, bimestre
- Digita nota diretamente na tabela (0-10)
- Salva na tabela `notas` (modelo atual)

### Modo 2: Lançamento por avaliação (novo - com banco de questões)
**Fluxo novo** para professores que usam avaliações:

#### Passo 1: Seleção
- Professor seleciona turma, disciplina, bimestre
- **NOVO:** Aparece combobox "Avaliação" com avaliações aplicadas para essa combinação
- Ao selecionar avaliação, carregar lista de alunos

#### Passo 2: Criação de registros de aluno
- Para cada aluno da turma, criar `avaliacoes_alunos` automaticamente (se não existir)
- Marcar `presente=true` (padrão) ou permitir marcar ausente

#### Passo 3: Registro de respostas
- **Opção A - Importação em lote:**
  - Professor importa planilha CSV/XLS com colunas: `aluno_id, questao_id, alternativa_letra` (ou `resposta_texto`)
  - Sistema chama `RespostaService.registrar_resposta_objetiva()` para cada linha
  - Correção automática acontece imediatamente para objetivas
  
- **Opção B - Entrada manual:**
  - Professor clica em aluno → abre janela com lista de questões da avaliação
  - Para cada questão:
    - Se objetiva: combobox com A, B, C, D, E
    - Se dissertativa: campo texto + botão "anexar imagem"
  - Ao salvar, chama método apropriado do `RespostaService`

#### Passo 4: Correção de dissertativas
- Professor clica em "Fila de Correção"
- Sistema busca via `RespostaService.buscar_fila_correcao(professor_id=...)`
- Para cada resposta:
  - Mostra enunciado, resposta do aluno
  - Campo para pontuação (0 até máxima)
  - Campo para comentário (opcional)
  - Botão "Salvar" chama `RespostaService.corrigir_resposta()`

#### Passo 5: Finalização
- Quando todas as respostas corrigidas, professor clica "Finalizar"
- Sistema chama `RespostaService.finalizar_avaliacao_aluno()`
- Nota total é transferida para tabela `notas` (compatibilidade com boletim)

---

## 3. Modificações necessárias em InterfaceCadastroEdicaoNotas.py

### 3.1. Adicionar imports
```python
from banco_questoes.resposta_service import RespostaService
```

### 3.2. Adicionar campo de seleção de avaliação
Na função `criar_area_selecao()`, após o combobox de bimestre:

```python
# Novo frame para avaliação
frame_avaliacao = tk.LabelFrame(
    self.frame_selecao, text="Avaliação (opcional)", 
    bg=self.co0, font=("Arial", 10, "bold")
)
frame_avaliacao.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

tk.Label(frame_avaliacao, text="Avaliação:", bg=self.co0).grid(row=0, column=0, padx=5, pady=5, sticky="w")
self.cb_avaliacao = ttk.Combobox(frame_avaliacao, width=50, state="readonly")
self.cb_avaliacao.grid(row=0, column=1, padx=5, pady=5, sticky="w")
self.cb_avaliacao.bind("<<ComboboxSelected>>", self.ao_selecionar_avaliacao)

# Botões de ação para avaliações
tk.Button(
    frame_avaliacao, text="📋 Registrar Respostas",
    command=self.abrir_janela_respostas,
    bg=self.co4, fg="white"
).grid(row=0, column=2, padx=5)

tk.Button(
    frame_avaliacao, text="✍️ Fila de Correção",
    command=self.abrir_fila_correcao,
    bg=self.co2, fg="white"
).grid(row=0, column=3, padx=5)

tk.Button(
    frame_avaliacao, text="📥 Importar Respostas (CSV)",
    command=self.importar_respostas_csv,
    bg=self.co9, fg="white"
).grid(row=0, column=4, padx=5)
```

### 3.3. Carregar avaliações ao selecionar disciplina/bimestre
```python
def carregar_avaliacoes_disponiveis(self, event=None):
    """Carrega avaliações aplicadas para turma/disciplina/bimestre selecionados."""
    if not self.cb_turma.get() or not self.cb_disciplina.get() or not self.cb_bimestre.get():
        return
    
    conn = conectar_bd()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        turma_id = self.turmas_map.get(self.cb_turma.get())
        disciplina_nome = self.cb_disciplina.get()
        bimestre = self.cb_bimestre.get()
        
        query = """
            SELECT DISTINCT
                av.id,
                av.titulo,
                av.data_aplicacao,
                av.status
            FROM avaliacoes_aplicadas aa
            INNER JOIN avaliacoes av ON aa.avaliacao_id = av.id
            WHERE aa.turma_id = %s
              AND av.componente_curricular = %s
              AND av.bimestre = %s
              AND aa.status IN ('em_andamento', 'aguardando_lancamento', 'concluida')
            ORDER BY aa.data_aplicacao DESC
        """
        
        cursor.execute(query, (turma_id, disciplina_nome, bimestre))
        avaliacoes = cursor.fetchall()
        
        # Preencher combobox
        valores = [f"{av[0]} - {av[1]} ({av[2].strftime('%d/%m/%Y')})" for av in avaliacoes]
        self.cb_avaliacao['values'] = valores
        
        if valores:
            self.cb_avaliacao.current(0)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erro ao carregar avaliações: {e}")
```

### 3.4. Abrir janela de registro de respostas
```python
def abrir_janela_respostas(self):
    """Abre janela para registrar respostas de alunos."""
    if not self.cb_avaliacao.get():
        messagebox.showwarning("Aviso", "Selecione uma avaliação primeiro.")
        return
    
    # Extrair ID da avaliação do texto do combobox
    avaliacao_texto = self.cb_avaliacao.get()
    avaliacao_id = int(avaliacao_texto.split(' - ')[0])
    
    # Criar janela de respostas (implementar classe separada)
    from .janela_registro_respostas import JanelaRegistroRespostas
    JanelaRegistroRespostas(
        parent=self.janela,
        avaliacao_id=avaliacao_id,
        turma_id=self.turmas_map.get(self.cb_turma.get()),
        callback_atualizacao=self.carregar_notas_alunos
    )
```

### 3.5. Abrir fila de correção
```python
def abrir_fila_correcao(self):
    """Abre janela com fila de correção de questões dissertativas."""
    if not self.cb_avaliacao.get():
        messagebox.showwarning("Aviso", "Selecione uma avaliação primeiro.")
        return
    
    avaliacao_id = int(self.cb_avaliacao.get().split(' - ')[0])
    
    # Buscar respostas pendentes
    from banco_questoes.resposta_service import RespostaService
    respostas = RespostaService.buscar_fila_correcao(avaliacao_id=avaliacao_id)
    
    if not respostas:
        messagebox.showinfo("Info", "Não há respostas pendentes de correção.")
        return
    
    # Criar janela de correção (implementar classe separada)
    from .janela_fila_correcao import JanelaFilaCorrecao
    JanelaFilaCorrecao(
        parent=self.janela,
        respostas=respostas,
        callback_atualizacao=self.carregar_notas_alunos
    )
```

### 3.6. Importador CSV
```python
def importar_respostas_csv(self):
    """Importa respostas de alunos via arquivo CSV."""
    from tkinter import filedialog
    
    if not self.cb_avaliacao.get():
        messagebox.showwarning("Aviso", "Selecione uma avaliação primeiro.")
        return
    
    arquivo = filedialog.askopenfilename(
        title="Selecionar arquivo CSV",
        filetypes=[("Arquivos CSV", "*.csv"), ("Todos", "*.*")]
    )
    
    if not arquivo:
        return
    
    # Implementar importação (ver próxima seção)
    self.processar_importacao_csv(arquivo)
```

---

## 4. Classes auxiliares a criar

### 4.1. JanelaRegistroRespostas
Arquivo: `InterfaceCadastroEdicaoNotas_registro_respostas.py`

Responsabilidades:
- Lista todos os alunos da turma
- Para cada aluno, permite selecionar respostas para cada questão
- Chama `RespostaService.registrar_resposta_objetiva()` ou `registrar_resposta_dissertativa()`

### 4.2. JanelaFilaCorrecao
Arquivo: `InterfaceCadastroEdicaoNotas_fila_correcao.py`

Responsabilidades:
- Lista respostas dissertativas pendentes
- Navegação anterior/próximo
- Mostra enunciado + resposta do aluno
- Campo para pontuação e comentário
- Chama `RespostaService.corrigir_resposta()`

---

## 5. Sincronização com tabela `notas`

Após finalizar a correção de uma avaliação de aluno, copiar nota para a tabela `notas`:

```python
def sincronizar_nota_para_tabela_notas(avaliacao_aluno_id: int):
    """Copia nota da avaliação para a tabela notas (compatibilidade)."""
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Buscar dados da avaliação de aluno
    cursor.execute("""
        SELECT 
            aa.aluno_id,
            aa.nota_total,
            av.componente_curricular,
            av.bimestre
        FROM avaliacoes_alunos aa
        INNER JOIN avaliacoes av ON aa.avaliacao_id = av.id
        WHERE aa.id = %s AND aa.status = 'finalizada'
    """, (avaliacao_aluno_id,))
    
    resultado = cursor.fetchone()
    if not resultado:
        return False
    
    aluno_id, nota, componente, bimestre = resultado
    
    # Buscar disciplina_id
    cursor.execute("SELECT id FROM disciplinas WHERE nome = %s", (componente,))
    disciplina = cursor.fetchone()
    if not disciplina:
        return False
    
    disciplina_id = disciplina[0]
    
    # Inserir ou atualizar na tabela notas
    cursor.execute("""
        INSERT INTO notas (ano_letivo_id, aluno_id, disciplina_id, bimestre, nota)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE nota = VALUES(nota)
    """, (config.ANO_LETIVO_ATUAL, aluno_id, disciplina_id, bimestre, nota))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return True
```

---

## 6. Testes recomendados

1. **Teste de criação de avaliação de aluno:**
   - Criar avaliação no banco de questões
   - Aplicar para turma
   - Verificar se `avaliacoes_alunos` é criado automaticamente

2. **Teste de registro de resposta objetiva:**
   - Registrar resposta correta → verificar pontuação = máxima
   - Registrar resposta incorreta → verificar pontuação = 0
   - Verificar se `calcular_nota_total()` é chamado

3. **Teste de correção manual:**
   - Registrar resposta dissertativa
   - Corrigir com pontuação parcial
   - Verificar atualização de `nota_total`

4. **Teste de importação CSV:**
   - Criar CSV com 10 alunos e 5 questões
   - Importar e verificar auto-correção
   - Conferir log de erros

---

## 7. Próximos passos

1. ✅ Migração SQL executada
2. ✅ `RespostaService` implementado
3. 🔄 Modificar `InterfaceCadastroEdicaoNotas.py` (em andamento)
4. ⏳ Criar `JanelaRegistroRespostas`
5. ⏳ Criar `JanelaFilaCorrecao`
6. ⏳ Implementar importador CSV
7. ⏳ Testes de integração
8. ⏳ Piloto com professores

---

Documento vivo - atualizar conforme implementação avança.
