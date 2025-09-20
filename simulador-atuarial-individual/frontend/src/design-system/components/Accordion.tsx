import React, { useState, type ReactNode } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { cva } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const accordionVariants = cva(
  "border border-slate-200 rounded-xl bg-white shadow-sm transition-all duration-200",
  {
    variants: {
      state: {
        expanded: "shadow-md border-primary-200",
        collapsed: "hover:shadow-md hover:border-slate-300",
      },
    },
    defaultVariants: {
      state: "collapsed",
    },
  }
);

const accordionTriggerVariants = cva(
  "w-full flex items-center justify-between p-4 text-left transition-all duration-200 group",
  {
    variants: {
      state: {
        expanded: "bg-primary-50 text-primary-900 border-b border-primary-100",
        collapsed: "hover:bg-slate-50",
      },
    },
    defaultVariants: {
      state: "collapsed",
    },
  }
);

interface AccordionItemProps {
  id: string;
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  children: ReactNode;
  isExpanded: boolean;
  onToggle: (id: string) => void;
  className?: string;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  id,
  title,
  subtitle,
  icon,
  children,
  isExpanded,
  onToggle,
  className,
}) => {
  return (
    <div className={cn(accordionVariants({ state: isExpanded ? "expanded" : "collapsed" }), className)}>
      <button
        onClick={() => onToggle(id)}
        className={accordionTriggerVariants({ state: isExpanded ? "expanded" : "collapsed" })}
        aria-expanded={isExpanded}
        aria-controls={`accordion-content-${id}`}
      >
        <div className="flex items-center gap-3">
          {icon && (
            <div className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center transition-colors",
              isExpanded ? "bg-primary-100" : "bg-slate-100 group-hover:bg-slate-200"
            )}>
              {icon}
            </div>
          )}
          <div className="text-left">
            <div className="text-base font-semibold">{title}</div>
            {subtitle && (
              <div className={cn(
                "text-sm transition-colors",
                isExpanded ? "text-primary-600" : "text-slate-500"
              )}>
                {subtitle}
              </div>
            )}
          </div>
        </div>
        <div className={cn(
          "transition-transform duration-200",
          isExpanded ? "rotate-90" : "rotate-0"
        )}>
          <ChevronRight className="w-5 h-5" />
        </div>
      </button>

      {isExpanded && (
        <div 
          id={`accordion-content-${id}`}
          className="p-6 pt-0 animate-fade-in"
        >
          {children}
        </div>
      )}
    </div>
  );
};

interface AccordionProps {
  items: {
    id: string;
    title: string;
    subtitle?: string;
    icon?: ReactNode;
    content: ReactNode;
  }[];
  defaultExpanded?: string;
  allowMultiple?: boolean;
  className?: string;
}

export const Accordion: React.FC<AccordionProps> = ({
  items,
  defaultExpanded,
  allowMultiple = false,
  className,
}) => {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(
    new Set(defaultExpanded ? [defaultExpanded] : [])
  );

  const handleToggle = (id: string) => {
    if (allowMultiple) {
      setExpandedItems(prev => {
        const newSet = new Set(prev);
        if (newSet.has(id)) {
          newSet.delete(id);
        } else {
          newSet.add(id);
        }
        return newSet;
      });
    } else {
      setExpandedItems(prev => 
        prev.has(id) ? new Set() : new Set([id])
      );
    }
  };

  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item) => (
        <AccordionItem
          key={item.id}
          id={item.id}
          title={item.title}
          subtitle={item.subtitle}
          icon={item.icon}
          isExpanded={expandedItems.has(item.id)}
          onToggle={handleToggle}
        >
          {item.content}
        </AccordionItem>
      ))}
    </div>
  );
};

export default Accordion;