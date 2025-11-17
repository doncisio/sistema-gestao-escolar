@echo off
chcp 65001 > nul
echo ====================================
echo     SINCRONIZAÇÃO DO PROJETO
echo ====================================
echo.

cd /d "%~dp0"

:: Uso: sync_projeto.bat [branch]
:: Se nenhum argumento for passado, o alvo é 'main'.
set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=main"

:: Detectar branch atual
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "CURBR=%%b"
if "%CURBR%"=="" (
    echo [ERRO] Este diretório nao parece um repositório Git.
    timeout /t 5
    exit /b 1
)



































































































timeout /t 3echo FIM.)    git checkout %CURBR% 2>nul || echo Nao foi possivel retornar automaticamente para %CURBR%.    echo Retornando para branch original: %CURBR%...if not "%CURBR%"=="%TARGET%" (:: Voltar ao branch original, se necessario)    echo Se necessario force com: git push origin %TARGET% --force-with-lease    echo ❌ [ERRO] Falha ao enviar para origin/%TARGET%.    echo.) else (    echo ✅ [OK] Sincronizado com sucesso em origin/%TARGET%!    echo.if %ERRORLEVEL% EQU 0 (git push origin %TARGET%echo [6/6] Enviando para origin/%TARGET%...:: Push)    echo Nada para commitar.) else (    )        echo Alteracoes commitadas.    ) else (        exit /b 1        timeout /t 5        echo [ERRO] Falha ao commitar alteracoes.    if %ERRORLEVEL% NEQ 0 (    git commit -m "Auto-sync: %date% %time:~0,5%"if %ERRORLEVEL% NEQ 0 (git add .
ngit diff --cached --quietecho [5/6] Verificando e commitando alteracoes locais (se houver)...:: Comitar se houver algo para commitar)    )        exit /b 1        timeout /t 5        echo [ERRO] Conflito ao reaplicar stash. Resolva manualmente.    if %ERRORLEVEL% NEQ 0 (    git stash pop    echo [4/6] Reaplicando stash...if "%STASHED%"=="1" (:: Se criamos um stash antes, reaplicar)    exit /b 1    timeout /t 5    echo [ERRO] Falha no rebase. Resolva conflitos manualmente e tente novamente.if %ERRORLEVEL% NEQ 0 (git pull --rebase origin %TARGET%echo [3/6] Atualizando (rebase) a partir de origin/%TARGET%...:: Rebase do remoto)    exit /b 1    timeout /t 5    echo [ERRO] Falha ao mudar/criar branch %TARGET%.if %ERRORLEVEL% NEQ 0 (git checkout %TARGET% 2>nul || git checkout -B %TARGET% origin/%TARGET%echo [2/6] Mudando para o branch alvo: %TARGET%...:: Trocar para o branch alvo (cria a partir do remoto se necessario))    exit /b 1    timeout /t 5    echo [ERRO] Falha ao buscar do remoto.if %ERRORLEVEL% NEQ 0 (git fetch originecho [1/6] Buscando atualizacoes do remoto...:: Buscar atualizações)    echo [0/6] Sem mudancas locais a stashar.) else (    )        set "STASHED=0"        echo [AVISO] Nao foi possivel criar stash; continuando sem stash.    ) else (        echo Stash criado.        set "STASHED=1"    if %ERRORLEVEL% EQU 0 (    git stash push -u -m "auto-sync before switching to %TARGET%" >nul 2>nul    echo [0/6] Mudancas locais detectadas — aplicando stash temporario...if "%NEEDS_STASH%"=="1" (for /f "usebackq delims=" %%x in (`type "%TMPSTAT%" ^| findstr /n "."`) do set "NEEDS_STASH=1"git status --porcelain > "%TMPSTAT%" 2>nulif exist "%TMPSTAT%" del /q "%TMPSTAT%"set "TMPSTAT=%TEMP%\_gitstatus_sync.txt"set "NEEDS_STASH=0"set "STASHED=0":: Verificar mudanças locais usando git status --porcelainecho Branch alvo: %TARGET%necho Branch atual: %CURBR%