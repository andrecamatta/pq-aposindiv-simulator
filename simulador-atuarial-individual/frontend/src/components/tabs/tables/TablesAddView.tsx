import React, { useState } from 'react';
import PymortTablesList from '../../admin/PymortTablesList';
import UploadCSVForm from '../../admin/UploadCSVForm';
import { useMortalityTables } from '../../admin/hooks/useMortalityTables';

const TablesAddView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'pymort' | 'csv'>('pymort');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  const {
    tables,
    loadFromPymort,
    uploadCSV
  } = useMortalityTables();

  // Filtrar tábuas pymort instaladas
  const installedPymortIds = tables
    .filter(t => t.source === 'pymort' && t.source_id)
    .map(t => parseInt(t.source_id));

  const handleLoadFromPymort = async (tableId: number) => {
    try {
      setActionLoading(tableId);
      await loadFromPymort(tableId);
      alert('Tábua carregada do pymort com sucesso!');
    } catch (err: any) {
      alert(`Erro ao carregar tábua: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Adicionar Nova Tábua de Mortalidade
        </h3>
        <p className="text-sm text-gray-600">
          Escolha entre carregar uma tábua do catálogo SOA ou fazer upload de um arquivo CSV personalizado.
        </p>
      </div>

      {/* Tab Selector */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex gap-8">
          <button
            onClick={() => setActiveTab('pymort')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'pymort'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Catálogo SOA
          </button>

          <button
            onClick={() => setActiveTab('csv')}
            className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'csv'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Upload CSV Personalizado
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="mt-6">
        {activeTab === 'pymort' ? (
          <PymortTablesList
            onLoadTable={handleLoadFromPymort}
            loadingTableId={actionLoading}
            installedTableIds={installedPymortIds}
          />
        ) : (
          <UploadCSVForm
            onUpload={handleUpload}
            loading={uploadLoading}
          />
        )}
      </div>
    </div>
  );
};

export default TablesAddView;
