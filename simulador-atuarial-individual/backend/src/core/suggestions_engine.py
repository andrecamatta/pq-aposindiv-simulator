import time
import uuid
from typing import List, Dict, Any
# Usando funções centralizadas de root finding do módulo VPA (fsolve + fallbacks)

from ..models import SimulatorState, SimulatorResults
from ..models.participant import PlanType, CDConversionMode, BenefitTargetMode
from ..models.suggestions import (
    Suggestion, SuggestionType, SuggestionAction, 
    SuggestionsRequest, SuggestionsResponse
)
from .actuarial_engine import ActuarialEngine
from ..utils.formatters import format_currency_safe, format_currency_inline, format_currency_br, apply_br_number_format
from ..utils.pydantic_validators import get_enum_value


class SuggestionsEngine:
    """Engine para gerar sugestões inteligentes contextuais"""

    def __init__(self, actuarial_engine: 'ActuarialEngine' = None):
        from .actuarial_engine import ActuarialEngine
        self.actuarial_engine = actuarial_engine or ActuarialEngine()

    
    def generate_suggestions(self, request: SuggestionsRequest) -> SuggestionsResponse:
        """Gera sugestões contextuais baseadas no estado atual"""
        start_time = time.time()
        
        state = request.state
        plan_type_value = state.plan_type.value if hasattr(state.plan_type, 'value') else str(state.plan_type)
        mode_value = state.benefit_target_mode.value if hasattr(state.benefit_target_mode, 'value') else str(state.benefit_target_mode)
        is_bd_supported = plan_type_value == "BD" and mode_value in ["VALUE", "REPLACEMENT_RATE"]

        if not is_bd_supported:
            computation_time = (time.time() - start_time) * 1000
            return SuggestionsResponse(
                suggestions=[],
                context={
                    "plan_type": plan_type_value,
                    "benefit_target_mode": mode_value,
                    "is_bd_supported": False,
                    "unsupported_reason": "Sugestões inteligentes estão disponíveis para planos BD com Valor Fixo ou Taxa de Reposição."
                },
                computation_time_ms=computation_time
            )

        # Executar simulação atual para análise (somente planos BD/Valor)
        current_results = self.actuarial_engine.calculate_individual_simulation(state)

        # Gerar contexto detalhado antes de decidir sobre sugestões
        suggestions: List[Suggestion] = []
        context = self._build_context(state, current_results)
        context["is_bd_value"] = True

        deficit = current_results.deficit_surplus

        # Ajustar contribuição quando há déficit relevante
        if deficit < -500:
            balance_suggestion = self._suggest_balance_plan(state, current_results)
            if balance_suggestion:
                suggestions.append(balance_suggestion)

        # Benefício/Taxa sustentável - chamar função apropriada baseada no modo
        # IMPORTANTE: Cada modo só deve gerar sugestões compatíveis
        if mode_value == "VALUE":
            # BD + Valor Fixo: APENAS sugerir benefício sustentável em R$
            sustainable_suggestion = self._suggest_sustainable_benefit(state, current_results)
            if sustainable_suggestion:
                suggestions.append(sustainable_suggestion)
                context["suggested_sustainable_benefit"] = sustainable_suggestion.action_value
                context["suggested_sustainable_confidence"] = sustainable_suggestion.confidence
        elif mode_value == "REPLACEMENT_RATE":
            # BD + Taxa de Reposição: APENAS sugerir taxa de reposição sustentável em %
            sustainable_suggestion = self._suggest_sustainable_replacement_rate(state, current_results)
            if sustainable_suggestion:
                suggestions.append(sustainable_suggestion)
                context["suggested_sustainable_replacement_rate"] = sustainable_suggestion.action_value
                context["suggested_sustainable_confidence"] = sustainable_suggestion.confidence

        # Superávit elevado: considerar aumento de benefício
        if deficit > 5000:
            benefit_suggestion = self._suggest_improve_benefit(state, current_results)
            if benefit_suggestion:
                suggestions.append(benefit_suggestion)

        # Janela para recomendar ajustes na idade de aposentadoria quando aplicável
        retirement_suggestion = self._suggest_optimize_retirement(state, current_results)
        if retirement_suggestion:
            suggestions.append(retirement_suggestion)

        # Em cenários de déficit, ofertar opções de trade-off adicionais
        if deficit < -200 and len(suggestions) < request.max_suggestions:
            tradeoff_suggestions = self._suggest_balance_tradeoffs(state, current_results, suggestions)
            existing_ids = {s.id for s in suggestions}
            for suggestion in tradeoff_suggestions:
                if suggestion.id in existing_ids:
                    continue
                suggestions.append(suggestion)
                existing_ids.add(suggestion.id)
                if len(suggestions) >= request.max_suggestions:
                    break

        # Ordenar por prioridade (e confiança como desempate) e limitar a no máximo 3 sugestões
        suggestions.sort(key=lambda x: (x.priority, -x.confidence))
        max_items = min(request.max_suggestions, 3)
        suggestions = suggestions[:max_items]
        
        computation_time = (time.time() - start_time) * 1000
        
        return SuggestionsResponse(
            suggestions=suggestions,
            context=context,
            computation_time_ms=computation_time
        )
    
    def _build_context(self, state: SimulatorState, results: SimulatorResults) -> Dict[str, Any]:
        """Constrói contexto rico para as sugestões usando dados atuariais"""
        context = {
            "current_deficit_surplus": results.deficit_surplus,
            "current_replacement_ratio": results.replacement_ratio,
            "sustainable_replacement_ratio": results.sustainable_replacement_ratio,
            "years_to_retirement": state.retirement_age - state.age,
            "current_contribution_rate": state.contribution_rate,
            "current_benefit": state.target_benefit or 0,
            "current_retirement_age": state.retirement_age,
            "plan_type": str(state.plan_type),
            "benefit_target_mode": str(state.benefit_target_mode)
        }

        required_rate = getattr(results, 'required_contribution_rate', None)
        context["required_contribution_rate"] = required_rate
        context["current_accrual_rate"] = getattr(state, 'accrual_rate', None)

        salary_months = getattr(state, 'salary_months_per_year', 12) or 12
        annual_salary = state.salary * salary_months
        context["annual_payroll_estimate"] = annual_salary

        if annual_salary:
            context["deficit_ratio_to_payroll"] = results.deficit_surplus / annual_salary

        if required_rate is not None:
            context["required_contribution_gap"] = required_rate - (state.contribution_rate or 0)
        
        # Adicionar dados atuariais se disponíveis
        if hasattr(results, 'vpa_benefits'):
            context["vpa_benefits"] = results.vpa_benefits
            context["vpa_contributions"] = results.vpa_contributions
            context["rmba"] = results.rmba
            
        # Adicionar análise de sensibilidade se disponível
        if hasattr(results, 'sensitivity_discount_rate'):
            context["sensitivity_data"] = {
                "discount_rate": getattr(results, 'sensitivity_discount_rate', {}),
                "mortality": getattr(results, 'sensitivity_mortality', {}),
                "retirement_age": getattr(results, 'sensitivity_retirement_age', {}),
                "salary_growth": getattr(results, 'sensitivity_salary_growth', {})
            }
            
        # Flags de situação para sugestões inteligentes
        deficit_abs = abs(results.deficit_surplus)
        context["flags"] = {
            "has_significant_deficit": deficit_abs > 5000,
            "has_moderate_deficit": 1000 < deficit_abs <= 5000,
            "is_young_participant": state.age < 40,
            "is_close_to_retirement": (state.retirement_age - state.age) < 10,
            "high_replacement_ratio": results.replacement_ratio > 80,
            "low_replacement_ratio": results.replacement_ratio < 50,
            "severe_deficit_vs_payroll": bool(annual_salary) and (abs(results.deficit_surplus) / annual_salary) >= 0.05
        }

        return context
    
    def _suggest_balance_plan(self, state: SimulatorState, results: SimulatorResults) -> Suggestion:
        """Sugere como balancear o plano (déficit zero)"""
        try:
            if results.deficit_surplus >= -500:
                return None

            current_rate = state.contribution_rate or 0.0
            required_rate = getattr(results, 'required_contribution_rate', None)

            from .calculations.vpa_calculations import calculate_optimal_contribution_rate

            optimal_rate = calculate_optimal_contribution_rate(state, self.actuarial_engine)
            candidate_rate = optimal_rate

            if required_rate is not None and required_rate > 0:
                candidate_rate = max(candidate_rate, required_rate)

            candidate_rate = min(candidate_rate, 30.0)
            candidate_rate = round(candidate_rate, 2)

            delta_rate = candidate_rate - current_rate
            if delta_rate < 0.25:
                return None

            deficit_text = format_currency_safe(abs(results.deficit_surplus))
            candidate_label = f"{candidate_rate:.2f}".replace('.', ',')
            delta_label = f"{delta_rate:.2f}".replace('.', ',')
            current_label = f"{current_rate:.2f}".replace('.', ',')

            return Suggestion(
                id=str(uuid.uuid4()),
                type=SuggestionType.BALANCE_PLAN,
                title="Reforçar contribuição para zerar déficit",
                description=(
                    f"Elevar a taxa de contribuição para {candidate_label}% reduz o déficit para próximo de zero."
                ),
                action=SuggestionAction.UPDATE_CONTRIBUTION_RATE,
                action_value=candidate_rate,
                action_label=f"Aplicar {candidate_label}%",
                priority=1,
                impact_description=f"{candidate_label}%",
                confidence=0.92,
                trade_off_info=f"Aumento de {delta_label} p.p. preserva o benefício contratado"
            )
        except Exception:
            pass
        return None
    
    def _suggest_improve_benefit(self, state: SimulatorState, results: SimulatorResults) -> Suggestion:
        """Sugere como usar superávit para melhorar benefício usando análise de sensibilidade"""
        try:
            superavit = results.deficit_surplus
            
            # Usar dados atuariais mais precisos se disponíveis
            if hasattr(results, 'sensitivity_discount_rate') and results.sensitivity_discount_rate:
                # Calcular usando análise de sensibilidade e VPAs
                current_benefit = state.target_benefit or 0
                
                # Estimar aumento usando VPA dos benefícios (mais preciso)
                # Superávit pode sustentar X de benefício adicional baseado no VPA
                additional_monthly = superavit / 240  # Estimativa baseada em 20 anos de aposentadoria
                
                # Validar com simulação
                test_benefit = current_benefit + additional_monthly
                modified_state = state.model_copy()
                modified_state.target_benefit = test_benefit
                test_results = self.actuarial_engine.calculate_individual_simulation(modified_state)
                
                # Se ainda há superávit, a sugestão é válida
                if test_results.deficit_surplus > 0 and additional_monthly > 100:
                    return Suggestion(
                        id=str(uuid.uuid4()),
                        type=SuggestionType.IMPROVE_BENEFIT,
                        title="Otimizar Benefício com Superávit",
                        description=f"Baseado em análise atuarial, você pode aumentar seu benefício",
                        action=SuggestionAction.UPDATE_TARGET_BENEFIT,
                        action_value=test_benefit,
                        action_label=f"Aplicar {format_currency_inline(test_benefit)}",
                        priority=2,
                        impact_description=f"{format_currency_inline(test_benefit)}",
                        confidence=0.9,  # Mais confiança por usar dados atuariais
                        trade_off_info=f"Aumento de {apply_br_number_format(f'R$ {additional_monthly:,.2f}')}/mês mantém equilíbrio atuarial"
                    )
            else:
                # Fallback para método anterior se dados atuariais não estão disponíveis
                years_retirement = max(20, 85 - state.retirement_age)
                annual_factor = years_retirement * 12 * 0.8
                additional_benefit = superavit / annual_factor
                
                if additional_benefit > 100:
                    current_benefit = state.target_benefit or 0
                    new_benefit = current_benefit + additional_benefit
                    
                    return Suggestion(
                        id=str(uuid.uuid4()),
                        type=SuggestionType.IMPROVE_BENEFIT,
                        title="Aumentar Benefício",
                        description=f"Com superávit de {apply_br_number_format(f'R$ {superavit:,.2f}')}, você pode ter mais",
                        action=SuggestionAction.UPDATE_TARGET_BENEFIT,
                        action_value=new_benefit,
                        action_label=f"Aplicar {format_currency_inline(new_benefit)}",
                        priority=2,
                        impact_description=f"{format_currency_inline(new_benefit)}",
                        confidence=0.75
                    )
        except:
            pass
        return None
    
    def _suggest_optimize_retirement(self, state: SimulatorState, results: SimulatorResults) -> Suggestion:
        """Sugere otimização da idade de aposentadoria"""
        try:
            # Se pessoa é jovem, sugerir aposentar mais cedo mantendo mesmo benefício
            if state.age < 35 and state.retirement_age > 62:
                # Testar aposentadoria 2-3 anos mais cedo
                for earlier_age in [state.retirement_age - 2, state.retirement_age - 3]:
                    if earlier_age >= 60:
                        modified_state = state.model_copy()
                        modified_state.retirement_age = earlier_age
                        modified_results = self.actuarial_engine.calculate_individual_simulation(modified_state)
                        
                        # Se déficit não aumenta muito, vale a pena
                        if modified_results.deficit_surplus > -10000:  # Déficit tolerável
                            return Suggestion(
                                id=str(uuid.uuid4()),
                                type=SuggestionType.OPTIMIZE_RETIREMENT,
                                title="Aposentar Mais Cedo",
                                description=f"Você pode se aposentar {state.retirement_age - earlier_age} anos mais cedo",
                                action=SuggestionAction.UPDATE_RETIREMENT_AGE,
                                action_value=float(earlier_age),
                                action_label=f"Aplicar {earlier_age} anos",
                                priority=3,
                                impact_description=f"{earlier_age} anos",
                                confidence=0.7
                            )
        except:
            pass
        return None
    
    def _suggest_sustainable_benefit(self, state: SimulatorState, results: SimulatorResults) -> Suggestion:
        """Sugere benefício sustentável usando root finding com ActuarialEngine - apenas para BD + VALUE"""
        # Filtrar por modo: benefício sustentável só aparece para BD + VALUE
        mode_value = state.benefit_target_mode.value if hasattr(state.benefit_target_mode, 'value') else str(state.benefit_target_mode)
        if mode_value != "VALUE":
            return None

        # Relaxar restrições - permitir para todos os tipos de plano
        # Comentando validações restritivas para melhorar disponibilidade das sugestões
        # if state.plan_type == PlanType.CD:
        #     # Para CD, só permitir se modalidade suporta cálculo atuarial
        #     if state.cd_conversion_mode in [CDConversionMode.PERCENTAGE, CDConversionMode.PROGRAMMED]:
        #         return None
            
        try:
            from ..core.calculations.vpa_calculations import calculate_sustainable_benefit_with_engine
            import logging
            
            logger = logging.getLogger(__name__)
            logger.info(f"[SUGESTÕES] Calculando benefício sustentável para déficit: {format_currency_safe(results.deficit_surplus)}")
            logger.debug(f"[SUGESTÕES] Estado atual - Benefício: {format_currency_safe(state.target_benefit, 'Não definido')}, Modo: {state.benefit_target_mode}")
            
            # Calcular benefício sustentável usando fsolve
            sustainable_benefit = calculate_sustainable_benefit_with_engine(
                state, 
                self.actuarial_engine
            )
            
            logger.info(f"[SUGESTÕES] Benefício sustentável calculado: R$ {sustainable_benefit:.2f}")
            
            # VALIDAÇÃO CRÍTICA: Verificar se sustainable_benefit é válido
            import math
            if math.isnan(sustainable_benefit) or math.isinf(sustainable_benefit) or sustainable_benefit <= 0:
                logger.error(f"[SUGESTÕES] Benefício sustentável inválido: {sustainable_benefit}")
                return None
                
            # VALIDAÇÃO CRÍTICA: Verificar se o benefício realmente zera o déficit
            validation_state = state.model_copy()
            # Comparação robusta do modo de benefício (suporta Enum ou string)
            mode_value = str(state.benefit_target_mode)
            if mode_value == "REPLACEMENT_RATE":
                # Se estamos em modo taxa de reposição, validar usando a mesma taxa que será aplicada
                years_to_retirement = state.retirement_age - state.age
                salary_at_retirement = state.salary * ((1 + state.salary_growth_real) ** years_to_retirement)
                sustainable_ratio = (sustainable_benefit / salary_at_retirement) * 100
                
                # Validar que a taxa calculada também é válida
                if math.isnan(sustainable_ratio) or math.isinf(sustainable_ratio):
                    logger.warning(f"[SUGESTÕES] Taxa de reposição inválida: {sustainable_ratio}%")
                    return None
                    
                validation_state.target_replacement_rate = sustainable_ratio
                validation_state.benefit_target_mode = BenefitTargetMode.REPLACEMENT_RATE
            else:
                # Modo VALUE - validar com o benefício direto
                validation_state.target_benefit = sustainable_benefit
                validation_state.benefit_target_mode = BenefitTargetMode.VALUE
            
            try:
                validation_results = self.actuarial_engine.calculate_individual_simulation(validation_state)
                actual_deficit = validation_results.deficit_surplus
                
                # Tolerância muito mais rigorosa para garantir precisão
                original_deficit_abs = abs(results.deficit_surplus)
                if original_deficit_abs > 100000:  # Déficits grandes (>100k)
                    tolerance = min(original_deficit_abs * 0.01, 1000)  # 1% do déficit, max R$ 1k
                else:
                    tolerance = min(max(original_deficit_abs * 0.005, 100), 500)  # 0.5% do déficit, min R$ 100, max R$ 500
                
                logger.info(f"[SUGESTÕES] Validação - Déficit original: R$ {results.deficit_surplus:.2f}")
                logger.info(f"[SUGESTÕES] Validação - Déficit residual: R$ {actual_deficit:.2f}")
                logger.info(f"[SUGESTÕES] Validação - Tolerância aplicada: R$ {tolerance:.2f}")
                
                # Se o déficit não foi zerado adequadamente (tolerância rigorosa), rejeitar sugestão
                if abs(actual_deficit) > tolerance:
                    logger.warning(f"[SUGESTÕES] Benefício sustentável não zerou déficit adequadamente: R$ {actual_deficit:.2f} (tolerância: R$ {tolerance:.2f})")
                    
                    # Implementar validação dupla: tentar refinamento adicional se falha inicial
                    logger.debug(f"[SUGESTÕES] Tentando refinamento adicional do benefício sustentável")
                    try:
                        # Ajustar benefício baseado no déficit residual
                        adjustment_factor = actual_deficit / results.deficit_surplus if results.deficit_surplus != 0 else 0
                        refined_benefit = sustainable_benefit * (1 - adjustment_factor * 0.1)  # Ajuste de 10% do fator
                        
                        # Re-validar com benefício refinado
                        refined_state = state.model_copy()
                        if mode_value == "REPLACEMENT_RATE":
                            years_to_retirement = state.retirement_age - state.age
                            salary_at_retirement = state.salary * ((1 + state.salary_growth_real) ** years_to_retirement)
                            refined_ratio = (refined_benefit / salary_at_retirement) * 100
                            refined_state.target_replacement_rate = refined_ratio
                            refined_state.benefit_target_mode = BenefitTargetMode.REPLACEMENT_RATE
                        else:
                            refined_state.target_benefit = refined_benefit
                            refined_state.benefit_target_mode = BenefitTargetMode.VALUE
                        
                        refined_results = self.actuarial_engine.calculate_individual_simulation(refined_state)
                        refined_deficit = refined_results.deficit_surplus
                        
                        if abs(refined_deficit) <= tolerance:
                            logger.info(f"[SUGESTÕES] ✅ Refinamento bem-sucedido: déficit refinado R$ {refined_deficit:.2f}")
                            sustainable_benefit = refined_benefit
                            actual_deficit = refined_deficit
                        else:
                            logger.error(f"[SUGESTÕES] ❌ Refinamento falhou: déficit refinado R$ {refined_deficit:.2f}")
                            return None
                    except Exception as refinement_error:
                        logger.error(f"[SUGESTÕES] Erro no refinamento: {refinement_error}")
                        return None
                    
            except Exception as validation_error:
                import traceback
                logger.error(f"[SUGESTÕES] Erro na validação do benefício sustentável: {validation_error}")
                logger.error(f"[SUGESTÕES] Traceback detalhado: {traceback.format_exc()}")
                return None
            
            # Construir sugestão no formato coerente com o modo atual
            # CRITICAL: Garantir consistência na comparação do modo
            mode_value_str = state.benefit_target_mode.value if hasattr(state.benefit_target_mode, 'value') else str(state.benefit_target_mode)
            if mode_value_str == "VALUE":
                current_benefit = state.target_benefit or 0
                if abs(sustainable_benefit - current_benefit) > 50:  # Diferença significativa (relaxado)
                    deficit_info = "com déficit" if results.deficit_surplus < 0 else "com superávit"
                    
                    logger.info(f"[SUGESTÕES] ✅ Sugestão de benefício sustentável criada com sucesso")
                    return Suggestion(
                        id=str(uuid.uuid4()),
                        type=SuggestionType.SUSTAINABLE_BENEFIT,
                        title="Benefício Sustentável",
                        description=f"Valor calculado para zerar o déficit/superávit usando métodos atuariais avançados",
                        action=SuggestionAction.APPLY_SUSTAINABLE_BENEFIT,
                        action_value=sustainable_benefit,
                        action_label=f"Aplicar {format_currency_inline(sustainable_benefit)}",
                        priority=1,
                        impact_description=f"{format_currency_inline(sustainable_benefit)}",
                        confidence=0.98,  # Confiança aumentada devido às validações rigorosas
                        trade_off_info="Benefício calculado para equilíbrio atuarial perfeito"
                    )
            else:  # REPLACEMENT_RATE mode
                # Para modo taxa de reposição, converter benefício para taxa correta (com salário projetado)
                years_to_retirement = state.retirement_age - state.age
                salary_at_retirement = state.salary * ((1 + state.salary_growth_real) ** years_to_retirement)
                sustainable_ratio = (sustainable_benefit / salary_at_retirement) * 100
                current_ratio = state.target_replacement_rate or 70.0
                
                logger.debug(f"[SUGESTÕES] Taxa sustentável calculada: {sustainable_ratio:.2f}% (atual: {current_ratio:.2f}%)")
                
                if abs(sustainable_ratio - current_ratio) > 1.0:  # Diferença de 1%+ (relaxado ainda mais)
                    return Suggestion(
                        id=str(uuid.uuid4()),
                        type=SuggestionType.SUSTAINABLE_BENEFIT,
                        title="Taxa de Reposição Sustentável",
                        description=f"Taxa calculada para zerar déficit/superávit: {sustainable_ratio:.2f}%".replace('.', ','),
                        action=SuggestionAction.UPDATE_REPLACEMENT_RATE,
                        action_value=sustainable_ratio,
                        action_label=f"Aplicar {sustainable_ratio:.2f}%".replace('.', ','),
                        priority=1,
                        impact_description=f"{sustainable_ratio:.1f}%".replace('.', ','),
                        confidence=0.95,
                        trade_off_info="Esta taxa equilibra perfeitamente contribuições e benefícios"
                    )
        except Exception as e:
            # Log do erro para debug
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"[SUGESTÕES] Erro ao calcular benefício sustentável: {e}")
            logger.error(f"[SUGESTÕES] Traceback completo: {traceback.format_exc()}")
            pass
        return None

    def _suggest_sustainable_replacement_rate(self, state: SimulatorState, results: SimulatorResults) -> Suggestion:
        """Sugere taxa de reposição sustentável para planos BD/REPLACEMENT_RATE"""
        # Validação crítica: só funciona para modo REPLACEMENT_RATE
        mode_value = state.benefit_target_mode.value if hasattr(state.benefit_target_mode, 'value') else str(state.benefit_target_mode)
        if mode_value != "REPLACEMENT_RATE":
            return None

        try:
            from ..core.calculations.vpa_calculations import calculate_sustainable_benefit_with_engine
            import logging
            import math
            import uuid

            logger = logging.getLogger(__name__)
            logger.info(f"[SUGESTÕES] Calculando taxa de reposição sustentável para déficit: {format_currency_safe(results.deficit_surplus)}")
            logger.debug(f"[SUGESTÕES] Estado atual - Taxa: {state.target_replacement_rate}%, Modo: {state.benefit_target_mode}")

            # Calcular benefício sustentável em valor absoluto primeiro
            sustainable_benefit = calculate_sustainable_benefit_with_engine(
                state,
                self.actuarial_engine
            )

            logger.info(f"[SUGESTÕES] Benefício sustentável base calculado: R$ {sustainable_benefit:.2f}")

            # Validar se o benefício é válido
            if math.isnan(sustainable_benefit) or math.isinf(sustainable_benefit) or sustainable_benefit <= 0:
                logger.error(f"[SUGESTÕES] Benefício sustentável inválido: {sustainable_benefit}")
                return None

            # Converter para taxa de reposição sustentável
            years_to_retirement = state.retirement_age - state.age
            salary_at_retirement = state.salary * ((1 + state.salary_growth_real) ** years_to_retirement)
            sustainable_ratio = (sustainable_benefit / salary_at_retirement) * 100

            logger.info(f"[SUGESTÕES] Taxa de reposição sustentável calculada: {sustainable_ratio:.2f}%")

            # Validar taxa calculada
            if math.isnan(sustainable_ratio) or math.isinf(sustainable_ratio) or sustainable_ratio <= 0:
                logger.warning(f"[SUGESTÕES] Taxa de reposição sustentável inválida: {sustainable_ratio}%")
                return None

            # Validar se realmente zera o déficit
            validation_state = state.model_copy()
            validation_state.target_replacement_rate = sustainable_ratio
            validation_state.benefit_target_mode = BenefitTargetMode.REPLACEMENT_RATE

            try:
                validation_results = self.actuarial_engine.calculate_individual_simulation(validation_state)
                actual_deficit = validation_results.deficit_surplus

                # Tolerância para validação
                original_deficit_abs = abs(results.deficit_surplus)
                tolerance = max(original_deficit_abs * 0.05, 500)  # 5% do déficit ou R$ 500

                if abs(actual_deficit) > tolerance:
                    logger.warning(f"[SUGESTÕES] Taxa sustentável não zerou déficit adequadamente: R$ {actual_deficit:.2f} (tolerância: R$ {tolerance:.2f})")
                    return None

            except Exception as validation_error:
                logger.error(f"[SUGESTÕES] Erro na validação da taxa sustentável: {validation_error}")
                return None

            # Verificar se há diferença significativa da taxa atual
            current_ratio = state.target_replacement_rate or 70.0
            if abs(sustainable_ratio - current_ratio) < 2.0:  # Diferença mínima de 2%
                logger.debug(f"[SUGESTÕES] Diferença insuficiente entre taxas: atual {current_ratio:.2f}% vs sustentável {sustainable_ratio:.2f}%")
                return None

            # Construir sugestão de taxa de reposição
            deficit_info = "com déficit" if results.deficit_surplus < 0 else "com superávit"

            logger.info(f"[SUGESTÕES] ✅ Sugestão de taxa de reposição sustentável criada com sucesso")
            return Suggestion(
                id=str(uuid.uuid4()),
                type=SuggestionType.SUSTAINABLE_BENEFIT,
                title="Taxa de Reposição Sustentável",
                description=f"Taxa calculada para zerar o déficit/superávit usando métodos atuariais avançados",
                action=SuggestionAction.APPLY_SUSTAINABLE_REPLACEMENT_RATE,
                action_value=sustainable_ratio,
                action_label=f"Aplicar {sustainable_ratio:.1f}%".replace('.', ','),
                priority=1,
                impact_description=f"{sustainable_ratio:.1f}%".replace('.', ','),
                confidence=0.95,
                trade_off_info="Taxa calculada para equilíbrio atuarial perfeito"
            )

        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"[SUGESTÕES] Erro ao calcular taxa de reposição sustentável: {e}")
            logger.error(f"[SUGESTÕES] Traceback completo: {traceback.format_exc()}")
            pass
        return None

    def _suggest_balance_tradeoffs(self, state: SimulatorState, results: SimulatorResults, existing_suggestions: List[Suggestion] = None) -> List[Suggestion]:
        """Sugere múltiplas opções para balancear o plano (trade-offs)"""
        suggestions = []
        existing_suggestions = existing_suggestions or []
        
        try:
            # Opção 1: Ajustar só contribuição (não adicionar se já existe sugestão similar)
            # Verificar se já não temos uma sugestão de balancear via contribuição
            has_contribution_balance = any(
                s for s in existing_suggestions 
                if s and s.action == SuggestionAction.UPDATE_CONTRIBUTION_RATE
            )
            
            if not has_contribution_balance:
                contribution_option = self._calculate_contribution_to_balance(state, results)
                if contribution_option:
                    suggestions.append(contribution_option)
            
            # Opção 2: Ajustar só idade de aposentadoria
            retirement_option = self._calculate_retirement_age_to_balance(state, results)
            if retirement_option:
                suggestions.append(retirement_option)
                
            # Opção 3: Ajustar só benefício (usar sustentável) - só se ainda não foi sugerido
            # Verificar em TODAS as sugestões existentes, não apenas nas locais
            has_benefit_suggestion = any(
                s for s in existing_suggestions 
                if s and s.action in [
                    SuggestionAction.APPLY_SUSTAINABLE_BENEFIT, 
                    SuggestionAction.UPDATE_TARGET_BENEFIT,
                    SuggestionAction.UPDATE_REPLACEMENT_RATE  # Evitar duplicação de sugestões de taxa
                ]
            )
            
            if not has_benefit_suggestion:
                benefit_option = self._suggest_sustainable_benefit(state, results)
                if benefit_option:
                    # Modificar para ser trade-off
                    benefit_option.type = SuggestionType.TRADE_OFF_OPTIONS
                    benefit_option.title = "Opção: Ajustar Benefício"
                    benefit_option.priority = 2
                    suggestions.append(benefit_option)
            
            # Opção 4: Combinação ótima (50% contribuição + 50% benefício)
            combo_option = self._calculate_combo_balance(state, results)
            if combo_option:
                suggestions.append(combo_option)
                
        except:
            pass
            
        return suggestions[:3]  # Máximo 3 trade-offs
    
    def _calculate_contribution_to_balance(self, state: SimulatorState, results: SimulatorResults) -> Suggestion:
        """Calcula contribuição necessária para zerar déficit usando fsolve"""
        try:
            from .calculations.vpa_calculations import calculate_optimal_contribution_rate
            
            optimal_rate = calculate_optimal_contribution_rate(state, self.actuarial_engine)
            
            if optimal_rate <= 25:
                increase = optimal_rate - state.contribution_rate
                return Suggestion(
                    id=str(uuid.uuid4()),
                    type=SuggestionType.TRADE_OFF_OPTIONS,
                    title="Opção: Aumentar Contribuição",
                    description=f"Aumentar {increase:.2f} pontos percentuais zera o déficit".replace('.', ','),
                    action=SuggestionAction.UPDATE_CONTRIBUTION_RATE,
                    action_value=optimal_rate,
                    action_label=f"Aplicar {optimal_rate:.2f}%".replace('.', ','),
                    priority=2,
                    impact_description=f"{optimal_rate:.1f}%".replace('.', ','),
                    confidence=0.9,
                    trade_off_info="Vantagem: mantém benefício • Desvantagem: maior custo mensal"
                )
        except:
            pass
        return None
    
    def _calculate_retirement_age_to_balance(self, state: SimulatorState, results: SimulatorResults) -> Suggestion:
        """Calcula idade de aposentadoria necessária para zerar déficit usando fsolve"""
        try:
            from .calculations.vpa_calculations import calculate_optimal_retirement_age
            
            optimal_age = calculate_optimal_retirement_age(state, self.actuarial_engine)
            
            # Garantir que é uma idade válida e razoável
            if 50 <= optimal_age <= 100 and optimal_age > state.age:
                years_later = optimal_age - state.retirement_age
                
                # Só sugerir se não for um aumento muito grande (máximo 10 anos)
                if 0 < years_later <= 10:
                    return Suggestion(
                        id=str(uuid.uuid4()),
                        type=SuggestionType.TRADE_OFF_OPTIONS,
                        title="Opção: Postergar Aposentadoria",
                        description=f"Aposentar {years_later:.0f} ano{'s' if years_later > 1 else ''} mais tarde equilibra o plano",
                        action=SuggestionAction.UPDATE_RETIREMENT_AGE,
                        action_value=float(optimal_age),
                        action_label=f"Aplicar {optimal_age:.0f} anos",
                        priority=2,
                        impact_description=f"{optimal_age:.0f} anos",
                        confidence=0.85,
                        trade_off_info="Vantagem: sem aumento de custos • Desvantagem: aposentadoria mais tardia"
                    )
        except:
            pass
        return None
    
    def _calculate_combo_balance(self, state: SimulatorState, results: SimulatorResults) -> Suggestion:
        """Calcula combinação ótima de ajustes para balancear plano"""
        try:
            # Estratégia: 50% do ajuste via contribuição, 50% via benefício
            deficit = abs(results.deficit_surplus)
            
            # Estimar ajustes necessários (fórmulas simplificadas mas baseadas nos cálculos)
            current_contrib = state.contribution_rate
            current_benefit = state.target_benefit or (state.salary * 0.7)
            
            # Teste: aumentar contribuição pela metade do necessário
            contrib_increase = deficit / (state.salary * 12 * (state.retirement_age - state.age) * 0.5)
            new_contrib = min(current_contrib + contrib_increase, 25.0)
            
            # E reduzir benefício pela metade
            benefit_reduction = deficit / ((state.retirement_age - state.age) * 12 * 0.5)
            new_benefit = max(current_benefit - benefit_reduction, current_benefit * 0.5)
            
            # Validar se funciona
            modified_state = state.model_copy()
            modified_state.contribution_rate = new_contrib
            modified_state.target_benefit = new_benefit
            test_results = self.actuarial_engine.calculate_individual_simulation(modified_state)
            
            if abs(test_results.deficit_surplus) < abs(results.deficit_surplus) * 0.2:  # Melhoria significativa
                return Suggestion(
                    id=str(uuid.uuid4()),
                    type=SuggestionType.TRADE_OFF_OPTIONS,
                    title="Opção: Ajuste Combinado",
                    description="Pequenos ajustes em contribuição E benefício",
                    action=SuggestionAction.UPDATE_MULTIPLE_PARAMS,
                    action_values={
                        "contribution_rate": new_contrib,
                        "target_benefit": new_benefit
                    },
                    action_label=f"Aplicar combo",
                    priority=1,  # Prioridade alta por ser balanceado
                    impact_description=f"{new_contrib:.1f}% e {format_currency_inline(new_benefit)}".replace('.', ','),
                    confidence=0.8,
                    trade_off_info="Vantagem: impacto moderado em ambos • Solução equilibrada"
                )
        except:
            pass
        return None
