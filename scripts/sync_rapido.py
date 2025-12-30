#!/usr/bin/env python3
"""Sincronização rápida cross-platform.

Comportamento:
- Faz `git fetch --all`.
- Se houver commits no remoto, tenta atualizar com `git pull --rebase`.
- Caso existam mudanças locais não comitadas, faz `git stash push -u` antes do pull e `git stash pop` depois.
- Se houver mudanças locais (após aplicar stash) ou novos arquivos, adiciona e comita com mensagem `Auto-sync: <date>` e faz push.

Saída textual é pensada para ser mostrada ao usuário.
"""
import subprocess
import os
import sys
from datetime import datetime


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace')


def main():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # obter branch atual
    p = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
    branch = p.stdout.strip() if p.returncode == 0 else 'main'

    print(f"Repo: {repo_dir}  Branch: {branch}")

    print("Fetching...")
    fetch = run(["git", "fetch", "--all"], cwd=repo_dir)
    if fetch.returncode != 0:
        print("Erro no git fetch:")
        print(fetch.stderr or fetch.stdout)
        return 2

    revlist = run(["git", "rev-list", "--count", f"HEAD..origin/{branch}"], cwd=repo_dir)
    if revlist.returncode != 0:
        print("Erro ao verificar diferenças com remoto:")
        print(revlist.stderr or revlist.stdout)
        return 3

    try:
        count = int(revlist.stdout.strip() or '0')
    except Exception:
        count = 0

    if count == 0:
        print("Já está atualizado.")
        # Ainda sincronizar commits locais se houver
    else:
        print(f"Encontrado(s) {count} commit(s) no remoto. Atualizando...")

    # Detectar mudanças locais
    status = run(["git", "status", "--porcelain"], cwd=repo_dir)
    dirty = bool(status.stdout.strip())
    stashed = False
    stash_ref = None
    if dirty:
        print("Existem alterações locais não comitadas. Fazendo stash...")
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        stash = run(["git", "stash", "push", "-u", "-m", f"autostash-{ts}"], cwd=repo_dir)
        if stash.returncode != 0:
            print("Falha ao criar stash:")
            print(stash.stderr or stash.stdout)
            return 4
        stashed = True
        # obter referência do stash para aplicar depois
        stash_ref = 'stash@{0}'

    # Se houver commits remotos, puxar
    if count > 0:
        pull = run(["git", "pull", "--rebase", "origin", branch], cwd=repo_dir)
        if pull.returncode != 0:
            print("Falha ao puxar alterações:")
            print(pull.stderr or pull.stdout)
            # tentar reverter stash se criado
            if stashed:
                print("Tentando aplicar o stash de volta...")
                pop = run(["git", "stash", "pop"], cwd=repo_dir)
                print(pop.stdout or pop.stderr)
            return 5

    # Se stashed, tentar aplicar de volta
    if stashed:
        print("Aplicando stash de volta...")
        pop = run(["git", "stash", "pop"], cwd=repo_dir)
        if pop.returncode != 0:
            print("Conflito/erro ao aplicar stash. Verifique manualmente:")
            print(pop.stderr or pop.stdout)
            return 6

    # Após atualização, verificar se há alterações a commitar
    status2 = run(["git", "status", "--porcelain"], cwd=repo_dir)
    if status2.stdout.strip():
        print("Existem alterações a commitar. Commit automático de sincronização...")
        add = run(["git", "add", "."], cwd=repo_dir)
        if add.returncode != 0:
            print("Falha ao adicionar arquivos:")
            print(add.stderr or add.stdout)
            return 7
        msg = f"Auto-sync: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        commit = run(["git", "commit", "-m", msg], cwd=repo_dir)
        # Se nada comitado, ok
        if commit.returncode != 0 and 'nothing to commit' not in (commit.stdout + commit.stderr):
            print("Falha ao commitar:")
            print(commit.stderr or commit.stdout)
            return 8
        push = run(["git", "push", "origin", branch], cwd=repo_dir)
        if push.returncode != 0:
            print("Falha ao enviar para remoto:")
            print(push.stderr or push.stdout)
            return 9

    print("Sincronização concluída com sucesso.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
