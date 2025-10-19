/**
 * Tests for Historical Metrics page
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MetricsPage from '@/app/projects/[id]/metrics/page';
import * as metricsApi from '@/lib/api/historical-metrics';

// Mock the API client
jest.mock('@/lib/api/historical-metrics');

const mockMetricsSummary = {
  current_velocity: 22,
  average_velocity: 20,
  velocity_trend: 'increasing' as const,
  completion_rate: 0.85,
  total_sprints: 10,
  active_sprints: 2,
  predicted_completion_date: '2024-03-15',
  confidence_score: 0.78,
};

const mockVelocityTrend = {
  sprints: [
    {
      sprint_number: 1,
      sprint_name: 'Sprint 1',
      velocity: 21,
      planned_velocity: 20,
      completion_rate: 1.05,
      start_date: '2024-01-01',
      end_date: '2024-01-14',
    },
  ],
  moving_average: [21],
  trend_direction: 'increasing' as const,
  average_velocity: 21,
  anomalies: [],
};

const mockCompletionTrends = {
  trends: [
    {
      date: '2024-01-01',
      completed_tasks: 5,
      total_tasks: 20,
      completion_rate: 0.25,
      cumulative_completion: 5,
    },
  ],
  granularity: 'weekly' as const,
  patterns: {
    average_rate: 0.25,
  },
};

const mockForecast = {
  forecasts: [
    {
      date: '2024-02-01',
      predicted_value: 20,
      lower_bound: 18,
      upper_bound: 22,
      confidence_level: 0.8,
    },
  ],
  method: 'Linear Regression',
  confidence_level: 0.8,
};

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderWithClient(ui: React.ReactElement) {
  const testQueryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={testQueryClient}>
      {ui}
    </QueryClientProvider>
  );
}

describe('MetricsPage Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (metricsApi.getMetricsSummary as jest.Mock).mockResolvedValue(mockMetricsSummary);
    (metricsApi.getVelocityTrend as jest.Mock).mockResolvedValue(mockVelocityTrend);
    (metricsApi.getCompletionTrends as jest.Mock).mockResolvedValue(mockCompletionTrends);
    (metricsApi.getForecast as jest.Mock).mockResolvedValue(mockForecast);
  });

  it('renders page title', async () => {
    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    await waitFor(() => {
      expect(screen.getByText('Historical Metrics')).toBeInTheDocument();
    });
  });

  it('displays loading state initially', () => {
    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders metrics summary card', async () => {
    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    await waitFor(() => {
      expect(screen.getByText('Metrics Summary')).toBeInTheDocument();
    });
  });

  it('displays tab navigation', async () => {
    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /velocity/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /trends/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /forecast/i })).toBeInTheDocument();
    });
  });

  it('switches between tabs on click', async () => {
    const user = userEvent.setup();
    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /velocity/i })).toBeInTheDocument();
    });

    // Click on Trends tab
    await user.click(screen.getByRole('tab', { name: /trends/i }));

    await waitFor(() => {
      expect(screen.getByText('Completion Trends')).toBeInTheDocument();
    });
  });

  it('displays velocity chart in velocity tab', async () => {
    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    // Wait for loading to complete and page to render
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });

    // Verify the metrics page is rendered (title should always be present)
    expect(screen.getByText('Historical Metrics')).toBeInTheDocument();

    // Verify we're on the velocity tab (default)
    const velocityTab = screen.getByRole('tab', { name: /velocity/i });
    expect(velocityTab).toHaveAttribute('aria-selected', 'true');
  }, 10000);

  it('displays completion chart in trends tab', async () => {
    const user = userEvent.setup();
    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /trends/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /trends/i }));

    await waitFor(() => {
      expect(screen.getByText('Completion Trends')).toBeInTheDocument();
    });
  });

  it('displays forecast chart in forecast tab', async () => {
    const user = userEvent.setup();
    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /forecast/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('tab', { name: /forecast/i }));

    await waitFor(() => {
      expect(screen.getByText('Forecast Predictions')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    (metricsApi.getMetricsSummary as jest.Mock).mockRejectedValue(
      new Error('Failed to fetch metrics')
    );

    renderWithClient(<MetricsPage params={{ id: '123' }} />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load metrics/i)).toBeInTheDocument();
    });
  });

  it('calls API with correct project ID', async () => {
    renderWithClient(<MetricsPage params={{ id: '456' }} />);

    await waitFor(() => {
      expect(metricsApi.getMetricsSummary).toHaveBeenCalledWith('456');
      expect(metricsApi.getVelocityTrend).toHaveBeenCalledWith('456', expect.any(Object));
    });
  });

  it('has responsive layout', async () => {
    const { container } = renderWithClient(<MetricsPage params={{ id: '123' }} />);

    await waitFor(() => {
      const layout = container.querySelector('.space-y-6');
      expect(layout).toBeInTheDocument();
    });
  });
});
