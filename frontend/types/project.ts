/**
 * Project type definitions matching backend API schemas
 */

export interface ProjectFeatures {
  monte_carlo: boolean;
  critical_path: boolean;
  gantt_chart: boolean;
  earned_value: boolean;
  resource_leveling: boolean;
  burndown_chart: boolean;
  sprint_tracking: boolean;
}

export interface ProjectConfiguration {
  project_id?: string;
  project_name: string;
  sprint_pattern: string;
  sprint_duration_weeks: number;
  working_days: number[]; // ISO weekday numbers (1=Monday, 7=Sunday)
  holidays: string[]; // ISO date strings (YYYY-MM-DD)
  hours_per_day: number;
  features: ProjectFeatures;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  template_id?: string;
  configuration: ProjectConfiguration;
}

export interface ProjectResponse {
  id: string;
  name: string;
  description?: string;
  template_id: string;
  owner_id: string;
  configuration: Record<string, any>;
  template_version: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  last_generated_at?: string;
}

export interface ProjectListResponse {
  total: number;
  limit: number;
  offset: number;
  projects: ProjectResponse[];
}

export interface TemplateInfo {
  id: string;
  name: string;
  description: string;
  category: 'agile' | 'waterfall' | 'hybrid';
  features: string[];
  recommended: boolean;
  preview?: string;
}

export interface SprintPattern {
  id: string;
  label: string;
  format: string;
  example: string;
  description: string;
}

export interface HolidayPreset {
  id: string;
  name: string;
  country: string;
  holidays: Array<{
    date: string;
    name: string;
  }>;
}

export interface WizardFormData {
  // Step 1: Project Basics
  name: string;
  description: string;
  template_id: string;

  // Step 2: Sprint Configuration
  sprint_pattern: string;
  sprint_duration_weeks: number;
  working_days: number[];

  // Step 3: Holiday Calendar
  holidays: string[];
  holiday_preset?: string;

  // Step 4: Feature Selection
  features: ProjectFeatures;

  // Additional config
  hours_per_day: number;
}
