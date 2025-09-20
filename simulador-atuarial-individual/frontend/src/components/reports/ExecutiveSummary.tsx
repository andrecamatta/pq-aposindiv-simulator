import React from 'react';
import type { SimulatorResults, SimulatorState } from '../../types';
import { Card, CardHeader, CardTitle, CardContent } from '../../design-system/components';
import { formatCurrencyBR, formatSimplePercentageBR, formatDateBR } from '../../utils/formatBR';

interface ExecutiveSummaryProps {
  results: SimulatorResults;
  state: SimulatorState;
}

const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({ results, state }) => {
  const isCD = state.plan_type === 'CD';

  // Análise de situação para BD
  const getSituationAnalysis = () => {
    if (isCD) {
      const adequacyRatio = results.replacement_ratio / (state.target_replacement_rate || 70);
      if (adequacyRatio >= 1.1) return { status: 'Excelente', color: 'emerald', description: 'Renda projetada supera a meta de aposentadoria' };
      if (adequacyRatio >= 0.9) return { status: 'Adequada', color: 'green', description: 'Renda projetada próxima à meta estabelecida' };
      if (adequacyRatio >= 0.7) return { status: 'Moderada', color: 'yellow', description: 'Renda projetada abaixo da meta, requer atenção' };
      return { status: 'Insuficiente', color: 'red', description: 'Renda projetada muito abaixo da meta' };
    } else {
      if (results.deficit_surplus > 50000) return { status: 'Superavitário', color: 'emerald', description: 'Reservas suficientes com folga' };
      if (results.deficit_surplus > 0) return { status: 'Equilibrado', color: 'green', description: 'Reservas adequadas às obrigações' };
      if (results.deficit_surplus > -50000) return { status: 'Atenção', color: 'yellow', description: 'Pequeno déficit, monitoramento necessário' };
      return { status: 'Crítico', color: 'red', description: 'Déficit significativo, ação imediata necessária' };
    }
  };

  // Recomendações baseadas nos resultados
  const getRecommendations = () => {
    const recommendations: string[] = [];

    if (isCD) {
      const targetRate = state.target_replacement_rate || 70;
      const actualRate = results.replacement_ratio;

      // Análise da taxa de reposição
      if (actualRate < targetRate * 0.8) {
        recommendations.push(`Taxa de reposição atual (${formatSimplePercentageBR(actualRate, 1)}) muito abaixo da meta (${formatSimplePercentageBR(targetRate, 1)}). Considerar aumento da contribuição de ${formatSimplePercentageBR(state.contribution_rate, 1)} para ${formatSimplePercentageBR(state.contribution_rate * 1.3, 1)}`);
      } else if (actualRate < targetRate * 0.9) {
        recommendations.push(`Taxa de reposição próxima mas abaixo da meta. Pequeno ajuste na contribuição pode ser suficiente`);
      } else if (actualRate > targetRate * 1.2) {
        recommendations.push(`Taxa de reposição significativamente acima da meta. Possível redução de contribuições ou aumento do benefício alvo`);
      }

      // Análise da modalidade de conversão
      if (state.cd_conversion_mode === 'ACTUARIAL_EQUIVALENT') {
        recommendations.push('Modalidade de equivalência atuarial escolhida: benefício será recalculado anualmente, proporcionando maior flexibilidade e proteção contra longevidade');
      } else if (state.cd_conversion_mode === 'PERCENTAGE') {
        recommendations.push('Modalidade percentual do saldo: atenção para sustentabilidade a longo prazo, considerar conversão para modalidade vitalícia');
      } else if ((results.benefit_duration_years || 0) < 20) {
        recommendations.push('Duração projetada dos benefícios relativamente baixa. Avaliar mudança para modalidade vitalícia ou equivalência atuarial');
      }

      // Análise da idade e tempo para aposentadoria
      const yearsToRetirement = state.retirement_age - state.age;
      if (yearsToRetirement < 10) {
        recommendations.push('Próximo à aposentadoria: considerar estratégias mais conservadoras e revisão das premissas de conversão');
      } else if (yearsToRetirement > 20) {
        recommendations.push('Longo período para aposentadoria: oportunidade para otimizar estratégia de contribuição e acumulação');
      }

    } else {
      // Análise do déficit/superávit
      const deficitSurplus = results.deficit_surplus;
      const deficitPercentage = Math.abs(results.deficit_surplus_percentage || 0);

      if (deficitSurplus < -100000) {
        recommendations.push(`Déficit atuarial crítico de ${formatCurrencyBR(Math.abs(deficitSurplus), 0)} (${formatSimplePercentageBR(deficitPercentage, 1)}). Ação imediata necessária: aporte extraordinário ou revisão das premissas`);
      } else if (deficitSurplus < 0) {
        recommendations.push(`Déficit atuarial de ${formatCurrencyBR(Math.abs(deficitSurplus), 0)}. Implementar aporte ou ajuste gradual das contribuições`);
      } else if (deficitSurplus > 200000) {
        recommendations.push(`Superávit significativo de ${formatCurrencyBR(deficitSurplus, 0)}. Oportunidade para melhoria de benefícios ou redução de contribuições`);
      }

      // Análise da taxa de contribuição necessária
      const currentRate = state.contribution_rate;
      const requiredRate = results.required_contribution_rate;

      if (requiredRate > currentRate * 1.3) {
        recommendations.push(`Taxa de contribuição atual (${formatSimplePercentageBR(currentRate, 1)}) insuficiente. Taxa necessária: ${formatSimplePercentageBR(requiredRate, 1)}. Revisar benefício alvo ou aumentar contribuições gradualmente`);
      } else if (requiredRate < currentRate * 0.8) {
        recommendations.push(`Taxa de contribuição atual superior à necessária. Oportunidade para redução ou melhoria de benefícios`);
      }

      // Análise da taxa de reposição
      const sustainableRate = results.sustainable_replacement_ratio;
      const targetRate = results.target_replacement_ratio;

      if (sustainableRate < targetRate * 0.9) {
        recommendations.push(`Taxa de reposição sustentável (${formatSimplePercentageBR(sustainableRate, 1)}) abaixo da meta (${formatSimplePercentageBR(targetRate, 1)}). Revisar benefício alvo ou aumentar contribuições`);
      }
    }

    // Recomendações gerais baseadas nas premissas
    if (state.mortality_aggravation === 0) {
      recommendations.push('Avaliar aplicação de suavização na tábua de mortalidade (5-10%) para alongar expectativas de sobrevivência quando apropriado');
    }

    const discountRate = isCD ? (state.accumulation_rate || 0.065) : state.discount_rate;
    if (discountRate > 0.08) {
      recommendations.push('Taxa de desconto/acumulação elevada: revisar se é sustentável no longo prazo dado o cenário econômico');
    } else if (discountRate < 0.04) {
      recommendations.push('Taxa de desconto/acumulação conservadora: verificar se está alinhada com a estratégia de investimento');
    }

    recommendations.push('Revisar premissas atuariais anualmente e monitorar indicadores econômicos relevantes');

    return recommendations;
  };

  const situation = getSituationAnalysis();
  const recommendations = getRecommendations();

  return (
    <div className="space-y-6">
      {/* Cabeçalho */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              RESUMO EXECUTIVO - SIMULAÇÃO ATUARIAL
            </h2>
            <div className="text-sm text-gray-600 space-y-1">
              <p><strong>Tipo de Plano:</strong> {isCD ? 'Contribuição Definida (CD)' : 'Benefício Definido (BD)'}</p>
              <p><strong>Data da Simulação:</strong> {formatDateBR(new Date())}</p>
              <p><strong>Participante:</strong> {state.gender === 'M' ? 'Masculino' : 'Feminino'}, {state.age} anos</p>
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Situação Geral */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className={`w-4 h-4 rounded-full bg-${situation.color}-500`}></div>
            <span>Situação Geral: {situation.status}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">{situation.description}</p>
        </CardContent>
      </Card>

      {/* Resultados Principais */}
      <Card>
        <CardHeader>
          <CardTitle>📊 Resultados Principais</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {isCD ? (
              <>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-600 uppercase font-medium mb-1">Saldo Acumulado</p>
                  <p className="text-lg font-bold text-blue-900">
                    {formatCurrencyBR(results.individual_balance || 0, 0)}
                  </p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-xs text-green-600 uppercase font-medium mb-1">Renda Mensal CD</p>
                  <p className="text-lg font-bold text-green-900">
                    {formatCurrencyBR(results.monthly_income_cd || 0, 0)}
                  </p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-xs text-purple-600 uppercase font-medium mb-1">Taxa Reposição</p>
                  <p className="text-lg font-bold text-purple-900">
                    {formatSimplePercentageBR(results.replacement_ratio, 1)}
                  </p>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <p className="text-xs text-orange-600 uppercase font-medium mb-1">Rendimento Total</p>
                  <p className="text-lg font-bold text-orange-900">
                    {formatCurrencyBR(results.accumulated_return || 0, 0)}
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-600 uppercase font-medium mb-1">RMBA</p>
                  <p className="text-lg font-bold text-blue-900">
                    {formatCurrencyBR(results.rmba, 0)}
                  </p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-xs text-green-600 uppercase font-medium mb-1">RMBC</p>
                  <p className="text-lg font-bold text-green-900">
                    {formatCurrencyBR(results.rmbc, 0)}
                  </p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-xs text-purple-600 uppercase font-medium mb-1">Superávit/Déficit</p>
                  <p className={`text-lg font-bold ${results.deficit_surplus >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                    {formatCurrencyBR(results.deficit_surplus, 0)}
                  </p>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <p className="text-xs text-orange-600 uppercase font-medium mb-1">Taxa Reposição</p>
                  <p className="text-lg font-bold text-orange-900">
                    {formatSimplePercentageBR(results.replacement_ratio, 1)}
                  </p>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Premissas Utilizadas */}
      <Card>
        <CardHeader>
          <CardTitle>⚙️ Premissas Utilizadas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900">Dados do Participante</h4>
              <div className="text-sm space-y-1">
                <p><strong>Idade Atual:</strong> {state.age} anos</p>
                <p><strong>Idade de Aposentadoria:</strong> {state.retirement_age} anos</p>
                <p><strong>Salário Mensal:</strong> {formatCurrencyBR(state.salary)}</p>
                <p><strong>Saldo Inicial:</strong> {formatCurrencyBR(state.initial_balance)}</p>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold text-gray-900">Hipóteses Atuariais</h4>
              <div className="text-sm space-y-1">
                <p><strong>Taxa de Contribuição:</strong> {formatSimplePercentageBR(state.contribution_rate, 1)}</p>
                {isCD ? (
                  <>
                    <p><strong>Taxa de Acumulação:</strong> {formatSimplePercentageBR((state.accumulation_rate || 0.065) * 100, 1)} a.a.</p>
                    <p><strong>Taxa de Conversão:</strong> {formatSimplePercentageBR((state.conversion_rate || 0.045) * 100, 1)} a.a.</p>
                  </>
                ) : (
                  <>
                    <p><strong>Taxa de Desconto:</strong> {formatSimplePercentageBR(state.discount_rate * 100, 1)} a.a.</p>
                    <p><strong>Crescimento Salarial:</strong> {formatSimplePercentageBR(state.salary_growth_real * 100, 1)} a.a.</p>
                  </>
                )}
                <p><strong>Tábua de Mortalidade:</strong> {state.mortality_table}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Análise e Recomendações */}
      <Card>
        <CardHeader>
          <CardTitle>💡 Análise e Recomendações</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Principais Observações:</h4>
              <div className="text-sm space-y-2">
                {isCD ? (
                  <>
                    <p>• A simulação projeta um saldo acumulado de <strong>{formatCurrencyBR(results.individual_balance || 0, 0)}</strong> na aposentadoria</p>
                    <p>• A renda mensal estimada é de <strong>{formatCurrencyBR(results.monthly_income_cd || 0, 0)}</strong>, representando <strong>{formatSimplePercentageBR(results.replacement_ratio, 1)}</strong> do salário final</p>
                    <p>• O período estimado de duração dos benefícios é de <strong>{results.benefit_duration_years || 0} anos</strong></p>
                  </>
                ) : (
                  <>
                    <p>• A RMBA atual é de <strong>{formatCurrencyBR(results.rmba, 0)}</strong>, representando as obrigações futuras</p>
                    <p>• O {results.deficit_surplus >= 0 ? 'superávit' : 'déficit'} é de <strong>{formatCurrencyBR(Math.abs(results.deficit_surplus), 0)}</strong></p>
                    <p>• A taxa de reposição sustentável é de <strong>{formatSimplePercentageBR(results.sustainable_replacement_ratio, 1)}</strong></p>
                  </>
                )}
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Recomendações:</h4>
              <ul className="text-sm space-y-1">
                {recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <Card className="bg-gray-50">
        <CardContent className="p-4">
          <p className="text-xs text-gray-600 text-center">
            <strong>Importante:</strong> Esta simulação é baseada nas premissas atuariais informadas e serve como ferramenta de apoio à decisão.
            Os resultados podem variar conforme mudanças nas condições econômicas, demográficas e regulatórias.
            Recomenda-se revisão periódica das premissas e acompanhamento atuarial especializado.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ExecutiveSummary;
