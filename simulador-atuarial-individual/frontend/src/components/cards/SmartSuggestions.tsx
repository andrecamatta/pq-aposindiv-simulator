import React, { useState, useEffect } from 'react';
import { Button } from '../../design-system/components';
import { apiService } from '../../services/api';
import { formatCurrencyBR } from '../../utils/formatBR';
import type {
  SimulatorState,
  Suggestion,
  SimulatorResults,
  SuggestionAction
} from '../../types';

interface SmartSuggestionsProps {
  state: SimulatorState;
  results?: SimulatorResults | null;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading?: boolean;
}

const SmartSuggestions: React.FC<SmartSuggestionsProps> = ({
  state,
  results,
  onStateChange,
  loading = false
}) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [applyingId, setApplyingId] = useState<string | null>(null);
  const [context, setContext] = useState<Record<string, any>>({});
  const [validationWarnings, setValidationWarnings] = useState<Record<string, string>>({});
  const planType = state.plan_type || 'BD';
  const benefitMode = state.benefit_target_mode || 'VALUE';
  const isBDSupported = planType === 'BD' && (benefitMode === 'VALUE' || benefitMode === 'REPLACEMENT_RATE');

  // Função removida - elimina redundância com impact_description

  // Buscar sugestões quando estado mudar
  useEffect(() => {
    if (!loading && state) {
      if (isBDSupported) {
        fetchSuggestions();
      } else {
        setSuggestions([]);
        setContext({
          plan_type: planType,
          benefit_target_mode: benefitMode,
          is_bd_supported: false,
          unsupported_reason: 'Sugestões inteligentes estão disponíveis para planos BD com Valor Fixo ou Taxa de Reposição.'
        });
        setSuggestionsLoading(false);
      }
    }
  }, [
    loading,
    isBDSupported,
    state.plan_type,
    results?.deficit_surplus,
    state.contribution_rate,
    state.retirement_age,
    state.target_benefit,
    state.target_replacement_rate,
    state.benefit_target_mode
  ]);

  const fetchSuggestions = async () => {
    try {
      if (!isBDSupported) {
        return;
      }
      setSuggestionsLoading(true);
      
      const data = await apiService.getSuggestions({
        state: state,
        max_suggestions: 3
      });
      
      setSuggestions(data.suggestions);
      setContext(data.context);
    } catch (error) {
      console.error('Erro ao buscar sugestões:', error);
      setSuggestions([]);

      // Atualizar contexto com informação de erro
      setContext({
        plan_type: planType,
        benefit_target_mode: benefitMode,
        is_bd_supported: isBDSupported,
        error: error instanceof Error ? error.message : 'Erro desconhecido',
        unsupported_reason: 'Erro ao conectar com o servidor de sugestões.'
      });
    } finally {
      setSuggestionsLoading(false);
    }
  };

  // Função para validar se sugestão realmente funcionou
  const validateSuggestionApplication = async (
    newState: SimulatorState,
    originalDeficit: number,
    suggestionId: string
  ): Promise<boolean> => {
    try {
      // Simular com novo estado para verificar se déficit foi realmente zerado
      const results: SimulatorResults = await apiService.calculate(newState);
      const newDeficit = results.deficit_surplus;
      
      // Tolerância para validação (R$ 100)
      const tolerance = 100;
      const deficitReduced = Math.abs(newDeficit) < Math.abs(originalDeficit);
      const deficitZeroed = Math.abs(newDeficit) <= tolerance;
      
      if (!deficitZeroed) {
        const warningMsg = `Sugestão aplicada mas déficit não foi zerado (R$ ${formatCurrencyBR(Math.abs(newDeficit))})`;
        setValidationWarnings(prev => ({
          ...prev,
          [suggestionId]: warningMsg
        }));
        return false;
      }
      
      return true;
    } catch {
      return false; // Se não conseguir validar, assumir que falhou
    }
  };

  const applySuggestion = async (suggestion: Suggestion) => {
    try {
      setApplyingId(suggestion.id);
      
      // Limpar warnings anteriores
      setValidationWarnings(prev => {
        const newWarnings = { ...prev };
        delete newWarnings[suggestion.id];
        return newWarnings;
      });
      
      // Preparar request com suporte para múltiplos valores
      const request: any = {
        state: state,
        action: suggestion.action
      };
      
      // Adicionar valores conforme o tipo de ação
      if (suggestion.action === 'update_multiple_params' && suggestion.action_values) {
        request.action_value = suggestion.action_values;
      } else {
        request.action_value = suggestion.action_value;
      }
      
      const data = await apiService.applySuggestion(request);
      
      // Aplicar as mudanças ao estado
      const updates: Partial<SimulatorState> = {};
      
      switch (suggestion.action) {
        case 'update_contribution_rate':
          updates.contribution_rate = suggestion.action_value;
          break;
        case 'update_retirement_age':
          updates.retirement_age = Math.round(suggestion.action_value!);
          break;
        case 'update_target_benefit':
        case 'apply_sustainable_benefit':
          updates.target_benefit = suggestion.action_value;
          updates.benefit_target_mode = 'VALUE';
          break;
        case 'update_replacement_rate':
        case 'apply_sustainable_replacement_rate':
          updates.target_replacement_rate = suggestion.action_value;
          updates.benefit_target_mode = 'REPLACEMENT_RATE';
          break;
        case 'update_accrual_rate':
          updates.accrual_rate = suggestion.action_value;
          break;
        case 'update_multiple_params':
          if (suggestion.action_values) {
            Object.entries(suggestion.action_values).forEach(([key, value]) => {
              (updates as any)[key] = value;
            });
          }
          break;
      }
      
      // Criar novo estado com as atualizações
      const newState = { ...state, ...updates };
      
      // Aplicar mudanças imediatamente
      onStateChange(updates);
      
      // Validar pós-aplicação para sugestões de benefício sustentável
      if (suggestion.action === 'apply_sustainable_benefit' ||
          suggestion.action === 'apply_sustainable_replacement_rate' ||
          suggestion.action === 'update_replacement_rate' ||
          suggestion.action === 'update_target_benefit') {
        
        const originalDeficit = context.current_deficit_surplus || 0;
        
        // Aguardar um pouco para garantir que o estado foi atualizado
        setTimeout(async () => {
          const validationSuccess = await validateSuggestionApplication(
            newState, 
            originalDeficit, 
            suggestion.id
          );
          
          if (validationSuccess) {
            // Remove warning se existe
            setValidationWarnings(prev => {
              const newWarnings = { ...prev };
              delete newWarnings[suggestion.id];
              return newWarnings;
            });
          }
        }, 500);
      }
      
    } catch (error) {
      // Erro ao aplicar sugestão - melhor diagnóstico
      console.error('Erro detalhado ao aplicar sugestão:', error);
      let errorMessage = 'Erro ao aplicar sugestão';

      if (error instanceof Error) {
        if (error.message.includes('404')) {
          errorMessage = 'Serviço de sugestões indisponível';
        } else if (error.message.includes('422')) {
          errorMessage = 'Dados inválidos para aplicar sugestão';
        } else if (error.message.includes('500')) {
          errorMessage = 'Erro interno do servidor';
        } else {
          errorMessage = error.message;
        }
      }

      setValidationWarnings(prev => ({
        ...prev,
        [suggestion.id]: errorMessage
      }));
    } finally {
      setApplyingId(null);
    }
  };

  // UI minimalista: sem ícones por item e sem indicador de confiança visual

  if (loading) {
    return (
      <div role="region" aria-labelledby="smart-suggestions-title" className="space-y-1">
        <h3 id="smart-suggestions-title" className="text-sm font-semibold text-gray-900">Sugestões Inteligentes</h3>
        <p className="text-sm text-gray-600">Analisando seus dados...</p>
      </div>
    );
  }

  if (!isBDSupported) {
    return (
      <div role="region" aria-labelledby="smart-suggestions-title" className="space-y-1">
        <h3 id="smart-suggestions-title" className="text-sm font-semibold text-gray-900">Sugestões Inteligentes</h3>
        <p className="text-sm text-gray-600">
          {context.unsupported_reason || 'Sugestões estarão disponíveis em breve para esta modalidade.'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3" role="region" aria-labelledby="smart-suggestions-title">
      <h3 id="smart-suggestions-title" className="text-sm font-semibold text-gray-900">Sugestões Inteligentes</h3>

      {suggestionsLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Gerando sugestões...</span>
        </div>
      ) : suggestions.length > 0 ? (
        <div className="space-y-2">
          {/* Contexto atual */}
          {typeof context.current_deficit_surplus === 'number' && (
            <p className="text-xs text-gray-600">
              {context.current_deficit_surplus > 0
                ? `Superávit: ${formatCurrencyBR(Math.abs(context.current_deficit_surplus))}`
                : `Déficit: ${formatCurrencyBR(Math.abs(context.current_deficit_surplus))}`}
            </p>
          )}

          {/* Lista de sugestões (minimalista) */}
          {suggestions.map((suggestion) => (
            <div key={suggestion.id} className="py-1 first:pt-0">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm text-gray-800 truncate">
                  {suggestion.title}
                  {suggestion.impact_description && (
                    <span className="text-gray-500"> — {suggestion.impact_description}</span>
                  )}
                  {validationWarnings[suggestion.id] && (
                    <span className="text-yellow-700"> — {validationWarnings[suggestion.id]}</span>
                  )}
                </p>
                <Button
                  variant="link"
                  size="sm"
                  loading={applyingId === suggestion.id}
                  onClick={() => applySuggestion(suggestion)}
                  aria-label={`Aplicar sugestão: ${suggestion.action_label}`}
                >
                  {applyingId === suggestion.id ? 'Aplicando...' : 'Aplicar'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-2">
          {(() => {
            // Determinar se o plano está realmente equilibrado ou se apenas não há sugestões
            const currentDeficit = context.current_deficit_surplus || 0;
            const isActuallyBalanced = Math.abs(currentDeficit) <= 1000;
            
            if (isActuallyBalanced) {
              // Realmente equilibrado
              return (
                <>
                  <p className="text-sm text-gray-700">Seus parâmetros estão equilibrados.</p>
                </>
              );
            } else {
              // Tem déficit/superávit mas sem sugestões disponíveis
              
              return (
                <>
                  <p className="text-sm text-gray-700">Não há sugestões disponíveis no momento.</p>
                </>
              );
            }
          })()}
        </div>
      )}
    </div>
  );
};

export default SmartSuggestions;
