import React, { useState, useEffect } from 'react';
import { useMortalityTables } from '../../admin/hooks/useMortalityTables';
import type { MortalityTableAdmin } from '../../admin/hooks/useMortalityTables';
import { Tooltip } from '../../../design-system/components/Tooltip';

const TablesManageView: React.FC = () => {
  const {
    tables,
    loading,
    error,
    toggleTableActive,
    deleteTable
  } = useMortalityTables();

  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [openDropdown, setOpenDropdown] = useState<number | null>(null);

  // Filtrar tábuas
  const filteredTables = tables.filter((table) => {
    const query = searchQuery.toLowerCase();
    return (
      table.name.toLowerCase().includes(query) ||
      table.code.toLowerCase().includes(query) ||
      table.source.toLowerCase().includes(query)
    );
  });

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openDropdown !== null) {
        setOpenDropdown(null);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [openDropdown]);

  const toggleDropdown = (tableId: number) => {
    setOpenDropdown(openDropdown === tableId ? null : tableId);
  };

  const handleToggleActive = async (tableId: number) => {
    try {
      setActionLoading(tableId);
      await toggleTableActive(tableId);
    } catch (err: any) {
      alert(`Erro ao alterar status: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (tableId: number, tableName: string) => {
    if (!confirm(`Tem certeza que deseja excluir a tábua "${tableName}"? Esta ação não pode ser desfeita.`)) {
      return;
    }

    try {
      setActionLoading(tableId);
      await deleteTable(tableId);
      alert('Tábua excluída com sucesso!');
    } catch (err: any) {
      alert(`Erro ao excluir tábua: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Busca */}
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
        <div className="text-sm text-gray-600">
          {filteredTables.length} {filteredTables.length === 1 ? 'tábua' : 'tábuas'}
        </div>
      </div>

      {/* Lista de Tábuas */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-gray-600">Carregando tábuas...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8">
            <p className="text-red-600">{error}</p>
          </div>
        ) : filteredTables.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Nenhuma tábua encontrada</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nome
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredTables.map((table) => (
                <tr
                  key={table.id}
                  className={`hover:bg-gray-50 transition-colors ${
                    table.is_active ? 'bg-green-50' : ''
                  }`}
                >
                  {/* Nome com Tooltip */}
                  <td className="px-4 py-3">
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
                  <td className="px-4 py-3 text-center">
                    {table.is_active ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Ativa
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                        Inativa
                      </span>
                    )}
                  </td>

                  {/* Ações - Menu Dropdown */}
                  <td className="px-4 py-3 text-center relative">
                    <div className="relative inline-block">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleDropdown(table.id);
                        }}
                        className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                        title="Mais ações"
                      >
                        <span className="material-icons text-gray-400" style={{ fontSize: '16px' }}>more_horiz</span>
                      </button>

                      {openDropdown === table.id && (
                        <div className="absolute right-0 mt-1 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleToggleActive(table.id);
                              setOpenDropdown(null);
                            }}
                            disabled={actionLoading === table.id}
                            className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                          >
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
                              className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                            >
                              Excluir
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default TablesManageView;
