import io, os, sys
sys.path.insert(0, r'C:\gestao')
from gerarPDF import salvar

b = io.BytesIO()
b.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
# garantir inicio do buffer
b.seek(0)
# criar pasta
os.makedirs('9 Ano', exist_ok=True)
# chamar salvar
salvar(b, 'TESTE_USUARIO')
print('salvar chamado com sucesso')
