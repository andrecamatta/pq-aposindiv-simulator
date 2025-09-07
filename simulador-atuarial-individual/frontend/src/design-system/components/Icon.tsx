import React from 'react';
import { cn } from '../../lib/utils';
import { iconMap, iconSizes, iconColors, type IconName, type IconSize, type IconColor } from '../icons/iconConfig';

export interface IconProps {
  name: IconName;
  size?: IconSize;
  color?: IconColor;
  className?: string;
  'aria-hidden'?: boolean;
}

export const Icon: React.FC<IconProps> = ({ 
  name, 
  size = 'sm', 
  color = 'neutral',
  className,
  'aria-hidden': ariaHidden = true,
  ...props 
}) => {
  const IconComponent = iconMap[name];
  
  if (!IconComponent) {
    return null;
  }
  
  return (
    <IconComponent 
      className={cn(
        iconSizes[size],
        iconColors[color],
        className
      )}
      aria-hidden={ariaHidden}
      {...props}
    />
  );
};

// Componente wrapper para compatibilidade com componentes que esperam um React.ComponentType
export const createIconComponent = (name: IconName): React.ComponentType<{ className?: string }> => {
  return ({ className, ...props }) => {
    const IconComponent = iconMap[name];
    return IconComponent ? <IconComponent className={className} {...props} /> : null;
  };
};