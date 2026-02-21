"""
Script para mapear códigos INEP do arquivo Excel com os alunos do banco de dados.
Autor: Sistema de Gestão Escolar
Data: 21/02/2026
"""

import pandas as pd
from difflib import SequenceMatcher
from typing import List, Dict, Tuple
from db.connection import get_connection
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class MapeadorCodigoINEP:
    """Classe responsável pelo mapeamento de códigos INEP"""
    
    def __init__(self, arquivo_excel: str):
        """
        Inicializa o mapeador
        
        Args:
            arquivo_excel: Caminho para o arquivo Excel com os códigos INEP
        """
        self.arquivo_excel = arquivo_excel
        self.df_excel = None
        self.alunos_banco = []
        self.mapeamentos = []
        
    def carregar_excel(self) -> bool:
        """
        Carrega o arquivo Excel
        
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        try:
            self.df_excel = pd.read_excel(self.arquivo_excel)
            logger.info(f"Arquivo Excel carregado com sucesso: {len(self.df_excel)} registros")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar Excel: {e}")
            return False
    
    def carregar_alunos_banco(self) -> bool:
        """
        Carrega os alunos do banco de dados
        
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT a.id, a.nome, a.codigo_inep, e.nome as escola_nome
                    FROM alunos a
                    LEFT JOIN escolas e ON a.escola_id = e.id
                    ORDER BY a.nome
                """)
                self.alunos_banco = cursor.fetchall()
                logger.info(f"Alunos carregados do banco: {len(self.alunos_banco)} registros")
                return True
        except Exception as e:
            logger.error(f"Erro ao carregar alunos do banco: {e}")
            return False
    
    def calcular_similaridade(self, nome1: str, nome2: str) -> float:
        """
        Calcula a similaridade entre dois nomes
        
        Args:
            nome1: Primeiro nome
            nome2: Segundo nome
            
        Returns:
            Valor entre 0 e 1 indicando a similaridade
        """
        # Normalizar nomes: remover acentos, converter para maiúsculas
        nome1 = self.normalizar_nome(nome1)
        nome2 = self.normalizar_nome(nome2)
        
        return SequenceMatcher(None, nome1, nome2).ratio()
    
    def normalizar_nome(self, nome: str) -> str:
        """
        Normaliza um nome para comparação
        
        Args:
            nome: Nome a ser normalizado
            
        Returns:
            Nome normalizado
        """
        if not nome:
            return ""
        
        # Converter para maiúsculas
        nome = nome.upper().strip()
        
        # Remover acentos
        acentos = {
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A', 'Ä': 'A',
            'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
            'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
            'Ó': 'O', 'Ò': 'O', 'Õ': 'O', 'Ô': 'O', 'Ö': 'O',
            'Ú': 'U', 'Ù': 'U', 'Û': 'U', 'Ü': 'U',
            'Ç': 'C'
        }
        
        for acento, sem_acento in acentos.items():
            nome = nome.replace(acento, sem_acento)
        
        return nome
    
    def mapear_alunos(self, limite_similaridade: float = 0.85) -> List[Dict]:
        """
        Mapeia os alunos do Excel com os do banco de dados
        
        Args:
            limite_similaridade: Limite mínimo de similaridade para considerar uma correspondência
            
        Returns:
            Lista de mapeamentos encontrados
        """
        self.mapeamentos = []
        
        for _, row in self.df_excel.iterrows():
            nome_excel = row['Nome do(a) Aluno(a)']
            codigo_inep = str(row['Identificação única'])
            turma = row['Nome da turma']
            
            # Procurar correspondência no banco
            melhor_correspondencia = None
            melhor_similaridade = 0
            
            for aluno_id, nome_banco, codigo_inep_atual, escola_nome in self.alunos_banco:
                similaridade = self.calcular_similaridade(nome_excel, nome_banco)
                
                if similaridade > melhor_similaridade:
                    melhor_similaridade = similaridade
                    melhor_correspondencia = {
                        'id': aluno_id,
                        'nome_banco': nome_banco,
                        'codigo_inep_atual': codigo_inep_atual,
                        'escola_nome': escola_nome
                    }
            
            # Adicionar mapeamento se a similaridade for suficiente
            status = 'confirmado' if melhor_similaridade >= limite_similaridade else 'revisar'
            
            mapeamento = {
                'nome_excel': nome_excel,
                'codigo_inep': codigo_inep,
                'turma': turma,
                'aluno_id': melhor_correspondencia['id'] if melhor_correspondencia else None,
                'nome_banco': melhor_correspondencia['nome_banco'] if melhor_correspondencia else None,
                'codigo_inep_atual': melhor_correspondencia['codigo_inep_atual'] if melhor_correspondencia else None,
                'escola_nome': melhor_correspondencia['escola_nome'] if melhor_correspondencia else None,
                'similaridade': melhor_similaridade,
                'status': status
            }
            
            self.mapeamentos.append(mapeamento)
        
        logger.info(f"Mapeamento concluído: {len(self.mapeamentos)} registros")
        return self.mapeamentos
    
    def obter_estatisticas(self) -> Dict:
        """
        Obtém estatísticas do mapeamento
        
        Returns:
            Dicionário com estatísticas
        """
        total = len(self.mapeamentos)
        confirmados = sum(1 for m in self.mapeamentos if m['status'] == 'confirmado')
        revisar = sum(1 for m in self.mapeamentos if m['status'] == 'revisar')
        ja_tem_codigo = sum(1 for m in self.mapeamentos if m['codigo_inep_atual'])
        
        return {
            'total': total,
            'confirmados': confirmados,
            'revisar': revisar,
            'ja_tem_codigo': ja_tem_codigo,
            'sem_codigo': total - ja_tem_codigo
        }
    
    def aplicar_mapeamentos(self, mapeamentos_aprovados: List[Dict]) -> Tuple[int, int]:
        """
        Aplica os mapeamentos aprovados no banco de dados
        
        Args:
            mapeamentos_aprovados: Lista de mapeamentos que devem ser aplicados
            
        Returns:
            Tupla com (sucessos, erros)
        """
        sucessos = 0
        erros = 0
        
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                for mapeamento in mapeamentos_aprovados:
                    try:
                        cursor.execute("""
                            UPDATE alunos 
                            SET codigo_inep = %s 
                            WHERE id = %s
                        """, (mapeamento['codigo_inep'], mapeamento['aluno_id']))
                        
                        sucessos += 1
                        logger.info(f"Código INEP atualizado para aluno ID {mapeamento['aluno_id']}: {mapeamento['codigo_inep']}")
                        
                    except Exception as e:
                        erros += 1
                        logger.error(f"Erro ao atualizar aluno ID {mapeamento['aluno_id']}: {e}")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Erro ao aplicar mapeamentos: {e}")
            erros += len(mapeamentos_aprovados)
        
        return sucessos, erros


if __name__ == "__main__":
    # Teste do mapeador
    mapeador = MapeadorCodigoINEP("C:/gestao/codigo inep.xlsx")
    
    if mapeador.carregar_excel():
        print("✓ Excel carregado com sucesso")
    else:
        print("✗ Erro ao carregar Excel")
        exit(1)
    
    if mapeador.carregar_alunos_banco():
        print("✓ Alunos do banco carregados com sucesso")
    else:
        print("✗ Erro ao carregar alunos do banco")
        exit(1)
    
    mapeamentos = mapeador.mapear_alunos()
    
    print(f"\nMapeamento concluído!")
    print(f"Total de registros: {len(mapeamentos)}")
    
    stats = mapeador.obter_estatisticas()
    print(f"\nEstatísticas:")
    print(f"  - Confirmados automaticamente: {stats['confirmados']}")
    print(f"  - Para revisar: {stats['revisar']}")
    print(f"  - Já possuem código INEP: {stats['ja_tem_codigo']}")
    print(f"  - Sem código INEP: {stats['sem_codigo']}")
    
    print(f"\nExemplos de mapeamento:")
    for i, m in enumerate(mapeamentos[:5]):
        print(f"\n{i+1}. {m['nome_excel']}")
        print(f"   → {m['nome_banco']} (similaridade: {m['similaridade']:.2%})")
        print(f"   Código INEP: {m['codigo_inep']}")
        print(f"   Status: {m['status']}")
