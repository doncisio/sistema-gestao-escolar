# ============================================
# Script para Localizar my.ini do MySQL
# Sistema de Gestão Escolar
# ============================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  LOCALIZANDO ARQUIVO my.ini DO MYSQL" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Locais comuns onde o my.ini pode estar
$locaisComuns = @(
    "C:\ProgramData\MySQL\MySQL Server 8.0\my.ini",
    "C:\ProgramData\MySQL\MySQL Server 8.4\my.ini",
    "C:\ProgramData\MySQL\MySQL Server 5.7\my.ini",
    "C:\Program Files\MySQL\MySQL Server 8.0\my.ini",
    "C:\Program Files\MySQL\MySQL Server 8.4\my.ini",
    "C:\Program Files\MySQL\MySQL Server 5.7\my.ini",
    "C:\mysql\my.ini",
    "C:\Windows\my.ini",
    "$env:WINDIR\my.ini"
)

Write-Host "Procurando em locais comuns..." -ForegroundColor Yellow

$encontrados = @()

foreach ($caminho in $locaisComuns) {
    if (Test-Path $caminho) {
        $encontrados += $caminho
        Write-Host "✓ ENCONTRADO: $caminho" -ForegroundColor Green
    }
}

# Buscar no MySQL instalado
Write-Host "`nVerificando instalação do MySQL..." -ForegroundColor Yellow

try {
    $mysqlPath = (Get-Command mysql -ErrorAction SilentlyContinue).Source
    if ($mysqlPath) {
        Write-Host "✓ MySQL encontrado em: $mysqlPath" -ForegroundColor Green
        
        # Tentar descobrir o diretório base do MySQL
        $mysqlDir = Split-Path (Split-Path $mysqlPath -Parent) -Parent
        Write-Host "  Diretório base: $mysqlDir" -ForegroundColor Cyan
        
        # Procurar my.ini recursivamente nesse diretório
        $arquivosIni = Get-ChildItem -Path $mysqlDir -Filter "my.ini" -Recurse -ErrorAction SilentlyContinue
        foreach ($arquivo in $arquivosIni) {
            if ($arquivo.FullName -notin $encontrados) {
                $encontrados += $arquivo.FullName
                Write-Host "✓ ENCONTRADO: $($arquivo.FullName)" -ForegroundColor Green
            }
        }
    }
} catch {
    Write-Host "  MySQL não encontrado no PATH" -ForegroundColor Gray
}

# Perguntar ao MySQL onde está o arquivo de configuração
Write-Host "`nConsultando MySQL sobre arquivos de configuração..." -ForegroundColor Yellow

try {
    $mysqlConfig = mysql --help 2>&1 | Select-String "Default options are read from"
    if ($mysqlConfig) {
        Write-Host "✓ Informação do MySQL:" -ForegroundColor Green
        Write-Host "  $mysqlConfig" -ForegroundColor Cyan
        
        # Extrair caminhos da mensagem
        $configLine = mysql --help 2>&1 | Select-String "order:"
        if ($configLine) {
            Write-Host "  $configLine" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "  Não foi possível consultar MySQL" -ForegroundColor Gray
}

# Buscar em todo o drive C: (pode demorar)
Write-Host "`nDeseja buscar em todo o drive C:? (pode demorar alguns minutos)" -ForegroundColor Yellow
$resposta = Read-Host "Digite S para sim ou N para não"

if ($resposta -eq "S" -or $resposta -eq "s") {
    Write-Host "`nBuscando em todo o drive C:..." -ForegroundColor Yellow
    Write-Host "(Isso pode levar alguns minutos...)" -ForegroundColor Gray
    
    $todosDrive = Get-ChildItem -Path "C:\" -Filter "my.ini" -Recurse -ErrorAction SilentlyContinue
    foreach ($arquivo in $todosDrive) {
        if ($arquivo.FullName -notin $encontrados) {
            $encontrados += $arquivo.FullName
            Write-Host "✓ ENCONTRADO: $($arquivo.FullName)" -ForegroundColor Green
        }
    }
}

# Resumo
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RESUMO" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($encontrados.Count -eq 0) {
    Write-Host "✗ Nenhum arquivo my.ini foi encontrado." -ForegroundColor Red
    Write-Host "`nPOSSÍVEIS SOLUÇÕES:" -ForegroundColor Yellow
    Write-Host "1. O MySQL pode não ter um arquivo my.ini (usa configurações padrão)" -ForegroundColor White
    Write-Host "2. Você pode criar um arquivo my.ini manualmente" -ForegroundColor White
    Write-Host "3. Use a solução temporária com o script fix_backup_error.ps1`n" -ForegroundColor White
    
    Write-Host "Deseja criar um arquivo my.ini agora? (S/N)" -ForegroundColor Yellow
    $criar = Read-Host
    
    if ($criar -eq "S" -or $criar -eq "s") {
        # Tentar encontrar o diretório de dados do MySQL
        try {
            $dataDir = mysql -u root -p -e "SELECT @@datadir;" 2>&1 | Select-String -Pattern "^\w:"
            if ($dataDir) {
                $mysqlBase = Split-Path $dataDir.ToString().Trim() -Parent
                $myIniPath = Join-Path $mysqlBase "my.ini"
                
                Write-Host "`nCriando my.ini em: $myIniPath" -ForegroundColor Cyan
                
                $conteudoIni = @"
[mysqld]
# Porta padrão do MySQL
port=3306

# Diretório de dados
datadir=$($dataDir.ToString().Trim())

# Configuração para permitir criação de functions/procedures sem privilégio SUPER
log_bin_trust_function_creators=1

# Charset padrão
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

[client]
# Charset padrão para cliente
default-character-set=utf8mb4
"@
                
                Set-Content -Path $myIniPath -Value $conteudoIni -Encoding UTF8
                Write-Host "✓ Arquivo my.ini criado com sucesso!" -ForegroundColor Green
                Write-Host "`nIMPORTANTE: Reinicie o serviço MySQL para aplicar as configurações:" -ForegroundColor Yellow
                Write-Host "  net stop MySQL" -ForegroundColor White
                Write-Host "  net start MySQL`n" -ForegroundColor White
            }
        } catch {
            Write-Host "✗ Não foi possível criar o arquivo automaticamente." -ForegroundColor Red
        }
    }
} else {
    Write-Host "Foram encontrados $($encontrados.Count) arquivo(s) my.ini:" -ForegroundColor Green
    Write-Host ""
    
    for ($i = 0; $i -lt $encontrados.Count; $i++) {
        Write-Host "[$($i + 1)] $($encontrados[$i])" -ForegroundColor Cyan
    }
    
    Write-Host "`nO arquivo correto geralmente está em:" -ForegroundColor Yellow
    Write-Host "  C:\ProgramData\MySQL\MySQL Server X.X\my.ini" -ForegroundColor White
    
    Write-Host "`nDeseja abrir um desses arquivos? (Digite o número ou N para não)" -ForegroundColor Yellow
    $escolha = Read-Host
    
    if ($escolha -match "^\d+$") {
        $index = [int]$escolha - 1
        if ($index -ge 0 -and $index -lt $encontrados.Count) {
            $arquivoEscolhido = $encontrados[$index]
            
            Write-Host "`nAbrindo $arquivoEscolhido..." -ForegroundColor Cyan
            
            # Verificar se precisa de permissões de administrador
            try {
                notepad $arquivoEscolhido
            } catch {
                Write-Host "✗ Erro ao abrir arquivo. Tente executar como Administrador." -ForegroundColor Red
            }
            
            Write-Host "`nPara aplicar a correção do backup, adicione esta linha na seção [mysqld]:" -ForegroundColor Yellow
            Write-Host "  log_bin_trust_function_creators=1" -ForegroundColor White
            Write-Host "`nDepois reinicie o MySQL:" -ForegroundColor Yellow
            Write-Host "  net stop MySQL" -ForegroundColor White
            Write-Host "  net start MySQL`n" -ForegroundColor White
        }
    }
}

Write-Host "`nALTERNATIVA MAIS FÁCIL:" -ForegroundColor Yellow
Write-Host "Se não encontrar ou não quiser editar o my.ini," -ForegroundColor White
Write-Host "use a solução temporária executando:" -ForegroundColor White
Write-Host "  .\fix_backup_error.ps1" -ForegroundColor Cyan
Write-Host "(Deve ser executado como Administrador)`n" -ForegroundColor Gray

Read-Host "Pressione Enter para sair"
