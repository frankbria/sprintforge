/**
 * Tests for SimulationResultsChart component
 */

import { render, screen } from '@testing-library/react';
import SimulationResultsChart from '@/components/analytics/SimulationResultsChart';
import { TestQueryClientProvider } from '../../setup/test-utils';

// Mock the API function
jest.mock('@/lib/api/analytics', () => ({
  getSimulationAnalytics: jest.fn().mockResolvedValue({
    percentiles: { p10: 100, p50: 115, p75: 125, p90: 135, p95: 140 },
    mean_duration: 115.5,
    std_deviation: 10.2,
    risk_level: 'medium',
    confidence_80pct_range: [105, 130],
    histogram_data: [],
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

describe('SimulationResultsChart Component', () => {
  it('renders component title', () => {
    render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    expect(screen.getByText('Monte Carlo Simulation Results')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    const skeletons = screen.queryAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders without crashing', () => {
    const { container } = render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    expect(container).toBeInTheDocument();
  });
});
