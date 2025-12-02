"""
Models do módulo de Transporte Escolar.

Define as dataclasses e enums para:
- Veículos
- Rotas
- Pontos de parada
- Alunos usuários de transporte
- Ocorrências
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Optional, List
from decimal import Decimal


class TipoVeiculo(str, Enum):
    """Tipos de veículos de transporte escolar."""
    ONIBUS = "Ônibus"
    VAN = "Van"
    MICRO_ONIBUS = "Micro-ônibus"


class StatusVeiculo(str, Enum):
    """Status do veículo."""
    ATIVO = "Ativo"
    MANUTENCAO = "Manutenção"
    INATIVO = "Inativo"


class Turno(str, Enum):
    """Turnos de funcionamento das rotas."""
    MATUTINO = "Matutino"
    VESPERTINO = "Vespertino"
    NOTURNO = "Noturno"
    INTEGRAL = "Integral"


class TipoOcorrencia(str, Enum):
    """Tipos de ocorrências de transporte."""
    ATRASO = "Atraso"
    ACIDENTE = "Acidente"
    MANUTENCAO = "Manutenção"
    OUTRO = "Outro"


@dataclass
class Veiculo:
    """
    Representa um veículo da frota de transporte escolar.
    
    Attributes:
        id: Identificador único
        placa: Placa do veículo (formato ABC-1234 ou ABC1D23)
        tipo: Tipo do veículo (ônibus, van, micro-ônibus)
        capacidade: Capacidade de passageiros
        ano_fabricacao: Ano de fabricação
        motorista_id: ID do funcionário motorista responsável
        motorista_nome: Nome do motorista (preenchido em consultas)
        status: Status atual do veículo
        km_atual: Quilometragem atual
        ultima_revisao: Data da última revisão
        proxima_revisao: Data prevista para próxima revisão
        created_at: Data de criação do registro
        updated_at: Data da última atualização
    """
    id: Optional[int] = None
    placa: str = ""
    tipo: TipoVeiculo = TipoVeiculo.ONIBUS
    capacidade: int = 0
    ano_fabricacao: Optional[int] = None
    motorista_id: Optional[int] = None
    motorista_nome: Optional[str] = None
    status: StatusVeiculo = StatusVeiculo.ATIVO
    km_atual: Decimal = Decimal("0")
    ultima_revisao: Optional[date] = None
    proxima_revisao: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Converte strings para enums se necessário."""
        if isinstance(self.tipo, str):
            self.tipo = TipoVeiculo(self.tipo)
        if isinstance(self.status, str):
            self.status = StatusVeiculo(self.status)
        if isinstance(self.km_atual, (int, float)):
            self.km_atual = Decimal(str(self.km_atual))

    @property
    def precisa_revisao(self) -> bool:
        """Verifica se o veículo está com revisão atrasada."""
        if self.proxima_revisao is None:
            return False
        return date.today() >= self.proxima_revisao

    @property
    def descricao_completa(self) -> str:
        """Retorna descrição completa do veículo."""
        return f"{self.tipo.value} - {self.placa} ({self.capacidade} lugares)"


@dataclass
class Rota:
    """
    Representa uma rota de transporte escolar.
    
    Attributes:
        id: Identificador único
        nome: Nome descritivo da rota
        turno: Turno de funcionamento
        veiculo_id: ID do veículo associado
        veiculo_placa: Placa do veículo (preenchido em consultas)
        km_total: Quilometragem total da rota
        tempo_estimado_min: Tempo estimado em minutos
        horario_saida: Horário de saída
        horario_chegada: Horário de chegada na escola
        ativa: Se a rota está ativa
        pontos: Lista de pontos de parada (preenchido em consultas)
        total_alunos: Total de alunos na rota (preenchido em consultas)
        created_at: Data de criação do registro
    """
    id: Optional[int] = None
    nome: str = ""
    turno: Turno = Turno.MATUTINO
    veiculo_id: Optional[int] = None
    veiculo_placa: Optional[str] = None
    km_total: Optional[Decimal] = None
    tempo_estimado_min: Optional[int] = None
    horario_saida: Optional[time] = None
    horario_chegada: Optional[time] = None
    ativa: bool = True
    pontos: List['PontoParada'] = field(default_factory=list)
    total_alunos: int = 0
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Converte strings para enums se necessário."""
        if isinstance(self.turno, str):
            self.turno = Turno(self.turno)
        if isinstance(self.km_total, (int, float)):
            self.km_total = Decimal(str(self.km_total))
        if isinstance(self.horario_saida, str):
            self.horario_saida = datetime.strptime(self.horario_saida, "%H:%M:%S").time()
        if isinstance(self.horario_chegada, str):
            self.horario_chegada = datetime.strptime(self.horario_chegada, "%H:%M:%S").time()

    @property
    def descricao_completa(self) -> str:
        """Retorna descrição completa da rota."""
        horario = ""
        if self.horario_saida:
            horario = f" - {self.horario_saida.strftime('%H:%M')}"
        return f"{self.nome} ({self.turno.value}){horario}"


@dataclass
class PontoParada:
    """
    Representa um ponto de parada em uma rota.
    
    Attributes:
        id: Identificador único
        rota_id: ID da rota
        ordem: Ordem do ponto na rota
        descricao: Descrição/nome do ponto
        endereco: Endereço completo
        latitude: Coordenada latitude
        longitude: Coordenada longitude
        horario_previsto: Horário previsto de passagem
        total_alunos: Alunos que embarcam/desembarcam neste ponto
    """
    id: Optional[int] = None
    rota_id: int = 0
    ordem: int = 0
    descricao: str = ""
    endereco: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    horario_previsto: Optional[time] = None
    total_alunos: int = 0

    def __post_init__(self):
        """Converte strings para tipos corretos se necessário."""
        if isinstance(self.horario_previsto, str):
            self.horario_previsto = datetime.strptime(self.horario_previsto, "%H:%M:%S").time()
        if isinstance(self.latitude, (int, float)):
            self.latitude = Decimal(str(self.latitude))
        if isinstance(self.longitude, (int, float)):
            self.longitude = Decimal(str(self.longitude))


@dataclass
class AlunoTransporte:
    """
    Representa a associação de um aluno com o transporte escolar.
    
    Attributes:
        id: Identificador único
        aluno_id: ID do aluno
        aluno_nome: Nome do aluno (preenchido em consultas)
        rota_id: ID da rota
        rota_nome: Nome da rota (preenchido em consultas)
        ponto_embarque_id: ID do ponto de embarque
        ponto_embarque_desc: Descrição do ponto de embarque
        ponto_desembarque_id: ID do ponto de desembarque
        ponto_desembarque_desc: Descrição do ponto de desembarque
        ano_letivo_id: ID do ano letivo
        ativo: Se o vínculo está ativo
        serie: Série do aluno (preenchido em consultas)
        turma: Turma do aluno (preenchido em consultas)
        created_at: Data de criação do registro
    """
    id: Optional[int] = None
    aluno_id: int = 0
    aluno_nome: Optional[str] = None
    rota_id: int = 0
    rota_nome: Optional[str] = None
    ponto_embarque_id: Optional[int] = None
    ponto_embarque_desc: Optional[str] = None
    ponto_desembarque_id: Optional[int] = None
    ponto_desembarque_desc: Optional[str] = None
    ano_letivo_id: int = 0
    ativo: bool = True
    serie: Optional[str] = None
    turma: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class OcorrenciaTransporte:
    """
    Representa uma ocorrência/incidente de transporte.
    
    Attributes:
        id: Identificador único
        veiculo_id: ID do veículo envolvido
        veiculo_placa: Placa do veículo (preenchido em consultas)
        rota_id: ID da rota envolvida
        rota_nome: Nome da rota (preenchido em consultas)
        tipo: Tipo de ocorrência
        descricao: Descrição detalhada
        data_ocorrencia: Data e hora da ocorrência
        resolvido: Se foi resolvido
        observacoes: Observações adicionais
        registrado_por: ID do funcionário que registrou
        registrado_por_nome: Nome do funcionário (preenchido em consultas)
        created_at: Data de criação do registro
    """
    id: Optional[int] = None
    veiculo_id: Optional[int] = None
    veiculo_placa: Optional[str] = None
    rota_id: Optional[int] = None
    rota_nome: Optional[str] = None
    tipo: TipoOcorrencia = TipoOcorrencia.OUTRO
    descricao: str = ""
    data_ocorrencia: Optional[datetime] = None
    resolvido: bool = False
    observacoes: Optional[str] = None
    registrado_por: Optional[int] = None
    registrado_por_nome: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Converte strings para enums se necessário."""
        if isinstance(self.tipo, str):
            self.tipo = TipoOcorrencia(self.tipo)


@dataclass
class EstatisticasTransporte:
    """
    Estatísticas gerais do transporte escolar.
    
    Attributes:
        total_veiculos: Total de veículos cadastrados
        veiculos_ativos: Veículos em operação
        veiculos_manutencao: Veículos em manutenção
        total_rotas: Total de rotas cadastradas
        rotas_ativas: Rotas ativas
        total_alunos_transporte: Total de alunos que utilizam transporte
        capacidade_total: Soma da capacidade de todos veículos ativos
        taxa_ocupacao: Percentual de ocupação (alunos/capacidade)
        ocorrencias_mes: Ocorrências no mês atual
        veiculos_revisao_pendente: Veículos com revisão atrasada
    """
    total_veiculos: int = 0
    veiculos_ativos: int = 0
    veiculos_manutencao: int = 0
    total_rotas: int = 0
    rotas_ativas: int = 0
    total_alunos_transporte: int = 0
    capacidade_total: int = 0
    taxa_ocupacao: float = 0.0
    ocorrencias_mes: int = 0
    veiculos_revisao_pendente: int = 0
