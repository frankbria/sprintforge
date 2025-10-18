/**
 * MetricsSummaryCard - displays key metrics dashboard
 */

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import type { MetricsSummaryResponse } from '@/types/historical-metrics';
import { TrendingUp, TrendingDown, Minus, Target, CheckCircle2, Activity, Calendar } from 'lucide-react';
import { format } from 'date-fns';

interface MetricsSummaryCardProps {
  data: MetricsSummaryResponse;
}

export default function MetricsSummaryCard({ data }: MetricsSummaryCardProps) {
  const getTrendIcon = () => {
    switch (data.velocity_trend) {
      case 'increasing':
        return <TrendingUp className="w-5 h-5 text-green-600" />;
      case 'decreasing':
        return <TrendingDown className="w-5 h-5 text-red-600" />;
      case 'stable':
        return <Minus className="w-5 h-5 text-gray-600" />;
    }
  };

  const getTrendColor = () => {
    switch (data.velocity_trend) {
      case 'increasing':
        return 'text-green-600';
      case 'decreasing':
        return 'text-red-600';
      case 'stable':
        return 'text-gray-600';
    }
  };

  const getConfidenceColor = () => {
    if (data.confidence_score >= 0.8) return 'text-green-600';
    if (data.confidence_score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Metrics Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {/* Current Velocity */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-700">Current Velocity</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{data.current_velocity}</div>
          </div>

          {/* Average Velocity */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-purple-600" />
              <span className="text-sm text-gray-700">Average Velocity</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{data.average_velocity}</div>
          </div>

          {/* Velocity Trend */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              {getTrendIcon()}
              <span className="text-sm text-gray-700">Velocity Trend</span>
            </div>
            <div className={`text-lg font-semibold capitalize ${getTrendColor()}`}>
              {data.velocity_trend}
            </div>
          </div>

          {/* Completion Rate */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              <span className="text-sm text-gray-700">Completion Rate</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {(data.completion_rate * 100).toFixed(0)}%
            </div>
          </div>

          {/* Total Sprints */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700">Total Sprints</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{data.total_sprints}</div>
          </div>

          {/* Active Sprints */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-orange-600" />
              <span className="text-sm text-gray-700">Active Sprints</span>
            </div>
            <div className="text-2xl font-bold text-gray-900">{data.active_sprints}</div>
          </div>

          {/* Confidence Score */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-700">Confidence Score</span>
            </div>
            <div className={`text-2xl font-bold ${getConfidenceColor()}`}>
              {(data.confidence_score * 100).toFixed(0)}%
            </div>
          </div>

          {/* Predicted Completion Date */}
          {data.predicted_completion_date && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-indigo-600" />
                <span className="text-sm text-gray-700">Predicted Completion</span>
              </div>
              <div className="text-lg font-bold text-gray-900">
                {format(new Date(data.predicted_completion_date), 'MMM dd, yyyy')}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
