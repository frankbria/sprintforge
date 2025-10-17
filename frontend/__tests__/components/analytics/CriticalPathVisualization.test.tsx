/**
 * Tests for CriticalPathVisualization component
 */

import { render, screen } from '@testing-library/react';
import CriticalPathVisualization from '@/components/analytics/CriticalPathVisualization';
import { TestQueryClientProvider } from '../../setup/test-utils';

// Mock the API function
jest.mock('@/lib/api/analytics', () => ({
  getCriticalPathAnalytics: jest.fn().mockResolvedValue({
    critical_tasks: [],
    total_duration: 120,
    float_time: {},
    risk_tasks: [],
    path_stability_score: 78.5,
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

describe('CriticalPathVisualization Component', () => {
  it('renders critical path title', () => {
    render(
      <TestQueryClientProvider>
        <CriticalPathVisualization projectId="test-project" />
      </TestQueryClientProvider>
    );

    expect(screen.getByText('Critical Path Analysis')).toBeInTheDocument();
  });


  it('shows loading state initially', () => {
    render(
      <TestQueryClientProvider>
        <CriticalPathVisualization projectId="test-project" />
      </TestQueryClientProvider>
    );

    const skeletons = screen.queryAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders without crashing', () => {
    const { container } = render(
      <TestQueryClientProvider>
        <CriticalPathVisualization projectId="test-project" />
      </TestQueryClientProvider>
    );

    expect(container).toBeInTheDocument();
  });
});
