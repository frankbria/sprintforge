/**
 * TrendIndicator Component
 *
 * Displays a trend indicator with up/down arrow and percentage change.
 * Color-coded: green for positive trends, red for negative trends.
 */

import * as React from 'react';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface TrendIndicatorProps {
  /** Current value */
  value: number;
  /** Previous value for comparison (optional) */
  previousValue?: number;
  /** Format type for display */
  format?: 'number' | 'percent' | 'currency';
  /** Whether higher values are better (default: true) */
  higherIsBetter?: boolean;
  /** Custom className */
  className?: string;
}

/**
 * Formats a number based on the specified format type
 */
function formatValue(value: number, format: 'number' | 'percent' | 'currency' = 'number'): string {
  switch (format) {
    case 'percent':
      return `${value.toFixed(1)}%`;
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    case 'number':
    default:
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(Math.round(value));
  }
}

/**
 * Calculates percentage change between two values
 */
function calculatePercentageChange(current: number, previous: number): number {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / Math.abs(previous)) * 100;
}

export default function TrendIndicator({
  value,
  previousValue,
  format = 'number',
  higherIsBetter = true,
  className,
}: TrendIndicatorProps) {
  // Calculate trend
  const hasTrend = previousValue !== undefined && previousValue !== null;
  const percentageChange = hasTrend ? calculatePercentageChange(value, previousValue!) : 0;
  const isPositive = percentageChange > 0;
  const isNegative = percentageChange < 0;
  const isNeutral = percentageChange === 0;

  // Determine if trend is good or bad based on direction and higherIsBetter
  const isGoodTrend = (isPositive && higherIsBetter) || (isNegative && !higherIsBetter);
  const isBadTrend = (isPositive && !higherIsBetter) || (isNegative && higherIsBetter);

  // Color classes
  const trendColorClass = isGoodTrend
    ? 'text-green-600'
    : isBadTrend
    ? 'text-red-600'
    : 'text-gray-700';

  const bgColorClass = isGoodTrend
    ? 'bg-green-50'
    : isBadTrend
    ? 'bg-red-50'
    : 'bg-gray-50';

  // Icon component
  const TrendIcon = isPositive ? ArrowUp : isNegative ? ArrowDown : Minus;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="text-2xl font-bold text-gray-900" aria-label={`Current value: ${formatValue(value, format)}`}>
        {formatValue(value, format)}
      </span>

      {hasTrend && (
        <div
          className={cn(
            'flex items-center gap-1 px-2 py-1 rounded-full text-sm font-medium',
            bgColorClass,
            trendColorClass
          )}
          role="status"
          aria-label={`${isGoodTrend ? 'Positive' : isBadTrend ? 'Negative' : 'Neutral'} trend: ${Math.abs(
            percentageChange
          ).toFixed(1)}% ${isPositive ? 'increase' : isNegative ? 'decrease' : 'no change'}`}
        >
          <TrendIcon className="h-4 w-4" aria-hidden="true" />
          <span>{Math.abs(percentageChange).toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
}
