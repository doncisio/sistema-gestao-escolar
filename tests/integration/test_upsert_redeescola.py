import os
import time
import pytest
from src.utils.horarios_persistence import upsert_horarios
from src.core.conexao import conectar_bd


pytestmark = pytest.mark.integration


def test_upsert_redeescola_roundtrip():
    # Requer variáveis de ambiente para apontar para redeescola
    required = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        pytest.skip(f"Variáveis de ambiente faltando: {missing}")

    conn = conectar_bd()
    assert conn is not None, "Não foi possível obter conexão com redeescola"

    cursor = conn.cursor()
    # Usar turma_id temporário (provavelmente não conflita)
    turma_id = 999999
    unique_val = f"INTEGRATION_TEST_{int(time.time())}"

    dados = [
        {
            'turma_id': turma_id,
            'dia': 'Segunda',
            'horario': '07:10-08:00',
            'valor': unique_val,
            'disciplina_id': None,
            'professor_id': None,
        }
    ]

    try:
        count = upsert_horarios(dados)
        assert count == 1

        # Verificar que a linha foi inserida
        cursor.execute("SELECT COUNT(*) FROM horarios_importados WHERE turma_id=%s AND valor=%s", (turma_id, unique_val))
        res = cursor.fetchone()
        assert res is not None
        assert res[0] >= 1

    finally:
        # Remover as linhas criadas pelo teste
        try:
            cursor.execute("DELETE FROM horarios_importados WHERE turma_id=%s AND valor=%s", (turma_id, unique_val))
            conn.commit()
        except Exception:
            pass
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
