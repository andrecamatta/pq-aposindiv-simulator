/**
 * Serviço para geração e download de relatórios em PDF
 */

import type { SimulatorState, SimulatorResults } from '../types';
import { API_BASE_URL } from './api';

export interface ReportRequest {
  state: SimulatorState;
  results: SimulatorResults;
}

export interface ReportResponse {
  success: boolean;
  message: string;
  file_size?: number;
  generation_time_ms?: number;
  report_id?: string;
}

export class ReportsService {
  private baseUrl = `${API_BASE_URL}/reports`;

  /**
   * Gerar e baixar relatório executivo em PDF
   */
  async downloadExecutivePDF(request: ReportRequest): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/executive-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
      }

      // Extrair nome do arquivo do header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'relatorio_executivo.pdf';

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Converter resposta para blob
      const blob = await response.blob();

      // Criar URL temporária e baixar
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Limpar URL temporária
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Erro ao baixar PDF:', error);
      throw new Error(
        error instanceof Error
          ? `Falha no download: ${error.message}`
          : 'Erro desconhecido ao baixar PDF'
      );
    }
  }

  /**
   * Gerar e baixar planilha Excel com dados estruturados
   */
  async downloadDataExcel(request: ReportRequest): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/data-excel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
      }

      // Extrair nome do arquivo do header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'dados_simulacao.xlsx';

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Converter resposta para blob
      const blob = await response.blob();

      // Criar URL temporária e baixar
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Limpar URL temporária
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Erro ao baixar planilha Excel:', error);
      throw new Error(
        error instanceof Error
          ? `Falha no download: ${error.message}`
          : 'Erro desconhecido ao baixar planilha Excel'
      );
    }
  }

  /**
   * Gerar e baixar arquivo CSV com dados estruturados
   */
  async downloadDataCSV(request: ReportRequest): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/data-csv`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
      }

      // Extrair nome do arquivo do header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'dados_simulacao.csv';

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Converter resposta para blob
      const blob = await response.blob();

      // Criar URL temporária e baixar
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Limpar URL temporária
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Erro ao baixar arquivo CSV:', error);
      throw new Error(
        error instanceof Error
          ? `Falha no download: ${error.message}`
          : 'Erro desconhecido ao baixar arquivo CSV'
      );
    }
  }

  /**
   * Gerar e baixar relatório técnico em PDF
   */
  async downloadTechnicalPDF(request: ReportRequest): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/technical-pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
      }

      // Extrair nome do arquivo do header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'relatorio_tecnico.pdf';

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      // Converter resposta para blob
      const blob = await response.blob();

      // Criar URL temporária e baixar
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.style.display = 'none';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Limpar URL temporária
      window.URL.revokeObjectURL(url);

    } catch (error) {
      console.error('Erro ao baixar PDF:', error);
      throw new Error(
        error instanceof Error
          ? `Falha no download: ${error.message}`
          : 'Erro desconhecido ao baixar PDF'
      );
    }
  }

  /**
   * Gerar preview HTML do relatório executivo
   */
  async generateExecutivePreview(request: ReportRequest): Promise<{
    success: boolean;
    html_content: string;
    charts_count: number;
    report_type: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/preview-executive`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erro ao gerar preview:', error);
      throw error;
    }
  }

  /**
   * Gerar preview HTML do relatório técnico
   */
  async generateTechnicalPreview(request: ReportRequest): Promise<{
    success: boolean;
    html_content: string;
    charts_count: number;
    report_type: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/preview-technical`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erro ao gerar preview:', error);
      throw error;
    }
  }

  /**
   * Verificar saúde do sistema de relatórios
   */
  async checkHealth(): Promise<{
    status: string;
    service: string;
    dependencies?: Record<string, string>;
    directories?: Record<string, boolean>;
    config?: Record<string, any>;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return await response.json();
    } catch (error) {
      console.error('Erro ao verificar saúde dos relatórios:', error);
      throw error;
    }
  }

  /**
   * Limpar cache de relatórios
   */
  async cleanupCache(): Promise<{
    success: boolean;
    message: string;
    files_removed: number;
    remaining_files: number;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/cache/cleanup`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erro ao limpar cache:', error);
      throw error;
    }
  }

  /**
   * Testar geração de PDF
   */
  async testPDFGeneration(): Promise<ReportResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/test-generation`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Erro HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erro no teste de PDF:', error);
      throw error;
    }
  }
}

// Instância singleton
export const reportsService = new ReportsService();