"""
Gerenciador de Métricas Atuariais
Responsável por calcular todas as métricas e indicadores atuariais.
"""

import logging
import numpy as np
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .context_manager import ActuarialContext

logger = logging.getLogger(__name__)


class MetricsManager:
    """Gerenciador especializado para cálculo de métricas atuariais"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_key_metrics(self, state: 'SimulatorState', context: 'ActuarialContext',
                            projections: Dict) -> Dict:
        """
        Calcula métricas-chave usando base atuarial consistente.

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções temporais

        Returns:
            Dicionário com métricas calculadas
        """
        metrics = {}

        # Métricas básicas de projeção
        metrics.update(self._calculate_projection_metrics(projections))

        # Métricas de taxa de reposição
        metrics.update(self._calculate_replacement_metrics(state, context, projections))

        # Métricas de acumulação
        metrics.update(self._calculate_accumulation_metrics(projections))

        # Métricas de risco
        metrics.update(self._calculate_risk_metrics(state, context, projections))

        self.logger.debug(f"Calculadas {len(metrics)} métricas-chave")
        return metrics

    def calculate_sufficiency_analysis(self, state: 'SimulatorState', context: 'ActuarialContext',
                                     projections: Dict, vpa_data: Dict) -> Dict:
        """
        Calcula análise de suficiência seguindo a fórmula: Saldo Inicial + (-RMBA) = Superávit.

        Args:
            state: Estado do simulador
            context: Contexto atuarial
            projections: Projeções temporais
            vpa_data: Dados de VPA já calculados

        Returns:
            Análise de suficiência
        """
        analysis = {}

        # Saldo inicial
        initial_balance = getattr(state, 'initial_balance', 0.0)

        # RMBA (Reserva Matemática de Benefícios Ativos)
        rmba = vpa_data.get('rmba', 0.0)

        # Cálculo fundamental da suficiência
        sufficiency_balance = initial_balance + (-rmba)
        analysis['sufficiency_balance'] = sufficiency_balance

        # Análise de adequação
        analysis.update(self._analyze_adequacy(state, context, sufficiency_balance, vpa_data))

        # Projeções de suficiência
        analysis.update(self._project_sufficiency(state, context, projections, sufficiency_balance))

        self.logger.debug(f"Análise de suficiência: saldo {sufficiency_balance:,.2f}")
        return analysis

    def calculate_scenario_metrics(self, state: 'SimulatorState', base_metrics: Dict) -> Dict:
        """
        Calcula métricas de análise de cenários.

        Args:
            state: Estado do simulador
            base_metrics: Métricas base para comparação

        Returns:
            Métricas de cenários
        """
        scenarios = {}

        # Cenário otimista
        scenarios['optimistic'] = self._calculate_optimistic_scenario(state, base_metrics)

        # Cenário pessimista
        scenarios['pessimistic'] = self._calculate_pessimistic_scenario(state, base_metrics)

        # Cenário conservador
        scenarios['conservative'] = self._calculate_conservative_scenario(state, base_metrics)

        # Análise de sensibilidade resumida
        scenarios['sensitivity_summary'] = self._calculate_sensitivity_summary(scenarios)

        return scenarios

    def _calculate_projection_metrics(self, projections: Dict) -> Dict:
        """Calcula métricas básicas das projeções"""
        metrics = {}

        # Arrays básicos
        salaries = np.array(projections.get('monthly_salaries', []))
        contributions = np.array(projections.get('monthly_contributions', []))
        benefits = np.array(projections.get('monthly_benefits', []))

        if len(salaries) > 0:
            # Totais acumulados
            metrics['total_contributions'] = float(np.sum(contributions))
            metrics['total_benefits'] = float(np.sum(benefits))
            metrics['net_flow'] = metrics['total_contributions'] - metrics['total_benefits']

            # Médias
            metrics['avg_monthly_salary'] = float(np.mean(salaries[salaries > 0]))
            metrics['avg_monthly_contribution'] = float(np.mean(contributions[contributions > 0]))

            # Crescimento
            if len(salaries) > 12:  # Pelo menos 1 ano
                final_salary = salaries[-1] if salaries[-1] > 0 else salaries[len(salaries)//2]
                initial_salary = salaries[0]
                if initial_salary > 0:
                    metrics['salary_growth_factor'] = final_salary / initial_salary

        return metrics

    def _calculate_replacement_metrics(self, state: 'SimulatorState', context: 'ActuarialContext',
                                     projections: Dict) -> Dict:
        """Calcula métricas de taxa de reposição"""
        metrics = {}

        # Salário na aposentadoria
        salaries = projections.get('monthly_salaries', [])
        if salaries and context.months_to_retirement > 0:
            retirement_month_idx = min(context.months_to_retirement, len(salaries) - 1)
            salary_at_retirement = salaries[retirement_month_idx]

            if salary_at_retirement > 0:
                metrics['salary_at_retirement'] = salary_at_retirement

                # Taxa de reposição atual
                if hasattr(state, 'target_benefit') and state.target_benefit:
                    current_replacement = (state.target_benefit / salary_at_retirement) * 100
                    metrics['current_replacement_ratio'] = current_replacement

                # Taxa de reposição do primeiro salário
                initial_replacement = (state.target_benefit / state.salary) * 100 if state.target_benefit else 0
                metrics['initial_replacement_ratio'] = initial_replacement

        return metrics

    def _calculate_accumulation_metrics(self, projections: Dict) -> Dict:
        """Calcula métricas de acumulação"""
        metrics = {}

        reserves = projections.get('monthly_reserves', [])
        if reserves:
            reserves_array = np.array(reserves)

            # Pico de reservas
            metrics['peak_reserve'] = float(np.max(reserves_array))
            metrics['peak_reserve_month'] = int(np.argmax(reserves_array))

            # Reserva final
            metrics['final_reserve'] = float(reserves_array[-1])

            # Taxa de acumulação (crescimento médio mensal)
            if len(reserves_array) > 1:
                growth_rates = np.diff(reserves_array) / (reserves_array[:-1] + 1e-10)  # Evitar divisão por zero
                valid_rates = growth_rates[~np.isnan(growth_rates) & ~np.isinf(growth_rates)]
                if len(valid_rates) > 0:
                    metrics['avg_monthly_growth_rate'] = float(np.mean(valid_rates))

        return metrics

    def _calculate_risk_metrics(self, state: 'SimulatorState', context: 'ActuarialContext',
                              projections: Dict) -> Dict:
        """Calcula métricas de risco"""
        metrics = {}

        # Risco de longevidade (anos além da expectativa)
        life_expectancy = 85  # Padrão brasileiro
        longevity_risk_years = max(0, life_expectancy - state.retirement_age)
        metrics['longevity_risk_years'] = longevity_risk_years

        # Risco de mercado (volatilidade das reservas)
        reserves = projections.get('monthly_reserves', [])
        if len(reserves) > 12:  # Pelo menos 1 ano
            reserves_array = np.array(reserves)
            returns = np.diff(reserves_array) / (reserves_array[:-1] + 1e-10)
            valid_returns = returns[~np.isnan(returns) & ~np.isinf(returns)]
            if len(valid_returns) > 0:
                metrics['reserve_volatility'] = float(np.std(valid_returns))

        # Risco de inflação (diferença de crescimento)
        real_vs_nominal_gap = context.discount_rate_monthly * 12 - context.salary_growth_real_monthly * 12
        metrics['inflation_risk_gap'] = real_vs_nominal_gap

        return metrics

    def _analyze_adequacy(self, state: 'SimulatorState', context: 'ActuarialContext',
                        sufficiency_balance: float, vpa_data: Dict) -> Dict:
        """Analisa adequação do plano"""
        analysis = {}

        # Classificação da adequação
        annual_salary = state.salary * context.salary_annual_factor
        adequacy_ratio = sufficiency_balance / annual_salary if annual_salary > 0 else 0

        if adequacy_ratio >= 1.0:
            analysis['adequacy_level'] = 'EXCELENTE'
        elif adequacy_ratio >= 0.5:
            analysis['adequacy_level'] = 'ADEQUADO'
        elif adequacy_ratio >= 0.0:
            analysis['adequacy_level'] = 'LIMITADO'
        else:
            analysis['adequacy_level'] = 'INADEQUADO'

        analysis['adequacy_ratio'] = adequacy_ratio

        # Análise de gaps
        deficit = vpa_data.get('deficit_surplus', 0.0)
        if deficit < 0:
            gap_years = abs(deficit) / (state.salary * 12) if state.salary > 0 else 0
            analysis['deficit_years_equivalent'] = gap_years

        return analysis

    def _project_sufficiency(self, state: 'SimulatorState', context: 'ActuarialContext',
                           projections: Dict, initial_sufficiency: float) -> Dict:
        """Projeta evolução da suficiência"""
        projection = {}

        # Projeção simples baseada nos fluxos
        contributions = projections.get('monthly_contributions', [])
        benefits = projections.get('monthly_benefits', [])

        if contributions and benefits:
            # Calcular evolução da suficiência mês a mês
            sufficiency_evolution = [initial_sufficiency]
            current_balance = initial_sufficiency

            for i in range(min(len(contributions), len(benefits))):
                net_flow = contributions[i] - benefits[i]
                current_balance += net_flow
                sufficiency_evolution.append(current_balance)

            projection['sufficiency_evolution'] = sufficiency_evolution
            projection['final_sufficiency'] = sufficiency_evolution[-1] if sufficiency_evolution else 0

        return projection

    def _calculate_optimistic_scenario(self, state: 'SimulatorState', base_metrics: Dict) -> Dict:
        """Calcula cenário otimista (+20% nas métricas principais)"""
        scenario = {}
        multiplier = 1.2

        for key, value in base_metrics.items():
            if isinstance(value, (int, float)) and key in ['total_contributions', 'peak_reserve', 'final_reserve']:
                scenario[f'{key}_optimistic'] = value * multiplier

        return scenario

    def _calculate_pessimistic_scenario(self, state: 'SimulatorState', base_metrics: Dict) -> Dict:
        """Calcula cenário pessimista (-20% nas métricas principais)"""
        scenario = {}
        multiplier = 0.8

        for key, value in base_metrics.items():
            if isinstance(value, (int, float)) and key in ['total_contributions', 'peak_reserve', 'final_reserve']:
                scenario[f'{key}_pessimistic'] = value * multiplier

        return scenario

    def _calculate_conservative_scenario(self, state: 'SimulatorState', base_metrics: Dict) -> Dict:
        """Calcula cenário conservador (mediana entre base e pessimista)"""
        scenario = {}

        for key, value in base_metrics.items():
            if isinstance(value, (int, float)) and key in ['total_contributions', 'peak_reserve', 'final_reserve']:
                conservative_value = value * 0.9  # 10% de desconto
                scenario[f'{key}_conservative'] = conservative_value

        return scenario

    def _calculate_sensitivity_summary(self, scenarios: Dict) -> Dict:
        """Resume análise de sensibilidade"""
        summary = {}

        # Range de variação das métricas principais
        metrics_to_analyze = ['total_contributions', 'peak_reserve', 'final_reserve']

        for metric in metrics_to_analyze:
            optimistic_key = f'{metric}_optimistic'
            pessimistic_key = f'{metric}_pessimistic'

            if optimistic_key in scenarios.get('optimistic', {}) and pessimistic_key in scenarios.get('pessimistic', {}):
                opt_value = scenarios['optimistic'][optimistic_key]
                pess_value = scenarios['pessimistic'][pessimistic_key]
                variation_range = opt_value - pess_value
                summary[f'{metric}_variation_range'] = variation_range

        return summary