import React, { useState } from 'react';
import { BarChart3, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { StatusBadge } from '../design-system/components';

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  connected: boolean;
}

const menuItems = [
  {
    id: 'dashboard',
    name: 'Dashboard',
    icon: BarChart3,
    description: 'Simulação'
  },
  {
    id: 'reports',
    name: 'Relatórios',
    icon: FileText,
    description: 'Exportação'
  }
];

const Sidebar: React.FC<SidebarProps> = ({ activeSection, onSectionChange, connected }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className={`bg-gray-900 text-white transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    } min-h-screen flex flex-col shadow-xl border-r border-gray-800`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div>
              <h1 className="text-lg font-bold text-white">Simulador</h1>
              <p className="text-xs text-gray-400">Atuarial Individual</p>
            </div>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 rounded-lg hover:bg-gray-800 transition-colors group"
            title={isCollapsed ? 'Expandir sidebar' : 'Recolher sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-white" />
            ) : (
              <ChevronLeft className="w-4 h-4 text-gray-400 group-hover:text-white" />
            )}
          </button>
        </div>
      </div>

      {/* Status */}
      <div className="px-4 py-3">
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'}`}>
          <StatusBadge 
            status={connected ? 'online' : 'offline'} 
            size="xs"
            className={isCollapsed ? '' : ''}
          >
            {!isCollapsed && (connected ? 'Online' : 'Offline')}
          </StatusBadge>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2">
        <ul className="space-y-1">
          {menuItems.map((item) => {
            const isActive = activeSection === item.id;
            const IconComponent = item.icon;
            
            return (
              <li key={item.id}>
                <button
                  onClick={() => onSectionChange(item.id)}
                  className={`w-full flex items-center px-3 py-3 rounded-lg transition-all duration-200 group ${
                    isActive 
                      ? 'bg-primary-600 text-white shadow-lg' 
                      : 'hover:bg-gray-800 text-gray-300 hover:text-white'
                  } ${isCollapsed ? 'justify-center' : 'space-x-3'}`}
                  title={isCollapsed ? item.name : undefined}
                >
                  <IconComponent className={`w-5 h-5 flex-shrink-0 ${
                    isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'
                  }`} />
                  {!isCollapsed && (
                    <div className="text-left flex-1 min-w-0">
                      <div className="text-sm font-medium truncate">{item.name}</div>
                      <div className="text-xs text-gray-400 truncate">{item.description}</div>
                    </div>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-4 border-t border-gray-800">
          <div className="text-xs text-gray-400 space-y-1">
            <p className="font-medium text-gray-300">v1.0.0</p>
            <p className="opacity-75">Uso Profissional</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;