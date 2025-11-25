@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   CORRIGINDO ERRO DE BACKUP MYSQL
echo ========================================
echo.
echo Este script vai configurar o MySQL para permitir
echo a restauracao de backups sem erro.
echo.
echo Voce precisara fornecer a senha do usuario ROOT do MySQL.
echo.
pause

echo.
echo Aplicando correcao...
echo.

mysql -u root -p -e "SET GLOBAL log_bin_trust_function_creators=1; SELECT 'SUCESSO: Configuracao aplicada!' AS Status; SHOW VARIABLES LIKE 'log_bin_trust_function_creators';"

if %errorlevel%==0 (
    echo.
    echo ✓ Configuracao aplicada com sucesso!
    echo.
    echo Agora voce pode restaurar backups normalmente.
    echo.
    echo IMPORTANTE:
    echo   Esta configuracao e temporaria.
    echo   Sera perdida ao reiniciar o MySQL.
    echo.
) else (
    echo.
    echo ✗ Erro ao aplicar configuracao.
    echo   Verifique se voce forneceu a senha correta do root.
    echo.
)

pause
