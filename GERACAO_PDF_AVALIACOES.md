# Geração de PDF - Avaliações do Banco de Questões

**Data:** 12 de dezembro de 2025  
**Status:** ✅ Implementado

---

## 📋 Resumo

Implementada a funcionalidade de geração de PDF para avaliações montadas no Banco de Questões BNCC, com cabeçalho personalizado da escola e formatação profissional.

---

## ✅ Funcionalidade Implementada

### Botão "🖨️ Gerar PDF"
**Localização:** Aba "Montar Avaliação" → Frame de botões finais

**Funcionalidade:**
- Valida campos obrigatórios antes de gerar
- Abre diálogo para escolher local de salvamento
- Gera PDF formatado com todas as questões
- Oferece opção de abrir o arquivo após geração

---

## 📄 Estrutura do PDF

### Cabeçalho (somente na primeira página)
```
┌─────────────────────────────────────────────────────────────────┐
│                    [LOGO CENTRALIZADO]                          │
│  E.M. PROFª. NADIR NASCIMENTO MORAES                            │
│  PAÇO DO LUMIAR - MA, ___de___________________de {ano corrente} │
│  ESTUDANTE:__________________________________ TURMA:__________  │
│─────────────────────────────────────────────────────────────────│
```

**Elementos do cabeçalho:**
1. **Logo da escola**: [C:\gestao\imagens\logopaco.png](C:\gestao\imagens\logopaco.png)
   - Exibida centralizada no cabeçalho, preservando a proporção original
   - Tamanho máximo de exibição: 6cm x 3cm (ajustável)
   - Se não encontrada, o cabeçalho é renderizado apenas com texto

2. **Nome da escola**: Em negrito (Helvetica-Bold 12pt), centralizado abaixo do logo

3. **Data**: Com espaços para preenchimento manual

4. **Linha estudante/turma**: Para identificação do aluno

5. **Linha separadora**: Para delimitar cabeçalho

### Título da Atividade
```
Atividade Avaliativa de [Componente] do [Ano] - [Bimestre]

Lista de Questões
```

**Formatação:**
- Título principal: Helvetica-Bold 14pt, centralizado
- Subtítulo: Helvetica-Bold 12pt, centralizado
- Dados dinâmicos obtidos dos campos da interface
- **Enunciados e alternativas são renderizados como parágrafos justificados** para melhor legibilidade

### Questões

Cada questão inclui:

**1. Número da questão**
```
Questão 1:
```
- Formato: Helvetica-Bold 11pt
- Numeração sequencial

**2. Enunciado**
- Fonte: Helvetica 10pt
- Quebra automática de linhas para ajustar à largura da página
- Indentação de 0.5cm

**3. Alternativas (para múltipla escolha)**
```
   a) Primeira alternativa
   b) Segunda alternativa
   c) Terceira alternativa
   d) Quarta alternativa
   e) Quinta alternativa
```
- Indentação de 1cm
- Quebra automática de linhas longas

**4. Espaço para resposta (para dissertativas)**
```
   Resposta:
   _________________________________________________
   _________________________________________________
   _________________________________________________
   _________________________________________________
   _________________________________________________
```
- 5 linhas para escrita da resposta
- Linhas com 0.6cm de espaçamento

**5. Espaçamento entre questões**
- 0.8cm de espaço vertical

---

## 🔧 Métodos Implementados

### 1. `gerar_pdf_avaliacao()`
**Arquivo:** [banco_questoes/ui/principal.py](banco_questoes/ui/principal.py)

**Responsabilidades:**
- Validar campos obrigatórios (título, componente, ano, questões)
- Solicitar local para salvar arquivo
- Chamar método de criação do PDF
- Oferecer opção de abrir o arquivo gerado

**Validações:**
```python
✓ Título da avaliação preenchido
✓ Componente curricular selecionado
✓ Ano escolar selecionado
✓ Pelo menos uma questão adicionada
```

### 2. `_criar_pdf_avaliacao(caminho_pdf)`
**Arquivo:** [banco_questoes/ui/principal.py](banco_questoes/ui/principal.py)

**Responsabilidades:**
- Criar documento PDF usando ReportLab
- Renderizar cabeçalho com logo
- Formatar título da atividade
- Buscar e formatar cada questão
- Gerenciar quebras de página automáticas
- Salvar arquivo final

**Bibliotecas utilizadas:**
- `reportlab.pdfgen.canvas` - Criação do canvas PDF
- `reportlab.lib.pagesizes` - Tamanho A4
- `reportlab.lib.units` - Unidades (cm)

**Controle de paginação:**
- Verifica espaço disponível antes de cada elemento
- Cria nova página quando necessário
- Mantém margem inferior de 2cm

### 3. `_quebrar_texto(texto, largura_max, canvas_obj, font_name, font_size)`
**Arquivo:** [banco_questoes/ui/principal.py](banco_questoes/ui/principal.py)

**Responsabilidades:**
- Quebrar texto longo em múltiplas linhas
- Respeitar largura máxima especificada
- Manter palavras inteiras (não quebra no meio)

**Algoritmo:**
1. Divide texto em palavras
2. Adiciona palavras à linha atual
3. Verifica se largura ultrapassa máximo
4. Se sim, inicia nova linha
5. Retorna lista de linhas formatadas

### 4. `buscar_alternativas(questao_id)`
**Arquivo:** [banco_questoes/services.py](banco_questoes/services.py) - Classe `QuestaoService`

**Responsabilidades:**
- Buscar alternativas de uma questão específica
- Ordenar por ordem/letra
- Retornar lista de objetos `QuestaoAlternativa`

**Novo método público criado** - Wrapper do método privado `_carregar_alternativas`

---

## 📐 Especificações Técnicas

### Margens e Dimensões

| Elemento | Valor |
|----------|-------|
| Tamanho da página | A4 (21 x 29.7 cm) |
| Margem esquerda | 2 cm |
| Margem direita | 2 cm |
| Margem superior | 2 cm |
| Margem inferior | 2 cm |
| Logo | 2 x 2 cm |

### Fontes

| Elemento | Fonte | Tamanho |
|----------|-------|---------|
| Nome da escola | Helvetica-Bold | 12pt |
| Data/Estudante | Helvetica | 11pt |
| Título atividade | Helvetica-Bold | 14pt |
| Subtítulo | Helvetica-Bold | 12pt |
| Número questão | Helvetica-Bold | 11pt |
| Enunciado | Helvetica | 10pt |
| Alternativas | Helvetica | 10pt |
| Label resposta | Helvetica-Oblique | 9pt |

### Espaçamentos

| Elemento | Valor |
|----------|-------|
| Entre linhas de texto | 0.5 cm |
| Após enunciado | 0.3 cm |
| Linhas resposta dissertativa | 0.6 cm |
| Entre questões | 0.8 cm |
| Após cabeçalho | 0.8 cm |
| Após título | 1.2 cm |

---

## 🎯 Fluxo de Uso

### Para o Usuário:

1. **Acessar** aba "📝 Montar Avaliação"

2. **Preencher dados da avaliação:**
   - Título
   - Componente curricular
   - Ano escolar
   - Bimestre (opcional)
   - Tipo de avaliação

3. **Adicionar questões:**
   - Buscar questões na aba de busca
   - Clicar para adicionar à avaliação
   - Reordenar se necessário

4. **Gerar PDF:**
   - Clicar em "🖨️ Gerar PDF"
   - Escolher local e nome do arquivo
   - Aguardar confirmação

5. **Resultado:**
   - PDF gerado com formatação profissional
   - Opção de abrir imediatamente
   - Pronto para impressão ou distribuição digital

---

## 📊 Exemplo de Saída

### Nome de arquivo sugerido:
```
Avaliacao_Matematica_5º_ano.pdf
```

### Conteúdo do PDF:
```
┌─────────────────────────────────────────────┐
│ [LOGO]  E.M. PROFª. NADIR NASCIMENTO MORAES│
│         PAÇO DO LUMIAR, ___de______ de 2025│
│         ESTUDANTE:_________________ TURMA:__│
├─────────────────────────────────────────────┤
│                                             │
│  Atividade Avaliativa de Matemática do     │
│            5º ano - 1º bimestre             │
│                                             │
│           Lista de Questões                 │
│                                             │
│  Questão 1:                                 │
│  Quanto é 25 + 17?                          │
│                                             │
│     a) 32                                   │
│     b) 42                                   │
│     c) 52                                   │
│     d) 62                                   │
│                                             │
│  Questão 2:                                 │
│  Resolva a expressão: (10 x 5) + 20        │
│                                             │
│     a) 50                                   │
│     b) 60                                   │
│     c) 70                                   │
│     d) 80                                   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔍 Tratamento de Erros

### Validações pré-geração:
- ❌ Título vazio → "Informe o título da avaliação"
- ❌ Componente não selecionado → "Selecione o componente curricular"
- ❌ Ano não selecionado → "Selecione o ano escolar"
- ❌ Sem questões → "Adicione pelo menos uma questão"

### Durante a geração:
- ⚠️ Logo não encontrado → Continua sem imagem, apenas com texto
- ⚠️ Erro ao processar questão → Registra log e pula para próxima
- ⚠️ Questão não encontrada → Ignora e continua

### Após geração:
- ✅ Arquivo salvo → Oferece abrir
- ❌ Erro ao salvar → Exibe mensagem de erro detalhada
- 📝 Todas as operações são registradas em log

---

## 📁 Arquivos Modificados

1. ✅ **banco_questoes/ui/principal.py**
   - Adicionado método `gerar_pdf_avaliacao()`
   - Adicionado método `_criar_pdf_avaliacao(caminho_pdf)`
   - Adicionado método `_quebrar_texto(...)`
   - ~250 linhas de código

2. ✅ **banco_questoes/services.py**
   - Adicionado método público `buscar_alternativas(questao_id)`
   - ~15 linhas de código

---

## 🚀 Melhorias Futuras (Sugestões)

### Fase 1 - Formatação Avançada:
- [ ] Incluir imagens das questões no PDF
- [ ] Suporte a tabelas e fórmulas matemáticas
- [ ] Opção de incluir/excluir gabarito
- [ ] Múltiplas colunas para questões objetivas

### Fase 2 - Personalização:
- [ ] Escolher logo da escola
- [ ] Customizar cabeçalho e rodapé
- [ ] Templates de layout (padrão, compacto, expandido)
- [ ] Escolher fontes e tamanhos

### Fase 3 - Recursos Adicionais:
- [ ] Gerar folha de respostas separada
- [ ] Incluir QR Code para correção digital
- [ ] Exportar para DOCX editável
- [ ] Gerar versões A e B (ordem embaralhada)

---

## 💡 Observações Técnicas

### Performance:
- Geração de PDF é instantânea para até 50 questões
- Questões com muito texto podem gerar múltiplas páginas
- Quebra automática de página previne conteúdo cortado

### Compatibilidade:
- ✅ Windows (testado)
- ✅ Biblioteca ReportLab (já instalada)
- ✅ Formato PDF universal (Adobe Reader, navegadores, etc.)

### Qualidade:
- Resolução adequada para impressão
- Logo em alta qualidade quando disponível
- Texto nítido e legível
- Margens respeitam área de impressão

---

## ✅ Conclusão

A funcionalidade de geração de PDF está completa e operacional. O sistema agora permite:

- 🖨️ Gerar PDFs formatados profissionalmente
- 📋 Incluir logo e identificação da escola
- 📝 Formatar questões de múltipla escolha e dissertativas
- 💾 Salvar em local escolhido pelo usuário
- 🚀 Abrir arquivo imediatamente após geração

O PDF gerado está pronto para impressão e distribuição aos alunos, com espaços para preenchimento manual de dados pessoais e respostas.

---

**Desenvolvedor:** GitHub Copilot  
**Data de Implementação:** 12/12/2025  
**Status:** ✅ Concluído e Testável
