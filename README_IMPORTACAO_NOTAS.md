# 📊 Sistema de Importação de Notas GEDUC → Excel

## 🎯 Objetivo

Automatizar a transferência de notas do sistema GEDUC para arquivos Excel, eliminando digitação manual e reduzindo erros.

## ✨ Funcionalidades

✅ Extração automática de dados do HTML exportado do GEDUC  
✅ Identificação automática de turma, disciplina e bimestre  
✅ Geração de arquivo Excel formatado  
✅ Cálculo automático de médias  
✅ Interface gráfica amigável  
✅ Opção de linha de comando para automação  
✅ Integrado ao menu "Serviços" do sistema principal  

## 🚀 Acesso Rápido

### Opção 1: Pelo Menu do Sistema
1. Abra o sistema principal (`python main.py`)
2. Clique em **Serviços**
3. Selecione **Importar Notas do GEDUC (HTML → Excel)**

### Opção 2: Interface Independente
```bash
python importar_notas_html.py
```

### Opção 3: Linha de Comando
```bash
python processar_notas_html.py "arquivo.html"
```

## 📖 Como Usar

### Passo 1: Exportar do GEDUC
1. Acesse https://semed.geduc.com.br
2. Vá para **Registro de Notas**
3. Selecione turma, disciplina e período
4. Clique em **Exibir Alunos**
5. Salve a página: `Ctrl+S` → Salvar como HTML

### Passo 2: Processar
1. Execute uma das opções acima
2. Selecione o arquivo HTML salvo
3. Clique em **Processar**
4. ✅ Pronto! Arquivo Excel criado

## 📁 Arquivos Criados

**Formato do nome:**
```
Template_Notas__-_MAT_{DISCIPLINA}_{BIMESTRE}_bimestre.xlsx
```

**Exemplos:**
- `Template_Notas__-_MAT_MATEMÁTICA_1º_bimestre.xlsx`
- `Template_Notas__-_MAT_ARTE_3º_bimestre.xlsx`

## 📊 Estrutura do Excel

```
Turma: 1º ANO-MATU
Disciplina: MATEMÁTICA
Bimestre: 3º

┌────┬──────────────────┬────────┬────────┬────────┬────────┬───────┐
│ Nº │ Nome do Aluno    │ Nota 1 │ Nota 2 │ Nota 3 │ Nota 4 │ Média │
├────┼──────────────────┼────────┼────────┼────────┼────────┼───────┤
│ 1  │ ALUNO A          │ 7.00   │ 8.00   │ 9.00   │ 7.50   │ 7.88  │
│ 2  │ ALUNO B          │ 8.50   │ 9.00   │ 10.00  │ 8.00   │ 8.88  │
└────┴──────────────────┴────────┴────────┴────────┴────────┴───────┘
```

## 🔧 Requisitos

- Python 3.12+
- BeautifulSoup4 (`pip install beautifulsoup4`)
- OpenPyXL (`pip install openpyxl`)
- Tkinter (incluído no Python)

## 📚 Documentação Completa

Consulte `GUIA_IMPORTACAO_NOTAS.md` para documentação detalhada.

## 🎨 Arquivos do Sistema

| Arquivo | Descrição |
|---------|-----------|
| `importar_notas_html.py` | Interface gráfica principal |
| `processar_notas_html.py` | Script de linha de comando |
| `GUIA_IMPORTACAO_NOTAS.md` | Documentação completa |
| `README_IMPORTACAO_NOTAS.md` | Este arquivo (resumo) |

## ⚡ Exemplo Rápido

```bash
# 1. Salvar HTML do GEDUC
# 2. Executar:
python processar_notas_html.py "notas_geduc.html"

# Resultado:
✓ Turma: 1º ANO-MATU
✓ Disciplina: MATEMÁTICA
✓ Bimestre: 3º
✓ Total de alunos: 25
✓ Arquivo criado: Template_Notas__-_MAT_MATEMÁTICA_3º_bimestre.xlsx
```

## 💡 Dicas

- 🔄 Processe múltiplas disciplinas salvando cada página HTML
- 📋 Use templates existentes com a opção "Usar template Excel"
- 🚀 Automatize com scripts em lote para processar vários arquivos
- 💾 Mantenha backup dos HTMLs originais

## ⚠️ Importante

- ✅ As notas devem estar cadastradas no GEDUC antes da exportação
- ✅ Salve sempre como "Página da Web, Completa" (.html)
- ✅ Não edite o HTML antes de processar
- ✅ Verifique o arquivo gerado antes de usar

## 🆘 Problemas Comuns

**"Nenhum aluno encontrado"**
→ Verifique se clicou em "Exibir Alunos" antes de salvar

**"Erro ao extrair dados"**
→ Salve o HTML completo, não apenas o texto

**"Módulo não encontrado"**
→ Execute: `pip install beautifulsoup4 openpyxl`

---

**✨ Desenvolvido para otimizar o trabalho docente e administrativo!**
