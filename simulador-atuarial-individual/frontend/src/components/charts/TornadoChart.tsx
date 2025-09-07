import React from 'react';
import { Bar } from 'react-chartjs-2';
import { Icon } from '../../design-system/components/Icon';
import { getZeroLineGridConfig } from '../../utils/chartSetup';
import { formatCurrencyBR, formatPercentageBR } from '../../utils/formatBR';
import ChartErrorBoundary from './ChartErrorBoundary';

export interface TornadoItem {
  label: string;
  deltaLow: number;
  deltaHigh: number;
  unit: 'R$' | '%';
  tooltip?: string;
}

interface TornadoChartProps {
  items: TornadoItem[];
  baseline: number;
  title?: string;
  height?: number;
  className?: string;
}

const TornadoChart: React.FC<TornadoChartProps> = React.memo(({
  items,
  baseline,
  title = 'Análise de Sensibilidade',
  height = 400,
  className = ''
}) => {
  // Log detalhado para debug
  console.log('[TornadoChart] Renderizando com:', { 
    itemsCount: items?.length || 0, 
    baseline, 
    title,
    items: items?.slice(0, 3) // Log apenas primeiros 3 itens
  });

  if (!items || items.length === 0) {
    console.warn('[TornadoChart] Nenhum item para renderizar');
    return (
      <div className={`h-64 flex items-center justify-center ${className}`}>
        <div className="text-center">
          <Icon name="bar-chart" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500 font-medium">Dados de sensibilidade não disponíveis</p>
          <p className="text-sm text-gray-400 mt-2">
            Execute a simulação atuarial para gerar a análise de sensibilidade
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Certifique-se de que o tipo de plano está configurado corretamente
          </p>
        </div>
      </div>
    );
  }

  // Função para normalizar valores extremos
  const normalizeValue = (value: number): number => {
    if (!isFinite(value) || isNaN(value)) {
      return 0;
    }
    
    // Limitar valores extremos que podem quebrar o Chart.js
    const MAX_VALUE = 1e12; // 1 trilhão
    const MIN_VALUE = -1e12;
    
    if (value > MAX_VALUE) {
      console.warn(`[TornadoChart] Valor muito grande normalizado: ${value} -> ${MAX_VALUE}`);
      return MAX_VALUE;
    }
    if (value < MIN_VALUE) {
      console.warn(`[TornadoChart] Valor muito pequeno normalizado: ${value} -> ${MIN_VALUE}`);
      return MIN_VALUE;
    }
    
    return value;
  };

  // Filtrar itens com dados válidos e normalizar valores extremos
  const validItems = items.filter(item => {
    const isValidLow = typeof item.deltaLow === 'number' && !isNaN(item.deltaLow) && isFinite(item.deltaLow);
    const isValidHigh = typeof item.deltaHigh === 'number' && !isNaN(item.deltaHigh) && isFinite(item.deltaHigh);
    return isValidLow && isValidHigh;
  }).map(item => ({
    ...item,
    deltaLow: normalizeValue(item.deltaLow),
    deltaHigh: normalizeValue(item.deltaHigh)
  }));

  console.log(`[TornadoChart] Itens válidos: ${validItems.length} de ${items.length}`);

  if (validItems.length === 0) {
    console.warn('[TornadoChart] Nenhum item válido após filtragem');
    return (
      <div className={`h-64 flex items-center justify-center ${className}`}>
        <div className="text-center">
          <Icon name="bar-chart" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500 font-medium">Dados de sensibilidade inválidos</p>
          <p className="text-sm text-gray-400 mt-2">
            Os dados contêm valores não numéricos ou infinitos
          </p>
        </div>
      </div>
    );
  }

  const sortedItems = [...validItems].sort((a, b) => {
    const impactA = Math.max(Math.abs(a.deltaLow), Math.abs(a.deltaHigh));
    const impactB = Math.max(Math.abs(b.deltaLow), Math.abs(b.deltaHigh));
    return impactB - impactA;
  });

  // Pegar apenas os top 5 para melhor visualização
  const displayItems = sortedItems.slice(0, 5);

  const formatValue = React.useCallback((value: number, unit: 'R$' | '%') => {
    return unit === 'R$' ? formatCurrencyBR(value) : formatPercentageBR(value);
  }, []);

  const formatDelta = React.useCallback((value: number, unit: 'R$' | '%') => {
    const formatted = unit === 'R$' ? formatCurrencyBR(Math.abs(value)) : formatPercentageBR(Math.abs(value));
    return value >= 0 ? `+${formatted}` : `-${formatted}`;
  }, []);

  // Formatação inteligente: para valores monetários grandes, mostrar absoluto + percentual
  const formatIntelligentDelta = React.useCallback((value: number, unit: 'R$' | '%', baseline: number) => {
    if (unit === '%') {
      // Para percentuais, manter formato atual
      return formatDelta(value, unit);
    }
    
    // Para valores monetários
    const absoluteFormatted = formatDelta(value, unit);
    
    // Calcular percentual relativo apenas se baseline > 0
    if (baseline > 0 && Math.abs(baseline) > 1) {
      const percentChange = (value / baseline) * 100;
      const percentFormatted = Math.abs(percentChange) >= 0.1 
        ? `${percentChange >= 0 ? '+' : ''}${percentChange.toFixed(1)}%`
        : `${percentChange >= 0 ? '+' : ''}${percentChange.toFixed(2)}%`;
      
      return `${absoluteFormatted} (${percentFormatted})`;
    }
    
    return absoluteFormatted;
  }, [formatDelta]);

  // Preparar dados para Chart.js (gráfico horizontal) - memoizado para evitar re-renders
  const data = React.useMemo(() => ({
    labels: displayItems.map(item => item.label),
    datasets: [
      {
        label: 'Impacto Negativo',
        data: displayItems.map(item => item.deltaLow),
        backgroundColor: 'rgba(239, 68, 68, 0.8)', // Vermelho
        borderColor: 'rgb(239, 68, 68)',
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false,
      },
      {
        label: 'Impacto Positivo', 
        data: displayItems.map(item => item.deltaHigh),
        backgroundColor: 'rgba(16, 185, 129, 0.8)', // Verde
        borderColor: 'rgb(16, 185, 129)',
        borderWidth: 2,
        borderRadius: 4,
        borderSkipped: false,
      }
    ],
  }), [displayItems]);

  // Memoizar opções do gráfico para evitar re-renders
  const options = React.useMemo(() => ({
    indexAxis: 'y' as const, // Gráfico horizontal
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        top: 20,
        bottom: 20,
        left: 200, // Espaço máximo para labels longos
        right: 50, // Espaço para labels
      },
    },
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        callbacks: {
          title: function(context: any) {
            try {
              if (!context || !Array.isArray(context) || context.length === 0) {
                return 'Análise de Sensibilidade';
              }
              const dataIndex = context[0]?.dataIndex;
              if (dataIndex === undefined || dataIndex < 0 || dataIndex >= displayItems.length) {
                return 'Análise de Sensibilidade';
              }
              const item = displayItems[dataIndex];
              return item?.tooltip || item?.label || 'Análise de Sensibilidade';
            } catch (error) {
              console.warn('[TornadoChart] Erro no tooltip title:', error);
              return 'Análise de Sensibilidade';
            }
          },
          label: function(context: any) {
            try {
              if (!context || typeof context.dataIndex !== 'number' || !context.parsed) {
                return 'Dados indisponíveis';
              }
              
              const dataIndex = context.dataIndex;
              if (dataIndex < 0 || dataIndex >= displayItems.length) {
                return 'Dados indisponíveis';
              }
              
              const item = displayItems[dataIndex];
              if (!item) {
                return 'Dados indisponíveis';
              }
              
              const value = context.parsed.x;
              if (typeof value !== 'number' || !isFinite(value)) {
                return 'Valor inválido';
              }
              
              const impact = formatIntelligentDelta(value, item.unit, baseline);
              const newValue = baseline + value;
              const baselineFormatted = formatValue(baseline, item.unit);
              const newFormatted = formatValue(newValue, item.unit);
              
              // Extrair informação de range do label se disponível
              const hasRange = item.label.includes('(') && item.label.includes(')');
              const rangeInfo = hasRange ? item.label.match(/\(([^)]+)\)/)?.[1] : null;
              
              const tooltipLines = [
                `Impacto: ${impact}`,
                `Baseline: ${baselineFormatted}`,
                `Novo valor: ${newFormatted}`
              ];
              
              // Adicionar informação de cenário se disponível
              if (rangeInfo) {
                tooltipLines.push('', `Cenário testado: ${rangeInfo}`);
                tooltipLines.push('💡 Variação centrada no valor atual configurado');
              }
              
              // Adicionar tooltip personalizado da variável se disponível
              if (item.tooltip && item.tooltip.trim()) {
                tooltipLines.push('', item.tooltip);
              }
              
              return tooltipLines;
            } catch (error) {
              console.warn('[TornadoChart] Erro no tooltip label:', error);
              return 'Erro ao calcular tooltip';
            }
          },
        },
      },
      datalabels: {
        display: true,
        anchor: 'end' as const,
        align: function(context: any) {
          try {
            if (!context || !context.parsed || typeof context.parsed.x !== 'number') {
              return 'start';
            }
            return context.parsed.x >= 0 ? 'start' : 'end';
          } catch (error) {
            console.warn('[TornadoChart] Erro no datalabel align:', error);
            return 'start';
          }
        },
        formatter: function(value: number, context: any) {
          try {
            if (typeof value !== 'number' || !isFinite(value)) {
              return '';
            }
            if (!context || typeof context.dataIndex !== 'number') {
              return '';
            }
            const dataIndex = context.dataIndex;
            if (dataIndex < 0 || dataIndex >= displayItems.length) {
              return '';
            }
            const item = displayItems[dataIndex];
            if (!item) {
              return '';
            }
            return formatIntelligentDelta(value, item.unit, baseline);
          } catch (error) {
            console.warn('[TornadoChart] Erro no datalabel formatter:', error);
            return '';
          }
        },
        font: {
          size: 11,
          weight: 'bold' as const,
        },
        color: '#374151',
        offset: 4,
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        grid: getZeroLineGridConfig(),
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
          callback: function(value: any) {
            try {
              if (typeof value !== 'number' || !isFinite(value)) {
                return '';
              }
              // Usar a unidade do primeiro item (assumindo que todos têm a mesma unidade)
              const unit = displayItems[0]?.unit || 'R$';
              return formatValue(value, unit);
            } catch (error) {
              console.warn('[TornadoChart] Erro no x-axis tick callback:', error);
              return '';
            }
          },
        },
        title: {
          display: true,
          text: 'Variação da Métrica',
          font: {
            size: 12,
            weight: 'bold' as const,
          },
          color: '#374151',
        },
      },
      y: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 12,
            weight: 'bold' as const,
          },
          color: '#374151',
          maxTicksLimit: 8,
          callback: function(_value: any, index: any) {
            try {
              if (typeof index !== 'number' || index < 0 || index >= displayItems.length) {
                return '';
              }
              const label = displayItems[index]?.label || '';
              // Truncar labels muito longos - permitindo mais caracteres
              return label.length > 40 ? label.substring(0, 37) + '...' : label;
            } catch (error) {
              console.warn('[TornadoChart] Erro no y-axis tick callback:', error);
              return '';
            }
          },
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  }), [displayItems, baseline, formatValue, formatDelta, formatIntelligentDelta]);

  // Gerar ID único para evitar conflito de canvas
  const chartId = React.useMemo(() => {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(7);
    const safeTitle = title.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase();
    return `tornado-${safeTitle}-${items.length}-${timestamp}-${random}`;
  }, [title, items.length]);

  // Ref para cleanup do chart
  const chartRef = React.useRef<any>(null);

  React.useEffect(() => {
    return () => {
      // Cleanup do chart quando componente desmonta
      if (chartRef.current) {
        try {
          chartRef.current.destroy();
        } catch (error) {
          console.warn('[TornadoChart] Erro ao destruir chart:', error);
        }
      }
    };
  }, []);

  return (
    <div className={`space-y-4 ${className}`}>
      {title && (
        <div className="flex items-center gap-2">
          <Icon name="bar-chart" size="sm" className="text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      )}
      
      <ChartErrorBoundary>
        <div style={{ height: `${height}px` }}>
          <Bar 
            key={chartId} 
            ref={chartRef}
            data={data} 
            options={options} 
          />
        </div>
      </ChartErrorBoundary>

    </div>
  );
});

export default TornadoChart;