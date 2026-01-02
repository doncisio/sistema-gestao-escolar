# Exemplos de Integração - Importação de Horários GEDUC

## Integração com Outros Módulos

### 1. Importação Automática em Cadastro de Notas

Se você quiser adicionar importação de horários ao módulo de cadastro de notas:

```python
# Em src/interfaces/cadastro_notas.py

def importar_horarios_turma_atual(self):
    """Importa horários da turma selecionada do GEDUC"""
    if not self.cb_turma.get():
        messagebox.showwarning("Atenção", "Selecione uma turma primeiro!")
        return
    
    from src.importadores.geduc import AutomacaoGEDUC
    import threading
    
    # Construir nome da turma para busca
    serie = self.cb_serie.get()
    turma = self.cb_turma.get()
    nome_busca = f"{serie} {turma}"
    
    def executar():
        automacao = AutomacaoGEDUC()
        try:
            automacao.iniciar_navegador()
            # Login com credenciais armazenadas
            automacao.fazer_login(usuario, senha)
            dados = automacao.extrair_horario_turma(nome_busca)
            
            if dados:
                # Processar dados
                self._salvar_horarios(dados)
                messagebox.showinfo("Sucesso", "Horários importados!")
        finally:
            automacao.fechar()
    
    threading.Thread(target=executar, daemon=True).start()
```

### 2. Sincronização em Lote de Múltiplas Turmas

```python
# script: sincronizar_todas_turmas.py

from src.importadores.geduc import AutomacaoGEDUC
from src.core.conexao import conectar_bd

def sincronizar_todas_turmas():
    """Sincroniza horários de todas as turmas do sistema"""
    
    # Conectar ao banco
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    
    # Buscar todas as turmas ativas
    cursor.execute("""
        SELECT t.id, t.nome, s.nome as serie, t.turno
        FROM turmas t
        INNER JOIN series s ON t.serie_id = s.id
        WHERE t.ativo = 1
    """)
    turmas = cursor.fetchall()
    
    # Iniciar automação
    automacao = AutomacaoGEDUC()
    automacao.iniciar_navegador()
    automacao.fazer_login("usuario", "senha")
    
    importadas = 0
    erros = []
    
    for turma in turmas:
        # Construir nome para busca
        nome_busca = f"{turma['serie']} {turma['turno']} {turma['nome']}"
        
        print(f"Importando: {nome_busca}...")
        
        try:
            dados = automacao.extrair_horario_turma(nome_busca)
            
            if dados:
                salvar_horarios_bd(dados, turma['id'])
                importadas += 1
                print(f"  ✓ OK - {len(dados['horarios'])} horários")
            else:
                erros.append(f"{nome_busca}: Não encontrada")
                print(f"  ✗ Não encontrada")
                
        except Exception as e:
            erros.append(f"{nome_busca}: {str(e)}")
            print(f"  ✗ Erro: {e}")
    
    automacao.fechar()
    
    print(f"\n{'='*60}")
    print(f"Concluído!")
    print(f"  Importadas: {importadas}/{len(turmas)}")
    print(f"  Erros: {len(erros)}")
    
    if erros:
        print("\nErros:")
        for erro in erros:
            print(f"  - {erro}")

if __name__ == "__main__":
    sincronizar_todas_turmas()
```

### 3. Validação de Horários Importados

```python
# Em qualquer módulo

def validar_horarios_turma(turma_id):
    """Valida horários de uma turma"""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    
    # Buscar horários
    cursor.execute("""
        SELECT dia, horario, valor, disciplina_id, professor_id
        FROM horarios_importados
        WHERE turma_id = %s
        ORDER BY 
            FIELD(dia, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'),
            horario
    """, (turma_id,))
    
    horarios = cursor.fetchall()
    
    problemas = []
    
    # Verificar disciplinas não mapeadas
    for h in horarios:
        if not h['disciplina_id']:
            problemas.append(
                f"{h['dia']} {h['horario']}: "
                f"Disciplina '{h['valor']}' não mapeada"
            )
    
    # Verificar sobreposições
    ocupacao = {}
    for h in horarios:
        chave = f"{h['dia']}_{h['horario']}"
        if chave in ocupacao:
            problemas.append(
                f"Sobreposição: {h['dia']} {h['horario']}"
            )
        ocupacao[chave] = h
    
    # Verificar carga horária
    disciplinas_count = {}
    for h in horarios:
        disc = h['valor'].split('\n')[0]  # Pegar só disciplina
        disciplinas_count[disc] = disciplinas_count.get(disc, 0) + 1
    
    # Relatório
    print(f"Validação de Horários - Turma {turma_id}")
    print(f"Total de horários: {len(horarios)}")
    print(f"\nCarga horária por disciplina:")
    for disc, count in sorted(disciplinas_count.items()):
        print(f"  {disc}: {count}h/semana")
    
    if problemas:
        print(f"\n⚠️ Problemas encontrados ({len(problemas)}):")
        for p in problemas:
            print(f"  - {p}")
    else:
        print("\n✓ Nenhum problema encontrado!")
    
    cursor.close()
    conn.close()
```

### 4. Exportação de Horários para PDF/Excel

```python
# Adicionar ao módulo de horários

def exportar_horarios_turma_pdf(turma_id):
    """Gera PDF com horários da turma"""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    from reportlab.lib import colors
    
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    
    # Buscar dados
    cursor.execute("""
        SELECT h.dia, h.horario, h.valor,
               t.nome as turma, s.nome as serie
        FROM horarios_importados h
        INNER JOIN turmas t ON h.turma_id = t.id
        INNER JOIN series s ON t.serie_id = s.id
        WHERE h.turma_id = %s
    """, (turma_id,))
    
    horarios = cursor.fetchall()
    
    if not horarios:
        print("Nenhum horário encontrado")
        return
    
    # Organizar dados em grade
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
    horarios_unicos = sorted(set(h['horario'] for h in horarios))
    
    # Montar matriz
    dados = [['Horário'] + dias]
    
    for horario in horarios_unicos:
        linha = [horario]
        for dia in dias:
            # Buscar disciplina para este dia/horário
            encontrado = next(
                (h['valor'] for h in horarios 
                 if h['dia'] == dia and h['horario'] == horario),
                ''
            )
            linha.append(encontrado)
        dados.append(linha)
    
    # Gerar PDF
    turma_nome = horarios[0]['turma']
    serie_nome = horarios[0]['serie']
    filename = f"horario_{serie_nome}_{turma_nome}.pdf"
    
    doc = SimpleDocTemplate(
        filename, 
        pagesize=landscape(A4),
        title=f"Horário - {serie_nome} {turma_nome}"
    )
    
    tabela = Table(dados)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    doc.build([tabela])
    print(f"PDF gerado: {filename}")
    
    cursor.close()
    conn.close()
```

### 5. API REST para Horários (Flask)

```python
# api/horarios.py

from flask import Flask, jsonify, request
from src.core.conexao import conectar_bd

app = Flask(__name__)

@app.route('/api/horarios/<int:turma_id>', methods=['GET'])
def obter_horarios(turma_id):
    """Retorna horários de uma turma em JSON"""
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT dia, horario, valor, disciplina_id, professor_id
        FROM horarios_importados
        WHERE turma_id = %s
        ORDER BY 
            FIELD(dia, 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta'),
            horario
    """, (turma_id,))
    
    horarios = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'turma_id': turma_id,
        'total': len(horarios),
        'horarios': horarios
    })

@app.route('/api/horarios/importar', methods=['POST'])
def importar_horarios():
    """Endpoint para importar horários do GEDUC"""
    data = request.json
    
    turma_nome = data.get('turma_nome')
    turma_id = data.get('turma_id')
    
    if not turma_nome or not turma_id:
        return jsonify({'erro': 'Dados incompletos'}), 400
    
    try:
        from src.importadores.geduc import AutomacaoGEDUC
        
        automacao = AutomacaoGEDUC(headless=True)
        automacao.iniciar_navegador()
        automacao.fazer_login(usuario, senha)
        
        dados = automacao.extrair_horario_turma(turma_nome)
        
        if dados:
            salvar_horarios_bd(dados, turma_id)
            return jsonify({
                'sucesso': True,
                'total_importado': len(dados['horarios'])
            })
        else:
            return jsonify({'erro': 'Turma não encontrada'}), 404
            
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    
    finally:
        automacao.fechar()

if __name__ == '__main__':
    app.run(debug=True)
```

### 6. Agendamento Automático (Windows Task Scheduler)

```python
# scripts/agendador_horarios.py

"""
Agendar com Task Scheduler:
- Trigger: Diariamente às 02:00
- Ação: python C:\gestao\scripts\agendador_horarios.py
"""

import logging
from datetime import datetime
from src.importadores.geduc import AutomacaoGEDUC
from src.core.conexao import conectar_bd

# Configurar logging
logging.basicConfig(
    filename='logs/agendador_horarios.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def executar_sincronizacao():
    """Executa sincronização agendada"""
    logging.info("="*60)
    logging.info("Iniciando sincronização agendada de horários")
    
    try:
        # Buscar turmas ativas
        conn = conectar_bd()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT t.id, t.nome, s.nome as serie, t.turno
            FROM turmas t
            INNER JOIN series s ON t.serie_id = s.id
            WHERE t.ativo = 1
        """)
        turmas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        logging.info(f"Encontradas {len(turmas)} turmas ativas")
        
        # Processar cada turma
        automacao = AutomacaoGEDUC(headless=True)
        automacao.iniciar_navegador()
        automacao.fazer_login("usuario", "senha")
        
        for turma in turmas:
            try:
                nome_busca = f"{turma['serie']} {turma['turno']} {turma['nome']}"
                dados = automacao.extrair_horario_turma(nome_busca)
                
                if dados:
                    salvar_horarios_bd(dados, turma['id'])
                    logging.info(f"✓ {nome_busca}: {len(dados['horarios'])} horários")
                else:
                    logging.warning(f"✗ {nome_busca}: Não encontrada")
                    
            except Exception as e:
                logging.error(f"✗ {nome_busca}: {str(e)}")
        
        automacao.fechar()
        logging.info("Sincronização concluída com sucesso")
        
    except Exception as e:
        logging.error(f"Erro fatal na sincronização: {str(e)}")
        raise

if __name__ == "__main__":
    executar_sincronizacao()
```

## Dicas de Integração

1. **Sempre use try/finally** para garantir que o navegador seja fechado
2. **Use headless=True** em ambientes de produção/automação
3. **Implemente cache** de credenciais de forma segura
4. **Valide dados** antes de salvar no banco
5. **Registre logs** de todas as operações
6. **Trate exceções** específicas do Selenium
7. **Implemente retry** para operações de rede

## Segurança

```python
# Nunca commite credenciais!
# Use variáveis de ambiente:

import os

GEDUC_USER = os.getenv('GEDUC_USER')
GEDUC_PASS = os.getenv('GEDUC_PASS')

# Ou arquivo de configuração fora do repositório:
import json

with open('config_local.json') as f:
    config = json.load(f)
    GEDUC_USER = config['geduc']['usuario']
    GEDUC_PASS = config['geduc']['senha']
```

---

**Estes exemplos demonstram como integrar a funcionalidade de importação de horários em diversos contextos do sistema.**
