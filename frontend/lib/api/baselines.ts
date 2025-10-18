/**
 * API client for baseline management endpoints
 *
 * Provides functions to interact with the baseline backend API for:
 * - Creating project baselines (snapshots)
 * - Listing and retrieving baselines
 * - Deleting baselines
 * - Setting active baseline
 * - Comparing baseline to current project state
 */

import axios, { AxiosError } from 'axios';
import type {
  Baseline,
  BaselineDetail,
  BaselineComparison,
  CreateBaselineRequest,
  BaselineListResponse,
  SetBaselineActiveResponse,
} from '@/types/baseline';

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
 * Get all baselines for a project
 *
 * @param projectId - UUID of the project
 * @param page - Page number (default: 1)
 * @param limit - Items per page (default: 50)
 * @returns Paginated list of baselines
 */
export async function getBaselines(
  projectId: string,
  page: number = 1,
  limit: number = 50
): Promise<BaselineListResponse> {
  try {
    const response = await apiClient.get<BaselineListResponse>(
      `/projects/${projectId}/baselines`,
      {
        params: { page, limit },
      }
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch baselines'
      );
    }
    throw error;
  }
}

/**
 * Get detailed baseline information including snapshot data
 *
 * @param projectId - UUID of the project
 * @param baselineId - UUID of the baseline
 * @returns Full baseline details with snapshot data
 */
export async function getBaseline(
  projectId: string,
  baselineId: string
): Promise<BaselineDetail> {
  try {
    const response = await apiClient.get<BaselineDetail>(
      `/projects/${projectId}/baselines/${baselineId}`
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch baseline details'
      );
    }
    throw error;
  }
}

/**
 * Create a new baseline snapshot
 *
 * @param projectId - UUID of the project
 * @param data - Baseline name and optional description
 * @returns Created baseline information
 */
export async function createBaseline(
  projectId: string,
  data: CreateBaselineRequest
): Promise<Baseline> {
  try {
    const response = await apiClient.post<Baseline>(
      `/projects/${projectId}/baselines`,
      data
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      // Handle specific error codes
      if (error.response?.status === 413) {
        throw new Error('Snapshot size exceeds maximum allowed size (10MB)');
      }
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to create baseline'
      );
    }
    throw error;
  }
}

/**
 * Delete a baseline
 *
 * @param projectId - UUID of the project
 * @param baselineId - UUID of the baseline to delete
 */
export async function deleteBaseline(
  projectId: string,
  baselineId: string
): Promise<void> {
  try {
    await apiClient.delete(
      `/projects/${projectId}/baselines/${baselineId}`
    );
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to delete baseline'
      );
    }
    throw error;
  }
}

/**
 * Set a baseline as the active baseline for the project
 *
 * Automatically deactivates all other baselines for the project.
 *
 * @param projectId - UUID of the project
 * @param baselineId - UUID of the baseline to activate
 * @returns Activation confirmation
 */
export async function setBaselineActive(
  projectId: string,
  baselineId: string
): Promise<SetBaselineActiveResponse> {
  try {
    const response = await apiClient.patch<SetBaselineActiveResponse>(
      `/projects/${projectId}/baselines/${baselineId}/activate`
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to activate baseline'
      );
    }
    throw error;
  }
}

/**
 * Compare baseline to current project state
 *
 * Returns variance analysis showing how the project has changed
 * since the baseline was created.
 *
 * @param projectId - UUID of the project
 * @param baselineId - UUID of the baseline to compare against
 * @param includeUnchanged - Whether to include tasks with no variance (default: false)
 * @returns Comparison results with variance analysis
 */
export async function compareBaseline(
  projectId: string,
  baselineId: string,
  includeUnchanged: boolean = false
): Promise<BaselineComparison> {
  try {
    const response = await apiClient.get<BaselineComparison>(
      `/projects/${projectId}/baselines/${baselineId}/compare`,
      {
        params: { include_unchanged: includeUnchanged },
      }
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to compare baseline'
      );
    }
    throw error;
  }
}
