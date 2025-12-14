"""
Relatório de Transição de Ano Letivo
====================================

Gera relatório PDF detalhado após execução da transição de ano letivo.

Autor: Sistema de Gestão Escolar
Data: Dezembro 2025
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import os
import tempfile
import platform

from src.core.config_logs import get_logger

logger = get_logger(__name__)


class RelatorioTransicaoAnoLetivo:
    """Gerador de relatórios PDF para transição de ano letivo."""
    
    def __init__(
        self,
        ano_origem: int,
        ano_destino: int,
        escola_nome: str = "Escola Municipal",
        escola_id: int = None
    ):
        """
        Inicializa o gerador de relatório.
        
        Args:
            ano_origem: Ano letivo de origem (ex: 2024)
            ano_destino: Ano letivo de destino (ex: 2025)
            escola_nome: Nome da escola
            escola_id: ID da escola no sistema
        """
        self.ano_origem = ano_origem
        self.ano_destino = ano_destino
        self.escola_nome = escola_nome
        self.escola_id = escola_id
        self.data_geracao = datetime.now()
        
        # Estilos
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        """Configura estilos personalizados para o relatório."""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='TituloRelatorio',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#3b5998'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            alignment=TA_CENTER,
            spaceAfter=15
        ))
        
        # Seção
        self.styles.add(ParagraphStyle(
            name='Secao',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#3b5998'),
            spaceBefore=15,
            spaceAfter=10
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='TextoNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
        
        # Texto destaque
        self.styles.add(ParagraphStyle(
            name='Destaque',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#4CAF50'),
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            spaceAfter=10
        ))
        
        # Texto de erro
        self.styles.add(ParagraphStyle(
            name='Erro',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#f44336')
        ))
    
    def gerar_relatorio(
        self,
        dados: Dict[str, Any],
        caminho_saida: str = None,
        abrir_apos_gerar: bool = True
    ) -> Optional[str]:
        """
        Gera o relatório PDF da transição.
        
        Args:
            dados: Dicionário com os dados da transição:
                - matriculas_encerradas: int
                - matriculas_criadas: int
                - alunos_promovidos: int
                - alunos_retidos: int
                - alunos_concluintes: int
                - status: str ('sucesso', 'erro', 'dry_run')
                - duracao_segundos: float (opcional)
                - detalhes: dict (opcional)
                - lista_promovidos: List[Dict] (opcional)
                - lista_retidos: List[Dict] (opcional)
            caminho_saida: Caminho do arquivo PDF (opcional)
            abrir_apos_gerar: Se True, abre o PDF após gerar
            
        Returns:
            Caminho do arquivo gerado ou None em caso de erro
        """
        try:
            # Definir caminho de saída
            if not caminho_saida:
                pasta = self._obter_pasta_relatorios()
                timestamp = self.data_geracao.strftime('%Y%m%d_%H%M%S')
                nome_arquivo = f"Relatorio_Transicao_{self.ano_origem}_{self.ano_destino}_{timestamp}.pdf"
                caminho_saida = os.path.join(pasta, nome_arquivo)
            
            # Criar documento
            doc = SimpleDocTemplate(
                caminho_saida,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Construir elementos
            elementos = []
            
            # Cabeçalho
            elementos.extend(self._criar_cabecalho())
            
            # Resumo da transição
            elementos.extend(self._criar_resumo(dados))
            
            # Estatísticas detalhadas
            elementos.extend(self._criar_estatisticas(dados))
            
            # Lista de alunos promovidos (se disponível)
            if dados.get('lista_promovidos'):
                elementos.extend(self._criar_lista_alunos(
                    "Alunos Promovidos", 
                    dados['lista_promovidos'],
                    cor_destaque=colors.HexColor('#4CAF50')
                ))
            
            # Lista de alunos retidos (se disponível)
            if dados.get('lista_retidos'):
                elementos.extend(self._criar_lista_alunos(
                    "Alunos Retidos", 
                    dados['lista_retidos'],
                    cor_destaque=colors.HexColor('#ff9800')
                ))
            
            # Rodapé com informações técnicas
            elementos.extend(self._criar_rodape(dados))
            
            # Gerar PDF
            doc.build(elementos)
            
            logger.info(f"Relatório de transição gerado: {caminho_saida}")
            
            # Abrir PDF
            if abrir_apos_gerar:
                self._abrir_arquivo(caminho_saida)
            
            return caminho_saida
            
        except Exception as e:
            logger.exception(f"Erro ao gerar relatório de transição: {e}")
            return None
    
    def _obter_pasta_relatorios(self) -> str:
        """Obtém a pasta para salvar relatórios."""
        try:
            # Tentar usar pasta de documentos do sistema
            from src.relatorios.gerar_pdf import _get_documents_root, _ensure_docs_dirs
            root = _get_documents_root()
            _ensure_docs_dirs(self.ano_destino)
            pasta = os.path.join(root, f"Documentos Secretaria {self.ano_destino}", "Relatorios Gerais")
            os.makedirs(pasta, exist_ok=True)
            return pasta
        except Exception:
            # Fallback para pasta temporária
            pasta = os.path.join(tempfile.gettempdir(), "relatorios_transicao")
            os.makedirs(pasta, exist_ok=True)
            return pasta
    
    def _criar_cabecalho(self) -> List:
        """Cria o cabeçalho do relatório."""
        elementos = []
        
        # Título
        elementos.append(Paragraph(
            f"📄 RELATÓRIO DE TRANSIÇÃO DE ANO LETIVO",
            self.styles['TituloRelatorio']
        ))
        
        # Subtítulo
        elementos.append(Paragraph(
            f"{self.ano_origem} → {self.ano_destino}",
            self.styles['Subtitulo']
        ))
        
        # Nome da escola
        elementos.append(Paragraph(
            f"{self.escola_nome}",
            self.styles['Subtitulo']
        ))
        
        # Linha separadora
        elementos.append(HRFlowable(
            width="100%",
            thickness=1,
            lineCap='round',
            color=colors.HexColor('#3b5998'),
            spaceAfter=20
        ))
        
        return elementos
    
    def _criar_resumo(self, dados: Dict) -> List:
        """Cria a seção de resumo."""
        elementos = []
        
        status = dados.get('status', 'sucesso')
        
        # Status da transição
        if status == 'sucesso':
            msg_status = "✅ TRANSIÇÃO CONCLUÍDA COM SUCESSO"
            estilo = self.styles['Destaque']
        elif status == 'dry_run':
            msg_status = "🔍 SIMULAÇÃO (DRY-RUN) - Nenhuma alteração foi feita"
            estilo = self.styles['TextoNormal']
        else:
            msg_status = "❌ ERRO NA TRANSIÇÃO"
            estilo = self.styles['Erro']
        
        elementos.append(Paragraph(msg_status, estilo))
        elementos.append(Spacer(1, 10))
        
        # Data/hora da execução
        elementos.append(Paragraph(
            f"<b>Data de execução:</b> {self.data_geracao.strftime('%d/%m/%Y às %H:%M:%S')}",
            self.styles['TextoNormal']
        ))
        
        # Duração
        if dados.get('duracao_segundos'):
            duracao = dados['duracao_segundos']
            if duracao < 60:
                tempo_str = f"{duracao:.1f} segundos"
            else:
                minutos = int(duracao // 60)
                segundos = duracao % 60
                tempo_str = f"{minutos} min {segundos:.0f} seg"
            
            elementos.append(Paragraph(
                f"<b>Duração:</b> {tempo_str}",
                self.styles['TextoNormal']
            ))
        
        elementos.append(Spacer(1, 15))
        
        return elementos
    
    def _criar_estatisticas(self, dados: Dict) -> List:
        """Cria a seção de estatísticas."""
        elementos = []
        
        elementos.append(Paragraph("📊 ESTATÍSTICAS DA TRANSIÇÃO", self.styles['Secao']))
        
        # Tabela de estatísticas
        dados_tabela = [
            ["Descrição", "Quantidade"],
            ["Matrículas encerradas", str(dados.get('matriculas_encerradas', 0))],
            ["Novas matrículas criadas", str(dados.get('matriculas_criadas', 0))],
            ["Alunos promovidos", str(dados.get('alunos_promovidos', 0))],
            ["Alunos retidos (reprovados)", str(dados.get('alunos_retidos', 0))],
            ["Alunos concluintes (9º ano)", str(dados.get('alunos_concluintes', 0))],
        ]
        
        tabela = Table(dados_tabela, colWidths=[12*cm, 4*cm])
        tabela.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b5998')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Corpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Linhas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elementos.append(tabela)
        elementos.append(Spacer(1, 20))
        
        return elementos
    
    def _criar_lista_alunos(
        self, 
        titulo: str, 
        alunos: List[Dict],
        cor_destaque: colors.Color = colors.HexColor('#333333')
    ) -> List:
        """Cria uma lista de alunos."""
        elementos = []
        
        if not alunos:
            return elementos
        
        elementos.append(PageBreak())
        elementos.append(Paragraph(f"📋 {titulo.upper()}", self.styles['Secao']))
        elementos.append(Paragraph(
            f"Total: {len(alunos)} aluno(s)",
            self.styles['TextoNormal']
        ))
        elementos.append(Spacer(1, 10))
        
        # Cabeçalho da tabela
        dados_tabela = [["Nº", "Nome do Aluno", "Série Anterior", "Nova Série"]]
        
        for i, aluno in enumerate(alunos[:100], 1):  # Limitar a 100 para não ficar muito grande
            dados_tabela.append([
                str(i),
                aluno.get('nome', 'N/A'),
                aluno.get('serie_anterior', 'N/A'),
                aluno.get('serie_nova', 'N/A')
            ])
        
        if len(alunos) > 100:
            dados_tabela.append(["...", f"+ {len(alunos) - 100} alunos", "...", "..."])
        
        tabela = Table(dados_tabela, colWidths=[1*cm, 9*cm, 3*cm, 3*cm])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cor_destaque),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elementos.append(tabela)
        
        return elementos
    
    def _criar_rodape(self, dados: Dict) -> List:
        """Cria o rodapé com informações técnicas."""
        elementos = []
        
        elementos.append(Spacer(1, 30))
        elementos.append(HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.grey,
            spaceAfter=10
        ))
        
        # Informações técnicas
        info_tecnica = f"""
        <font size="8" color="#666666">
        <b>Informações Técnicas</b><br/>
        Escola ID: {self.escola_id or 'N/A'}<br/>
        Gerado em: {self.data_geracao.strftime('%d/%m/%Y %H:%M:%S')}<br/>
        Sistema: Gestão Escolar v1.0<br/>
        </font>
        """
        
        elementos.append(Paragraph(info_tecnica, self.styles['Normal']))
        
        return elementos
    
    def _abrir_arquivo(self, caminho: str):
        """Abre o arquivo PDF no visualizador padrão."""
        try:
            sistema = platform.system()
            if sistema == 'Windows':
                os.startfile(caminho)
            elif sistema == 'Darwin':  # macOS
                os.system(f'open "{caminho}"')
            else:  # Linux
                os.system(f'xdg-open "{caminho}"')
        except Exception as e:
            logger.warning(f"Não foi possível abrir o arquivo: {e}")


def gerar_relatorio_transicao(
    ano_origem: int,
    ano_destino: int,
    dados: Dict[str, Any],
    escola_nome: str = "Escola Municipal",
    escola_id: int = None,
    abrir: bool = True
) -> Optional[str]:
    """
    Função de conveniência para gerar relatório de transição.
    
    Args:
        ano_origem: Ano letivo de origem
        ano_destino: Ano letivo de destino
        dados: Dicionário com dados da transição
        escola_nome: Nome da escola
        escola_id: ID da escola
        abrir: Se True, abre o PDF após gerar
        
    Returns:
        Caminho do arquivo gerado ou None
    """
    gerador = RelatorioTransicaoAnoLetivo(
        ano_origem=ano_origem,
        ano_destino=ano_destino,
        escola_nome=escola_nome,
        escola_id=escola_id
    )
    
    return gerador.gerar_relatorio(dados, abrir_apos_gerar=abrir)


# Exemplo de uso
if __name__ == '__main__':
    # Dados de exemplo
    dados_exemplo = {
        'matriculas_encerradas': 150,
        'matriculas_criadas': 140,
        'alunos_promovidos': 130,
        'alunos_retidos': 10,
        'alunos_concluintes': 15,
        'status': 'sucesso',
        'duracao_segundos': 45.3
    }
    
    caminho = gerar_relatorio_transicao(
        ano_origem=2024,
        ano_destino=2025,
        dados=dados_exemplo,
        escola_nome="Escola Municipal Exemplo",
        escola_id=60
    )
    
    if caminho:
        print(f"Relatório gerado: {caminho}")
