import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

// S-Tier Button Component with professional variants and states
const buttonVariants = cva(
  // Base styles - always applied
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium',
    'transition-all duration-150 ease-in-out',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50',
    'active:scale-[0.98]', // Subtle press animation
  ],
  {
    variants: {
      variant: {
        // Primary - main action button
        primary: [
          'bg-primary-500 text-white shadow-button',
          'hover:bg-primary-600 hover:shadow-button-hover',
          'active:bg-primary-700',
        ],
        // Secondary - important but not primary action
        secondary: [
          'bg-gray-100 text-gray-900 shadow-button border border-gray-200',
          'hover:bg-gray-200 hover:shadow-button-hover hover:border-gray-300',
          'active:bg-gray-300',
        ],
        // Outline - less prominent action
        outline: [
          'bg-transparent text-gray-700 border border-gray-300 shadow-sm',
          'hover:bg-gray-50 hover:text-gray-900 hover:border-gray-400',
          'active:bg-gray-100',
        ],
        // Ghost - minimal styling
        ghost: [
          'bg-transparent text-gray-600 shadow-none',
          'hover:bg-gray-100 hover:text-gray-900',
          'active:bg-gray-200',
        ],
        // Destructive - for dangerous actions
        destructive: [
          'bg-error-500 text-white shadow-button',
          'hover:bg-error-600 hover:shadow-button-hover',
          'active:bg-error-700',
        ],
        // Success - for positive actions
        success: [
          'bg-success-500 text-white shadow-button',
          'hover:bg-success-600 hover:shadow-button-hover',
          'active:bg-success-700',
        ],
        // Link - text-style button
        link: [
          'bg-transparent text-primary-600 underline-offset-4 shadow-none p-0',
          'hover:underline hover:text-primary-700',
          'active:text-primary-800',
        ],
      },
      size: {
        xs: 'h-7 px-2 text-xs',
        sm: 'h-8 px-3 text-sm',
        md: 'h-9 px-4 text-sm',
        lg: 'h-10 px-6 text-base',
        xl: 'h-11 px-8 text-base',
        icon: 'h-9 w-9 p-0',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          // Loading spinner
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
        ) : (
          leftIcon && <span className="w-4 h-4 flex-shrink-0">{leftIcon}</span>
        )}
        
        {children && <span>{children}</span>}
        
        {!loading && rightIcon && (
          <span className="w-4 h-4 flex-shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };