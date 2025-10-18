/**
 * Resource Utilization Chart - displays resource allocation over time
 * TODO: Integrate with chart library for stacked bar chart
 */

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { getResourceAnalytics } from '@/lib/api/analytics';

interface ResourceUtilizationChartProps {
  projectId: string;
}

export default function ResourceUtilizationChart({ projectId }: ResourceUtilizationChartProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'resources', projectId],
    queryFn: () => getResourceAnalytics(projectId),
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
          Failed to load resource data. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resource Utilization</CardTitle>
        <CardDescription>
          Resource allocation and utilization over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* TODO: Replace with stacked bar chart */}
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">Total Resources</div>
              <div className="text-2xl font-bold">{data?.total_resources}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">Allocated</div>
              <div className="text-2xl font-bold">{data?.allocated_resources}</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">Utilization</div>
              <div className="text-2xl font-bold">{data?.utilization_pct.toFixed(1)}%</div>
            </div>
          </div>

          {data?.over_allocated && data.over_allocated.length > 0 && (
            <div className="border-t pt-4">
              <h4 className="font-semibold mb-2 text-red-600">Over-Allocated Resources ({data.over_allocated.length})</h4>
              <div className="space-y-2">
                {data.over_allocated.map((resource) => (
                  <div key={resource.resource_id} className="bg-red-50 p-3 rounded">
                    <div className="font-medium">{resource.resource_name}</div>
                    <div className="text-sm text-gray-800">
                      {resource.allocation_pct.toFixed(1)}% allocated ({resource.tasks_assigned} tasks)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {data?.under_utilized && data.under_utilized.length > 0 && (
            <div className="border-t pt-4">
              <h4 className="font-semibold mb-2 text-yellow-600">Under-Utilized Resources ({data.under_utilized.length})</h4>
              <div className="space-y-2">
                {data.under_utilized.map((resource) => (
                  <div key={resource.resource_id} className="bg-yellow-50 p-3 rounded">
                    <div className="font-medium">{resource.resource_name}</div>
                    <div className="text-sm text-gray-800">
                      {resource.allocation_pct.toFixed(1)}% allocated ({resource.tasks_assigned} tasks)
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
