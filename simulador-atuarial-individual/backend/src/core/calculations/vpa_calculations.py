"""
Cálculos de Valor Presente Atuarial (VPA) especializados
Consolida funções relacionadas a VPA de utils/vpa.py
"""

from typing import List
from .basic_math import calculate_discount_factor


def calculate_actuarial_present_value(
    cash_flows: List[float],
    survival_probs: List[float],
    discount_rate: float,
    timing: str = "postecipado",
    start_month: int = 0,
    end_month: int = None
) -> float:
    """
    Calcula Valor Presente Atuarial de um fluxo de caixa considerando mortalidade
    
    Args:
        cash_flows: Fluxos de caixa por período
        survival_probs: Probabilidades de sobrevivência cumulativas
        discount_rate: Taxa de desconto por período
        timing: "antecipado" ou "postecipado"
        start_month: Mês de início do cálculo
        end_month: Mês de fim do cálculo (None = até o final)
    
    Returns:
        VPA total
    """
    if end_month is None:
        end_month = min(len(cash_flows), len(survival_probs))
    
    vpa_total = 0.0
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0
    
    for month in range(start_month, min(end_month, len(cash_flows), len(survival_probs))):
        cash_flow = cash_flows[month]
        survival_prob = survival_probs[month]
        
        if cash_flow != 0 and survival_prob > 0:  # Otimização
            discount_factor = calculate_discount_factor(discount_rate, month, timing_adjustment)
            vpa_total += cash_flow * survival_prob * discount_factor
    
    return vpa_total


def calculate_vpa_benefits_contributions(
    monthly_benefits: List[float],
    monthly_contributions: List[float],
    monthly_survival_probs: List[float],
    discount_rate_monthly: float,
    timing: str,
    months_to_retirement: int,
    admin_fee_monthly: float = 0.0
) -> tuple:
    """
    Calcula VPA de benefícios e contribuições considerando custos administrativos
    
    Args:
        monthly_benefits: Lista de benefícios mensais
        monthly_contributions: Lista de contribuições mensais
        monthly_survival_probs: Probabilidades de sobrevivência
        discount_rate_monthly: Taxa de desconto mensal
        timing: Timing dos pagamentos
        months_to_retirement: Meses até aposentadoria
        admin_fee_monthly: Taxa administrativa mensal
    
    Returns:
        Tupla (VPA benefícios, VPA contribuições líquido)
    """
    # VPA dos benefícios (sempre começam na aposentadoria)
    vpa_benefits = calculate_actuarial_present_value(
        monthly_benefits,
        monthly_survival_probs,
        discount_rate_monthly,
        timing,
        start_month=months_to_retirement
    )
    
    # VPA das contribuições com taxa administrativa aplicada CORRETAMENTE
    # Taxa admin deve ser aplicada em cada contribuição individual, não no VPA total
    if admin_fee_monthly > 0:
        # Aplicar taxa admin em cada contribuição antes do cálculo do VPA
        net_contributions = []
        for month in range(len(monthly_contributions)):
            if month < months_to_retirement:
                # Durante fase ativa: contribuição líquida = bruta * (1 - taxa_admin)
                net_contribution = monthly_contributions[month] * (1 - admin_fee_monthly)
                net_contributions.append(net_contribution)
            else:
                # Após aposentadoria: sem contribuições
                net_contributions.append(0.0)
        
        # Calcular VPA das contribuições líquidas
        vpa_contributions_net = calculate_actuarial_present_value(
            net_contributions,
            monthly_survival_probs,
            discount_rate_monthly,
            timing,
            start_month=0,
            end_month=months_to_retirement
        )
    else:
        # Sem taxa administrativa
        vpa_contributions_net = calculate_actuarial_present_value(
            monthly_contributions,
            monthly_survival_probs,
            discount_rate_monthly,
            timing,
            start_month=0,
            end_month=months_to_retirement
        )
    
    return vpa_benefits, vpa_contributions_net


def calculate_sustainable_benefit(
    initial_balance: float,
    vpa_contributions: float,
    monthly_survival_probs: List[float],
    discount_rate_monthly: float,
    timing: str,
    months_to_retirement: int,
    benefit_months_per_year: int = 12,
    admin_fee_monthly: float = 0.0
) -> float:
    """
    Calcula benefício sustentável que equilibra recursos com VPA de benefícios
    
    Args:
        initial_balance: Saldo inicial disponível
        vpa_contributions: VPA das contribuições futuras
        monthly_survival_probs: Probabilidades de sobrevivência
        discount_rate_monthly: Taxa de desconto mensal
        timing: Timing dos pagamentos
        months_to_retirement: Meses até aposentadoria
        benefit_months_per_year: Número de pagamentos anuais de benefício
        admin_fee_monthly: Taxa administrativa mensal
    
    Returns:
        Benefício mensal sustentável
    """
    # Recursos totais disponíveis
    total_resources = initial_balance + vpa_contributions
    
    if total_resources <= 0:
        return 0.0
    
    # Calcular fator de anuidade vitalícia a partir da aposentadoria
    annuity_factor = 0.0
    max_months = len(monthly_survival_probs)
    
    for month in range(months_to_retirement, max_months):
        if month < len(monthly_survival_probs):
            survival_prob = monthly_survival_probs[month]
            
            if survival_prob > 0:
                discount_factor = calculate_discount_factor(discount_rate_monthly, month, timing)
                
                # Ajuste para custos administrativos
                net_discount_factor = discount_factor * (1 - admin_fee_monthly)
                
                # Considerar múltiplos pagamentos por ano
                months_in_year = month % 12
                payment_multiplier = 1.0
                
                # Pagamentos extras (13º, 14º, etc.)
                extra_payments = benefit_months_per_year - 12
                if extra_payments > 0:
                    if months_in_year == 11:  # Dezembro
                        if extra_payments >= 1:
                            payment_multiplier += 1.0
                    if months_in_year == 0:  # Janeiro
                        if extra_payments >= 2:
                            payment_multiplier += 1.0
                
                annuity_factor += survival_prob * net_discount_factor * payment_multiplier
    
    # Calcular benefício sustentável
    if annuity_factor > 0:
        return total_resources / annuity_factor
    else:
        return 0.0


def calculate_life_annuity_immediate(
    survival_probs: List[float],
    discount_rate: float,
    start_period: int = 0
) -> float:
    """
    Calcula fator de anuidade vitalícia imediata (postecipada)
    
    Args:
        survival_probs: Probabilidades de sobrevivência cumulativas
        discount_rate: Taxa de desconto por período
        start_period: Período de início
    
    Returns:
        Fator de anuidade vitalícia
    """
    annuity_factor = 0.0
    
    for period in range(start_period, len(survival_probs)):
        survival_prob = survival_probs[period]
        if survival_prob > 0:
            discount_factor = (1 + discount_rate) ** -(period + 1)  # Postecipado
            annuity_factor += survival_prob * discount_factor
    
    return annuity_factor


def calculate_life_annuity_due(
    survival_probs: List[float],
    discount_rate: float,
    start_period: int = 0
) -> float:
    """
    Calcula fator de anuidade vitalícia antecipada
    
    Args:
        survival_probs: Probabilidades de sobrevivência cumulativas
        discount_rate: Taxa de desconto por período
        start_period: Período de início
    
    Returns:
        Fator de anuidade vitalícia antecipada
    """
    annuity_factor = 0.0
    
    for period in range(start_period, len(survival_probs)):
        survival_prob = survival_probs[period]
        if survival_prob > 0:
            discount_factor = (1 + discount_rate) ** -period  # Antecipado
            annuity_factor += survival_prob * discount_factor
    
    return annuity_factor


def calculate_deferred_annuity(
    survival_probs: List[float],
    discount_rate: float,
    deferral_periods: int,
    annuity_periods: int = None
) -> float:
    """
    Calcula valor presente de anuidade diferida
    
    Args:
        survival_probs: Probabilidades de sobrevivência
        discount_rate: Taxa de desconto
        deferral_periods: Períodos de diferimento
        annuity_periods: Períodos de anuidade (None = vitalícia)
    
    Returns:
        Valor presente da anuidade diferida
    """
    if annuity_periods is None:
        end_period = len(survival_probs)
    else:
        end_period = min(deferral_periods + annuity_periods, len(survival_probs))
    
    annuity_factor = 0.0
    
    for period in range(deferral_periods, end_period):
        if period < len(survival_probs):
            survival_prob = survival_probs[period]
            if survival_prob > 0:
                discount_factor = (1 + discount_rate) ** -(period + 1)
                annuity_factor += survival_prob * discount_factor
    
    return annuity_factor