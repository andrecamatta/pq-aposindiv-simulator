"""
Gerenciamento de tábuas de decrementos múltiplos
Providencia infraestrutura para invalidez, rotatividade, divórcio, etc.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Union
import logging
import time
from dataclasses import dataclass

from ..models.participant import DecrementType
from ..models.database import DecrementTable
from .mortality_tables import MortalityTableCache  # Reutilizar cache existente

logger = logging.getLogger(__name__)


@dataclass
class MultiDecrementResult:
    """Resultado de cálculo de múltiplos decrementos"""
    survival_total: List[float]        # Sobrevivência total (permanece ativo)
    survival_mortality_only: List[float]  # Sobrevivência apenas mortalidade
    probability_disability: List[float]   # Probabilidade de entrada em invalidez
    survival_disabled: List[float]       # Sobrevivência como inválido
    decrement_probabilities: Dict[DecrementType, List[float]]  # Probabilidades por tipo


class DecrementTableManager:
    """
    Gerenciador centralizado para tábuas de decrementos múltiplos
    Utiliza cache otimizado e providencia interface unificada
    """

    def __init__(self):
        # Reutilizar sistema de cache da mortalidade
        self._cache = MortalityTableCache(max_entries=150, default_ttl=3600)
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_decrement_table(
        self,
        table_code: str,
        decrement_type: DecrementType,
        gender: str = "M",
        aggravation_pct: float = 0.0
    ) -> Optional[np.ndarray]:
        """
        Obtém tábua de decremento específica com cache otimizado

        Args:
            table_code: Código da tábua (ex: "UP84_DISABILITY")
            decrement_type: Tipo de decremento
            gender: Gênero ("M", "F", "UNISEX")
            aggravation_pct: Suavização percentual

        Returns:
            Array numpy com probabilidades de decremento por idade
        """
        # Chave de cache incluindo tipo de decremento
        cache_key = (table_code, decrement_type.value, gender, aggravation_pct)

        # Tentar obter do cache
        cached_table = self._cache.get(cache_key)
        if cached_table is not None:
            return cached_table

        # Carregar do banco de dados
        table_data = self._load_decrement_from_database(table_code, decrement_type, gender)
        if table_data is None:
            self._logger.warning(f"Tábua {table_code} tipo {decrement_type.value} não encontrada")
            return None

        # Aplicar suavização se necessário
        if aggravation_pct != 0.0:
            table_data = self._apply_decrement_aggravation(table_data, aggravation_pct)

        # Armazenar no cache
        self._cache.set(cache_key, table_data)
        return table_data

    def get_combined_probabilities(
        self,
        mortality_table_code: str,
        disability_table_code: Optional[str] = None,
        gender: str = "M",
        **kwargs
    ) -> Dict[str, np.ndarray]:
        """
        Obtém probabilidades combinadas de múltiplos decrementos

        Args:
            mortality_table_code: Código da tábua de mortalidade
            disability_table_code: Código da tábua de invalidez (opcional)
            gender: Gênero
            **kwargs: Outros parâmetros (turnover_table_code, etc.)

        Returns:
            Dicionário com arrays de probabilidades por tipo
        """
        result = {}

        # Mortalidade (sempre presente)
        mortality_table = self._get_mortality_table(mortality_table_code, gender)
        if mortality_table is not None:
            result[DecrementType.MORTALITY] = mortality_table

        # Invalidez (opcional)
        if disability_table_code:
            disability_table = self.get_decrement_table(
                disability_table_code, DecrementType.DISABILITY, gender
            )
            if disability_table is not None:
                result[DecrementType.DISABILITY] = disability_table

        # Extensível para outros decrementos
        for decrement_type in [DecrementType.TURNOVER, DecrementType.DIVORCE]:
            table_key = f"{decrement_type.value.lower()}_table_code"
            if table_key in kwargs and kwargs[table_key]:
                table = self.get_decrement_table(
                    kwargs[table_key], decrement_type, gender
                )
                if table is not None:
                    result[decrement_type] = table

        return result

    def apply_multiple_decrements(
        self,
        decrement_tables: Dict[DecrementType, np.ndarray],
        initial_age: int,
        total_months: int
    ) -> MultiDecrementResult:
        """
        Aplica múltiplos decrementos usando teoria atuarial

        Args:
            decrement_tables: Dicionário {tipo: array_probabilidades}
            initial_age: Idade inicial
            total_months: Total de meses de projeção

        Returns:
            Resultado com probabilidades combinadas
        """
        # Inicializar resultados
        survival_total = []
        survival_mortality_only = []
        probability_disability = []
        survival_disabled = []
        decrement_probs = {dt: [] for dt in decrement_tables.keys()}

        # Estado inicial
        cumulative_survival_total = 1.0
        cumulative_survival_mortality = 1.0
        cumulative_disabled_population = 0.0
        cumulative_disabled_survival = 1.0

        for month in range(total_months):
            current_age_years = initial_age + (month / 12)
            age_index = int(current_age_years)

            # === CÁLCULO DE DECREMENTOS INDEPENDENTES ===

            # Mortalidade base
            q_mortality = self._get_probability_at_age(
                decrement_tables.get(DecrementType.MORTALITY), age_index
            )
            q_mortality_monthly = self._annual_to_monthly_probability(q_mortality)

            # Invalidez (se presente)
            q_disability = 0.0
            if DecrementType.DISABILITY in decrement_tables:
                q_disability = self._get_probability_at_age(
                    decrement_tables[DecrementType.DISABILITY], age_index
                )
                q_disability_monthly = self._annual_to_monthly_probability(q_disability)
            else:
                q_disability_monthly = 0.0

            # === APLICAÇÃO DE MÚLTIPLOS DECREMENTOS ===

            # Sobrevivência apenas mortalidade
            p_mortality_monthly = 1 - q_mortality_monthly
            cumulative_survival_mortality *= p_mortality_monthly

            # Probabilidade de permanecer ativo (sem morrer nem ficar inválido)
            p_active_monthly = (1 - q_mortality_monthly) * (1 - q_disability_monthly)
            cumulative_survival_total *= p_active_monthly

            # Probabilidade de entrada em invalidez (sobrevive mas fica inválido)
            prob_disability_entry = (1 - q_mortality_monthly) * q_disability_monthly

            # Atualizar população inválida
            cumulative_disabled_population += cumulative_survival_total * q_disability_monthly

            # Mortalidade diferenciada para inválidos (assumir 1.5x maior por default)
            q_disabled_mortality = min(q_mortality * 1.5, 1.0)
            q_disabled_mortality_monthly = self._annual_to_monthly_probability(q_disabled_mortality)
            p_disabled_survival_monthly = 1 - q_disabled_mortality_monthly
            cumulative_disabled_survival *= p_disabled_survival_monthly

            # Armazenar resultados
            survival_total.append(cumulative_survival_total)
            survival_mortality_only.append(cumulative_survival_mortality)
            probability_disability.append(prob_disability_entry)
            survival_disabled.append(cumulative_disabled_survival)

            # Probabilidades por tipo
            decrement_probs[DecrementType.MORTALITY].append(q_mortality_monthly)
            if DecrementType.DISABILITY in decrement_probs:
                decrement_probs[DecrementType.DISABILITY].append(q_disability_monthly)

        return MultiDecrementResult(
            survival_total=survival_total,
            survival_mortality_only=survival_mortality_only,
            probability_disability=probability_disability,
            survival_disabled=survival_disabled,
            decrement_probabilities=decrement_probs
        )

    def validate_decrement_table(self, table_code: str, decrement_type: DecrementType) -> bool:
        """Valida se a tábua de decremento existe no banco"""
        try:
            from ..database import engine
            from sqlmodel import Session, select

            with Session(engine) as session:
                statement = select(DecrementTable).where(
                    DecrementTable.code == table_code,
                    DecrementTable.decrement_type == decrement_type,
                    DecrementTable.is_active == True
                )
                return session.exec(statement).first() is not None
        except Exception as e:
            self._logger.error(f"Erro ao validar tábua {table_code}: {e}")
            return False

    def get_available_tables(self, decrement_type: Optional[DecrementType] = None) -> List[Dict[str, Any]]:
        """Retorna lista de tábuas disponíveis"""
        try:
            from ..database import engine
            from sqlmodel import Session, select

            with Session(engine) as session:
                statement = select(DecrementTable).where(DecrementTable.is_active == True)

                if decrement_type:
                    statement = statement.where(DecrementTable.decrement_type == decrement_type)

                tables = session.exec(statement).all()

                return [
                    {
                        "code": table.code,
                        "name": table.name,
                        "decrement_type": table.decrement_type,
                        "description": table.description,
                        "gender": table.gender,
                        "is_official": table.is_official
                    }
                    for table in tables
                ]
        except Exception as e:
            self._logger.error(f"Erro ao listar tábuas: {e}")
            return []

    def clear_cache(self):
        """Limpa cache de tábuas"""
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        return self._cache.stats()

    # === MÉTODOS PRIVADOS ===

    def _load_decrement_from_database(
        self,
        table_code: str,
        decrement_type: DecrementType,
        gender: str
    ) -> Optional[np.ndarray]:
        """Carrega tábua de decremento do banco de dados"""
        try:
            from ..database import engine
            from sqlmodel import Session, select

            with Session(engine) as session:
                # Procurar tábua específica
                patterns = [table_code, f"{table_code}_{gender}"]

                for pattern in patterns:
                    statement = select(DecrementTable).where(
                        DecrementTable.code == pattern,
                        DecrementTable.decrement_type == decrement_type,
                        DecrementTable.is_active == True
                    )
                    table = session.exec(statement).first()

                    if table:
                        table_data_dict = table.get_table_data()
                        # Converter para numpy array
                        max_age = max(table_data_dict.keys()) if table_data_dict else 110
                        decrement_rates = np.zeros(max_age + 1)
                        for age, rate in table_data_dict.items():
                            decrement_rates[age] = rate
                        return decrement_rates

                return None
        except Exception as e:
            self._logger.error(f"Erro ao carregar tábua {table_code}: {e}")
            return None

    def _get_mortality_table(self, table_code: str, gender: str) -> Optional[np.ndarray]:
        """Obtém tábua de mortalidade usando sistema existente"""
        try:
            from .mortality_tables import get_mortality_table
            return get_mortality_table(table_code, gender)
        except Exception as e:
            self._logger.error(f"Erro ao obter tábua de mortalidade {table_code}: {e}")
            return None

    def _apply_decrement_aggravation(self, table: np.ndarray, aggravation_pct: float) -> np.ndarray:
        """Aplica suavização à tábua de decremento"""
        if aggravation_pct == 0.0:
            return table.copy()

        # Mesmo padrão da mortalidade: positivo = suavização (menos decremento)
        aggravation_factor = 1 - (aggravation_pct / 100)
        adjusted_table = table * aggravation_factor
        return np.clip(adjusted_table, 0.0, 1.0)

    def _get_probability_at_age(self, table: Optional[np.ndarray], age: int) -> float:
        """Obtém probabilidade de decremento na idade específica"""
        if table is None or age < 0 or age >= len(table):
            return 0.0
        return float(table[age])

    def _annual_to_monthly_probability(self, annual_prob: float) -> float:
        """Converte probabilidade anual para mensal"""
        if annual_prob <= 0:
            return 0.0
        if annual_prob >= 1:
            return 1.0
        return 1 - ((1 - annual_prob) ** (1/12))


# Instância global do gerenciador
_DECREMENT_MANAGER = DecrementTableManager()


def get_decrement_table(table_code: str, decrement_type: DecrementType, gender: str = "M") -> Optional[np.ndarray]:
    """Interface simplificada para obter tábua de decremento"""
    return _DECREMENT_MANAGER.get_decrement_table(table_code, decrement_type, gender)


def get_combined_probabilities(mortality_table: str, **decrement_tables) -> Dict[str, np.ndarray]:
    """Interface simplificada para obter probabilidades combinadas"""
    return _DECREMENT_MANAGER.get_combined_probabilities(mortality_table, **decrement_tables)


def apply_multiple_decrements(decrement_tables: Dict[DecrementType, np.ndarray], initial_age: int, total_months: int) -> MultiDecrementResult:
    """Interface simplificada para aplicar múltiplos decrementos"""
    return _DECREMENT_MANAGER.apply_multiple_decrements(decrement_tables, initial_age, total_months)


def validate_decrement_table(table_code: str, decrement_type: DecrementType) -> bool:
    """Interface simplificada para validar tábua"""
    return _DECREMENT_MANAGER.validate_decrement_table(table_code, decrement_type)


def get_available_decrement_tables(decrement_type: Optional[DecrementType] = None) -> List[Dict[str, Any]]:
    """Interface simplificada para listar tábuas disponíveis"""
    return _DECREMENT_MANAGER.get_available_tables(decrement_type)


def clear_decrement_cache():
    """Interface simplificada para limpar cache"""
    _DECREMENT_MANAGER.clear_cache()