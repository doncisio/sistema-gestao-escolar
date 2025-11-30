"""
Script para analisar dependências circulares no projeto.

Este script identifica imports circulares que podem causar problemas
de inicialização e dificultar a manutenção do código.
"""

import os
import re
import sys
from typing import Dict, Set, List, Tuple
from pathlib import Path
from collections import defaultdict

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_logs import get_logger

logger = get_logger(__name__)


class DependencyAnalyzer:
    """Analisador de dependências entre módulos Python."""
    
    def __init__(self, root_dir: str):
        """
        Inicializa o analisador.
        
        Args:
            root_dir: Diretório raiz do projeto
        """
        self.root_dir = Path(root_dir)
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.circular_deps: List[Tuple[str, str]] = []
        
    def analyze(self) -> None:
        """Analisa todos os arquivos Python no projeto."""
        logger.info("Iniciando análise de dependências...")
        
        # Encontrar todos os arquivos .py
        py_files = list(self.root_dir.rglob("*.py"))
        logger.info(f"Encontrados {len(py_files)} arquivos Python")
        
        # Analisar cada arquivo
        for py_file in py_files:
            if self._should_skip(py_file):
                continue
            
            self._analyze_file(py_file)
        
        # Detectar dependências circulares
        self._detect_circular_dependencies()
        
    def _should_skip(self, file_path: Path) -> bool:
        """
        Verifica se um arquivo deve ser ignorado.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se deve ser ignorado
        """
        # Ignorar diretórios específicos
        skip_dirs = {'__pycache__', '.git', 'venv', 'env', '.venv', 'node_modules'}
        
        for part in file_path.parts:
            if part in skip_dirs:
                return True
        
        return False
    
    def _analyze_file(self, file_path: Path) -> None:
        """
        Analisa imports de um arquivo.
        
        Args:
            file_path: Caminho do arquivo a analisar
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Obter nome do módulo relativo ao root
            relative_path = file_path.relative_to(self.root_dir)
            module_name = str(relative_path).replace(os.sep, '.').replace('.py', '')
            
            # Encontrar todos os imports
            imports = self._extract_imports(content)
            
            # Adicionar dependências
            for imp in imports:
                self.dependencies[module_name].add(imp)
                
        except Exception as e:
            logger.error(f"Erro ao analisar {file_path}: {e}")
    
    def _extract_imports(self, content: str) -> Set[str]:
        """
        Extrai imports de um arquivo Python.
        
        Args:
            content: Conteúdo do arquivo
            
        Returns:
            Conjunto de módulos importados
        """
        imports = set()
        
        # Padrões de import
        patterns = [
            r'^import\s+(\w+(?:\.\w+)*)',  # import module
            r'^from\s+(\w+(?:\.\w+)*)\s+import',  # from module import ...
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Ignorar comentários
            if line.startswith('#'):
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    module = match.group(1)
                    # Pegar apenas o primeiro nível do módulo
                    module = module.split('.')[0]
                    imports.add(module)
        
        return imports
    
    def _detect_circular_dependencies(self) -> None:
        """Detecta dependências circulares usando busca em profundidade."""
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> bool:
            """
            Busca em profundidade para detectar ciclos.
            
            Args:
                node: Nó atual
                path: Caminho percorrido
                
            Returns:
                True se encontrou ciclo
            """
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Visitar dependências
            for neighbor in self.dependencies.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Encontrou ciclo
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    logger.warning(f"🔴 Dependência circular detectada: {' → '.join(cycle)}")
                    
                    # Adicionar pares de dependências circulares
                    for i in range(len(cycle) - 1):
                        self.circular_deps.append((cycle[i], cycle[i + 1]))
                    
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        # Executar DFS para cada nó não visitado
        for node in list(self.dependencies.keys()):
            if node not in visited:
                dfs(node, [])
    
    def print_report(self) -> None:
        """Imprime relatório de análise."""
        print("\n" + "="*80)
        print("📊 RELATÓRIO DE ANÁLISE DE DEPENDÊNCIAS")
        print("="*80)
        
        print(f"\n📁 Total de módulos analisados: {len(self.dependencies)}")
        
        # Módulos mais dependentes
        print("\n📦 Top 10 módulos com mais dependências:")
        sorted_deps = sorted(
            self.dependencies.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        
        for module, deps in sorted_deps:
            print(f"  • {module}: {len(deps)} dependências")
        
        # Dependências circulares
        if self.circular_deps:
            print(f"\n🔴 ATENÇÃO: {len(set(self.circular_deps))} dependências circulares encontradas!")
            print("\nPares de módulos com dependência circular:")
            for mod1, mod2 in set(self.circular_deps):
                print(f"  ⚠️  {mod1} ↔ {mod2}")
        else:
            print("\n✅ Nenhuma dependência circular detectada!")
        
        print("\n" + "="*80)


def main():
    """Função principal."""
    # Diretório raiz do projeto
    root_dir = Path(__file__).parent.parent
    
    # Criar analisador
    analyzer = DependencyAnalyzer(str(root_dir))
    
    # Executar análise
    analyzer.analyze()
    
    # Imprimir relatório
    analyzer.print_report()


if __name__ == "__main__":
    main()
