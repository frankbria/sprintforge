/**
 * Tests for notification API client
 */

import type {
  NotificationListResponse,
  NotificationStats,
  NotificationRuleListResponse,
  NotificationRule,
  NotificationRuleCreate,
  NotificationLogListResponse,
} from '@/types/notification';

// Mock axios module BEFORE imports
jest.mock('axios', () => {
  class AxiosError extends Error {
    response?: any;
    constructor(message: string, response?: any) {
      super(message);
      this.response = response;
      this.name = 'AxiosError';
    }
  }

  return {
    __esModule: true,
    default: {
      create: jest.fn(() => ({
        get: jest.fn(),
        post: jest.fn(),
        patch: jest.fn(),
        delete: jest.fn(),
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() },
        },
      })),
    },
    AxiosError,
  };
});

// Import after mocking
import axios, { AxiosError } from 'axios';
import {
  getNotifications,
  getNotificationStats,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  getNotificationRules,
  createNotificationRule,
  updateNotificationRule,
  deleteNotificationRule,
  getNotificationLogs,
} from '@/lib/api/notifications';

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Notification API Client', () => {
  let mockApiClient: any;

  beforeAll(() => {
    // Get the mock client created by axios.create (created during module initialization)
    mockApiClient = (mockedAxios.create as jest.Mock).mock.results[0]?.value;
  });

  beforeEach(() => {
    // Clear mock call history but keep the instance
    if (mockApiClient) {
      mockApiClient.get.mockClear();
      mockApiClient.post.mockClear();
      mockApiClient.patch.mockClear();
      mockApiClient.delete.mockClear();
    }
  });

  describe('getNotifications', () => {
    it('should fetch notifications with default params', async () => {
      const mockResponse: NotificationListResponse = {
        total: 10,
        limit: 20,
        offset: 0,
        notifications: [
          {
            id: '1',
            user_id: 'user-1',
            title: 'Test Notification',
            message: 'Test message',
            event_type: 'project_created',
            priority: 'normal',
            channel: 'email',
            is_read: false,
            created_at: '2025-01-01T00:00:00Z',
          },
        ],
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await getNotifications();

      expect(mockApiClient.get).toHaveBeenCalledWith('/notifications', {
        params: {},
      });
      expect(result).toEqual(mockResponse);
    });

    it('should fetch notifications with custom params', async () => {
      const mockResponse: NotificationListResponse = {
        total: 5,
        limit: 10,
        offset: 0,
        notifications: [],
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      await getNotifications({ limit: 10, offset: 0, is_read: false });

      expect(mockApiClient.get).toHaveBeenCalledWith('/notifications', {
        params: { limit: 10, offset: 0, is_read: false },
      });
    });

    it('should throw error on API failure', async () => {
      const errorResponse = new AxiosError('Request failed', {
        data: { detail: 'Failed to fetch notifications' },
      });

      mockApiClient.get.mockRejectedValue(errorResponse);

      await expect(getNotifications()).rejects.toThrow(
        'Failed to fetch notifications'
      );
    });
  });

  describe('getNotificationStats', () => {
    it('should fetch notification statistics', async () => {
      const mockStats: NotificationStats = {
        unread_count: 5,
        total_count: 20,
        by_priority: { low: 5, normal: 10, high: 3, urgent: 2 },
        by_event_type: {
          project_created: 5,
          project_updated: 3,
          project_deleted: 1,
          baseline_created: 2,
          baseline_deviation: 1,
          sprint_started: 3,
          sprint_completed: 2,
          task_assigned: 1,
          task_completed: 1,
          deadline_approaching: 1,
          deadline_missed: 0,
        },
      };

      mockApiClient.get.mockResolvedValue({ data: mockStats });

      const result = await getNotificationStats();

      expect(mockApiClient.get).toHaveBeenCalledWith('/notifications/stats');
      expect(result).toEqual(mockStats);
    });
  });

  describe('markNotificationAsRead', () => {
    it('should mark a notification as read', async () => {
      mockApiClient.patch.mockResolvedValue({ data: {} });

      await markNotificationAsRead('notification-1');

      expect(mockApiClient.patch).toHaveBeenCalledWith(
        '/notifications/notification-1/read'
      );
    });

    it('should throw error on failure', async () => {
      const errorResponse = new AxiosError('Request failed', {
        data: { detail: 'Notification not found' },
      });

      mockApiClient.patch.mockRejectedValue(errorResponse);

      await expect(markNotificationAsRead('invalid-id')).rejects.toThrow(
        'Notification not found'
      );
    });
  });

  describe('markAllNotificationsAsRead', () => {
    it('should mark all notifications as read', async () => {
      mockApiClient.post.mockResolvedValue({ data: {} });

      await markAllNotificationsAsRead();

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/notifications/mark-all-read'
      );
    });
  });

  describe('getNotificationRules', () => {
    it('should fetch notification rules', async () => {
      const mockResponse: NotificationRuleListResponse = {
        total: 2,
        rules: [
          {
            id: 'rule-1',
            user_id: 'user-1',
            name: 'Project Updates',
            event_type: 'project_updated',
            channels: ['email', 'in_app'],
            enabled: true,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z',
          },
        ],
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await getNotificationRules();

      expect(mockApiClient.get).toHaveBeenCalledWith('/notification-rules');
      expect(result).toEqual(mockResponse);
    });
  });

  describe('createNotificationRule', () => {
    it('should create a new notification rule', async () => {
      const ruleData: NotificationRuleCreate = {
        name: 'New Rule',
        event_type: 'deadline_approaching',
        channels: ['email'],
        enabled: true,
      };

      const mockResponse: NotificationRule = {
        id: 'rule-2',
        user_id: 'user-1',
        ...ruleData,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      };

      mockApiClient.post.mockResolvedValue({ data: mockResponse });

      const result = await createNotificationRule(ruleData);

      expect(mockApiClient.post).toHaveBeenCalledWith(
        '/notification-rules',
        ruleData
      );
      expect(result).toEqual(mockResponse);
    });

    it('should throw error on validation failure', async () => {
      const errorResponse = new AxiosError('Request failed', {
        data: { detail: 'Invalid event type' },
      });

      mockApiClient.post.mockRejectedValue(errorResponse);

      const ruleData: NotificationRuleCreate = {
        name: 'Invalid Rule',
        event_type: 'invalid_type' as any,
        channels: ['email'],
      };

      await expect(createNotificationRule(ruleData)).rejects.toThrow(
        'Invalid event type'
      );
    });
  });

  describe('updateNotificationRule', () => {
    it('should update an existing notification rule', async () => {
      const updateData = {
        name: 'Updated Rule',
        enabled: false,
      };

      const mockResponse: NotificationRule = {
        id: 'rule-1',
        user_id: 'user-1',
        name: 'Updated Rule',
        event_type: 'project_created',
        channels: ['email'],
        enabled: false,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T12:00:00Z',
      };

      mockApiClient.patch.mockResolvedValue({ data: mockResponse });

      const result = await updateNotificationRule('rule-1', updateData);

      expect(mockApiClient.patch).toHaveBeenCalledWith(
        '/notification-rules/rule-1',
        updateData
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('deleteNotificationRule', () => {
    it('should delete a notification rule', async () => {
      mockApiClient.delete.mockResolvedValue({ data: {} });

      await deleteNotificationRule('rule-1');

      expect(mockApiClient.delete).toHaveBeenCalledWith(
        '/notification-rules/rule-1'
      );
    });

    it('should throw error on failure', async () => {
      const errorResponse = new AxiosError('Request failed', {
        data: { detail: 'Rule not found' },
      });

      mockApiClient.delete.mockRejectedValue(errorResponse);

      await expect(deleteNotificationRule('invalid-id')).rejects.toThrow(
        'Rule not found'
      );
    });
  });

  describe('getNotificationLogs', () => {
    it('should fetch notification logs with params', async () => {
      const mockResponse: NotificationLogListResponse = {
        total: 50,
        limit: 20,
        offset: 0,
        logs: [
          {
            id: 'log-1',
            notification_id: 'notif-1',
            channel: 'email',
            status: 'delivered',
            sent_at: '2025-01-01T00:00:00Z',
            delivered_at: '2025-01-01T00:01:00Z',
            created_at: '2025-01-01T00:00:00Z',
          },
        ],
      };

      mockApiClient.get.mockResolvedValue({ data: mockResponse });

      const result = await getNotificationLogs({ limit: 20, offset: 0 });

      expect(mockApiClient.get).toHaveBeenCalledWith('/notifications/logs', {
        params: { limit: 20, offset: 0 },
      });
      expect(result).toEqual(mockResponse);
    });
  });
});
