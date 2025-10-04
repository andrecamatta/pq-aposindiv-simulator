import React from 'react';

export type TablesSubView = 'analysis' | 'manage' | 'add';

interface TablesSubNavigationProps {
  activeView: TablesSubView;
  onViewChange: (view: TablesSubView) => void;
}

const TablesSubNavigation: React.FC<TablesSubNavigationProps> = ({
  activeView,
  onViewChange
}) => {
  const subTabs = [
    {
      id: 'analysis' as TablesSubView,
      label: 'Análise',
      icon: 'insights',
      description: 'Visualização e comparação de tábuas'
    },
    {
      id: 'manage' as TablesSubView,
      label: 'Gerenciar',
      icon: 'storage',
      description: 'Lista e administração de tábuas'
    },
    {
      id: 'add' as TablesSubView,
      label: 'Adicionar',
      icon: 'add_circle',
      description: 'Upload CSV e busca Pymort'
    }
  ];

  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="flex space-x-8" aria-label="Sub-navegação de tábuas">
        {subTabs.map((tab) => {
          const isActive = activeView === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onViewChange(tab.id)}
              className={`
                flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors
                ${isActive
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={isActive ? 'page' : undefined}
              title={tab.description}
            >
              <span className="material-icons" style={{ fontSize: '20px' }}>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default TablesSubNavigation;
