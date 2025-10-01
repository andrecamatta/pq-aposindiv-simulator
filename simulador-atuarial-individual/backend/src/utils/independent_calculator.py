"""
Calculadora independente para validação cruzada dos cálculos atuariais
Implementa fórmulas manuais para comparar com o engine principal
"""

import math
import logging
from typing import Dict, List
from dataclasses import dataclass
from ..models.participant import (
    DEFAULT_SALARY_MONTHS_PER_YEAR,
    DEFAULT_BENEFIT_MONTHS_PER_YEAR,
    DEFAULT_CONTRIBUTION_RATE
)

logger = logging.getLogger(__name__)


@dataclass
class ScenarioParams:
    """Parâmetros do cenário atuarial"""
    current_age: int = 30
    retirement_age: int = 65
    salary_monthly: float = 8000.0
    salary_months_per_year: int = DEFAULT_SALARY_MONTHS_PER_YEAR
    contribution_rate: float = DEFAULT_CONTRIBUTION_RATE
    target_benefit_monthly: float = 8000.0
    benefit_months_per_year: int = DEFAULT_BENEFIT_MONTHS_PER_YEAR
    discount_rate_annual: float = 0.05
    salary_growth_real: float = 0.02
    admin_fee_rate: float = 0.01
    initial_balance: float = 0.0
    life_expectancy_at_retirement: float = 15.0  # anos adicionais aos 65


class IndependentActuarialCalculator:
    """Calculadora independente para validação de cálculos atuariais"""
    
    def __init__(self, params: ScenarioParams):
        self.params = params
        self.years_to_retirement = params.retirement_age - params.current_age
        self.discount_rate_monthly = (1 + params.discount_rate_annual) ** (1/12) - 1
        
    def calculate_independent_analysis(self) -> Dict:
        """Calcula análise atuarial independente completa"""

        logger.info("=" * 60)
        logger.info("🔍 ANÁLISE ATUARIAL INDEPENDENTE")
        logger.info("=" * 60)
        
        # 1. Cálculos básicos
        basic_calcs = self._calculate_basic_values()
        
        # 2. VPA das Contribuições  
        vpa_contributions = self._calculate_vpa_contributions_manual()
        
        # 3. VPA dos Benefícios
        vpa_benefits = self._calculate_vpa_benefits_manual()
        
        # 4. RMBA e Superávit
        rmba = vpa_benefits["vpa_total"] - vpa_contributions["vpa_total"]
        surplus = self.params.initial_balance - rmba
        
        # 5. Análise detalhada
        analysis = {
            "scenario_params": basic_calcs,
            "vpa_contributions": vpa_contributions,
            "vpa_benefits": vpa_benefits,
            "rmba": rmba,
            "surplus": surplus,
            "validation_checks": self._perform_validation_checks(vpa_contributions, vpa_benefits, rmba)
        }
        
        self._print_detailed_analysis(analysis)
        return analysis
    
    def _calculate_basic_values(self) -> Dict:
        """Calcula valores básicos do cenário"""
        annual_salary_initial = self.params.salary_monthly * self.params.salary_months_per_year
        annual_contribution_initial = annual_salary_initial * self.params.contribution_rate
        annual_benefit = self.params.target_benefit_monthly * self.params.benefit_months_per_year
        
        # Salário final (com crescimento)
        salary_growth_factor = (1 + self.params.salary_growth_real) ** self.years_to_retirement
        annual_salary_final = annual_salary_initial * salary_growth_factor
        
        basic = {
            "years_to_retirement": self.years_to_retirement,
            "annual_salary_initial": annual_salary_initial,
            "annual_salary_final": annual_salary_final,
            "annual_contribution_initial": annual_contribution_initial,
            "annual_benefit_target": annual_benefit,
            "replacement_rate_target": annual_benefit / annual_salary_final,
            "discount_rate_monthly": self.discount_rate_monthly,
            "life_expectancy": self.params.life_expectancy_at_retirement
        }
        
        return basic
    
    def _calculate_vpa_contributions_manual(self) -> Dict:
        """Calcula VPA das contribuições usando fórmulas manuais"""
        logger.info("\n📊 CALCULANDO VPA DAS CONTRIBUIÇÕES")

        # Contribuição inicial líquida (após taxa administrativa)
        monthly_contribution_initial = (self.params.salary_monthly * self.params.contribution_rate *
                                      (1 - self.params.admin_fee_rate))

        logger.info(f"Contribuição mensal inicial (líquida): R$ {monthly_contribution_initial:,.2f}")
        
        # Anuidade crescente com pagamentos mensais
        # Fórmula: Σ(t=0 to n-1) PMT₀ * (1+g)^t * (1+i)^(-t)
        
        total_months = self.years_to_retirement * 12
        monthly_growth_rate = (1 + self.params.salary_growth_real) ** (1/12) - 1
        
        vpa_total = 0.0
        vpa_details = []
        
        for month in range(total_months):
            year = month // 12
            
            # Contribuição crescente
            contribution_growth_factor = (1 + self.params.salary_growth_real) ** year
            monthly_contribution = monthly_contribution_initial * contribution_growth_factor
            
            # Fator de desconto
            discount_factor = (1 + self.discount_rate_monthly) ** (-month)
            
            # VPA desta contribuição
            pv_contribution = monthly_contribution * discount_factor
            vpa_total += pv_contribution
            
            if month < 5 or month % 60 == 0:  # Mostrar primeiros meses e alguns ao longo do tempo
                vpa_details.append({
                    "month": month,
                    "year": year,
                    "contribution": monthly_contribution,
                    "discount_factor": discount_factor,
                    "pv": pv_contribution
                })

        logger.info(f"VPA Total das Contribuições: R$ {vpa_total:,.2f}")

        return {
            "vpa_total": vpa_total,
            "monthly_contribution_initial": monthly_contribution_initial,
            "total_months": total_months,
            "sample_calculations": vpa_details[:5]  # Primeiros 5 meses como exemplo
        }
    
    def _calculate_vpa_benefits_manual(self) -> Dict:
        """Calcula VPA dos benefícios usando fórmulas manuais"""
        logger.info("\n📊 CALCULANDO VPA DOS BENEFÍCIOS")

        monthly_benefit = self.params.target_benefit_monthly
        logger.info(f"Benefício mensal: R$ {monthly_benefit:,.2f}")
        
        # Diferir por anos_to_retirement, depois anuidade vitalícia
        months_to_retirement = self.years_to_retirement * 12
        life_expectancy_months = self.params.life_expectancy_at_retirement * 12
        
        vpa_total = 0.0
        
        for month_in_retirement in range(int(life_expectancy_months)):
            total_month = months_to_retirement + month_in_retirement
            
            # Fator de desconto total (diferimento + período de benefício)
            discount_factor = (1 + self.discount_rate_monthly) ** (-total_month)
            
            # Assumindo mortalidade constante (simplificação)
            # Em uma análise real, usaríamos a tábua de mortalidade completa
            survival_probability = max(0, 1 - (month_in_retirement / life_expectancy_months))
            
            # VPA deste benefício
            pv_benefit = monthly_benefit * discount_factor * survival_probability
            vpa_total += pv_benefit

        logger.info(f"Meses até aposentadoria: {months_to_retirement}")
        logger.info(f"Expectativa de vida (meses): {life_expectancy_months}")
        logger.info(f"VPA Total dos Benefícios: R$ {vpa_total:,.2f}")
        
        return {
            "vpa_total": vpa_total,
            "monthly_benefit": monthly_benefit,
            "months_to_retirement": months_to_retirement,
            "life_expectancy_months": life_expectancy_months
        }
    
    def _perform_validation_checks(self, vpa_contrib: Dict, vpa_benefits: Dict, rmba: float) -> Dict:
        """Realiza verificações de validação dos resultados"""
        
        annual_contrib_total = vpa_contrib["vpa_total"] / self.years_to_retirement
        annual_benefit_total = vpa_benefits["vpa_total"] / self.params.life_expectancy_at_retirement
        
        checks = {
            "contribution_benefit_ratio": vpa_contrib["vpa_total"] / vpa_benefits["vpa_total"],
            "rmba_vs_annual_salary": abs(rmba) / (self.params.salary_monthly * 12),
            "benefit_coverage_ratio": annual_contrib_total / annual_benefit_total,
            "economic_reasonableness": "OK" if abs(rmba) < vpa_contrib["vpa_total"] * 0.5 else "ALERTA"
        }
        
        return checks
    
    def _print_detailed_analysis(self, analysis: Dict):
        """Imprime análise detalhada formatada"""

        logger.info("\n" + "=" * 60)
        logger.info("📋 RESUMO DA ANÁLISE INDEPENDENTE")
        logger.info("=" * 60)

        basic = analysis["scenario_params"]
        logger.info(f"⏰ Anos até aposentadoria: {basic['years_to_retirement']}")
        logger.info(f"💰 Salário anual inicial: R$ {basic['annual_salary_initial']:,.2f}")
        logger.info(f"💰 Salário anual final: R$ {basic['annual_salary_final']:,.2f}")
        logger.info(f"💸 Contribuição anual inicial: R$ {basic['annual_contribution_initial']:,.2f}")
        logger.info(f"🎯 Benefício anual alvo: R$ {basic['annual_benefit_target']:,.2f}")
        logger.info(f"📊 Taxa de reposição alvo: {basic['replacement_rate_target']:.1%}")

        logger.info(f"\n📈 VPA Contribuições: R$ {analysis['vpa_contributions']['vpa_total']:,.2f}")
        logger.info(f"📉 VPA Benefícios: R$ {analysis['vpa_benefits']['vpa_total']:,.2f}")
        logger.info(f"🧮 RMBA: R$ {analysis['rmba']:,.2f}")
        logger.info(f"💎 Superávit: R$ {analysis['surplus']:,.2f}")

        checks = analysis["validation_checks"]
        logger.info(f"\n🔍 VERIFICAÇÕES:")
        logger.info(f"   • Razão Contribuições/Benefícios: {checks['contribution_benefit_ratio']:.2f}")
        logger.info(f"   • RMBA vs Salário Anual: {checks['rmba_vs_annual_salary']:.2f}")
        logger.info(f"   • Cobertura Benefícios: {checks['benefit_coverage_ratio']:.2f}")
        logger.info(f"   • Razoabilidade Econômica: {checks['economic_reasonableness']}")

        logger.info("\n" + "=" * 60)


def run_independent_validation():
    """Executa validação independente com parâmetros padrão do sistema"""

    # Parâmetros idênticos ao caso base do sistema
    params = ScenarioParams(
        current_age=30,
        retirement_age=65,
        salary_monthly=8000.0,
        salary_months_per_year=13,
        contribution_rate=DEFAULT_CONTRIBUTION_RATE,
        target_benefit_monthly=8000.0,
        benefit_months_per_year=13,
        discount_rate_annual=0.05,
        salary_growth_real=0.02,
        admin_fee_rate=0.01,
        initial_balance=0.0,
        life_expectancy_at_retirement=15.0  # Estimativa para BR_EMS_2021, homem, 65 anos
    )
    
    calculator = IndependentActuarialCalculator(params)
    return calculator.calculate_independent_analysis()


if __name__ == "__main__":
    run_independent_validation()