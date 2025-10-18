/**
 * Step 3: Sprint Configuration
 * Pattern, duration, and working days
 */

'use client';

import * as React from 'react';
import { UseFormReturn } from 'react-hook-form';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { SPRINT_PATTERNS } from '@/lib/wizard-constants';
import { cn } from '@/lib/utils';
import type { WizardFormData } from '@/lib/wizard-schema';

interface SprintConfigStepProps {
  form: UseFormReturn<WizardFormData>;
}

const WEEKDAYS = [
  { value: 1, label: 'Mon' },
  { value: 2, label: 'Tue' },
  { value: 3, label: 'Wed' },
  { value: 4, label: 'Thu' },
  { value: 5, label: 'Fri' },
  { value: 6, label: 'Sat' },
  { value: 7, label: 'Sun' },
];

export function SprintConfigStep({ form }: SprintConfigStepProps) {
  const {
    register,
    watch,
    setValue,
    formState: { errors },
  } = form;

  const selectedPattern = watch('sprint_pattern');
  const selectedDuration = watch('sprint_duration_weeks');
  const workingDays = watch('working_days') || [];

  const toggleWorkingDay = (day: number) => {
    const current = workingDays || [];
    if (current.includes(day)) {
      setValue(
        'working_days',
        current.filter((d) => d !== day)
      );
    } else {
      setValue('working_days', [...current, day].sort());
    }
  };

  // Generate sprint preview
  const getSprintPreview = () => {
    const pattern = SPRINT_PATTERNS.find((p) => p.id === selectedPattern);
    return pattern?.example || 'Sprint 1';
  };

  return (
    <div className="space-y-6">
      {/* Sprint Pattern */}
      <div className="space-y-2">
        <Label>Sprint Numbering Pattern</Label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {SPRINT_PATTERNS.map((pattern) => (
            <button
              key={pattern.id}
              type="button"
              onClick={() => setValue('sprint_pattern', pattern.id)}
              className={cn(
                'p-3 border-2 rounded-lg text-left transition-all',
                selectedPattern === pattern.id
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              )}
            >
              <div className="font-medium text-gray-900">{pattern.label}</div>
              <div className="text-sm text-gray-800 mt-1">
                {pattern.description}
              </div>
              <div className="text-xs text-gray-700 mt-1 font-mono bg-gray-100 px-2 py-1 rounded">
                {pattern.example}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Live Preview */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>Preview:</strong> Your sprints will be numbered like:{' '}
          <span className="font-mono font-semibold">{getSprintPreview()}</span>
        </p>
      </div>

      {/* Sprint Duration */}
      <div className="space-y-2">
        <Label htmlFor="sprint_duration_weeks">
          Sprint Duration (weeks) <span className="text-red-500">*</span>
        </Label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            id="sprint_duration_weeks"
            min="1"
            max="8"
            {...register('sprint_duration_weeks', { valueAsNumber: true })}
            className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
          <div className="flex items-center gap-2 min-w-[100px]">
            <Input
              type="number"
              min="1"
              max="8"
              {...register('sprint_duration_weeks', { valueAsNumber: true })}
              className="w-20 text-center"
            />
            <span className="text-sm text-gray-800">weeks</span>
          </div>
        </div>
        {errors.sprint_duration_weeks && (
          <p className="text-sm text-red-600">
            {errors.sprint_duration_weeks.message}
          </p>
        )}
      </div>

      {/* Working Days */}
      <div className="space-y-2">
        <Label>Working Days <span className="text-red-500">*</span></Label>
        <div className="flex gap-2">
          {WEEKDAYS.map((day) => (
            <button
              key={day.value}
              type="button"
              onClick={() => toggleWorkingDay(day.value)}
              className={cn(
                'flex-1 py-2 px-3 rounded-md font-medium text-sm transition-all',
                workingDays.includes(day.value)
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
              )}
            >
              {day.label}
            </button>
          ))}
        </div>
        {errors.working_days && (
          <p className="text-sm text-red-600">{errors.working_days.message}</p>
        )}
        <p className="text-xs text-gray-700">
          Selected: {workingDays.length} day{workingDays.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Hours per Day */}
      <div className="space-y-2">
        <Label htmlFor="hours_per_day">Working Hours per Day</Label>
        <Input
          id="hours_per_day"
          type="number"
          min="1"
          max="24"
          step="0.5"
          {...register('hours_per_day', { valueAsNumber: true })}
        />
        {errors.hours_per_day && (
          <p className="text-sm text-red-600">{errors.hours_per_day.message}</p>
        )}
      </div>
    </div>
  );
}
