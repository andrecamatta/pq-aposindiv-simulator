import React from 'react';
import { BaseProjectionChart } from './BaseProjectionChart';
import type { SimulatorResults } from '../../types/simulator.types';

interface ActuarialChartProps {
  results: SimulatorResults;
  currentAge: number;
  retirementAge: number;
}

const ActuarialChart: React.FC<ActuarialChartProps> = ({ results, currentAge, retirementAge }) => {
  // Detectar se a pessoa já está aposentada
  const isAlreadyRetired = currentAge >= retirementAge;

  // Usar dados reais do backend para projeções atuariais
  const vpaBenefits = results.projected_vpa_benefits || [];
  const vpaContributions = results.projected_vpa_contributions || [];

  // Escolher RMBA (ativos) ou RMBC (aposentados) baseado no status
  const reserveEvolution = isAlreadyRetired
    ? (results.projected_rmbc_evolution || [])
    : (results.projected_rmba_evolution || []);

  // Label dinâmico baseado no status
  const reserveLabel = isAlreadyRetired
    ? 'RMBC (Benefícios Concedidos)'
    : 'RMBA (Reserva Matemática)';

  const datasets = [
    {
      label: 'VPA Benefícios Futuros',
      data: vpaBenefits,
      borderColor: '#F87171', // red-400 - softer red
      backgroundColor: 'transparent',
      tension: 0.4,
      fill: false,
      pointRadius: 2,
      borderDash: [5, 5],
    },
    {
      label: 'VPA Contribuições Futuras',
      data: vpaContributions,
      borderColor: '#34D399', // emerald-400 - softer green
      backgroundColor: 'transparent',
      tension: 0.4,
      fill: false,
      pointRadius: 2,
      borderDash: [3, 3],
    },
    {
      label: reserveLabel,
      data: reserveEvolution,
      borderColor: '#13a4ec', // primary color from inspiration
      backgroundColor: 'rgba(19, 164, 236, 0.1)',
      tension: 0.4,
      fill: true,
      pointRadius: 3,
      borderWidth: 2,
    },
  ];

  const tooltipContent = isAlreadyRetired
    ? "Para aposentados: RMBC (Reserva Matemática de Benefícios Concedidos) = valor presente dos benefícios restantes a serem pagos. VPA Contribuições = 0 (não há contribuições futuras). Usado para análise da sustentabilidade dos benefícios."
    : "Para ativos: RMBA (Reserva Matemática de Benefícios a Conceder) = diferença entre VPA benefícios futuros e VPA contribuições futuras. VPA considera probabilidades de sobrevivência da tábua de mortalidade. Usado para cálculos regulatórios e análise de suficiência.";

  return (
    <BaseProjectionChart
      results={results}
      currentAge={currentAge}
      title="Análise Atuarial - Considerando Mortalidade"
      tooltipContent={tooltipContent}
      datasets={datasets}
      yAxisLabel="Valores Presentes Atuariais (R$)"
    />
  );
};

export default ActuarialChart;
