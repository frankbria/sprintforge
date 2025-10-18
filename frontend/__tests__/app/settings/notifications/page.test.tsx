/**
 * Tests for notification settings page
 * Note: These are simplified integration tests focusing on core rendering and structure
 */

import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import NotificationSettingsPage from '@/app/settings/notifications/page';

// Mock the API module
jest.mock('@/lib/api/notifications', () => ({
  getNotificationRules: jest.fn().mockResolvedValue({ total: 0, rules: [] }),
  getNotificationLogs: jest.fn().mockResolvedValue({ total: 0, limit: 20, offset: 0, logs: [] }),
  createNotificationRule: jest.fn(),
  updateNotificationRule: jest.fn(),
  deleteNotificationRule: jest.fn(),
}));

describe('NotificationSettingsPage', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <NotificationSettingsPage />
      </QueryClientProvider>
    );
  };

  it('should render page title and description', () => {
    renderPage();

    expect(screen.getByText('Notification Settings')).toBeInTheDocument();
    expect(screen.getByText(/manage your notification preferences/i)).toBeInTheDocument();
  });

  it('should render tabs for settings and history', () => {
    renderPage();

    expect(screen.getByRole('tab', { name: /settings/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /history/i })).toBeInTheDocument();
  });

  it('should render notification rules section', () => {
    renderPage();

    expect(screen.getByText('Notification Rules')).toBeInTheDocument();
  });

  it('should render create rule button', () => {
    renderPage();

    expect(screen.getByRole('button', { name: /create rule/i })).toBeInTheDocument();
  });
});
