import React, { useState } from 'react';
import { Database, Upload, FileUp } from 'lucide-react';
import PymortTablesList from './PymortTablesList';
import UploadCSVForm from './UploadCSVForm';

interface AddTableViewProps {
  onLoadFromPymort: (tableId: number) => Promise<void>;
  onUploadCSV: (file: File, metadata: {
    name: string;
    description: string;
    country: string;
    gender: string;
  }) => Promise<void>;
  loadingTableId: number | null;
  uploadLoading: boolean;
  installedPymortIds?: number[];
}

const AddTableView: React.FC<AddTableViewProps> = ({
  onLoadFromPymort,
  onUploadCSV,
  loadingTableId,
  uploadLoading,
  installedPymortIds = []
}) => {
  const [activeTab, setActiveTab] = useState<'pymort' | 'csv'>('pymort');

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
            className={`group inline-flex items-center py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'pymort'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Database className={`mr-2 h-5 w-5 ${
              activeTab === 'pymort' ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'
            }`} />
            Catálogo SOA
          </button>

          <button
            onClick={() => setActiveTab('csv')}
            className={`group inline-flex items-center py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'csv'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FileUp className={`mr-2 h-5 w-5 ${
              activeTab === 'csv' ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-500'
            }`} />
            Upload CSV Personalizado
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="mt-6">
        {activeTab === 'pymort' ? (
          <PymortTablesList
            onLoadTable={onLoadFromPymort}
            loadingTableId={loadingTableId}
            installedTableIds={installedPymortIds}
          />
        ) : (
          <UploadCSVForm
            onUpload={onUploadCSV}
            loading={uploadLoading}
          />
        )}
      </div>
    </div>
  );
};

export default AddTableView;
