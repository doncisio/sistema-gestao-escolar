@echo off
chcp 65001 > nul
echo ====================================
echo   SINCRONIZAÇÃO - FIM DO TRABALHO
echo ====================================
echo.

cd /d "%~dp0"

echo [1/4] Verificando arquivos modificados...
git status

echo.
set /p CONTINUAR="Deseja sincronizar estas alterações? (S/N): "

if /i "%CONTINUAR%" NEQ "S" (
    echo.
    echo Sincronização cancelada pelo usuário.
    pause
    exit /b 0
)

echo.
echo [2/4] Adicionando alterações...
git add .

echo.
set /p MENSAGEM="Digite uma descrição das alterações: "

if "%MENSAGEM%"=="" (
    set MENSAGEM=Atualização automática - %date% %time:~0,5%
)

echo.
echo [3/4] Criando commit com mensagem: "%MENSAGEM%"
git commit -m "%MENSAGEM%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] Nenhuma alteração para commitar ou commit falhou.
    pause
    exit /b 0
)

echo.
echo [4/4] Enviando para o repositório remoto...
git push origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha ao enviar alterações!
    echo Possíveis causas:
    echo  - Sem conexão com internet
    echo  - Repositório remoto ainda não configurado
    echo  - Conflitos com versão remota
    echo.
    echo Suas alterações foram salvas LOCALMENTE.
    echo Execute novamente quando tiver conexão.
    pause
    exit /b 1
)

echo.
echo ====================================
echo  SINCRONIZAÇÃO CONCLUÍDA COM SUCESSO!
echo ====================================
echo.
echo Suas alterações foram salvas na nuvem!
echo.
pause
