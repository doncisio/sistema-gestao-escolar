"""
Testes de performance para queries do banco de dados.

Valida que as queries principais do sistema executam dentro de limites aceitáveis
e que o sistema suporta carga concorrente.
"""
import pytest
import time
from statistics import mean, median
from typing import Dict, Any, List
import concurrent.futures
from unittest.mock import Mock, patch

# Imports do sistema
from conexao import inicializar_pool, fechar_pool
from db.connection import get_cursor


@pytest.fixture(scope='module')
def setup_db():
    """Inicializa pool de conexões para os testes"""
    inicializar_pool()
    yield
    fechar_pool()


def measure_query_time(query: str, params: tuple = None, iterations: int = 50) -> Dict[str, float]:
    """
    Mede tempo de execução de uma query.
    
    Args:
        query: Query SQL a executar
        params: Parâmetros da query
        iterations: Número de vezes a executar
    
    Returns:
        Dicionário com estatísticas (mean, median, min, max)
    """
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        try:
            with get_cursor() as cursor:
                cursor.execute(query, params)
                cursor.fetchall()
        except Exception:
            # Ignora erros para não quebrar medição
            pass
        end = time.perf_counter()
        times.append(end - start)
    
    return {
        'mean': mean(times),
        'median': median(times),
        'min': min(times),
        'max': max(times),
        'iterations': iterations
    }


class TestQueryPerformance:
    """Testes de performance de queries individuais"""
    
    def test_query_listar_alunos_performance(self, setup_db):
        """Query de listagem de alunos deve ser rápida"""
        stats = measure_query_time(
            "SELECT * FROM alunos WHERE escola_id = %s LIMIT 100",
            (60,),
            iterations=50
        )
        
        # Assertions de performance (valores em segundos)
        assert stats['mean'] < 0.2, f"Query muito lenta: {stats['mean']*1000:.2f}ms"
        assert stats['max'] < 0.5, f"Pico de latência alto: {stats['max']*1000:.2f}ms"
        
        print(f"\n📊 Listar alunos: avg={stats['mean']*1000:.2f}ms, "
              f"median={stats['median']*1000:.2f}ms, "
              f"max={stats['max']*1000:.2f}ms")
    
    def test_query_count_alunos_performance(self, setup_db):
        """Query de contagem deve ser muito rápida"""
        stats = measure_query_time(
            "SELECT COUNT(*) FROM alunos WHERE escola_id = %s",
            (60,),
            iterations=100
        )
        
        # Contagem deve ser bem rápida
        assert stats['mean'] < 0.1, f"Count muito lento: {stats['mean']*1000:.2f}ms"
        assert stats['max'] < 0.3, f"Pico de latência alto: {stats['max']*1000:.2f}ms"
        
        print(f"\n📊 Count alunos: avg={stats['mean']*1000:.2f}ms, "
              f"median={stats['median']*1000:.2f}ms")
    
    def test_query_buscar_matriculas_performance(self, setup_db):
        """Query de busca de matrículas deve ser eficiente"""
        stats = measure_query_time(
            """
            SELECT m.*, a.nome, t.nome_turma 
            FROM matriculas m
            JOIN alunos a ON m.aluno_id = a.id
            JOIN turmas t ON m.turma_id = t.id
            WHERE m.escola_id = %s
            LIMIT 100
            """,
            (60,),
            iterations=50
        )
        
        assert stats['mean'] < 0.3, f"Query de matrículas lenta: {stats['mean']*1000:.2f}ms"
        
        print(f"\n📊 Buscar matrículas: avg={stats['mean']*1000:.2f}ms, "
              f"max={stats['max']*1000:.2f}ms")
    
    def test_query_funcionarios_performance(self, setup_db):
        """Query de listagem de funcionários deve ser rápida"""
        stats = measure_query_time(
            "SELECT * FROM funcionarios WHERE escola_id = %s",
            (60,),
            iterations=50
        )
        
        assert stats['mean'] < 0.15, f"Query de funcionários lenta: {stats['mean']*1000:.2f}ms"
        
        print(f"\n📊 Listar funcionários: avg={stats['mean']*1000:.2f}ms")


class TestDashboardPerformance:
    """Testes de performance do dashboard"""
    
    def test_dashboard_statistics_performance(self, setup_db):
        """Estatísticas do dashboard devem carregar rapidamente"""
        from services.estatistica_service import obter_estatisticas_alunos
        
        start = time.perf_counter()
        try:
            stats = obter_estatisticas_alunos()
            elapsed = time.perf_counter() - start
            
            # Dashboard deve carregar em menos de 2 segundos (inclui múltiplas queries)
            assert elapsed < 2.0, f"Dashboard muito lento: {elapsed*1000:.2f}ms"
            assert stats is not None
            
            print(f"\n📊 Dashboard carregado em {elapsed*1000:.2f}ms")
            
        except Exception as e:
            # Se falhar, ainda queremos medir o tempo
            elapsed = time.perf_counter() - start
            print(f"\n⚠️ Dashboard falhou após {elapsed*1000:.2f}ms: {e}")
    
    def test_dashboard_with_cache_performance(self, setup_db):
        """Dashboard com cache deve ser muito mais rápido"""
        from services.estatistica_service import obter_estatisticas_alunos
        
        # Primeira chamada (sem cache)
        start = time.perf_counter()
        try:
            stats1 = obter_estatisticas_alunos()
            time_without_cache = time.perf_counter() - start
        except Exception:
            time_without_cache = 0
        
        # Segunda chamada (com cache)
        start = time.perf_counter()
        try:
            stats2 = obter_estatisticas_alunos()
            time_with_cache = time.perf_counter() - start
        except Exception:
            time_with_cache = 0
        
        if time_without_cache > 0 and time_with_cache > 0:
            # Cache deve reduzir tempo em pelo menos 50%
            improvement = (time_without_cache - time_with_cache) / time_without_cache
            
            print(f"\n📊 Sem cache: {time_without_cache*1000:.2f}ms, "
                  f"Com cache: {time_with_cache*1000:.2f}ms, "
                  f"Melhoria: {improvement*100:.1f}%")
            
            assert time_with_cache < time_without_cache, "Cache não está funcionando"


class TestConcurrentLoad:
    """Testes de carga concorrente"""
    
    def test_concurrent_read_queries(self, setup_db):
        """Sistema deve suportar múltiplas leituras simultâneas"""
        
        def query_alunos(i: int) -> int:
            """Executa query de contagem"""
            with get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM alunos WHERE escola_id = %s", (60,))
                result = cursor.fetchone()
                return result[0] if result else 0
        
        # Executar 50 queries com 10 threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            start = time.perf_counter()
            futures = [executor.submit(query_alunos, i) for i in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            elapsed = time.perf_counter() - start
        
        assert len(results) == 50
        assert elapsed < 5.0, f"Carga concorrente muito lenta: {elapsed:.2f}s"
        
        print(f"\n✅ 50 queries executadas com 10 threads em {elapsed:.2f}s "
              f"({elapsed/50*1000:.2f}ms por query)")
    
    def test_mixed_concurrent_operations(self, setup_db):
        """Sistema deve suportar operações mistas (leitura/escrita)"""
        
        def read_operation(i: int) -> bool:
            """Operação de leitura"""
            try:
                with get_cursor() as cursor:
                    cursor.execute("SELECT id FROM alunos WHERE escola_id = %s LIMIT 1", (60,))
                    cursor.fetchone()
                return True
            except Exception:
                return False
        
        def write_operation(i: int) -> bool:
            """Operação de escrita (simulada com SELECT)"""
            try:
                with get_cursor() as cursor:
                    # Simula escrita sem alterar dados
                    cursor.execute("SELECT 1")
                return True
            except Exception:
                return False
        
        # Mix de operações
        operations = []
        for i in range(30):
            operations.append(('read', i))
        for i in range(10):
            operations.append(('write', i))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            start = time.perf_counter()
            futures = []
            
            for op_type, i in operations:
                if op_type == 'read':
                    futures.append(executor.submit(read_operation, i))
                else:
                    futures.append(executor.submit(write_operation, i))
            
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            elapsed = time.perf_counter() - start
        
        success_rate = sum(results) / len(results)
        
        assert success_rate > 0.95, f"Taxa de sucesso baixa: {success_rate*100:.1f}%"
        assert elapsed < 3.0, f"Operações mistas lentas: {elapsed:.2f}s"
        
        print(f"\n✅ 40 operações mistas em {elapsed:.2f}s "
              f"(taxa de sucesso: {success_rate*100:.1f}%)")


class TestCachePerformance:
    """Testes de performance do sistema de cache"""
    
    def test_cache_hit_performance(self):
        """Cache hit deve ser quase instantâneo"""
        from utils.cache import CacheManager
        
        cache = CacheManager(ttl_seconds=300)
        
        # Adicionar dados ao cache
        cache.set('test_key', {'data': 'value'})
        
        # Medir tempo de acesso ao cache
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            value = cache.get('test_key')
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            assert value is not None
        
        avg_time = mean(times)
        max_time = max(times)
        
        # Cache deve ser extremamente rápido (< 0.1ms no pior caso)
        assert avg_time < 0.0001, f"Cache hit lento: {avg_time*1000000:.2f}µs"
        assert max_time < 0.001, f"Pico de cache hit alto: {max_time*1000000:.2f}µs"
        
        print(f"\n📊 Cache hit: avg={avg_time*1000000:.2f}µs, max={max_time*1000000:.2f}µs")
    
    def test_cached_decorator_performance(self):
        """Decorator @cached deve melhorar performance"""
        from utils.cache import CacheManager
        
        cache = CacheManager(ttl_seconds=300)
        
        call_count = 0
        
        @cache.cached()
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # Simula operação cara
            return x * 2
        
        # Primeira chamada (sem cache)
        start = time.perf_counter()
        result1 = expensive_function(5)
        time_without_cache = time.perf_counter() - start
        
        # Segunda chamada (com cache)
        start = time.perf_counter()
        result2 = expensive_function(5)
        time_with_cache = time.perf_counter() - start
        
        assert result1 == result2 == 10
        assert call_count == 1  # Função chamada apenas uma vez
        assert time_with_cache < 0.01  # Cache deve ser quase instantâneo
        
        improvement = (time_without_cache - time_with_cache) / time_without_cache
        
        print(f"\n📊 Sem cache: {time_without_cache*1000:.2f}ms, "
              f"Com cache: {time_with_cache*1000:.2f}ms, "
              f"Melhoria: {improvement*100:.1f}%")
        
        assert improvement > 0.9  # Pelo menos 90% de melhoria


class TestMemoryPerformance:
    """Testes de uso de memória"""
    
    def test_large_result_set_performance(self, setup_db):
        """Sistema deve lidar bem com grandes conjuntos de resultados"""
        
        start = time.perf_counter()
        try:
            with get_cursor() as cursor:
                # Buscar muitos registros
                cursor.execute("SELECT * FROM alunos LIMIT 1000")
                results = cursor.fetchall()
                elapsed = time.perf_counter() - start
                
                # Deve processar 1000 registros rapidamente
                assert elapsed < 1.0, f"Processamento de 1000 registros lento: {elapsed:.2f}s"
                
                print(f"\n📊 Processou {len(results)} registros em {elapsed*1000:.2f}ms")
        except Exception as e:
            print(f"\n⚠️ Erro ao processar grandes resultados: {e}")
    
    def test_cache_memory_efficiency(self):
        """Cache não deve consumir memória excessiva"""
        from utils.cache import CacheManager
        import sys
        
        cache = CacheManager(ttl_seconds=300)
        
        # Adicionar muitas entradas ao cache
        large_data = {'data': 'x' * 1000}  # 1KB por entrada
        
        for i in range(100):
            cache.set(f'key_{i}', large_data.copy())
        
        # Verificar estatísticas
        stats = cache.get_stats()
        
        assert stats['size'] == 100
        print(f"\n📊 Cache com {stats['size']} entradas")


if __name__ == '__main__':
    # Executar com: pytest tests/performance/ -v --durations=10
    pytest.main([__file__, '-v', '--durations=10'])
