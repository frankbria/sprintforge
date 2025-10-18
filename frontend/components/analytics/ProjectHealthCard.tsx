/**
 * Project Health Card - displays overall project health score
 * TODO: Integrate with chart library (Recharts) for gauge visualization
 */

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface ProjectHealthCardProps {
  healthScore: number; // 0-100
}

export default function ProjectHealthCard({ healthScore }: ProjectHealthCardProps) {
  // Determine health status and color
  const getHealthStatus = (score: number) => {
    if (score >= 70) return { status: 'Excellent', color: 'text-green-600', bgColor: 'bg-green-100' };
    if (score >= 40) return { status: 'Fair', color: 'text-yellow-600', bgColor: 'bg-yellow-100' };
    return { status: 'At Risk', color: 'text-red-600', bgColor: 'bg-red-100' };
  };

  const { status, color, bgColor } = getHealthStatus(healthScore);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Project Health Score</CardTitle>
        <CardDescription>
          Overall project health based on multiple factors
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            {/* TODO: Replace with gauge chart */}
            <div className="relative w-32 h-32 mx-auto">
              <div className={cn('absolute inset-0 flex items-center justify-center rounded-full', bgColor)}>
                <div className="text-center">
                  <div className={cn('text-3xl font-bold', color)}>{healthScore}</div>
                  <div className="text-xs text-gray-800">out of 100</div>
                </div>
              </div>
            </div>
          </div>
          <div className="flex-1 text-center">
            <div className={cn('text-2xl font-semibold mb-2', color)}>{status}</div>
            <div className="text-sm text-gray-800 space-y-1">
              <p>Schedule adherence: {healthScore >= 70 ? 'On track' : 'Behind'}</p>
              <p>Resource utilization: {healthScore >= 70 ? 'Optimal' : 'Review needed'}</p>
              <p>Risk level: {healthScore >= 70 ? 'Low' : healthScore >= 40 ? 'Medium' : 'High'}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
