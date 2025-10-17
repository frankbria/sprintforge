/**
 * API client for analytics endpoints
 */

import axios, { AxiosError } from 'axios';
import type {
  AnalyticsOverviewResponse,
  CriticalPathResponse,
  ResourceUtilizationResponse,
  SimulationResultsResponse,
  ProgressMetricsResponse,
} from '@/types/analytics';

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
 * Get comprehensive analytics overview for a project
 */
export async function getAnalyticsOverview(
  projectId: string
): Promise<AnalyticsOverviewResponse> {
  try {
    const response = await apiClient.get<AnalyticsOverviewResponse>(
      `/projects/${projectId}/analytics/overview`
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch analytics overview'
      );
    }
    throw error;
  }
}

/**
 * Get detailed critical path analysis
 */
export async function getCriticalPathAnalytics(
  projectId: string
): Promise<CriticalPathResponse> {
  try {
    const response = await apiClient.get<CriticalPathResponse>(
      `/projects/${projectId}/analytics/critical-path`
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch critical path analytics'
      );
    }
    throw error;
  }
}

/**
 * Get resource utilization metrics
 */
export async function getResourceAnalytics(
  projectId: string
): Promise<ResourceUtilizationResponse> {
  try {
    const response = await apiClient.get<ResourceUtilizationResponse>(
      `/projects/${projectId}/analytics/resources`
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch resource analytics'
      );
    }
    throw error;
  }
}

/**
 * Get Monte Carlo simulation summary
 */
export async function getSimulationAnalytics(
  projectId: string
): Promise<SimulationResultsResponse> {
  try {
    const response = await apiClient.get<SimulationResultsResponse>(
      `/projects/${projectId}/analytics/simulation`
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch simulation analytics'
      );
    }
    throw error;
  }
}

/**
 * Get progress tracking metrics
 */
export async function getProgressAnalytics(
  projectId: string
): Promise<ProgressMetricsResponse> {
  try {
    const response = await apiClient.get<ProgressMetricsResponse>(
      `/projects/${projectId}/analytics/progress`
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch progress analytics'
      );
    }
    throw error;
  }
}
