/**
 * Historical Metrics Page - displays interactive trend charts and forecasting
 */

'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import {
  getMetricsSummary,
  getVelocityTrend,
  getCompletionTrends,
  getForecast,
} from '@/lib/api/historical-metrics';
import MetricsSummaryCard from '@/components/metrics/MetricsSummaryCard';
import VelocityTrendChart from '@/components/metrics/VelocityTrendChart';
import CompletionTrendChart from '@/components/metrics/CompletionTrendChart';
import ForecastChart from '@/components/metrics/ForecastChart';
import { Tabs } from '@/components/ui/Tabs';
import { Skeleton } from '@/components/ui/Skeleton';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Download, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface MetricsPageProps {
  params: {
    id: string;
  };
}

export default function MetricsPage({ params }: MetricsPageProps) {
  const projectId = params.id;
  const [activeTab, setActiveTab] = React.useState<'velocity' | 'trends' | 'forecast'>('velocity');
  const [dateRange, setDateRange] = React.useState<{ start?: string; end?: string }>({});

  // Fetch metrics summary
  const {
    data: summaryData,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({
    queryKey: ['metrics', 'summary', projectId],
    queryFn: () => getMetricsSummary(projectId),
  });

  // Fetch velocity trend
  const {
    data: velocityData,
    isLoading: velocityLoading,
    error: velocityError,
  } = useQuery({
    queryKey: ['metrics', 'velocity', projectId, dateRange],
    queryFn: () => getVelocityTrend(projectId, {
      start_date: dateRange.start,
      end_date: dateRange.end,
    }),
  });

  // Fetch completion trends
  const {
    data: completionData,
    isLoading: completionLoading,
    error: completionError,
  } = useQuery({
    queryKey: ['metrics', 'completion', projectId, dateRange],
    queryFn: () => getCompletionTrends(projectId, {
      start_date: dateRange.start,
      end_date: dateRange.end,
      granularity: 'weekly',
    }),
  });

  // Fetch forecast
  const {
    data: forecastData,
    isLoading: forecastLoading,
    error: forecastError,
  } = useQuery({
    queryKey: ['metrics', 'forecast', projectId],
    queryFn: () => getForecast(projectId, {
      forecast_days: 90,
      confidence_level: 0.8,
    }),
  });

  const handleExport = (format: 'csv' | 'png') => {
    // TODO: Implement export functionality
    console.log(`Exporting ${activeTab} as ${format}`);
  };

  if (summaryError || velocityError || completionError || forecastError) {
    return (
      <div className="container mx-auto py-8">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load metrics. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const isLoading = summaryLoading || velocityLoading || completionLoading || forecastLoading;

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="space-y-6">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
        <div className="text-center text-gray-600 mt-4">Loading metrics...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Historical Metrics</h1>
            <p className="text-gray-700 mt-1">
              Track velocity, completion trends, and forecasts
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('csv')}
              className="flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('png')}
              className="flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export PNG
            </Button>
          </div>
        </div>

        {/* Metrics Summary */}
        {summaryData && <MetricsSummaryCard data={summaryData} />}

        {/* Tab Navigation and Charts */}
        <Tabs defaultValue="velocity" onValueChange={(value) => setActiveTab(value as any)}>
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" role="tablist">
              <button
                role="tab"
                aria-selected={activeTab === 'velocity'}
                onClick={() => setActiveTab('velocity')}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                  ${
                    activeTab === 'velocity'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-700 hover:text-gray-800 hover:border-gray-300'
                  }
                `}
              >
                Velocity
              </button>
              <button
                role="tab"
                aria-selected={activeTab === 'trends'}
                onClick={() => setActiveTab('trends')}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                  ${
                    activeTab === 'trends'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-700 hover:text-gray-800 hover:border-gray-300'
                  }
                `}
              >
                Trends
              </button>
              <button
                role="tab"
                aria-selected={activeTab === 'forecast'}
                onClick={() => setActiveTab('forecast')}
                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                  ${
                    activeTab === 'forecast'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-700 hover:text-gray-800 hover:border-gray-300'
                  }
                `}
              >
                Forecast
              </button>
            </nav>
          </div>

          {/* Chart Content */}
          <div className="mt-6">
            {activeTab === 'velocity' && velocityData && (
              <VelocityTrendChart data={velocityData} />
            )}
            {activeTab === 'trends' && completionData && (
              <CompletionTrendChart data={completionData} />
            )}
            {activeTab === 'forecast' && forecastData && (
              <ForecastChart data={forecastData} />
            )}
          </div>
        </Tabs>
      </div>
    </div>
  );
}
