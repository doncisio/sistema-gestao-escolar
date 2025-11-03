@echo off
chcp 65001 > nul
echo ====================================
echo     SINCRONIZAÇÃO RÁPIDA
echo ====================================
echo.

cd /d "%~dp0"

:: Puxar alterações
echo [1/3] Puxando alterações...
git pull origin main

if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao puxar alterações!
    timeout /t 5
    exit /b 1
)

:: Adicionar e commitar
echo.
echo [2/3] Salvando alterações locais...
git add .
git commit -m "Auto-sync: %date% %time:~0,5%"

:: Enviar
echo.
echo [3/3] Enviando para nuvem...
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ [OK] Sincronizado com sucesso!
) else (
    echo.
    echo ❌ [ERRO] Falha ao enviar!
)

timeout /t 5
