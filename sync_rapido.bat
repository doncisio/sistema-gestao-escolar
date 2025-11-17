@echo off
chcp 65001 > nul
echo ====================================
echo     SINCRONIZAÇÃO RÁPIDA
echo ====================================
echo.

cd /d "%~dp0"

:: Detectar branch atual
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%b"
if "%BRANCH%"=="" (
    echo [ERRO] Este diretório nao parece um repositório Git.
    timeout /t 5
    exit /b 1
)

echo Branch atual: %BRANCH%

:: Buscar atualizações do remoto
echo [1/4] Buscando atualizações do remoto...
git fetch origin
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao buscar do remoto.
    timeout /t 5
    exit /b 1
)

:: Verificar se estamos atrás do remoto
set BEHIND=0
set AHEAD=0
for /f "tokens=1,2" %%x in ('git rev-list --left-right --count origin/%BRANCH%...%BRANCH% 2^>nul') do (
    set BEHIND=%%x
    set AHEAD=%%y
)

echo Local está %AHEAD% commits à frente, %BEHIND% commits atrás de origin/%BRANCH%.

if not "%BEHIND%"=="0" (
    echo [2/4] Atualizando (rebase) a partir de origin/%BRANCH%...
    git pull --rebase origin %BRANCH%
    if %ERRORLEVEL% NEQ 0 (
        echo [ERRO] Falha ao rebasing. Resolva conflitos manualmente e tente novamente.
        timeout /t 5
        exit /b 1
    )
) else (
    echo [2/4] Branch local já está atualizado com origin/%BRANCH%.
)

:: Adicionar e commitar somente se houver alterações
echo.
echo [3/4] Salvando alterações locais (se houver)...
git add .
git diff --cached --quiet
if %ERRORLEVEL% NEQ 0 (
    git commit -m "Auto-sync: %date% %time:~0,5%"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERRO] Falha ao commitar alterações.
        timeout /t 5
        exit /b 1
    )
) else (
    echo Nada para commitar.
)

:: Enviar com comportamento seguro
echo.
echo [4/4] Enviando para remoto (%BRANCH%)...
git push origin %BRANCH%
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ [OK] Sincronizado com sucesso!
) else (
    echo.
    echo ❌ [ERRO] Falha ao enviar!
    echo Possiveis causas: push rejeitado (non-fast-forward) ou proteção do branch remoto.
    echo Se voce deseja forcar o push (sobrescrever origin/%BRANCH%), execute manualmente:
    echo   git push origin %BRANCH% --force-with-lease
)

timeout /t 5
