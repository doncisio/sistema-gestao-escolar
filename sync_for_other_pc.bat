@echo off
REM Script para o outro PC: busca atualizações e aplica em 'main', opcionalmente muda para a branch de refactor

echo 1/4 - Buscar atualizacoes remotas e limpar refs antigos...
git fetch origin --prune

echo 2/4 - Trocar para branch main e puxar as ultimas alteracoes...
git checkout main
git pull origin main

echo 3/4 - Opcional: trocar para a branch de refactor (se existir no remoto ou localmente)
git fetch origin
git checkout refactor/modularizacao 2>nul || git checkout -b refactor/modularizacao origin/refactor/modularizacao 2>nul || git checkout -b refactor/modularizacao

echo 4/4 - Finalizado. Caso tenha conflitos, resolva-os localmente e rode:
echo    git add . && git commit -m "fix: resolver conflitos" && git push origin refactor/modularizacao

echo Pressione qualquer tecla para fechar...
pause
