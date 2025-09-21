/**
 * Serviço para geração e download de relatórios em PDF
 * Refatorado para aplicar DRY e eliminar duplicação
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
   * Helper privado para unificar downloads de arquivos binários
   * Aplica DRY para eliminar duplicação entre métodos de download
   */
  private async downloadBinary(endpoint: string, request: ReportRequest, fallbackName: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/${endpoint}`, {
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
      let filename = fallbackName;

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
      throw new Error(
        `Erro ao baixar arquivo: ${error instanceof Error ? error.message : 'Erro desconhecido'}`
      );
    }
  }

  /**
   * Gerar e baixar relatório executivo em PDF
   */
  async downloadExecutivePDF(request: ReportRequest): Promise<void> {
    return this.downloadBinary('executive-pdf', request, 'relatorio_executivo.pdf');
  }

  /**
   * Gerar e baixar planilha Excel com dados estruturados
   */
  async downloadDataExcel(request: ReportRequest): Promise<void> {
    return this.downloadBinary('data-excel', request, 'dados_simulacao.xlsx');
  }

  /**
   * Gerar e baixar arquivo CSV com dados estruturados
   */
  async downloadDataCSV(request: ReportRequest): Promise<void> {
    return this.downloadBinary('data-csv', request, 'dados_simulacao.csv');
  }

  /**
   * Gerar e baixar relatório técnico em PDF
   */
  async downloadTechnicalPDF(request: ReportRequest): Promise<void> {
    return this.downloadBinary('technical-pdf', request, 'relatorio_tecnico.pdf');
  }
}

// Instância singleton
export const reportsService = new ReportsService();