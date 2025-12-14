"""
Script para exportar dados de questões e textos base para arquivo SQL
Permite sincronizar dados entre diferentes PCs/bancos de dados
"""
import sys
sys.path.insert(0, r'C:\gestao')

from src.core.conexao import conectar_bd
import config
from datetime import datetime

print("=" * 80)
print("EXPORTANDO DADOS DO BANCO DE QUESTÕES")
print("=" * 80)

conn = conectar_bd()
cursor = conn.cursor(dictionary=True)

# Nome do arquivo de saída
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
arquivo_sql = f"c:\\gestao\\sql\\dados_questoes_{timestamp}.sql"

with open(arquivo_sql, 'w', encoding='utf-8') as f:
    f.write("-- ============================================================================\n")
    f.write(f"-- EXPORTAÇÃO DE DADOS - BANCO DE QUESTÕES\n")
    f.write(f"-- Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("-- ============================================================================\n\n")
    f.write("SET NAMES utf8mb4;\n")
    f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")
    
    # ========================================================================
    # 1. CRIAR TABELAS
    # ========================================================================
    f.write("-- ============================================================================\n")
    f.write("-- 1. CRIAR TABELAS\n")
    f.write("-- ============================================================================\n\n")
    
    # Ler script de criação de textos_base
    with open(r'c:\gestao\sql\criar_tabela_textos_base.sql', 'r', encoding='utf-8') as tb:
        f.write(tb.read())
    f.write("\n\n")
    
    # ========================================================================
    # 2. EXPORTAR TEXTOS BASE
    # ========================================================================
    f.write("-- ============================================================================\n")
    f.write("-- 2. TEXTOS BASE\n")
    f.write("-- ============================================================================\n\n")
    
    cursor.execute("SELECT * FROM textos_base ORDER BY id")
    textos = cursor.fetchall()
    
    if textos:
        f.write(f"-- Total de textos base: {len(textos)}\n")
        f.write("DELETE FROM textos_base;\n")
        f.write("ALTER TABLE textos_base AUTO_INCREMENT = 1;\n\n")
        
        for texto in textos:
            campos = []
            valores = []
            
            for campo, valor in texto.items():
                if valor is not None:
                    campos.append(f"`{campo}`")
                    
                    if isinstance(valor, str):
                        # Escapar aspas e caracteres especiais
                        valor_escapado = valor.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                        valores.append(f"'{valor_escapado}'")
                    elif isinstance(valor, datetime):
                        valores.append(f"'{valor.strftime('%Y-%m-%d %H:%M:%S')}'")
                    else:
                        valores.append(str(valor))
            
            f.write(f"INSERT INTO textos_base ({', '.join(campos)}) VALUES ({', '.join(valores)});\n")
        
        f.write(f"\n-- ✓ {len(textos)} textos base exportados\n\n")
    else:
        f.write("-- Nenhum texto base encontrado\n\n")
    
    # ========================================================================
    # 3. EXPORTAR QUESTÕES
    # ========================================================================
    f.write("-- ============================================================================\n")
    f.write("-- 3. QUESTÕES\n")
    f.write("-- ============================================================================\n\n")
    
    cursor.execute("SELECT * FROM questoes ORDER BY id")
    questoes = cursor.fetchall()
    
    if questoes:
        f.write(f"-- Total de questões: {len(questoes)}\n")
        f.write("-- ATENÇÃO: Não apaga questões existentes, apenas insere novas\n")
        f.write("-- Se quiser substituir, execute: DELETE FROM questoes; antes\n\n")
        
        for questao in questoes:
            campos = []
            valores = []
            
            for campo, valor in questao.items():
                if valor is not None and campo != 'id':  # Não incluir ID para evitar conflitos
                    campos.append(f"`{campo}`")
                    
                    if isinstance(valor, str):
                        valor_escapado = valor.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                        valores.append(f"'{valor_escapado}'")
                    elif isinstance(valor, datetime):
                        valores.append(f"'{valor.strftime('%Y-%m-%d %H:%M:%S')}'")
                    else:
                        valores.append(str(valor))
            
            f.write(f"-- Questão original ID: {questao['id']}\n")
            f.write(f"INSERT INTO questoes ({', '.join(campos)}) VALUES ({', '.join(valores)});\n")
            f.write(f"SET @questao_{questao['id']}_id = LAST_INSERT_ID();\n\n")
            
            # Exportar alternativas desta questão
            cursor.execute("SELECT * FROM questoes_alternativas WHERE questao_id = %s ORDER BY letra", (questao['id'],))
            alternativas = cursor.fetchall()
            
            if alternativas:
                for alt in alternativas:
                    campos_alt = []
                    valores_alt = []
                    
                    for campo, valor in alt.items():
                        if valor is not None and campo not in ['id', 'questao_id']:
                            campos_alt.append(f"`{campo}`")
                            
                            if isinstance(valor, str):
                                valor_escapado = valor.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                                valores_alt.append(f"'{valor_escapado}'")
                            elif isinstance(valor, (bool, int)) and campo == 'correta':
                                valores_alt.append('1' if valor else '0')
                            elif isinstance(valor, datetime):
                                valores_alt.append(f"'{valor.strftime('%Y-%m-%d %H:%M:%S')}'")
                            else:
                                valores_alt.append(str(valor))
                    
                    f.write(f"INSERT INTO questoes_alternativas (questao_id, {', '.join(campos_alt)}) ")
                    f.write(f"VALUES (@questao_{questao['id']}_id, {', '.join(valores_alt)});\n")
                
                f.write("\n")
        
        f.write(f"\n-- ✓ {len(questoes)} questões exportadas com suas alternativas\n\n")
    else:
        f.write("-- Nenhuma questão encontrada\n\n")
    
    # ========================================================================
    # 4. EXPORTAR AVALIAÇÕES (se existirem)
    # ========================================================================
    f.write("-- ============================================================================\n")
    f.write("-- 4. AVALIAÇÕES\n")
    f.write("-- ============================================================================\n\n")
    
    try:
        cursor.execute("SELECT * FROM avaliacoes ORDER BY id")
        avaliacoes = cursor.fetchall()
        
        if avaliacoes:
            f.write(f"-- Total de avaliações: {len(avaliacoes)}\n\n")
            
            for aval in avaliacoes:
                campos = []
                valores = []
                
                for campo, valor in aval.items():
                    if valor is not None and campo != 'id':
                        campos.append(f"`{campo}`")
                        
                        if isinstance(valor, str):
                            valor_escapado = valor.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
                            valores.append(f"'{valor_escapado}'")
                        elif isinstance(valor, datetime):
                            valores.append(f"'{valor.strftime('%Y-%m-%d %H:%M:%S')}'")
                        else:
                            valores.append(str(valor))
                
                f.write(f"-- Avaliação original ID: {aval['id']}\n")
                f.write(f"INSERT INTO avaliacoes ({', '.join(campos)}) VALUES ({', '.join(valores)});\n")
                f.write(f"SET @avaliacao_{aval['id']}_id = LAST_INSERT_ID();\n\n")
                
                # Exportar questões da avaliação
                cursor.execute("SELECT * FROM avaliacoes_questoes WHERE avaliacao_id = %s ORDER BY ordem", (aval['id'],))
                aval_questoes = cursor.fetchall()
                
                if aval_questoes:
                    for aq in aval_questoes:
                        f.write(f"INSERT INTO avaliacoes_questoes (avaliacao_id, questao_id, ordem, pontos) ")
                        f.write(f"VALUES (@avaliacao_{aval['id']}_id, {aq['questao_id']}, {aq['ordem']}, {aq.get('pontos', 1.0)});\n")
                    f.write("\n")
                
                # Exportar textos base da avaliação
                cursor.execute("SELECT * FROM avaliacoes_textos_base WHERE avaliacao_id = %s ORDER BY ordem", (aval['id'],))
                aval_textos = cursor.fetchall()
                
                if aval_textos:
                    for at in aval_textos:
                        f.write(f"INSERT INTO avaliacoes_textos_base (avaliacao_id, texto_base_id, ordem, layout) ")
                        f.write(f"VALUES (@avaliacao_{aval['id']}_id, {at['texto_base_id']}, {at['ordem']}, '{at.get('layout', 'completo')}');\n")
                    f.write("\n")
            
            f.write(f"\n-- ✓ {len(avaliacoes)} avaliações exportadas\n\n")
        else:
            f.write("-- Nenhuma avaliação encontrada\n\n")
    except Exception as e:
        f.write(f"-- Erro ao exportar avaliações: {e}\n\n")
    
    # ========================================================================
    # FINALIZAR
    # ========================================================================
    f.write("-- ============================================================================\n")
    f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
    f.write("-- ✓ EXPORTAÇÃO CONCLUÍDA\n")
    f.write("-- ============================================================================\n")

cursor.close()
conn.close()

print(f"\n✓ Arquivo SQL gerado com sucesso!")
print(f"📄 Local: {arquivo_sql}")
print("\n" + "=" * 80)
print("INSTRUÇÕES PARA IMPORTAR NO OUTRO PC:")
print("=" * 80)
print("1. Copie o arquivo SQL gerado para o outro PC")
print("2. Abra o MySQL/MariaDB ou phpMyAdmin")
print("3. Selecione o banco 'redeescola'")
print("4. Execute o script SQL completo")
print("\nOu via linha de comando:")
print(f'mysql -u root -p redeescola < "{arquivo_sql}"')
print("=" * 80)
