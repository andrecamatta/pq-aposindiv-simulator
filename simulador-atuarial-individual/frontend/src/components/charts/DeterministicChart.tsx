import React from 'react';
import { BaseProjectionChart } from './BaseProjectionChart';
import type { SimulatorResults } from '../../types/simulator.types';

interface DeterministicChartProps {
  results: SimulatorResults;
  currentAge: number;
  planType?: string;
}

const DeterministicChart: React.FC<DeterministicChartProps> = ({ results, currentAge, planType }) => {
  // Determinar labels conforme o tipo de plano
  const isCDPlan = planType === 'CD';
  const reserveLabel = isCDPlan ? 'Saldo Individual CD' : 'Reservas Acumuladas (Determinística)';

  const datasets = [
    {
      label: reserveLabel,
      data: results.accumulated_reserves || [],
      borderColor: '#A78BFA', // softer violet-400
      backgroundColor: 'rgba(167, 139, 250, 0.1)',
      tension: 0.4,
      fill: true,
      pointRadius: 2,
    },
  ];

  return (
    <BaseProjectionChart
      results={results}
      currentAge={currentAge}
      title="Simulação Determinística - Evolução das Reservas"
      tooltipContent="Simulação realística assumindo que você viverá durante todo período projetado. Mostra exatamente quanto dinheiro você terá em cada idade, considerando salários, contribuições e benefícios. Reservas negativas = dinheiro insuficiente. Esta é a realidade financeira da sua conta individual."
      datasets={datasets}
      yAxisLabel="Reservas/Saldo (R$)"
    />
  );
};

export default DeterministicChart;
