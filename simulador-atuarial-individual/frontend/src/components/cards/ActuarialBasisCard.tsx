import React from 'react';
import { BarChart3, Info } from 'lucide-react';
import type { SimulatorState, MortalityTable } from '../../types';
import { Card, CardHeader, CardTitle, CardContent } from '../../design-system/components';

interface ActuarialBasisCardProps {
  state: SimulatorState;
  mortalityTables: MortalityTable[];
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const ActuarialBasisCard: React.FC<ActuarialBasisCardProps> = ({ 
  state, 
  mortalityTables, 
  onStateChange, 
  loading 
}) => {
  const handleInputChange = (field: keyof SimulatorState, value: any) => {
    onStateChange({ [field]: value });
  };

  return (
    <Card variant="default" padding="md">
      <CardHeader withBorder>
        <CardTitle className="flex items-center gap-3">
          <div className="w-10 h-10 bg-info-100 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-info-600" />
          </div>
          Base Atuarial
        </CardTitle>
      </CardHeader>
      
      <CardContent className="pt-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tábua de Mortalidade */}
        <div className="space-y-3">
          <label className="block text-base font-semibold text-slate-700 mb-2">
            Tábua de Mortalidade
            <span className="text-xs text-slate-500 font-normal ml-1">
              ℹ️
              <span className="hidden">Tábua utilizada para cálculos de probabilidade de sobrevivência</span>
            </span>
          </label>
          <select
            value={state.mortality_table}
            onChange={(e) => handleInputChange('mortality_table', e.target.value)}
            className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl bg-white hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all shadow-sm"
            disabled={loading}
          >
            {mortalityTables.map((table) => (
              <option key={table.code} value={table.code}>
                {table.code} {table.regulatory_approved && '✓'}
              </option>
            ))}
          </select>
        </div>

        {/* Método de Cálculo */}
        <div className="space-y-3">
          <label className="block text-base font-semibold text-slate-700 mb-2">
            Método de Cálculo Atuarial
            <span className="text-xs text-slate-500 font-normal ml-1">
              ℹ️
              <span className="hidden">Método utilizado para distribuir custos ao longo do tempo</span>
            </span>
          </label>
          <select
            value={state.calculation_method}
            onChange={(e) => handleInputChange('calculation_method', e.target.value as 'PUC' | 'EAN')}
            className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl bg-white hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all shadow-sm"
            disabled={loading}
          >
            <option value="PUC">PUC - Projected Unit Credit</option>
            <option value="EAN">EAN - Entry Age Normal</option>
          </select>
        </div>
        
        {/* Informações adicionais sobre os métodos */}
        <div className="mt-6 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-gray-600">
              <p className="font-semibold mb-2">Métodos de Cálculo:</p>
              <div className="space-y-2">
                <p><strong className="text-gray-700">PUC:</strong> Distribui o custo baseado no benefício acumulado até cada idade</p>
                <p><strong className="text-gray-700">EAN:</strong> Distribui o custo uniformemente durante toda a carreira</p>
              </div>
            </div>
          </div>
        </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ActuarialBasisCard;