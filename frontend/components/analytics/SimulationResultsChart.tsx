/**
 * Simulation Results Chart - displays Monte Carlo simulation histogram
 * TODO: Integrate with chart library for histogram visualization
 */

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { getSimulationAnalytics } from '@/lib/api/analytics';

interface SimulationResultsChartProps {
  projectId: string;
}

export default function SimulationResultsChart({ projectId }: SimulationResultsChartProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'simulation', projectId],
    queryFn: () => getSimulationAnalytics(projectId),
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
          Failed to load simulation data. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-800 bg-gray-100';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monte Carlo Simulation Results</CardTitle>
        <CardDescription>
          Probabilistic timeline predictions based on uncertainty factors
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* TODO: Replace with histogram chart */}
        <div className="space-y-4">
          <div className={`inline-flex px-4 py-2 rounded-full font-semibold ${getRiskColor(data?.risk_level || 'medium')}`}>
            Risk Level: {data?.risk_level.charAt(0).toUpperCase()}{data?.risk_level.slice(1)}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">Mean Duration</div>
              <div className="text-2xl font-bold">{data?.mean_duration.toFixed(1)} days</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">Standard Deviation</div>
              <div className="text-2xl font-bold">{data?.std_deviation.toFixed(1)} days</div>
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-semibold mb-3">Percentiles</h4>
            <div className="space-y-2">
              {[
                { label: 'P10 (Best Case)', value: data?.percentiles.p10 },
                { label: 'P50 (Median)', value: data?.percentiles.p50 },
                { label: 'P75', value: data?.percentiles.p75 },
                { label: 'P90 (Conservative)', value: data?.percentiles.p90 },
                { label: 'P95 (Worst Case)', value: data?.percentiles.p95 },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-center">
                  <span className="text-sm text-gray-800">{label}</span>
                  <span className="font-semibold">{value?.toFixed(1)} days</span>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-semibold mb-2">80% Confidence Range</h4>
            <div className="text-sm text-gray-800">
              {data?.confidence_80pct_range[0].toFixed(1)} - {data?.confidence_80pct_range[1].toFixed(1)} days
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
