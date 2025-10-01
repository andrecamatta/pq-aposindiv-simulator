import React, { useState } from 'react';
import type { SimulatorResults, SimulatorState } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../../design-system/components';
import { formatCurrencyBR, formatDecimalToPercentageBR, formatSimplePercentageBR } from '../../utils/formatBR';
import { reportsService } from '../../services/reportsService';

interface ReportsTabProps {
  results: SimulatorResults | null;
  state: SimulatorState;
  loading: boolean;
}

const ReportsTab: React.FC<ReportsTabProps> = ({ results, state, loading }) => {
  const [downloadingPDF, setDownloadingPDF] = useState(false);
  const [downloadingExcel, setDownloadingExcel] = useState(false);
  const [downloadingCSV, setDownloadingCSV] = useState(false);

  const handleDownload = async (format: string) => {
    if (!results) return;

    try {
      // Set appropriate loading state
      if (format.includes('pdf')) {
        setDownloadingPDF(true);
      } else if (format === 'data-excel') {
        setDownloadingExcel(true);
      } else if (format === 'data-csv') {
        setDownloadingCSV(true);
      }

      if (format === 'executive-pdf') {
        await reportsService.downloadExecutivePDF({
          state: state,
          results: results
        });
      } else if (format === 'technical-pdf') {
        await reportsService.downloadTechnicalPDF({
          state: state,
          results: results
        });
      } else if (format === 'data-excel') {
        await reportsService.downloadDataExcel({
          state: state,
          results: results
        });
      } else if (format === 'data-csv') {
        await reportsService.downloadDataCSV({
          state: state,
          results: results
        });
      } else {
        // TODO: Implementar outros formatos (email)
        alert(`Formato ${format} ainda não está disponível`);
      }
    } catch (error) {
      console.error('Erro no download:', error);
      alert(error instanceof Error ? error.message : 'Erro ao baixar relatório');
    } finally {
      setDownloadingPDF(false);
      setDownloadingExcel(false);
      setDownloadingCSV(false);
    }
  };


  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Relatórios e Exportações
        </h1>
        <p className="text-gray-600">
          Gere documentos profissionais com os resultados da simulação atuarial.
        </p>
      </div>

      {/* Status Card */}
      {!results ? (
        <Card className="bg-gradient-to-br from-pink-50/70 to-pink-100/70 border-pink-200">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-pink-200 rounded-2xl flex items-center justify-center mx-auto mb-4">
            </div>
            <h3 className="text-xl font-bold text-pink-900 mb-2">Aguardando Resultados</h3>
            <p className="text-pink-600">
              Configure os parâmetros e execute a simulação para gerar relatórios
            </p>
          </CardContent>
        </Card>
      ) : (
        <>

          {/* Reports Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Relatório Executivo */}
            <Card className="bg-gradient-to-br from-pink-50/70 to-pink-100/70 border-pink-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-pink-300 to-pink-500 rounded-xl flex items-center justify-center">
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-pink-900">Relatório Executivo</h3>
                    <p className="text-sm text-pink-600">Resumo gerencial dos resultados</p>
                  </div>
                </CardTitle>
              </CardHeader>
              
              <CardContent className="pt-2">
                <div className="bg-white/60 rounded-xl p-4 border border-pink-200/50 space-y-3">
                  <div className="text-sm text-pink-800">
                    <p className="mb-2"><strong>Conteúdo:</strong></p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li>Resumo executivo da simulação</li>
                      <li>Principais indicadores (RMBA, RMBC, Superávit)</li>
                      <li>Premissas utilizadas</li>
                      <li>Recomendações técnicas</li>
                    </ul>
                  </div>
                  
                  <div className="flex gap-2 pt-3">
                    <Button
                      size="sm"
                      onClick={() => handleDownload('executive-pdf')}
                      className="bg-pink-500 hover:bg-pink-600 text-white w-full"
                      disabled={downloadingPDF}
                    >
                      {downloadingPDF ? 'Gerando PDF...' : 'Baixar PDF'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Relatório Técnico */}
            <Card className="bg-gradient-to-br from-pink-50/70 to-pink-100/70 border-pink-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-pink-400 to-pink-600 rounded-xl flex items-center justify-center">
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-pink-900">Relatório Técnico</h3>
                    <p className="text-sm text-pink-600">Documentação completa dos cálculos</p>
                  </div>
                </CardTitle>
              </CardHeader>
              
              <CardContent className="pt-2">
                <div className="bg-white/60 rounded-xl p-4 border border-pink-200/50 space-y-3">
                  <div className="text-sm text-pink-800">
                    <p className="mb-2"><strong>Conteúdo:</strong></p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li>Base técnica e metodologia</li>
                      <li>Tábuas de mortalidade utilizadas</li>
                      <li>Fluxo detalhado dos cálculos</li>
                      <li>Análise de sensibilidade</li>
                    </ul>
                  </div>
                  
                  <div className="flex gap-2 pt-3">
                    <Button
                      size="sm"
                      onClick={() => handleDownload('technical-pdf')}
                      className="bg-pink-500 hover:bg-pink-600 text-white w-full"
                      disabled={downloadingPDF}
                    >
                      {downloadingPDF ? 'Gerando PDF...' : 'Baixar PDF'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Planilha de Dados */}
            <Card className="bg-gradient-to-br from-pink-50/70 to-pink-100/70 border-pink-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-pink-700 rounded-xl flex items-center justify-center">
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-pink-900">Planilha de Dados</h3>
                    <p className="text-sm text-pink-600">Dados estruturados para análise</p>
                  </div>
                </CardTitle>
              </CardHeader>
              
              <CardContent className="pt-2">
                <div className="bg-white/60 rounded-xl p-4 border border-pink-200/50 space-y-3">
                  <div className="text-sm text-pink-800">
                    <p className="mb-2"><strong>Conteúdo:</strong></p>
                    <ul className="list-disc list-inside space-y-1 text-xs">
                      <li>Dados de entrada e premissas</li>
                      <li>Resultados detalhados</li>
                      <li>Projeções anuais</li>
                      <li>Tabelas de valores</li>
                    </ul>
                  </div>
                  
                  <div className="flex gap-2 pt-3">
                    <Button
                      size="sm"
                      onClick={() => handleDownload('data-excel')}
                      className="bg-green-500 hover:bg-green-600 text-white"
                      disabled={downloadingExcel || downloadingPDF || downloadingCSV}
                    >
                      {downloadingExcel ? 'Gerando Excel...' : 'Excel'}
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleDownload('data-csv')}
                      className="bg-blue-500 hover:bg-blue-600 text-white"
                      disabled={downloadingCSV || downloadingPDF || downloadingExcel}
                    >
                      {downloadingCSV ? 'Gerando CSV...' : 'CSV'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Email Report */}
            <Card className="bg-gradient-to-br from-pink-50/70 to-pink-100/70 border-pink-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-pink-600 to-rose-600 rounded-xl flex items-center justify-center">
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-pink-900">Envio por Email</h3>
                    <p className="text-sm text-pink-600">Compartilhe os resultados</p>
                  </div>
                </CardTitle>
              </CardHeader>
              
              <CardContent className="pt-2">
                <div className="bg-white/60 rounded-xl p-4 border border-pink-200/50 space-y-3">
                  <div className="text-sm text-pink-800 mb-3">
                    <p><strong>Envie relatórios por email</strong></p>
                    <p className="text-xs">Ideal para compartilhar com stakeholders</p>
                  </div>
                  
                  <Button 
                    size="sm"
                    onClick={() => handleDownload('email')}
                    className="bg-pink-500 hover:bg-pink-600 text-white w-full"
                    disabled
                  >
                    Configurar Email (Em breve)
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Summary Card */}
          <Card className="bg-gradient-to-r from-pink-100 to-rose-100 border-pink-200">
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-pink-900 mb-4">📋 Status da Simulação</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {state.plan_type === 'CD' ? (
                  <>
                    <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                      <p className="text-xs text-pink-600 uppercase font-medium mb-1">Saldo Final</p>
                      <p className="text-sm font-bold text-pink-900">
                        {formatCurrencyBR(results.individual_balance || 0, 0)}
                      </p>
                    </div>
                    <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                      <p className="text-xs text-pink-600 uppercase font-medium mb-1">Renda Mensal</p>
                      <p className="text-sm font-bold text-pink-900">
                        {formatCurrencyBR(results.monthly_income_cd || 0, 0)}
                      </p>
                    </div>
                    <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                      <p className="text-xs text-pink-600 uppercase font-medium mb-1">Taxa Reposição</p>
                      <p className="text-sm font-bold text-pink-900">
                        {formatSimplePercentageBR(results.replacement_ratio, 1)}
                      </p>
                    </div>
                    <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                      <p className="text-xs text-pink-600 uppercase font-medium mb-1">Data</p>
                      <p className="text-sm font-bold text-pink-900">
                        {new Date().toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                      <p className="text-xs text-pink-600 uppercase font-medium mb-1">RMBA</p>
                      <p className="text-sm font-bold text-pink-900">
                        {formatCurrencyBR(results.rmba, 0)}
                      </p>
                    </div>
                    <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                      <p className="text-xs text-pink-600 uppercase font-medium mb-1">RMBC</p>
                      <p className="text-sm font-bold text-pink-900">
                        {formatCurrencyBR(results.rmbc, 0)}
                      </p>
                    </div>
                    <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                      <p className="text-xs text-pink-600 uppercase font-medium mb-1">Superávit</p>
                      <p className="text-sm font-bold text-pink-900">
                        {formatDecimalToPercentageBR(results.deficit_surplus_percentage, 1)}
                      </p>
                    </div>
                    <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                      <p className="text-xs text-pink-600 uppercase font-medium mb-1">Data</p>
                      <p className="text-sm font-bold text-pink-900">
                        {new Date().toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Help Card */}
      <Card className="bg-white border-pink-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-pink-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <span className="text-2xl">📄</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Sobre os Relatórios</h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <p className="mb-2"><strong>Relatório Executivo:</strong> Ideal para apresentações e decisões estratégicas.</p>
                  <p className="mb-2"><strong>Relatório Técnico:</strong> Para análise detalhada por atuários e especialistas.</p>
                </div>
                <div>
                  <p className="mb-2"><strong>Planilha Excel:</strong> Para manipulação de dados e análises complementares.</p>
                  <p className="mb-2"><strong>Formato PDF:</strong> Documentos finalizados para arquivamento e distribuição.</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ReportsTab;