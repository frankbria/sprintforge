/**
 * CompletionTrendChart - displays task completion trends with cumulative progress
 */

import * as React from 'react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import type { CompletionTrendsResponse } from '@/types/historical-metrics';
import { format } from 'date-fns';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface CompletionTrendChartProps {
  data: CompletionTrendsResponse;
}

export default function CompletionTrendChart({ data }: CompletionTrendChartProps) {
  // Transform data for chart
  const chartData = data.trends.map((trend) => ({
    date: format(new Date(trend.date), 'MMM dd'),
    completionRate: trend.completion_rate * 100,
    cumulativeCompletion: trend.cumulative_completion,
    tasksCompleted: trend.completed_tasks,
    totalTasks: trend.total_tasks,
  }));

  const getGranularityLabel = () => {
    return data.granularity.charAt(0).toUpperCase() + data.granularity.slice(1);
  };

  // Empty state
  if (data.trends.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Completion Trends</CardTitle>
          <CardDescription>
            Task completion rates over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No completion data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Completion Trends</CardTitle>
        <CardDescription>
          Task completion rates over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Metrics summary */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm text-gray-700">Granularity</div>
              <div className="text-lg font-bold text-gray-900">{getGranularityLabel()}</div>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm text-gray-700">Average Rate</div>
              <div className="text-lg font-bold text-gray-900">
                {(data.patterns.average_rate * 100).toFixed(0)}%
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm text-gray-700">Total Tasks</div>
              <div className="text-lg font-bold text-gray-900">
                {data.trends[data.trends.length - 1]?.cumulative_completion || 0}
              </div>
            </div>
          </div>

          {/* Chart */}
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart
              data={chartData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                <linearGradient id="colorCompletion" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                yAxisId="left"
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
                label={{ value: 'Completion Rate (%)', angle: -90, position: 'insideLeft' }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
                label={{ value: 'Cumulative Tasks', angle: 90, position: 'insideRight' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
                formatter={(value: number, name: string) => {
                  if (name === 'Completion Rate') {
                    return [`${value.toFixed(1)}%`, name];
                  }
                  return [value, name];
                }}
              />
              <Legend />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="completionRate"
                stroke="#3b82f6"
                fill="url(#colorCompletion)"
                name="Completion Rate"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="cumulativeCompletion"
                stroke="#10b981"
                strokeWidth={2}
                name="Cumulative Completion"
                dot={{ r: 3 }}
              />
            </ComposedChart>
          </ResponsiveContainer>

          {/* Pattern indicators */}
          {(data.patterns.best_day || data.patterns.worst_day) && (
            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
              {data.patterns.best_day && (
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <div>
                    <div className="text-sm text-gray-700">Best Period</div>
                    <div className="text-sm font-semibold text-gray-900">
                      {format(new Date(data.patterns.best_day), 'MMM dd, yyyy')}
                    </div>
                  </div>
                </div>
              )}
              {data.patterns.worst_day && (
                <div className="flex items-center gap-2">
                  <TrendingDown className="w-5 h-5 text-red-600" />
                  <div>
                    <div className="text-sm text-gray-700">Worst Period</div>
                    <div className="text-sm font-semibold text-gray-900">
                      {format(new Date(data.patterns.worst_day), 'MMM dd, yyyy')}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
