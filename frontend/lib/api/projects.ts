/**
 * API client for project CRUD operations
 */

import axios, { AxiosError } from 'axios';
import type {
  ProjectCreate,
  ProjectResponse,
  ProjectListResponse,
} from '@/types/project';

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
 * Create a new project
 */
export async function createProject(
  data: ProjectCreate,
  accessToken?: string
): Promise<ProjectResponse> {
  try {
    const config = accessToken
      ? { headers: { Authorization: `Bearer ${accessToken}` } }
      : {};

    const response = await apiClient.post<ProjectResponse>('/projects', data, config);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to create project'
      );
    }
    throw error;
  }
}

/**
 * Get list of projects
 */
export async function getProjects(params?: {
  limit?: number;
  offset?: number;
  sort?: string;
  search?: string;
}): Promise<ProjectListResponse> {
  try {
    const response = await apiClient.get<ProjectListResponse>('/projects', { params });
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch projects'
      );
    }
    throw error;
  }
}

/**
 * Get a single project by ID
 */
export async function getProject(id: string): Promise<ProjectResponse> {
  try {
    const response = await apiClient.get<ProjectResponse>(`/projects/${id}`);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch project'
      );
    }
    throw error;
  }
}

/**
 * Update a project
 */
export async function updateProject(
  id: string,
  data: Partial<ProjectCreate>
): Promise<ProjectResponse> {
  try {
    const response = await apiClient.patch<ProjectResponse>(`/projects/${id}`, data);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to update project'
      );
    }
    throw error;
  }
}

/**
 * Delete a project
 */
export async function deleteProject(id: string): Promise<void> {
  try {
    await apiClient.delete(`/projects/${id}`);
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to delete project'
      );
    }
    throw error;
  }
}

/**
 * Generate Excel file for a project
 */
export async function generateExcel(id: string): Promise<Blob> {
  try {
    const response = await apiClient.post(
      `/projects/${id}/generate`,
      {},
      { responseType: 'blob' }
    );
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to generate Excel'
      );
    }
    throw error;
  }
}
