import React from 'react';
import { Loader2 } from 'lucide-react';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const spinnerVariants = cva(
  "animate-spin",
  {
    variants: {
      size: {
        sm: "w-4 h-4",
        md: "w-6 h-6",
        lg: "w-8 h-8",
        xl: "w-10 h-10",
      },
      variant: {
        default: "text-primary-600",
        white: "text-white",
        muted: "text-slate-400",
      }
    },
    defaultVariants: {
      size: "md",
      variant: "default",
    }
  }
);

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'white' | 'muted';
  className?: string;
  text?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = "md",
  variant = "default",
  className,
  text
}) => {
  if (text) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        <Loader2 className={spinnerVariants({ size, variant })} />
        <span className={cn(
          "text-sm font-medium",
          variant === "white" ? "text-white" : 
          variant === "muted" ? "text-slate-500" : "text-slate-700"
        )}>
          {text}
        </span>
      </div>
    );
  }

  return (
    <Loader2 className={cn(spinnerVariants({ size, variant }), className)} />
  );
};

export default LoadingSpinner;