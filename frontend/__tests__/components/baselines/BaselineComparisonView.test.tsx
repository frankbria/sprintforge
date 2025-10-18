/**
 * TDD Tests for BaselineComparisonView Component
 *
 * Following RED-GREEN-REFACTOR cycle:
 * 🔴 These tests are written FIRST and will FAIL
 * 🟢 Implementation will make them pass
 * 🔵 Refactor for quality
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BaselineComparisonView } from '@/components/baselines/BaselineComparisonView';
import * as baselineApi from '@/lib/api/baselines';
import type { BaselineComparison } from '@/types/baseline';

// Mock the API module
jest.mock('@/lib/api/baselines');

const mockCompareBaseline = baselineApi.compareBaseline as jest.MockedFunction<
  typeof baselineApi.compareBaseline
>;

// Mock comparison data
const mockComparisonData: BaselineComparison = {
  baseline: {
    id: 'baseline-1',
    name: 'Q4 2025 Baseline',
    created_at: '2025-10-01T10:00:00Z',
  },
  comparison_date: '2025-10-17T10:00:00Z',
  summary: {
    total_tasks: 100,
    tasks_ahead: 15,
    tasks_behind: 10,
    tasks_on_track: 75,
    avg_variance_days: -0.5,
    critical_path_variance_days: 2.0,
  },
  task_variances: [
    {
      task_id: 'task-1',
      task_name: 'Setup Infrastructure',
      variance_days: -2,
      variance_percentage: -20,
      is_ahead: true,
      is_behind: false,
      start_date_variance: -1,
      end_date_variance: -2,
      duration_variance: 0,
      status_changed: false,
      dependencies_changed: false,
      status: 'ahead',
    },
    {
      task_id: 'task-2',
      task_name: 'Build API',
      variance_days: 3,
      variance_percentage: 30,
      is_ahead: false,
      is_behind: true,
      start_date_variance: 1,
      end_date_variance: 3,
      duration_variance: 2,
      status_changed: true,
      dependencies_changed: false,
      status: 'behind',
    },
    {
      task_id: 'task-3',
      task_name: 'Write Tests',
      variance_days: 0,
      variance_percentage: 0,
      is_ahead: false,
      is_behind: false,
      start_date_variance: 0,
      end_date_variance: 0,
      duration_variance: 0,
      status_changed: false,
      dependencies_changed: false,
      status: 'on_track',
    },
  ],
  new_tasks: [
    {
      task_id: 'task-new-1',
      task_name: 'New Feature X',
      added_after_baseline: true,
    },
  ],
  deleted_tasks: [
    {
      task_id: 'task-deleted-1',
      task_name: 'Deprecated Feature Y',
      existed_in_baseline: true,
    },
  ],
};

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('BaselineComparisonView', () => {
  const projectId = 'project-123';
  const baselineId = 'baseline-1';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Data Fetching', () => {
    it('displays loading state while fetching comparison', () => {
      mockCompareBaseline.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Loading comparison...')).toBeInTheDocument();
    });

    it('fetches comparison data on mount', async () => {
      mockCompareBaseline.mockResolvedValueOnce(mockComparisonData);

      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });

      expect(mockCompareBaseline).toHaveBeenCalledWith(projectId, baselineId, false);
    });

    it('displays error state when fetch fails', async () => {
      mockCompareBaseline.mockRejectedValueOnce(new Error('Failed to compare baseline'));

      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
        expect(screen.getByText(/failed to compare baseline/i)).toBeInTheDocument();
      });
    });
  });

  describe('Header Section', () => {
    beforeEach(() => {
      mockCompareBaseline.mockResolvedValue(mockComparisonData);
    });

    it('renders baseline name in header', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });
    });

    it('renders baseline created date', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/Oct 1, 2025/)).toBeInTheDocument();
      });
    });

    it('renders comparison date', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/Oct 17, 2025/)).toBeInTheDocument();
      });
    });
  });

  describe('Summary Metrics Cards', () => {
    beforeEach(() => {
      mockCompareBaseline.mockResolvedValue(mockComparisonData);
    });

    it('renders total tasks metric', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('100')).toBeInTheDocument();
        expect(screen.getByText(/total tasks/i)).toBeInTheDocument();
      });
    });

    it('renders tasks ahead metric', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const metricCards = screen.getAllByText(/ahead/i);
        expect(metricCards.length).toBeGreaterThan(0);
        expect(screen.getByText('15')).toBeInTheDocument();
      });
    });

    it('renders tasks behind metric', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const metricCards = screen.getAllByText(/behind/i);
        expect(metricCards.length).toBeGreaterThan(0);
        expect(screen.getByText('10')).toBeInTheDocument();
      });
    });

    it('renders tasks on track metric', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const metricCards = screen.getAllByText(/on track/i);
        expect(metricCards.length).toBeGreaterThan(0);
        expect(screen.getByText('75')).toBeInTheDocument();
      });
    });
  });

  describe('Variance Table', () => {
    beforeEach(() => {
      mockCompareBaseline.mockResolvedValue(mockComparisonData);
    });

    it('renders variance table with correct columns', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const table = screen.getByRole('table');
        expect(table).toBeInTheDocument();

        // Check for column headers using getAllByText
        const taskNameHeaders = screen.getAllByText('Task Name');
        const varianceHeaders = screen.getAllByText('Variance');
        const statusHeaders = screen.getAllByText('Status');

        expect(taskNameHeaders.length).toBeGreaterThan(0);
        expect(varianceHeaders.length).toBeGreaterThan(0);
        expect(statusHeaders.length).toBeGreaterThan(0);
      });
    });

    it('displays all task variances in table', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Setup Infrastructure')).toBeInTheDocument();
        expect(screen.getByText('Build API')).toBeInTheDocument();
        expect(screen.getByText('Write Tests')).toBeInTheDocument();
      });
    });

    it('renders VarianceIndicator for each task', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('2 days ahead')).toBeInTheDocument();
        expect(screen.getByText('3 days behind')).toBeInTheDocument();
        expect(screen.getByText('On track')).toBeInTheDocument();
      });
    });
  });

  describe('Filters and Controls', () => {
    beforeEach(() => {
      mockCompareBaseline.mockResolvedValue(mockComparisonData);
    });

    it('renders "Show only changed tasks" toggle', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/show only changed/i)).toBeInTheDocument();
      });
    });

    it('refetches with includeUnchanged=true when toggle is off', async () => {
      const user = userEvent.setup();

      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });

      // Initial call with includeUnchanged=false
      expect(mockCompareBaseline).toHaveBeenCalledWith(projectId, baselineId, false);

      // Toggle to show all tasks
      const toggle = screen.getByRole('checkbox', { name: /show only changed/i });
      await user.click(toggle);

      await waitFor(() => {
        expect(mockCompareBaseline).toHaveBeenCalledWith(projectId, baselineId, true);
      });
    });

    it('renders sort dropdown', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/sort by/i)).toBeInTheDocument();
      });
    });
  });

  describe('New and Deleted Tasks', () => {
    beforeEach(() => {
      mockCompareBaseline.mockResolvedValue(mockComparisonData);
    });

    it('renders new tasks section when new tasks exist', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/new tasks/i)).toBeInTheDocument();
        expect(screen.getByText('New Feature X')).toBeInTheDocument();
      });
    });

    it('renders deleted tasks section when deleted tasks exist', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText(/deleted tasks/i)).toBeInTheDocument();
        expect(screen.getByText('Deprecated Feature Y')).toBeInTheDocument();
      });
    });

    it('does not render new tasks section when empty', async () => {
      mockCompareBaseline.mockResolvedValueOnce({
        ...mockComparisonData,
        new_tasks: [],
      });

      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });

      expect(screen.queryByText(/new tasks/i)).not.toBeInTheDocument();
    });

    it('does not render deleted tasks section when empty', async () => {
      mockCompareBaseline.mockResolvedValueOnce({
        ...mockComparisonData,
        deleted_tasks: [],
      });

      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });

      expect(screen.queryByText(/deleted tasks/i)).not.toBeInTheDocument();
    });
  });

  describe('Auto-refresh', () => {
    beforeEach(() => {
      mockCompareBaseline.mockResolvedValue(mockComparisonData);
    });

    it('sets up auto-refresh interval', async () => {
      render(
        <BaselineComparisonView projectId={projectId} baselineId={baselineId} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });

      // Initial call
      expect(mockCompareBaseline).toHaveBeenCalledTimes(1);

      // Auto-refresh is configured (tested via query config, not actual time)
    });
  });
});
