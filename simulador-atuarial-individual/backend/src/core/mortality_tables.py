import numpy as np
from typing import Dict, Any
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrada de cache com TTL (Time To Live)"""
    data: np.ndarray
    timestamp: float
    ttl_seconds: float = 3600  # 1 hora por padrão
    
    @property
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou"""
        return time.time() - self.timestamp > self.ttl_seconds


class MortalityTableCache:
    """Cache otimizado para tábuas de mortalidade com TTL e limpeza automática"""
    
    def __init__(self, max_entries: int = 100, default_ttl: float = 3600):
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self._cache: Dict[tuple, CacheEntry] = {}
        self._last_cleanup = time.time()
        self._cleanup_interval = 600  # Limpeza a cada 10 minutos
    
    def get(self, key: tuple) -> np.ndarray:
        """
        Obtém entrada do cache
        
        Args:
            key: Chave do cache (table_code, gender, aggravation_pct)
            
        Returns:
            Tábua de mortalidade ou None se não encontrada/expirada
        """
        self._cleanup_if_needed()
        
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired:
                # Retornar cópia apropriada dependendo do tipo
                if isinstance(entry.data, tuple):
                    # Para tupla (array, str), copiar apenas o array
                    return (entry.data[0].copy() if hasattr(entry.data[0], 'copy') else entry.data[0], entry.data[1])
                elif hasattr(entry.data, 'copy'):
                    return entry.data.copy()
                else:
                    import copy
                    return copy.deepcopy(entry.data)
            else:
                # Remover entrada expirada
                del self._cache[key]

        return None
    
    def set(self, key: tuple, data: np.ndarray, ttl: float = None) -> None:
        """
        Armazena entrada no cache
        
        Args:
            key: Chave do cache
            data: Tábua de mortalidade
            ttl: Time to live em segundos (usa default se None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Se cache estiver cheio, remover entradas mais antigas
        if len(self._cache) >= self.max_entries:
            self._evict_oldest()

        # Fazer cópia dos dados - se for tupla, copiar cada elemento
        if isinstance(data, tuple):
            # Para tupla (array, str), copiar apenas o array
            cached_data = (data[0].copy() if hasattr(data[0], 'copy') else data[0], data[1])
        elif hasattr(data, 'copy'):
            cached_data = data.copy()
        else:
            import copy
            cached_data = copy.deepcopy(data)

        entry = CacheEntry(
            data=cached_data,
            timestamp=time.time(),
            ttl_seconds=ttl
        )
        self._cache[key] = entry
    
    def _cleanup_if_needed(self) -> None:
        """Executa limpeza automática de entradas expiradas se necessário"""
        current_time = time.time()
        if current_time - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = current_time
    
    def _cleanup_expired(self) -> None:
        """Remove todas as entradas expiradas"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"[CACHE] Removidas {len(expired_keys)} entradas expiradas")
    
    def _evict_oldest(self) -> None:
        """Remove a entrada mais antiga para liberar espaço"""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].timestamp
        )
        del self._cache[oldest_key]
        logger.info(f"[CACHE] Removida entrada mais antiga: {oldest_key}")
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        self._cache.clear()
        logger.info("[CACHE] Cache limpo completamente")
    
    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        current_time = time.time()
        expired_count = sum(1 for entry in self._cache.values() if entry.is_expired)
        
        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "max_entries": self.max_entries,
            "last_cleanup": self._last_cleanup,
            "time_since_cleanup": current_time - self._last_cleanup
        }


# Cache global otimizado
_MORTALITY_CACHE = MortalityTableCache()



def apply_mortality_aggravation(mortality_table: np.ndarray, aggravation_pct: float) -> np.ndarray:
    """
    Aplica suavização percentual à tábua de mortalidade.

    Por convenção do projeto, valores positivos representam suavização (redução dos
    qx), alongando a sobrevivência e aumentando reservas. Valores negativos
    intensificam a mortalidade.

    Args:
        mortality_table: Array numpy com probabilidades de morte anuais (qx)
        aggravation_pct: Percentual de suavização (-10 a +20)

    Returns:
        Array numpy com probabilidades ajustadas
    """
    if aggravation_pct == 0.0:
        return mortality_table.copy()

    # Suavização positiva = menor mortalidade = mais benefícios futuros
    aggravation_factor = 1 - (aggravation_pct / 100)  # Sinal invertido
    adjusted_table = mortality_table * aggravation_factor

    # Garantir que qx permaneça no intervalo válido [0, 1]
    adjusted_table = np.clip(adjusted_table, 0.0, 1.0)
    
    return adjusted_table


def get_mortality_table(table_code: str, gender: str, aggravation_pct: float = 0.0) -> tuple[np.ndarray, str]:
    """Obtém tábua de mortalidade do banco de dados com suavização opcional

    Returns:
        tuple: (mortality_rates_array, actual_table_code)
    """
    # Cache considerando o percentual de suavização
    # Agora o cache armazena tuplas (array, code)
    cache_key = (table_code, gender, aggravation_pct)

    # Tentar obter do cache otimizado
    cached_data = _MORTALITY_CACHE.get(cache_key)
    if cached_data is not None:
        return cached_data

    # Obter a tábua base do banco (sem suavização)
    base_cache_key = (table_code, gender, 0.0)  # Sempre suavização zero para tábua base

    cached_base = _MORTALITY_CACHE.get(base_cache_key)
    if cached_base is None:
        # Carregar do banco de dados
        base_table, actual_code = _load_from_database(table_code, gender)
        if base_table is None:
            raise ValueError(f"Tábua {table_code} para gênero {gender} não encontrada no banco de dados")

        # Armazenar tábua base no cache com TTL maior (2 horas)
        _MORTALITY_CACHE.set(base_cache_key, (base_table, actual_code), ttl=7200)
    else:
        base_table, actual_code = cached_base

    # Aplicar suavização à tábua base
    adjusted_table = apply_mortality_aggravation(base_table, aggravation_pct)

    # Armazenar no cache com TTL padrão (1 hora)
    _MORTALITY_CACHE.set(cache_key, (adjusted_table, actual_code))

    return adjusted_table, actual_code


def _load_from_database(table_code: str, gender: str) -> tuple[np.ndarray, str]:
    """Carrega tábua do banco de dados

    Returns:
        tuple: (mortality_rates_array, actual_table_code)
    """
    logger.info(f"[DB LOAD] Carregando tábua: code='{table_code}', gender='{gender}'")

    try:
        from ..database import engine
        from ..models.database import MortalityTable
        from sqlmodel import Session, select

        with Session(engine) as session:
            # Procurar tábua específica por gênero
            specific_code = f"{table_code}_{gender}"
            logger.debug(f"[DB LOAD] Tentando código específico: '{specific_code}'")

            statement = select(MortalityTable).where(
                MortalityTable.code == specific_code,
                MortalityTable.is_active == True
            )
            table = session.exec(statement).first()

            if not table:
                # Se não encontrar específica, procurar genérica com o gênero correto
                statement = select(MortalityTable).where(
                    MortalityTable.code.like(f"{table_code}%"),
                    MortalityTable.gender == gender,
                    MortalityTable.is_active == True
                )
                table = session.exec(statement).first()

            if not table and table_code.startswith("SOA_"):
                # Para tábuas SOA (pymort), buscar diretamente por source_id e gender
                # Exemplo: SOA_1097_F não existe, então buscar tábua pymort com gender='F' e source_id próximo a 1097
                try:
                    # Extrair ID base do código (ex: SOA_1097 -> 1097)
                    base_id = table_code.replace("SOA_", "").split("_")[0]

                    logger.info(f"[SOA LOOKUP] Buscando tábua pymort com source_id próximo a '{base_id}' e gender='{gender}'")

                    # Buscar tábua com source='pymort', gender correto, e source_id exato ou próximo
                    # Primeiro tentar source_id exato
                    statement = select(MortalityTable).where(
                        MortalityTable.source == 'pymort',
                        MortalityTable.source_id == base_id,
                        MortalityTable.gender == gender,
                        MortalityTable.is_active == True
                    )
                    table = session.exec(statement).first()

                    if not table:
                        # Se não encontrou exato, tentar IDs próximos (±10)
                        try:
                            base_num = int(base_id)
                            for offset in range(1, 11):
                                for candidate_id in [str(base_num + offset), str(base_num - offset)]:
                                    statement = select(MortalityTable).where(
                                        MortalityTable.source == 'pymort',
                                        MortalityTable.source_id == candidate_id,
                                        MortalityTable.gender == gender,
                                        MortalityTable.is_active == True
                                    )
                                    table = session.exec(statement).first()
                                    if table:
                                        logger.info(f"✅ Encontrada tábua SOA complementar próxima: {table.code} (source_id={candidate_id})")
                                        break
                                if table:
                                    break
                        except ValueError:
                            pass
                    else:
                        logger.info(f"✅ Encontrada tábua SOA complementar exata: {table.code} para {table_code}_{gender}")

                except Exception as e:
                    logger.warning(f"[SOA LOOKUP] Erro ao buscar tábua complementar: {e}")

            if not table:
                # Buscar tábua UNISEX se não encontrar específica
                statement = select(MortalityTable).where(
                    MortalityTable.code == table_code,
                    MortalityTable.gender == 'UNISEX',
                    MortalityTable.is_active == True
                )
                table = session.exec(statement).first()

            if not table:
                # Buscar tábua sem gênero definido (fallback para tábuas antigas)
                statement = select(MortalityTable).where(
                    MortalityTable.code == table_code,
                    MortalityTable.gender == None,
                    MortalityTable.is_active == True
                )
                table = session.exec(statement).first()

            if table:
                logger.info(f"✅ [DB LOAD] Tábua carregada: {table.code} (source={table.source}, gender={table.gender})")

                table_data_dict = table.get_table_data()
                # Converter para numpy array no formato esperado
                max_age = max(table_data_dict.keys())
                mortality_rates = np.zeros(max_age + 1)
                for age, rate in table_data_dict.items():
                    mortality_rates[age] = rate
                return mortality_rates, table.code  # Retornar array e código real

            logger.warning(f"❌ [DB LOAD] Tábua {table_code}_{gender} não encontrada no banco")
            return None, None

    except Exception as e:
        logger.error(f"❌ [DB LOAD] Erro ao carregar tábua {table_code}_{gender} do banco: {e}")
        return None, None


def get_mortality_table_info() -> list[Dict[str, Any]]:
    """Retorna informações sobre todas as tábuas disponíveis do banco de dados"""
    tables_info = []

    try:
        from ..database import engine
        from ..models.database import MortalityTable
        from sqlmodel import Session, select

        with Session(engine) as session:
            statement = select(MortalityTable).where(MortalityTable.is_active == True)
            db_tables = session.exec(statement).all()

            # Retornar todas as tábuas individualmente (sem agrupamento)
            for table in db_tables:
                # Criar nome de exibição mais amigável
                display_name = table.name

                # Para tábuas com sufixo de gênero, mostrar de forma mais clara
                if table.gender == "M":
                    if "Masculina" not in display_name and "Male" not in display_name:
                        display_name = f"{display_name} (M)"
                elif table.gender == "F":
                    if "Feminina" not in display_name and "Female" not in display_name:
                        display_name = f"{display_name} (F)"

                tables_info.append({
                    "code": table.code,
                    "name": display_name,
                    "description": table.description or "",
                    "source": table.source,
                    "gender": table.gender,
                    "is_official": table.is_official,
                    "regulatory_approved": table.regulatory_approved
                })

    except Exception as e:
        logger.error(f"Erro ao carregar informações das tábuas do banco: {e}")

    return tables_info


def validate_mortality_table(table_code: str) -> bool:
    """Valida se a tábua existe no banco de dados"""
    try:
        from ..database import engine
        from ..models.database import MortalityTable
        from sqlmodel import Session, select
        
        with Session(engine) as session:
            # Procurar por códigos com sufixos _M/_F ou código exato
            patterns = [table_code, f"{table_code}_M", f"{table_code}_F"]
            
            for pattern in patterns:
                statement = select(MortalityTable).where(
                    MortalityTable.code == pattern,
                    MortalityTable.is_active == True
                )
                if session.exec(statement).first():
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Erro ao validar tábua {table_code}: {e}")
        return False


def get_cache_stats() -> Dict[str, Any]:
    """
    Retorna estatísticas do cache de tábuas de mortalidade
    
    Returns:
        Dicionário com estatísticas do cache
    """
    return _MORTALITY_CACHE.stats()


def clear_mortality_cache() -> None:
    """
    Limpa completamente o cache de tábuas de mortalidade
    Útil para testes ou liberação de memória
    """
    _MORTALITY_CACHE.clear()
