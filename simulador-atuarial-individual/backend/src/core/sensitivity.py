"""
Módulo de análise de sensibilidade para simulações atuariais
Versão simplificada para resolver erros de import
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class SensitivityResult:
    """Resultado de análise de sensibilidade"""
    parameter: str
    base_value: float
    test_value: float
    impact_percent: float
    new_result: Any


class SensitivityAnalyzer:
    """Analisador de sensibilidade simplificado"""

    def __init__(self):
        self.parameters = []

    def analyze_parameter(self, parameter: str, base_value: float, test_values: List[float], calculation_func) -> List[SensitivityResult]:
        """Analisa sensibilidade de um parâmetro"""
        results = []

        # Calcular resultado base
        base_result = calculation_func(base_value)

        for test_value in test_values:
            # Calcular resultado com valor teste
            test_result = calculation_func(test_value)

            # Calcular impacto percentual
            if hasattr(base_result, 'monthly_income') and hasattr(test_result, 'monthly_income'):
                base_income = base_result.monthly_income
                test_income = test_result.monthly_income
                impact = ((test_income - base_income) / base_income * 100) if base_income != 0 else 0
            else:
                impact = 0

            results.append(SensitivityResult(
                parameter=parameter,
                base_value=base_value,
                test_value=test_value,
                impact_percent=impact,
                new_result=test_result
            ))

        return results

    def generate_report(self, results: List[SensitivityResult]) -> Dict[str, Any]:
        """Gera relatório de sensibilidade"""
        return {
            "parameter_count": len(results),
            "max_impact": max([abs(r.impact_percent) for r in results]) if results else 0,
            "results": [
                {
                    "parameter": r.parameter,
                    "base_value": r.base_value,
                    "test_value": r.test_value,
                    "impact_percent": r.impact_percent
                }
                for r in results
            ]
        }


# Classes simplificadas para compatibilidade
class SensitivityCalculator:
    """Calculador de sensibilidade simplificado"""

    def __init__(self):
        self.analyzer = SensitivityAnalyzer()

    def calculate_discount_rate_sensitivity(self, state, context) -> Dict:
        """Calcula sensibilidade da taxa de desconto"""
        return {"discount_rate": "analysis_placeholder"}

    def calculate_mortality_sensitivity(self, state, context) -> Dict:
        """Calcula sensibilidade da mortalidade"""
        return {"mortality": "analysis_placeholder"}

    def calculate_salary_growth_sensitivity(self, state, context) -> Dict:
        """Calcula sensibilidade do crescimento salarial"""
        return {"salary_growth": "analysis_placeholder"}


class SensitivityEngine:
    """Engine de sensibilidade simplificado"""

    def __init__(self):
        self.calculator = SensitivityCalculator()

    def run_full_analysis(self, state, context) -> Dict:
        """Executa análise completa de sensibilidade"""
        return {
            "discount_rate": self.calculator.calculate_discount_rate_sensitivity(state, context),
            "mortality": self.calculator.calculate_mortality_sensitivity(state, context),
            "salary_growth": self.calculator.calculate_salary_growth_sensitivity(state, context)
        }