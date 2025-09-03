import React, { useState, useRef, useEffect } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';
import { ChevronDown } from 'lucide-react';

const selectVariants = cva(
  [
    'flex w-full items-center justify-between border border-[#dbe2e6] bg-white px-4 py-3 text-base text-[#111618]',
    'transition-all duration-150 ease-in-out cursor-pointer rounded-md',
    'focus:border-[#13a4ec] focus:ring-1 focus:ring-[#13a4ec] focus:ring-opacity-20 focus:outline-none',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50',
    'aria-invalid:border-red-500 aria-invalid:ring-red-500 aria-invalid:ring-opacity-20',
  ],
  {
    variants: {
      size: {
        sm: 'h-9 px-2 text-xs',
        md: 'h-11 px-3 text-sm',
        lg: 'h-12 px-4 text-base',
      },
      variant: {
        default: '',
        success: 'border-success-500 ring-success-500 ring-opacity-20',
        error: 'border-error-500 ring-error-500 ring-opacity-20',
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'default',
    },
  }
);

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps
  extends Omit<React.HTMLAttributes<HTMLDivElement>, 'size'>,
    VariantProps<typeof selectVariants> {
  label?: string;
  helperText?: string;
  error?: string;
  options: SelectOption[];
  placeholder?: string;
  loading?: boolean;
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  name?: string;
}

const Select = React.forwardRef<HTMLDivElement, SelectProps>(
  (
    {
      className,
      size,
      variant,
      label,
      helperText,
      error,
      options,
      placeholder,
      loading,
      value,
      onChange,
      disabled,
      name,
      id,
      'aria-invalid': ariaInvalid,
      ...props
    },
    ref
  ) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedValue, setSelectedValue] = useState(value || '');
    const containerRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const listRef = useRef<HTMLUListElement>(null);
    const reactId = React.useId();
    const selectId = id || `select-${reactId}`;
    const hasError = Boolean(error);
    const actualVariant = hasError ? 'error' : variant;
    const isInvalid = ariaInvalid || hasError;

    // Encontrar a opção selecionada
    const selectedOption = options.find(option => option.value === selectedValue);
    const displayText = selectedOption?.label || placeholder || 'Selecione...';

    // Sincronizar com prop value externa
    useEffect(() => {
      if (value !== undefined) {
        setSelectedValue(value);
      }
    }, [value]);

    // Fechar dropdown quando clicar fora
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
          setIsOpen(false);
        }
      };

      if (isOpen) {
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
      }
    }, [isOpen]);

    // Navegação por teclado
    const handleKeyDown = (event: React.KeyboardEvent) => {
      if (disabled || loading) return;

      switch (event.key) {
        case 'Enter':
        case ' ':
          event.preventDefault();
          setIsOpen(!isOpen);
          break;
        case 'Escape':
          setIsOpen(false);
          buttonRef.current?.focus();
          break;
        case 'ArrowDown':
          event.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
          } else {
            // Focar no primeiro item da lista
            const firstItem = listRef.current?.querySelector('[role="option"]') as HTMLElement;
            firstItem?.focus();
          }
          break;
        case 'ArrowUp':
          event.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
          } else {
            // Focar no último item da lista
            const items = listRef.current?.querySelectorAll('[role="option"]');
            const lastItem = items?.[items.length - 1] as HTMLElement;
            lastItem?.focus();
          }
          break;
      }
    };

    const handleOptionClick = (optionValue: string) => {
      if (disabled || loading) return;
      
      setSelectedValue(optionValue);
      setIsOpen(false);
      onChange?.(optionValue);
      buttonRef.current?.focus();
    };

    const handleOptionKeyDown = (event: React.KeyboardEvent, optionValue: string, index: number) => {
      switch (event.key) {
        case 'Enter':
        case ' ':
          event.preventDefault();
          handleOptionClick(optionValue);
          break;
        case 'Escape':
          setIsOpen(false);
          buttonRef.current?.focus();
          break;
        case 'ArrowDown':
          event.preventDefault();
          const nextIndex = (index + 1) % options.length;
          const nextItem = listRef.current?.children[nextIndex] as HTMLElement;
          nextItem?.focus();
          break;
        case 'ArrowUp':
          event.preventDefault();
          const prevIndex = index === 0 ? options.length - 1 : index - 1;
          const prevItem = listRef.current?.children[prevIndex] as HTMLElement;
          prevItem?.focus();
          break;
      }
    };

    return (
      <div className="space-y-2" ref={containerRef}>
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-medium text-[#111618] mb-2"
          >
            {label}
          </label>
        )}
        
        <div className="relative" ref={ref} {...props}>
          <button
            ref={buttonRef}
            type="button"
            className={cn(
              selectVariants({ size, variant: actualVariant, className })
            )}
            id={selectId}
            disabled={disabled || loading}
            aria-invalid={isInvalid}
            aria-expanded={isOpen}
            aria-haspopup="listbox"
            aria-describedby={
              error ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined
            }
            onClick={() => !disabled && !loading && setIsOpen(!isOpen)}
            onKeyDown={handleKeyDown}
          >
            <span className={cn(
              'block truncate text-left',
              !selectedOption && 'text-[#9ca3af]'
            )}>
              {displayText}
            </span>
            
            <span className="flex items-center ml-2">
              {loading ? (
                <div className="w-5 h-5 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
              ) : (
                <ChevronDown className={cn(
                  'w-5 h-5 text-[#617c89] transition-transform duration-200',
                  isOpen && 'rotate-180'
                )} />
              )}
            </span>
          </button>

          {/* Dropdown */}
          {isOpen && !disabled && !loading && (
            <ul
              ref={listRef}
              className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto focus:outline-none"
              role="listbox"
              aria-labelledby={selectId}
            >
              {options.map((option, index) => (
                <li
                  key={option.value}
                  className={cn(
                    'cursor-pointer select-none relative px-3 py-2 focus:outline-none',
                    option.disabled && 'opacity-50 cursor-not-allowed',
                    selectedValue === option.value 
                      ? 'bg-white text-gray-900 font-medium' 
                      : 'bg-white hover:bg-gray-100 focus:bg-gray-100'
                  )}
                  role="option"
                  tabIndex={-1}
                  aria-selected={selectedValue === option.value}
                  aria-disabled={option.disabled}
                  onClick={() => !option.disabled && handleOptionClick(option.value)}
                  onKeyDown={(e) => !option.disabled && handleOptionKeyDown(e, option.value, index)}
                >
                  <span className="block truncate">{option.label}</span>
                  {selectedValue === option.value && (
                    <span className="absolute inset-y-0 right-0 flex items-center pr-3 text-[#13a4ec]">
                      <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
        
        {error && (
          <p
            id={`${selectId}-error`}
            className="text-sm text-error-600"
            role="alert"
          >
            {error}
          </p>
        )}
        
        {helperText && !error && (
          <p
            id={`${selectId}-helper`}
            className="text-sm text-gray-500"
          >
            {helperText}
          </p>
        )}

        {/* Hidden input para compatibilidade com forms */}
        {name && (
          <input
            type="hidden"
            name={name}
            value={selectedValue}
          />
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

export { Select, selectVariants };