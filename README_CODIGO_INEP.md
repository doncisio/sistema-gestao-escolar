# Importação de Códigos INEP - Guia Rápido

## ✅ Status da Implementação

- [x] Campo `codigo_inep` adicionado ao banco de dados
- [x] Interfaces de cadastro e edição atualizadas
- [x] Script de mapeamento criado
- [x] Interface gráfica de confirmação criada
- [x] Tests executados com sucesso

## 🚀 Como Usar

### 1. Executar a Migration (se necessário)

```bash
cd C:\gestao
python verificar_banco_inep.py
```

### 2. Testar o Mapeamento

```bash
python testar_mapeamento_inep.py
```

### 3. Usar a Interface Gráfica

```bash
python -m src.interfaces.mapeamento_codigo_inep
```

Ou via código Python:

```python
from src.interfaces.mapeamento_codigo_inep import abrir_interface_mapeamento_inep

abrir_interface_mapeamento_inep()
```

## 📋 Fluxo de Trabalho

1. **Selecionar Arquivo Excel** com os códigos INEP
2. **Processar Mapeamento** - O sistema mapeia automaticamente os nomes
3. **Revisar Mapeamentos** - Verificar e ajustar se necessário
4. **Aplicar ao Banco** - Confirmar e salvar os códigos INEP

## 📊 Resultados do Teste

```
Total de registros no Excel:     316
Confirmados automaticamente:     316 (≥85% similaridade)
Para revisar manualmente:        0 (<85% similaridade)
Já possuem código INEP:          0
Sem código INEP:                 316
```

✅ **100% de sucesso no mapeamento!**

## 💾 Banco de Dados

### Nova Coluna

```sql
ALTER TABLE alunos 
ADD COLUMN codigo_inep VARCHAR(20) NULL AFTER cpf;
```

### Verificar Dados

```sql
SELECT nome, codigo_inep 
FROM alunos 
WHERE codigo_inep IS NOT NULL;
```

## 📝 Interfaces Atualizadas

### Cadastro de Aluno
- Novo campo: **Código INEP**
- Localização: Coluna 2, entre NIS e Cartão SUS

### Edição de Aluno
- Campo preenchido automaticamente após importação
- Pode ser editado manualmente

## 🔧 Arquivos Criados

1. `migrations/adicionar_campo_codigo_inep.sql` - Migration SQL
2. `src/services/mapeador_codigo_inep.py` - Lógica de mapeamento
3. `src/interfaces/mapeamento_codigo_inep.py` - Interface gráfica
4. `testar_mapeamento_inep.py` - Script de teste
5. `verificar_banco_inep.py` - Verificação e aplicação de migration
6. `docs/guias/GUIA_IMPORTACAO_CODIGO_INEP.md` - Documentação completa

## 🎯 Algoritmo de Mapeamento

O sistema usa **SequenceMatcher** da biblioteca `difflib`:

- Normaliza os nomes (remove acentos, converte para maiúsculas)
- Calcula similaridade entre 0% e 100%
- Limite padrão: **85%** para confirmação automática

## 📸 Screenshots da Interface

A interface possui:

- ✅ Seleção de arquivo Excel
- ✅ Processamento automático de mapeamento
- ✅ Tabela com resultados e cores:
  - **Verde**: Confirmados automaticamente
  - **Amarelo**: Para revisar manualmente
  - **Vermelho**: Não serão aplicados
- ✅ Filtros por status e busca
- ✅ Seleção individual ou em massa
- ✅ Estatísticas em tempo real

## 🆘 Troubleshooting

### Erro de encoding no Windows

Se encontrar erros de Unicode, execute:

```powershell
$env:PYTHONIOENCODING='utf-8'
python script.py
```

### Problema de conexão com banco

Verifique:
- MySQL está rodando
- Credenciais em `config/settings.py`
- Migration foi aplicada

## 📞 Suporte

Para mais detalhes, consulte o guia completo em:
`docs/guias/GUIA_IMPORTACAO_CODIGO_INEP.md`

---

**Implementado em:** 21/02/2026  
**Versão:** 1.0
