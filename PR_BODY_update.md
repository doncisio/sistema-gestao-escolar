Atualização: migração incremental do gerador de frequência

Resumo das mudanças:
- Adiciona wrapper `services/report_service.gerar_tabela_frequencia` que prefere mocks em `sys.modules` (compatível com padrão de testes do repositório).
- Implementa `_impl_gerar_tabela_frequencia()` (versão migrada que usa `Lista_atualizada.fetch_student_data` e helpers de PDF em `services.utils.pdf`).
- Adiciona teste `tests/test_report_service_gerar_tabela_frequencia.py` que injeta um mock em `sys.modules` e valida delegação.
- Corrige aviso do Pylance usando `cast(Any, _mod)` ao acessar atributos dinâmicos de módulos injetados.

Testes locais: `python -m pytest -q`  13 passed in 1.66s

Notas:
- Mantivemos fallback para os módulos legados (`gerar_tabela_frequencia` / `lista_frequencia`) como último recurso.
- Esta PR continua pequena e atômica para facilitar review. Se desejar, posso extrair partes em commits menores.
