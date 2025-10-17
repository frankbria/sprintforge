/**
 * Skeleton component for loading states
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps extends React.ComponentProps<'div'> {
  variant?: 'default' | 'text' | 'circular' | 'rectangular';
}

function Skeleton({ variant = 'default', className, ...props }: SkeletonProps) {
  const variantClass = {
    default: 'rounded-md',
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-none',
  }[variant];

  return (
    <div
      className={cn('animate-pulse bg-gray-200', variantClass, className)}
      {...props}
    />
  );
}

export { Skeleton };
