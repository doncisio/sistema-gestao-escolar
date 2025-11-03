# Menus Dropdown - Interface de Cadastro e Edição de Notas

## 📋 Resumo das Alterações

Foram criados **dois menus dropdown** na interface de Cadastro e Edição de Notas para organizar melhor as funcionalidades relacionadas ao GEDUC e às operações de Importar/Exportar.

## 🎯 Objetivo

Melhorar a organização da interface, agrupando funcionalidades relacionadas em menus dropdown, tornando a barra de botões mais limpa, organizada e profissional.

## 🔧 O que foi modificado

### Antes:
A interface tinha **6 botões separados** na barra de botões:
- 🔄 Preencher do GEDUC
- 📥 Extrair Todas Disciplinas  
- 📝 Recuperação Bimestral
- 📥 Importar do Excel
- 📄 Exportar Template
- 📤 Exportar para Excel

### Depois:
Agora existem **2 menus dropdown** organizados:

#### Menu 1: 🌐 GEDUC ▼
- 🔄 Preencher do GEDUC
- 📥 Extrair Todas Disciplinas
- 📝 Recuperação Bimestral

#### Menu 2: 📊 Importar/Exportar ▼
- 📥 Importar do Excel
- 📄 Exportar Template
- 📤 Exportar para Excel

## 📝 Detalhes Técnicos

### Arquivo Modificado
- `InterfaceCadastroEdicaoNotas.py`

### Métodos Alterados/Criados

#### 1. `criar_barra_botoes()` - Modificado
- Removeu os 6 botões individuais (GEDUC + Importar/Exportar)
- Adicionou chamada para `criar_menu_geduc()`
- Adicionou chamada para `criar_menu_importar_exportar()`
- Manteve apenas os botões (Salvar, Limpar)

#### 2. `criar_menu_geduc()` - Novo Método
- Cria um frame para o menu GEDUC
- Define um `Menubutton` com estilo personalizado (roxo #673AB7)
- Cria um `Menu` com os 3 itens do GEDUC
- Associa os comandos corretos a cada item:
  - `abrir_preenchimento_automatico()`
  - `extrair_todas_disciplinas_geduc()`
  - `processar_recuperacao_bimestral()`

#### 3. `criar_menu_importar_exportar()` - Novo Método
- Cria um frame para o menu Importar/Exportar
- Define um `Menubutton` com estilo personalizado (azul #0288D1)
- Cria um `Menu` com os 3 itens de Import/Export
- Adiciona separador visual entre Importar e Exportar
- Associa os comandos corretos a cada item:
  - `importar_do_excel()`
  - `exportar_template_excel()`
  - `exportar_para_excel()`

## 🎨 Design dos Menus

### Menu GEDUC
- **Cor de fundo**: #673AB7 (roxo)
- **Cor do texto**: Branco
- **Largura**: 18 caracteres
- **Fonte**: Arial, 10, bold
- **Ícone**: 🌐 GEDUC ▼
- **Itens**: 3 opções relacionadas ao sistema GEDUC

### Menu Importar/Exportar
- **Cor de fundo**: #0288D1 (azul)
- **Cor do texto**: Branco
- **Largura**: 22 caracteres
- **Fonte**: Arial, 10, bold
- **Ícone**: 📊 Importar/Exportar ▼
- **Itens**: 3 opções (1 importação + 2 exportações)
- **Separador visual**: Entre Importar e Exportar

### Características Comuns
- **Fonte dos itens**: Arial, 9
- **Ícones**: Mantidos os ícones originais de cada funcionalidade
- **Sem separação**: tearoff=0 (não permite destacar o menu)
- **Hover**: Efeito visual ao passar o mouse

## ✅ Benefícios

1. **Organização Visual**: Reduz de 8 para 4 botões na barra (50% de redução!)
2. **Agrupamento Lógico**: 
   - Funcionalidades do GEDUC agrupadas
   - Operações de Import/Export agrupadas
3. **Espaço Otimizado**: Libera muito espaço na barra de botões
4. **Interface Profissional**: Aparência mais limpa e moderna
5. **Facilidade de Uso**: Usuário encontra facilmente funcionalidades relacionadas
6. **Escalabilidade**: Fácil adicionar novas funcionalidades sem poluir a interface
7. **Hierarquia Visual**: Menus coloridos ajudam a identificar categorias rapidamente

## 🔄 Funcionalidades Mantidas

Todas as funcionalidades continuam funcionando exatamente como antes:

### Menu GEDUC 🌐

#### 🔄 Preencher do GEDUC
- Abre o assistente de preenchimento automático
- Permite extrair notas de uma disciplina específica
- Requer seleção prévia de turma e disciplina

#### 📥 Extrair Todas Disciplinas
- Extrai TODAS as disciplinas de uma turma do GEDUC
- Salva direto no banco de dados
- Gera relatório de inconsistências
- Tempo estimado: 2-5 minutos

#### 📝 Recuperação Bimestral
- Processa recuperação para TODAS as turmas
- Atualiza notas seguindo a regra: se (nota/10 < 6) e (nota/10 < Recuperação)
- Processa todas as disciplinas de todas as turmas
- Tempo estimado: 5-15 minutos

### Menu Importar/Exportar 📊

#### 📥 Importar do Excel
- Permite importar notas de um arquivo Excel
- Valida formato e dados antes de importar
- Atualiza campos automaticamente na interface
- Requer seleção prévia de turma e disciplina

#### 📄 Exportar Template
- Gera arquivo Excel vazio para preenchimento
- Inclui estrutura correta (ID, Nome, Nota)
- Facilita o preenchimento em massa de notas
- Arquivo pronto para importação posterior

#### 📤 Exportar para Excel
- Exporta notas atuais para arquivo Excel
- Inclui todos os alunos da turma selecionada
- Gera relatório formatado
- Útil para backup ou análise externa

## 📚 Como Usar

### Menu GEDUC
1. Abra a interface de Cadastro e Edição de Notas
2. Clique no botão "🌐 GEDUC ▼" (roxo)
3. Selecione a opção desejada no menu dropdown
4. Siga as instruções específicas de cada funcionalidade

### Menu Importar/Exportar
1. Abra a interface de Cadastro e Edição de Notas
2. Clique no botão "📊 Importar/Exportar ▼" (azul)
3. Selecione a opção desejada (Importar ou Exportar)
4. Siga o assistente de importação/exportação

## 🔍 Observações

- Os menus são implementados usando `Menubutton` e `Menu` do tkinter
- Cada menu tem sua cor própria para facilitar identificação:
  - **GEDUC**: Roxo (#673AB7) - Funcionalidades externas
  - **Importar/Exportar**: Azul (#0288D1) - Operações de dados
- Os comandos associados aos itens são os mesmos dos botões originais
- Nenhuma funcionalidade foi removida ou alterada
- Layout responsivo - menus se ajustam ao tamanho da janela
- Separador visual no menu Importar/Exportar divide Importação de Exportações

## 🎓 Exemplo de Código

### Menu GEDUC
```python
def criar_menu_geduc(self):
    """Cria um menu dropdown para funcionalidades do GEDUC"""
    frame_menu = tk.Frame(self.frame_botoes, bg=self.co0)
    frame_menu.pack(side="left", padx=5)
    
    self.btn_menu_geduc = tk.Menubutton(
        frame_menu,
        text="🌐 GEDUC ▼",
        bg="#673AB7",
        fg="white",
        font=("Arial", 10, "bold"),
        width=18,
        relief="raised",
        bd=2
    )
    self.btn_menu_geduc.pack()
    
    self.menu_geduc = tk.Menu(self.btn_menu_geduc, tearoff=0, font=("Arial", 9))
    
    self.menu_geduc.add_command(
        label="🔄 Preencher do GEDUC",
        command=self.abrir_preenchimento_automatico
    )
    
    self.menu_geduc.add_command(
        label="📥 Extrair Todas Disciplinas",
        command=self.extrair_todas_disciplinas_geduc
    )
    
    self.menu_geduc.add_command(
        label="📝 Recuperação Bimestral",
        command=self.processar_recuperacao_bimestral
    )
    
    self.btn_menu_geduc["menu"] = self.menu_geduc
```

### Menu Importar/Exportar
```python
def criar_menu_importar_exportar(self):
    """Cria um menu dropdown para funcionalidades de Importar/Exportar"""
    frame_menu = tk.Frame(self.frame_botoes, bg=self.co0)
    frame_menu.pack(side="left", padx=5)
    
    self.btn_menu_io = tk.Menubutton(
        frame_menu,
        text="📊 Importar/Exportar ▼",
        bg="#0288D1",
        fg="white",
        font=("Arial", 10, "bold"),
        width=22,
        relief="raised",
        bd=2
    )
    self.btn_menu_io.pack()
    
    self.menu_io = tk.Menu(self.btn_menu_io, tearoff=0, font=("Arial", 9))
    
    self.menu_io.add_command(
        label="📥 Importar do Excel",
        command=self.importar_do_excel
    )
    
    self.menu_io.add_separator()  # Separador visual
    
    self.menu_io.add_command(
        label="📄 Exportar Template",
        command=self.exportar_template_excel
    )
    
    self.menu_io.add_command(
        label="📤 Exportar para Excel",
        command=self.exportar_para_excel
    )
    
    self.btn_menu_io["menu"] = self.menu_io
```

## 📅 Data da Modificação
2 de novembro de 2025

---

✅ **Status**: Implementado e testado com sucesso
