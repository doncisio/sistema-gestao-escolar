"""
Testes para modelos Pydantic de validação.
"""

import pytest
from datetime import date, datetime, timedelta
from pydantic import ValidationError
from models.aluno import AlunoCreate, AlunoUpdate
from models.funcionario import FuncionarioCreate, FuncionarioUpdate
from models.turma import TurmaCreate, TurmaUpdate
from models.matricula import MatriculaCreate, MatriculaUpdate


class TestAlunoModels:
    """Testes para modelos de Aluno."""
    
    def test_aluno_create_valido(self):
        """Testa criação de aluno com dados válidos."""
        aluno = AlunoCreate(
            nome="João da Silva Santos",
            data_nascimento=date(2015, 3, 15),
            sexo="M",
            local_nascimento="Paço do Lumiar",
            UF_nascimento="MA",
            mae="Maria Silva Santos",
            escola_id=60,
            responsavel_nome="Maria Silva Santos",
            responsavel_cpf="12345678909",
            responsavel_telefone="98987654321"
        )
        
        assert aluno.nome == "João da Silva Santos"
        assert aluno.sexo == "M"
        assert len(aluno.responsavel_cpf) == 11
    
    def test_aluno_cpf_invalido(self):
        """Testa validação de CPF inválido."""
        with pytest.raises(ValidationError) as exc_info:
            AlunoCreate(
                nome="João da Silva",
                data_nascimento=date(2015, 3, 15),
                sexo="M",
                mae="Maria Silva",
                escola_id=60,
                responsavel_nome="Maria Silva",
                responsavel_cpf="11111111111",  # CPF inválido
                responsavel_telefone="98987654321"
            )
        
        assert "CPF inválido" in str(exc_info.value)
    
    def test_aluno_idade_invalida(self):
        """Testa validação de idade."""
        # Muito jovem (< 3 anos)
        with pytest.raises(ValidationError) as exc_info:
            AlunoCreate(
                nome="Bebê Silva",
                data_nascimento=date.today() - timedelta(days=365),  # 1 ano
                sexo="M",
                mae="Maria Silva",
                escola_id=60,
                responsavel_nome="Maria Silva",
                responsavel_cpf="12345678909",
                responsavel_telefone="98987654321"
            )
        
        assert "pelo menos 3 anos" in str(exc_info.value)
    
    def test_aluno_data_futura(self):
        """Testa que data de nascimento futura é inválida."""
        with pytest.raises(ValidationError) as exc_info:
            AlunoCreate(
                nome="João do Futuro",
                data_nascimento=date.today() + timedelta(days=365),
                sexo="M",
                mae="Maria Silva",
                escola_id=60,
                responsavel_nome="Maria Silva",
                responsavel_cpf="12345678909",
                responsavel_telefone="98987654321"
            )
        
        assert "futuro" in str(exc_info.value)
    
    def test_aluno_uf_invalida(self):
        """Testa validação de UF."""
        with pytest.raises(ValidationError) as exc_info:
            AlunoCreate(
                nome="João da Silva",
                data_nascimento=date(2015, 3, 15),
                sexo="M",
                local_nascimento="Alguma Cidade",
                UF_nascimento="XX",  # UF inválida
                mae="Maria Silva",
                escola_id=60,
                responsavel_nome="Maria Silva",
                responsavel_cpf="12345678909",
                responsavel_telefone="98987654321"
            )
        
        assert "UF inválida" in str(exc_info.value)
    
    def test_aluno_update_parcial(self):
        """Testa update com campos opcionais."""
        update = AlunoUpdate(nome="Novo Nome")
        
        assert update.nome == "Novo Nome"
        assert update.sexo is None  # Campos opcionais podem ser None


class TestFuncionarioModels:
    """Testes para modelos de Funcionário."""
    
    def test_funcionario_create_valido(self):
        """Testa criação de funcionário válido."""
        func = FuncionarioCreate(
            nome="Maria Eduarda Silva",
            cargo="Professora",
            cpf="12345678909",
            data_nascimento=date(1985, 6, 20),
            telefone="98987654321",
            email="maria@escola.edu.br",
            escola_id=60,
            tipo="Professor"
        )
        
        assert func.nome == "Maria Eduarda Silva"
        assert func.tipo == "Professor"
    
    def test_funcionario_idade_minima(self):
        """Testa validação de idade mínima (18 anos)."""
        with pytest.raises(ValidationError) as exc_info:
            FuncionarioCreate(
                nome="Jovem Demais",
                cargo="Estagiário",
                cpf="12345678909",
                data_nascimento=date.today() - timedelta(days=365*16),  # 16 anos
                escola_id=60,
                tipo="Administrativo"
            )
        
        assert "18 anos" in str(exc_info.value)


class TestTurmaModels:
    """Testes para modelos de Turma."""
    
    def test_turma_create_valida(self):
        """Testa criação de turma válida."""
        turma = TurmaCreate(
            nome="5º Ano A",
            serie_id=7,
            ano_letivo_id=5,
            turno="Matutino",
            capacidade=30,
            escola_id=60
        )
        
        assert turma.nome == "5º Ano A"
        assert turma.capacidade == 30
    
    def test_turma_capacidade_invalida(self):
        """Testa validação de capacidade."""
        # Muito pequena
        with pytest.raises(ValidationError):
            TurmaCreate(
                nome="Turma Pequena",
                serie_id=7,
                ano_letivo_id=5,
                turno="Matutino",
                capacidade=2,  # < 5
                escola_id=60
            )
        
        # Muito grande
        with pytest.raises(ValidationError):
            TurmaCreate(
                nome="Turma Grande",
                serie_id=7,
                ano_letivo_id=5,
                turno="Matutino",
                capacidade=60,  # > 50
                escola_id=60
            )


class TestMatriculaModels:
    """Testes para modelos de Matrícula."""
    
    def test_matricula_create_valida(self):
        """Testa criação de matrícula válida."""
        matricula = MatriculaCreate(
            aluno_id=123,
            turma_id=45,
            ano_letivo_id=5,
            status="Ativo"
        )
        
        assert matricula.status == "Ativo"
        assert matricula.aluno_id == 123
    
    def test_matricula_data_muito_antiga(self):
        """Testa validação de data muito antiga."""
        with pytest.raises(ValidationError) as exc_info:
            MatriculaCreate(
                aluno_id=123,
                turma_id=45,
                ano_letivo_id=5,
                data_matricula=date(2020, 1, 1)  # Mais de 2 anos no passado
            )
        
        assert "muito antiga" in str(exc_info.value)
    
    def test_matricula_status_valido(self):
        """Testa que apenas status válidos são aceitos."""
        statuses_validos = ['Ativo', 'Transferido', 'Transferida', 'Evadido', 'Concluído', 'Cancelado']
        
        for status in statuses_validos:
            matricula = MatriculaCreate(
                aluno_id=123,
                turma_id=45,
                ano_letivo_id=5,
                status=status
            )
            assert matricula.status == status


class TestIntegracaoModelos:
    """Testes de integração entre modelos."""
    
    def test_fluxo_completo_aluno(self):
        """Testa fluxo completo de criação e atualização."""
        # Criação
        aluno = AlunoCreate(
            nome="Pedro Henrique Santos",
            data_nascimento=date(2012, 8, 10),
            sexo="Masculino",  # Será normalizado para 'M'
            mae="Ana Santos",
            escola_id=60,
            responsavel_nome="Ana Santos",
            responsavel_cpf="98765432100",
            responsavel_telefone="98912345678"
        )
        
        assert aluno.sexo == "M"  # Normalizado
        
        # Atualização
        update = AlunoUpdate(
            nome="Pedro Henrique Santos Junior",
            cpf="12345678909"
        )
        
        assert update.nome == "Pedro Henrique Santos Junior"
        assert len(update.cpf) == 11


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
