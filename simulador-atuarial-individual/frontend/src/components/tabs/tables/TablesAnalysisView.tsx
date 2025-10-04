import React, { useState, useEffect } from 'react';
import { Card, CardContent, Input, Badge, Button, useToast } from '../../../design-system/components';
import { useMortalityTables } from '../../admin/hooks/useMortalityTables';
import { MortalityMainChart, MortalityComparisonChart } from '../../admin/charts';
import type { TableStatistics } from '../../admin/hooks/useMortalityTables';
import MortalityTableSelector from '../../selectors/MortalityTableSelector';

type ChartType = 'mortality' | 'survival' | 'life_expectancy' | 'deaths';

const TablesAnalysisView: React.FC = () => {
  // Estados principais
  const [selectedTableCode, setSelectedTableCode] = useState<string>('');
  const [comparisonTables, setComparisonTables] = useState<string[]>([]);
  const [chartType, setChartType] = useState<ChartType>('mortality');
  const [filterText, setFilterText] = useState<string>('');
  const [showTableMenu, setShowTableMenu] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const { showToast } = useToast();
  const MAX_COMPARISONS = 5;

  // Estados para dados da análise
  const [selectedTableStats, setSelectedTableStats] = useState<TableStatistics | null>(null);
  const [selectedTableData, setSelectedTableData] = useState<Array<{ age: number; qx: number }> | null>(null);
  const [comparisonData, setComparisonData] = useState<Array<{
    name: string;
    data: Array<{ age: number; qx: number }>;
    color: string;
  }>>([]);

  // Hook para funcionalidades admin
  const {
    tables: adminTables,
    loading,
    getTableStatistics,
    getTableMortalityData,
    toggleTableActive,
    deleteTable
  } = useMortalityTables();

  // Inicializar com primeira tábua disponível
  useEffect(() => {
    if (adminTables.length > 0 && !selectedTableCode) {
      setSelectedTableCode(adminTables[0].code);
    }
  }, [adminTables, selectedTableCode]);

  // Carregar dados quando tábua principal muda
  useEffect(() => {
    if (selectedTableCode) {
      loadTableData(selectedTableCode);
    }
  }, [selectedTableCode, adminTables]);

  // Recarregar dados de comparação quando lista muda
  useEffect(() => {
    if (comparisonTables.length > 0) {
      loadComparisonData();
    } else {
      setComparisonData([]);
    }
  }, [comparisonTables, adminTables]);

  // Fechar menu quando clicar fora
  useEffect(() => {
    const handleClickOutside = () => setShowTableMenu(false);
    if (showTableMenu) {
      const timeoutId = setTimeout(() => {
        document.addEventListener('click', handleClickOutside);
      }, 0);

      return () => {
        clearTimeout(timeoutId);
        document.removeEventListener('click', handleClickOutside);
      };
    }
  }, [showTableMenu]);

  const findTableById = (code: string) => {
    let table = adminTables.find(t => t.code === code);
    if (!table) {
      table = adminTables.find(t => t.code.startsWith(code + '_'));
    }
    return table;
  };

  const getGenderLabel = (gender: string) => {
    if (gender === 'M' || gender === 'male') return 'Masculino';
    if (gender === 'F' || gender === 'female') return 'Feminino';
    return gender || 'Unissex';
  };

  const getGenderColor = (gender: string) => {
    if (gender === 'M' || gender === 'male') return '#3B82F6';
    if (gender === 'F' || gender === 'female') return '#EC4899';
    return '#6B7280';
  };

  const getUniqueColor = (index: number) => {
    const chartJsColors = [
      'rgb(255, 99, 132)',
      'rgb(54, 162, 235)',
      'rgb(255, 205, 86)',
      'rgb(75, 192, 192)',
      'rgb(153, 102, 255)',
      'rgb(255, 159, 64)',
      'rgb(199, 199, 199)',
      'rgb(83, 102, 255)',
      'rgb(255, 99, 255)',
      'rgb(99, 255, 132)',
      'rgb(255, 206, 84)',
      'rgb(75, 192, 255)',
    ];
    return chartJsColors[index % chartJsColors.length];
  };

  const loadTableData = async (code: string) => {
    const table = findTableById(code);
    if (!table) return;

    try {
      const stats = await getTableStatistics(table.id);
      const response = await getTableMortalityData(table.id);
      setSelectedTableStats(stats);
      setSelectedTableData(response?.data || null);
    } catch (error) {
      console.error('Erro ao carregar dados da tábua:', error);
    }
  };

  const loadComparisonData = async () => {
    const data = await Promise.all(
      comparisonTables.map(async (code, index) => {
        const table = findTableById(code);
        if (table) {
          const response = await getTableMortalityData(table.id);
          return {
            name: `${code} (${getGenderLabel(table.gender)})`,
            data: response?.data || [],
            color: getUniqueColor(index)
          };
        }
        return null;
      })
    );
    setComparisonData(data.filter(Boolean) as any);
  };

  const handleToggleComparison = (tableCode: string, checked: boolean) => {
    if (checked) {
      if (comparisonTables.includes(tableCode)) return;
      if (comparisonTables.length >= MAX_COMPARISONS) {
        showToast({ title: `Máximo de ${MAX_COMPARISONS} tábuas para comparação`, variant: 'warning' });
        return;
      }
      setComparisonTables([...comparisonTables, tableCode]);
    } else {
      setComparisonTables(comparisonTables.filter(c => c !== tableCode));
    }
  };

  const handleToggleTableActive = async () => {
    const table = findTableById(selectedTableCode);
    if (!table) return;

    try {
      setActionLoading(true);
      await toggleTableActive(table.id);
      showToast({
        title: `Tábua ${table.is_active ? 'desativada' : 'ativada'} com sucesso!`,
        variant: 'success'
      });
    } catch (error: any) {
      showToast({
        title: 'Erro ao alterar status da tábua',
        description: error.message,
        variant: 'error'
      });
    } finally {
      setActionLoading(false);
      setShowTableMenu(false);
    }
  };

  const handleDeleteTable = async () => {
    const table = findTableById(selectedTableCode);
    if (!table) return;

    if (!confirm(`Tem certeza que deseja excluir a tábua "${table.name}"? Esta ação não pode ser desfeita.`)) {
      return;
    }

    try {
      setActionLoading(true);
      await deleteTable(table.id);
      showToast({
        title: 'Tábua excluída com sucesso!',
        variant: 'success'
      });

      const remainingTables = adminTables.filter(t => t.id !== table.id);
      if (remainingTables.length > 0) {
        setSelectedTableCode(remainingTables[0].code);
      } else {
        setSelectedTableCode('');
      }
    } catch (error: any) {
      showToast({
        title: 'Erro ao excluir tábua',
        description: error.message,
        variant: 'error'
      });
    } finally {
      setActionLoading(false);
      setShowTableMenu(false);
    }
  };

  const showComparisonChart = comparisonData.length > 0 && selectedTableData;
  const allComparisonData = showComparisonChart ? [
    {
      name: `${selectedTableCode} (${getGenderLabel(findTableById(selectedTableCode)?.gender || '')})`,
      data: selectedTableData!,
      color: getUniqueColor(0)
    },
    ...comparisonData.map((item, index) => ({
      ...item,
      color: getUniqueColor(index + 1)
    }))
  ] : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      {/* Sidebar - Controles */}
      <div className="lg:col-span-1">
        <Card>
          <CardContent className="p-4">
            {/* Seleção da Tábua Principal */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tábua Principal
              </label>
              <div className="flex items-center gap-2">
                <div className="flex-1">
                  <MortalityTableSelector
                    value={selectedTableCode}
                    mortalityTables={adminTables}
                    onChange={setSelectedTableCode}
                    disabled={loading}
                  />
                </div>

                {/* Menu de ações da tábua */}
                {selectedTableCode && (
                  <div className="relative">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowTableMenu(!showTableMenu);
                      }}
                      disabled={actionLoading}
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                      title="Opções da tábua"
                    >
                      <span className="material-icons" style={{ fontSize: '16px' }}>more_vert</span>
                    </button>

                    {showTableMenu && (
                      <div
                        className="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          onClick={handleToggleTableActive}
                          disabled={actionLoading}
                          className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2 disabled:opacity-50"
                        >
                          <span className={`material-icons ${findTableById(selectedTableCode)?.is_active ? 'text-orange-500' : 'text-green-500'}`} style={{ fontSize: '16px' }}>
                            power_settings_new
                          </span>
                          {findTableById(selectedTableCode)?.is_active ? 'Desativar' : 'Ativar'}
                        </button>

                        {!findTableById(selectedTableCode)?.is_system && (
                          <button
                            onClick={handleDeleteTable}
                            disabled={actionLoading}
                            className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 disabled:opacity-50"
                          >
                            <span className="material-icons text-red-500" style={{ fontSize: '16px' }}>delete</span>
                            Excluir
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Comparação */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Comparar com ({comparisonTables.length}/{MAX_COMPARISONS})
              </label>
              {comparisonTables.length > 0 && (
                <div className="flex items-start justify-between mb-2">
                  <div className="flex flex-wrap gap-2">
                    {comparisonTables.map((code) => {
                      const t = findTableById(code);
                      const label = t ? `${code} (${getGenderLabel(t.gender || '')})` : code;
                      return (
                        <Badge
                          key={code}
                          interactive
                          className="select-none"
                          rightIcon={<span className="material-icons" style={{ fontSize: '12px' }}>close</span>}
                          onClick={() => handleToggleComparison(code, false)}
                        >
                          {label}
                        </Badge>
                      );
                    })}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setComparisonTables([])}
                  >
                    Limpar
                  </Button>
                </div>
              )}

              {/* Busca */}
              <div className="mb-2">
                <Input
                  placeholder="Buscar por código, nome ou gênero"
                  value={filterText}
                  onChange={(e) => setFilterText(e.target.value)}
                />
              </div>

              {/* Lista filtrada */}
              <div className="space-y-1 max-h-64 overflow-y-auto">
                {filterText.trim() === '' ? (
                  <p className="text-xs text-gray-500 py-2">Digite para buscar tábuas…</p>
                ) : (
                  adminTables
                    .filter((table) => table.code !== selectedTableCode)
                    .filter((table) => {
                      const q = filterText.trim().toLowerCase();
                      const genderLabel = getGenderLabel(table.gender || '').toLowerCase();
                      const code = table.code.toLowerCase();
                      const name = (table.name || '').toLowerCase();
                      return code.includes(q) || name.includes(q) || genderLabel.includes(q);
                    })
                    .map((table) => {
                      const genderLabel = getGenderLabel(table.gender || '');
                      const genderColor = getGenderColor(table.gender || '');
                      const isSelected = comparisonTables.includes(table.code);
                      const disabledAdd = !isSelected && comparisonTables.length >= MAX_COMPARISONS;

                      return (
                        <button
                          key={table.code}
                          onClick={() => !disabledAdd && handleToggleComparison(table.code, !isSelected)}
                          className={`flex items-center gap-2 w-full p-2 rounded-lg text-left transition-colors ${
                            isSelected
                              ? 'bg-blue-50 border border-blue-200 text-blue-900'
                              : disabledAdd
                                ? 'border border-transparent opacity-50 cursor-not-allowed'
                                : 'border border-transparent'
                          }`}
                          aria-disabled={disabledAdd}
                        >
                          <div
                            className="w-3 h-3 rounded-full flex-shrink-0"
                            style={{ backgroundColor: genderColor }}
                          />
                          <div className="flex-1 min-w-0">
                            <span className="font-medium text-sm">
                              {table.code} ({genderLabel})
                            </span>
                          </div>
                          {isSelected && (
                            <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0" />
                          )}
                        </button>
                      );
                    })
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Área Principal - Gráficos */}
      <div className="lg:col-span-3">
        {selectedTableData ? (
          <Card>
            <CardContent className="p-0">
              {/* Seletor de tipo de gráfico integrado */}
              <div className="flex border-b border-gray-200 overflow-x-auto">
                <button
                  onClick={() => setChartType('mortality')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    chartType === 'mortality'
                      ? 'border-blue-600 text-blue-600 bg-blue-50'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Taxa de Mortalidade (qx)
                </button>
                <button
                  onClick={() => setChartType('survival')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    chartType === 'survival'
                      ? 'border-blue-600 text-blue-600 bg-blue-50'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Curva de Sobrevivência (lx)
                </button>
                <button
                  onClick={() => setChartType('life_expectancy')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    chartType === 'life_expectancy'
                      ? 'border-blue-600 text-blue-600 bg-blue-50'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Expectativa de Vida (êx)
                </button>
                <button
                  onClick={() => setChartType('deaths')}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    chartType === 'deaths'
                      ? 'border-blue-600 text-blue-600 bg-blue-50'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  Número de Mortes (dx)
                </button>
              </div>

              {/* Área do Gráfico */}
              <div className="p-4">
                {showComparisonChart ? (
                  <MortalityComparisonChart
                    tables={allComparisonData}
                    chartType={chartType}
                    title=""
                  />
                ) : (
                  <MortalityMainChart
                    data={selectedTableData}
                    tableName={selectedTableCode}
                    chartType={chartType}
                  />
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          !loading && (
            <div className="text-center py-12 text-gray-500">
              <span className="material-icons text-gray-300 mx-auto mb-4" style={{ fontSize: '48px' }}>insights</span>
              <p>Selecione uma tábua para visualizar os dados</p>
            </div>
          )
        )}

        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-4 text-gray-600">Carregando dados...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TablesAnalysisView;
