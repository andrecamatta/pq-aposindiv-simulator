import React from 'react';
import type { SimulatorResults, SimulatorState } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../../design-system/components';
import { formatCurrencyBR, formatDecimalToPercentageBR } from '../../utils/formatBR';

interface ReportsTabProps {
  results: SimulatorResults | null;
  state: SimulatorState;
  loading: boolean;
}

const ReportsTab: React.FC<ReportsTabProps> = ({ results, state, loading }) => {
  const handleDownload = (format: string) => {
    // TODO: Implementar download dos relatórios
    console.log(`Download ${format} report`);
  };

  const handlePreview = (format: string) => {
    // TODO: Implementar preview dos relatórios
    console.log(`Preview ${format} report`);
  };

  return (
    <div className="space-y-6">
      {/* Hero Card */}
      <Card className="bg-gradient-to-br from-pink-50 to-pink-100 border-pink-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-pink-200 to-pink-400 rounded-2xl flex items-center justify-center shadow-lg">
            </div>
            <div>
              <h2 className="text-2xl font-bold text-pink-900">Relatórios e Exportações</h2>
              <p className="text-pink-600 text-base">Gere documentos profissionais com os resultados</p>
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

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
                      variant="ghost"
                      onClick={() => handlePreview('executive-pdf')}
                      className="text-pink-700 hover:bg-pink-100"
                    >
                      Preview
                    </Button>
                    <Button 
                      size="sm"
                      onClick={() => handleDownload('executive-pdf')}
                      className="bg-pink-500 hover:bg-pink-600 text-white"
                    >
                      PDF
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
                      variant="ghost"
                      onClick={() => handlePreview('technical-pdf')}
                      className="text-pink-700 hover:bg-pink-100"
                    >
                      Preview
                    </Button>
                    <Button 
                      size="sm"
                      onClick={() => handleDownload('technical-pdf')}
                      className="bg-pink-500 hover:bg-pink-600 text-white"
                    >
                      PDF
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
                    >
                      Excel
                    </Button>
                    <Button 
                      size="sm"
                      onClick={() => handleDownload('data-csv')}
                      className="bg-blue-500 hover:bg-blue-600 text-white"
                    >
                      CSV
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
                    {formatDecimalToPercentageBR(results.superavit_percentage, 1)}
                  </p>
                </div>
                <div className="text-center bg-white/60 rounded-lg p-3 border border-pink-200/50">
                  <p className="text-xs text-pink-600 uppercase font-medium mb-1">Data</p>
                  <p className="text-sm font-bold text-pink-900">
                    {new Date().toLocaleDateString('pt-BR')}
                  </p>
                </div>
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