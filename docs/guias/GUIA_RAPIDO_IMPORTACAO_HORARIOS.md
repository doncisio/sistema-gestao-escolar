# Guia Rápido - Importação de Horários do GEDUC

## ⚡ Início Rápido

### 1️⃣ Configure as Credenciais (Opcional)
Edite `src/core/config.py`:
```python
GEDUC_DEFAULT_USER = "seu_usuario"
GEDUC_DEFAULT_PASS = "sua_senha"
```

### 2️⃣ Abra a Interface
- Execute o sistema principal
- Menu → "Horários Escolares"

### 3️⃣ Selecione a Turma
- **Turno**: Matutino ou Vespertino
- **Série/Ano**: Ex: 1º Ano, 6º Ano
- **Turma**: Ex: A, B, MATUTINO

### 4️⃣ Importe do GEDUC
1. Clique em **"🌐 Importar do GEDUC"**
2. Insira suas credenciais (se não configuradas)
3. **Aguarde o navegador abrir**
4. **RESOLVA O reCAPTCHA** ✅
5. **Clique em LOGIN** no navegador
6. Aguarde a extração automática

### 5️⃣ Verifique os Resultados
- Horários aparecem automaticamente na grade
- Mensagem de sucesso mostra quantidade importada

## 🎯 Comandos Rápidos

### Teste via Script
```bash
cd c:\gestao
python scripts\teste_importacao_horarios.py
```

### Uso Programático
```python
from src.importadores.geduc import AutomacaoGEDUC

# Inicializar
auto = AutomacaoGEDUC()
auto.iniciar_navegador()

# Login (você deve resolver reCAPTCHA)
auto.fazer_login("usuario", "senha", timeout_recaptcha=120)

# Extrair
dados = auto.extrair_horario_turma("1º ANO-MATU")

# Usar dados
for h in dados['horarios']:
    print(f"{h['dia']} {h['horario']}: {h['disciplina']}")

# Fechar
auto.fechar()
```

## 🔧 Solução de Problemas Rápida

| Problema | Solução |
|----------|---------|
| Navegador não abre | Instale Chrome; baixe ChromeDriver |
| Timeout reCAPTCHA | Resolva mais rápido; aumente timeout |
| Turma não encontrada | Verifique nome exato no GEDUC |
| Disciplinas NULL | Cadastre disciplinas no sistema local |

## 📁 Arquivos Importantes

- **Código principal**: `src/importadores/geduc.py`
- **Interface**: `src/interfaces/horarios_escolares.py`
- **Config**: `src/core/config.py`
- **Teste**: `scripts/teste_importacao_horarios.py`
- **Docs**: `docs/IMPORTACAO_HORARIOS_GEDUC.md`

## ⚙️ Requisitos

```bash
pip install selenium beautifulsoup4 webdriver-manager
```

## 🎓 Formato de Nomes de Turmas

O GEDUC usa formatos variados:
- `"1º ANO-MATU"`
- `"2º Ano MAT"`
- `"6º ANO-VESP - A"`
- `"9º ANO-VESP - B"`

O sistema busca correspondência parcial.

## 💡 Dicas

1. **Primeira vez**: Use modo não-headless para ver o processo
2. **Produção**: Configure credenciais em `config.py`
3. **Múltiplas turmas**: Execute script de teste em loop
4. **Atualização**: Basta reimportar (UPSERT evita duplicatas)

## 📞 Suporte

- **Logs**: Verifique console para detalhes
- **Erros**: Consulte `docs/IMPORTACAO_HORARIOS_GEDUC.md`
- **Código**: Revise `src/importadores/geduc.py` (linhas 1000+)

---

**Pronto para usar!** 🚀
