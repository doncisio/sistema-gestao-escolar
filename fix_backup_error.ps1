# ============================================
# Script PowerShell - Corrigir Erro de Backup MySQL
# Sistema de Gestão Escolar
# ============================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  CORRECAO DE ERRO DE BACKUP MYSQL" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$mysqlUser = "root"
$mysqlDb = "redeescola"

Write-Host "Este script ira configurar o MySQL para permitir restauracao de backups." -ForegroundColor Yellow
Write-Host "Voce precisara fornecer a senha do usuario 'root' do MySQL.`n" -ForegroundColor Yellow

# Verificar se o MySQL está instalado e acessível
try {
    $testConnection = mysql --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "MySQL nao encontrado"
    }
    Write-Host "✓ MySQL detectado: $testConnection`n" -ForegroundColor Green
} catch {
    Write-Host "✗ ERRO: MySQL nao esta instalado ou nao esta no PATH do sistema." -ForegroundColor Red
    Write-Host "  Por favor, instale o MySQL ou adicione ao PATH.`n" -ForegroundColor Red
    Read-Host "Pressione Enter para sair"
    exit 1
}

# Executar o script SQL
Write-Host "Aplicando correcao..." -ForegroundColor Cyan

$sqlScript = @"
SET GLOBAL log_bin_trust_function_creators=1;
SELECT 'SUCESSO: Configuracao aplicada!' AS Status;
SHOW VARIABLES LIKE 'log_bin_trust_function_creators';
"@

$sqlScript | mysql -u $mysqlUser -p

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✓ Configuracao aplicada com sucesso!" -ForegroundColor Green
    Write-Host "`nAgora voce pode restaurar backups normalmente.`n" -ForegroundColor Green
    
    Write-Host "IMPORTANTE:" -ForegroundColor Yellow
    Write-Host "  Esta configuracao e temporaria (perdida ao reiniciar MySQL)." -ForegroundColor Yellow
    Write-Host "  Para tornar permanente, adicione ao arquivo my.ini:" -ForegroundColor Yellow
    Write-Host "  [mysqld]" -ForegroundColor White
    Write-Host "  log_bin_trust_function_creators=1`n" -ForegroundColor White
} else {
    Write-Host "`n✗ Erro ao aplicar configuracao." -ForegroundColor Red
    Write-Host "  Verifique se voce forneceu a senha correta do root.`n" -ForegroundColor Red
}

Read-Host "`nPressione Enter para sair"
