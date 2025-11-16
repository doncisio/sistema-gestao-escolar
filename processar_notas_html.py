from config_logs import get_logger
logger = get_logger(__name__)
"""
Script simplificado para processar um arquivo HTML específico do GEDUC
e gerar automaticamente o arquivo Excel com as notas.

Uso: python processar_notas_html.py "caminho/arquivo.html"
"""

import sys
import os
from importar_notas_html import extrair_informacoes_html, criar_excel_com_notas

def main():
    # Verificar se o caminho do arquivo foi fornecido
    if len(sys.argv) < 2:
        # Se não foi fornecido, usar o arquivo padrão
        html_path = r"c:\gestao\AMBIENTE SEMED - GEDUC GESTÃO EDUCACIONAL.html"
        logger.info(f"Nenhum arquivo especificado. Usando arquivo padrão:")
        logger.info(f"  {html_path}")
    else:
        html_path = sys.argv[1]
    
    # Verificar se o arquivo existe
    if not os.path.exists(html_path):
        logger.error(f"ERRO: Arquivo não encontrado: {html_path}")
        sys.exit(1)
    
    logger.info(f"\n{'='*60}")
    logger.info("PROCESSANDO NOTAS DO GEDUC")
    logger.info(f"{'='*60}\n")
    
    # Extrair dados do HTML
    logger.info("Extraindo dados do arquivo HTML...")
    dados = extrair_informacoes_html(html_path)
    
    if not dados or not dados['alunos']:
        logger.error("ERRO: Não foi possível extrair dados do HTML ou nenhum aluno encontrado!")
        sys.exit(1)
    
    # Exibir informações extraídas
    logger.info(f"\n  ✓ Turma: {dados['turma']}")
    logger.info(f"  ✓ Disciplina: {dados['disciplina']}")
    logger.info(f"  ✓ Bimestre: {dados['bimestre']}")
    logger.info(f"  ✓ Total de alunos: {len(dados['alunos'])}\n")
    
    # Gerar nome do arquivo de saída
    disciplina_safe = dados['disciplina'].replace(' ', '_').replace('/', '_')
    output_filename = f"Template_Notas__-_MAT_{disciplina_safe}_{dados['bimestre']}_bimestre.xlsx"
    
    # Diretório de saída (mesmo diretório do HTML)
    output_dir = os.path.dirname(html_path) if os.path.dirname(html_path) else '.'
    output_path = os.path.join(output_dir, output_filename)
    
    # Criar arquivo Excel
    logger.info(f"Gerando arquivo Excel: {output_filename}")
    sucesso = criar_excel_com_notas(dados, output_path)
    
    if sucesso:
        logger.info(f"\n{'='*60}")
        logger.info("✓ SUCESSO!")
        logger.info(f"{'='*60}\n")
        logger.info(f"Arquivo Excel criado com sucesso!\n")
        logger.info(f"Localização: {output_path}\n")
        
        # Listar alguns alunos como amostra
        logger.info("Amostra de alunos processados:")
        for i, aluno in enumerate(dados['alunos'][:5]):
            nota_str = f"{aluno['nota']:.2f}" if aluno['nota'] != '' else '-'
            logger.info(f"  {aluno['ordem']}. {aluno['nome']}")
            logger.info(f"     Nota Final: {nota_str}")
        
        if len(dados['alunos']) > 5:
            logger.info(f"  ... e mais {len(dados['alunos']) - 5} alunos")
        
        logger.info(f"\n{'='*60}\n")
    else:
        logger.error("\nERRO: Falha ao criar arquivo Excel!")
        sys.exit(1)

if __name__ == "__main__":
    main()