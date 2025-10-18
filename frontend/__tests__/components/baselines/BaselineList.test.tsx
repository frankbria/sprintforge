/**
 * TDD Tests for BaselineList Component
 *
 * Following RED-GREEN-REFACTOR cycle:
 * 🔴 These tests are written FIRST and will FAIL
 * 🟢 Implementation will make them pass
 * 🔵 Refactor for quality
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BaselineList } from '@/components/baselines/BaselineList';
import * as baselineApi from '@/lib/api/baselines';
import type { BaselineListResponse } from '@/types/baseline';

// Mock the API module
jest.mock('@/lib/api/baselines');

const mockGetBaselines = baselineApi.getBaselines as jest.MockedFunction<
  typeof baselineApi.getBaselines
>;
const mockDeleteBaseline = baselineApi.deleteBaseline as jest.MockedFunction<
  typeof baselineApi.deleteBaseline
>;
const mockSetBaselineActive = baselineApi.setBaselineActive as jest.MockedFunction<
  typeof baselineApi.setBaselineActive
>;

// Mock data
const mockBaselinesResponse: BaselineListResponse = {
  baselines: [
    {
      id: 'baseline-1',
      project_id: 'project-123',
      name: 'Q4 2025 Baseline',
      description: 'Initial project plan',
      created_at: '2025-10-01T10:00:00Z',
      is_active: true,
      snapshot_size_bytes: 1024,
    },
    {
      id: 'baseline-2',
      project_id: 'project-123',
      name: 'Q1 2026 Baseline',
      description: null,
      created_at: '2025-10-15T14:00:00Z',
      is_active: false,
      snapshot_size_bytes: 2048,
    },
  ],
  total: 2,
  page: 1,
  limit: 50,
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

describe('BaselineList', () => {
  const projectId = 'project-123';

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Data Fetching', () => {
    it('displays loading state while fetching baselines', () => {
      mockGetBaselines.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Loading baselines...')).toBeInTheDocument();
    });

    it('fetches and displays baselines on mount', async () => {
      mockGetBaselines.mockResolvedValueOnce(mockBaselinesResponse);

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
        expect(screen.getByText('Q1 2026 Baseline')).toBeInTheDocument();
      });

      expect(mockGetBaselines).toHaveBeenCalledWith(projectId, 1, 50);
    });

    it('displays error state when fetch fails', async () => {
      mockGetBaselines.mockRejectedValueOnce(new Error('Failed to fetch baselines'));

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
        expect(screen.getByText(/failed to fetch baselines/i)).toBeInTheDocument();
      });
    });

    it('displays empty state when no baselines exist', async () => {
      mockGetBaselines.mockResolvedValueOnce({
        baselines: [],
        total: 0,
        page: 1,
        limit: 50,
      });

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText(/no baselines/i)).toBeInTheDocument();
      });
    });
  });

  describe('Table Display', () => {
    beforeEach(() => {
      mockGetBaselines.mockResolvedValue(mockBaselinesResponse);
    });

    it('renders table with correct columns', async () => {
      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Created')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Size')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('displays active baseline with badge', async () => {
      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument();
      });
    });

    it('formats created date correctly', async () => {
      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        // Should display formatted dates for both baselines
        expect(screen.getByText('Oct 1, 2025')).toBeInTheDocument();
        expect(screen.getByText('Oct 15, 2025')).toBeInTheDocument();
      });
    });

    it('displays snapshot size in human-readable format', async () => {
      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        // 1024 bytes = 1 KB, 2048 bytes = 2 KB
        expect(screen.getByText('1 KB')).toBeInTheDocument();
        expect(screen.getByText('2 KB')).toBeInTheDocument();
      });
    });
  });

  describe('Baseline Actions', () => {
    beforeEach(() => {
      mockGetBaselines.mockResolvedValue(mockBaselinesResponse);
    });

    it('shows "Set Active" button for inactive baselines', async () => {
      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const buttons = screen.getAllByRole('button', { name: /set active/i });
        expect(buttons).toHaveLength(1); // Only for baseline-2
      });
    });

    it('activates baseline when "Set Active" clicked', async () => {
      const user = userEvent.setup();
      mockSetBaselineActive.mockResolvedValueOnce({
        id: 'baseline-2',
        is_active: true,
        message: 'Baseline activated successfully',
      });

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Q1 2026 Baseline')).toBeInTheDocument();
      });

      const setActiveButton = screen.getByRole('button', { name: /set active/i });
      await user.click(setActiveButton);

      await waitFor(() => {
        expect(mockSetBaselineActive).toHaveBeenCalledWith(projectId, 'baseline-2');
      });
    });

    it('shows Compare button for all baselines', async () => {
      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const compareButtons = screen.getAllByRole('button', { name: /compare/i });
        expect(compareButtons).toHaveLength(2);
      });
    });

    it('shows Delete button for all baselines', async () => {
      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        expect(deleteButtons).toHaveLength(2);
      });
    });
  });

  describe('Delete Baseline', () => {
    beforeEach(() => {
      mockGetBaselines.mockResolvedValue(mockBaselinesResponse);
    });

    it('shows confirmation dialog when delete clicked', async () => {
      const user = userEvent.setup();

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });
    });

    it('deletes baseline when confirmed', async () => {
      const user = userEvent.setup();
      mockDeleteBaseline.mockResolvedValueOnce();

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm|delete/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockDeleteBaseline).toHaveBeenCalledWith(projectId, 'baseline-1');
      });
    });

    it('cancels delete when user clicks cancel', async () => {
      const user = userEvent.setup();

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByText('Q4 2025 Baseline')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
      });

      expect(mockDeleteBaseline).not.toHaveBeenCalled();
    });
  });

  describe('Create Baseline Button', () => {
    beforeEach(() => {
      mockGetBaselines.mockResolvedValue(mockBaselinesResponse);
    });

    it('renders "Create Baseline" button', async () => {
      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create baseline/i })).toBeInTheDocument();
      });
    });

    it('opens create dialog when button clicked', async () => {
      const user = userEvent.setup();

      render(<BaselineList projectId={projectId} />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create baseline/i })).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /create baseline/i });
      await user.click(createButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });
  });
});
