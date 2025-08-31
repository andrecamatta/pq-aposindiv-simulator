import React, { useState, useRef, useEffect } from 'react';
import { InfoIcon } from 'lucide-react';

interface InfoTooltipProps {
  content: string;
  className?: string;
  iconSize?: number;
}

const InfoTooltip: React.FC<InfoTooltipProps> = ({
  content,
  className = '',
  iconSize = 16,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState<'left' | 'right' | 'center'>('center');
  const buttonRef = useRef<HTMLButtonElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isVisible && buttonRef.current && tooltipRef.current) {
      const buttonRect = buttonRef.current.getBoundingClientRect();
      const tooltipWidth = 400; // Reduced from 560px for better fit
      const viewportWidth = window.innerWidth;
      const leftSpace = buttonRect.left;
      const rightSpace = viewportWidth - buttonRect.right;

      // Check if tooltip would be cut off on the left
      if (leftSpace < tooltipWidth / 2) {
        setPosition('left');
      }
      // Check if tooltip would be cut off on the right
      else if (rightSpace < tooltipWidth / 2) {
        setPosition('right');
      }
      // Default to center if there's enough space
      else {
        setPosition('center');
      }
    }
  }, [isVisible]);

  const getTooltipStyles = () => {
    const baseStyles = {
      width: '400px',
      backgroundColor: '#FFFFFF',
    };

    switch (position) {
      case 'left':
        return {
          ...baseStyles,
          left: '0',
          transform: 'translateX(0)',
        };
      case 'right':
        return {
          ...baseStyles,
          right: '0',
          transform: 'translateX(0)',
        };
      default:
        return {
          ...baseStyles,
          left: '50%',
          transform: 'translateX(-50%)',
        };
    }
  };

  const getArrowPosition = () => {
    switch (position) {
      case 'left':
        return 'left-4';
      case 'right':
        return 'right-4';
      default:
        return 'left-1/2 -translate-x-1/2';
    }
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        ref={buttonRef}
        type="button"
        className="text-gray-500 hover:text-blue-600 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 rounded-full"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        aria-label="Informação adicional"
      >
        <InfoIcon size={iconSize} className="drop-shadow-sm" />
      </button>
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className="absolute z-[9999] p-3 mt-2 text-sm text-gray-700 bg-white border border-gray-200 rounded-lg shadow-xl backdrop-blur-sm"
          style={getTooltipStyles()}
        >
          {/* Seta do tooltip */}
          <div className={`absolute -top-1 transform ${getArrowPosition()}`}>
            <div className="w-2 h-2 bg-white border-l border-t border-gray-200 rotate-45"></div>
          </div>
          
          {/* Conteúdo */}
          <div className="relative">
            <div className="font-medium text-blue-700 mb-1 text-xs uppercase tracking-wide">
              ℹ️ Observação Técnica
            </div>
            <div className="text-gray-800 leading-relaxed">
              {content}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InfoTooltip;