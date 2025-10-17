/**
 * RiskIndicator Component
 *
 * Displays a color-coded risk level badge with optional tooltip.
 * Supports three risk levels: low, medium, high.
 */

import * as React from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface RiskIndicatorProps {
  /** Risk level */
  riskLevel: 'low' | 'medium' | 'high';
  /** Optional numeric risk score (0-100) */
  riskScore?: number;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Custom className */
  className?: string;
}

/**
 * Risk level configuration
 */
const RISK_CONFIG = {
  low: {
    label: 'Low Risk',
    description: 'Project is on track with minimal risks',
    bgColor: 'bg-green-100',
    textColor: 'text-green-800',
    borderColor: 'border-green-300',
    icon: CheckCircle,
  },
  medium: {
    label: 'Medium Risk',
    description: 'Some risks identified that need attention',
    bgColor: 'bg-yellow-100',
    textColor: 'text-yellow-800',
    borderColor: 'border-yellow-300',
    icon: AlertTriangle,
  },
  high: {
    label: 'High Risk',
    description: 'Significant risks require immediate action',
    bgColor: 'bg-red-100',
    textColor: 'text-red-800',
    borderColor: 'border-red-300',
    icon: XCircle,
  },
} as const;

/**
 * Size configuration
 */
const SIZE_CONFIG = {
  sm: {
    padding: 'px-2 py-1',
    text: 'text-xs',
    icon: 'h-3 w-3',
  },
  md: {
    padding: 'px-3 py-1.5',
    text: 'text-sm',
    icon: 'h-4 w-4',
  },
  lg: {
    padding: 'px-4 py-2',
    text: 'text-base',
    icon: 'h-5 w-5',
  },
} as const;

export default function RiskIndicator({
  riskLevel,
  riskScore,
  size = 'md',
  className,
}: RiskIndicatorProps) {
  const config = RISK_CONFIG[riskLevel];
  const sizeConfig = SIZE_CONFIG[size];
  const Icon = config.icon;

  // Build aria label
  const ariaLabel = riskScore
    ? `${config.label}: Risk score ${riskScore} out of 100. ${config.description}`
    : `${config.label}: ${config.description}`;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-2 rounded-full border font-medium',
        config.bgColor,
        config.textColor,
        config.borderColor,
        sizeConfig.padding,
        sizeConfig.text,
        className
      )}
      role="status"
      aria-label={ariaLabel}
      title={ariaLabel}
    >
      <Icon className={cn(sizeConfig.icon)} aria-hidden="true" />
      <span>{config.label}</span>
      {riskScore !== undefined && (
        <span className="font-bold">({riskScore})</span>
      )}
    </div>
  );
}
