import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Bar } from 'react-chartjs-2';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';
import { formatCurrencyBR } from '../../utils/formatBR';
import { getZeroLineGridConfig } from '../../utils/chartSetup';

interface SufficiencyAnalysisChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}


const SufficiencyAnalysisChart: React.FC<SufficiencyAnalysisChartProps> = ({ results, state }) => {
  // Verificações de segurança
  if (!results || !state) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-center">
          <Icon name="scale" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
        </div>
      </div>
    );
  }

  const isCDPlan = state.plan_type === 'CD';

  // Lógica condicional para BD vs CD
  let chartData, labels, analysisTitle;

  if (isCDPlan) {
    // Para CD: Análise de Adequação do Saldo
    const saldoFinalCD = results.individual_balance || 0;
    const rendaAnualCD = (results.monthly_income_cd || 0) * 12;
    const contribuicoesTotais = results.total_contributions || 0;
    
    chartData = [contribuicoesTotais, saldoFinalCD - contribuicoesTotais, rendaAnualCD];
    labels = ['Contribuições\nTotais', 'Rendimentos\nAcumulados', 'Renda Anual\nCD'];
    analysisTitle = 'Análise de Adequação do Saldo CD';
  } else {
    // Para BD: Análise de Suficiência original
    const initialBalance = isNaN(state.initial_balance) ? 0 : state.initial_balance;
    const negativeRMBA = isNaN(results.rmba) ? 0 : -results.rmba;
    const deficitSurplus = isNaN(results.deficit_surplus) ? 0 : results.deficit_surplus;
    
    chartData = [initialBalance, negativeRMBA, deficitSurplus];
    labels = ['Saldo\nInicial', '-RMBA\n(Passivo Reduzido)', 'Déficit/Superávit\n(Resultado)'];
    analysisTitle = 'Análise de Suficiência Financeira';
  }

  const data = {
    labels: labels,
    datasets: [
      {
        label: analysisTitle + ' (R$)',
        data: chartData,
        backgroundColor: [
          'rgba(147, 197, 253, 0.8)',  // Azul suave
          'rgba(252, 211, 77, 0.8)',   // Âmbar suave
          'rgba(167, 139, 250, 0.8)',  // Roxo suave
        ],
        borderColor: [
          'rgb(147, 197, 253)',       // Azul suave
          'rgb(252, 211, 77)',        // Âmbar suave
          'rgb(167, 139, 250)',       // Roxo suave
        ],
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        top: 40, // Espaço para rótulos superiores
        bottom: 10,
        left: 10,
        right: 10,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const value = context.parsed.y;
            return `${context.label}: ${formatCurrencyBR(value)}`;
          },
        },
      },
      datalabels: {
        display: true,
        anchor: 'end' as const,
        align: (context: any) => {
          // Para valores negativos, posiciona abaixo da barra
          const value = context.parsed?.y ?? context.raw;
          return value < 0 ? 'bottom' : 'top';
        },
        formatter: (value: number) => formatCurrencyBR(value),
        font: {
          size: 11,
          weight: 'bold' as const,
        },
        color: '#374151',
        clamp: true, // Garante que os rótulos ficam dentro da área visível
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
            weight: 'bold' as const,
          },
          color: '#6B7280',
        },
      },
      y: {
        beginAtZero: false,
        grid: getZeroLineGridConfig(),
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
          callback: function(value: any) {
            return formatCurrencyBR(value);
          },
        },
        title: {
          display: true,
          text: 'Valores (R$)',
          font: {
            size: 12,
            weight: 'bold' as const,
          },
          color: '#374151',
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  return (
    <div className="space-y-3">      
      {/* Gráfico */}
      <div className="h-[448px]"> {/* Aumentada de h-80 para h-[448px] (40% maior) para melhor visualização */}
        <Bar data={data} options={options} />
      </div>
      
      {/* Explicação da Fórmula */}
      <div className="bg-gray-50 rounded-lg p-3">
        <div className="text-center text-sm text-gray-600">
          {isCDPlan ? (
            <>
              <div className="font-medium mb-1">Composição do Patrimônio CD:</div>
              <div className="font-mono text-xs">
                <span className="text-blue-400">Contribuições</span>
                {" + "}
                <span className="text-amber-400">Rendimentos</span>
                {" → "}
                <span className="text-violet-400">Renda Anual</span>
              </div>
            </>
          ) : (
            <>
              <div className="font-medium mb-1">Equação de Suficiência Financeira:</div>
              <div className="font-mono text-xs">
                <span className="text-blue-400">Saldo Inicial</span>
                {" + "}
                <span className="text-amber-400">(-RMBA)</span>
                {" = "}
                <span className="text-violet-400">
                  {chartData[2] >= 0 ? 'Superávit' : 'Déficit'}
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SufficiencyAnalysisChart;