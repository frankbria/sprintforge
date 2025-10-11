/**
 * Step 6: Review & Confirm
 * Summary of all selections before creation
 */

'use client';

import * as React from 'react';
import { UseFormReturn } from 'react-hook-form';
import { CheckCircle, Calendar, Settings, Sparkles } from 'lucide-react';
import {
  PROJECT_TEMPLATES,
  SPRINT_PATTERNS,
  FEATURE_INFO,
} from '@/lib/wizard-constants';
import type { WizardFormData } from '@/lib/wizard-schema';

interface ReviewStepProps {
  form: UseFormReturn<WizardFormData>;
}

export function ReviewStep({ form }: ReviewStepProps) {
  const { watch } = form;
  const formData = watch();

  const template = PROJECT_TEMPLATES.find((t) => t.id === formData.template_id);
  const sprintPattern = SPRINT_PATTERNS.find(
    (p) => p.id === formData.sprint_pattern
  );

  const enabledFeatures = Object.entries(formData.features)
    .filter(([_, enabled]) => enabled)
    .map(([key]) => FEATURE_INFO[key as keyof typeof FEATURE_INFO]);

  const weekdayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const workingDaysText = formData.working_days
    .map((day) => weekdayNames[day - 1])
    .join(', ');

  return (
    <div className="space-y-6">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center gap-2">
          <CheckCircle className="h-5 w-5 text-green-600" />
          <p className="text-sm text-green-800 font-medium">
            Ready to create your project! Review the configuration below.
          </p>
        </div>
      </div>

      {/* Project Basics */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-600" />
          Project Basics
        </h4>
        <dl className="space-y-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">Project Name</dt>
            <dd className="text-sm text-gray-900 font-medium">
              {formData.name}
            </dd>
          </div>
          {formData.description && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Description</dt>
              <dd className="text-sm text-gray-900">{formData.description}</dd>
            </div>
          )}
          <div>
            <dt className="text-sm font-medium text-gray-500">Template</dt>
            <dd className="text-sm text-gray-900">
              {template?.name}{' '}
              <span className="text-gray-500">({template?.category})</span>
            </dd>
          </div>
        </dl>
      </div>

      {/* Sprint Configuration */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Calendar className="h-5 w-5 text-blue-600" />
          Sprint Configuration
        </h4>
        <dl className="space-y-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">
              Sprint Pattern
            </dt>
            <dd className="text-sm text-gray-900">
              {sprintPattern?.label}{' '}
              <span className="text-gray-500 font-mono text-xs">
                ({sprintPattern?.example})
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">
              Sprint Duration
            </dt>
            <dd className="text-sm text-gray-900">
              {formData.sprint_duration_weeks} week
              {formData.sprint_duration_weeks !== 1 ? 's' : ''}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Working Days</dt>
            <dd className="text-sm text-gray-900">{workingDaysText}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">
              Hours per Day
            </dt>
            <dd className="text-sm text-gray-900">
              {formData.hours_per_day} hours
            </dd>
          </div>
        </dl>
      </div>

      {/* Holidays */}
      {formData.holidays.length > 0 && (
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">
            Holidays ({formData.holidays.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {formData.holidays.slice(0, 5).map((date) => (
              <span
                key={date}
                className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
              >
                {new Date(date + 'T00:00:00').toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                })}
              </span>
            ))}
            {formData.holidays.length > 5 && (
              <span className="text-xs text-gray-500 px-2 py-1">
                +{formData.holidays.length - 5} more
              </span>
            )}
          </div>
        </div>
      )}

      {/* Features */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Settings className="h-5 w-5 text-blue-600" />
          Enabled Features
        </h4>
        {enabledFeatures.length > 0 ? (
          <div className="space-y-2">
            {enabledFeatures.map((feature) => (
              <div key={feature.name} className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {feature.name}
                  </p>
                  <p className="text-xs text-gray-500">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">
            No advanced features enabled (basic configuration)
          </p>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Next Steps:</strong> After creation, you can generate Excel
          files, share your project, and manage tasks through the dashboard.
        </p>
      </div>
    </div>
  );
}
