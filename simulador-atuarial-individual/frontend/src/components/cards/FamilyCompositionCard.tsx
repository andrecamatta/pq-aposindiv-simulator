import { Card, FormField, Select, Input, Icon } from '../../design-system/components';
import { FamilyMembersTable } from '../family/FamilyMembersTable';
import type { SimulatorState, FamilyMember, BenefitShareType, InheritanceRule } from '../../types/simulator.types';

interface FamilyCompositionCardProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading?: boolean;
}

export function FamilyCompositionCard({ state, onStateChange }: FamilyCompositionCardProps) {
  const handleMembersChange = (members: FamilyMember[]) => {
    onStateChange({
      family: { ...state.family, members }
    });
  };

  const handleToggleSurvivorBenefits = (enabled: boolean) => {
    onStateChange({ include_survivor_benefits: enabled });

    // Inicializar family se não existir
    if (enabled && !state.family) {
      onStateChange({
        family: {
          members: [],
          benefit_share_type: 'EQUAL_QUOTA',
          inheritance_rule: 'CONTINUED_INCOME',
          survivor_benefit_percentage: 100,
          enable_quota_reversion: true
        }
      });
    }
  };

  const benefitShareOptions: Array<{ value: BenefitShareType; label: string; description: string }> = [
    {
      value: 'EQUAL_QUOTA',
      label: 'Cotas Iguais',
      description: 'Divide o benefício em partes iguais entre todos os dependentes elegíveis. Exemplo: 3 dependentes = 33,33% cada.'
    },
    {
      value: 'PROPORTIONAL',
      label: 'Percentual Individual',
      description: 'Cada dependente recebe o percentual específico configurado na sua linha da tabela (coluna "% Ben.").'
    },
    {
      value: 'PRIORITY_CLASS',
      label: 'Classes de Prioridade Legal',
      description: 'Segue ordem legal (Lei 8.213/91): 1ª classe (cônjuge/filhos), 2ª classe (pais), 3ª classe (irmãos). Classe superior exclui as inferiores.'
    },
    {
      value: 'TOTAL_REVERSION',
      label: 'Reversão Total ao Sobrevivente',
      description: 'Quando um dependente perde elegibilidade, sua cota é redistribuída aos demais. Último sobrevivente recebe 100%.'
    }
  ];

  const inheritanceRuleOptions: Array<{ value: InheritanceRule; label: string; description: string }> = [
    {
      value: 'CONTINUED_INCOME',
      label: 'Continuar Renda Programada',
      description: 'Mantém pagamentos aos herdeiros'
    },
    {
      value: 'LUMP_SUM',
      label: 'Saque Único',
      description: 'Paga saldo total de uma vez'
    },
    {
      value: 'TEMPORARY_ANNUITY',
      label: 'Anuidade Temporária',
      description: 'Converte em renda por prazo fixo'
    },
    {
      value: 'PROPORTIONAL_SPLIT',
      label: 'Divisão Proporcional',
      description: 'Divide saldo conforme % de cada herdeiro'
    }
  ];

  return (
    <>
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Icon name="user" size="lg" className="text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Composição Familiar</h3>
              <p className="text-sm text-gray-600">Configure dependentes e regras de pensão/herança</p>
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={state.include_survivor_benefits || false}
              onChange={(e) => handleToggleSurvivorBenefits(e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <span className="text-sm font-medium">Habilitar</span>
          </label>
        </div>

        {state.include_survivor_benefits && (
          <div className="space-y-6">
            {/* Configurações Globais */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-4">
              <h4 className="font-medium text-gray-900">Configurações de Distribuição</h4>

              <div className="space-y-4">
                {/* Tipo de Distribuição */}
                <FormField
                  label="Tipo de Distribuição"
                  tooltip="Como os benefícios são distribuídos entre dependentes"
                >
                  <Select
                    value={state.family?.benefit_share_type || 'EQUAL_QUOTA'}
                    onChange={(value) => onStateChange({
                      family: { ...state.family, benefit_share_type: value as BenefitShareType }
                    })}
                    options={benefitShareOptions.map(opt => ({
                      value: opt.value,
                      label: opt.label
                    }))}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {benefitShareOptions.find(o => o.value === state.family?.benefit_share_type)?.description}
                  </p>
                </FormField>

                {/* Regra de Cálculo */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    label="Regra de Cálculo do Benefício"
                    tooltip="Define como o benefício dos sobreviventes é calculado"
                  >
                    <Select
                      value={state.family?.benefit_calculation_rule || 'FIXED_PERCENTAGE'}
                      onChange={(value) => onStateChange({
                        family: { ...state.family, benefit_calculation_rule: value as any }
                      })}
                      options={[
                        { value: 'FIXED_PERCENTAGE', label: 'Percentual Fixo' },
                        { value: 'BASE_PLUS_PER_DEPENDENT', label: '50% + 10% por Dependente' }
                      ]}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {state.family?.benefit_calculation_rule === 'BASE_PLUS_PER_DEPENDENT'
                        ? 'Base de 50% + 10% adicional por dependente. Ex: 3 dependentes = 80%.'
                        : 'Percentual fixo configurado ao lado.'}
                    </p>
                  </FormField>

                  {(!state.family?.benefit_calculation_rule || state.family?.benefit_calculation_rule === 'FIXED_PERCENTAGE') && (
                    <FormField
                      label="% do Benefício Original"
                      tooltip="Percentual do benefício do titular que será pago aos sobreviventes"
                    >
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          value={state.family?.survivor_benefit_percentage || 100}
                          onChange={(e) => onStateChange({
                            family: { ...state.family, survivor_benefit_percentage: Number(e.target.value) }
                          })}
                          min={0}
                          max={100}
                          className="flex-1"
                        />
                        <span className="text-gray-600">%</span>
                      </div>
                    </FormField>
                  )}
                </div>
              </div>

              {/* Regra de Herança (apenas CD) */}
              {state.plan_type === 'CD' && (
                <FormField
                  label="Regra de Herança do Saldo"
                  tooltip="Como o saldo remanescente será distribuído aos herdeiros"
                >
                  <Select
                    value={state.family?.inheritance_rule || 'CONTINUED_INCOME'}
                    onChange={(value) => onStateChange({
                      family: { ...state.family, inheritance_rule: value as InheritanceRule }
                    })}
                    options={inheritanceRuleOptions.map(opt => ({
                      value: opt.value,
                      label: opt.label
                    }))}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {inheritanceRuleOptions.find(o => o.value === state.family?.inheritance_rule)?.description}
                  </p>
                </FormField>
              )}

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={state.family?.enable_quota_reversion ?? true}
                    onChange={(e) => onStateChange({
                      family: { ...state.family, enable_quota_reversion: e.target.checked }
                    })}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">
                    Habilitar reversão de cotas quando dependente perde elegibilidade
                  </span>
                </label>
              </div>
            </div>

            {/* Tabela de Dependentes */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">
                Dependentes ({state.family?.members?.length || 0})
              </h4>

              <FamilyMembersTable
                members={state.family?.members || []}
                onChange={handleMembersChange}
              />
            </div>
          </div>
        )}

        {!state.include_survivor_benefits && (
          <div className="text-center py-8 text-gray-500">
            <Icon name="user" size="xl" className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">Ative os benefícios de sobrevivência para incluir dependentes</p>
          </div>
        )}
      </Card>
    </>
  );
}

export default FamilyCompositionCard;
