import React, { useState, useEffect } from 'react';
import { Icon } from '../../design-system/components';
import type { FamilyMember, DependentType } from '../../types/simulator.types';

interface FamilyMembersTableProps {
  members: FamilyMember[];
  onChange: (members: FamilyMember[]) => void;
}

const dependentTypeOptions: Array<{ value: DependentType; label: string }> = [
  { value: 'SPOUSE', label: 'Cônjuge' },
  { value: 'CHILD', label: 'Filho(a)' },
  { value: 'PARENT', label: 'Pai/Mãe' },
  { value: 'EX_SPOUSE', label: 'Ex-cônjuge' },
  { value: 'OTHER', label: 'Outro' }
];

const genderOptions = [
  { value: 'F', label: 'F' },
  { value: 'M', label: 'M' }
];

export function FamilyMembersTable({ members, onChange }: FamilyMembersTableProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newRow, setNewRow] = useState<Partial<FamilyMember>>({
    name: '',
    dependent_type: 'SPOUSE',
    age: 30,
    gender: 'F',
    benefit_share_percentage: 50,
    economic_dependency: true,
    is_disabled: false,
    priority_class: 1
  });

  // Auto-save quando newRow.name tem conteúdo
  useEffect(() => {
    if (newRow.name && newRow.name.trim().length > 0) {
      const timer = setTimeout(() => {
        handleAddRow();
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [newRow.name]);

  const handleAddRow = () => {
    if (!newRow.name || newRow.name.trim().length === 0) return;

    const newMember: FamilyMember = {
      id: crypto.randomUUID(),
      name: newRow.name.trim(),
      dependent_type: newRow.dependent_type || 'SPOUSE',
      age: newRow.age || 30,
      gender: newRow.gender || 'F',
      benefit_share_percentage: newRow.benefit_share_percentage || 50,
      economic_dependency: newRow.economic_dependency !== undefined ? newRow.economic_dependency : true,
      is_disabled: newRow.is_disabled || false,
      priority_class: newRow.priority_class || 1
    };

    onChange([...members, newMember]);

    // Reset nova linha
    setNewRow({
      name: '',
      dependent_type: 'SPOUSE',
      age: 30,
      gender: 'F',
      benefit_share_percentage: 50,
      economic_dependency: true,
      is_disabled: false,
      priority_class: 1
    });
  };

  const handleUpdateMember = (id: string, field: keyof FamilyMember, value: any) => {
    const updatedMembers = members.map(m =>
      m.id === id ? { ...m, [field]: value } : m
    );
    onChange(updatedMembers);
  };

  const handleRemoveMember = (id: string, name: string) => {
    if (confirm(`Remover ${name} da lista de dependentes?`)) {
      onChange(members.filter(m => m.id !== id));
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-50 border-b-2 border-gray-200">
            <th className="text-left px-3 py-2 text-sm font-semibold text-gray-700">Nome</th>
            <th className="text-left px-3 py-2 text-sm font-semibold text-gray-700">Tipo</th>
            <th className="text-center px-3 py-2 text-sm font-semibold text-gray-700">Idade</th>
            <th className="text-center px-3 py-2 text-sm font-semibold text-gray-700">Gênero</th>
            <th className="text-center px-3 py-2 text-sm font-semibold text-gray-700">% Ben.</th>
            <th className="text-center px-3 py-2 text-sm font-semibold text-gray-700">Dep.Econ.</th>
            <th className="text-center px-3 py-2 text-sm font-semibold text-gray-700">Invalidez</th>
            <th className="text-center px-3 py-2 text-sm font-semibold text-gray-700 w-16">Ações</th>
          </tr>
        </thead>
        <tbody>
          {members.length === 0 && (
            <tr>
              <td colSpan={8} className="text-center py-8 text-gray-500 text-sm">
                Nenhum dependente cadastrado. Preencha a linha abaixo para adicionar.
              </td>
            </tr>
          )}

          {members.map((member, index) => (
            <tr
              key={member.id}
              className={`border-b border-gray-200 hover:bg-gray-50 transition-colors ${
                index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
              }`}
            >
              {/* Nome */}
              <td className="px-3 py-2">
                <input
                  type="text"
                  value={member.name}
                  onChange={(e) => handleUpdateMember(member.id!, 'name', e.target.value)}
                  onFocus={() => setEditingId(member.id!)}
                  onBlur={() => setEditingId(null)}
                  className={`w-full px-2 py-1 text-sm border rounded ${
                    editingId === member.id
                      ? 'border-blue-500 ring-1 ring-blue-500'
                      : 'border-transparent hover:border-gray-300'
                  } focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500`}
                />
              </td>

              {/* Tipo */}
              <td className="px-3 py-2">
                <select
                  value={member.dependent_type}
                  onChange={(e) => handleUpdateMember(member.id!, 'dependent_type', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-transparent hover:border-gray-300 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {dependentTypeOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </td>

              {/* Idade */}
              <td className="px-3 py-2">
                <input
                  type="number"
                  value={member.age || ''}
                  onChange={(e) => handleUpdateMember(member.id!, 'age', Number(e.target.value))}
                  min={0}
                  max={120}
                  className="w-20 px-2 py-1 text-sm text-center border border-transparent hover:border-gray-300 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </td>

              {/* Gênero */}
              <td className="px-3 py-2">
                <select
                  value={member.gender || 'F'}
                  onChange={(e) => handleUpdateMember(member.id!, 'gender', e.target.value)}
                  className="w-16 px-2 py-1 text-sm text-center border border-transparent hover:border-gray-300 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  {genderOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </td>

              {/* % Benefício */}
              <td className="px-3 py-2">
                <div className="flex items-center justify-center gap-1">
                  <input
                    type="number"
                    value={member.benefit_share_percentage}
                    onChange={(e) => handleUpdateMember(member.id!, 'benefit_share_percentage', Number(e.target.value))}
                    min={0}
                    max={100}
                    className="w-16 px-2 py-1 text-sm text-center border border-transparent hover:border-gray-300 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-600">%</span>
                </div>
              </td>

              {/* Dep. Econômica */}
              <td className="px-3 py-2 text-center">
                <input
                  type="checkbox"
                  checked={member.economic_dependency}
                  onChange={(e) => handleUpdateMember(member.id!, 'economic_dependency', e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
              </td>

              {/* Invalidez */}
              <td className="px-3 py-2 text-center">
                <input
                  type="checkbox"
                  checked={member.is_disabled}
                  onChange={(e) => handleUpdateMember(member.id!, 'is_disabled', e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
              </td>

              {/* Ações */}
              <td className="px-3 py-2 text-center">
                <button
                  onClick={() => handleRemoveMember(member.id!, member.name)}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50 p-1 rounded transition-colors"
                  title="Remover dependente"
                >
                  <Icon name="trash" size={16} />
                </button>
              </td>
            </tr>
          ))}

          {/* Linha para adicionar novo */}
          <tr className="border-b-2 border-blue-200 bg-blue-50/30">
            {/* Nome */}
            <td className="px-3 py-2">
              <input
                type="text"
                value={newRow.name}
                onChange={(e) => setNewRow({ ...newRow, name: e.target.value })}
                placeholder="Digite o nome para adicionar..."
                className="w-full px-2 py-1 text-sm border border-blue-200 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white"
              />
            </td>

            {/* Tipo */}
            <td className="px-3 py-2">
              <select
                value={newRow.dependent_type}
                onChange={(e) => setNewRow({ ...newRow, dependent_type: e.target.value as DependentType })}
                className="w-full px-2 py-1 text-sm border border-blue-200 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white"
              >
                {dependentTypeOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </td>

            {/* Idade */}
            <td className="px-3 py-2">
              <input
                type="number"
                value={newRow.age}
                onChange={(e) => setNewRow({ ...newRow, age: Number(e.target.value) })}
                min={0}
                max={120}
                className="w-20 px-2 py-1 text-sm text-center border border-blue-200 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white"
              />
            </td>

            {/* Gênero */}
            <td className="px-3 py-2">
              <select
                value={newRow.gender}
                onChange={(e) => setNewRow({ ...newRow, gender: e.target.value as 'M' | 'F' })}
                className="w-16 px-2 py-1 text-sm text-center border border-blue-200 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white"
              >
                {genderOptions.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </td>

            {/* % Benefício */}
            <td className="px-3 py-2">
              <div className="flex items-center justify-center gap-1">
                <input
                  type="number"
                  value={newRow.benefit_share_percentage}
                  onChange={(e) => setNewRow({ ...newRow, benefit_share_percentage: Number(e.target.value) })}
                  min={0}
                  max={100}
                  className="w-16 px-2 py-1 text-sm text-center border border-blue-200 rounded focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 bg-white"
                />
                <span className="text-sm text-gray-600">%</span>
              </div>
            </td>

            {/* Dep. Econômica */}
            <td className="px-3 py-2 text-center">
              <input
                type="checkbox"
                checked={newRow.economic_dependency}
                onChange={(e) => setNewRow({ ...newRow, economic_dependency: e.target.checked })}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
            </td>

            {/* Invalidez */}
            <td className="px-3 py-2 text-center">
              <input
                type="checkbox"
                checked={newRow.is_disabled}
                onChange={(e) => setNewRow({ ...newRow, is_disabled: e.target.checked })}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
            </td>

            {/* Ações */}
            <td className="px-3 py-2 text-center">
              <div className="text-blue-600 text-sm font-medium">Nova</div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
