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
  MoreHorizontal
} from 'lucide-react';
import { useMortalityTables } from './hooks/useMortalityTables';
import type { MortalityTableAdmin, TableStatistics } from './hooks/useMortalityTables';
import { MortalityMainChart, StatisticsPanel, MortalityComparisonChart } from './charts';
import { Tooltip } from '../../design-system/components/Tooltip';
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
  
  // Estado para dropdown de ações
  const [openDropdown, setOpenDropdown] = useState<number | null>(null);

  // useEffect para limpar dados quando não há tábuas selecionadas
  useEffect(() => {
    if (analysisView === 'comparison' && comparisonTables.length === 0) {
      setComparisonData([]);
    }
  }, [comparisonTables, analysisView]);

  // Fechar modal com Escape
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

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
      <div className="max-h-96 overflow-y-auto">
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
                              <div className="space-y-2 text-xs">
                                <div>
                                  <span className="font-semibold">Código:</span>
                                  <span className="ml-2 font-mono">{table.code}</span>
                                </div>
                                <div>
                                  <span className="font-semibold">Fonte:</span>
                                  <span className="ml-2">{table.source}</span>
                                </div>
                                <div>
                                  <span className="font-semibold">Gênero:</span>
                                  <span className="ml-2">{table.gender}</span>
                                </div>
                                <div>
                                  <span className="font-semibold">País:</span>
                                  <span className="ml-2">{table.country || 'N/A'}</span>
                                </div>
                                {table.description && (
                                  <div>
                                    <span className="font-semibold">Descrição:</span>
                                    <div className="mt-1">{table.description}</div>
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
                            className="max-w-sm"
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
                        <td className="px-3 py-2 text-center">
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
                              <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
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
        className="fixed inset-0 bg-gray-900/80 backdrop-blur-sm z-[9998] transition-opacity duration-200 flex items-center justify-center p-4"
        onClick={onClose}
        aria-hidden="true"
      >
        <div
          className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col transform transition-all duration-200 ease-out"
          onClick={(e) => e.stopPropagation()}
          style={{
            backgroundColor: 'rgb(255, 255, 255)',
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-white rounded-t-xl shadow-sm">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Gerenciamento de Tábuas de Mortalidade</h2>
              <p className="text-sm text-gray-600 mt-1">Upload, análise e configuração de tábuas</p>
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
            {/* Sidebar */}
            <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
              <nav className="space-y-2">
                <button
                  onClick={() => setActiveView('dashboard')}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-150 ${
                    activeView === 'dashboard' 
                      ? 'bg-blue-100 text-blue-700 shadow-sm' 
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Database className="h-4 w-4" />
                  <span className="font-medium">Dashboard</span>
                </button>
                
                <button
                  onClick={() => setActiveView('search')}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-150 ${
                    activeView === 'search' 
                      ? 'bg-blue-100 text-blue-700 shadow-sm' 
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Search className="h-4 w-4" />
                  <span className="font-medium">Buscar SOA</span>
                </button>
                
                <button
                  onClick={() => setActiveView('upload')}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-150 ${
                    activeView === 'upload' 
                      ? 'bg-blue-100 text-blue-700 shadow-sm' 
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Upload className="h-4 w-4" />
                  <span className="font-medium">Upload CSV</span>
                </button>
                
                <button
                  onClick={() => setActiveView('analysis')}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-150 ${
                    activeView === 'analysis' 
                      ? 'bg-blue-100 text-blue-700 shadow-sm' 
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <BarChart3 className="h-4 w-4" />
                  <span className="font-medium">Análises</span>
                </button>
              </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 p-6 overflow-y-auto bg-white">
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
    </>
  );
};

export default MortalityTablesManager;