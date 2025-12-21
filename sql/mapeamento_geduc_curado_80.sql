
-- Curadoria automática: mapeamentos com similaridade >= 80%
-- Gerado por scripts/curar_mapeamento_geduc.py

CREATE TABLE IF NOT EXISTS mapeamento_geduc (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tipo ENUM('escola', 'disciplina', 'curso', 'curriculo', 'serie', 'turno') NOT NULL,
    id_local INT NOT NULL,
    nome_local VARCHAR(255),
    id_geduc INT NOT NULL,
    nome_geduc VARCHAR(255),
    similaridade VARCHAR(10),
    verificado BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserts automáticos (escola)
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 60, 'Escola Municipal Profª Nadir Nascimento Moraes', 1384, 'EM PROFª NADIR NASCIMENTO MORAES', '82.1%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 7, 'UEB Bandeira Tribuzzi', 1326, 'EM BANDEIRA TRIBUZZI', '92.7%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 59, 'UEB Criança Feliz', 1331, 'EM CRIANCA FELIZ', '90.9%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 75, 'UEB Lêda Tajra', 1359, 'EM LEDA TAJRA', '88.9%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 12, 'UEB Lima Verde', 1361, 'EM LIMA VERDE', '88.9%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 45, 'UEB Mickey Mouse', 1365, 'EM MICKEY MOUSE', '90.3%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 11, 'UEB Padre Maurice Lacroix', 1373, 'EM PADRE MAURICE LACROIX', '93.9%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 6, 'UEB Padre Maurício', 1374, 'EM PADRE MAURICIO', '91.4%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 26, 'UEB Padre Maurício', 1374, 'EM PADRE MAURICIO', '91.4%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 30, 'UEB Pão da Vida', 1376, 'EM PAO DA VIDA', '89.7%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 99, 'UEB Poeta Gonçalves Dias', 1379, 'EM POETA GONÇALVES DIAS', '93.6%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 89, 'UEB Poeta Gonçalves Dias - CAIC', 1379, 'EM POETA GONÇALVES DIAS', '81.5%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 28, 'UEB Profª Maria de Lourdes Carvalho Silva', 1386, 'EM PROFª MARIA DE LOURDES CARVALHO SILVA', '96.3%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 3, 'UEB Profª Nadir Nascimento Moraes', 1384, 'EM PROFª NADIR NASCIMENTO MORAES', '95.4%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 4, 'UEB Profº José Maria Ramos Martins', 1382, 'EM PROF. JOSE MARIA RAMOS MARTINS', '92.5%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 76, 'UEB Profº José Maria Ramos Martins', 1382, 'EM PROF. JOSE MARIA RAMOS MARTINS', '92.5%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 141, 'UEB Raio de Luz', 1387, 'EM RAIO DE LUZ', '89.7%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 56, 'UEB Tia Dalva', 1355, 'EM TIA DALVA', '88.0%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 88, 'UEB Tia Marly', 1351, 'EM TIA MARLY', '88.0%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 2, 'UEB Vereador José Ribamar Coelho', 1348, 'EM VER. JOSE RIBAMAR COELHO', '84.7%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 8, 'UEB Vereador Raimundo Romualdo', 1350, 'EM VER. RAIMUNDO ROMUALDO', '83.6%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 156, 'UEB Vila São José', 1345, 'EM VILA SAO JOSE', '90.9%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 32, 'UEB Vovó Filuca', 1344, 'EM VOVO FILUCA', '89.7%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 157, 'UEB Vovô João', 1343, 'EM VOVO JOAO', '88.0%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 34, 'UEBI Alana Ludmila', 1341, 'EMI ALANA LUDMILA', '91.4%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 77, 'UI Ministro Henrique de La Roque', 1366, 'EM MIN. HENRIQUE DE LA ROQUE', '83.3%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 13, 'UI Profª Nadir Nascimento Moraes', 1384, 'EM PROFª NADIR NASCIMENTO MORAES', '93.8%');
INSERT INTO mapeamento_geduc (tipo, id_local, nome_local, id_geduc, nome_geduc, similaridade) VALUES ('escola', 160, 'UI Profº José Maria Ramos Martins', 1382, 'EM PROF. JOSE MARIA RAMOS MARTINS', '90.9%');
