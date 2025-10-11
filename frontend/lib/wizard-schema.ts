/**
 * Zod schema for wizard form validation
 */

import { z } from 'zod';

export const wizardSchema = z.object({
  // Step 1: Project Basics
  name: z.string()
    .min(1, 'Project name is required')
    .max(255, 'Project name must be 255 characters or less'),

  description: z.string()
    .max(5000, 'Description must be 5000 characters or less')
    .optional()
    .default(''),

  template_id: z.string()
    .min(1, 'Please select a template'),

  // Step 2: Sprint Configuration
  sprint_pattern: z.string()
    .min(1, 'Sprint pattern is required'),

  sprint_duration_weeks: z.number()
    .int('Duration must be a whole number')
    .min(1, 'Duration must be at least 1 week')
    .max(8, 'Duration must be 8 weeks or less')
    .default(2),

  working_days: z.array(z.number().int().min(1).max(7))
    .min(1, 'At least one working day must be selected')
    .refine(
      (days) => days.length === new Set(days).size,
      'Duplicate working days are not allowed'
    ),

  hours_per_day: z.number()
    .min(1, 'Hours per day must be at least 1')
    .max(24, 'Hours per day cannot exceed 24')
    .default(8),

  // Step 3: Holiday Calendar
  holidays: z.array(z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format'))
    .default([]),

  holiday_preset: z.string().optional(),

  // Step 4: Feature Selection
  features: z.object({
    monte_carlo: z.boolean().default(false),
    critical_path: z.boolean().default(true),
    gantt_chart: z.boolean().default(true),
    earned_value: z.boolean().default(false),
    resource_leveling: z.boolean().default(false),
    burndown_chart: z.boolean().default(false),
    sprint_tracking: z.boolean().default(false),
  }),
});

export type WizardFormData = z.infer<typeof wizardSchema>;

/**
 * Step-specific validation schemas
 */
export const step1Schema = wizardSchema.pick({
  name: true,
  description: true,
  template_id: true,
});

export const step2Schema = wizardSchema.pick({
  sprint_pattern: true,
  sprint_duration_weeks: true,
  working_days: true,
  hours_per_day: true,
});

export const step3Schema = wizardSchema.pick({
  holidays: true,
  holiday_preset: true,
});

export const step4Schema = wizardSchema.pick({
  features: true,
});
