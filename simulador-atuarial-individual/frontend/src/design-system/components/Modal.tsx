import React, { type ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const modalVariants = cva(
  "fixed inset-0 z-50 flex items-center justify-center p-4",
  {
    variants: {
      size: {
        sm: "",
        md: "",
        lg: "",
        xl: "",
        full: "",
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
);

const modalContentVariants = cva(
  "relative bg-white rounded-xl shadow-2xl transform transition-all duration-300 ease-out max-h-[90vh] overflow-hidden",
  {
    variants: {
      size: {
        sm: "w-full max-w-sm",
        md: "w-full max-w-md",
        lg: "w-full max-w-2xl",
        xl: "w-full max-w-4xl",
        full: "w-full max-w-7xl h-[90vh]",
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
);

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showCloseButton?: boolean;
  closeOnOverlay?: boolean;
  className?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  size = "md",
  showCloseButton = true,
  closeOnOverlay = true,
  className,
}) => {
  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 transition-opacity duration-300 ease-out z-40"
        onClick={closeOnOverlay ? onClose : undefined}
        aria-hidden="true"
      />
      
      {/* Modal */}
      <div className={modalVariants({ size })}>
        <div 
          className={cn(modalContentVariants({ size }), className)}
          onClick={(e) => e.stopPropagation()}
          role="dialog"
          aria-modal="true"
          aria-labelledby={title ? "modal-title" : undefined}
        >
          {/* Header */}
          {(title || showCloseButton) && (
            <div className="flex items-start justify-between p-6 pb-4 border-b border-slate-200">
              <div className="flex-1">
                {title && (
                  <h2 id="modal-title" className="text-xl font-bold text-slate-900">
                    {title}
                  </h2>
                )}
                {subtitle && (
                  <p className="mt-1 text-sm text-slate-600">
                    {subtitle}
                  </p>
                )}
              </div>
              {showCloseButton && (
                <button
                  onClick={onClose}
                  className="ml-4 p-2 rounded-lg hover:bg-slate-100 transition-colors group"
                  aria-label="Fechar modal"
                >
                  <X className="w-5 h-5 text-slate-400 group-hover:text-slate-600" />
                </button>
              )}
            </div>
          )}

          {/* Content */}
          <div className={cn(
            "overflow-y-auto",
            size === "full" ? "flex-1 p-6" : "p-6",
            title || showCloseButton ? "pt-4" : ""
          )}>
            {children}
          </div>
        </div>
      </div>
    </>
  );
};

interface ModalFooterProps {
  children: ReactNode;
  className?: string;
}

export const ModalFooter: React.FC<ModalFooterProps> = ({ children, className }) => {
  return (
    <div className={cn("flex items-center justify-end gap-3 px-6 py-4 bg-slate-50 border-t border-slate-200", className)}>
      {children}
    </div>
  );
};

export default Modal;