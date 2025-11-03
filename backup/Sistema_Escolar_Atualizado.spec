# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('retangulooval.png', '.'), ('ante.png', '.'), ('capa_documento.png', '.'), ('Daco_5738580.png', '.'), ('logopaco1.png', '.'), ('logopacobranco.png', '.'), ('logosemed.png', '.'), ('logosemed1.png', '.'), ('pacologo.png', '.'), ('rodapepaco.png', '.'), ('logopaco.png', '.'), ('arquivo.png', '.'), ('logopaco.jpg', '.'), ('icon/learning.png', 'icon'), ('icon/video-conference.png', 'icon'), ('icon/diskette.png', 'icon'), ('icon/plus.png', 'icon'), ('icon/trash.png', 'icon'), ('icon/update.png', 'icon'), ('icon/left.png', 'icon'), ('icon/casa.png', 'icon'), ('icon/notebook.png', 'icon'), ('icon/book.png', 'icon'), ('icon/settings.png', 'icon'), ('icon/history.png', 'icon'), ('main.py', '.'), ('aluno.py', '.'), ('Ata_1a5ano.py', '.'), ('atualizadisciplinaCH.py', '.'), ('boletim.py', '.'), ('conexao.py', '.'), ('ConselhodeClasseVazio.py', '.'), ('extrairdados.py', '.'), ('Funcionario.py', '.'), ('geador_solicitacao.py', '.'), ('gerador_solicitacao.py', '.'), ('Gerar_Declaracao_Aluno.py', '.'), ('gerarPDF.py', '.'), ('historico_escolar.py', '.'), ('inserir_reponsavel.py', '.'), ('inserir1a5ano.py', '.'), ('inserir6a9ano.py', '.'), ('inserirfaltas.py', '.'), ('inserirmediaconceito.py', '.'), ('interface_notas_historico.py', '.'), ('Lista_atualizada.py', '.'), ('Lista_notas.py', '.'), ('main_backup.py', '.'), ('NotaAta.py', '.'), ('pastagoogle.py', '.'), ('renomearplanilhas.py', '.'), ('Seguranca.py', '.'), ('gerar_tabela_notas.py', '.'), ('transferencia.py', '.'), ('inserirtelefones.py', '.'), ('Ata_6a9ano.py', '.'), ('diploma_9ano.py', '.'), ('teste3.py', '.'), ('inserir_no_historico_escolar.py', '.'), ('diploma.py', '.'), ('lista_frequencia.py', '.'), ('biblio_editor.py', '.'), ('Lista_livros_recebidos.py', '.'), ('Lista_fardamentos_recebidos.py', '.'), ('Lista_reuniao.py', '.'), ('gerar_cracha.py', '.'), ('inserirfuncionarios.py', '.'), ('gerar_tabela_frequencia.py', '.'), ('interface_historico_escolar.py', '.'), ('integrar_historico_escolar.py', '.'), ('interface_administrativa.py', '.'), ('InterfaceCadastroAluno.py', '.'), ('setup.py', '.'), ('verificar_imagens.py', '.'), ('corrigir_caminhos.py', '.'), ('criar_executavel.py', '.'), ('corrigir_problemas_imagens.py', '.'), ('verificar_mysql.py', '.'), ('launcher.py', '.'), ('movimentomensal.py', '.'), ('teste_conexao.py', '.'), ('teste_lista_alunos.py', '.'), ('associar_funcionario_admin.py', '.'), ('associar_admin_sql.py', '.'), ('ler_calendario.py', '.'), ('adicionar_eventos_calendario.py', '.'), ('check_count.py', '.'), ('check_alunos_controller.py', '.'), ('fix_frequencia_aluno_view.py', '.'), ('comparar_frequencia_digital.py', '.'), ('comparar_lista_atualizada.py', '.'), ('comparar_ambos.py', '.'), ('verificar_matriculas_duplicadas.py', '.'), ('verificar_filtros.py', '.'), ('gerar_documentos.py', '.'), ('gerar_lista_reuniao.py', '.'), ('gerar_lista_alunos.py', '.'), ('utils_imagem.py', '.'), ('InterfaceEdicaoAluno.py', '.'), ('InterfaceCadastroFuncionario.py', '.'), ('InterfaceEdicaoFuncionario.py', '.'), ('InterfaceCadastroEdicaoNotas.py', '.'), ('resource_path.py', '.')],
    hiddenimports=['Ata_1a5ano', 'Funcionario', 'Gerar_Declaracao_Aluno', 'InterfaceCadastroAluno', 'InterfaceCadastroEdicaoNotas', 'InterfaceCadastroFuncionario', 'InterfaceEdicaoAluno', 'InterfaceEdicaoFuncionario', 'Lista_atualizada', 'Lista_notas', 'Lista_reuniao', 'NotaAta', 'PyInstaller.__main__', 'PyPDF2', 'PyPDF2.generic', 'Seguranca', 'aluno', 'biblio_editor', 'boletim', 'conexao', 'controllers.aluno_controller', 'controllers.evento_academico_controller', 'controllers.frequencia_controller', 'ctypes', 'dotenv', 'editar_aluno', 'extrairdados', 'gerarPDF', 'gerar_documentos', 'gerar_lista_alunos', 'gerar_lista_reuniao', 'gerar_tabela_frequencia', 'gerar_tabela_notas', 'google.oauth2', 'googleapiclient.discovery', 'historico_escolar', 'importlib', 'inserir_no_historico_escolar', 'integrar_historico_escolar', 'interface_administrativa', 'interface_historico_escolar', 'io', 'lista_frequencia', 'logging', 'main', 'movimentomensal', 'mysql', 'mysql.connector', 'openpyxl', 'pathlib', 'platform', 'pymysql', 'reportlab.lib', 'reportlab.lib.colors', 'reportlab.lib.enums', 'reportlab.lib.pagesizes', 'reportlab.lib.styles', 'reportlab.lib.units', 'reportlab.pdfgen', 'reportlab.platypus', 'resource_path', 'tempfile', 'tkcalendar', 'tkinter.ttk', 'traceback', 'transferencia', 'urllib', 'utils.config', 'utils.db_config', 'utils.db_utils', 'utils.error_handler', 'views.aluno_view', 'weakref'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Sistema_Escolar_Atualizado',
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
    icon='icon/learning.png',
)
