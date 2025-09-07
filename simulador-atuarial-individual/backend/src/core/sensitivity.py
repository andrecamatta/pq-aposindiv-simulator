"""
Módulo de análise de sensibilidade consolidada
Elimina duplicação entre cálculos de RMBA e déficit/superávit
"""

from typing import Dict, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.database import SimulatorState
    from .mortality_tables import get_mortality_table


class SensitivityCalculator:
    """Calculadora de análise de sensibilidade parametrizável"""
    
    def __init__(self, base_calculation_func: Callable):
        """
        Args:
            base_calculation_func: Função que calcula o valor base (RMBA, deficit, etc.)
        """
        self.base_calculation_func = base_calculation_func
    
    def calculate_sensitivity(
        self, 
        state: 'SimulatorState',
        variations_config: Dict[str, Dict] = None
    ) -> Dict[str, Dict]:
        """
        Calcula análise de sensibilidade genérica
        
        Args:
            state: Estado base do simulador
            variations_config: Configurações de variação por parâmetro
            
        Returns:
            Dicionário de sensibilidades por parâmetro
        """
        if variations_config is None:
            variations_config = self._get_default_variations_config(state)
        
        sensitivity_results = {}
        
        # Calcular valor base para referência
        base_value = self.base_calculation_func(state)
        
        # Análise por cada parâmetro
        for param_name, config in variations_config.items():
            sensitivity_results[param_name] = self._analyze_parameter(
                state, param_name, config, base_value
            )
        
        return sensitivity_results
    
    def _analyze_parameter(
        self,
        state: 'SimulatorState', 
        param_name: str,
        config: Dict,
        base_value: float
    ) -> Dict[float, float]:
        """
        Analisa sensibilidade de um parâmetro específico
        
        Args:
            state: Estado do simulador
            param_name: Nome do parâmetro
            config: Configuração de variação
            base_value: Valor base de referência
            
        Returns:
            Dicionário {valor_parametro: resultado}
        """
        results = {}
        
        for variation_value in config['values']:
            try:
                # Criar estado modificado
                modified_state = self._create_modified_state(state, param_name, variation_value)
                
                # Calcular resultado com variação
                result = self.base_calculation_func(modified_state)
                results[variation_value] = result
                
            except Exception as e:
                print(f"[SENSITIVITY] Erro com {param_name}={variation_value}: {e}")
                results[variation_value] = base_value  # Fallback para valor base
        
        return results
    
    def _create_modified_state(self, state: 'SimulatorState', param_name: str, value) -> 'SimulatorState':
        """
        Cria estado modificado com novo valor de parâmetro
        
        Args:
            state: Estado original
            param_name: Nome do parâmetro
            value: Novo valor
            
        Returns:
            Estado modificado
        """
        modified_state = state.copy()
        
        # Mapeamento de parâmetros para atributos do estado
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
        else:
            # Para parâmetros especiais como mortality_table que são strings
            if param_name == 'mortality':
                setattr(modified_state, 'mortality_table', value)
        
        return modified_state
    
    def _get_default_variations_config(self, state: 'SimulatorState') -> Dict[str, Dict]:
        """
        Retorna configuração padrão de variações centradas nos valores atuais
        
        Args:
            state: Estado do simulador
            
        Returns:
            Configuração de variações por parâmetro
        """
        config = {}
        
        # Sensibilidade taxa de desconto - centrada no valor atual ±1%
        current_discount = state.discount_rate
        config['discount_rate'] = {
            'values': [
                max(0.001, current_discount - 0.01),  # -1% com mínimo de 0.1%
                current_discount,                      # Valor atual
                current_discount + 0.01                # +1%
            ]
        }
        
        # Sensibilidade idade aposentadoria - centrada na idade atual ±1 ano
        current_retirement_age = state.retirement_age
        valid_ages = [age for age in [
            max(state.age + 1, current_retirement_age - 1),  # -1 ano (mínimo: idade+1)
            current_retirement_age,                          # Idade atual
            min(75, current_retirement_age + 1)              # +1 ano (máximo: 75)
        ] if age > state.age]
        
        config['retirement_age'] = {'values': valid_ages}
        
        # Sensibilidade crescimento salarial - centrada no valor atual ±1%
        current_salary_growth = state.salary_growth_real
        config['salary_growth'] = {
            'values': [
                max(0.0, current_salary_growth - 0.01),  # -1% com mínimo de 0%
                current_salary_growth,                    # Valor atual
                current_salary_growth + 0.01              # +1%
            ]
        }
        
        # Sensibilidade tábuas de mortalidade - usar 3 tábuas típicas
        config['mortality'] = {
            'values': ["BR_EMS_2021", "2012_IAM_BASIC", "AT_83"]
        }
        
        # Inflação - mantida vazia para compatibilidade com código antigo
        config['inflation'] = {
            'values': []  # Campo vazio para compatibilidade
        }
        
        # Para CD: adicionar taxas específicas
        if hasattr(state, 'accumulation_rate') and state.accumulation_rate:
            current_accumulation = state.accumulation_rate
            config['accumulation_rate'] = {
                'values': [
                    max(0.001, current_accumulation - 0.01),  # -1%
                    current_accumulation,                      # Atual
                    current_accumulation + 0.01                # +1%
                ]
            }
        
        if hasattr(state, 'conversion_rate') and state.conversion_rate:
            current_conversion = state.conversion_rate
            config['conversion_rate'] = {
                'values': [
                    max(0.001, current_conversion - 0.01),  # -1%
                    current_conversion,                      # Atual
                    current_conversion + 0.01                # +1%
                ]
            }
        
        return config


def create_rmba_sensitivity_calculator() -> SensitivityCalculator:
    """
    Factory para calculadora de sensibilidade baseada em RMBA
    
    Returns:
        SensitivityCalculator configurada para RMBA
    """
    def calculate_rmba_for_sensitivity(state: 'SimulatorState') -> float:
        """Função auxiliar para calcular RMBA em análise de sensibilidade"""
        # Importação dinâmica para evitar circular imports
        from .actuarial_engine import ActuarialEngine, ActuarialContext
        from .mortality_tables import get_mortality_table
        
        engine = ActuarialEngine()
        context = ActuarialContext.from_state(state)
        mortality_table = get_mortality_table(
            state.mortality_table, 
            state.gender, 
            state.mortality_aggravation
        )
        
        projections = engine._calculate_projections(state, context, mortality_table)
        return engine._calculate_rmba(state, context, projections)
    
    return SensitivityCalculator(calculate_rmba_for_sensitivity)


def create_deficit_sensitivity_calculator() -> SensitivityCalculator:
    """
    Factory para calculadora de sensibilidade baseada em déficit/superávit
    
    Returns:
        SensitivityCalculator configurada para déficit/superávit
    """
    def calculate_deficit_for_sensitivity(state: 'SimulatorState') -> float:
        """Função auxiliar para calcular déficit em análise de sensibilidade"""
        from .actuarial_engine import ActuarialEngine, ActuarialContext
        from .mortality_tables import get_mortality_table
        
        engine = ActuarialEngine()
        context = ActuarialContext.from_state(state)
        mortality_table = get_mortality_table(
            state.mortality_table,
            state.gender,
            state.mortality_aggravation
        )
        
        projections = engine._calculate_projections(state, context, mortality_table)
        rmba = engine._calculate_rmba(state, context, projections)
        
        # Déficit/Superávit = Saldo Inicial - RMBA
        return state.initial_balance - rmba
    
    return SensitivityCalculator(calculate_deficit_for_sensitivity)


def create_cd_sensitivity_calculator() -> SensitivityCalculator:
    """
    Factory para calculadora de sensibilidade específica para CD
    
    Returns:
        SensitivityCalculator configurada para renda mensal CD
    """
    def calculate_cd_income_for_sensitivity(state: 'SimulatorState') -> float:
        """Função auxiliar para calcular renda mensal CD em análise de sensibilidade"""
        from .actuarial_engine import ActuarialEngine, ActuarialContext
        from .mortality_tables import get_mortality_table
        
        engine = ActuarialEngine()
        context = engine._create_cd_context(state)
        mortality_table = get_mortality_table(
            state.mortality_table,
            state.gender,
            state.mortality_aggravation
        )
        
        projections = engine._calculate_cd_projections(state, context, mortality_table)
        accumulated_balance = projections["final_balance"]
        
        return engine._calculate_cd_monthly_income(state, context, accumulated_balance, mortality_table)
    
    return SensitivityCalculator(calculate_cd_income_for_sensitivity)