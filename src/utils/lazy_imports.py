"""
Sistema de lazy loading para imports pesados.

Este módulo permite postergar imports de bibliotecas pesadas até que sejam
efetivamente necessárias, melhorando significativamente o tempo de startup.
"""

import importlib
import sys
from types import ModuleType
from typing import Any, Optional, cast
from functools import wraps
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class LazyModule(ModuleType):
    """Wrapper para carregar módulos sob demanda."""
    
    def __init__(self, module_name: str, submodule: Optional[str] = None):
        """
        Inicializa o lazy loader.
        
        Args:
            module_name: Nome do módulo a ser carregado
            submodule: Submódulo específico a importar (opcional)
        """
        # Inicializar como ModuleType
        super().__init__(module_name)
        
        self._module_name = module_name
        self._submodule = submodule
        self._module: Optional[Any] = None
        self._load_attempted = False
    
    def _load(self) -> Any:
        """Carrega o módulo efetivamente."""
        if self._module is None and not self._load_attempted:
            self._load_attempted = True
            try:
                if self._submodule:
                    base_module = importlib.import_module(self._module_name)
                    self._module = getattr(base_module, self._submodule)
                else:
                    self._module = importlib.import_module(self._module_name)
                
                logger.info(f"Lazy loaded: {self._module_name}" + 
                          (f".{self._submodule}" if self._submodule else ""))
            except ImportError as e:
                logger.exception(f"Falha ao carregar {self._module_name}: {e}")
                raise
        
        return self._module
    
    def __getattr__(self, name: str) -> Any:
        """Redireciona acessos de atributos para o módulo real."""
        module = self._load()
        return getattr(module, name)
    
    def __call__(self, *args, **kwargs):
        """Permite chamar o módulo como função se aplicável."""
        module = self._load()
        return module(*args, **kwargs)


# Módulos pesados com lazy loading
_matplotlib = LazyModule('matplotlib')
_matplotlib_pyplot = LazyModule('matplotlib.pyplot')
_matplotlib_figure = LazyModule('matplotlib.figure', 'Figure')
_matplotlib_backends = LazyModule('matplotlib.backends.backend_tkagg', 'FigureCanvasTkAgg')

_pandas = LazyModule('pandas')
_numpy = LazyModule('numpy')

_reportlab_platypus = LazyModule('reportlab.platypus')
_reportlab_lib_pagesizes = LazyModule('reportlab.lib.pagesizes')
_reportlab_lib_styles = LazyModule('reportlab.lib.styles')


def get_matplotlib():
    """Retorna matplotlib com lazy loading."""
    return _matplotlib._load()


def get_pyplot():
    """Retorna matplotlib.pyplot com lazy loading."""
    return _matplotlib_pyplot._load()


def get_matplotlib_figure():
    """Retorna matplotlib.figure.Figure com lazy loading."""
    return _matplotlib_figure._load()


def get_matplotlib_canvas():
    """Retorna FigureCanvasTkAgg com lazy loading."""
    return _matplotlib_backends._load()


def get_pandas():
    """Retorna pandas com lazy loading."""
    return _pandas._load()


def get_numpy():
    """Retorna numpy com lazy loading."""
    return _numpy._load()


def get_reportlab_platypus():
    """Retorna reportlab.platypus com lazy loading."""
    return _reportlab_platypus._load()


def get_reportlab_pagesizes():
    """Retorna reportlab.lib.pagesizes com lazy loading."""
    return _reportlab_lib_pagesizes._load()


def get_reportlab_styles():
    """Retorna reportlab.lib.styles com lazy loading."""
    return _reportlab_lib_styles._load()


def with_lazy_import(module_getter):
    """
    Decorator para funções que usam imports pesados.
    
    Usage:
        @with_lazy_import(get_pandas)
        def processar_dados():
            pd = get_pandas()
            df = pd.DataFrame(...)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Garante que o módulo está carregado
            module_getter()
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Compatibilidade com código existente que faz import direto
def enable_lazy_imports():
    """
    Injeta lazy loaders no sys.modules para interceptar imports.
    
    ATENÇÃO: Use com cuidado. Pode causar problemas se módulos já foram importados.
    """
    lazy_modules = {
        'matplotlib': _matplotlib,
        'matplotlib.pyplot': _matplotlib_pyplot,
        'pandas': _pandas,
        'numpy': _numpy,
    }
    
    for name, lazy_module in lazy_modules.items():
        if name not in sys.modules:
            sys.modules[name] = lazy_module
            logger.debug(f"Registrado lazy loader para {name}")


def preload_heavy_modules_async():
    """
    Pré-carrega módulos pesados em background thread.
    
    Útil para carregar módulos durante idle time do usuário.
    """
    import threading
    
    def _preload():
        try:
            logger.info("Iniciando pré-carregamento de módulos pesados...")
            get_matplotlib()
            get_pandas()
            logger.info("Módulos pesados pré-carregados com sucesso")
        except Exception as e:
            logger.exception(f"Erro ao pré-carregar módulos: {e}")
    
    thread = threading.Thread(target=_preload, daemon=True, name="PreloadThread")
    thread.start()
    return thread


if __name__ == "__main__":
    # Teste do sistema de lazy loading
    import time
    
    print("Testando lazy loading...")
    start = time.time()
    
    # Acesso que deve carregar o módulo
    pd = get_pandas()
    print(f"Pandas carregado em {time.time() - start:.2f}s")
    
    # Segunda chamada deve ser instantânea
    start2 = time.time()
    pd2 = get_pandas()
    print(f"Segunda chamada: {time.time() - start2:.4f}s")
    
    assert pd is pd2, "Deve retornar a mesma instância"
    print("✅ Teste de lazy loading OK")
