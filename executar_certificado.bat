@echo off
REM Script para gerar certificado de conclusão do aluno

echo ================================================
echo   GERADOR DE CERTIFICADO DE CONCLUSAO
echo ================================================
echo.

REM Verifica se foi passado o ID do aluno
if "%1"=="" (
    echo ERRO: ID do aluno nao foi fornecido!
    echo.
    echo Uso: executar_certificado.bat ID_ALUNO [arquivo_saida.pdf]
    echo Exemplo: executar_certificado.bat 1234
    echo Exemplo com arquivo: executar_certificado.bat 1234 "meu_certificado.pdf"
    echo.
    pause
    exit /b 1
)

set ALUNO_ID=%1
set ARQUIVO_SAIDA=%2

echo Gerando certificado para o aluno ID: %ALUNO_ID%
echo.

REM Executa o script Python
if "%ARQUIVO_SAIDA%"=="" (
    python gerar_certificado_pdf.py %ALUNO_ID%
) else (
    python gerar_certificado_pdf.py %ALUNO_ID% %ARQUIVO_SAIDA%
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================
    echo   CERTIFICADO GERADO COM SUCESSO!
    echo ================================================
) else (
    echo.
    echo ================================================
    echo   ERRO AO GERAR CERTIFICADO
    echo ================================================
)

echo.
pause
