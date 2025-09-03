import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import type { SimulatorResults } from '../../types/simulator.types';

interface ContributionGaugeProps {
  results: SimulatorResults;
  currentRate: number;
}

const ContributionGauge: React.FC<ContributionGaugeProps> = ({ results, currentRate }) => {
  const requiredRate = results.required_contribution_rate;
  const maxRate = Math.max(requiredRate * 1.5, 15);
  
  const getColor = (rate: number) => {
    if (rate <= 8) return '#6EE7B7'; // Soft Green
    if (rate <= 12) return '#FCD34D'; // Soft Amber
    return '#F87171'; // Soft Red
  };

  const currentColor = getColor(currentRate);
  const requiredColor = getColor(requiredRate);

  const data = {
    datasets: [
      {
        data: [currentRate, maxRate - currentRate],
        backgroundColor: [currentColor, '#F3F4F6'],
        borderColor: [currentColor, '#E5E7EB'],
        borderWidth: 1,
        cutout: '75%',
        circumference: 180,
        rotation: 270,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: false,
      },
    },
  };

  return (
    <div className="relative h-48">
      <Doughnut data={data} options={options} />
      
      {/* Center Values */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-center mb-4">
          <div className="text-2xl font-bold" style={{ color: currentColor }}>
            {currentRate.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 font-medium">Taxa Atual</div>
        </div>
      </div>

      {/* Required Rate Indicator */}
      <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 text-center">
        <div className="flex items-center justify-center space-x-4 text-sm">
          <div className="flex items-center">
            <div 
              className="w-3 h-3 rounded-full mr-2" 
              style={{ backgroundColor: requiredColor }}
            ></div>
            <span>Necessária: {requiredRate.toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Scale markers */}
      <div className="absolute bottom-8 left-0 text-xs text-gray-400">0%</div>
      <div className="absolute bottom-8 right-0 text-xs text-gray-400">{maxRate.toFixed(0)}%</div>
    </div>
  );
};

export default ContributionGauge;