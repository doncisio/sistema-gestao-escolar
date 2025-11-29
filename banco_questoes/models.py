"""
Models do Banco de Questões BNCC

Definições de classes que representam as entidades do banco de questões.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum
from decimal import Decimal
import json


# ============================================================================
# ENUMERAÇÕES
# ============================================================================

class ComponenteCurricular(Enum):
    """Componentes curriculares da BNCC."""
    LINGUA_PORTUGUESA = "Língua Portuguesa"
    MATEMATICA = "Matemática"
    CIENCIAS = "Ciências"
    GEOGRAFIA = "Geografia"
    HISTORIA = "História"
    ARTE = "Arte"
    EDUCACAO_FISICA = "Educação Física"
    LINGUA_INGLESA = "Língua Inglesa"
    ENSINO_RELIGIOSO = "Ensino Religioso"


class AnoEscolar(Enum):
    """Anos escolares do Ensino Fundamental."""
    ANO_1 = "1º ano"
    ANO_2 = "2º ano"
    ANO_3 = "3º ano"
    ANO_4 = "4º ano"
    ANO_5 = "5º ano"
    ANO_6 = "6º ano"
    ANO_7 = "7º ano"
    ANO_8 = "8º ano"
    ANO_9 = "9º ano"


class TipoQuestao(Enum):
    """Tipos de questão suportados."""
    MULTIPLA_ESCOLHA = "multipla_escolha"
    DISSERTATIVA = "dissertativa"
    VERDADEIRO_FALSO = "verdadeiro_falso"
    ASSOCIACAO = "associacao"
    COMPLETAR = "completar"
    ORDENACAO = "ordenacao"


class DificuldadeQuestao(Enum):
    """Níveis de dificuldade da questão."""
    FACIL = "facil"
    MEDIA = "media"
    DIFICIL = "dificil"


class StatusQuestao(Enum):
    """Status de revisão da questão."""
    RASCUNHO = "rascunho"
    REVISAO = "revisao"
    APROVADA = "aprovada"
    ARQUIVADA = "arquivada"


class VisibilidadeQuestao(Enum):
    """Níveis de visibilidade da questão."""
    PRIVADA = "privada"
    ESCOLA = "escola"
    REDE = "rede"
    PUBLICA = "publica"


class ContextoQuestao(Enum):
    """Contextos temáticos da questão."""
    COTIDIANO = "cotidiano"
    ESCOLAR = "escolar"
    CIENTIFICO = "cientifico"
    LITERARIO = "literario"
    HISTORICO = "historico"
    ARTISTICO = "artistico"
    INTERDISCIPLINAR = "interdisciplinar"


class TipoAvaliacao(Enum):
    """Tipos de avaliação."""
    DIAGNOSTICA = "diagnostica"
    FORMATIVA = "formativa"
    SOMATIVA = "somativa"
    RECUPERACAO = "recuperacao"
    SIMULADO = "simulado"
    EXERCICIO = "exercicio"


class StatusAvaliacao(Enum):
    """Status da avaliação."""
    RASCUNHO = "rascunho"
    PRONTA = "pronta"
    APLICADA = "aplicada"
    ARQUIVADA = "arquivada"


class StatusAplicacao(Enum):
    """Status de uma aplicação de avaliação."""
    AGENDADA = "agendada"
    EM_ANDAMENTO = "em_andamento"
    AGUARDANDO_LANCAMENTO = "aguardando_lancamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class NivelDominio(Enum):
    """Níveis de domínio de uma habilidade."""
    INICIAL = "inicial"
    BASICO = "basico"
    INTERMEDIARIO = "intermediario"
    AVANCADO = "avancado"


class TipoArquivo(Enum):
    """Tipos de arquivo permitidos."""
    IMAGEM = "imagem"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENTO = "documento"


# ============================================================================
# MODELS
# ============================================================================

@dataclass
class QuestaoAlternativa:
    """Alternativa de uma questão de múltipla escolha."""
    id: Optional[int] = None
    questao_id: Optional[int] = None
    letra: str = ""
    texto: str = ""
    correta: bool = False
    feedback: Optional[str] = None
    ordem: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'id': self.id,
            'questao_id': self.questao_id,
            'letra': self.letra,
            'texto': self.texto,
            'correta': self.correta,
            'feedback': self.feedback,
            'ordem': self.ordem
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuestaoAlternativa':
        """Cria instância a partir de dicionário."""
        return cls(
            id=data.get('id'),
            questao_id=data.get('questao_id'),
            letra=data.get('letra', ''),
            texto=data.get('texto', ''),
            correta=bool(data.get('correta', False)),
            feedback=data.get('feedback'),
            ordem=data.get('ordem', 0)
        )


@dataclass
class QuestaoArquivo:
    """Arquivo (imagem, vídeo, etc.) vinculado a uma questão."""
    id: Optional[int] = None
    questao_id: Optional[int] = None
    alternativa_id: Optional[int] = None
    tipo_arquivo: TipoArquivo = TipoArquivo.IMAGEM
    nome_original: str = ""
    nome_armazenado: str = ""
    caminho: str = ""
    tamanho_bytes: int = 0
    mime_type: str = ""
    largura: Optional[int] = None
    altura: Optional[int] = None
    alt_text: Optional[str] = None
    posicao: int = 1
    uploaded_by: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'id': self.id,
            'questao_id': self.questao_id,
            'alternativa_id': self.alternativa_id,
            'tipo_arquivo': self.tipo_arquivo.value if isinstance(self.tipo_arquivo, TipoArquivo) else self.tipo_arquivo,
            'nome_original': self.nome_original,
            'nome_armazenado': self.nome_armazenado,
            'caminho': self.caminho,
            'tamanho_bytes': self.tamanho_bytes,
            'mime_type': self.mime_type,
            'largura': self.largura,
            'altura': self.altura,
            'alt_text': self.alt_text,
            'posicao': self.posicao
        }


@dataclass
class Questao:
    """Questão do banco de questões."""
    id: Optional[int] = None
    
    # Vínculo curricular
    componente_curricular: Optional[ComponenteCurricular] = None
    ano_escolar: Optional[AnoEscolar] = None
    habilidade_bncc_codigo: str = ""
    habilidade_bncc_secundaria: Optional[str] = None
    
    # Metadados
    tipo: TipoQuestao = TipoQuestao.MULTIPLA_ESCOLHA
    dificuldade: DificuldadeQuestao = DificuldadeQuestao.MEDIA
    tempo_estimado: int = 3
    
    # Conteúdo
    enunciado: str = ""
    comando: Optional[str] = None
    texto_apoio: Optional[str] = None
    fonte_texto: Optional[str] = None
    
    # Gabarito
    gabarito_letra: Optional[str] = None
    gabarito_dissertativa: Optional[str] = None
    rubrica_correcao: Optional[str] = None
    pontuacao_maxima: Decimal = Decimal("10.00")
    gabarito_vf: Optional[List[bool]] = None
    
    # Contexto e tags
    contexto: ContextoQuestao = ContextoQuestao.ESCOLAR
    tags: List[str] = field(default_factory=list)
    
    # Estatísticas
    vezes_aplicada: int = 0
    taxa_acerto_media: Optional[Decimal] = None
    
    # Controle de qualidade
    status: StatusQuestao = StatusQuestao.RASCUNHO
    revisada_por: Optional[int] = None
    revisada_em: Optional[datetime] = None
    observacoes_revisao: Optional[str] = None
    
    # Visibilidade
    visibilidade: VisibilidadeQuestao = VisibilidadeQuestao.ESCOLA
    escola_id: Optional[int] = None
    
    # Autoria
    autor_id: Optional[int] = None
    autor_nome: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relações (carregadas sob demanda)
    alternativas: List[QuestaoAlternativa] = field(default_factory=list)
    arquivos: List[QuestaoArquivo] = field(default_factory=list)
    
    @property
    def is_multipla_escolha(self) -> bool:
        """Verifica se é questão de múltipla escolha."""
        return self.tipo == TipoQuestao.MULTIPLA_ESCOLHA
    
    @property
    def is_dissertativa(self) -> bool:
        """Verifica se é questão dissertativa."""
        return self.tipo == TipoQuestao.DISSERTATIVA
    
    @property
    def is_verdadeiro_falso(self) -> bool:
        """Verifica se é questão V/F."""
        return self.tipo == TipoQuestao.VERDADEIRO_FALSO
    
    @property
    def gabarito_display(self) -> str:
        """Retorna gabarito formatado para exibição."""
        if self.is_multipla_escolha and self.gabarito_letra:
            return f"Alternativa {self.gabarito_letra}"
        elif self.is_dissertativa and self.gabarito_dissertativa:
            return self.gabarito_dissertativa[:100] + "..." if len(self.gabarito_dissertativa or "") > 100 else self.gabarito_dissertativa
        elif self.is_verdadeiro_falso and self.gabarito_vf:
            return ", ".join("V" if v else "F" for v in self.gabarito_vf)
        return "Não definido"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'id': self.id,
            'componente_curricular': self.componente_curricular.value if self.componente_curricular else None,
            'ano_escolar': self.ano_escolar.value if self.ano_escolar else None,
            'habilidade_bncc_codigo': self.habilidade_bncc_codigo,
            'habilidade_bncc_secundaria': self.habilidade_bncc_secundaria,
            'tipo': self.tipo.value if isinstance(self.tipo, TipoQuestao) else self.tipo,
            'dificuldade': self.dificuldade.value if isinstance(self.dificuldade, DificuldadeQuestao) else self.dificuldade,
            'tempo_estimado': self.tempo_estimado,
            'enunciado': self.enunciado,
            'comando': self.comando,
            'texto_apoio': self.texto_apoio,
            'fonte_texto': self.fonte_texto,
            'gabarito_letra': self.gabarito_letra,
            'gabarito_dissertativa': self.gabarito_dissertativa,
            'rubrica_correcao': self.rubrica_correcao,
            'pontuacao_maxima': float(self.pontuacao_maxima) if self.pontuacao_maxima else None,
            'gabarito_vf': self.gabarito_vf,
            'contexto': self.contexto.value if isinstance(self.contexto, ContextoQuestao) else self.contexto,
            'tags': self.tags,
            'vezes_aplicada': self.vezes_aplicada,
            'taxa_acerto_media': float(self.taxa_acerto_media) if self.taxa_acerto_media else None,
            'status': self.status.value if isinstance(self.status, StatusQuestao) else self.status,
            'visibilidade': self.visibilidade.value if isinstance(self.visibilidade, VisibilidadeQuestao) else self.visibilidade,
            'escola_id': self.escola_id,
            'autor_id': self.autor_id,
            'autor_nome': self.autor_nome,
            'alternativas': [a.to_dict() for a in self.alternativas],
            'arquivos': [a.to_dict() for a in self.arquivos]
        }
    
    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> 'Questao':
        """Cria instância a partir de uma linha do banco de dados."""
        # Processar tags (pode vir como JSON string)
        tags = row.get('tags', [])
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except:
                tags = []
        
        # Processar gabarito V/F
        gabarito_vf = row.get('gabarito_vf')
        if isinstance(gabarito_vf, str):
            try:
                gabarito_vf = json.loads(gabarito_vf)
            except:
                gabarito_vf = None
        
        return cls(
            id=row.get('id'),
            componente_curricular=ComponenteCurricular(row['componente_curricular']) if row.get('componente_curricular') else None,
            ano_escolar=AnoEscolar(row['ano_escolar']) if row.get('ano_escolar') else None,
            habilidade_bncc_codigo=row.get('habilidade_bncc_codigo', ''),
            habilidade_bncc_secundaria=row.get('habilidade_bncc_secundaria'),
            tipo=TipoQuestao(row['tipo']) if row.get('tipo') else TipoQuestao.MULTIPLA_ESCOLHA,
            dificuldade=DificuldadeQuestao(row['dificuldade']) if row.get('dificuldade') else DificuldadeQuestao.MEDIA,
            tempo_estimado=row.get('tempo_estimado', 3),
            enunciado=row.get('enunciado', ''),
            comando=row.get('comando'),
            texto_apoio=row.get('texto_apoio'),
            fonte_texto=row.get('fonte_texto'),
            gabarito_letra=row.get('gabarito_letra'),
            gabarito_dissertativa=row.get('gabarito_dissertativa'),
            rubrica_correcao=row.get('rubrica_correcao'),
            pontuacao_maxima=Decimal(str(row.get('pontuacao_maxima', 10))) if row.get('pontuacao_maxima') else Decimal("10.00"),
            gabarito_vf=gabarito_vf,
            contexto=ContextoQuestao(row['contexto']) if row.get('contexto') else ContextoQuestao.ESCOLAR,
            tags=tags if isinstance(tags, list) else [],
            vezes_aplicada=row.get('vezes_aplicada', 0),
            taxa_acerto_media=Decimal(str(row['taxa_acerto_media'])) if row.get('taxa_acerto_media') else None,
            status=StatusQuestao(row['status']) if row.get('status') else StatusQuestao.RASCUNHO,
            revisada_por=row.get('revisada_por'),
            revisada_em=row.get('revisada_em'),
            observacoes_revisao=row.get('observacoes_revisao'),
            visibilidade=VisibilidadeQuestao(row['visibilidade']) if row.get('visibilidade') else VisibilidadeQuestao.ESCOLA,
            escola_id=row.get('escola_id'),
            autor_id=row.get('autor_id'),
            autor_nome=row.get('autor_nome'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )


@dataclass
class AvaliacaoQuestao:
    """Relacionamento entre avaliação e questão."""
    id: Optional[int] = None
    avaliacao_id: Optional[int] = None
    questao_id: Optional[int] = None
    ordem: int = 0
    pontuacao: Optional[Decimal] = None
    obrigatoria: bool = True
    
    # Dados da questão (preenchido em joins)
    questao: Optional[Questao] = None


@dataclass
class Avaliacao:
    """Avaliação/prova composta por questões."""
    id: Optional[int] = None
    
    # Identificação
    titulo: str = ""
    descricao: Optional[str] = None
    
    # Vínculo curricular
    componente_curricular: Optional[ComponenteCurricular] = None
    ano_escolar: Optional[AnoEscolar] = None
    bimestre: Optional[str] = None
    
    # Tipo
    tipo: TipoAvaliacao = TipoAvaliacao.SOMATIVA
    
    # Configurações
    pontuacao_total: Decimal = Decimal("10.00")
    tempo_limite: Optional[int] = None
    
    # Configurações de impressão
    instrucoes: Optional[str] = None
    cabecalho_personalizado: Optional[str] = None
    mostrar_gabarito_professor: bool = True
    embaralhar_questoes: bool = False
    embaralhar_alternativas: bool = False
    num_versoes: int = 1
    
    # Status
    status: StatusAvaliacao = StatusAvaliacao.RASCUNHO
    
    # Vínculo
    escola_id: Optional[int] = None
    professor_id: Optional[int] = None
    professor_nome: Optional[str] = None
    
    # Controle
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Questões (carregadas sob demanda)
    questoes: List[AvaliacaoQuestao] = field(default_factory=list)
    
    @property
    def total_questoes(self) -> int:
        """Retorna número de questões."""
        return len(self.questoes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'componente_curricular': self.componente_curricular.value if self.componente_curricular else None,
            'ano_escolar': self.ano_escolar.value if self.ano_escolar else None,
            'bimestre': self.bimestre,
            'tipo': self.tipo.value if isinstance(self.tipo, TipoAvaliacao) else self.tipo,
            'pontuacao_total': float(self.pontuacao_total) if self.pontuacao_total else None,
            'tempo_limite': self.tempo_limite,
            'instrucoes': self.instrucoes,
            'status': self.status.value if isinstance(self.status, StatusAvaliacao) else self.status,
            'escola_id': self.escola_id,
            'professor_id': self.professor_id,
            'professor_nome': self.professor_nome,
            'total_questoes': self.total_questoes
        }


@dataclass
class AvaliacaoAplicada:
    """Registro de aplicação de avaliação para uma turma."""
    id: Optional[int] = None
    avaliacao_id: Optional[int] = None
    turma_id: Optional[int] = None
    
    data_aplicacao: Optional[date] = None
    data_limite_lancamento: Optional[date] = None
    
    status: StatusAplicacao = StatusAplicacao.AGENDADA
    
    # Estatísticas
    total_alunos: int = 0
    total_presentes: int = 0
    media_turma: Optional[Decimal] = None
    maior_nota: Optional[Decimal] = None
    menor_nota: Optional[Decimal] = None
    
    observacoes: Optional[str] = None
    
    aplicada_por: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Dados relacionados
    avaliacao: Optional[Avaliacao] = None
    turma_nome: Optional[str] = None


@dataclass
class RespostaAluno:
    """Resposta de um aluno a uma questão."""
    id: Optional[int] = None
    avaliacao_aplicada_id: Optional[int] = None
    aluno_id: Optional[int] = None
    questao_id: Optional[int] = None
    
    # Resposta
    resposta_letra: Optional[str] = None
    resposta_texto: Optional[str] = None
    resposta_vf: Optional[List[bool]] = None
    
    # Correção
    correta: Optional[bool] = None
    pontuacao_obtida: Optional[Decimal] = None
    
    # Feedback
    feedback_professor: Optional[str] = None
    corrigida_por: Optional[int] = None
    corrigida_em: Optional[datetime] = None
    
    # Controle
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Dados relacionados
    aluno_nome: Optional[str] = None
    questao: Optional[Questao] = None


@dataclass
class QuestaoFavorita:
    """Questão favoritada por um professor."""
    id: Optional[int] = None
    questao_id: Optional[int] = None
    professor_id: Optional[int] = None
    pasta: Optional[str] = None
    anotacoes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    # Dados relacionados
    questao: Optional[Questao] = None


@dataclass
class QuestaoComentario:
    """Comentário/avaliação de uma questão."""
    id: Optional[int] = None
    questao_id: Optional[int] = None
    professor_id: Optional[int] = None
    avaliacao: Optional[int] = None  # 1 a 5 estrelas
    comentario: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Dados relacionados
    professor_nome: Optional[str] = None


@dataclass
class DesempenhoAlunoHabilidade:
    """Desempenho consolidado de um aluno em uma habilidade BNCC."""
    id: Optional[int] = None
    aluno_id: Optional[int] = None
    habilidade_bncc_codigo: str = ""
    ano_letivo_id: Optional[int] = None
    
    # Estatísticas
    total_questoes_respondidas: int = 0
    total_acertos: int = 0
    taxa_acerto: Optional[Decimal] = None
    
    # Evolução
    ultima_avaliacao_id: Optional[int] = None
    ultima_avaliacao_em: Optional[date] = None
    
    # Classificação
    nivel_dominio: NivelDominio = NivelDominio.INICIAL
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Dados relacionados
    aluno_nome: Optional[str] = None
    habilidade_descricao: Optional[str] = None
    
    @property
    def taxa_acerto_percentual(self) -> float:
        """Retorna taxa de acerto como percentual."""
        if self.taxa_acerto:
            return float(self.taxa_acerto)
        elif self.total_questoes_respondidas > 0:
            return (self.total_acertos / self.total_questoes_respondidas) * 100
        return 0.0
    
    @classmethod
    def calcular_nivel_dominio(cls, taxa_acerto: float) -> NivelDominio:
        """Calcula nível de domínio baseado na taxa de acerto."""
        if taxa_acerto >= 80:
            return NivelDominio.AVANCADO
        elif taxa_acerto >= 60:
            return NivelDominio.INTERMEDIARIO
        elif taxa_acerto >= 40:
            return NivelDominio.BASICO
        else:
            return NivelDominio.INICIAL


# ============================================================================
# CLASSES AUXILIARES
# ============================================================================

@dataclass
class FiltroQuestoes:
    """Filtros para busca de questões."""
    componente_curricular: Optional[ComponenteCurricular] = None
    ano_escolar: Optional[AnoEscolar] = None
    habilidade_bncc: Optional[str] = None
    tipo: Optional[TipoQuestao] = None
    dificuldade: Optional[DificuldadeQuestao] = None
    status: Optional[StatusQuestao] = None
    visibilidade: Optional[VisibilidadeQuestao] = None
    contexto: Optional[ContextoQuestao] = None
    tags: Optional[List[str]] = None
    autor_id: Optional[int] = None
    escola_id: Optional[int] = None
    texto_busca: Optional[str] = None
    taxa_acerto_min: Optional[float] = None
    taxa_acerto_max: Optional[float] = None
    apenas_favoritas: bool = False
    professor_id_favoritas: Optional[int] = None
    
    def to_sql_conditions(self) -> tuple:
        """
        Gera condições SQL e parâmetros para a busca.
        
        Returns:
            Tupla (lista_condicoes, lista_parametros)
        """
        conditions = []
        params = []
        
        if self.componente_curricular:
            conditions.append("q.componente_curricular = %s")
            params.append(self.componente_curricular.value)
        
        if self.ano_escolar:
            conditions.append("q.ano_escolar = %s")
            params.append(self.ano_escolar.value)
        
        if self.habilidade_bncc:
            conditions.append("q.habilidade_bncc_codigo LIKE %s")
            params.append(f"%{self.habilidade_bncc}%")
        
        if self.tipo:
            conditions.append("q.tipo = %s")
            params.append(self.tipo.value)
        
        if self.dificuldade:
            conditions.append("q.dificuldade = %s")
            params.append(self.dificuldade.value)
        
        if self.status:
            conditions.append("q.status = %s")
            params.append(self.status.value)
        
        if self.visibilidade:
            conditions.append("q.visibilidade = %s")
            params.append(self.visibilidade.value)
        
        if self.contexto:
            conditions.append("q.contexto = %s")
            params.append(self.contexto.value)
        
        if self.autor_id:
            conditions.append("q.autor_id = %s")
            params.append(self.autor_id)
        
        if self.escola_id:
            conditions.append("(q.escola_id = %s OR q.escola_id IS NULL)")
            params.append(self.escola_id)
        
        if self.texto_busca:
            conditions.append("(q.enunciado LIKE %s OR q.texto_apoio LIKE %s)")
            params.extend([f"%{self.texto_busca}%", f"%{self.texto_busca}%"])
        
        if self.taxa_acerto_min is not None:
            conditions.append("q.taxa_acerto_media >= %s")
            params.append(self.taxa_acerto_min)
        
        if self.taxa_acerto_max is not None:
            conditions.append("q.taxa_acerto_media <= %s")
            params.append(self.taxa_acerto_max)
        
        if self.tags:
            # Busca por tags usando JSON_CONTAINS (MySQL 5.7+)
            for tag in self.tags:
                conditions.append("JSON_CONTAINS(q.tags, %s)")
                params.append(f'"{tag}"')
        
        return conditions, params


@dataclass
class EstatisticasQuestao:
    """Estatísticas de uso de uma questão."""
    questao_id: int
    total_aplicacoes: int = 0
    total_respostas: int = 0
    total_acertos: int = 0
    taxa_acerto: float = 0.0
    media_pontuacao: float = 0.0
    distribuicao_alternativas: Dict[str, int] = field(default_factory=dict)


@dataclass
class RelatorioDesempenhoTurma:
    """Relatório de desempenho de uma turma em uma avaliação."""
    avaliacao_aplicada_id: int
    turma_id: int
    turma_nome: str
    avaliacao_titulo: str
    data_aplicacao: date
    
    total_alunos: int = 0
    total_presentes: int = 0
    media_turma: float = 0.0
    maior_nota: float = 0.0
    menor_nota: float = 0.0
    
    desempenho_por_habilidade: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    desempenho_por_questao: List[EstatisticasQuestao] = field(default_factory=list)
    alunos_abaixo_media: int = 0
    alunos_acima_media: int = 0
