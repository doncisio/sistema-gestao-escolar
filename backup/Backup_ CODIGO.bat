@echo off
setlocal


REM Defina o caminho da pasta de origem
set "origem=G:\Meu Drive\NADIR_2025\Backup\Recentes"


REM Defina o caminho da pasta de destino
set "destino=C:\gestao"


REM Use o comando xcopy para copiar apenas arquivos recentes
xcopy "%destino%" "%origem%" /D /Y

echo Copia concluída!
pause