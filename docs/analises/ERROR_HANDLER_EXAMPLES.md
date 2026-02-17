# Exemplos de Uso - Sistema de Tratamento de Erros

Este documento demonstra como usar o sistema robusto de tratamento de erros implementado em `utils/error_handler.py`.

## 📚 Índice

1. [Instalação do Handler Global](#instalação-do-handler-global)
2. [Decorator @safe_action](#decorator-safe_action)
3. [Decorator @safe_db_operation](#decorator-safe_db_operation)
4. [Context Manager ErrorContext](#context-manager-errorcontext)
5. [Decorator @retry_on_error](#decorator-retry_on_error)
6. [Integração com Application](#integração-com-application)

---

## Instalação do Handler Global

O handler global é instalado automaticamente ao importar o módulo:

```python
from utils.error_handler import ErrorHandler

# O handler já está instalado via sys.excepthook
# Todas as exceções não capturadas serão logadas e mostradas ao usuário
```

Para instalar manualmente (caso necessário):

```python
from utils.error_handler import ErrorHandler

ErrorHandler.install()
```

---

## Decorator @safe_action

Use `@safe_action` para proteger funções de UI contra erros:

### Exemplo Básico

```python
from utils.error_handler import safe_action

@safe_action(error_title="Erro ao Cadastrar Aluno")
def cadastrar_aluno():
    # Código que pode falhar
    dados = obter_dados_formulario()
    validar_dados(dados)
    salvar_no_banco(dados)
    messagebox.showinfo("Sucesso", "Aluno cadastrado com sucesso!")
```

### Com Customizações

```python
@safe_action(
    error_title="Erro ao Validar CPF",
    error_message="CPF inválido. Use apenas números.",
    show_dialog=True,
    return_on_error=False,
    log_level="warning"
)
def validar_cpf(cpf: str) -> bool:
    if not cpf.isdigit() or len(cpf) != 11:
        raise ValueError("CPF deve ter 11 dígitos")
    return True
```

### Sem Dialog (apenas log)

```python
@safe_action(show_dialog=False, return_on_error=None)
def operacao_background():
    # Operação que não deve interromper o usuário
    sincronizar_dados()
```

---

## Decorator @safe_db_operation

Use `@safe_db_operation` para operações de banco de dados:

### Exemplo com Rollback Automático

```python
from utils.error_handler import safe_db_operation

@safe_db_operation(error_title="Erro ao Salvar Matrícula", rollback=True)
def criar_matricula(conn, aluno_id, turma_id):
    cursor = conn.cursor()
    
    # Inserir matrícula
    cursor.execute(
        "INSERT INTO matriculas (aluno_id, turma_id) VALUES (%s, %s)",
        (aluno_id, turma_id)
    )
    
    # Atualizar contador de vagas
    cursor.execute(
        "UPDATE turmas SET vagas_ocupadas = vagas_ocupadas + 1 WHERE id = %s",
        (turma_id,)
    )
    
    conn.commit()
    return cursor.lastrowid
```

Se qualquer operação falhar, o rollback é executado automaticamente.

---

## Context Manager ErrorContext

Use `ErrorContext` para operações que precisam de cleanup:

### Exemplo: Geração de Arquivo Temporário

```python
from utils.error_handler import ErrorContext
import tempfile
import os

def gerar_relatorio():
    temp_file = None
    
    def cleanup():
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
            print("Arquivo temporário removido")
    
    with ErrorContext("Gerando relatório", cleanup=cleanup):
        # Criar arquivo temporário
        temp_file = tempfile.mktemp(suffix='.pdf')
        
        # Gerar relatório (pode falhar)
        gerar_pdf(temp_file)
        
        # Mover para local final
        mover_arquivo(temp_file, 'relatorio_final.pdf')
        
        # cleanup é executado automaticamente mesmo se falhar
```

### Exemplo: Operação com Conexão

```python
with ErrorContext("Atualizando registros", show_error=True):
    conn = conectar_bd()
    cursor = conn.cursor()
    
    for registro in registros:
        cursor.execute("UPDATE ...", registro)
    
    conn.commit()
    # Se falhar, o erro é logado e mostrado ao usuário
```

---

## Decorator @retry_on_error

Use `@retry_on_error` para operações que podem falhar temporariamente:

### Exemplo: Conexão de Rede

```python
from utils.error_handler import retry_on_error
import requests

@retry_on_error(
    max_attempts=3,
    delay=2.0,
    exceptions=(requests.ConnectionError, requests.Timeout)
)
def enviar_dados_servidor(dados):
    response = requests.post('https://api.example.com/data', json=dados)
    response.raise_for_status()
    return response.json()
```

### Exemplo: Operação de Arquivo

```python
@retry_on_error(max_attempts=5, delay=0.5, exceptions=(PermissionError, IOError))
def salvar_arquivo(caminho, conteudo):
    with open(caminho, 'w') as f:
        f.write(conteudo)
```

---

## Integração com Application

### main.py

```python
from utils.error_handler import ErrorHandler

def main():
    # Handler global já foi instalado ao importar
    
    app = Application()
    app.initialize()
    app.run()

if __name__ == "__main__":
    main()
```

### Exemplo: Botão de Cadastro

```python
from utils.error_handler import safe_action

class InterfaceCadastroAluno:
    def __init__(self, root):
        self.root = root
        
        # Botão de salvar com proteção de erro
        btn_salvar = tk.Button(
            root,
            text="Salvar",
            command=self.salvar_aluno_safe
        )
        btn_salvar.pack()
    
    @safe_action(error_title="Erro ao Cadastrar")
    def salvar_aluno_safe(self):
        """Versão protegida do método de salvar."""
        dados = self.obter_dados_formulario()
        
        # Validar com Pydantic
        aluno = AlunoCreate(**dados)
        
        # Salvar no banco
        aluno_id = cadastrar_aluno_service(aluno)
        
        # Atualizar UI
        self.limpar_formulario()
        self.atualizar_lista()
        
        messagebox.showinfo("Sucesso", f"Aluno #{aluno_id} cadastrado!")
```

### Exemplo: Operação de Banco Complexa

```python
from utils.error_handler import safe_db_operation
from db.connection import get_connection

@safe_db_operation(error_title="Erro ao Transferir Aluno", rollback=True)
def transferir_aluno(aluno_id, turma_origem_id, turma_destino_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Remover da turma origem
        cursor.execute(
            "DELETE FROM matriculas WHERE aluno_id = %s AND turma_id = %s",
            (aluno_id, turma_origem_id)
        )
        
        # Adicionar na turma destino
        cursor.execute(
            "INSERT INTO matriculas (aluno_id, turma_id, data_matricula) "
            "VALUES (%s, %s, NOW())",
            (aluno_id, turma_destino_id)
        )
        
        # Atualizar contadores
        cursor.execute(
            "UPDATE turmas SET vagas_ocupadas = vagas_ocupadas - 1 WHERE id = %s",
            (turma_origem_id,)
        )
        cursor.execute(
            "UPDATE turmas SET vagas_ocupadas = vagas_ocupadas + 1 WHERE id = %s",
            (turma_destino_id,)
        )
        
        conn.commit()
        return True
```

---

## Tratamento de Erros Específicos

### ValidationError (Pydantic)

```python
from pydantic import BaseModel, validator
from utils.error_handler import safe_action

class AlunoCreate(BaseModel):
    nome: str
    cpf: str
    
    @validator('cpf')
    def validar_cpf(cls, v):
        if not v.isdigit() or len(v) != 11:
            raise ValueError('CPF deve ter 11 dígitos numéricos')
        return v

@safe_action(error_title="Erro de Validação")
def processar_aluno():
    # Se a validação falhar, uma mensagem amigável é mostrada
    aluno = AlunoCreate(nome="João", cpf="123")  # Vai falhar
```

### ImportError

```python
@safe_action(error_title="Módulo Não Encontrado")
def gerar_grafico():
    import matplotlib.pyplot as plt  # Pode não estar instalado
    plt.plot([1, 2, 3])
    plt.show()
```

### PermissionError

```python
@safe_action(error_title="Erro de Permissão")
def salvar_configuracao():
    with open('C:\\Windows\\System32\\config.txt', 'w') as f:
        f.write("teste")  # Vai falhar por falta de permissão
```

---

## Boas Práticas

### ✅ DO

```python
# Usar decorators em funções de UI
@safe_action(error_title="Erro ao Salvar")
def salvar_dados():
    # ...

# Usar context manager para cleanup
with ErrorContext("Operação", cleanup=cleanup_func):
    # ...

# Usar retry para operações temporárias
@retry_on_error(max_attempts=3)
def operacao_rede():
    # ...
```

### ❌ DON'T

```python
# Não capturar Exception genérico sem relanç
ar
try:
    operacao()
except Exception:
    pass  # ❌ Erro silencioso

# Não usar try/except quando @safe_action é suficiente
def func():
    try:  # ❌ Redundante
        @safe_action()
        def inner():
            # ...
    except:
        pass
```

---

## Configuração de Logging

Os erros são logados automaticamente. Para customizar:

```python
# config_logs.py (já existe)
import logging

def get_logger(name):
    logger = logging.getLogger(name)
    # ... configuração
    return logger
```

---

## Testando o Sistema

Execute os testes integrados:

```bash
python -c "import sys; sys.path.insert(0, '.'); from utils import error_handler; print('OK')"
```

Ou teste manualmente:

```python
from utils.error_handler import safe_action

@safe_action(show_dialog=False, return_on_error="ERRO")
def teste():
    raise ValueError("Erro de teste")

resultado = teste()
print(resultado)  # Deve printar "ERRO"
```

---

## Troubleshooting

### Problema: Diálogos de erro não aparecem

**Solução**: Verificar que `show_dialog=True` (padrão) e que Tkinter está inicializado.

### Problema: Rollback não funciona

**Solução**: Passar a conexão como primeiro argumento da função decorada com `@safe_db_operation`.

### Problema: Retry infinito

**Solução**: Verificar que a exceção lançada está na tupla `exceptions` do decorator.

---

**Implementado em**: Sprint 17  
**Data**: 25/11/2025  
**Módulo**: `utils/error_handler.py`
