"""Testes unitários para modelos e utilitários"""
import pytest
import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Adiciona o diretório src ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.participant import SimulatorState
from src.models.results import SimulatorResults
from src.utils.rates import annual_to_monthly_rate, monthly_to_annual_rate
from src.utils.formatters import format_currency, format_percentage


class TestSimulatorState:
    """Testes para o modelo SimulatorState"""
    
    def test_state_creation_minimal(self):
        """Testa criação com campos mínimos"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        
        assert state.age == 30
        assert state.gender == "M"
        assert state.salary == 5000.0
        assert state.retirement_age == 65
        assert state.contribution_rate == 10.0
    
    def test_state_creation_bd_complete(self):
        """Testa criação completa para BD"""
        state = SimulatorState(
            age=35,
            gender="F",
            salary=8000.0,
            retirement_age=60,
            contribution_rate=12.0,
            target_benefit=5000.0,
            benefit_target_mode="VALUE",
            mortality_table="AT_2000",
            discount_rate=0.05,
            salary_growth_real=0.02,
            plan_type="BD"
        )
        
        assert state.plan_type == "BD"
        assert state.target_benefit == 5000.0
        assert state.benefit_target_mode == "VALUE"
        assert state.salary_growth_real == 0.02
    
    def test_state_creation_cd_complete(self):
        """Testa criação completa para CD"""
        state = SimulatorState(
            age=40,
            gender="M",
            salary=10000.0,
            retirement_age=65,
            contribution_rate=15.0,
            initial_balance=50000.0,
            accrual_rate=0.06,
            mortality_table="BR_EMS_2021",
            discount_rate=0.055,
            plan_type="CD",
            cd_conversion_mode="ACTUARIAL"
        )
        
        assert state.plan_type == "CD"
        assert state.initial_balance == 50000.0
        assert state.accrual_rate == 0.06
        assert state.cd_conversion_mode == "ACTUARIAL"
    
    def test_state_validation_age(self):
        """Testa validação de idade"""
        # Idade válida
        state = SimulatorState(
            age=25,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        assert state.age == 25
        
        # Idade extrema mas válida
        state_old = SimulatorState(
            age=70,
            gender="F",
            salary=5000.0,
            retirement_age=75,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        assert state_old.age == 70
    
    def test_state_validation_gender(self):
        """Testa validação de gênero"""
        # Gênero masculino
        state_m = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        assert state_m.gender == "M"
        
        # Gênero feminino
        state_f = SimulatorState(
            age=30,
            gender="F",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        assert state_f.gender == "F"
    
    def test_state_model_copy(self):
        """Testa cópia do modelo"""
        original_state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        
        # Cópia sem modificações
        copied_state = original_state.model_copy()
        assert copied_state.age == original_state.age
        assert copied_state.salary == original_state.salary
        
        # Cópia com modificações
        modified_state = original_state.model_copy(update={'age': 35, 'salary': 6000.0})
        assert modified_state.age == 35
        assert modified_state.salary == 6000.0
        assert modified_state.gender == original_state.gender  # Não modificado
    
    def test_state_default_values(self):
        """Testa valores padrão"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        
        # Verifica valores padrão
        assert state.plan_type == "BD"  # Padrão
        assert state.initial_balance == 0.0  # Padrão
        assert state.admin_fee_rate == 0.0  # Padrão
        assert state.loading_fee_rate == 0.0  # Padrão


class TestSimulatorResults:
    """Testes para o modelo SimulatorResults"""
    
    def test_results_creation_bd(self):
        """Testa criação de resultados BD"""
        results = SimulatorResults(
            rmba=150000.0,
            total_contributions=120000.0,
            deficit_surplus=30000.0,
            sustainable_replacement_ratio=65.5,
            cash_flows=[1000, 1100, 1200],
            accumulated_reserves=[10000, 21000, 33000]
        )
        
        assert results.rmba == 150000.0
        assert results.total_contributions == 120000.0
        assert results.deficit_surplus == 30000.0
        assert results.sustainable_replacement_ratio == 65.5
        assert len(results.cash_flows) == 3
        assert len(results.accumulated_reserves) == 3
    
    def test_results_creation_cd(self):
        """Testa criação de resultados CD"""
        results = SimulatorResults(
            accumulated_balance_retirement=500000.0,
            estimated_benefit=4500.0,
            contribution_phase_balances=[0, 5000, 12000, 20000]
        )
        
        assert results.accumulated_balance_retirement == 500000.0
        assert results.estimated_benefit == 4500.0
        assert len(results.contribution_phase_balances) == 4
    
    def test_results_optional_fields(self):
        """Testa campos opcionais dos resultados"""
        results = SimulatorResults(
            rmba=100000.0,
            total_contributions=80000.0,
            deficit_surplus=20000.0,
            sustainable_replacement_ratio=70.0,
            cash_flows=[],
            accumulated_reserves=[],
            suggestions=[]
        )
        
        assert results.suggestions == []
        assert results.cash_flows == []
        assert results.accumulated_reserves == []
    
    def test_results_model_copy(self):
        """Testa cópia do modelo de resultados"""
        original_results = SimulatorResults(
            rmba=100000.0,
            total_contributions=80000.0,
            deficit_surplus=20000.0,
            sustainable_replacement_ratio=70.0,
            cash_flows=[1000, 1100],
            accumulated_reserves=[10000, 21000]
        )
        
        copied_results = original_results.model_copy()
        assert copied_results.rmba == original_results.rmba
        assert copied_results.cash_flows == original_results.cash_flows
        
        # Modificação não deve afetar original
        copied_results.rmba = 200000.0
        assert original_results.rmba == 100000.0


class TestRateUtils:
    """Testes para utilitários de taxas"""
    
    def test_annual_to_monthly_conversion(self):
        """Testa conversão de taxa anual para mensal"""
        # 12% ao ano
        annual_rate = 0.12
        monthly_rate = annual_to_monthly_rate(annual_rate)
        
        # Taxa mensal deve ser menor que anual/12 devido a juros compostos
        assert monthly_rate < annual_rate / 12
        assert monthly_rate > 0
        
        # Verifica valor aproximado
        expected_monthly = (1 + annual_rate) ** (1/12) - 1
        assert abs(monthly_rate - expected_monthly) < 0.0001
    
    def test_monthly_to_annual_conversion(self):
        """Testa conversão de taxa mensal para anual"""
        # 1% ao mês
        monthly_rate = 0.01
        annual_rate = monthly_to_annual_rate(monthly_rate)
        
        # Taxa anual deve ser maior que mensal*12 devido a juros compostos
        assert annual_rate > monthly_rate * 12
        
        # Verifica valor aproximado
        expected_annual = (1 + monthly_rate) ** 12 - 1
        assert abs(annual_rate - expected_annual) < 0.0001
    
    def test_rate_conversion_round_trip(self):
        """Testa conversão ida e volta"""
        original_annual = 0.08  # 8% ao ano
        
        # Converte para mensal e volta para anual
        monthly = annual_to_monthly_rate(original_annual)
        back_to_annual = monthly_to_annual_rate(monthly)
        
        # Deve ser muito próximo ao original
        assert abs(back_to_annual - original_annual) < 0.000001
    
    def test_rate_conversion_edge_cases(self):
        """Testa casos extremos de conversão"""
        # Taxa zero
        assert annual_to_monthly_rate(0.0) == 0.0
        assert monthly_to_annual_rate(0.0) == 0.0
        
        # Taxa muito pequena
        small_annual = 0.001  # 0.1%
        small_monthly = annual_to_monthly_rate(small_annual)
        assert small_monthly > 0
        assert small_monthly < small_annual
        
        # Taxa negativa (deflação)
        negative_annual = -0.02  # -2%
        negative_monthly = annual_to_monthly_rate(negative_annual)
        assert negative_monthly < 0
        assert negative_monthly > negative_annual / 12
    
    def test_rate_conversion_high_rates(self):
        """Testa conversão com taxas altas"""
        # 50% ao ano
        high_annual = 0.50
        high_monthly = annual_to_monthly_rate(high_annual)
        
        assert high_monthly > 0
        assert high_monthly < high_annual / 12
        
        # Verifica conversão reversa
        back_annual = monthly_to_annual_rate(high_monthly)
        assert abs(back_annual - high_annual) < 0.001


class TestFormatters:
    """Testes para utilitários de formatação"""
    
    def test_format_currency_basic(self):
        """Testa formatação básica de moeda"""
        # Valor inteiro
        assert "1.000" in format_currency(1000)
        assert "R$" in format_currency(1000)
        
        # Valor com decimais
        formatted = format_currency(1234.56)
        assert "1.234" in formatted
        assert "56" in formatted
        
        # Valor zero
        zero_formatted = format_currency(0)
        assert "0" in zero_formatted
        assert "R$" in zero_formatted
    
    def test_format_currency_negative(self):
        """Testa formatação de valores negativos"""
        negative_formatted = format_currency(-1000)
        
        # Deve conter o valor 1000 e indicação de negativo
        assert "1.000" in negative_formatted
        assert ("-" in negative_formatted or "(" in negative_formatted)
    
    def test_format_currency_large_values(self):
        """Testa formatação de valores grandes"""
        large_value = 1234567.89
        formatted = format_currency(large_value)
        
        # Deve ter separadores de milhares
        assert "1.234.567" in formatted or "1,234,567" in formatted
    
    def test_format_percentage_basic(self):
        """Testa formatação básica de percentual"""
        # 50%
        assert "50" in format_percentage(0.5)
        assert "%" in format_percentage(0.5)
        
        # 10%
        assert "10" in format_percentage(0.1)
        
        # 0%
        zero_formatted = format_percentage(0)
        assert "0" in zero_formatted
        assert "%" in zero_formatted
    
    def test_format_percentage_decimals(self):
        """Testa formatação de percentuais com decimais"""
        # 12.5%
        formatted = format_percentage(0.125)
        assert "12" in formatted
        assert "5" in formatted or "50" in formatted  # Pode ser 12.5% ou 12,50%
        
        # Percentual muito pequeno
        small_formatted = format_percentage(0.001)
        assert "0" in small_formatted
        assert "%" in small_formatted
    
    def test_format_percentage_over_100(self):
        """Testa formatação de percentuais acima de 100%"""
        formatted = format_percentage(1.5)  # 150%
        assert "150" in formatted
        assert "%" in formatted
    
    def test_format_percentage_negative(self):
        """Testa formatação de percentuais negativos"""
        negative_formatted = format_percentage(-0.1)
        assert "-" in negative_formatted
        assert "10" in negative_formatted
        assert "%" in negative_formatted


class TestDataValidation:
    """Testes para validação de dados"""
    
    def test_numeric_field_validation(self):
        """Testa validação de campos numéricos"""
        # Valores válidos
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        
        assert isinstance(state.age, int)
        assert isinstance(state.salary, float)
        assert isinstance(state.contribution_rate, float)
    
    def test_string_field_validation(self):
        """Testa validação de campos de string"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        
        assert isinstance(state.gender, str)
        assert isinstance(state.mortality_table, str)
        assert len(state.gender) > 0
        assert len(state.mortality_table) > 0
    
    def test_boolean_field_validation(self):
        """Testa validação de campos booleanos"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            use_ettj=True
        )
        
        assert isinstance(state.use_ettj, bool)
        assert state.use_ettj is True
    
    def test_optional_field_handling(self):
        """Testa tratamento de campos opcionais"""
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06
        )
        
        # Campos opcionais devem ter valores padrão ou None
        assert state.target_benefit is None or isinstance(state.target_benefit, (int, float))
        assert state.target_replacement_rate is None or isinstance(state.target_replacement_rate, (int, float))
    
    def test_date_field_handling(self):
        """Testa tratamento de campos de data"""
        # Se houver campos de data, devem ser tratados corretamente
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.0,
            retirement_age=65,
            contribution_rate=10.0,
            mortality_table="BR_EMS_2021",
            discount_rate=0.06,
            last_update=datetime.now().isoformat()
        )
        
        # last_update pode ser string ISO ou datetime
        assert isinstance(state.last_update, str)
    
    def test_decimal_precision_handling(self):
        """Testa tratamento de precisão decimal"""
        # Valores com muitas casas decimais
        state = SimulatorState(
            age=30,
            gender="M",
            salary=5000.123456789,
            retirement_age=65,
            contribution_rate=10.999999,
            mortality_table="BR_EMS_2021",
            discount_rate=0.061234567
        )
        
        # Valores devem ser aceitos
        assert state.salary > 5000
        assert state.contribution_rate < 11
        assert state.discount_rate > 0.06