import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

// S-Tier Badge Component for status indicators
const badgeVariants = cva(
  [
    'inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium',
    'transition-all duration-150 ease-in-out',
  ],
  {
    variants: {
      variant: {
        // Semantic variants
        default: 'bg-gray-100 text-gray-800 border border-gray-200',
        primary: 'bg-primary-100 text-primary-800 border border-primary-200',
        success: 'bg-success-100 text-success-800 border border-success-200',
        warning: 'bg-warning-100 text-warning-800 border border-warning-200',
        error: 'bg-error-100 text-error-800 border border-error-200',
        info: 'bg-info-100 text-info-800 border border-info-200',
        
        // Solid variants for higher emphasis
        'primary-solid': 'bg-primary-500 text-white border border-primary-500',
        'success-solid': 'bg-success-500 text-white border border-success-500',
        'warning-solid': 'bg-warning-500 text-white border border-warning-500',
        'error-solid': 'bg-error-500 text-white border border-error-500',
        'info-solid': 'bg-info-500 text-white border border-info-500',
        
        // Outline variants
        outline: 'bg-transparent text-gray-700 border border-gray-300',
        'outline-primary': 'bg-transparent text-primary-700 border border-primary-300',
        'outline-success': 'bg-transparent text-success-700 border border-success-300',
        'outline-warning': 'bg-transparent text-warning-700 border border-warning-300',
        'outline-error': 'bg-transparent text-error-700 border border-error-300',
        'outline-info': 'bg-transparent text-info-700 border border-info-300',
      },
      size: {
        xs: 'px-1.5 py-0.5 text-xs',
        sm: 'px-2 py-1 text-xs',
        md: 'px-2.5 py-1 text-sm',
        lg: 'px-3 py-1.5 text-sm',
      },
      interactive: {
        true: 'cursor-pointer hover:opacity-80 active:scale-95',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'sm',
      interactive: false,
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, interactive, leftIcon, rightIcon, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(badgeVariants({ variant, size, interactive }), className)}
        {...props}
      >
        {leftIcon && <span className="w-3 h-3 flex-shrink-0">{leftIcon}</span>}
        {children && <span>{children}</span>}
        {rightIcon && <span className="w-3 h-3 flex-shrink-0">{rightIcon}</span>}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

// Status Badge presets for common use cases
export const StatusBadge = React.forwardRef<
  HTMLSpanElement,
  Omit<BadgeProps, 'variant'> & {
    status: 'online' | 'offline' | 'pending' | 'success' | 'error' | 'warning';
  }
>(({ status, ...props }, ref) => {
  const statusConfig = {
    online: { variant: 'success' as const, leftIcon: <div className="w-2 h-2 bg-success-500 rounded-full" /> },
    offline: { variant: 'error' as const, leftIcon: <div className="w-2 h-2 bg-error-500 rounded-full" /> },
    pending: { variant: 'warning' as const, leftIcon: <div className="w-2 h-2 bg-warning-500 rounded-full" /> },
    success: { variant: 'success' as const, leftIcon: <div className="w-2 h-2 bg-success-500 rounded-full" /> },
    error: { variant: 'error' as const, leftIcon: <div className="w-2 h-2 bg-error-500 rounded-full" /> },
    warning: { variant: 'warning' as const, leftIcon: <div className="w-2 h-2 bg-warning-500 rounded-full" /> },
  };

  const config = statusConfig[status];

  return (
    <Badge
      ref={ref}
      variant={config.variant}
      leftIcon={config.leftIcon}
      {...props}
    />
  );
});

StatusBadge.displayName = 'StatusBadge';

export { Badge, badgeVariants };