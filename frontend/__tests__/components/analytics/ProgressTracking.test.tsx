/**
 * Tests for ProgressTracking component
 */

import { render, screen, waitFor } from '@testing-library/react';
import ProgressTracking from '@/components/analytics/ProgressTracking';
import { TestQueryClientProvider } from '../../setup/test-utils';
import * as analyticsApi from '@/lib/api/analytics';

// Mock the API module
jest.mock('@/lib/api/analytics');

const mockProgressData = {
  completion_pct: 65,
  tasks_completed: 50,
  tasks_total: 76,
  on_time_pct: 80,
  delayed_tasks: 5,
  burn_rate: 2.5,
  estimated_completion_date: '2025-12-31',
  variance_from_plan: -3,
};

// Mock Skeleton and Alert
jest.mock('@/components/ui/Skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));

jest.mock('@/components/ui/Alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div>{children}</div>,
}));

describe('ProgressTracking Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (analyticsApi.getProgressAnalytics as jest.Mock).mockResolvedValue(mockProgressData);
  });

  it('renders component title', async () => {
    render(
      <TestQueryClientProvider>
        <ProgressTracking projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Progress Tracking')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    (analyticsApi.getProgressAnalytics as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(
      <TestQueryClientProvider>
        <ProgressTracking projectId="test-project" />
      </TestQueryClientProvider>
    );

    const skeletons = screen.queryAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders without crashing', async () => {
    const { container } = render(
      <TestQueryClientProvider>
        <ProgressTracking projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Progress Tracking')).toBeInTheDocument();
    });

    expect(container).toBeInTheDocument();
  });

  it('displays progress metrics correctly', async () => {
    render(
      <TestQueryClientProvider>
        <ProgressTracking projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('65.0%')).toBeInTheDocument();
      expect(screen.getByText('50 of 76 tasks')).toBeInTheDocument();
      expect(screen.getByText('80.0%')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  it('shows error state when API fails', async () => {
    (analyticsApi.getProgressAnalytics as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    render(
      <TestQueryClientProvider>
        <ProgressTracking projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load progress data. Please try again.')).toBeInTheDocument();
    });
  });
});
