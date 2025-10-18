/**
 * Critical Path Visualization - displays critical path analysis
 * TODO: Integrate with chart library for network diagram or Gantt chart
 */

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { getCriticalPathAnalytics } from '@/lib/api/analytics';

interface CriticalPathVisualizationProps {
  projectId: string;
}

export default function CriticalPathVisualization({ projectId }: CriticalPathVisualizationProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'critical-path', projectId],
    queryFn: () => getCriticalPathAnalytics(projectId),
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load critical path data. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Critical Path Analysis</CardTitle>
        <CardDescription>
          Network diagram highlighting critical tasks and float time
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* TODO: Replace with interactive chart */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">Total Duration</div>
              <div className="text-2xl font-bold text-gray-900">{data?.total_duration} days</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">Critical Tasks</div>
              <div className="text-2xl font-bold text-gray-900">{data?.critical_tasks.length}</div>
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-900 mb-2">Path Stability Score</h4>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all"
                style={{ width: `${data?.path_stability_score}%` }}
              />
            </div>
            <div className="text-right text-sm text-gray-800 mt-1">
              {data?.path_stability_score.toFixed(1)}%
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-900 mb-2">Risk Tasks ({data?.risk_tasks.length})</h4>
            <div className="text-sm text-gray-800">
              Tasks with high risk factors that could impact the critical path
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
