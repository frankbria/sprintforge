/**
 * Historical metrics type definitions matching backend API schemas
 */

// Query parameters
export interface HistoricalMetricsParams {
  start_date?: string;
  end_date?: string;
  metric_types?: string[];
  limit?: number;
}

export interface VelocityTrendParams {
  start_date?: string;
  end_date?: string;
  window_size?: number;
}

export interface CompletionTrendsParams {
  start_date?: string;
  end_date?: string;
  granularity?: 'daily' | 'weekly' | 'monthly';
}

export interface ForecastParams {
  forecast_days?: number;
  confidence_level?: number;
}

// Response types
export interface HistoricalMetric {
  id: string;
  project_id: string;
  metric_type: string;
  metric_value: number;
  recorded_at: string;
  metadata?: Record<string, unknown>;
}

export interface SprintVelocity {
  sprint_number: number;
  sprint_name: string;
  velocity: number;
  planned_velocity: number;
  completion_rate: number;
  start_date: string;
  end_date: string;
  is_anomaly?: boolean;
}

export interface VelocityTrendResponse {
  sprints: SprintVelocity[];
  moving_average: number[];
  trend_direction: 'increasing' | 'decreasing' | 'stable';
  average_velocity: number;
  anomalies: number[];
}

export interface CompletionTrend {
  date: string;
  completed_tasks: number;
  total_tasks: number;
  completion_rate: number;
  cumulative_completion: number;
}

export interface CompletionTrendsResponse {
  trends: CompletionTrend[];
  granularity: 'daily' | 'weekly' | 'monthly';
  patterns: {
    best_day?: string;
    worst_day?: string;
    average_rate: number;
  };
}

export interface ForecastPoint {
  date: string;
  predicted_value: number;
  lower_bound: number;
  upper_bound: number;
  confidence_level: number;
}

export interface ForecastData {
  forecasts: ForecastPoint[];
  method: string;
  confidence_level: number;
  rmse?: number;
  mae?: number;
}

export interface MetricsSummaryResponse {
  current_velocity: number;
  average_velocity: number;
  velocity_trend: 'increasing' | 'decreasing' | 'stable';
  completion_rate: number;
  total_sprints: number;
  active_sprints: number;
  predicted_completion_date?: string;
  confidence_score: number;
}

// Chart data types
export interface VelocityChartData {
  sprintNumber: number;
  sprintName: string;
  actualVelocity: number;
  plannedVelocity: number;
  movingAverage?: number;
  isAnomaly?: boolean;
}

export interface CompletionChartData {
  date: string;
  completionRate: number;
  cumulativeCompletion: number;
  tasksCompleted: number;
  totalTasks: number;
}

export interface ForecastChartData {
  date: string;
  actual?: number;
  predicted?: number;
  lowerBound?: number;
  upperBound?: number;
}

// UI-specific types
export type MetricsTab = 'velocity' | 'trends' | 'forecast';

export interface DateRangeFilter {
  startDate?: Date;
  endDate?: Date;
}

export interface ExportOptions {
  format: 'csv' | 'png';
  tab: MetricsTab;
}
