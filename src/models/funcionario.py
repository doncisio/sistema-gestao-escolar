"""
Modelos Pydantic para validação de dados de Funcionários.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime
from typing import Optional, Literal
import re


class FuncionarioBase(BaseModel):
    """Campos base compartilhados entre modelos de funcionário."""
    nome: str = Field(..., min_length=3, max_length=200, description="Nome completo")
    cargo: str = Field(..., min_length=2, max_length=100, description="Cargo/função")
    data_nascimento: Optional[date] = Field(None, description="Data de nascimento")
    telefone: Optional[str] = Field(None, description="Telefone de contato")
    email: Optional[str] = Field(None, description="E-mail")
    
    @field_validator('data_nascimento')
    @classmethod
    def validar_idade(cls, v):
        """Valida se a idade está em faixa razoável para funcionário (18 a 100 anos)."""
        if v is None:
            return v
        
        hoje = date.today()
        idade = (hoje - v).days / 365.25
        
        if idade < 18:
            raise ValueError('Funcionário deve ter pelo menos 18 anos')
        if idade > 100:
            raise ValueError('Idade muito alta, verifique a data de nascimento')
        
        if v > hoje:
            raise ValueError('Data de nascimento não pode ser no futuro')
        
        return v
    
    @field_validator('telefone')
    @classmethod
    def validar_telefone(cls, v):
        """Valida formato de telefone."""
        if v is None:
            return v
        
        # Remove pontuação
        telefone = re.sub(r'[^0-9]', '', v)
        
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError('Telefone deve ter 10 ou 11 dígitos (DDD + número)')
        
        return telefone


class FuncionarioCreate(FuncionarioBase):
    """Modelo para criação de funcionário."""
    cpf: str = Field(..., description="CPF do funcionário")
    escola_id: int = Field(..., gt=0, description="ID da escola")
    matricula: Optional[str] = Field(None, max_length=50, description="Matrícula funcional")
    tipo: Literal['Professor', 'Administrativo', 'Diretor', 'Coordenador', 'Outro'] = Field(
        ..., description="Tipo de funcionário"
    )
    
    @field_validator('cpf')
    @classmethod
    def validar_cpf(cls, v):
        """Valida formato de CPF."""
        # Remove pontuação
        cpf_numeros = re.sub(r'[^0-9]', '', v)
        
        if len(cpf_numeros) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        
        if not cpf_numeros.isdigit():
            raise ValueError('CPF deve conter apenas números')
        
        # Valida CPFs conhecidos como inválidos
        if cpf_numeros == cpf_numeros[0] * 11:
            raise ValueError('CPF inválido (todos os dígitos iguais)')
        
        # Validação do algoritmo do CPF
        def calcular_digito(cpf_parcial, peso_inicial):
            soma = sum(int(cpf_parcial[i]) * (peso_inicial - i) for i in range(len(cpf_parcial)))
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)
        
        digito1 = calcular_digito(cpf_numeros[:9], 10)
        digito2 = calcular_digito(cpf_numeros[:9] + digito1, 11)
        
        if cpf_numeros[-2:] != digito1 + digito2:
            raise ValueError('CPF inválido (dígitos verificadores incorretos)')
        
        return cpf_numeros
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "Maria Eduarda Silva",
                "cargo": "Professora de Matemática",
                "cpf": "12345678901",
                "data_nascimento": "1985-06-20",
                "telefone": "98987654321",
                "email": "maria.silva@escola.edu.br",
                "escola_id": 60,
                "matricula": "MAT2024001",
                "tipo": "Professor"
            }
        }
    }


class FuncionarioUpdate(BaseModel):
    """Modelo para atualização de funcionário (campos opcionais)."""
    nome: Optional[str] = Field(None, min_length=3, max_length=200)
    cargo: Optional[str] = Field(None, min_length=2, max_length=100)
    data_nascimento: Optional[date] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    matricula: Optional[str] = Field(None, max_length=50)
    tipo: Optional[Literal['Professor', 'Administrativo', 'Diretor', 'Coordenador', 'Outro']] = None
    
    @field_validator('data_nascimento')
    @classmethod
    def validar_idade(cls, v):
        """Valida idade."""
        if v is None:
            return v
        
        hoje = date.today()
        idade = (hoje - v).days / 365.25
        
        if idade < 18 or idade > 100:
            raise ValueError('Idade deve estar entre 18 e 100 anos')
        
        if v > hoje:
            raise ValueError('Data de nascimento não pode ser no futuro')
        
        return v
    
    @field_validator('telefone')
    @classmethod
    def validar_telefone(cls, v):
        """Valida formato de telefone."""
        if v is None:
            return v
        
        telefone = re.sub(r'[^0-9]', '', v)
        
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError('Telefone deve ter 10 ou 11 dígitos')
        
        return telefone


class FuncionarioRead(FuncionarioBase):
    """Modelo para leitura de funcionário."""
    id: int
    cpf: str
    escola_id: int
    matricula: Optional[str] = None
    tipo: str
    data_cadastro: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
