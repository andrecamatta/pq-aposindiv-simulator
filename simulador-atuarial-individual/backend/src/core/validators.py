"""
Validadores centralizados para parâmetros atuariais
Consolida lógica de validação espalhada pelo código
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.participant import SimulatorState


class ValidationError(Exception):
    """Exceção personalizada para erros de validação"""
    pass


class StateValidator:
    """Validador centralizado para estados do simulador"""
    
    @staticmethod
    def validate_basic_parameters(state: 'SimulatorState') -> None:
        """
        Valida parâmetros básicos de entrada
        
        Args:
            state: Estado do simulador
            
        Raises:
            ValidationError: Se algum parâmetro for inválido
        """
        errors = []
        
        # Validação de idade
        if state.age < 18 or state.age > 90:
            errors.append("Idade deve estar entre 18 e 90 anos")
        
        # Validação de idade de aposentadoria
        if state.retirement_age < 50 or state.retirement_age > 75:
            errors.append("Idade de aposentadoria deve estar entre 50 e 75 anos")
        
        # Validação lógica: idade atual vs idade de aposentadoria
        # Permitir pessoas já aposentadas (idade >= retirement_age)
        if state.age > state.retirement_age + 10:  # Limite razoável
            errors.append("Idade atual muito superior à idade de aposentadoria")
        
        # Validação de salário
        if state.salary <= 0:
            errors.append("Salário deve ser positivo")
        
        # Validação de salário extremo (proteção contra inputs absurdos)
        if state.salary > 1_000_000:  # 1 milhão por mês
            errors.append("Salário muito elevado (máximo R$ 1.000.000)")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod
    def validate_rates(state: 'SimulatorState') -> None:
        """
        Valida taxas de desconto, crescimento e contribuição
        
        Args:
            state: Estado do simulador
            
        Raises:
            ValidationError: Se alguma taxa for inválida
        """
        errors = []
        
        # Taxa de desconto
        if state.discount_rate < 0 or state.discount_rate > 1:  # 0% a 100%
            errors.append("Taxa de desconto deve estar entre 0% e 100%")
        
        # Taxa de crescimento salarial real
        if state.salary_growth_real < -0.1 or state.salary_growth_real > 0.2:  # -10% a +20%
            errors.append("Crescimento salarial real deve estar entre -10% e +20%")
        
        # Taxa de contribuição
        if state.contribution_rate < 0 or state.contribution_rate > 50:  # 0% a 50%
            errors.append("Taxa de contribuição deve estar entre 0% e 50%")
        
        # Taxa administrativa
        if state.admin_fee_rate < 0 or state.admin_fee_rate > 0.1:  # 0% a 10%
            errors.append("Taxa administrativa deve estar entre 0% e 10%")
        
        # Taxa de carregamento
        if state.loading_fee_rate < 0 or state.loading_fee_rate > 0.3:  # 0% a 30%
            errors.append("Taxa de carregamento deve estar entre 0% e 30%")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod
    def validate_cd_parameters(state: 'SimulatorState') -> None:
        """
        Valida parâmetros específicos para CD
        
        Args:
            state: Estado do simulador (deve ser CD)
            
        Raises:
            ValidationError: Se algum parâmetro CD for inválido
        """
        errors = []
        
        # Taxa de acumulação
        if hasattr(state, 'accumulation_rate') and state.accumulation_rate is not None:
            if state.accumulation_rate < 0 or state.accumulation_rate > 1:
                errors.append("Taxa de acumulação deve estar entre 0% e 100%")
        
        # Taxa de conversão
        if hasattr(state, 'conversion_rate') and state.conversion_rate is not None:
            if state.conversion_rate < 0 or state.conversion_rate > 1:
                errors.append("Taxa de conversão deve estar entre 0% e 100%")
        
        # Percentual de saque (para modalidade percentage)
        if hasattr(state, 'cd_withdrawal_percentage') and state.cd_withdrawal_percentage is not None:
            if state.cd_withdrawal_percentage < 1 or state.cd_withdrawal_percentage > 20:
                errors.append("Percentual de saque deve estar entre 1% e 20%")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod  
    def validate_benefit_parameters(state: 'SimulatorState') -> None:
        """
        Valida parâmetros de benefício alvo
        
        Args:
            state: Estado do simulador
            
        Raises:
            ValidationError: Se algum parâmetro de benefício for inválido
        """
        errors = []
        
        # Validação baseada no modo de benefício alvo - compatível com string ou enum
        benefit_mode = str(state.benefit_target_mode)  # Converte enum para string se necessário
        if benefit_mode == "VALUE":
            if state.target_benefit is not None:
                if state.target_benefit <= 0:
                    errors.append("Benefício alvo deve ser positivo")
                elif state.target_benefit > 100_000:  # R$ 100.000 por mês
                    errors.append("Benefício alvo muito elevado (máximo R$ 100.000)")
        
        elif benefit_mode == "REPLACEMENT_RATE":
            if state.target_replacement_rate is not None:
                if state.target_replacement_rate <= 0 or state.target_replacement_rate > 300:
                    errors.append("Taxa de reposição deve estar entre 0% e 300%")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod
    def validate_projection_parameters(state: 'SimulatorState') -> None:
        """
        Valida parâmetros de projeção temporal
        
        Args:
            state: Estado do simulador
            
        Raises:
            ValidationError: Se algum parâmetro de projeção for inválido  
        """
        errors = []
        
        # Anos de projeção
        if state.projection_years < 5 or state.projection_years > 80:
            errors.append("Anos de projeção devem estar entre 5 e 80 anos")
        
        # Meses por ano (salário e benefício)
        if state.salary_months_per_year < 12 or state.salary_months_per_year > 15:
            errors.append("Meses de salário por ano devem estar entre 12 e 15")
        
        if state.benefit_months_per_year < 12 or state.benefit_months_per_year > 15:
            errors.append("Meses de benefício por ano devem estar entre 12 e 15")
        
        # Saldo inicial
        if state.initial_balance < 0:
            errors.append("Saldo inicial não pode ser negativo")
        elif state.initial_balance > 10_000_000:  # 10 milhões
            errors.append("Saldo inicial muito elevado (máximo R$ 10.000.000)")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod
    def validate_mortality_parameters(state: 'SimulatorState') -> None:
        """
        Valida parâmetros de mortalidade
        
        Args:
            state: Estado do simulador
            
        Raises:
            ValidationError: Se algum parâmetro de mortalidade for inválido
        """
        errors = []
        
        # Suavização de mortalidade
        if state.mortality_aggravation < -50 or state.mortality_aggravation > 50:
            errors.append("Suavização de mortalidade deve estar entre -50% e +50%")
        
        # Validação básica de tábua de mortalidade
        if not state.mortality_table or len(state.mortality_table.strip()) == 0:
            errors.append("Tábua de mortalidade deve ser especificada")
        
        # Gênero
        if state.gender not in ['M', 'F']:
            errors.append("Gênero deve ser M (masculino) ou F (feminino)")
        
        if errors:
            raise ValidationError("; ".join(errors))
    
    @staticmethod
    def validate_full_state(state: 'SimulatorState') -> List[str]:
        """
        Executa validação completa do estado
        
        Args:
            state: Estado do simulador
            
        Returns:
            Lista de mensagens de erro (vazia se tudo válido)
        """
        all_errors = []
        
        validation_methods = [
            StateValidator.validate_basic_parameters,
            StateValidator.validate_rates,
            StateValidator.validate_benefit_parameters,
            StateValidator.validate_projection_parameters,
            StateValidator.validate_mortality_parameters
        ]
        
        # Para CD, adicionar validações específicas
        if hasattr(state, 'plan_type') and state.plan_type == "CD":
            validation_methods.append(StateValidator.validate_cd_parameters)
        
        for validation_method in validation_methods:
            try:
                validation_method(state)
            except ValidationError as e:
                all_errors.append(str(e))
        
        return all_errors
    
    @staticmethod
    def is_valid(state: 'SimulatorState') -> bool:
        """
        Verifica se o estado é válido
        
        Args:
            state: Estado do simulador
            
        Returns:
            True se válido, False caso contrário
        """
        return len(StateValidator.validate_full_state(state)) == 0


class CalculationValidator:
    """Validador para resultados de cálculos atuariais"""
    
    @staticmethod
    def validate_financial_result(value: float, name: str = "Valor") -> float:
        """
        Valida e sanitiza resultados financeiros
        
        Args:
            value: Valor a ser validado
            name: Nome do valor para mensagens de erro
            
        Returns:
            Valor sanitizado
        """
        import math
        
        # Tratar valores infinitos
        if math.isinf(value):
            if value > 0:
                return 1e6  # 1 milhão para +inf
            else:
                return -1e6  # -1 milhão para -inf
        
        # Tratar NaN
        if math.isnan(value):
            return 0.0
        
        # Validar faixas razoáveis
        if abs(value) > 1e9:  # 1 bilhão
            print(f"[VALIDATION_WARNING] {name} muito elevado: {value}, limitando")
            return 1e9 if value > 0 else -1e9
        
        return value
    
    @staticmethod
    def validate_probability(value: float, name: str = "Probabilidade") -> float:
        """
        Valida probabilidades (devem estar entre 0 e 1)
        
        Args:
            value: Probabilidade a ser validada
            name: Nome para mensagens de erro
            
        Returns:
            Probabilidade válida entre 0 e 1
        """
        import math
        
        if math.isnan(value) or math.isinf(value):
            return 0.0
        
        return max(0.0, min(1.0, value))
    
    @staticmethod
    def validate_rate(value: float, name: str = "Taxa") -> float:
        """
        Valida taxas (normalmente entre -1 e 10)
        
        Args:
            value: Taxa a ser validada  
            name: Nome para mensagens de erro
            
        Returns:
            Taxa válida
        """
        import math
        
        if math.isnan(value) or math.isinf(value):
            return 0.0
        
        # Limitar taxas a faixas razoáveis
        if value < -0.99:  # Mínimo -99%
            print(f"[VALIDATION_WARNING] {name} muito baixa: {value}, limitando a -99%")
            return -0.99
        elif value > 10.0:  # Máximo 1000%
            print(f"[VALIDATION_WARNING] {name} muito alta: {value}, limitando a 1000%")
            return 10.0
        
        return value
