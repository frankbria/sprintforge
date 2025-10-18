/**
 * Tests for NotificationRuleForm component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NotificationRuleForm } from '@/components/notifications/NotificationRuleForm';
import type { NotificationRule } from '@/types/notification';

describe('NotificationRuleForm', () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render form fields', () => {
    render(<NotificationRuleForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    expect(screen.getByLabelText(/rule name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/event type/i)).toBeInTheDocument();
    expect(screen.getByText(/notification channels/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/enabled/i)).toBeInTheDocument();
  });

  it('should display form in create mode by default', () => {
    render(<NotificationRuleForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    expect(screen.getByRole('button', { name: /create rule/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /update rule/i })).not.toBeInTheDocument();
  });

  it('should display form in edit mode when rule is provided', () => {
    const rule: NotificationRule = {
      id: 'rule-1',
      user_id: 'user-1',
      name: 'Test Rule',
      event_type: 'project_created',
      channels: ['email', 'in_app'],
      enabled: true,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    };

    render(<NotificationRuleForm rule={rule} onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    expect(screen.getByRole('button', { name: /update rule/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Rule')).toBeInTheDocument();
  });

  it('should validate required fields', async () => {
    render(<NotificationRuleForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    const submitButton = screen.getByRole('button', { name: /create rule/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/rule name is required/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('should validate that at least one channel is selected', async () => {
    render(<NotificationRuleForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    const nameInput = screen.getByLabelText(/rule name/i);
    fireEvent.change(nameInput, { target: { value: 'Test Rule' } });

    const submitButton = screen.getByRole('button', { name: /create rule/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/at least one channel must be selected/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('should submit form with valid data', async () => {
    render(<NotificationRuleForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    const nameInput = screen.getByLabelText(/rule name/i);
    fireEvent.change(nameInput, { target: { value: 'My Rule' } });

    const eventSelect = screen.getByLabelText(/event type/i);
    fireEvent.change(eventSelect, { target: { value: 'project_created' } });

    const emailCheckbox = screen.getByLabelText(/email/i);
    fireEvent.click(emailCheckbox);

    const submitButton = screen.getByRole('button', { name: /create rule/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'My Rule',
        event_type: 'project_created',
        channels: ['email'],
        enabled: true,
      });
    });
  });

  it('should call onCancel when cancel button is clicked', () => {
    render(<NotificationRuleForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('should show loading state during submission', async () => {
    const slowSubmit = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<NotificationRuleForm onSubmit={slowSubmit} onCancel={mockOnCancel} />);

    const nameInput = screen.getByLabelText(/rule name/i);
    fireEvent.change(nameInput, { target: { value: 'Test' } });

    const emailCheckbox = screen.getByLabelText(/email/i);
    fireEvent.click(emailCheckbox);

    const submitButton = screen.getByRole('button', { name: /create rule/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });

  it('should allow multiple channels to be selected', async () => {
    render(<NotificationRuleForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    const nameInput = screen.getByLabelText(/rule name/i);
    fireEvent.change(nameInput, { target: { value: 'Multi-channel Rule' } });

    const emailCheckbox = screen.getByLabelText(/email/i);
    const inAppCheckbox = screen.getByLabelText(/in-app/i);

    fireEvent.click(emailCheckbox);
    fireEvent.click(inAppCheckbox);

    const submitButton = screen.getByRole('button', { name: /create rule/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          channels: expect.arrayContaining(['email', 'in_app']),
        })
      );
    });
  });
});
