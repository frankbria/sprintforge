/**
 * Tests for ProgressTracking component
 */

import { render, screen } from '@testing-library/react';
import ProgressTracking from '@/components/analytics/ProgressTracking';
import { TestQueryClientProvider } from '../../setup/test-utils';

// Mock the API function
jest.mock('@/lib/api/analytics', () => ({
  getProgressAnalytics: jest.fn().mockResolvedValue({
    completion_pct: 65,
    tasks_completed: 50,
    tasks_total: 76,
    on_time_pct: 80,
    delayed_tasks: 5,
    burn_rate: 2.5,
    estimated_completion_date: '2025-12-31',
    variance_from_plan: -3,
  }),
}));

// Mock Skeleton and Alert
jest.mock('@/components/ui/Skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));

jest.mock('@/components/ui/Alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div>{children}</div>,
}));

describe('ProgressTracking Component', () => {
  it('renders component title', () => {
    render(
      <TestQueryClientProvider>
        <ProgressTracking projectId="test-project" />
      </TestQueryClientProvider>
    );

    expect(screen.getByText('Progress Tracking')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(
      <TestQueryClientProvider>
        <ProgressTracking projectId="test-project" />
      </TestQueryClientProvider>
    );

    const skeletons = screen.queryAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders without crashing', () => {
    const { container } = render(
      <TestQueryClientProvider>
        <ProgressTracking projectId="test-project" />
      </TestQueryClientProvider>
    );

    expect(container).toBeInTheDocument();
  });
});
