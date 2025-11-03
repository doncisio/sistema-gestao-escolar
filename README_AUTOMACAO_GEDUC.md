# 🤖 Automação de Extração de Notas GEDUC

## ⚠️ IMPORTANTE: reCAPTCHA

O GEDUC usa **reCAPTCHA** no login. Você precisará:
1. ✅ Resolver o reCAPTCHA **UMA VEZ** manualmente (30 segundos)
2. ✅ O resto é 100% automático (20-25 minutos)

**Você economiza HORAS de trabalho!** Detalhes: [`IMPORTANTE_RECAPTCHA.md`](IMPORTANTE_RECAPTCHA.md)

---

## ✨ Funcionalidades

✅ **Login semi-automático** (você resolve o reCAPTCHA, o resto é automático)  
✅ **Extração automática** de todas as notas  
✅ **Suporte a múltiplos bimestres** (1º, 2º, 3º, 4º)  
✅ **Geração automática** de arquivos Excel  
✅ **Interface gráfica** amigável  
✅ **Barra de progresso** em tempo real  

---

## 🚀 Início Rápido

### 1️⃣ Instalar Dependências

**Opção A - Automático (Windows):**
```bash
instalar_automacao.bat
```

**Opção B - Manual:**
```bash
pip install selenium beautifulsoup4 openpyxl webdriver-manager lxml
```

### 2️⃣ Executar

**Interface Gráfica (Mais fácil):**
```bash
python automatizar_extracao_geduc.py
```

**Linha de Comando (Exemplo):**
```bash
python exemplo_automacao_geduc.py
```

---

## 📖 Instruções Detalhadas

### Interface Gráfica

1. Execute: `python automatizar_extracao_geduc.py`
2. Preencha **usuário** e **senha** do GEDUC
3. Selecione os **bimestres** desejados
4. Clique em **"INICIAR EXTRAÇÃO AUTOMÁTICA"**
5. **⚠️ NO NAVEGADOR:** Marque "Não sou um robô" e clique em LOGIN
6. Aguarde... Os arquivos serão salvos em `notas_extraidas/`

### Uso Programático

```python
from automatizar_extracao_geduc import AutomacaoGEDUC

# Criar automação
automacao = AutomacaoGEDUC(headless=False)

# Iniciar e fazer login
automacao.iniciar_navegador()
automacao.fazer_login("seu_usuario", "sua_senha")

# Extrair notas de todos os bimestres
automacao.extrair_todas_notas(bimestres=[1, 2, 3, 4])

# Salvar arquivos
arquivos = automacao.salvar_dados_excel()

# Fechar
automacao.fechar()

print(f"✓ {len(arquivos)} arquivos criados!")
```

---

## 📁 Arquivos Gerados

### Localização
```
notas_extraidas/
├── Notas_1_ANO_A_LINGUA_PORTUGUESA_1bim.xlsx
├── Notas_1_ANO_A_MATEMATICA_1bim.xlsx
├── Notas_2_ANO_B_CIENCIAS_2bim.xlsx
└── ...
```

### Formato Excel
```
Turma: 1º ANO A
Disciplina: LÍNGUA PORTUGUESA
Bimestre: 1º

Nº | Nome do Aluno          | Nota
---|------------------------|------
1  | JOÃO SILVA             | 8.5
2  | MARIA OLIVEIRA         | 9.0
```

---

## ⚙️ Opções Avançadas

### Extrair apenas turmas específicas
```python
# IDs das turmas (você pode descobrir pelo HTML)
turmas = ['123', '456']

automacao.extrair_todas_notas(
    turmas_selecionadas=turmas,
    bimestres=[1, 2]
)
```

### Callback de progresso
```python
def meu_progresso(processadas, total):
    print(f"Processadas: {processadas}/{total}")

automacao.extrair_todas_notas(
    bimestres=[1],
    callback_progresso=meu_progresso
)
```

### Modo headless (sem abrir janela)
```python
automacao = AutomacaoGEDUC(headless=True)
```

---

## 🐛 Solução de Problemas

### ❌ Erro: "ChromeDriver not found"

**Solução:**
```bash
pip install webdriver-manager
```

O webdriver-manager baixa automaticamente o ChromeDriver correto!

---

### ❌ Erro: "Login falhou"

**Verifique:**
- ✅ Usuário e senha corretos
- ✅ Conexão com internet
- ✅ Site do GEDUC acessível

---

### ❌ Navegador abre mas não faz nada

**Soluções:**
- Aguarde alguns segundos (pode ser lento)
- Desative o modo headless para ver o que acontece
- Verifique sua conexão

---

## 📊 Desempenho

| Configuração | Tempo Estimado |
|-------------|----------------|
| 1 bimestre, 10 turmas | ~5 minutos |
| 2 bimestres, 10 turmas | ~10 minutos |
| 4 bimestres, 10 turmas | ~20 minutos |

**Dica:** Use modo headless para +20% de velocidade

---

## 📚 Arquivos do Projeto

| Arquivo | Descrição |
|---------|-----------|
| `automatizar_extracao_geduc.py` | **Script principal** com classe e interface |
| `exemplo_automacao_geduc.py` | Exemplos de uso simples |
| `GUIA_AUTOMACAO_GEDUC.md` | Guia completo e detalhado |
| `instalar_automacao.bat` | Instalador automático (Windows) |

---

## 🔒 Segurança

⚠️ **IMPORTANTE:**
- Suas credenciais são usadas **apenas** para login
- **Nenhum dado** é enviado para servidores externos
- Todo processamento é **local**
- Credenciais **não são salvas**

---

## 💡 Dicas

1. **Teste primeiro com 1 bimestre** para verificar se está funcionando
2. **Use modo headless** para processos em lote
3. **Execute fora do horário de pico** do servidor GEDUC
4. **Mantenha o Chrome atualizado** para melhor compatibilidade

---

## 📞 Suporte

Se encontrar problemas:

1. ✅ Verifique o `GUIA_AUTOMACAO_GEDUC.md`
2. ✅ Execute em modo **não-headless** para debug visual
3. ✅ Verifique os logs no terminal
4. ✅ Certifique-se que todas as dependências estão instaladas

---

## 📝 Changelog

**v1.0** (Outubro 2025)
- ✨ Extração automática completa
- ✨ Interface gráfica
- ✨ Modo headless
- ✨ Suporte a webdriver-manager
- ✨ Barra de progresso
- ✨ Callbacks personalizáveis

---

## 📄 Licença

Uso interno e educacional. Respeite os termos de uso do GEDUC.

---

**Desenvolvido para automação de tarefas educacionais** 🎓
