import os, zipfile
p = r'C:\gestao\pendencias_por_bimestre.xlsx'
print('Exists:', os.path.exists(p))
print('Is zipfile (valid xlsx):', zipfile.is_zipfile(p))

import glob
files = glob.glob(r'C:\gestao\pendencias_por_bimestre*.xlsx')
print('\nMatches:')
for f in files:
    print(' -', f)
