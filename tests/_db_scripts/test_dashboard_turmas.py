"""
Teste para verificar o novo formato de dados do dashboard com turmas detalhadas
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.estatistica_service import obter_estatisticas_alunos

def main():
    print("=" * 80)
    print("TESTE: Dashboard com Turmas Detalhadas")
    print("=" * 80)
    
    dados = obter_estatisticas_alunos(escola_id=60, ano_letivo=None)
    
    if dados:
        print(f"✓ Dados obtidos com sucesso!\n")
        
        print("Estatísticas Gerais:")
        print(f"  • Total: {dados.get('total_alunos', 0)}")
        print(f"  • Ativos: {dados.get('alunos_ativos', 0)}")
        print(f"  • Transferidos: {dados.get('alunos_transferidos', 0)}")
        
        print("\n" + "=" * 80)
        print("ALUNOS POR SÉRIE (Agregado)")
        print("=" * 80)
        alunos_por_serie = dados.get('alunos_por_serie', [])
        for item in alunos_por_serie:
            print(f"  {item['serie']}: {item['quantidade']} alunos")
        
        print("\n" + "=" * 80)
        print("ALUNOS POR SÉRIE E TURMA (Detalhado)")
        print("=" * 80)
        turmas_detalhadas = dados.get('alunos_por_serie_turma', [])
        
        if turmas_detalhadas:
            serie_atual = None
            total_serie = 0
            
            for item in turmas_detalhadas:
                if item['serie'] != serie_atual:
                    if serie_atual is not None:
                        print(f"    └─ TOTAL: {total_serie} alunos\n")
                    serie_atual = item['serie']
                    total_serie = 0
                    print(f"  {item['serie']}:")
                
                turma = item['turma'] if item['turma'].strip() else '(sem nome)'
                print(f"    ├─ Turma {turma}: {item['quantidade']} alunos")
                total_serie += item['quantidade']
            
            if serie_atual is not None:
                print(f"    └─ TOTAL: {total_serie} alunos")
        
        print("\n" + "=" * 80)
        print("VERIFICAÇÃO: SÉRIES COM MÚLTIPLAS TURMAS")
        print("=" * 80)
        
        # Agrupar para verificar
        series_com_multiplas = {}
        for item in turmas_detalhadas:
            serie = item['serie']
            if serie not in series_com_multiplas:
                series_com_multiplas[serie] = []
            series_com_multiplas[serie].append(item)
        
        for serie, turmas in series_com_multiplas.items():
            if len(turmas) > 1:
                print(f"\n  ✓ {serie} tem {len(turmas)} turmas:")
                for turma in turmas:
                    print(f"    - Turma {turma['turma']}: {turma['quantidade']} alunos")
            else:
                print(f"  • {serie}: 1 turma apenas")
        
        print("\n" + "=" * 80)
        print("SIMULAÇÃO: COMO APARECERÁ NO GRÁFICO")
        print("=" * 80)
        
        labels = []
        quantidades = []
        
        for item in alunos_por_serie:
            serie = item['serie']
            qtd_total = item['quantidade']
            
            # Se a série tem múltiplas turmas, mostrar detalhadas
            if serie in series_com_multiplas and len(series_com_multiplas[serie]) > 1:
                for turma_item in series_com_multiplas[serie]:
                    turma = turma_item['turma']
                    qtd_turma = turma_item['quantidade']
                    label = f"{serie} {turma}" if turma.strip() else serie
                    labels.append(label)
                    quantidades.append(qtd_turma)
            else:
                labels.append(serie)
                quantidades.append(qtd_total)
        
        print("\nLabels do gráfico:")
        for label, qtd in zip(labels, quantidades):
            print(f"  • {label}: {qtd} alunos ({qtd/sum(quantidades)*100:.1f}%)")
        
        print(f"\n✓ Total de fatias no gráfico: {len(labels)}")
        
    else:
        print("✗ Falha ao obter dados")
        return 1
    
    print("\n" + "=" * 80)
    return 0

if __name__ == '__main__':
    sys.exit(main())
