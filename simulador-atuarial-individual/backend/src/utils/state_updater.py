from typing import Dict, Any, Callable
from ..models import SimulatorState


class StateActionHandler:
    """Centralize logic for updating simulator state based on actions"""
    
    def __init__(self):
        self._action_handlers: Dict[str, Callable[[SimulatorState, Any], SimulatorState]] = {
            "update_contribution_rate": self._update_contribution_rate,
            "update_retirement_age": self._update_retirement_age,
            "update_target_benefit": self._update_target_benefit,
            "update_accrual_rate": self._update_accrual_rate,
            "update_salary": self._update_salary,
            "update_discount_rate": self._update_discount_rate,
            "update_salary_growth_real": self._update_salary_growth_real,
            # Novas ações para sugestões inteligentes
            "apply_sustainable_benefit": self._apply_sustainable_benefit,
            "update_replacement_rate": self._update_replacement_rate,
            "update_multiple_params": self._update_multiple_params,
            "optimize_cd_contribution_rate": self._update_contribution_rate,
        }
    
    def apply_action(self, state: SimulatorState, action: str, value: Any) -> SimulatorState:
        """
        Apply an action to update the simulator state
        
        Args:
            state: Current simulator state
            action: Action to perform
            value: New value for the action
            
        Returns:
            Updated simulator state
            
        Raises:
            ValueError: If action is not supported
        """
        if action not in self._action_handlers:
            raise ValueError(f"Ação não suportada: {action}. Ações disponíveis: {list(self._action_handlers.keys())}")
        
        handler = self._action_handlers[action]
        updated_state = state.model_copy()
        return handler(updated_state, value)
    
    def get_supported_actions(self) -> list[str]:
        """Get list of supported actions"""
        return list(self._action_handlers.keys())
    
    def register_action(self, action: str, handler: Callable[[SimulatorState, Any], SimulatorState]):
        """Register a new action handler"""
        self._action_handlers[action] = handler
    
    # Action handlers
    
    def _update_contribution_rate(self, state: SimulatorState, value: float) -> SimulatorState:
        """Update contribution rate"""
        if not isinstance(value, (int, float)) or value < 0 or value > 100:
            raise ValueError("Taxa de contribuição deve ser um número entre 0 e 100")
        state.contribution_rate = float(value)
        return state
    
    def _update_retirement_age(self, state: SimulatorState, value: int) -> SimulatorState:
        """Update retirement age"""
        if not isinstance(value, (int, float)) or value < state.age or value > 100:
            raise ValueError(f"Idade de aposentadoria deve ser entre {state.age} e 100")
        state.retirement_age = int(value)
        return state
    
    def _update_target_benefit(self, state: SimulatorState, value: float) -> SimulatorState:
        """Update target benefit"""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Benefício alvo deve ser um valor positivo")
        state.target_benefit = float(value)
        return state
    
    def _update_accrual_rate(self, state: SimulatorState, value: float) -> SimulatorState:
        """Update accrual rate"""
        if not isinstance(value, (int, float)) or value < 0 or value > 20:
            raise ValueError("Taxa de acumulação deve ser um número entre 0 e 20")
        state.accrual_rate = float(value)
        return state
    
    def _update_salary(self, state: SimulatorState, value: float) -> SimulatorState:
        """Update salary"""
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValueError("Salário deve ser um valor positivo")
        state.salary = float(value)
        return state
    
    def _update_discount_rate(self, state: SimulatorState, value: float) -> SimulatorState:
        """Update discount rate"""
        if not isinstance(value, (int, float)) or value < -0.1 or value > 1.0:
            raise ValueError("Taxa de desconto deve ser entre -10% e 100%")
        state.discount_rate = float(value)
        return state
    
    def _update_salary_growth_real(self, state: SimulatorState, value: float) -> SimulatorState:
        """Update real salary growth rate"""
        if not isinstance(value, (int, float)) or value < -0.1 or value > 0.5:
            raise ValueError("Crescimento real do salário deve ser entre -10% e 50%")
        state.salary_growth_real = float(value)
        return state
    
    def _apply_sustainable_benefit(self, state: SimulatorState, value: float) -> SimulatorState:
        """Apply sustainable benefit (same as update target benefit)"""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Benefício sustentável deve ser um valor positivo")
        state.target_benefit = float(value)
        # Ensure we're in VALUE mode when applying sustainable benefit
        state.benefit_target_mode = "VALUE"
        return state
    
    def _update_replacement_rate(self, state: SimulatorState, value: float) -> SimulatorState:
        """Update target replacement rate"""
        if not isinstance(value, (int, float)) or value < 0 or value > 200:
            raise ValueError("Taxa de reposição deve ser entre 0% e 200%")
        state.target_replacement_rate = float(value)
        # Ensure we're in REPLACEMENT_RATE mode when updating replacement rate
        state.benefit_target_mode = "REPLACEMENT_RATE"
        return state
    
    def _update_multiple_params(self, state: SimulatorState, values: dict) -> SimulatorState:
        """Update multiple parameters at once"""
        if not isinstance(values, dict):
            raise ValueError("Valores múltiplos devem ser fornecidos como dicionário")
        
        # Apply each parameter change sequentially
        updated_state = state
        for param_name, param_value in values.items():
            # Map parameter names to action names
            action_mapping = {
                "contribution_rate": "update_contribution_rate",
                "retirement_age": "update_retirement_age",
                "target_benefit": "update_target_benefit",
                "accrual_rate": "update_accrual_rate",
                "salary": "update_salary",
                "discount_rate": "update_discount_rate",
                "salary_growth_real": "update_salary_growth_real",
                "target_replacement_rate": "update_replacement_rate"
            }
            
            if param_name in action_mapping:
                action_name = action_mapping[param_name]
                if action_name in self._action_handlers:
                    handler = self._action_handlers[action_name]
                    updated_state = handler(updated_state, param_value)
        
        return updated_state


# Global instance to be used across the application
state_action_handler = StateActionHandler()