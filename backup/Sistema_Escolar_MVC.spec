# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_mvc.py'],
    pathex=[],
    binaries=[],
    datas=[('icon/', 'icon/'), ('retangulooval.png', '.'), ('ante.png', '.'), ('capa_documento.png', '.'), ('Daco_5738580.png', '.'), ('logopaco1.png', '.'), ('logopacobranco.png', '.'), ('logosemed.png', '.'), ('logosemed1.png', '.'), ('pacologo.png', '.'), ('rodapepaco.png', '.'), ('logopaco.png', '.'), ('arquivo.png', '.'), ('MODELO CERTIFICADO 2024.pdf', '.'), ('CERTIFICADO form 2024.pdf', '.'), ('Elika Marcelly Leite Rabelo 9º Ano A.pdf', '.'), ('relatorio_frequencia.pdf', '.'), ('texto_vertical.pdf', '.'), ('MODELO CRACHA.pdf', '.'), ('João Henrique Ferreira de Assunção 9º Ano .pdf', '.'), ('Alexandre Bastos Pinheiro 9º Ano .pdf', '.'), ('calendário.pdf', '.'), ('Diploma_9º_ANO/', 'Diploma_9º_ANO/'), ('Diploma_9º_ANO versão UEB/', 'Diploma_9º_ANO versão UEB/'), ('backup_redeescola.sql', '.'), ('consulta_corpo_docente.sql', '.')],
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
    name='Sistema_Escolar_MVC',
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
