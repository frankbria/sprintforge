/**
 * Form component for creating/editing notification rules
 */

'use client';

import * as React from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import type {
  NotificationRule,
  NotificationRuleCreate,
  NotificationEventType,
  NotificationChannel,
} from '@/types/notification';

interface NotificationRuleFormProps {
  rule?: NotificationRule;
  onSubmit: (data: NotificationRuleCreate) => Promise<void> | void;
  onCancel: () => void;
}

const EVENT_TYPE_OPTIONS: { value: NotificationEventType; label: string }[] = [
  { value: 'project_created', label: 'Project Created' },
  { value: 'project_updated', label: 'Project Updated' },
  { value: 'project_deleted', label: 'Project Deleted' },
  { value: 'baseline_created', label: 'Baseline Created' },
  { value: 'baseline_deviation', label: 'Baseline Deviation' },
  { value: 'sprint_started', label: 'Sprint Started' },
  { value: 'sprint_completed', label: 'Sprint Completed' },
  { value: 'task_assigned', label: 'Task Assigned' },
  { value: 'task_completed', label: 'Task Completed' },
  { value: 'deadline_approaching', label: 'Deadline Approaching' },
  { value: 'deadline_missed', label: 'Deadline Missed' },
];

const CHANNEL_OPTIONS: { value: NotificationChannel; label: string }[] = [
  { value: 'email', label: 'Email' },
  { value: 'in_app', label: 'In-App' },
  { value: 'webhook', label: 'Webhook' },
];

export function NotificationRuleForm({
  rule,
  onSubmit,
  onCancel,
}: NotificationRuleFormProps) {
  const [formData, setFormData] = React.useState<NotificationRuleCreate>({
    name: rule?.name || '',
    event_type: rule?.event_type || 'project_created',
    channels: rule?.channels || [],
    enabled: rule?.enabled !== undefined ? rule.enabled : true,
  });

  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Rule name is required';
    }

    if (formData.channels.length === 0) {
      newErrors.channels = 'At least one channel must be selected';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChannelToggle = (channel: NotificationChannel) => {
    setFormData((prev) => {
      const channels = prev.channels.includes(channel)
        ? prev.channels.filter((c) => c !== channel)
        : [...prev.channels, channel];

      return { ...prev, channels };
    });

    if (errors.channels) {
      setErrors((prev) => ({ ...prev, channels: '' }));
    }
  };

  const handleInputChange = (field: keyof NotificationRuleCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));

    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <Label htmlFor="name">Rule Name</Label>
        <Input
          id="name"
          type="text"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          placeholder="Enter rule name"
          className={errors.name ? 'border-red-500' : ''}
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
        )}
      </div>

      <div>
        <Label htmlFor="event_type">Event Type</Label>
        <select
          id="event_type"
          value={formData.event_type}
          onChange={(e) =>
            handleInputChange('event_type', e.target.value as NotificationEventType)
          }
          className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:border-blue-500"
        >
          {EVENT_TYPE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <Label>Notification Channels</Label>
        <div className="mt-2 space-y-2">
          {CHANNEL_OPTIONS.map((option) => (
            <label
              key={option.value}
              className="flex items-center space-x-2 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={formData.channels.includes(option.value)}
                onChange={() => handleChannelToggle(option.value)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-900">{option.label}</span>
            </label>
          ))}
        </div>
        {errors.channels && (
          <p className="mt-1 text-sm text-red-600">{errors.channels}</p>
        )}
      </div>

      <div>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            id="enabled"
            checked={formData.enabled}
            onChange={(e) => handleInputChange('enabled', e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <Label htmlFor="enabled" className="cursor-pointer">
            Enabled
          </Label>
        </label>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <Button
          type="button"
          variant="ghost"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          {rule ? 'Update Rule' : 'Create Rule'}
        </Button>
      </div>
    </form>
  );
}
