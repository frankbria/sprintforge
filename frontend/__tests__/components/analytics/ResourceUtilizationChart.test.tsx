/**
 * Tests for ResourceUtilizationChart component
 */

import { render, screen } from '@testing-library/react';
import ResourceUtilizationChart from '@/components/analytics/ResourceUtilizationChart';
import { TestQueryClientProvider } from '../../setup/test-utils';

// Mock the API function
jest.mock('@/lib/api/analytics', () => ({
  getResourceAnalytics: jest.fn().mockResolvedValue({
    total_resources: 10,
    allocated_resources: 8,
    utilization_pct: 80,
    over_allocated: [],
    under_utilized: [],
    resource_timeline: {},
  }),
}));

// Mock Skeleton and Alert components
jest.mock('@/components/ui/Skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));

jest.mock('@/components/ui/Alert', () => ({
  Alert: ({ children }: any) => <div data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div>{children}</div>,
}));

describe('ResourceUtilizationChart Component', () => {
  it('renders component title', () => {
    render(
      <TestQueryClientProvider>
        <ResourceUtilizationChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    expect(screen.getByText('Resource Utilization')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(
      <TestQueryClientProvider>
        <ResourceUtilizationChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    const skeletons = screen.queryAllByTestId('skeleton');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders without crashing', () => {
    const { container } = render(
      <TestQueryClientProvider>
        <ResourceUtilizationChart projectId="test-project" />
      </TestQueryClientProvider>
    );

    expect(container).toBeInTheDocument();
  });
});
