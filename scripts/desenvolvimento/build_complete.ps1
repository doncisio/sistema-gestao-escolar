# Script PowerShell para Build Completo
# Cria executáveis e instalador do Sistema de Gestão Escolar

Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "     BUILD COMPLETO - SISTEMA DE GESTÃO ESCOLAR" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Python não encontrado!" -ForegroundColor Red
    Write-Host "Instale Python 3.8+ e tente novamente." -ForegroundColor Red
    pause
    exit 1
}
Write-Host "OK: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Verificar PyInstaller
Write-Host "Verificando PyInstaller..." -ForegroundColor Yellow
$pyinstallerCheck = pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller não encontrado. Instalando..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Falha ao instalar PyInstaller!" -ForegroundColor Red
        pause
        exit 1
    }
}
Write-Host "OK: PyInstaller instalado" -ForegroundColor Green
Write-Host ""

# Verificar Inno Setup
Write-Host "Verificando Inno Setup..." -ForegroundColor Yellow
$innoSetupPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    Write-Host "AVISO: Inno Setup não encontrado!" -ForegroundColor Yellow
    Write-Host "Baixe em: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    Write-Host "Continuando apenas com executáveis..." -ForegroundColor Yellow
    $innoSetupInstalled = $false
} else {
    Write-Host "OK: Inno Setup encontrado" -ForegroundColor Green
    $innoSetupInstalled = $true
}
Write-Host ""

# Construir executáveis
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "ETAPA 1: Construindo Executáveis" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

python build_exe.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha ao construir executáveis!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "Executáveis criados com sucesso!" -ForegroundColor Green
Write-Host ""

# Verificar se executáveis foram criados
if (-not (Test-Path "dist\GestaoEscolar.exe")) {
    Write-Host "ERRO: GestaoEscolar.exe não foi criado!" -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path "dist\setup_wizard.exe")) {
    Write-Host "ERRO: setup_wizard.exe não foi criado!" -ForegroundColor Red
    pause
    exit 1
}

# Testar executável principal (opcional)
Write-Host "Deseja testar o executável agora? (S/N)" -ForegroundColor Yellow
$teste = Read-Host
if ($teste -eq "S" -or $teste -eq "s") {
    Write-Host "Executando GestaoEscolar.exe..." -ForegroundColor Yellow
    Start-Process "dist\GestaoEscolar.exe"
    Write-Host "Feche a aplicação para continuar..." -ForegroundColor Yellow
    pause
}

# Construir instalador se Inno Setup estiver instalado
if ($innoSetupInstalled) {
    Write-Host ""
    Write-Host "=============================================================================" -ForegroundColor Cyan
    Write-Host "ETAPA 2: Construindo Instalador" -ForegroundColor Cyan
    Write-Host "=============================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    & $innoSetupPath "GestaoEscolar.iss"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Falha ao construir instalador!" -ForegroundColor Red
        pause
        exit 1
    }
    
    Write-Host ""
    Write-Host "Instalador criado com sucesso!" -ForegroundColor Green
    Write-Host ""
    
    # Verificar se instalador foi criado
    $installerPath = Get-ChildItem "installer_output\*.exe" | Select-Object -First 1
    if ($installerPath) {
        Write-Host "=============================================================================" -ForegroundColor Green
        Write-Host "BUILD COMPLETO COM SUCESSO!" -ForegroundColor Green
        Write-Host "=============================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Arquivos criados:" -ForegroundColor Cyan
        Write-Host "  Executáveis:" -ForegroundColor Yellow
        Write-Host "    - dist\GestaoEscolar.exe" -ForegroundColor White
        Write-Host "    - dist\setup_wizard.exe" -ForegroundColor White
        Write-Host ""
        Write-Host "  Instalador:" -ForegroundColor Yellow
        Write-Host "    - $($installerPath.FullName)" -ForegroundColor White
        Write-Host ""
        Write-Host "Próximos passos:" -ForegroundColor Cyan
        Write-Host "  1. Teste o instalador em uma máquina limpa" -ForegroundColor White
        Write-Host "  2. Distribua o arquivo .exe do instalador" -ForegroundColor White
        Write-Host "  3. O assistente de configuração será executado automaticamente" -ForegroundColor White
        Write-Host "=============================================================================" -ForegroundColor Green
    }
} else {
    Write-Host "=============================================================================" -ForegroundColor Yellow
    Write-Host "BUILD PARCIAL CONCLUÍDO" -ForegroundColor Yellow
    Write-Host "=============================================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Executáveis criados em dist\" -ForegroundColor White
    Write-Host "Instale o Inno Setup para criar o instalador:" -ForegroundColor Yellow
    Write-Host "  https://jrsoftware.org/isdl.php" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Depois execute: & '$innoSetupPath' GestaoEscolar.iss" -ForegroundColor White
    Write-Host "=============================================================================" -ForegroundColor Yellow
}

Write-Host ""
pause
