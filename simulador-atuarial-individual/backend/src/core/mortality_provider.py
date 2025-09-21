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
    """Provedor baseado em banco de dados SQLModel/SQLite"""

    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string
        self.logger = logging.getLogger(self.__class__.__name__)

        # Importar dependências do banco
        from ..database import get_session, engine
        from ..repositories.mortality_repository import MortalityTableRepository
        from sqlmodel import Session

        self.get_session = get_session
        self.engine = engine
        self.repository_class = MortalityTableRepository

    def get_mortality_table(self, table_name: str, gender: str) -> np.ndarray:
        """Implementação para banco de dados"""
        try:
            with Session(self.engine) as session:
                repo = self.repository_class(session)

                # Buscar por nome ou código
                table = repo.get_by_name(table_name)
                if not table:
                    table = repo.get_by_code(table_name)

                if not table:
                    raise ValueError(f"Tábua de mortalidade '{table_name}' não encontrada no banco")

                if not table.is_active:
                    raise ValueError(f"Tábua de mortalidade '{table_name}' está inativa")

                # Verificar compatibilidade de gênero
                if table.gender and table.gender.upper() != "UNISEX" and table.gender.upper() != gender.upper():
                    self.logger.warning(f"Tábua '{table_name}' é para gênero '{table.gender}', usando para '{gender}'")

                # Converter dados para array numpy
                table_data = table.get_table_data()
                if not table_data:
                    raise ValueError(f"Tábua '{table_name}' não contém dados válidos")

                # Criar array numpy ordenado por idade
                max_age = max(table_data.keys())
                mortality_array = np.zeros(max_age + 1)

                for age, qx in table_data.items():
                    if 0 <= age <= max_age:
                        mortality_array[age] = float(qx)

                self.logger.info(f"Tábua '{table_name}' carregada do banco com {len(table_data)} idades")
                return mortality_array

        except Exception as e:
            self.logger.error(f"Erro ao carregar tábua '{table_name}' do banco: {str(e)}")
            raise

    def get_available_tables(self) -> List[str]:
        """Lista tábuas do banco"""
        try:
            with Session(self.engine) as session:
                repo = self.repository_class(session)
                active_tables = repo.get_active_tables()

                # Retornar lista de nomes das tábuas ativas
                table_names = [table.name for table in active_tables]
                self.logger.info(f"Encontradas {len(table_names)} tábuas ativas no banco")
                return table_names

        except Exception as e:
            self.logger.error(f"Erro ao listar tábuas do banco: {str(e)}")
            return []

    def get_table_info(self, table_name: str) -> Dict:
        """Recupera metadados do banco"""
        try:
            with Session(self.engine) as session:
                repo = self.repository_class(session)

                # Buscar por nome ou código
                table = repo.get_by_name(table_name)
                if not table:
                    table = repo.get_by_code(table_name)

                if not table:
                    return {}

                return {
                    "name": table.name,
                    "code": table.code,
                    "description": table.description,
                    "country": table.country,
                    "year": table.year,
                    "gender": table.gender,
                    "source": table.source,
                    "version": table.version,
                    "is_official": table.is_official,
                    "regulatory_approved": table.regulatory_approved,
                    "is_active": table.is_active,
                    "metadata": table.get_metadata()
                }

        except Exception as e:
            self.logger.error(f"Erro ao obter informações da tábua '{table_name}': {str(e)}")
            return {}

    def validate_table(self, table_name: str, gender: str) -> bool:
        """Valida existência no banco"""
        try:
            with Session(self.engine) as session:
                repo = self.repository_class(session)

                # Buscar por nome ou código
                table = repo.get_by_name(table_name)
                if not table:
                    table = repo.get_by_code(table_name)

                if not table:
                    return False

                # Verificar se está ativa
                if not table.is_active:
                    return False

                # Verificar dados
                table_data = table.get_table_data()
                if not table_data:
                    return False

                return True

        except Exception as e:
            self.logger.error(f"Erro na validação da tábua '{table_name}': {str(e)}")
            return False


class APIMortalityProvider(MortalityTableProvider):
    """Provedor baseado em API externa REST"""

    def __init__(self, api_base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        self.api_base_url = api_base_url.rstrip('/')  # Remove trailing slash
        self.api_key = api_key
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

        # Headers padrão
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        if api_key:
            self.default_headers['Authorization'] = f'Bearer {api_key}'

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Faz requisição HTTP para a API"""
        try:
            import requests

            url = f"{self.api_base_url}{endpoint}"
            headers = {**self.default_headers, **kwargs.pop('headers', {})}

            self.logger.debug(f"API Request: {method.upper()} {url}")

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )

            response.raise_for_status()

            # Tentar decodificar JSON
            try:
                return response.json()
            except ValueError:
                return {"success": True, "data": response.text}

        except ImportError:
            raise ImportError("requests library is required for APIMortalityProvider")
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise

    def get_mortality_table(self, table_name: str, gender: str) -> np.ndarray:
        """Implementação para API externa"""
        try:
            # GET /api/mortality-tables/{table_name}/{gender}
            endpoint = f"/api/mortality-tables/{table_name}/{gender.upper()}"
            response = self._make_request('GET', endpoint)

            # Esperar formato: {"success": true, "data": {"ages": [0,1,2,...], "rates": [0.001, 0.002, ...]}}
            if not response.get('success', False):
                raise ValueError(f"API retornou erro: {response.get('message', 'Unknown error')}")

            data = response.get('data', {})
            ages = data.get('ages', [])
            rates = data.get('rates', [])

            if not ages or not rates or len(ages) != len(rates):
                raise ValueError(f"Dados inválidos da API para tábua '{table_name}'")

            # Criar array numpy
            max_age = max(ages)
            mortality_array = np.zeros(max_age + 1)

            for age, rate in zip(ages, rates):
                if 0 <= age <= max_age:
                    mortality_array[age] = float(rate)

            self.logger.info(f"Tábua '{table_name}' carregada da API com {len(rates)} idades")
            return mortality_array

        except Exception as e:
            self.logger.error(f"Erro ao carregar tábua '{table_name}' da API: {str(e)}")
            raise

    def get_available_tables(self) -> List[str]:
        """Lista tábuas da API"""
        try:
            # GET /api/mortality-tables
            endpoint = "/api/mortality-tables"
            response = self._make_request('GET', endpoint)

            if not response.get('success', False):
                raise ValueError(f"API retornou erro: {response.get('message', 'Unknown error')}")

            tables = response.get('data', [])

            # Esperar formato: {"success": true, "data": ["BR_EMS_2021", "AT_83", ...]}
            if isinstance(tables, list):
                table_names = [str(table) for table in tables]
            else:
                # Formato alternativo: {"success": true, "data": {"tables": [...]}}
                table_names = [str(table) for table in tables.get('tables', [])]

            self.logger.info(f"Encontradas {len(table_names)} tábuas na API")
            return table_names

        except Exception as e:
            self.logger.error(f"Erro ao listar tábuas da API: {str(e)}")
            return []

    def get_table_info(self, table_name: str) -> Dict:
        """Recupera metadados da API"""
        try:
            # GET /api/mortality-tables/{table_name}/info
            endpoint = f"/api/mortality-tables/{table_name}/info"
            response = self._make_request('GET', endpoint)

            if not response.get('success', False):
                self.logger.warning(f"API não retornou informações para tábua '{table_name}'")
                return {}

            return response.get('data', {})

        except Exception as e:
            self.logger.error(f"Erro ao obter informações da tábua '{table_name}' da API: {str(e)}")
            return {}

    def validate_table(self, table_name: str, gender: str) -> bool:
        """Valida via API"""
        try:
            # HEAD /api/mortality-tables/{table_name}/{gender}
            endpoint = f"/api/mortality-tables/{table_name}/{gender.upper()}"

            import requests
            url = f"{self.api_base_url}{endpoint}"

            response = requests.head(
                url=url,
                headers=self.default_headers,
                timeout=self.timeout
            )

            # Retornar True se status for 200 ou 204
            return response.status_code in [200, 204]

        except ImportError:
            raise ImportError("requests library is required for APIMortalityProvider")
        except Exception as e:
            self.logger.debug(f"Validação da tábua '{table_name}' falhou: {str(e)}")
            return False


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