/**
 * VarianceIndicator Component
 *
 * Displays task variance status with color-coded badges.
 * Shows whether a task is ahead, behind, or on track relative to baseline.
 *
 * Implemented following TDD RED-GREEN-REFACTOR cycle.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { ArrowDown, ArrowUp, Minus } from 'lucide-react';

export interface VarianceIndicatorProps {
  /** Variance in days (negative = ahead, positive = behind, 0 = on track) */
  varianceDays: number;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Whether to show the text label */
  showLabel?: boolean;
  /** Additional CSS classes */
  className?: string;
}

interface VarianceStyle {
  text: string;
  bg: string;
  border: string;
  icon: typeof ArrowDown | typeof ArrowUp | typeof Minus;
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs gap-1',
  md: 'px-2.5 py-1 text-sm gap-1.5',
  lg: 'px-3 py-1.5 text-base gap-2',
};

const iconSizes = {
  sm: 12,
  md: 14,
  lg: 16,
};

export function VarianceIndicator({
  varianceDays,
  size = 'md',
  showLabel = true,
  className,
}: VarianceIndicatorProps) {
  // Determine variance status and styling
  const getVarianceStyle = (): VarianceStyle => {
    if (varianceDays < 0) {
      // Ahead of baseline
      return {
        text: 'text-green-700',
        bg: 'bg-green-50',
        border: 'border-green-200',
        icon: ArrowDown,
      };
    } else if (varianceDays > 0) {
      // Behind baseline
      return {
        text: 'text-red-700',
        bg: 'bg-red-50',
        border: 'border-red-200',
        icon: ArrowUp,
      };
    } else {
      // On track
      return {
        text: 'text-gray-700',
        bg: 'bg-gray-50',
        border: 'border-gray-200',
        icon: Minus,
      };
    }
  };

  const style = getVarianceStyle();
  const Icon = style.icon;
  const absoluteDays = Math.abs(varianceDays);

  // Generate display text
  const getDisplayText = (): string => {
    if (varianceDays < 0) {
      const dayText = absoluteDays === 1 ? 'day' : 'days';
      return `${absoluteDays} ${dayText} ahead`;
    } else if (varianceDays > 0) {
      const dayText = absoluteDays === 1 ? 'day' : 'days';
      return `${absoluteDays} ${dayText} behind`;
    } else {
      return 'On track';
    }
  };

  // Generate aria-label for accessibility
  const getAriaLabel = (): string => {
    if (varianceDays < 0) {
      return `${absoluteDays} days ahead of baseline`;
    } else if (varianceDays > 0) {
      return `${absoluteDays} days behind baseline`;
    } else {
      return 'On track with baseline';
    }
  };

  const displayText = getDisplayText();
  const ariaLabel = getAriaLabel();

  return (
    <span
      role="status"
      aria-label={ariaLabel}
      className={cn(
        'inline-flex items-center rounded-md border font-medium',
        style.bg,
        style.text,
        style.border,
        sizeClasses[size],
        className
      )}
    >
      <Icon size={iconSizes[size]} className="flex-shrink-0" />
      {showLabel && <span>{displayText}</span>}
    </span>
  );
}
