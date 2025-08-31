import React from 'react';
import { User, Settings, TrendingUp, Cog, FileText } from 'lucide-react';
import SaiLogo from '../../assets/sai-logo.svg';

export interface Tab {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: {
    primary: string;
    light: string;
    gradient: string;
    bg: string;
  };
  disabled?: boolean;
}

export const tabs: Tab[] = [
  {
    id: 'participant',
    label: 'Participante',
    icon: User,
    color: {
      primary: '#2563eb', // blue-600
      light: '#60a5fa',   // blue-400
      gradient: 'from-blue-400 to-blue-600',
      bg: 'bg-blue-50'
    }
  },
  {
    id: 'assumptions',
    label: 'Premissas',
    icon: Settings,
    color: {
      primary: '#8b5cf6', // violet-600
      light: '#a78bfa',   // violet-400
      gradient: 'from-violet-400 to-violet-600',
      bg: 'bg-violet-50'
    }
  },
  {
    id: 'technical',
    label: 'Técnico',
    icon: Cog,
    color: {
      primary: '#ea580c', // orange-600
      light: '#fb923c',   // orange-400
      gradient: 'from-orange-400 to-orange-600',
      bg: 'bg-orange-50'
    }
  },
  {
    id: 'results',
    label: 'Resultados',
    icon: TrendingUp,
    color: {
      primary: '#059669', // emerald-600
      light: '#34d399',   // emerald-400
      gradient: 'from-emerald-400 to-emerald-600',
      bg: 'bg-emerald-50'
    }
  },
  {
    id: 'reports',
    label: 'Relatórios',
    icon: FileText,
    color: {
      primary: '#db2777', // pink-600
      light: '#f472b6',   // pink-400
      gradient: 'from-pink-400 to-pink-600',
      bg: 'bg-pink-50'
    }
  }
];

interface TabNavigationProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
}

const TabNavigation: React.FC<TabNavigationProps> = ({
  activeTab,
  onTabChange,
  className = ''
}) => {
  return (
    <div className={`w-full bg-gradient-to-r from-gray-50/20 via-white/30 to-gray-100/20 border-b border-gray-200/10 shadow-2xl backdrop-blur-2xl relative overflow-hidden ${className}`}>
      {/* Floating orbs background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-4 -left-4 w-20 h-20 bg-gradient-to-br from-blue-200/15 to-purple-200/15 rounded-full blur-xl animate-pulse"></div>
        <div className="absolute -top-2 right-1/4 w-16 h-16 bg-gradient-to-br from-pink-200/10 to-rose-200/10 rounded-full blur-lg animate-pulse delay-1000"></div>
        <div className="absolute -bottom-2 right-1/3 w-12 h-12 bg-gradient-to-br from-green-200/15 to-emerald-200/15 rounded-full blur-md animate-pulse delay-2000"></div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="flex items-center justify-between py-4">
          {/* Logo/Brand with enhanced gradient */}
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 flex items-center justify-center shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 relative">
              <img src={SaiLogo} alt="SAI Logo" className="w-full h-full" />
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-gray-700 via-gray-800 to-gray-900 bg-clip-text text-transparent">
              Simulador Atuarial
            </h1>
          </div>

          {/* Enhanced Tab Navigation with glassmorphism */}
          <nav className="flex items-center space-x-1 bg-white/70 backdrop-blur-md rounded-2xl p-1.5 border border-white/30 shadow-2xl relative overflow-hidden">
            {/* Animated background glow */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-50/30 via-purple-50/20 to-pink-50/30 rounded-2xl opacity-60"></div>
            
            {tabs.map((tab, index) => {
              const isActive = activeTab === tab.id;
              const Icon = tab.icon;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`
                    relative flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm
                    transition-all duration-500 ease-out hover:scale-105 active:scale-95
                    ${isActive 
                      ? `text-white shadow-xl transform scale-[1.05] z-10`
                      : 'text-gray-600 hover:text-gray-800 hover:bg-white/60 hover:shadow-md'
                    }
                  `}
                  style={{
                    backgroundColor: isActive ? tab.color.primary : 'transparent',
                    animationDelay: `${index * 100}ms`
                  }}
                >
                  {isActive && (
                    <>
                      {/* Primary background with gradient */}
                      <div 
                        className="absolute inset-0 rounded-xl opacity-90"
                        style={{
                          background: `linear-gradient(135deg, ${tab.color.primary}, ${tab.color.light})`
                        }}
                      />
                      
                      {/* Glow effect */}
                      <div 
                        className="absolute inset-0 rounded-xl opacity-40 blur-md scale-110"
                        style={{
                          background: `linear-gradient(135deg, ${tab.color.primary}, ${tab.color.light})`
                        }}
                      />
                      
                      {/* Inner highlight */}
                      <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/20 to-transparent"></div>
                    </>
                  )}
                  
                  <Icon className={`
                    w-4 h-4 transition-all duration-300 relative z-10
                    ${isActive ? 'text-white drop-shadow-sm' : 'text-gray-500'}
                    ${isActive ? 'animate-pulse' : ''}
                  `} />
                  <span className="relative z-10 drop-shadow-sm">{tab.label}</span>
                  
                  {isActive && (
                    <div 
                      className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-8 h-0.5 rounded-full shadow-md animate-pulse"
                      style={{ 
                        backgroundColor: tab.color.light,
                        boxShadow: `0 0 8px ${tab.color.light}40`
                      }}
                    />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
};

export default TabNavigation;
