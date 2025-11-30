from config_logs import get_logger
logger = get_logger(__name__)
"""
Resumo das correções realizadas
================================

PROBLEMA ORIGINAL:
Ao tentar gerar PDF do 3º bimestre pelo menu "Gerenciamento de Notas",
aparecia a mensagem: "Nenhum dado encontrado para o bimestre 3º bimestre 
e nível iniciais no ano 2025"

CAUSA:
A função construir_consulta_sql() foi modificada para aceitar nomes de série
específicos (ex: "3º Ano"), mas a função gerar_relatorio_notas() estava 
passando condições SQL (ex: "s.id <= 7" para séries iniciais).

SOLUÇÃO IMPLEMENTADA:
Modificada a linha 245 em NotaAta.py para aceitar AMBOS os formatos:
- Condições SQL: "s.id <= 7" ou "s.id > 7"  
- Nomes de série: "3º Ano", "4º Ano", etc.

A linha agora detecta automaticamente o formato:
```python
AND {filtro_serie if ('<' in filtro_serie or '>' in filtro_serie or 's.nome' in filtro_serie) 
    else f"s.nome = '{filtro_serie}'"}
```

RESULTADO:
✅ PDFs do menu "Gerenciamento de Notas" agora são gerados corretamente
✅ Professores aparecem ordenados por quantidade de disciplinas
✅ Apenas primeiro e segundo nome dos professores são exibidos
✅ Formato de exibição: "Nome1 e Nome2" ou "Nome1, Nome2 e Nome3"

TESTES REALIZADOS:
1. debug_menu_relatorio.py - Simulou geração pelo menu: SUCESSO
2. verificar_professores_pdf_menu.py - Verificou professores no PDF: SUCESSO
   - Fernanda Carneiro e Josué
   - Maria Ferreira e Sebastiana
   - Ana Lúcia e Sebastiana Santos
   - Luisiane Cristina e Sebastiana

STATUS: ✅ RESOLVIDO
"""

logger.info(__doc__)