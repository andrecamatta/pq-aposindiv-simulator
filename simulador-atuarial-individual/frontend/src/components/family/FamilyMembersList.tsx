import React from 'react';
import { Badge, Button, Icon } from '../../design-system/components';
import type { FamilyMember, DependentType } from '../../types/simulator.types';

interface FamilyMembersListProps {
  members: FamilyMember[];
  onEdit: (member: FamilyMember) => void;
  onRemove: (id: string) => void;
}

const dependentTypeLabels: Record<DependentType, string> = {
  SPOUSE: 'Cônjuge',
  CHILD: 'Filho(a)',
  PARENT: 'Pai/Mãe',
  EX_SPOUSE: 'Ex-cônjuge',
  OTHER: 'Outro'
};

const dependentTypeIcons: Record<DependentType, string> = {
  SPOUSE: 'heart',
  CHILD: 'user',
  PARENT: 'users',
  EX_SPOUSE: 'user-minus',
  OTHER: 'user-plus'
};

export function FamilyMembersList({ members, onEdit, onRemove }: FamilyMembersListProps) {
  if (members.length === 0) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <Icon name="users" size={48} className="mx-auto mb-3 text-gray-400" />
        <p className="text-gray-600 mb-1">Nenhum dependente cadastrado</p>
        <p className="text-sm text-gray-500">Clique em "Adicionar Dependente" para começar</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {members.map((member) => (
        <div
          key={member.id}
          className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-4 flex-1">
            {/* Ícone do tipo */}
            <div className="p-2 bg-blue-50 rounded-lg">
              <Icon
                name={dependentTypeIcons[member.dependent_type]}
                size={20}
                className="text-blue-600"
              />
            </div>

            {/* Informações principais */}
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-gray-900">{member.name}</span>
                {member.is_disabled && (
                  <Badge variant="warning" size="sm">
                    Invalidez
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-3 text-sm text-gray-600">
                <span>{dependentTypeLabels[member.dependent_type]}</span>
                <span>•</span>
                <span>{member.age} anos</span>
                <span>•</span>
                <span>{member.benefit_share_percentage}% do benefício</span>

                {member.eligible_until_age && !member.is_disabled && (
                  <>
                    <span>•</span>
                    <span className="text-orange-600">
                      Elegível até {member.eligible_until_age} anos
                    </span>
                  </>
                )}
              </div>

              {member.notes && (
                <p className="text-xs text-gray-500 mt-1 italic">{member.notes}</p>
              )}
            </div>

            {/* Badges adicionais */}
            <div className="flex items-center gap-2">
              {member.priority_class && member.priority_class > 1 && (
                <Badge variant="secondary" size="sm">
                  Classe {member.priority_class}
                </Badge>
              )}

              {!member.economic_dependency && (
                <Badge variant="secondary" size="sm">
                  Sem dep. econômica
                </Badge>
              )}
            </div>
          </div>

          {/* Ações */}
          <div className="flex items-center gap-2 ml-4">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onEdit(member)}
              className="text-blue-600 hover:text-blue-700"
            >
              <Icon name="edit" size={16} />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                if (confirm(`Remover ${member.name} da lista de dependentes?`)) {
                  onRemove(member.id!);
                }
              }}
              className="text-red-600 hover:text-red-700"
            >
              <Icon name="trash" size={16} />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
