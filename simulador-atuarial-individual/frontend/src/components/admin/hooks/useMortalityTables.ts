import { useState, useEffect } from 'react';
import axios from 'axios';

export interface MortalityTableAdmin {
  id: number;
  name: string;
  code: string;
  description?: string;
  country?: string;
  year?: number;
  gender: string;
  source: string;
  source_id?: string;
  version?: string;
  is_official: boolean;
  regulatory_approved: boolean;
  is_active: boolean;
  is_system: boolean;
  last_loaded?: string;
  created_at: string;
  metadata?: any;
}

export interface TableStatistics {
  success: boolean;
  table_info: {
    id: number;
    name: string;
    code: string;
    gender: string;
  };
  statistics: {
    basic_stats: {
      records_count: number;
      age_range: { min: number; max: number };
      qx_stats: {
        min: number;
        max: number;
        mean: number;
        median: number;
        std: number;
      };
    };
    age_groups: {
      young: { ages: string; avg_qx: number };
      adult: { ages: string; avg_qx: number };
      elderly: { ages: string; avg_qx: number };
    };
    percentiles: {
      p25: number;
      p50: number;
      p75: number;
      p90: number;
      p95: number;
    };
  };
}

export interface PymortSearchResult {
  success: boolean;
  query: string;
  results: Array<{
    id: number;
    name: string;
    description: string;
  }>;
  total_found: number;
}

export const useMortalityTables = () => {
  const [tables, setTables] = useState<MortalityTableAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000/api/mortality-tables';

  // Carregar todas as tábuas
  const fetchTables = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get<MortalityTableAdmin[]>(`${API_BASE}/`);
      setTables(response.data);
    } catch (err: any) {
      console.error('Erro ao carregar tábuas:', err);
      setError(err.response?.data?.detail || 'Erro ao carregar tábuas de mortalidade');
    } finally {
      setLoading(false);
    }
  };

  // Obter estatísticas de uma tábua
  const getTableStatistics = async (tableId: number): Promise<TableStatistics | null> => {
    try {
      const response = await axios.get<TableStatistics>(`${API_BASE}/${tableId}/statistics`);
      return response.data;
    } catch (err: any) {
      console.error('Erro ao carregar estatísticas:', err);
      throw new Error(err.response?.data?.detail || 'Erro ao carregar estatísticas');
    }
  };

  // Obter dados de mortalidade para gráficos
  const getTableMortalityData = async (
    tableId: number, 
    minAge?: number, 
    maxAge?: number
  ): Promise<{ data: Array<{ age: number; qx: number }>; table_info: any } | null> => {
    try {
      const params = new URLSearchParams({
        format: 'chart'
      });
      
      if (minAge !== undefined) params.append('min_age', minAge.toString());
      if (maxAge !== undefined) params.append('max_age', maxAge.toString());
      
      const response = await axios.get(`${API_BASE}/${tableId}/data?${params}`);
      return response.data;
    } catch (err: any) {
      console.error('Erro ao carregar dados de mortalidade:', err);
      throw new Error(err.response?.data?.detail || 'Erro ao carregar dados de mortalidade');
    }
  };

  // Buscar tábuas no pymort
  const searchPymort = async (query: string): Promise<PymortSearchResult> => {
    try {
      const response = await axios.get<PymortSearchResult>(
        `${API_BASE}/admin/search-pymort?query=${encodeURIComponent(query)}`
      );
      return response.data;
    } catch (err: any) {
      console.error('Erro ao buscar no pymort:', err);
      throw new Error(err.response?.data?.detail || 'Erro na busca do pymort');
    }
  };

  // Carregar tábua do pymort
  const loadFromPymort = async (tableId: number): Promise<void> => {
    try {
      const response = await axios.post(`${API_BASE}/load/pymort/${tableId}`);
      console.log(response.data.message);
      
      // Recarregar lista após alguns segundos (processamento em background)
      setTimeout(() => {
        fetchTables();
      }, 3000);
    } catch (err: any) {
      console.error('Erro ao carregar do pymort:', err);
      throw new Error(err.response?.data?.detail || 'Erro ao carregar tábua do pymort');
    }
  };

  // Upload de CSV
  const uploadCSV = async (
    file: File,
    name: string,
    description: string,
    country: string,
    gender: string
  ): Promise<void> => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const params = new URLSearchParams({
        name,
        description,
        country,
        gender
      });

      const response = await axios.post(
        `${API_BASE}/admin/upload-csv?${params}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      console.log(response.data.message);
      
      // Recarregar lista
      await fetchTables();
    } catch (err: any) {
      console.error('Erro ao fazer upload:', err);
      throw new Error(err.response?.data?.detail || 'Erro ao fazer upload do CSV');
    }
  };

  // Ativar/desativar tábua
  const toggleTableActive = async (tableId: number): Promise<void> => {
    try {
      const response = await axios.post(`${API_BASE}/admin/${tableId}/toggle-active`);
      console.log(response.data.message);
      
      // Atualizar a tábua na lista local
      setTables(prevTables => 
        prevTables.map(table => 
          table.id === tableId 
            ? { ...table, is_active: !table.is_active }
            : table
        )
      );
    } catch (err: any) {
      console.error('Erro ao alterar status:', err);
      throw new Error(err.response?.data?.detail || 'Erro ao alterar status da tábua');
    }
  };

  // Remover tábua
  const deleteTable = async (tableId: number): Promise<void> => {
    try {
      const response = await axios.delete(`${API_BASE}/${tableId}`);
      console.log(response.data.message);
      
      // Remover da lista local
      setTables(prevTables => prevTables.filter(table => table.id !== tableId));
    } catch (err: any) {
      console.error('Erro ao remover tábua:', err);
      throw new Error(err.response?.data?.detail || 'Erro ao remover tábua');
    }
  };

  // Carregar na inicialização
  useEffect(() => {
    fetchTables();
  }, []);

  return {
    tables,
    loading,
    error,
    fetchTables,
    getTableStatistics,
    getTableMortalityData,
    searchPymort,
    loadFromPymort,
    uploadCSV,
    toggleTableActive,
    deleteTable,
  };
};