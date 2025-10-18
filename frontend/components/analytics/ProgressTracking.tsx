/**
 * Progress Tracking Component
 *
 * Displays project progress with burndown/burnup charts showing actual vs planned progress.
 */

'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { getProgressAnalytics } from '@/lib/api/analytics';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from 'recharts';
import { cn } from '@/lib/utils';

interface ProgressTrackingProps {
  projectId: string;
}

export default function ProgressTracking({ projectId }: ProgressTrackingProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['analytics', 'progress', projectId],
    queryFn: () => getProgressAnalytics(projectId),
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
          Failed to load progress data. Please try again.
        </AlertDescription>
      </Alert>
    );
  }

  const isAhead = (data?.variance_from_plan || 0) < 0;
  const isBehind = (data?.variance_from_plan || 0) > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Progress Tracking</CardTitle>
        <CardDescription>
          Task completion progress and schedule performance
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* TODO: Replace with burndown/burnup chart */}
        <div className="space-y-4">
          <div className="bg-gray-50 p-6 rounded-lg">
            <div className="text-sm text-gray-800 mb-2">Overall Completion</div>
            <div className="flex items-center justify-between mb-2">
              <div className="text-3xl font-bold text-gray-900">{data?.completion_pct.toFixed(1)}%</div>
              <div className="text-sm text-gray-800">
                {data?.tasks_completed} of {data?.tasks_total} tasks
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all"
                style={{ width: `${data?.completion_pct}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">On-Time Completion</div>
              <div className="text-2xl font-bold text-gray-900">{data?.on_time_pct.toFixed(1)}%</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-sm text-gray-800">Delayed Tasks</div>
              <div className="text-2xl font-bold text-red-600">{data?.delayed_tasks}</div>
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-semibold text-gray-900 mb-3">Performance Metrics</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-800">Burn Rate</span>
                <span className="font-semibold text-gray-900">{data?.burn_rate.toFixed(2)} tasks/day</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-800">Est. Completion Date</span>
                <span className="font-semibold text-gray-900">
                  {data?.estimated_completion_date ? new Date(data.estimated_completion_date).toLocaleDateString() : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-800">Schedule Variance</span>
                <span className={`font-semibold ${isAhead ? 'text-green-600' : isBehind ? 'text-red-600' : 'text-gray-900'}`}>
                  {isAhead && '-'}{Math.abs(data?.variance_from_plan || 0)} days {isAhead ? 'ahead' : isBehind ? 'behind' : 'on schedule'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
