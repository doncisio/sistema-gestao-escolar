"""
Modelos Pydantic para validação de dados de Matrículas.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional, Literal


class MatriculaBase(BaseModel):
    """Campos base compartilhados entre modelos de matrícula."""
    status: Literal['Ativo', 'Transferido', 'Transferida', 'Evadido', 'Concluído', 'Cancelado'] = Field(
        default='Ativo', description="Status da matrícula"
    )
    data_matricula: date = Field(default_factory=date.today, description="Data da matrícula")


class MatriculaCreate(MatriculaBase):
    """Modelo para criação de matrícula."""
    aluno_id: int = Field(..., gt=0, description="ID do aluno")
    turma_id: int = Field(..., gt=0, description="ID da turma")
    ano_letivo_id: int = Field(..., gt=0, description="ID do ano letivo")
    numero_matricula: Optional[str] = Field(None, max_length=50, description="Número da matrícula")
    
    @field_validator('data_matricula')
    @classmethod
    def validar_data_matricula(cls, v):
        """Valida que a data de matrícula não é muito antiga nem futura."""
        hoje = date.today()
        
        # Não pode ser mais de 2 anos no passado
        if (hoje - v).days > 730:
            raise ValueError('Data de matrícula muito antiga (mais de 2 anos)')
        
        # Não pode ser mais de 1 ano no futuro
        if (v - hoje).days > 365:
            raise ValueError('Data de matrícula não pode ser mais de 1 ano no futuro')
        
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "aluno_id": 123,
                "turma_id": 45,
                "ano_letivo_id": 5,
                "status": "Ativo",
                "data_matricula": "2024-02-01",
                "numero_matricula": "2024001234"
            }
        }
    }


class MatriculaUpdate(BaseModel):
    """Modelo para atualização de matrícula."""
    status: Optional[Literal['Ativo', 'Transferido', 'Transferida', 'Evadido', 'Concluído', 'Cancelado']] = None
    turma_id: Optional[int] = Field(None, gt=0)
    data_matricula: Optional[date] = None
    data_transferencia: Optional[date] = None
    motivo_transferencia: Optional[str] = Field(None, max_length=500)
    
    @field_validator('data_matricula', 'data_transferencia')
    @classmethod
    def validar_datas(cls, v):
        """Valida datas."""
        if v is None:
            return v
        
        hoje = date.today()
        
        # Não pode ser muito antiga (5 anos)
        if (hoje - v).days > 1825:
            raise ValueError('Data muito antiga (mais de 5 anos)')
        
        # Não pode ser futura (exceto planejamento)
        if (v - hoje).days > 365:
            raise ValueError('Data não pode ser mais de 1 ano no futuro')
        
        return v


class MatriculaRead(MatriculaBase):
    """Modelo para leitura de matrícula."""
    id: int
    aluno_id: int
    turma_id: int
    ano_letivo_id: int
    numero_matricula: Optional[str] = None
    data_transferencia: Optional[date] = None
    motivo_transferencia: Optional[str] = None
    data_cadastro: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
