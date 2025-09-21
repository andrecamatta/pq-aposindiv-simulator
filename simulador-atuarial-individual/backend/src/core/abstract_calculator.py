"""
Classe base abstrata para todas as calculadoras atuariais.
Consolida lógica comum e estabelece padrões para implementações específicas.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
import hashlib
import json
import logging

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .actuarial_engine import ActuarialContext

logger = logging.getLogger(__name__)


class AbstractCalculator(ABC):
    """Classe base para todas as calculadoras atuariais especializadas"""

    def __init__(self):
        """Inicializa cache e configurações comuns"""
        self.cache: Dict[str, Any] = {}
        self._cache_enabled = True
        self._logger = logging.getLogger(self.__class__.__name__)

    def _generate_cache_key(self, *args, **kwargs) -> str:
        """Gera chave única para cache baseada nos parâmetros"""
        try:
            # Criar uma representação determinística dos argumentos
            cache_data = {
                'args': str(args),
                'kwargs': sorted(kwargs.items()) if kwargs else None,
                'class': self.__class__.__name__
            }
            cache_str = json.dumps(cache_data, sort_keys=True)
            return hashlib.md5(cache_str.encode()).hexdigest()
        except Exception:
            # Fallback para chave simples se serialização falhar
            return f"{self.__class__.__name__}_{id(args)}_{id(kwargs)}"

    def _get_from_cache(self, cache_key: str) -> Any:
        """Recupera valor do cache se disponível"""
        if not self._cache_enabled:
            return None
        return self.cache.get(cache_key)

    def _set_cache(self, cache_key: str, value: Any) -> None:
        """Armazena valor no cache"""
        if self._cache_enabled:
            self.cache[cache_key] = value

    def clear_cache(self) -> None:
        """Limpa todo o cache da calculadora"""
        self.cache.clear()
        self._logger.debug("Cache limpo")

    def disable_cache(self) -> None:
        """Desabilita o sistema de cache"""
        self._cache_enabled = False
        self.clear_cache()

    def enable_cache(self) -> None:
        """Habilita o sistema de cache"""
        self._cache_enabled = True

    def _validate_state(self, state: 'SimulatorState') -> None:
        """Validação comum de estado para todas as calculadoras"""
        if not state:
            raise ValueError("Estado do simulador não pode ser None")

        if state.age < 18 or state.age > 100:
            raise ValueError(f"Idade inválida: {state.age}")

        if state.retirement_age <= state.age:
            raise ValueError(f"Idade de aposentadoria ({state.retirement_age}) deve ser maior que idade atual ({state.age})")

        if state.salary <= 0:
            raise ValueError(f"Salário deve ser positivo: {state.salary}")

    def _validate_context(self, context: 'ActuarialContext') -> None:
        """Validação comum de contexto atuarial"""
        if not context:
            raise ValueError("Contexto atuarial não pode ser None")

        if context.discount_rate_monthly < 0:
            raise ValueError(f"Taxa de desconto mensal inválida: {context.discount_rate_monthly}")

        if context.months_to_retirement <= 0:
            raise ValueError(f"Meses até aposentadoria inválido: {context.months_to_retirement}")

    @abstractmethod
    def calculate(self, state: 'SimulatorState', context: 'ActuarialContext') -> Dict[str, Any]:
        """
        Método principal de cálculo que deve ser implementado por cada calculadora.

        Args:
            state: Estado atual do simulador
            context: Contexto atuarial com taxas e períodos

        Returns:
            Dicionário com resultados dos cálculos específicos
        """
        pass

    def calculate_with_cache(self, state: 'SimulatorState', context: 'ActuarialContext') -> Dict[str, Any]:
        """
        Wrapper que implementa cache automático para o método calculate.

        Args:
            state: Estado atual do simulador
            context: Contexto atuarial

        Returns:
            Resultados do cálculo (do cache ou recém-calculados)
        """
        # Validações comum
        self._validate_state(state)
        self._validate_context(context)

        # Gerar chave de cache
        cache_key = self._generate_cache_key(
            state.model_dump() if hasattr(state, 'model_dump') else str(state),
            context.__dict__ if hasattr(context, '__dict__') else str(context)
        )

        # Tentar recuperar do cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            self._logger.debug(f"Resultado recuperado do cache: {cache_key[:8]}...")
            return cached_result

        # Calcular novo resultado
        self._logger.debug(f"Calculando novo resultado: {cache_key[:8]}...")
        result = self.calculate(state, context)

        # Armazenar no cache
        self._set_cache(cache_key, result)

        return result

    def __str__(self) -> str:
        """Representação string da calculadora"""
        return f"{self.__class__.__name__}(cache_size={len(self.cache)})"

    def __repr__(self) -> str:
        """Representação técnica da calculadora"""
        return f"{self.__class__.__name__}(cache_enabled={self._cache_enabled}, cache_size={len(self.cache)})"