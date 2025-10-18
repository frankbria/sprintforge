/**
 * Tests for ForecastChart component
 */

import { render, screen } from '@testing-library/react';
import ForecastChart from '@/components/metrics/ForecastChart';
import type { ForecastData } from '@/types/historical-metrics';

const mockForecastData: ForecastData = {
  forecasts: [
    {
      date: '2024-02-01',
      predicted_value: 20,
      lower_bound: 18,
      upper_bound: 22,
      confidence_level: 0.8,
    },
    {
      date: '2024-02-08',
      predicted_value: 21,
      lower_bound: 18,
      upper_bound: 24,
      confidence_level: 0.8,
    },
    {
      date: '2024-02-15',
      predicted_value: 22,
      lower_bound: 18,
      upper_bound: 26,
      confidence_level: 0.8,
    },
    {
      date: '2024-02-22',
      predicted_value: 23,
      lower_bound: 18,
      upper_bound: 28,
      confidence_level: 0.8,
    },
  ],
  method: 'Linear Regression',
  confidence_level: 0.8,
  rmse: 2.5,
  mae: 1.8,
};

describe('ForecastChart Component', () => {
  it('renders chart title and description', () => {
    render(<ForecastChart data={mockForecastData} />);

    expect(screen.getByText('Forecast Predictions')).toBeInTheDocument();
    expect(
      screen.getByText(/Future predictions with confidence intervals/i)
    ).toBeInTheDocument();
  });

  it('displays forecast method', () => {
    render(<ForecastChart data={mockForecastData} />);

    expect(screen.getByText('Method')).toBeInTheDocument();
    expect(screen.getByText('Linear Regression')).toBeInTheDocument();
  });

  it('shows confidence level', () => {
    render(<ForecastChart data={mockForecastData} />);

    expect(screen.getByText('Confidence Level')).toBeInTheDocument();
    expect(screen.getByText('80%')).toBeInTheDocument();
  });

  it('displays accuracy metrics when available', () => {
    render(<ForecastChart data={mockForecastData} />);

    expect(screen.getByText('RMSE')).toBeInTheDocument();
    expect(screen.getByText('2.5')).toBeInTheDocument();
    expect(screen.getByText('MAE')).toBeInTheDocument();
    expect(screen.getByText('1.8')).toBeInTheDocument();
  });

  it('renders with empty data gracefully', () => {
    const emptyData: ForecastData = {
      forecasts: [],
      method: 'None',
      confidence_level: 0,
    };

    render(<ForecastChart data={emptyData} />);

    expect(screen.getByText(/No forecast data available/i)).toBeInTheDocument();
  });

  it('renders without accuracy metrics', () => {
    const dataWithoutMetrics: ForecastData = {
      forecasts: mockForecastData.forecasts,
      method: 'Simple Average',
      confidence_level: 0.7,
    };

    render(<ForecastChart data={dataWithoutMetrics} />);

    expect(screen.getByText('Method')).toBeInTheDocument();
    expect(screen.queryByText('RMSE')).not.toBeInTheDocument();
  });

  it('displays confidence interval information', () => {
    render(<ForecastChart data={mockForecastData} />);

    expect(screen.getByText(/Forecast Confidence/i)).toBeInTheDocument();
    expect(screen.getByText(/80% confidence interval/i)).toBeInTheDocument();
  });

  it('formats confidence level correctly', () => {
    const customData: ForecastData = {
      ...mockForecastData,
      confidence_level: 0.95,
    };

    render(<ForecastChart data={customData} />);

    expect(screen.getByText('95%')).toBeInTheDocument();
  });
});
