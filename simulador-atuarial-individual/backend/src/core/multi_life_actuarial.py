"""
Módulo de cálculos atuariais multi-vida
Funções especializadas para pensões, reversão e herança
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_joint_survival(
    survival_probs_participant: np.ndarray,
    survival_probs_dependent: np.ndarray,
    join_type: str = "last_survivor"
) -> np.ndarray:
    """
    Calcula probabilidades de sobrevivência conjunta entre duas vidas

    Args:
        survival_probs_participant: tPx do titular (array de probabilidades cumulativas)
        survival_probs_dependent: tPy do dependente
        join_type:
            - "last_survivor": P(pelo menos um vivo) = 1 - P(ambos mortos)
            - "joint_life": P(ambos vivos)
            - "survivor_only": P(titular morto E dependente vivo)

    Returns:
        Array com probabilidades combinadas

    Fórmulas:
        - Last survivor: 1 - (1 - Px) × (1 - Py)
        - Joint life: Px × Py
        - Survivor only: (1 - Px) × Py
    """
    px = np.array(survival_probs_participant)
    py = np.array(survival_probs_dependent)

    # Ajustar tamanhos se diferentes (pegar o menor)
    min_len = min(len(px), len(py))
    px = px[:min_len]
    py = py[:min_len]

    if join_type == "last_survivor":
        # P(X vivo OU Y vivo) = 1 - P(ambos mortos)
        return 1 - (1 - px) * (1 - py)

    elif join_type == "joint_life":
        # P(X vivo E Y vivo)
        return px * py

    elif join_type == "survivor_only":
        # P(X morto E Y vivo) - base para pensão por morte
        return (1 - px) * py

    else:
        raise ValueError(f"join_type inválido: {join_type}. Use: last_survivor, joint_life, survivor_only")


def calculate_survivor_benefit_stream(
    benefit_amount: float,
    survival_probs_participant: np.ndarray,
    survival_probs_dependent: np.ndarray,
    survivor_percentage: float,
    discount_rate: float,
    timing: str = "postecipado",
    benefit_months_per_year: int = 13
) -> Dict[str, Any]:
    """
    Calcula VPA de benefícios de sobrevivência (pensão por morte)

    Args:
        benefit_amount: Valor do benefício mensal original
        survival_probs_participant: Probabilidades de sobrevivência do titular
        survival_probs_dependent: Probabilidades de sobrevivência do dependente
        survivor_percentage: % do benefício que vai para o sobrevivente
        discount_rate: Taxa de desconto anual
        timing: "antecipado" ou "postecipado"
        benefit_months_per_year: Número de pagamentos por ano (13 = com 13º)

    Returns:
        {
            'vpa_survivor_benefits': float,
            'survivor_cash_flows': np.ndarray,
            'survivor_only_probs': np.ndarray,
            'joint_life_probs': np.ndarray
        }

    Fórmula:
        VPA_pensão = Σ(t=0 até ω) B_pensão × P(titular morto E dependente vivo) × v^t
    """
    # Probabilidade de titular morto e dependente vivo (cada período)
    survivor_only_probs = calculate_joint_survival(
        survival_probs_participant,
        survival_probs_dependent,
        join_type="survivor_only"
    )

    # Benefício do sobrevivente
    survivor_benefit = benefit_amount * (survivor_percentage / 100) * benefit_months_per_year

    # Fluxo de caixa anual para sobrevivente
    survivor_cash_flows = survivor_benefit * survivor_only_probs

    # Calcular VPA
    periods = len(survivor_cash_flows)
    timing_adjustment = 0.0 if timing == "antecipado" else 1.0

    vpa = 0.0
    for t in range(periods):
        discount_factor = (1 + discount_rate) ** (t + timing_adjustment)
        vpa += survivor_cash_flows[t] / discount_factor

    # Também calcular probabilidades de vida conjunta (para referência)
    joint_life_probs = calculate_joint_survival(
        survival_probs_participant,
        survival_probs_dependent,
        join_type="joint_life"
    )

    return {
        'vpa_survivor_benefits': vpa,
        'survivor_cash_flows': survivor_cash_flows,
        'survivor_only_probs': survivor_only_probs,
        'joint_life_probs': joint_life_probs
    }


def calculate_inheritance_value_by_age(
    initial_balance: float,
    projected_balances: np.ndarray,
    survival_probs_participant: np.ndarray,
    participant_age: int,
    projection_years: int
) -> Dict[str, Any]:
    """
    Calcula o valor da função de heritor por idade do titular

    Esta função mostra quanto cada dependente herdaria se o titular
    falecesse em cada idade específica.

    Args:
        initial_balance: Saldo inicial
        projected_balances: Saldo projetado por ano
        survival_probs_participant: Probabilidades de sobrevivência do titular
        participant_age: Idade inicial do titular
        projection_years: Anos de projeção

    Returns:
        {
            'inheritance_by_age': List[float],  # Valor herdado em cada idade
            'ages': List[int],                   # Idades correspondentes
            'death_probability': List[float],    # Prob de morte em cada idade
            'expected_inheritance_value': float  # Valor esperado de herança
        }

    Fórmula:
        Valor_Heranca(idade x) = Saldo(x) × P(morte na idade x)
        P(morte na idade x) = tPx-1 × qx
    """
    ages = list(range(participant_age, participant_age + projection_years + 1))
    inheritance_values = []
    death_probs = []

    # Garantir que arrays têm mesmo tamanho
    balances = np.array(projected_balances)
    survival = np.array(survival_probs_participant)

    # Calcular para cada idade
    for t in range(min(len(ages), len(balances))):
        # Saldo na idade t
        balance_at_age = balances[t] if t < len(balances) else balances[-1]

        # Probabilidade de estar vivo até t e morrer em t
        if t == 0:
            # Na idade inicial
            death_prob = 1 - survival[0] if len(survival) > 0 else 0
        elif t < len(survival):
            # P(morte no ano t) = P(vivo até t-1) - P(vivo até t)
            death_prob = survival[t-1] - survival[t]
        else:
            death_prob = 0

        # Valor da herança se morrer nesta idade
        inheritance_value = balance_at_age * death_prob

        inheritance_values.append(float(inheritance_value))
        death_probs.append(float(death_prob))

    # Valor esperado de herança = Σ(saldo × P(morte))
    expected_inheritance = sum(inheritance_values)

    return {
        'inheritance_by_age': inheritance_values,
        'ages': ages[:len(inheritance_values)],
        'death_probability': death_probs,
        'expected_inheritance_value': expected_inheritance
    }


def calculate_family_protection_score(
    vpa_survivor_benefits: float,
    target_benefit: float,
    survivor_income_ratio: float,
    has_dependents: bool,
    include_survivor_benefits: bool
) -> float:
    """
    Calcula um score de proteção familiar (0-100)

    Args:
        vpa_survivor_benefits: VPA dos benefícios de sobrevivência
        target_benefit: Benefício mensal alvo
        survivor_income_ratio: Razão renda sobrevivente / benefício
        has_dependents: Se há dependentes cadastrados
        include_survivor_benefits: Se benefícios de sobrevivência estão habilitados

    Returns:
        Score de 0 a 100

    Critérios:
        - Sem dependentes: 100 (não aplicável)
        - Com dependentes mas sem proteção: 0
        - Com proteção parcial: proporcional à cobertura
        - Com proteção adequada (>70%): 70-100
    """
    if not has_dependents:
        return 100.0  # Sem dependentes = proteção não aplicável

    if not include_survivor_benefits:
        return 0.0  # Dependentes sem proteção

    # Score baseado na razão de renda do sobrevivente
    if survivor_income_ratio >= 1.0:
        return 100.0  # Proteção integral ou superior
    elif survivor_income_ratio >= 0.7:
        # Proteção adequada (70-100%)
        return 70 + (survivor_income_ratio - 0.7) * 100
    else:
        # Proteção parcial (0-70%)
        return survivor_income_ratio * 100
