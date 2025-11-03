# Sistema de Backup Automático

## 📋 Visão Geral

O sistema de backup automático foi implementado para garantir que o banco de dados seja copiado diariamente de forma automática, sem intervenção manual.

## ⚙️ Configuração

### Horários de Execução
- **Horários agendados**: 14:05 e 17:00 (todos os dias)
- **Backup final**: Ao fechar o programa
- **Janela permitida**: 14:00 às 19:00
- O backup agendado só será executado se o sistema estiver dentro desta janela de horário
- O backup final ao fechar é executado independente do horário

### Locais de Backup
O backup é salvo em dois locais:
1. **Local**: `backup_redeescola.sql` (pasta do projeto)
2. **Google Drive**: `G:\Meu Drive\NADIR_2025\Backup\backup_redeescola.sql`

## 🚀 Como Funciona

### Inicialização Automática
Quando você inicia o sistema (`main.py`), o backup automático é iniciado automaticamente em segundo plano (thread separada), não interferindo na interface gráfica.

### Execução Automática
- O sistema verifica a cada 1 minuto se há tarefas agendadas
- Às 14:05 e 17:00 de cada dia, o backup é executado automaticamente
- Se o sistema não estiver rodando nestes horários, o backup não será executado
- **NOVO**: Ao fechar o programa, um backup final é executado automaticamente

### Logs
O sistema exibe mensagens no console informando:
- Quando o sistema de backup foi iniciado
- Quando um backup automático é executado
- Status de sucesso ou falha do backup

## 📝 Funções Disponíveis

### `iniciar_backup_automatico()`
Inicia o sistema de backup automático. Já é chamada automaticamente no `main.py`.

### `parar_backup_automatico(executar_backup_final=True)`
Para o sistema de backup automático. Por padrão, executa um backup final antes de encerrar.
- `executar_backup_final=True`: Executa backup final antes de parar
- `executar_backup_final=False`: Para imediatamente sem backup final

### `status_backup_automatico()`
Exibe o status atual do sistema de backup automático.

### `executar_backup_automatico()`
Executa um backup imediatamente (se estiver dentro do horário permitido).

## 🔧 Personalização

### Alterar Horário de Execução
Para alterar o horário, edite o arquivo `Seguranca.py`, função `agendar_backup_diario()`:

```python
# Altere "14:05" para o horário desejado (formato 24h)
schedule.every().day.at("14:05").do(executar_backup_automatico)
```

### Alterar Janela de Horário Permitida
Para alterar a janela de horário (14h-19h), edite a função `executar_backup_automatico()`:

```python
# Altere os valores 14 e 19 conforme necessário
if 14 <= hora_atual < 19:
```

### Executar Backup em Múltiplos Horários
O sistema já está configurado para executar em dois horários (14:05 e 17:00). Para adicionar mais horários:

```python
def agendar_backup_diario():
    schedule.every().day.at("14:05").do(executar_backup_automatico)
    schedule.every().day.at("17:00").do(executar_backup_automatico)
    schedule.every().day.at("19:00").do(executar_backup_automatico)  # Exemplo
    # Adicione mais horários conforme necessário
```

## 📊 Monitoramento

### Ver Status do Sistema
Para verificar se o backup automático está ativo, você pode adicionar um botão na interface ou executar via console Python:

```python
import Seguranca
Seguranca.status_backup_automatico()
```

### Logs de Execução
Todas as operações de backup são registradas no console com timestamp:
```
[23/10/2025 14:05:00] Iniciando backup automático...
✓ Backup local salvo em: backup_redeescola.sql
✓ Backup no Google Drive salvo em: G:\Meu Drive\NADIR_2025\Backup\backup_redeescola.sql
✓ Backup realizado com sucesso!
[23/10/2025 14:05:05] Backup automático concluído com sucesso!
```

## ⚠️ Observações Importantes

1. **O sistema precisa estar rodando**: O backup agendado (14:05 e 17:00) só funciona enquanto o `main.py` estiver em execução
2. **Backup ao fechar**: Um backup final é executado automaticamente ao fechar o programa, garantindo que os dados mais recentes sejam salvos
3. **Google Drive**: Se o Google Drive não estiver montado/sincronizado, o backup será salvo apenas localmente
4. **Credenciais**: Certifique-se de que o arquivo `.env` está configurado corretamente com as credenciais do banco
5. **Thread daemon**: O backup roda em uma thread daemon, ou seja, será encerrado automaticamente quando o programa principal fechar (após executar o backup final)

## 🔒 Segurança

- As credenciais do banco de dados são carregadas do arquivo `.env`
- Nunca compartilhe o arquivo de backup sem criptografia adequada
- O arquivo `.env` não deve ser incluído no controle de versão (Git)

## 🐛 Solução de Problemas

### Backup não está executando
1. Verifique se o sistema está rodando durante o horário agendado
2. Verifique os logs no console
3. Execute `Seguranca.status_backup_automatico()` para verificar o status

### Erro "Credenciais incompletas"
- Verifique se o arquivo `.env` existe e contém todas as variáveis necessárias:
  - DB_USER
  - DB_PASSWORD
  - DB_HOST
  - DB_NAME

### Backup não está sendo salvo no Google Drive
- Verifique se o Google Drive está montado corretamente
- Confirme se o caminho `G:\Meu Drive\NADIR_2025\Backup\` existe
- O sistema continuará funcionando salvando apenas localmente

## 📦 Dependências

```
schedule>=1.1.0
python-dotenv>=0.19.0
mysql-connector-python>=8.0.32
```

Todas as dependências são instaladas automaticamente via `requirements.txt`.
