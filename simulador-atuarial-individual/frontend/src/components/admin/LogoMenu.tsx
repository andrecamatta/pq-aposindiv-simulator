import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Settings, Database, Info, Home } from 'lucide-react';

interface LogoMenuProps {
  onOpenMortalityTables?: () => void;
}

const LogoMenu: React.FC<LogoMenuProps> = ({ onOpenMortalityTables }) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Fechar menu ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        menuRef.current && 
        buttonRef.current && 
        !menuRef.current.contains(event.target as Node) &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Fechar menu com Escape
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('keydown', handleEscape);
      };
    }
  }, [isOpen]);

  const handleMenuItemClick = (action: () => void) => {
    action();
    setIsOpen(false);
  };

  const handleDashboard = () => {
    // Já está no dashboard, apenas fecha o menu
    console.log('Navegando para Dashboard');
  };

  const handleMortalityTables = () => {
    if (onOpenMortalityTables) {
      onOpenMortalityTables();
    }
  };

  const handleSettings = () => {
    console.log('Abrindo Configurações');
    // TODO: Implementar modal de configurações
  };

  const handleAbout = () => {
    console.log('Abrindo Sobre');
    // TODO: Implementar modal sobre
  };

  return (
    <>
      <div className="relative">
        {/* Logo com dropdown */}
        <button
          ref={buttonRef}
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 sm:gap-3 hover:bg-gray-50 rounded-lg p-1 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 relative z-[9999]"
          aria-label="Menu administrativo"
          aria-expanded={isOpen}
        >
          <img
            src="/logo.png"
            alt="ActuarialSim Logo"
            className="h-7 w-auto max-w-[38px] object-contain shrink-0"
          />
          <h1 className="hidden sm:block text-lg md:text-xl font-semibold text-gray-800 leading-none">
            ActuarialSim
          </h1>
          <ChevronDown 
            className={`h-4 w-4 text-gray-400 transition-transform duration-200 ${
              isOpen ? 'transform rotate-180' : ''
            }`}
          />
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div
            ref={menuRef}
            className={`absolute top-full left-0 mt-2 w-64 bg-white rounded-xl shadow-2xl border border-gray-200 py-2 z-[9999] backdrop-blur-sm transform transition-all duration-200 ease-out ${
              isOpen ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
            }`}
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.98)',
              backdropFilter: 'blur(8px) saturate(180%)',
            }}
            role="menu"
            aria-label="Menu administrativo"
          >
            <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
              <h3 className="text-sm font-semibold text-gray-800">Menu Administrativo</h3>
              <p className="text-xs text-gray-600">Gerenciamento e configurações</p>
            </div>

            <div className="py-1">
              {/* Dashboard */}
              <button
                onClick={() => handleMenuItemClick(handleDashboard)}
                className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-150"
                role="menuitem"
              >
                <Home className="h-4 w-4 text-gray-500" />
                <span className="font-medium">Dashboard</span>
              </button>

              {/* Gerenciar Tábuas */}
              <button
                onClick={() => handleMenuItemClick(handleMortalityTables)}
                className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-150"
                role="menuitem"
              >
                <Database className="h-4 w-4 text-gray-500" />
                <div className="flex-1 text-left">
                  <div className="font-medium">Gerenciar Tábuas</div>
                  <div className="text-xs text-gray-500">Upload, análise e pymort</div>
                </div>
              </button>

              {/* Configurações */}
              <button
                onClick={() => handleMenuItemClick(handleSettings)}
                className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-150"
                role="menuitem"
              >
                <Settings className="h-4 w-4 text-gray-500" />
                <span className="font-medium">Configurações</span>
              </button>

              {/* Sobre */}
              <button
                onClick={() => handleMenuItemClick(handleAbout)}
                className="flex items-center gap-3 w-full px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-colors duration-150"
                role="menuitem"
              >
                <Info className="h-4 w-4 text-gray-500" />
                <span className="font-medium">Sobre</span>
              </button>
            </div>

            <div className="border-t border-gray-100 pt-2 pb-1 bg-gray-50/30 rounded-b-xl">
              <div className="px-4 py-2">
                <p className="text-xs text-gray-500 font-medium">
                  ActuarialSim v1.0.0
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Backdrop quando menu está aberto */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-[9998]"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}
    </>
  );
};

export default LogoMenu;