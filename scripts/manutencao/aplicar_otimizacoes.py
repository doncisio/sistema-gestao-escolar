#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar as otimizações específicas de histórico escolar
Executa os índices SQL documentados em OTIMIZACOES_BD_HISTORICO.md
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from typing import Any, cast
from src.core.config_logs import get_logger

logger = get_logger(__name__)

# Carregar variáveis do .env
load_dotenv()

def conectar_banco():
    """Conecta ao banco de dados usando as configurações do .env"""
    try:
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'), 
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'auth_plugin': 'mysql_native_password'
        }
        
        logger.info("🔗 Conectando ao banco: %s -> %s", config['host'], config['database'])
        
        conn = mysql.connector.connect(**config)
        
        if conn.is_connected():
            info = conn.get_server_info()
            logger.info("✅ Conectado ao MySQL Server versão %s", info)
            return conn
        else:
            logger.error("❌ Falha na conexão")
            return None
            
    except Error as e:
        logger.exception("❌ Erro ao conectar ao banco: %s", e)
        logger.error("\n🔍 Verifique se:")
        logger.error("   1. O MySQL está rodando")
        logger.error("   2. As credenciais no .env estão corretas")
        logger.error("   3. O banco de dados existe")
        return None

def verificar_indice_existe(cursor, tabela, nome_indice):
    """Verifica se um índice já existe na tabela"""
    try:
        query = """
        SELECT COUNT(*) as existe
        FROM information_schema.STATISTICS 
        WHERE table_schema = DATABASE()
        AND table_name = %s 
        AND index_name = %s
        """
        cursor.execute(query, (tabela, nome_indice))
        resultado = cursor.fetchone()
        return resultado[0] > 0
    except Error as e:
        logger.exception("⚠️  Erro ao verificar índice %s: %s", nome_indice, e)
        return False

def executar_sql_seguro(cursor, sql, descricao):
    """Executa SQL com tratamento de erro"""
    try:
        logger.info("🔄 %s...", descricao)
        cursor.execute(sql)
        logger.info("✅ %s - SUCESSO", descricao)
        return True
    except Error as e:
        logger.exception("❌ %s - ERRO: %s", descricao, e)
        return False

def aplicar_otimizacoes_historico():
    """Aplica as otimizações específicas para histórico escolar"""
    
    logger.info("%s", "=" * 80)
    logger.info("🚀 APLICANDO OTIMIZAÇÕES DE HISTÓRICO ESCOLAR")
    logger.info("%s", "=" * 80)
    
    # Conectar ao banco
    conn = conectar_banco()
    if not conn:
        return False
    
    cursor = cast(Any, conn).cursor()
    
    try:
        # ==================================================================
        # VERIFICAR TABELAS NECESSÁRIAS
        # ==================================================================
        logger.info("\n📋 Verificando estrutura do banco...")
        
        tabelas_necessarias = ['historico_escolar', 'alunos', 'disciplinas', 'serie', 'escolas', 'anosletivos']
        
        for tabela in tabelas_necessarias:
            cursor.execute("SHOW TABLES LIKE %s", (tabela,))
            if not cursor.fetchone():
                logger.warning("⚠️  Tabela '%s' não encontrada!", tabela)
            else:
                logger.info("✅ Tabela '%s' encontrada", tabela)
        
        # ==================================================================
        # ÍNDICES ESPECÍFICOS PARA HISTÓRICO ESCOLAR
        # ==================================================================
        logger.info("\n🔧 Aplicando índices específicos para histórico escolar...")
        
        indices_historico = [
            {
                'tabela': 'historico_escolar',
                'nome': 'idx_aluno_historico',
                'sql': 'CREATE INDEX idx_aluno_historico ON historico_escolar (aluno_id, ano_letivo_id DESC, serie_id)',
                'descricao': 'Índice principal para consultas de histórico por aluno'
            },
            {
                'tabela': 'historico_escolar', 
                'nome': 'idx_historico_filtros',
                'sql': 'CREATE INDEX idx_historico_filtros ON historico_escolar (aluno_id, disciplina_id, serie_id, escola_id, ano_letivo_id)',
                'descricao': 'Índice para aplicação de filtros no histórico'
            },
            {
                'tabela': 'historico_escolar',
                'nome': 'idx_escola_serie', 
                'sql': 'CREATE INDEX idx_escola_serie ON historico_escolar (escola_id, serie_id, ano_letivo_id)',
                'descricao': 'Índice para consultas por escola e série'
            },
            {
                'tabela': 'historico_escolar',
                'nome': 'idx_disciplinas_disponiveis',
                'sql': 'CREATE INDEX idx_disciplinas_disponiveis ON historico_escolar (escola_id, serie_id, ano_letivo_id, disciplina_id)',
                'descricao': 'Índice para listar disciplinas disponíveis'
            }
        ]
        
        indices_criados = 0
        indices_existentes = 0
        
        for indice in indices_historico:
            if verificar_indice_existe(cursor, indice['tabela'], indice['nome']):
                logger.info("⏭️  Índice %s já existe - PULANDO", indice['nome'])
                indices_existentes += 1
            else:
                if executar_sql_seguro(cursor, indice['sql'], indice['descricao']):
                    indices_criados += 1
        
        # ==================================================================
        # ÍNDICES COMPLEMENTARES (se não existirem)
        # ==================================================================
        logger.info("\n🔧 Verificando índices complementares...")
        
        indices_complementares = [
            {
                'tabela': 'alunos',
                'nome': 'ft_nome',
                'sql': 'CREATE FULLTEXT INDEX ft_nome ON alunos (nome)',
                'descricao': 'Índice FULLTEXT para busca de alunos por nome'
            },
            {
                'tabela': 'disciplinas',
                'nome': 'idx_disciplina_nome',
                'sql': 'CREATE INDEX idx_disciplina_nome ON disciplinas (nome)',
                'descricao': 'Índice para disciplinas por nome'
            },
            {
                'tabela': 'serie',
                'nome': 'idx_serie_nome',
                'sql': 'CREATE INDEX idx_serie_nome ON serie (nome)',
                'descricao': 'Índice para séries por nome'
            },
            {
                'tabela': 'escolas',
                'nome': 'idx_escola_nome',
                'sql': 'CREATE INDEX idx_escola_nome ON escolas (nome)',
                'descricao': 'Índice para escolas por nome'
            },
            {
                'tabela': 'anosletivos',
                'nome': 'idx_ano_letivo',
                'sql': 'CREATE INDEX idx_ano_letivo ON anosletivos (ano_letivo DESC)',
                'descricao': 'Índice para anos letivos ordenados'
            }
        ]
        
        for indice in indices_complementares:
            if verificar_indice_existe(cursor, indice['tabela'], indice['nome']):
                logger.info("⏭️  Índice %s já existe - PULANDO", indice['nome'])
                indices_existentes += 1
            else:
                if executar_sql_seguro(cursor, indice['sql'], indice['descricao']):
                    indices_criados += 1
        
        # ==================================================================
        # ANALISAR TABELAS PARA ATUALIZAR ESTATÍSTICAS
        # ==================================================================
        logger.info("\n📊 Atualizando estatísticas das tabelas...")
        
        tabelas_analisar = ['historico_escolar', 'alunos', 'disciplinas', 'serie', 'escolas', 'anosletivos']
        
        for tabela in tabelas_analisar:
            executar_sql_seguro(cursor, f"ANALYZE TABLE {tabela}", f"Análise da tabela {tabela}")
        
        # Commit das alterações
        conn.commit()
        
        # ==================================================================
        # RELATÓRIO FINAL
        # ==================================================================
        logger.info("\n%s", "=" * 80)
        logger.info("📊 RELATÓRIO DE OTIMIZAÇÕES APLICADAS")
        logger.info("%s", "=" * 80)
        logger.info("✅ Índices criados: %d", indices_criados)
        logger.info("⏭️  Índices que já existiam: %d", indices_existentes)
        logger.info("📊 Tabelas analisadas: %d", len(tabelas_analisar))
        
        if indices_criados > 0:
            logger.info("\n🎉 %d novos índices foram criados com sucesso!", indices_criados)
            logger.info("🚀 A interface de histórico escolar deve estar mais rápida agora!")
        else:
            logger.info("\n✨ Todos os índices já estavam criados!")
            logger.info("👍 Sistema já otimizado para histórico escolar!")
        
        return True
        
    except Error as e:
        logger.exception("\n❌ Erro durante a aplicação das otimizações: %s", e)
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()
        logger.info("\n🔌 Conexão com o banco fechada")

def verificar_configuracao():
    """Verifica se a configuração está correta antes de executar"""
    
    logger.info("🔍 Verificando configuração...")
    
    # Verificar se arquivo .env existe
    if not os.path.exists('.env'):
        logger.error("⚠️  Arquivo .env não encontrado!")
        logger.error("📝 Você precisa criar o arquivo .env com as configurações do banco.")
        logger.error("💡 Use o arquivo .env.example como modelo:")
        logger.error("   cp .env.example .env")
        logger.error("   # Edite o .env com suas configurações")
        return False
    
    # Verificar se variáveis essenciais existem
    vars_necessarias = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    vars_faltando = []
    
    for var in vars_necessarias:
        if not os.getenv(var):
            vars_faltando.append(var)
    
    if vars_faltando:
        logger.error("❌ Variáveis faltando no .env: %s", ', '.join(vars_faltando))
        return False
    
    logger.info("✅ Configuração do .env está correta")
    return True

def main():
    """Função principal"""
    
    logger.info("🔧 APLICADOR DE OTIMIZAÇÕES - HISTÓRICO ESCOLAR")
    logger.info("%s", "=" * 60)
    
    # Verificar configuração
    if not verificar_configuracao():
        logger.error("\n❌ Configuração inválida. Operação cancelada.")
        return 1
    
    # Aplicar otimizações
    if aplicar_otimizacoes_historico():
        logger.info("\n🎉 OTIMIZAÇÕES APLICADAS COM SUCESSO!")
        logger.info("🚀 A interface de histórico escolar deve estar mais rápida!")
        return 0
    else:
        logger.error("\n❌ FALHA NA APLICAÇÃO DAS OTIMIZAÇÕES")
        return 1

if __name__ == "__main__":
    sys.exit(main())