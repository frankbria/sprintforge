/**
 * Constants and data for project wizard
 */

import type { TemplateInfo, SprintPattern, HolidayPreset } from '@/types/project';

/**
 * Available project templates
 */
export const PROJECT_TEMPLATES: TemplateInfo[] = [
  {
    id: 'agile_basic',
    name: 'Agile Basic',
    description: 'Simple sprint-based project with essential features',
    category: 'agile',
    features: ['Sprint Tracking', 'Gantt Chart', 'Basic Analytics'],
    recommended: true,
  },
  {
    id: 'agile_advanced',
    name: 'Agile Advanced',
    description: 'Full-featured agile project with Monte Carlo and EVM',
    category: 'agile',
    features: [
      'Sprint Tracking',
      'Monte Carlo Simulation',
      'Critical Path Analysis',
      'Earned Value Management',
      'Burndown Charts',
      'Gantt Chart',
    ],
    recommended: false,
  },
  {
    id: 'waterfall_basic',
    name: 'Waterfall Basic',
    description: 'Traditional project management with phase-based planning',
    category: 'waterfall',
    features: ['Phase Tracking', 'Gantt Chart', 'Critical Path'],
    recommended: false,
  },
  {
    id: 'waterfall_advanced',
    name: 'Waterfall Advanced',
    description: 'Advanced waterfall with resource leveling and EVM',
    category: 'waterfall',
    features: [
      'Phase Tracking',
      'Critical Path Analysis',
      'Resource Leveling',
      'Earned Value Management',
      'Gantt Chart',
    ],
    recommended: false,
  },
  {
    id: 'hybrid',
    name: 'Hybrid Approach',
    description: 'Combines agile sprints with waterfall phases',
    category: 'hybrid',
    features: [
      'Sprint & Phase Tracking',
      'Flexible Planning',
      'Gantt Chart',
      'Critical Path',
    ],
    recommended: false,
  },
];

/**
 * Sprint pattern options
 */
export const SPRINT_PATTERNS: SprintPattern[] = [
  {
    id: 'yy_q_num',
    label: 'Year.Quarter.Number',
    format: 'YY.Q.#',
    example: '25.1.3 (2025, Q1, Sprint 3)',
    description: 'Sprint number within year and quarter',
  },
  {
    id: 'pi_sprint',
    label: 'PI-Sprint Format',
    format: 'PI-N.Sprint-M',
    example: 'PI-2.Sprint-4',
    description: 'Program Increment with sprint number (SAFe)',
  },
  {
    id: 'sequential',
    label: 'Sequential Numbering',
    format: 'Sprint #',
    example: 'Sprint 42',
    description: 'Simple sequential sprint numbers',
  },
  {
    id: 'yy_ww',
    label: 'Year.Week',
    format: 'YY.WW',
    example: '25.15 (Week 15 of 2025)',
    description: 'Year and ISO week number',
  },
];

/**
 * Holiday presets for different countries/regions
 */
export const HOLIDAY_PRESETS: HolidayPreset[] = [
  {
    id: 'us_2025',
    name: 'United States 2025',
    country: 'US',
    holidays: [
      { date: '2025-01-01', name: 'New Year\'s Day' },
      { date: '2025-01-20', name: 'Martin Luther King Jr. Day' },
      { date: '2025-02-17', name: 'Presidents\' Day' },
      { date: '2025-05-26', name: 'Memorial Day' },
      { date: '2025-07-04', name: 'Independence Day' },
      { date: '2025-09-01', name: 'Labor Day' },
      { date: '2025-10-13', name: 'Columbus Day' },
      { date: '2025-11-11', name: 'Veterans Day' },
      { date: '2025-11-27', name: 'Thanksgiving' },
      { date: '2025-12-25', name: 'Christmas' },
    ],
  },
  {
    id: 'uk_2025',
    name: 'United Kingdom 2025',
    country: 'UK',
    holidays: [
      { date: '2025-01-01', name: 'New Year\'s Day' },
      { date: '2025-04-18', name: 'Good Friday' },
      { date: '2025-04-21', name: 'Easter Monday' },
      { date: '2025-05-05', name: 'Early May Bank Holiday' },
      { date: '2025-05-26', name: 'Spring Bank Holiday' },
      { date: '2025-08-25', name: 'Summer Bank Holiday' },
      { date: '2025-12-25', name: 'Christmas Day' },
      { date: '2025-12-26', name: 'Boxing Day' },
    ],
  },
  {
    id: 'eu_2025',
    name: 'European Union 2025 (Common)',
    country: 'EU',
    holidays: [
      { date: '2025-01-01', name: 'New Year\'s Day' },
      { date: '2025-04-18', name: 'Good Friday' },
      { date: '2025-04-21', name: 'Easter Monday' },
      { date: '2025-05-01', name: 'Labour Day' },
      { date: '2025-12-25', name: 'Christmas Day' },
      { date: '2025-12-26', name: 'St. Stephen\'s Day' },
    ],
  },
];

/**
 * Feature descriptions and dependencies
 */
export const FEATURE_INFO = {
  monte_carlo: {
    name: 'Monte Carlo Simulation',
    description: 'Probabilistic timeline predictions using Monte Carlo methods',
    warning: 'May increase generation time for large projects',
    dependencies: [],
  },
  critical_path: {
    name: 'Critical Path Analysis',
    description: 'Identify critical tasks and timeline dependencies',
    warning: null,
    dependencies: [],
  },
  gantt_chart: {
    name: 'Gantt Chart',
    description: 'Visual timeline and task scheduling',
    warning: null,
    dependencies: [],
  },
  earned_value: {
    name: 'Earned Value Management',
    description: 'Track project performance and forecasting (EVM)',
    warning: null,
    dependencies: [],
  },
  resource_leveling: {
    name: 'Resource Leveling',
    description: 'Balance resource allocation and prevent overload',
    warning: 'Requires resource assignments for tasks',
    dependencies: [],
  },
  burndown_chart: {
    name: 'Burndown Chart',
    description: 'Sprint progress tracking and velocity metrics',
    warning: null,
    dependencies: ['sprint_tracking'],
  },
  sprint_tracking: {
    name: 'Sprint Tracking',
    description: 'Agile sprint management and reporting',
    warning: null,
    dependencies: [],
  },
} as const;

/**
 * Default feature configurations by template
 */
export const DEFAULT_FEATURES_BY_TEMPLATE: Record<string, Record<string, boolean>> = {
  agile_basic: {
    monte_carlo: false,
    critical_path: true,
    gantt_chart: true,
    earned_value: false,
    resource_leveling: false,
    burndown_chart: true,
    sprint_tracking: true,
  },
  agile_advanced: {
    monte_carlo: true,
    critical_path: true,
    gantt_chart: true,
    earned_value: true,
    resource_leveling: true,
    burndown_chart: true,
    sprint_tracking: true,
  },
  waterfall_basic: {
    monte_carlo: false,
    critical_path: true,
    gantt_chart: true,
    earned_value: false,
    resource_leveling: false,
    burndown_chart: false,
    sprint_tracking: false,
  },
  waterfall_advanced: {
    monte_carlo: true,
    critical_path: true,
    gantt_chart: true,
    earned_value: true,
    resource_leveling: true,
    burndown_chart: false,
    sprint_tracking: false,
  },
  hybrid: {
    monte_carlo: false,
    critical_path: true,
    gantt_chart: true,
    earned_value: true,
    resource_leveling: false,
    burndown_chart: true,
    sprint_tracking: true,
  },
};

/**
 * Wizard step configuration
 */
export const WIZARD_STEPS = [
  {
    id: 1,
    title: 'Project Basics',
    description: 'Name and template selection',
  },
  {
    id: 2,
    title: 'Sprint Configuration',
    description: 'Pattern, duration, and working days',
  },
  {
    id: 3,
    title: 'Holiday Calendar',
    description: 'Add holidays and import presets',
  },
  {
    id: 4,
    title: 'Feature Selection',
    description: 'Enable advanced features',
  },
  {
    id: 5,
    title: 'Review & Create',
    description: 'Confirm and create project',
  },
] as const;
