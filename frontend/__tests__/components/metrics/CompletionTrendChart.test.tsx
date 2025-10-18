/**
 * Tests for CompletionTrendChart component
 */

import { render, screen } from '@testing-library/react';
import CompletionTrendChart from '@/components/metrics/CompletionTrendChart';
import type { CompletionTrendsResponse } from '@/types/historical-metrics';

const mockCompletionData: CompletionTrendsResponse = {
  trends: [
    {
      date: '2024-01-01',
      completed_tasks: 5,
      total_tasks: 20,
      completion_rate: 0.25,
      cumulative_completion: 5,
    },
    {
      date: '2024-01-08',
      completed_tasks: 8,
      total_tasks: 20,
      completion_rate: 0.4,
      cumulative_completion: 13,
    },
    {
      date: '2024-01-15',
      completed_tasks: 6,
      total_tasks: 20,
      completion_rate: 0.3,
      cumulative_completion: 19,
    },
    {
      date: '2024-01-22',
      completed_tasks: 1,
      total_tasks: 20,
      completion_rate: 0.05,
      cumulative_completion: 20,
    },
  ],
  granularity: 'weekly',
  patterns: {
    best_day: '2024-01-08',
    worst_day: '2024-01-22',
    average_rate: 0.25,
  },
};

describe('CompletionTrendChart Component', () => {
  it('renders chart title and description', () => {
    render(<CompletionTrendChart data={mockCompletionData} />);

    expect(screen.getByText('Completion Trends')).toBeInTheDocument();
    expect(
      screen.getByText(/Task completion rates over time/i)
    ).toBeInTheDocument();
  });

  it('displays granularity selector', () => {
    render(<CompletionTrendChart data={mockCompletionData} />);

    expect(screen.getByText('Weekly')).toBeInTheDocument();
  });

  it('shows average completion rate', () => {
    render(<CompletionTrendChart data={mockCompletionData} />);

    expect(screen.getByText('Average Rate')).toBeInTheDocument();
    expect(screen.getByText('25%')).toBeInTheDocument();
  });

  it('displays best and worst periods', () => {
    render(<CompletionTrendChart data={mockCompletionData} />);

    expect(screen.getByText(/Best Period/i)).toBeInTheDocument();
    expect(screen.getByText(/Worst Period/i)).toBeInTheDocument();
  });

  it('renders with empty data gracefully', () => {
    const emptyData: CompletionTrendsResponse = {
      trends: [],
      granularity: 'daily',
      patterns: {
        average_rate: 0,
      },
    };

    render(<CompletionTrendChart data={emptyData} />);

    expect(screen.getByText(/No completion data available/i)).toBeInTheDocument();
  });

  it('displays daily granularity correctly', () => {
    const dailyData: CompletionTrendsResponse = {
      ...mockCompletionData,
      granularity: 'daily',
    };

    render(<CompletionTrendChart data={dailyData} />);

    expect(screen.getByText('Daily')).toBeInTheDocument();
  });

  it('displays monthly granularity correctly', () => {
    const monthlyData: CompletionTrendsResponse = {
      ...mockCompletionData,
      granularity: 'monthly',
    };

    render(<CompletionTrendChart data={monthlyData} />);

    expect(screen.getByText('Monthly')).toBeInTheDocument();
  });

  it('displays total tasks completed', () => {
    render(<CompletionTrendChart data={mockCompletionData} />);

    expect(screen.getByText('Total Tasks')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('renders without best/worst day indicators', () => {
    const dataWithoutPatterns: CompletionTrendsResponse = {
      ...mockCompletionData,
      patterns: {
        average_rate: 0.25,
      },
    };

    render(<CompletionTrendChart data={dataWithoutPatterns} />);

    expect(screen.queryByText(/Best Period/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Worst Period/i)).not.toBeInTheDocument();
  });
});
