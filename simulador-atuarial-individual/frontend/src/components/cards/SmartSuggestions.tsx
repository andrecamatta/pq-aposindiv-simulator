import React, { useState, useEffect } from 'react';
import { Icon } from '../../design-system/components/Icon';
import { apiService } from '../../services/api';
import { formatCurrencyBR, formatPercentageBR } from '../../utils/formatBR';
import type { 
  SimulatorState, 
  Suggestion, 
  SuggestionsResponse,
  ApplySuggestionResponse
} from '../../types';

interface SmartSuggestionsProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading?: boolean;
}

const SmartSuggestions: React.FC<SmartSuggestionsProps> = ({ 
  state, 
  onStateChange, 
  loading = false 
}) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [applyingId, setApplyingId] = useState<string | null>(null);
  const [context, setContext] = useState<Record<string, any>>({});

  // Buscar sugestões quando estado mudar
  useEffect(() => {
    if (!loading && state) {
      fetchSuggestions();
    }
  }, [state.deficit_surplus, state.contribution_rate, state.retirement_age, state.target_benefit, state.target_replacement_rate, state.benefit_target_mode]);

  const fetchSuggestions = async () => {
    try {
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
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const applySuggestion = async (suggestion: Suggestion) => {
    try {
      setApplyingId(suggestion.id);
      
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
      
      onStateChange(updates);
    } catch (error) {
      console.error('Erro ao aplicar sugestão:', error);
    } finally {
      setApplyingId(null);
    }
  };

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'balance_plan':
        return <Icon name="scale" size="sm" color="primary" />;
      case 'improve_benefit':
        return <Icon name="bar-chart" size="sm" color="success" />;
      case 'reduce_contribution':
        return <Icon name="coins" size="sm" color="warning" />;
      case 'optimize_retirement':
        return <Icon name="calendar" size="sm" className="text-purple-600" />;
      case 'sustainable_benefit':
        return <Icon name="target" size="sm" className="text-green-600" />;
      case 'trade_off_options':
        return <Icon name="fork" size="sm" className="text-blue-600" />;
      case 'optimize_multiple':
        return <Icon name="sliders" size="sm" className="text-indigo-600" />;
      default:
        return <Icon name="lightbulb" size="sm" color="primary" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-orange-600';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
            <Icon name="loader" size="sm" color="primary" className="animate-spin" />
          </div>
          <h3 className="text-base font-semibold text-gray-900">Sugestões Inteligentes</h3>
        </div>
        <p className="text-sm text-gray-600">Analisando seus dados...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6" role="region" aria-labelledby="smart-suggestions-title">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
          <Icon name="lightbulb" size="sm" color="primary" />
        </div>
        <h3 id="smart-suggestions-title" className="text-base font-semibold text-gray-900">Sugestões Inteligentes</h3>
      </div>

      {suggestionsLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Icon name="loader" size="sm" className="animate-spin text-gray-600" />
          <span>Gerando sugestões...</span>
        </div>
      ) : suggestions.length > 0 ? (
        <div className="space-y-2">
          {/* Contexto atual */}
          {context.current_deficit_surplus && (
            <div className="pb-4 border-b border-gray-100">
              <div className="text-xs text-gray-500 mb-1">Situação Atual</div>
              <div className="text-sm font-medium text-gray-900">
                {context.current_deficit_surplus > 0 
                  ? `Superávit: ${formatCurrencyBR(Math.abs(context.current_deficit_surplus))}`
                  : `Déficit: ${formatCurrencyBR(Math.abs(context.current_deficit_surplus))}`
                }
              </div>
            </div>
          )}

          {/* Lista de sugestões */}
          {suggestions.map((suggestion, index) => (
            <div 
              key={suggestion.id} 
              className={`p-4 rounded-lg ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}
            >
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="w-6 h-6 bg-gray-50 rounded-lg flex items-center justify-center flex-shrink-0">
                    {getSuggestionIcon(suggestion.type)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-gray-900 mb-1">
                      {suggestion.title}
                    </h4>
                    <p className="text-xs text-gray-600">
                      {suggestion.description} • {suggestion.impact_description}
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => applySuggestion(suggestion)}
                  disabled={applyingId === suggestion.id}
                  aria-label={`Aplicar sugestão: ${suggestion.action_label}`}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium py-2 px-4 rounded-md transition-colors duration-200 flex items-center gap-2 flex-shrink-0"
                >
                  {applyingId === suggestion.id ? (
                    <>
                      <Icon name="loader" className="w-3 h-3 animate-spin" />
                      <span>Aplicando...</span>
                    </>
                  ) : (
                    <>
                      <Icon name="sparkles" className="w-3 h-3" />
                      <span>{suggestion.action_label}</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-4">
          <Icon name="trending-up" size="lg" className="text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-700 mb-1">Seus parâmetros estão equilibrados!</p>
          <p className="text-xs text-gray-500">Continue ajustando para ver novas sugestões.</p>
        </div>
      )}
    </div>
  );
};

export default SmartSuggestions;