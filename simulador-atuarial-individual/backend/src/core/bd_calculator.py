"""
Calculadora especializada para planos BD (Benefício Definido)
Extrai lógica específica BD do ActuarialEngine
"""

import numpy as np
from typing import Dict, TYPE_CHECKING
from .projections import (
    calculate_salary_projections, 
    calculate_benefit_projections,
    calculate_contribution_projections,
    calculate_survival_probabilities,
    calculate_accumulated_reserves,
    convert_monthly_to_yearly_projections
)
from .mortality_tables import get_mortality_table
from ..utils import (
    calculate_vpa_benefits_contributions,
    calculate_sustainable_benefit,
    get_timing_adjustment,
    calculate_discount_factor,
    calculate_actuarial_present_value,
    get_payment_survival_probability,
    calculate_life_annuity_factor
)

if TYPE_CHECKING:
    from ..models.database import SimulatorState
    from .actuarial_engine import ActuarialContext


class BDCalculator:
    """Calculadora especializada para planos de Benefício Definido"""
    
    def __init__(self):
        self.cache = {}
    
    def calculate_projections(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        mortality_table: np.ndarray
    ) -> Dict:
        """
        Calcula projeções temporais para BD usando funções modulares
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            mortality_table: Tábua de mortalidade
            
        Returns:
            Dicionário com projeções mensais e anuais
        """
        total_months = context.total_months_projection
        
        # 1. Projeções salariais mensais
        monthly_salaries = calculate_salary_projections(context, state, total_months)
        
        # 2. Determinar benefício mensal alvo
        monthly_benefit_amount = self._calculate_target_benefit_amount(state, context, monthly_salaries)
        
        # 3. Projeções de benefícios mensais
        monthly_benefits = calculate_benefit_projections(context, state, total_months, monthly_benefit_amount)
        
        # 4. Projeções de contribuições mensais
        monthly_contributions = calculate_contribution_projections(monthly_salaries, state, context)
        
        # 5. Probabilidades de sobrevivência
        monthly_survival_probs = calculate_survival_probabilities(state, mortality_table, total_months)
        
        # 6. Evolução das reservas
        monthly_reserves = calculate_accumulated_reserves(
            state, context, monthly_contributions, monthly_benefits, total_months
        )
        
        # 7. Converter para dados anuais
        monthly_data = {
            "months": list(range(total_months)),
            "salaries": monthly_salaries,
            "benefits": monthly_benefits, 
            "contributions": monthly_contributions,
            "survival_probs": monthly_survival_probs,
            "reserves": monthly_reserves
        }
        
        yearly_data = convert_monthly_to_yearly_projections(monthly_data, total_months)
        yearly_data["monthly_data"] = monthly_data

        # 8. Gerar vetores por idade para frontend
        age_projections = self._generate_age_projections(
            state, context, monthly_salaries, monthly_benefits, total_months
        )
        yearly_data.update(age_projections)

        return yearly_data
    
    def calculate_rmba(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        projections: Dict
    ) -> float:
        """
        Calcula Reserva Matemática de Benefícios a Conceder (RMBA) para BD
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções calculadas
            
        Returns:
            Valor da RMBA
        """
        # Para pessoas já aposentadas, RMBA = 0 (não há benefícios futuros a conceder)
        if context.is_already_retired:
            print(f"[BD_RMBA] Pessoa aposentada: RMBA = 0")
            return 0.0
        
        # Para pessoas ativas: RMBA = VPA(Benefícios) - VPA(Contribuições)
        monthly_data = projections["monthly_data"]
        
        # Usar utilitário para calcular VPAs de benefícios e contribuições
        vpa_benefits, vpa_contributions = calculate_vpa_benefits_contributions(
            monthly_data["benefits"],
            monthly_data["contributions"],
            monthly_data["survival_probs"],
            context.discount_rate_monthly,
            context.payment_timing,
            context.months_to_retirement,
            context.admin_fee_monthly
        )
        
        print(f"[BD_RMBA] Pessoa ativa: VPA Benefícios = {vpa_benefits:.2f}, VPA Contrib = {vpa_contributions:.2f}")
        
        return vpa_benefits - vpa_contributions
    
    def calculate_rmbc(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        projections: Dict
    ) -> float:
        """
        Calcula Reserva Matemática de Benefícios Concedidos (RMBC) para BD
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções calculadas
            
        Returns:
            Valor da RMBC
        """
        # Para pessoas ativas, RMBC = 0 
        if not context.is_already_retired:
            print(f"[BD_RMBC] Pessoa ativa: RMBC = 0")
            return 0.0
        
        # Para pessoas aposentadas: RMBC = VPA dos benefícios restantes
        monthly_data = projections["monthly_data"]
        
        vpa_benefits = 0.0
        timing_adjustment = get_timing_adjustment(context.payment_timing)
        
        for month_idx, benefit in enumerate(monthly_data["benefits"]):
            if benefit > 0:  # Só benefícios positivos
                survival_prob = get_payment_survival_probability(
                    monthly_data["survival_probs"],
                    month_idx,
                    context.payment_timing
                )

                discount_factor = calculate_discount_factor(
                    context.discount_rate_monthly,
                    month_idx,
                    timing_adjustment
                )
                
                present_value = (benefit * survival_prob) / discount_factor
                vpa_benefits += present_value
        
        print(f"[BD_RMBC] Pessoa aposentada: RMBC = {vpa_benefits:.2f}")
        return vpa_benefits
    
    def calculate_normal_cost(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        projections: Dict
    ) -> float:
        """
        Calcula Custo Normal anual para BD
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções calculadas
            
        Returns:
            Custo Normal anual
        """
        months_to_retirement = context.months_to_retirement

        if months_to_retirement <= 0:
            return 0.0

        monthly_data = projections.get("monthly_data", {})
        survival_probs = monthly_data.get("survival_probs", [])

        if state.calculation_method == "PUC":
            # Projected Unit Credit: VPA do benefício incremental deste ano
            projected_final_salary = context.monthly_salary * (
                (1 + context.salary_growth_real_monthly) ** months_to_retirement
            )
            annual_benefit_increment = projected_final_salary * (state.accrual_rate / 100)
            monthly_benefit_increment = annual_benefit_increment / max(context.benefit_months_per_year, 1)

            # Taxa efetiva considerando que a taxa admin incide sobre o saldo
            # Taxa efetiva = (1 + retorno) / (1 + taxa_admin) - 1
            effective_discount_rate = (1 + context.discount_rate_monthly) / (1 + context.admin_fee_monthly) - 1
            effective_discount_rate = max(effective_discount_rate, -0.99)

            annuity_factor = calculate_life_annuity_factor(
                survival_probs,
                effective_discount_rate,
                context.payment_timing,
                start_month=months_to_retirement
            )

            return monthly_benefit_increment * annuity_factor

        # Entry Age Normal: custo uniforme proporcional ao salário esperado
        monthly_salaries = monthly_data.get("salaries", [])
        monthly_benefits = monthly_data.get("benefits", [])

        # VPA dos benefícios futuros (incluindo fase pós-aposentadoria)
        vpa_benefits = calculate_actuarial_present_value(
            monthly_benefits,
            survival_probs,
            context.discount_rate_monthly,
            context.payment_timing,
            start_month=context.months_to_retirement
        )

        # VPA dos salários futuros até a aposentadoria
        apv_future_salaries = calculate_actuarial_present_value(
            monthly_salaries,
            survival_probs,
            context.discount_rate_monthly,
            context.payment_timing,
            start_month=0,
            end_month=months_to_retirement
        )

        if apv_future_salaries <= 0:
            return 0.0

        # Recursos já existentes (saldo inicial) reduzem o passivo a financiar
        resources_available = state.initial_balance if hasattr(state, 'initial_balance') else 0.0

        # Custo total a financiar via contribuições niveladas
        total_cost_to_fund = max(vpa_benefits - resources_available, 0.0)

        level_rate = total_cost_to_fund / apv_future_salaries
        annual_salary_base = context.monthly_salary * context.salary_months_per_year
        return annual_salary_base * level_rate
    
    def calculate_key_metrics(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        projections: Dict
    ) -> Dict:
        """
        Calcula métricas-chave para BD
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções calculadas
            
        Returns:
            Dicionário com métricas calculadas
        """
        total_contributions = sum(projections["contributions"])
        total_benefits = sum(projections["benefits"])
        
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement

        if context.is_already_retired:
            final_salary_monthly_base = context.monthly_salary
        else:
            salary_growth_factor = (1 + context.salary_growth_real_monthly) ** max(months_to_retirement - 1, 0)
            final_salary_monthly_base = context.monthly_salary * salary_growth_factor
        
        # Benefício mensal base para comparação consistente - compatível com string ou enum
        if str(state.benefit_target_mode) == "REPLACEMENT_RATE":
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            benefit_monthly_base = final_salary_monthly_base * (replacement_rate / 100)
        else:  # VALUE mode
            benefit_monthly_base = state.target_benefit if state.target_benefit is not None else 0
        
        # Taxa de reposição real
        replacement_ratio = (benefit_monthly_base / final_salary_monthly_base * 100) if final_salary_monthly_base > 0 else 0
        
        # Taxa de reposição alvo - compatível com string ou enum
        if str(state.benefit_target_mode) == "REPLACEMENT_RATE":
            target_replacement_ratio = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
        else:
            target_replacement_ratio = (benefit_monthly_base / final_salary_monthly_base * 100) if final_salary_monthly_base > 0 else 0
        
        # Taxa de reposição sustentável usando utilitário
        sustainable_monthly_benefit = 0
        sustainable_replacement_ratio = 0
        
        if final_salary_monthly_base > 0:
            _, vpa_contributions = calculate_vpa_benefits_contributions(
                monthly_data["benefits"],
                monthly_data["contributions"],
                monthly_data["survival_probs"],
                context.discount_rate_monthly,
                context.payment_timing,
                context.months_to_retirement,
                context.admin_fee_monthly
            )
            
            sustainable_monthly_benefit = calculate_sustainable_benefit(
                state.initial_balance,
                vpa_contributions,
                monthly_data["survival_probs"],
                context.discount_rate_monthly,
                context.payment_timing,
                context.months_to_retirement,
                context.benefit_months_per_year,
                context.admin_fee_monthly
            )
            
            sustainable_replacement_ratio = (sustainable_monthly_benefit / final_salary_monthly_base * 100) if final_salary_monthly_base > 0 else 0
        
        return {
            "total_contributions": total_contributions,
            "total_benefits": total_benefits,
            "replacement_ratio": replacement_ratio,
            "target_replacement_ratio": target_replacement_ratio,
            "sustainable_replacement_ratio": sustainable_replacement_ratio
        }
    
    def calculate_sufficiency_analysis(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        projections: Dict, 
        metrics: Dict
    ) -> Dict:
        """
        Calcula análise de suficiência para BD
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções calculadas
            metrics: Métricas calculadas
            
        Returns:
            Dicionário com análise de suficiência
        """
        rmba = self.calculate_rmba(state, context, projections)
        deficit_surplus = state.initial_balance - rmba
        
        # Calcular VPA do benefício alvo para percentuais
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement
        mortality_table = get_mortality_table(state.mortality_table, state.gender, state.mortality_aggravation)
        
        # Obter benefício alvo mensal - compatível com string ou enum
        if str(state.benefit_target_mode) == "REPLACEMENT_RATE":
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            active_monthly_salaries = [s for s in monthly_data["salaries"] if s > 0]
            final_monthly_salary = active_monthly_salaries[-1] if active_monthly_salaries else context.monthly_salary
            monthly_target_benefit = final_monthly_salary * (replacement_rate / 100)
        else:
            monthly_target_benefit = state.target_benefit if state.target_benefit is not None else 0
        
        # Calcular VPA do benefício desejado
        target_benefit_apv = self._calculate_target_benefit_apv(
            state, context, monthly_target_benefit, mortality_table, months_to_retirement
        )
        
        # Percentual do déficit/superávit
        deficit_surplus_percentage = (deficit_surplus / target_benefit_apv * 100) if target_benefit_apv > 0 else 0
        
        # Taxa de contribuição necessária
        required_contribution_rate = 0
        if rmba > state.initial_balance:
            required_total_contributions = rmba - state.initial_balance
            
            apv_future_salaries = calculate_actuarial_present_value(
                monthly_data["salaries"],
                monthly_data["survival_probs"],
                context.discount_rate_monthly,
                context.payment_timing,
                start_month=0,
                end_month=months_to_retirement
            )
            
            required_contribution_rate = (required_total_contributions / apv_future_salaries * 100) if apv_future_salaries > 0 else 0
            required_contribution_rate = min(required_contribution_rate, 50)  # Máximo 50%
        
        return {
            "deficit_surplus": deficit_surplus,
            "deficit_surplus_percentage": deficit_surplus_percentage,
            "required_contribution_rate": required_contribution_rate
        }
    
    def _calculate_target_benefit_amount(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        monthly_salaries: list
    ) -> float:
        """Calcula valor do benefício mensal alvo baseado no modo configurado"""
        from ..models.database import BenefitTargetMode
        
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            months_to_retirement = context.months_to_retirement
            salary_growth_factor = (1 + context.salary_growth_real_monthly) ** max(months_to_retirement - 1, 0)
            final_salary_base = context.monthly_salary * salary_growth_factor
            return final_salary_base * (replacement_rate / 100)
        else:  # VALUE
            return state.target_benefit if state.target_benefit is not None else 0
    
    def _calculate_target_benefit_apv(
        self, 
        state: 'SimulatorState',
        context: 'ActuarialContext', 
        monthly_target_benefit: float,
        mortality_table: np.ndarray,
        months_to_retirement: int
    ) -> float:
        """Calcula VPA do benefício alvo como anuidade vitalícia mensal"""
        target_benefit_apv = 0.0
        cumulative_survival = 1.0
        
        # Calcular sobrevivência até aposentadoria
        for month in range(months_to_retirement):
            current_age_years = state.age + (month / 12)
            age_index = int(current_age_years)
            if age_index < len(mortality_table):
                q_x_annual = mortality_table[age_index]
                q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                p_x_monthly = 1 - q_x_monthly
                cumulative_survival *= p_x_monthly
            else:
                cumulative_survival = 0.0
                break
        
        survival_to_retirement = cumulative_survival
        
        # Calcular anuidade
        max_projection_age = state.age + state.projection_years
        max_months_after_retirement = (max_projection_age - state.retirement_age) * 12
        
        for month_after_retirement in range(max_months_after_retirement):
            total_month = months_to_retirement + month_after_retirement
            current_age_years = state.age + (total_month / 12)
            age_index = int(current_age_years)
            
            if age_index < len(mortality_table):
                if month_after_retirement == 0:
                    survival_prob = survival_to_retirement
                else:
                    q_x_annual = mortality_table[age_index - 1]
                    q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                    p_x_monthly = 1 - q_x_monthly
                    cumulative_survival *= p_x_monthly
                    survival_prob = cumulative_survival
                
                benefit_timing_adjustment = get_timing_adjustment(context.payment_timing)
                discount_factor = calculate_discount_factor(
                    context.discount_rate_monthly,
                    total_month,
                    benefit_timing_adjustment
                )
                present_value = (monthly_target_benefit * survival_prob) / discount_factor
                target_benefit_apv += present_value
            else:
                break
        
        return target_benefit_apv

    def _generate_age_projections(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        monthly_salaries: list,
        monthly_benefits: list,
        total_months: int
    ) -> Dict:
        """
        Gera vetores de projeção por idade para o frontend (BD)

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            monthly_salaries: Salários mensais calculados
            monthly_benefits: Benefícios mensais calculados
            total_months: Total de meses de projeção

        Returns:
            Dicionário com vetores por idade
        """
        projection_ages = []
        projected_salaries_by_age = []
        projected_benefits_by_age = []

        # Gerar lista de idades (apenas anos completos)
        for month in range(0, total_months, 12):  # A cada 12 meses (início de cada ano)
            age = state.age + (month // 12)
            projection_ages.append(age)

            # Para benefícios e salários, usar valor do primeiro mês do ano (mês base)
            if month < len(monthly_salaries):
                monthly_salary = monthly_salaries[month]
                monthly_benefit = monthly_benefits[month]

                # Converter para valores anuais considerando múltiplos pagamentos
                # Para salários: multiplicar pela quantidade de salários por ano
                annual_salary = monthly_salary * context.salary_months_per_year if monthly_salary > 0 else 0

                # Para benefícios: multiplicar pela quantidade de benefícios por ano
                annual_benefit = monthly_benefit * context.benefit_months_per_year if monthly_benefit > 0 else 0

                projected_salaries_by_age.append(annual_salary)
                projected_benefits_by_age.append(annual_benefit)
            else:
                projected_salaries_by_age.append(0.0)
                projected_benefits_by_age.append(0.0)

        return {
            "projection_ages": projection_ages,
            "projected_salaries_by_age": projected_salaries_by_age,
            "projected_benefits_by_age": projected_benefits_by_age
        }
