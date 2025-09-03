from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class SimulatorResults(BaseModel):
    """Resultados calculados da simulação"""
    # Reservas Matemáticas (BD)
    rmba: float                # Reserva de Benefícios a Conceder
    rmbc: float                # Reserva de Benefícios Concedidos
    normal_cost: float         # Custo Normal anual
    
    # Campos específicos para CD (Contribuição Definida)
    individual_balance: Optional[float] = None       # Saldo individual acumulado
    net_accumulated_value: Optional[float] = None    # Valor líquido (saldo - custos admin)
    accumulated_return: Optional[float] = None       # Rendimento acumulado total
    effective_return_rate: Optional[float] = None    # Taxa de retorno efetiva (% a.a.)
    monthly_income_cd: Optional[float] = None        # Renda mensal calculada para CD
    conversion_factor: Optional[float] = None        # Fator de conversão utilizado
    administrative_cost_total: Optional[float] = None  # Custos administrativos totais
    benefit_duration_years: Optional[float] = None   # Duração dos benefícios em anos (CD)
    
    # Análise de Suficiência
    deficit_surplus: float     # Déficit(-) ou Superávit(+) em R$
    deficit_surplus_percentage: float  # Percentual do déficit/superávit
    required_contribution_rate: float  # Taxa necessária para déficit zero (%)
    
    # Projeções anuais (vetores para gráficos)
    projection_years: List[int]
    projected_salaries: List[float]
    projected_benefits: List[float]
    projected_contributions: List[float]
    survival_probabilities: List[float]
    accumulated_reserves: List[float]
    
    # Projeções atuariais para gráfico separado
    projected_vpa_benefits: List[float]    # VPA dos benefícios por ano
    projected_vpa_contributions: List[float]  # VPA das contribuições por ano
    projected_rmba_evolution: List[float]     # Evolução da RMBA por ano
    
    # Métricas-chave
    total_contributions: float  # Contribuições totais projetadas
    total_benefits: float      # Benefícios totais projetados
    replacement_ratio: float   # Taxa de reposição (%)
    target_replacement_ratio: float   # Taxa de reposição alvo (%)
    sustainable_replacement_ratio: float  # Taxa de reposição sustentável (%)
    funding_ratio: Optional[float] = None  # Cobertura patrimonial
    
    # Análise detalhada de sensibilidade
    sensitivity_discount_rate: Dict[float, float]  # Taxa → Impacto RMBA
    sensitivity_mortality: Dict[str, float]        # Tabela → Impacto RMBA  
    sensitivity_retirement_age: Dict[int, float]   # Idade → Impacto RMBA
    sensitivity_salary_growth: Dict[float, float]  # Taxa → Impacto RMBA
    sensitivity_inflation: Dict[float, float]      # Taxa → Impacto RMBA
    
    # Decomposição atuarial detalhada
    actuarial_present_value_benefits: float        # VPA dos benefícios futuros
    actuarial_present_value_salary: float          # VPA dos salários futuros
    service_cost_breakdown: Dict[str, float]       # Decomposição do custo normal
    liability_duration: float                      # Duration dos passivos
    convexity: float                              # Convexidade para análise de risco
    
    # Análise de cenários
    best_case_scenario: Dict[str, float]          # Cenário otimista (5%)
    worst_case_scenario: Dict[str, float]         # Cenário pessimista (95%)
    confidence_intervals: Dict[str, Tuple[float, float]]  # Intervalos de confiança
    
    # Metadados técnicos
    calculation_timestamp: datetime
    computation_time_ms: float
    actuarial_method_details: Dict[str, str]      # Detalhes dos métodos utilizados
    assumptions_validation: Dict[str, bool]       # Validação das premissas
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }