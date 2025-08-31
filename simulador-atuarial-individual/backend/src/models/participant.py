from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"


class CalculationMethod(str, Enum):
    PUC = "PUC"  # Projected Unit Credit
    EAN = "EAN"  # Entry Age Normal


class BenefitTargetMode(str, Enum):
    VALUE = "VALUE"
    REPLACEMENT_RATE = "REPLACEMENT_RATE"


class PaymentTiming(str, Enum):
    POSTECIPADO = "postecipado"  # Pagamento no final do período
    ANTECIPADO = "antecipado"    # Pagamento no início do período


class SimulatorState(BaseModel):
    """Estado reativo do simulador"""
    # Dados do participante (editáveis)
    age: int
    gender: Gender
    salary: float
    
    # Parâmetros do plano (editáveis)
    initial_balance: float     # Saldo inicial acumulado
    benefit_target_mode: BenefitTargetMode = BenefitTargetMode.VALUE
    target_benefit: Optional[float] = None      # Benefício mensal desejado
    target_replacement_rate: Optional[float] = None # Taxa de reposição desejada (%)
    accrual_rate: float        # Taxa de acumulação (%)
    retirement_age: int        # Idade de aposentadoria
    contribution_rate: float   # Taxa de contribuição (%)
    
    # Base atuarial (pré-definida + editável)
    mortality_table: str       # "BR_EMS_2021", "AT_2000", "SOA_2017", "CUSTOM"
    discount_rate: float       # Taxa de desconto atuarial (ex: 0.06 = 6% a.a.)
    salary_growth_real: float  # Crescimento salarial real (ex: 0.02 = 2% a.a.)
    
    # Hipóteses demográficas avançadas
    turnover_rates: Optional[Dict[int, float]] = None  # Taxa rotatividade por idade
    disability_rates: Optional[Dict[int, float]] = None  # Taxa invalidez por idade
    early_retirement_factors: Optional[Dict[int, float]] = None  # Fatores aposentadoria antecipada
    
    # Hipóteses econômicas avançadas
    salary_scale: Optional[Dict[int, float]] = None  # Escala salarial por idade
    benefit_indexation: str = "none"  # "salary", "none", "custom"
    contribution_indexation: str = "salary"  # "salary", "none"
    
    # Estrutura a termo de juros (ETTJ)
    use_ettj: bool = False
    ettj_curve: Optional[Dict[int, float]] = None  # {ano: taxa} para ETTJ ANBIMA/PREVIC
    
    # Configurações técnicas
    payment_timing: PaymentTiming = PaymentTiming.POSTECIPADO  # Timing dos pagamentos
    salary_months_per_year: int = 13    # Número de salários por ano (padrão 13º)
    benefit_months_per_year: int = 13   # Número de benefícios por ano (padrão 13º)
    
    # Configurações de cálculo
    projection_years: int      # Horizonte de projeção
    calculation_method: CalculationMethod
    
    # Metadados
    last_update: Optional[datetime] = None
    calculation_id: Optional[str] = None

    @field_validator('target_benefit', 'target_replacement_rate', mode='before')
    def check_benefit_target(cls, v, info):
        mode = info.data.get('benefit_target_mode')
        if mode == BenefitTargetMode.VALUE and info.field_name == 'target_benefit':
            return v if v is not None else None
        if mode == BenefitTargetMode.REPLACEMENT_RATE and info.field_name == 'target_replacement_rate':
            return v if v is not None else None
        return v