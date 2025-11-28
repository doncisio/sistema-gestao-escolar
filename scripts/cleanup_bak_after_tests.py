#!/usr/bin/env python3
"""Cleanup .bak files after tests.

Usage:
    python ./scripts/cleanup_bak_after_tests.py [--dry-run] [--root PATH]

Behavior:
- Runs `pytest -q` in the repository root (or `--root` if provided).
- If pytest returns success (exit code 0), finds and deletes all `*.bak` files under the root.
- With `--dry-run` it only prints which files would be deleted.

This is intended to be run after applying the automated changes and verifying tests.
"""
import argparse
import os
import subprocess
import sys


def find_bak_files(root):
    bak_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith('.bak'):
                bak_files.append(os.path.join(dirpath, fn))
    return bak_files


def run_pytest(root):
    print('Running pytest -q in:', root)
    # Use the same python executable to run pytest module if available
    proc = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=root)
    return proc.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='Run pytest and delete .bak files if tests pass')
    parser.add_argument('--dry-run', action='store_true', help='Only list .bak files that would be removed')
    parser.add_argument('--root', default=os.getcwd(), help='Root path to search for .bak files (default: cwd)')
    args = parser.parse_args()

    root = os.path.abspath(args.root)

    ok = run_pytest(root)
    if not ok:
        print('\nPytest failed — not deleting any .bak files.')
        sys.exit(1)

    bak_files = find_bak_files(root)
    if not bak_files:
        print('\nNo .bak files found under', root)
        return

    if args.dry_run:
        print('\nDry run — would delete the following .bak files:')
        for p in bak_files:
            print('  ', p)
        print('\nTotal:', len(bak_files))
        return

    print('\nDeleting .bak files:')
    deleted = 0
    for p in bak_files:
        try:
            os.remove(p)
            print('  Deleted', p)
            deleted += 1
        except Exception as e:
            print('  Failed to delete', p, '-', e)
    print('\nDeleted', deleted, 'of', len(bak_files), 'files.')


if __name__ == '__main__':
    main()
