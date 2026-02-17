# Instruções para Limpeza Manual do Arquivo InterfaceEdicaoAluno.py

## Problema
O arquivo `InterfaceEdicaoAluno.py` ficou com código duplicado após as edições automáticas.

## Solução Manual

### Passo 1: Abrir o arquivo
Abra o arquivo `InterfaceEdicaoAluno.py` em um editor de texto.

### Passo 2: Localizar o método `editar_matricula`
Procure por `def editar_matricula(self):` (linha ~936).

O método correto deve ter apenas este conteúdo:
```python
    def editar_matricula(self):
        # Usar interface unificada de matrícula
        try:
            from interface_matricula_unificada import abrir_interface_matricula
            
            # Obter nome do aluno
            cast(Any, self.cursor).execute("SELECT nome FROM alunos WHERE id = %s", (self.aluno_id,))
            nome_aluno = cast(Any, self.cursor).fetchone()[0]
            
            # Callback para recarregar dados após salvar
            def ao_salvar():
                self.carregar_dados_matricula()
            
            # Abrir interface unificada
            abrir_interface_matricula(
                parent=self.master,
                aluno_id=self.aluno_id,
                nome_aluno=nome_aluno,
                colors={
                    'co0': self.co0, 'co1': self.co1, 'co2': self.co2, 'co3': self.co3,
                    'co4': self.co4, 'co5': self.co5, 'co6': self.co6, 'co7': self.co7
                },
                conn=self.conn,
                cursor=self.cursor,
                callback_sucesso=ao_salvar
            )
            
        except Exception as e:
            logger.exception(f"Erro ao abrir edição de matrícula: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir edição: {str(e)}")
```

### Passo 3: Remover código duplicado
Se houver código adicional após o método `editar_matricula` e antes do método `nova_matricula`, remova-o.

### Passo 4: Localizar o método `nova_matricula`
Deve haver APENAS UM método `nova_matricula`.  Se houver dois, mantenha apenas o segundo (o mais completo).

O método correto deve ter este conteúdo:
```python
    def nova_matricula(self):
        # Usar interface unificada de matrícula
        try:
            from interface_matricula_unificada import abrir_interface_matricula
            
            # Obter nome do aluno
            cast(Any, self.cursor).execute("SELECT nome FROM alunos WHERE id = %s", (self.aluno_id,))
            nome_aluno = cast(Any, self.cursor).fetchone()[0]
            
            # Callback para recarregar dados após salvar
            def ao_salvar():
                self.carregar_dados_matricula()
            
            # Abrir interface unificada
            abrir_interface_matricula(
                parent=self.master,
                aluno_id=self.aluno_id,
                nome_aluno=nome_aluno,
                colors={
                    'co0': self.co0, 'co1': self.co1, 'co2': self.co2, 'co3': self.co3,
                    'co4': self.co4, 'co5': self.co5, 'co6': self.co6, 'co7': self.co7
                },
                conn=self.conn,
                cursor=self.cursor,
                callback_sucesso=ao_salvar
            )
            
        except Exception as e:
            logger.exception(f"Erro ao abrir nova matrícula: {e}")
            messagebox.showerror("Erro", f"Não foi possível realizar a matrícula: {str(e)}")
```

### Passo 5: Salvar o arquivo
Salve o arquivo após remover todo o código duplicado.

## Alternativa Automática

Execute o seguinte comando PowerShell para fazer a limpeza automaticamente:

```powershell
python -c "
import re

# Ler arquivo
with open('c:/gestao/InterfaceEdicaoAluno.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar primeira ocorrência de 'def nova_matricula'
first_nova = content.find('    def nova_matricula(self):')
if first_nova == -1:
    print('Método nova_matricula não encontrado')
    exit(1)

# Encontrar segunda ocorrência
second_nova = content.find('    def nova_matricula(self):', first_nova + 10)
if second_nova == -1:
    print('Apenas uma ocorrência encontrada - arquivo já está limpo')
    exit(0)

# Remover tudo entre a primeira e segunda ocorrência
cleaned = content[:first_nova] + content[second_nova:]

# Salvar arquivo limpo
with open('c:/gestao/InterfaceEdicaoAluno.py', 'w', encoding='utf-8') as f:
    f.write(cleaned)

print('Arquivo limpo com sucesso!')
"
```

## Verificação

Após a limpeza, verifique:
1. Há apenas UM método `def editar_matricula`
2. Há apenas UM método `def nova_matricula`
3. Ambos chamam `abrir_interface_matricula` da `interface_matricula_unificada`
4. Não há código duplicado entre os métodos
