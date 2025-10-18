/**
 * VelocityTrendChart - displays sprint velocity trends with moving average
 */

import * as React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import type { VelocityTrendResponse } from '@/types/historical-metrics';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface VelocityTrendChartProps {
  data: VelocityTrendResponse;
}

export default function VelocityTrendChart({ data }: VelocityTrendChartProps) {
  // Transform data for chart
  const chartData = data.sprints.map((sprint, index) => ({
    sprintNumber: sprint.sprint_number,
    sprintName: sprint.sprint_name,
    actualVelocity: sprint.velocity,
    plannedVelocity: sprint.planned_velocity,
    movingAverage: data.moving_average[index],
    isAnomaly: sprint.is_anomaly,
  }));

  const getTrendIcon = () => {
    switch (data.trend_direction) {
      case 'increasing':
        return <TrendingUp className="w-5 h-5 text-green-600" />;
      case 'decreasing':
        return <TrendingDown className="w-5 h-5 text-red-600" />;
      case 'stable':
        return <Minus className="w-5 h-5 text-gray-600" />;
    }
  };

  const getTrendColor = () => {
    switch (data.trend_direction) {
      case 'increasing':
        return 'text-green-600';
      case 'decreasing':
        return 'text-red-600';
      case 'stable':
        return 'text-gray-600';
    }
  };

  // Empty state
  if (data.sprints.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Velocity Trend</CardTitle>
          <CardDescription>
            Sprint velocity over time with moving average
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No velocity data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Velocity Trend</CardTitle>
        <CardDescription>
          Sprint velocity over time with moving average
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Metrics summary */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Average Velocity</span>
              <span className="text-2xl font-bold text-gray-900">{data.average_velocity}</span>
            </div>
            <div className="flex items-center gap-2">
              {getTrendIcon()}
              <span className={`text-sm font-medium capitalize ${getTrendColor()}`}>
                {data.trend_direction}
              </span>
            </div>
          </div>

          {/* Chart */}
          <ResponsiveContainer width="100%" height={400}>
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="sprintName"
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                stroke="#6b7280"
                style={{ fontSize: '12px' }}
                label={{ value: 'Story Points', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="actualVelocity"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Actual Velocity"
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="plannedVelocity"
                stroke="#94a3b8"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Planned Velocity"
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="movingAverage"
                stroke="#10b981"
                strokeWidth={2}
                name="Moving Average"
                dot={{ r: 3 }}
              />
              {/* Highlight anomalies */}
              {chartData.map((item, index) =>
                item.isAnomaly ? (
                  <ReferenceDot
                    key={`anomaly-${index}`}
                    x={item.sprintName}
                    y={item.actualVelocity}
                    r={8}
                    fill="#ef4444"
                    fillOpacity={0.3}
                    stroke="#ef4444"
                    strokeWidth={2}
                    data-anomaly="true"
                  />
                ) : null
              )}
            </LineChart>
          </ResponsiveContainer>

          {/* Anomaly legend */}
          {data.anomalies.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-gray-700">
              <div className="w-3 h-3 rounded-full bg-red-500 opacity-30 border-2 border-red-500" />
              <span>Anomaly detected - significant deviation from trend</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
