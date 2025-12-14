"""
Services do módulo de Transporte Escolar.

Contém a lógica de negócio e operações CRUD para:
- Veículos
- Rotas
- Pontos de parada
- Alunos usuários de transporte
- Ocorrências
"""

import logging
from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any

from .models import (
    Veiculo, Rota, PontoParada, AlunoTransporte, 
    OcorrenciaTransporte, EstatisticasTransporte,
    TipoVeiculo, StatusVeiculo, Turno, TipoOcorrencia
)

logger = logging.getLogger(__name__)


class TransporteService:
    """
    Serviço para gerenciamento do transporte escolar.
    
    Fornece métodos para CRUD de veículos, rotas, pontos,
    alunos usuários e ocorrências, além de estatísticas.
    """

    def __init__(self, conexao):
        """
        Inicializa o serviço de transporte.
        
        Args:
            conexao: Objeto de conexão com o banco de dados
        """
        self.conexao = conexao
        self._garantir_tabelas()

    def _garantir_tabelas(self):
        """Garante que as tabelas do módulo existam."""
        try:
            self._criar_tabelas_se_nao_existem()
        except Exception as e:
            logger.error(f"Erro ao criar tabelas de transporte: {e}")

    def _criar_tabelas_se_nao_existem(self):
        """Cria as tabelas do módulo de transporte se não existirem."""
        cursor = self.conexao.cursor()
        
        # Tabela de veículos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transporte_veiculos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                placa VARCHAR(10) NOT NULL UNIQUE,
                tipo ENUM('Ônibus', 'Van', 'Micro-ônibus') NOT NULL,
                capacidade INT NOT NULL,
                ano_fabricacao YEAR,
                motorista_id BIGINT UNSIGNED,
                status ENUM('Ativo', 'Manutenção', 'Inativo') DEFAULT 'Ativo',
                km_atual DECIMAL(10,1) DEFAULT 0,
                ultima_revisao DATE,
                proxima_revisao DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_motorista (motorista_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Tabela de rotas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transporte_rotas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                turno ENUM('Matutino', 'Vespertino', 'Noturno', 'Integral') NOT NULL,
                veiculo_id INT,
                km_total DECIMAL(10,2),
                tempo_estimado_min INT,
                horario_saida TIME,
                horario_chegada TIME,
                ativa BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_turno (turno),
                INDEX idx_veiculo (veiculo_id),
                INDEX idx_ativa (ativa),
                FOREIGN KEY (veiculo_id) REFERENCES transporte_veiculos(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Tabela de pontos de parada
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transporte_pontos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                rota_id INT NOT NULL,
                ordem INT NOT NULL,
                descricao VARCHAR(200) NOT NULL,
                endereco VARCHAR(255),
                latitude DECIMAL(10,8),
                longitude DECIMAL(11,8),
                horario_previsto TIME,
                UNIQUE KEY uk_rota_ordem (rota_id, ordem),
                INDEX idx_rota (rota_id),
                FOREIGN KEY (rota_id) REFERENCES transporte_rotas(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Tabela de alunos usuários de transporte
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transporte_alunos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                aluno_id BIGINT UNSIGNED NOT NULL,
                rota_id INT NOT NULL,
                ponto_embarque_id INT,
                ponto_desembarque_id INT,
                ano_letivo_id INT NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_aluno_ano (aluno_id, ano_letivo_id),
                INDEX idx_rota (rota_id),
                INDEX idx_aluno (aluno_id),
                INDEX idx_ano_letivo (ano_letivo_id),
                FOREIGN KEY (rota_id) REFERENCES transporte_rotas(id) ON DELETE CASCADE,
                FOREIGN KEY (ponto_embarque_id) REFERENCES transporte_pontos(id) ON DELETE SET NULL,
                FOREIGN KEY (ponto_desembarque_id) REFERENCES transporte_pontos(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Tabela de ocorrências
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transporte_ocorrencias (
                id INT AUTO_INCREMENT PRIMARY KEY,
                veiculo_id INT,
                rota_id INT,
                tipo ENUM('Atraso', 'Acidente', 'Manutenção', 'Outro') NOT NULL,
                descricao TEXT NOT NULL,
                data_ocorrencia DATETIME NOT NULL,
                resolvido BOOLEAN DEFAULT FALSE,
                observacoes TEXT,
                registrado_por BIGINT UNSIGNED,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_tipo (tipo),
                INDEX idx_data (data_ocorrencia),
                INDEX idx_resolvido (resolvido),
                FOREIGN KEY (veiculo_id) REFERENCES transporte_veiculos(id) ON DELETE SET NULL,
                FOREIGN KEY (rota_id) REFERENCES transporte_rotas(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        self.conexao.commit()
        cursor.close()
        logger.info("Tabelas de transporte verificadas/criadas com sucesso")

    # ==================== VEÍCULOS ====================

    def listar_veiculos(self, status: Optional[StatusVeiculo] = None) -> List[Veiculo]:
        """
        Lista todos os veículos, opcionalmente filtrados por status.
        
        Args:
            status: Filtrar por status específico
            
        Returns:
            Lista de veículos
        """
        cursor = self.conexao.cursor(dictionary=True)
        
        query = """
            SELECT v.*, f.nome as motorista_nome
            FROM transporte_veiculos v
            LEFT JOIN Funcionarios f ON v.motorista_id = f.id
        """
        params = []
        
        if status:
            query += " WHERE v.status = %s"
            params.append(status.value)
        
        query += " ORDER BY v.placa"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        
        return [self._row_to_veiculo(row) for row in rows]

    def buscar_veiculo(self, veiculo_id: int) -> Optional[Veiculo]:
        """
        Busca um veículo por ID.
        
        Args:
            veiculo_id: ID do veículo
            
        Returns:
            Veículo encontrado ou None
        """
        cursor = self.conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT v.*, f.nome as motorista_nome
            FROM transporte_veiculos v
            LEFT JOIN Funcionarios f ON v.motorista_id = f.id
            WHERE v.id = %s
        """, (veiculo_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            return self._row_to_veiculo(row)
        return None

    def criar_veiculo(self, veiculo: Veiculo) -> int:
        """
        Cria um novo veículo.
        
        Args:
            veiculo: Dados do veículo
            
        Returns:
            ID do veículo criado
        """
        cursor = self.conexao.cursor()
        cursor.execute("""
            INSERT INTO transporte_veiculos 
            (placa, tipo, capacidade, ano_fabricacao, motorista_id, 
             status, km_atual, ultima_revisao, proxima_revisao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            veiculo.placa.upper(),
            veiculo.tipo.value,
            veiculo.capacidade,
            veiculo.ano_fabricacao,
            veiculo.motorista_id,
            veiculo.status.value,
            float(veiculo.km_atual),
            veiculo.ultima_revisao,
            veiculo.proxima_revisao
        ))
        self.conexao.commit()
        veiculo_id = cursor.lastrowid
        cursor.close()
        
        logger.info(f"Veículo criado: {veiculo.placa} (ID: {veiculo_id})")
        return veiculo_id

    def atualizar_veiculo(self, veiculo: Veiculo) -> bool:
        """
        Atualiza um veículo existente.
        
        Args:
            veiculo: Dados do veículo com ID
            
        Returns:
            True se atualizado com sucesso
        """
        if not veiculo.id:
            raise ValueError("ID do veículo é obrigatório para atualização")
        
        cursor = self.conexao.cursor()
        cursor.execute("""
            UPDATE transporte_veiculos SET
                placa = %s,
                tipo = %s,
                capacidade = %s,
                ano_fabricacao = %s,
                motorista_id = %s,
                status = %s,
                km_atual = %s,
                ultima_revisao = %s,
                proxima_revisao = %s
            WHERE id = %s
        """, (
            veiculo.placa.upper(),
            veiculo.tipo.value,
            veiculo.capacidade,
            veiculo.ano_fabricacao,
            veiculo.motorista_id,
            veiculo.status.value,
            float(veiculo.km_atual),
            veiculo.ultima_revisao,
            veiculo.proxima_revisao,
            veiculo.id
        ))
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        
        logger.info(f"Veículo atualizado: {veiculo.placa} (ID: {veiculo.id})")
        return affected > 0

    def excluir_veiculo(self, veiculo_id: int) -> bool:
        """
        Exclui um veículo.
        
        Args:
            veiculo_id: ID do veículo
            
        Returns:
            True se excluído com sucesso
        """
        cursor = self.conexao.cursor()
        cursor.execute("DELETE FROM transporte_veiculos WHERE id = %s", (veiculo_id,))
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        
        if affected > 0:
            logger.info(f"Veículo excluído: ID {veiculo_id}")
        return affected > 0

    def atualizar_km_veiculo(self, veiculo_id: int, km_atual: Decimal) -> bool:
        """
        Atualiza a quilometragem de um veículo.
        
        Args:
            veiculo_id: ID do veículo
            km_atual: Nova quilometragem
            
        Returns:
            True se atualizado com sucesso
        """
        cursor = self.conexao.cursor()
        cursor.execute("""
            UPDATE transporte_veiculos SET km_atual = %s WHERE id = %s
        """, (float(km_atual), veiculo_id))
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0

    def _row_to_veiculo(self, row: Dict) -> Veiculo:
        """Converte uma linha do banco para objeto Veiculo."""
        return Veiculo(
            id=row['id'],
            placa=row['placa'],
            tipo=TipoVeiculo(row['tipo']),
            capacidade=row['capacidade'],
            ano_fabricacao=row.get('ano_fabricacao'),
            motorista_id=row.get('motorista_id'),
            motorista_nome=row.get('motorista_nome'),
            status=StatusVeiculo(row['status']),
            km_atual=Decimal(str(row.get('km_atual', 0))),
            ultima_revisao=row.get('ultima_revisao'),
            proxima_revisao=row.get('proxima_revisao'),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )

    # ==================== ROTAS ====================

    def listar_rotas(self, apenas_ativas: bool = False, turno: Optional[Turno] = None) -> List[Rota]:
        """
        Lista todas as rotas.
        
        Args:
            apenas_ativas: Se True, lista apenas rotas ativas
            turno: Filtrar por turno específico
            
        Returns:
            Lista de rotas
        """
        cursor = self.conexao.cursor(dictionary=True)
        
        query = """
            SELECT r.*, v.placa as veiculo_placa,
                   (SELECT COUNT(*) FROM transporte_alunos ta 
                    WHERE ta.rota_id = r.id AND ta.ativo = TRUE) as total_alunos
            FROM transporte_rotas r
            LEFT JOIN transporte_veiculos v ON r.veiculo_id = v.id
            WHERE 1=1
        """
        params = []
        
        if apenas_ativas:
            query += " AND r.ativa = TRUE"
        
        if turno:
            query += " AND r.turno = %s"
            params.append(turno.value)
        
        query += " ORDER BY r.turno, r.nome"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        
        return [self._row_to_rota(row) for row in rows]

    def buscar_rota(self, rota_id: int, com_pontos: bool = False) -> Optional[Rota]:
        """
        Busca uma rota por ID.
        
        Args:
            rota_id: ID da rota
            com_pontos: Se True, inclui os pontos de parada
            
        Returns:
            Rota encontrada ou None
        """
        cursor = self.conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT r.*, v.placa as veiculo_placa,
                   (SELECT COUNT(*) FROM transporte_alunos ta 
                    WHERE ta.rota_id = r.id AND ta.ativo = TRUE) as total_alunos
            FROM transporte_rotas r
            LEFT JOIN transporte_veiculos v ON r.veiculo_id = v.id
            WHERE r.id = %s
        """, (rota_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            return None
        
        rota = self._row_to_rota(row)
        
        if com_pontos:
            rota.pontos = self.listar_pontos_rota(rota_id)
        
        return rota

    def criar_rota(self, rota: Rota) -> int:
        """
        Cria uma nova rota.
        
        Args:
            rota: Dados da rota
            
        Returns:
            ID da rota criada
        """
        cursor = self.conexao.cursor()
        cursor.execute("""
            INSERT INTO transporte_rotas 
            (nome, turno, veiculo_id, km_total, tempo_estimado_min, 
             horario_saida, horario_chegada, ativa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            rota.nome,
            rota.turno.value,
            rota.veiculo_id,
            float(rota.km_total) if rota.km_total else None,
            rota.tempo_estimado_min,
            rota.horario_saida,
            rota.horario_chegada,
            rota.ativa
        ))
        self.conexao.commit()
        rota_id = cursor.lastrowid
        cursor.close()
        
        logger.info(f"Rota criada: {rota.nome} (ID: {rota_id})")
        return rota_id

    def atualizar_rota(self, rota: Rota) -> bool:
        """
        Atualiza uma rota existente.
        
        Args:
            rota: Dados da rota com ID
            
        Returns:
            True se atualizado com sucesso
        """
        if not rota.id:
            raise ValueError("ID da rota é obrigatório para atualização")
        
        cursor = self.conexao.cursor()
        cursor.execute("""
            UPDATE transporte_rotas SET
                nome = %s,
                turno = %s,
                veiculo_id = %s,
                km_total = %s,
                tempo_estimado_min = %s,
                horario_saida = %s,
                horario_chegada = %s,
                ativa = %s
            WHERE id = %s
        """, (
            rota.nome,
            rota.turno.value,
            rota.veiculo_id,
            float(rota.km_total) if rota.km_total else None,
            rota.tempo_estimado_min,
            rota.horario_saida,
            rota.horario_chegada,
            rota.ativa,
            rota.id
        ))
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        
        logger.info(f"Rota atualizada: {rota.nome} (ID: {rota.id})")
        return affected > 0

    def excluir_rota(self, rota_id: int) -> bool:
        """
        Exclui uma rota.
        
        Args:
            rota_id: ID da rota
            
        Returns:
            True se excluído com sucesso
        """
        cursor = self.conexao.cursor()
        cursor.execute("DELETE FROM transporte_rotas WHERE id = %s", (rota_id,))
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        
        if affected > 0:
            logger.info(f"Rota excluída: ID {rota_id}")
        return affected > 0

    def _row_to_rota(self, row: Dict) -> Rota:
        """Converte uma linha do banco para objeto Rota."""
        return Rota(
            id=row['id'],
            nome=row['nome'],
            turno=Turno(row['turno']),
            veiculo_id=row.get('veiculo_id'),
            veiculo_placa=row.get('veiculo_placa'),
            km_total=Decimal(str(row['km_total'])) if row.get('km_total') else None,
            tempo_estimado_min=row.get('tempo_estimado_min'),
            horario_saida=row.get('horario_saida'),
            horario_chegada=row.get('horario_chegada'),
            ativa=bool(row.get('ativa', True)),
            total_alunos=row.get('total_alunos', 0),
            created_at=row.get('created_at')
        )

    # ==================== PONTOS DE PARADA ====================

    def listar_pontos_rota(self, rota_id: int) -> List[PontoParada]:
        """
        Lista todos os pontos de parada de uma rota.
        
        Args:
            rota_id: ID da rota
            
        Returns:
            Lista de pontos ordenados
        """
        cursor = self.conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.*,
                   (SELECT COUNT(*) FROM transporte_alunos ta 
                    WHERE (ta.ponto_embarque_id = p.id OR ta.ponto_desembarque_id = p.id) 
                    AND ta.ativo = TRUE) as total_alunos
            FROM transporte_pontos p
            WHERE p.rota_id = %s
            ORDER BY p.ordem
        """, (rota_id,))
        rows = cursor.fetchall()
        cursor.close()
        
        return [self._row_to_ponto(row) for row in rows]

    def criar_ponto(self, ponto: PontoParada) -> int:
        """
        Cria um novo ponto de parada.
        
        Args:
            ponto: Dados do ponto
            
        Returns:
            ID do ponto criado
        """
        cursor = self.conexao.cursor()
        cursor.execute("""
            INSERT INTO transporte_pontos 
            (rota_id, ordem, descricao, endereco, latitude, longitude, horario_previsto)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            ponto.rota_id,
            ponto.ordem,
            ponto.descricao,
            ponto.endereco,
            float(ponto.latitude) if ponto.latitude else None,
            float(ponto.longitude) if ponto.longitude else None,
            ponto.horario_previsto
        ))
        self.conexao.commit()
        ponto_id = cursor.lastrowid
        cursor.close()
        
        logger.info(f"Ponto criado: {ponto.descricao} (ID: {ponto_id})")
        return ponto_id

    def atualizar_ponto(self, ponto: PontoParada) -> bool:
        """
        Atualiza um ponto de parada.
        
        Args:
            ponto: Dados do ponto com ID
            
        Returns:
            True se atualizado com sucesso
        """
        if not ponto.id:
            raise ValueError("ID do ponto é obrigatório para atualização")
        
        cursor = self.conexao.cursor()
        cursor.execute("""
            UPDATE transporte_pontos SET
                ordem = %s,
                descricao = %s,
                endereco = %s,
                latitude = %s,
                longitude = %s,
                horario_previsto = %s
            WHERE id = %s
        """, (
            ponto.ordem,
            ponto.descricao,
            ponto.endereco,
            float(ponto.latitude) if ponto.latitude else None,
            float(ponto.longitude) if ponto.longitude else None,
            ponto.horario_previsto,
            ponto.id
        ))
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0

    def excluir_ponto(self, ponto_id: int) -> bool:
        """
        Exclui um ponto de parada.
        
        Args:
            ponto_id: ID do ponto
            
        Returns:
            True se excluído com sucesso
        """
        cursor = self.conexao.cursor()
        cursor.execute("DELETE FROM transporte_pontos WHERE id = %s", (ponto_id,))
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0

    def reordenar_pontos(self, rota_id: int, nova_ordem: List[int]) -> bool:
        """
        Reordena os pontos de uma rota.
        
        Args:
            rota_id: ID da rota
            nova_ordem: Lista de IDs de pontos na nova ordem
            
        Returns:
            True se reordenado com sucesso
        """
        cursor = self.conexao.cursor()
        for ordem, ponto_id in enumerate(nova_ordem, 1):
            cursor.execute("""
                UPDATE transporte_pontos SET ordem = %s 
                WHERE id = %s AND rota_id = %s
            """, (ordem, ponto_id, rota_id))
        self.conexao.commit()
        cursor.close()
        return True

    def _row_to_ponto(self, row: Dict) -> PontoParada:
        """Converte uma linha do banco para objeto PontoParada."""
        return PontoParada(
            id=row['id'],
            rota_id=row['rota_id'],
            ordem=row['ordem'],
            descricao=row['descricao'],
            endereco=row.get('endereco'),
            latitude=Decimal(str(row['latitude'])) if row.get('latitude') else None,
            longitude=Decimal(str(row['longitude'])) if row.get('longitude') else None,
            horario_previsto=row.get('horario_previsto'),
            total_alunos=row.get('total_alunos', 0)
        )

    # ==================== ALUNOS USUÁRIOS ====================

    def listar_alunos_transporte(
        self, 
        rota_id: Optional[int] = None,
        ano_letivo_id: Optional[int] = None,
        apenas_ativos: bool = True
    ) -> List[AlunoTransporte]:
        """
        Lista alunos usuários de transporte.
        
        Args:
            rota_id: Filtrar por rota
            ano_letivo_id: Filtrar por ano letivo
            apenas_ativos: Se True, lista apenas vínculos ativos
            
        Returns:
            Lista de alunos com transporte
        """
        cursor = self.conexao.cursor(dictionary=True)
        
        query = """
            SELECT ta.*, 
                   a.nome as aluno_nome,
                   r.nome as rota_nome,
                   pe.descricao as ponto_embarque_desc,
                   pd.descricao as ponto_desembarque_desc,
                   s.nome as serie,
                   t.turma
            FROM transporte_alunos ta
            JOIN alunos a ON ta.aluno_id = a.id
            JOIN transporte_rotas r ON ta.rota_id = r.id
            LEFT JOIN transporte_pontos pe ON ta.ponto_embarque_id = pe.id
            LEFT JOIN transporte_pontos pd ON ta.ponto_desembarque_id = pd.id
            LEFT JOIN matriculas m ON a.id = m.aluno_id AND m.ano_letivo_id = ta.ano_letivo_id
            LEFT JOIN series s ON m.serie_id = s.id
            LEFT JOIN turmas t ON m.turma_id = t.id
            WHERE 1=1
        """
        params = []
        
        if apenas_ativos:
            query += " AND ta.ativo = TRUE"
        
        if rota_id:
            query += " AND ta.rota_id = %s"
            params.append(rota_id)
        
        if ano_letivo_id:
            query += " AND ta.ano_letivo_id = %s"
            params.append(ano_letivo_id)
        
        query += " ORDER BY a.nome"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        
        return [self._row_to_aluno_transporte(row) for row in rows]

    def vincular_aluno_transporte(self, aluno_transporte: AlunoTransporte) -> int:
        """
        Vincula um aluno ao transporte escolar.
        
        Args:
            aluno_transporte: Dados do vínculo
            
        Returns:
            ID do vínculo criado
        """
        cursor = self.conexao.cursor()
        cursor.execute("""
            INSERT INTO transporte_alunos 
            (aluno_id, rota_id, ponto_embarque_id, ponto_desembarque_id, ano_letivo_id, ativo)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                rota_id = VALUES(rota_id),
                ponto_embarque_id = VALUES(ponto_embarque_id),
                ponto_desembarque_id = VALUES(ponto_desembarque_id),
                ativo = VALUES(ativo)
        """, (
            aluno_transporte.aluno_id,
            aluno_transporte.rota_id,
            aluno_transporte.ponto_embarque_id,
            aluno_transporte.ponto_desembarque_id,
            aluno_transporte.ano_letivo_id,
            aluno_transporte.ativo
        ))
        self.conexao.commit()
        vinculo_id = cursor.lastrowid
        cursor.close()
        
        logger.info(f"Aluno vinculado ao transporte: aluno_id={aluno_transporte.aluno_id}, rota_id={aluno_transporte.rota_id}")
        return vinculo_id

    def desvincular_aluno_transporte(self, aluno_id: int, ano_letivo_id: int) -> bool:
        """
        Desvincula um aluno do transporte (desativa).
        
        Args:
            aluno_id: ID do aluno
            ano_letivo_id: ID do ano letivo
            
        Returns:
            True se desvinculado com sucesso
        """
        cursor = self.conexao.cursor()
        cursor.execute("""
            UPDATE transporte_alunos SET ativo = FALSE 
            WHERE aluno_id = %s AND ano_letivo_id = %s
        """, (aluno_id, ano_letivo_id))
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0

    def listar_alunos_por_ponto(self, ponto_id: int, ano_letivo_id: int) -> List[AlunoTransporte]:
        """
        Lista alunos que embarcam ou desembarcam em um ponto.
        
        Args:
            ponto_id: ID do ponto
            ano_letivo_id: ID do ano letivo
            
        Returns:
            Lista de alunos do ponto
        """
        cursor = self.conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT ta.*, 
                   a.nome as aluno_nome,
                   r.nome as rota_nome,
                   CASE 
                       WHEN ta.ponto_embarque_id = %s THEN 'Embarque'
                       ELSE 'Desembarque'
                   END as tipo_uso
            FROM transporte_alunos ta
            JOIN alunos a ON ta.aluno_id = a.id
            JOIN transporte_rotas r ON ta.rota_id = r.id
            WHERE (ta.ponto_embarque_id = %s OR ta.ponto_desembarque_id = %s)
              AND ta.ano_letivo_id = %s
              AND ta.ativo = TRUE
            ORDER BY a.nome
        """, (ponto_id, ponto_id, ponto_id, ano_letivo_id))
        rows = cursor.fetchall()
        cursor.close()
        
        return [self._row_to_aluno_transporte(row) for row in rows]

    def _row_to_aluno_transporte(self, row: Dict) -> AlunoTransporte:
        """Converte uma linha do banco para objeto AlunoTransporte."""
        return AlunoTransporte(
            id=row['id'],
            aluno_id=row['aluno_id'],
            aluno_nome=row.get('aluno_nome'),
            rota_id=row['rota_id'],
            rota_nome=row.get('rota_nome'),
            ponto_embarque_id=row.get('ponto_embarque_id'),
            ponto_embarque_desc=row.get('ponto_embarque_desc'),
            ponto_desembarque_id=row.get('ponto_desembarque_id'),
            ponto_desembarque_desc=row.get('ponto_desembarque_desc'),
            ano_letivo_id=row['ano_letivo_id'],
            ativo=bool(row.get('ativo', True)),
            serie=row.get('serie'),
            turma=row.get('turma'),
            created_at=row.get('created_at')
        )

    # ==================== OCORRÊNCIAS ====================

    def listar_ocorrencias(
        self,
        resolvido: Optional[bool] = None,
        tipo: Optional[TipoOcorrencia] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        limite: int = 100
    ) -> List[OcorrenciaTransporte]:
        """
        Lista ocorrências de transporte.
        
        Args:
            resolvido: Filtrar por status de resolução
            tipo: Filtrar por tipo
            data_inicio: Data inicial
            data_fim: Data final
            limite: Quantidade máxima de registros
            
        Returns:
            Lista de ocorrências
        """
        cursor = self.conexao.cursor(dictionary=True)
        
        query = """
            SELECT o.*, 
                   v.placa as veiculo_placa,
                   r.nome as rota_nome,
                   f.nome as registrado_por_nome
            FROM transporte_ocorrencias o
            LEFT JOIN transporte_veiculos v ON o.veiculo_id = v.id
            LEFT JOIN transporte_rotas r ON o.rota_id = r.id
            LEFT JOIN Funcionarios f ON o.registrado_por = f.id
            WHERE 1=1
        """
        params = []
        
        if resolvido is not None:
            query += " AND o.resolvido = %s"
            params.append(resolvido)
        
        if tipo:
            query += " AND o.tipo = %s"
            params.append(tipo.value)
        
        if data_inicio:
            query += " AND DATE(o.data_ocorrencia) >= %s"
            params.append(data_inicio)
        
        if data_fim:
            query += " AND DATE(o.data_ocorrencia) <= %s"
            params.append(data_fim)
        
        query += f" ORDER BY o.data_ocorrencia DESC LIMIT {limite}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        
        return [self._row_to_ocorrencia(row) for row in rows]

    def criar_ocorrencia(self, ocorrencia: OcorrenciaTransporte) -> int:
        """
        Registra uma nova ocorrência.
        
        Args:
            ocorrencia: Dados da ocorrência
            
        Returns:
            ID da ocorrência criada
        """
        cursor = self.conexao.cursor()
        cursor.execute("""
            INSERT INTO transporte_ocorrencias 
            (veiculo_id, rota_id, tipo, descricao, data_ocorrencia, 
             resolvido, observacoes, registrado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ocorrencia.veiculo_id,
            ocorrencia.rota_id,
            ocorrencia.tipo.value,
            ocorrencia.descricao,
            ocorrencia.data_ocorrencia or datetime.now(),
            ocorrencia.resolvido,
            ocorrencia.observacoes,
            ocorrencia.registrado_por
        ))
        self.conexao.commit()
        ocorrencia_id = cursor.lastrowid
        cursor.close()
        
        logger.info(f"Ocorrência registrada: {ocorrencia.tipo.value} (ID: {ocorrencia_id})")
        return ocorrencia_id

    def resolver_ocorrencia(self, ocorrencia_id: int, observacoes: Optional[str] = None) -> bool:
        """
        Marca uma ocorrência como resolvida.
        
        Args:
            ocorrencia_id: ID da ocorrência
            observacoes: Observações sobre a resolução
            
        Returns:
            True se atualizado com sucesso
        """
        cursor = self.conexao.cursor()
        
        if observacoes:
            cursor.execute("""
                UPDATE transporte_ocorrencias 
                SET resolvido = TRUE, observacoes = CONCAT(IFNULL(observacoes, ''), '\n', %s)
                WHERE id = %s
            """, (observacoes, ocorrencia_id))
        else:
            cursor.execute("""
                UPDATE transporte_ocorrencias SET resolvido = TRUE WHERE id = %s
            """, (ocorrencia_id,))
        
        self.conexao.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected > 0

    def _row_to_ocorrencia(self, row: Dict) -> OcorrenciaTransporte:
        """Converte uma linha do banco para objeto OcorrenciaTransporte."""
        return OcorrenciaTransporte(
            id=row['id'],
            veiculo_id=row.get('veiculo_id'),
            veiculo_placa=row.get('veiculo_placa'),
            rota_id=row.get('rota_id'),
            rota_nome=row.get('rota_nome'),
            tipo=TipoOcorrencia(row['tipo']),
            descricao=row['descricao'],
            data_ocorrencia=row.get('data_ocorrencia'),
            resolvido=bool(row.get('resolvido', False)),
            observacoes=row.get('observacoes'),
            registrado_por=row.get('registrado_por'),
            registrado_por_nome=row.get('registrado_por_nome'),
            created_at=row.get('created_at')
        )

    # ==================== ESTATÍSTICAS ====================

    def obter_estatisticas(self, ano_letivo_id: Optional[int] = None) -> EstatisticasTransporte:
        """
        Obtém estatísticas gerais do transporte escolar.
        
        Args:
            ano_letivo_id: ID do ano letivo para estatísticas de alunos
            
        Returns:
            Objeto com estatísticas
        """
        cursor = self.conexao.cursor(dictionary=True)
        
        # Estatísticas de veículos
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Ativo' THEN 1 ELSE 0 END) as ativos,
                SUM(CASE WHEN status = 'Manutenção' THEN 1 ELSE 0 END) as manutencao,
                SUM(CASE WHEN status = 'Ativo' THEN capacidade ELSE 0 END) as capacidade_total,
                SUM(CASE WHEN proxima_revisao <= CURDATE() THEN 1 ELSE 0 END) as revisao_pendente
            FROM transporte_veiculos
        """)
        veiculos = cursor.fetchone()
        
        # Estatísticas de rotas
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ativa = TRUE THEN 1 ELSE 0 END) as ativas
            FROM transporte_rotas
        """)
        rotas = cursor.fetchone()
        
        # Total de alunos no transporte
        query_alunos = """
            SELECT COUNT(*) as total
            FROM transporte_alunos
            WHERE ativo = TRUE
        """
        params = []
        if ano_letivo_id:
            query_alunos += " AND ano_letivo_id = %s"
            params.append(ano_letivo_id)
        
        cursor.execute(query_alunos, params)
        alunos = cursor.fetchone()
        
        # Ocorrências do mês
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM transporte_ocorrencias
            WHERE MONTH(data_ocorrencia) = MONTH(CURDATE())
              AND YEAR(data_ocorrencia) = YEAR(CURDATE())
        """)
        ocorrencias = cursor.fetchone()
        
        cursor.close()
        
        total_alunos = alunos['total'] or 0
        capacidade = veiculos['capacidade_total'] or 1
        taxa_ocupacao = (total_alunos / capacidade * 100) if capacidade > 0 else 0
        
        return EstatisticasTransporte(
            total_veiculos=veiculos['total'] or 0,
            veiculos_ativos=veiculos['ativos'] or 0,
            veiculos_manutencao=veiculos['manutencao'] or 0,
            total_rotas=rotas['total'] or 0,
            rotas_ativas=rotas['ativas'] or 0,
            total_alunos_transporte=total_alunos,
            capacidade_total=veiculos['capacidade_total'] or 0,
            taxa_ocupacao=round(taxa_ocupacao, 1),
            ocorrencias_mes=ocorrencias['total'] or 0,
            veiculos_revisao_pendente=veiculos['revisao_pendente'] or 0
        )

    def buscar_motoristas_disponiveis(self) -> List[Dict]:
        """
        Busca funcionários que podem ser motoristas.
        
        Returns:
            Lista de funcionários com id e nome
        """
        cursor = self.conexao.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nome 
            FROM Funcionarios 
            WHERE status = 'Ativo'
            ORDER BY nome
        """)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def buscar_alunos_sem_transporte(self, ano_letivo_id: int, termo_busca: str = "") -> List[Dict]:
        """
        Busca alunos que não estão vinculados ao transporte.
        
        Args:
            ano_letivo_id: ID do ano letivo
            termo_busca: Termo para filtrar por nome
            
        Returns:
            Lista de alunos disponíveis
        """
        cursor = self.conexao.cursor(dictionary=True)
        
        query = """
            SELECT a.id, a.nome, s.nome as serie, t.turma
            FROM alunos a
            JOIN matriculas m ON a.id = m.aluno_id
            LEFT JOIN series s ON m.serie_id = s.id
            LEFT JOIN turmas t ON m.turma_id = t.id
            WHERE m.ano_letivo_id = %s
              AND m.status = 'Ativo'
              AND a.id NOT IN (
                  SELECT aluno_id FROM transporte_alunos 
                  WHERE ano_letivo_id = %s AND ativo = TRUE
              )
        """
        params = [ano_letivo_id, ano_letivo_id]
        
        if termo_busca:
            query += " AND a.nome LIKE %s"
            params.append(f"%{termo_busca}%")
        
        query += " ORDER BY a.nome LIMIT 100"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows
