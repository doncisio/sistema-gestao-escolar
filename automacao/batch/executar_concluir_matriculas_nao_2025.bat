@echo off
echo ========================================
echo CONCLUIR MATRICULAS DE ANOS ANTERIORES
echo ========================================
echo.
echo Este script altera o status das matriculas de anos anteriores para 'Concluido'
echo (exceto alunos evadidos ou transferidos)
echo.

cd /d "%~dp0"
python concluir_matriculas_nao_2025.py %*

echo.
pause
