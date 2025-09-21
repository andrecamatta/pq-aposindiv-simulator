import React from 'react';
import './TabNavigation.css';
import ConnectionStatus, { type ConnectionState } from './ConnectionStatus';

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
    id: 'tables',
    label: 'Tábuas',
    icon: 'table_chart',
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
  connectionStatus?: ConnectionState;
  lastPing?: Date;
  responseTime?: number;
  onReconnect?: () => void;
}

const TabNavigation: React.FC<TabNavigationProps> = ({
  className = '',
  activeTab = 'technical',
  onTabChange,
  connectionStatus = 'disconnected',
  lastPing,
  responseTime,
  onReconnect,
}) => {
  return (
    <header className={`bg-white shadow-sm ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center gap-3">
            <img
              src="/logo.png"
              alt="PrevLab Logo"
              className="h-8 w-auto max-w-[40px] object-contain"
            />
            <h1 className="text-xl font-semibold text-gray-800">
              PrevLab
            </h1>
          </div>
          <div className="flex items-center gap-4">
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
            <ConnectionStatus
              status={connectionStatus}
              lastPing={lastPing || undefined}
              responseTime={responseTime}
              onReconnect={onReconnect}
            />
          </div>
        </div>
      </div>
    </header>
  );
};

export default TabNavigation;
