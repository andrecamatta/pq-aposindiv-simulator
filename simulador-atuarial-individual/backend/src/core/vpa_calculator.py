"""
Módulo de cálculos de Valor Presente Atuarial (VPA)
Extrai e centraliza a lógica de cálculo de VPA do motor atuarial.
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class VPAContext:
    """Contexto para cálculos de VPA"""
    discount_rate_monthly: float
    months_to_retirement: int
    payment_timing: str  # "antecipado" ou "postecipado"
    
    @property
    def timing_adjustment(self) -> float:
        """Ajuste temporal baseado no timing de pagamento"""
        # Usar convenção padrão: antecipado = 0.0, postecipado = 1.0
        return 0.0 if self.payment_timing == "antecipado" else 1.0


def calculate_vpa_benefits(
    monthly_benefits: List[float],
    survival_probs: List[float],
    months_to_retirement: int,
    context: VPAContext
) -> float:
    """
    Calcula VPA dos benefícios futuros (pós-aposentadoria)
    
    Args:
        monthly_benefits: Lista de benefícios mensais projetados
        survival_probs: Lista de probabilidades de sobrevivência
        months_to_retirement: Número de meses até aposentadoria
        context: Contexto com parâmetros de desconto e timing
    
    Returns:
        Valor presente atuarial dos benefícios
    """
    vpa_benefits = 0.0
    
    for month, (benefit, survival_prob) in enumerate(zip(monthly_benefits, survival_probs)):
        # Considerar apenas período pós-aposentadoria
        if month >= months_to_retirement and benefit > 0:
            # Fator de desconto mensal ajustado pelo timing
            adjusted_month = month + context.timing_adjustment
            discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
            
            # Acumular VPA com probabilidade de sobrevivência
            vpa_benefits += (benefit * survival_prob) / discount_factor
    
    return vpa_benefits


def calculate_vpa_contributions(
    monthly_contributions: List[float],
    survival_probs: List[float],
    months_to_retirement: int,
    context: VPAContext
) -> float:
    """
    Calcula VPA das contribuições futuras (pré-aposentadoria)
    
    Args:
        monthly_contributions: Lista de contribuições mensais projetadas
        survival_probs: Lista de probabilidades de sobrevivência
        months_to_retirement: Número de meses até aposentadoria
        context: Contexto com parâmetros de desconto e timing
    
    Returns:
        Valor presente atuarial das contribuições
    """
    vpa_contributions = 0.0
    
    for month, (contribution, survival_prob) in enumerate(zip(monthly_contributions, survival_probs)):
        # Considerar apenas período pré-aposentadoria
        if month < months_to_retirement and contribution > 0:
            # Fator de desconto mensal ajustado pelo timing
            adjusted_month = month + context.timing_adjustment
            discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
            
            # Acumular VPA com probabilidade de sobrevivência
            vpa_contributions += (contribution * survival_prob) / discount_factor
    
    return vpa_contributions


def calculate_vpa_target_benefit(
    monthly_target_benefit: float,
    survival_probs: List[float],
    months_to_retirement: int,
    context: VPAContext
) -> float:
    """
    Calcula VPA do benefício alvo como anuidade vitalícia mensal
    
    Args:
        monthly_target_benefit: Valor mensal do benefício alvo
        survival_probs: Lista de probabilidades de sobrevivência
        months_to_retirement: Número de meses até aposentadoria
        context: Contexto com parâmetros de desconto e timing
    
    Returns:
        Valor presente atuarial do benefício alvo
    """
    vpa_target = 0.0
    
    for month in range(months_to_retirement, len(survival_probs)):
        # Fator de desconto mensal ajustado pelo timing
        adjusted_month = month + context.timing_adjustment
        discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
        
        # Acumular VPA do benefício constante
        vpa_target += (monthly_target_benefit * survival_probs[month]) / discount_factor
    
    return vpa_target


def calculate_vpa_salaries(
    monthly_salaries: List[float],
    survival_probs: List[float],
    months_to_retirement: int,
    context: VPAContext
) -> float:
    """
    Calcula VPA dos salários futuros (pré-aposentadoria)
    
    Args:
        monthly_salaries: Lista de salários mensais projetados
        survival_probs: Lista de probabilidades de sobrevivência
        months_to_retirement: Número de meses até aposentadoria
        context: Contexto com parâmetros de desconto e timing
    
    Returns:
        Valor presente atuarial dos salários
    """
    vpa_salaries = 0.0
    
    for month, (salary, survival_prob) in enumerate(zip(monthly_salaries, survival_probs)):
        # Considerar apenas período pré-aposentadoria
        if month < months_to_retirement and salary > 0:
            # Fator de desconto mensal ajustado pelo timing
            adjusted_month = month + context.timing_adjustment
            discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
            
            # Acumular VPA dos salários
            vpa_salaries += (salary * survival_prob) / discount_factor
    
    return vpa_salaries


def calculate_yearly_vpa_projections(
    monthly_benefits: List[float],
    monthly_contributions: List[float],
    survival_probs: List[float],
    months_to_retirement: int,
    context: VPAContext,
    projection_years: int
) -> Dict[str, List[float]]:
    """
    Calcula projeções anuais de VPA para análise de evolução temporal
    
    Args:
        monthly_benefits: Lista de benefícios mensais projetados
        monthly_contributions: Lista de contribuições mensais projetadas
        survival_probs: Lista de probabilidades de sobrevivência
        months_to_retirement: Número de meses até aposentadoria
        context: Contexto com parâmetros de desconto e timing
        projection_years: Anos de projeção
    
    Returns:
        Dicionário com listas anuais de VPA de benefícios, contribuições e RMBA
    """
    vpa_benefits_yearly = []
    vpa_contributions_yearly = []
    rmba_yearly = []
    
    timing_adjustment = context.timing_adjustment
    
    # Para cada ano da projeção, calcular VPAs restantes
    for year in range(projection_years):
        year_start_month = year * 12
        
        # VPA dos benefícios futuros a partir deste ano
        vpa_benefits = 0.0
        for month in range(year_start_month, len(monthly_benefits)):
            if month >= months_to_retirement and monthly_benefits[month] > 0:
                adjusted_month = (month - year_start_month) + timing_adjustment
                discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                vpa_benefits += (monthly_benefits[month] * survival_probs[month]) / discount_factor
        
        # VPA das contribuições futuras a partir deste ano
        vpa_contributions = 0.0
        for month in range(year_start_month, min(months_to_retirement, len(monthly_contributions))):
            if monthly_contributions[month] > 0:
                adjusted_month = (month - year_start_month) + timing_adjustment
                discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
                vpa_contributions += (monthly_contributions[month] * survival_probs[month]) / discount_factor
        
        # RMBA neste ponto = VPA benefícios - VPA contribuições
        rmba_year = vpa_benefits - vpa_contributions
        
        vpa_benefits_yearly.append(vpa_benefits)
        vpa_contributions_yearly.append(vpa_contributions)
        rmba_yearly.append(rmba_year)
    
    return {
        "vpa_benefits": vpa_benefits_yearly,
        "vpa_contributions": vpa_contributions_yearly,
        "rmba": rmba_yearly
    }


def calculate_sustainable_benefit(
    initial_balance: float,
    vpa_contributions: float,
    survival_probs: List[float],
    months_to_retirement: int,
    context: VPAContext,
    benefit_annual_factor: float = 12.0
) -> float:
    """
    Calcula benefício sustentável usando equilíbrio atuarial
    
    Args:
        initial_balance: Saldo inicial acumulado
        vpa_contributions: VPA das contribuições futuras
        survival_probs: Lista de probabilidades de sobrevivência
        months_to_retirement: Número de meses até aposentadoria
        context: Contexto com parâmetros de desconto e timing
        benefit_annual_factor: Fator para conversão mensal → anual
    
    Returns:
        Benefício mensal sustentável
    """
    # Recursos totais disponíveis
    total_resources = initial_balance + vpa_contributions
    
    # Calcular fator de anuidade vitalícia mensal
    annuity_factor = 0.0
    timing_adjustment = context.timing_adjustment
    
    for month in range(months_to_retirement, len(survival_probs)):
        adjusted_month = month + timing_adjustment
        discount_factor = (1 + context.discount_rate_monthly) ** adjusted_month
        annuity_factor += survival_probs[month] / discount_factor
    
    # Ajustar por múltiplos pagamentos anuais (13º, 14º salário)
    effective_annuity_factor = annuity_factor * benefit_annual_factor / 12.0
    
    # Benefício sustentável = Recursos / Fator de Anuidade
    if effective_annuity_factor > 0:
        return total_resources / effective_annuity_factor
    else:
        return 0.0