/**
 * API client for notification operations
 */

import axios, { AxiosError, AxiosInstance } from 'axios';
import type {
  NotificationListResponse,
  NotificationStats,
  NotificationRuleListResponse,
  NotificationRule,
  NotificationRuleCreate,
  NotificationRuleUpdate,
  NotificationLogListResponse,
} from '@/types/notification';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default config
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add auth token interceptor
  client.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined'
      ? sessionStorage.getItem('auth_token')
      : null;

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  });

  return client;
}

const apiClient = createApiClient();

/**
 * Get list of notifications
 */
export async function getNotifications(params?: {
  limit?: number;
  offset?: number;
  is_read?: boolean;
  priority?: string;
  event_type?: string;
}): Promise<NotificationListResponse> {
  try {
    const response = await apiClient.get<NotificationListResponse>('/notifications', { params: params || {} });
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch notifications'
      );
    }
    throw error;
  }
}

/**
 * Get notification statistics
 */
export async function getNotificationStats(): Promise<NotificationStats> {
  try {
    const response = await apiClient.get<NotificationStats>('/notifications/stats');
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch notification stats'
      );
    }
    throw error;
  }
}

/**
 * Mark a notification as read
 */
export async function markNotificationAsRead(id: string): Promise<void> {
  try {
    await apiClient.patch(`/notifications/${id}/read`);
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to mark notification as read'
      );
    }
    throw error;
  }
}

/**
 * Mark all notifications as read
 */
export async function markAllNotificationsAsRead(): Promise<void> {
  try {
    await apiClient.post('/notifications/mark-all-read');
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to mark all notifications as read'
      );
    }
    throw error;
  }
}

/**
 * Get list of notification rules
 */
export async function getNotificationRules(): Promise<NotificationRuleListResponse> {
  try {
    const response = await apiClient.get<NotificationRuleListResponse>('/notification-rules');
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch notification rules'
      );
    }
    throw error;
  }
}

/**
 * Create a new notification rule
 */
export async function createNotificationRule(
  data: NotificationRuleCreate
): Promise<NotificationRule> {
  try {
    const response = await apiClient.post<NotificationRule>('/notification-rules', data);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to create notification rule'
      );
    }
    throw error;
  }
}

/**
 * Update a notification rule
 */
export async function updateNotificationRule(
  id: string,
  data: NotificationRuleUpdate
): Promise<NotificationRule> {
  try {
    const response = await apiClient.patch<NotificationRule>(`/notification-rules/${id}`, data);
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to update notification rule'
      );
    }
    throw error;
  }
}

/**
 * Delete a notification rule
 */
export async function deleteNotificationRule(id: string): Promise<void> {
  try {
    await apiClient.delete(`/notification-rules/${id}`);
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to delete notification rule'
      );
    }
    throw error;
  }
}

/**
 * Get notification logs
 */
export async function getNotificationLogs(params?: {
  limit?: number;
  offset?: number;
  status?: string;
  channel?: string;
}): Promise<NotificationLogListResponse> {
  try {
    const response = await apiClient.get<NotificationLogListResponse>('/notifications/logs', { params: params || {} });
    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw new Error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch notification logs'
      );
    }
    throw error;
  }
}
