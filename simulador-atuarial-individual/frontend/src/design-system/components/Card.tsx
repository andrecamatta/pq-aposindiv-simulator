import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

// S-Tier Card Component for content containers
const cardVariants = cva(
  [
    'bg-white rounded-lg',
    'transition-all duration-150 ease-in-out',
  ],
  {
    variants: {
      variant: {
        default: 'shadow-sm',
        elevated: 'shadow-md hover:shadow-lg border border-gray-100',
        flat: 'shadow-none',
        minimal: 'shadow-none border-none',
        interactive: 'cursor-pointer shadow-sm hover:shadow-md active:scale-[0.99]',
      },
      padding: {
        none: 'p-0',
        xs: 'p-3',
        sm: 'p-4',
        md: 'p-5',
        lg: 'p-6',
        xl: 'p-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      padding: 'sm',
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, padding, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, padding }), className)}
      {...props}
    />
  )
);
Card.displayName = 'Card';

// Card Header Component
const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    withBorder?: boolean;
  }
>(({ className, withBorder = false, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex flex-col space-y-1.5 pb-4',
      withBorder && 'border-b border-gray-100',
      className
    )}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

// Card Title Component
const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement> & {
    as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
  }
>(({ className, as: Component = 'h3', ...props }, ref) => (
  <Component
    ref={ref}
    className={cn('text-lg font-semibold text-gray-900 leading-none tracking-tight', className)}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

// Card Description Component
const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-gray-600', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

// Card Content Component
const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('pt-0', className)}
    {...props}
  />
));
CardContent.displayName = 'CardContent';

// Card Footer Component
const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    withBorder?: boolean;
  }
>(({ className, withBorder = false, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex items-center pt-4',
      withBorder && 'border-t border-gray-100',
      className
    )}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  cardVariants,
};