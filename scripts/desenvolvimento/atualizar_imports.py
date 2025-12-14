"""
Script para atualizar todos os imports após reorganização do projeto.
"""

import os
import re
from pathlib import Path

# Diretório raiz do projeto
PROJECT_ROOT = Path(r"c:\gestao")

# Mapeamento de imports antigos para novos
IMPORT_MAPPING = {
    # Módulos core
    r"from src.core.config_logs import": "from src.core.config_logs import",
    r"from src.core.config import": "from src.core.config import",
    r"from src.core.conexao import": "from src.core.conexao import",
    r"from src.core.seguranca import": "from src.core.seguranca import",
    r"import src.core.seguranca as Seguranca": "import src.core.seguranca as Seguranca",
    
    # GerarPDF (movido para src/relatorios/)
    r"from src.relatorios.gerar_pdf import": "from src.relatorios.gerar_pdf import",
    r"from src.relatorios import gerar_pdf as gerarPDF": "from src.relatorios import gerar_pdf as gerarPDF",
    
    # Relatórios - Atas
    r"from src.relatorios.atas.ata_geral import": "from src.relatorios.atas.ata_geral import",
    r"from src.relatorios.atas.ata_1a5ano import": "from src.relatorios.atas.ata_1a5ano import",
    r"from src.relatorios.atas.ata_1a9ano import": "from src.relatorios.atas.ata_1a9ano import",
    r"from src.relatorios.atas.ata_6a9ano import": "from src.relatorios.atas.ata_6a9ano import",
    
    # Relatórios - Listas
    r"from src.relatorios.listas.lista_alfabetica import": "from src.relatorios.listas.lista_alfabetica import",
    r"from src.relatorios.listas.lista_transtornos import": "from src.relatorios.listas.lista_transtornos import",
    r"from src.relatorios.listas.lista_contatos import": "from src.relatorios.listas.lista_contatos import",
    r"from src.relatorios.listas.lista_frequencia import": "from src.relatorios.listas.lista_frequencia import",
    r"from src.relatorios.listas.lista_notas import": "from src.relatorios.listas.lista_notas import",
    r"from src.relatorios.listas.lista_reuniao import": "from src.relatorios.listas.lista_reuniao import",
    r"from src.relatorios.listas.lista_atualizada import": "from src.relatorios.listas.lista_atualizada import",
    r"from src.relatorios.listas.lista_semed import": "from src.relatorios.listas.lista_semed import",
    
    # Relatórios - Geradores
    r"from src.relatorios.geradores.certificado_v1 import": "from src.relatorios.geradores.certificado_v1 import",
    r"from src.relatorios.geradores.certificado import": "from src.relatorios.geradores.certificado import",
    r"from src.relatorios.geradores.folha_ponto import": "from src.relatorios.geradores.folha_ponto import",
    r"from src.relatorios.geradores.tabela_frequencia import": "from src.relatorios.geradores.tabela_frequencia import",
    r"from src.relatorios.geradores.resumo_ponto import": "from src.relatorios.geradores.resumo_ponto import",
    r"from src.relatorios.geradores.reuniao import": "from src.relatorios.geradores.reuniao import",
    
    # Relatórios principais
    r"from src.relatorios.boletim import": "from src.relatorios.boletim import",
    r"from src.relatorios.declaracao_comparecimento import": "from src.relatorios.declaracao_comparecimento import",
    r"from src.relatorios.historico_escolar import": "from src.relatorios.historico_escolar import",
    r"from src.relatorios.movimento_mensal import": "from src.relatorios.movimento_mensal import",
    r"from src.relatorios.nota_ata import": "from src.relatorios.nota_ata import",
    r"from src.relatorios.relatorio_analise_notas import": "from src.relatorios.relatorio_analise_notas import",
    r"from src.relatorios.relatorio_pendencias import": "from src.relatorios.relatorio_pendencias import",
    
    # Interfaces
    r"from src.interfaces.cadastro_aluno import": "from src.interfaces.cadastro_aluno import",
    r"from src.interfaces.edicao_aluno import": "from src.interfaces.edicao_aluno import",
    r"from src.interfaces.cadastro_funcionario import": "from src.interfaces.cadastro_funcionario import",
    r"from src.interfaces.edicao_funcionario import": "from src.interfaces.edicao_funcionario import",
    r"from src.interfaces.cadastro_notas import": "from src.interfaces.cadastro_notas import",
    r"from src.interfaces.cadastro_faltas import": "from src.interfaces.cadastro_faltas import",
    r"from src.interfaces.lancamento_frequencia import": "from src.interfaces.lancamento_frequencia import",
    r"from src.interfaces.matricula_unificada import": "from src.interfaces.matricula_unificada import",
    r"from src.interfaces.historico_escolar import": "from src.interfaces.historico_escolar import",
    r"from src.interfaces.administrativa import": "from src.interfaces.administrativa import",
    r"from src.interfaces.solicitacao_professores import": "from src.interfaces.solicitacao_professores import",
    r"from src.interfaces.gerenciamento_licencas import": "from src.interfaces.gerenciamento_licencas import",
    
    # Gestores
    r"from src.gestores.documentos_funcionarios import": "from src.gestores.documentos_funcionarios import",
    r"from src.gestores.documentos_sistema import": "from src.gestores.documentos_sistema import",
    r"from src.gestores.historico_manager import": "from src.gestores.historico_manager import",
    r"from src.gestores.storage_manager import": "from src.gestores.storage_manager import",
    r"from src.gestores.storage_manager_impl import": "from src.gestores.storage_manager_impl import",
    
    # Importadores
    r"from src.importadores.bncc_excel import": "from src.importadores.bncc_excel import",
    r"from src.importadores.notas_html import": "from src.importadores.notas_html import",
    r"from src.importadores.geduc import": "from src.importadores.geduc import",
    
    # Avaliações
    r"from src.avaliacoes.janela_fila_correcao import": "from src.avaliacoes.janela_fila_correcao import",
    r"from src.avaliacoes.janela_registro_respostas import": "from src.avaliacoes.janela_registro_respostas import",
    r"from src.avaliacoes.integrador_preenchimento import": "from src.avaliacoes.integrador_preenchimento import",
}

# Arquivos a ignorar (já movidos ou que não devem ser alterados)
IGNORE_PATTERNS = [
    r"__pycache__",
    r"\.git",
    r"\.venv",
    r"venv",
    r"node_modules",
    r"arquivos_nao_utilizados",
    r"scripts_nao_utilizados",
    r"\.pyc$",
    r"\.pyo$",
]

def should_ignore(path: Path) -> bool:
    """Verifica se o arquivo deve ser ignorado."""
    path_str = str(path)
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, path_str):
            return True
    return False

def update_imports_in_file(file_path: Path) -> int:
    """
    Atualiza imports em um arquivo Python.
    Retorna o número de substituições feitas.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements = 0
        
        # Aplicar cada mapeamento de import
        for old_pattern, new_import in IMPORT_MAPPING.items():
            # Contar quantas vezes o padrão aparece
            matches = re.findall(old_pattern, content)
            if matches:
                content = re.sub(old_pattern, new_import, content)
                replacements += len(matches)
        
        # Se houve mudanças, salvar o arquivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ {file_path.relative_to(PROJECT_ROOT)}: {replacements} imports atualizados")
            return replacements
        
        return 0
        
    except Exception as e:
        print(f"✗ Erro ao processar {file_path}: {e}")
        return 0

def main():
    """Função principal."""
    print("=" * 70)
    print("ATUALIZANDO IMPORTS DO PROJETO")
    print("=" * 70)
    print()
    
    total_files = 0
    total_replacements = 0
    updated_files = []
    
    # Percorrer todos os arquivos .py do projeto
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_ignore(py_file):
            continue
        
        total_files += 1
        replacements = update_imports_in_file(py_file)
        
        if replacements > 0:
            total_replacements += replacements
            updated_files.append(py_file)
    
    print()
    print("=" * 70)
    print("RESUMO")
    print("=" * 70)
    print(f"Arquivos analisados: {total_files}")
    print(f"Arquivos atualizados: {len(updated_files)}")
    print(f"Total de imports corrigidos: {total_replacements}")
    print()
    
    if updated_files:
        print("Arquivos atualizados:")
        for file_path in updated_files[:20]:  # Mostrar apenas os primeiros 20
            print(f"  - {file_path.relative_to(PROJECT_ROOT)}")
        
        if len(updated_files) > 20:
            print(f"  ... e mais {len(updated_files) - 20} arquivos")
    
    print()
    print("✅ Atualização de imports concluída!")

if __name__ == "__main__":
    main()
