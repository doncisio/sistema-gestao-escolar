# Guia de Atualização dos Arquivos .bat

## 📋 Visão Geral

Os arquivos `.bat` foram movidos para `automacao/batch/`, mas alguns podem precisar de ajustes nos caminhos que referenciam.

## 📁 Localização

**Antes**: `c:\gestao\*.bat`  
**Agora**: `c:\gestao\automacao\batch\*.bat`

## 🔧 Arquivos que Podem Precisar de Ajuste

### 1. executar_sistema.bat
**Localização**: `automacao/batch/executar_sistema.bat`

Se o arquivo executava:
```batch
python main.py
```

Agora deve executar:
```batch
cd ..\..
python main.py
```

Ou usar caminho absoluto:
```batch
python c:\gestao\main.py
```

### 2. Scripts que executam Python

Para scripts em `automacao/batch/` que executam scripts Python movidos:

**Antes**:
```batch
python executar_lista_matriculados.py
```

**Agora**:
```batch
python ..\..\automacao\python\executar_lista_matriculados.py
```

Ou:
```batch
cd ..\..
python automacao\python\executar_lista_matriculados.py
```

### 3. Scripts de diagnóstico

**Antes**:
```batch
python check_alunos_342.py
```

**Agora**:
```batch
python ..\..\scripts\diagnostico\check_alunos_342.py
```

### 4. Scripts de manutenção

**Antes**:
```batch
python aplicar_otimizacoes_historico.py
```

**Agora**:
```batch
python ..\..\scripts\manutencao\aplicar_otimizacoes.py
```

## 📝 Template Genérico

Para qualquer `.bat` em `automacao/batch/`:

```batch
@echo off
REM Navegar para raiz do projeto
cd ..\..

REM Executar comando Python
python [caminho_relativo_do_raiz]

REM Pausar para ver resultado
pause
```

## 🔍 Lista de Arquivos .bat Movidos

1. `executar_sistema.bat` → Main do sistema
2. `executar_certificado.bat` → Certificados
3. `executar_folha_ponto.bat` → Folha de ponto
4. `executar_exportacao.bat` → Exportações
5. `executar_lista_matriculados.bat` → Listas
6. `executar_lista_matriculados_depois.bat` → Listas
7. `executar_lista_transferidos.bat` → Listas
8. `executar_limpeza_duplicatas.bat` → Manutenção
9. `executar_otimizacoes_historico.bat` → Manutenção
10. `executar_concluir_matriculas_nao_2025.bat` → Migração
11. `executar_teste_listas_escolas.bat` → Testes
12. `restaurar_banco.bat` → Backup

## 🛠️ Como Testar

1. Abrir CMD ou PowerShell
2. Navegar até `c:\gestao\automacao\batch\`
3. Executar um `.bat`
4. Verificar se funciona corretamente

## ⚠️ Atenção

- Alguns `.bat` podem já estar usando caminhos absolutos (não precisam ajuste)
- Scripts que executavam `python main.py` podem precisar do `cd ..\..` antes
- Scripts PowerShell em `automacao/powershell/` podem ter lógica diferente

## ✅ Recomendação

Se os `.bat` não estiverem funcionando após a reorganização:

1. Abrir o arquivo `.bat` no editor
2. Adicionar `cd ..\..` no início (para voltar ao raiz)
3. Ajustar caminhos relativos conforme necessário
4. Testar novamente

## 📞 Exemplo Prático

**executar_sistema.bat** (ajustado):
```batch
@echo off
echo ========================================
echo  Sistema de Gestão Escolar
echo ========================================
echo.

REM Navegar para raiz do projeto
cd ..\..

REM Executar sistema
python main.py

REM Pausar no final
pause
```

---

**Nota**: A maioria dos `.bat` deve funcionar sem ajustes se eles já usavam caminhos absolutos ou eram executados do diretório correto.
