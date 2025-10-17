/**
 * Tests for ResourceUtilizationChart component
 */

import { render, screen, waitFor } from '@testing-library/react';
import ResourceUtilizationChart from '@/components/analytics/ResourceUtilizationChart';
import { TestQueryClientProvider } from '../../setup/test-utils';
import * as analyticsApi from '@/lib/api/analytics';

// Mock the API module
jest.mock('@/lib/api/analytics');

const mockResourceData = {
  total_resources: 10,
  allocated_resources: 8,
  over_allocated: [
    {
      resource_id: 'resource-1',
      resource_name: 'John Doe',
      allocation_pct: 120.0,
      tasks_assigned: 8,
    },
  ],
  under_utilized: [
    {
      resource_id: 'resource-2',
      resource_name: 'Jane Smith',
      allocation_pct: 40.0,
      tasks_assigned: 2,
    },
    {
      resource_id: 'resource-3',
      resource_name: 'Bob Johnson',
      allocation_pct: 30.0,
      tasks_assigned: 1,
    },
  ],
  utilization_pct: 80.0,
  allocation_timeline: [],
};

// Mock Skeleton and Alert components
jest.mock('@/components/ui/Skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));

jest.mock('@/components/ui/Alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div>{children}</div>,
}));

describe('ResourceUtilizationChart Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (analyticsApi.getResourceAnalytics as jest.Mock).mockResolvedValue(mockResourceData);
  });

  it('renders component title', async () => {
    render(
      <TestQueryClientProvider>
        <ResourceUtilizationChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Resource Utilization')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    (analyticsApi.getResourceAnalytics as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(
      <TestQueryClientProvider>
        <ResourceUtilizationChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    const skeletons = screen.queryAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders without crashing', async () => {
    const { container } = render(
      <TestQueryClientProvider>
        <ResourceUtilizationChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Resource Utilization')).toBeInTheDocument();
    });

    expect(container).toBeInTheDocument();
  });

  it('displays resource metrics correctly', async () => {
    render(
      <TestQueryClientProvider>
        <ResourceUtilizationChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument(); // Total Resources
      expect(screen.getByText('8')).toBeInTheDocument(); // Allocated
      expect(screen.getByText('80.0%')).toBeInTheDocument(); // Utilization
    });
  });

  it('shows error state when API fails', async () => {
    (analyticsApi.getResourceAnalytics as jest.Mock).mockRejectedValue(
      new Error('API Error')
    );

    render(
      <TestQueryClientProvider>
        <ResourceUtilizationChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load resource data. Please try again.')).toBeInTheDocument();
    });
  });
});
