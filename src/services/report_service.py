"""Fachada de compatibilidade - re-exporta todos os simbolos do pacote `src.services.reports`.

Callers existentes que fazem `from src.services.report_service import X` ou
`from services import report_service; report_service.X(...)` continuam funcionando
sem necessidade de alteracao.

A implementacao real esta dividida em submodulos dentro de `src/services/reports/`.
"""

# Re-exportar TUDO do pacote de relatorios para compatibilidade total
from src.services.reports import *  # noqa: F401, F403

# Garantir que os simbolos internos (_prefixados) tambem fiquem acessiveis
from src.services.reports._utils import _find_image_in_repo, _ensure_legacy_module  # noqa: F401
from src.services.reports.boletim import (  # noqa: F401
    _impl_gerar_relatorio_notas_com_assinatura,
    _impl_lista_notas,
)
from src.services.reports.historico import _impl_gerar_relatorio_series_faltantes  # noqa: F401
from src.services.reports.frequencia import (  # noqa: F401
    _impl_gerar_tabela_frequencia,
    _impl_lista_frequencia,
)
from src.services.reports.folha_ponto import (  # noqa: F401
    _impl_gerar_folhas_de_ponto,
    _impl_gerar_resumo_ponto,
)
from src.services.reports.outros import _impl_gerar_lista_reuniao  # noqa: F401