/**
 * Metrics Grid - displays key project metrics in a grid layout
 */

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import type { AnalyticsOverviewResponse } from '@/types/analytics';

interface MetricsGridProps {
  metrics: AnalyticsOverviewResponse;
}

export default function MetricsGrid({ metrics }: MetricsGridProps) {
  const gridMetrics = [
    {
      label: 'Critical Path Duration',
      value: `${metrics.critical_path_summary.total_duration} days`,
      icon: '🎯',
    },
    {
      label: 'Path Stability',
      value: `${metrics.critical_path_summary.path_stability_score.toFixed(1)}/100`,
      icon: '📊',
    },
    {
      label: 'Resource Utilization',
      value: `${metrics.resource_summary.utilization_pct.toFixed(1)}%`,
      icon: '👥',
    },
    {
      label: 'Completion Progress',
      value: `${metrics.progress_summary.completion_pct.toFixed(1)}%`,
      icon: '✅',
    },
    {
      label: 'Tasks Completed',
      value: `${metrics.progress_summary.tasks_completed} / ${metrics.progress_summary.tasks_total}`,
      icon: '📝',
    },
    {
      label: 'Risk Level',
      value: metrics.simulation_summary.risk_level.charAt(0).toUpperCase() + metrics.simulation_summary.risk_level.slice(1),
      icon: metrics.simulation_summary.risk_level === 'low' ? '🟢' : metrics.simulation_summary.risk_level === 'medium' ? '🟡' : '🔴',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {gridMetrics.map((metric, index) => (
        <Card key={index}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{metric.label}</CardTitle>
            <span className="text-2xl">{metric.icon}</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-900">{metric.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
