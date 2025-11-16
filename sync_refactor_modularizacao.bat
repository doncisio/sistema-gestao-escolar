@echo off
chcp 65001 > nul
echo ====================================
echo     SINCRONIZAÇÃO RÁPIDA (branch: refactor/modularizacao)
echo ====================================
echo.

cd /d "%~dp0"

:: Puxar alterações do branch alvo
set BRANCH=refactor/modularizacao
echo [1/4] Puxando alterações de %BRANCH%...
git fetch origin %BRANCH%
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao buscar o branch %BRANCH%!
    timeout /t 5
    exit /b 1
)

git checkout %BRANCH%
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao trocar para o branch %BRANCH%!
    timeout /t 5
    exit /b 1
)

git pull origin %BRANCH%
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao puxar alterações de %BRANCH%!
    timeout /t 5
    exit /b 1
)

:: Adicionar e commitar alterações locais (se houver)
echo.
echo [2/4] Salvando alterações locais (se houver)...
git add .
git commit -m "Auto-sync (%BRANCH%): %date% %time:~0,5%"
if %ERRORLEVEL% EQU 0 (
    echo [OK] Commit criado.
) else (
    echo [INFO] Sem alterações para commitar.
)

:: Enviar para o branch remoto
echo.
echo [3/4] Enviando para origin/%BRANCH%...
git push origin %BRANCH%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ [OK] Sincronizado com sucesso com %BRANCH%!
) else (
    echo.
    echo ❌ [ERRO] Falha ao enviar para origin/%BRANCH%!
)

echo.
echo [4/4] Operação concluída.
timeout /t 3
