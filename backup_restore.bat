@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ============================================
REM Script de Backup e Restauração - MySQL
REM Sistema de Gestão Escolar
REM ============================================

set MYSQL_USER=doncisio
set MYSQL_DB=redeescola
set BACKUP_PATH="G:\Meu Drive\NADIR_2025\Backup\backup_redeescola.sql"
set BACKUP_LOCAL=".\backup_redeescola.sql"

echo.
echo ========================================
echo   BACKUP E RESTAURACAO DO BANCO
echo ========================================
echo.
echo Escolha uma opcao:
echo.
echo   1 - Fazer backup do banco de dados
echo   2 - Restaurar do Google Drive
echo   3 - Restaurar do arquivo local
echo   4 - Sair
echo.
set /p escolha="Digite o numero da opcao: "

if "%escolha%"=="1" goto FAZER_BACKUP
if "%escolha%"=="2" goto RESTAURAR_DRIVE
if "%escolha%"=="3" goto RESTAURAR_LOCAL
if "%escolha%"=="4" goto FIM
goto OPCAO_INVALIDA

:FAZER_BACKUP
echo.
echo Fazendo backup do banco de dados...
echo.
mysqldump -u %MYSQL_USER% -p --single-transaction --routines --triggers --events %MYSQL_DB% > %BACKUP_PATH%
if %errorlevel%==0 (
    echo.
    echo ✓ Backup realizado com sucesso em %BACKUP_PATH%
    echo.
) else (
    echo.
    echo ✗ Erro ao realizar o backup.
    echo.
)
pause
goto FIM

:RESTAURAR_DRIVE
echo.
echo Restaurando do Google Drive: %BACKUP_PATH%
echo.
if not exist %BACKUP_PATH% (
    echo ✗ ERRO: Arquivo de backup nao encontrado no Google Drive!
    echo   Caminho: %BACKUP_PATH%
    echo.
    pause
    goto FIM
)

REM Verificar se log_bin_trust_function_creators está habilitado
echo Verificando configuracao do MySQL...
mysql -u %MYSQL_USER% -p -e "SHOW VARIABLES LIKE 'log_bin_trust_function_creators';" 2>nul | findstr "ON" >nul

if %errorlevel%==0 (
    echo ✓ Configuracao OK - Restaurando backup...
    echo.
) else (
    echo.
    echo ⚠ AVISO: A configuracao necessaria nao esta ativa!
    echo   Execute primeiro: fix_backup_rapido.bat
    echo.
    set /p continuar="Deseja tentar mesmo assim? (S/N): "
    if /i not "%continuar%"=="S" goto FIM
    echo.
)

REM Restaurar normalmente (sem tentar modificar sessão)
mysql -u %MYSQL_USER% -p %MYSQL_DB% < %BACKUP_PATH% 2>restore_error.log

if %errorlevel%==0 (
    echo.
    echo ✓ Banco de dados restaurado com sucesso!
    echo.
    if exist restore_error.log del restore_error.log
) else (
    REM Verificar tipo de erro
    findstr /C:"ERROR 1419" restore_error.log >nul
    if %errorlevel%==0 (
        echo.
        echo ✗ ERRO 1419: Privilegio SUPER necessario
        echo.
        echo SOLUCAO: Execute o comando abaixo primeiro:
        echo   fix_backup_rapido.bat
        echo.
        echo Isso vai configurar o MySQL para aceitar o backup.
        echo.
    ) else (
        findstr /C:"ERROR 1227" restore_error.log >nul
        if %errorlevel%==0 (
            echo.
            echo ✗ ERRO 1227: Permissao negada
            echo.
            echo SOLUCAO: Execute o comando abaixo primeiro:
            echo   fix_backup_rapido.bat
            echo.
        ) else (
            echo.
            echo ✗ Erro ao restaurar o banco de dados.
            echo Detalhes do erro:
            type restore_error.log
            echo.
        )
    )
)
if exist restore_error.log del restore_error.log
pause
goto FIM

:RESTAURAR_LOCAL
echo.
echo Restaurando do arquivo local: %BACKUP_LOCAL%
echo.
if not exist %BACKUP_LOCAL% (
    echo ✗ ERRO: Arquivo de backup nao encontrado localmente!
    echo   Caminho: %BACKUP_LOCAL%
    echo.
    pause
    goto FIM
)

REM Verificar se log_bin_trust_function_creators está habilitado
echo Verificando configuracao do MySQL...
mysql -u %MYSQL_USER% -p -e "SHOW VARIABLES LIKE 'log_bin_trust_function_creators';" 2>nul | findstr "ON" >nul

if %errorlevel%==0 (
    echo ✓ Configuracao OK - Restaurando backup...
    echo.
) else (
    echo.
    echo ⚠ AVISO: A configuracao necessaria nao esta ativa!
    echo   Execute primeiro: fix_backup_rapido.bat
    echo.
    set /p continuar="Deseja tentar mesmo assim? (S/N): "
    if /i not "%continuar%"=="S" goto FIM
    echo.
)

echo Restaurando...
echo.
mysql -u %MYSQL_USER% -p %MYSQL_DB% < %BACKUP_LOCAL% 2>restore_error.log

if %errorlevel%==0 (
    echo.
    echo ✓ Banco de dados restaurado com sucesso!
    echo.
    if exist restore_error.log del restore_error.log
) else (
    findstr /C:"ERROR 1419" restore_error.log >nul
    if %errorlevel%==0 (
        echo.
        echo ✗ ERRO 1419: Privilegio SUPER necessario
        echo.
        echo SOLUCAO: Execute o comando abaixo primeiro:
        echo   fix_backup_rapido.bat
        echo.
    ) else (
        findstr /C:"ERROR 1227" restore_error.log >nul
        if %errorlevel%==0 (
            echo.
            echo ✗ ERRO 1227: Permissao negada
            echo.
            echo SOLUCAO: Execute o comando abaixo primeiro:
            echo   fix_backup_rapido.bat
            echo.
        ) else (
            echo.
            echo ✗ Erro ao restaurar o banco de dados.
            echo Detalhes do erro:
            type restore_error.log
            echo.
        )
    )
)
if exist restore_error.log del restore_error.log
pause
goto FIM

:OPCAO_INVALIDA
echo.
echo ✗ Opcao invalida. Tente novamente.
echo.
pause
goto FIM

:FIM
echo.
echo Encerrando script...
endlocal
