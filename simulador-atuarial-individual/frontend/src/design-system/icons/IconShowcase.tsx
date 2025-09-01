import React from 'react';
import { Icon } from '../components/Icon';
import { iconMap, type IconName, type IconSize, type IconColor } from './iconConfig';

const IconShowcase: React.FC = () => {
  const sizes: IconSize[] = ['xs', 'sm', 'md', 'lg', 'xl'];
  const colors: IconColor[] = ['primary', 'success', 'warning', 'error', 'neutral', 'muted'];
  const featuredIcons: IconName[] = [
    'user', 'settings', 'bar-chart', 'dollar-sign', 'check-circle', 
    'alert-triangle', 'info', 'help-circle', 'chevron-down', 'trending-up'
  ];

  return (
    <div className="p-6 space-y-8 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-gray-900">Sistema de Ícones Padronizado</h2>
      
      {/* Tamanhos */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Tamanhos</h3>
        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
          {sizes.map(size => (
            <div key={size} className="flex flex-col items-center gap-2">
              <Icon name="user" size={size} color="primary" />
              <span className="text-xs font-medium text-gray-600">{size}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Cores */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Cores Semânticas</h3>
        <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
          {colors.map(color => (
            <div key={color} className="flex flex-col items-center gap-2">
              <Icon name="check-circle" size="md" color={color} />
              <span className="text-xs font-medium text-gray-600">{color}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Ícones em destaque */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Ícones Principais</h3>
        <div className="grid grid-cols-5 gap-4">
          {featuredIcons.map(iconName => (
            <div key={iconName} className="flex flex-col items-center gap-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
              <Icon name={iconName} size="lg" color="neutral" />
              <span className="text-xs font-medium text-gray-600 text-center">{iconName}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Todos os ícones */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Todos os Ícones ({Object.keys(iconMap).length})</h3>
        <div className="grid grid-cols-8 gap-2 max-h-64 overflow-y-auto">
          {Object.keys(iconMap).map(iconName => (
            <div key={iconName} className="flex flex-col items-center gap-1 p-2 border border-gray-100 rounded hover:bg-gray-50">
              <Icon name={iconName as IconName} size="md" color="neutral" />
              <span className="text-xs text-gray-500 text-center truncate w-full">{iconName}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Estatísticas */}
      <section className="bg-blue-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Melhorias Implementadas</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Icon name="check-circle" size="sm" color="success" />
            <span>Sistema centralizado ({Object.keys(iconMap).length} ícones)</span>
          </div>
          <div className="flex items-center gap-2">
            <Icon name="check-circle" size="sm" color="success" />
            <span>Tamanhos padronizados (5 sizes)</span>
          </div>
          <div className="flex items-center gap-2">
            <Icon name="check-circle" size="sm" color="success" />
            <span>Cores semânticas (6 cores)</span>
          </div>
          <div className="flex items-center gap-2">
            <Icon name="check-circle" size="sm" color="success" />
            <span>Única biblioteca (Lucide React)</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default IconShowcase;