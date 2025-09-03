import React from 'react';

export interface Tab {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: {
    primary: string;
    light: string;
    gradient: string;
    bg: string;
  };
  disabled?: boolean;
}

// Ícones SVG otimizados para cada tab
const TechnicalIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
  </svg>
);

const ParticipantIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const AssumptionsIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const ResultsIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const ReportsIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

export const tabs: Tab[] = [
  {
    id: 'technical',
    label: 'Técnico',
    icon: <TechnicalIcon className="w-6 h-6" />,
    color: {
      primary: '#1e3a8a', // Navy blue - Base sólida
      light: '#3b82f6',   // Blue 500
      gradient: 'from-blue-900 to-blue-700',
      bg: 'bg-blue-50'
    }
  },
  {
    id: 'participant',
    label: 'Participante', 
    icon: <ParticipantIcon className="w-6 h-6" />,
    color: {
      primary: '#f59e0b', // Dourado premium
      light: '#fbbf24',   // Amber 400
      gradient: 'from-amber-500 to-yellow-600',
      bg: 'bg-amber-50'
    }
  },
  {
    id: 'assumptions',
    label: 'Premissas',
    icon: <AssumptionsIcon className="w-6 h-6" />,
    color: {
      primary: '#7c3aed', // Roxo real
      light: '#a855f7',   // Purple 500
      gradient: 'from-purple-600 to-violet-700', 
      bg: 'bg-purple-50'
    }
  },
  {
    id: 'results',
    label: 'Resultados',
    icon: <ResultsIcon className="w-6 h-6" />,
    color: {
      primary: '#059669', // Verde esmeralda
      light: '#10b981',   // Emerald 500
      gradient: 'from-emerald-600 to-teal-700',
      bg: 'bg-emerald-50'
    }
  },
  {
    id: 'reports',
    label: 'Relatórios',
    icon: <ReportsIcon className="w-6 h-6" />,
    color: {
      primary: '#ef4444', // Vermelho coral
      light: '#f87171',   // Red 400
      gradient: 'from-red-500 to-rose-600',
      bg: 'bg-red-50'
    }
  }
];

interface TabNavigationProps {
  className?: string;
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
  state?: any; // SimulatorState para preview data
  results?: any; // SimulatorResults para preview data
}

const TabNavigation: React.FC<TabNavigationProps> = ({
  className = '',
  activeTab = 'technical',
  onTabChange,
  state,
  results
}) => {
  return (
    <div className={`w-full bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 ${className}`}>
      {/* Premium Header */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between">
          {/* Logo Premium */}
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 text-amber-400 drop-shadow-lg">
              <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path d="M42.4379 44C42.4379 44 36.0744 33.9038 41.1692 24C46.8624 12.9336 42.2078 4 42.2078 4L7.01134 4C7.01134 4 11.6577 12.932 5.96912 23.9969C0.876273 33.9029 7.27094 44 7.27094 44L42.4379 44Z" fill="currentColor"></path>
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">ActuarialSim</h1>
            </div>
          </div>

          {/* Elegant Tabs Navigation */}
          <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md p-2 rounded-2xl border border-white/20">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange?.(tab.id)}
                  className={`group relative flex items-center gap-3 px-6 py-4 rounded-xl font-semibold text-sm transition-all duration-300 transform hover:scale-105 ${
                    isActive
                      ? 'text-white shadow-2xl'
                      : 'text-slate-300 hover:text-white hover:bg-white/10'
                  }`}
                  style={{
                    background: isActive 
                      ? `linear-gradient(135deg, ${tab.color.primary}, ${tab.color.light})`
                      : undefined
                  }}
                >
                  {/* Glow effect for active tab */}
                  {isActive && (
                    <div 
                      className="absolute inset-0 rounded-xl blur-lg opacity-50 -z-10 scale-110"
                      style={{
                        background: `linear-gradient(135deg, ${tab.color.primary}, ${tab.color.light})`
                      }}
                    />
                  )}

                  {/* Icon with premium styling */}
                  <div className={`flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200 ${
                    isActive 
                      ? 'bg-white/20 text-white shadow-inner' 
                      : 'text-slate-400 group-hover:text-slate-200'
                  }`}>
                    {tab.icon}
                  </div>

                  {/* Label */}
                  <span className="font-bold tracking-wide whitespace-nowrap">
                    {tab.label}
                  </span>

                  {/* Active pulse indicator */}
                  {isActive && (
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-gradient-to-r from-amber-400 to-yellow-500 rounded-full animate-pulse shadow-lg" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Premium User Avatar */}
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-amber-400 to-amber-600 rounded-full w-12 h-12 shadow-lg border-2 border-amber-300/50 flex items-center justify-center">
              <svg className="w-7 h-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TabNavigation;
