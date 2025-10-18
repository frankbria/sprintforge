/**
 * List component for displaying notification rules
 */

'use client';

import * as React from 'react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import type { NotificationRule } from '@/types/notification';

interface NotificationRulesListProps {
  rules: NotificationRule[];
  onEdit: (rule: NotificationRule) => void;
  onDelete: (id: string) => void;
  onToggle: (id: string, enabled: boolean) => void;
  loading?: boolean;
}

const CHANNEL_LABELS: Record<string, string> = {
  email: 'Email',
  in_app: 'In-App',
  webhook: 'Webhook',
};

const EVENT_TYPE_LABELS: Record<string, string> = {
  project_created: 'Project Created',
  project_updated: 'Project Updated',
  project_deleted: 'Project Deleted',
  baseline_created: 'Baseline Created',
  baseline_deviation: 'Baseline Deviation',
  sprint_started: 'Sprint Started',
  sprint_completed: 'Sprint Completed',
  task_assigned: 'Task Assigned',
  task_completed: 'Task Completed',
  deadline_approaching: 'Deadline Approaching',
  deadline_missed: 'Deadline Missed',
};

export function NotificationRulesList({
  rules,
  onEdit,
  onDelete,
  onToggle,
  loading,
}: NotificationRulesListProps) {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <p className="text-gray-700">Loading notification rules...</p>
      </div>
    );
  }

  if (rules.length === 0) {
    return (
      <Card className="p-12 text-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="rounded-full bg-gray-100 p-3">
            <svg
              className="h-8 w-8 text-gray-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              No Notification Rules
            </h3>
            <p className="mt-1 text-sm text-gray-700">
              Get started by creating your first notification rule.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {rules.map((rule) => (
        <Card key={rule.id} className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <h3 className="text-lg font-medium text-gray-900">
                  {rule.name}
                </h3>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    role="switch"
                    checked={rule.enabled}
                    onChange={(e) => onToggle(rule.id, e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
              <p className="mt-1 text-sm text-gray-700">
                {EVENT_TYPE_LABELS[rule.event_type] || rule.event_type}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {rule.channels.map((channel) => (
                  <span
                    key={channel}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {CHANNEL_LABELS[channel] || channel}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex items-center space-x-2 ml-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onEdit(rule)}
                aria-label={`Edit ${rule.name}`}
              >
                Edit
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(rule.id)}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                aria-label={`Delete ${rule.name}`}
              >
                Delete
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
