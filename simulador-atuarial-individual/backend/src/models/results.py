from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import math


class SimulatorResults(BaseModel):
    """Resultados calculados da simulação"""
    # Reservas Matemáticas (BD) - campos essenciais
    rmba: float                # Reserva de Benefícios a Conceder
    rmbc: float                # Reserva de Benefícios Concedidos
    normal_cost: Optional[float] = 0.0         # Custo Normal anual

    # Campos específicos para CD (Contribuição Definida)
    individual_balance: Optional[float] = None       # Saldo individual acumulado
    net_accumulated_value: Optional[float] = None    # Valor líquido (saldo - custos admin)
    accumulated_return: Optional[float] = None       # Rendimento acumulado total
    effective_return_rate: Optional[float] = None    # Taxa de retorno efetiva (% a.a.)
    monthly_income_cd: Optional[float] = None        # Renda mensal calculada para CD
    conversion_factor: Optional[float] = None        # Fator de conversão utilizado
    administrative_cost_total: Optional[float] = None  # Custos administrativos totais
    benefit_duration_years: Optional[float] = None   # Duração dos benefícios em anos (CD)

    # Análise de Suficiência - campos essenciais
    deficit_surplus: Optional[float] = 0.0     # Déficit(-) ou Superávit(+) em R$
    deficit_surplus_percentage: float  # Percentual do déficit/superávit
    required_contribution_rate: Optional[float] = 0.0  # Taxa necessária para déficit zero (%)

    # Projeções anuais (vetores para gráficos) - opcionais com valores padrão
    projection_years: Optional[List[int]] = None
    projected_salaries: Optional[List[float]] = None
    projected_benefits: Optional[List[float]] = None
    projected_contributions: Optional[List[float]] = None
    survival_probabilities: Optional[List[float]] = None
    accumulated_reserves: Optional[List[float]] = None

    # Vetores por idade para gráfico de evolução salarial/benefícios
    projection_ages: Optional[List[int]] = None            # Idades correspondentes
    projected_salaries_by_age: Optional[List[float]] = None  # Salários mensais por idade
    projected_benefits_by_age: Optional[List[float]] = None  # Benefícios mensais por idade

    # Projeções atuariais para gráfico separado - opcionais
    projected_vpa_benefits: Optional[List[float]] = None    # VPA dos benefícios por ano
    projected_vpa_contributions: Optional[List[float]] = None  # VPA das contribuições por ano
    projected_rmba_evolution: Optional[List[float]] = None     # Evolução da RMBA por ano (pessoas ativas)
    projected_rmbc_evolution: Optional[List[float]] = None     # Evolução da RMBC por ano (pessoas aposentadas)

    # Métricas-chave - essencial apenas replacement_ratio
    total_contributions: Optional[float] = 0.0  # Contribuições totais projetadas
    total_benefits: Optional[float] = 0.0      # Benefícios totais projetados
    replacement_ratio: float   # Taxa de reposição (%) - essencial
    target_replacement_ratio: Optional[float] = 0.0   # Taxa de reposição alvo (%)
    sustainable_replacement_ratio: Optional[float] = 0.0  # Taxa de reposição sustentável (%)
    funding_ratio: Optional[float] = None  # Cobertura patrimonial


    # Decomposição atuarial detalhada - todas opcionais
    actuarial_present_value_benefits: Optional[float] = 0.0        # VPA dos benefícios futuros
    actuarial_present_value_salary: Optional[float] = 0.0          # VPA dos salários futuros
    service_cost_breakdown: Optional[Dict[str, float]] = None       # Decomposição do custo normal
    liability_duration: Optional[float] = 0.0                      # Duration dos passivos
    convexity: Optional[float] = 0.0                              # Convexidade para análise de risco

    # Análise de cenários - todas opcionais
    best_case_scenario: Optional[Dict[str, float]] = None          # Cenário otimista (5%)
    worst_case_scenario: Optional[Dict[str, float]] = None         # Cenário pessimista (95%)
    confidence_intervals: Optional[Dict[str, Tuple[float, float]]] = None  # Intervalos de confiança

    # Cenários diferenciados para CD
    actuarial_scenario: Optional[Dict[str, Any]] = None            # Cenário baseado nas contribuições atuais
    desired_scenario: Optional[Dict[str, Any]] = None             # Cenário para atingir benefício desejado
    scenario_comparison: Optional[Dict[str, Any]] = None          # Comparação entre cenários

    # Campos específicos CD adicionais (compatibilidade com ResultsBuilder)
    accumulated_balance: Optional[float] = None                    # Saldo acumulado final CD
    monthly_income: Optional[float] = None                        # Renda mensal CD (alias para monthly_income_cd)
    conversion_analysis: Optional[Dict[str, Any]] = None          # Análise de modalidades de conversão


    # Metadados técnicos - todos opcionais
    calculation_timestamp: Optional[datetime] = None
    computation_time_ms: Optional[float] = 0.0
    actuarial_method_details: Optional[Dict[str, str]] = None      # Detalhes dos métodos utilizados
    assumptions_validation: Optional[Dict[str, bool]] = None       # Validação das premissas
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @field_validator('*', mode='before')
    @classmethod
    def sanitize_floats(cls, value: Any) -> Any:
        """
        Aplica sanitização automática a todos os campos float
        Converte inf, -inf e nan para None para compatibilidade JSON
        """
        def sanitize_value(v: Any) -> Any:
            if isinstance(v, float):
                if math.isinf(v) or math.isnan(v):
                    return None
                return v
            elif isinstance(v, list):
                return [sanitize_value(item) for item in v]
            elif isinstance(v, dict):
                return {key: sanitize_value(val) for key, val in v.items()}
            elif isinstance(v, tuple):
                return tuple(sanitize_value(item) for item in v)
            return v

        return sanitize_value(value)