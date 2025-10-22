from pydantic import BaseModel, field_validator, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import uuid
from ..utils.pydantic_validators import EnumMixin, create_enum_validator, get_enum_value


class Gender(str, Enum):
    MALE = "M"
    FEMALE = "F"


class CalculationMethod(str, Enum):
    PUC = "PUC"  # Projected Unit Credit
    EAN = "EAN"  # Entry Age Normal
    CD = "CD"    # Contribution Defined


class BenefitTargetMode(str, Enum):
    VALUE = "VALUE"
    REPLACEMENT_RATE = "REPLACEMENT_RATE"


class PaymentTiming(str, Enum):
    POSTECIPADO = "postecipado"  # Pagamento no final do período
    ANTECIPADO = "antecipado"    # Pagamento no início do período


class PlanType(str, Enum):
    BD = "BD"  # Benefício Definido
    CD = "CD"  # Contribuição Definida


class CDConversionMode(str, Enum):
    ACTUARIAL = "ACTUARIAL"        # Anuidade vitalícia atuarial
    ACTUARIAL_EQUIVALENT = "ACTUARIAL_EQUIVALENT"  # Equivalência atuarial anual
    CERTAIN_5Y = "CERTAIN_5Y"      # Renda certa por 5 anos
    CERTAIN_10Y = "CERTAIN_10Y"    # Renda certa por 10 anos
    CERTAIN_15Y = "CERTAIN_15Y"    # Renda certa por 15 anos
    CERTAIN_20Y = "CERTAIN_20Y"    # Renda certa por 20 anos
    PERCENTAGE = "PERCENTAGE"      # Percentual do saldo por ano
    PROGRAMMED = "PROGRAMMED"      # Saque programado


# Constantes de Valores Padrão
DEFAULT_CONTRIBUTION_RATE = 0.12              # Taxa de contribuição padrão (12%)
DEFAULT_CD_WITHDRAWAL_PERCENTAGE = 8.0        # Percentual de saque anual do saldo (CD)
DEFAULT_CD_FLOOR_PERCENTAGE = 70.0            # Piso de renda para ACTUARIAL_EQUIVALENT (70% do primeiro ano)
DEFAULT_CD_PERCENTAGE_GROWTH = 0.1            # Crescimento anual do percentual de saque (0.1% a.a.)
DEFAULT_BENEFIT_MONTHS_PER_YEAR = 13          # Pagamentos de benefício por ano (13º)
DEFAULT_SALARY_MONTHS_PER_YEAR = 13           # Pagamentos de salário por ano (13º)
DEFAULT_CD_CONVERSION_RATE = 0.045            # Taxa de conversão CD (4.5% a.a.)


class DecrementType(str, Enum):
    """Tipos de decrementos atuariais suportados"""
    MORTALITY = "MORTALITY"        # Mortalidade (morte)
    DISABILITY = "DISABILITY"      # Invalidez
    TURNOVER = "TURNOVER"         # Rotatividade (saída do emprego)
    DIVORCE = "DIVORCE"           # Divórcio (para pensões)


class DisabilityEntryMode(str, Enum):
    """Modalidades de entrada em invalidez"""
    IMMEDIATE = "IMMEDIATE"            # Invalidez imediata
    GRADUAL = "GRADUAL"               # Entrada gradual por idade
    OCCUPATION_BASED = "OCCUPATION_BASED"  # Baseada na ocupação


# === ENUMS PARA FAMÍLIA E DEPENDENTES ===

class DependentType(str, Enum):
    """Tipos de dependentes para cálculos de pensão e herança"""
    SPOUSE = "SPOUSE"              # Cônjuge
    CHILD = "CHILD"                # Filho(a)
    PARENT = "PARENT"              # Pai/Mãe
    EX_SPOUSE = "EX_SPOUSE"        # Ex-cônjuge (pensão alimentícia)
    OTHER = "OTHER"                # Outro dependente


class BenefitShareType(str, Enum):
    """Como o benefício/saldo é distribuído entre dependentes"""
    EQUAL_QUOTA = "EQUAL_QUOTA"              # Cotas iguais entre elegíveis
    PROPORTIONAL = "PROPORTIONAL"            # Proporcional aos %s definidos
    PRIORITY_CLASS = "PRIORITY_CLASS"        # Classes de prioridade (Lei 8.213/91)
    TOTAL_REVERSION = "TOTAL_REVERSION"      # Reversão total ao sobrevivente único


class InheritanceRule(str, Enum):
    """Regras de herança para saldo remanescente (CD)"""
    LUMP_SUM = "LUMP_SUM"                    # Saque único do saldo
    CONTINUED_INCOME = "CONTINUED_INCOME"    # Continua renda programada
    TEMPORARY_ANNUITY = "TEMPORARY_ANNUITY"  # Anuidade temporária (prazo fixo)
    PROPORTIONAL_SPLIT = "PROPORTIONAL_SPLIT" # Divide saldo por %s


# === MODELOS DE FAMÍLIA E DEPENDENTES ===

class FamilyMember(BaseModel):
    """Membro da família / dependente para cálculos atuariais"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(min_length=1, max_length=100)
    dependent_type: DependentType

    # Dados demográficos
    birth_date: Optional[datetime] = None     # Data de nascimento (para idade exata)
    age: Optional[int] = None                 # Idade atual (alternativa se não tiver birth_date)
    gender: Optional[Gender] = None           # Gênero (opcional, pode inferir da tábua)

    # Configuração atuarial
    mortality_table: Optional[str] = None     # Tábua específica (None = usa default do tipo)
    age_differential: Optional[int] = None    # Diferença de idade vs. titular (ex: -3 = 3 anos mais novo)

    # Configuração de benefícios
    benefit_share_percentage: float = Field(default=50.0, ge=0, le=100)  # % do benefício
    economic_dependency: bool = True          # Dependência econômica comprovada
    eligible_until_age: Optional[int] = None  # Idade limite (ex: 21 para filhos, 24 se universitário)
    is_disabled: bool = False                 # Invalidez (pensão vitalícia)

    # Metadados
    priority_class: int = Field(default=1, ge=1, le=3)  # Classes de prioridade legal
    notes: Optional[str] = None

    @field_validator('age', mode='before')
    def calculate_age_from_birth_date(cls, v, info):
        """Se birth_date fornecido, calcula idade automaticamente"""
        if v is None and 'birth_date' in info.data and info.data['birth_date']:
            birth = info.data['birth_date']
            today = datetime.now()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return v

    @field_validator('dependent_type', mode='before')
    def validate_dependent_type(cls, v):
        return create_enum_validator(DependentType)(cls, v)

    @field_validator('gender', mode='before')
    def validate_gender_optional(cls, v):
        if v is None:
            return v
        return create_enum_validator(Gender)(cls, v)


class FamilyComposition(BaseModel):
    """Agregado que encapsula toda a estrutura familiar"""
    members: List[FamilyMember] = Field(default_factory=list)

    # Configurações globais de distribuição
    benefit_share_type: BenefitShareType = BenefitShareType.EQUAL_QUOTA
    inheritance_rule: InheritanceRule = InheritanceRule.CONTINUED_INCOME  # Para CD

    # Regras de pensão
    survivor_benefit_percentage: float = Field(default=100.0, ge=0, le=100)  # % do benefício original
    minimum_survivor_income: Optional[float] = None  # Piso mínimo regulatório
    enable_quota_reversion: bool = True              # Reversão quando dependente perde elegibilidade

    @field_validator('benefit_share_type', mode='before')
    def validate_benefit_share_type(cls, v):
        return create_enum_validator(BenefitShareType)(cls, v)

    @field_validator('inheritance_rule', mode='before')
    def validate_inheritance_rule(cls, v):
        return create_enum_validator(InheritanceRule)(cls, v)

    @classmethod
    def empty(cls) -> "FamilyComposition":
        """Retorna composição vazia (sem dependentes) - para compatibilidade retroativa"""
        return cls(members=[], benefit_share_type=BenefitShareType.EQUAL_QUOTA)


class SimulatorState(BaseModel, EnumMixin):
    """Estado reativo do simulador"""
    # Dados do participante (editáveis)
    age: int
    gender: Gender
    salary: float
    
    # Tipo de plano
    plan_type: PlanType = PlanType.BD  # Padrão BD para compatibilidade
    
    # Parâmetros do plano (editáveis)
    initial_balance: float     # Saldo inicial acumulado
    benefit_target_mode: BenefitTargetMode = BenefitTargetMode.VALUE
    target_benefit: Optional[float] = None      # Benefício mensal desejado
    target_replacement_rate: Optional[float] = None # Taxa de reposição desejada (%)
    accrual_rate: float        # Taxa de acumulação (%)
    retirement_age: int        # Idade de aposentadoria
    contribution_rate: float   # Taxa de contribuição (%)
    
    # Parâmetros específicos para CD
    cd_conversion_mode: Optional[CDConversionMode] = None
    cd_withdrawal_percentage: Optional[float] = None  # Para modo PERCENTAGE
    cd_floor_percentage: Optional[float] = None       # Piso de renda para ACTUARIAL_EQUIVALENT (% do 1º ano)
    cd_percentage_growth: Optional[float] = None      # Crescimento anual do % de saque (PERCENTAGE)
    accumulation_rate: Optional[float] = None         # Taxa durante acumulação (CD)
    conversion_rate: Optional[float] = None           # Taxa para conversão em renda (CD)
    
    # Base atuarial (pré-definida + editável)
    mortality_table: str       # "BR_EMS_2021", "AT_2000", "SOA_2017", "CUSTOM"
    mortality_aggravation: float = 0.0  # Suavização percentual da tábua (-10% a +20%)
    discount_rate: float       # Taxa de desconto atuarial (ex: 0.06 = 6% a.a.)
    salary_growth_real: float  # Crescimento salarial real (ex: 0.02 = 2% a.a.)
    
    # Hipóteses demográficas avançadas
    turnover_rates: Optional[Dict[int, float]] = None  # Taxa rotatividade por idade
    disability_rates: Optional[Dict[int, float]] = None  # Taxa invalidez por idade
    early_retirement_factors: Optional[Dict[int, float]] = None  # Fatores aposentadoria antecipada

    # Configurações de múltiplos decrementos
    disability_enabled: bool = False                           # Habilitar invalidez
    disability_entry_mode: Optional[DisabilityEntryMode] = None  # Modalidade de entrada
    disability_table: Optional[str] = None                    # Tábua de entrada em invalidez
    disability_mortality_table: Optional[str] = None          # Tábua de mortalidade do inválido
    
    # Hipóteses econômicas avançadas
    salary_scale: Optional[Dict[int, float]] = None  # Escala salarial por idade
    benefit_indexation: str = "none"  # "salary", "none", "custom"
    contribution_indexation: str = "salary"  # "salary", "none"
    
    # Estrutura a termo de juros (ETTJ)
    use_ettj: bool = False
    ettj_curve: Optional[Dict[int, float]] = None  # {ano: taxa} para ETTJ ANBIMA/PREVIC
    
    # Custos administrativos
    admin_fee_rate: float = 0.01        # Taxa anual sobre saldo (1% default)
    loading_fee_rate: float = 0.0       # Taxa de carregamento sobre contribuições (0% default)
    
    # Configurações técnicas
    payment_timing: PaymentTiming = PaymentTiming.POSTECIPADO  # Timing dos pagamentos
    salary_months_per_year: int = 13    # Número de salários por ano (padrão 13º)
    benefit_months_per_year: int = 13   # Número de benefícios por ano (padrão 13º)
    
    # Configurações de cálculo
    projection_years: int      # Horizonte de projeção
    calculation_method: CalculationMethod

    # === FAMÍLIA E DEPENDENTES ===
    family: Optional[FamilyComposition] = Field(default_factory=FamilyComposition.empty)
    include_survivor_benefits: bool = False  # Flag para ativar cálculos de pensão/herança

    # Metadados
    last_update: Optional[datetime] = None
    calculation_id: Optional[str] = None

    @property
    def has_dependents(self) -> bool:
        """Verifica se há dependentes cadastrados"""
        return self.family is not None and len(self.family.members) > 0

    @field_validator('mortality_aggravation')
    def validate_mortality_aggravation(cls, v):
        if v < -10 or v > 20:
            raise ValueError('Suavização deve estar entre -10% e +20%')
        return v
    
    @field_validator('target_benefit', 'target_replacement_rate', mode='before')
    def check_benefit_target(cls, v, info):
        mode = info.data.get('benefit_target_mode')
        if mode == BenefitTargetMode.VALUE and info.field_name == 'target_benefit':
            return v if v is not None else None
        if mode == BenefitTargetMode.REPLACEMENT_RATE and info.field_name == 'target_replacement_rate':
            return v if v is not None else None
        return v

    # Validadores de enum robustos
    @field_validator('gender', mode='before')
    def validate_gender(cls, v):
        return create_enum_validator(Gender)(cls, v)

    @field_validator('plan_type', mode='before')
    def validate_plan_type(cls, v):
        return create_enum_validator(PlanType)(cls, v)

    @field_validator('benefit_target_mode', mode='before')
    def validate_benefit_target_mode(cls, v):
        return create_enum_validator(BenefitTargetMode)(cls, v)

    @field_validator('cd_conversion_mode', mode='before')
    def validate_cd_conversion_mode(cls, v):
        if v is None:
            return v
        return create_enum_validator(CDConversionMode)(cls, v)

    @field_validator('payment_timing', mode='before')
    def validate_payment_timing(cls, v):
        return create_enum_validator(PaymentTiming)(cls, v)

    @field_validator('calculation_method', mode='before')
    def validate_calculation_method(cls, v):
        return create_enum_validator(CalculationMethod)(cls, v)

    @property
    def derived_plan_type(self) -> PlanType:
        """Mapeia calculation_method para plan_type automaticamente"""
        if self.calculation_method == CalculationMethod.CD:
            return PlanType.CD
        else:  # PUC, EAN
            return PlanType.BD
