from typing import Dict, Any
from ...models import SimulatorState, SimulatorResults


class ResultsBuilder:
    """Builder para construção padronizada de SimulatorResults"""

    def __init__(self):
        self._reset()

    def _reset(self) -> None:
        """Reset do builder para nova construção"""
        self._bd_results: Dict[str, Any] = {}
        self._cd_results: Dict[str, Any] = {}
        self._projections: Dict[str, Any] = {}
        self._metrics: Dict[str, Any] = {}
        self._sufficiency_analysis: Dict[str, Any] = {}
        self._actuarial_projections: Dict[str, Any] = {}
        self._decomposition: Dict[str, Any] = {}
        self._scenarios: Dict[str, Any] = {}
        self._cd_scenarios: Dict[str, Any] = {}
        self._conversion_analysis: Dict[str, Any] = {}
        self._computation_time: float = 0.0
        self._benefit_duration_years: float = 0.0
        self._accumulated_balance: float = 0.0
        self._monthly_income: float = 0.0
        self._actuarial_scenario: Dict[str, Any] = {}
        self._desired_scenario: Dict[str, Any] = {}
        self._scenario_comparison: Dict[str, Any] = {}

    def with_bd_results(self, bd_results: Dict[str, Any]) -> 'ResultsBuilder':
        """Configura resultados BD"""
        self._bd_results = bd_results
        self._projections = bd_results.get("projections", {})
        self._metrics = bd_results.get("metrics", {})
        self._sufficiency_analysis = bd_results.get("sufficiency_analysis", {})
        return self

    def with_cd_results(self, cd_results: Dict[str, Any]) -> 'ResultsBuilder':
        """Configura resultados CD"""
        self._cd_results = cd_results
        self._projections = cd_results.get("projections", {})
        self._accumulated_balance = cd_results.get("final_balance", 0.0)
        self._cd_scenarios = cd_results.get("scenarios", {})
        return self

    def with_actuarial_projections(self, projections: Dict[str, Any]) -> 'ResultsBuilder':
        """Configura projeções atuariais"""
        self._actuarial_projections = projections
        return self


    def with_decomposition(self, decomposition: Dict[str, Any]) -> 'ResultsBuilder':
        """Configura decomposição atuarial"""
        self._decomposition = decomposition
        return self

    def with_scenarios(self, scenarios: Dict[str, Any]) -> 'ResultsBuilder':
        """Configura análise de cenários"""
        self._scenarios = scenarios
        return self

    def with_cd_specific_data(self, monthly_income: float, benefit_duration_years: float,
                             conversion_analysis: Dict[str, Any], cd_metrics: Dict[str, Any]) -> 'ResultsBuilder':
        """Configura dados específicos CD"""
        self._monthly_income = monthly_income
        self._benefit_duration_years = benefit_duration_years
        self._conversion_analysis = conversion_analysis
        self._metrics.update(cd_metrics)
        return self

    def with_cd_scenarios(self, scenarios: Dict[str, Any]) -> 'ResultsBuilder':
        """Configura cenários CD diferenciados"""
        self._actuarial_scenario = scenarios.get("actuarial", {})
        self._desired_scenario = scenarios.get("desired", {})
        self._scenario_comparison = scenarios.get("comparison", {})
        return self

    def with_computation_time(self, computation_time: float) -> 'ResultsBuilder':
        """Configura tempo de computação"""
        self._computation_time = computation_time
        return self

    def build_bd_results(self) -> SimulatorResults:
        """Constrói SimulatorResults para BD"""
        result = SimulatorResults(
            # Resultados das calculadoras especializadas
            rmba=self._bd_results.get("rmba", 0.0),
            rmbc=self._bd_results.get("rmbc", 0.0),
            normal_cost=self._bd_results.get("normal_cost", 0.0),

            # Análise de Suficiência
            deficit_surplus=self._sufficiency_analysis.get("deficit_surplus", 0.0),
            deficit_surplus_percentage=self._sufficiency_analysis.get("deficit_surplus_percentage", 0.0),
            required_contribution_rate=self._sufficiency_analysis.get("required_contribution_rate", 0.0),

            # Projeções temporais
            projection_years=self._projections.get("years", []),
            projected_salaries=self._projections.get("salaries", []),
            projected_benefits=self._projections.get("benefits", []),
            projected_contributions=self._projections.get("contributions", []),
            survival_probabilities=self._projections.get("survival_probs", []),
            accumulated_reserves=self._projections.get("reserves", []),

            # Vetores por idade
            projection_ages=self._projections.get("projection_ages"),
            projected_salaries_by_age=self._projections.get("projected_salaries_by_age"),
            projected_benefits_by_age=self._projections.get("projected_benefits_by_age"),

            # Dados mensais detalhados (para relatórios precisos)
            monthly_data=self._projections.get("monthly_data"),

            # Projeções atuariais específicas BD
            projected_vpa_benefits=self._actuarial_projections.get("vpa_benefits", []),
            projected_vpa_contributions=self._actuarial_projections.get("vpa_contributions", []),
            projected_rmba_evolution=self._actuarial_projections.get("rmba_evolution", []),
            projected_rmbc_evolution=self._actuarial_projections.get("rmbc_evolution", []),

            # Métricas das calculadoras
            total_contributions=self._metrics.get("total_contributions", 0.0),
            total_benefits=self._metrics.get("total_benefits", 0.0),
            replacement_ratio=self._metrics.get("replacement_ratio", 0.0),
            target_replacement_ratio=self._metrics.get("target_replacement_ratio", 0.0),
            sustainable_replacement_ratio=self._metrics.get("sustainable_replacement_ratio", 0.0),
            funding_ratio=self._metrics.get("funding_ratio", 100.0),


            # Decomposição atuarial
            decomposition=self._decomposition,
            actuarial_present_value_benefits=self._decomposition.get("apv_benefits", 0.0),
            actuarial_present_value_salary=self._decomposition.get("apv_future_contributions", 0.0),

            # Análise de cenários
            scenarios=self._scenarios,

            # Tempo de computação
            computation_time_ms=self._computation_time,

            # Campos CD zerados
            accumulated_balance=0.0,
            monthly_income=0.0,
            benefit_duration_years=0.0,
            conversion_analysis={}
        )

        self._reset()
        return result

    def build_cd_results(self, state: SimulatorState) -> SimulatorResults:
        """Constrói SimulatorResults para CD"""
        # Calcular métricas específicas CD
        total_contributions_value = sum(self._projections.get("contributions", []))
        administrative_costs = total_contributions_value * state.loading_fee_rate + self._accumulated_balance * state.admin_fee_rate
        net_balance = self._accumulated_balance - administrative_costs
        accumulated_return_value = self._accumulated_balance - state.initial_balance - total_contributions_value
        effective_return = (accumulated_return_value / total_contributions_value * 100) if total_contributions_value > 0 else 0.0
        conversion_factor_value = self._monthly_income / self._accumulated_balance if self._accumulated_balance > 0 else 0.0

        result = SimulatorResults(
            # Reservas Matemáticas (zeradas para CD)
            rmba=0.0,
            rmbc=0.0,
            normal_cost=0.0,

            # Análise de Suficiência (não aplicável para CD)
            deficit_surplus=0.0,
            deficit_surplus_percentage=0.0,
            required_contribution_rate=0.0,

            # Projeções temporais CD
            projection_years=self._projections.get("years", []),
            projected_salaries=self._projections.get("salaries", []),
            projected_benefits=self._projections.get("benefits", []),
            projected_contributions=self._projections.get("contributions", []),
            survival_probabilities=self._projections.get("survival_probs", []),
            accumulated_reserves=self._projections.get("reserves", []),

            # Vetores por idade (agora preenchidos para CD)
            projection_ages=self._projections.get("projection_ages"),
            projected_salaries_by_age=self._projections.get("projected_salaries_by_age"),
            projected_benefits_by_age=self._projections.get("projected_benefits_by_age"),

            # Dados mensais detalhados (para relatórios precisos)
            monthly_data=self._projections.get("monthly_data"),

            # Projeções atuariais específicas BD (zeradas para CD)
            projected_vpa_benefits=[],
            projected_vpa_contributions=[],
            projected_rmba_evolution=[],
            projected_rmbc_evolution=[],

            # Métricas CD
            total_contributions=total_contributions_value,
            total_benefits=self._metrics.get("total_benefits", 0.0),
            replacement_ratio=self._metrics.get("replacement_ratio", 0.0),
            target_replacement_ratio=self._metrics.get("target_replacement_ratio", 0.0),
            sustainable_replacement_ratio=self._metrics.get("sustainable_replacement_ratio", 0.0),
            funding_ratio=100.0,


            # Dados específicos CD
            individual_balance=self._accumulated_balance,  # Saldo individual acumulado
            accumulated_balance=self._accumulated_balance,
            net_accumulated_value=net_balance,  # Valor líquido (após custos)
            accumulated_return=accumulated_return_value,  # Rendimento acumulado
            effective_return_rate=effective_return,  # Taxa de retorno efetiva
            monthly_income=self._monthly_income,
            monthly_income_cd=self._monthly_income,  # Preencher campo específico CD
            conversion_factor=conversion_factor_value,  # Fator de conversão
            administrative_cost_total=administrative_costs,  # Custos administrativos totais
            benefit_duration_years=self._benefit_duration_years,
            conversion_analysis=self._conversion_analysis,


            # Decomposição (não aplicável para CD)
            decomposition={},

            # Análise de cenários (não aplicável para CD)
            scenarios={},

            # Cenários diferenciados CD
            actuarial_scenario=self._actuarial_scenario,
            desired_scenario=self._desired_scenario,
            scenario_comparison=self._scenario_comparison,

            # Tempo de computação
            computation_time_ms=self._computation_time
        )

        self._reset()
        return result