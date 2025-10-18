/**
 * Tests for NotificationRulesList component
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { NotificationRulesList } from '@/components/notifications/NotificationRulesList';
import type { NotificationRule } from '@/types/notification';

describe('NotificationRulesList', () => {
  const mockRules: NotificationRule[] = [
    {
      id: 'rule-1',
      user_id: 'user-1',
      name: 'Project Updates',
      event_type: 'project_updated',
      channels: ['email', 'in_app'],
      enabled: true,
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 'rule-2',
      user_id: 'user-1',
      name: 'Deadline Alerts',
      event_type: 'deadline_approaching',
      channels: ['email'],
      enabled: false,
      created_at: '2025-01-02T00:00:00Z',
      updated_at: '2025-01-02T00:00:00Z',
    },
  ];

  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnToggle = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render list of rules', () => {
    render(
      <NotificationRulesList
        rules={mockRules}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggle={mockOnToggle}
      />
    );

    expect(screen.getByText('Project Updates')).toBeInTheDocument();
    expect(screen.getByText('Deadline Alerts')).toBeInTheDocument();
  });

  it('should display empty state when no rules exist', () => {
    render(
      <NotificationRulesList
        rules={[]}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggle={mockOnToggle}
      />
    );

    expect(screen.getByText(/no notification rules/i)).toBeInTheDocument();
  });

  it('should display enabled status', () => {
    render(
      <NotificationRulesList
        rules={mockRules}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggle={mockOnToggle}
      />
    );

    const switches = screen.getAllByRole('switch');
    expect(switches[0]).toBeChecked();
    expect(switches[1]).not.toBeChecked();
  });

  it('should call onEdit when edit button is clicked', () => {
    render(
      <NotificationRulesList
        rules={mockRules}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggle={mockOnToggle}
      />
    );

    const editButtons = screen.getAllByRole('button', { name: /edit/i });
    fireEvent.click(editButtons[0]);

    expect(mockOnEdit).toHaveBeenCalledWith(mockRules[0]);
  });

  it('should call onDelete when delete button is clicked', () => {
    render(
      <NotificationRulesList
        rules={mockRules}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggle={mockOnToggle}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[0]);

    expect(mockOnDelete).toHaveBeenCalledWith('rule-1');
  });

  it('should call onToggle when switch is clicked', () => {
    render(
      <NotificationRulesList
        rules={mockRules}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggle={mockOnToggle}
      />
    );

    const switches = screen.getAllByRole('switch');
    fireEvent.click(switches[0]);

    expect(mockOnToggle).toHaveBeenCalledWith('rule-1', false);
  });

  it('should display channels as badges', () => {
    render(
      <NotificationRulesList
        rules={mockRules}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggle={mockOnToggle}
      />
    );

    expect(screen.getAllByText('Email').length).toBeGreaterThan(0);
    expect(screen.getByText('In-App')).toBeInTheDocument();
  });

  it('should show loading state', () => {
    render(
      <NotificationRulesList
        rules={mockRules}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onToggle={mockOnToggle}
        loading
      />
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
