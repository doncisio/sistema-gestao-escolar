@echo off
setlocal
set MYSQL_USER=root
set MYSQL_PASS=987412365
set MYSQL_DB=redeescola
set BACKUP_PATH="G:\Meu Drive\NADIR_2025\Backup\backup_redeescola.sql"

echo ========================================
echo    RESTAURACAO DO BANCO DE DADOS
echo ========================================
echo.
echo Restaurando o banco de dados...
echo Origem: %BACKUP_PATH%
echo.

mysql -u %MYSQL_USER% -p%MYSQL_PASS% %MYSQL_DB% < %BACKUP_PATH%

if %errorlevel%==0 (
    echo.
    echo ========================================
    echo Banco de dados restaurado com sucesso!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ERRO ao restaurar o banco de dados.
    echo ========================================
)
echo.
timeout /t 3 >nul
