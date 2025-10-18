/**
 * Badge component for displaying unread notification count
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

interface NotificationBadgeProps {
  count: number;
  size?: 'sm' | 'md';
  className?: string;
}

export function NotificationBadge({
  count,
  size = 'md',
  className,
}: NotificationBadgeProps) {
  if (count === 0) {
    return null;
  }

  const displayCount = count > 99 ? '99+' : count.toString();

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center font-medium bg-red-500 text-white rounded-full',
        size === 'sm' && 'text-xs min-w-[16px] h-4 px-1',
        size === 'md' && 'text-xs min-w-[20px] h-5 px-1.5',
        className
      )}
      aria-label={`${count} unread notifications`}
    >
      {displayCount}
    </span>
  );
}
