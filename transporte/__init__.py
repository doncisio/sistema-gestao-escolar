"""
Módulo de Transporte Escolar

Este módulo gerencia:
- Cadastro de veículos da frota escolar
- Gestão de rotas de transporte
- Pontos de parada
- Alunos usuários de transporte
- Ocorrências e manutenções
- Dashboard e relatórios de transporte
"""

from .models import (
    Veiculo,
    Rota,
    PontoParada,
    AlunoTransporte,
    OcorrenciaTransporte,
    TipoVeiculo,
    StatusVeiculo,
    Turno,
    TipoOcorrencia
)

from .services import TransporteService

__all__ = [
    # Models
    'Veiculo',
    'Rota',
    'PontoParada',
    'AlunoTransporte',
    'OcorrenciaTransporte',
    'TipoVeiculo',
    'StatusVeiculo',
    'Turno',
    'TipoOcorrencia',
    # Services
    'TransporteService',
]

__version__ = '1.0.0'
