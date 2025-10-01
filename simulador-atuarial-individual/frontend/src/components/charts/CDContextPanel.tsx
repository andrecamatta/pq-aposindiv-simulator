import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import type { SimulatorResults, SimulatorState, CDConversionMode } from '../../types/simulator.types';
import { formatCurrencyBR } from '../../utils/formatBR';

interface CDContextPanelProps {
  results: SimulatorResults;
  state: SimulatorState;
}

const CDContextPanel: React.FC<CDContextPanelProps> = ({ results, state }) => {
  // Mapear modalidades para descrições claras
  const getConversionModeInfo = (mode: CDConversionMode) => {
    const modeMap = {
      'ACTUARIAL': {
        label: 'Renda Vitalícia Atuarial',
        description: 'Benefício calculado pela expectativa de vida',
        icon: 'target' as const,
        color: 'bg-blue-100 text-blue-800'
      },
      'ACTUARIAL_EQUIVALENT': {
        label: 'Equivalente Atuarial',
        description: 'Benefício baseado em equivalência atuarial',
        icon: 'scale' as const,
        color: 'bg-indigo-100 text-indigo-800'
      },
      'CERTAIN_5Y': {
        label: 'Prazo Certo - 5 Anos',
        description: 'Pagamentos garantidos por 5 anos',
        icon: 'clock' as const,
        color: 'bg-green-100 text-green-800'
      },
      'CERTAIN_10Y': {
        label: 'Prazo Certo - 10 Anos',
        description: 'Pagamentos garantidos por 10 anos',
        icon: 'clock' as const,
        color: 'bg-green-100 text-green-800'
      },
      'CERTAIN_15Y': {
        label: 'Prazo Certo - 15 Anos',
        description: 'Pagamentos garantidos por 15 anos',
        icon: 'clock' as const,
        color: 'bg-green-100 text-green-800'
      },
      'CERTAIN_20Y': {
        label: 'Prazo Certo - 20 Anos',
        description: 'Pagamentos garantidos por 20 anos',
        icon: 'clock' as const,
        color: 'bg-green-100 text-green-800'
      },
      'PERCENTAGE': {
        label: 'Percentual do Saldo',
        description: 'Saque percentual mensal',
        icon: 'pie-chart' as const,
        color: 'bg-yellow-100 text-yellow-800'
      },
      'PROGRAMMED': {
        label: 'Saque Programado',
        description: 'Saques programados conforme estratégia',
        icon: 'trending-down' as const,
        color: 'bg-purple-100 text-purple-800'
      }
    };

    const fallbackInfo = {
      label: 'Renda Vitalícia Atuarial',
      description: 'Benefício calculado pela expectativa de vida (padrão)',
      icon: 'target' as const,
      color: 'bg-blue-100 text-blue-800'
    };

    return modeMap[mode] || fallbackInfo;
  };

  // Sempre garantir que há uma modalidade (usando fallback como outros componentes)
  const conversionMode = state.cd_conversion_mode || 'ACTUARIAL';
  const modeInfo = getConversionModeInfo(conversionMode);

  // Determinar cenários disponíveis
  const hasActuarialScenario = results.actuarial_scenario;
  const hasDesiredScenario = results.desired_scenario;
  const showComparison = hasActuarialScenario && hasDesiredScenario;

  // Extrair informações dos cenários
  const actuarialIncome = hasActuarialScenario
    ? results.actuarial_scenario?.monthly_income || results.monthly_income_cd
    : results.monthly_income_cd;

  const desiredIncome = hasDesiredScenario
    ? results.desired_scenario?.monthly_income
    : state.target_benefit;

  const peakBalance = Math.max(...(results.accumulated_reserves || []));

  // Calcular diferença percentual para status
  const percentDifference = showComparison && actuarialIncome && desiredIncome
    ? Math.round((desiredIncome / actuarialIncome - 1) * 100)
    : 0;

  return (
    <div className="bg-gray-50/50 rounded-lg px-4 py-3 mb-4 border-0">
      <div className="flex flex-wrap items-center gap-4 text-sm">

        {/* Modalidade */}
        <div className="flex items-center gap-2">
          <Icon name={modeInfo.icon} size="sm" className="text-blue-600" />
          <span className="font-medium text-gray-800">{modeInfo.label}</span>
        </div>

        {/* Separador */}
        <div className="text-gray-300 font-light">•</div>

        {/* Cenário Atual */}
        <div className="flex items-center gap-2">
          <span className="text-gray-600">Atual:</span>
          <span className="font-semibold text-gray-900">
            {formatCurrencyBR(actuarialIncome || 0, 0)}
          </span>
        </div>

        {/* Meta (se houver comparação) */}
        {showComparison && (
          <>
            <div className="text-gray-300 font-light">•</div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Meta:</span>
              <span className="font-semibold text-gray-900">
                {formatCurrencyBR(desiredIncome || 0, 0)}
              </span>
            </div>

            {/* Status Badge */}
            {percentDifference !== 0 && (
              <>
                <div className="text-gray-300 font-light">•</div>
                <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                  percentDifference > 0
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-green-100 text-green-700'
                }`}>
                  <Icon
                    name={percentDifference > 0 ? "alert-triangle" : "check-circle"}
                    size="xs"
                  />
                  {percentDifference > 0 ? `+${percentDifference}%` : '✓ Suficiente'}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default CDContextPanel;