import React from 'react';
import { cn } from '../../lib/utils';

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'rectangular' | 'circular' | 'text' | 'rounded';
  width?: string | number;
  height?: string | number;
  lines?: number;
}

const Skeleton: React.FC<SkeletonProps> = ({
  className,
  variant = 'rectangular',
  width,
  height,
  lines = 1,
  ...props
}) => {
  const baseClasses = 'bg-gray-200 animate-pulse';
  
  const variantClasses = {
    rectangular: 'rounded-none',
    circular: 'rounded-full',
    text: 'rounded-sm',
    rounded: 'rounded-md',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  if (variant === 'text' && lines > 1) {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={cn(
              baseClasses,
              variantClasses.text,
              'h-4',
              index === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full',
              className
            )}
            style={index === 0 ? style : undefined}
            {...props}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(
        baseClasses,
        variantClasses[variant],
        {
          'h-4': variant === 'text' && !height,
          'h-12 w-12': variant === 'circular' && !width && !height,
          'h-24': variant === 'rectangular' && !height,
        },
        className
      )}
      style={style}
      {...props}
    />
  );
};

// Preset skeleton components for common use cases
const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('p-6 border border-gray-200 rounded-lg space-y-4', className)}>
    <Skeleton variant="text" height={24} className="w-1/2" />
    <Skeleton variant="text" lines={3} />
    <div className="flex space-x-4 mt-4">
      <Skeleton variant="rectangular" width={80} height={32} className="rounded-md" />
      <Skeleton variant="rectangular" width={80} height={32} className="rounded-md" />
    </div>
  </div>
);

const SkeletonAvatar: React.FC<{ 
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({ 
  size = 'md', 
  className 
}) => {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-12 w-12',
    lg: 'h-16 w-16',
  };

  return (
    <Skeleton
      variant="circular"
      className={cn(sizeClasses[size], className)}
    />
  );
};

const SkeletonButton: React.FC<{ 
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}> = ({ 
  size = 'md', 
  className 
}) => {
  const sizeClasses = {
    sm: 'h-8 w-20',
    md: 'h-9 w-24',
    lg: 'h-10 w-28',
  };

  return (
    <Skeleton
      variant="rounded"
      className={cn(sizeClasses[size], className)}
    />
  );
};

const SkeletonTable: React.FC<{ 
  columns?: number;
  rows?: number;
  className?: string;
}> = ({ 
  columns = 4, 
  rows = 5, 
  className 
}) => (
  <div className={cn('border border-gray-200 rounded-lg overflow-hidden', className)}>
    {/* Header */}
    <div className="bg-gray-50 p-4 border-b border-gray-200">
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={index} variant="text" height={16} className="w-3/4" />
        ))}
      </div>
    </div>
    
    {/* Rows */}
    <div className="divide-y divide-gray-200">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="p-4">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton key={colIndex} variant="text" height={16} />
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

const SkeletonChart: React.FC<{ className?: string }> = ({ className }) => (
  <div className={cn('p-6 border border-gray-200 rounded-lg', className)}>
    <Skeleton variant="text" height={20} className="w-1/3 mb-4" />
    <div className="h-64 flex items-end space-x-2">
      {Array.from({ length: 12 }).map((_, index) => (
        <Skeleton
          key={index}
          variant="rectangular"
          className="flex-1"
          height={Math.random() * 200 + 50}
        />
      ))}
    </div>
  </div>
);

export {
  Skeleton,
  SkeletonCard,
  SkeletonAvatar,
  SkeletonButton,
  SkeletonTable,
  SkeletonChart,
};