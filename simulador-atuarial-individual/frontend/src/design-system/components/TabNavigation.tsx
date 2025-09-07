import React from 'react';
import LogoMenu from '../../components/admin/LogoMenu';
import './TabNavigation.css';

export interface Tab {
  id: string;
  label: string;
  icon: string; // Material icon name
  disabled?: boolean;
}

export const tabs: Tab[] = [
  {
    id: 'technical',
    label: 'Plano',
    icon: 'account_balance',
  },
  {
    id: 'participant',
    label: 'Participante', 
    icon: 'person',
  },
  {
    id: 'assumptions',
    label: 'Premissas',
    icon: 'list_alt',
  },
  {
    id: 'results',
    label: 'Resultados',
    icon: 'analytics',
  },
  {
    id: 'sensitivity',
    label: 'Sensibilidade',
    icon: 'settings',
  },
  {
    id: 'reports',
    label: 'Relatórios',
    icon: 'description',
  }
];

interface TabNavigationProps {
  className?: string;
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
  onOpenMortalityTables?: () => void;
}

const TabNavigation: React.FC<TabNavigationProps> = ({
  className = '',
  activeTab = 'technical',
  onTabChange,
  onOpenMortalityTables,
}) => {
  return (
    <header className={`bg-white shadow-sm ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <LogoMenu onOpenMortalityTables={onOpenMortalityTables} />
          <nav className="tab-navigation">
            <ul>
              {tabs.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <li key={tab.id}>
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        if (onTabChange) {
                          onTabChange(tab.id);
                        }
                      }}
                      className={isActive ? 'active' : ''}
                    >
                      <span className="material-icons">{tab.icon}</span>
                      {tab.label}
                    </a>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default TabNavigation;
