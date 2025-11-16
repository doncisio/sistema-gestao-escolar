Título: Refactor: migrar gerar_folhas_de_ponto para services (testável)

Descrição:
- Adiciona wrapper testável `services/report_service.gerar_folhas_de_ponto` que prefere mocks em `sys.modules`.
- Atualiza `main.py` para delegar ao serviço com fallback seguro para o módulo legado.
- Adiciona testes unitários para validar delegação (vários testes em `tests/`).
- Inclui `pytest.ini` para suprimir DeprecationWarnings externos.

- Migra `lista_frequencia` para `services/report_service.py`:
  - Implementação interna `_impl_lista_frequencia()` no serviço (evita executar código legado no import).
  - `gerar_lista_frequencia()` agora prefere mocks injetados em `sys.modules` e usa a implementação interna antes do fallback legado.
  - Adiciona teste `tests/test_report_service_lista_frequencia.py` que injeta mock com `__spec__` e valida delegação.

Resultado: suíte de testes local: 12 passed in 2.3s.

Notas de teste:
- Os mocks precisam ser injetados em `sys.modules` (com `__spec__`) antes de importar `services.report_service`, ou forçar reimport no teste.

Como criar o PR (opções):

1) Usando GitHub CLI (recomendado)

```powershell
gh pr create --base main --head refactor/modularizacao --title "Refactor: migrar gerar_folhas_de_ponto para services (testável)" --body (Get-Content PR_BODY.md -Raw)
```

2) Usando a API do GitHub (PowerShell) — defina `GITHUB_TOKEN` antes:

```powershell
$owner='doncisio'; $repo='sistema-gestao-escolar'
$url="https://api.github.com/repos/$owner/$repo/pulls"
$body=@{
  title='Refactor: migrar gerar_folhas_de_ponto para services (testável)'
  head='refactor/modularizacao'
  base='main'
  body=(Get-Content PR_BODY.md -Raw)
}
$json=$body | ConvertTo-Json -Depth 10
Invoke-RestMethod -Method Post -Uri $url -Headers @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'automation-script' } -Body $json -ContentType 'application/json'
```

3) Criar manualmente no navegador:

Abra: https://github.com/doncisio/sistema-gestao-escolar/compare/main...refactor/modularizacao?expand=1

--
Arquivo gerado automaticamente para ajudar na criação do PR.
