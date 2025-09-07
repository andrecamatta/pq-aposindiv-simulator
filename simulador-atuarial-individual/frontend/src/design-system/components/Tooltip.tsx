import React, { useState, useRef, useEffect } from 'react';
import { cn } from '../../lib/utils';

interface TooltipProps {
  children: React.ReactNode;
  content: string | React.ReactNode;
  side?: 'top' | 'right' | 'bottom' | 'left';
  align?: 'start' | 'center' | 'end';
  sideOffset?: number;
  disabled?: boolean;
  className?: string;
}

const Tooltip: React.FC<TooltipProps> = ({
  children,
  content,
  side = 'top',
  align = 'center',
  sideOffset = 4,
  disabled = false,
  className,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const updatePosition = () => {
    if (!triggerRef.current || !tooltipRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const viewport = {
      width: window.innerWidth,
      height: window.innerHeight,
    };

    let x = 0;
    let y = 0;

    // Calculate position based on side
    switch (side) {
      case 'top':
        y = triggerRect.top - tooltipRect.height - sideOffset;
        x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        break;
      case 'bottom':
        y = triggerRect.bottom + sideOffset;
        x = triggerRect.left + triggerRect.width / 2 - tooltipRect.width / 2;
        break;
      case 'left':
        y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        x = triggerRect.left - tooltipRect.width - sideOffset;
        break;
      case 'right':
        y = triggerRect.top + triggerRect.height / 2 - tooltipRect.height / 2;
        x = triggerRect.right + sideOffset;
        break;
    }

    // Adjust for alignment
    if (side === 'top' || side === 'bottom') {
      switch (align) {
        case 'start':
          x = triggerRect.left;
          break;
        case 'end':
          x = triggerRect.right - tooltipRect.width;
          break;
      }
    } else {
      switch (align) {
        case 'start':
          y = triggerRect.top;
          break;
        case 'end':
          y = triggerRect.bottom - tooltipRect.height;
          break;
      }
    }

    // Keep tooltip within viewport
    x = Math.max(8, Math.min(x, viewport.width - tooltipRect.width - 8));
    y = Math.max(8, Math.min(y, viewport.height - tooltipRect.height - 8));

    setPosition({ x, y });
  };

  useEffect(() => {
    if (isVisible) {
      updatePosition();
      window.addEventListener('scroll', updatePosition);
      window.addEventListener('resize', updatePosition);
      
      return () => {
        window.removeEventListener('scroll', updatePosition);
        window.removeEventListener('resize', updatePosition);
      };
    }
  }, [isVisible, side, align, sideOffset]);

  const showTooltip = () => {
    if (!disabled) {
      setIsVisible(true);
    }
  };

  const hideTooltip = () => {
    setIsVisible(false);
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        className="inline-block"
      >
        {children}
      </div>

      {isVisible && !disabled && (
        <div
          ref={tooltipRef}
          className={cn(
            'fixed z-50 px-3 py-2 text-xs rounded-md shadow-lg',
            'animate-in fade-in-0 zoom-in-95',
            'break-words',
            // Estilos base que nunca devem ser sobrescritos
            '!bg-gray-900 !text-white',
            // Classes customizáveis (max-width, etc)
            className || 'max-w-xs'
          )}
          style={{
            left: position.x,
            top: position.y,
            // Forçar estilos inline para garantir que sejam aplicados
            backgroundColor: '#111827 !important', // gray-900
            color: '#ffffff !important',
            zIndex: 9999,
          }}
          role="tooltip"
        >
          {content}
          
          {/* Arrow */}
          <div
            className={cn(
              'absolute w-2 h-2 rotate-45',
              '!bg-gray-900', // Garantir que a seta também tenha o fundo correto
              {
                'bottom-[-4px] left-1/2 -translate-x-1/2': side === 'top',
                'top-[-4px] left-1/2 -translate-x-1/2': side === 'bottom',
                'right-[-4px] top-1/2 -translate-y-1/2': side === 'left',
                'left-[-4px] top-1/2 -translate-y-1/2': side === 'right',
              }
            )}
            style={{
              backgroundColor: '#111827', // gray-900 - forçar inline também
            }}
          />
        </div>
      )}
    </>
  );
};

export { Tooltip };