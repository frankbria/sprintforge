/**
 * Alert component for displaying important messages
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

interface AlertProps extends React.ComponentProps<'div'> {
  variant?: 'default' | 'destructive' | 'warning' | 'success';
}

const variantStyles = {
  default: 'bg-blue-50 border-blue-200 text-blue-900',
  destructive: 'bg-red-50 border-red-200 text-red-900',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
  success: 'bg-green-50 border-green-200 text-green-900',
};

function Alert({ variant = 'default', className, ...props }: AlertProps) {
  return (
    <div
      role="alert"
      className={cn(
        'relative w-full rounded-lg border p-4',
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
}

function AlertTitle({ className, ...props }: React.ComponentProps<'h5'>) {
  return (
    <h5
      className={cn('mb-1 font-medium leading-none tracking-tight', className)}
      {...props}
    />
  );
}

function AlertDescription({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      className={cn('text-sm [&_p]:leading-relaxed', className)}
      {...props}
    />
  );
}

export { Alert, AlertTitle, AlertDescription };
