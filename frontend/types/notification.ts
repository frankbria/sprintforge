/**
 * Notification type definitions matching backend API schemas
 */

export type NotificationChannel = 'email' | 'in_app' | 'webhook';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';
export type NotificationEventType =
  | 'project_created'
  | 'project_updated'
  | 'project_deleted'
  | 'baseline_created'
  | 'baseline_deviation'
  | 'sprint_started'
  | 'sprint_completed'
  | 'task_assigned'
  | 'task_completed'
  | 'deadline_approaching'
  | 'deadline_missed';

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  event_type: NotificationEventType;
  priority: NotificationPriority;
  channel: NotificationChannel;
  is_read: boolean;
  metadata?: Record<string, any>;
  created_at: string;
  read_at?: string;
}

export interface NotificationRule {
  id: string;
  user_id: string;
  name: string;
  event_type: NotificationEventType;
  channels: NotificationChannel[];
  enabled: boolean;
  conditions?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface NotificationRuleCreate {
  name: string;
  event_type: NotificationEventType;
  channels: NotificationChannel[];
  enabled?: boolean;
  conditions?: Record<string, any>;
}

export interface NotificationRuleUpdate {
  name?: string;
  event_type?: NotificationEventType;
  channels?: NotificationChannel[];
  enabled?: boolean;
  conditions?: Record<string, any>;
}

export interface NotificationLog {
  id: string;
  notification_id: string;
  channel: NotificationChannel;
  status: 'pending' | 'sent' | 'failed' | 'delivered';
  error_message?: string;
  sent_at?: string;
  delivered_at?: string;
  created_at: string;
}

export interface NotificationTemplate {
  id: string;
  name: string;
  event_type: NotificationEventType;
  subject_template: string;
  body_template: string;
  channel: NotificationChannel;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  total: number;
  limit: number;
  offset: number;
  notifications: Notification[];
}

export interface NotificationRuleListResponse {
  total: number;
  rules: NotificationRule[];
}

export interface NotificationLogListResponse {
  total: number;
  limit: number;
  offset: number;
  logs: NotificationLog[];
}

export interface NotificationStats {
  unread_count: number;
  total_count: number;
  by_priority: Record<NotificationPriority, number>;
  by_event_type: Record<NotificationEventType, number>;
}
