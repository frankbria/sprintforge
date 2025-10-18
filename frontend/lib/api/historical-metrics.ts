/**
 * API client for historical metrics endpoints
 */

import axios, { AxiosError } from 'axios';
import type {
  HistoricalMetricsParams,
  VelocityTrendParams,
  CompletionTrendsParams,
  ForecastParams,
  HistoricalMetric,
  VelocityTrendResponse,
  CompletionTrendsResponse,
  ForecastData,
  MetricsSummaryResponse,
} from '@/types/historical-metrics';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token interceptor
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined'
    ? sessionStorage.getItem('auth_token')
    : null;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

/**
 * Get historical metrics for a project with optional filtering
 */
export async function getHistoricalMetrics(
  projectId: string,
  params?: HistoricalMetricsParams
): Promise<HistoricalMetric[]> {
  try {
    const response = await apiClient.get<HistoricalMetric[]>(
      `/projects/${projectId}/metrics/historical`,
      { params }
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch historical metrics'
      );
    }
    throw error;
  }
}

/**
 * Get velocity trend analysis with moving average
 */
export async function getVelocityTrend(
  projectId: string,
  params?: VelocityTrendParams
): Promise<VelocityTrendResponse> {
  try {
    const response = await apiClient.get<VelocityTrendResponse>(
      `/projects/${projectId}/metrics/velocity-trend`,
      { params }
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch velocity trend'
      );
    }
    throw error;
  }
}

/**
 * Get completion trends with configurable granularity
 */
export async function getCompletionTrends(
  projectId: string,
  params?: CompletionTrendsParams
): Promise<CompletionTrendsResponse> {
  try {
    const response = await apiClient.get<CompletionTrendsResponse>(
      `/projects/${projectId}/metrics/completion-trends`,
      { params }
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch completion trends'
      );
    }
    throw error;
  }
}

/**
 * Get forecast predictions with confidence intervals
 */
export async function getForecast(
  projectId: string,
  params?: ForecastParams
): Promise<ForecastData> {
  try {
    const response = await apiClient.get<ForecastData>(
      `/projects/${projectId}/metrics/forecast`,
      { params }
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch forecast data'
      );
    }
    throw error;
  }
}

/**
 * Get metrics summary dashboard
 */
export async function getMetricsSummary(
  projectId: string
): Promise<MetricsSummaryResponse> {
  try {
    const response = await apiClient.get<MetricsSummaryResponse>(
      `/projects/${projectId}/metrics/summary`
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch metrics summary'
      );
    }
    throw error;
  }
}
