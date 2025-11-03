@echo off
chcp 65001 > nul
echo ====================================
echo  SINCRONIZAÇÃO - INÍCIO DO TRABALHO
echo ====================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando atualizações remotas...
git fetch origin main 2>nul

echo.
echo [2/3] Puxando alterações do repositório...
git pull origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha ao puxar alterações!
    echo Possíveis causas:
    echo  - Repositório remoto ainda não configurado
    echo  - Sem conexão com internet
    echo  - Conflitos que precisam ser resolvidos
    echo.
    echo Você pode continuar trabalhando offline.
    pause
    exit /b 1
)

echo.
echo [3/3] Verificando status do repositório...
git status

echo.
echo ====================================
echo  SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!
echo ====================================
echo.
echo Você está pronto para trabalhar!
echo.
pause
