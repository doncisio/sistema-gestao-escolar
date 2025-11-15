# Sistema Gestão Escolar

![CI](https://github.com/doncisio/sistema-gestao-escolar/actions/workflows/ci.yml/badge.svg?branch=refactor/modularizacao)

Pequeno repositório para o sistema de gestão escolar. Esta branch contém mudanças de refatoração e testes.

Como rodar os testes localmente:

```powershell
# criar e ativar virtualenv, por exemplo
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # se existir
pip install pytest
pytest -q
```

Notas:
- O workflow de CI roda `pytest` em Python 3.10, 3.11 e 3.12.
- Branch de trabalho atual: `refactor/modularizacao` (usada no badge do CI).
