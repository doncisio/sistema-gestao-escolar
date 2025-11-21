"""
Modelos Pydantic para validação de dados de Turmas.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


class TurmaBase(BaseModel):
    """Campos base compartilhados entre modelos de turma."""
    nome: str = Field(..., min_length=1, max_length=100, description="Nome da turma")
    turno: Literal['Matutino', 'Vespertino', 'Noturno', 'Integral'] = Field(
        ..., description="Turno da turma"
    )
    capacidade: int = Field(..., gt=0, le=50, description="Capacidade máxima de alunos")
    
    @field_validator('capacidade')
    @classmethod
    def validar_capacidade(cls, v):
        """Valida capacidade razoável."""
        if v < 5:
            raise ValueError('Capacidade mínima é 5 alunos')
        if v > 50:
            raise ValueError('Capacidade máxima é 50 alunos')
        return v


class TurmaCreate(TurmaBase):
    """Modelo para criação de turma."""
    serie_id: int = Field(..., gt=0, description="ID da série")
    ano_letivo_id: int = Field(..., gt=0, description="ID do ano letivo")
    escola_id: int = Field(..., gt=0, description="ID da escola")
    sala: Optional[str] = Field(None, max_length=50, description="Sala/local")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "5º Ano A",
                "serie_id": 7,
                "ano_letivo_id": 5,
                "turno": "Matutino",
                "capacidade": 30,
                "escola_id": 60,
                "sala": "Sala 12"
            }
        }
    }


class TurmaUpdate(BaseModel):
    """Modelo para atualização de turma."""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    turno: Optional[Literal['Matutino', 'Vespertino', 'Noturno', 'Integral']] = None
    capacidade: Optional[int] = Field(None, gt=0, le=50)
    sala: Optional[str] = Field(None, max_length=50)
    
    @field_validator('capacidade')
    @classmethod
    def validar_capacidade(cls, v):
        """Valida capacidade razoável."""
        if v is None:
            return v
        if v < 5 or v > 50:
            raise ValueError('Capacidade deve estar entre 5 e 50 alunos')
        return v


class TurmaRead(TurmaBase):
    """Modelo para leitura de turma."""
    id: int
    serie_id: int
    ano_letivo_id: int
    escola_id: int
    sala: Optional[str] = None
    
    model_config = {"from_attributes": True}
