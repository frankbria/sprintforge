/**
 * TDD Tests for CreateBaselineDialog Component
 *
 * Following RED-GREEN-REFACTOR cycle:
 * 🔴 These tests are written FIRST and will FAIL
 * 🟢 Implementation will make them pass
 * 🔵 Refactor for quality
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CreateBaselineDialog } from '@/components/baselines/CreateBaselineDialog';
import * as baselineApi from '@/lib/api/baselines';

// Mock the API module
jest.mock('@/lib/api/baselines');

const mockCreateBaseline = baselineApi.createBaseline as jest.MockedFunction<
  typeof baselineApi.createBaseline
>;

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

describe('CreateBaselineDialog', () => {
  const projectId = 'project-123';
  const onClose = jest.fn();
  const onSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Dialog Visibility', () => {
    it('does not render when isOpen is false', () => {
      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={false}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('renders dialog when isOpen is true', () => {
      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/create baseline/i)).toBeInTheDocument();
    });

    it('calls onClose when dialog is closed', async () => {
      const user = userEvent.setup();

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Form Fields', () => {
    it('renders name input field', () => {
      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    });

    it('renders description textarea field', () => {
      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    });

    it('marks name field as required', () => {
      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      expect(nameInput).toBeRequired();
    });
  });

  describe('Form Validation', () => {
    it('shows error when name is empty', async () => {
      const user = userEvent.setup();

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      });

      expect(mockCreateBaseline).not.toHaveBeenCalled();
    });

    it('shows error when name exceeds 255 characters', async () => {
      const user = userEvent.setup();

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      const longName = 'a'.repeat(256);
      await user.type(nameInput, longName);

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/must be less than 255 characters/i)).toBeInTheDocument();
      });

      expect(mockCreateBaseline).not.toHaveBeenCalled();
    });

    it('trims whitespace from name', async () => {
      const user = userEvent.setup();
      mockCreateBaseline.mockResolvedValueOnce({
        id: 'baseline-1',
        project_id: projectId,
        name: 'Test Baseline',
        created_at: '2025-10-17T10:00:00Z',
        is_active: false,
        snapshot_size_bytes: 1024,
      });

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, '  Test Baseline  ');

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockCreateBaseline).toHaveBeenCalledWith(projectId, {
          name: 'Test Baseline', // Trimmed
          description: undefined,
        });
      });
    });
  });

  describe('Form Submission', () => {
    it('submits form with valid data', async () => {
      const user = userEvent.setup();
      mockCreateBaseline.mockResolvedValueOnce({
        id: 'baseline-1',
        project_id: projectId,
        name: 'Q4 2025 Baseline',
        description: 'Initial plan',
        created_at: '2025-10-17T10:00:00Z',
        is_active: false,
        snapshot_size_bytes: 1024,
      });

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'Q4 2025 Baseline');

      const descriptionInput = screen.getByLabelText(/description/i);
      await user.type(descriptionInput, 'Initial plan');

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockCreateBaseline).toHaveBeenCalledWith(projectId, {
          name: 'Q4 2025 Baseline',
          description: 'Initial plan',
        });
      });
    });

    it('calls onSuccess after successful submission', async () => {
      const user = userEvent.setup();
      mockCreateBaseline.mockResolvedValueOnce({
        id: 'baseline-1',
        project_id: projectId,
        name: 'Test Baseline',
        created_at: '2025-10-17T10:00:00Z',
        is_active: false,
        snapshot_size_bytes: 1024,
      });

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'Test Baseline');

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
      });
    });

    it('shows loading state during submission', async () => {
      const user = userEvent.setup();
      mockCreateBaseline.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'Test Baseline');

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      expect(screen.getByText(/creating/i)).toBeInTheDocument();
    });

    it('resets form after successful submission', async () => {
      const user = userEvent.setup();
      mockCreateBaseline.mockResolvedValueOnce({
        id: 'baseline-1',
        project_id: projectId,
        name: 'Test Baseline',
        created_at: '2025-10-17T10:00:00Z',
        is_active: false,
        snapshot_size_bytes: 1024,
      });

      const { rerender } = render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'Test Baseline');

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
      });

      // Reopen dialog
      rerender(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={false}
          onClose={onClose}
          onSuccess={onSuccess}
        />
      );

      rerender(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />
      );

      // Form should be reset
      const newNameInput = screen.getByLabelText(/name/i) as HTMLInputElement;
      expect(newNameInput.value).toBe('');
    });
  });

  describe('Error Handling', () => {
    it('displays error message when snapshot too large (413)', async () => {
      const user = userEvent.setup();
      mockCreateBaseline.mockRejectedValueOnce(
        new Error('Snapshot size exceeds maximum allowed size (10MB)')
      );

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'Huge Baseline');

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/snapshot size exceeds/i)).toBeInTheDocument();
      });

      expect(onSuccess).not.toHaveBeenCalled();
    });

    it('displays generic error message for other errors', async () => {
      const user = userEvent.setup();
      mockCreateBaseline.mockRejectedValueOnce(new Error('Network error'));

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'Test Baseline');

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      expect(onSuccess).not.toHaveBeenCalled();
    });

    it('keeps dialog open after error', async () => {
      const user = userEvent.setup();
      mockCreateBaseline.mockRejectedValueOnce(new Error('Failed to create baseline'));

      render(
        <CreateBaselineDialog
          projectId={projectId}
          isOpen={true}
          onClose={onClose}
          onSuccess={onSuccess}
        />,
        { wrapper: createWrapper() }
      );

      const nameInput = screen.getByLabelText(/name/i);
      await user.type(nameInput, 'Test Baseline');

      const submitButton = screen.getByRole('button', { name: /create/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to create baseline/i)).toBeInTheDocument();
      });

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(onClose).not.toHaveBeenCalled();
    });
  });
});
