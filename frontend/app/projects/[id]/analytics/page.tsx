/**
 * Analytics Dashboard Page
 *
 * Provides comprehensive project analytics with:
 * - Health score overview
 * - Critical path analysis
 * - Resource utilization
 * - Monte Carlo simulation results
 * - Progress tracking
 */

'use client';

import * as React from 'react';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { Button } from '@/components/ui/Button';
import { getAnalyticsOverview } from '@/lib/api/analytics';

// Chart components
import ProjectHealthCard from '@/components/analytics/ProjectHealthCard';
import MetricsGrid from '@/components/analytics/MetricsGrid';
import CriticalPathVisualization from '@/components/analytics/CriticalPathVisualization';
import ResourceUtilizationChart from '@/components/analytics/ResourceUtilizationChart';
import SimulationResultsChart from '@/components/analytics/SimulationResultsChart';
import ProgressTracking from '@/components/analytics/ProgressTracking';

/**
 * Loading skeleton for analytics dashboard
 */
function AnalyticsLoadingSkeleton() {
  return (
    <div className="container mx-auto p-4 sm:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-10 w-24" />
      </div>

      <Skeleton className="h-48 w-full" />
      <Skeleton className="h-64 w-full" />

      <div className="flex space-x-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-10 w-24" />
        ))}
      </div>

      <Skeleton className="h-96 w-full" />
    </div>
  );
}

/**
 * Error state with retry capability
 */
interface AnalyticsErrorStateProps {
  error: Error;
  onRetry: () => void;
}

function AnalyticsErrorState({ error, onRetry }: AnalyticsErrorStateProps) {
  return (
    <div className="container mx-auto p-4 sm:p-6">
      <Alert variant="destructive">
        <AlertTitle>Failed to Load Analytics</AlertTitle>
        <AlertDescription className="mt-2">
          <p className="mb-4">{error.message || 'An unexpected error occurred while loading analytics data.'}</p>
          <Button onClick={onRetry} variant="secondary" size="sm">
            Try Again
          </Button>
        </AlertDescription>
      </Alert>
    </div>
  );
}

/**
 * Main Analytics Dashboard Page
 */
export default function AnalyticsPage() {
  const params = useParams();
  const projectId = params.id as string;

  // Fetch analytics data with auto-refresh every 30 seconds
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['analytics', projectId],
    queryFn: () => getAnalyticsOverview(projectId),
    refetchInterval: 30000, // 30 seconds
    staleTime: 10000, // Consider stale after 10 seconds
    retry: 2,
  });

  // Loading state
  if (isLoading) {
    return <AnalyticsLoadingSkeleton />;
  }

  // Error state
  if (error) {
    return <AnalyticsErrorState error={error as Error} onRetry={() => refetch()} />;
  }

  // No data state
  if (!data) {
    return (
      <div className="container mx-auto p-4 sm:p-6">
        <Alert>
          <AlertTitle>No Analytics Data Available</AlertTitle>
          <AlertDescription>
            Analytics data could not be found for this project. Please ensure the project has been properly configured.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Project Analytics</h1>
          <p className="text-sm sm:text-base text-gray-600 mt-1">
            Comprehensive insights into project health and performance
          </p>
        </div>
        <Button onClick={() => refetch()} variant="ghost" size="sm">
          <svg
            className="mr-2 h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </Button>
      </div>

      {/* Health Score Overview */}
      <ProjectHealthCard healthScore={data.health_score} />

      {/* Key Metrics Grid */}
      <MetricsGrid metrics={data} />

      {/* Tabbed Analytics Views */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="w-full sm:w-auto overflow-x-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="critical-path">Critical Path</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
          <TabsTrigger value="simulation">Simulation</TabsTrigger>
          <TabsTrigger value="progress">Progress</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Critical Path Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Critical Path</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Duration</span>
                    <span className="font-semibold">{data.critical_path_summary.total_duration} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Critical Tasks</span>
                    <span className="font-semibold">{data.critical_path_summary.critical_tasks_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Stability Score</span>
                    <span className="font-semibold">{data.critical_path_summary.path_stability_score.toFixed(1)}/100</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Resource Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Resources</span>
                    <span className="font-semibold">{data.resource_summary.total_resources}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Allocated</span>
                    <span className="font-semibold">{data.resource_summary.allocated_resources}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Utilization</span>
                    <span className="font-semibold">{data.resource_summary.utilization_pct.toFixed(1)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Risk Level */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Risk Level</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className={`inline-flex px-3 py-1 rounded-full font-semibold text-sm ${
                    data.simulation_summary.risk_level === 'low'
                      ? 'bg-green-100 text-green-800'
                      : data.simulation_summary.risk_level === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {data.simulation_summary.risk_level.charAt(0).toUpperCase() + data.simulation_summary.risk_level.slice(1)}
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">P50</span>
                      <span className="font-semibold">{data.simulation_summary.p50.toFixed(1)} days</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">P90</span>
                      <span className="font-semibold">{data.simulation_summary.p90.toFixed(1)} days</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Critical Path Tab */}
        <TabsContent value="critical-path">
          <CriticalPathVisualization projectId={projectId} />
        </TabsContent>

        {/* Resources Tab */}
        <TabsContent value="resources">
          <ResourceUtilizationChart projectId={projectId} />
        </TabsContent>

        {/* Simulation Tab */}
        <TabsContent value="simulation">
          <SimulationResultsChart projectId={projectId} />
        </TabsContent>

        {/* Progress Tab */}
        <TabsContent value="progress">
          <ProgressTracking projectId={projectId} />
        </TabsContent>
      </Tabs>

      {/* Data timestamp */}
      <div className="text-center text-xs text-gray-500">
        Last updated: {new Date(data.generated_at).toLocaleString()}
      </div>
    </div>
  );
}
