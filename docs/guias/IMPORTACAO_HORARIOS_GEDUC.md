# Importação de Horários do GEDUC

## Visão Geral

O sistema agora permite importar horários de turmas diretamente do GEDUC para o banco de dados local, facilitando o gerenciamento de horários escolares.

## Funcionalidades Implementadas

### 1. Novos Métodos na Classe `AutomacaoGEDUC`

Foram adicionados três novos métodos na classe `AutomacaoGEDUC` (`src/importadores/geduc.py`):

#### `acessar_horarios_turma()`
- Navega até a página de horários por turma do GEDUC
- URL: `https://semed.geduc.com.br/index.php?class=TurmaHorarioForm`

#### `extrair_horario_turma(turma_nome: str) -> Optional[dict]`
- Extrai o horário completo de uma turma específica
- **Parâmetros:**
  - `turma_nome`: Nome da turma (ex: "1º ANO-MATU", "6º ANO-VESP - A")
- **Retorna:**
  ```python
  {
      'turma_nome': str,
      'turma_id': int ou None,
      'horarios': [
          {
              'dia': str,        # Segunda, Terça, Quarta, Quinta, Sexta
              'horario': str,    # 07:10-08:00
              'disciplina': str, # Nome da disciplina
              'professor': str   # Nome do professor (se disponível)
          }
      ],
      'timestamp': str
  }
  ```

#### `listar_turmas_disponiveis() -> list`
- Lista todas as turmas disponíveis no GEDUC
- **Retorna:** Lista de dicts com `'id'` e `'nome'` das turmas

### 2. Integração na Interface de Horários

Foram adicionados métodos na classe `InterfaceHorariosEscolares` (`src/interfaces/horarios_escolares.py`):

#### Botão "🌐 Importar do GEDUC"
- Novo botão adicionado na barra de ferramentas
- Abre assistente de importação com progresso em tempo real

#### `importar_geduc()`
- Método principal que coordena a importação
- Solicita credenciais do usuário
- Executa importação em thread separada
- Mostra progresso em janela modal

#### `_solicitar_credenciais_geduc()`
- Abre janela para inserir usuário e senha do GEDUC
- Utiliza credenciais padrão de `config.py` se disponíveis

#### `_salvar_horarios_geduc_bd(dados_horario, log_callback)`
- Salva horários extraídos no banco de dados
- Faz correspondência automática com disciplinas e professores existentes
- Usa UPSERT para evitar duplicatas

## Estrutura do Banco de Dados

Os horários são salvos na tabela `horarios_importados`:

```sql
CREATE TABLE `horarios_importados` (
  `id` int NOT NULL AUTO_INCREMENT,
  `turma_id` int NOT NULL,
  `dia` varchar(32) NOT NULL,
  `horario` varchar(32) NOT NULL,
  `valor` text NOT NULL,
  `disciplina_id` int DEFAULT NULL,
  `professor_id` int DEFAULT NULL,
  `geduc_turma_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ux_horario_turma` (`turma_id`,`dia`,`horario`)
) ENGINE=InnoDB;
```

### Campos:
- **turma_id**: ID da turma no sistema local
- **dia**: Dia da semana (Segunda, Terça, etc)
- **horario**: Faixa horária (ex: 07:10-08:00)
- **valor**: Texto exibido (disciplina + professor)
- **disciplina_id**: ID da disciplina no sistema local (se encontrada)
- **professor_id**: ID do professor no sistema local (se encontrado)
- **geduc_turma_id**: ID da turma no GEDUC (para referência)

## Como Usar

### Passo a Passo na Interface

1. **Abrir Interface de Horários**
   - Menu principal → "Horários Escolares"

2. **Selecionar Turma**
   - Escolher Turno (Matutino/Vespertino)
   - Selecionar Série/Ano
   - Selecionar Turma

3. **Importar do GEDUC**
   - Clicar no botão "🌐 Importar do GEDUC"
   - Inserir credenciais do GEDUC
   - Aguardar abertura do navegador
   - **IMPORTANTE**: Resolver o reCAPTCHA manualmente
   - Clicar em "Login" no navegador
   - Aguardar extração automática

4. **Acompanhar Progresso**
   - Janela de progresso mostra cada etapa:
     - Iniciando navegador
     - Fazendo login
     - Buscando horários
     - Salvando no banco de dados

5. **Verificar Resultado**
   - Após conclusão, horários são carregados automaticamente na grade
   - Mensagem de sucesso indica quantidade de horários importados

### Uso Programático

```python
from src.importadores.geduc import AutomacaoGEDUC

# Inicializar automação
automacao = AutomacaoGEDUC(headless=False)
automacao.iniciar_navegador()

# Fazer login
automacao.fazer_login("usuario", "senha", timeout_recaptcha=120)

# Listar turmas disponíveis
turmas = automacao.listar_turmas_disponiveis()
for turma in turmas:
    print(f"{turma['id']}: {turma['nome']}")

# Extrair horário de uma turma específica
dados = automacao.extrair_horario_turma("1º ANO-MATU")

if dados:
    print(f"Turma: {dados['turma_nome']}")
    print(f"Total de horários: {len(dados['horarios'])}")
    
    for h in dados['horarios']:
        print(f"{h['dia']} {h['horario']}: {h['disciplina']}")

# Fechar navegador
automacao.fechar()
```

## Mapeamento Automático

O sistema tenta fazer correspondência automática entre:

### Disciplinas
- Busca no banco local por disciplinas com nome similar
- Usa `LIKE` para correspondência parcial
- Exemplo: "LÍNGUA PORTUGUESA" no GEDUC → "LÍNGUA PORTUGUESA" local

### Professores
- Busca no banco local por professores com nome similar
- Apenas se o professor estiver especificado no GEDUC
- Usa `LIKE` para correspondência parcial

## Resolução de Problemas

### Turma não encontrada
- Verificar formato do nome da turma
- O GEDUC usa formatos como:
  - "2º ANO-MATU"
  - "6º ANO-VESP - A"
  - "1º Ano MAT"
- Conferir se a turma existe no GEDUC

### Disciplinas não mapeadas
- Disciplinas desconhecidas são salvas apenas com o nome
- `disciplina_id` fica NULL
- Necessário cadastrar disciplina no sistema local
- Ou mapear manualmente após importação

### Erro no reCAPTCHA
- Aguardar até 120 segundos para resolver
- Marcar caixa "Não sou um robô"
- Clicar em "Login" após resolver
- Se timeout, tentar novamente

### Erro de navegador
- Verificar se Google Chrome está instalado
- Baixar ChromeDriver compatível
- Colocar em: `src/importadores/chromedriver.exe`
- Ou instalar: `pip install webdriver-manager`

## Arquivos Modificados

1. **src/importadores/geduc.py**
   - Adicionados métodos para horários
   - Linhas ~1000-1200

2. **src/interfaces/horarios_escolares.py**
   - Botão de importação
   - Métodos de integração
   - Linhas ~1530-1850

## Dependências

As dependências já existem no projeto:

```txt
selenium
beautifulsoup4
webdriver-manager (opcional)
```

## Próximos Passos

### Melhorias Futuras
1. Importação em lote (múltiplas turmas)
2. Agendamento automático de importações
3. Sincronização bidirecional (exportar para GEDUC)
4. Detecção de conflitos de horários
5. Validação de carga horária por disciplina
6. Relatório de inconsistências

### Manutenção
- Monitorar mudanças na estrutura HTML do GEDUC
- Atualizar seletores se necessário
- Testar após atualizações do GEDUC
- Manter ChromeDriver atualizado

## Logs e Depuração

Os logs são gravados automaticamente:

```python
from src.core.config_logs import get_logger
logger = get_logger(__name__)

# Logs de extração
logger.info("→ Buscando horários...")
logger.error("✗ Erro ao extrair")
```

Verificar logs em:
- Console da aplicação
- Arquivo de log (se configurado)

## Suporte

Para problemas ou dúvidas:
1. Verificar logs de erro
2. Consultar documentação do GEDUC
3. Revisar código em `src/importadores/geduc.py`
4. Testar manualmente no navegador

---

**Data de Implementação**: 1 de janeiro de 2026  
**Versão**: 1.0  
**Status**: ✅ Implementado e Testado
