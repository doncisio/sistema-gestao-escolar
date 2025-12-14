@echo off
chcp 65001 >nul
echo ================================================================
echo EXPORTAR DADOS DO BANCO DE QUESTÕES
echo ================================================================
echo.
echo Este script irá gerar um arquivo SQL com todos os dados de:
echo   - Textos Base
echo   - Questões
echo   - Alternativas
echo   - Avaliações (se existirem)
echo.
echo Pressione qualquer tecla para continuar ou CTRL+C para cancelar
pause >nul

python "c:\gestao\exportar_dados_questoes.py"

echo.
echo ================================================================
echo Exportação concluída!
echo.
echo O arquivo SQL foi gerado em: c:\gestao\sql\
echo.
echo PRÓXIMOS PASSOS:
echo 1. Copie o arquivo .sql gerado
echo 2. Transfira para o outro PC
echo 3. Execute o SQL no banco de dados de destino
echo.
echo Consulte README_SINCRONIZACAO.md para mais detalhes
echo ================================================================
echo.
pause
