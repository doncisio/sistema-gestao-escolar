"""
Script de Migração - Fase 7: Criação de Usuários em Produção

Cria usuários para funcionários da escola_id=60 com os seguintes cargos:
- Gestor Escolar → perfil: administrador
- Professor@ → perfil: professor  
- Especialista (Coordenadora) → perfil: coordenador
- Auxiliar administrativo → perfil: administrador
- Técnico em Administração Escolar → perfil: administrador

Regras:
- Username: CPF (apenas números)
- Senha padrão: CPF (apenas números)
- Tarcisio Sousa de Almeida (ID=1) será o superusuário (administrador)
- primeiro_acesso = True (forçar troca de senha no primeiro login)

Executar: python scripts/migrar_usuarios_fase7.py
"""

import os
import sys
import re

# Garantir imports do projeto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from conexao import conectar_bd
from auth.password_utils import gerar_hash_senha
from config_logs import get_logger

logger = get_logger(__name__)

# Mapeamento de cargos para perfis
CARGO_PARA_PERFIL = {
    'Gestor Escolar': 'administrador',
    'Professor@': 'professor',
    'Especialista (Coordenadora)': 'coordenador',
    'Auxiliar administrativo': 'administrador',
    'Técnico em Administração Escolar': 'administrador',
}

# ID do funcionário Tarcisio (superusuário)
TARCISIO_ID = 1


def limpar_cpf(cpf: str) -> str:
    """Remove pontuação do CPF, retornando apenas números."""
    if not cpf:
        return ''
    return re.sub(r'\D', '', cpf)


def buscar_funcionarios_escola_60(cursor):
    """Busca funcionários da escola 60 com cargos relevantes."""
    cargos = list(CARGO_PARA_PERFIL.keys())
    placeholders = ', '.join(['%s'] * len(cargos))
    
    query = f'''
        SELECT id, nome, cpf, cargo 
        FROM funcionarios 
        WHERE escola_id = 60 
        AND cargo IN ({placeholders})
        ORDER BY cargo, nome
    '''
    cursor.execute(query, cargos)
    return cursor.fetchall()


def usuario_ja_existe(cursor, funcionario_id: int, cpf_limpo: str) -> bool:
    """Verifica se já existe usuário para o funcionário ou com o CPF como username."""
    # Verifica por funcionario_id
    cursor.execute("SELECT id FROM usuarios WHERE funcionario_id = %s", (funcionario_id,))
    if cursor.fetchone():
        return True
    
    # Verifica por username (CPF)
    cursor.execute("SELECT id FROM usuarios WHERE username = %s", (cpf_limpo,))
    if cursor.fetchone():
        return True
    
    return False


def criar_usuario(cursor, funcionario_id: int, nome: str, cpf: str, cargo: str) -> tuple:
    """
    Cria um usuário no sistema.
    
    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    cpf_limpo = limpar_cpf(cpf)
    
    if not cpf_limpo:
        return False, f"CPF não cadastrado para {nome}"
    
    if len(cpf_limpo) != 11:
        return False, f"CPF inválido ({cpf}) para {nome}"
    
    # Verifica se já existe
    if usuario_ja_existe(cursor, funcionario_id, cpf_limpo):
        return False, f"Usuário já existe para {nome}"
    
    # Determina o perfil
    perfil = CARGO_PARA_PERFIL.get(cargo)
    if not perfil:
        return False, f"Cargo '{cargo}' não mapeado para {nome}"
    
    # Senha = CPF (será forçado a trocar no primeiro acesso)
    senha_hash = gerar_hash_senha(cpf_limpo)
    
    # Insere o usuário
    cursor.execute('''
        INSERT INTO usuarios (funcionario_id, username, senha_hash, perfil, ativo, primeiro_acesso)
        VALUES (%s, %s, %s, %s, TRUE, TRUE)
    ''', (funcionario_id, cpf_limpo, senha_hash, perfil))
    
    return True, f"✅ Criado: {cpf_limpo} ({perfil}) - {nome}"


def main():
    """Executa a migração de usuários."""
    print("=" * 80)
    print("FASE 7 - MIGRAÇÃO DE USUÁRIOS PARA PRODUÇÃO")
    print("=" * 80)
    print()
    
    conn = conectar_bd()
    if not conn:
        print("❌ Erro: Não foi possível conectar ao banco de dados")
        return
    
    cursor = conn.cursor()
    
    try:
        # Busca funcionários elegíveis
        funcionarios = buscar_funcionarios_escola_60(cursor)
        
        print(f"📋 Encontrados {len(funcionarios)} funcionários elegíveis na escola 60")
        print()
        
        criados = 0
        erros = 0
        ignorados = 0
        
        resultados = {
            'administrador': [],
            'coordenador': [],
            'professor': [],
        }
        
        from decimal import Decimal
        from typing import Any

        for func_id, nome, cpf, cargo in funcionarios:
            # Normalizar campos que podem ter tipos não-string retornados pelo cursor
            nome_str = str(nome) if nome is not None else ''
            cargo_str = str(cargo) if cargo is not None else ''
            cpf_str = str(cpf) if cpf is not None else ''
            # Converter id retornado pelo cursor para `int` explicitamente
            # quando for um tipo compatível (int, Decimal, str de dígitos).
            # Se não for possível converter, registramos erro e pulamos.
            func_id_any: Any = func_id
            try:
                if isinstance(func_id_any, int):
                    funcionario_id_int: int = func_id_any
                elif isinstance(func_id_any, Decimal):
                    funcionario_id_int = int(func_id_any)
                elif isinstance(func_id_any, str) and func_id_any.isdigit():
                    funcionario_id_int = int(func_id_any)
                else:
                    funcionario_id_int = int(func_id_any)  # type: ignore[arg-type]
            except Exception:
                erros += 1
                print(f"IGNORADO: ID inválido para funcionário {nome!r}: {func_id!r}")
                continue

            sucesso, mensagem = criar_usuario(cursor, funcionario_id_int, nome_str, cpf_str, cargo_str)
            
            if sucesso:
                criados += 1
                perfil = CARGO_PARA_PERFIL.get(cargo_str, 'professor')
                resultados[perfil].append((limpar_cpf(cpf_str), nome_str))
                print(mensagem)
            elif "já existe" in mensagem:
                ignorados += 1
                print(f"⏭️  {mensagem}")
            else:
                erros += 1
                print(f"❌ {mensagem}")
        
        # Commit das alterações
        conn.commit()
        
        print()
        print("=" * 80)
        print("RESUMO DA MIGRAÇÃO")
        print("=" * 80)
        print(f"✅ Usuários criados: {criados}")
        print(f"⏭️  Ignorados (já existiam): {ignorados}")
        print(f"❌ Erros: {erros}")
        print()
        
        # Lista por perfil
        if resultados['administrador']:
            print("👤 ADMINISTRADORES:")
            for cpf, nome in resultados['administrador']:
                print(f"   Login: {cpf} | Senha: {cpf} | {nome}")
            print()
        
        if resultados['coordenador']:
            print("📚 COORDENADORES:")
            for cpf, nome in resultados['coordenador']:
                print(f"   Login: {cpf} | Senha: {cpf} | {nome}")
            print()
        
        if resultados['professor']:
            print("🎓 PROFESSORES:")
            for cpf, nome in resultados['professor']:
                print(f"   Login: {cpf} | Senha: {cpf} | {nome}")
            print()
        
        print("=" * 80)
        print("⚠️  IMPORTANTE: Todos os usuários devem trocar a senha no primeiro acesso!")
        print("=" * 80)
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro durante a migração: {e}")
        logger.exception("Erro na migração de usuários")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
