/**
 * TypeScript types for Baseline Management & Comparison
 *
 * These types match the backend Pydantic schemas for type safety
 * across the frontend-backend boundary.
 */

/**
 * Base baseline information without snapshot data
 */
export interface Baseline {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  created_at: string;
  is_active: boolean;
  snapshot_size_bytes: number;
}

/**
 * Full baseline including snapshot data
 */
export interface BaselineDetail extends Baseline {
  snapshot_data: {
    project: Record<string, any>;
    tasks: any[];
    critical_path?: string[];
    monte_carlo_results?: {
      p10?: number;
      p50?: number;
      p90?: number;
      p95?: number;
      p99?: number;
      mean_duration?: number;
    };
    snapshot_metadata: {
      total_tasks: number;
      completion_pct?: number;
      snapshot_timestamp: string;
    };
  };
}

/**
 * Variance for a single task between baseline and current state
 */
export interface TaskVariance {
  task_id: string;
  task_name: string;
  variance_days: number;
  variance_percentage: number;
  is_ahead: boolean;
  is_behind: boolean;
  start_date_variance: number;
  end_date_variance: number;
  duration_variance: number;
  status_changed: boolean;
  dependencies_changed: boolean;
  status: 'ahead' | 'behind' | 'on_track';
}

/**
 * Summary metrics for baseline comparison
 */
export interface ComparisonSummary {
  total_tasks: number;
  tasks_ahead: number;
  tasks_behind: number;
  tasks_on_track: number;
  avg_variance_days: number;
  critical_path_variance_days: number;
}

/**
 * Complete baseline comparison response
 */
export interface BaselineComparison {
  baseline: {
    id: string;
    name: string;
    created_at: string;
  };
  comparison_date: string;
  summary: ComparisonSummary;
  task_variances: TaskVariance[];
  new_tasks: Array<{
    task_id: string;
    task_name: string;
    added_after_baseline: boolean;
  }>;
  deleted_tasks: Array<{
    task_id: string;
    task_name: string;
    existed_in_baseline: boolean;
  }>;
}

/**
 * Request payload for creating a new baseline
 */
export interface CreateBaselineRequest {
  name: string;
  description?: string;
}

/**
 * Paginated list of baselines response
 */
export interface BaselineListResponse {
  baselines: Baseline[];
  total: number;
  page: number;
  limit: number;
}

/**
 * Response when activating a baseline
 */
export interface SetBaselineActiveResponse {
  id: string;
  is_active: boolean;
  message: string;
}

/**
 * Variance indicator status for UI rendering
 */
export type VarianceStatus = 'ahead' | 'behind' | 'on_track';

/**
 * Helper type for variance color coding
 */
export interface VarianceColorScheme {
  text: string;
  bg: string;
  border: string;
  icon: 'up' | 'down' | 'neutral';
}
