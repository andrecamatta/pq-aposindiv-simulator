import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Upload, 
  Search, 
  BarChart3, 
  Eye, 
  Power, 
  Trash2, 
  FileText,
  AlertCircle,
  CheckCircle,
  Loader2,
  TrendingUp,
  GitCompare,
  X,
  MoreHorizontal,
  Menu
} from 'lucide-react';
import { useMortalityTables } from './hooks/useMortalityTables';
import type { MortalityTableAdmin, TableStatistics } from './hooks/useMortalityTables';
import { MortalityMainChart, StatisticsPanel, MortalityComparisonChart } from './charts';
import { Tooltip } from '../../design-system/components/Tooltip';
import { cn } from '../../lib/utils';
import UploadCSVForm from './UploadCSVForm';

interface MortalityTablesManagerProps {
  onClose: () => void;
}

const MortalityTablesManager: React.FC<MortalityTablesManagerProps> = ({ onClose }) => {
  const {
    tables,
    loading,
    error,
    toggleTableActive,
    deleteTable,
    searchPymort,
    loadFromPymort,
    uploadCSV,
    getTableStatistics,
    getTableMortalityData
  } = useMortalityTables();

  const [activeView, setActiveView] = useState<'dashboard' | 'upload' | 'search' | 'analysis'>('dashboard');
  const [selectedTable, setSelectedTable] = useState<MortalityTableAdmin | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [pymortResults, setPymortResults] = useState<any[]>([]);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  
  // Analysis state
  const [analysisView, setAnalysisView] = useState<'individual' | 'comparison'>('individual');
  const [selectedTableStats, setSelectedTableStats] = useState<TableStatistics | null>(null);
  const [selectedTableData, setSelectedTableData] = useState<Array<{ age: number; qx: number }> | null>(null);
  const [comparisonTables, setComparisonTables] = useState<number[]>([]);
  const [comparisonData, setComparisonData] = useState<Array<{
    name: string;
    data: Array<{ age: number; qx: number }>;
    color: string;
  }>>([]);
  const [statsLoading, setStatsLoading] = useState(false);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [chartType, setChartType] = useState<'mortality' | 'survival'>('mortality');
  const [comparisonChartType, setComparisonChartType] = useState<'mortality' | 'survival'>('mortality');
  
  // Estado para dropdown de ações e drawer mobile
  const [openDropdown, setOpenDropdown] = useState<number | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // useEffect para limpar dados quando não há tábuas selecionadas
  useEffect(() => {
    if (analysisView === 'comparison' && comparisonTables.length === 0) {
      setComparisonData([]);
    }
  }, [comparisonTables, analysisView]);

  // Atalhos de teclado
  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      // Ignore se estiver digitando em um input ou textarea
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (event.key) {
        case 'Escape':
          if (sidebarOpen) {
            setSidebarOpen(false);
          } else {
            onClose();
          }
          break;
          
        case '/':
          event.preventDefault();
          if (activeView === 'dashboard') {
            // Foca na busca do dashboard
            const searchInput = document.querySelector('input[placeholder*="Buscar por nome"]') as HTMLInputElement;
            searchInput?.focus();
          } else if (activeView === 'search') {
            // Foca na busca do SOA
            const soaInput = document.querySelector('input[placeholder*="Digite termos"]') as HTMLInputElement;
            soaInput?.focus();
          }
          break;
          
        case '1':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            setActiveView('dashboard');
            setSidebarOpen(false);
          }
          break;
          
        case '2':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            setActiveView('search');
            setSidebarOpen(false);
          }
          break;
          
        case '3':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            setActiveView('upload');
            setSidebarOpen(false);
          }
          break;
          
        case '4':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            setActiveView('analysis');
            setSidebarOpen(false);
          }
          break;
      }
    };

    document.addEventListener('keydown', handleKeydown);
    return () => {
      document.removeEventListener('keydown', handleKeydown);
    };
  }, [onClose, sidebarOpen, activeView]);

  // Filtrar tábuas
  const filteredTables = tables.filter(table =>
    table.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    table.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    table.source.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Estatísticas resumidas
  const stats = {
    total: tables.length,
    active: tables.filter(t => t.is_active).length,
    official: tables.filter(t => t.is_official).length,
    sources: [...new Set(tables.map(t => t.source))].length
  };

  // Handlers
  const toggleDropdown = (tableId: number) => {
    setOpenDropdown(openDropdown === tableId ? null : tableId);
  };

  // Fechar dropdown quando clica fora
  useEffect(() => {
    const handleClickOutside = () => setOpenDropdown(null);
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const handleToggleActive = async (tableId: number) => {
    try {
      setActionLoading(tableId);
      await toggleTableActive(tableId);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (tableId: number, tableName: string) => {
    if (!confirm(`Tem certeza que deseja excluir a tábua "${tableName}"?`)) return;
    
    try {
      setActionLoading(tableId);
      await deleteTable(tableId);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSearchPymort = async () => {
    if (!searchQuery.trim()) return;
    
    try {
      setActionLoading(-1);
      const results = await searchPymort(searchQuery);
      setPymortResults(results.results);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleLoadFromPymort = async (tableId: number) => {
    try {
      setActionLoading(tableId);
      await loadFromPymort(tableId);
      alert('Tábua será carregada em background. Aguarde alguns segundos.');
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openDropdown !== null) {
        setOpenDropdown(null);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [openDropdown]);

  // Analysis handlers
  const handleAnalyzeTable = async (table: MortalityTableAdmin) => {
    try {
      setStatsLoading(true);
      setSelectedTable(table);
      
      // Carregar estatísticas e dados em paralelo
      const [stats, mortalityData] = await Promise.all([
        getTableStatistics(table.id),
        getTableMortalityData(table.id)
      ]);
      
      setSelectedTableStats(stats);
      setSelectedTableData(mortalityData?.data || null);
      setAnalysisView('individual');
      setActiveView('analysis');
    } catch (err: any) {
      alert(err.message);
    } finally {
      setStatsLoading(false);
    }
  };

  const handleToggleComparison = (tableId: number) => {
    setComparisonTables(prev => {
      let newTables;
      if (prev.includes(tableId)) {
        newTables = prev.filter(id => id !== tableId);
      } else if (prev.length < 5) { // Limit to 5 tables for readability
        newTables = [...prev, tableId];
      } else {
        alert('Máximo de 5 tábuas para comparação');
        return prev;
      }
      
      // Se estivermos na view de comparação, recarregar dados automaticamente
      if (analysisView === 'comparison') {
        if (newTables.length > 0) {
          // Passar os novos valores diretamente para evitar race condition
          loadComparisonData(newTables);
        } else {
          // Se não há mais tábuas, limpar os dados
          setComparisonData([]);
        }
      }
      
      return newTables;
    });
  };

  // Carregar dados de comparação
  const loadComparisonData = async (tablesToLoad?: number[]) => {
    const tables = tablesToLoad || comparisonTables;
    if (tables.length === 0) {
      setComparisonData([]);
      return;
    }
    
    try {
      setComparisonLoading(true);
      
      const colors = [
        'rgb(59, 130, 246)',   // blue
        'rgb(239, 68, 68)',    // red
        'rgb(34, 197, 94)',    // green
        'rgb(251, 191, 36)',   // yellow
        'rgb(168, 85, 247)',   // purple
      ];
      
      const dataPromises = tables.map(async (tableId, index) => {
        const table = filteredTables.find(t => t.id === tableId);
        if (!table) return null;
        
        const mortalityData = await getTableMortalityData(tableId);
        return {
          name: table.name,
          data: mortalityData?.data || [],
          color: colors[index % colors.length]
        };
      });
      
      const results = await Promise.all(dataPromises);
      setComparisonData(results.filter(r => r !== null) as typeof comparisonData);
    } catch (err: any) {
      alert(`Erro ao carregar dados de comparação: ${err.message}`);
    } finally {
      setComparisonLoading(false);
    }
  };

  // Upload handler
  const handleUpload = async (file: File, metadata: {
    name: string;
    description: string;
    country: string;
    gender: string;
  }) => {
    try {
      setUploadLoading(true);
      await uploadCSV(file, metadata.name, metadata.description, metadata.country, metadata.gender);
      alert('Tábua carregada com sucesso!');
    } catch (err: any) {
      throw new Error(err.message);
    } finally {
      setUploadLoading(false);
    }
  };

  // Navigation Component
  const NavigationMenu = () => {
    const navItems = [
      { 
        id: 'dashboard', 
        label: 'Dashboard', 
        icon: Database, 
        disabled: false, 
        shortcut: 'Ctrl+1',
        badge: stats.total ? stats.total.toString() : null
      },
      { 
        id: 'search', 
        label: 'Buscar SOA', 
        icon: Search, 
        disabled: false, 
        shortcut: 'Ctrl+2',
        badge: null
      },
      { 
        id: 'upload', 
        label: 'Upload CSV', 
        icon: Upload, 
        disabled: false, 
        shortcut: 'Ctrl+3',
        badge: null
      },
      { 
        id: 'analysis', 
        label: 'Análises', 
        icon: BarChart3, 
        disabled: false, 
        shortcut: 'Ctrl+4',
        badge: selectedTable || comparisonTables.length > 0 ? '●' : null
      },
    ] as const;

    const handleNavClick = (viewId: typeof activeView) => {
      setActiveView(viewId);
      setSidebarOpen(false); // Close mobile drawer
    };

    return (
      <nav className="space-y-2">
        {navItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => !item.disabled && handleNavClick(item.id)}
              disabled={item.disabled}
              title={`${item.label} (${item.shortcut})`}
              className={cn(
                "w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-all duration-150",
                isActive 
                  ? 'bg-blue-600 text-white shadow-sm ring-2 ring-blue-600 ring-offset-2 ring-offset-gray-50' 
                  : item.disabled
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 hover:shadow-sm'
              )}
            >
              <div className="flex items-center gap-3">
                <Icon className="h-4 w-4 flex-shrink-0" />
                <span className="font-medium text-sm">{item.label}</span>
              </div>
              
              {/* Badge ou atalho */}
              <div className="flex items-center gap-2">
                {item.badge && (
                  <span className={cn(
                    "text-xs px-2 py-0.5 rounded-full font-medium",
                    isActive 
                      ? "bg-blue-500 text-blue-100" 
                      : "bg-blue-100 text-blue-700"
                  )}>
                    {item.badge}
                  </span>
                )}
                
                {/* Atalho - só mostra no desktop */}
                <span className={cn(
                  "hidden lg:block text-xs opacity-60 font-mono",
                  isActive ? "text-blue-200" : "text-gray-500"
                )}>
                  {index + 1}
                </span>
              </div>
            </button>
          );
        })}
        
        {/* Dicas de atalhos */}
        <div className="pt-4 mt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500 space-y-1">
            <div className="flex justify-between">
              <span>Buscar:</span>
              <kbd className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">/</kbd>
            </div>
            <div className="flex justify-between">
              <span>Fechar:</span>
              <kbd className="bg-gray-100 px-1.5 py-0.5 rounded text-xs font-mono">Esc</kbd>
            </div>
          </div>
        </div>
      </nav>
    );
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Busca e Filtros */}
      <div className="flex gap-4 items-center">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Buscar por nome, código ou fonte..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Lista de Tábuas */}
      <div className="max-h-96 overflow-y-auto overflow-x-visible relative">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-600">Carregando tábuas...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-2" />
            <p className="text-red-600">{error}</p>
          </div>
        ) : filteredTables.length === 0 ? (
          <div className="text-center py-8">
            <Database className="h-12 w-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500">Nenhuma tábua encontrada</p>
          </div>
        ) : (
          /* Tabela de Tábuas */
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
                  <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredTables.map((table) => {
                  const isInComparison = comparisonTables.includes(table.id);
                  const comparisonIndex = comparisonTables.indexOf(table.id);
                  
                  return (
                    <tr key={table.id} className={`hover:bg-gray-50 transition-colors ${
                      table.is_active ? 'bg-green-50' : ''
                    } ${isInComparison ? 'bg-blue-50' : ''}`}>
                        
                        {/* Nome com Tooltip */}
                        <td className="px-3 py-2">
                          <Tooltip
                            content={
                              <div className="space-y-2">
                                <div>
                                  <span className="font-semibold text-gray-300">Código:</span>
                                  <span className="ml-2 font-mono text-white">{table.code}</span>
                                </div>
                                <div>
                                  <span className="font-semibold text-gray-300">Fonte:</span>
                                  <span className="ml-2 text-white">{table.source}</span>
                                </div>
                                <div>
                                  <span className="font-semibold text-gray-300">Gênero:</span>
                                  <span className="ml-2 text-white">{table.gender}</span>
                                </div>
                                <div>
                                  <span className="font-semibold text-gray-300">País:</span>
                                  <span className="ml-2 text-white">{table.country || 'N/A'}</span>
                                </div>
                                {table.description && (
                                  <div>
                                    <span className="font-semibold text-gray-300">Descrição:</span>
                                    <div className="mt-1 text-white">{table.description}</div>
                                  </div>
                                )}
                                {table.is_official && (
                                  <div className="mt-2">
                                    <span className="inline-block text-xs bg-blue-600 text-white px-2 py-1 rounded">
                                      Tabela Oficial
                                    </span>
                                  </div>
                                )}
                              </div>
                            }
                            side="top"
                            className="!max-w-sm"
                          >
                            <div className="font-medium text-sm text-gray-900 truncate cursor-help">
                              {table.name}
                              {table.is_official && (
                                <span className="ml-2 inline-block text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded font-medium">
                                  Oficial
                                </span>
                              )}
                            </div>
                          </Tooltip>
                        </td>

                        {/* Status */}
                        <td className="px-3 py-2 text-center">
                          {table.is_active ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Ativa
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Inativa
                            </span>
                          )}
                        </td>

                        {/* Ações - Menu Dropdown */}
                        <td className="px-3 py-2 text-center relative">
                          <div className="relative inline-block">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleDropdown(table.id);
                              }}
                              className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                              title="Mais ações"
                            >
                              <MoreHorizontal className="h-4 w-4 text-gray-400" />
                            </button>
                            
                            {openDropdown === table.id && (
                              <div className="absolute right-0 mt-1 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-[60]">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleAnalyzeTable(table);
                                    setOpenDropdown(null);
                                  }}
                                  disabled={statsLoading}
                                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                                >
                                  <TrendingUp className="h-4 w-4 text-blue-500" />
                                  Analisar
                                </button>
                                
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleToggleComparison(table.id);
                                    setOpenDropdown(null);
                                  }}
                                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                                >
                                  <GitCompare className="h-4 w-4 text-gray-500" />
                                  {isInComparison ? 'Remover da Comparação' : 'Adicionar à Comparação'}
                                  {isInComparison && (
                                    <span className="ml-auto bg-blue-600 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
                                      {comparisonIndex + 1}
                                    </span>
                                  )}
                                </button>

                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleToggleActive(table.id);
                                    setOpenDropdown(null);
                                  }}
                                  disabled={actionLoading === table.id}
                                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                                >
                                  {actionLoading === table.id ? (
                                    <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
                                  ) : (
                                    <Power className={`h-4 w-4 ${table.is_active ? 'text-orange-500' : 'text-green-500'}`} />
                                  )}
                                  {table.is_active ? 'Desativar' : 'Ativar'}
                                </button>

                                {!table.is_system && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDelete(table.id, table.name);
                                      setOpenDropdown(null);
                                    }}
                                    disabled={actionLoading === table.id}
                                    className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                                  >
                                    <Trash2 className="h-4 w-4 text-red-500" />
                                    Excluir
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );

  const renderSearch = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Buscar Tábuas no pymort (SOA)</h3>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Digite termos como 'annuity', 'mortality', 'pension'..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && handleSearchPymort()}
          />
          <button
            onClick={handleSearchPymort}
            disabled={!searchQuery.trim() || actionLoading === -1}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {actionLoading === -1 ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Buscar
          </button>
        </div>
      </div>

      {pymortResults.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium text-gray-900">Resultados Encontrados:</h4>
          {pymortResults.map((result) => (
            <div key={result.id} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h5 className="font-medium text-gray-900">{result.name}</h5>
                  <p className="text-sm text-gray-600">{result.description}</p>
                  <p className="text-xs text-gray-500">ID: {result.id}</p>
                </div>
                <button
                  onClick={() => handleLoadFromPymort(result.id)}
                  disabled={actionLoading === result.id}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {actionLoading === result.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Database className="h-4 w-4" />
                  )}
                  Carregar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderAnalysis = () => (
    <div className="space-y-6">
      {/* Analysis Type Toggle */}
      <div className="flex gap-4 border-b border-gray-200 pb-4">
        <button
          onClick={() => setAnalysisView('individual')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            analysisView === 'individual' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <TrendingUp className="h-4 w-4 inline mr-2" />
          Análise Individual
        </button>
        <button
          onClick={() => {
            if (comparisonTables.length === 0) {
              alert('Selecione ao menos uma tábua para comparação no dashboard');
              setActiveView('dashboard');
              return;
            }
            setAnalysisView('comparison');
            loadComparisonData(comparisonTables);
          }}
          className={`px-4 py-2 rounded-lg transition-colors ${
            analysisView === 'comparison' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          <GitCompare className="h-4 w-4 inline mr-2" />
          Comparação ({comparisonTables.length})
        </button>
      </div>

      {analysisView === 'individual' && selectedTable && selectedTableStats ? (
        <div className="space-y-6">
          {/* Combobox para selecionar tipo de gráfico */}
          <div className="flex justify-start">
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value as 'mortality' | 'survival')}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="mortality">Taxa de Mortalidade (qx)</option>
              <option value="survival">Curva de Sobrevivência (lx)</option>
            </select>
          </div>
          
          {/* Professional Layout: Main Chart + Statistics Panel */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Main Mortality Chart - 70% width */}
            <div className="xl:col-span-2">
              {selectedTableData ? (
                <MortalityMainChart 
                  data={selectedTableData} 
                  tableName={selectedTable.name}
                  color="rgb(59, 130, 246)"
                  showLogScale={chartType === 'mortality'}
                  chartType={chartType}
                />
              ) : (
                <div className="w-full h-[500px] bg-white rounded-lg border border-gray-200 flex items-center justify-center">
                  <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-600">Carregando curva de mortalidade...</p>
                  </div>
                </div>
              )}
            </div>

            {/* Statistics Panel - 30% width */}
            <div className="xl:col-span-1">
              <div className="h-[500px] overflow-y-auto pr-2">
                <StatisticsPanel 
                  statistics={selectedTableStats}
                  mortalityData={selectedTableData || []}
                />
              </div>
            </div>
          </div>
        </div>
      ) : analysisView === 'comparison' && comparisonTables.length > 0 ? (
        <div className="space-y-6">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Comparação de Tábuas ({comparisonTables.length})
              </h3>
              
              {/* Combobox para tipo de gráfico na comparação */}
              <select
                value={comparisonChartType}
                onChange={(e) => setComparisonChartType(e.target.value as 'mortality' | 'survival')}
                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="mortality">Taxa de Mortalidade (qx)</option>
                <option value="survival">Curva de Sobrevivência (lx)</option>
              </select>
            </div>
            
            {/* Selected Tables List */}
            <div className="mb-4">
              <div className="flex flex-wrap gap-2">
                {comparisonTables.map((tableId) => {
                  const table = tables.find(t => t.id === tableId);
                  return (
                    <span
                      key={tableId}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                    >
                      {table?.name}
                      <button
                        onClick={() => handleToggleComparison(tableId)}
                        className="ml-2 text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </span>
                  );
                })}
              </div>
            </div>

            {/* Comparison Chart */}
            {comparisonLoading ? (
              <div className="flex items-center justify-center h-96 bg-white rounded-lg border border-gray-200">
                <div className="text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600">Carregando dados para comparação...</p>
                </div>
              </div>
            ) : comparisonData.length > 0 ? (
              <MortalityComparisonChart 
                tables={comparisonData}
                title={`Comparação de ${comparisonData.length} Tábuas de ${comparisonChartType === 'survival' ? 'Sobrevivência' : 'Mortalidade'}`}
                chartType={comparisonChartType}
              />
            ) : (
              <div className="flex items-center justify-center h-96 bg-white rounded-lg border border-gray-200">
                <div className="text-center">
                  <BarChart3 className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Carregando dados...</h4>
                  <p className="text-gray-600">
                    Os gráficos de comparação estão sendo carregados.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <TrendingUp className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Selecione uma Tábua para Análise</h3>
          <p className="text-gray-600">
            Use o botão "Analisar" no dashboard para visualizar estatísticas e gráficos de uma tábua específica.
          </p>
        </div>
      )}
    </div>
  );

  const renderPlaceholder = (title: string, description: string, icon: React.ReactNode) => (
    <div className="text-center py-12">
      <div className="text-gray-300 mb-4">{icon}</div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );

  return (
    <>
      {/* Backdrop + Modal Container */}
      <div
        className="fixed inset-0 bg-gray-900/80 backdrop-blur-sm z-[9998] transition-opacity duration-200 flex items-center justify-center p-8"
        onClick={onClose}
        aria-hidden="true"
      >
        <div
          className="bg-white rounded-xl shadow-2xl max-w-7xl w-full max-h-[85vh] overflow-hidden flex flex-col transform transition-all duration-200 ease-out"
          onClick={(e) => e.stopPropagation()}
          style={{
            backgroundColor: 'rgb(255, 255, 255)',
          }}
        >
          {/* Header - Sticky */}
          <div className="sticky top-0 z-20 flex items-center justify-between p-6 border-b border-gray-200 bg-white rounded-t-xl shadow-sm">
            <div className="flex items-center gap-4">
              {/* Mobile Menu Button */}
              <button
                onClick={() => setSidebarOpen(true)}
                className="md:hidden p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Abrir menu"
              >
                <Menu className="h-5 w-5" />
              </button>
              
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Gerenciamento de Tábuas de Mortalidade</h2>
                <p className="text-sm text-gray-600 mt-1">Upload, análise e configuração de tábuas</p>
              </div>
            </div>
            
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg p-2 transition-colors duration-150"
              aria-label="Fechar (ESC)"
              title="Fechar (ESC)"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex flex-1 overflow-hidden">
            {/* Desktop Sidebar - Hidden on mobile */}
            <aside className="hidden md:block w-64 shrink-0 border-r border-gray-200 bg-gray-50">
              <div className="sticky top-0 h-[calc(100vh-120px)] overflow-y-auto p-4">
                <NavigationMenu />
              </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto bg-white">
              <div className="p-6">
                {activeView === 'dashboard' && renderDashboard()}
                {activeView === 'search' && renderSearch()}
                {activeView === 'upload' && (
                  <UploadCSVForm onUpload={handleUpload} loading={uploadLoading} />
                )}
                {activeView === 'analysis' && renderAnalysis()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {sidebarOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/40 z-[9999] md:hidden" 
            onClick={() => setSidebarOpen(false)}
          />
          
          {/* Drawer Panel */}
          <div className={cn(
            "fixed inset-y-0 left-0 w-64 bg-white z-[10000] transform transition-transform duration-300 ease-out md:hidden shadow-xl",
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          )}>
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="font-medium text-gray-900">Navegação</h3>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <div className="p-4">
              <NavigationMenu />
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default MortalityTablesManager;