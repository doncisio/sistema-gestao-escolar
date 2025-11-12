@echo off
echo ============================================================================
echo   APLICADOR DE OTIMIZACOES - HISTORICO ESCOLAR
echo   Sistema de Gestao Escolar - Melhorias de Performance
echo ============================================================================
echo.

echo Escolha o metodo de execucao:
echo.
echo 1. Executar via Python (requer .env configurado)
echo 2. Executar via MySQL diretamente (requer credenciais)
echo 3. Gerar apenas o script SQL para execucao manual
echo 4. Sair
echo.

set /p opcao="Digite sua opcao (1-4): "

if "%opcao%"=="1" goto python_execution
if "%opcao%"=="2" goto mysql_execution  
if "%opcao%"=="3" goto sql_generation
if "%opcao%"=="4" goto exit

echo Opcao invalida!
pause
goto :eof

:python_execution
echo.
echo ===== EXECUCAO VIA PYTHON =====
echo.
echo Verificando arquivo .env...

if not exist ".env" (
    echo ERRO: Arquivo .env nao encontrado!
    echo.
    echo Criando arquivo .env baseado no .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANTE: Edite o arquivo .env com suas credenciais antes de continuar.
    echo.
    echo Exemplo de configuracao no .env:
    echo DB_HOST=localhost
    echo DB_USER=seu_usuario
    echo DB_PASSWORD=sua_senha  
    echo DB_NAME=seu_banco
    echo.
    pause
    notepad .env
    echo.
    echo Apos configurar o .env, pressione qualquer tecla para continuar...
    pause
)

echo Executando script Python...
"C:/Users/donci/AppData/Local/Programs/Python/Python312/python.exe" aplicar_otimizacoes_historico.py

if %ERRORLEVEL%==0 (
    echo.
    echo ✓ Otimizacoes aplicadas com sucesso via Python!
) else (
    echo.
    echo ✗ Erro na execucao via Python. Tente o metodo MySQL direto.
)

pause
goto :eof

:mysql_execution
echo.
echo ===== EXECUCAO VIA MYSQL =====
echo.
echo Insira suas credenciais do MySQL:
echo.

set /p mysql_host="Host do MySQL (padrao: localhost): "
if "%mysql_host%"=="" set mysql_host=localhost

set /p mysql_user="Usuario do MySQL: "
set /p mysql_database="Nome do banco de dados: "

echo.
echo Executando script SQL no MySQL...
echo IMPORTANTE: Voce precisara digitar a senha do MySQL quando solicitado.
echo.

mysql -h %mysql_host% -u %mysql_user% -p %mysql_database% < otimizacoes_historico_escolar.sql

if %ERRORLEVEL%==0 (
    echo.
    echo ✓ Otimizacoes aplicadas com sucesso via MySQL!
) else (
    echo.
    echo ✗ Erro na execucao via MySQL. Verifique as credenciais.
)

pause
goto :eof

:sql_generation
echo.
echo ===== GERACAO DE SCRIPT SQL =====
echo.
echo O script SQL ja esta disponivel em: otimizacoes_historico_escolar.sql
echo.
echo Para executar manualmente:
echo.
echo 1. Abra seu cliente MySQL (MySQL Workbench, phpMyAdmin, etc.)
echo 2. Conecte ao seu banco de dados
echo 3. Execute o arquivo: otimizacoes_historico_escolar.sql
echo.
echo O arquivo contem:
echo - Verificacao de estrutura do banco
echo - Criacao de indices especificos para historico escolar
echo - Indices complementares (FULLTEXT, etc.)
echo - Atualizacao de estatisticas das tabelas
echo - Relatorio final dos indices criados
echo.

echo Abrindo o arquivo SQL para visualizacao...
notepad otimizacoes_historico_escolar.sql

pause
goto :eof

:exit
echo.
echo Operacao cancelada pelo usuario.
echo.
pause
goto :eof