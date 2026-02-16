"""Pacote de relatórios — dividido por domínio a partir do report_service.py monolítico.

Todos os símbolos públicos são re-exportados aqui para manter compatibilidade
com callers existentes que fazem ``from src.services.report_service import X``.
"""

from src.services.reports._utils import _find_image_in_repo, _ensure_legacy_module  # noqa: F401
from src.services.reports.boletim import (  # noqa: F401
    gerar_relatorio_avancado_com_assinatura,
    gerar_relatorio_notas,
    gerar_boletim,
    gerar_boletim_interno,
    gerar_lista_notas,
    _impl_gerar_relatorio_notas_com_assinatura,
    _impl_lista_notas,
)
from src.services.reports.declaracao import gerar_declaracao  # noqa: F401
from src.services.reports.historico import (  # noqa: F401
    gerar_historico_escolar,
    gerar_relatorio_series_faltantes,
    _impl_gerar_relatorio_series_faltantes,
)
from src.services.reports.frequencia import (  # noqa: F401
    gerar_relatorio_frequencia,
    gerar_lista_frequencia,
    gerar_tabela_frequencia,
    _impl_gerar_tabela_frequencia,
    _impl_lista_frequencia,
)
from src.services.reports.folha_ponto import (  # noqa: F401
    gerar_resumo_ponto,
    gerar_folhas_de_ponto,
    _impl_gerar_folhas_de_ponto,
    _impl_gerar_resumo_ponto,
)
from src.services.reports.outros import (  # noqa: F401
    gerar_crachas_para_todos_os_alunos,
    gerar_relatorio_pendencias,
    gerar_relatorio_movimentacao_mensal,
    gerar_relatorio_matriculas,
    gerar_lista_reuniao,
    _impl_gerar_lista_reuniao,
)
