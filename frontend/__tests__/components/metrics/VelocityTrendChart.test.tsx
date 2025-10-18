/**
 * Tests for VelocityTrendChart component
 */

import { render, screen } from '@testing-library/react';
import VelocityTrendChart from '@/components/metrics/VelocityTrendChart';
import type { VelocityTrendResponse } from '@/types/historical-metrics';

const mockVelocityData: VelocityTrendResponse = {
  sprints: [
    {
      sprint_number: 1,
      sprint_name: 'Sprint 1',
      velocity: 21,
      planned_velocity: 20,
      completion_rate: 1.05,
      start_date: '2024-01-01',
      end_date: '2024-01-14',
      is_anomaly: false,
    },
    {
      sprint_number: 2,
      sprint_name: 'Sprint 2',
      velocity: 18,
      planned_velocity: 20,
      completion_rate: 0.9,
      start_date: '2024-01-15',
      end_date: '2024-01-28',
      is_anomaly: false,
    },
    {
      sprint_number: 3,
      sprint_name: 'Sprint 3',
      velocity: 35,
      planned_velocity: 20,
      completion_rate: 1.75,
      start_date: '2024-01-29',
      end_date: '2024-02-11',
      is_anomaly: true,
    },
    {
      sprint_number: 4,
      sprint_name: 'Sprint 4',
      velocity: 22,
      planned_velocity: 20,
      completion_rate: 1.1,
      start_date: '2024-02-12',
      end_date: '2024-02-25',
      is_anomaly: false,
    },
  ],
  moving_average: [21, 19.5, 24.67, 25],
  trend_direction: 'increasing',
  average_velocity: 24,
  anomalies: [2],
};

describe('VelocityTrendChart Component', () => {
  it('renders chart title and description', () => {
    render(<VelocityTrendChart data={mockVelocityData} />);

    expect(screen.getByText('Velocity Trend')).toBeInTheDocument();
    expect(
      screen.getByText(/Sprint velocity over time with moving average/i)
    ).toBeInTheDocument();
  });

  it('displays velocity metrics', () => {
    render(<VelocityTrendChart data={mockVelocityData} />);

    expect(screen.getByText('Average Velocity')).toBeInTheDocument();
    expect(screen.getByText('24')).toBeInTheDocument();
  });

  it('shows trend direction indicator', () => {
    render(<VelocityTrendChart data={mockVelocityData} />);

    expect(screen.getByText(/increasing/i)).toBeInTheDocument();
  });

  it('renders with empty data gracefully', () => {
    const emptyData: VelocityTrendResponse = {
      sprints: [],
      moving_average: [],
      trend_direction: 'stable',
      average_velocity: 0,
      anomalies: [],
    };

    render(<VelocityTrendChart data={emptyData} />);

    expect(screen.getByText(/No velocity data available/i)).toBeInTheDocument();
  });

  it('renders decreasing trend correctly', () => {
    const decreasingData: VelocityTrendResponse = {
      ...mockVelocityData,
      trend_direction: 'decreasing',
    };

    render(<VelocityTrendChart data={decreasingData} />);

    expect(screen.getByText(/decreasing/i)).toBeInTheDocument();
  });

  it('renders stable trend correctly', () => {
    const stableData: VelocityTrendResponse = {
      ...mockVelocityData,
      trend_direction: 'stable',
    };

    render(<VelocityTrendChart data={stableData} />);

    expect(screen.getByText(/stable/i)).toBeInTheDocument();
  });

  it('formats velocity values correctly', () => {
    render(<VelocityTrendChart data={mockVelocityData} />);

    // Average velocity should be displayed
    expect(screen.getByText('24')).toBeInTheDocument();
  });

  it('displays anomaly legend when anomalies exist', () => {
    render(<VelocityTrendChart data={mockVelocityData} />);

    expect(screen.getByText(/Anomaly detected/i)).toBeInTheDocument();
  });

  it('hides anomaly legend when no anomalies exist', () => {
    const dataWithoutAnomalies: VelocityTrendResponse = {
      ...mockVelocityData,
      anomalies: [],
    };

    render(<VelocityTrendChart data={dataWithoutAnomalies} />);

    expect(screen.queryByText(/Anomaly detected/i)).not.toBeInTheDocument();
  });
});
