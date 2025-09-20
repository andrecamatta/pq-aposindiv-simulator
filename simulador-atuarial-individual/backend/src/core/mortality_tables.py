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
                return entry.data.copy()  # Retornar cópia para evitar modificação
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
        
        entry = CacheEntry(
            data=data.copy(),
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


def get_mortality_table(table_code: str, gender: str, aggravation_pct: float = 0.0) -> np.ndarray:
    """Obtém tábua de mortalidade do banco de dados com suavização opcional"""
    # Cache considerando o percentual de suavização
    cache_key = (table_code, gender, aggravation_pct)
    
    # Tentar obter do cache otimizado
    cached_table = _MORTALITY_CACHE.get(cache_key)
    if cached_table is not None:
        return cached_table
    
    # Obter a tábua base do banco (sem suavização)
    base_cache_key = (table_code, gender, 0.0)  # Sempre suavização zero para tábua base
    
    base_table = _MORTALITY_CACHE.get(base_cache_key)
    if base_table is None:
        # Carregar do banco de dados
        base_table = _load_from_database(table_code, gender)
        if base_table is None:
            raise ValueError(f"Tábua {table_code} para gênero {gender} não encontrada no banco de dados")
        
        # Armazenar tábua base no cache com TTL maior (2 horas)
        _MORTALITY_CACHE.set(base_cache_key, base_table, ttl=7200)
    
    # Aplicar suavização à tábua base
    adjusted_table = apply_mortality_aggravation(base_table, aggravation_pct)
    
    # Armazenar no cache com TTL padrão (1 hora)
    _MORTALITY_CACHE.set(cache_key, adjusted_table)
    
    return adjusted_table


def _load_from_database(table_code: str, gender: str) -> np.ndarray:
    """Carrega tábua do banco de dados"""
    try:
        from ..database import engine
        from ..models.database import MortalityTable
        from sqlmodel import Session, select
        
        with Session(engine) as session:
            # Procurar tábua específica por gênero
            specific_code = f"{table_code}_{gender}"
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
            
            if table:
                table_data_dict = table.get_table_data()
                # Converter para numpy array no formato esperado
                max_age = max(table_data_dict.keys())
                mortality_rates = np.zeros(max_age + 1)
                for age, rate in table_data_dict.items():
                    mortality_rates[age] = rate
                return mortality_rates
            
            logger.warning(f"Tábua {table_code}_{gender} não encontrada no banco")
            return None
    
    except Exception as e:
        logger.error(f"Erro ao carregar tábua {table_code}_{gender} do banco: {e}")
        return None


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
            
            # Agrupar tábuas por família (removendo sufixo _M/_F)
            table_families = {}
            for table in db_tables:
                # Extrair código da família (remover _M, _F)
                family_code = table.code
                if family_code.endswith('_M') or family_code.endswith('_F'):
                    family_code = family_code[:-2]
                
                if family_code not in table_families:
                    # Usar dados da primeira tábua da família para metadados
                    table_families[family_code] = {
                        "code": family_code,
                        "name": table.name.replace(" Masculina", "").replace(" Feminina", ""),
                        "description": table.description or "",
                        "source": table.source,
                        "is_official": table.is_official,
                        "regulatory_approved": table.regulatory_approved
                    }
            
            # Adicionar todas as famílias de tábuas
            tables_info.extend(table_families.values())
    
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
