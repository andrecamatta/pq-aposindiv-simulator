import React, { type ReactNode, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const drawerContentVariants = cva(
  "fixed top-0 bottom-0 right-0 bg-white shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col",
  {
    variants: {
      size: {
        sm: "w-full max-w-md",
        md: "w-full max-w-xl",
        lg: "w-full max-w-2xl",
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
);

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
  showCloseButton?: boolean;
  closeOnOverlay?: boolean;
  className?: string;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
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

  // Prevent body scroll when drawer is open
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

  const drawerContent = (
    <>
      {/* Overlay - completamente opaco para evitar confusão visual */}
      <div
        className="fixed inset-0 transition-opacity duration-300 ease-out z-40"
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: '#111827',
          zIndex: 40
        }}
        onClick={closeOnOverlay ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Drawer Panel */}
      <div
        className={cn(
          drawerContentVariants({ size }),
          className,
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
        style={{ top: 0, bottom: 0, right: 0 }}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "drawer-title" : undefined}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-start justify-between px-6 py-5 border-b border-gray-200 flex-shrink-0">
            <div className="flex-1">
              {title && (
                <h2 id="drawer-title" className="text-xl font-bold text-gray-900">
                  {title}
                </h2>
              )}
              {subtitle && (
                <p className="mt-1 text-sm text-gray-600">
                  {subtitle}
                </p>
              )}
            </div>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="ml-4 p-2 rounded-lg hover:bg-gray-100 transition-colors group flex-shrink-0"
                aria-label="Fechar painel"
              >
                <X className="w-5 h-5 text-gray-400 group-hover:text-gray-600" />
              </button>
            )}
          </div>
        )}

        {/* Content - scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {children}
        </div>

        {/* Footer - fixed at bottom */}
        {footer && (
          <div className="flex-shrink-0">
            {footer}
          </div>
        )}
      </div>
    </>
  );

  return createPortal(drawerContent, document.body);
};

interface DrawerFooterProps {
  children: ReactNode;
  className?: string;
}

export const DrawerFooter: React.FC<DrawerFooterProps> = ({ children, className }) => {
  return (
    <div className={cn(
      "flex items-center justify-end gap-3 px-6 py-4 bg-gray-50 border-t border-gray-200 flex-shrink-0",
      className
    )}>
      {children}
    </div>
  );
};

export default Drawer;
