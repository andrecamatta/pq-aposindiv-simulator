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
      .map(d => Math.min(Math.max(d.qx, 0), 0.999)) // Sanitizar valores qx (máx 99.9%)
      .sort((a, b) => a - b);
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

  const calculateAgeGroups = () => {
    if (!mortalityData.length) return { young: { avg_qx: 0, ages: '0-0' }, adult: { avg_qx: 0, ages: '0-0' }, elderly: { avg_qx: 0, ages: '0-0' } };
    
    const young = mortalityData.filter(d => d.age >= 0 && d.age <= 30);
    const adult = mortalityData.filter(d => d.age > 30 && d.age <= 65);
    const elderly = mortalityData.filter(d => d.age > 65);
    
    const avgQx = (group: typeof mortalityData) => {
      if (!group.length) return 0;
      const sanitized = group.map(d => Math.min(Math.max(d.qx, 0), 0.999));
      return sanitized.reduce((acc, qx) => acc + qx, 0) / sanitized.length;
    };
    const ageRange = (group: typeof mortalityData) => group.length ? `${Math.min(...group.map(d => d.age))}-${Math.max(...group.map(d => d.age))}` : '0-0';
    
    return {
      young: { avg_qx: avgQx(young), ages: ageRange(young) },
      adult: { avg_qx: avgQx(adult), ages: ageRange(adult) },
      elderly: { avg_qx: avgQx(elderly), ages: ageRange(elderly) }
    };
  };

  const calculatePercentiles = () => {
    if (!mortalityData.length) return { p25: 0, p50: 0, p75: 0, p90: 0, p95: 0 };
    
    const sorted = mortalityData
      .map(d => Math.min(Math.max(d.qx, 0), 0.999)) // Sanitizar valores qx (máx 99.9%)
      .sort((a, b) => a - b);
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
  const ageGroups = calculateAgeGroups();
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
      const qx = Math.min(Math.max(mortalityData[i].qx, 0), 0.999); // Garantir 0 ≤ qx ≤ 99.9%
      
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
      const currentQx = Math.min(Math.max(mortalityData[i].qx, 0), 0.999);
      const prevQx = Math.min(Math.max(mortalityData[i - 1].qx, 0), 0.999);
      const increase = currentQx - prevQx;
      if (increase > maxIncrease) {
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

  const StatCard: React.FC<{
    icon: React.ReactNode;
    title: string;
    value: string;
    subtitle?: string;
    color: string;
  }> = ({ icon, title, value, subtitle, color }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <div className={`p-1.5 rounded-md ${color}`}>
              {icon}
            </div>
            <h4 className="text-sm font-medium text-gray-900">{title}</h4>
          </div>
          <p className="text-2xl font-bold text-gray-900 mb-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center space-x-3 mb-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <BarChart3 className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Análise Estatística</h3>
            <p className="text-sm text-gray-600">{tableInfo.name}</p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Código:</span>
            <span className="ml-2 font-medium text-gray-900">{tableInfo.code}</span>
          </div>
          <div>
            <span className="text-gray-500">Gênero:</span>
            <span className="ml-2 font-medium text-gray-900 capitalize">{tableInfo.gender}</span>
          </div>
        </div>
      </div>

      {/* Métricas Atuariais */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">Métricas Atuariais</h4>
        
        <StatCard
          icon={<Activity className="h-4 w-4 text-white" />}
          title="Esperança de Vida e₀"
          value={formatLifeExpectancy(lifeExpectancy)}
          subtitle="Expectativa de vida ao nascer"
          color="bg-green-500"
        />

        <StatCard
          icon={<Target className="h-4 w-4 text-white" />}
          title="Idade Modal"
          value={`${modalAge} anos`}
          subtitle="Maior incremento de mortalidade"
          color="bg-purple-500"
        />

        <StatCard
          icon={<Users className="h-4 w-4 text-white" />}
          title="Total de Idades"
          value={basicStats.count.toLocaleString()}
          subtitle={`Faixa: ${Math.min(...mortalityData.map(d => d.age))}-${Math.max(...mortalityData.map(d => d.age))} anos`}
          color="bg-blue-500"
        />
      </div>

      {/* Estatísticas Básicas */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
          <TrendingUp className="h-4 w-4 mr-2" />
          Estatísticas qx
        </h4>
        
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Mínimo:</span>
            <span className="font-mono text-gray-900">{(basicStats.min * 1000).toFixed(3)}‰</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-600">Máximo:</span>
            <span className="font-mono text-gray-900">{(basicStats.max * 1000).toFixed(3)}‰</span>
          </div>
          
          <div className="flex justify-between border-t pt-2">
            <span className="text-gray-600">Média:</span>
            <span className="font-mono font-medium text-gray-900">{(basicStats.mean * 1000).toFixed(3)}‰</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-600">Mediana:</span>
            <span className="font-mono text-gray-900">{(basicStats.median * 1000).toFixed(3)}‰</span>
          </div>
          
          <div className="flex justify-between">
            <span className="text-gray-600">Desvio Padrão:</span>
            <span className="font-mono text-gray-900">{(basicStats.std * 1000).toFixed(3)}‰</span>
          </div>
        </div>
      </div>

      {/* Análise por Faixa Etária */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Por Faixa Etária</h4>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between p-2 bg-green-50 rounded-md">
            <div>
              <span className="text-sm font-medium text-green-900">Jovens ({ageGroups.young.ages})</span>
            </div>
            <span className="text-sm font-mono text-green-800">
              {(ageGroups.young.avg_qx * 1000).toFixed(3)}‰
            </span>
          </div>
          
          <div className="flex items-center justify-between p-2 bg-yellow-50 rounded-md">
            <div>
              <span className="text-sm font-medium text-yellow-900">Adultos ({ageGroups.adult.ages})</span>
            </div>
            <span className="text-sm font-mono text-yellow-800">
              {(ageGroups.adult.avg_qx * 1000).toFixed(3)}‰
            </span>
          </div>
          
          <div className="flex items-center justify-between p-2 bg-red-50 rounded-md">
            <div>
              <span className="text-sm font-medium text-red-900">Idosos ({ageGroups.elderly.ages})</span>
            </div>
            <span className="text-sm font-mono text-red-800">
              {(ageGroups.elderly.avg_qx * 1000).toFixed(3)}‰
            </span>
          </div>
        </div>
      </div>

      {/* Percentis */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Distribuição (Percentis)</h4>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">P25:</span>
            <span className="font-mono text-gray-900">{(percentiles.p25 * 1000).toFixed(3)}‰</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">P50:</span>
            <span className="font-mono text-gray-900">{(percentiles.p50 * 1000).toFixed(3)}‰</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">P75:</span>
            <span className="font-mono text-gray-900">{(percentiles.p75 * 1000).toFixed(3)}‰</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">P90:</span>
            <span className="font-mono text-gray-900">{(percentiles.p90 * 1000).toFixed(3)}‰</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">P95:</span>
            <span className="font-mono text-gray-900">{(percentiles.p95 * 1000).toFixed(3)}‰</span>
          </div>
        </div>
      </div>

      {/* Nota Informativa */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-4">
        <div className="flex items-start space-x-3">
          <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="text-blue-900 font-medium mb-1">Sobre as Métricas</p>
            <p className="text-blue-800 text-xs leading-relaxed">
              As taxas qx representam a probabilidade de morte entre as idades x e x+1. 
              Valores em ‰ (por mil) são padrão na indústria atuarial.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatisticsPanel;