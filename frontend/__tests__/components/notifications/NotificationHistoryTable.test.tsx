/**
 * Tests for NotificationHistoryTable component
 */

import { render, screen, fireEvent } from '@testing-library/react';
import { NotificationHistoryTable } from '@/components/notifications/NotificationHistoryTable';
import type { NotificationLog } from '@/types/notification';

describe('NotificationHistoryTable', () => {
  const mockLogs: NotificationLog[] = [
    {
      id: 'log-1',
      notification_id: 'notif-1',
      channel: 'email',
      status: 'delivered',
      sent_at: '2025-01-01T10:00:00Z',
      delivered_at: '2025-01-01T10:01:00Z',
      created_at: '2025-01-01T10:00:00Z',
    },
    {
      id: 'log-2',
      notification_id: 'notif-2',
      channel: 'in_app',
      status: 'sent',
      sent_at: '2025-01-02T12:00:00Z',
      created_at: '2025-01-02T12:00:00Z',
    },
    {
      id: 'log-3',
      notification_id: 'notif-3',
      channel: 'webhook',
      status: 'failed',
      error_message: 'Connection timeout',
      created_at: '2025-01-03T14:00:00Z',
    },
  ];

  it('should render table with logs', () => {
    render(<NotificationHistoryTable logs={mockLogs} />);

    expect(screen.getByText('email')).toBeInTheDocument();
    expect(screen.getByText('in_app')).toBeInTheDocument();
    expect(screen.getByText('webhook')).toBeInTheDocument();
  });

  it('should display empty state when no logs exist', () => {
    render(<NotificationHistoryTable logs={[]} />);

    expect(screen.getByText(/no notification history/i)).toBeInTheDocument();
  });

  it('should display status badges with correct colors', () => {
    render(<NotificationHistoryTable logs={mockLogs} />);

    const deliveredBadge = screen.getByText('delivered');
    const sentBadge = screen.getByText('sent');
    const failedBadge = screen.getByText('failed');

    expect(deliveredBadge).toHaveClass('bg-green-100', 'text-green-800');
    expect(sentBadge).toHaveClass('bg-blue-100', 'text-blue-800');
    expect(failedBadge).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('should display error message for failed logs', () => {
    render(<NotificationHistoryTable logs={mockLogs} />);

    expect(screen.getByText('Connection timeout')).toBeInTheDocument();
  });

  it('should format dates correctly', () => {
    render(<NotificationHistoryTable logs={mockLogs} />);

    expect(screen.getByText(/Jan 1, 2025/)).toBeInTheDocument();
  });

  it('should show loading state', () => {
    render(<NotificationHistoryTable logs={[]} loading />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should display pagination when total exceeds limit', () => {
    render(
      <NotificationHistoryTable
        logs={mockLogs}
        total={50}
        limit={20}
        offset={0}
        onPageChange={jest.fn()}
      />
    );

    expect(screen.getByText(/showing 1 to 20 of 50/i)).toBeInTheDocument();
  });

  it('should call onPageChange when pagination is clicked', () => {
    const mockOnPageChange = jest.fn();

    render(
      <NotificationHistoryTable
        logs={mockLogs}
        total={50}
        limit={20}
        offset={0}
        onPageChange={mockOnPageChange}
      />
    );

    const nextButtons = screen.getAllByRole('button', { name: /next/i });
    // Click the visible (desktop) next button
    fireEvent.click(nextButtons[nextButtons.length - 1]);

    expect(mockOnPageChange).toHaveBeenCalledWith(20);
  });
});
