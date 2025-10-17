/**
 * Tests for Analytics Dashboard Page
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import AnalyticsPage from '@/app/projects/[id]/analytics/page';
import * as analyticsApi from '@/lib/api/analytics';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useParams: jest.fn(),
}));

// Mock analytics API
jest.mock('@/lib/api/analytics');

// Mock analytics components to avoid complex chart rendering in tests
jest.mock('@/components/analytics/ProjectHealthCard', () => {
  return function MockProjectHealthCard({ healthScore }: { healthScore: number }) {
    return <div data-testid="health-card">Health Score: {healthScore}</div>;
  };
});

jest.mock('@/components/analytics/MetricsGrid', () => {
  return function MockMetricsGrid() {
    return <div data-testid="metrics-grid">Metrics Grid</div>;
  };
});

jest.mock('@/components/analytics/CriticalPathVisualization', () => {
  return function MockCriticalPath() {
    return <div data-testid="critical-path">Critical Path</div>;
  };
});

jest.mock('@/components/analytics/ResourceUtilizationChart', () => {
  return function MockResourceChart() {
    return <div data-testid="resource-chart">Resource Chart</div>;
  };
});

jest.mock('@/components/analytics/SimulationResultsChart', () => {
  return function MockSimulationChart() {
    return <div data-testid="simulation-chart">Simulation Chart</div>;
  };
});

jest.mock('@/components/analytics/ProgressTracking', () => {
  return function MockProgressTracking() {
    return <div data-testid="progress-tracking">Progress Tracking</div>;
  };
});

// Mock analytics data
const mockAnalyticsData = {
  health_score: 75,
  critical_path_summary: {
    total_duration: 120,
    critical_tasks_count: 15,
    path_stability_score: 85.5,
  },
  resource_summary: {
    total_resources: 10,
    allocated_resources: 8,
    utilization_pct: 80.0,
    over_allocated_count: 1,
    under_utilized_count: 2,
  },
  simulation_summary: {
    risk_level: 'medium' as const,
    p50: 125.5,
    p90: 145.2,
    mean_duration: 130.0,
  },
  progress_summary: {
    completion_pct: 45.5,
    tasks_completed: 25,
    tasks_total: 55,
    on_time_pct: 85.0,
    delayed_tasks: 3,
  },
  generated_at: '2025-10-17T12:00:00Z',
};

describe('Analytics Page', () => {
  const projectId = 'test-project-123';
  let queryClient: QueryClient;

  beforeEach(() => {
    // Reset query client for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          cacheTime: 0,
        },
      },
    });

    // Mock useParams to return test project ID
    (useParams as jest.Mock).mockReturnValue({ id: projectId });

    // Reset all mocks
    jest.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  const renderWithProviders = (ui: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {ui}
      </QueryClientProvider>
    );
  };

  describe('Loading State', () => {
    it('should display loading skeleton when data is being fetched', () => {
      // Mock API to never resolve
      (analyticsApi.getAnalyticsOverview as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );

      const { container } = renderWithProviders(<AnalyticsPage />);

      // Check for skeleton elements by class
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });

  describe('Success State', () => {
    beforeEach(() => {
      (analyticsApi.getAnalyticsOverview as jest.Mock).mockResolvedValue(mockAnalyticsData);
    });

    it('should render analytics dashboard with all sections', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByText(/project analytics/i)).toBeInTheDocument();
      });

      // Check for main components
      expect(screen.getByTestId('health-card')).toBeInTheDocument();
      expect(screen.getByTestId('metrics-grid')).toBeInTheDocument();
    });

    it('should display health score correctly', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByText(`Health Score: ${mockAnalyticsData.health_score}`)).toBeInTheDocument();
      });
    });

    it('should display all tab navigation options', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument();
      });

      expect(screen.getByRole('tab', { name: /critical path/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /resources/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /simulation/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /progress/i })).toBeInTheDocument();
    });

    it('should display overview tab content by default', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByRole('tabpanel')).toBeInTheDocument();
      });

      // Check for overview summary cards - use more specific selectors
      const overviewPanel = screen.getByRole('tabpanel');
      expect(overviewPanel).toHaveTextContent(`${mockAnalyticsData.critical_path_summary.total_duration} days`);
      expect(overviewPanel).toHaveTextContent(mockAnalyticsData.resource_summary.total_resources.toString());
    });

    it('should switch between tabs when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument();
      });

      // Click on Critical Path tab
      const criticalPathTab = screen.getByRole('tab', { name: /critical path/i });
      await user.click(criticalPathTab);

      await waitFor(() => {
        expect(screen.getByTestId('critical-path')).toBeInTheDocument();
      });

      // Click on Resources tab
      const resourcesTab = screen.getByRole('tab', { name: /resources/i });
      await user.click(resourcesTab);

      await waitFor(() => {
        expect(screen.getByTestId('resource-chart')).toBeInTheDocument();
      });

      // Click on Simulation tab
      const simulationTab = screen.getByRole('tab', { name: /simulation/i });
      await user.click(simulationTab);

      await waitFor(() => {
        expect(screen.getByTestId('simulation-chart')).toBeInTheDocument();
      });

      // Click on Progress tab
      const progressTab = screen.getByRole('tab', { name: /progress/i });
      await user.click(progressTab);

      await waitFor(() => {
        expect(screen.getByTestId('progress-tracking')).toBeInTheDocument();
      });
    });

    it('should display data timestamp', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByText(/last updated:/i)).toBeInTheDocument();
      });
    });

    it('should have a refresh button', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
      });
    });

    it('should refetch data when refresh button is clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
      });

      expect(analyticsApi.getAnalyticsOverview).toHaveBeenCalledTimes(1);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(analyticsApi.getAnalyticsOverview).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Error State', () => {
    it('should display error message when API call fails', async () => {
      const errorMessage = 'Failed to fetch analytics data';
      (analyticsApi.getAnalyticsOverview as jest.Mock).mockRejectedValue(
        new Error(errorMessage)
      );

      renderWithProviders(<AnalyticsPage />);

      // Wait for error state to appear by checking for error message text
      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify retry button exists
      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    it('should have retry button in error state', async () => {
      (analyticsApi.getAnalyticsOverview as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );

      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      }, { timeout: 5000 });

      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });
  });

  describe('API Integration', () => {
    it('should call getAnalyticsOverview with correct project ID', async () => {
      (analyticsApi.getAnalyticsOverview as jest.Mock).mockResolvedValue(mockAnalyticsData);

      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(analyticsApi.getAnalyticsOverview).toHaveBeenCalledWith(projectId);
      });
    });
  });

  describe('Responsive Design', () => {
    beforeEach(() => {
      (analyticsApi.getAnalyticsOverview as jest.Mock).mockResolvedValue(mockAnalyticsData);
    });

    it('should render header with responsive classes', async () => {
      const { container } = renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByText(/project analytics/i)).toBeInTheDocument();
      });

      const header = container.querySelector('h1');
      expect(header?.className).toContain('sm:text-3xl');
    });

    it('should render container with responsive padding', async () => {
      const { container } = renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByText(/project analytics/i)).toBeInTheDocument();
      });

      const mainContainer = container.querySelector('.container');
      expect(mainContainer?.className).toContain('sm:p-6');
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      (analyticsApi.getAnalyticsOverview as jest.Mock).mockResolvedValue(mockAnalyticsData);
    });

    it('should have proper heading hierarchy', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1, name: /project analytics/i })).toBeInTheDocument();
      });
    });

    it('should have accessible tab navigation', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        const tabs = screen.getAllByRole('tab');
        expect(tabs.length).toBe(5);
        tabs.forEach(tab => {
          expect(tab).toHaveAttribute('aria-selected');
        });
      });
    });

    it('should have accessible refresh button', async () => {
      renderWithProviders(<AnalyticsPage />);

      await waitFor(() => {
        const refreshButton = screen.getByRole('button', { name: /refresh/i });
        expect(refreshButton).toBeInTheDocument();
      });
    });
  });
});
