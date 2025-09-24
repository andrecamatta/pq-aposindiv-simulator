import React, { useState, useRef } from 'react';
import { Upload, FileText, AlertCircle, X, Loader2 } from 'lucide-react';

interface UploadCSVFormProps {
  onUpload: (file: File, metadata: {
    name: string;
    description: string;
    country: string;
    gender: string;
  }) => Promise<void>;
  loading?: boolean;
}

const UploadCSVForm: React.FC<UploadCSVFormProps> = ({ onUpload, loading = false }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    country: 'Brasil',
    gender: 'unissex'
  });
  const [previewData, setPreviewData] = useState<string[][] | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Validar arquivo CSV
  const validateFile = (file: File): string[] => {
    const errors: string[] = [];
    
    if (!file.name.toLowerCase().endsWith('.csv')) {
      errors.push('Arquivo deve ter extensão .csv');
    }
    
    if (file.size > 5 * 1024 * 1024) { // 5MB
      errors.push('Arquivo deve ter no máximo 5MB');
    }
    
    return errors;
  };

  // Ler preview do arquivo CSV
  const readFilePreview = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n').slice(0, 6); // Primeiras 6 linhas
      const csvData = lines.map(line => 
        line.split(',').map(cell => cell.trim().replace(/"/g, ''))
      );
      setPreviewData(csvData.filter(row => row.some(cell => cell.length > 0)));
    };
    reader.readAsText(file);
  };

  // Handle file selection
  const handleFileSelect = (file: File) => {
    const fileErrors = validateFile(file);
    setErrors(fileErrors);
    
    if (fileErrors.length === 0) {
      setSelectedFile(file);
      readFilePreview(file);
      
      // Auto-preencher nome se não foi definido
      if (!formData.name) {
        const fileName = file.name.replace('.csv', '');
        setFormData(prev => ({ ...prev, name: fileName }));
      }
    }
  };

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile || errors.length > 0) {
      return;
    }

    if (!formData.name.trim()) {
      setErrors(['Nome da tábua é obrigatório']);
      return;
    }

    try {
      await onUpload(selectedFile, formData);
      
      // Reset form
      setSelectedFile(null);
      setPreviewData(null);
      setFormData({
        name: '',
        description: '',
        country: 'Brasil',
        gender: 'unissex'
      });
      setErrors([]);
      
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err: any) {
      setErrors([err.message || 'Erro no upload']);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setPreviewData(null);
    setErrors([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Upload de Tábua CSV</h3>
        <p className="text-sm text-gray-600 mb-4">
          Faça upload de um arquivo CSV contendo dados de mortalidade. 
          O arquivo deve conter colunas 'age' e 'qx'.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Upload Area */}
        <div
          className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
            dragActive
              ? 'border-blue-400 bg-blue-50'
              : selectedFile
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />

          {selectedFile ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="h-8 w-8 text-green-600" />
                <div>
                  <p className="font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={removeFile}
                className="p-1 hover:bg-white rounded-full transition-colors"
              >
                <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
          ) : (
            <div className="text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-900">
                  Arraste um arquivo CSV aqui ou clique para selecionar
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Máximo 5MB • Apenas arquivos .csv
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Errors */}
        {errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
              <h4 className="text-sm font-medium text-red-800">Erros encontrados:</h4>
            </div>
            <ul className="mt-2 text-sm text-red-700">
              {errors.map((error, index) => (
                <li key={index}>• {error}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Preview */}
        {previewData && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Preview dos dados:</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <tbody>
                  {previewData.map((row, index) => (
                    <tr key={index} className={index === 0 ? 'font-medium bg-gray-100' : ''}>
                      {row.map((cell, cellIndex) => (
                        <td key={cellIndex} className="px-2 py-1 border-r border-gray-200">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Mostrando apenas as primeiras linhas do arquivo
            </p>
          </div>
        )}

        {/* Metadata Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome da Tábua *
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Ex: IBGE 2020 Unissex"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              País
            </label>
            <input
              type="text"
              value={formData.country}
              onChange={(e) => setFormData(prev => ({ ...prev, country: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Gênero
            </label>
            <select
              value={formData.gender}
              onChange={(e) => setFormData(prev => ({ ...prev, gender: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="unissex">Unissex</option>
              <option value="masculino">Masculino</option>
              <option value="feminino">Feminino</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrição
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="Descrição opcional da tábua de mortalidade"
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!selectedFile || errors.length > 0 || loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            {loading ? 'Enviando...' : 'Fazer Upload'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default UploadCSVForm;