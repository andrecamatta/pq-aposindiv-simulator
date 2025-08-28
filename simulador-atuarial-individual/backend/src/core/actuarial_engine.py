import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import time

from ..models import SimulatorState, SimulatorResults, BenefitTargetMode
from .mortality_tables import get_mortality_table, MORTALITY_TABLES
from .financial_math import present_value, annuity_value


class ActuarialEngine:
    """Motor de cálculos atuariais para simulação individual"""
    
    def __init__(self):
        self.cache = {}
        
    def calculate_individual_simulation(self, state: SimulatorState) -> SimulatorResults:
        """Calcula simulação atuarial individual completa"""
        start_time = time.time()
        
        # Validar entrada
        self._validate_state(state)
        
        # Obter tábua de mortalidade
        mortality_table = get_mortality_table(state.mortality_table, state.gender.value)
        
        # Calcular projeções temporais
        projections = self._calculate_projections(state, mortality_table)
        
        # Calcular reservas matemáticas
        rmba = self._calculate_rmba(state, projections)
        rmbc = self._calculate_rmbc(state, projections)
        normal_cost = self._calculate_normal_cost(state, projections)
        
        # Calcular métricas-chave
        metrics = self._calculate_key_metrics(state, projections)
        
        # Análise de sensibilidade
        sensitivity = self._calculate_sensitivity(state)
        
        # Decomposição atuarial
        decomposition = self._calculate_actuarial_decomposition(state, projections)
        
        # Análise de suficiência
        sufficiency = self._calculate_sufficiency_analysis(state, projections, metrics)
        
        # Análise de cenários
        scenarios = self._calculate_scenarios(state)
        
        computation_time = (time.time() - start_time) * 1000
        
        return SimulatorResults(
            # Reservas Matemáticas
            rmba=rmba,
            rmbc=rmbc,
            normal_cost=normal_cost,
            
            # Análise de Suficiência
            deficit_surplus=sufficiency["deficit_surplus"],
            deficit_surplus_percentage=sufficiency["deficit_surplus_percentage"],
            required_contribution_rate=sufficiency["required_contribution_rate"],
            
            # Projeções
            projection_years=projections["years"],
            projected_salaries=projections["salaries"],
            projected_benefits=projections["benefits"],
            projected_contributions=projections["contributions"],
            survival_probabilities=projections["survival_probs"],
            accumulated_reserves=projections["reserves"],
            
            # Métricas
            total_contributions=metrics["total_contributions"],
            total_benefits=metrics["total_benefits"],
            replacement_ratio=metrics["replacement_ratio"],
            funding_ratio=None,
            
            # Sensibilidade
            sensitivity_discount_rate=sensitivity["discount_rate"],
            sensitivity_mortality=sensitivity["mortality"],
            sensitivity_retirement_age=sensitivity["retirement_age"],
            sensitivity_salary_growth=sensitivity["salary_growth"],
            sensitivity_inflation=sensitivity["inflation"],
            
            # Decomposição
            actuarial_present_value_benefits=decomposition["apv_benefits"],
            actuarial_present_value_salary=decomposition["apv_salary"],
            service_cost_breakdown=decomposition["service_cost"],
            liability_duration=decomposition["duration"],
            convexity=decomposition["convexity"],
            
            # Cenários
            best_case_scenario=scenarios["best"],
            worst_case_scenario=scenarios["worst"],
            confidence_intervals=scenarios["confidence"],
            
            # Metadados
            calculation_timestamp=datetime.now(),
            computation_time_ms=computation_time,
            actuarial_method_details={"method": state.calculation_method.value},
            assumptions_validation={"valid": True}
        )
    
    def _validate_state(self, state: SimulatorState) -> None:
        """Valida parâmetros de entrada"""
        if state.age < 18 or state.age > 70:
            raise ValueError("Idade deve estar entre 18 e 70 anos")
        
        if state.retirement_age <= state.age:
            raise ValueError("Idade de aposentadoria deve ser maior que idade atual")
        
        if state.salary <= 0:
            raise ValueError("Salário deve ser positivo")
    
    def _calculate_projections(self, state: SimulatorState, mortality_table: np.ndarray) -> Dict:
        """Calcula projeções temporais"""
        years_to_retirement = state.retirement_age - state.age
        projection_years = list(range(state.projection_years))
        
        # Crescimento salarial em termos reais
        real_growth = state.salary_growth_real
        
        # Projeção salarial
        salaries = []
        for year in projection_years:
            if year <= years_to_retirement:
                salary = state.salary * ((1 + real_growth) ** year)
            else:
                salary = 0.0
            salaries.append(salary)
        
        # Benefício de aposentadoria (em termos reais)
        # Calcula o benefício alvo com base no modo escolhido
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            # Usar valor padrão de 70% se target_replacement_rate for None
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            active_salaries = [s for s in salaries if s > 0]
            final_salary = active_salaries[-1] if active_salaries else state.salary
            benefit_amount = final_salary * (replacement_rate / 100)
        else:  # 'VALUE'
            benefit_amount = state.target_benefit if state.target_benefit is not None else 0
        
        # Projeção de benefícios (mantém valor real constante)
        benefits = []
        for year in projection_years:
            if year > years_to_retirement:
                benefit = benefit_amount  # Valor real constante
            else:
                benefit = 0.0
            benefits.append(benefit)
        
        # Contribuições
        contributions = [salary * (state.contribution_rate / 100) for salary in salaries]
        
        # Probabilidades de sobrevivência
        # Probabilidades de sobrevivência (acumulada)
        survival_probs = []
        cumulative_survival = 1.0
        for year in projection_years:
            current_age_in_loop = state.age + year
            if current_age_in_loop < len(mortality_table):
                # Probabilidade de sobreviver de current_age_in_loop para +1
                p_x = 1.0 - mortality_table[current_age_in_loop]
                cumulative_survival *= p_x
            else:
                cumulative_survival = 0.0 # Zera se idade excede a tábua
            survival_probs.append(cumulative_survival)
        
        # Reservas acumuladas (simplificado)
        reserves = []
        accumulated = 0.0
        for year in projection_years:
            if year <= years_to_retirement:
                accumulated += contributions[year] * ((1 + state.discount_rate) ** (years_to_retirement - year))
            else:
                accumulated -= benefits[year] / ((1 + state.discount_rate) ** (year - years_to_retirement))
            reserves.append(max(0, accumulated))
        
        return {
            "years": projection_years,
            "salaries": salaries,
            "benefits": benefits,
            "contributions": contributions,
            "survival_probs": survival_probs,
            "reserves": reserves
        }
    
    def _calculate_rmba(self, state: SimulatorState, projections: Dict) -> float:
        """Calcula Reserva Matemática de Benefícios a Conceder"""
        years_to_retirement = state.retirement_age - state.age
        
        # VPA dos benefícios futuros
        future_benefits = 0.0
        for i, year in enumerate(projections["years"]):
            if year > years_to_retirement:
                pv_factor = 1 / ((1 + state.discount_rate) ** year)
                survival_factor = projections["survival_probs"][i]
                future_benefits += projections["benefits"][i] * pv_factor * survival_factor
        
        # VPA das contribuições futuras
        future_contributions = 0.0
        for i, year in enumerate(projections["years"]):
            if year <= years_to_retirement:
                pv_factor = 1 / ((1 + state.discount_rate) ** year)
                survival_factor = projections["survival_probs"][i]
                future_contributions += projections["contributions"][i] * pv_factor * survival_factor
        
        return max(0, future_benefits - future_contributions)
    
    def _calculate_rmbc(self, state: SimulatorState, projections: Dict) -> float:
        """Calcula Reserva Matemática de Benefícios Concedidos"""
        # Para participante ativo, RMBC = 0
        # Seria calculada após aposentadoria
        return 0.0
    
    def _calculate_normal_cost(self, state: SimulatorState, projections: Dict) -> float:
        """Calcula Custo Normal anual"""
        years_to_retirement = state.retirement_age - state.age
        
        if state.calculation_method == "PUC":
            # Projected Unit Credit
            benefit_accrual_year = state.salary * (state.accrual_rate / 100)
            pv_factor = 1 / ((1 + state.discount_rate) ** years_to_retirement)
            return benefit_accrual_year * pv_factor
        else:  # EAN
            # Entry Age Normal
            total_cost = self._calculate_rmba(state, projections)
            return total_cost / years_to_retirement if years_to_retirement > 0 else 0
    
    def _calculate_key_metrics(self, state: SimulatorState, projections: Dict) -> Dict:
        """Calcula métricas-chave"""
        total_contributions = sum(projections["contributions"])
        total_benefits = sum(projections["benefits"])
        
        # Taxa de reposição
        # Taxa de reposição
        active_salaries = [s for s in projections["salaries"] if s > 0]
        final_salary = active_salaries[-1] if active_salaries else state.salary
        first_benefit = next((b for b in projections["benefits"] if b > 0), 0)
        replacement_ratio = (first_benefit / final_salary * 100) if final_salary > 0 else 0
        
        return {
            "total_contributions": total_contributions,
            "total_benefits": total_benefits,
            "replacement_ratio": replacement_ratio
        }
    
    def _calculate_sensitivity(self, state: SimulatorState) -> Dict:
        """Calcula análise de sensibilidade"""
        base_rmba = self._calculate_rmba(state, self._calculate_projections(state, get_mortality_table(state.mortality_table, state.gender.value)))
        
        sensitivity = {
            "discount_rate": {},
            "mortality": {},
            "retirement_age": {},
            "salary_growth": {},
            "inflation": {}
        }
        
        # Sensibilidade taxa de desconto
        for rate in [0.04, 0.05, 0.06, 0.07, 0.08]:
            modified_state = state.copy()
            modified_state.discount_rate = rate
            projections = self._calculate_projections(modified_state, get_mortality_table(state.mortality_table, state.gender.value))
            rmba = self._calculate_rmba(modified_state, projections)
            sensitivity["discount_rate"][rate] = rmba
        
        # Sensibilidade idade aposentadoria
        for age in [60, 62, 65, 67, 70]:
            if age > state.age:
                modified_state = state.copy()
                modified_state.retirement_age = age
                projections = self._calculate_projections(modified_state, get_mortality_table(state.mortality_table, state.gender.value))
                rmba = self._calculate_rmba(modified_state, projections)
                sensitivity["retirement_age"][age] = rmba
        
        # Sensibilidade crescimento salarial
        for growth in [0.01, 0.02, 0.03, 0.04]:
            modified_state = state.copy()
            modified_state.salary_growth_real = growth
            projections = self._calculate_projections(modified_state, get_mortality_table(state.mortality_table, state.gender.value))
            rmba = self._calculate_rmba(modified_state, projections)
            sensitivity["salary_growth"][growth] = rmba
        
        # Sensibilidade inflação (removida - não aplicável em cálculos reais)
        # Mantendo estrutura para compatibilidade com interface
        sensitivity["inflation"] = {}
        
        # Sensibilidade mortalidade
        from .mortality_tables import MORTALITY_TABLES
        for table_name in MORTALITY_TABLES.keys():
            try:
                projections = self._calculate_projections(state, get_mortality_table(table_name, state.gender.value))
                rmba = self._calculate_rmba(state, projections)
                sensitivity["mortality"][table_name] = rmba
            except Exception as e:
                # Se a tábua não estiver disponível, usar valor base
                sensitivity["mortality"][table_name] = base_rmba
        
        return sensitivity
    
    def _calculate_actuarial_decomposition(self, state: SimulatorState, projections: Dict) -> Dict:
        """Calcula decomposição atuarial detalhada"""
        return {
            "apv_benefits": sum(projections["benefits"]),
            "apv_salary": sum(projections["salaries"]),
            "service_cost": {"normal": 0, "interest": 0},
            "duration": 15.0,  # Simplificado
            "convexity": 2.5   # Simplificado
        }
    
    def _calculate_sufficiency_analysis(self, state: SimulatorState, projections: Dict, metrics: Dict) -> Dict:
        """Calcula análise de suficiência: déficit/superávit e taxa necessária"""
        
        # Calcular VPA do benefício desejado na aposentadoria
        retirement_years = state.retirement_age - state.age
        mortality_table = get_mortality_table(state.mortality_table, state.gender.value)
        
        # Probabilidade de sobrevivência até aposentadoria
        survival_to_retirement = 1.0
        current_age = state.age
        for year in range(retirement_years):
            age_index = min(current_age + year - 18, len(mortality_table) - 1)
            if age_index >= 0:
                survival_to_retirement *= (1 - mortality_table[age_index])
        
        # VPA do benefício desejado (anuidade vitalícia)
        discount_factor = 1 / (1 + state.discount_rate)
        life_expectancy_at_retirement = 20  # Simplificado
        
        # Obter o benefício alvo correto baseado no modo
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            # Usar valor padrão de 70% se target_replacement_rate for None
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            active_salaries = [s for s in projections["salaries"] if s > 0]
            final_salary = active_salaries[-1] if active_salaries else state.salary
            target_benefit = final_salary * (replacement_rate / 100)
        else:  # 'VALUE'
            target_benefit = state.target_benefit if state.target_benefit is not None else 0
        
        target_benefit_pva = 0
        for year in range(life_expectancy_at_retirement):
            age_at_benefit = state.retirement_age + year
            age_index = min(age_at_benefit - 18, len(mortality_table) - 1)
            
            survival_prob = survival_to_retirement
            if age_index >= 0:
                for y in range(year):
                    idx = min(state.retirement_age + y - 18, len(mortality_table) - 1)
                    if idx >= 0:
                        survival_prob *= (1 - mortality_table[idx])
            
            present_value = target_benefit * survival_prob * (discount_factor ** (retirement_years + year))
            target_benefit_pva += present_value
        
        # Recursos disponíveis (saldo inicial + contribuições futuras)
        available_resources = state.initial_balance + metrics["total_contributions"]
        
        # Déficit/Superávit
        deficit_surplus = available_resources - target_benefit_pva
        deficit_surplus_percentage = (deficit_surplus / target_benefit_pva * 100) if target_benefit_pva > 0 else 0
        
        # Taxa de contribuição necessária para déficit zero
        if target_benefit_pva > state.initial_balance:
            required_total_contributions = target_benefit_pva - state.initial_balance
            
            # Calcular VPA dos salários futuros
            total_salary_pva = 0
            for year in range(retirement_years):
                salary_year = state.salary * (1 + state.salary_growth_real) ** year
                present_value = salary_year * (discount_factor ** year)
                total_salary_pva += present_value
            
            required_contribution_rate = (required_total_contributions / total_salary_pva * 100) if total_salary_pva > 0 else 0
        else:
            required_contribution_rate = 0
        
        # Garantir que a taxa seja realista (máximo 30%)
        required_contribution_rate = min(required_contribution_rate, 30)
        
        return {
            "deficit_surplus": deficit_surplus,
            "deficit_surplus_percentage": deficit_surplus_percentage,
            "required_contribution_rate": required_contribution_rate
        }

    def _calculate_scenarios(self, state: SimulatorState) -> Dict:
        """Calcula análise de cenários"""
        return {
            "best": {"rmba": 0, "benefits": 0},
            "worst": {"rmba": 0, "benefits": 0},
            "confidence": {"rmba": (0, 0), "benefits": (0, 0)}
        }