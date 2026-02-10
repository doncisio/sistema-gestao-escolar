# 📚 GUIA RÁPIDO: Lista de Livros Faltantes por Turma

## ✅ Instalação Concluída

A funcionalidade foi instalada com sucesso! A tabela `livros_faltantes` foi criada no banco de dados.

## 🚀 Como Usar (Passo a Passo)

### 1️⃣ Cadastrar Livros Faltantes

1. Abra o sistema: `python main.py`
2. No menu superior, clique em **Listas**
3. Selecione **"Gerenciar Livros Faltantes"**
4. Preencha:
   - **Ano Letivo**: Selecione o ano (ex: 2026)
   - **Série**: Escolha a série (1º Ano, 2º Ano, etc.)
   - **Turma**: Escolha a turma (A, B, C, etc.)
5. Clique em **"Carregar Dados"** (para ver dados já salvos)
6. Preencha a **quantidade de livros faltantes** para cada disciplina:
   - PRT (Português)
   - MTM (Matemática)
   - CNC (Ciências)
   - HST (História)
   - GEO (Geografia)
   - ING (Inglês)
   - ART (Arte)
7. Adicione observações se necessário
8. Clique em **"Salvar"**
9. Repita para todas as turmas

### 2️⃣ Gerar o PDF

1. No menu **Listas**
2. Clique em **"Gerar PDF Livros Faltantes"**
3. O PDF será gerado automaticamente com:
   - Capa profissional
   - Uma página por turma cadastrada
   - Tabela com quantidades por disciplina
   - Total de livros faltantes por turma
   - Espaço para observações
4. Escolha onde salvar ou visualize diretamente

## 📊 Exemplo de Cadastro

**1º Ano - Turma A:**
- PRT: 5 livros
- MTM: 3 livros
- CNC: 2 livros
- HST: 0 livros
- GEO: 0 livros
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
