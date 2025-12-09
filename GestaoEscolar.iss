; Script para criar instalador do Sistema de Gestão Escolar
; Requer Inno Setup 6.0 ou superior
; Download: https://jrsoftware.org/isdl.php

#define MyAppName "Sistema de Gestão Escolar"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Sistema de Gestão Escolar"
#define MyAppURL "https://github.com/doncisio/sistema-gestao-escolar"
#define MyAppExeName "GestaoEscolar.exe"

[Setup]
; Informações básicas
AppId={{A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=README_INSTALACAO.txt
OutputDir=installer_output
OutputBaseFilename=GestaoEscolar_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

; Ícone do instalador
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Executáveis principais
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\setup_wizard.exe"; DestDir: "{app}"; Flags: ignoreversion; Check: not FileExists(ExpandConstant('{app}\.env'))

; Arquivos de configuração
Source: ".env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist confirmoverwrite
Source: "credentials.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "feature_flags.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "habilidades_bncc_parsed.csv"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Documentação
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; Diretórios de configuração (se existirem)
Source: "config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "static\*"; DestDir: "{app}\static"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Executar assistente de configuração na primeira instalação
Filename: "{app}\setup_wizard.exe"; Description: "Configurar Sistema de Gestão Escolar"; Flags: nowait postinstall skipifsilent; Check: NeedConfiguration
; Ou executar diretamente se já configurado
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent; Check: not NeedConfiguration

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\backup"
Type: filesandordirs; Name: "{app}\__pycache__"

[Code]
function NeedConfiguration(): Boolean;
var
  EnvFile: String;
begin
  EnvFile := ExpandConstant('{app}\.env');
  Result := not FileExists(EnvFile);
end;

procedure InitializeWizard;
var
  InfoPage: TOutputMsgWizardPage;
begin
  // Página de informações
  InfoPage := CreateOutputMsgPage(wpWelcome,
    'Bem-vindo ao Sistema de Gestão Escolar', 
    'Assistente de Instalação',
    'Este instalador irá:' + #13#10 + #13#10 +
    '  ✓ Instalar o Sistema de Gestão Escolar' + #13#10 +
    '  ✓ Copiar todos os arquivos necessários' + #13#10 +
    '  ✓ Criar atalhos no menu iniciar e desktop' + #13#10 + #13#10 +
    'IMPORTANTE: Após a instalação, um assistente de configuração' + #13#10 +
    'será executado para configurar o MySQL e opções de armazenamento.' + #13#10 + #13#10 +
    'Clique em Próximo para continuar.');
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsAdminInstallMode then
  begin
    MsgBox('É recomendado executar o instalador como Administrador para garantir permissões adequadas.', 
           mbInformation, MB_OK);
  end;
end;
