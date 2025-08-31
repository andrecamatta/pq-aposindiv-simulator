export type BenefitTargetMode = "VALUE" | "REPLACEMENT_RATE";
export type PaymentTiming = "postecipado" | "antecipado";

export interface SimulatorState {
  // Dados do participante
  age: number;
  gender: "M" | "F";
  salary: number;
  
  // Parâmetros do plano
  initial_balance: number;
  benefit_target_mode: BenefitTargetMode;
  target_benefit?: number;
  target_replacement_rate?: number;
  accrual_rate: number;
  retirement_age: number;
  contribution_rate: number;
  
  // Base atuarial
  mortality_table: string;
  discount_rate: number;
  salary_growth_real: number;
  
  // Configurações
  benefit_indexation: string;
  contribution_indexation: string;
  use_ettj: boolean;
  
  // Configurações técnicas
  payment_timing: PaymentTiming;
  salary_months_per_year: number;
  benefit_months_per_year: number;
  
  projection_years: number;
  calculation_method: "PUC" | "EAN";
  
  // Metadados
  last_update?: string;
  calculation_id?: string;
}

export interface SimulatorResults {
  // Reservas Matemáticas
  rmba: number;
  rmbc: number;
  normal_cost: number;
  
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
  
  // Projeções atuariais para gráfico separado
  projected_vpa_benefits: number[];
  projected_vpa_contributions: number[];
  projected_rmba_evolution: number[];
  
  // Métricas
  total_contributions: number;
  total_benefits: number;
  replacement_ratio: number;
  target_replacement_ratio: number;
  sustainable_replacement_ratio: number;
  funding_ratio?: number;
  
  // Sensibilidade
  sensitivity_discount_rate: Record<number, number>;
  sensitivity_mortality: Record<string, number>;
  sensitivity_retirement_age: Record<number, number>;
  sensitivity_salary_growth: Record<number, number>;
  sensitivity_inflation: Record<number, number>;
  
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
  
  // Metadados
  calculation_timestamp: string;
  computation_time_ms: number;
  actuarial_method_details: Record<string, string>;
  assumptions_validation: Record<string, boolean>;
}

export interface MortalityTable {
  code: string;
  name: string;
  description: string;
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