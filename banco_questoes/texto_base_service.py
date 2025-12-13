"""
Modelos e serviços para gerenciamento de Textos Base.

Textos base são materiais (textos, imagens, gráficos) usados como base
para questões em avaliações.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from datetime import datetime
from enum import Enum

from config_logs import get_logger
logger = get_logger(__name__)


class TipoTextoBase(Enum):
    """Tipos de texto base."""
    TEXTO = "texto"
    IMAGEM = "imagem"


class LayoutTextoBase(Enum):
    """Layout do texto base quando múltiplos na mesma avaliação."""
    COMPLETO = "completo"
    LADO_ESQUERDO = "lado_esquerdo"
    LADO_DIREITO = "lado_direito"
    SUPERIOR = "superior"
    INFERIOR = "inferior"


@dataclass
class TextoBase:
    """Representa um texto/imagem base para avaliações."""
    id: Optional[int] = None
    titulo: Optional[str] = None
    tipo: Optional[TipoTextoBase] = None
    conteudo: Optional[str] = None  # Para tipo=texto
    caminho_imagem: Optional[str] = None  # Para tipo=imagem
    link_drive: Optional[str] = None
    drive_file_id: Optional[str] = None
    largura: Optional[int] = None
    altura: Optional[int] = None
    escola_id: Optional[int] = None
    autor_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AvaliacaoTextoBase:
    """Relacionamento entre avaliação e texto base."""
    id: Optional[int] = None
    avaliacao_id: Optional[int] = None
    texto_base_id: Optional[int] = None
    ordem: int = 1
    layout: LayoutTextoBase = LayoutTextoBase.COMPLETO
    created_at: Optional[datetime] = None


class TextoBaseService:
    """Serviço para gerenciamento de textos base."""
    
    @staticmethod
    def criar(texto_base: TextoBase) -> Optional[int]:
        """
        Cria um novo texto base.
        
        Args:
            texto_base: Objeto TextoBase com os dados
            
        Returns:
            ID do texto base criado ou None em caso de erro
        """
        try:
            from conexao import conectar_bd
            conn = conectar_bd()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            sql = """
                INSERT INTO textos_base 
                (titulo, tipo, conteudo, caminho_imagem, link_drive, drive_file_id,
                 largura, altura, escola_id, autor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            valores = (
                texto_base.titulo,
                texto_base.tipo.value if texto_base.tipo else None,
                texto_base.conteudo,
                texto_base.caminho_imagem,
                texto_base.link_drive,
                texto_base.drive_file_id,
                texto_base.largura,
                texto_base.altura,
                texto_base.escola_id,
                texto_base.autor_id
            )
            
            cursor.execute(sql, valores)
            conn.commit()
            
            texto_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            logger.info(f"Texto base criado: ID={texto_id}")
            return texto_id
            
        except Exception as e:
            logger.error(f"Erro ao criar texto base: {e}")
            return None
    
    @staticmethod
    def buscar_por_id(texto_id: int) -> Optional[TextoBase]:
        """Busca um texto base por ID."""
        try:
            from conexao import conectar_bd
            conn = conectar_bd()
            if not conn:
                return None
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM textos_base WHERE id = %s", (texto_id,))
            row = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not row:
                return None
            
            return TextoBase(
                id=row['id'],
                titulo=row['titulo'],
                tipo=TipoTextoBase(row['tipo']) if row['tipo'] else None,
                conteudo=row.get('conteudo'),
                caminho_imagem=row.get('caminho_imagem'),
                link_drive=row.get('link_drive'),
                drive_file_id=row.get('drive_file_id'),
                largura=row.get('largura'),
                altura=row.get('altura'),
                escola_id=row['escola_id'],
                autor_id=row.get('autor_id'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at')
            )
            
        except Exception as e:
            logger.error(f"Erro ao buscar texto base: {e}")
            return None
    
    @staticmethod
    def listar(escola_id: int, tipo: Optional[TipoTextoBase] = None, limite: int = 100) -> List[TextoBase]:
        """Lista textos base de uma escola."""
        try:
            from conexao import conectar_bd
            conn = conectar_bd()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            sql = "SELECT * FROM textos_base WHERE escola_id = %s"
            params = [escola_id]
            
            if tipo:
                sql += " AND tipo = %s"
                params.append(tipo.value)
            
            sql += " ORDER BY created_at DESC LIMIT %s"
            params.append(limite)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            textos = []
            for row in rows:
                textos.append(TextoBase(
                    id=row['id'],
                    titulo=row['titulo'],
                    tipo=TipoTextoBase(row['tipo']) if row['tipo'] else None,
                    conteudo=row.get('conteudo'),
                    caminho_imagem=row.get('caminho_imagem'),
                    link_drive=row.get('link_drive'),
                    drive_file_id=row.get('drive_file_id'),
                    largura=row.get('largura'),
                    altura=row.get('altura'),
                    escola_id=row['escola_id'],
                    autor_id=row.get('autor_id'),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                ))
            
            return textos
            
        except Exception as e:
            logger.error(f"Erro ao listar textos base: {e}")
            return []
    
    @staticmethod
    def buscar_textos_avaliacao(avaliacao_id: int) -> List[Tuple[TextoBase, AvaliacaoTextoBase]]:
        """
        Busca textos base vinculados a uma avaliação (ordenados).
        
        Returns:
            Lista de tuplas (TextoBase, AvaliacaoTextoBase)
        """
        try:
            from conexao import conectar_bd
            conn = conectar_bd()
            if not conn:
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            sql = """
                SELECT tb.*, atb.id as rel_id, atb.ordem, atb.layout
                FROM textos_base tb
                INNER JOIN avaliacoes_textos_base atb ON tb.id = atb.texto_base_id
                WHERE atb.avaliacao_id = %s
                ORDER BY atb.ordem
            """
            
            cursor.execute(sql, (avaliacao_id,))
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            result = []
            for row in rows:
                texto = TextoBase(
                    id=row['id'],
                    titulo=row['titulo'],
                    tipo=TipoTextoBase(row['tipo']) if row['tipo'] else None,
                    conteudo=row.get('conteudo'),
                    caminho_imagem=row.get('caminho_imagem'),
                    link_drive=row.get('link_drive'),
                    drive_file_id=row.get('drive_file_id'),
                    largura=row.get('largura'),
                    altura=row.get('altura'),
                    escola_id=row['escola_id'],
                    autor_id=row.get('autor_id'),
                    created_at=row.get('created_at'),
                    updated_at=row.get('updated_at')
                )
                
                rel = AvaliacaoTextoBase(
                    id=row['rel_id'],
                    avaliacao_id=avaliacao_id,
                    texto_base_id=row['id'],
                    ordem=row['ordem'],
                    layout=LayoutTextoBase(row['layout']) if row.get('layout') else LayoutTextoBase.COMPLETO
                )
                
                result.append((texto, rel))
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar textos da avaliação: {e}")
            return []
    
    @staticmethod
    def vincular_texto_avaliacao(avaliacao_id: int, texto_base_id: int, ordem: int = 1, 
                                 layout: LayoutTextoBase = LayoutTextoBase.COMPLETO) -> bool:
        """Vincula um texto base a uma avaliação."""
        try:
            from conexao import conectar_bd
            conn = conectar_bd()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            sql = """
                INSERT INTO avaliacoes_textos_base (avaliacao_id, texto_base_id, ordem, layout)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE ordem = %s, layout = %s
            """
            
            cursor.execute(sql, (avaliacao_id, texto_base_id, ordem, layout.value, ordem, layout.value))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao vincular texto à avaliação: {e}")
            return False
    
    @staticmethod
    def excluir(texto_id: int) -> bool:
        """Exclui um texto base (e seus vínculos por CASCADE)."""
        try:
            from conexao import conectar_bd
            conn = conectar_bd()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("DELETE FROM textos_base WHERE id = %s", (texto_id,))
            conn.commit()
            
            linhas_afetadas = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            return linhas_afetadas > 0
            
        except Exception as e:
            logger.error(f"Erro ao excluir texto base: {e}")
            return False
