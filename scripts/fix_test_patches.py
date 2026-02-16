"""Script para corrigir mecanicamente paths de @patch nos testes."""
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

files = [
    'tests/test_services.py',
    'tests/test_transicao_ano_letivo.py',
    'tests/test_integration/test_matricula_flow.py',
    'tests/test_integration/test_services_sprint8.py',
    'tests/test_services/test_aluno_service.py',
    'tests/test_services/test_boletim_service.py',
    'tests/test_services/test_serie_service.py',
    'tests/test_services/test_turma_service.py',
    'tests/test_ui/test_actions.py',
    'tests/test_ui/test_app.py',
    'tests/test_ui/test_menu.py',
    'tests/test_ui/test_table.py',
]

total_changes = 0
for rel_path in files:
    fpath = os.path.join(ROOT, rel_path)
    if not os.path.exists(fpath):
        print(f"NOT FOUND: {rel_path}")
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    # Fix patch paths in quotes: 'services.X' -> 'src.services.X'
    # Match 'services. or "services. but NOT 'src.services.
    content = re.sub(r"""(['"])services\.""", r'\1src.services.', content)

    # Fix patch paths: 'ui.X' -> 'src.ui.X'
    content = re.sub(r"""(['"])ui\.""", r'\1src.ui.', content)

    # Fix patch paths: 'models.X' -> 'src.models.X'
    content = re.sub(r"""(['"])models\.""", r'\1src.models.', content)

    # Double src fix: 'src.src.X' -> 'src.X'
    content = content.replace('src.src.', 'src.')

    # Fix imports: from services import X -> from src.services import X
    content = re.sub(r'^from services import ', 'from src.services import ', content, flags=re.MULTILINE)
    content = re.sub(r'^from services\.', 'from src.services.', content, flags=re.MULTILINE)

    # Fix imports: from ui.X import -> from src.ui.X import
    content = re.sub(r'^from ui\.', 'from src.ui.', content, flags=re.MULTILINE)
    content = re.sub(r'^from ui import ', 'from src.ui import ', content, flags=re.MULTILINE)

    # Fix imports: from models.X -> from src.models.X
    content = re.sub(r'^from models\.', 'from src.models.', content, flags=re.MULTILINE)
    content = re.sub(r'^from models import ', 'from src.models import ', content, flags=re.MULTILINE)

    # Fix transicao import
    content = content.replace(
        'from transicao_ano_letivo import',
        'from src.interfaces.transicao_ano_letivo import'
    )

    # Fix InterfaceCadastro paths in patches
    content = content.replace(
        "'InterfaceCadastroAluno.InterfaceCadastroAluno'",
        "'src.interfaces.cadastro_aluno.InterfaceCadastroAluno'"
    )
    content = content.replace(
        "'InterfaceCadastroFuncionario.InterfaceCadastroFuncionario'",
        "'src.interfaces.cadastro_funcionario.InterfaceCadastroFuncionario'"
    )

    if content != original:
        orig_lines = original.split('\n')
        new_lines = content.split('\n')
        changes = sum(1 for a, b in zip(orig_lines, new_lines) if a != b)
        total_changes += changes
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'FIXED: {rel_path} ({changes} lines changed)')
    else:
        print(f'NO CHANGE: {rel_path}')

print(f'\nTotal lines changed: {total_changes}')
