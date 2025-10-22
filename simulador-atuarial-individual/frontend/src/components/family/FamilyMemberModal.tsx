import React, { useState } from 'react';
import { Modal, FormField, Input, Select, Textarea, Button, Icon } from '../../design-system/components';
import type { FamilyMember, DependentType } from '../../types/simulator.types';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface FamilyMemberModalProps {
  member: FamilyMember | null;
  onSave: (member: FamilyMember) => void;
  onClose: () => void;
}

const dependentTypeOptions: Array<{ value: DependentType; label: string }> = [
  { value: 'SPOUSE', label: 'Cônjuge' },
  { value: 'CHILD', label: 'Filho(a)' },
  { value: 'PARENT', label: 'Pai/Mãe' },
  { value: 'EX_SPOUSE', label: 'Ex-cônjuge' },
  { value: 'OTHER', label: 'Outro' }
];

export function FamilyMemberModal({ member, onSave, onClose }: FamilyMemberModalProps) {
  const [formData, setFormData] = useState<Partial<FamilyMember>>({
    name: '',
    dependent_type: 'SPOUSE',
    age: 30,
    gender: 'F',
    benefit_share_percentage: 50,
    economic_dependency: true,
    is_disabled: false,
    priority_class: 1,
    ...member
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (field: keyof FamilyMember, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Limpar erro do campo quando modificado
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name || formData.name.trim().length < 2) {
      newErrors.name = 'Nome deve ter pelo menos 2 caracteres';
    }

    if (!formData.age || formData.age < 0 || formData.age > 120) {
      newErrors.age = 'Idade deve estar entre 0 e 120';
    }

    if (formData.benefit_share_percentage! < 0 || formData.benefit_share_percentage! > 100) {
      newErrors.benefit_share_percentage = 'Percentual deve estar entre 0 e 100';
    }

    if (formData.eligible_until_age && formData.eligible_until_age <= formData.age!) {
      newErrors.eligible_until_age = 'Idade limite deve ser maior que idade atual';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);
    try {
      onSave(formData as FamilyMember);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={member ? 'Editar Dependente' : 'Adicionar Dependente'}
      subtitle="Configure as informações do dependente para cálculo de benefícios de sobrevivência"
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Campos Essenciais */}
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField
              label="Nome Completo"
              required
              error={errors.name}
              className="sm:col-span-2"
            >
              <Input
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="Ex: Maria Silva"
                autoFocus
                className={errors.name ? 'border-red-300 focus:ring-red-500' : ''}
              />
            </FormField>

            <FormField label="Tipo de Dependente" required>
              <Select
                value={formData.dependent_type}
                onChange={(value) => handleChange('dependent_type', value as DependentType)}
                options={dependentTypeOptions}
              />
            </FormField>

            <FormField label="Gênero">
              <Select
                value={formData.gender || 'F'}
                onChange={(value) => handleChange('gender', value as 'M' | 'F')}
                options={[
                  { value: 'F', label: 'Feminino' },
                  { value: 'M', label: 'Masculino' }
                ]}
              />
            </FormField>

            <FormField label="Idade Atual" required error={errors.age}>
              <Input
                type="number"
                value={formData.age}
                onChange={(e) => handleChange('age', Number(e.target.value))}
                min={0}
                max={120}
                className={errors.age ? 'border-red-300 focus:ring-red-500' : ''}
              />
            </FormField>

            <FormField
              label="% do Benefício"
              tooltip="Percentual do benefício original que este dependente receberá"
              error={errors.benefit_share_percentage}
            >
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  value={formData.benefit_share_percentage}
                  onChange={(e) => handleChange('benefit_share_percentage', Number(e.target.value))}
                  min={0}
                  max={100}
                  className={errors.benefit_share_percentage ? 'border-red-300 focus:ring-red-500' : 'flex-1'}
                />
                <span className="text-gray-600 font-medium">%</span>
              </div>
            </FormField>
          </div>

          {/* Checkboxes Principais */}
          <div className="space-y-3 pt-2">
            <label className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={formData.economic_dependency}
                onChange={(e) => handleChange('economic_dependency', e.target.checked)}
                className="mt-0.5 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <div className="flex-1">
                <span className="text-sm font-medium text-gray-900">
                  Dependência Econômica Comprovada
                </span>
                <p className="text-xs text-gray-500 mt-0.5">
                  Marque se o dependente comprova dependência econômica do titular
                </p>
              </div>
            </label>

            <label className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors">
              <input
                type="checkbox"
                checked={formData.is_disabled}
                onChange={(e) => handleChange('is_disabled', e.target.checked)}
                className="mt-0.5 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <div className="flex-1">
                <span className="text-sm font-medium text-gray-900">
                  Invalidez (Pensão Vitalícia)
                </span>
                <p className="text-xs text-gray-500 mt-0.5">
                  Dependente com invalidez recebe pensão vitalícia, independente da idade
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Toggle Opções Avançadas */}
        <div className="border-t pt-4">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center justify-between w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors group"
          >
            <div className="flex items-center gap-2">
              {showAdvanced ? (
                <ChevronUp className="w-5 h-5 text-gray-500 group-hover:text-gray-700" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-500 group-hover:text-gray-700" />
              )}
              <span className="font-medium text-gray-700 group-hover:text-gray-900">
                Opções Avançadas
              </span>
            </div>
            <span className="text-xs text-gray-500">
              {showAdvanced ? 'Ocultar' : 'Mostrar'} configurações detalhadas
            </span>
          </button>
        </div>

        {/* Opções Avançadas (Colapsável) */}
        {showAdvanced && (
          <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                label="Classe de Prioridade"
                tooltip="Classe legal de prioridade (1 = maior prioridade)"
              >
                <Select
                  value={formData.priority_class}
                  onChange={(value) => handleChange('priority_class', Number(value))}
                  options={[
                    { value: 1, label: 'Classe 1 (Cônjuge + Filhos)' },
                    { value: 2, label: 'Classe 2 (Pais)' },
                    { value: 3, label: 'Classe 3 (Outros)' }
                  ]}
                />
              </FormField>

              <FormField
                label="Elegível Até (Idade)"
                tooltip="Idade limite de elegibilidade (ex: 21 para filhos, 24 se universitário)"
                error={errors.eligible_until_age}
              >
                <Input
                  type="number"
                  value={formData.eligible_until_age || ''}
                  onChange={(e) => handleChange('eligible_until_age', e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="Deixe vazio para vitalício"
                  min={formData.age}
                  max={120}
                  className={errors.eligible_until_age ? 'border-red-300 focus:ring-red-500' : ''}
                />
              </FormField>

              <FormField
                label="Diferencial de Idade"
                tooltip="Diferença de idade em relação ao titular (ex: -3 = 3 anos mais novo)"
              >
                <Input
                  type="number"
                  value={formData.age_differential || ''}
                  onChange={(e) => handleChange('age_differential', e.target.value ? Number(e.target.value) : undefined)}
                  placeholder="Opcional"
                />
              </FormField>

              <FormField
                label="Tábua de Mortalidade"
                tooltip="Deixe em branco para usar a mesma tábua do titular"
              >
                <Input
                  value={formData.mortality_table || ''}
                  onChange={(e) => handleChange('mortality_table', e.target.value || undefined)}
                  placeholder="Ex: BR_EMS_2021_F"
                />
              </FormField>
            </div>

            <FormField label="Observações">
              <Textarea
                value={formData.notes || ''}
                onChange={(e) => handleChange('notes', e.target.value || undefined)}
                placeholder="Informações adicionais sobre este dependente..."
                rows={3}
              />
            </FormField>
          </div>
        )}

        {/* Mensagens de Erro Globais */}
        {Object.keys(errors).length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex gap-2">
              <Icon name="alert-circle" size="sm" className="text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-red-900">
                  Corrija os erros abaixo:
                </h4>
                <ul className="mt-1 text-sm text-red-700 list-disc list-inside">
                  {Object.entries(errors).map(([field, error]) => (
                    <li key={field}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Botões de Ação */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={isSubmitting}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting}
            className="min-w-[180px]"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Salvando...
              </span>
            ) : (
              member ? 'Salvar Alterações' : 'Adicionar Dependente'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
