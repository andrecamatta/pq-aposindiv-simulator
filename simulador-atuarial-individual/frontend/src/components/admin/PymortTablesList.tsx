import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';

interface PymortTable {
  id: number;
  name: string;
  description: string;
  category: string;
  gender: string;
  year: number | null;
}

interface PymortTablesListProps {
  onLoadTable: (tableId: number) => Promise<void>;
  loadingTableId: number | null;
  installedTableIds?: number[];
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const PymortTablesList: React.FC<PymortTablesListProps> = ({
  onLoadTable,
  loadingTableId,
  installedTableIds = []
}) => {
  const [tables, setTables] = useState<PymortTable[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [categories, setCategories] = useState<{value: string, label: string}[]>([]);

  // Paginação
  const [currentPage, setCurrentPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const itemsPerPage = 50;

  // Carregar categorias
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/mortality-tables/pymort-categories/`);
        setCategories(response.data.categories);
      } catch (error) {
        console.error('Erro ao carregar categorias:', error);
      }
    };
    fetchCategories();
  }, []);

  // Carregar tábuas
  useEffect(() => {
    const fetchTables = async () => {
      setLoading(true);
      try {
        const offset = (currentPage - 1) * itemsPerPage;
        const params = new URLSearchParams({
          offset: offset.toString(),
          limit: itemsPerPage.toString(),
        });

        if (searchQuery) params.append('search', searchQuery);
        if (selectedCategory && selectedCategory !== 'all') params.append('category', selectedCategory);

        const response = await axios.get(
          `${API_BASE_URL}/api/mortality-tables/pymort-tables/?${params}`
        );

        setTables(response.data.tables);
        setTotal(response.data.total);
        setHasMore(response.data.has_more);
      } catch (error) {
        console.error('Erro ao carregar tábuas:', error);
        setTables([]);
      } finally {
        setLoading(false);
      }
    };

    // Debounce na busca
    const timer = setTimeout(() => {
      fetchTables();
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, selectedCategory, currentPage]);

  const isInstalled = (tableId: number) => installedTableIds.includes(tableId);
  const totalPages = Math.ceil(total / itemsPerPage);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  return (
    <div className="space-y-4">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" aria-hidden="true" />
          <input
            type="text"
            placeholder="Buscar por nome ou descrição..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full rounded-lg border border-gray-300 py-2 pl-11 pr-4 focus:border-transparent focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <select
          value={selectedCategory}
          onChange={(e) => {
            setSelectedCategory(e.target.value);
            setCurrentPage(1);
          }}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {categories.map(cat => (
            <option key={cat.value} value={cat.value}>{cat.label}</option>
          ))}
        </select>
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        {loading ? 'Carregando...' : `${total} tábua${total !== 1 ? 's' : ''} encontrada${total !== 1 ? 's' : ''}`}
      </div>

      {/* Compact Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoria</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Gênero</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ano</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ação</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto"></div>
                </td></tr>
              ) : tables.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Nenhuma tábua encontrada</td></tr>
              ) : (
                tables.map((table) => {
                  const installed = isInstalled(table.id);
                  const isLoading = loadingTableId === table.id;
                  return (
                    <tr key={table.id} className={`hover:bg-gray-50 transition-colors ${installed ? 'bg-green-50' : ''}`} title={table.description}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{table.id}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <div className="max-w-md">
                          <div className="font-medium truncate">{table.name}</div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">{table.category}</span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{table.gender || 'N/A'}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{table.year || '-'}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                        <button
                          onClick={() => onLoadTable(table.id)}
                          disabled={isLoading || installed}
                          className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                            installed ? 'bg-green-100 text-green-700 cursor-not-allowed' :
                            isLoading ? 'bg-blue-100 text-blue-600 cursor-wait' :
                            'bg-blue-600 text-white hover:bg-blue-700'
                          }`}
                        >
                          {isLoading ? 'Carregando...' : installed ? 'Instalada' : 'Carregar'}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 bg-white border border-gray-200 rounded-lg">
          <div className="flex-1 flex justify-between sm:hidden">
            <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Anterior</button>
            <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">Próxima</button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Mostrando <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span> até{' '}
                <span className="font-medium">{Math.min(currentPage * itemsPerPage, total)}</span> de <span className="font-medium">{total}</span> resultados
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                </button>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) pageNum = i + 1;
                  else if (currentPage <= 3) pageNum = i + 1;
                  else if (currentPage >= totalPages - 2) pageNum = totalPages - 4 + i;
                  else pageNum = currentPage - 2 + i;
                  return (
                    <button key={pageNum} onClick={() => handlePageChange(pageNum)}
                      className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                        currentPage === pageNum ? 'z-10 bg-blue-50 border-blue-500 text-blue-600' :
                        'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                      }`}>{pageNum}</button>
                  );
                })}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <ChevronRight className="h-5 w-5" aria-hidden="true" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PymortTablesList;
