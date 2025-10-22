export type BenefitTargetMode = "VALUE" | "REPLACEMENT_RATE";
export type PaymentTiming = "postecipado" | "antecipado";
export type PlanType = "BD" | "CD";
export type CDConversionMode = "ACTUARIAL" | "ACTUARIAL_EQUIVALENT" | "CERTAIN_5Y" | "CERTAIN_10Y" | "CERTAIN_15Y" | "CERTAIN_20Y" | "PERCENTAGE" | "PROGRAMMED";

// === TIPOS PARA FAMÍLIA E DEPENDENTES ===
export type DependentType = "SPOUSE" | "CHILD" | "PARENT" | "EX_SPOUSE" | "OTHER";
export type BenefitShareType = "EQUAL_QUOTA" | "PROPORTIONAL" | "PRIORITY_CLASS" | "TOTAL_REVERSION";
export type InheritanceRule = "LUMP_SUM" | "CONTINUED_INCOME" | "TEMPORARY_ANNUITY" | "PROPORTIONAL_SPLIT";

export interface FamilyMember {
  id?: string;
  name: string;
  dependent_type: DependentType;

  // Dados demográficos
  birth_date?: string;  // ISO date string
  age?: number;
  gender?: "M" | "F";

  // Configuração atuarial
  mortality_table?: string;
  age_differential?: number;

  // Configuração de benefícios
  benefit_share_percentage: number;
  economic_dependency: boolean;
  eligible_until_age?: number;
  is_disabled: boolean;

  // Metadados
  priority_class: number;
  notes?: string;
}

export interface FamilyComposition {
  members: FamilyMember[];
  benefit_share_type: BenefitShareType;
  inheritance_rule: InheritanceRule;
  survivor_benefit_percentage: number;
  minimum_survivor_income?: number;
  enable_quota_reversion: boolean;
}

export interface SimulatorState {
  // Dados do participante
  age: number;
  gender: "M" | "F";
  salary: number;
  
  // Tipo de plano
  plan_type: PlanType;
  
  // Parâmetros do plano
  initial_balance: number;
  benefit_target_mode: BenefitTargetMode;
  target_benefit?: number;
  target_replacement_rate?: number;
  accrual_rate: number;
  retirement_age: number;
  contribution_rate: number;
  
  // Parâmetros específicos para CD
  cd_conversion_mode?: CDConversionMode;
  cd_withdrawal_percentage?: number;  // Para modo PERCENTAGE
  cd_floor_percentage?: number;       // Piso de renda para ACTUARIAL_EQUIVALENT (% do 1º ano)
  cd_percentage_growth?: number;      // Crescimento anual do % de saque (PERCENTAGE)
  accumulation_rate?: number;         // Taxa durante acumulação (CD)
  conversion_rate?: number;           // Taxa para conversão em renda (CD)
  
  // Base atuarial
  mortality_table: string;
  actual_mortality_table?: string;  // Tábua realmente usada após lookup automático (ex: SOA complementar)
  mortality_aggravation: number;  // Suavização percentual da tábua (-10% a +20%)
  discount_rate: number;
  salary_growth_real: number;
  
  // Configurações
  benefit_indexation: string;
  contribution_indexation: string;
  use_ettj: boolean;
  
  // Custos administrativos
  admin_fee_rate: number;      // Taxa anual sobre saldo
  loading_fee_rate: number;    // Taxa de carregamento sobre contribuições
  admin_fee_annual?: number;   // Taxa administrativa anual (valor absoluto)

  // Tempo de serviço
  service_years?: number;       // Anos de serviço já cumpridos

  // Configurações técnicas
  payment_timing: PaymentTiming;
  salary_months_per_year: number;
  benefit_months_per_year: number;
  
  projection_years: number;
  calculation_method: "PUC" | "EAN";

  // === FAMÍLIA E DEPENDENTES ===
  family?: FamilyComposition;
  include_survivor_benefits: boolean;

  // Metadados
  last_update?: string;
  calculation_id?: string;
}

export interface SimulatorResults {
  // Reservas Matemáticas (BD)
  rmba: number;
  rmbc: number;
  normal_cost: number;
  
  // Campos específicos para CD
  individual_balance?: number;
  net_accumulated_value?: number;
  accumulated_return?: number;
  effective_return_rate?: number;
  monthly_income_cd?: number;
  conversion_factor?: number;
  administrative_cost_total?: number;
  benefit_duration_years?: number;
  
  // Análise de Suficiência
  deficit_surplus: number;
  deficit_surplus_percentage: number;
  required_contribution_rate: number;
  
  // Projeções
  projection_years: number[];
  projected_salaries: number[];
  projected_benefits: number[];
  projected_contributions: number[];
  survival_probabilities: number[];
  accumulated_reserves: number[];

  // Vetores por idade para gráfico de evolução salarial/benefícios
  projection_ages?: number[];            // Idades correspondentes
  projected_salaries_by_age?: number[];  // Salários anuais por idade
  projected_benefits_by_age?: number[];  // Benefícios anuais por idade
  
  // Projeções atuariais para gráfico separado
  projected_vpa_benefits: number[];
  projected_vpa_contributions: number[];
  projected_rmba_evolution: number[];      // Para pessoas ativas
  projected_rmbc_evolution: number[];      // Para pessoas aposentadas
  
  // Métricas
  total_contributions: number;
  total_benefits: number;
  replacement_ratio: number;
  target_replacement_ratio: number;
  sustainable_replacement_ratio: number;
  funding_ratio?: number;
  
  
  // Decomposição
  actuarial_present_value_benefits: number;
  actuarial_present_value_salary: number;
  service_cost_breakdown: Record<string, number>;
  liability_duration: number;
  convexity: number;
  
  // Cenários
  best_case_scenario: Record<string, number>;
  worst_case_scenario: Record<string, number>;
  confidence_intervals: Record<string, [number, number]>;

  // Cenários diferenciados CD
  actuarial_scenario?: {
    description: string;
    contribution_rate: number;
    final_balance: number;
    monthly_income: number;
    annual_income: number;
    replacement_ratio: number;
    projections: {
      years: number[];
      salaries: number[];
      benefits: number[];
      contributions: number[];
      survival_probs: number[];
      reserves: number[];
      monthly_data: {
        months: number[];
        salaries: number[];
        benefits: number[];
      };
    };
  };
  desired_scenario?: {
    description: string;
    required_contribution_rate: number;
    final_balance: number;
    monthly_income: number;
    annual_income: number;
    replacement_ratio: number;
    projections: {
      years: number[];
      salaries: number[];
      benefits: number[];
      contributions: number[];
      survival_probs: number[];
      reserves: number[];
      monthly_data: {
        months: number[];
        salaries: number[];
        benefits: number[];
      };
    };
  };
  scenario_comparison?: {
    contribution_gap: number;
    contribution_gap_percentage: number;
    income_gap: number;
    income_gap_percentage: number;
    feasibility: string;
    recommendation: string;
  };

  // === ANÁLISE DE SOBREVIVÊNCIA E HERANÇA ===
  survivor_analysis?: {
    vpa_survivor_benefits: number;
    survivor_details: Array<{
      member_id: string;
      member_name: string;
      vpa: number;
      cash_flows: number[];
      inheritance_value_by_age?: number[];  // Valor da função de heritor por idade
    }>;
  };

  // Métricas de cobertura familiar
  survivor_income_ratio?: number;      // Renda sobrevivente / Benefício original
  inheritance_balance?: number;        // Saldo remanescente (CD)
  family_protection_score?: number;    // Score de proteção (0-100)

  // Metadados
  calculation_timestamp: string;
  computation_time_ms: number;
  actuarial_method_details: Record<string, string>;
  assumptions_validation: Record<string, boolean>;
}

export interface MortalityTable {
  code: string;
  name: string;
  description?: string;
  source: string;
  is_official: boolean;
  regulatory_approved: boolean;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  message?: string;
  timestamp?: string;
  calculation_id?: string;
  computation_time_ms?: number;
}

// Tipos para sugestões inteligentes
export type SuggestionType = "balance_plan" | "improve_benefit" | "reduce_contribution" | "optimize_retirement" | "sustainable_benefit" | "trade_off_options" | "optimize_multiple";
export type SuggestionAction = "update_contribution_rate" | "update_retirement_age" | "update_target_benefit" | "update_accrual_rate" | "apply_sustainable_benefit" | "apply_sustainable_replacement_rate" | "update_replacement_rate" | "update_multiple_params" | "optimize_cd_contribution_rate";

export interface Suggestion {
  id: string;
  type: SuggestionType;
  title: string;
  description: string;
  action: SuggestionAction;
  action_value?: number;
  action_values?: Record<string, number>;  // Para múltiplos parâmetros
  action_label: string;
  priority: number;
  impact_description: string;
  confidence: number;
  trade_off_info?: string;  // Informação sobre trade-offs
}

export interface SuggestionsRequest {
  state: SimulatorState;
  max_suggestions?: number;
  focus_area?: string;
}

export interface SuggestionsResponse {
  suggestions: Suggestion[];
  context: Record<string, any>;
  computation_time_ms: number;
}

export interface ApplySuggestionRequest {
  state: SimulatorState;
  action: SuggestionAction;
  action_value?: number;
  action_values?: Record<string, number>;
}

export interface ApplySuggestionResponse {
  updated_state: SimulatorState;
  new_results: SimulatorResults;
  message: string;
}
