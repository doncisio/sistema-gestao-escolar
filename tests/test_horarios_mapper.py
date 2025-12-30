"""
Testes unitários para src/utils/horarios_mapper.py
"""
import pytest
from src.utils.horarios_mapper import mapear_disc_prof, _norm


class TestNormalizacao:
    """Testes para a função de normalização _norm"""
    
    def test_norm_remove_acentos(self):
        assert _norm("Matemática") == "MATEMATICA"
        assert _norm("Língua Portuguesa") == "LINGUA PORTUGUESA"
        assert _norm("História") == "HISTORIA"
        assert _norm("Ciências") == "CIENCIAS"
    
    def test_norm_remove_pontuacao(self):
        assert _norm("Prof. João") == "PROF JOAO"
        assert _norm("Ciências/História") == "CIENCIAS HISTORIA"
        assert _norm("(Recreio)") == "RECREIO"
    
    def test_norm_colapsa_espacos(self):
        assert _norm("  Matemática   Aplicada  ") == "MATEMATICA APLICADA"
        assert _norm("A  B    C") == "A B C"
    
    def test_norm_vazio(self):
        assert _norm("") == ""
        assert _norm("   ") == ""
        assert _norm(None) == ""


class TestMapearDiscProf:
    """Testes para mapeamento de disciplinas e professores"""
    
    @pytest.fixture
    def disciplinas_mock(self):
        return [
            {'id': 1, 'nome': 'MATEMÁTICA'},
            {'id': 2, 'nome': 'LÍNGUA PORTUGUESA'},
            {'id': 3, 'nome': 'CIÊNCIAS'},
            {'id': 4, 'nome': 'EDUCAÇÃO FÍSICA'},
        ]
    
    @pytest.fixture
    def professores_mock(self):
        return [
            {'id': 10, 'nome': 'Maria Silva Santos'},
            {'id': 11, 'nome': 'João Pedro Costa'},
            {'id': 12, 'nome': 'Ana Paula Oliveira'},
        ]
    
    def test_mapear_disciplina_nome_exato(self, disciplinas_mock, professores_mock):
        """Testa mapeamento por nome exato da disciplina"""
        disc_id, prof_id = mapear_disc_prof(
            "MATEMÁTICA",
            disciplinas_mock,
            professores_mock,
            {'disciplinas': {}, 'professores': {}}
        )
        assert disc_id == 1
        assert prof_id is None
    
    def test_mapear_disciplina_case_insensitive(self, disciplinas_mock, professores_mock):
        """Testa que matching de disciplina é case-insensitive"""
        disc_id, prof_id = mapear_disc_prof(
            "matemática",
            disciplinas_mock,
            professores_mock,
            {'disciplinas': {}, 'professores': {}}
        )
        assert disc_id == 1
    
    def test_mapear_com_professor_formato_padrao(self, disciplinas_mock, professores_mock):
        """Testa formato padrão: 'DISCIPLINA (Professor)'"""
        disc_id, prof_id = mapear_disc_prof(
            "MATEMÁTICA (Maria Silva Santos)",
            disciplinas_mock,
            professores_mock,
            {'disciplinas': {}, 'professores': {}}
        )
        assert disc_id == 1
        assert prof_id == 10
    
    def test_mapear_professor_primeiro_nome(self, disciplinas_mock, professores_mock):
        """Testa mapeamento de professor por primeiro nome (prefixo)"""
        disc_id, prof_id = mapear_disc_prof(
            "MATEMÁTICA (Maria)",
            disciplinas_mock,
            professores_mock,
            {'disciplinas': {}, 'professores': {}}
        )
        assert disc_id == 1
        assert prof_id == 10
    
    def test_mapear_usando_alias_disciplina(self, disciplinas_mock, professores_mock):
        """Testa mapeamento usando alias local para disciplina"""
        mapeamentos = {
            'disciplinas': {'MAT': 1, 'PORT': 2},
            'professores': {}
        }
        disc_id, prof_id = mapear_disc_prof(
            "MAT",
            disciplinas_mock,
            professores_mock,
            mapeamentos
        )
        assert disc_id == 1
    
    def test_mapear_usando_alias_professor(self, disciplinas_mock, professores_mock):
        """Testa mapeamento usando alias local para professor"""
        mapeamentos = {
            'disciplinas': {},
            'professores': {'MARIA SILVA SANTOS': 10}
        }
        disc_id, prof_id = mapear_disc_prof(
            "MATEMÁTICA (Maria Silva Santos)",
            disciplinas_mock,
            professores_mock,
            mapeamentos
        )
        assert disc_id == 1
        assert prof_id == 10
    
    def test_mapear_recreio_sem_mapeamento(self, disciplinas_mock, professores_mock):
        """Testa valor que não mapeia para nada (ex: RECREIO)"""
        disc_id, prof_id = mapear_disc_prof(
            "RECREIO",
            disciplinas_mock,
            professores_mock,
            {'disciplinas': {}, 'professores': {}}
        )
        assert disc_id is None
        assert prof_id is None
    
    def test_mapear_vazio(self, disciplinas_mock, professores_mock):
        """Testa valor vazio"""
        disc_id, prof_id = mapear_disc_prof(
            "",
            disciplinas_mock,
            professores_mock,
            {'disciplinas': {}, 'professores': {}}
        )
        assert disc_id is None
        assert prof_id is None
    
    def test_mapear_com_listas_vazias(self):
        """Testa com listas vazias de disciplinas e professores"""
        disc_id, prof_id = mapear_disc_prof(
            "MATEMÁTICA (João)",
            [],
            [],
            {'disciplinas': {}, 'professores': {}}
        )
        assert disc_id is None
        assert prof_id is None
    
    def test_mapear_com_acentos(self, disciplinas_mock, professores_mock):
        """Testa que acentos são tratados corretamente"""
        # Adicionar disciplina com acento à lista
        disciplinas_com_acento = disciplinas_mock + [{'id': 5, 'nome': 'HISTÓRIA'}]
        
        disc_id, prof_id = mapear_disc_prof(
            "História",
            disciplinas_com_acento,
            professores_mock,
            {'disciplinas': {}, 'professores': {}}
        )
        # Deve mapear mesmo com diferença de case
        assert disc_id == 5
    
    def test_mapear_multiplos_professores_mesmo_primeiro_nome(self, disciplinas_mock):
        """Testa desambiguação quando múltiplos professores têm mesmo primeiro nome"""
        professores = [
            {'id': 20, 'nome': 'João Silva'},
            {'id': 21, 'nome': 'João Pedro Costa'},
        ]
        
        # Deve pegar o primeiro match
        disc_id, prof_id = mapear_disc_prof(
            "MATEMÁTICA (João)",
            disciplinas_mock,
            professores,
            {'disciplinas': {}, 'professores': {}}
        )
        assert disc_id == 1
        assert prof_id == 20  # Primeiro João encontrado
