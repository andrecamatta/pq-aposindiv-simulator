"""
Calculadora de Pensões por Morte e Herança
Gerencia múltiplos dependentes, reversão e distribuição de benefícios
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..models.participant import (
    FamilyComposition, FamilyMember, DependentType,
    BenefitShareType, InheritanceRule, Gender
)
from .multi_life_actuarial import (
    calculate_joint_survival,
    calculate_survivor_benefit_stream,
    calculate_inheritance_value_by_age,
    calculate_family_protection_score
)
from .mortality_tables import get_mortality_table

logger = logging.getLogger(__name__)


class SurvivorPensionCalculator:
    """
    Calculadora especializada para pensões por morte e herança

    Funcionalidades:
    - Cálculo de VPA para múltiplos dependentes
    - Distribuição de benefícios (cotas, proporcional, prioridade)
    - Reversão automática quando dependente perde elegibilidade
    - Valor da função de heritor por idade
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_multi_beneficiary_pension(
        self,
        participant_age: int,
        participant_gender: str,
        participant_mortality_table: str,
        participant_survival_probs: np.ndarray,
        family: FamilyComposition,
        benefit_amount: float,
        discount_rate: float,
        projection_years: int,
        timing: str = "postecipado",
        benefit_months_per_year: int = 13,
        mortality_aggravation: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calcula pensão com múltiplos dependentes

        Args:
            participant_age: Idade do titular
            participant_gender: Gênero do titular
            participant_mortality_table: Código da tábua do titular
            participant_survival_probs: Probabilidades de sobrevivência do titular
            family: Composição familiar completa
            benefit_amount: Valor do benefício mensal original
            discount_rate: Taxa de desconto anual
            projection_years: Anos de projeção
            timing: "antecipado" ou "postecipado"
            benefit_months_per_year: Pagamentos por ano (13 = com 13º)
            mortality_aggravation: Suavização da tábua

        Returns:
            {
                'vpa_survivor_benefits': float,
                'survivor_details': List[Dict],
                'total_survivor_income_ratio': float,
                'distribution_analysis': Dict
            }
        """
        if not family or not family.members:
            self.logger.info("Sem dependentes cadastrados")
            return {
                'vpa_survivor_benefits': 0.0,
                'survivor_details': [],
                'total_survivor_income_ratio': 0.0,
                'distribution_analysis': {}
            }

        # Calcular benefício para cada dependente
        survivor_details = []
        total_vpa = 0.0

        for member in family.members:
            try:
                # Calcular VPA para este dependente
                member_analysis = self._calculate_single_member_pension(
                    participant_age=participant_age,
                    participant_gender=participant_gender,
                    participant_mortality_table=participant_mortality_table,
                    participant_survival_probs=participant_survival_probs,
                    member=member,
                    benefit_amount=benefit_amount,
                    discount_rate=discount_rate,
                    projection_years=projection_years,
                    timing=timing,
                    benefit_months_per_year=benefit_months_per_year,
                    mortality_aggravation=mortality_aggravation,
                    family_config=family
                )

                survivor_details.append(member_analysis)
                total_vpa += member_analysis['vpa']

            except Exception as e:
                self.logger.error(f"Erro ao calcular pensão para {member.name}: {e}")
                continue

        # Calcular razão de renda total dos sobreviventes
        total_survivor_income_ratio = sum(
            detail['survivor_income_ratio'] for detail in survivor_details
        )

        # Análise de distribuição
        distribution_analysis = self._analyze_benefit_distribution(
            family, survivor_details
        )

        return {
            'vpa_survivor_benefits': total_vpa,
            'survivor_details': survivor_details,
            'total_survivor_income_ratio': total_survivor_income_ratio,
            'distribution_analysis': distribution_analysis
        }

    def _calculate_single_member_pension(
        self,
        participant_age: int,
        participant_gender: str,
        participant_mortality_table: str,
        participant_survival_probs: np.ndarray,
        member: FamilyMember,
        benefit_amount: float,
        discount_rate: float,
        projection_years: int,
        timing: str,
        benefit_months_per_year: int,
        mortality_aggravation: float,
        family_config: FamilyComposition
    ) -> Dict[str, Any]:
        """Calcula pensão para um único dependente"""

        # 1. Determinar idade do dependente
        dependent_age = self._get_dependent_age(member, participant_age)

        # 2. Determinar gênero (inferir se necessário)
        dependent_gender = member.gender or self._infer_gender(member.dependent_type)

        # 3. Obter tábua de mortalidade do dependente
        dependent_mortality_table = member.mortality_table or participant_mortality_table
        dependent_table_data, _ = get_mortality_table(
            dependent_mortality_table,
            dependent_gender,
            mortality_aggravation
        )

        # 4. Calcular probabilidades de sobrevivência do dependente
        dependent_survival_probs = self._calculate_dependent_survival(
            dependent_age,
            dependent_table_data,
            projection_years,
            member.eligible_until_age
        )

        # 5. Determinar percentual de benefício
        survivor_percentage = self._calculate_member_benefit_percentage(
            member, family_config
        )

        # 6. Calcular VPA de pensão
        pension_result = calculate_survivor_benefit_stream(
            benefit_amount=benefit_amount,
            survival_probs_participant=participant_survival_probs,
            survival_probs_dependent=dependent_survival_probs,
            survivor_percentage=survivor_percentage,
            discount_rate=discount_rate,
            timing=timing,
            benefit_months_per_year=benefit_months_per_year
        )

        # 7. Compilar resultado
        return {
            'member_id': member.id,
            'member_name': member.name,
            'dependent_type': member.dependent_type.value,
            'age': dependent_age,
            'gender': dependent_gender,
            'vpa': pension_result['vpa_survivor_benefits'],
            'survivor_percentage': survivor_percentage,
            'survivor_income_ratio': survivor_percentage / 100,
            'cash_flows': pension_result['survivor_cash_flows'].tolist(),
            'survivor_only_probs': pension_result['survivor_only_probs'].tolist(),
            'eligible_until_age': member.eligible_until_age,
            'is_disabled': member.is_disabled,
            'priority_class': member.priority_class
        }

    def calculate_inheritance_analysis(
        self,
        family: FamilyComposition,
        initial_balance: float,
        projected_balances: np.ndarray,
        participant_survival_probs: np.ndarray,
        participant_age: int,
        projection_years: int
    ) -> Dict[str, Any]:
        """
        Calcula análise completa de herança para CD

        Retorna valor da função de heritor por idade para cada dependente
        """
        if not family or not family.members:
            return {
                'inheritance_rule': 'NO_HEIRS',
                'expected_inheritance_value': initial_balance,
                'inheritance_by_member': []
            }

        # Calcular valor base de herança por idade
        inheritance_base = calculate_inheritance_value_by_age(
            initial_balance=initial_balance,
            projected_balances=projected_balances,
            survival_probs_participant=participant_survival_probs,
            participant_age=participant_age,
            projection_years=projection_years
        )

        # Distribuir entre membros conforme regra
        inheritance_by_member = []

        for member in family.members:
            # Calcular share do membro
            member_share = self._calculate_inheritance_share(
                member, family
            )

            # Aplicar share ao valor de herança por idade
            member_inheritance_by_age = [
                value * member_share
                for value in inheritance_base['inheritance_by_age']
            ]

            inheritance_by_member.append({
                'member_id': member.id,
                'member_name': member.name,
                'share_percentage': member_share * 100,
                'inheritance_value_by_age': member_inheritance_by_age,
                'expected_value': sum(member_inheritance_by_age)
            })

        return {
            'inheritance_rule': family.inheritance_rule.value,
            'ages': inheritance_base['ages'],
            'death_probability': inheritance_base['death_probability'],
            'expected_inheritance_value': inheritance_base['expected_inheritance_value'],
            'inheritance_by_member': inheritance_by_member
        }

    # === MÉTODOS AUXILIARES ===

    def _get_dependent_age(self, member: FamilyMember, participant_age: int) -> int:
        """Determina idade do dependente"""
        if member.age is not None:
            return member.age

        if member.age_differential is not None:
            return max(0, participant_age + member.age_differential)

        # Defaults por tipo
        defaults = {
            DependentType.SPOUSE: participant_age - 2,  # Cônjuge 2 anos mais novo
            DependentType.CHILD: max(0, participant_age - 30),  # Filho: pai tinha 30
            DependentType.PARENT: participant_age + 30,  # Pai: 30 anos mais velho
            DependentType.EX_SPOUSE: participant_age,
            DependentType.OTHER: participant_age
        }

        return max(0, defaults.get(member.dependent_type, participant_age))

    def _infer_gender(self, dependent_type: DependentType) -> str:
        """Infere gênero baseado no tipo (fallback)"""
        # Por padrão, usar distribuição 50/50 ou mais comum
        return "F"  # Simplificação: pode ser refinado

    def _calculate_dependent_survival(
        self,
        initial_age: int,
        mortality_table: np.ndarray,
        projection_years: int,
        eligible_until_age: Optional[int]
    ) -> np.ndarray:
        """
        Calcula probabilidades de sobrevivência do dependente
        considerando idade limite de elegibilidade
        """
        survival_probs = []
        cumulative_survival = 1.0

        for year in range(projection_years + 1):
            age = initial_age + year

            # Verificar elegibilidade
            if eligible_until_age and age >= eligible_until_age:
                survival_probs.append(0.0)  # Perde elegibilidade
                continue

            # Probabilidade de mortalidade nesta idade
            if age < len(mortality_table):
                q_x = mortality_table[age]
            else:
                q_x = 1.0  # Certeza de morte se exceder tábua

            # Atualizar sobrevivência cumulativa
            cumulative_survival *= (1 - q_x)
            survival_probs.append(cumulative_survival)

        return np.array(survival_probs)

    def _calculate_member_benefit_percentage(
        self,
        member: FamilyMember,
        family_config: FamilyComposition
    ) -> float:
        """Calcula percentual de benefício para o membro"""

        if family_config.benefit_share_type == BenefitShareType.PROPORTIONAL:
            # Usa percentual configurado do membro
            return member.benefit_share_percentage * (family_config.survivor_benefit_percentage / 100)

        elif family_config.benefit_share_type == BenefitShareType.EQUAL_QUOTA:
            # Divide igualmente entre membros elegíveis
            eligible_count = len([m for m in family_config.members if m.economic_dependency])
            share = family_config.survivor_benefit_percentage / eligible_count if eligible_count > 0 else 0
            return share

        elif family_config.benefit_share_type == BenefitShareType.TOTAL_REVERSION:
            # Um único beneficiário recebe tudo
            return family_config.survivor_benefit_percentage

        elif family_config.benefit_share_type == BenefitShareType.PRIORITY_CLASS:
            # Implementar lógica de prioridades (Lei 8.213/91)
            return self._calculate_priority_based_percentage(member, family_config)

        return member.benefit_share_percentage

    def _calculate_priority_based_percentage(
        self,
        member: FamilyMember,
        family_config: FamilyComposition
    ) -> float:
        """
        Calcula distribuição baseada em classes de prioridade

        Classe 1: Cônjuge + filhos menores (dividem igualmente)
        Classe 2: Pais (se não houver classe 1)
        Classe 3: Outros
        """
        members_by_class = {}
        for m in family_config.members:
            if m.priority_class not in members_by_class:
                members_by_class[m.priority_class] = []
            members_by_class[m.priority_class].append(m)

        # Encontrar classe de maior prioridade (menor número)
        highest_priority = min(members_by_class.keys())

        # Se membro não está na classe de maior prioridade, recebe 0
        if member.priority_class > highest_priority:
            return 0.0

        # Dividir entre membros da mesma classe
        same_class_count = len(members_by_class[highest_priority])
        return family_config.survivor_benefit_percentage / same_class_count

    def _calculate_inheritance_share(
        self,
        member: FamilyMember,
        family_config: FamilyComposition
    ) -> float:
        """Calcula share de herança para CD"""

        if family_config.inheritance_rule == InheritanceRule.PROPORTIONAL_SPLIT:
            # Usar percentual do membro
            total_percentage = sum(m.benefit_share_percentage for m in family_config.members)
            return member.benefit_share_percentage / total_percentage if total_percentage > 0 else 0

        else:
            # Divisão igualitária por padrão
            return 1.0 / len(family_config.members)

    def _analyze_benefit_distribution(
        self,
        family: FamilyComposition,
        survivor_details: List[Dict]
    ) -> Dict[str, Any]:
        """Analisa distribuição de benefícios entre dependentes"""

        total_vpa = sum(d['vpa'] for d in survivor_details)

        distribution = {
            'distribution_type': family.benefit_share_type.value,
            'total_members': len(family.members),
            'eligible_members': len(survivor_details),
            'total_vpa': total_vpa,
            'by_type': {},
            'by_priority_class': {}
        }

        # Agrupar por tipo de dependente
        for detail in survivor_details:
            dep_type = detail['dependent_type']
            if dep_type not in distribution['by_type']:
                distribution['by_type'][dep_type] = {
                    'count': 0,
                    'total_vpa': 0,
                    'average_percentage': 0
                }

            distribution['by_type'][dep_type]['count'] += 1
            distribution['by_type'][dep_type]['total_vpa'] += detail['vpa']
            distribution['by_type'][dep_type]['average_percentage'] += detail['survivor_percentage']

        # Calcular médias
        for dep_type in distribution['by_type']:
            count = distribution['by_type'][dep_type]['count']
            if count > 0:
                distribution['by_type'][dep_type]['average_percentage'] /= count

        return distribution
