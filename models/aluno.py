"""
Modelos Pydantic para validação de dados de Alunos.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date, datetime
from typing import Optional, Literal
import re

class AlunoBase(BaseModel):
    """Campos base compartilhados entre modelos de aluno."""
    nome: str = Field(..., min_length=3, max_length=200, description="Nome completo do aluno")
    data_nascimento: date = Field(..., description="Data de nascimento")
    sexo: Literal['M', 'F', 'Masculino', 'Feminino'] = Field(..., description="Sexo do aluno")
    local_nascimento: Optional[str] = Field(None, max_length=100, description="Cidade de nascimento")
    UF_nascimento: Optional[str] = Field(None, min_length=2, max_length=2, description="UF de nascimento")
    
    @field_validator('sexo')
    @classmethod
    def normalizar_sexo(cls, v):
        """Normaliza valores de sexo para M/F."""
        if v in ['M', 'Masculino']:
            return 'M'
        elif v in ['F', 'Feminino']:
            return 'F'
        return v
    
    @field_validator('data_nascimento')
    @classmethod
    def validar_idade(cls, v):
        """Valida se a idade está em faixa razoável (3 a 100 anos)."""
        if not isinstance(v, date):
            raise ValueError('Data de nascimento deve ser um objeto date')
        
        hoje = date.today()
        
        # Não pode ser data futura (validar primeiro)
        if v > hoje:
            raise ValueError('Data de nascimento não pode ser no futuro')
        
        idade = (hoje - v).days / 365.25
        
        if idade < 3:
            raise ValueError('Aluno deve ter pelo menos 3 anos de idade')
        if idade > 100:
            raise ValueError('Idade muito alta, verifique a data de nascimento')
        
        return v
    
    @field_validator('UF_nascimento')
    @classmethod
    def validar_uf(cls, v):
        """Valida UF brasileira."""
        if v is None:
            return v
        
        v = v.upper()
        ufs_validas = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        
        if v not in ufs_validas:
            raise ValueError(f'UF inválida. Use uma das: {", ".join(ufs_validas)}')
        
        return v


class AlunoCreate(AlunoBase):
    """Modelo para criação de aluno."""
    cpf: Optional[str] = Field(None, description="CPF do aluno (opcional)")
    mae: str = Field(..., min_length=3, max_length=200, description="Nome da mãe")
    pai: Optional[str] = Field(None, max_length=200, description="Nome do pai (opcional)")
    escola_id: int = Field(..., gt=0, description="ID da escola")
    
    # Dados do responsável (obrigatórios na criação)
    responsavel_nome: str = Field(..., min_length=3, max_length=200, description="Nome do responsável")
    responsavel_cpf: str = Field(..., description="CPF do responsável")
    responsavel_telefone: str = Field(..., description="Telefone do responsável")
    responsavel_parentesco: Optional[str] = Field('Mãe', max_length=50, description="Parentesco")
    
    @field_validator('cpf', 'responsavel_cpf')
    @classmethod
    def validar_cpf(cls, v, info):
        """Valida formato de CPF."""
        if v is None and info.field_name == 'cpf':
            return v  # CPF do aluno é opcional
        
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
    
    @field_validator('responsavel_telefone')
    @classmethod
    def validar_telefone(cls, v):
        """Valida formato de telefone."""
        # Remove pontuação
        telefone = re.sub(r'[^0-9]', '', v)
        
        if len(telefone) < 10 or len(telefone) > 11:
            raise ValueError('Telefone deve ter 10 ou 11 dígitos (DDD + número)')
        
        return telefone
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "João da Silva Santos",
                "data_nascimento": "2015-03-15",
                "sexo": "M",
                "local_nascimento": "Paço do Lumiar",
                "UF_nascimento": "MA",
                "cpf": "12345678901",
                "mae": "Maria Silva Santos",
                "pai": "José Santos",
                "escola_id": 60,
                "responsavel_nome": "Maria Silva Santos",
                "responsavel_cpf": "98765432100",
                "responsavel_telefone": "98987654321",
                "responsavel_parentesco": "Mãe"
            }
        }
    }


class AlunoUpdate(BaseModel):
    """Modelo para atualização de aluno (todos os campos opcionais)."""
    nome: Optional[str] = Field(None, min_length=3, max_length=200)
    data_nascimento: Optional[date] = None
    sexo: Optional[Literal['M', 'F', 'Masculino', 'Feminino']] = None
    local_nascimento: Optional[str] = Field(None, max_length=100)
    UF_nascimento: Optional[str] = Field(None, min_length=2, max_length=2)
    cpf: Optional[str] = None
    mae: Optional[str] = Field(None, min_length=3, max_length=200)
    pai: Optional[str] = Field(None, max_length=200)
    
    @field_validator('cpf')
    @classmethod
    def validar_cpf(cls, v):
        """Valida formato de CPF."""
        if v is None:
            return v
        
        # Remove pontuação
        cpf_numeros = re.sub(r'[^0-9]', '', v)
        
        if len(cpf_numeros) != 11:
            raise ValueError('CPF deve ter 11 dígitos')
        
        if not cpf_numeros.isdigit():
            raise ValueError('CPF deve conter apenas números')
        
        # Valida CPFs conhecidos como inválidos
        if cpf_numeros == cpf_numeros[0] * 11:
            raise ValueError('CPF inválido (todos os dígitos iguais)')
        
        return cpf_numeros
    
    @field_validator('sexo')
    @classmethod
    def normalizar_sexo(cls, v):
        """Normaliza valores de sexo para M/F."""
        if v is None:
            return v
        if v in ['M', 'Masculino']:
            return 'M'
        elif v in ['F', 'Feminino']:
            return 'F'
        return v
    
    @field_validator('data_nascimento')
    @classmethod
    def validar_idade(cls, v):
        """Valida se a idade está em faixa razoável."""
        if v is None:
            return v
        
        hoje = date.today()
        idade = (hoje - v).days / 365.25
        
        if idade < 3 or idade > 100:
            raise ValueError('Idade deve estar entre 3 e 100 anos')
        
        if v > hoje:
            raise ValueError('Data de nascimento não pode ser no futuro')
        
        return v
    
    @field_validator('UF_nascimento')
    @classmethod
    def validar_uf(cls, v):
        """Valida UF brasileira."""
        if v is None:
            return v
        
        v = v.upper()
        ufs_validas = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        
        if v not in ufs_validas:
            raise ValueError(f'UF inválida. Use uma das: {", ".join(ufs_validas)}')
        
        return v


class AlunoRead(AlunoBase):
    """Modelo para leitura de aluno (com ID e timestamps)."""
    id: int
    cpf: Optional[str] = None
    mae: str
    pai: Optional[str] = None
    escola_id: int
    data_cadastro: Optional[datetime] = None
    
    model_config = {"from_attributes": True}  # Permite criar a partir de ORM models
