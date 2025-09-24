"""
Factory para criação de calculadores de sensibilidade
Versão simplificada para resolver erros de import
"""

from ..sensitivity import (
    SensitivityCalculator,
    SensitivityEngine,
    SensitivityAnalyzer
)


class SensitivityCalculatorFactory:
    """Factory para criação de calculadores de sensibilidade"""

    @staticmethod
    def create_calculator() -> SensitivityCalculator:
        """Cria uma instância do calculador de sensibilidade"""
        return SensitivityCalculator()

    @staticmethod
    def create_engine() -> SensitivityEngine:
        """Cria uma instância do engine de sensibilidade"""
        return SensitivityEngine()

    @staticmethod
    def create_analyzer() -> SensitivityAnalyzer:
        """Cria uma instância do analisador de sensibilidade"""
        return SensitivityAnalyzer()

    def __init__(self):
        """Inicializa a factory"""
        self.calculator = self.create_calculator()
        self.engine = self.create_engine()
        self.analyzer = self.create_analyzer()

    def get_calculator(self) -> SensitivityCalculator:
        """Retorna instância do calculador"""
        return self.calculator

    def get_engine(self) -> SensitivityEngine:
        """Retorna instância do engine"""
        return self.engine

    def get_analyzer(self) -> SensitivityAnalyzer:
        """Retorna instância do analisador"""
        return self.analyzer