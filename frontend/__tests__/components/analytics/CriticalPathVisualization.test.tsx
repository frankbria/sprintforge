/**
 * Tests for CriticalPathVisualization component
 */

import { render, screen, waitFor } from '@testing-library/react';
import CriticalPathVisualization from '@/components/analytics/CriticalPathVisualization';
import { TestQueryClientProvider } from '../../setup/test-utils';
import * as analyticsApi from '@/lib/api/analytics';

// Mock the API module
jest.mock('@/lib/api/analytics');

const mockCriticalPathData = {
  critical_tasks: ['task-1', 'task-2'],
  total_duration: 120,
  float_time: { 'task-3': 5.0 },
  risk_tasks: ['task-4'],
  path_stability_score: 85.5,
};

// Mock Skeleton and Alert
jest.mock('@/components/ui/Skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));

jest.mock('@/components/ui/Alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div>{children}</div>,
}));

describe('CriticalPathVisualization Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (analyticsApi.getCriticalPathAnalytics as jest.Mock).mockResolvedValue(mockCriticalPathData);
  });

  it('renders critical path title', async () => {
    render(
      <TestQueryClientProvider>
        <CriticalPathVisualization projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Critical Path Analysis')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    (analyticsApi.getCriticalPathAnalytics as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(
      <TestQueryClientProvider>
        <CriticalPathVisualization projectId="test-project" />
      </TestQueryClientProvider>
    );

    const skeletons = screen.queryAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders without crashing', async () => {
    const { container } = render(
      <TestQueryClientProvider>
        <CriticalPathVisualization projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Critical Path Analysis')).toBeInTheDocument();
    });

    expect(container).toBeInTheDocument();
  });
});
