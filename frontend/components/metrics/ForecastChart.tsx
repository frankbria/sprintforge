/**
 * ForecastChart - displays forecast predictions with confidence intervals
 */

import * as React from 'react';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import type { ForecastData } from '@/types/historical-metrics';
import { format } from 'date-fns';
import { TrendingUp } from 'lucide-react';

interface ForecastChartProps {
  data: ForecastData;
}

export default function ForecastChart({ data }: ForecastChartProps) {
  // Transform data for chart
  const chartData = data.forecasts.map((forecast) => ({
    date: format(new Date(forecast.date), 'MMM dd'),
    predicted: forecast.predicted_value,
    lowerBound: forecast.lower_bound,
    upperBound: forecast.upper_bound,
    // Calculate confidence band range for area chart
    confidenceBand: [forecast.lower_bound, forecast.upper_bound],
  }));

  // Empty state
  if (data.forecasts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Forecast Predictions</CardTitle>
          <CardDescription>
            Future predictions with confidence intervals
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            No forecast data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Forecast Predictions</CardTitle>
        <CardDescription>
          Future predictions with confidence intervals
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Metrics summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm text-gray-700">Method</div>
              <div className="text-lg font-bold text-gray-900">{data.method}</div>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm text-gray-700">Confidence Level</div>
              <div className="text-lg font-bold text-gray-900">
                {(data.confidence_level * 100).toFixed(0)}%
              </div>
            </div>
            {data.rmse !== undefined && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-700">RMSE</div>
                <div className="text-lg font-bold text-gray-900">{data.rmse.toFixed(1)}</div>
              </div>
            )}
            {data.mae !== undefined && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-700">MAE</div>
                <div className="text-lg font-bold text-gray-900">{data.mae.toFixed(1)}</div>
              </div>
            )}
          </div>

          {/* Chart */}
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart
              data={chartData}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
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
                formatter={(value: number, name: string) => {
                  if (name === 'Predicted Value') {
                    return [value.toFixed(1), name];
                  }
                  return [value.toFixed(1), name];
                }}
              />
              <Legend />

              {/* Confidence interval band */}
              <Area
                type="monotone"
                dataKey="upperBound"
                stroke="none"
                fill="url(#colorConfidence)"
                name="Upper Bound"
                legendType="none"
              />
              <Area
                type="monotone"
                dataKey="lowerBound"
                stroke="none"
                fill="url(#colorConfidence)"
                name="Lower Bound"
                legendType="none"
              />

              {/* Confidence bounds as lines */}
              <Line
                type="monotone"
                dataKey="upperBound"
                stroke="#93c5fd"
                strokeWidth={1}
                strokeDasharray="3 3"
                name="Upper Bound"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="lowerBound"
                stroke="#93c5fd"
                strokeWidth={1}
                strokeDasharray="3 3"
                name="Lower Bound"
                dot={false}
              />

              {/* Predicted value line */}
              <Line
                type="monotone"
                dataKey="predicted"
                stroke="#3b82f6"
                strokeWidth={3}
                name="Predicted Value"
                dot={{ r: 4, fill: '#3b82f6' }}
                activeDot={{ r: 6 }}
              />
            </ComposedChart>
          </ResponsiveContainer>

          {/* Info box */}
          <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg">
            <TrendingUp className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-gray-800">
              <span className="font-semibold">Forecast Confidence:</span> The shaded area
              represents the {(data.confidence_level * 100).toFixed(0)}% confidence interval.
              Actual values are expected to fall within this range.
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
