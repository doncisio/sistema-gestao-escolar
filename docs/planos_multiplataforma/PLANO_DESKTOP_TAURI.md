# 🖥️ Plano de Migração para Plataforma Desktop Moderna (Electron/Tauri)

## Visão Geral

Este documento detalha o plano para modernização da aplicação desktop, oferecendo duas abordagens: **Electron** (mais maduro e amplamente usado) ou **Tauri** (mais leve e performático). Ambas permitem criar aplicações desktop multiplataforma (Windows, macOS, Linux) usando tecnologias web.

---

## 📊 Análise Comparativa: Electron vs Tauri

### Electron

| Aspecto | Detalhes |
|---------|----------|
| **Base** | Chromium + Node.js |
| **Tamanho do app** | ~150-200 MB |
| **Memória RAM** | ~200-400 MB |
| **Maturidade** | Alta (desde 2013) |
| **Ecossistema** | Muito rico |
| **Exemplos** | VS Code, Slack, Discord |
| **Curva de aprendizado** | Moderada |

### Tauri

| Aspecto | Detalhes |
|---------|----------|
| **Base** | WebView nativo + Rust |
| **Tamanho do app** | ~10-30 MB |
| **Memória RAM** | ~50-100 MB |
| **Maturidade** | Média (v1.0 em 2022) |
| **Ecossistema** | Crescendo rapidamente |
| **Exemplos** | Tauri apps, Pake |
| **Curva de aprendizado** | Moderada a Alta |

### Recomendação

**Para este projeto: Tauri** é recomendado por:
1. ✅ App significativamente menor (~90% menor)
2. ✅ Uso de memória muito reduzido
3. ✅ Performance superior
4. ✅ Backend em Rust pode se integrar bem com Python via FFI
5. ✅ Segurança superior (sem Node.js)
6. ✅ Atualizações OTA nativas

**Alternativa Electron** se:
- Equipe já tem experiência com Electron
- Necessidade de plugins Node.js específicos
- Prazo muito apertado

---

## 🏗️ Arquitetura Tauri

### Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React/TypeScript)                     │
├─────────────────────────────────────────────────────────────────────┤
│  React 18 │ TypeScript │ TanStack Query │ Tailwind CSS │ Shadcn/ui │
│  React Router │ Zustand │ Tauri API                                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ IPC (Inter-Process Communication)
┌─────────────────────────────────────────────────────────────────────┐
│                      TAURI CORE (Rust)                               │
├─────────────────────────────────────────────────────────────────────┤
│  Commands │ Events │ State │ Window Management │ System Tray        │
│  File System │ Notifications │ Updater │ CLI                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ Sidecar/FFI
┌─────────────────────────────────────────────────────────────────────┐
│                      PYTHON BACKEND (Sidecar)                        │
├─────────────────────────────────────────────────────────────────────┤
│  Services existentes │ Conexão MySQL │ Geração PDF │ Cache          │
│  Lógica de negócio │ Relatórios │ Backup                            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        BANCO DE DADOS                                │
├─────────────────────────────────────────────────────────────────────┤
│     MySQL 8.0+ (Local ou Remoto) │ SQLite (Cache Local)             │
└─────────────────────────────────────────────────────────────────────┘
```

### Vantagens desta Arquitetura

1. **Reaproveitamento Total**: Services Python existentes funcionam como sidecar
2. **Performance**: Frontend nativo via WebView, não Chromium completo
3. **Segurança**: Rust para camada de segurança crítica
4. **Tamanho Pequeno**: App final ~30-50 MB (vs ~200 MB do atual empacotado)
5. **Atualizações**: Sistema de atualização automática integrado
6. **Multiplataforma**: Um único código para Windows, macOS e Linux

---

## 📁 Estrutura de Diretórios (Tauri)

```
desktop/
├── src/                           # Frontend React
│   ├── App.tsx
│   ├── main.tsx
│   │
│   ├── api/                       # Comunicação com Tauri/Python
│   │   ├── tauri.ts               # Wrapper Tauri invoke
│   │   ├── commands/
│   │   │   ├── alunos.ts
│   │   │   ├── funcionarios.ts
│   │   │   ├── turmas.ts
│   │   │   ├── notas.ts
│   │   │   ├── frequencia.ts
│   │   │   ├── relatorios.ts
│   │   │   └── backup.ts
│   │   └── index.ts
│   │
│   ├── components/
│   │   ├── ui/                    # Shadcn/ui
│   │   ├── layout/
│   │   │   ├── TitleBar.tsx       # Barra de título customizada
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MainContent.tsx
│   │   │   └── StatusBar.tsx
│   │   ├── common/
│   │   ├── forms/
│   │   └── features/
│   │       ├── alunos/
│   │       ├── funcionarios/
│   │       ├── turmas/
│   │       ├── notas/
│   │       ├── frequencia/
│   │       ├── relatorios/
│   │       └── dashboard/
│   │
│   ├── hooks/
│   │   ├── useTauri.ts
│   │   ├── useWindow.ts
│   │   ├── useNotification.ts
│   │   └── useShortcuts.ts
│   │
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── settingsStore.ts
│   │   └── uiStore.ts
│   │
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── shortcuts.ts
│   │
│   └── types/
│       └── *.ts
│
├── src-tauri/                     # Backend Rust
│   ├── src/
│   │   ├── main.rs                # Entry point
│   │   ├── lib.rs
│   │   │
│   │   ├── commands/              # Tauri commands
│   │   │   ├── mod.rs
│   │   │   ├── alunos.rs
│   │   │   ├── funcionarios.rs
│   │   │   ├── turmas.rs
│   │   │   ├── notas.rs
│   │   │   ├── frequencia.rs
│   │   │   ├── relatorios.rs
│   │   │   ├── backup.rs
│   │   │   └── system.rs
│   │   │
│   │   ├── state/                 # Estado global Tauri
│   │   │   ├── mod.rs
│   │   │   └── app_state.rs
│   │   │
│   │   ├── python/                # Integração Python
│   │   │   ├── mod.rs
│   │   │   └── sidecar.rs
│   │   │
│   │   ├── db/                    # Conexão direta (opcional)
│   │   │   ├── mod.rs
│   │   │   └── mysql.rs
│   │   │
│   │   └── utils/
│   │       ├── mod.rs
│   │       └── helpers.rs
│   │
│   ├── binaries/                  # Sidecar Python empacotado
│   │   └── python-backend/
│   │
│   ├── icons/                     # Ícones do app
│   │   ├── 32x32.png
│   │   ├── 128x128.png
│   │   ├── 128x128@2x.png
│   │   ├── icon.icns
│   │   └── icon.ico
│   │
│   ├── Cargo.toml                 # Dependências Rust
│   ├── tauri.conf.json            # Config Tauri
│   └── build.rs
│
├── python-backend/                # Backend Python (sidecar)
│   ├── main.py                    # Entry point do sidecar
│   ├── api/
│   │   ├── __init__.py
│   │   ├── alunos.py
│   │   ├── funcionarios.py
│   │   ├── turmas.py
│   │   ├── notas.py
│   │   ├── frequencia.py
│   │   ├── relatorios.py
│   │   └── backup.py
│   │
│   ├── services/                  # REUTILIZAR do projeto atual!
│   │   └── ... (copiar de gestao/services)
│   │
│   ├── models/                    # REUTILIZAR do projeto atual!
│   │   └── ... (copiar de gestao/models)
│   │
│   ├── db/                        # REUTILIZAR do projeto atual!
│   │   └── ... (copiar de gestao/db)
│   │
│   ├── utils/                     # REUTILIZAR do projeto atual!
│   │   └── ...
│   │
│   ├── requirements.txt
│   └── pyproject.toml
│
├── scripts/
│   ├── build-python.ps1           # Build do sidecar Python
│   ├── build-python.sh
│   └── dev.ps1
│
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
├── .eslintrc.js
└── README.md
```

---

## 🔧 Configuração Tauri

### tauri.conf.json

```json
{
  "$schema": "../node_modules/@tauri-apps/cli/schema.json",
  "build": {
    "beforeBuildCommand": "npm run build",
    "beforeDevCommand": "npm run dev",
    "devPath": "http://localhost:5173",
    "distDir": "../dist"
  },
  "package": {
    "productName": "Gestão Escolar",
    "version": "1.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "sidecar": true,
        "scope": [
          {
            "name": "python-backend",
            "sidecar": true,
            "args": true
          }
        ]
      },
      "fs": {
        "all": false,
        "readFile": true,
        "writeFile": true,
        "readDir": true,
        "createDir": true,
        "removeDir": true,
        "removeFile": true,
        "scope": ["$APP/*", "$DOCUMENT/*", "$DOWNLOAD/*"]
      },
      "dialog": {
        "all": true
      },
      "notification": {
        "all": true
      },
      "globalShortcut": {
        "all": true
      },
      "clipboard": {
        "all": true
      },
      "window": {
        "all": true
      },
      "path": {
        "all": true
      },
      "os": {
        "all": true
      },
      "process": {
        "all": true
      },
      "protocol": {
        "asset": true,
        "assetScope": ["**"]
      }
    },
    "bundle": {
      "active": true,
      "category": "Education",
      "copyright": "© 2025 Sistema de Gestão Escolar",
      "deb": {
        "depends": []
      },
      "externalBin": ["binaries/python-backend"],
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/128x128@2x.png",
        "icons/icon.icns",
        "icons/icon.ico"
      ],
      "identifier": "br.com.escola.gestao",
      "longDescription": "Sistema completo de gestão escolar para escolas municipais",
      "macOS": {
        "entitlements": null,
        "exceptionDomain": "",
        "frameworks": [],
        "providerShortName": null,
        "signingIdentity": null
      },
      "resources": [],
      "shortDescription": "Gestão Escolar",
      "targets": "all",
      "windows": {
        "certificateThumbprint": null,
        "digestAlgorithm": "sha256",
        "timestampUrl": "",
        "wix": null
      }
    },
    "security": {
      "csp": "default-src 'self'; img-src 'self' data: asset: https:; style-src 'self' 'unsafe-inline'"
    },
    "updater": {
      "active": true,
      "endpoints": [
        "https://gestao-escolar.com.br/api/updates/{{target}}/{{arch}}/{{current_version}}"
      ],
      "dialog": true,
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk..."
    },
    "windows": [
      {
        "fullscreen": false,
        "height": 700,
        "width": 900,
        "minHeight": 600,
        "minWidth": 800,
        "resizable": true,
        "title": "Sistema de Gestão Escolar",
        "center": true,
        "decorations": false,
        "transparent": true
      }
    ],
    "systemTray": {
      "iconPath": "icons/32x32.png",
      "iconAsTemplate": true,
      "menuOnLeftClick": true
    }
  }
}
```

### Cargo.toml (Dependências Rust)

```toml
[package]
name = "gestao-escolar"
version = "1.0.0"
description = "Sistema de Gestão Escolar"
authors = ["Escola Municipal"]
license = "MIT"
repository = ""
edition = "2021"

[build-dependencies]
tauri-build = { version = "1.5", features = [] }

[dependencies]
tauri = { version = "1.6", features = [
    "shell-sidecar",
    "fs-all",
    "dialog-all",
    "notification-all",
    "global-shortcut-all",
    "clipboard-all",
    "window-all",
    "path-all",
    "os-all",
    "process-all",
    "protocol-asset",
    "system-tray",
    "updater"
] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1", features = ["full"] }
anyhow = "1.0"
thiserror = "1.0"
log = "0.4"
env_logger = "0.10"

# Opcional: conexão direta MySQL (se não usar sidecar)
# mysql = "24.0"
# sqlx = { version = "0.7", features = ["runtime-tokio-rustls", "mysql"] }

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
```

---

## 🔄 Integração Python (Sidecar)

### Conceito do Sidecar

O Sidecar permite empacotar um executável Python junto com o app Tauri, permitindo reutilizar todo o código Python existente.

### main.rs (Entry Point Rust)

```rust
// src-tauri/src/main.rs
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod state;
mod python;

use tauri::Manager;
use state::AppState;

fn main() {
    tauri::Builder::default()
        .manage(AppState::new())
        .setup(|app| {
            // Iniciar sidecar Python
            let python_path = app
                .path_resolver()
                .resolve_resource("binaries/python-backend")
                .expect("failed to resolve python backend");
            
            // Spawnar processo Python
            python::start_sidecar(&python_path)?;
            
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::alunos::listar_alunos,
            commands::alunos::buscar_aluno,
            commands::alunos::criar_aluno,
            commands::alunos::atualizar_aluno,
            commands::alunos::excluir_aluno,
            commands::funcionarios::listar_funcionarios,
            commands::turmas::listar_turmas,
            commands::notas::lancar_notas,
            commands::frequencia::lancar_frequencia,
            commands::relatorios::gerar_relatorio,
            commands::backup::fazer_backup,
            commands::backup::restaurar_backup,
            commands::system::get_version,
            commands::system::check_updates,
        ])
        .system_tray(tauri::SystemTray::new())
        .on_system_tray_event(|app, event| {
            // Handle system tray events
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Comunicação com Sidecar Python

```rust
// src-tauri/src/python/sidecar.rs
use std::process::{Command, Child, Stdio};
use std::sync::Mutex;
use tauri::api::process::{Command as TauriCommand, CommandEvent};
use serde::{Deserialize, Serialize};

static PYTHON_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

#[derive(Serialize, Deserialize)]
pub struct PythonRequest {
    pub command: String,
    pub params: serde_json::Value,
}

#[derive(Serialize, Deserialize)]
pub struct PythonResponse {
    pub success: bool,
    pub data: Option<serde_json::Value>,
    pub error: Option<String>,
}

pub fn start_sidecar(path: &std::path::Path) -> Result<(), Box<dyn std::error::Error>> {
    let (mut rx, child) = TauriCommand::new_sidecar("python-backend")?
        .args(&["--mode", "ipc"])
        .spawn()?;
    
    // Armazenar processo
    *PYTHON_PROCESS.lock().unwrap() = Some(child);
    
    // Escutar eventos do sidecar
    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(line) => {
                    println!("[Python]: {}", line);
                }
                CommandEvent::Stderr(line) => {
                    eprintln!("[Python Error]: {}", line);
                }
                _ => {}
            }
        }
    });
    
    Ok(())
}

pub async fn call_python(request: PythonRequest) -> Result<PythonResponse, String> {
    // Comunicação via stdin/stdout ou HTTP local
    // Implementação depende da estratégia escolhida
    todo!()
}
```

### Backend Python (Sidecar)

```python
# python-backend/main.py
"""
Backend Python para o Tauri Sidecar.
Reutiliza services do sistema existente.
"""

import sys
import json
import argparse
from typing import Any, Dict

# Adicionar path do projeto original
sys.path.insert(0, '.')

# Importar services existentes
from services.aluno_service import AlunoService
from services.funcionario_service import FuncionarioService
from services.estatistica_service import EstatisticaService
from services.report_service import ReportService
from services.backup_service import BackupService
from conexao import inicializar_pool


class IPCHandler:
    """Handler para comunicação IPC com Tauri."""
    
    def __init__(self):
        # Inicializar pool de conexões
        inicializar_pool()
        
        # Instanciar services
        self.aluno_service = AlunoService()
        self.funcionario_service = FuncionarioService()
        self.estatistica_service = EstatisticaService()
        self.report_service = ReportService()
        self.backup_service = BackupService()
        
        # Mapear comandos para handlers
        self.commands = {
            'alunos.listar': self.aluno_service.listar_alunos,
            'alunos.buscar': self.aluno_service.buscar_aluno,
            'alunos.criar': self.aluno_service.criar_aluno,
            'alunos.atualizar': self.aluno_service.atualizar_aluno,
            'alunos.excluir': self.aluno_service.excluir_aluno,
            
            'funcionarios.listar': self.funcionario_service.listar_funcionarios,
            'funcionarios.buscar': self.funcionario_service.buscar_funcionario,
            
            'estatisticas.dashboard': self.estatistica_service.obter_estatisticas_alunos,
            'estatisticas.turmas': self.estatistica_service.obter_estatisticas_turmas,
            
            'relatorios.gerar': self.report_service.gerar_relatorio,
            
            'backup.criar': self.backup_service.fazer_backup,
            'backup.restaurar': self.backup_service.restaurar_backup,
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Processa uma requisição IPC."""
        command = request.get('command')
        params = request.get('params', {})
        
        if command not in self.commands:
            return {
                'success': False,
                'error': f'Comando desconhecido: {command}'
            }
        
        try:
            handler = self.commands[command]
            result = handler(**params) if params else handler()
            
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_ipc_loop(self):
        """Loop principal de IPC via stdin/stdout."""
        while True:
            try:
                # Ler linha do stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Parsear JSON
                request = json.loads(line.strip())
                
                # Processar
                response = self.handle_request(request)
                
                # Enviar resposta
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                print(json.dumps({
                    'success': False,
                    'error': f'JSON inválido: {e}'
                }), flush=True)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(json.dumps({
                    'success': False,
                    'error': str(e)
                }), flush=True)


def main():
    parser = argparse.ArgumentParser(description='Backend Python para Gestão Escolar')
    parser.add_argument('--mode', choices=['ipc', 'http'], default='ipc',
                       help='Modo de comunicação: ipc (stdin/stdout) ou http')
    parser.add_argument('--port', type=int, default=8765,
                       help='Porta HTTP (se mode=http)')
    
    args = parser.parse_args()
    
    handler = IPCHandler()
    
    if args.mode == 'ipc':
        handler.run_ipc_loop()
    else:
        # Modo HTTP para desenvolvimento
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class RequestHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                request = json.loads(body)
                response = handler.handle_request(request)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
        
        server = HTTPServer(('127.0.0.1', args.port), RequestHandler)
        print(f'Python backend rodando em http://127.0.0.1:{args.port}')
        server.serve_forever()


if __name__ == '__main__':
    main()
```

---

## 💻 Frontend React/TypeScript

### Wrapper para Tauri Commands

```typescript
// src/api/tauri.ts
import { invoke } from '@tauri-apps/api/tauri'

interface TauriResponse<T> {
  success: boolean
  data?: T
  error?: string
}

export async function tauriInvoke<T>(
  command: string,
  args?: Record<string, unknown>
): Promise<T> {
  try {
    const response = await invoke<TauriResponse<T>>(command, args)
    
    if (!response.success) {
      throw new Error(response.error || 'Erro desconhecido')
    }
    
    return response.data as T
  } catch (error) {
    if (error instanceof Error) {
      throw error
    }
    throw new Error(String(error))
  }
}

// Exemplo de uso específico
export const alunosApi = {
  listar: (params?: { nome?: string; turma_id?: number }) =>
    tauriInvoke<Aluno[]>('listar_alunos', params),
  
  buscar: (id: number) =>
    tauriInvoke<Aluno>('buscar_aluno', { id }),
  
  criar: (data: AlunoCreate) =>
    tauriInvoke<Aluno>('criar_aluno', { data }),
  
  atualizar: (id: number, data: AlunoUpdate) =>
    tauriInvoke<Aluno>('atualizar_aluno', { id, data }),
  
  excluir: (id: number) =>
    tauriInvoke<void>('excluir_aluno', { id }),
}
```

### Barra de Título Customizada

```tsx
// src/components/layout/TitleBar.tsx
import { appWindow } from '@tauri-apps/api/window'
import { useState, useEffect } from 'react'

export function TitleBar() {
  const [isMaximized, setIsMaximized] = useState(false)
  
  useEffect(() => {
    const checkMaximized = async () => {
      setIsMaximized(await appWindow.isMaximized())
    }
    
    checkMaximized()
    
    // Escutar mudanças
    const unlisten = appWindow.onResized(checkMaximized)
    
    return () => {
      unlisten.then(fn => fn())
    }
  }, [])
  
  const handleMinimize = () => appWindow.minimize()
  const handleMaximize = () => appWindow.toggleMaximize()
  const handleClose = () => appWindow.close()
  
  return (
    <div 
      data-tauri-drag-region
      className="h-8 bg-primary-700 flex items-center justify-between select-none"
    >
      {/* Logo e Título */}
      <div className="flex items-center gap-2 px-3" data-tauri-drag-region>
        <img src="/logo.png" alt="Logo" className="w-5 h-5" />
        <span className="text-white text-sm font-medium">
          Sistema de Gestão Escolar
        </span>
      </div>
      
      {/* Botões de controle */}
      <div className="flex">
        <button
          onClick={handleMinimize}
          className="w-12 h-8 hover:bg-white/10 flex items-center justify-center"
        >
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 10 1">
            <rect width="10" height="1" />
          </svg>
        </button>
        
        <button
          onClick={handleMaximize}
          className="w-12 h-8 hover:bg-white/10 flex items-center justify-center"
        >
          {isMaximized ? (
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 10 10">
              <path d="M2 0h6v6H2zM0 2h6v6H0z" strokeWidth="1" />
            </svg>
          ) : (
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 10 10">
              <rect width="10" height="10" strokeWidth="1" />
            </svg>
          )}
        </button>
        
        <button
          onClick={handleClose}
          className="w-12 h-8 hover:bg-red-500 flex items-center justify-center"
        >
          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 10 10">
            <path d="M1 1l8 8M9 1l-8 8" strokeWidth="1.5" />
          </svg>
        </button>
      </div>
    </div>
  )
}
```

### Atalhos Globais

```typescript
// src/hooks/useShortcuts.ts
import { useEffect } from 'react'
import { register, unregister } from '@tauri-apps/api/globalShortcut'
import { useNavigate } from 'react-router-dom'

interface Shortcut {
  key: string
  action: () => void
  description: string
}

export function useGlobalShortcuts() {
  const navigate = useNavigate()
  
  const shortcuts: Shortcut[] = [
    { key: 'CommandOrControl+N', action: () => navigate('/alunos/novo'), description: 'Novo Aluno' },
    { key: 'CommandOrControl+F', action: () => document.getElementById('search')?.focus(), description: 'Buscar' },
    { key: 'CommandOrControl+D', action: () => navigate('/dashboard'), description: 'Dashboard' },
    { key: 'CommandOrControl+B', action: () => navigate('/backup'), description: 'Backup' },
    { key: 'F5', action: () => window.location.reload(), description: 'Atualizar' },
    { key: 'F1', action: () => navigate('/ajuda'), description: 'Ajuda' },
  ]
  
  useEffect(() => {
    // Registrar atalhos
    shortcuts.forEach(async ({ key, action }) => {
      try {
        await register(key, action)
      } catch (error) {
        console.error(`Erro ao registrar atalho ${key}:`, error)
      }
    })
    
    // Cleanup
    return () => {
      shortcuts.forEach(async ({ key }) => {
        try {
          await unregister(key)
        } catch (error) {
          console.error(`Erro ao desregistrar atalho ${key}:`, error)
        }
      })
    }
  }, [navigate])
  
  return shortcuts
}
```

### Notificações Nativas

```typescript
// src/hooks/useNotification.ts
import { sendNotification, isPermissionGranted, requestPermission } from '@tauri-apps/api/notification'
import { useEffect, useState } from 'react'

export function useNotification() {
  const [hasPermission, setHasPermission] = useState(false)
  
  useEffect(() => {
    checkPermission()
  }, [])
  
  const checkPermission = async () => {
    let permission = await isPermissionGranted()
    
    if (!permission) {
      const result = await requestPermission()
      permission = result === 'granted'
    }
    
    setHasPermission(permission)
  }
  
  const notify = async (title: string, body?: string, icon?: string) => {
    if (!hasPermission) {
      console.warn('Permissão de notificação não concedida')
      return
    }
    
    await sendNotification({
      title,
      body,
      icon,
    })
  }
  
  return { notify, hasPermission }
}
```

---

## 📋 Cronograma de Implementação

### Fase 1: Setup e Infraestrutura (2 semanas)

#### Semana 1: Configuração do Projeto
- [ ] Instalar Rust e Tauri CLI
- [ ] Criar projeto Tauri com template React + Vite
- [ ] Configurar TypeScript e Tailwind CSS
- [ ] Configurar Shadcn/ui
- [ ] Criar estrutura de diretórios
- [ ] Configurar ESLint e Prettier

#### Semana 2: Backend Python Sidecar
- [ ] Estruturar sidecar Python
- [ ] Copiar services existentes
- [ ] Implementar IPC handler
- [ ] Testar comunicação Tauri ↔ Python
- [ ] Configurar PyInstaller para build do sidecar
- [ ] Configurar bundle do sidecar no Tauri

### Fase 2: UI e Funcionalidades Core (4 semanas)

#### Semana 3: Layout Base
- [ ] Implementar TitleBar customizada
- [ ] Criar Sidebar com navegação
- [ ] Implementar sistema de rotas
- [ ] Criar layout responsivo
- [ ] Implementar tema claro/escuro

#### Semana 4: Módulo Alunos
- [ ] Lista de alunos com busca e filtros
- [ ] Formulário de cadastro/edição
- [ ] Detalhes do aluno
- [ ] CRUD completo integrado
- [ ] Testes

#### Semana 5: Módulos Funcionários e Turmas
- [ ] CRUD Funcionários
- [ ] CRUD Turmas
- [ ] Relacionamentos entre entidades
- [ ] Testes

#### Semana 6: Notas e Frequência
- [ ] Interface de lançamento de notas
- [ ] Interface de frequência
- [ ] Integração com services existentes
- [ ] Testes

### Fase 3: Funcionalidades Avançadas (2-3 semanas)

#### Semana 7: Dashboard e Relatórios
- [ ] Dashboard com estatísticas
- [ ] Gráficos (Recharts)
- [ ] Geração de relatórios PDF
- [ ] Visualização de PDFs
- [ ] Download/Impressão

#### Semana 8: Recursos Desktop
- [ ] System Tray com menu
- [ ] Notificações nativas
- [ ] Atalhos globais
- [ ] Backup automático
- [ ] Sistema de atualizações

#### Semana 9: Polimento
- [ ] Animações e transições
- [ ] Loading states
- [ ] Error handling global
- [ ] Performance optimization
- [ ] Acessibilidade

### Fase 4: Build e Distribuição (1-2 semanas)

#### Semana 10: Build e Testes
- [ ] Build para Windows
- [ ] Build para macOS
- [ ] Build para Linux
- [ ] Testes em cada plataforma
- [ ] Correção de bugs específicos

#### Semana 11: Distribuição
- [ ] Configurar assinatura de código (Windows/macOS)
- [ ] Configurar servidor de atualizações
- [ ] Criar instaladores
- [ ] Documentação de instalação
- [ ] Release inicial

---

## 🚀 Build e Distribuição

### Scripts de Build

```powershell
# scripts/build-python.ps1 (Windows)
# Build do sidecar Python com PyInstaller

$ErrorActionPreference = "Stop"

Write-Host "🐍 Building Python sidecar..."

# Ativar venv
& python-backend\.venv\Scripts\Activate.ps1

# Build com PyInstaller
pyinstaller `
    --onefile `
    --name "python-backend" `
    --distpath "src-tauri/binaries" `
    --workpath "build/pyinstaller" `
    --specpath "build" `
    --add-data "python-backend/services;services" `
    --add-data "python-backend/models;models" `
    --add-data "python-backend/db;db" `
    --hidden-import "mysql.connector" `
    --hidden-import "pydantic" `
    python-backend/main.py

Write-Host "✅ Python sidecar built successfully!"
```

```bash
#!/bin/bash
# scripts/build-python.sh (macOS/Linux)

echo "🐍 Building Python sidecar..."

source python-backend/.venv/bin/activate

pyinstaller \
    --onefile \
    --name "python-backend" \
    --distpath "src-tauri/binaries" \
    --workpath "build/pyinstaller" \
    --specpath "build" \
    --add-data "python-backend/services:services" \
    --add-data "python-backend/models:models" \
    --add-data "python-backend/db:db" \
    --hidden-import "mysql.connector" \
    --hidden-import "pydantic" \
    python-backend/main.py

echo "✅ Python sidecar built successfully!"
```

### Package.json Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri",
    "tauri:dev": "tauri dev",
    "tauri:build": "npm run build:python && tauri build",
    "build:python": "pwsh -ExecutionPolicy Bypass -File scripts/build-python.ps1",
    "build:python:unix": "bash scripts/build-python.sh"
  }
}
```

---

## 🔐 Segurança

### Configuração CSP (Content Security Policy)

```json
// tauri.conf.json > tauri > security
{
  "security": {
    "csp": {
      "default-src": "'self'",
      "script-src": "'self'",
      "style-src": "'self' 'unsafe-inline'",
      "img-src": "'self' data: asset: https:",
      "connect-src": "'self' https://gestao-escolar.com.br",
      "font-src": "'self' data:"
    }
  }
}
```

### Assinatura de Código

```toml
# Cargo.toml - Windows Code Signing
[package.metadata.tauri.bundle.windows]
certificate-thumbprint = "YOUR_CERTIFICATE_THUMBPRINT"
digest-algorithm = "sha256"
timestamp-url = "http://timestamp.digicert.com"
```

---

## 📊 Comparativo: Antes vs Depois

| Aspecto | Tkinter Atual | Tauri Novo |
|---------|---------------|------------|
| Tamanho do instalador | ~200 MB | ~50 MB |
| Memória RAM | ~300 MB | ~100 MB |
| Tempo de inicialização | 3-5s | < 1s |
| Look & Feel | Nativo básico | Moderno customizável |
| Atualizações | Manual | Automático OTA |
| Multiplataforma | Sim | Sim (melhor) |
| Integração OS | Limitada | Completa |
| Performance UI | Moderada | Excelente |

---

## 💰 Estimativa de Custos

### Desenvolvimento
- **Desenvolvedor Full Stack**: 10-11 semanas
- **Custo estimado**: R$ 40.000 - R$ 55.000

### Custos de Distribuição

| Item | Custo |
|------|-------|
| Apple Developer ID | $99/ano (~R$ 500) |
| Windows Code Signing | $100-400/ano (~R$ 500-2000) |
| Servidor de atualizações | R$ 50-100/mês |
| **Total Anual** | **~R$ 1.500 - R$ 3.500** |

---

## ✅ Checklist de Pré-Requisitos

- [ ] Rust instalado (rustup)
- [ ] Node.js 18+ instalado
- [ ] Python 3.12+ instalado
- [ ] Certificado de assinatura (Windows/macOS)
- [ ] Servidor para atualizações OTA
- [ ] Conhecimento básico de Rust (ou equipe com)
- [ ] Testes dos services Python existentes funcionando

---

## 📚 Referências

- [Tauri Documentation](https://tauri.app/v1/guides/)
- [Tauri Sidecar](https://tauri.app/v1/guides/building/sidecar/)
- [React Documentation](https://react.dev/)
- [Shadcn/ui](https://ui.shadcn.com/)
- [PyInstaller](https://pyinstaller.org/)
- [Tauri Updater](https://tauri.app/v1/guides/distribution/updater/)
