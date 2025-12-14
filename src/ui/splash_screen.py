"""
Splash screen com loading progressivo para melhorar percepção de performance.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import threading
import time
from src.core.config_logs import get_logger

logger = get_logger(__name__)


class SplashScreen:
    """Tela de carregamento com barra de progresso."""
    
    def __init__(self, title: str = "Sistema de Gestão Escolar"):
        """
        Inicializa a splash screen.
        
        Args:
            title: Título da aplicação
        """
        self.root = tk.Toplevel()
        self.root.title("")
        self.root.overrideredirect(True)  # Remove bordas da janela
        
        # Centralizar na tela
        window_width = 500
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Frame principal com borda
        main_frame = tk.Frame(
            self.root,
            bg='white',
            highlightbackground='#2563eb',
            highlightthickness=2
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Logo/Título
        title_label = tk.Label(
            main_frame,
            text=title,
            font=('Arial', 20, 'bold'),
            bg='white',
            fg='#2563eb'
        )
        title_label.pack(pady=30)
        
        # Subtítulo
        subtitle_label = tk.Label(
            main_frame,
            text="Carregando sistema...",
            font=('Arial', 10),
            bg='white',
            fg='#6b7280'
        )
        subtitle_label.pack(pady=5)
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=20)
        
        # Label de status
        self.status_var = tk.StringVar(value="Inicializando...")
        self.status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Arial', 9),
            bg='white',
            fg='#6b7280'
        )
        self.status_label.pack(pady=10)
        
        # Versão
        version_label = tk.Label(
            main_frame,
            text="v1.0.0 - Sprint 17",
            font=('Arial', 8),
            bg='white',
            fg='#9ca3af'
        )
        version_label.pack(side=tk.BOTTOM, pady=10)
        
        self.root.update()
    
    def update_progress(self, value: float, status: str = ""):
        """
        Atualiza a barra de progresso.
        
        Args:
            value: Valor de 0 a 100
            status: Mensagem de status opcional
        """
        try:
            self.progress_var.set(value)
            if status:
                self.status_var.set(status)
            self.root.update()
        except Exception as e:
            logger.warning(f"Erro ao atualizar splash: {e}")
    
    def close(self):
        """Fecha a splash screen."""
        try:
            self.root.destroy()
        except Exception as e:
            logger.warning(f"Erro ao fechar splash: {e}")


class ProgressiveLoader:
    """Gerencia carregamento progressivo de componentes."""
    
    def __init__(self, splash: Optional[SplashScreen] = None):
        """
        Inicializa o loader.
        
        Args:
            splash: Splash screen para feedback visual (opcional)
        """
        self.splash = splash
        self.tasks: list[tuple[str, Callable, float]] = []
        self.total_weight = 0.0
        self.current_progress = 0.0
    
    def add_task(
        self,
        name: str,
        func: Callable,
        weight: float = 1.0
    ):
        """
        Adiciona uma tarefa ao loader.
        
        Args:
            name: Nome descritivo da tarefa
            func: Função a executar
            weight: Peso relativo da tarefa (para cálculo de progresso)
        """
        self.tasks.append((name, func, weight))
        self.total_weight += weight
    
    def run(self) -> dict:
        """
        Executa todas as tarefas sequencialmente.
        
        Returns:
            Dicionário com resultados {task_name: result}
        """
        results = {}
        
        for name, func, weight in self.tasks:
            logger.info(f"Executando tarefa: {name}")
            
            # Atualizar splash
            if self.splash:
                progress = (self.current_progress / self.total_weight) * 100
                self.splash.update_progress(progress, name)
            
            # Executar tarefa
            start_time = time.time()
            try:
                result = func()
                results[name] = result
                elapsed = time.time() - start_time
                logger.info(f"Tarefa '{name}' concluída em {elapsed:.2f}s")
            except Exception as e:
                logger.exception(f"Erro na tarefa '{name}': {e}")
                results[name] = None
            
            self.current_progress += weight
        
        # Progresso final
        if self.splash:
            self.splash.update_progress(100, "Iniciando aplicação...")
        
        return results
    
    def run_async(
        self,
        on_complete: Optional[Callable] = None
    ) -> threading.Thread:
        """
        Executa tarefas em thread separada.
        
        Args:
            on_complete: Callback ao finalizar todas as tarefas
        
        Returns:
            Thread de execução
        """
        def _run_wrapper():
            results = self.run()
            if on_complete:
                on_complete(results)
        
        thread = threading.Thread(
            target=_run_wrapper,
            daemon=True,
            name="ProgressiveLoaderThread"
        )
        thread.start()
        return thread


def show_splash_with_loading(
    tasks: list[tuple[str, Callable, float]],
    title: str = "Sistema de Gestão Escolar"
) -> dict:
    """
    Mostra splash screen e executa tarefas de carregamento.
    
    Args:
        tasks: Lista de tuplas (name, func, weight)
        title: Título da splash screen
    
    Returns:
        Dicionário com resultados das tarefas
    """
    splash = SplashScreen(title)
    loader = ProgressiveLoader(splash)
    
    for name, func, weight in tasks:
        loader.add_task(name, func, weight)
    
    results = loader.run()
    
    # Manter splash visível por breve momento antes de fechar
    time.sleep(0.3)
    splash.close()
    
    return results


if __name__ == "__main__":
    # Teste da splash screen
    import random
    
    def task1():
        time.sleep(0.5)
        return "Task 1 OK"
    
    def task2():
        time.sleep(0.3)
        return "Task 2 OK"
    
    def task3():
        time.sleep(0.4)
        return "Task 3 OK"
    
    root = tk.Tk()
    root.withdraw()  # Esconde janela principal
    
    tasks = [
        ("Carregando módulos...", task1, 1.0),
        ("Conectando ao banco...", task2, 0.5),
        ("Preparando interface...", task3, 1.0),
    ]
    
    results = show_splash_with_loading(tasks)
    print("Resultados:", results)
    
    root.destroy()
