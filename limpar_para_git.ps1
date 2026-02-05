# =============================================================================
# Script de Limpeza Automatizada para Publicacao no Git
# =============================================================================
# Este script remove arquivos sensiveis e temporarios antes de publicar
# Executar: .\limpar_para_git.ps1
# =============================================================================

Write-Host "[LIMPEZA] Iniciando limpeza do projeto para publicacao no Git..." -ForegroundColor Cyan
Write-Host ""

# Contador de arquivos removidos
$removidos = 0

# =============================================================================
# 1. CREDENCIAIS E CONFIGURACOES SENSIVEIS
# =============================================================================
Write-Host "[CREDENCIAIS] Removendo arquivos com credenciais..." -ForegroundColor Yellow

$credenciais = @(
    "credentials.json",
    "deepseek.json",
    "local_config.json",
    "feature_flags.json",
    "token.pickle"
)

foreach ($arquivo in $credenciais) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "  [OK] Removido: $arquivo" -ForegroundColor Green
        $removidos++
    }
}

# =============================================================================
# 2. ARQUIVOS TEMPORARIOS
# =============================================================================
Write-Host ""
Write-Host "[TEMP] Removendo arquivos temporarios..." -ForegroundColor Yellow

$temporarios = @(
    "temp_admin_check.txt",
    "ata_8ano_geduc.txt",
    "ata_8ano_real.txt",
    "sync_for_other_pc.bat.local.backup",
    "arquivos_antes_limpeza.txt"
)

foreach ($arquivo in $temporarios) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "  [OK] Removido: $arquivo" -ForegroundColor Green
        $removidos++
    }
}

# Padrões com wildcard
$padroes = @(
    "temp_*.txt",
    "ata_*.txt",
    "sync_*.bat"
)

foreach ($padrao in $padroes) {
    Get-ChildItem -Path . -Filter $padrao -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "  [OK] Removido: $($_.Name)" -ForegroundColor Green
        $removidos++
    }
}

# =============================================================================
# 3. DOCUMENTACAO TECNICA INTERNA
# =============================================================================
Write-Host ""
Write-Host "[DOCS] Removendo documentacao tecnica interna..." -ForegroundColor Yellow

$docs_remover = @(
    "docs\todos_codigos_sistema.txt",
    "docs\lista_arquivos_codigo.txt",
    "docs\lista_arquivos_temp.txt",
    "docs\pytest_full_output.txt",
    "docs\ANALISE_main_py.md.bak",
    "docs\pr_body.txt"
)

foreach ($arquivo in $docs_remover) {
    if (Test-Path $arquivo) {
        Remove-Item $arquivo -Force
        Write-Host "  [OK] Removido: $arquivo" -ForegroundColor Green
        $removidos++
    }
}

# =============================================================================
# 4. CONFIGURACOES DE RELATORIOS TEMPORARIOS
# =============================================================================
Write-Host ""
Write-Host "[CONFIG] Removendo relatorios temporarios de config..." -ForegroundColor Yellow

Get-ChildItem -Path "config" -Filter "relatorio_*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  [OK] Removido: config\$($_.Name)" -ForegroundColor Green
    $removidos++
}

Get-ChildItem -Path "config" -Filter "revisao_*.csv" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  [OK] Removido: config\$($_.Name)" -ForegroundColor Green
    $removidos++
}

Get-ChildItem -Path "config" -Filter "casos_*.csv" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force
    Write-Host "  [OK] Removido: config\$($_.Name)" -ForegroundColor Green
    $removidos++
}

# =============================================================================
# 5. VERIFICACAO DE SEGURANCA
# =============================================================================
Write-Host ""
Write-Host "[SEGURANCA] Verificando vazamento de credenciais no codigo..." -ForegroundColor Yellow

$vazamentos = @()

# Buscar por possiveis chaves de API
$busca_api = git grep -i "sk-[0-9a-f]" 2>$null
if ($busca_api) {
    $vazamentos += "[ALERTA] Possivel API key encontrada (sk-...)"
}

# Buscar por client_secret
$busca_secret = git grep -i "GOCSPX-" 2>$null
if ($busca_secret) {
    $vazamentos += "[ALERTA] Possivel Google client_secret encontrada (GOCSPX-...)"
}

if ($vazamentos.Count -eq 0) {
    Write-Host "  [OK] Nenhum vazamento de credencial detectado" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[ATENCAO] Possiveis vazamentos detectados:" -ForegroundColor Red
    foreach ($vazamento in $vazamentos) {
        Write-Host "  $vazamento" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Execute manualmente: git grep -i 'sk-' | git grep -i 'GOCSPX-'" -ForegroundColor Yellow
}

# =============================================================================
# 6. RESUMO FINAL
# =============================================================================
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "[SUCESSO] Limpeza concluida!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[ESTATISTICAS]" -ForegroundColor Cyan
Write-Host "  - Arquivos removidos: $removidos" -ForegroundColor White
Write-Host ""

# =============================================================================
# 7. PROXIMOS PASSOS
# =============================================================================
Write-Host "[PROXIMOS PASSOS]" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Revisar mencoes a IA na documentacao (ver LIMPEZA_GIT.md)" -ForegroundColor White
Write-Host "2. Executar: git status" -ForegroundColor Yellow
Write-Host "3. Executar: git add ." -ForegroundColor Yellow
Write-Host "4. Revisar com: git status" -ForegroundColor Yellow
Write-Host "5. Commit: git commit -m 'Preparacao para publicacao'" -ForegroundColor Yellow
Write-Host ""

# Perguntar se quer ver o status do Git
Write-Host "Deseja visualizar 'git status' agora? (S/N): " -NoNewline -ForegroundColor Cyan
$resposta = Read-Host

if ($resposta -eq "S" -or $resposta -eq "s") {
    Write-Host ""
    git status
}

Write-Host ""
Write-Host "[PRONTO] Revise o checklist em LIMPEZA_GIT.md antes de publicar." -ForegroundColor Green
