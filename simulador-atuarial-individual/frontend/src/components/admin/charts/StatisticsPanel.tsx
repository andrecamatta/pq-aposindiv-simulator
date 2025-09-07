import React from 'react';
import { 
  TrendingUp, 
  Users, 
  BarChart3, 
  Target,
  Activity,
  Info
} from 'lucide-react';
import type { TableStatistics } from '../hooks/useMortalityTables';

// Formatação brasileira para percentuais
const formatPercentBR = (value: number): string => {
  if (!isFinite(value) || isNaN(value)) return '0,00%';
  return (value * 100).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }) + '%';
};

interface StatisticsPanelProps {
  statistics?: any; // Temporário até implementar API completa
  mortalityData: Array<{ age: number; qx: number }>;
}

const StatisticsPanel: React.FC<StatisticsPanelProps> = ({ 
  statistics,
  mortalityData = []
}) => {
  // Calcular estatísticas a partir dos dados reais
  const calculateBasicStats = () => {
    if (!mortalityData.length) return { min: 0, max: 0, mean: 0, median: 0, std: 0, count: 0 };
    
    const qxValues = mortalityData
      .map(d => Math.max(d.qx, 0)) // Apenas garantir que não seja negativo
      .filter(qx => isFinite(qx) && !isNaN(qx)) // Remover valores inválidos
      .sort((a, b) => a - b);
    
    if (!qxValues.length) return { min: 0, max: 0, mean: 0, median: 0, std: 0, count: 0 };
    
    const sum = qxValues.reduce((a, b) => a + b, 0);
    const mean = sum / qxValues.length;
    const median = qxValues[Math.floor(qxValues.length / 2)];
    const variance = qxValues.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / qxValues.length;
    const std = Math.sqrt(variance);
    
    return {
      min: Math.min(...qxValues),
      max: Math.max(...qxValues),
      mean,
      median,
      std,
      count: qxValues.length
    };
  };


  const calculatePercentiles = () => {
    if (!mortalityData.length) return { p25: 0, p50: 0, p75: 0, p90: 0, p95: 0 };
    
    const sorted = mortalityData
      .map(d => Math.max(d.qx, 0))
      .filter(qx => isFinite(qx) && !isNaN(qx))
      .sort((a, b) => a - b);
      
    if (!sorted.length) return { p25: 0, p50: 0, p75: 0, p90: 0, p95: 0 };
      
    const getPercentile = (p: number) => {
      const index = Math.ceil(p / 100 * sorted.length) - 1;
      return sorted[Math.max(0, index)];
    };
    
    return {
      p25: getPercentile(25),
      p50: getPercentile(50),
      p75: getPercentile(75),
      p90: getPercentile(90),
      p95: getPercentile(95)
    };
  };

  const basicStats = calculateBasicStats();
  const percentiles = calculatePercentiles();
  
  const tableInfo = {
    name: statistics?.table_info?.name || 'Tábua de Mortalidade',
    code: statistics?.table_info?.code || 'N/A',
    gender: statistics?.table_info?.gender || 'N/A'
  };
  
  // Calcular métricas atuariais adicionais
  const calculateLifeExpectancy = (): number => {
    if (!mortalityData.length) return 0;
    
    // Calcular esperança de vida usando método atuarial correto
    // e₀ = Σ(lx / l₀) onde lx são os sobreviventes ao início de cada idade
    let survivors = 100000; // radix da tábua
    let expectancy = 0;
    const initialPop = 100000;
    
    for (let i = 0; i < mortalityData.length; i++) {
      const qx = Math.min(Math.max(mortalityData[i].qx, 0), 1.0); // Garantir 0 ≤ qx ≤ 1.0 (100%)
      
      // Somar a contribuição de cada idade para a esperança de vida
      expectancy += survivors / initialPop;
      
      // Aplicar mortalidade para próxima idade
      survivors = survivors * (1 - qx);
      
      // Parar quando sobreviventes chegam próximo a zero
      if (survivors < 0.1) break;
    }
    
    return Math.round(expectancy * 10) / 10; // Uma casa decimal
  };

  const calculateModalAge = (): number => {
    if (!mortalityData.length) return 0;
    
    // Idade com maior incremento de mortalidade
    let maxIncrease = 0;
    let modalAge = 0;
    
    for (let i = 1; i < mortalityData.length; i++) {
      const currentQx = Math.max(mortalityData[i].qx, 0);
      const prevQx = Math.max(mortalityData[i - 1].qx, 0);
      const increase = currentQx - prevQx;
      if (increase > maxIncrease && isFinite(increase)) {
        maxIncrease = increase;
        modalAge = mortalityData[i].age;
      }
    }
    
    return modalAge;
  };

  const lifeExpectancy = calculateLifeExpectancy();
  const modalAge = calculateModalAge();

  const formatLifeExpectancy = (years: number): string => {
    const wholeYears = Math.floor(years);
    const months = Math.round((years - wholeYears) * 12);
    
    if (months === 0) {
      return `${wholeYears} anos`;
    }
    return `${wholeYears} anos e ${months} ${months === 1 ? 'mês' : 'meses'}`;
  };


  return (
    <div className="w-full space-y-3">
      {/* Header Compacto */}
      <div className="bg-white rounded-lg border border-gray-200 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4 text-blue-600" />
            <h3 className="text-sm font-semibold text-gray-900">{tableInfo.name}</h3>
          </div>
          <div className="flex items-center space-x-3 text-xs text-gray-600">
            <span>Código: <span className="font-medium text-gray-900">{tableInfo.code}</span></span>
            <span>•</span>
            <span>Gênero: <span className="font-medium text-gray-900 capitalize">{tableInfo.gender}</span></span>
          </div>
        </div>
      </div>

      {/* Métricas em Linha Única */}
      <div className="bg-white rounded-lg border border-gray-200 p-3">
        <div className="grid grid-cols-3 gap-4 text-xs">
          <div className="text-center">
            <div className="text-gray-600 mb-1">Esperança de Vida</div>
            <div className="font-semibold text-gray-900">{formatLifeExpectancy(lifeExpectancy)}</div>
          </div>
          <div className="text-center border-x border-gray-200">
            <div className="text-gray-600 mb-1">Idade Modal</div>
            <div className="font-semibold text-gray-900">{modalAge} anos</div>
          </div>
          <div className="text-center">
            <div className="text-gray-600 mb-1">Faixa de Idades</div>
            <div className="font-semibold text-gray-900">
              {Math.min(...mortalityData.map(d => d.age))}-{Math.max(...mortalityData.map(d => d.age))} anos
            </div>
          </div>
        </div>
      </div>



    </div>
  );
};

export default StatisticsPanel;