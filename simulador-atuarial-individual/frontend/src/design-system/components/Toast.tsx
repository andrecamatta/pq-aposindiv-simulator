import React from 'react';
import { Icon } from './Icon';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const toastVariants = cva(
  "relative flex w-full items-center justify-between space-x-4 overflow-hidden rounded-xl border p-4 pr-8 shadow-lg transition-all",
  {
    variants: {
      variant: {
        default: "border-slate-200 bg-white text-slate-950",
        success: "border-success-200 bg-success-50 text-success-800",
        error: "border-error-200 bg-error-50 text-error-800",
        warning: "border-warning-200 bg-warning-50 text-warning-800",
        info: "border-info-200 bg-info-50 text-info-800",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

interface ToastProps {
  title: string;
  description?: string;
  variant?: 'default' | 'success' | 'error' | 'warning' | 'info';
  onClose?: () => void;
  className?: string;
}

const Toast: React.FC<ToastProps> = ({
  title,
  description,
  variant = "default",
  onClose,
  className,
}) => {
  const getIcon = () => {
    switch (variant) {
      case 'success':
        return <Icon name="check-circle" size="md" color="success" />;
      case 'error':
        return <Icon name="x-circle" size="md" color="error" />;
      case 'warning':
        return <Icon name="alert-triangle" size="md" color="warning" />;
      case 'info':
        return <Icon name="info" size="md" className="text-info-600" />;
      default:
        return <Icon name="info" size="md" color="neutral" />;
    }
  };

  return (
    <div className={cn(toastVariants({ variant }), className)}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-0.5">
          {getIcon()}
        </div>
        <div className="flex-1 space-y-1">
          <div className="text-sm font-semibold leading-tight">
            {title}
          </div>
          {description && (
            <div className="text-sm opacity-90">
              {description}
            </div>
          )}
        </div>
      </div>
      
      {onClose && (
        <button
          onClick={onClose}
          className="absolute right-2 top-2 rounded-md p-1 hover:bg-black/10 transition-colors"
          aria-label="Close notification"
        >
          <Icon name="close" size="sm" />
        </button>
      )}
      
      {/* Progress bar for auto-dismiss */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/10 overflow-hidden">
        <div className="h-full bg-current opacity-20 animate-[shrink_4s_linear_forwards]" />
      </div>
    </div>
  );
};

export default Toast;