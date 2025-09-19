import React from 'react';
import type { MortalityTable } from '../../types';
import { Select, type SelectOption } from '../../design-system/components';

interface MortalityTableSelectorProps {
  value: string;
  mortalityTables: MortalityTable[];
  onChange: (value: string) => void;
  disabled?: boolean;
}

const MortalityTableSelector: React.FC<MortalityTableSelectorProps> = ({
  value,
  mortalityTables,
  onChange,
  disabled = false,
}) => {
  const options: SelectOption[] = mortalityTables.map((table) => ({
    value: table.code,
    label: table.code,
  }));

  return (
    <Select
      value={value}
      onChange={onChange}
      options={options}
      placeholder="Selecione..."
      disabled={disabled}
    />
  );
};

export default MortalityTableSelector;
