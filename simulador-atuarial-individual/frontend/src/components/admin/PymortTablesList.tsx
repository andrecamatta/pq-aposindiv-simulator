import React, { useState } from 'react';
import { Database, Loader2, CheckCircle, Search } from 'lucide-react';

interface PymortTable {
  id: number;
  name: string;
  description: string;
  category: string;
}

interface PymortTablesListProps {
  onLoadTable: (tableId: number) => Promise<void>;
  loadingTableId: number | null;
  installedTableIds?: number[];
}

const PymortTablesList: React.FC<PymortTablesListProps> = ({
  onLoadTable,
  loadingTableId,
  installedTableIds = []
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  // Lista expandida de tábuas SOA conhecidas e funcionais
  const availableTables: PymortTable[] = [
    // Tábuas de Anuidades
    { id: 825, name: "1983 GAM Female", description: "1983 Group Annuity Mortality Table – Female", category: "Anuidades" },
    { id: 826, name: "1983 GAM Male", description: "1983 Group Annuity Mortality Table – Male", category: "Anuidades" },
    { id: 809, name: "1951 GAM Male", description: "1951 Group Annuity Mortality (GAM) Table – Male", category: "Anuidades" },
    { id: 810, name: "1951 GAM Female", description: "1951 Group Annuity Mortality (GAM) Table – Female", category: "Anuidades" },

    // Tábuas CSO (Commissioners Standard Ordinary)
    { id: 1, name: "1941 CSO Basic ANB", description: "1941 Commissioners Standard Ordinary Basic Table", category: "CSO" },
    { id: 2, name: "1941 CSO Experience ANB", description: "1941 Commissioners Standard Ordinary Experience Table", category: "CSO" },
    { id: 3, name: "1941 CSO Standard ANB", description: "1941 Commissioners Standard Ordinary Table", category: "CSO" },
    { id: 17, name: "1958 CSO ANB", description: "1958 Commissioners Standard Ordinary Table", category: "CSO" },
    { id: 20, name: "1980 CSO Basic Male ANB", description: "1980 Commissioners Standard Ordinary Basic Table - Male", category: "CSO" },
    { id: 21, name: "1980 CSO Basic Female ANB", description: "1980 Commissioners Standard Ordinary Basic Table - Female", category: "CSO" },

    // Tábuas VBT (Valuation Basic Table)
    { id: 3262, name: "2015 VBT Male Smoker", description: "2015 Valuation Basic Table - Male 100%, Smoker", category: "VBT" },

    // Tábuas UP (Ultimate Pension)
    { id: 1619, name: "UP-1984 Male", description: "1984 Uninsured Pensioner Mortality Table - Male", category: "Previdência" },
    { id: 1620, name: "UP-1984 Female", description: "1984 Uninsured Pensioner Mortality Table - Female", category: "Previdência" },

    // Tábuas RP (Retirement Plan)
    { id: 1478, name: "RP-2014 Employee Male", description: "RP-2014 Mortality Tables - Employee Male", category: "Previdência" },
    { id: 1479, name: "RP-2014 Employee Female", description: "RP-2014 Mortality Tables - Employee Female", category: "Previdência" },
    { id: 1487, name: "RP-2014 Healthy Annuitant Male", description: "RP-2014 Mortality Tables - Healthy Annuitant Male", category: "Previdência" },
    { id: 1488, name: "RP-2014 Healthy Annuitant Female", description: "RP-2014 Mortality Tables - Healthy Annuitant Female", category: "Previdência" },
  ];

  // Filtrar tábuas baseado na busca
  const filteredTables = availableTables.filter(table =>
    table.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    table.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    table.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Agrupar por categoria
  const tablesByCategory = filteredTables.reduce((acc, table) => {
    if (!acc[table.category]) {
      acc[table.category] = [];
    }
    acc[table.category].push(table);
    return acc;
  }, {} as Record<string, PymortTable[]>);

  const isInstalled = (tableId: number) => installedTableIds.includes(tableId);

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Buscar por nome, descrição ou categoria..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Info Header */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <Database className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-medium text-blue-900 mb-1">
              Catálogo pymort (Society of Actuaries)
            </h4>
            <p className="text-sm text-blue-700">
              Tábuas de mortalidade oficiais da SOA. Clique em "Carregar" para adicionar ao seu projeto.
              O carregamento é feito em background e leva alguns segundos.
            </p>
          </div>
        </div>
      </div>

      {/* Tables by Category */}
      {Object.keys(tablesByCategory).length === 0 ? (
        <div className="text-center py-12">
          <Search className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Nenhuma tábua encontrada com "{searchQuery}"</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(tablesByCategory).map(([category, tables]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3 flex items-center gap-2">
                <span className="h-px flex-1 bg-gray-300"></span>
                <span>{category}</span>
                <span className="h-px flex-1 bg-gray-300"></span>
              </h3>

              <div className="grid grid-cols-1 gap-3">
                {tables.map((table) => {
                  const installed = isInstalled(table.id);
                  const isLoading = loadingTableId === table.id;

                  return (
                    <div
                      key={table.id}
                      className={`border rounded-lg p-4 transition-all ${
                        installed
                          ? 'bg-green-50 border-green-300'
                          : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-sm'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium text-gray-900 text-sm">
                              {table.name}
                            </h4>
                            {installed && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Instalada
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 truncate">
                            {table.description}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            ID: {table.id}
                          </p>
                        </div>

                        <button
                          onClick={() => onLoadTable(table.id)}
                          disabled={isLoading || installed}
                          className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center gap-2 whitespace-nowrap ${
                            installed
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : isLoading
                              ? 'bg-blue-100 text-blue-600 cursor-wait'
                              : 'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          {isLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Carregando...
                            </>
                          ) : installed ? (
                            <>
                              <CheckCircle className="h-4 w-4" />
                              Instalada
                            </>
                          ) : (
                            <>
                              <Database className="h-4 w-4" />
                              Carregar
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PymortTablesList;
