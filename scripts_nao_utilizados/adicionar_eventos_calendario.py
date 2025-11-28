import sys
import os
from config_logs import get_logger
logger = get_logger(__name__)
import tkinter as tk
from datetime import datetime, date
import mysql.connector
from tkinter import messagebox

# Adiciona a raiz do projeto ao path para importar os módulos do projeto
project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa o controlador de eventos acadêmicos (tenta importar e dá erro amigável se falhar)
try:
    from controllers.evento_academico_controller import EventoAcademicoController  # type: ignore
except Exception:
    # Tenta recarregar sys.path caso o ambiente de execução (IDE) não tenha atualizado
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from controllers.evento_academico_controller import EventoAcademicoController  # type: ignore
    except Exception:
        # Fallback: define um stub leve para permitir execução em modo dry-run
        class EventoAcademicoController:
            def adicionar_evento(self, ano_letivo, data_evento, nome, tipo, descricao):
                logger.warning("Stub EventoAcademicoController.adicionar_evento chamado (módulo 'controllers' ausente).")
                return True

try:
    from utils.error_handler import ErrorHandler  # type: ignore
except Exception:
    class ErrorHandler:
        @staticmethod
        def handle(exc: Exception):
            logger.exception(exc)
            return None

try:
    from utils.db_config import get_db_config  # type: ignore
except Exception:
    def get_db_config():
        # Fallback simples: lê variáveis de ambiente usadas pelo projeto
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'redeescola'),
        }

def obter_ano_letivo_2025():
    """Obtém o ano letivo de 2025 (não o ID)."""
    return 2025  # Retorna diretamente o valor do ano, não o ID

def obter_ano_letivo_2026():
    """Obtém o ano letivo de 2026 (não o ID)."""
    return 2026  # Retorna diretamente o valor do ano, não o ID

def identificar_tipo_evento(descricao):
    """Identifica o tipo de evento baseado na descrição."""
    descricao_lower = descricao.lower()
    
    if 'feriado nacional' in descricao_lower:
        return 'Feriado Nacional'
    elif 'feriado municipal' in descricao_lower or 'feriado estadual' in descricao_lower:
        return 'Feriado Municipal'
    elif 'recesso' in descricao_lower or 'férias' in descricao_lower:
        return 'Recesso Escolar'
    elif 'reunião' in descricao_lower or 'jornada pedagógica' in descricao_lower:
        return 'Reunião Pedagógica'
    elif 'conselho de classe' in descricao_lower:
        return 'Conselho de Classe'
    elif 'avaliação' in descricao_lower or 'prova' in descricao_lower or 'somativa' in descricao_lower or 'parc' in descricao_lower:
        return 'Prova/Avaliação'
    elif 'recuperação' in descricao_lower or 'estudos direcionados' in descricao_lower:
        return 'Recuperação'
    elif 'início' in descricao_lower and 'período' in descricao_lower or 'término' in descricao_lower and 'período' in descricao_lower:
        return 'Início/Fim de Bimestre'
    elif 'início' in descricao_lower and 'letivo' in descricao_lower or 'término' in descricao_lower and 'letivo' in descricao_lower:
        return 'Início/Fim de Ano Letivo'
    else:
        return 'Evento Escolar'

def adicionar_eventos():
    """Adiciona todos os eventos acadêmicos ao calendário."""
    controller = EventoAcademicoController()
    
    # Obtém os valores dos anos letivos
    ano_letivo_2025 = obter_ano_letivo_2025()  # Vai retornar 2025, não o ID
    ano_letivo_2026 = obter_ano_letivo_2026()  # Vai retornar 2026, não o ID
    
    # Lista de eventos a serem adicionados
    eventos = [
        # Janeiro 2025
        {"data": "2025-01-01", "nome": "Confraternização Universal", "descricao": "Feriado Nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-01-02", "nome": "Início das Férias Docentes", "descricao": "Período de férias dos professores: 02/01 a 16/01", "ano_letivo": ano_letivo_2025},
        {"data": "2025-01-14", "nome": "Aniversário de Paço do Lumiar", "descricao": "Feriado Municipal", "ano_letivo": ano_letivo_2025},
        {"data": "2025-01-17", "nome": "Início da Jornada Pedagógica na escola", "descricao": "Período: 17/01 a 31/01", "ano_letivo": ano_letivo_2025},
        {"data": "2025-01-30", "nome": "Dia Internacional pela Paz e não violência", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        
        # Fevereiro 2025
        {"data": "2025-02-03", "nome": "Jornada Pedagógica na escola", "descricao": "Continuação da jornada pedagógica", "ano_letivo": ano_letivo_2025},
        {"data": "2025-02-04", "nome": "Jornada Pedagógica da SEMED", "descricao": "Primeiro dia - Jornada Pedagógica da Secretaria Municipal de Educação", "ano_letivo": ano_letivo_2025},
        {"data": "2025-02-05", "nome": "Jornada Pedagógica da SEMED", "descricao": "Segundo dia - Jornada Pedagógica da Secretaria Municipal de Educação", "ano_letivo": ano_letivo_2025},
        {"data": "2025-02-06", "nome": "Continuação da Jornada Pedagógica na escola", "descricao": "Período: 06/02 a 28/02", "ano_letivo": ano_letivo_2025},
        {"data": "2025-02-27", "nome": "Dia Nacional do Livro Didático", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        
        # Março 2025
        {"data": "2025-03-03", "nome": "Carnaval", "descricao": "Feriado Nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-04", "nome": "Carnaval", "descricao": "Feriado Nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-05", "nome": "Quarta-feira de Cinzas", "descricao": "Ponto Facultativo", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-08", "nome": "Dia Internacional da Mulher", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-10", "nome": "Início do 1º período letivo", "descricao": "Primeiro dia de aula do ano letivo", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-10", "nome": "Semana escolar de combate à violência contra a mulher", "descricao": "Período: 10/03 a 14/03", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-10", "nome": "Início da Avaliação Diagnóstica", "descricao": "Período: 10/03 a 21/03", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-15", "nome": "Dia da Escola", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-16", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-17", "nome": "Avaliação PARC (2º ano)", "descricao": "Período: 17/03 a 21/03", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-21", "nome": "Dia Nacional da Síndrome de Down", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-21", "nome": "Dia Internacional contra a Discriminação Racial", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-03-29", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        
        # Abril 2025
        {"data": "2025-04-02", "nome": "Dia Mundial de Sensibilização para o Autismo", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-06", "nome": "Dia Internacional do Esporte para o Desenvolvimento pela Paz", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-07", "nome": "Dia do Combate ao Bullying e à Violência na Escola", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-07", "nome": "Avaliação do 1º período", "descricao": "Período: 07/04 a 11/04", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-12", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-17", "nome": "Quinta-feira Santa", "descricao": "Ponto Facultativo", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-18", "nome": "Paixão de Cristo", "descricao": "Feriado Nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-18", "nome": "Dia Nacional do Livro infantil", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-19", "nome": "Dia dos Povos Indígenas", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-20", "nome": "Domingo de Páscoa", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-21", "nome": "Tiradentes", "descricao": "Feriado Nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-22", "nome": "Descobrimento do Brasil", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-22", "nome": "Estudos Direcionados de Recuperação", "descricao": "Período: 22/04 a 28/04", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-24", "nome": "Dia da Libras", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-26", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-04-28", "nome": "Dia da Educação", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        
        # Maio 2025
        {"data": "2025-05-01", "nome": "Dia do Trabalho", "descricao": "Feriado Nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-03", "nome": "Sábado letivo/Conselho de classe", "descricao": "Dia de aula e conselho de classe", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-06", "nome": "Término do 1º período letivo", "descricao": "Encerramento do 1º período", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-06", "nome": "VI Conferência Infanto-juvenil pelo Meio-Ambiente", "descricao": "Evento escolar", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-07", "nome": "Início do 2º período letivo", "descricao": "Início do 2º período", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-11", "nome": "Dia das Mães", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-17", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-17", "nome": "Conferência Municipal de Combate ao Abuso e à Exploração Sexual de Crianças e Adolescentes", "descricao": "Evento municipal", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-18", "nome": "Dia Nacional de Combate ao Abuso e à Exploração Sexual de Crianças e Adolescentes", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-20", "nome": "Dia municipal da Escola Comunitária", "descricao": "Data comemorativa municipal", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-26", "nome": "Semana do Brincar", "descricao": "Período: 26/05 a 30/05", "ano_letivo": ano_letivo_2025},
        {"data": "2025-05-28", "nome": "Dia Internacional do Brincar", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        
        # Junho 2025
        {"data": "2025-06-03", "nome": "1° fase OBMEP", "descricao": "Olimpíada Brasileira de Matemática das Escolas Públicas", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-09", "nome": "Dia do Porteiro escolar", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-09", "nome": "Avaliação do 2° período", "descricao": "Período: 09/06 a 13/06", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-12", "nome": "Dia Mundial contra o Trabalho infantil", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-16", "nome": "Estudos Direcionados de Recuperação", "descricao": "Período: 16/06 a 20/06", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-19", "nome": "Corpus Christi", "descricao": "Ponto facultativo", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-21", "nome": "Sábado letivo/Conselho de classe", "descricao": "Dia de aula e conselho de classe", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-27", "nome": "Dia Mundial da Surdocegueira", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-28", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-29", "nome": "Dia de São Pedro", "descricao": "Feriado municipal", "ano_letivo": ano_letivo_2025},
        {"data": "2025-06-30", "nome": "Término do 2° período", "descricao": "Encerramento do 2º período", "ano_letivo": ano_letivo_2025},
        
        # Julho 2025
        {"data": "2025-07-01", "nome": "Férias docentes", "descricao": "Período: 01/07 a 30/07", "ano_letivo": ano_letivo_2025},
        {"data": "2025-07-13", "nome": "Dia Mundial de Conscientização e Sensibilização do TDAH", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-07-28", "nome": "Dia de Adesão do Maranhão à Independência do Brasil", "descricao": "Feriado estadual", "ano_letivo": ano_letivo_2025},
        {"data": "2025-07-31", "nome": "Início do 3° período", "descricao": "Início do 3º período letivo", "ano_letivo": ano_letivo_2025},
        
        # Agosto 2025
        {"data": "2025-08-01", "nome": "Mês da Primeira Infância", "descricao": "Mês temático", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-06", "nome": "Dia Nacional dos Profissionais da Educação", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-09", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-10", "nome": "Dia da Família na Escola", "descricao": "Evento escolar", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-10", "nome": "Dia dos Pais", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-10", "nome": "Dia Internacional da Superdotação", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-11", "nome": "Dia do Estudante", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-21", "nome": "Semana Nacional da Pessoa com Deficiência Intelectual e Múltipla", "descricao": "Período: 21/08 a 28/08", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-22", "nome": "Dia do Folclore", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-22", "nome": "Dia do Coordenador Pedagógico", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-23", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-25", "nome": "Dia do soldado", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-08-25", "nome": "Dia Nacional da Educação Infantil", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        
        # Setembro 2025
        {"data": "2025-09-05", "nome": "Dia da Raça", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-06", "nome": "Sábado letivo/Desfile cívico", "descricao": "Dia de aula com desfile", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-07", "nome": "Independência do Brasil", "descricao": "Feriado nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-08", "nome": "Dia Internacional da Alfabetização", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-10", "nome": "Dia Mundial de Prevenção do Suicídio", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-11", "nome": "Dia Nacional da Pessoa com Deficiência", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-21", "nome": "Dia da Árvore", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-22", "nome": "Avaliação do 3° período", "descricao": "Período: 22/09 a 26/09", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-26", "nome": "Dia Nacional do Surdo", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-27", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-29", "nome": "Estudos Direcionados de Recuperação", "descricao": "Período: 29/09 a 30/09", "ano_letivo": ano_letivo_2025},
        {"data": "2025-09-30", "nome": "Dia do Secretário escolar", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        
        # Outubro 2025
        {"data": "2025-10-01", "nome": "Dia Nacional do Idoso", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-01", "nome": "Dia Internacional da Terceira Idade", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-01", "nome": "Continuação dos Estudos Direcionados de Recuperação", "descricao": "Período: 01/10 a 03/10", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-06", "nome": "Semana da Criança", "descricao": "Período: 06/10 a 10/10", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-11", "nome": "Sábado letivo/Conselho de classe", "descricao": "Dia de aula e conselho de classe", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-12", "nome": "Nossa Senhora Aparecida", "descricao": "Feriado nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-12", "nome": "Dia das Crianças", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-13", "nome": "Término do 3º período", "descricao": "Encerramento do 3º período", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-14", "nome": "Início do 4º período", "descricao": "Início do 4º período letivo", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-15", "nome": "Dia do Professor", "descricao": "Feriado escolar", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-25", "nome": "Sábado letivo", "descricao": "Dia de aula", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-25", "nome": "2° fase da OBMEP", "descricao": "Olimpíada Brasileira de Matemática das Escolas Públicas", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-28", "nome": "Dia do Servidor Público", "descricao": "Ponto facultativo", "ano_letivo": ano_letivo_2025},
        {"data": "2025-10-30", "nome": "Dia do Merendeiro Escolar", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        
        # Novembro 2025
        {"data": "2025-11-02", "nome": "Finados", "descricao": "Feriado nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-11-12", "nome": "Dia do Diretor Escolar", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-11-14", "nome": "Dia Nacional da Alfabetização", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-11-15", "nome": "Proclamação da República", "descricao": "Feriado nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-11-17", "nome": "Avaliação Somativa SEAMA 2025", "descricao": "Período: 17/11 a 28/11 - 2º, 5º e 9º ano", "ano_letivo": ano_letivo_2025},
        {"data": "2025-11-20", "nome": "Dia Nacional de Zumbi e da Consciência Negra", "descricao": "Feriado nacional", "ano_letivo": ano_letivo_2025},
        
        # Dezembro 2025
        {"data": "2025-12-02", "nome": "Dia do Samba", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-12-08", "nome": "Dia de Nossa Senhora da Conceição", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-12-13", "nome": "Dia Nacional da Pessoa com Deficiência visual", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2025-12-15", "nome": "Semana de avaliação do 4º período letivo", "descricao": "Período: 15/12 a 19/12", "ano_letivo": ano_letivo_2025},
        {"data": "2025-12-24", "nome": "Véspera de Natal", "descricao": "Ponto facultativo", "ano_letivo": ano_letivo_2025},
        {"data": "2025-12-25", "nome": "Natal", "descricao": "Feriado nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2025-12-31", "nome": "Ano Novo", "descricao": "Ponto facultativo", "ano_letivo": ano_letivo_2025},
        
        # Janeiro 2026
        {"data": "2026-01-01", "nome": "Confraternização Universal", "descricao": "Feriado nacional", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-05", "nome": "Estudos Direcionados de Recuperação", "descricao": "Período: 05/01 a 09/01", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-09", "nome": "Término do 4° período", "descricao": "Encerramento do 4º período letivo", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-12", "nome": "Avaliação Final", "descricao": "Período: 12/01 a 13/01", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-14", "nome": "Aniversário de Paço do Lumiar", "descricao": "Feriado municipal", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-15", "nome": "Conselho de Classe", "descricao": "Reunião de conselho de classe", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-16", "nome": "Entrega de Resultado", "descricao": "Divulgação dos resultados finais", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-19", "nome": "Férias docentes", "descricao": "Período: 19/01 a 03/02", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-21", "nome": "Dia nacional de Combate à Intolerância Religiosa", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
        {"data": "2026-01-24", "nome": "Dia Mundial da Cultura Africana e Afrodescendente", "descricao": "Data comemorativa", "ano_letivo": ano_letivo_2025},
    ]
    
    # Contador de eventos adicionados e eventos com erro
    contador_sucesso = 0
    contador_erro = 0
    eventos_com_erro = []
    
    logger.info("Iniciando a adição de eventos ao calendário...")
    logger.info(f"Total de eventos a adicionar: {len(eventos)}")
    
    # Para cada evento, adiciona ao banco de dados
    for evento in eventos:
        try:
            # Determina o tipo de evento
            tipo = identificar_tipo_evento(evento['descricao'])
            
            # Converte a data de string para objeto date
            data_evento = date.fromisoformat(evento['data'])
            
            # Usa o controller para adicionar o evento
            resultado = controller.adicionar_evento(
                evento['ano_letivo'],
                data_evento,
                evento['nome'],
                tipo,
                evento['descricao']
            )
            
            if resultado:
                contador_sucesso += 1
                logger.info(f"Evento adicionado: {evento['data']} - {evento['nome']}")
            else:
                contador_erro += 1
                eventos_com_erro.append(f"{evento['data']} - {evento['nome']}")
                logger.error(f"Erro ao adicionar evento: {evento['data']} - {evento['nome']}")
                
        except Exception as e:
            contador_erro += 1
            eventos_com_erro.append(f"{evento['data']} - {evento['nome']}: {str(e)}")
            logger.info(f"Exceção ao adicionar evento: {evento['data']} - {evento['nome']}: {e}")
    
    # Exibe o resultado final
    logger.info("\n=== RESUMO DA OPERAÇÃO ===")
    logger.info(f"Total de eventos processados: {len(eventos)}")
    logger.info(f"Eventos adicionados com sucesso: {contador_sucesso}")
    logger.error(f"Eventos com erro: {contador_erro}")
    
    if eventos_com_erro:
        logger.error("\nLista de eventos com erro:")
        for evento in eventos_com_erro:
            logger.info(f"- {evento}")
    
    return contador_sucesso > 0

if __name__ == "__main__":
    # Inicia uma instância Tkinter básica para mensagens
    root = tk.Tk()
    root.withdraw()  # Não mostrar a janela principal
    
    try:
        # Verifica se a tabela de eventos existe
        db_config = get_db_config()
        conn = mysql.connector.connect(**db_config)
        
        if not conn:
            messagebox.showerror("Erro", "Não foi possível conectar ao banco de dados.")
            sys.exit(1)
            
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'eventos_academicos'
        """)
        r = cursor.fetchone()
        table_count = r[0] if r and r[0] is not None else 0

        if table_count == 0:
            messagebox.showerror("Erro", "A tabela 'eventos_academicos' não existe no banco de dados.")
            conn.close()
            sys.exit(1)
            
        conn.close()
        
        # Adiciona os eventos
        if adicionar_eventos():
            messagebox.showinfo("Sucesso", "Eventos acadêmicos adicionados com sucesso ao calendário!")
        else:
            messagebox.showerror("Erro", "Não foi possível adicionar os eventos ao calendário.")
    
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro durante a operação: {e}")
    
    finally:
        # Encerra a aplicação Tkinter
        root.destroy() 