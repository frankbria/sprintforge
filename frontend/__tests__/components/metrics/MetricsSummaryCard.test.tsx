/**
 * Tests for MetricsSummaryCard component
 */

import { render, screen } from '@testing-library/react';
import MetricsSummaryCard from '@/components/metrics/MetricsSummaryCard';
import type { MetricsSummaryResponse } from '@/types/historical-metrics';

const mockSummaryData: MetricsSummaryResponse = {
  current_velocity: 22,
  average_velocity: 20,
  velocity_trend: 'increasing',
  completion_rate: 0.85,
  total_sprints: 10,
  active_sprints: 2,
  predicted_completion_date: '2024-03-15',
  confidence_score: 0.78,
};

describe('MetricsSummaryCard Component', () => {
  it('renders card title', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Metrics Summary')).toBeInTheDocument();
  });

  it('displays current velocity', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Current Velocity')).toBeInTheDocument();
    expect(screen.getByText('22')).toBeInTheDocument();
  });

  it('displays average velocity', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Average Velocity')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('shows velocity trend indicator', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Velocity Trend')).toBeInTheDocument();
    expect(screen.getByText(/increasing/i)).toBeInTheDocument();
  });

  it('displays completion rate as percentage', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Completion Rate')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('shows total sprints', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Total Sprints')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('shows active sprints', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Active Sprints')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('displays predicted completion date when available', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Predicted Completion')).toBeInTheDocument();
    // Date format is "Mar 15, 2024" - check for the formatted date string
    expect(screen.getByText(/Mar.*2024/i)).toBeInTheDocument();
  });

  it('shows confidence score', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    expect(screen.getByText('Confidence Score')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument();
  });

  it('renders without predicted completion date', () => {
    const dataWithoutPrediction: MetricsSummaryResponse = {
      ...mockSummaryData,
      predicted_completion_date: undefined,
    };

    render(<MetricsSummaryCard data={dataWithoutPrediction} />);

    expect(screen.queryByText('Predicted Completion')).not.toBeInTheDocument();
  });

  it('displays increasing trend with green color', () => {
    const { container } = render(<MetricsSummaryCard data={mockSummaryData} />);

    const trendElement = container.querySelector('.text-green-600');
    expect(trendElement).toBeInTheDocument();
  });

  it('displays decreasing trend with red color', () => {
    const decreasingData: MetricsSummaryResponse = {
      ...mockSummaryData,
      velocity_trend: 'decreasing',
    };

    const { container } = render(<MetricsSummaryCard data={decreasingData} />);

    const trendElement = container.querySelector('.text-red-600');
    expect(trendElement).toBeInTheDocument();
  });

  it('displays stable trend with gray color', () => {
    const stableData: MetricsSummaryResponse = {
      ...mockSummaryData,
      velocity_trend: 'stable',
    };

    const { container } = render(<MetricsSummaryCard data={stableData} />);

    const trendElement = container.querySelector('.text-gray-600');
    expect(trendElement).toBeInTheDocument();
  });

  it('has responsive grid layout', () => {
    const { container } = render(<MetricsSummaryCard data={mockSummaryData} />);

    const grid = container.querySelector('.grid');
    expect(grid).toBeInTheDocument();
  });

  it('displays all metrics in organized sections', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    // All key metrics should be present
    expect(screen.getByText('Current Velocity')).toBeInTheDocument();
    expect(screen.getByText('Average Velocity')).toBeInTheDocument();
    expect(screen.getByText('Velocity Trend')).toBeInTheDocument();
    expect(screen.getByText('Completion Rate')).toBeInTheDocument();
    expect(screen.getByText('Total Sprints')).toBeInTheDocument();
    expect(screen.getByText('Active Sprints')).toBeInTheDocument();
    expect(screen.getByText('Confidence Score')).toBeInTheDocument();
  });

  it('formats completion rate correctly', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    // 0.85 should be displayed as 85%
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('formats confidence score correctly', () => {
    render(<MetricsSummaryCard data={mockSummaryData} />);

    // 0.78 should be displayed as 78%
    expect(screen.getByText('78%')).toBeInTheDocument();
  });
});
