"""
Interface e implementações para provedores de tábuas de mortalidade.
Segue o princípio de Inversão de Dependência (DIP) do SOLID.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MortalityTableProvider(ABC):
    """Interface abstrata para provedores de tábuas de mortalidade"""

    @abstractmethod
    def get_mortality_table(self, table_name: str, gender: str) -> np.ndarray:
        """
        Recupera tábua de mortalidade específica.

        Args:
            table_name: Nome da tábua (ex: "AT-2000", "BR-EMS")
            gender: Gênero ("M" ou "F")

        Returns:
            Array numpy com probabilidades de morte por idade

        Raises:
            ValueError: Se tábua não for encontrada
        """
        pass

    @abstractmethod
    def get_available_tables(self) -> List[str]:
        """
        Lista tábuas disponíveis.

        Returns:
            Lista com nomes das tábuas disponíveis
        """
        pass

    @abstractmethod
    def get_table_info(self, table_name: str) -> Dict:
        """
        Recupera metadados de uma tábua.

        Args:
            table_name: Nome da tábua

        Returns:
            Dicionário com informações da tábua

        Raises:
            ValueError: Se tábua não for encontrada
        """
        pass

    @abstractmethod
    def validate_table(self, table_name: str, gender: str) -> bool:
        """
        Valida se uma tábua está disponível e é válida.

        Args:
            table_name: Nome da tábua
            gender: Gênero

        Returns:
            True se válida, False caso contrário
        """
        pass


class FileMortalityProvider(MortalityTableProvider):
    """Provedor baseado em arquivos do sistema (implementação atual)"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cache = {}

    def get_mortality_table(self, table_name: str, gender: str) -> np.ndarray:
        """Implementação baseada nos arquivos existentes"""
        # Importar funções existentes para manter compatibilidade
        from .mortality_tables import get_mortality_table

        cache_key = f"{table_name}_{gender}"
        if cache_key not in self._cache:
            try:
                table = get_mortality_table(table_name, gender)
                self._cache[cache_key] = table
                self.logger.debug(f"Tábua carregada: {cache_key}")
            except Exception as e:
                self.logger.error(f"Erro ao carregar tábua {cache_key}: {e}")
                raise ValueError(f"Tábua de mortalidade não encontrada: {table_name} ({gender})")

        return self._cache[cache_key]

    def get_available_tables(self) -> List[str]:
        """Lista tábuas disponíveis no sistema de arquivos"""
        from .mortality_tables import get_mortality_table_info

        # Tábuas conhecidas (pode ser expandido dinamicamente)
        known_tables = ["AT-2000", "BR-EMS", "IBGE-2019", "GAM-1971"]
        available = []

        for table in known_tables:
            try:
                info = get_mortality_table_info(table)
                if info:
                    available.append(table)
            except:
                continue

        return available

    def get_table_info(self, table_name: str) -> Dict:
        """Recupera informações da tábua"""
        from .mortality_tables import get_mortality_table_info

        try:
            info = get_mortality_table_info(table_name)
            if not info:
                raise ValueError(f"Informações não encontradas para: {table_name}")
            return info
        except Exception as e:
            self.logger.error(f"Erro ao buscar info da tábua {table_name}: {e}")
            raise ValueError(f"Tábua não encontrada: {table_name}")

    def validate_table(self, table_name: str, gender: str) -> bool:
        """Valida tábua testando carregamento"""
        try:
            table = self.get_mortality_table(table_name, gender)
            # Validações básicas
            if len(table) < 50:  # Mínimo de idades
                return False
            if np.any(table < 0) or np.any(table > 1):  # Probabilidades válidas
                return False
            return True
        except:
            return False


class DatabaseMortalityProvider(MortalityTableProvider):
    """Provedor baseado em banco de dados (implementação futura)"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(self.__class__.__name__)
        # TODO: Implementar conexão com banco

    def get_mortality_table(self, table_name: str, gender: str) -> np.ndarray:
        """Implementação para banco de dados"""
        # TODO: Implementar consulta SQL
        raise NotImplementedError("DatabaseMortalityProvider ainda não implementado")

    def get_available_tables(self) -> List[str]:
        """Lista tábuas do banco"""
        # TODO: SELECT DISTINCT table_name FROM mortality_tables
        raise NotImplementedError("DatabaseMortalityProvider ainda não implementado")

    def get_table_info(self, table_name: str) -> Dict:
        """Recupera metadados do banco"""
        # TODO: Consultar tabela de metadados
        raise NotImplementedError("DatabaseMortalityProvider ainda não implementado")

    def validate_table(self, table_name: str, gender: str) -> bool:
        """Valida existência no banco"""
        # TODO: Verificar se registro existe
        raise NotImplementedError("DatabaseMortalityProvider ainda não implementado")


class APIMortalityProvider(MortalityTableProvider):
    """Provedor baseado em API externa (implementação futura)"""

    def __init__(self, api_base_url: str, api_key: Optional[str] = None):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_mortality_table(self, table_name: str, gender: str) -> np.ndarray:
        """Implementação para API externa"""
        # TODO: Fazer requisição HTTP para API
        raise NotImplementedError("APIMortalityProvider ainda não implementado")

    def get_available_tables(self) -> List[str]:
        """Lista tábuas da API"""
        # TODO: GET /api/mortality-tables
        raise NotImplementedError("APIMortalityProvider ainda não implementado")

    def get_table_info(self, table_name: str) -> Dict:
        """Recupera metadados da API"""
        # TODO: GET /api/mortality-tables/{table_name}/info
        raise NotImplementedError("APIMortalityProvider ainda não implementado")

    def validate_table(self, table_name: str, gender: str) -> bool:
        """Valida via API"""
        # TODO: HEAD /api/mortality-tables/{table_name}/{gender}
        raise NotImplementedError("APIMortalityProvider ainda não implementado")


class CompositeMortalityProvider(MortalityTableProvider):
    """Provedor composto que tenta múltiplas fontes em ordem de prioridade"""

    def __init__(self, providers: List[MortalityTableProvider]):
        if not providers:
            raise ValueError("Lista de provedores não pode estar vazia")

        self.providers = providers
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_mortality_table(self, table_name: str, gender: str) -> np.ndarray:
        """Tenta cada provedor em ordem até encontrar a tábua"""
        for i, provider in enumerate(self.providers):
            try:
                table = provider.get_mortality_table(table_name, gender)
                if i > 0:  # Log apenas se não foi o primeiro provedor
                    self.logger.info(f"Tábua {table_name}_{gender} encontrada no provedor {i+1}")
                return table
            except Exception as e:
                self.logger.debug(f"Provedor {i+1} falhou para {table_name}_{gender}: {e}")
                continue

        raise ValueError(f"Tábua não encontrada em nenhum provedor: {table_name} ({gender})")

    def get_available_tables(self) -> List[str]:
        """Combina tábuas de todos os provedores"""
        all_tables = set()
        for provider in self.providers:
            try:
                tables = provider.get_available_tables()
                all_tables.update(tables)
            except Exception as e:
                self.logger.warning(f"Erro ao listar tábuas de um provedor: {e}")

        return sorted(list(all_tables))

    def get_table_info(self, table_name: str) -> Dict:
        """Busca informações no primeiro provedor que tiver a tábua"""
        for provider in self.providers:
            try:
                return provider.get_table_info(table_name)
            except:
                continue

        raise ValueError(f"Informações não encontradas para: {table_name}")

    def validate_table(self, table_name: str, gender: str) -> bool:
        """Valida se pelo menos um provedor tem a tábua"""
        for provider in self.providers:
            if provider.validate_table(table_name, gender):
                return True
        return False


class MortalityTableFactory:
    """Factory para criar provedores de tábuas de mortalidade"""

    @staticmethod
    def create_default_provider() -> MortalityTableProvider:
        """
        Cria o provedor padrão do sistema.

        Returns:
            Provedor padrão baseado em arquivos
        """
        return FileMortalityProvider()

    @staticmethod
    def create_composite_provider(enable_database: bool = False,
                                enable_api: bool = False) -> MortalityTableProvider:
        """
        Cria provedor composto com múltiplas fontes.

        Args:
            enable_database: Se deve incluir provedor de banco
            enable_api: Se deve incluir provedor de API

        Returns:
            Provedor composto configurado
        """
        providers = [FileMortalityProvider()]  # Sempre incluir arquivo como fallback

        if enable_database:
            try:
                db_provider = DatabaseMortalityProvider("sqlite:///mortality.db")
                providers.insert(0, db_provider)  # Prioridade mais alta
            except Exception as e:
                logger.warning(f"Não foi possível criar provedor de banco: {e}")

        if enable_api:
            try:
                api_provider = APIMortalityProvider("https://api.mortality-tables.com")
                providers.insert(-1, api_provider)  # Segunda prioridade
            except Exception as e:
                logger.warning(f"Não foi possível criar provedor de API: {e}")

        if len(providers) == 1:
            return providers[0]
        else:
            return CompositeMortalityProvider(providers)