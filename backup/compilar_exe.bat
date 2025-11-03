@echo off
echo ===============================================
echo Compilador do Sistema de Gerenciamento Escolar
echo ===============================================
echo.

echo [1/6] Verificando dependências...
echo ---------------------------------------------

echo Verificando se o Python está instalado...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado. Por favor, instale o Python 3.6 ou superior.
    pause
    exit /b 1
) else (
    python --version
)

echo Verificando se o pip está disponível...
pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] pip não encontrado. Verifique sua instalação do Python.
    pause
    exit /b 1
)

echo.
echo [2/6] Verificando diretorios de destino...
echo ---------------------------------------------

echo Verificando acesso ao drive D:...
if not exist D:\ (
    echo [ERRO] O drive D: não está disponível. Por favor, verifique se está conectado.
    pause
    exit /b 1
)

echo Verificando permissões de escrita em D:...
echo Teste > D:\temp_test.txt 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Sem permissão para escrever no drive D:. Execute como administrador.
    pause
    exit /b 1
) else (
    del D:\temp_test.txt
    echo Permissões de escrita no drive D: verificadas.
)

echo.
echo [3/6] Verificando e instalando pacotes necessários...
echo ---------------------------------------------

echo Verificando se o PyInstaller está instalado...
pip show pyinstaller > nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller não encontrado. Instalando...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar PyInstaller.
        pause
        exit /b 1
    )
    echo PyInstaller instalado com sucesso!
) else (
    echo PyInstaller já está instalado.
)

echo Verificando pacotes necessários...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [AVISO] Alguns pacotes podem não ter sido instalados corretamente.
) else (
    echo Todos os pacotes foram instalados com sucesso.
)

echo.
echo [4/6] Verificando estrutura de arquivos do projeto...
echo ---------------------------------------------

if not exist main.py (
    echo [ERRO] Arquivo principal 'main.py' não encontrado.
    pause
    exit /b 1
)

echo Diretórios de saída configurados:
echo - Executável será criado em D:\dist
echo - Arquivos temporários em D:\build
echo - Arquivo de especificação em D:\Sistema_Escolar.spec

echo.
echo [5/6] Iniciando a compilação do executável...
echo ---------------------------------------------
python setup.py

echo.
echo [6/6] Verificando resultados...
echo ---------------------------------------------
if %errorlevel% == 0 (
    if exist D:\dist\Sistema_Escolar.exe (
        echo ===============================================
        echo Compilação concluída com sucesso!
        echo O executável está disponível em: D:\dist\Sistema_Escolar.exe
        echo Tamanho do arquivo: 
        for %%F in (D:\dist\Sistema_Escolar.exe) do @echo %%~zF bytes
        echo ===============================================
    ) else (
        echo [AVISO] Compilação concluída, mas o executável não foi encontrado na pasta 'D:\dist'.
    )
) else (
    echo [ERRO] Ocorreu um erro durante a compilação.
)

echo.
echo Pressione qualquer tecla para sair...
pause 