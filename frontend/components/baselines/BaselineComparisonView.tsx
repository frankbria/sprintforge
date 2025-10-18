/**
 * BaselineComparisonView Component
 *
 * Main comparison dashboard showing variance analysis between
 * baseline snapshot and current project state.
 *
 * Implemented following TDD RED-GREEN-REFACTOR cycle.
 */

'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/Table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Alert } from '@/components/ui/Alert';
import { Label } from '@/components/ui/Label';
import { VarianceIndicator } from './VarianceIndicator';
import { compareBaseline } from '@/lib/api/baselines';
import type { TaskVariance } from '@/types/baseline';

export interface BaselineComparisonViewProps {
  projectId: string;
  baselineId: string;
}

/**
 * Format date to human-readable format
 */
function formatDate(dateString: string): string {
  try {
    return format(new Date(dateString), 'MMM d, yyyy');
  } catch {
    return dateString;
  }
}

/**
 * Summary metric card component
 */
function MetricCard({
  title,
  value,
  color = 'blue',
}: {
  title: string;
  value: number;
  color?: 'blue' | 'green' | 'red' | 'gray';
}) {
  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    red: 'text-red-600',
    gray: 'text-gray-800',
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-800">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-bold ${colorClasses[color]}`}>{value}</div>
      </CardContent>
    </Card>
  );
}

export function BaselineComparisonView({
  projectId,
  baselineId,
}: BaselineComparisonViewProps) {
  const [includeUnchanged, setIncludeUnchanged] = React.useState(false);
  const [sortBy, setSortBy] = React.useState<'variance' | 'name'>('variance');

  // Fetch comparison data
  const {
    data: comparison,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['baseline-comparison', baselineId, projectId, includeUnchanged],
    queryFn: () => compareBaseline(projectId, baselineId, includeUnchanged),
    refetchInterval: 30000, // Auto-refresh every 30s
  });

  // Sort task variances
  const sortedVariances = React.useMemo(() => {
    if (!comparison?.task_variances) return [];

    const sorted = [...comparison.task_variances];

    if (sortBy === 'variance') {
      sorted.sort((a, b) => Math.abs(b.variance_days) - Math.abs(a.variance_days));
    } else if (sortBy === 'name') {
      sorted.sort((a, b) => a.task_name.localeCompare(b.task_name));
    }

    return sorted;
  }, [comparison?.task_variances, sortBy]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-800">Loading comparison...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert variant="destructive" className="my-4">
        <div className="flex items-center justify-between">
          <div>
            <strong className="font-semibold">Error loading comparison</strong>
            <p className="text-sm mt-1">
              {error instanceof Error ? error.message : 'Failed to compare baseline'}
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="px-3 py-1 text-sm bg-white border border-red-300 rounded-md hover:bg-red-50"
          >
            Retry
          </button>
        </div>
      </Alert>
    );
  }

  if (!comparison) {
    return null;
  }

  const { baseline, comparison_date, summary, task_variances, new_tasks, deleted_tasks } =
    comparison;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h1 className="text-2xl font-bold text-gray-900">{baseline.name}</h1>
        <div className="flex gap-4 mt-2 text-sm text-gray-800">
          <div>
            <span className="font-medium">Created:</span> {formatDate(baseline.created_at)}
          </div>
          <div>
            <span className="font-medium">Comparing to:</span>{' '}
            {formatDate(comparison_date)} (Current State)
          </div>
        </div>
      </div>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Total Tasks" value={summary.total_tasks} color="blue" />
        <MetricCard title="Ahead" value={summary.tasks_ahead} color="green" />
        <MetricCard title="Behind" value={summary.tasks_behind} color="red" />
        <MetricCard title="On Track" value={summary.tasks_on_track} color="gray" />
      </div>

      {/* Filters & Controls */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="show-only-changed"
            checked={!includeUnchanged}
            onChange={(e) => setIncludeUnchanged(!e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <Label htmlFor="show-only-changed" className="cursor-pointer">
            Show only changed tasks
          </Label>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-800">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'variance' | 'name')}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="variance">Variance</option>
            <option value="name">Task Name</option>
          </select>
        </div>
      </div>

      {/* Variance Table */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Task Variances</h2>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task Name</TableHead>
              <TableHead>Variance</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedVariances.map((variance) => (
              <TableRow key={variance.task_id}>
                <TableCell className="font-medium">
                  <div>
                    <div>{variance.task_name}</div>
                    {variance.status_changed && (
                      <span className="text-xs text-orange-600">Status changed</span>
                    )}
                    {variance.dependencies_changed && (
                      <span className="text-xs text-purple-600 ml-2">
                        Dependencies changed
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <VarianceIndicator varianceDays={variance.variance_days} />
                </TableCell>
                <TableCell>
                  <span
                    className={`text-sm capitalize ${
                      variance.status === 'ahead'
                        ? 'text-green-700'
                        : variance.status === 'behind'
                        ? 'text-red-700'
                        : 'text-gray-700'
                    }`}
                  >
                    {variance.status.replace('_', ' ')}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {sortedVariances.length === 0 && (
          <div className="text-center py-8 text-gray-700">
            No task variances to display.
          </div>
        )}
      </div>

      {/* New Tasks Section */}
      {new_tasks.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">New Tasks</h2>
          <Card>
            <CardContent className="pt-6">
              <ul className="space-y-2">
                {new_tasks.map((task) => (
                  <li key={task.task_id} className="flex items-center gap-2">
                    <span className="text-green-600">+</span>
                    <span>{task.task_name}</span>
                    <span className="text-xs text-gray-700">
                      (added after baseline)
                    </span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Deleted Tasks Section */}
      {deleted_tasks.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Deleted Tasks</h2>
          <Card>
            <CardContent className="pt-6">
              <ul className="space-y-2">
                {deleted_tasks.map((task) => (
                  <li key={task.task_id} className="flex items-center gap-2">
                    <span className="text-red-600">−</span>
                    <span className="line-through text-gray-700">{task.task_name}</span>
                    <span className="text-xs text-gray-700">
                      (existed in baseline)
                    </span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
