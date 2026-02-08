"""
Detecta erros na comparação de alunos entre Sistema Local e GEDUC
Identifica alunos que são a mesma pessoa mas com grafias diferentes de nome
"""

import json
from db.connection import conectar_bd
from comparar_alunos_geduc import normalizar_nome, buscar_alunos_sistema_local, carregar_alunos_geduc

def main():
    # Carregar dados
    print("Carregando dados...")
    alunos_local = buscar_alunos_sistema_local(2026, 60)
    alunos_geduc = carregar_alunos_geduc('alunos_geduc.json')
    
    print(f"\n{'='*80}")
    print("PROCURANDO ERROS NA COMPARACAO")
    print(f"{'='*80}\n")
    
    # Criar índices por CPF
    local_por_cpf = {}
    geduc_por_cpf = {}
    
    for aluno in alunos_local:
        cpf = aluno.get('cpf')
        if cpf:
            local_por_cpf[str(cpf)] = aluno
    
    for aluno in alunos_geduc:
        cpf = aluno.get('cpf')
        if cpf:
            geduc_por_cpf[str(cpf)] = aluno
    
    # Procurar alunos com mesmo CPF mas nomes normalizados diferentes
    erros_encontrados = []
    
    for cpf, aluno_geduc in geduc_por_cpf.items():
        if cpf in local_por_cpf:
            aluno_local = local_por_cpf[cpf]
            nome_local_norm = normalizar_nome(aluno_local['nome'])
            nome_geduc_norm = normalizar_nome(aluno_geduc['nome'])
            
            if nome_local_norm != nome_geduc_norm:
                # Calcular diferença entre os nomes
                palavras_local = set(nome_local_norm.split())
                palavras_geduc = set(nome_geduc_norm.split())
                diff = palavras_local ^ palavras_geduc
                
                erros_encontrados.append({
                    'cpf': cpf,
                    'local': aluno_local['nome'],
                    'geduc': aluno_geduc['nome'],
                    'local_norm': nome_local_norm,
                    'geduc_norm': nome_geduc_norm,
                    'nascimento': str(aluno_local.get('data_nascimento', '')),
                    'diferenca': diff
                })
    
    # Exibir resultados
    if erros_encontrados:
        print(f"AVISO: ENCONTRADOS {len(erros_encontrados)} ERROS DE COMPARACAO!\n")
        print("Estes alunos possuem o MESMO CPF mas nomes com grafias diferentes:")
        print("Sao a MESMA PESSOA e deveriam estar na secao 'EM AMBOS OS SISTEMAS'\n")
        print("="*80)
        
        for i, erro in enumerate(erros_encontrados, 1):
            print(f"\n{i}. CPF: {erro['cpf']}")
            print(f"   Nascimento: {erro['nascimento']}")
            print(f"   Sistema Local: {erro['local']}")
            print(f"   GEDUC        : {erro['geduc']}")
            print(f"   -" * 40)
            print(f"   Normalizado Local: {erro['local_norm']}")
            print(f"   Normalizado GEDUC: {erro['geduc_norm']}")
            print(f"   Palavras diferentes: {erro['diferenca']}")
        
        # Salvar em arquivo
        with open('erros_comparacao.txt', 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("ERROS DETECTADOS NA COMPARACAO\n")
            f.write("="*80 + "\n\n")
            f.write(f"Total de erros: {len(erros_encontrados)}\n\n")
            
            for i, erro in enumerate(erros_encontrados, 1):
                f.write(f"{i}. MESMO CPF - GRAFIAS DIFERENTES\n")
                f.write(f"   CPF: {erro['cpf']}\n")
                f.write(f"   Nascimento: {erro['nascimento']}\n")
                f.write(f"   Sistema Local: {erro['local']}\n")
                f.write(f"   GEDUC        : {erro['geduc']}\n")
                f.write(f"   Normalizado Local: {erro['local_norm']}\n")
                f.write(f"   Normalizado GEDUC: {erro['geduc_norm']}\n")
                f.write(f"   Diferenca: {erro['diferenca']}\n")
                f.write("\n")
        
        print(f"\n{'='*80}")
        print(f"Relatorio salvo em: erros_comparacao.txt")
        print(f"{'='*80}\n")
        
        # Estatísticas
        print("\nIMPACTO:")
        print(f"- {len(erros_encontrados)} alunos estao DUPLICADOS no relatorio")
        print(f"- Eles aparecem em 'Apenas no Sistema Local' E 'Apenas no GEDUC'")
        print(f"- Quando deveriam estar em 'Em Ambos os Sistemas'")
        
    else:
        print("OK: Nenhum erro encontrado!")
        print("Todos os alunos com mesmo CPF tem nomes identicos apos normalizacao.")

if __name__ == "__main__":
    main()
