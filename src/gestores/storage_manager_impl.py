"""
Implementação limpa do StorageManager.
Este módulo contém a lógica real; `storage_manager.py` pode atuar como wrapper
que importa tudo daqui para não quebrar importações existentes.
"""
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from datetime import datetime

from src.core.config_logs import get_logger

logger = get_logger(__name__)


class StorageManager:
    ESTRUTURA_PASTAS: Dict[str, object] = {
        "alunos": {
            "anos_iniciais": {
                "1_ano": "1º Ano",
                "2_ano": "2º Ano",
                "3_ano": "3º Ano",
                "4_ano": "4º Ano",
                "5_ano": "5º Ano",
            },
            "anos_finais": {
                "6_ano_a": "6º Ano A",
                "6_ano_b": "6º Ano B",
                "7_ano": "7º Ano",
                "8_ano": "8º Ano",
                "9_ano": "9º Ano",
            },
        },
        "funcionarios": {
            "professores": "Professores",
            "administrativo": "Administrativo",
            "apoio": "Apoio",
        },
        "backup": "Backup",
        "relatorios": {
            "mensais": "Relatórios Mensais",
            "anuais": "Relatórios Anuais",
            "personalizados": "Relatórios Personalizados",
        },
        "atas": "Atas",
        "boletins": "Boletins",
        "declaracoes": "Declarações",
        "historicos": "Históricos Escolares",
    }

    def __init__(self, base_local: Optional[str] = None, usar_google_drive: Optional[bool] = None):
        if usar_google_drive is None:
            self.usar_google_drive = self._detectar_google_drive()
        else:
            self.usar_google_drive = bool(usar_google_drive)

        if self.usar_google_drive:
            self.base_drive = self._detectar_caminho_drive()
            if self.base_drive:
                self.base_storage = self.base_drive / "Gestao_Escolar"
                self.modo = "Google Drive"
            else:
                logger.warning("Google Drive não encontrado; revertendo para armazenamento local")
                self.usar_google_drive = False
                self.base_drive = None
                self.base_storage = self._obter_caminho_local(base_local)
                self.modo = "Local"
        else:
            self.base_drive = None
            self.base_storage = self._obter_caminho_local(base_local)
            self.modo = "Local"

        self._inicializar_estrutura()

    def _obter_caminho_local(self, base_local: Optional[str]) -> Path:
        if base_local:
            return Path(base_local)
        return Path(os.path.dirname(os.path.abspath(__file__))) / "documentos"

    def _detectar_google_drive(self) -> bool:
        try:
            credentials_path = Path(os.path.dirname(os.path.abspath(__file__))) / 'credentials.json'
            if not credentials_path.exists():
                return False
            import google.oauth2.credentials  # type: ignore
            import google_auth_oauthlib.flow  # type: ignore
            return True
        except Exception:
            return False

    def _detectar_caminho_drive(self) -> Optional[Path]:
        possiveis = [
            Path(os.path.expanduser("~")) / "Google Drive",
            Path("G:") / "Meu Drive",
            Path("G:") / "My Drive",
            Path(os.path.expanduser("~")) / "GoogleDrive",
        ]
        for caminho in possiveis:
            try:
                if caminho.exists():
                    return caminho
            except Exception:
                continue
        return None

    def _inicializar_estrutura(self) -> None:
        self._criar_estrutura_recursiva(self.base_storage, self.ESTRUTURA_PASTAS)

    def _criar_estrutura_recursiva(self, base: Path, estrutura: Dict[str, object]) -> None:
        for chave, valor in estrutura.items():
            pasta = base / chave
            pasta.mkdir(parents=True, exist_ok=True)
            if isinstance(valor, dict):
                self._criar_estrutura_recursiva(pasta, valor)  # type: ignore

    def obter_caminho_turma(self, nome_turma: str) -> Optional[Path]:
        n = nome_turma.strip()
        base = self.base_storage / "alunos"
        if "1º Ano" in n or ("1º" in n and "Ano" in n):
            return base / "anos_iniciais" / "1_ano"
        if "2º Ano" in n or "2º" in n:
            return base / "anos_iniciais" / "2_ano"
        if "3º Ano" in n or "3º" in n:
            return base / "anos_iniciais" / "3_ano"
        if "4º Ano" in n or "4º" in n:
            return base / "anos_iniciais" / "4_ano"
        if "5º Ano" in n or "5º" in n:
            return base / "anos_iniciais" / "5_ano"
        if "6º" in n:
            if "6º Ano B" in n or "6 B" in n or "6º B" in n:
                return base / "anos_finais" / "6_ano_b"
            return base / "anos_finais" / "6_ano_a"
        if "7º" in n:
            return base / "anos_finais" / "7_ano"
        if "8º" in n:
            return base / "anos_finais" / "8_ano"
        if "9º" in n:
            return base / "anos_finais" / "9_ano"
        return None

    def salvar_arquivo(
        self,
        arquivo_origem: str,
        categoria: str,
        subcategoria: Optional[str] = None,
        nome_arquivo: Optional[str] = None,
        turma: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        try:
            if not os.path.exists(arquivo_origem):
                return False, f"Arquivo origem não encontrado: {arquivo_origem}", None

            if not nome_arquivo:
                nome_arquivo = os.path.basename(arquivo_origem)

            if turma and categoria == "alunos":
                caminho_destino = self.obter_caminho_turma(turma)
                if not caminho_destino:
                    return False, f"Turma não mapeada: {turma}", None
            else:
                caminho_destino = self.base_storage / categoria
                if subcategoria:
                    caminho_destino = caminho_destino / subcategoria

            caminho_destino.mkdir(parents=True, exist_ok=True)
            arquivo_destino = caminho_destino / nome_arquivo

            shutil.copy2(arquivo_origem, arquivo_destino)
            logger.info(f"Arquivo salvo ({self.modo}): {arquivo_destino}")
            return True, "Arquivo salvo com sucesso", str(arquivo_destino)
        except Exception as e:
            logger.exception(f"Erro ao salvar arquivo: {e}")
            return False, f"Erro ao salvar: {e}", None

    def listar_arquivos(
        self,
        categoria: str,
        subcategoria: Optional[str] = None,
        turma: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        try:
            if turma and categoria == "alunos":
                caminho = self.obter_caminho_turma(turma)
            else:
                caminho = self.base_storage / categoria
                if subcategoria:
                    caminho = caminho / subcategoria

            if not caminho or not caminho.exists():
                return []

            arquivos = []
            for item in caminho.iterdir():
                if item.is_file():
                    stat = item.stat()
                    arquivos.append({
                        "nome": item.name,
                        "caminho": str(item),
                        "tamanho": stat.st_size,
                        "modificado": datetime.fromtimestamp(stat.st_mtime),
                    })
            return arquivos
        except Exception as e:
            logger.exception(f"Erro ao listar arquivos: {e}")
            return []

    def obter_info_armazenamento(self) -> Dict[str, object]:
        return {
            "modo": self.modo,
            "caminho_armazenamento": str(self.base_storage),
            "armazenamento_existe": self.base_storage.exists(),
            "usando_google_drive": self.usar_google_drive,
            "caminho_drive": str(self.base_drive) if self.base_drive else None,
        }


# Singleton
_storage_manager: Optional[StorageManager] = None


def get_storage_manager(base_local: Optional[str] = None, usar_google_drive: Optional[bool] = None) -> StorageManager:
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager(base_local=base_local, usar_google_drive=usar_google_drive)
    return _storage_manager


# Funções de conveniência

def salvar_documento_turma(arquivo: str, turma: str, nome: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    manager = get_storage_manager()
    return manager.salvar_arquivo(arquivo_origem=arquivo, categoria="alunos", turma=turma, nome_arquivo=nome)


def salvar_backup(arquivo: str, nome: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    manager = get_storage_manager()
    nome_arquivo = nome or os.path.basename(arquivo)
    return manager.salvar_arquivo(arquivo_origem=arquivo, categoria="backup", nome_arquivo=nome_arquivo)


def salvar_relatorio(arquivo: str, tipo: str = "personalizados", nome: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    manager = get_storage_manager()
    nome_arquivo = nome or os.path.basename(arquivo)
    return manager.salvar_arquivo(arquivo_origem=arquivo, categoria="relatorios", subcategoria=tipo, nome_arquivo=nome_arquivo)
