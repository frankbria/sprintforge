/**
 * Tests for SimulationResultsChart component
 */

import { render, screen, waitFor } from '@testing-library/react';
import SimulationResultsChart from '@/components/analytics/SimulationResultsChart';
import { TestQueryClientProvider } from '../../setup/test-utils';
import * as analyticsApi from '@/lib/api/analytics';

// Mock the API module
jest.mock('@/lib/api/analytics');

const mockSimulationData = {
  percentiles: { p10: 100, p50: 115, p75: 125, p90: 135, p95: 140 },
  mean_duration: 115.5,
  std_deviation: 10.2,
  risk_level: 'medium' as const,
  confidence_80pct_range: [105, 130] as [number, number],
  histogram_data: [],
};

// Mock Skeleton and Alert
jest.mock('@/components/ui/Skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));

jest.mock('@/components/ui/Alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div>{children}</div>,
}));

describe('SimulationResultsChart Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (analyticsApi.getSimulationAnalytics as jest.Mock).mockResolvedValue(mockSimulationData);
  });

  it('renders component title', async () => {
    render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Monte Carlo Simulation Results')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    (analyticsApi.getSimulationAnalytics as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    const skeletons = screen.queryAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders without crashing', async () => {
    const { container } = render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Monte Carlo Simulation Results')).toBeInTheDocument();
    });

    expect(container).toBeInTheDocument();
  });

  it('displays simulation metrics correctly', async () => {
    render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('115.5 days')).toBeInTheDocument();
      expect(screen.getByText('10.2 days')).toBeInTheDocument();
      expect(screen.getByText('Risk Level: Medium')).toBeInTheDocument();
    });
  });

  it('displays percentiles correctly', async () => {
    render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('100.0 days')).toBeInTheDocument();
      expect(screen.getByText('115.0 days')).toBeInTheDocument();
      expect(screen.getByText('125.0 days')).toBeInTheDocument();
      expect(screen.getByText('135.0 days')).toBeInTheDocument();
      expect(screen.getByText('140.0 days')).toBeInTheDocument();
    });
  });

  it('displays confidence range correctly', async () => {
    render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('105.0 - 130.0 days')).toBeInTheDocument();
    });
  });

  it('shows error state when API fails', async () => {
    (analyticsApi.getSimulationAnalytics as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    render(
      <TestQueryClientProvider>
        <SimulationResultsChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load simulation data. Please try again.')).toBeInTheDocument();
    });
  });
});
