from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

from .participant import SimulatorState


class SuggestionType(str, Enum):
    """Tipos de sugestão disponíveis"""
    BALANCE_PLAN = "balance_plan"           # Balancear o plano (déficit zero)
    IMPROVE_BENEFIT = "improve_benefit"     # Melhorar benefício
    REDUCE_CONTRIBUTION = "reduce_contribution"  # Reduzir contribuição
    OPTIMIZE_RETIREMENT = "optimize_retirement"  # Otimizar idade aposentadoria
    SUSTAINABLE_BENEFIT = "sustainable_benefit"  # Benefício sustentável
    TRADE_OFF_OPTIONS = "trade_off_options"  # Múltiplas opções para mesmo objetivo
    OPTIMIZE_MULTIPLE = "optimize_multiple"  # Otimização de múltiplos parâmetros


class SuggestionAction(str, Enum):
    """Ações que podem ser aplicadas"""
    UPDATE_CONTRIBUTION_RATE = "update_contribution_rate"
    UPDATE_RETIREMENT_AGE = "update_retirement_age"
    UPDATE_TARGET_BENEFIT = "update_target_benefit"
    UPDATE_ACCRUAL_RATE = "update_accrual_rate"
    UPDATE_REPLACEMENT_RATE = "update_replacement_rate"
    UPDATE_MULTIPLE_PARAMS = "update_multiple_params"  # Para múltiplas mudanças
    APPLY_SUSTAINABLE_BENEFIT = "apply_sustainable_benefit"
    APPLY_SUSTAINABLE_REPLACEMENT_RATE = "apply_sustainable_replacement_rate"
    OPTIMIZE_CD_CONTRIBUTION_RATE = "optimize_cd_contribution_rate"  # Otimizar contribuição CD para meta de renda


class Suggestion(BaseModel):
    """Uma sugestão individual"""
    id: str                                 # ID único da sugestão
    type: SuggestionType
    title: str                             # Título da sugestão
    description: str                       # Descrição detalhada
    action: SuggestionAction               # Ação a ser executada
    action_value: Optional[float] = None   # Valor para aplicar (pode ser None para ações complexas)
    action_values: Optional[Dict[str, float]] = None  # Múltiplos valores para UPDATE_MULTIPLE_PARAMS
    action_label: str                      # Label do botão (ex: "Aplicar 14,2%")
    priority: int                          # Prioridade (1=alta, 3=baixa)
    impact_description: str                # Descrição do impacto
    confidence: float                      # Confiança na sugestão (0-1)
    trade_off_info: Optional[str] = None   # Informação adicional sobre trade-offs


class SuggestionsRequest(BaseModel):
    """Solicitação de sugestões"""
    state: SimulatorState
    max_suggestions: int = 3               # Máximo de sugestões
    focus_area: Optional[str] = None       # Área de foco (opcional)


class SuggestionsResponse(BaseModel):
    """Resposta com sugestões"""
    suggestions: List[Suggestion]
    context: Dict[str, Any]               # Contexto adicional (déficit atual, etc.)
    computation_time_ms: float