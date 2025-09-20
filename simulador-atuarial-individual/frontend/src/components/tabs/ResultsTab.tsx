import React from 'react';
import type { SimulatorResults, SimulatorState } from '../../types';
import { formatCurrencyBR, formatSimplePercentageBR, formatIndexationBR, formatBenefitModalityBR } from '../../utils/formatBR';
import { DeterministicChart, ActuarialChart, VPABarChart, SufficiencyBarChart, SufficiencyAnalysisChart, CDLifecycleChart, CDContributionImpactChart, SalaryBenefitEvolutionChart } from '../charts';

interface ResultsTabProps {
  results: SimulatorResults | null;
  state: SimulatorState;
  loading: boolean;
}

const ResultsTab: React.FC<ResultsTabProps> = ({ results, state, loading }) => {

  const getSuperavitStatus = (superavit: number) => {
    if (superavit > 0) return { color: 'emerald', text: 'Superávit', bg: 'from-emerald-100 to-green-100' };
    if (superavit === 0) return { color: 'yellow', text: 'Equilibrado', bg: 'from-yellow-100 to-amber-100' };
    return { color: 'red', text: 'Déficit', bg: 'from-red-100 to-rose-100' };
  };

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Resultados da Simulação
          </h1>
          <p className="text-gray-600">Análise completa das projeções atuariais e financeiras.</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="flex items-center justify-center min-h-[200px]">
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Calculando Resultados</h2>
              <p className="text-gray-600">Processando as premissas atuariais...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="space-y-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Resultados da Simulação
          </h1>
          <p className="text-gray-600">Análise completa das projeções atuariais e financeiras.</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="text-center min-h-[200px] flex items-center justify-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Aguardando Dados</h2>
              <p className="text-gray-600">Configure os parâmetros nas abas anteriores para ver os resultados</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const superavitStatus = getSuperavitStatus(results.deficit_surplus);

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Resultados da Simulação
        </h1>
        <p className="text-gray-600">Análise completa das projeções atuariais e financeiras.</p>
      </div>

      {/* Premissas da Simulação — compacto em várias colunas, sem accordion */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 rounded-t-lg">
          <h2 className="text-lg font-semibold text-gray-900">Premissas da Simulação</h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 2xl:grid-cols-12 gap-2">
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Idade/Gênero</div>
              <div className="text-sm font-medium text-gray-900">
                {state.age || '—'} {state.age ? 'anos' : ''}{state.gender ? ` • ${state.gender}` : ''}
              </div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Salário</div>
              <div className="text-sm font-medium text-gray-900">{state.salary ? formatCurrencyBR(state.salary, 2) : '—'}</div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Saldo Inicial</div>
              <div className="text-sm font-medium text-gray-900">{state.initial_balance ? formatCurrencyBR(state.initial_balance, 2) : '—'}</div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Plano/Aposent.</div>
              <div className="text-sm font-medium text-gray-900">
                {(state.plan_type || 'BD')}{state.retirement_age ? ` • ${state.retirement_age}a` : ''}
              </div>
            </div>
            {/* Objetivo (benefício ou taxa de reposição) */}
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Objetivo</div>
              <div className="text-sm font-medium text-gray-900">
                {state.benefit_target_mode === 'VALUE'
                  ? (state.target_benefit ? formatCurrencyBR(state.target_benefit, 2) : '—')
                  : (state.target_replacement_rate !== undefined ? formatSimplePercentageBR(state.target_replacement_rate, 2) : '—')}
              </div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Modalidade</div>
              <div className="text-sm font-medium text-gray-900">
                {formatBenefitModalityBR(
                  state.plan_type === 'CD' 
                    ? (state.cd_conversion_mode || 'ACTUARIAL')
                    : (state.benefit_target_mode || 'VALUE'),
                  state.plan_type || 'BD'
                )}
              </div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Pag/ano</div>
              <div className="text-sm font-medium text-gray-900">{state.benefit_months_per_year || 13}x</div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Timing</div>
              <div className="text-sm font-medium text-gray-900">{state.payment_timing === 'antecipado' ? 'Antecipado' : 'Postecipado'}</div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Contribuição</div>
              <div className="text-sm font-medium text-gray-900">{formatSimplePercentageBR(state.contribution_rate || 0, 2)}</div>
            </div>
            {/* Taxas condicionais por tipo de plano */}
            {state.plan_type === 'CD' ? (
              // Para CD: mostra Taxa de Acumulação (CD)
              <div className="rounded-md bg-gray-50 p-2">
                <div className="text-[10px] uppercase tracking-wide text-gray-500">Acumulação</div>
                <div className="text-sm font-medium text-gray-900">{formatSimplePercentageBR((state.accumulation_rate || 0.065) * 100, 2)} a.a.</div>
              </div>
            ) : (
              // Para BD: mostra Taxa de Acumulação Real
              <div className="rounded-md bg-gray-50 p-2">
                <div className="text-[10px] uppercase tracking-wide text-gray-500">Acumulação Real</div>
                <div className="text-sm font-medium text-gray-900">{formatSimplePercentageBR(state.accrual_rate || 5, 2)} a.a.</div>
              </div>
            )}
            {state.plan_type === 'CD' ? (
              // Para CD: mostra Taxa de Conversão (CD)
              <div className="rounded-md bg-gray-50 p-2">
                <div className="text-[10px] uppercase tracking-wide text-gray-500">Conversão</div>
                <div className="text-sm font-medium text-gray-900">{formatSimplePercentageBR((state.conversion_rate || 0.045) * 100, 2)} a.a.</div>
              </div>
            ) : (
              // Para BD: mostra Taxa de Desconto Real
              <div className="rounded-md bg-gray-50 p-2">
                <div className="text-[10px] uppercase tracking-wide text-gray-500">Desconto Real</div>
                <div className="text-sm font-medium text-gray-900">{state.discount_rate !== undefined ? `${formatSimplePercentageBR(state.discount_rate * 100, 2)} a.a.` : '—'}</div>
              </div>
            )}
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Cresc. Sal. Real</div>
              <div className="text-sm font-medium text-gray-900">{formatSimplePercentageBR((state.salary_growth_real || 0.02) * 100, 2)} a.a.</div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Tábua/Método</div>
              <div className="text-sm font-medium text-gray-900">{state.mortality_table || 'BR_EMS_2021'}{state.calculation_method ? ` • ${state.calculation_method}` : ''}</div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Meses Salário/ano</div>
              <div className="text-sm font-medium text-gray-900">{state.salary_months_per_year || 12}x</div>
            </div>
            <div className="rounded-md bg-gray-50 p-2">
              <div className="text-[10px] uppercase tracking-wide text-gray-500">Suav. Tábua</div>
              <div className="text-sm font-medium text-gray-900">{(state.mortality_aggravation || 0) > 0 ? '+' : ''}{state.mortality_aggravation || 0}%</div>
            </div>
            {state.admin_fee_rate && state.admin_fee_rate > 0 ? (
              <div className="rounded-md bg-gray-50 p-2">
                <div className="text-[10px] uppercase tracking-wide text-gray-500">Taxa Admin.</div>
                <div className="text-sm font-medium text-gray-900">{formatSimplePercentageBR(state.admin_fee_rate * 100, 2)} a.a.</div>
              </div>
            ) : null}
            {state.loading_fee_rate && state.loading_fee_rate > 0 ? (
              <div className="rounded-md bg-gray-50 p-2">
                <div className="text-[10px] uppercase tracking-wide text-gray-500">Carregamento</div>
                <div className="text-sm font-medium text-gray-900">{formatSimplePercentageBR(state.loading_fee_rate * 100, 2)}</div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Visualizações Gráficas */}
      <div className="grid grid-cols-1 gap-8">
        {state.plan_type === 'CD' ? (
          <>
            {/* CD: Ciclo de Vida Completo */}
            <div className="bg-white rounded-xl shadow-sm p-8">
              <CDLifecycleChart results={results} state={state} />
            </div>

            {/* CD: Impacto da Contribuição */}
            <div className="bg-white rounded-xl shadow-sm p-8">
              <CDContributionImpactChart results={results} state={state} />
            </div>
          </>
        ) : (
          <>
            {/* BD: Análise de Suficiência Financeira */}
            <div className="bg-white rounded-xl shadow-sm p-8">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Análise de Suficiência Financeira
                </h2>
              </div>
              <SufficiencyAnalysisChart results={results} state={state} />
            </div>

            {/* BD: Composição da RMBA */}
            <div className="bg-white rounded-xl shadow-sm p-8">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Composição da RMBA
                </h2>
              </div>
              <VPABarChart results={results} />
            </div>
          </>
        )}
      </div>

      {/* Análise Temporal - Condicional por Tipo de Plano */}
      {state.plan_type === 'CD' ? null : (
        // BD: Dois gráficos lado a lado
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Simulação Determinística */}
          <div className="bg-white rounded-xl shadow-sm p-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Simulação Realística
              </h2>
            </div>
            <DeterministicChart results={results} currentAge={state.age} planType={state.plan_type} />
          </div>

          {/* Análise Atuarial */}
          <div className="bg-white rounded-xl shadow-sm p-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Análise Atuarial
              </h2>
            </div>
            <ActuarialChart results={results} currentAge={state.age} retirementAge={state.retirement_age} />
          </div>
        </div>
      )}


      {/* Gráfico de Evolução Salarial e Benefícios - Posicionado no final */}
      <div className="bg-white rounded-xl shadow-sm p-8">
        <SalaryBenefitEvolutionChart results={results} state={state} />
      </div>
    </div>
  );
};

export default ResultsTab;
