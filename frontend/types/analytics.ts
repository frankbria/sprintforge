/**
 * Analytics type definitions matching backend API schemas
 */

export interface AnalyticsOverviewResponse {
  health_score: number;
  critical_path_summary: CriticalPathSummary;
  resource_summary: ResourceSummary;
  simulation_summary: SimulationSummary;
  progress_summary: ProgressSummary;
  generated_at: string;
}

export interface CriticalPathSummary {
  total_duration: number;
  critical_tasks_count: number;
  path_stability_score: number;
}

export interface ResourceSummary {
  total_resources: number;
  allocated_resources: number;
  utilization_pct: number;
  over_allocated_count: number;
  under_utilized_count: number;
}

export interface SimulationSummary {
  risk_level: 'low' | 'medium' | 'high';
  p50: number;
  p90: number;
  mean_duration: number;
}

export interface ProgressSummary {
  completion_pct: number;
  tasks_completed: number;
  tasks_total: number;
  on_time_pct: number;
  delayed_tasks: number;
}

// Detailed analytics responses

export interface CriticalPathResponse {
  critical_tasks: string[];
  total_duration: number;
  float_time: Record<string, number>;
  risk_tasks: string[];
  path_stability_score: number;
}

export interface ResourceUtilizationResponse {
  total_resources: number;
  allocated_resources: number;
  utilization_pct: number;
  over_allocated: ResourceInfo[];
  under_utilized: ResourceInfo[];
  resource_timeline: Record<string, number>;
}

export interface ResourceInfo {
  resource_id: string;
  resource_name: string;
  allocation_pct: number;
  tasks_assigned: number;
}

export interface SimulationResultsResponse {
  percentiles: {
    p10: number;
    p50: number;
    p75: number;
    p90: number;
    p95: number;
  };
  mean_duration: number;
  std_deviation: number;
  risk_level: 'low' | 'medium' | 'high';
  confidence_80pct_range: [number, number];
  histogram_data: HistogramBucket[];
}

export interface HistogramBucket {
  bucket: string;
  count: number;
  min_value: number;
  max_value: number;
}

export interface ProgressMetricsResponse {
  completion_pct: number;
  tasks_completed: number;
  tasks_total: number;
  on_time_pct: number;
  delayed_tasks: number;
  burn_rate: number;
  estimated_completion_date: string;
  variance_from_plan: number;
}

// UI-specific types

export type AnalyticsTab = 'overview' | 'critical-path' | 'resources' | 'simulation' | 'progress';

export interface MetricCardData {
  label: string;
  value: string | number;
  trend?: number;
  format?: 'number' | 'percent' | 'currency' | 'days';
  icon?: string;
}
