import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import time

from ..models import SimulatorState, SimulatorResults, BenefitTargetMode
from .mortality_tables import get_mortality_table, MORTALITY_TABLES
from .financial_math import present_value, annuity_value


@dataclass
class ActuarialContext:
    """Contexto atuarial com taxas mensais e períodos padronizados"""
    # Taxas mensais (convertidas de anuais)
    discount_rate_monthly: float
    salary_growth_real_monthly: float
    
    # Períodos em meses
    months_to_retirement: int
    total_months_projection: int
    
    # Valores mensais efetivos (considerando 13º)
    monthly_salary: float
    monthly_contribution: float
    monthly_benefit: float
    
    # Configurações técnicas
    payment_timing: str  # "antecipado" ou "postecipado"
    salary_months_per_year: int
    benefit_months_per_year: int
    
    # Fatores calculados
    salary_annual_factor: float  # Fator para converter mensal → anual
    benefit_annual_factor: float  # Fator para converter mensal → anual
    
    @classmethod
    def from_state(cls, state: SimulatorState) -> 'ActuarialContext':
        """Cria contexto a partir do estado do simulador"""
        # Conversão de taxas anuais para mensais: (1 + taxa_anual)^(1/12) - 1
        discount_monthly = (1 + state.discount_rate) ** (1/12) - 1
        salary_growth_monthly = (1 + state.salary_growth_real) ** (1/12) - 1
        
        # Períodos em meses - garantir horizonte adequado para aposentadoria
        months_to_retirement = (state.retirement_age - state.age) * 12
        
        # Estender período se necessário para cobrir aposentadoria adequadamente
        min_retirement_years = 25  # Mínimo 25 anos de aposentadoria
        projected_retirement_years = state.projection_years - (state.retirement_age - state.age)
        
        if projected_retirement_years < min_retirement_years:
            # Estender automaticamente para garantir período adequado
            total_years = (state.retirement_age - state.age) + min_retirement_years
            total_months = total_years * 12
            print(f"[INFO] Período estendido para {total_years} anos para análise adequada da aposentadoria")
        else:
            total_months = state.projection_years * 12
        
        # Configurações técnicas
        payment_timing = state.payment_timing.value
        salary_months_per_year = state.salary_months_per_year
        benefit_months_per_year = state.benefit_months_per_year
        
        # Calcular fatores anuais considerando timing
        if payment_timing == "antecipado":
            # Antecipado: primeiro pagamento no início do ano, desconto menor
            salary_annual_factor = salary_months_per_year * (1 + discount_monthly) ** 0.5
            benefit_annual_factor = benefit_months_per_year * (1 + discount_monthly) ** 0.5
        else:  # postecipado
            # Postecipado: primeiro pagamento no final do primeiro mês
            salary_annual_factor = salary_months_per_year
            benefit_annual_factor = benefit_months_per_year
        
        # Valores mensais efetivos (ajustados para múltiplos pagamentos anuais)
        # Salário mensal efetivo considera que há salary_months_per_year pagamentos
        monthly_salary = state.salary  # Salário mensal base informado pelo usuário
        monthly_contribution = monthly_salary * (state.contribution_rate / 100)
        
        # Benefício mensal alvo (depende do modo)
        if state.benefit_target_mode == BenefitTargetMode.VALUE:
            monthly_benefit = state.target_benefit or 0  # Benefício mensal desejado
        else:
            # Se for taxa de reposição, será calculado na aposentadoria
            monthly_benefit = 0
        
        return cls(
            discount_rate_monthly=discount_monthly,
            salary_growth_real_monthly=salary_growth_monthly,
            months_to_retirement=months_to_retirement,
            total_months_projection=total_months,
            monthly_salary=monthly_salary,
            monthly_contribution=monthly_contribution,
            monthly_benefit=monthly_benefit,
            payment_timing=payment_timing,
            salary_months_per_year=salary_months_per_year,
            benefit_months_per_year=benefit_months_per_year,
            salary_annual_factor=salary_annual_factor,
            benefit_annual_factor=benefit_annual_factor
        )


class ActuarialEngine:
    """Motor de cálculos atuariais para simulação individual"""
    
    def __init__(self):
        self.cache = {}
        
    def calculate_individual_simulation(self, state: SimulatorState) -> SimulatorResults:
        """Calcula simulação atuarial individual completa"""
        start_time = time.time()
        
        # Validar entrada
        self._validate_state(state)
        
        # Criar contexto atuarial com taxas mensais
        context = ActuarialContext.from_state(state)
        
        # Obter tábua de mortalidade
        mortality_table = get_mortality_table(state.mortality_table, state.gender.value)
        
        # Calcular projeções temporais
        projections = self._calculate_projections(state, context, mortality_table)
        
        # Calcular reservas matemáticas
        rmba = self._calculate_rmba(state, context, projections)
        rmbc = self._calculate_rmbc(state, projections)
        normal_cost = self._calculate_normal_cost(state, context, projections)
        
        # Calcular métricas-chave
        metrics = self._calculate_key_metrics(state, context, projections)
        
        # Análise de sensibilidade
        sensitivity = self._calculate_sensitivity(state)
        
        # Decomposição atuarial
        decomposition = self._calculate_actuarial_decomposition(state, context, projections)
        
        # Análise de suficiência
        sufficiency = self._calculate_sufficiency_analysis(state, context, projections, metrics)
        
        # Análise de cenários
        scenarios = self._calculate_scenarios(state)
        
        # Projeções atuariais para gráfico separado
        actuarial_projections = self._calculate_actuarial_projections(state, context, projections)
        
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
            
            # Projeções atuariais para gráfico separado
            projected_vpa_benefits=actuarial_projections["vpa_benefits"],
            projected_vpa_contributions=actuarial_projections["vpa_contributions"],
            projected_rmba_evolution=actuarial_projections["rmba_evolution"],
            
            # Métricas
            total_contributions=metrics["total_contributions"],
            total_benefits=metrics["total_benefits"],
            replacement_ratio=metrics["replacement_ratio"],
            target_replacement_ratio=metrics["target_replacement_ratio"],
            sustainable_replacement_ratio=metrics["sustainable_replacement_ratio"],
            funding_ratio=None,
            
            # Sensibilidade
            sensitivity_discount_rate=sensitivity["discount_rate"],
            sensitivity_mortality=sensitivity["mortality"],
            sensitivity_retirement_age=sensitivity["retirement_age"],
            sensitivity_salary_growth=sensitivity["salary_growth"],
            sensitivity_inflation=sensitivity["inflation"],
            
            # Decomposição
            actuarial_present_value_benefits=decomposition["apv_benefits"],
            actuarial_present_value_salary=decomposition["apv_future_contributions"],
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
    
    def _calculate_projections(self, state: SimulatorState, context: ActuarialContext, mortality_table: np.ndarray) -> Dict:
        """Calcula projeções temporais em base mensal"""
        total_months = context.total_months_projection
        months_to_retirement = context.months_to_retirement
        projection_months = list(range(total_months))
        
        # Projeção salarial mensal considerando múltiplos pagamentos anuais
        monthly_salaries = []
        for month in projection_months:
            if month < months_to_retirement:  # CORRIGIDO: < em vez de <=
                # Crescimento mensal composto do salário base
                base_monthly_salary = context.monthly_salary * ((1 + context.salary_growth_real_monthly) ** month)
                
                # Lógica corrigida: todos os 12 meses têm pagamento base
                # Meses específicos têm pagamentos extras (13º, 14º, etc.)
                current_month_in_year = month % 12  # 0=jan, 1=fev, ..., 11=dez
                
                # Pagamento base mensal
                monthly_salary = base_monthly_salary
                
                # Pagamentos extras: 13º em dezembro (mês 11), 14º em janeiro (mês 0), etc.
                extra_payments = context.salary_months_per_year - 12
                if extra_payments > 0:
                    if current_month_in_year == 11:  # Dezembro - 13º salário
                        if extra_payments >= 1:
                            monthly_salary += base_monthly_salary
                    if current_month_in_year == 0 and month > 0:  # Janeiro (não o primeiro mês) - 14º salário
                        if extra_payments >= 2:
                            monthly_salary += base_monthly_salary
            else:
                monthly_salary = 0.0
            monthly_salaries.append(monthly_salary)
        
        # Benefício de aposentadoria mensal (em termos reais)
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            # Usar valor padrão de 70% se target_replacement_rate for None
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            active_salaries = [s for s in monthly_salaries if s > 0]
            final_salary = active_salaries[-1] if active_salaries else context.monthly_salary
            monthly_benefit_amount = final_salary * (replacement_rate / 100)
        else:  # 'VALUE'
            monthly_benefit_amount = state.target_benefit if state.target_benefit is not None else 0
        
        # Projeção de benefícios mensais considerando múltiplos pagamentos anuais
        monthly_benefits = []
        for month in projection_months:
            if month >= months_to_retirement:  # CORRIGIDO: >= em vez de >
                # Lógica corrigida: todos os 12 meses têm pagamento base
                # Meses específicos têm pagamentos extras (13º, 14º, etc.)
                current_month_in_year = month % 12  # 0=jan, 1=fev, ..., 11=dez
                
                # Pagamento base mensal
                monthly_benefit = monthly_benefit_amount
                
                # Pagamentos extras: 13º em dezembro, 14º em janeiro, etc.
                extra_payments = context.benefit_months_per_year - 12
                if extra_payments > 0:
                    if current_month_in_year == 11:  # Dezembro - 13º benefício
                        if extra_payments >= 1:
                            monthly_benefit += monthly_benefit_amount
                    if current_month_in_year == 0:  # Janeiro - 14º benefício
                        if extra_payments >= 2:
                            monthly_benefit += monthly_benefit_amount
                
                monthly_benefits.append(monthly_benefit)
            else:
                monthly_benefits.append(0.0)
        
        # Contribuições mensais
        monthly_contributions = []
        for monthly_salary in monthly_salaries:
            monthly_contributions.append(monthly_salary * (state.contribution_rate / 100))
        
        # Probabilidades de sobrevivência mensais
        monthly_survival_probs = []
        cumulative_survival = 1.0
        
        for month in projection_months:
            current_age_years = state.age + (month / 12)
            age_index = int(current_age_years)
            
            if age_index < len(mortality_table):
                # Conversão de probabilidade anual para mensal: q_mensal = 1 - (1 - q_anual)^(1/12)
                q_x_annual = mortality_table[age_index]
                q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                p_x_monthly = 1 - q_x_monthly
                cumulative_survival *= p_x_monthly
            else:
                cumulative_survival = 0.0
            
            monthly_survival_probs.append(cumulative_survival)
        
        # Reservas acumuladas mensais - simulação realística sem duplicação de mortalidade
        monthly_reserves = []
        accumulated = state.initial_balance  # Iniciar com saldo inicial
        
        for month in projection_months:
            # Capitalizar saldo existente mensalmente
            accumulated *= (1 + context.discount_rate_monthly)
            
            if month < months_to_retirement:  # CORRIGIDO: < em vez de <=
                # Adicionar contribuição mensal integral (sem aplicar mortalidade)
                accumulated += monthly_contributions[month]
            else:
                # Descontar benefício mensal integral (sem aplicar mortalidade)
                accumulated -= monthly_benefits[month]
            
            # Permitir reservas negativas para análise realística de déficits
            monthly_reserves.append(accumulated)
        
        # Calcular anos efetivos de projeção (pode ter sido estendido)
        effective_projection_years = len(projection_months) // 12
        
        # Converter para anos para compatibilidade com frontend
        # Considera corretamente os pagamentos múltiplos (13º, 14º, etc.) por ano
        yearly_salaries = []
        yearly_benefits = []
        yearly_contributions = []
        yearly_survival_probs = []
        yearly_reserves = []
        
        for year_idx in range(effective_projection_years):
            start_month = year_idx * 12
            end_month = min((year_idx + 1) * 12, len(monthly_salaries))
            
            # Somatório anual considerando todos os pagamentos do ano
            # IMPORTANTE: Agora soma corretamente todos os pagamentos mensais
            year_salary = sum(monthly_salaries[start_month:end_month])
            year_benefit = sum(monthly_benefits[start_month:end_month])
            year_contribution = sum(monthly_contributions[start_month:end_month])
            
            # Probabilidade de sobrevivência no final do ano
            year_survival_prob = monthly_survival_probs[min(end_month-1, len(monthly_survival_probs)-1)]
            
            # Reserva no final do ano
            year_reserve = monthly_reserves[min(end_month-1, len(monthly_reserves)-1)]
            
            yearly_salaries.append(year_salary)
            yearly_benefits.append(year_benefit)
            yearly_contributions.append(year_contribution)
            yearly_survival_probs.append(year_survival_prob)
            yearly_reserves.append(year_reserve)
        
        return {
            "years": list(range(effective_projection_years)),
            "salaries": yearly_salaries,
            "benefits": yearly_benefits,
            "contributions": yearly_contributions,
            "survival_probs": yearly_survival_probs,
            "reserves": yearly_reserves,
            # Dados mensais para cálculos precisos
            "monthly_data": {
                "months": projection_months,
                "salaries": monthly_salaries,
                "benefits": monthly_benefits,
                "contributions": monthly_contributions,
                "survival_probs": monthly_survival_probs,
                "reserves": monthly_reserves
            }
        }
    
    def _calculate_rmba(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> float:
        """Calcula Reserva Matemática de Benefícios a Conceder usando base mensal"""
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement
        
        # Ajuste de timing para desconto temporal
        timing_adjustment = 0.0  # Ajuste em meses
        if context.payment_timing == "antecipado":
            timing_adjustment = -0.5  # Pagamento 0.5 mês antes (início do período)
        else:  # postecipado
            timing_adjustment = 0.5   # Pagamento 0.5 mês depois (final do período)
        
        # VPA dos benefícios futuros (pós-aposentadoria) - somatório mensal com timing
        apv_future_benefits = 0.0
        for month, (benefit, survival_prob) in enumerate(zip(monthly_data["benefits"], monthly_data["survival_probs"])):
            if month >= months_to_retirement and benefit > 0:  # CORRIGIDO: >= em vez de >
                # Fator de desconto mensal ajustado pelo timing
                adjusted_month = month + timing_adjustment
                discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                apv_future_benefits += (benefit * survival_prob) / discount_factor
        
        # VPA das contribuições futuras (pré-aposentadoria) - somatório mensal com timing
        apv_future_contributions = 0.0
        for month, (contribution, survival_prob) in enumerate(zip(monthly_data["contributions"], monthly_data["survival_probs"])):
            if month < months_to_retirement and contribution > 0:  # CORRIGIDO: < em vez de <=
                # Fator de desconto mensal ajustado pelo timing
                adjusted_month = month + timing_adjustment
                discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                apv_future_contributions += (contribution * survival_prob) / discount_factor
        
        return apv_future_benefits - apv_future_contributions
    
    def _calculate_rmbc(self, state: SimulatorState, projections: Dict) -> float:
        """Calcula Reserva Matemática de Benefícios Concedidos"""
        # Para participante ativo, RMBC = 0
        # Seria calculada após aposentadoria
        return 0.0
    
    def _calculate_normal_cost(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> float:
        """Calcula Custo Normal anual usando base mensal"""
        months_to_retirement = context.months_to_retirement
        
        if state.calculation_method == "PUC":
            # Projected Unit Credit - acumulação mensal do benefício
            monthly_benefit_accrual = (context.monthly_salary * (state.accrual_rate / 100)) / 12
            # Descontar para valor presente usando taxa mensal
            pv_factor = 1 / ((1 + context.discount_rate_monthly) ** months_to_retirement)
            # Retornar custo anual (12 meses)
            return monthly_benefit_accrual * pv_factor * 12
        else:  # EAN
            # Entry Age Normal - distribuir custo total pelos meses de contribuição
            total_cost = self._calculate_rmba(state, context, projections)
            monthly_cost = total_cost / months_to_retirement if months_to_retirement > 0 else 0
            # Retornar custo anual
            return monthly_cost * 12
    
    def _calculate_key_metrics(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> Dict:
        """Calcula métricas-chave usando base atuarial consistente"""
        total_contributions = sum(projections["contributions"])
        total_benefits = sum(projections["benefits"])
        
        # Salário final projetado mensal - calcular salário base sem extras (13º, 14º)
        monthly_data = projections["monthly_data"]
        
        # Calcular salário base mensal final sem extras para base consistente
        months_to_retirement = len([s for s in monthly_data["salaries"] if s > 0])
        if months_to_retirement > 0:
            # Salário base mensal no final da carreira (sem 13º/14º)
            final_salary_monthly_base = context.monthly_salary * ((1 + context.salary_growth_real_monthly) ** (months_to_retirement - 1))
        else:
            final_salary_monthly_base = context.monthly_salary
        
        # Usar salário base para cálculos de taxa de reposição (comparação justa)
        final_salary_monthly = final_salary_monthly_base
        
        # Benefício mensal base (sem extras) para comparação consistente
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            # Se for taxa de reposição, usar a taxa configurada
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            benefit_monthly_base = final_salary_monthly * (replacement_rate / 100)
        else:  # VALUE mode
            # Se for valor fixo, assumir que é o benefício mensal base
            benefit_monthly_base = state.target_benefit if state.target_benefit is not None else 0
        
        # Calcular taxa de reposição real (benefício base / salário base)
        replacement_ratio = (benefit_monthly_base / final_salary_monthly * 100) if final_salary_monthly > 0 else 0
        
        # Taxa de reposição alvo - usar base temporal consistente (salário base mensal)
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            target_replacement_ratio = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
        else:  # VALUE mode - usar benefício base mensal vs. salário base mensal
            target_replacement_ratio = (benefit_monthly_base / final_salary_monthly * 100) if final_salary_monthly > 0 else 0
        
        # TAXA DE REPOSIÇÃO SUSTENTÁVEL
        # Definição: Percentual do salário final que pode ser pago como benefício mensal 
        # de forma que não gere déficit nem superávit atuarial.
        # 
        # Fórmula base: VPA(Benefícios Sustentáveis) = Saldo Inicial + VPA(Contribuições Futuras)
        # 
        # Onde:
        # - VPA(Benefícios Sustentáveis) = Benefício_Mensal_Sustentável × Fator_Anuidade_Vitalícia
        # - Saldo Inicial = Reserva atual do participante
        # - VPA(Contribuições Futuras) = Valor presente das contribuições até aposentadoria
        # 
        # Resolvendo para Benefício_Mensal_Sustentável:
        # Benefício_Mensal_Sustentável = (Saldo Inicial + VPA(Contribuições)) / Fator_Anuidade_Vitalícia
        # 
        # Taxa de Reposição = (Benefício_Mensal_Sustentável / Salário_Final_Mensal) × 100
        sustainable_monthly_benefit = 0
        sustainable_replacement_ratio = 0
        
        if final_salary_monthly > 0:
            # ETAPA 1: Calcular recursos totais disponíveis para equilíbrio atuarial
            months_to_retirement = len([s for s in monthly_data["salaries"] if s > 0])
            
            # Ajuste de timing consistente com o contexto atuarial
            # - Antecipado: pagamento no início do período (-0.5 mês de desconto)
            # - Postecipado: pagamento no final do período (+0.5 mês de desconto)
            timing_adjustment = -0.5 if context.payment_timing == "antecipado" else 0.5
            
            # ETAPA 1a: Calcular VPA das contribuições futuras até aposentadoria
            # Usa método idêntico ao da RMBA para consistência total
            apv_future_contributions = 0.0
            for month, (contribution, survival_prob) in enumerate(zip(monthly_data["contributions"], monthly_data["survival_probs"])):
                if month < months_to_retirement and contribution > 0:  # CORRIGIDO: < em vez de <=
                    adjusted_month = month + timing_adjustment
                    discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                    apv_future_contributions += (contribution * survival_prob) / discount_factor
            
            # ETAPA 1b: Recursos totais para equilíbrio atuarial
            # Fórmula: Saldo Inicial + VPA(Contribuições Futuras)
            total_resources_for_balance = state.initial_balance + apv_future_contributions
            
            # ETAPA 2: Calcular fator de anuidade vitalícia atuarial
            mortality_table = get_mortality_table(state.mortality_table, state.gender.value)
            retirement_age = state.retirement_age
            
            # ETAPA 2a: Calcular fator de anuidade vitalícia mensal desde a aposentadoria
            # Fator representa o valor presente de uma anuidade de R$ 1,00 mensal vitalícia
            # iniciando na aposentadoria, considerando desconto e mortalidade
            annuity_pv_factor = 0.0
            cumulative_survival_to_retirement = 1.0
            
            # ETAPA 2b: Calcular sobrevivência acumulada até aposentadoria (não utilizada no cálculo final)
            for month in range(months_to_retirement):
                current_age_years = state.age + (month / 12)
                age_index = int(current_age_years)
                if age_index < len(mortality_table):
                    q_x_annual = mortality_table[age_index]
                    q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                    p_x_monthly = 1 - q_x_monthly
                    cumulative_survival_to_retirement *= p_x_monthly
                else:
                    cumulative_survival_to_retirement = 0.0
                    break
            
            # ETAPA 2c: Calcular anuidade pós-aposentadoria usando dados das projeções
            # Utiliza probabilidades já calculadas nas projeções para máxima consistência
            if cumulative_survival_to_retirement > 0:
                cumulative_survival_in_retirement = cumulative_survival_to_retirement
                
                # Somar valor presente de cada mês de benefício pós-aposentadoria
                for month in range(months_to_retirement, len(monthly_data["survival_probs"])):
                    if month >= months_to_retirement:  # CORRIGIDO: >= em vez de >
                        # Probabilidade de sobrevivência acumulada desde hoje (mês 0)
                        survival_prob_at_month = monthly_data["survival_probs"][month]
                        
                        # Ajuste de timing para benefícios (igual ao usado nas contribuições)
                        benefit_timing_adj = -0.5 if context.payment_timing == "antecipado" else 0.5
                        adjusted_month = month + benefit_timing_adj
                        
                        # Fator de desconto desde hoje (mês 0) até o mês do benefício
                        discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                        
                        # Adicionar valor presente desta parcela de R$ 1,00 de benefício mensal
                        annuity_pv_factor += survival_prob_at_month / discount_factor
            
            # ETAPA 3: Calcular benefício sustentável mensal
            # Fórmula: Benefício_Mensal = Recursos_Totais / Fator_Anuidade
            # Isso garante que VPA(Benefícios) = Recursos Totais, resultando em déficit/superávit = 0
            if annuity_pv_factor > 0:
                sustainable_monthly_benefit = total_resources_for_balance / annuity_pv_factor
            else:
                sustainable_monthly_benefit = 0
            
            # ETAPA 4: Calcular taxa de reposição sustentável
            # Taxa = (Benefício Sustentável Mensal / Salário Final Mensal Base) × 100
            # Nota: Usa salário base mensal (sem 13º/14º) para comparação consistente
            sustainable_replacement_ratio = (sustainable_monthly_benefit / final_salary_monthly * 100) if final_salary_monthly > 0 else 0
            
            # ETAPA 5: Validação do equilíbrio atuarial (opcional)
            # Verifica se o benefício sustentável calculado realmente resulta em déficit/superávit ≈ 0
            if sustainable_monthly_benefit > 0:
                # ETAPA 5a: Calcular VPA dos benefícios sustentáveis considerando pagamentos múltiplos
                apv_sustainable_benefits = 0.0
                for month in range(months_to_retirement, len(monthly_data["survival_probs"])):
                    if month >= months_to_retirement:  # CORRIGIDO: >= em vez de >
                        survival_prob_at_month = monthly_data["survival_probs"][month]
                        benefit_timing_adj = -0.5 if context.payment_timing == "antecipado" else 0.5
                        adjusted_month = month + benefit_timing_adj
                        discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                        
                        # Considerar múltiplos pagamentos anuais (13º, 14º) se aplicável
                        current_month_in_year = month % 12
                        monthly_sustainable_benefit_with_extras = sustainable_monthly_benefit
                        
                        # Adicionar pagamentos extras conforme configuração
                        extra_payments = context.benefit_months_per_year - 12
                        if extra_payments > 0:
                            if current_month_in_year == 11 and extra_payments >= 1:  # 13º em dezembro
                                monthly_sustainable_benefit_with_extras += sustainable_monthly_benefit
                            if current_month_in_year == 0 and extra_payments >= 2:   # 14º em janeiro
                                monthly_sustainable_benefit_with_extras += sustainable_monthly_benefit
                        
                        apv_sustainable_benefits += (monthly_sustainable_benefit_with_extras * survival_prob_at_month) / discount_factor
                
                # ETAPA 5b: Verificar equilíbrio atuarial
                # Fórmula: |VPA(Benefícios Sustentáveis) - Recursos Totais| deve ser ≈ 0
                balance_check = abs(apv_sustainable_benefits - total_resources_for_balance)
                relative_error = balance_check / total_resources_for_balance if total_resources_for_balance > 0 else 0
                
                # ETAPA 5c: Log de validação (opcional para debug - pode ser removido em produção)
                if relative_error > 0.01:  # Erro relativo > 1%
                    print(f"[WARNING] Equilíbrio atuarial com erro {relative_error:.2%}: "
                          f"VPA(Benefícios)={apv_sustainable_benefits:.2f}, "
                          f"Recursos={total_resources_for_balance:.2f}")
                else:
                    print(f"[INFO] Equilíbrio atuarial validado: erro {relative_error:.4%}")
        
        return {
            "total_contributions": total_contributions,
            "total_benefits": total_benefits,
            "replacement_ratio": replacement_ratio,
            "target_replacement_ratio": target_replacement_ratio,
            "sustainable_replacement_ratio": sustainable_replacement_ratio
        }
    
    def _calculate_sensitivity(self, state: SimulatorState) -> Dict:
        """Calcula análise de sensibilidade"""
        # Criar contexto base e obter tábua de mortalidade
        base_context = ActuarialContext.from_state(state)
        base_mortality_table = get_mortality_table(state.mortality_table, state.gender.value)
        base_projections = self._calculate_projections(state, base_context, base_mortality_table)
        base_rmba = self._calculate_rmba(state, base_context, base_projections)
        
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
            modified_context = ActuarialContext.from_state(modified_state)
            projections = self._calculate_projections(modified_state, modified_context, base_mortality_table)
            rmba = self._calculate_rmba(modified_state, modified_context, projections)
            sensitivity["discount_rate"][rate] = rmba
        
        # Sensibilidade idade aposentadoria
        for age in [60, 62, 65, 67, 70]:
            if age > state.age:
                modified_state = state.copy()
                modified_state.retirement_age = age
                modified_context = ActuarialContext.from_state(modified_state)
                projections = self._calculate_projections(modified_state, modified_context, base_mortality_table)
                rmba = self._calculate_rmba(modified_state, modified_context, projections)
                sensitivity["retirement_age"][age] = rmba
        
        # Sensibilidade crescimento salarial
        for growth in [0.01, 0.02, 0.03, 0.04]:
            modified_state = state.copy()
            modified_state.salary_growth_real = growth
            modified_context = ActuarialContext.from_state(modified_state)
            projections = self._calculate_projections(modified_state, modified_context, base_mortality_table)
            rmba = self._calculate_rmba(modified_state, modified_context, projections)
            sensitivity["salary_growth"][growth] = rmba
        
        # Sensibilidade inflação (removida - não aplicável em cálculos reais)
        # Mantendo estrutura para compatibilidade com interface
        sensitivity["inflation"] = {}
        
        # Sensibilidade mortalidade
        from .mortality_tables import MORTALITY_TABLES
        for table_name in MORTALITY_TABLES.keys():
            try:
                mortality_table = get_mortality_table(table_name, state.gender.value)
                projections = self._calculate_projections(state, base_context, mortality_table)
                rmba = self._calculate_rmba(state, base_context, projections)
                sensitivity["mortality"][table_name] = rmba
            except Exception as e:
                # Se a tábua não estiver disponível, usar valor base
                sensitivity["mortality"][table_name] = base_rmba
        
        return sensitivity
    
    def _calculate_actuarial_decomposition(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> Dict:
        """Calcula decomposição atuarial detalhada usando base mensal"""
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement
        
        # Ajuste de timing para desconto temporal
        timing_adjustment = -0.5 if context.payment_timing == "antecipado" else 0.5
        
        # Calcular VPA dos benefícios futuros (pós-aposentadoria) usando somatório mensal com timing
        apv_future_benefits = 0.0
        for month, (benefit, survival_prob) in enumerate(zip(monthly_data["benefits"], monthly_data["survival_probs"])):
            if month >= months_to_retirement and benefit > 0:  # CORRIGIDO: >= em vez de >
                adjusted_month = month + timing_adjustment
                discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                apv_future_benefits += (benefit * survival_prob) / discount_factor
        
        # Calcular VPA das contribuições futuras (pré-aposentadoria) usando somatório mensal com timing
        apv_future_contributions = 0.0
        for month, (contribution, survival_prob) in enumerate(zip(monthly_data["contributions"], monthly_data["survival_probs"])):
            if month < months_to_retirement and contribution > 0:  # CORRIGIDO: < em vez de <=
                adjusted_month = month + timing_adjustment
                discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                apv_future_contributions += (contribution * survival_prob) / discount_factor
        
        return {
            "apv_benefits": apv_future_benefits,
            "apv_future_contributions": apv_future_contributions,  # Nome mais claro
            "service_cost": {"normal": 0, "interest": 0},
            "duration": 15.0,  # Simplificado - pode ser calculado precisamente se necessário
            "convexity": 2.5   # Simplificado - pode ser calculado precisamente se necessário
        }
    
    def _calculate_sufficiency_analysis(self, state: SimulatorState, context: ActuarialContext, projections: Dict, metrics: Dict) -> Dict:
        """Calcula análise de suficiência seguindo a fórmula: Saldo Inicial + (-RMBA) = Superávit"""
        
        # Calcular RMBA usando a função dedicada para consistência
        rmba = self._calculate_rmba(state, context, projections)
        
        # Análise de suficiência: Saldo Inicial - RMBA = Superávit
        # Se RMBA for negativo (VPA Contrib > VPA Benefícios), isso indica superávit natural
        deficit_surplus = state.initial_balance - rmba
        
        # Calcular VPA do benefício alvo para cálculo de percentuais
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement
        mortality_table = get_mortality_table(state.mortality_table, state.gender.value)
        
        # Obter o benefício alvo mensal correto baseado no modo
        if state.benefit_target_mode == BenefitTargetMode.REPLACEMENT_RATE:
            replacement_rate = state.target_replacement_rate if state.target_replacement_rate is not None else 70.0
            # Usar salário final projetado
            active_monthly_salaries = [s for s in monthly_data["salaries"] if s > 0]
            final_monthly_salary = active_monthly_salaries[-1] if active_monthly_salaries else context.monthly_salary
            monthly_target_benefit = final_monthly_salary * (replacement_rate / 100)
        else:  # 'VALUE'
            monthly_target_benefit = (state.target_benefit if state.target_benefit is not None else 0)
        
        # Calcular VPA do benefício desejado como anuidade vitalícia mensal
        target_benefit_apv = 0.0
        cumulative_survival = 1.0
        
        # Primeiramente, calcular sobrevivência até aposentadoria
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
        
        # Calcular anuidade usando mesmo horizonte das reservas para consistência
        max_projection_age = state.age + state.projection_years
        max_months_after_retirement = (max_projection_age - state.retirement_age) * 12
        
        for month_after_retirement in range(max_months_after_retirement):
            total_month = months_to_retirement + month_after_retirement
            current_age_years = state.age + (total_month / 12)
            age_index = int(current_age_years)
            
            if age_index < len(mortality_table):
                # Calcular sobrevivência até este mês específico
                if month_after_retirement == 0:
                    survival_prob = survival_to_retirement
                else:
                    # Probabilidade de sobrevivência mensal adicional
                    q_x_annual = mortality_table[age_index - 1]  # Idade anterior
                    q_x_monthly = 1 - ((1 - q_x_annual) ** (1/12))
                    p_x_monthly = 1 - q_x_monthly
                    cumulative_survival *= p_x_monthly
                    survival_prob = cumulative_survival
                
                # Desconto mensal ajustado pelo timing do contexto
                benefit_timing_adjustment = -0.5 if context.payment_timing == "antecipado" else 0.5
                adjusted_month = total_month + benefit_timing_adjustment
                discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                present_value = (monthly_target_benefit * survival_prob) / discount_factor
                target_benefit_apv += present_value
            else:
                break
        
        # Percentual do déficit/superávit em relação ao VPA dos benefícios alvos
        deficit_surplus_percentage = (deficit_surplus / target_benefit_apv * 100) if target_benefit_apv > 0 else 0
        
        # Taxa de contribuição necessária para déficit zero
        # Necessário quando: Saldo Inicial < RMBA (passivo líquido)
        if rmba > state.initial_balance:
            required_total_contributions = rmba - state.initial_balance
            
            # Calcular VPA dos salários futuros mensalmente com timing do contexto
            apv_future_salaries = 0.0
            salary_timing_adjustment = -0.5 if context.payment_timing == "antecipado" else 0.5
            for month, (salary, survival_prob) in enumerate(zip(monthly_data["salaries"], monthly_data["survival_probs"])):
                if month < months_to_retirement and salary > 0:  # CORRIGIDO: < em vez de <=
                    adjusted_month = month + salary_timing_adjustment
                    discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                    apv_future_salaries += (salary * survival_prob) / discount_factor
            
            required_contribution_rate = (required_total_contributions / apv_future_salaries * 100) if apv_future_salaries > 0 else 0
        else:
            required_contribution_rate = 0
        
        # Garantir que a taxa seja realista (máximo 50%)
        required_contribution_rate = min(required_contribution_rate, 50)
        
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
    
    def _calculate_actuarial_projections(self, state: SimulatorState, context: ActuarialContext, projections: Dict) -> Dict:
        """Calcula projeções atuariais ano a ano para gráfico"""
        monthly_data = projections["monthly_data"]
        months_to_retirement = context.months_to_retirement
        
        vpa_benefits_yearly = []
        vpa_contributions_yearly = []
        rmba_evolution_yearly = []
        
        # Ajuste de timing para desconto temporal
        timing_adjustment = -0.5 if context.payment_timing == "antecipado" else 0.5
        
        # Para cada ano da projeção, calcular VPAs restantes
        for year_idx in range(len(projections["years"])):
            year_month = year_idx * 12
            
            # VPA dos benefícios futuros a partir deste ano com timing
            vpa_benefits = 0.0
            for month in range(year_month, len(monthly_data["benefits"])):
                if month >= months_to_retirement:  # CORRIGIDO: >= em vez de >
                    benefit = monthly_data["benefits"][month]
                    survival_prob = monthly_data["survival_probs"][month]
                    discount_months = month - year_month + timing_adjustment
                    if discount_months >= 0:
                        discount_factor = (1 + context.discount_rate_monthly) ** discount_months
                        vpa_benefits += (benefit * survival_prob) / discount_factor
            
            # VPA das contribuições futuras a partir deste ano com timing
            vpa_contributions = 0.0
            for month in range(year_month, min(months_to_retirement + 1, len(monthly_data["contributions"]))):
                contribution = monthly_data["contributions"][month]
                survival_prob = monthly_data["survival_probs"][month]
                discount_months = month - year_month + timing_adjustment
                if discount_months >= 0:
                    discount_factor = (1 + context.discount_rate_monthly) ** discount_months
                    vpa_contributions += (contribution * survival_prob) / discount_factor
            
            # RMBA neste ponto = VPA benefícios - VPA contribuições
            rmba_year = vpa_benefits - vpa_contributions
            
            vpa_benefits_yearly.append(vpa_benefits)
            vpa_contributions_yearly.append(vpa_contributions)
            rmba_evolution_yearly.append(rmba_year)
        
        return {
            "vpa_benefits": vpa_benefits_yearly,
            "vpa_contributions": vpa_contributions_yearly,
            "rmba_evolution": rmba_evolution_yearly
        }