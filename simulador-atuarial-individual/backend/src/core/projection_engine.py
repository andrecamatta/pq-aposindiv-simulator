"""
Motor de projeções temporais centralizado
Consolida e otimiza cálculos de projeções para BD e CD
"""

import numpy as np
from typing import Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from .projections import (
    calculate_salary_projections,
    calculate_contribution_projections,
    calculate_survival_probabilities,
    calculate_accumulated_reserves,
    calculate_benefit_projections,
    convert_monthly_to_yearly_projections
)

if TYPE_CHECKING:
    from ..models.participant import SimulatorState
    from .actuarial_engine import ActuarialContext


@dataclass
class ProjectionConfig:
    """Configuração para projeções temporais"""
    include_salaries: bool = True
    include_contributions: bool = True
    include_benefits: bool = False
    include_reserves: bool = False
    include_survival: bool = True
    monthly_resolution: bool = True
    yearly_aggregation: bool = True
    

class ProjectionEngine:
    """
    Motor centralizado para cálculos de projeções temporais
    Otimiza e reutiliza cálculos comuns entre BD e CD
    """
    
    def __init__(self):
        self.cache = {}
        self.debug_enabled = False
    
    def calculate_unified_projections(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext', 
        mortality_table: np.ndarray,
        config: ProjectionConfig = None
    ) -> Dict:
        """
        Calcula projeções unificadas configuráveis para BD e CD
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            mortality_table: Tábua de mortalidade
            config: Configuração de quais projeções calcular
            
        Returns:
            Dicionário com projeções solicitadas
        """
        if config is None:
            config = ProjectionConfig()
        
        total_months = context.total_months_projection
        cache_key = self._generate_cache_key(state, context, config)
        
        # Verificar cache
        if cache_key in self.cache:
            if self.debug_enabled:
                print(f"[PROJECTION_ENGINE] Cache hit para {cache_key[:20]}...")
            return self.cache[cache_key]
        
        projections = {}
        monthly_data = {"months": list(range(total_months))}
        
        # 1. Projeções salariais (sempre necessárias se há contribuições)
        if config.include_salaries or config.include_contributions:
            monthly_salaries = calculate_salary_projections(context, state, total_months)
            if config.include_salaries:
                monthly_data["salaries"] = monthly_salaries
        
        # 2. Contribuições mensais
        if config.include_contributions:
            monthly_contributions = calculate_contribution_projections(monthly_salaries, state, context)
            monthly_data["contributions"] = monthly_contributions
        
        # 3. Probabilidades de sobrevivência
        if config.include_survival:
            monthly_survival_probs = calculate_survival_probabilities(state, mortality_table, total_months)
            monthly_data["survival_probs"] = monthly_survival_probs
        
        # 4. Benefícios (se solicitados - implementação específica por tipo de plano)
        if config.include_benefits:
            # Para benefícios, usar valor padrão baseado no target ou valor zero
            monthly_benefit_amount = getattr(state, 'target_benefit', 0.0) or 0.0
            monthly_benefits = calculate_benefit_projections(context, state, total_months, monthly_benefit_amount)
            monthly_data["benefits"] = monthly_benefits

        # 5. Reservas/Saldos (se solicitados - implementação específica)
        if config.include_reserves:
            # Calcular reservas baseadas em contribuições e benefícios
            monthly_contributions = monthly_data.get("contributions", [0.0] * total_months)
            monthly_benefits = monthly_data.get("benefits", [0.0] * total_months)
            monthly_reserves = calculate_accumulated_reserves(state, context, monthly_contributions, monthly_benefits, total_months)
            monthly_data["reserves"] = monthly_reserves
        
        # 6. Agregar dados anuais se solicitado
        if config.yearly_aggregation:
            yearly_data = convert_monthly_to_yearly_projections(monthly_data, total_months)
            projections.update(yearly_data)
        
        # 7. Incluir dados mensais se solicitado
        if config.monthly_resolution:
            projections["monthly_data"] = monthly_data
        
        # Cache resultado
        self.cache[cache_key] = projections
        
        return projections
    
    def calculate_bd_enhanced_projections(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        mortality_table: np.ndarray,
        monthly_benefit_amount: float
    ) -> Dict:
        """
        Projeções aprimoradas específicas para BD
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial
            mortality_table: Tábua de mortalidade  
            monthly_benefit_amount: Valor do benefício mensal
            
        Returns:
            Projeções completas BD
        """
        config = ProjectionConfig(include_benefits=True, include_reserves=True)
        projections = self.calculate_unified_projections(state, context, mortality_table, config)
        
        # Calcular benefícios BD específicos
        total_months = context.total_months_projection
        months_to_retirement = context.months_to_retirement
        
        monthly_benefits = self._calculate_bd_benefits(
            context, total_months, months_to_retirement, monthly_benefit_amount
        )
        
        # Calcular reservas BD 
        monthly_reserves = self._calculate_bd_reserves(
            state, context, projections["monthly_data"]["contributions"], 
            monthly_benefits, total_months
        )
        
        # Atualizar projeções
        projections["monthly_data"]["benefits"] = monthly_benefits
        projections["monthly_data"]["reserves"] = monthly_reserves
        
        # Reagregar dados anuais
        yearly_data = convert_monthly_to_yearly_projections(projections["monthly_data"], total_months)
        projections.update(yearly_data)
        
        return projections
    
    def calculate_cd_enhanced_projections(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext', 
        mortality_table: np.ndarray,
        monthly_income: float
    ) -> Dict:
        """
        Projeções aprimoradas específicas para CD
        
        Args:
            state: Estado do simulador
            context: Contexto atuarial CD
            mortality_table: Tábua de mortalidade
            monthly_income: Renda mensal CD
            
        Returns:
            Projeções completas CD com evolução de saldo
        """
        config = ProjectionConfig(include_benefits=True, include_reserves=True)
        base_projections = self.calculate_unified_projections(state, context, mortality_table, config)
        
        total_months = context.total_months_projection
        months_to_retirement = context.months_to_retirement
        
        # Calcular evolução específica CD
        monthly_balances, monthly_benefits = self._calculate_cd_balance_evolution(
            state, context, base_projections["monthly_data"]["contributions"],
            monthly_income, total_months, months_to_retirement
        )
        
        # Atualizar projeções
        base_projections["monthly_data"]["benefits"] = monthly_benefits
        base_projections["monthly_data"]["balances"] = monthly_balances
        base_projections["final_balance"] = monthly_balances[months_to_retirement] if months_to_retirement < len(monthly_balances) else 0
        
        # Reagregar dados anuais 
        yearly_data = convert_monthly_to_yearly_projections(base_projections["monthly_data"], total_months)
        base_projections.update(yearly_data)
        
        return base_projections
    
    def calculate_sensitivity_projections(
        self,
        base_state: 'SimulatorState',
        base_context: 'ActuarialContext',
        mortality_table: np.ndarray,
        parameter_variations: Dict[str, List]
    ) -> Dict[str, Dict]:
        """
        Calcula projeções para múltiplas variações de parâmetros (otimizado para sensibilidade)
        
        Args:
            base_state: Estado base
            base_context: Contexto base
            mortality_table: Tábua de mortalidade
            parameter_variations: Dicionário {param_name: [values]}
            
        Returns:
            Dicionário {param_name: {value: projections}}
        """
        sensitivity_projections = {}
        
        for param_name, values in parameter_variations.items():
            sensitivity_projections[param_name] = {}
            
            for value in values:
                # Criar estado/contexto modificado
                modified_state, modified_context = self._create_modified_state_context(
                    base_state, base_context, param_name, value
                )
                
                # Calcular projeções otimizadas (só o essencial para sensibilidade)
                config = ProjectionConfig(
                    include_salaries=True,
                    include_contributions=True, 
                    include_survival=True,
                    include_benefits=False,  # Não necessário para cálculo de sensibilidade básica
                    include_reserves=False,
                    monthly_resolution=True,
                    yearly_aggregation=False  # Reduzir processamento
                )
                
                projections = self.calculate_unified_projections(
                    modified_state, modified_context, mortality_table, config
                )
                
                sensitivity_projections[param_name][value] = projections
        
        return sensitivity_projections
    
    def enable_debug(self, enabled: bool = True):
        """Ativa/desativa debug das projeções"""
        self.debug_enabled = enabled
    
    def clear_cache(self):
        """Limpa cache de projeções"""
        self.cache.clear()
        if self.debug_enabled:
            print("[PROJECTION_ENGINE] Cache limpo")
    
    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        return {
            "cached_projections": len(self.cache),
            "cache_keys": list(self.cache.keys())[:5]  # Primeiras 5 chaves
        }
    
    def _generate_cache_key(
        self, 
        state: 'SimulatorState', 
        context: 'ActuarialContext', 
        config: ProjectionConfig
    ) -> str:
        """Gera chave única para cache baseada em parâmetros relevantes"""
        key_parts = [
            f"age_{state.age}",
            f"ret_{state.retirement_age}",
            f"sal_{state.salary}",
            f"disc_{state.discount_rate:.4f}",
            f"months_{context.total_months_projection}",
            f"config_{hash(str(config))}"
        ]
        return "_".join(key_parts)
    
    def _calculate_bd_benefits(
        self,
        context: 'ActuarialContext',
        total_months: int,
        months_to_retirement: int,
        monthly_benefit_amount: float
    ) -> List[float]:
        """Calcula benefícios BD com múltiplos pagamentos"""
        monthly_benefits = []
        
        for month in range(total_months):
            if context.is_already_retired or month >= months_to_retirement:
                # Lógica de pagamentos múltiplos
                current_month_in_year = month % 12
                monthly_benefit = monthly_benefit_amount
                
                # Pagamentos extras
                extra_payments = context.benefit_months_per_year - 12
                if extra_payments > 0:
                    if current_month_in_year == 11:  # Dezembro
                        if extra_payments >= 1:
                            monthly_benefit += monthly_benefit_amount
                    if current_month_in_year == 0:  # Janeiro  
                        if extra_payments >= 2:
                            monthly_benefit += monthly_benefit_amount
                
                monthly_benefits.append(monthly_benefit)
            else:
                monthly_benefits.append(0.0)
        
        return monthly_benefits
    
    def _calculate_bd_reserves(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext', 
        monthly_contributions: List[float],
        monthly_benefits: List[float],
        total_months: int
    ) -> List[float]:
        """Calcula evolução das reservas BD"""
        monthly_reserves = []
        accumulated = state.initial_balance
        months_to_retirement = context.months_to_retirement
        
        for month in range(total_months):
            # Capitalizar com taxa de desconto
            accumulated *= (1 + context.discount_rate_monthly)
            
            # Aplicar taxa administrativa
            accumulated *= (1 - context.admin_fee_monthly)
            
            # Contribuições/benefícios
            if context.is_already_retired:
                accumulated -= monthly_benefits[month]
            elif month < months_to_retirement:
                accumulated += monthly_contributions[month]
            else:
                accumulated -= monthly_benefits[month]
            
            monthly_reserves.append(accumulated)
        
        return monthly_reserves
    
    def _calculate_cd_balance_evolution(
        self,
        state: 'SimulatorState',
        context: 'ActuarialContext',
        monthly_contributions: List[float],
        monthly_income: float,
        total_months: int,
        months_to_retirement: int
    ) -> tuple:
        """Calcula evolução de saldo e benefícios CD"""
        monthly_balances = []
        monthly_benefits = []
        balance = state.initial_balance
        
        for month in range(total_months):
            if month < months_to_retirement:
                # Fase de acumulação
                balance *= (1 + context.discount_rate_monthly)  # Taxa de acumulação
                balance *= (1 - context.admin_fee_monthly)
                balance += monthly_contributions[month]
                monthly_balances.append(max(0, balance))
                monthly_benefits.append(0.0)
            else:
                # Fase de benefícios 
                months_since_retirement = month - months_to_retirement
                
                if months_since_retirement == 0:
                    monthly_balances.append(max(0, balance))  # Pico inicial
                
                # Calcular benefício com múltiplos pagamentos
                current_month_in_year = month % 12
                monthly_benefit_payment = monthly_income
                
                extra_payments = context.benefit_months_per_year - 12
                if extra_payments > 0:
                    if current_month_in_year == 11:  # Dezembro
                        if extra_payments >= 1:
                            monthly_benefit_payment += monthly_income
                    if current_month_in_year == 0:  # Janeiro
                        if extra_payments >= 2:
                            monthly_benefit_payment += monthly_income
                
                # Consumir saldo e capitalizar
                balance -= monthly_benefit_payment
                conversion_rate_monthly = getattr(context, 'conversion_rate_monthly', context.discount_rate_monthly)
                balance *= (1 + conversion_rate_monthly)
                
                monthly_benefits.append(monthly_benefit_payment)
                
                if months_since_retirement > 0:
                    monthly_balances.append(max(0, balance))
        
        return monthly_balances, monthly_benefits
    
    def _create_modified_state_context(
        self,
        base_state: 'SimulatorState',
        base_context: 'ActuarialContext',
        param_name: str,
        value
    ) -> tuple:
        """Cria estado e contexto modificados para análise de sensibilidade"""
        modified_state = base_state.model_copy()
        
        # Aplicar modificação no estado
        param_mapping = {
            'discount_rate': 'discount_rate',
            'retirement_age': 'retirement_age',
            'salary_growth': 'salary_growth_real',
            'accumulation_rate': 'accumulation_rate',
            'conversion_rate': 'conversion_rate',
            'mortality_table': 'mortality_table'
        }
        
        if param_name in param_mapping:
            setattr(modified_state, param_mapping[param_name], value)
        
        # Recriar contexto a partir do estado modificado
        from .actuarial_engine import ActuarialContext
        modified_context = ActuarialContext.from_state(modified_state)
        
        return modified_state, modified_context