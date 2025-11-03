# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('*.png', '.'), ('*.jpg', '.'), ('logopaco.png', '.'), ('icon/learning.png', 'icon'), ('icon/book.png', 'icon'), ('icon/left.png', 'icon'), ('icon/plus.png', 'icon'), ('icon/video-conference.png', 'icon'), ('icon/history.png', 'icon'), ('icon/settings.png', 'icon'), ('icon\\learning.png', 'icon'), ('icon\\video-conference.png', 'icon'), ('icon\\diskette.png', 'icon'), ('icon\\plus.png', 'icon'), ('icon\\trash.png', 'icon'), ('icon\\update.png', 'icon'), ('icon\\left.png', 'icon'), ('icon\\casa.png', 'icon'), ('icon\\notebook.png', 'icon'), ('icon\\book.png', 'icon'), ('icon\\settings.png', 'icon'), ('icon\\history.png', 'icon'), ('arquivo.png', '.'), ('main.py', '.'), ('aluno.py', '.'), ('Ata_1a5ano.py', '.'), ('atualizadisciplinaCH.py', '.'), ('boletim.py', '.'), ('conexao.py', '.'), ('ConselhodeClasseVazio.py', '.'), ('extrairdados.py', '.'), ('Funcionario.py', '.'), ('geador_solicitacao.py', '.'), ('gerador_solicitacao.py', '.'), ('Gerar_Declaracao_Aluno (1).py', '.'), ('Gerar_Declaracao_Aluno.py', '.'), ('Gerar_Declaracao_Aluno2.py', '.'), ('gerarPDF.py', '.'), ('historico_escolar.py', '.'), ('inserir_reponsavel.py', '.'), ('inserir1a5ano.py', '.'), ('inserir6a9ano.py', '.'), ('inserirfaltas.py', '.'), ('inserirmediaconceito.py', '.'), ('interface_notas_historico.py', '.'), ('Lista_atualizada.py', '.'), ('Lista_notas.py', '.'), ('main_backup.py', '.'), ('NotaAta.py', '.'), ('pastagoogle.py', '.'), ('renomearplanilhas.py', '.'), ('Seguranca.py', '.'), ('teste.py', '.'), ('transferencia.py', '.'), ('inserirtelefones.py', '.'), ('Ata_6a9ano.py', '.'), ('diploma_9ano.py', '.'), ('teste3.py', '.'), ('inserir_no_historico_escolar.py', '.'), ('diploma.py', '.'), ('lista_frequencia.py', '.'), ('biblio_editor.py', '.'), ('Lista_livros_recebidos.py', '.'), ('Lista_fardamentos_recebidos.py', '.'), ('Lista_reuniao.py', '.'), ('gerar_cracha.py', '.'), ('inserirfuncionarios.py', '.'), ('teste2.py', '.'), ('EditorAluno.py', '.'), ('interface_historico_escolar.py', '.'), ('integrar_historico_escolar.py', '.'), ('interface_administrativa.py', '.'), ('editar_aluno.py', '.'), ('InterfaceCadastroAluno.py', '.'), ('interface_editar_aluno.py', '.'), ('setup.py', '.'), ('verificar_imagens.py', '.'), ('corrigir_caminhos.py', '.'), ('criar_executavel.py', '.'), ('corrigir_problemas_imagens.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Sistema_Escolar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon\\learning.png'],
)
