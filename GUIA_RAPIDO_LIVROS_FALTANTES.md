# 📚 GUIA RÁPIDO: Lista de Livros Faltantes por Turma

## ✅ Instalação Concluída

A funcionalidade foi instalada com sucesso! A tabela `livros_faltantes` foi criada no banco de dados.

## 🆕 Novidades - Suporte Completo 1º ao 9º Ano

✨ **Agora suporta do 1º ao 9º ano com layouts diferenciados!**

- **Anos Iniciais (1º ao 5º)**: PDF em formato retrato com disciplinas apropriadas
- **Anos Finais (6º ao 9º)**: PDF em formato paisagem com disciplinas separadas + Inglês

## 🚀 Como Usar (Passo a Passo)

### 1️⃣ Cadastrar Livros Faltantes

1. Abra o sistema: `python main.py`
2. No menu superior, clique em **Listas**
3. Selecione **"Gerenciar Livros Faltantes"**
4. Preencha:
   - **Ano Letivo**: Selecione o ano (ex: 2026)
   - **Série**: Escolha a série (**1º ao 9º Ano**)
   - **Turma**: Escolha a turma (A, B, C, etc.)
5. Clique em **"Carregar Dados"** (para ver dados já salvos)
6. Preencha os dados para cada disciplina:
   - **Quantidade de livros faltantes**
   - **Editora** (opcional)
   - **Coleção** (opcional)
   
   **As disciplinas mudam automaticamente conforme a série:**
   - **1º ao 5º Ano**: PRT, MTM, CNC, GEO/HIST, ART
   - **6º ao 9º Ano**: PRT, MTM, CNC, HST, GEO, ING, ART
   
7. Adicione observações se necessário
8. Clique em **"Salvar"**
9. Repita para todas as turmas

### 2️⃣ Gerar os PDFs

1. No menu **Listas**
2. Clique em **"Gerar PDF Livros Faltantes"**
3. O sistema gerará **automaticamente dois PDFs**:
   
   📄 **PDF Anos Iniciais** (1º ao 5º):
   - Formato retrato (A4)
   - Disciplinas: PRT, MTM, CNC, GEO/HIST, ART
   - Nome: `Livros_Faltantes_Anos_Iniciais_2026.pdf`
   
   📄 **PDF Anos Finais** (6º ao 9º):
   - Formato paisagem (A4)
   - Disciplinas: PRT, MTM, CNC, HST, GEO, ING, ART
   - Nome: `Livros_Faltantes_Anos_Finais_2026.pdf`

4. Escolha onde salvar cada arquivo
5. Os PDFs serão abertos automaticamente

## 📊 Exemplo de Cadastro

**3º Ano - Turma A (Anos Iniciais):**
- PRT: 15 livros - Editora: ÁTICA - Coleção: ÁPIS MAIS
- MTM: 25 livros - Editora: ÁTICA - Coleção: DIÁLOGOS
- CNC: 25 livros
- GEO/HIST: 20 livros - Editora: FTD
- ART: 20 livros

**8º Ano - Turma B (Anos Finais):**
- PRT: 10 livros - Editora: MODERNA
- MTM: 15 livros
- CNC: 12 livros
- HST: 8 livros (separado de Geografia)
- GEO: 8 livros (separado de História)
- ING: 20 livros
- ART: 10 livros
- ING: 4 livros
- ART: 1 livro

**Observação:** "Solicitar livros de Português urgente"

## 💡 Dicas

✅ **Cadastre todas as turmas** antes de gerar o PDF  
✅ **Atualize regularmente** conforme livros são recebidos  
✅ **Use as observações** para anotar informações importantes  
✅ **Salve o PDF** para enviar à Secretaria de Educação  

## 🔐 Quem Pode Usar

Esta funcionalidade está disponível para:
- ✓ Administradores
- ✓ Coordenadores

## ❓ Dúvidas Comuns

**P: Posso editar dados já cadastrados?**  
R: Sim! Basta selecionar a série/turma e clicar em "Carregar Dados". Os valores aparecerão e você pode alterá-los.

**P: E se eu não cadastrar alguma turma?**  
R: Não tem problema. O PDF só será gerado para as turmas que tiverem dados cadastrados.

**P: Posso gerar PDF de anos anteriores?**  
R: Sim! Basta selecionar o ano letivo desejado ao cadastrar ou alterar os dados.

## 📁 Arquivos Criados

```
✓ db/migrations/criar_tabela_livros_faltantes.sql
✓ src/ui/livros_faltantes_window.py
✓ src/relatorios/listas/lista_livros_faltantes.py
✓ executar_migracao_livros_faltantes.py
✓ README_LIVROS_FALTANTES.md
```

## 🎯 Menu Principal

```
Listas
├── Lista de Controle de Livros          ← Lista de alunos (já existia)
├── Gerenciar Livros Faltantes           ← NOVO! Cadastrar quantidades
└── Gerar PDF Livros Faltantes           ← NOVO! Gerar relatório
```

---

**Pronto para usar!** 🎉

Execute o sistema (`python main.py`) e comece a cadastrar os livros faltantes.
