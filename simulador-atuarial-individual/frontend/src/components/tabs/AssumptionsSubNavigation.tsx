import React from 'react';

export type AssumptionsSubView = 'financial' | 'family';

interface AssumptionsSubNavigationProps {
  activeView: AssumptionsSubView;
  onViewChange: (view: AssumptionsSubView) => void;
}

const AssumptionsSubNavigation: React.FC<AssumptionsSubNavigationProps> = ({
  activeView,
  onViewChange
}) => {
  const subTabs = [
    {
      id: 'financial' as AssumptionsSubView,
      label: 'Financeiras',
      description: 'Benefícios, contribuições e taxas de rentabilidade'
    },
    {
      id: 'family' as AssumptionsSubView,
      label: 'Família',
      description: 'Dependentes e benefícios de sobreviventes'
    }
  ];

  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="flex space-x-8" aria-label="Sub-navegação de premissas">
        {subTabs.map((tab) => {
          const isActive = activeView === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onViewChange(tab.id)}
              className={`
                py-3 px-1 border-b-2 font-medium text-sm transition-colors
                ${isActive
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={isActive ? 'page' : undefined}
              title={tab.description}
            >
              {tab.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default AssumptionsSubNavigation;
